# BOSS Trader Lab — CODEX 030 journal backup preview and restore

Issue #55. Baseline: `8b801dae5c13a264167ddfe56c58c5052118c496`.
Separate branch `research/issue-55-demo-journal-restore`, stacked Draft PR targeting
`research/issue-53-offline-dashboard` (PR #54). This explicitly depends on the
unmerged dashboard, not PR #52. PR #54's branch and metadata are untouched.
Repository README/SECURITY instructions reviewed; no AGENTS.md in baseline tree.

## Run and review

```sh
python -B -m research.dashboard_029 --output boss-trader-demo.html
```

Open the generated self-contained HTML locally in an already permitted browser.
[Committed HTML](artifacts/boss-trader-demo-029.html) contains no private journal.
Accepted design and existing scanner/accounting formulas are retained. The visible
**Restore demo journal** button sits alongside Export and opens a local file picker.
No server, upload, URL input, remote resources or market-data ingestion.

One `.json` file is accepted; file bytes are capped at 128 KiB before reading and
UTF-8 bytes checked again before JSON parsing. The existing exact version-1
DEMO_ONLY validator enforces allowed spot USD pairs, amounts, references, unique
IDs, no oversells and all existing size/count limits. Restoration uses its
accounting and session loader; it does not implement another engine.

The preview is temporary and displays original backup counts, current counts,
replacement counts (including the displayed fixture session), gross/net realized
paper P&L, replacement consequences and storage availability. Current fixture
session metadata must agree on ID, revision, as-of and DEMO_ONLY source; a missing
session is added exactly once within existing limits. Other arbitrary hashes
remain user-supplied labels, never authentication or genuine provenance evidence.

Explicit confirmation REPLACES the journal. Cancel/Escape discards pending state
without writes. A later failed preview invalidates earlier pending confirmation.
Same-tab changes invalidate the preview; existing production write checks prevent
silent overwrite after another tab changes storage or when corruption has locked
the journal. Pending file reads are invalidated when another selection begins.
Storage read/write failure uses the existing visible memory-only fallback and
cannot claim durable saving. Unknown previously stored bytes are not cleared.

Export now emits compact JSON to avoid indentation inflating otherwise restorable
backups; an over-limit UTF-8 backup refuses visibly without creating a file.
No owner file is opened for writing, deleted or overwritten. Download/export uses
the browser's ordinary download mechanism. Notes and preview text use textContent.
Schema validity is not proof of trusted market data or investment performance.

## Exact offline evidence

| Command | Result |
| --- | --- |
| `node tests/test_restore_030.cjs` | 14 checks passed |
| `node tests/test_paper_029.cjs` | 26 checks passed |
| `python -B -m unittest tests.test_dashboard_029 -v` | 11 tests passed, 0.021s |
| `python -B -m unittest discover -s tests -v` | 486 tests passed, 6.002s, no skips |
| `node --check research/dashboard_029/app.js` | passed |
| `node --check research/dashboard_029/restore.js` | passed |
| `python -B tests/browser_restore_030.py --run` | BLOCKED at browser launch, exit 2 |

Restore tests execute the production transaction module, validator, accounting and
unchanged production write function with controlled storage dependencies. They
cover export/preview/cancel/exact replacement, retained IDs, no duplicate sessions,
missing-session reconciliation, colliding metadata, malformed/oversized/schema/
mode/version/quote/reference/oversell/duplicate and count-limit rejection without
mutation, pending invalidation, same-tab/concurrent-tab changes, corruption lock,
unavailable/quota/read-failure fallback and literal malicious notes. The accounting
fixture has entry 2 at 100 USD, fee 1, slippage 0.5. Two exits of 1 at 110, each fee
0.5 and slippage 0.25, produce 10/8.50 USD after the first and 20/17 USD final
gross/net with no remaining position. Serialization retains IDs and exact costs.

These are controlled-dependency tests, not native browser persistence or a browser
DOM interaction demonstration. Python verifies self-contained generation and the
bounded local input/explicit confirmation controls, plus existing source parity.
An initial focused-test selector incorrectly omitted the button's type attribute;
that assertion was corrected and focused/full suites rerun to the passing results
above. No runtime fix was needed for that assertion failure.

## Browser limitation and owner acceptance

[Browser attempt record](artifacts/restore-030-browser-evidence.json) records one
attempt with installed Playwright/Chromium, browser sandbox enabled and a temporary
profile. Launch failed with TargetClosedError and
`setsockopt: Operation not permitted (1)`. It did not reach document navigation.
No escalation, retry, weaker isolation, storage substitution or installation.
The record distinguishes attempted and final HTML hashes because final offline
changes followed the failed launch; neither artifact was browser-verified.
No new screenshots were captured or old screenshots reused as current evidence.
Native storage/reload/tab reopen/browser restart remain UNVERIFIED. Issue #53's
persistence gap is not resolved. Mobile/desktop restore interactions, file picker,
dialog rendering, export download and literal-note DOM behavior need actual
browser verification. The opt-in browser script is provided, not reported passed.

Smallest safe owner action, in an already permitted intended browser:

1. Generate/open this revision. Add an invented BTC/USD watch and paper entry
   (100 USD, quantity 2, fee 1, slippage 0.5). Record a partial exit (110 USD,
   quantity 1, fee 0.5, slippage 0.25). Export the demo JSON to a new backup.
2. With a different current demo journal, choose Restore and that backup. Verify
   preview counts, synthetic labels, 10 USD gross / 8.50 USD net and replacement
   warning. Cancel; confirm current state/exported bytes remain unchanged.
3. Preview again and explicitly confirm. Verify backup record/source IDs, watches,
   single current fixture session, open quantity 1 and unchanged partial P&L.
4. Close remaining quantity 1 with the same exit inputs. Expect 20 USD gross,
   17 USD net and zero open positions. Export and inspect the three exact records.
5. Verify malformed/oversized backups refuse; malicious notes render literally;
   a second tab's intervening write refuses confirmation. Capture desktop/390px
   only after successful actual execution, without private financial data.
6. Test reload, same-profile/path tab reopen, and browser restart separately if
   permitted; report each independently. Different file locations/profiles/origins
   do not establish persistence at the intended location.

The optional `python -B tests/browser_restore_030.py --run` exercises the invented
export → preview → cancel → preview → confirm → partial/final-accounting path and
captures only on success. Use only existing permitted browser capabilities; do
not install or weaken policy to make it run.

## Scope and limits

Changed: generator, screen, app wiring, paper engine restore entry point,
new restore transaction module, generated HTML, focused Python test, new Node
restore tests, opt-in browser script, blocked-browser evidence, this report.
Existing formulas, observer, refusal registry, baseline screenshots, workflows,
PR #52 and PR #54 remain unchanged. This is recovery of untrusted synthetic
user-supplied journal data, not source admission, authentication or native storage
certification. No live requests, credentials, orders, scheduling, hosting,
deployment, installations, workflow dispatch, merge, ZUMERAVO or BOSS539 changes.
B1/B2/B3/B5 HOLD; B4 NO-GO; real reversal admission HOLD; NO ORDERS.

Keep both PRs Draft/unmerged and Issue #53 open. STOP FOR OWNER AND BOSS AI REVIEW.
