# Security and safety policy

BOSS Trader Lab is **public, experimental, read-only research software**.

- Never commit SSH keys, API keys, account credentials, personal details, balances, portfolio exports, private audit logs, or secrets.
- Never accept or request exchange trading permissions.
- The current program only accesses Binance's public historical candle endpoint when `--live` is explicitly used; the default uses synthetic data.
- There are **no order placement endpoints, exchange authentication, signals, alerts, or scheduled workflows** in this initial version.
- All observations are `OBSERVE_ONLY` and are **not** validated strategies or recommendations.
- Public API data may be blocked, incomplete, delayed, or inaccurate; fail closed if unavailable.
- Report possible vulnerabilities via GitHub private vulnerability reporting if enabled, or contact the repository owner privately. Do not post secrets in public issues.
- Keep ZUMERAVO source code, private governance, evidence, and credentials completely separate.
