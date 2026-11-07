# BOSS Trader dashboard — CODEX 029 / Issue #53

Baseline: `457531a92df4112957d3c3744c081a15f16858ed`.
Current README.md, SECURITY.md and 024 source/report were read. No AGENTS.md applies.
PR #52 is **not a dependency** and remains Draft/unmerged.

## Open the screen

From the repository root, with Python 3.11+ and no installed packages:

```sh
python -B -m research.dashboard_029 --output boss-trader-demo.html
```

Open that generated file in a normal JavaScript-enabled browser. No server, framework, account, API key, network connection or deployment is needed. A pre-generated review copy is [here](artifacts/boss-trader-demo-029.html); download it before opening locally.

The single scrollable screen contains the existing static scan, a local demo watch list, manual hypothetical paper entries/exits and a realized-paper session report. Green WATCH is monitoring only; no real entry or order authorization exists.

## Actual source, unchanged calculations

The generator calls `manual_kraken_reversal_024.offline_demo()` and uses its operator report. It does not reimplement scanner formulas, rebuild candles from observer closes or admit a new source. The unchanged sealed 022 fixture SHA-256 is `761c171e090bcfc14c8ab87ea4ce3a20b8278aa01b6445e0871438dc4fc8285b`.

Actual embedded result: three WATCH candidates ordered BTC/USD, SOL/USD, XRP/USD, original rule score 26666 each and original feature results. Each $101 USD reference is explicitly a fixture value, not a market price. Fixture as-of is 2030-03-17 18:00 UTC; the invented coordinate is distinct from file generation time, which is labeled local-system time rather than trusted UTC. Source revision refers to the unchanged scanner baseline, not a claim that this UI existed in that revision.

Session identity hashes the source revision, fixture digest and decision data, excluding generation time. Reopening/regenerating the same demo cannot silently create duplicate sessions. Numeric entry/invalidation rules remain “Not defined”; catalysts remain UNVERIFIED. Explanations are labeled “Rule-based explanation.” Rule scores are ranking values, not probability or confidence.

The screen-state selector offers explicitly labeled **presentation-only** WAIT/no-candidate and BLOCKED examples. It does not mutate scanner calculations or fixture bytes; watch addition and paper entry are paused in these views. The valid empty view says “No qualifying setup.” It is a layout exercise, not a second scanner.

## Paper walkthrough

1. Click **Load demo scan**, then **Add to demo watch** on BTC/USD. Conditions and source session are retained locally.
2. In **Record paper entry**, enter hypothetical price 100 USD, base quantity 2, fee 1 USD and slippage cost 0.5 USD.
3. Choose **Record paper exit**, select that open paper entry, enter price 110 USD, quantity 2, fee 1 USD and slippage cost 0.5 USD.
4. The session report shows **$20 gross / $17 net realized paper P&L**, two paper records and zero open entries. These are hypothetical arithmetic, not exchange fills or strategy validation.
5. Export the demo journal as JSON if wanted. Clear opens a confirmation dialog; cancel preserves records, while explicit confirmation resets demo state.

Quantity and USD-notional sizing are supported. Notional sizing floors quantity to eight decimals; the journal uses BigInt fixed-point arithmetic at eight decimal places, with nearest-unit rounding for products/cost allocation and cent rounding for display. Entry fees/slippage are allocated cumulatively in proportion to partial exits, conserving the total through the final exit. Slippage is an additional user-entered USD cost, not an invented execution price adjustment.

Prices/quantities must be positive bounded decimals; fees/slippage may be zero. NaN, infinity, exponent notation, negative values, excessive precision and USD/USDT mismatch refuse. An exit cannot exceed the selected entry's remaining quantity. One-time submission IDs and form clearing prevent accidental double submissions. Open quantity/cost basis are separate from realized P&L; market marks and unrealized P&L are unavailable. No actual balance, forced candidate, WATCH-based win rate or money recommendation appears.

## Local storage and rendering

State is versioned and segregated as DEMO_ONLY, at key `boss-trader-demo-paper-v1`. Every watch and paper record retains a demo source session. No import or future real-source mixing is implemented. State is capped at 128 KiB, 200 journal records, 20 sessions and 12 watches; activity retains its latest 80 entries. Records are not silently truncated.

