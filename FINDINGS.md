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

