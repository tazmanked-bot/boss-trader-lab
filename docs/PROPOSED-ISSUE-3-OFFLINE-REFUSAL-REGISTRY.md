# PROPOSED ONLY — offline spot refusal registry

This is a separate future assignment proposal from BOSS-TRADER-ISSUE-3-ARCHITECTURE-AUDIT.
**NOT AUTHORIZED FOR EXECUTION.** Do not implement it without an explicit owner
decision. Patterns 2 (dedupe state) and 3 (ledger) are excluded.

## Suggested mission

Create an original, optional stdlib-only research module that classifies
deterministic Kraken spot USD fixture refusals before any ranking. Do not copy
upstream implementation. Recognize the architecture inspiration and exact
upstream commit 431c79bb45fb31ca9609c48ccc0f17376731b9da in documentation; any later
code copying would require MIT notice preservation and a separate review.

## Boundaries

- New dedicated research branch and draft PR only; no main or production changes.
- Do not modify Kraken adapter/workflow, boss_trader_lab.py, Issue #1 or #2 work,
  existing tests, ZUMERAVO, dependencies, network configuration or workflows.
- No network calls, installed packages, API credentials, orders, futures, shorts,
  leverage, funding, derivatives sizing, schedules, alerts or automatic approvals.
- No strategy, reversal formula, numerical indicator changes or live/backtest run.
- No ENTRY READY state or notification transport. Return evidence/refusal results
  only; any future WATCH display is a separate owner decision.

## Acceptance tests

1. Original stable reason-code registry with separate human detail, evidence
   reference, symbol/venue/market/quote/timeframe, as-of time and policy version.
   Unknown reason or policy fields fail closed. Do not parse dynamic error text.
2. Malformed, missing, wrong-market, nonfinite, unclosed, future, stale, duplicate,
   unordered, gapped and wrong-unit fixtures each produce the documented refusal.
3. Per-symbol staleness is assessed before any candidate selection. A fresh BTC
   fixture cannot mask stale XRP or SOL data. Invalid data never becomes synthetic
   live-price fallback or a partial PASS.
4. Contradictory input refuses independent of any supplied score. No score is
   treated as a probability, no forced candidate minimum, and no automatic WATCH
   to ENTRY READY conversion. Do not implement strategy ranking.
5. Explicit 21-close observation-window fixtures distinguish insufficient
   history from valid data without borrowing upstream indicator defaults.
6. Fixed-as-of output remains identical after adversarial future data is appended;
   no current-price, timestamp, reason-detail or evidence field leaks future data.
7. Dependency-free unittest coverage, no network at import or execution, strict
   JSON serialization, no raw exception bodies, and deterministic bounded output.
8. Publish exact branch/commit/draft refs and test results; preserve all existing
   tests; stop for owner/BOSS AI review without merging or closing any issue.

## Excluded follow-ups

Do not implement persistent cooldown/dedupe storage, an outcome ledger, spot
strategy thresholds, simulation performance, alerts or live-data collection.
Those require their own requirements and approvals. Zero candidates is valid.