Storage is validated before rendering/accounting. Missing data starts an empty journal. Unsupported/corrupt data is not overwritten: changes pause until an explicit confirmed reset. Disabled or full storage falls back to the current tab with a visible warning; export before leaving. Clearing while storage is unavailable clears only this tab and explicitly warns that previously saved data could not be changed. File-local storage availability/isolation varies by browser, profile and file path.

Use one tab at a time. A storage-change check/event pauses editing on detected concurrent changes, but localStorage is not a transactional database and does not guarantee race-free multi-tab writes. Export is a local JSON download; there is no import, remote sync or backup service. Do not commit private exported journal data.

Untrusted notes/source strings use textContent rather than dynamic HTML. Embedded JSON escapes script boundaries. CSP denies connections, external resources and form actions. No external fonts, CDN, analytics, polling, order route or notification exists. Detailed B1–B5 notes are expandable rather than obstructing the workflow.

## Verification and screenshots

| Check | Exact result |
| --- | --- |
| `python -B -m unittest tests.test_dashboard_029 -v` | 9 tests, 0.022s, OK |
| `node tests/test_paper_029.cjs` | 25 checks passed; Node was already installed, no packages added |
| `python -B -m unittest discover -s tests -v` | 484 tests, 5.994s, OK, no skips |
| `python -B tests/browser_dashboard_029.py` | 25 browser checks passed using installed Playwright/Chromium, no installation |
| Desktop | 1440px, no horizontal overflow |
| Phone | 390px, no horizontal overflow; visible buttons at least 44px high |
| Browser errors / external document requests | 0 / 0 |

[Browser evidence JSON](artifacts/dashboard-029-browser-evidence.json) lists each check.

- [Desktop screenshot](artifacts/dashboard-029-desktop.png)
- [390px phone screenshot](artifacts/dashboard-029-phone.png)
- [Empty/WAIT presentation test](artifacts/dashboard-029-empty.png)
- [BLOCKED presentation test](artifacts/dashboard-029-blocked.png)

Screenshots show only invented walkthrough transactions, never private owner journal data. The committed HTML itself contains no journal records; it starts from browser-local state or an empty journal.

The browser walkthrough verified adding a watch, double-submit refusal, entry/open position, visible oversell refusal, exit and correct net P&L, JSON export, confirmation cancel/reset, quote mismatch, escaped malicious notes, corrupt storage preservation/recovery and disabled-storage usability. The Python generator tests verify exact source parity, stable IDs, missing/blocked values, network boundary and script escaping. The pure journal tests cover partial exits, cost conservation, numeric/unit validation, persisted oversell/corruption and JSON round-trip without session duplication.

**Browser scope limitation:** managed Chromium blocked file navigation, and loopback navigation timed out. The exact standalone document was therefore rendered via Playwright set_content at about:blank, with all external document requests aborted. DOM, layout and interactions are real Chromium executions. Journal rehydration used an explicitly controlled storage test double; native file-origin storage/reload was **not verified**. Separately, the real browser's unavailable-storage path was exercised without the double, and the production journal engine's serialize/load round-trip passed. Ordinary-browser file persistence and cross-browser/mobile-device behavior require owner review; no synthetic result is presented as native persistence evidence.

Chromium initially required the supported additional sandbox permission for local IPC; it was not used for exchange/time queries. No browser policy, operating-system safety gate, proxy policy or repository gate was changed. No server was started or deployed.

## File scope and owner review

New implementation: `research/dashboard_029.py`; `research/dashboard_029/{screen.html,paper.js,app.js}`.
New tests: `tests/test_dashboard_029.py`, `tests/test_paper_029.cjs`, `tests/browser_dashboard_029.py`.
Review artifacts: this report, generated HTML, browser evidence JSON and four PNGs.

All 113 baseline files are unchanged. There is no dependence on PR #52, no new UTC/chrony work, scanner change or real-source admission. B1/B2/B3/B5 HOLD; B4 NO-GO; NO ORDERS.

Smallest owner action: download/open the reviewed HTML in the intended phone/desktop browser and confirm that local persistence works there, then review the Draft PR. Keep it draft and unmerged. No deployment or workflow dispatch is part of this assignment.

STOP FOR OWNER AND BOSS AI REVIEW.

