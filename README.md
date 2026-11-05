# BOSS Trader Lab

Open-source, **research-only** crypto spot market observation prototype (MIT).

> **Status: early prototype.** This is *not* the owner's existing local V3.8 scanner. That version remains on an offline Debian desktop and is not yet migrated. No profitability or reversal-detection performance has been validated.

## What is available now

- Python 3.11+ standard-library-only observer for a short allowlist of spot pairs
- 5-bar and 20-bar simple moving averages, last-bar change, `OBSERVE_ONLY` output
- Synthetic offline demonstration (default); optional public Binance 1-hour closed candles
- Dependency-free offline unit tests
- Manually triggered GitHub Actions safety test (**not scheduled**)

## Usage

```bash
python boss_trader_lab.py
python -m unittest discover -s tests -v
python boss_trader_lab.py --live --symbol XRPUSDT
```

The live command accesses only public market data and may fail if regional API access is restricted. It does **not** authenticate, place orders, or produce buy/entry approvals.

## GitHub Actions on a phone

Open **Actions → BOSS Trader offline safety check → Run workflow**. The workflow only runs unit tests and a synthetic fixture. It is not a live scan and has no scheduled automation or notifications.

## Roadmap (owner approval required)

1. Validate the offline-only workflow and audit the repository for leaks.
2. Review an optional manually run public-data test (no credentials).
3. Specify the WATCH / ENTRY READY / owner authorization gates before proposing any alert workflow.
4. Reconcile the local V3.8 scanner once the owner's desktop is accessible.
5. Consider hourly scheduled research and mobile alerts only after safety and resource-use review.

No trading advice. No guaranteed returns. Never share keys or personal data in this public repository. **Independent of ZUMERAVO.**
