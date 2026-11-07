# BOSS Trader Lab — CODEX 031 read-only market view

Issue #57. Baseline `499edbedf4c5ae7e6aa31891f01809afc373e6ef` (Draft PR #56),
stacked on Draft PR #54 at `8b801dae5c13a264167ddfe56c58c5052118c496`.
New branch `research/issue-57-read-only-market-view`, Draft PR targeting
`research/issue-55-demo-journal-restore`. Existing branch heads and PR metadata
are not changed. PR #52 stays parked. README.md, SECURITY.md and the 024/025
source-admission reports were read; no AGENTS.md exists in the baseline tree.

## Run locally

```sh
python -B -m research.market_observation_031
# Offline default: no server or requests.
python -B -m research.market_observation_031 --serve
# Open exactly http://127.0.0.1:8765/ in the same machine's browser.
```

The server serves the generated UI at GET `/`. Select **Market observation** and
press **Refresh market observation** explicitly. Opening/switching views does not
fetch. One manual refresh requests one fixed public endpoint. There is no polling,
scheduler, auto-retry, redirect, fallback, quote request or credential field.
`--port` changes only the local port (1024–65535); binding remains 127.0.0.1.
Ctrl-C stops the runner. It does not deploy or alter the hosted review site.

Standalone review artifact:
[Generated HTML](artifacts/boss-trader-demo-029.html).
Regenerate with `python -B -m research.dashboard_029 --output boss-trader-demo.html`.
The standalone file retains functional offline demo/export/restore; its market
Refresh instructs the user to run the local server instead of attempting file-origin
fetch. A local-only runner requires a browser on the same host: a separate phone
cannot connect to its own 127.0.0.1 to reach a desktop. Remote phone access,
forwarding, public hosting and deployment are outside this slice. A 390px browser
viewport test is supplied, not claimed equivalent to a physical phone.

## Feature availability

| Feature | Availability |
| --- | --- |
| Existing offline USD demo | Retained, static synthetic fixtures and original formulas |
| Real market observation | Manual local runner implemented; LIVE FETCH UNVERIFIED here |
| Observation identity | Binance spot BTC/USDT only, never Kraken BTC/USD |
| Latest completed 1h close | Displayed with capture, candle close boundary, freshness-at-capture and local-clock caveat |
| Current executable quote | Unavailable; no separately reviewed quote endpoint used |
| Reversal classification | Unavailable for real source; all admission gates retained |
| Paper source | Existing version-1 DEMO_ONLY store/accounting unchanged; observation-linked paper unavailable |
| Export/restore | Retained for demo only; no observation enters journal |
| Google Drive | Pending/not connected; local records may be lost; no persistence promise |
| LLM | Not integrated; explanations remain plain rule/source availability statements |

The screen has a separate market view, read-only header identity and manual loading,
success, concrete error and stale-last-success states. No OBSERVE_ONLY row becomes
WATCH/WAIT/ENTRY READY or confidence. The intended future 0–3 reversal candidate
behavior, including zero and no forced trade, is unchanged and unactivated.
A successful view is a static snapshot with freshness at capture, not continually
fresh data. Refresh rechecks; no background clock/network loop is started.

## Reviewed endpoint and request manifest

| Item | Fixed scope/bound |
| --- | --- |
| Provider | Binance public spot; existing `boss_trader_lab.BINANCE_KLINES` |
| Allowlist | Exactly one pair: `BTCUSDT` = BTC/USDT spot, quote USDT |
| GET | `https://api.binance.com/api/v3/klines?symbol=BTCUSDT&interval=1h&limit=30` |
| Request count | One GET per accepted manual Refresh; no retry/redirect/fallback |
| Endpoint weight | 2 in the pinned official documentation |
| Cooldown | At least 30 seconds between attempts across tabs on this runner; concurrent Refresh rejected |
| Provider limits | 418/429 numeric Retry-After honored with minimum 120s; missing header 120s; unknown/date/oversized value effectively pauses this runner (10^15 seconds), requiring owner review/restart |
| Socket timeout | Existing observer convention: 12 seconds per socket operation |
| Child wait | Disposable Python child, `subprocess.run(timeout=15)`; expiry kills/waits for direct child per stdlib behavior; no shell |
| UI request | Explicit POST, client abort after 18s, no background retry |
| Provider bytes | Content-Length, if supplied, must be numeric and <=65536; read at most 65537 and reject overflow; compression refused |
| Result bytes | Child JSON <=8192 checked on return; fixed trusted child emits summary/error only |
| Local UI bytes | Generator <=512 KiB; local response <=512 KiB; market summary <=8192 from child |
| Local input | Exact POST `/api/market-read`, Content-Type application/json, single Content-Length 2, body exactly `{}`; no caller symbol/URL/quote fields |
| Origin/Host | Exact 127.0.0.1:<bound port>; POST requires matching http Origin; foreign/duplicate Host/Origin and cross-site Fetch-Site refused; no CORS grants |
| Credentials | None; client fetch credentials omitted; no account/wallet/order endpoint |

