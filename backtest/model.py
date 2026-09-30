"""The four methods of PREREGISTRATION.md v1.0 §5.2, and the test of §5.3.

  python backtest/model.py validate    # train -> validation only; tunes M (at most 20 configurations)
  python backtest/model.py test        # opens the test set ONCE; refuses if already opened or the tree is dirty
  python backtest/model.py selfcheck   # synthetic data, no network; checks the plumbing, not the science

This file must be committed before `test` is ever run (§5.1, §7).
"""
import datetime as dt, itertools, json, os, subprocess, sys, tempfile
import numpy as np
from sklearn.ensemble import HistGradientBoostingRegressor

DAY = 86400
ROOT = os.path.join(os.path.dirname(__file__), "..")
SPLITS = {"train": ("2024-01-01", "2024-09-30"), "validation": ("2024-10-01", "2024-12-31"),
          "test": ("2025-01-01", "2025-09-29")}
B1_RATIO = 10 ** 0.5  # geometric midpoint of "2-5x" = 3.16
GRID = [dict(learning_rate=lr, max_leaf_nodes=leaves, min_samples_leaf=msl)
        for lr, leaves, msl in itertools.product((0.03, 0.1), (7, 15, 31), (20, 50))]  # 12 <= 20
assert len(GRID) <= 20
FEATURES = ["ln_w1", "ln1p_pre", "day0", "day1", "day2", "day3_6", "n_lang", "sh_english", "sh_schinese",
            "med_ln_playtime", "sh_play_lt2h", "sh_play_gt10h", "pos_share", "n_rec_known"]


def t0(d):
    return int(dt.datetime.combine(dt.date.fromisoformat(d), dt.time(), dt.timezone.utc).timestamp())


def features(w1, pre, release, reviews):
    """§4 only: what existed before t0+7d and cannot change afterwards."""
    s = t0(release)
    rv = [r for r in reviews if s <= r["created"] < s + 7 * DAY]
    n = max(len(rv), 1)
    day = [(r["created"] - s) // DAY for r in rv]
    lang = [r["language"] for r in rv]
    play = np.log1p([r["playtime_at_review"] or 0 for r in rv]) if rv else np.zeros(1)
    # Recommendation only from reviews not edited after the cutoff: an edit can flip it (FEASIBILITY §6).
    known = [r["voted_up"] for r in rv if r["updated"] < s + 7 * DAY]
    return [np.log(w1), np.log1p(pre),
            day.count(0) / n, day.count(1) / n, day.count(2) / n, sum(d >= 3 for d in day) / n,
            len(set(lang)), lang.count("english") / n, lang.count("schinese") / n,
            float(np.median(play)), float(np.mean(play < np.log1p(120))), float(np.mean(play > np.log1p(600))),
            (sum(known) / len(known)) if known else 0.5, len(known)]


def load(data_dir):
    rows = [l.rstrip("\n").split("\t") for l in open(f"{data_dir}/eligible.tsv", encoding="utf-8")][1:]
    out = {k: [] for k in SPLITS}
    for appid, release, w1, pre, y, *_ in rows:
        w1, pre, y = int(w1), int(pre), int(y)
        if w1 < 10 or pre >= 0.1 * w1:  # §2: eligible and clean
            continue
        split = next((k for k, (a, b) in SPLITS.items() if a <= release <= b), None)
        if split is None:
            continue
        with open(f"{data_dir}/reviews/{appid}.jsonl", encoding="utf-8") as f:
            rv = [json.loads(l) for l in f]
        out[split].append((appid, w1, max(y, w1), features(w1, pre, release, rv)))
    return {k: (np.array([r[1] for r in v], float), np.array([r[2] for r in v], float),
                np.array([r[3] for r in v], float), [r[0] for r in v]) for k, v in out.items()}


def male(yhat, y):
    return float(np.mean(np.abs(np.log(yhat) - np.log(y))))


def fit_methods(train, validation):
    w, y, X, _ = train
    r = float(np.median(y / w))  # B2
    b, a = np.polyfit(np.log(w), np.log(y), 1)  # B3: ln y = a + b ln w1
    wv, yv, Xv, _ = validation
    tried = []
    for cfg in GRID:
        m = HistGradientBoostingRegressor(max_iter=500, random_state=0, **cfg).fit(X, np.log(y))
        tried.append((male(np.exp(m.predict(Xv)), yv), cfg, m))
    score, cfg, m = min(tried, key=lambda t: t[0])
    lo, hi = (HistGradientBoostingRegressor(loss="quantile", quantile=q, max_iter=500, random_state=0, **cfg)
              .fit(X, np.log(y)) for q in (0.1, 0.9))
    methods = {"B1": lambda w, X: B1_RATIO * w, "B2": lambda w, X: r * w,
               "B3": lambda w, X: np.exp(a + b * np.log(w)), "M": lambda w, X: np.exp(m.predict(X))}
    return methods, dict(b2_ratio=r, b3=(a, b), m_config=cfg, m_validation_male=score), (lo, hi)


def evaluate(methods, pi, split, seed=20260930):
    w, y, X, _ = split
    pred = {k: f(w, X) for k, f in methods.items()}
    err = {k: np.abs(np.log(p) - np.log(y)) for k, p in pred.items()}
    res = {"n": int(len(y)), "male": {k: float(e.mean()) for k, e in err.items()}}
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(y), (2000, len(y)))  # §5.3: paired bootstrap over launches
    diff = err["M"][idx].mean(1) - err["B3"][idx].mean(1)
    rel = 1 - res["male"]["M"] / res["male"]["B3"]
    ci = [float(np.percentile(diff, 2.5)), float(np.percentile(diff, 97.5))]
    res["m_vs_b3"] = {"relative_reduction": rel, "diff_ci95": ci}
    res["male_ci95"] = {k: [float(np.percentile(e[idx].mean(1), q)) for q in (2.5, 97.5)] for k, e in err.items()}
    res["underpowered"] = len(y) < 1500  # §5.4
    res["verdict"] = ("UNDERPOWERED" if res["underpowered"]
                      else "SUCCESS" if rel >= 0.10 and ci[1] < 0 else "NULL")
    ratio = y / w  # §5.5
    res["share_in_2_5x_band"] = float(np.mean((ratio >= 2) & (ratio <= 5)))
    bands = [(10, 19), (20, 49), (50, 199), (200, 10 ** 12)]
    res["male_by_w1_band"] = {f"{a}-{b if b < 10 ** 12 else ''}": {k: float(e[(w >= a) & (w <= b)].mean())
                                                                  for k, e in err.items()}
                              for a, b in bands if ((w >= a) & (w <= b)).any()}
    lo, hi = (np.exp(q.predict(X)) for q in pi)
    res["m_pi80_coverage"] = float(np.mean((y >= lo) & (y <= hi)))
    return res


