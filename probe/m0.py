"""M0 feasibility probe. Stdlib only.

  python probe/m0.py enumerate   # data/launches.tsv  (appid, release date, name)
  python probe/m0.py sample      # data/m0_sample.tsv (windowed review counts)
  python probe/m0.py report      # prints the M0 numbers

Nothing here is a result. It measures whether the question can be asked.
"""
import datetime as dt, json, random, re, sys, time, urllib.request, urllib.error
from concurrent.futures import ThreadPoolExecutor

UA = {"User-Agent": "Longtail-M0 (research; github.com/Muhammad-Haris-3)"}
DAY = 86400
# The store rate-limits near ~200 requests / 5 min per IP (429s after ~300 calls at 6 in flight).
PACE = 0.5  # date-filtered calls take ~4s server-side, so 2 workers stay near 0.5 calls/s
SEARCH = ("https://store.steampowered.com/search/results/?query&start={s}&count=100"
          "&sort_by=Released_DESC&category1=998&infinite=1&cc=us&l=english")
REVIEWS = ("https://store.steampowered.com/appreviews/{a}?json=1&language=all&purchase_type=all"
           "&num_per_page=0&filter=all")


def get(url):
    time.sleep(PACE)
    for wait in (60, 300, 600, 900, 1800):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
                return json.loads(r.read().decode("utf-8"))
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as e:
            print(f"  retry in {wait}s: {e}", file=sys.stderr)
            time.sleep(wait)
    raise RuntimeError(url)


def parse_date(s):
    # Store dates look like "Sep 29, 2026"; "Q4 2026", "Coming soon" etc. are not launches.
    try:
        return dt.datetime.strptime(s.strip(), "%b %d, %Y").date()
    except ValueError:
        return None


def enumerate_launches(start_offset=0, stop=dt.date(2023, 1, 1)):
    with open("data/launches.tsv", "a", encoding="utf-8") as out:
        s = start_offset
        while True:
            h = get(SEARCH.format(s=s))["results_html"]
            rows = re.findall(r'data-ds-appid="(\d+)".*?<span class="title">([^<]*)</span>'
                              r'.*?search_released[^>]*>\s*([^<]*?)\s*<', h, re.S)
            if not rows:
                break
            for appid, name, rel in rows:
                d = parse_date(rel)
                out.write(f"{appid}\t{d or ''}\t{name}\n")
            out.flush()
            last = [parse_date(r[2]) for r in rows if parse_date(r[2])]
            print(s, last[-1] if last else "-")
            if last and last[-1] < stop:
                break
            s += 100
            time.sleep(1)


def count(appid, start, end):
    u = REVIEWS.format(a=appid) + f"&start_date={start}&end_date={end}&date_range_type=include"
    return get(u)["query_summary"]["total_reviews"]


def sample(n=600, seed=20260930, lo=dt.date(2024, 1, 1), hi=dt.date(2025, 6, 30)):
    seen, pool = set(), []
    for line in open("data/launches.tsv", encoding="utf-8"):
        appid, d, _ = line.rstrip("\n").split("\t", 2)
        if d and appid not in seen and lo <= dt.date.fromisoformat(d) <= hi:
            seen.add(appid)
            pool.append((appid, d))
    pool.sort()
    random.Random(seed).shuffle(pool)
    print(f"pool {len(pool)} launches in [{lo}, {hi}]; sampling {n}")
    def one(job):
        appid, d = job
        t0 = int(dt.datetime.combine(dt.date.fromisoformat(d), dt.time(), dt.timezone.utc).timestamp())
        c = [count(appid, 1, t0 - 1)] + [count(appid, t0, t0 + k * DAY - 1) for k in (7, 30, 90, 365)]
        total = get(REVIEWS.format(a=appid))["query_summary"]["total_reviews"]
        return [appid, d, *c, total]

    # Resumable, 2 workers: 6 in flight drew 429s after ~300 calls.
    path = "data/m0_sample.tsv"
    try:
        done = {l.split("\t")[0] for l in open(path, encoding="utf-8")}
    except FileNotFoundError:
        done = set()
    with open(path, "a", encoding="utf-8") as out, ThreadPoolExecutor(2) as ex:
        if not done:
            out.write("appid\trelease\tpre\tw1\td30\td90\td365\tall\n")
        for i, row in enumerate(ex.map(one, [j for j in pool[:n] if j[0] not in done])):
            out.write("\t".join(map(str, row)) + "\n")
            out.flush()
            if i % 25 == 0:
                print(i, *row, flush=True)


def q(xs, p):
    xs = sorted(xs)
    return xs[min(len(xs) - 1, int(p * len(xs)))]


def report():
    rows = [l.rstrip("\n").split("\t") for l in open("data/m0_sample.tsv", encoding="utf-8")][1:]
    R = [dict(zip(("appid", "rel", "pre", "w1", "d30", "d90", "d365", "all"), r)) for r in rows]
    for r in R:
        for k in ("pre", "w1", "d30", "d90", "d365", "all"):
            r[k] = int(r[k])
    n = len(R)
    print(f"sampled launches: {n}")
    print(f"zero reviews in year 1: {sum(r['d365'] == 0 for r in R) / n:.1%}")
    for k in (1, 5, 10, 20, 50):
        print(f"week-1 reviews >= {k:>2}: {sum(r['w1'] >= k for r in R) / n:.1%}")
    pre = [r for r in R if r["pre"] > 0]
    print(f"any review before store release date: {len(pre) / n:.1%} "
          f"(pre >= week-1: {sum(r['pre'] >= r['w1'] for r in pre) / n:.1%})")
    # Windowed counts must never exceed the all-time total; if they do, the date filter is not doing what we think.
    bad = sum(r["pre"] + r["d365"] > r["all"] for r in R)
    print(f"windowed > all-time total (should be 0): {bad}")
    e = [r for r in R if r["w1"] >= 10 and r["pre"] < 0.1 * r["w1"]]
    print(f"\neligible (w1 >= 10, clean launch): {len(e)} = {len(e) / n:.1%}")
    if e:
        ratio = [r["d365"] / r["w1"] for r in e]
        print(f"year-1 / week-1 ratio: p10 {q(ratio, .1):.2f}  median {q(ratio, .5):.2f}  p90 {q(ratio, .9):.2f}")
        inside = sum(2 <= x <= 5 for x in ratio) / len(ratio)
        print(f"inside the '2x-5x' rule of thumb: {inside:.1%}")


if __name__ == "__main__":
    {"enumerate": lambda: enumerate_launches(int(sys.argv[2]) if len(sys.argv) > 2 else 0),
     "sample": sample, "report": report}[sys.argv[1]]()
