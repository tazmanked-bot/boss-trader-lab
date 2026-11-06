# BOSS TRADER — Gated public probe design 013

**Verdict: HOLD. No real transport factory, clock provider, activation or live
workflow is implemented. REVIEW the evidence and offline correction proposal.**

Authorization: [Issue #20](https://github.com/tazmanked-bot/boss-trader-lab/issues/20).
Baseline: `11819e4bb3c2e666959fddfb2f1c2cec964e8da4` (owner's PR #19 integration).
Review/retrieval: **2026-11-06 UTC**. Branch: `research/issue-3-public-probe-design`.
Authoritative [diagnostic 012](BOSS-TRADER-KRAKEN-DIAGNOSTIC-012.md) and
[readiness 011](BOSS-TRADER-KRAKEN-LIVE-READINESS-011.md) were read fully.
All their live/operational HOLDs remain. Only this report and a new offline test
file are added; all runtime behavior, earlier tests, fixtures and workflows stay
byte-identical. No existing evidence is rewritten or issue closed.

## 1. Acceptance criteria assessed before implementation

| Gate | Necessary evidence | Result |
| --- | --- | --- |
| No request without separately recorded future owner approval | Default execution stays disabled; no self-approved flag or environment bypass | PASS existing disabled behavior; future approval mechanism absent |
| Total deadline / no start after expiry | Pre-launch/worker checks, finite startup, DNS/connect/read deadline, kill and verified reap on target platform | **FAIL pre-launch ordering in deterministic example; HOLD real bound** |
| Bounded real parser allocation | Cap status/headers before materialization, body cap+1, bounded framing and no decompression | **FAIL if stdlib response is merely plugged into current post-parse guard** |
| Terminal routing/451 and stop on failure | No retries/rerouting; no further symbol attempts after first failed future probe stage | **Not met by existing offline isolation policy**; separate future coordinator needed |
| Trusted UTC and frozen cutoff | Independent initial clock bound, monotonic checks throughout capture, Date consistency, no forward shift | Local arithmetic PASS; initial clock/hosted runner evidence **UNKNOWN/HOLD** |
| Exact current spot USD identities/schema | Official documentation distinguished from actual authorized captures; identity before OHLC | Documentation partial; real identities/schema **UNKNOWN/HOLD** |
| Safe environment, code and workflow identities | Exact reviewed commit, runtime/image evidence, permitted direct route, no active live dispatch now | Existing source pins known; future environment/activation **HOLD** |

Because essential gates fail or remain unverified, Issue #20's conditional
permission to implement a real factory is **not satisfied**. Adding one now
would contradict its fail-closed instruction. The implementation delivered here
is offline review/characterization code only, not a new network path.

## 2. Source anchors and evidence limits

All retrieval below was source/document research, not an exchange test. No
api.kraken.com request or diagnostic DNS/connection/TLS/time-service operation
was executed.

| Source | Exact anchor / verified fact | Limit |
| --- | --- | --- |
| [Kraken OHLC](https://docs.kraken.com/api-reference/market-data/get-ohlc-data) | Response example; Query Parameters pair/interval/since/assetVersion; opening description of current final row and 720-row maximum | Documentation/example only. Supports 60-minute requests and internal/display distinction, not current exchange behavior. Expanded response children unavailable through reader. |
| [Kraken AssetPairs](https://docs.kraken.com/api-reference/market-data/get-tradable-asset-pairs) | XXBTZUSD example links XBTUSD, XXBT and ZUSD; asset-class and naming sections | BTC example; current XRP/SOL result keys remain UNKNOWN. |
| [Kraken OHLCVT support](https://support.kraken.com/articles/360047124832-downloadable-historical-ohlcvt-open-high-low-close-volume-trades-data) | Definitions / About the data: quote prices, base quantity volume, missing no-trade intervals | CSV is not REST schema; never fill hours to satisfy the registry. Page updated 2026-11-02; retrieved 2026-11-06. |
| [Pinned diagnostic, _exchange](https://github.com/tazmanked-bot/boss-trader-lab/blob/11819e4bb3c2e666959fddfb2f1c2cec964e8da4/research/kraken_spot_diagnostic.py#L159) | getresponse precedes getheaders/8192-character check; fixed paths/TLS policy, body limit+1, no real constructor | Injected protocol, not real header preallocation enforcement. |
| [Pinned supervisor](https://github.com/tazmanked-bot/boss-trader-lab/blob/11819e4bb3c2e666959fddfb2f1c2cec964e8da4/research/kraken_spot_diagnostic.py#L279) | job_factory and job.start run before first post-start deadline check | Rejecting late results does not prevent expired startup. |
| [Pinned clock](https://github.com/tazmanked-bot/boss-trader-lab/blob/11819e4bb3c2e666959fddfb2f1c2cec964e8da4/research/kraken_spot_diagnostic.py#L338) | trusted flag, frozen guarded as_of, relative drift checks | Flag is an injected assertion, not runner UTC attestation. |
| [Pinned offline coordinator](https://github.com/tazmanked-bot/boss-trader-lab/blob/11819e4bb3c2e666959fddfb2f1c2cec964e8da4/research/kraken_spot_diagnostic.py#L447) | Ordinary HTTP_REFUSED does not join the global stop set | Valid existing offline symbol isolation; not the proposed all-stop live policy. |
| [Owner's PR19 launcher](https://github.com/tazmanked-bot/boss-trader-lab/blob/11819e4bb3c2e666959fddfb2f1c2cec964e8da4/.github/workflows/launch-offline-kraken-diagnostic-pr19.yml) | ubuntu-24.04, Python 3.11.17; immutable checkout 4e4f184f4847e84bafcd3e1ea7d7eaad6f466419, SHA-pinned actions, manual-only offline tests | This PR is not tested by that old checkout. YAML is not a new run/log or clock/deadline measurement. |

CPython primary-source review (retrieved 2026-11-06 UTC):

- Python **3.11.17** at [e6392eb68a39cef49c9fe6431253050caa17a426](https://github.com/python/cpython/blob/e6392eb68a39cef49c9fe6431253050caa17a426/Lib/http/client.py#L225),
  `_read_headers` and `HTTPResponse.begin` (line 359), blob
  `a0e3260a08eabfdf7d2bf1aea24c61174570ba4d`.
- Python **3.12.14** at [2abcf904b8dac8c999d2b3aac76681abb333798a](https://github.com/python/cpython/blob/2abcf904b8dac8c999d2b3aac76681abb333798a/Lib/http/client.py#L225),
  same header collection before parse_headers (line 365), blob
  `3a9eb406d62021476b7e7b07533e11bff5e5666d`.
  Local installed http/client.py matched this exact Git blob hash.
- [HTTPSConnection.connect, 3.12.14](https://github.com/python/cpython/blob/2abcf904b8dac8c999d2b3aac76681abb333798a/Lib/http/client.py#L1517)
  wraps the socket with the supplied context and server_hostname. HTTPConnection
  connects using socket.create_connection; ordinary construction is not an HTTP
  transaction. Default constructor has no proxy-environment routing logic.

Both inspected versions have finite `_MAXLINE=65536` and `_MAXHEADERS=100`;
that does **not** establish the desired 8 KiB aggregate allocation bound. Joining
header bytes and creating email header objects adds memory beyond raw bytes.
This is a scope mismatch, not a claim that stdlib parsing has no limits or a
published vulnerability. No CPython implementation was copied into this repo.

## 3. Independently reproduced blockers

**B1 — deadline ordering, FAIL for a live pre-start guarantee.** A deterministic
job factory advances the injected clock from 0 to 11s. `_supervise` still calls
job.start, then sees expiry, kills and reaps. No network call occurs in the test;
the verified result is the ordering flaw, not an observed real late request.
Another test advances time inside start and proves the parent checks only after
start returns. Late-result rejection and kill/reap work, but cannot preempt a
blocked factory/start. Parent descheduling, native allocation/fork stalls,
SIGKILL delivery and uninterruptible kernel state remain target-platform HOLDs.

Required future correction: deadline check before launch **and in the child
before connection/DNS**, with validated common monotonic deadline, bounded
startup/handshake and verified process cleanup. A pre-start check alone does not
prove startup is interruptible. A larger safety supervisor/process-group design
would itself need review and tests. Do not replace these requirements with a
thread, socket timeout or unjoined background request. No such correction is
made to the existing offline code under this issue.

**B2 — header limit timing, FAIL for simply attaching the real stdlib client.**
The new memory client invokes the actual `HTTPResponse.begin` over BytesIO.
Two 6000-character headers are parsed before `_exchange` returns CONTENT_INVALID.
The counted stream has consumed >12000 bytes before the diagnostic's header
check; no body read occurred. This reproduces a preallocation gap independently
of TLS/network behavior. Existing fake headers alone did not test that boundary.

Required future correction: reviewed bounded status/header reader **before**
stdlib header object materialization, with aggregate raw-byte, count and line
limits, including interim responses and framing/trailers. Avoid process-global
monkeypatches to private http.client constants. Compression stays rejected.
Either implement and test bounded chunked framing or explicitly refuse it; do
not rely only on a decoded-body cap for framing allocation. A compatible real
parser/factory is not responsibly supported yet and is not implemented here.

**B3 — stop policy, additional future acceptance gap.** With BTC AssetPairs 451,
the unchanged offline coordinator still attempts XRP/SOL, for five total mock
requests. It never retries BTC or follows another route, and overall stays HOLD.
That respects existing offline behavior but is unsuitable for the proposed
owner-approved probe's **global stop on first failure**. A separate coordinator
must preserve partial safe evidence while preventing every subsequent attempt.

**B4 — UTC attestation, HOLD.** A constant initial one-day offset is accepted when
the injected clock asserts trusted=True; subsequent relative drift is detected.
This is not evidence of a real bad clock. It proves the flag and guard cannot
establish initial absolute UTC accuracy. HTTP Date is coarse, source-controlled
and observable only after a future authorized request; it cannot authorize the
first request. No sufficiently trusted local clock attestation was provided.

**B5 — actual runner/runtime, HOLD.** Local execution was CPython 3.12.14 on
Linux 6.18.57 x86_64/glibc 2.41, not a measured GitHub Ubuntu job. The owner's
launcher selects 3.11.17, unavailable locally; its source was reviewed but not
executed here. An ubuntu-24.04 label does not freeze image/kernel/scheduler/CA/
OpenSSL identity or establish synchronization and timing bounds. No new workflow
run/log is inferred from the user's prior success or from source inspection.

## 4. Exact conditional real factory design — NO implementation

Only after B1-B5 and owner acceptance are resolved, a candidate could wrap direct
`http.client.HTTPSConnection` with the existing strict client TLS context,
hostname/CERT_REQUIRED checks, fixed host `api.kraken.com` and port 443. The
constructor-only test confirms the context remains attached and proxy variables
do not configure a tunnel; **it performs no connect/request/handshake**. That
supports a design choice, not certificate validation or real compatibility.

Do not use a general URL opener, cookie/auth session, proxy, custom tunnel,
mirror, redirect or retry. Never disable certificate/hostname checks or add an
insecure fallback. Detect proxy/mandatory-routing-policy conflicts **before DNS**
and return POLICY_BLOCKED rather than silently ignoring managed controls or
unsetting variables. Direct-client proxy independence is not permission to bypass
a managed route. Current task networking does not establish Kraken permission or
reachability; no egress test or policy change was performed.

Exact proposed request surface (no executable live commands supplied):

| Stage | Public endpoint | Fixed parameters / gate |
| --- | --- | --- |
| Identity, once per symbol | https://api.kraken.com/0/public/AssetPairs | pair=XBTUSD/XRPUSD/SOLUSD, aclass_base=currency, info=info; no assetVersion switch. Exact base/quote/classes/key/altname/wsname/status checks must pass first. |
| OHLC, at most once after that identity | https://api.kraken.com/0/public/OHLC | same verified pair; interval=60; since=frozen_as_of-86400. No extra parameters or body. Exact OHLC key must match verified metadata. |

Only BTC/USD, XRP/USD, SOL/USD; at most three identity + three OHLC GET attempts,
sequential and manual one-shot. Any transport/API/identity/schema/clock/commitment
failure, including 451 or hard routing error, **ends the whole invocation**.
No account/private endpoints, positions, orders, credentials, retries, discovery
of replacement aliases, stablecoin substitution or data fallback. Previously
collected valid evidence stays explicitly partial, overall HOLD.

The worker must enforce the corrected total 10-second contract independently of
socket timeouts, with verified termination/reap; inability to establish that
contract is NO-GO. Body remains <=262144 decoded bytes via limit+1; unsupported
compression refuses. Strict JSON/UTF-8, bounded headers/framing and safe evidence
must pass adversarial tests before any provider exists in an executable path.

Clock proposal retains initial paired UTC/monotonic capture, independently
supported <=2s absolute uncertainty, conservative two-second guard and common
hour-aligned as_of frozen before requests. Check every capture against initial
and previous pairs, <=1s drift discrepancy, <10s elapsed, canonical Date within
the reviewed bounds, and current-row commitment/time consistency. No time-service
query or treating cursor last as proof of closure. If accuracy cannot be attested,
CLOCK_UNVERIFIED and **zero requests**, even if an owner approved a different gate.

Use unchanged bridge/registry as_of projection, 21 consecutive eligible hourly
bars, finite exact-consistent OHLCV, <=3h per-symbol age and all existing refusal
semantics. Never sort/repair/fill gaps, accept eligible corruption or leak future
values into summaries/hashes. New outer safety gates cannot auto-promote data
checks to readiness, signals, WATCH, ENTRY READY, simulation or order authority.

## 5. Manual workflow and approval design — absent/NO-GO now

No workflow is created or changed, not even an input-toggle live dispatch. Existing
CLI remains AUTHORIZATION_MISSING regardless of environment flags. A future
workflow is a separate reviewable artifact: workflow_dispatch only, contents:read,
SHA-pinned reviewed actions, exact immutable checkout/HEAD assertion, explicitly
chosen tested Python, short job/worker limits, concurrency one, no push/PR/cron/
workflow chaining, no raw payload artifact or external telemetry. A job timeout
is not a replacement for each request's deadline.

The readiness 011 action pins may be proposed only after renewed owner review;
their historical resolution is not security clearance. Choose and test the
actual Python/image combination instead of assuming this local run reproduces
the 3.11.17 Ubuntu launcher. Record non-secret image/kernel/OpenSSL/CA/runtime
identities and clock attestation without dumping environment or secret files.
Only the minimal ephemeral read token for checkout may be used, with
persist-credentials:false; no stored secrets/tokens, auth or token passed to
diagnostic workers. No new paid resource authorization or billing guarantee.

An approval cannot be a self-set boolean, --live argument, branch text, untrusted
PR content or a successful offline run. It must be an independently recorded
owner decision tied to the exact **future corrected commit**, approved environment,
request set, one invocation and expiry. The gate must refuse without that record;
the approval verification mechanism itself needs separate review. This report
does not implement it or create an actionable request path.

### Separate future owner consent checklist (NOT an approval request now)

- [ ] Exact corrected future code commit recorded and independently reviewed;
  current draft documentation/test commit does not contain a live provider.
- [ ] B1-B5 closed with source-anchored tests and target-platform evidence;
  strict deadline and allocation requirements unchanged unless owner separately
  revises the specification through explicit review. No silent relaxation.
- [ ] Approved safe execution environment and permitted direct Kraken route;
  attested initial clock and verified cleanup. Any missing evidence is NO-GO.
- [ ] Only the two public HTTPS endpoints above; BTC/XRP/SOL SPOT USD;
  at most 3 AssetPairs + 3 identity-gated OHLC GET attempts, total deadlines/caps,
  global stop on first failure, no retries/proxy/mirror/redirect/substitution.
- [ ] No credentials, account endpoints, positions, orders, fills, trading,
  strategies, ranking, signals, paper execution, monitoring or schedules.
- [ ] Manual single invocation only, exact expiry/run identity and named owner
  approval recorded separately; no automatic next run or Operational Test Mode.
- [ ] Bounded canonical summaries only: safe request metadata, capture/cutoff/
  policies/identity/clock/refusal status and eligible evidence references; no raw
  captures, headers beyond sanitized Date, raw response hashes or future values.
- [ ] Zero paid resources: owner confirms an existing allowed free quota;
  stop if execution would require paid infrastructure/API or other authorization.
- [ ] Explicit decision **GO / NO-GO**, owner identity and date recorded.

**Current consent record:** decision=NO-GO; future_live_commit=NOT_SET;
clock/environment_attestation=ABSENT; real_provider=ABSENT; owner_live_approval=NONE.
Even checking this document into the repo grants no network authorization.

## 6. Offline implementation and exact test evidence

New file: `tests/test_kraken_public_probe_review.py`. Its memory adapter uses the
actual stdlib HTTPResponse parser over BytesIO. It cannot open a connection; all
socket/create_connection/getaddrinfo/urlopen operations are blocked and asserted
**not called** per new test. The real HTTPSConnection constructor is inspected
without connect/request. No external implementation was copied or installed.

Local CPython **3.12.14**; deterministic injected clocks, no installations:

```text
python -B -m unittest discover -s tests -p test_kraken_public_probe_review.py -v
Ran 12 tests in 0.450s
OK

python -B -m unittest discover -s tests -v
Ran 129 tests in 3.499s
OK
```

All **117 baseline + 12 new** methods passed, no skips in this environment.
New tests cover real in-memory parser request/response flow, header-allocation
counterexample, Content-Length and chunked decoded body cap+1, redirect/compression
refusal without body read, malformed/duplicate/nonfinite JSON, TLS constructor
policy/proxy independence, expired-start/startup counterexamples, 451 policy
gap, identity-first alias refusal, initial clock-vs-drift distinction and default
zero requests. Baseline tests continue to cover blocked fake DNS/connect/read
workers, kill/reap, skew/Date/races and full no-lookahead/refusal invariance.

**Passing counterexample tests document failed live acceptance conditions.**
They assert the reproducible current behavior to preserve evidence, not endorse
it or imply those blockers are fixed. The report's FAIL/HOLD verdicts remain
despite the green suite. No CI result, live aliases, real TLS/DNS, 3.11 execution,
hard timing guarantee, vulnerability clearance or profitability is claimed.

Twenty-four existing Python/fixture files matched baseline Git blob hashes.
Only this new document and the new review test file belong in the commit.
All existing source, earlier tests/fixtures, workflow/dependency files and main
remain unchanged. Original BOSS research/test code under repository MIT; CPython
source was reviewed by link/hash, not vendored.

**Smallest safe owner decision:** accept continued live HOLD and authorize a
separate **offline correction review** for the expired-start and preallocation
gaps plus a distinct global-stop coordinator. Independently verify this draft
with an owner-run offline workflow pinned at its exact head if desired; old
launchers pin prior commits. Do not approve a real probe yet. A future consent
request is eligible only after the above blockers and platform/clock gates close.

No real request, workflow dispatch/activation, observer/scanner/registry/bridge/
offline-runtime change, merge, issue closure, trading, futures/shorts/leverage,
paid API, ZUMERAVO access or VM migration. **STOP FOR OWNER AND BOSS AI REVIEW.**