def main(mode, data_dir=os.path.join(ROOT, "data", "backtest")):
    d = load(data_dir)
    print({k: len(v[1]) for k, v in d.items()})
    methods, params, pi = fit_methods(d["train"], d["validation"])
    print("fitted:", params)
    if mode == "validate":
        print(json.dumps(evaluate(methods, pi, d["validation"]), indent=2))
        return
    out = os.path.join(ROOT, "results", "test.json")
    if os.path.exists(out):
        sys.exit("refusing: the test set has already been opened (results/test.json exists)")
    if subprocess.run(["git", "status", "--porcelain", "--", "backtest", "PREREGISTRATION.md"],
                      cwd=ROOT, capture_output=True, text=True).stdout.strip():
        sys.exit("refusing: methods are not committed")
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    res = evaluate(methods, pi, d["test"])
    res.update(params=params, commit=head, opened_at=dt.datetime.now(dt.timezone.utc).isoformat())
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        json.dump(res, f, indent=2, default=str)
    print(json.dumps(res, indent=2, default=str))


def selfcheck():
    """Synthetic launches with a known signal in the day curve; M should find it, B1 must be exact."""
    rng = np.random.default_rng(0)
    with tempfile.TemporaryDirectory() as tmp:
        os.makedirs(f"{tmp}/reviews")
        rows = ["appid\trelease\tw1\tpre\ty365\tn_fetched\tcollected_at"]
        for i in range(3000):
            release = (dt.date(2024, 1, 1) + dt.timedelta(days=int(rng.integers(0, 365)))).isoformat()
            w1 = int(rng.integers(10, 300))
            late = rng.uniform(0.05, 0.6)  # share of week one arriving on days 3-6: the hidden driver
            y = int(w1 * np.exp(0.3 + 2.0 * late + rng.normal(0, 0.15)))
            s = t0(release)
            rv = [{"id": str(k), "created": s + int(rng.uniform(3, 7) if rng.random() < late else rng.uniform(0, 3)) * DAY,
                   "updated": s, "language": "english", "voted_up": True, "playtime_at_review": 100}
                  for k in range(w1)]
            with open(f"{tmp}/reviews/{i}.jsonl", "w") as f:
                f.writelines(json.dumps(r) + "\n" for r in rv)
            rows.append(f"{i}\t{release}\t{w1}\t0\t{y}\t{w1}\t0")
        rows.append("x\t2024-05-01\t10\t5\t99\t0\t0")  # unclean: must be dropped before its reviews are read
        open(f"{tmp}/eligible.tsv", "w").write("\n".join(rows) + "\n")
        d = load(tmp)
        assert sum(len(v[1]) for v in d.values()) == 3000, "clean filter or split is wrong"
        methods, _, pi = fit_methods(d["train"], d["validation"])
        w = np.array([10.0, 100.0])
        assert np.allclose(methods["B1"](w, None), [31.6228, 316.228], rtol=1e-4)
        r = evaluate(methods, pi, d["validation"])
        assert r["male"]["M"] < r["male"]["B3"], r["male"]  # the signal is only in the day curve
        print("selfcheck ok:", {k: round(v, 3) for k, v in r["male"].items()})


if __name__ == "__main__":
    selfcheck() if sys.argv[1] == "selfcheck" else main(sys.argv[1])
