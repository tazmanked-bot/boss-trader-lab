# Phase 2: Manual public market-data test

This is **a separate manually triggered GitHub Actions workflow**; the original offline test remains unchanged.

## Running it on an iPhone

1. Open the repository's **Actions** tab.
2. Choose **BOSS Trader manual public-data observation**.
3. Select **Run workflow** on the **main** branch.
4. Open the new run, then **public-market-observation** to review its logs.
5. Look for three `OBSERVE_ONLY` results: `BTCUSDT`, `XRPUSDT`, and `SOLUSDT`.

**Green run** means the offline tests and all three public-data requests completed. It does not mean a trade opportunity has been found.

**Red run** means a safety test or one/more data requests failed. Regional restrictions, network issues, API throttling, and invalid responses can cause this. The code fails closed; no trading action is possible.

## Guardrails

- Public Binance Spot hourly candles only. No API keys or secrets; no trading endpoints.
- 5-bar and 20-bar SMA observations are descriptive, **not reversal qualification**.
- No scheduled workflows, exchange orders, position sizing, buy proposals, or notifications.
- No personal holdings or trading account data.
- GitHub public Actions logs are public. Never paste personal details or keys into workflow inputs or code.
- BOSS Trader Lab is independent of ZUMERAVO.
- Existing local scanner V3.8 still needs independent migration and validation when available.

**Next gate:** owner reviews the first live run and then explicitly approves or rejects any extension to broader market scanning or scheduled alerts.
