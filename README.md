# BOSS Trader Lab

Open-source, **research-only** crypto spot market observation prototype (MIT).

> **Status: early prototype.** This is *not* the owner's existing local V3.8 scanner. That version remains on an offline Debian desktop and is not yet migrated. No profitability or reversal-detection performance has been validated.

## What is available now

- Python 3.11+ standard-library-only observer for a short allowlist of spot pairs
- 5-bar and 20-bar simple moving averages, last-bar change, `OBSERVE_ONLY` output
- Synthetic offline demonstration (default); optional public Binance 1-hour closed candles
- Dependency-free offline unit tests
- Manually triggered GitHub Actions safety test (**not scheduled**)

## Data-source responsibility (public repository)

This MIT-licensed repository contains code, **not a license to third-party exchange data**. It is publicly available for independent use; each person who runs it is responsible for checking the applicable exchange/API/data-provider terms, local law, permitted purposes, rate limits, storage, retention and redistribution rules. Do not assume the maintainer has cleared data rights for other users.

**Owner decision (2026-11-06):** Remove the additional repository-wide **data-licensing research approval gate** previously discussed for BOSS Trader Lab's private, personal, noncommercial use. Prior archive-rights reports are historical assessments, **not a mandatory permission-clearance or outreach prerequisite imposed on all users**. They do not certify any particular user's rights and do not prohibit legitimate public, read-only data observation merely because a separate historical archive's commercial or redistribution terms were unresolved.

This decision **does not** make restricted data free to use, authorize redistribution of third-party candles, bypass provider limitations or override any applicable terms. Data-source responsibility belongs to the individual user.

**Operational safety remains separate:** the existing technical refusal checks and HOLD/NO-GO gates for unapproved real-data integration, clock/transport qualification and automated trading are unchanged. No live orders, account-key collection, futures trading, unattended execution or new scheduled requests are enabled by this documentation change. Existing explicitly available manual public-data features retain their documented scope; any new runtime integration still requires independent technical review.

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
