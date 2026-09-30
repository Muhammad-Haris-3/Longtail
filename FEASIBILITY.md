# Longtail — M0 feasibility

**Measured 30 September 2026, before the pre-registration was drafted.**
Everything here was seen by the author before the rules were written. The 600
sampled launches are therefore **excluded from every test set** under
[`PREREGISTRATION.md`](PREREGISTRATION.md), and no figure below is a result.

Reproduce: `python probe/m0.py enumerate 25000`, then `sample`, then `report`.

---

## 1. The launch list exists, and goes back years

Steam's store search, sorted by release date and filtered to games, pages back
through the whole catalogue with no key: **122,670 games** on the day of
measurement, 100 per request, each with its store release date.

Enumerated from mid-2025 back to December 2023: **29,896 rows**. Launch volume
runs at **1,060–1,680 games a month**, about 18,000 a year. The sampling pool
(release dates 1 Jan 2024 – 30 Jun 2025) holds **24,915 launches**.

## 2. Historical windows are one request each

`/appreviews/{app}` accepts `start_date`, `end_date` and
`date_range_type=include`, and returns the number of reviews **created in that
window**. So a game's week-one and year-one counts can be rebuilt for any past
launch without paging through its reviews.

**The windows are internally consistent.** For all 600 sampled games, reviews
before launch plus reviews in year one never exceeded the all-time total. The
check was written to fail and did not.

## 3. Most launches are too small to forecast

From 600 launches drawn at random from the pool (seed `20260930`):

| Week-one reviews | Share of launches |
|---|---|
| none in the whole first year | 9.3% |
| ≥ 1 | 77.8% |
| ≥ 5 | 43.5% |
| **≥ 10** | **30.5%** |
| ≥ 20 | 20.3% |
| ≥ 50 | 10.2% |

A ratio forecast from two or three reviews is noise, so there has to be a
floor. At **≥ 10 week-one reviews with a clean launch** (§4), **28.0%** are
eligible. Applied to the 21 months from January 2024 to September 2025 (~29,600
launches), that is roughly **8,300 games** with
a finished first year, which is enough to split by time and still test on
several thousand.

**The finding is about the market that is visible, not all of Steam.** Seven
launches in ten never get enough early reviews to be forecast, and every figure
has to say so.

## 4. Early Access breaks "week one"

The store's release date is the **full** release. Games that sold in Early
Access first arrive at it with a review history already in place. *Hades* had
**24,092 reviews before its store release date** and 5,001 in the week after
it. Treating that week as a launch is meaningless.

In the sample, **7.2%** of launches have any review before the release date,
and in **7.0%** those earlier reviews outnumber week one. The rule adopted: a
launch is **clean** only if reviews before the release date are under 10% of
week one. That removes nearly all of that 7%.

## 5. The rule of thumb is roughly right on average and wide at the edges

**Seen before pre-registration, and not a result.** On the 168 eligible sampled
launches, year one divided by week one:

| p10 | median | p90 |
|---|---|---|
| 1.60 | **2.70** | 5.78 |

**64.3%** land inside the "2–5×" band. The central tendency matches the
folklore. The spread is the opportunity: the 10th and 90th percentiles are
3.6× apart, and a studio budgeting on "about 3×" is 2× wrong about one time in
five.

## 6. Only review-derived features are point-in-time

The backtest can only use what was knowable on day seven.

- **Usable:** each week-one review's creation time, language and
  `playtime_at_review` (recorded when the review was written). Fetching them
  with the same date filter works: 12 eligible games, **457 reviews, every one
  inside the window**. Median playtime at review is **141 minutes**.
- **Not usable in the backtest:** price, tags, discounts, follower counts. The
  API returns today's values, not the values on day seven.
- **Contaminated:** thumbs-up or thumbs-down. **8.1%** of week-one reviews
  (37 of 457) were edited after day seven, and an edit can flip the
  recommendation. Recommendation share is computed only from reviews **not**
  edited after the cutoff, and that restriction is stated.
- **Undetectable:** reviews deleted since launch. Today's week-one count can
  only be at or below what was visible on day seven. The live register records
  the day-seven count as it stood, so the size of this gap gets measured rather
  than assumed.

## 7. The rate limit, measured

Six requests in flight drew **HTTP 429 after about 300 calls**. Date-filtered
calls take about **4 seconds** server-side. Two workers with a 0.5 s pause ran
the rest of the 600-game sample (about 3,300 calls) with **29 retries**, and
none of them failed.

**Backtest cost:** one call per launch to test eligibility (~29,600), then
about three more per eligible launch (~8,300). Roughly **55,000 calls, about 35
hours** at the measured rate. That is free, but it can't finish in one GitHub
Actions job (6 h ceiling). It runs on a local machine, resumably, or sharded
across runners.

**Live cost:** about 350 launches a week, which is a few hundred calls. No
constraint.

## 8. What would stop the project, and didn't

| Risk | Outcome |
|---|---|
| No historical launch list | 122,670 games, paged by release date |
| Windowed counts unavailable or inconsistent | One call per window; consistency check passed on 600/600 |
| Too few forecastable launches | ~28% eligible, ~8,300 with a finished year one |
| Early Access contamination | 7%, removable with a stated rule |
| Features leak the future | Only review-derived features are admitted; edit and deletion leaks named |
| Cost | Zero; the constraint is time, ~35 h of collection |
