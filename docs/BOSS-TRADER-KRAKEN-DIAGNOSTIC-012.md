# BOSS TRADER — Disabled Kraken diagnostic 012

**Decision: REVIEW offline implementation; HOLD all live use and Operational Test Mode.**
Authorization: [Issue #18](https://github.com/tazmanked-bot/boss-trader-lab/issues/18).
Specification read fully: [readiness 011](BOSS-TRADER-KRAKEN-LIVE-READINESS-011.md).
Baseline: `1115eb9730100ae99c2d05ed12c50d75aef104f8` (owner's PR #17 merge).
Date: 2026-11-06 UTC. Branch: `research/issue-3-offline-kraken-diagnostic`.
Draft PR only; owner/BOSS AI review before any follow-up.

## What is implemented and what remains disabled

New optional stdlib module: `research/kraken_spot_diagnostic.py`. It implements
fixed request construction, injected connection/worker orchestration, identity,
clock and commitment gates, unchanged bridge integration, strict response parsing
and bounded summaries. New synthetic identity fixture and offline tests accompany
it. Existing source/tests/workflows/dependencies are untouched.

**There is no real HTTPS connection constructor or real clock provider in this
module.** `run_offline` requires a dependency-injected test connection factory,
trusted injected clock and a 40-hex revision claim. Missing factory returns
AUTHORIZATION_MISSING before clock/file/worker use. Import performs no request
or worker startup. The CLI always refuses, even with --live/--authorize arguments;
no flag, environment variable, dispatch or green test activates a live mode.

```text
python -B -m research.kraken_spot_diagnostic
{"diagnostic_hash":"b29f8b61248be5ad7d90ae6294e6ba14271ecc82b33a48d0532893666bdca0eb","mode":"DISABLED","overall":"HOLD","reason":"AUTHORIZATION_MISSING","requests":0,"version":"kraken-spot-diagnostic-v1"}
exit status: 2
```

This command was executed only to verify disabled behavior. No real Kraken
request, monitoring, market scan or live workflow occurred. An eventually runnable
live tool requires a separate reviewed change and explicit owner authorization;
injecting arbitrary application code is not a supported activation mechanism.
Factories, job implementations and clock objects are trusted test dependencies,
not an arbitrary-code sandbox. A malicious injected callable could itself perform
I/O; this implementation does not claim to contain arbitrary Python code.

## Fixed request and identity contracts

Only host `api.kraken.com`, port 443, relative paths `/0/public/AssetPairs` and
`/0/public/OHLC`, method GET, no body. Exact AssetPairs parameters:
`pair=<fixed altname>`, `aclass_base=currency`, `info=info`. Exact OHLC parameters:
`pair=<same altname>`, integer `interval=60`, integer aligned `since=as_of-86400`.
No assetVersion/display switch, arbitrary URL, private path, additional parameter,
auth/cookie header, proxy handler, redirect follow, mirror, substitution or retry.
The injected connection receives only the fixed host/port and strict TLS context.

| Symbol | Request altname | Required metadata/OHLC result key | Required base / wsname |
| --- | --- | --- | --- |
| BTC/USD | XBTUSD | XXBTZUSD | XXBT / XBT/USD |
| XRP/USD | XRPUSD | XXRPZUSD | XXRP / XRP/USD |
| SOL/USD | SOLUSD | SOLUSD | SOL / SOL/USD |

These are conservative **research expectations**, not newly verified current
exchange aliases. Require one exact AssetPairs record with matching altname,
wsname, base, quote=ZUSD, both asset classes=currency and status=online. Missing
fields, changed key, USDT, other base/market or conflicting names refuse. Known
optional metadata fields (fees, lot/precision, leverage metadata etc.) are
explicitly allowlisted and ignored, not interpreted as trading authority; unknown
fields refuse. Optional field contents are not evidence of market eligibility.
Strict record/status/schema assumptions may reject a legitimate live response.

Only after this record matches does that symbol get one OHLC attempt. Its result
key must equal the **metadata key**. The bridge accepting an alternate XBTUSD
key does not override a metadata mismatch. XRP/SOL names cannot be inferred from
OHLC or auto-learned. Maximum six supervised attempts, fewer when identity fails;
each symbol has at most one identity and one subsequent OHLC attempt. Summary
`requests` counts supervised attempts, including rejected worker startup, not
independently observed network sends. Normal execution always reports zero.

The injected mock metadata is synthetic consistency evidence only. The source
anchors and KNOW/UNKNOWN distinctions in readiness 011 remain applicable:
[official OHLC](https://docs.kraken.com/api-reference/market-data/get-ohlc-data),
[AssetPairs](https://docs.kraken.com/api-reference/market-data/get-tradable-asset-pairs),
and [OHLCVT units/gaps](https://support.kraken.com/articles/360047124832-downloadable-historical-ohlcvt-open-high-low-close-volume-trades-data).
No fresh vendor schema retrieval or live identity check is claimed by 012.

## Transport and worker controls

`_exchange` is an internal injected-connection protocol, not a public network
client. It creates `SSLContext(PROTOCOL_TLS_CLIENT)`, loads standard trust roots,
and requires CERT_REQUIRED plus hostname verification before invoking the factory.
It avoids the SSLKEYLOGFILE hook of create_default_context. There is no insecure
TLS fallback, caller-supplied URL, auth header or request body. A trusted test
factory must honor that context; real certificate/hostname validation has not
been observed against any endpoint.

Only status 200 continues. Redirects and 451/429/5xx refuse without reading or
logging an error body, following Location or retrying. Require application/json
(optional UTF-8 charset), identity/no Content-Encoding, one unambiguous Date/type/
encoding/length header. At most 64 headers and 8192 aggregate characters are
accepted by the protocol loop. All compressed responses refuse **before** body
read/decompression; there is no gzip fallback or unbounded decompressor.

Read at most **262144+1 bytes**; actual size, not Content-Length, controls refusal.
Require UTF-8, strict duplicate-key handling and no NaN/Infinity/overflow exponent.
Schema/API errors never become partial captures or dynamically parsed log text.
Headers other than a sanitized Date value never reach summaries. A future real
connection implementation also needs bounded status/header parsing *before*
allocation: the injected factory currently owns getresponse/getheaders behavior.

Default `ProcessJob` uses POSIX fork only, requiring a single Python thread. No
spawn/thread or cross-platform fallback is attempted. A parent monotonic deadline
starts before worker creation/start and covers the entire worker's TLS setup,
fake DNS/connection, response read, parsing and close. Socket timeout=10 is only
an additional argument, not the total-deadline mechanism. The parent polls at
<=10ms, rejects completion **at or after 10s**, discards late data and immediately
sends kill to a still-running process. Termination has no grace/retry period.

IPC uses a fixed 264196-byte shared buffer, with bounded length-prefixed metadata and
body published last; the parent reads it only after worker exit. No blocking
pipe recv, arbitrary pickle payload, stdout response capture or raw-response file
is used. Unknown/fake success transport error codes cannot produce data success.
Reaping has a separate bounded **250ms** allowance, outside request acceptance;
failure to reap stops all later work with WORKER_UNREAPED/HOLD.

**Deadline limitations:** this is not a hard-real-time OS guarantee. Parent
descheduling, fork/start delays, a native/kernel stall, SIGKILL delivery and
uninterruptible kernel tasks can overrun wall time. Python cannot prove immediate
termination/reaping under every kernel condition. There is no live-capable default
to expose that uncertainty; unsupported multithread/platform cases refuse and an
unreaped worker stops all additional attempts. Real DNS, permitted routing and
real client header/TLS behavior remain untested. Do not enable a live adapter
unless the target platform's deadline/cleanup behavior receives separate review;
if the required bound cannot be established, continue HOLD rather than substituting
a thread, bare socket timeout, retry or fire-and-forget request.

## Clock, projection and refusal behavior

Injected clock supplies UTC nanoseconds and monotonic nanoseconds. An explicit
trusted flag is a test assertion, not independent synchronization evidence.
Capture initial pair before any worker; freeze common
`as_of=((initial_utc_ns//1e9-2)//3600)*3600`. No response end, cursor, fresh symbol
or later request can move it forward. Guard and supported epoch bounds are strict.

Each pre/post capture is compared against **both** the initial pair and previous
capture. Backward wall/monotonic jumps, cumulative drift >1s, per-request elapsed
>=10s or wall/monotonic discrepancy >1s refuse. Supervisor checks monotonic
progress around worker execution and result retrieval too. HTTP Date must be
canonical UTC IMF-fixdate (including correct weekday), supported epoch seconds,
and within `[floor(start)-2, floor(end)+2]`. Missing/bad Date, skew or clock failure
stops further requests; Date is a coarse untrusted consistency check, not a time
oracle or closure proof. No /Time or trades endpoint is called.

OHLC row headers must be exact eight-element arrays with native integer, aligned
second timestamps in range. No row can be beyond the captured service/end upper
hour. The claimed uncommitted final row must remain **outside** the eligible
window; if it would be eligible, COMMITMENT_CONFLICT refuses instead of admitting
an old unfinished candle. Projected-header order/spacing conflicts also refuse.
No values from excluded rows are examined for signal/data approval or hashed.

The unchanged bridge receives explicit as_of mode. Its exact decimal/float
checks, known pair schema, complete OHLCV, eligible order/duplicate/gap refusal,
21 closed bars and 3h per-symbol freshness remain unchanged. No fabricated bars,
sorting, gap fill, score or synthetic/live fallback. Clock/commitment checks may
refuse before the bridge, so a corrupt series need not reach its specific code.
Identity consistency, clock status/reason and bridge/registry decision are stored
separately. A fresh BTC result cannot rescue failed XRP/SOL. Overall is always
HOLD; even all three data-check successes never grant operational authority.

Same fixed-context output is byte-identical when excluded current-row values
change, including invalid/secret placeholder strings. Appending future-relative-
to-as_of rows is invariant **only within** the documented structural/time/resource
contract: e.g. the two-second guard can leave an additional already-captured hour
outside as_of. Appending a timestamp beyond capture time or a malformed header
must refuse, not be hidden by no-lookahead filtering. Global invalid JSON still
refuses even in excluded rows. Tests compare the entire canonical summary for
both successful and refused eligible histories, including hashes and receipts.

## Safe evidence and code identity

Only bounded canonical summaries are returned: version, capture/bridge policies,
fixed spot/USD identity/key, endpoint paths and fixed parameters, injected UTC/
monotonic receipts and sanitized Date, as_of, stage/reason, identity/clock state,
bridge/registry references and diagnostic hashes. No raw response/body/error,
arbitrary header, future price, source-row count, raw-response hash, account data
or opportunity calculation is returned/logged. Worker exceptions are redacted;
CLI prints only the disabled summary. Raw payload exists transiently in bounded
worker/shared memory to permit parsing, never as a log/artifact or debug capture.

`implementation_sha256` identifies the exact diagnostic source bytes; baseline
and an explicit 40-hex `reviewed_revision_claim` accompany it. The revision is a
**recorded claim**, not verified checkout identity or authorization. The next
owner workflow must independently assert HEAD equals the reviewed commit; tests
use a clearly synthetic all-zero claim. Dependency/source hashes do not establish
exchange authenticity. R3 references cover eligible data, not entire raw responses.
Per-symbol canonical output <=4096 bytes; total <=16384, enforced by sealing.
Every sealed hash covers the safe summary before its hash field is added.

## Executed evidence and safeguard matrix

Local Python **3.12.14**, stdlib only, no package installation. Exact commands from
staged repository root:

```text
python -B -m unittest discover -s tests -p test_kraken_spot_diagnostic.py -v
Ran 33 tests in 2.392s
OK

python -B -m unittest discover -s tests -v
Ran 117 tests in 2.409s
OK
```

All **84 baseline + 33 new** unittest methods passed; no skipped tests in this
environment, no coverage percentage asserted. Three real child processes blocked
on offline OS Events at fake DNS, connect and read phases were killed/reaped;
another real worker completed a bounded mock packet and was reaped. The injected
parent clock advances deterministically to the deadline **when each phase is
entered**. These tests demonstrate kill/reap control flow, not a measured real
10-second network/timing guarantee. No actual DNS/socket/HTTP operation occurred.

Socket creation/connect/getaddrinfo, urllib urlopen and HTTPSConnection are patched
to raise throughout each new test, including import reload, normal CLI and forked
fakes. Deterministic fake clocks/workers cover completion before/exactly at/after
the deadline, unreaped process refusal, guarded hour races and cumulative drift.
Additional tests cover TLS policy/keylog absence, identity/key/URL constraints,
451/redirects, byte limit+1, compressed/invalid content, strict JSON/Date, zero/
partial success and full-output no-lookahead/refusal invariance.

| Safeguard | Result and evidence scope |
| --- | --- |
| Default import/CLI zero requests; no live activation flag | **PASS** — blocked-network test plus executed disabled CLI, exit 2. |
| One identity then at most one OHLC per symbol; six maximum | **PASS offline** — zero/partial/all-three cases; failed identity has no OHLC. |
| Fixed URLs, SPOT/USD identity, no automatic alias learning | **PASS offline** — request validation and exact metadata/key comparison; real aliases **HOLD**. |
| TLS verify/hostname required, no key logging hook | **PASS policy tests**; real handshake/certificate/CA adequacy **HOLD**. |
| Redirect/451 refusal, no retries/proxy/mirror path | **PASS offline/static** — no error-body read, one attempt, no real client constructor. |
| Byte/encoding/strict JSON bounds; compressed refusal | **PASS offline** — limit+1, false length, gzip refusal, UTF-8/duplicate/nonfinite tests. Real library header allocation **HOLD**. |
| Total 10s acceptance deadline and kill/reap | **PASS offline mechanism** — fake clocks plus real blocked fake workers; real scheduler/DNS/kernel bound **HOLD**. |
| Unsupported platform/unreaped cleanup stops work | **PASS offline** — no unsafe timeout fallback. |
| Initial/subsequent clocks, guard, Date and commitment gates | **PASS offline** — boundary, backward/skew/cumulative drift and current/future header cases; real clock reliability **HOLD**. |
| Existing bridge semantics and no fabricated candles | **PASS** — unchanged files, full regression suite and whole-symbol negative cases. |
| Independent symbol failure / no promotion | **PASS** — BTC cannot rescue XRP/SOL; overall HOLD even for all mock successes. |
| Safe bounded/hash summaries and future-data exclusion | **PASS offline** — byte equality, redaction, hash verification and output-bound tests. |
| Existing runtime/tests/workflows/dependencies preserved | **PASS** — 21 baseline Python/fixture Git blob hashes matched; only four added paths in proposed commit. |
| Live schema, current identities, CI, operational acceptance | **HOLD / UNVERIFIED** — no real endpoint or Actions run performed here. |

No unresolved verified failing test is reported; this is not vulnerability or
profitability clearance. The reported totals are final passing runs.

## Remaining blockers and smallest owner action

1. Current official XRP/SOL identities/aliases, expanded schema constraints,
   real Date/current-row behavior and route availability remain unverified. Mock
   matches cannot close these readiness 011 HOLDs. HTTP/network blocks must remain
   refusal; no proxy/VPN/routing or environment policy was changed.
2. A real connection/clock provider and any live-capable command are **absent**.
   They require separate implementation review/authorization, including header
   allocation bounds, TLS trust, trusted clock setup and target-platform process
   deadline/kill/reap validation. No direct live injection recipe is supplied.
3. POSIX single-thread fork only; no Windows/multithread portability claim. OS
   descheduling/start/kernel stalls cannot be bounded absolutely by these mocks.
   Real-time acceptance stays HOLD if the platform cannot support the required
   safety contract. A partial worker start may conservatively report unreaped.
4. No pinned GitHub Actions run at this head or Operational Test Mode approval
   occurred. Real-world capture integrity/authenticity and paper/live acceptance
   are distinct future matters; no strategy, paper execution or trading code exists.

**Smallest safe owner action:** inspect the exact draft head, then separately
authorize a manual **offline** Actions check pinned to that SHA, Python version
and reviewed action SHAs with contents:read, no secrets/write credential, installs,
raw artifacts or network-dependent diagnostic steps. Run both commands above.
Existing launchers pin older revisions and must not be presumed to test this head.
No workflow is created/edited/launched by this assignment. After independent
review, propose a distinct, narrowly authorized real public Kraken probe; do not
infer network permission from offline success or merging research work.

New inventory: `research/kraken_spot_diagnostic.py`,
`tests/test_kraken_spot_diagnostic.py`,
`tests/fixtures/kraken_diagnostic_identity_v1.json`, and this report. Original BOSS
code/synthetic data under repository MIT; no vendor implementation or dependencies
copied. No scanner/observer/registry/bridge changes, monitoring, orders, credentials,
signals, futures, paid services, ZUMERAVO access, VM migration, merge or issue closure.

**STOP FOR OWNER AND BOSS AI REVIEW.**
