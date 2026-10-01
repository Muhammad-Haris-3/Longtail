# Longtail

**Every Steam launch is sized with a rule of thumb — "year one is two to five
times week one." Nobody publishes how wrong it is.**

Longtail forecasts a game's first-year demand from its first seven days on
Steam, scores that forecast against the rules the industry actually uses, and
publishes each live forecast **before the outcome exists**.

> **Status: primary test complete — the model clears the pre-registered bar.**
> On 3,889 games released in 2025, a model reading week one cut the typical
> forecast error from **59%** (the industry rule) and **55%** (the best simple
> formula) to **46%**, which is 13.8% below the formula against a bar of 10%. The
> rule's centre is about right: year one averages **2.65×** week one.
> [Decision memo](DECISION_MEMO.md) (two pages, no statistics) ·
> [Findings](FINDINGS.md) F6–F7 · [Result file](results/test.json).
> Live forecasting has not started.

---

## The question

A studio, publisher or investor looking at a game's launch week wants to know
one thing: how big does this get? The answers in circulation are rules of
thumb — year-one sales at 2–5× week one, sales at 20–60× the review count —
repeated in calculators and blog posts, and not scored in public against the
games that actually launched.

> **From a game's first seven days of public signals, how well can its
> first-year demand be forecast — and does anything beat the rule of thumb?**

The null is pre-committed as a publishable finding: that nothing beats the
rule, or that week one simply does not contain the answer.

## Why it can be checked rather than argued

Steam keeps the date of every review. The count of reviews for any game in any
past window is one public request away, so the rule of thumb can be scored on
thousands of launches whose year one has already finished — without waiting,
and without trusting anyone's reconstruction.

Past launches settle the backtest. Live launches settle whether it holds when
nobody can see the answer yet.

## What demand means here

**Reviews, not sales.** Steam publishes no sales figures. Review counts are the
proxy the industry itself uses, and the rules being scored are stated in
reviews. The gap between reviews and sales is measured against the developers
who have published their own numbers, and stated wherever a figure appears.

## Cost

Zero. Keyless public Steam endpoints, Python standard library for collection,
GitHub Actions for the weekly run, Vercel Hobby for the site.

## Layout

| Path | |
|---|---|
| `probe/m0.py` | M0 feasibility: enumerate launches, sample windowed review counts, report |
| `backtest/collect.py`, `run.cmd` | Backtest collection (resumable) |
| `backtest/model.py` | The four methods and the one-time test; `selfcheck` runs on synthetic data |
| `analysis/importance.py` | Exploratory: which week-one signals the model uses |
| `results/test.json` | The one-time test, with the commit it ran at |
| `FINDINGS.md` | Decisions and measurements, append-only |
| `data/` | Probe outputs: `launches.tsv` (29,896 launches), `m0_sample.tsv` (600, excluded from all tests) |
