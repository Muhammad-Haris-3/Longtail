# Longtail — findings

Numbered, dated, append-only. Each entry records something decided or learned,
including numbers this project chose not to use, and why.

---

### F1 — Steam's default review order cannot be paged (30 Sep 2026)

With `filter=all`, every cursor returned page one again: 200 reviews fetched for
a game with 228 in week one, only 100 of them distinct. `filter=recent`, with
the same date window, returned **228 of 228, all distinct, all inside the
window**. Week-one reviews are fetched with `filter=recent`. Counts still use
`filter=all`, which is what M0's consistency check validated.

### F2 — A field that looks point-in-time and is not (30 Sep 2026)

Each review carries its author's `num_reviews`. It is collected, because it
comes back in the same response, and it is **not used**: it is the author's
count *today*, not on day seven, so §4 does not admit it.

### F3 — An admitted feature not built (30 Sep 2026)

§4 admits the developer's earlier launches. The v1.0 methods do not use them,
because building them needs a developer lookup per game that is not yet
collected. This was decided **before the test set was opened**, and it is
recorded here so that adding it later is visibly an amendment, not a quiet
improvement.

### F4 — The plumbing works on data with a known answer (30 Sep 2026)

`python backtest/model.py selfcheck` builds 3,000 synthetic launches whose
year one depends only on how late in week one the reviews arrive, a signal the
baselines cannot see. Validation MALE: B1 0.345, B2 0.304, B3 0.304, **M
0.136**. The gap shows the pipeline can find a signal where one exists. It says
nothing about whether one exists in Steam.

### F5 — Collection complete; the split sizes (1 October 2026)

All **28,905** launches have a week-one count, and **9,110 of 9,111** with at
least 10 week-one reviews were collected in full (the exception is
PREREGISTRATION §9 A1). The local machine drew heavy 429s on paged review
calls. Eight GitHub Actions runners, each with its own IP, finished the rest in
about five hours, plus a catch-up pass.

After the clean-launch rule, without reading any outcome:

| Set | Launches |
|---|---|
| Train | 3,162 |
| Validation | 1,195 |
| **Test** | **3,807** |
| Removed as unclean (Early Access residue) | 619 |

The test set clears the §5.4 power floor of 1,500 by 2.5×.

**Eligible is a larger share than M0 suggested:** 31.5% of launches have at
least 10 week-one reviews, against 30.5% in the 600-launch sample.

### F6 — The primary test: the model clears the bar (1 October 2026)

Test set opened once, at commit `8496767`, recorded in
[`results/test.json`](results/test.json). **3,889** launches released
January–September 2025, every one with a finished first year.

| Method | Mean absolute log error | 95% CI | Typical miss |
|---|---|---|---|
| B1 — industry rule, 3.16× week one | 0.464 | [0.452, 0.477] | 1.59× |
| B2 — calibrated ratio, 2.65× | 0.442 | [0.429, 0.455] | 1.56× |
| B3 — log-linear | 0.440 | [0.428, 0.453] | 1.55× |
| **M — model** | **0.379** | [0.369, 0.392] | **1.46×** |

**M against B3: 13.8% lower error, difference CI [−0.069, −0.052].** The
pre-registered bar was 10% with an interval excluding zero (§5.3). **Verdict:
SUCCESS.** Against the industry rule the reduction is 18.2%.

M is better in every week-one size band (§5.5), by the most among the largest
launches (200+ reviews: 0.362 against B1's 0.440).

**What the success does not mean.** A typical forecast is still wrong by about
46% in one direction or the other. The model narrows the error; it does not
make year one predictable. The rule of thumb's centre is close to right: the
calibrated ratio is **2.65×**, inside "2–5×", and 58.6% of test launches fall
inside that band.

**Prediction intervals are too narrow.** The 80% intervals contained 74.5% of
outcomes. They are stated as such, and they must be widened before any live
forecast carries one.

**Correction to F5.** Its split sizes were counted before the catch-up pass
was merged. The final sizes are train **3,302**, validation **1,235**, test
**3,889**, and **684** removed as unclean.

### F7 — What the model leans on (exploratory, not pre-registered) (1 October 2026)

`analysis/importance.py` permutes each feature on the **validation** set, not
the test. Beyond week-one size itself, two signals carry nearly all of the
gain, and both have a plain reading:

- **Language spread.** Launches whose week-one reviews come in **3 or fewer
  languages** reach a median of **2.0×** week one by year end. Those with **more
  than 6** reach **3.6×**.
- **Momentum.** Launches where **30% or less** of week one's reviews arrive on
  days 4–7 (a launch-day spike that fades) reach **2.1×**. Those where **more
  than 45%** arrive late in the week reach **3.6×**.

Recommendation share adds little, and its relationship to year one is not
monotonic. Both leading signals are correlated with launch size, so they are
descriptions of what the model uses, not causes a studio can pull.

### F8 — The live record has started (1 October 2026)

The first live run (GitHub Actions, commit `a6fda89`) recorded **521**
launches released 21–24 September 2026, whose week one had just ended.
**162** were eligible and were forecast by all four methods, with the exact
model the test scored (`live/fit.py` asserts it reproduces the test error to
twelve decimal places). From now on the workflow runs every Monday at 06:00
UTC.

- `register/forecasts.tsv` and `register/grades.tsv` are append-only. The
  workflow refuses to commit if any existing line changed.
- Each row records the week-one count **as observed** on the day it was
  forecast. The backtest could only use today's counts.
- **Day-30 grades start in late October, day-90 grades in late December, and
  day-365 grades in September 2027.** No live accuracy figure is published
  before 300 day-90 grades exist (§6).

**Already visible, and not a result:** on the largest launches the model
departs sharply from the rule of thumb. For one launch with 5,654 week-one
reviews it forecasts about 91,600 by year end, where the rule says about
17,900. Large launches were where the model gained most in the backtest, and
they are also the thinnest part of its training data. The live grades will
show which reading is right.

