# Longtail — pre-registration v1.0 (FROZEN)

> **Frozen 30 September 2026.** Its SHA-256 is recorded in `frame/MANIFEST`,
> committed before the backtest frame was built, before any backtest data was
> collected and before any model was fitted.

**Drafted 30 September 2026, after [`FEASIBILITY.md`](FEASIBILITY.md) and
before any collection or modelling.** The M0 sample, including its year-one
outcomes, was seen when this was written. It is excluded from every test set.

Changes after freezing require a numbered amendment in §9 stating what
changed, why, and what had been seen, kept in git beside the original.

---

## 1. The question

> From a Steam game's first seven days of public reviews, how well can its
> first-year review count be forecast — and does a model beat the rules the
> industry uses?

**Pre-committed null:** no model clears §5 against the strongest baseline. That
is published as the finding, in the same place and at the same length a
positive result would have been.

## 2. Population

- **Source:** Steam store search, `category1=998` (games), store release date
  as listed on the enumeration date.
- **Clean launch:** reviews created before the release date are fewer than
  10% of week-one reviews ([`FEASIBILITY.md`](FEASIBILITY.md) §4).
- **Eligible:** clean, with **≥ 10 reviews created in week one**.
- **Excluded:** the 600 appids in `data/m0_sample.tsv`.

Every figure states that it describes eligible launches, about 28% of all
games released, and not Steam as a whole.

## 3. Definitions

- `t0` = 00:00 UTC on the store release date. Steam launches usually go live
  in the afternoon UTC, so week one is effectively about 6.3 days. That is a
  fixed offset applied identically to every launch and every method.
- **Week one** = reviews created in `[t0, t0 + 7d)`.
- **Target** `y` = reviews created in `[t0, t0 + 365d)`, all languages, all
  purchase types.
- **Error** = `|ln(ŷ) − ln(y)|`. **Primary metric:** mean absolute log error
  (MALE) over the test set. A MALE of 0.41 means a typical miss of ~1.5×, in
  either direction.

## 4. What each method may see

Only data **created before `t0 + 7d`** and **not changeable afterwards**:

| Admitted | Not admitted |
|---|---|
| Week-one review count and its day-by-day curve | Price, discounts, tags, genre (today's values, not day seven's) |
| Each review's language | Helpfulness votes (accrue later) |
| `playtime_at_review` | Follower and wishlist counts (no history) |
| Reviews before `t0` (Early Access residue) | Any review created on or after `t0 + 7d` |
| Recommendation, **only** for reviews not edited after `t0 + 7d` | Recommendation of reviews edited after the cutoff |
| The developer's earlier launches, with their outcomes as of `t0` | |

The developer's prior launches count only through reviews created before `t0`.

## 5. The test

### 5.1 Split, by time

| Set | Store release dates | Use |
|---|---|---|
| Train | 2024-01-01 – 2024-09-30 | Fitting |
| Validation | 2024-10-01 – 2024-12-31 | Tuning, at most 20 configurations |
| **Test** | **2025-01-01 – 2025-09-29** | Opened once, after the model is fixed |

Every test launch's year one ended before the freeze date, so the outcomes
already exist. The rule is that they are not looked at until §5.2 is fixed in a
commit.

### 5.2 Methods

| | Method | Fitted on |
|---|---|---|
| **B1** | Industry rule: `ŷ = 3.16 × week one` (geometric midpoint of "2–5×") | Nothing |
| **B2** | Calibrated ratio: `ŷ = r × week one`, `r` = train median ratio | Train |
| **B3** | Log-linear: `ln ŷ = a + b · ln(week one)` (Szabo & Huberman, 2010) | Train |
| **M** | Gradient-boosted regressor on §4 features, predicting `ln y` | Train, tuned on validation |

### 5.3 The bar

**M succeeds only if** its test MALE is at least **10% lower than B3's**, and
the 95% paired bootstrap interval of the difference (2,000 resamples over
launches) excludes zero.

The gate is against **B3**, the strongest baseline, and not against the
industry rule. Beating a weak baseline is the easiest way to manufacture a
result. The comparison with B1 is reported as context and is never the gate.

### 5.4 Power floor

If fewer than **1,500** eligible launches are in the test set, the test is
reported as **underpowered**, whatever it shows.

### 5.5 Always reported, whatever §5.3 says

- MALE for all four methods, with intervals.
- The share of launches inside B1's "2–5×" band.
- Errors by week-one size band (10–19, 20–49, 50–199, 200+).
- For M: 80% prediction interval coverage on the test set.

## 6. Live forecasts

From the first Monday after freezing, every eligible launch whose week one
ended in the previous Monday–Sunday is forecast by M and B1–B3, and appended to
`register/forecasts.tsv` in a **git commit before its outcome windows open**.
Each row records the week-one count **as observed on day seven**, which is the
measurement that deletions (FEASIBILITY §6) can later erode.

- Rows are never edited or deleted. A correction is a new row that references
  the old one.
- Rows are graded at day 30, 90 and 365, each grade a new row.
- **No live figure is published until 300 launches have a graded day-90
  outcome.** Day-365 live grades start a year after the freeze, and until then
  the page says so rather than extrapolating.

## 7. What would invalidate a result

- Any feature found to use information created after `t0 + 7d`. The result is
  withdrawn, and the leak and its effect are recorded in `FINDINGS.md`.
- The test set being read before §5.2 is fixed in a commit.
- A change to eligibility, split, metric or bar without an amendment.

## 8. What is not claimed

- **Sales.** Reviews are the proxy. Sales are discussed only against developers'
  own published figures, and as a separate, clearly marked analysis.
- **All of Steam.** The ~72% of launches below the week-one floor are outside
  the question, and their share is reported beside every headline.
- **Causes.** A feature that forecasts well is not a lever a studio can pull.

## 9. Amendments

### A1 — one training launch excluded (1 October 2026)

**What changed:** *Black Myth: Wukong* (appid 2358720, released 2024-08-19,
train split) is excluded from every set.

**Why:** its week one holds **502,562 reviews**, about 5,000 pages. A
collection runner spent more than an hour on it under Steam's rate limits
without finishing. Every other eligible launch, 9,110 of 9,111, was collected
in full.

**What had been seen:** its week-one count and its pre-release count. Not its
year-one outcome, and nothing from the test split. The test split is untouched
by this amendment, and one launch in 3,163 cannot move the fitted baselines
materially.
