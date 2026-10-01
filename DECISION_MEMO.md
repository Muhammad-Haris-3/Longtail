# Longtail — decision memo

**For:** anyone who sizes a game's first year from its launch week, whether a
studio, publisher, investor or platform.
**Date:** 1 October 2026.
**Bottom line:** the rule of thumb is right on average and wrong for most
individual games. A model reading three things from week one cuts the typical
error by about a fifth. Year one stays only partly predictable.

---

## The question

When a game launches, the people paying for it ask how big it gets. The usual
answer is a rule: **year one comes to two to five times week one**. Nobody had
published how wrong that rule is.

Longtail checked it against **3,889 Steam games released in 2025**, every one
with a finished first year, and against a model trained only on games released
in 2024.

Demand is measured in **Steam reviews**, because Steam publishes no sales. The
industry's own rules are stated in reviews too.

## What we found

**1. The rule's centre is about right.** The average game's first year comes to
**2.65 times** its first week. That sits inside "two to five".

**2. For individual games it is loose.** A forecast from the rule is typically
off by about **60%** in one direction or the other. 41% of games land outside
the "two to five" band altogether.

**3. Three week-one signals do better.** A model using week one's size, **how
many languages** the reviews are written in, and **whether reviews are still
arriving late in the week** cut the typical error from about 60% to about
**46%**. It did better in every size of launch, and most among the biggest.

| | Typical miss |
|---|---|
| Rule of thumb ("about 3×") | 59% |
| Best simple formula | 55% |
| **Model** | **46%** |

**4. The two signals have plain readings.** A game reviewed in more than six
languages in week one reaches about **3.6×** by year end. One reviewed in three
or fewer reaches about **2×**. A launch whose reviews keep coming through the
week behaves like the first. A launch-day spike that fades behaves like the
second.

## Why the result can be trusted

- **The test was fixed before the data existed.** The pass mark (beat the best
  simple formula by at least 10%), the data split and the error measure were
  committed to a public git history before any outcome was collected.
- **The bar was the hardest baseline, not the weakest.** Beating the rule of
  thumb alone would have been easier. The model had to beat a formula fitted to
  the data, and it did by 14%.
- **The test games were opened once.** The model was fixed and committed first,
  and the code refuses to run the test a second time.
- **Nothing from the future leaked in.** Price, tags and follower counts were
  excluded because Steam shows today's values, not launch-week ones.

## What it does not say

- **It is not sales.** Reviews track sales loosely. A studio's own
  review-to-sales ratio is still needed to turn this into revenue.
- **It covers about a third of launches.** Games with fewer than 10 reviews in
  week one, about 7 in 10 Steam releases, are too small to forecast this way.
- **It does not make year one predictable.** A typical miss of 46% is better
  than 59%, and it is still large. The model's own uncertainty ranges are also
  slightly too narrow, and that is stated wherever they appear.
- **It does not give levers.** Language spread and late-week momentum describe
  launches that grow. Translating a game will not by itself make it grow.

## Recommendation

Use **2.65× week one** as the starting point, not "two to five". Then **adjust
up** for wide language spread and reviews that keep arriving, and **down** for a
fading launch-day spike. Treat any single forecast as a range, not a number.

## What happens next

The next step is to run the same model on each week's new launches,
**publishing the forecasts before the outcomes exist**, and grading them at 30,
90 and 365 days, in public. The backtest says it should work. Only the live
record can show whether it does.