Allowlist/URL are code-reviewed constants, not runtime URL configuration. Changing
pairs requires review of this manifest/code/tests; there is no open proxy or mirror.
Normal urllib environment proxy and CA behavior is inherited, never bypassed.

Official source inspected via GitHub connector (documentation only):
[Binance Spot REST kline schema, commit 2bae3f5bd622ebfdea593daed066df14dc7e7362](https://github.com/binance/binance-spot-api-docs/blob/2bae3f5bd622ebfdea593daed066df14dc7e7362/rest-api.md#klinecandlestick-data).
It documents `/api/v3/klines`, unique open time, UTC default timezone, 1h interval,
limit, weight 2 and the exact 12-field array. This is source documentation, not
proof of current endpoint availability or authentic data captured in this task.

Existing observer comparison: `boss_trader_lab.fetch_closed_closes` already uses
this endpoint, 30 rows, 12s timeout and USDT identity; `observe` supplies the reused
non-actionable arithmetic. The original network helper has uncapped JSON reading
and permissive shape handling, so this local adapter keeps its documented endpoint
and observation function while adding strict input/response bounds. The Kraken
observer is a separate USD source; it is unchanged. The strict 025 raw Kraken
transport is NOT activated or presented as a production qualified adapter.

## Validation and remaining transport/clock limits

Exact 12-field rows, 22–30 input rows, hourly millisecond alignment, inclusive close
`open + 3600000 - 1`, strictly consecutive chronology, no duplicates/gaps and no
future opens. Numeric strings must be finite, bounded length and positive for
prices; volumes nonnegative, OHLC consistent, taker volume no greater than total,
zero base/quote volume consistent, integer nonnegative trade count and exact
reserved `"0"` profile. Unknown variants refuse. Incomplete rows are excluded from
observation arithmetic; at least 21 complete rows required. Latest completed close
must be less than one hour old relative to the sampled local clock. The displayed
close time is the exclusive hourly boundary (provider close millisecond + 1).
Only the completed close summary crosses to the view. No high/low/volume is invented
or retained from close-only results, and no raw candles are committed or exported.

Source symbol is bound by the exact TLS endpoint/request manifest; this response
schema does not echo a symbol or independently attest asset metadata/trading status.
There is no currency conversion or provider substitution. UI also refuses source,
quote, status, endpoint, mode and numeric mismatches. Errors are rendered as text.

**Limits:** 12s socket timeout is not a wall-clock proof. The 15s direct-child wait
is an application containment mechanism, not a measured hard scheduler/cleanup,
process-tree RSS or DNS/TLS/kernel guarantee. Popen/startup, kernel stalls, resource
limits and target-runner cleanup remain unqualified. Child output size is checked
after collection; it is fixed trusted code, not hostile-worker memory containment.
The local threaded HTTP server is a small loopback review runner, not hardened
public infrastructure or a connection-count/memory sandbox. Cooldowns are in-memory
and reset on explicit server restart; there is no automatic restart/retry. Do not
use restarting to defeat a provider limit.

Capture/completion/freshness use unverified local system UTC, explicitly labeled.
No NTS/time authority is contacted; HTTP time is not promoted to trusted UTC.
Clock skew can invalidate completion/freshness assertions. B4 NO-GO remains;
B1/B2/B3/B5 HOLD remain. This weaker OBSERVE_ONLY display does not admit data to the
strict reversal path, weaken that path, or certify trading/market performance.

## Exact test evidence

| Command | Result |
| --- | --- |
| `python -B -m unittest tests.test_market_observation_031 tests.test_dashboard_029 -v` | 23 passed, 0.021s |
| `python -B -m unittest discover -s tests -v` | 498 passed, 6.135s, no skips |
| `node tests/test_market_031.cjs` | 8 groups passed |
| `node tests/test_restore_030.cjs` | 14 checks passed |
| `node tests/test_paper_029.cjs` | 26 checks passed |
| `node --check research/dashboard_029/market.js` | passed |
| Default module CLI | Offline message; no server or market requests |
| `python -B -m tests.browser_market_031 --run` | BLOCKED at Chromium launch, exit 2; one attempt |

Offline tests use invented Binance-shaped arrays and controlled dependencies.
They cover import/default/page-load/view-switch no fetch, fixed request/allowlist,
quote mismatch, 12-field shape, byte limits, malformed/nonfinite/unfinished/gapped/
duplicate/stale/future data, volume semantics, no redirects/retries, timeout/output
refusal, 429/Retry-After holds, concurrent refresh, Host/Origin/fixed body validation,
loading, retained stale last success, text rendering and source/journal separation.
Existing demo accounting, restore and full offline regressions remain passing.
Node DOM/controller tests are controlled-dependency tests, not browser screenshots
or native persistence evidence. Python route tests invoke the real handler methods
with memory streams; they do not prove actual socket behavior.

## Browser, runner and live evidence gaps

[Browser attempt](artifacts/market-031-browser-evidence.json): installed Chromium,
sandbox enabled, one bounded launch, failed with TargetClosedError and
`setsockopt: Operation not permitted (1)`. No navigation, server, UI interaction or
screenshots succeeded. No retry/escalation, policy override, isolation disabling,
installation or storage double was used. The supplied opt-in browser harness
would run actual same-origin HTTP with an injected invented provider, visibly
labeled fixture data, and capture desktop loading/valid/stale plus 390px valid/
stale/source separation only on success. It is not reported passed.

[Local runner attempt](artifacts/market-031-loopback-evidence.json): a separate
controlled loopback-only socket smoke check could not bind; PermissionError,
`[Errno 1] Operation not permitted`. Zero external requests. No socket bypass or
retry. The runnable server is implemented but actual serving on this executor is
UNVERIFIED. Browser/file persistence and real phone behavior remain UNVERIFIED.
No historical screenshots were relabeled or reused as fresh evidence.

**LIVE FETCH UNVERIFIED:** current Cloud environment network policy was inspected:
restricted/enforced, observations current; GitHub hosts only, neither api.binance.com
nor api.kraken.com permitted. No provider request was attempted, and no authority
or proxy bypass used. The issue permits one existing-scope smoke test only when
endpoint bounds and target capability support it; the original helper is uncapped,
this target cannot bind loopback or launch Chromium, and the provider is not on the
allowed list. No authentic candles or genuine capture-time claims are published.

## Smallest safe owner action

Review the stacked diff, then run the controlled offline browser harness in an
already permitted environment:

```sh
python -B -m tests.browser_market_031 --run
```

It makes no exchange requests. Confirm manual loading/valid/error/stale views,
390px/desktop, source identities, demo export/restore still separate and zero
requests on initial load/view switch. Only actual successful execution can supply
fresh screenshots. Then, on an already permitted local target, start the runner
with `--serve`, select Market observation, and authorize exactly one manual Refresh
for this fixed BTC/USDT manifest. Verify OBSERVE_ONLY, capture/close time and local
clock caveat, no executable quote/reversal/paper admission. Honor any provider
cooldown/refusal; never retry automatically or seek a mirror. This is a proposed
next owner verification, not evidence of a successful live run here.

Hosted private Sites review is a separate repository/deployment. No GitHub PR in
this task updates it. The provider-neutral Drive snapshot draft at separate Sites
commit `033328cf1316b4b9700324595933d75af5622157` is not imported, duplicated,
operational or a dependency here. Drive remains disconnected.

No change to main, existing PRs/workflows, working Kraken observer, original
reversal formulas/refusal registry, demo paper schema/accounting, source admission,
clock limits, ZUMERAVO or BOSS539. No orders, accounts/keys, scheduling, dispatch,
paid service, installation, deployment or merge. Individual users retain their
README responsibility for provider data-use rights; no blanket licensing gate is
added. Keep all PRs Draft/unmerged. STOP FOR OWNER AND BOSS AI REVIEW.
