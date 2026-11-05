# Issue #1 — indicator evaluation, isolation and owner review

**Research branch:** `research/issue-1-indicator-parity`. Nothing here changes the existing Kraken live-data source or trade permissions.

Run the **BOSS Trader isolated indicator parity research** workflow manually after reviewing and merging the PR. It installs `pandas-ta-classic==0.9.0` into a temporary GitHub-hosted runner and uses **synthetic data exclusively**.

## Evidence gates

- [x] Written self-contained deterministic synthetic OHLCV fixture (180 rows).
- [x] Independent Python SMA(20) comparison against existing `boss_trader_lab.sma`.
- [x] Independent explicit SMA-seeded EMA(20) comparison, max absolute error <= 1e-8 across final 20 bars.
- [x] RSI(14), MACD(12/26/9), ATR(14) calculation and finite-result diagnostics.
- [ ] Run workflow and capture actual versions/output as evidence.
- [ ] Independently compare RSI, all MACD columns and ATR smoothing/warmup definitions; **do not claim full indicator parity yet**.
- [ ] Pin transitive dependencies/hashes and security-audit installed packages before any promotion.
- [ ] Owner review of results and risks.
- [ ] If approved, propose a separate integration change. **No automatic merge or production activation.**

## Known limits

- This PR is a prototype parity test; no market backtest or real price fetch takes place.
- PyPI release `0.9.0` is MIT, Python >=3.11, released Oct 28, 2026. It introduces breaking changes to previous 0.8.x behavior.
- Current workflow pins the direct dependency but not all transitive package versions; results include version evidence but are not yet a cryptographically locked reproducible build.
- GitHub Actions runs no more than manually on a hosted runner. Its installation accesses the package index; **the scanner itself remains offline in this test**.
- Source: https://pypi.org/project/pandas-ta-classic/0.9.0/ ; docs: https://xgboosted.github.io/pandas-ta-classic/installation.html

## Stop condition

Any unexpected error or discrepancy -> fail or remain unapproved. No signals, exchange authentication, scheduling, or orders.
