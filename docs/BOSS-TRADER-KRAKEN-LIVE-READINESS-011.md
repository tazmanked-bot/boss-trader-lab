# BOSS TRADER — Kraken schema and manual diagnostic readiness 011

**Verdict: REVIEW Stage A; HOLD live diagnostic and Operational Test Mode.**
Authorization: [Issue #16](https://github.com/tazmanked-bot/boss-trader-lab/issues/16).
Reviewed main: `ec539fafa9f4cbd0e4d655dcc8e214f135f0e0a8` (PR #15 integrated by owner).
Retrieval/review: **2026-11-06 UTC**, completed after 00:03 UTC.
Branch: `research/issue-3-kraken-live-readiness`; draft PR only.

This change adds this report and offline tests. No runtime prototype, transport,
workflow, live request, observer integration or activation is included. Issue #16
prefers documentation over a prototype while source evidence is incomplete.
All proposed network/clock/identity gates below remain **design**, not implemented
or operationally tested. This report supersedes no existing validation semantics.

## 1. Evidence sources and meanings

Sources read through documentation/GitHub connectors; **no api.kraken.com request**:

| Ref | Source / exact section | Retrieved | Evidence boundary |
| --- | --- | --- | --- |
| K1 | [Kraken OHLC](https://docs.kraken.com/api-reference/market-data/get-ohlc-data), response example, opening description, Query Parameters (`pair`, `assetVersion`, `interval`, `since`, `asset_class`) | 2026-11-06 UTC | Vendor prose/example, not measured exchange behavior. Expanded response-child attributes were not exposed by the reader. |
| K2 | [Kraken AssetPairs](https://docs.kraken.com/api-reference/market-data/get-tradable-asset-pairs), XXBTZUSD example and Query Parameters | 2026-11-06 UTC | BTC example and naming/asset-class documentation; no current XRP/SOL instrument inventory. |
| K3 | [Kraken OHLCVT support](https://support.kraken.com/articles/360047124832-downloadable-historical-ohlcvt-open-high-low-close-volume-trades-data), definitions and About the data | 2026-11-06 UTC; page says updated 2026-11-02 | Unit/gap documentation. CSV is a different format; no archives downloaded. |
| R1 | [Observer](https://github.com/tazmanked-bot/boss-trader-lab/blob/ec539fafa9f4cbd0e4d655dcc8e214f135f0e0a8/kraken_public_observer.py), PAIRS, parse_closed_candles | 2026-11-06 UTC | Static close-only, positional final-row discard; no claim it supplies verified OHLCV. |
| R2 | [Registry](https://github.com/tazmanked-bot/boss-trader-lab/blob/ec539fafa9f4cbd0e4d655dcc8e214f135f0e0a8/research/spot_refusal_registry.py), validate_symbol / validate_symbols | 2026-11-06 UTC | Known local semantics: fixed market/time policy, 21 closed bars, <=3h latest-close age, no ranking. |
| R3 | [Bridge](https://github.com/tazmanked-bot/boss-trader-lab/blob/ec539fafa9f4cbd0e4d655dcc8e214f135f0e0a8/research/kraken_spot_validation_bridge.py), PAIRS, validate_capture / validate_capture_json | 2026-11-06 UTC | Known offline conversion/allowlist, not vendor-confirmed current keys or source provenance. |

**KNOWN** means directly supported local behavior or explicit vendor prose, with
the source identified. **DOCUMENTED-EXAMPLE** means only the vendor's sample
demonstrates that representation. **UNVERIFIED-LIVE** means no current public
response was observed. A sample, bridge allowlist, synthetic PASS, SHA or green CI
cannot change the last category into live verification.

## 2. Verification matrix

| Subject | Documentation/local finding | Evidence classification | Current live finding |
| --- | --- | --- | --- |
| Request pair | K1 requires `pair`; R1/R3 choose XBTUSD, XRPUSD, SOLUSD. Only BTC alternate has K2 example support. | KNOWN local config; DOCUMENTED-EXAMPLE BTC | UNVERIFIED-LIVE all three |
| BTC response key | K1 uses XXBTZUSD; K2 links it with alt XBTUSD, base XXBT, quote ZUSD. | DOCUMENTED-EXAMPLE | UNVERIFIED-LIVE |
| XRP / SOL response keys | R3 accepts XXRPZUSD/XRPUSD and SOLUSD. These are research assumptions, not verified metadata. | KNOWN local allowlist; **UNKNOWN vendor-current keys** | UNVERIFIED-LIVE; HOLD identity gate |
| Internal vs display | K1/K2 distinguish default internal names from assetVersion=1 display naming. R3 rejects display keys. | KNOWN documented naming contract | UNVERIFIED-LIVE; display mode unsupported here |
| Row width/types | K1 sample: eight positions, integer endpoints, six numeric strings. Contract names: time, open, high, low, close, VWAP, volume, count. | DOCUMENTED-EXAMPLE; full expanded type constraints UNKNOWN | UNVERIFIED-LIVE |
| Envelope/cursor | K1 sample has error/result/pair/last; last is integer. Its exact response cursor semantics are not established by the rendered child schema. | DOCUMENTED-EXAMPLE; do not assume last proves closure | UNVERIFIED-LIVE |
| Timeframe | K1 interval is minutes, default 1; 60 supported. R3 requires asserted 60 and hourly continuity. | KNOWN documentation/local policy | UNVERIFIED-LIVE; response lacks independent interval attestation |
| Optional arguments | K1 documents since (incremental), assetVersion, asset_class. K2 documents pair/info/aclass_base and other filters. | KNOWN documented parameter surface | UNVERIFIED-LIVE; use narrow proposal below |
| Final row / limit | K1 describes a current uncommitted final entry and maximum 720 rows. | KNOWN documented contract | UNVERIFIED-LIVE; R3 cap is stricter (512) |
| Units | K3 identifies quote-asset prices, base-asset volume, epoch time and trade count. | KNOWN documentation; no unit scaling proposed | UNVERIFIED-LIVE |
| Gaps | K3 warns absent no-trade intervals; R2 refuses missing hours. | KNOWN documentation/local mismatch | UNVERIFIED-LIVE; legitimate gaps still HOLD, never fill |

K1's sample is minute-spaced, not evidence of a successful hourly payload.
K3's seven-column historical CSV is not the eight-field REST input. Neither
leverage-related metadata in K2 nor the availability of other markets grants
permission to use them. Expanded schema, current aliases and real capture-time
behavior remain open evidence gaps; do not invent a stronger vendor guarantee.

## 3. Proposed single-shot diagnostic — NOT installed or authorized to run

An eventual optional stdlib tool would be separate from R1/R2/R3 and all scanner
entry points. One explicit owner invocation, fixed BTC/USD, XRP/USD, SOL/USD,
sequential public GETs only. No polling, private endpoint, auth header, API key,
trade/fill data, order method, alert, ranking or strategy. No proxy/mirror setup,
redirect/failover, retry, venue substitution or network-policy bypass. A blocked
route/451 ends that symbol's attempt; do not find another route.

**Identity first, per symbol:** propose one bounded
`https://api.kraken.com/0/public/AssetPairs` GET with the corresponding `pair`,
`aclass_base=currency`, `info=info`; omit assetVersion for internal naming. Require
empty error list and one unambiguous relevant instrument record. Check its exact
result key, altname, wsname, base, quote, asset classes and spot identity against
the owner-reviewed specification. USD must resolve to USD/ZUSD with consistent
metadata, not USDT; BTC/XBT naming needs explicit reconciliation. For XRP/SOL,
current returned metadata must establish identity before any alias is considered
verified. Missing/conflicting identity yields IDENTITY_UNVERIFIED and **no OHLC
request for that symbol**. Do not learn a new approved alias from OHLC alone or
automatically extend R3. New names outside its allowlist need separate review.

**OHLC second:** only after identity checks, propose one GET to
`https://api.kraken.com/0/public/OHLC` with the verified request pair,
`interval=60`, `since=as_of-24*3600`; omit assetVersion and asset_class. No count
parameter is assumed. since bounds requested history but does not guarantee
returned size or continuity. Require the observed OHLC key to agree with the
verified instrument identity; an alternate accepted by R3 alone is insufficient.
Pass an exact asserted capture envelope to R3 with
`{"version":"spot-refusal-v1","future_mode":"as_of"}`. Keep the outer metadata
separate; do not add unknown fields to R3's capture schema or weaken it.

**Bounds:** at most six GET attempts (three identity + up to three OHLC), no
pagination/retries. 262144 bytes per response; limit actual decoded bytes even
when Content-Length is absent, detect limit+1 without accepting a truncated body.
Require JSON content, UTF-8 and strict duplicate/nonfinite checks. No compressed
body without a separately reviewed decompression bound. Require valid TLS and
fixed scheme/host/path, reject redirects. Each request has a **10-second total
deadline including DNS/connect/read**, not just a per-read socket timeout. A
future implementation must enforce this with a monotonic deadline plus a bounded
worker terminated/reaped by its parent at 10 seconds; a bare urlopen(timeout=10)
does not prove a total deadline. Maximum response data ~1.5 MiB across six requests,
three small summaries, no concurrent fan-out. No worker/transport is added here.

Any parser/transport/identity/clock failure refuses that symbol; retain independent
BTC evidence if XRP/SOL refuse, but mark overall readiness HOLD. No partially
successful candidate or automatic Operational Test Mode promotion. Metadata
validation is evidence consistency, not authenticated truth about an exchange.

## 4. Exact proposed capture clock contract

Proposed policy `manual-capture-v1` (new policy, **not yet approved/implemented**):

1. Capture one UTC epoch-nanosecond wall-clock `W0` and paired monotonic value
   **before the first request**. Confirm trusted runner clock setup independently;
   if unavailable, CLOCK_UNVERIFIED. Never derive cutoff from a candle/cursor,
   response completion, freshest symbol, later retry or a second capture.
2. Define the earlier conservative cutoff `C=floor(W0/1e9)-2` seconds, allowing a
   proposed two-second clock/HTTP-Date precision budget. Freeze common
   `as_of=(C//3600)*3600` for the entire invocation. The guard may exclude an
   additional hour near a boundary; do not relax warmup to compensate.
3. Around every request record local UTC start/end and monotonic elapsed. Require
   end >= start, elapsed in [0,10s], and wall/monotonic elapsed disagreement <=1s.
   Check consistency with the initial wall/monotonic pair across the invocation
   too, so slow clock drift cannot accumulate across requests. Refuse backward
   jumps, exceeded deadlines or inconsistent clocks; never move as_of forward.
4. Require a parseable UTC HTTP Date and check it against
   `[floor(request_start)-2, floor(request_end)+2]` seconds. Missing or conflicting
   service time gives CLOCK_UNVERIFIED / SERVICE_TIME_CONFLICT, not a fallback
   to response-end time. This header is a coarse consistency check, not an
   independent trusted clock or a new time-service call. Cursor last is not a
   service-time substitute. All clock bounds are proposed policy, not Kraken SLA.
5. Check source time headers conservatively against the captured service/local
   envelope. A purported current last-row open beyond the end envelope's UTC
   hour, unsupported units or contradictory source timestamps refuses. An older
   uncommitted row that would enter the eligible window is a commitment conflict:
   HOLD rather than assuming it committed. Identity/current-row structural checks
   must not read excluded OHLCV/count into any decision or evidence.
6. R3 projects only rows with open+3600 <= frozen as_of after width/time checks.
   Its unchanged eligible-value, exact-decimal/float, order/gap/duplicate, 21-bar
   and 3h per-symbol freshness checks apply. The normal current row remains
   excluded, including when a response crosses into the next hour. Strict R3
   policy would instead refuse that row; no positional last-row deletion occurs.

Concrete race: start=T-1s, end=T+1s gives as_of=T-3600, not T. In the existing
fixture, that leaves only 20 eligible rows and correctly refuses warmup. Using
end time would incorrectly admit the 21st close. This is covered by an offline
example. A start at T+1 still uses the previous hour under the two-second guard;
start at T+2 can use T. If the clock uncertainty exceeds the reviewed guard,
refuse instead of claiming that flooring alone removes skew.

The added test-only clock model covers first-request examples/skew/jumps, not
actual clock acquisition, HTTP Date parsing, worker deadlines, later-request
drift or current-row transport attestation. These are implementation blockers,
not test-proven features. Full bridge-byte future-append invariance is tested
only under its documented projection contract with fixed external context.
A future outer source-time gate may refuse inconsistent timestamp headers;
it must never use future **prices** to change a same-as-of decision.

## 5. Evidence and fixed failure vocabulary proposal

Record immutable bounded summaries: reviewed commit, Python and policy versions,
symbol, endpoint/path and allowed request parameters, verified pair key and
identity fields, UTC start/end, elapsed, service Date, as_of, per-symbol status,
fixed refusal category, registry/bridge references. Hash canonical summary bytes
and preserve them with owner-controlled run identification. Do not edit a past
summary to incorporate later observations; a new run is separate evidence.

Do not log raw bodies, raw errors/headers, future values, response latest prices,
raw-response hashes or excluded-row counts. Current-row changes must not perturb
same-context eligible evidence. R3 already hashes eligible full source rows
including VWAP/count separately from its normalized OHLCV decision. Those hashes
are diagnostic references, not origin authentication or a tamper-evident ledger.
Cap safe summary output at 4 KiB/symbol and 16 KiB/run, no raw artifacts or telemetry.

| Proposed outer category | Fixed behavior |
| --- | --- |
| AUTHORIZATION_MISSING / POLICY_BLOCKED | No request; HOLD. No implicit permission from dispatch/green tests. |
| IDENTITY_UNVERIFIED / ALIAS_CHANGED | Refuse symbol before OHLC; no automatic allowlist expansion. |
| TIMEOUT / TLS_FAILURE / NETWORK_UNAVAILABLE / HTTP_REFUSED | One attempt only, no error body or alternate route; DATA_UNAVAILABLE/HOLD. |
| RESPONSE_TOO_LARGE / CONTENT_INVALID / JSON_INVALID / API_ERROR | Refuse complete symbol, no partial capture. |
| CLOCK_UNVERIFIED / CLOCK_CONFLICT / SERVICE_TIME_CONFLICT / COMMITMENT_CONFLICT | Refuse, never repair clocks, shift cutoff forward or trust cursor. |
| BRIDGE_REFUSED | Preserve safe R3 and registry codes, no score override or partial approval. |
| DATA_CHECKS_PASSED | Data-only result; owner readiness review still required. |

These categories are a **proposal**, not additions to R2/R3 enums or claims of
implemented error handling. Preserve all existing refusal semantics.

## 6. GitHub Actions plan — not a workflow installation

Later draft/owner step: manual `workflow_dispatch` only; no push, PR, schedule,
repository_dispatch, workflow_run or automatic chaining. `permissions: contents:read`;
no named secrets, write token, OIDC, auth credentials or token passed to diagnostic
workers. Checkout uses the minimum read token with persist-credentials:false.
Immutable full commit checkout, independent HEAD equality assertion, fixed
Python **3.12.14**, no pip install, concurrency cap one, five-minute job limit.
Fixed command only, no arbitrary dispatch URLs/symbols/refs/shell arguments.

Candidate action identities, resolved on GitHub 2026-11-06 UTC:
[checkout@11d5960a326750d5838078e36cf38b85af677262](https://github.com/actions/checkout/commit/11d5960a326750d5838078e36cf38b85af677262)
and [setup-python@a26af69be951a213d495a4c3e4e4022e16d87065](https://github.com/actions/setup-python/commit/a26af69be951a213d495a4c3e4e4022e16d87065).
These match the owner's baseline PR15 launcher pins; resolution is not security
clearance. Review action source/support and hosted Python availability before
approving a new workflow. Pin the new reviewed commit, not a moving branch.

Separate offline verification from any later explicitly approved diagnostic.
Existing PR15 launcher checks out `96398d1f03bebc58a4429402c32f3a73f1b5ac76`;
it cannot verify this PR's new tests merely by selecting this branch on dispatch.
No existing launcher is edited or run here. Retain no raw responses in artifacts,
no external telemetry; any future summarized artifact would need its own reviewed
action SHA, retention/bounds and owner approval. No artifact step is proposed now.

## 7. Acceptance checklist and blockers

| Gate | Present evidence | Owner go/no-go criterion |
| --- | --- | --- |
| Stage A offline design | PASS: source matrix, explicit unknowns, offline tests | Review this draft and proposed clock/resource limits. |
| Current venue/spot/USD identity | HOLD: XRP/SOL current keys unknown; BTC example only | Authorized AssetPairs evidence reconciles exact keys/base/quote/asset class and request aliases for each symbol. |
| Current observed schema | HOLD: no live capture; expanded child schema unavailable | Authorized public capture matches all eight fields/types/units; undocumented differences refuse and return to review. |
| Runtime diagnostic safety | HOLD: no transport or production clock/identity gate implemented | Separate reviewed optional tool enforces total deadlines, bounds, no retries, time/commitment consistency and safe summary schema. |
| Immutable capture evidence | HOLD: summary design only | Reviewed exact commit + fixed context/policies, bounded retained summary, eligible references; no raw/future data leak or authenticity overclaim. |
| Complete closed 1h OHLCV | Offline PASS only | Each symbol has >=21 consecutive eligible bars, finite correct values, no duplicates/gaps/repair, <=3h age at frozen cutoff and full no-lookahead checks. |
| Offline and manual validation | 84 local tests PASS; CI/live UNVERIFIED | Pinned manual offline Actions run passes, then separately authorized manual diagnostic passes all three symbols; any single-symbol failure keeps overall readiness HOLD. |
| Operational Test Mode | NOT APPROVED | Separate explicit owner/BOSS AI decision after evidence; data success never self-promotes. |
| Future candidate/strategy scope | Not implemented | 0-3 is a maximum, no forced minimum/signals. Any ranking or WATCH/ENTRY READY design requires separate approval/tests. |
| Later paper-trading acceptance | Deferred, not implemented or authorized | Separate requirements, simulated-only safeguards and owner acceptance; paper/live orders cannot follow from this issue. |

The working observer remains unchanged. Its close-only results are not a
substitute for these gates. Legitimate no-trade gaps or stricter R3 input/512-row
limits can produce HOLD without a software defect; do not weaken validation to
obtain a PASS. No profitability, market performance or vulnerability clearance.

## 8. Executed offline evidence and final recommendation

Local Python **3.12.14**, no installations, deterministic existing synthetic
fixtures only. From the staged repository root:

```text
python -B -m unittest discover -s tests -p test_kraken_live_readiness_contract.py -v
Ran 8 tests in 0.012s
OK

python -B -m unittest discover -s tests -v
Ran 84 tests in 0.196s
OK
```

All **76 existing + 8 new** unittest methods passed. New coverage: conservative
cutoff examples, first-request clock-model refusal, hour-crossing warmup risk,
changed/display aliases, row/count changes, isolated BTC success/XRP alias/SOL
API failure, and complete refused-result canonical invariance after future append.
Existing tests cover malformed response, precision, stale/gap/duplicate/order,
JSON bounds and import/execution network suppression. No coverage percentage or
production clock/transport correctness is claimed.

Twenty existing Python/fixture files match base Git blob hashes. Only this new
document and `tests/test_kraken_live_readiness_contract.py` are changed paths.
All runtime source, prior tests/fixtures, workflows and dependencies remain
byte-identical in the proposed Git diff. Original BOSS documentation/test code
under repository MIT license; no vendor implementation/data archives copied.

**Recommendation: REVIEW this Stage A work; continue HOLD for live diagnostic and
Operational Test Mode. Smallest safe owner action:** inspect the exact draft
commit, then authorize a separate pinned **offline** Actions check for the eight
new tests and full suite. Next implementation/network authorization must be
separate and specific; none is inferred from this report or a green run.

No live network test, workflow launch, observer change, merge, issue closure,
trading activation, private data, secrets, orders, derivatives, paid services,
ZUMERAVO access or VM deployment. **STOP FOR OWNER AND BOSS AI REVIEW.**
