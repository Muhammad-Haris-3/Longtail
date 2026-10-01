"""Backtest collection under PREREGISTRATION.md v1.0. Resumable; rerun any stage after a stop.

  python backtest/collect.py frame     # frame/frame.tsv: every game released 2024-01-01..2025-09-29
  python backtest/collect.py counts    # data/backtest/counts.tsv: week-one count per launch
  python backtest/collect.py reviews   # data/backtest/eligible.tsv + reviews/<appid>.jsonl for w1 >= 10

Collects outcomes (y) but never scores anything: the test set is opened only after
the methods are fixed in a commit (PREREGISTRATION §5.1).
"""
import datetime as dt, json, os, re, sys, time
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import quote

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "probe"))
from m0 import DAY, REVIEWS, SEARCH, count, get, parse_date  # noqa: E402

LO, HI = dt.date(2024, 1, 1), dt.date(2025, 9, 29)
FRAME, COUNTS, ELIG, REV = "frame/frame.tsv", "data/backtest/counts.tsv", "data/backtest/eligible.tsv", "data/backtest/reviews"


def t0(d):
    return int(dt.datetime.combine(dt.date.fromisoformat(d), dt.time(), dt.timezone.utc).timestamp())


def frame(start=8000):
    offset = start
    # Sorted newest first; new releases shift pages down during the crawl, which repeats rows, never skips them.
    seen, rows = set(), []
    while True:
        h = get(SEARCH.format(s=offset))["results_html"]
        page = re.findall(r'data-ds-appid="(\d+)".*?<span class="title">([^<]*)</span>'
                          r'.*?search_released[^>]*>\s*([^<]*?)\s*<', h, re.S)
        if not page:
            raise RuntimeError(f"empty page at {offset}")
        dates = []
        for appid, name, rel in page:
            d = parse_date(rel)
            dates.append(d)
            if d and LO <= d <= HI and appid not in seen:
                seen.add(appid)
                rows.append((appid, d.isoformat(), name.replace("\t", " ")))
        known = [d for d in dates if d]
        print(offset, known[0] if known else "-", len(rows), flush=True)
        if offset == start and known and known[0] <= HI:
            raise RuntimeError("start offset is already inside the window; lower it")
        if known and known[-1] < LO:
            break
        offset += 100
        time.sleep(1)
    rows.sort()
    with open(FRAME, "w", encoding="utf-8", newline="\n") as f:
        f.write("appid\trelease\tname\n")
        f.writelines("\t".join(r) + "\n" for r in rows)
    print(f"frame: {len(rows)} launches in [{LO}, {HI}]")


def run(jobs, fn, path, header):
    # Append-only, resumable: rows already in `path` are skipped.
    try:
        done = {l.split("\t")[0] for l in open(path, encoding="utf-8")}
    except FileNotFoundError:
        done = set()
    todo = [j for j in jobs if j[0] not in done]
    print(f"{path}: {len(done) and len(done) - 1} done, {len(todo)} to go", flush=True)
    with open(path, "a", encoding="utf-8", newline="\n") as out, ThreadPoolExecutor(2) as ex:
        if not done:
            out.write(header + "\n")
        for i, row in enumerate(ex.map(fn, todo)):
            out.write("\t".join(map(str, row)) + "\n")
            out.flush()
            if i % 100 == 0:
                print(time.strftime("%H:%M"), i, *row, flush=True)


def launches():
    m0 = {l.split("\t")[0] for l in open("data/m0_sample.tsv", encoding="utf-8")}
    rows = [l.rstrip("\n").split("\t") for l in open(FRAME, encoding="utf-8")][1:]
    return [(a, d) for a, d, _ in rows if a not in m0]  # §2: M0 sample excluded


def counts():
    run(launches(), lambda j: (j[0], j[1], count(j[0], t0(j[1]), t0(j[1]) + 7 * DAY - 1)),
        COUNTS, "appid\trelease\tw1")


def fetch_week_one(appid, start):
    # Every review created in week one, with the fields PREREGISTRATION §4 admits (and timestamp_updated, to apply it).
    # filter=all repeats page one on every cursor; filter=recent pages correctly (228/228 unique on a test app).
    base = (REVIEWS.format(a=appid).replace("num_per_page=0", "num_per_page=100").replace("filter=all", "filter=recent")
            + f"&start_date={start}&end_date={start + 7 * DAY - 1}&date_range_type=include")
    out, cursor = [], "*"
    while True:
        j = get(base + "&cursor=" + quote(cursor, safe=""))
        out += [{"id": r["recommendationid"], "created": r["timestamp_created"], "updated": r["timestamp_updated"],
                 "language": r["language"], "voted_up": r["voted_up"],
                 "playtime_at_review": r["author"].get("playtime_at_review"),
                 "author_num_reviews": r["author"].get("num_reviews")} for r in j["reviews"]]
        if not j["reviews"] or j["cursor"] == cursor:
            return list({r["id"]: r for r in out}.values())
        cursor = j["cursor"]


def review_job(j, rev=REV):
    appid, d, w1 = j
    s = t0(d)
    pre = count(appid, 1, s - 1)
    y = count(appid, s, s + 365 * DAY - 1)
    rv = fetch_week_one(appid, s) if pre < 0.1 * w1 else []  # §2: only clean launches need features
    with open(f"{rev}/{appid}.jsonl", "w", encoding="utf-8", newline="\n") as f:
        f.writelines(json.dumps(r) + "\n" for r in rv)
    return appid, d, w1, pre, y, len(rv), int(time.time())


HEADER = "appid\trelease\tw1\tpre\ty365\tn_fetched\tcollected_at"


def reviews():
    os.makedirs(REV, exist_ok=True)
    rows = [l.rstrip("\n").split("\t") for l in open(COUNTS, encoding="utf-8")][1:]
    jobs = [(a, d, int(w)) for a, d, w in rows if int(w) >= 10]
    run(jobs, review_job, ELIG, HEADER)


def shard(jobs_path, i, n, outdir, limit="0"):
    """One slice of backtest/jobs.tsv, for a GitHub Actions runner (its own IP, so its own rate limit).
    Jobs with a blank w1 are counted first; launches under 10 week-one reviews get blank pre/y365/n_fetched."""
    rows = [l.rstrip("\n").split("\t") for l in open(jobs_path, encoding="utf-8")][1:][int(i)::int(n)]
    rows = rows[:int(limit)] if int(limit) else rows
    rev = f"{outdir}/reviews"
    os.makedirs(rev, exist_ok=True)

    def one(j):
        appid, d, w1 = j
        w1 = int(w1) if w1 else count(appid, t0(d), t0(d) + 7 * DAY - 1)
        return review_job((appid, d, w1), rev) if w1 >= 10 else (appid, d, w1, "", "", "", int(time.time()))

    run(rows, one, f"{outdir}/shard.tsv", HEADER)


if __name__ == "__main__":
    {"frame": frame, "counts": counts, "reviews": reviews, "shard": shard}[sys.argv[1]](*sys.argv[2:])
