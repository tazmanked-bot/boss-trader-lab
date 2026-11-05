# Owner-approved split workflow — 2026-11-05

**Owner decision:** Codex Cloud is inspection/review-only until its managed proxy and package-index access work normally. GitHub Actions may execute the standalone, synthetic-only indicator research test.

## Boundaries

- Codex: read GitHub repository, issue #1 and draft PR #4; review results; no proxy bypass, package installation, branch push, or merge.
- GitHub Actions: temporary hosted runner, dependency install for this experiment, numerical research tests and version logs. No secrets, live data, schedule, alerts, or orders.
- Owner: triggers the test, reviews results, authorizes all next steps.
- BOSS AI: organizes evidence and reviews problems; do not infer that a green result validates trading effectiveness.
- ZUMERAVO is completely separate and its existing HOLD status is unchanged.

## How to run from iPhone

1. Visit **Actions** on the `boss-trader-lab` repository.
2. Select **BOSS Trader owner-run indicator parity (PR 4)**.
3. Tap **Run workflow**, keeping **main** selected (the launcher explicitly checks out `research/issue-1-indicator-parity`).
4. Open its run and inspect the **isolated-synthetic-review** job.
5. Review **Show checked out commit**, **Run existing offline safety checks**, **Install pinned direct dependency**, **Record package versions**, and **Run synthetic indicator comparison only**.

A green check only establishes that the scripted offline checks completed with their current assertions. RSI/MACD/ATR independent formula parity, warmup rules, dependency security/locking, and owner review remain unresolved.

**No PR merging.** If installation fails, report PyPI error and stop; do not add proxy bypasses. If numerical parity fails, inspect failing logs, keep PR #4 in draft, and correct via another reviewable branch change. The original working Kraken workflow on `main` stays unchanged.
