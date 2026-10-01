"""Live forecasting under PREREGISTRATION.md §6. Run weekly (Monday, UTC) by .github/workflows/live.yml.

  python live/run.py forecast   # every launch whose week one has ended and is not yet in the register
  python live/run.py grade      # count reviews at day 30 / 90 / 365 for every forecast that has reached it

register/forecasts.tsv and register/grades.tsv are append-only: rows are never edited or deleted (§6).
No summary figure is computed here; none is published before 300 day-90 grades exist.
"""
import datetime as dt, math, os, pickle, re, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "backtest"))
sys.path.insert(0, os.path.join(HERE, "..", "probe"))
from m0 import DAY, SEARCH, count, get, parse_date  # noqa: E402
from collect import fetch_week_one, t0  # noqa: E402
from model import features  # noqa: E402

ROOT = os.path.join(HERE, "..")
FORECASTS, GRADES = f"{ROOT}/register/forecasts.tsv", f"{ROOT}/register/grades.tsv"
F_HEADER = ("appid\trelease\tname\tobserved_at\tw1_observed\tpre\teligible\tn_fetched"
            "\tb1\tb2\tb3\tm\tmodel_test_commit\tcode_commit")
G_HEADER = "appid\trelease\thorizon_days\treviews\tgraded_at"
LOOKBACK = 35  # days: a missed Monday is caught up the following week; features still stop at day seven
# §6: the live record starts with launches whose week one ended in the week before the first Monday after the
# freeze (2026-09-30). That Monday is 2026-10-05; its week is 09-28..10-04; so releases from 2026-09-21.
START = dt.date(2026, 9, 21)


def now():
    return dt.datetime.now(dt.timezone.utc)


def rows(path):
    try:
        return [l.rstrip("\n").split("\t") for l in open(path, encoding="utf-8")][1:]
    except FileNotFoundError:
        return []


def append(path, header, row):
    new = not os.path.exists(path)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a", encoding="utf-8", newline="\n") as f:
        if new:
            f.write(header + "\n")
        f.write("\t".join(map(str, row)) + "\n")


def recent_launches(today):
    # Week one has ended for release date d when d + 7 <= today (UTC date); take the last LOOKBACK days of those.
    hi, lo = today - dt.timedelta(days=7), max(START, today - dt.timedelta(days=LOOKBACK))
    out, offset = {}, 0
    while True:
        h = get(SEARCH.format(s=offset))["results_html"]
        page = re.findall(r'data-ds-appid="(\d+)".*?<span class="title">([^<]*)</span>'
                          r'.*?search_released[^>]*>\s*([^<]*?)\s*<', h, re.S)
        dates = [parse_date(r[2]) for r in page]
        for (appid, name, _), d in zip(page, dates):
            if d and lo <= d <= hi:
                out.setdefault(appid, (d.isoformat(), name.replace("\t", " ")))
        known = [d for d in dates if d]
        if not page or (known and known[-1] < lo):
            return out
        offset += 100
        time.sleep(1)


def forecast():
    with open(f"{ROOT}/models/methods.pkl", "rb") as f:
        mt = pickle.load(f)
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    seen = {r[0] for r in rows(FORECASTS)}
    todo = {a: v for a, v in recent_launches(now().date()).items() if a not in seen}
    print(f"{len(todo)} new launches with a finished week one", flush=True)
    for appid, (release, name) in sorted(todo.items()):
        s = t0(release)
        w1 = count(appid, s, s + 7 * DAY - 1)
        pre = count(appid, 1, s - 1) if w1 >= 10 else ""
        eligible = w1 >= 10 and pre < 0.1 * w1  # §2
        row = [appid, release, name, now().isoformat(timespec="seconds"), w1, pre, int(eligible)]
        if eligible:
            rv = fetch_week_one(appid, s)
            x = [features(w1, pre, release, rv)]
            a, b = mt["b3"]
            row += [len(rv), round(mt["b1_ratio"] * w1, 1), round(mt["b2_ratio"] * w1, 1),
                    round(math.exp(a + b * math.log(w1)), 1),
                    round(math.exp(float(mt["M"].predict(x)[0])), 1)]
        else:
            row += ["", "", "", "", ""]
        append(FORECASTS, F_HEADER, row + [mt["test_commit"], head])
        if eligible:
            print(f"  {appid} {release} w1={w1} -> M {row[-1]:.0f} (B1 {row[8]})", flush=True)


def grade():
    graded = {(r[0], r[2]) for r in rows(GRADES)}
    today = now()
    n = 0
    for r in rows(FORECASTS):
        if r[6] != "1":
            continue
        appid, release = r[0], r[1]
        s = t0(release)
        for k in (30, 90, 365):
            # One extra day so the window is closed in every time zone before it is counted.
            if (appid, str(k)) not in graded and today.timestamp() >= s + (k + 1) * DAY:
                append(GRADES, G_HEADER, [appid, release, k, count(appid, s, s + k * DAY - 1),
                                          today.isoformat(timespec="seconds")])
                n += 1
    print(f"{n} grades appended")


if __name__ == "__main__":
    {"forecast": forecast, "grade": grade}[sys.argv[1]]()
