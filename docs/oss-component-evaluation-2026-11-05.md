# Open-source component evaluation — 2026-11-05

**Scope:** research and evaluation design only. No third-party code has been copied into the working scanner, no live-trading functionality added, no scheduled jobs enabled. BOSS Trader Lab remains independent of ZUMERAVO.

## Decision snapshot

| Candidate | Verified license | Use for BOSS Trader | Decision |
|---|---|---|---|
| [Pandas TA Classic](https://github.com/xgboosted/pandas-ta-classic) | MIT | RSI, MACD, EMA, ATR and other indicators; library needs pandas + NumPy | **Isolated parity test first** |
| [CCXT](https://github.com/ccxt/ccxt) | MIT | Normalize public Kraken OHLCV data; provides private trading APIs, which must not be invoked | **Isolated adapter comparison first** |
| [Crypto Signal Scanner](https://github.com/Acekiller88/crypto-signal-scanner) | MIT stated in repository README and license file | Study stdlib indicator, rejection, dedupe, outcome and Actions patterns | **Architecture reference; do not copy entire system** |

## Evidence reviewed

- Pandas TA Classic upstream installation: https://xgboosted.github.io/pandas-ta-classic/installation.html ; release 0.9.0 on PyPI Oct 28, 2026: https://pypi.org/project/pandas-ta-classic/ . This is a breaking release relative to 0.8.x (API and invalid-input behavior). Upstream MIT license: https://github.com/xgboosted/pandas-ta-classic/blob/main/LICENSE .
- CCXT upstream source: https://github.com/ccxt/ccxt ; MIT: https://github.com/ccxt/ccxt/blob/master/LICENSE.txt ; documents multiple exchanges and public/private interfaces. Do not configure secrets or call authenticated methods.
- Crypto Signal Scanner: https://github.com/Acekiller88/crypto-signal-scanner ; README describes top-100 **Binance USDT perpetual futures**, LONG/SHORT, 4H/1H/15m SMC strategy, GitHub scheduled pipeline, and 191 offline tests. These are project claims, **not independently reproduced test results**. It has a small public commit history at this review and its Binance endpoints may be subject to HTTP 451 on our GitHub runner.

## Compatibility gates

1. **Never confuse USD spot and USDT spot**, and never substitute perpetual futures for spot. Current live working source is **Kraken spot USD**, not Binance.
2. **Preserve read-only sandbox:** prohibit credentials, account access, create_order, order submission, write-enabled GitHub Actions, and public user holdings.
3. **Reproducibility:** pin exact dependency versions and capture hashes before promotion. For Pandas TA Classic 0.9.0, validate supported Python/pandas/NumPy combinations. Keep standard-library-only observer as comparison baseline.
4. **Indicator parity:** on deterministic OHLCV fixtures, check SMA(5/20), EMA, RSI(14), MACD(12,26,9), ATR(14). Define warm-up, closed-candle handling, missing data and tolerance. Flag discrepancies; never silently change historical gates.
5. **Data adapter parity:** for CCXT vs current Kraken adapter, compare exact Kraken USD symbol mapping, timestamps (ms vs s), number of committed candles, rate-limit compliance, and no-open-candle policy; don't compare separate live snapshots as if synchronized.
6. **Architecture-only scanner review:** assess hard rejection, missing/stale data, dedupe and outcome-tracking patterns; compare with BOSS Trader's bottom-reversal / pullback-recovery / sneaky-pivot research priorities.
7. **Operational limits:** manually triggered Actions only; no auto alerts, no autonomous trades, no new expenses, no strategy profitability claim.
8. **Attribution:** preserve upstream copyright and license notice if source code is copied; prefer package imports or original reimplementation after proper review.
9. **Security:** audit dependencies, CI permissions, third-party Actions pinning and data provenance before deployment. Avoid copying the upstream workflow wholesale.

## Proposed sequence

- Stage A: build an **offline, manually triggered, isolated** Pandas TA indicator comparison and record result. Baseline workflows untouched.
- Stage B: optionally test CCXT Kraken-only public fetch after version/license/dependency review; avoid exchange-private APIs and require read-only code review.
- Stage C: document patterns from Crypto Signal Scanner, never import Binance futures or clone its signal assumptions.
- Stage D: owner reviews comparative results. Do not promote to main scanner until explicit approval.
- Stage E: only after finding accurate indicators and good data, design a research-only 0–3 candidate ranking with WATCH/WAIT/BLOCKED and separate ENTRY READY proposal.

## Current empirical evidence

- Our existing GitHub Actions offline safety checks succeeded (owner-supplied screenshot).
- Our Binance public USDT candles returned HTTP 451 for BTC/XRP/SOL (owner-supplied run logs).
- Our Kraken spot USD manual live observation succeeded (owner-supplied screenshot).
- No third-party dependency performance, data-adapter parity, or scanner strategy effectiveness has been validated yet.
