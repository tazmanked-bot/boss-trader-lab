# BOSS TRADER — Offline correction review 014

**Recommendation: REVIEW the isolated B1–B3 prototypes. Live use remains HOLD;
B4/B5 are NO-GO on available evidence. No hard kernel timing claim.**

Authorization: [Issue #22](https://github.com/tazmanked-bot/boss-trader-lab/issues/22).
Findings source: **unmerged PR #21**, exact
[`b70127b4fe3cafad1db2cbf4942fd517f5cc27be`](https://github.com/tazmanked-bot/boss-trader-lab/blob/b70127b4fe3cafad1db2cbf4942fd517f5cc27be/docs/BOSS-TRADER-KRAKEN-PUBLIC-PROBE-013.md).
That report was read fully; it is not assumed to exist in main.
Branch base: `eb86fc94617770c810ebb80c7b7b56cdae61c4c3`, observed main.
Protected runtime matches the PR19 baseline
`11819e4bb3c2e666959fddfb2f1c2cec964e8da4` byte-identically.
Date: **2026-11-06 UTC**. Branch: `research/issue-3-offline-probe-corrections`.

## 1. Scope and result matrix

Only isolated optional source/tests and this report are proposed. No real client,
socket/HTTPS/DNS operation, actual clock provider, attestation verifier, workflow,
trading path or activation is added. Existing offline coordinator behavior is
unchanged. All prototypes return overall HOLD and require trusted injected test
dependencies; arbitrary injected Python code is not a sandboxed capability.

| Blocker / safeguard | Proposed correction and executed evidence | Verdict |
| --- | --- | --- |
| B1: expired before construction/start | Validate absolute deadline before factory and again before start; 11s factory delay never starts a job | **PASS offline regression** |
| B1: slow start / child entry | Start paused, ready/release/cancel gates; child checks same deadline before injected pre-DNS action | **PASS offline**, including actual local child release-after-expiry |
| B1: wait/edge/kill/reap | Deadline at equality refuses, never-ready bootstrap/action killed and reaped, unreaped returns failure | **PASS offline mechanism** |
| B1: real 10-second wall-time guarantee | Factory/start/kernel scheduling and SIGKILL/reap remain non-preemptible/uncertain in Python | **HOLD**, not fixed by a green test |
| B2: bounded status/header parsing | One-byte header reads, 8192 aggregate raw bytes, 1024-byte lines, 64 fields, no library header object materialization | **PASS for declared memory-fixture profile** |
| B2: framing/body | Content-Length only, 262144-byte body; reject ambiguous/chunked/trailer/interim/compressed/unsupported input | **PASS fail-closed profile**, not general HTTP compatibility |
| B2: actual socket/client preallocation | No real stream adapter; complete input fixture is already caller-owned memory | **HOLD**, no live provider implemented |
| B3: explicit GLOBAL STOP | Separate coordinator stops after first failing stage; no subsequent symbols or retry calls | **PASS offline control-flow contract** |
| Existing offline isolation | Original diagnostic/per-symbol behavior preserved, PR21 counterexamples retained | **PASS preservation**, original live blockers not silently edited away |
| Unsafe-design sensitivity | Same assertions reject disabled deadline guards, widened parser limits, disabled global STOP | **PASS**, expected assertion failures are explicitly tested |
| B4: trusted initial UTC <=2s | No independently trusted, current, job-bound uncertainty evidence available | **HOLD / NO-GO** before any first request |
| B5: intended Ubuntu/Python/runtime | No new hosted-runner execution or clock/kernel/CA/cleanup attestation | **HOLD / UNKNOWN**, local execution only |
| Default CLI/import safety | Both CLIs AUTHORIZATION_MISSING, requests=0, exit 2; import reload tested with network blocked | **PASS**, no activation path |

No unresolved failing unittest remains. PASS labels are confined to the specified
offline model; they do not close live readiness, authenticate a market source or
provide vulnerability/profitability clearance.

## 2. Evidence lineage and exact counterexample comparisons

The baseline main tree contains the owner's PR21 **launcher**, but not PR21's
new report/test file. The exact original `tests/test_kraken_public_probe_review.py`
is included unchanged as a new file here to retain the independently observed
counterexamples alongside proposed corrections. Its source is the PR21 commit
above, Git blob **`ef73cb0c7a63c22d71dd0e500eaf241e19c07823`**; local bytes matched.
This does not merge PR21 or rewrite its evidence.

| PR21 counterexample | Correction regression / sensitivity evidence |
| --- | --- |
| Slow factory reaches 11s, legacy still starts then rejects | `test_slow_factory_cannot_launch_after_expiry_pr21_b1` requires TIMEOUT, no start/release/action. The same contract assertion fails when `_active` is intentionally disabled. |
| Legacy start checked only after return | Slow corrected start remains paused, no release, kill/reap; actual child receives an expired release and never enters its action. No claim native start is preemptible. |
| Stdlib consumes >12000 header bytes before post-parse guard | Same two 6000-character fields now refuse at the 1024-byte line limit, long before 12 KiB. Aggregate test detects byte 8193. Widening only prototype limits makes the same refusal assertion fail. |
| BTC 451 leaves five legacy mock attempts | Separate global coordinator halts at one stage for 451/429; source API/alias cases likewise stop. Patching its stop predicate false yields six calls and fails the same one-call contract assertion. |
| trusted=True cannot establish initial absolute UTC | No attestation authority is invented; B4 remains NO-GO. Relative monotonic examples do not establish UTC accuracy. |

Original source anchors remain:
[legacy supervisor](https://github.com/tazmanked-bot/boss-trader-lab/blob/11819e4bb3c2e666959fddfb2f1c2cec964e8da4/research/kraken_spot_diagnostic.py#L279),
[legacy post-parse headers](https://github.com/tazmanked-bot/boss-trader-lab/blob/11819e4bb3c2e666959fddfb2f1c2cec964e8da4/research/kraken_spot_diagnostic.py#L159),
[legacy offline coordinator](https://github.com/tazmanked-bot/boss-trader-lab/blob/11819e4bb3c2e666959fddfb2f1c2cec964e8da4/research/kraken_spot_diagnostic.py#L447).
PR21's pinned CPython 3.11.17/3.12.14 header-order source review remains evidence,
not vendored code or a claim that standard-library parsing is wholly unbounded.
The old counterexample tests still pass by documenting old behavior. They have
not been replaced with optimistic correction assertions.

## 3. B1 design, limits and real local fake-worker evidence

`research/kraken_probe_corrections.py` supplies `supervise_offline` and
`GatedProcessJob`. Before factory creation, before start, after start, before
release and around completion, the parent checks an injected monotonic absolute
deadline. Provided deadlines may not exceed ten seconds from entry; already
expired deadlines create no job. Equality is expired. Reversal/invalid clock
values refuse. Slow factory construction gets an unstarted close, never launch.

A worker starts paused and reports ready only after its initial checks/bootstrap.
It waits for an explicit parent release; cancellation is signaled before kill.
The child receives the same absolute deadline and clock domain and independently
checks cancellation/time immediately before the injected operation and after it.
This models pre-connection/DNS entry without implementing any network operation.
Results are fixed integer status codes, not raw captures, exception text, pipe
messages or arbitrary serialized objects.

The default local-process prototype requires POSIX fork, a single Python thread
and an explicitly shared test clock. This assertion is a test contract, not
attestation. Tests use an actual shared RawValue, not a forked private clock copy.
Parent polling is <=10ms; expired or failed workers are killed and get a separate
250ms reap allowance. Unreaped/partial-start cleanup failure is WORKER_UNREAPED,
never success. Every result stays HOLD, even COMPLETED.

Real local child tests demonstrate: (a) expiry after ready but before release
prevents action entry; (b) blocked offline bootstrap is killed without release;
(c) blocked injected action is killed/reaped. Workers block on OS Events, not
DNS/connect/read, and parent deadlines advance deterministically when the fake
phase is reached. Local ready/exit barriers have bounded five-second test waits.
These are lifecycle/control-flow observations, **not measured 10-second real
network or worst-case kernel timing guarantees**. Prior baseline tests separately
retain fake DNS/connect/read worker cleanup coverage.

Native construction/start can still stall before Python regains control. Parent
descheduling, a check-to-operation scheduling race, uninterruptible kernel state,
clock-domain truth and kill/reap delivery cannot be bounded absolutely by these
tests. The paused child fixes premature action release; it does not make native
startup interruptible. **A strict real ten-second transport contract remains
unproven and HOLD.** No thread fallback, extra grace request, retry or alternative
route is substituted. No real provider exists to expose that uncertainty.

## 4. B2 strict raw fixture profile

`parse_http_fixture` accepts only the module's `MemoryReader` over existing exact
bytes; it cannot consume a socket/file or arbitrary read adapter. No HTTP client
or general library header parser is invoked. The fixture already exists in caller
memory: the prototype limits **its own parsing/accumulation**, not upstream
allocation of a real network buffer. A real bounded stream driver is absent.

- Exact HTTP/1.1, status 200. Interim 1xx/upgrade responses refuse immediately;
  redirects and HTTP errors refuse rather than being followed or retried.
- Status/header raw bytes share an 8192-byte aggregate budget including CRLF and
  the blank terminator. Each line <=1024 bytes including CRLF, fields <=64, names
  <=64 bytes. Reads are one byte until the header phase ends. Limit+1 detection
  consumes byte 8193 or line byte 1025 without appending it to accepted content.
- Reject bare LF, broken CRLF, obs-fold, control/non-ASCII field values, malformed
  names and duplicate fields. Unknown syntactically valid fields are counted and
  discarded, not treated as authority. A syntactically valid extra header cannot
  be identified as malicious intent from bytes alone; duplicate authoritative
  framing injection is refused, and no untrusted header is reflected into a request.
- Require application/json (optional UTF-8 charset), canonical Date and canonical
  nonnegative decimal Content-Length <=262144. Require exact body length; premature
  EOF, extra/trailer bytes and pipelining refuse. Total fixture wire <=270336 bytes
  (body plus headers); no implicit EOF-framed body.
- Reject **every Transfer-Encoding**, including valid chunked responses. TE+CL is
  AMBIGUOUS_FRAMING. No chunk/trailer parser or decompressor exists. All non-identity
  Content-Encoding refuses. This narrow profile deliberately trades compatibility
  for refusal; unsupported legitimate server behavior stays HOLD.
- Body reads <=4096 bytes/call, bounded accumulation, strict UTF-8 and the unchanged
  diagnostic's duplicate/nonfinite/overflow JSON checks, object envelope only.
  Parsed payload is internal fixture data with repr disabled, not a public log.
  No raw exception/body/header logger or automatic evidence writer is added.

Header structures are bounded by byte/line/count rules before storage; raw-byte
caps are not a claim that all Python object/JSON heap overhead fits inside 8 KiB.
Exact 262144-byte JSON, cap+1, aggregate/line/count limits, framing ambiguity,
interim responses, CRLF cases, chunked/trailers, EOF and UTF-8 are tested.
Mutation tests widen **only this prototype's** limits; no stdlib parser globals
or TLS configuration are monkeypatched to weaken them.

**Assessment:** the declared in-memory profile has offline evidence for the B2
allocation fix. It is not a general HTTP implementation, a proven real socket
driver or tested Kraken compatibility. Real provider remains absent/HOLD.

## 5. B3 explicit global-stop contract

`coordinate_global_stop_offline` is a new, separate control-flow prototype.
Its trusted injected evaluator returns a typed stage result after an offline
IDENTITY or OHLC evaluation. It is called once per stage, in fixed BTC/XRP/SOL
order. The first failure/unknown result/exception ends the invocation immediately;
there are zero subsequent stage calls, no retries or reroutes. OHLC cannot be
called by this controller before that symbol's identity stage passed.

Tests cover 451/429 via parsed response status, API errors and alias failures via
the unchanged identity checker, and injected identity/clock/TLS/network/timeout/
unreaped failures. Partial BTC evidence can remain in the fixed audit list, but
XRP failure never leads to SOL evaluation. Even six STAGE_PASSED results yield
overall HOLD. Worker COMPLETED is not accepted as a stage-verification result.

This coordinator proves call sequencing, **not** real identity, clock attestation,
transport implementation or data validation. The stage executor/integration is
not implemented, and injected callbacks are trusted test code. Existing
`run_offline` per-symbol isolation remains byte-identical; there is no silent
change of policy or new live mode. All future integration needs its own review.

## 6. B4 decisive initial-clock assessment — NO-GO

No actual trusted initial UTC evidence was supplied or obtained. A wall/monotonic
pair checks relative progression only; HTTP Date arrives after a request and is
coarse/source-controlled. Neither can authorize the first request or prove
absolute UTC uncertainty <=2 seconds. No external clock/time-sync service was
called, and no boolean/caller assertion is upgraded into proof.

Before any future first request, require independently verifiable evidence of:

1. A trusted evidence authority/provenance and verification mechanism approved by
   owner/security review, bound to the actual job/host/image and reviewed commit.
2. A quantified UTC error/uncertainty bound <=2s at capture, including calibration
   age, drift, timestamp sampling skew and any step/holdover uncertainty. Generic
   "synchronized" status or an unsigned wall-clock reading alone is insufficient.
3. A validity horizon covering every permitted request, reliable freshness and
   rollback/reboot/domain checks. Evidence cannot be self-dated solely by the same
   unverified UTC clock it is supposed to attest.
4. A paired monotonic anchor in the same domain across parent/child, maintained
   relative checks, two-second conservative cutoff guard and no forward cutoff
   adjustment. Evidence failure/revocation/expiry/uncertainty means CLOCK_UNVERIFIED
   and zero requests, regardless of any separate owner authorization.

The intended generic hosted-runner interface has **no such attestation evidence
in this task**. Do not assume NTP configuration, HTTP Date, GitHub job timestamps,
green tests or a trusted=True flag closes that gap. It is not established that a
provider is impossible in principle; it is unavailable/unverified here. No
attestation verifier or live clock provider is implemented. **B4 remains NO-GO.**

## 7. B5 bounded offline runner plan — no execution/guarantee claimed

Observed locally: CPython **3.12.14**, Linux **6.18.57 x86_64/glibc 2.41**, OpenSSL
**3.5.8 (25 Aug 2026)**. Python 3.11 was unavailable; no installation attempted.
This is not GitHub-hosted Ubuntu evidence.
The [existing PR21 launcher](https://github.com/tazmanked-bot/boss-trader-lab/blob/eb86fc94617770c810ebb80c7b7b56cdae61c4c3/.github/workflows/launch-offline-public-probe-pr21.yml)
selects ubuntu-24.04/Python **3.11.17**, but checks out **b70127b...**, not this
correction head. Reading YAML is not an executed runner test, new CI log or proof
that PR21 is merged. No workflow was changed, dispatched or activated here.

Proposed separate owner-approved **offline-only** check, not installed:

- Immutable correction-head checkout/HEAD assertion, reviewed SHA-pinned actions,
  actual target Python 3.11.17 pinned, contents:read, persist-credentials:false,
  no named secrets/write token, schedules, installs or diagnostic network steps.
- Record only a bounded allowlist of non-secret image version, OS/kernel/machine,
  Python/build, OpenSSL and approved system-CA-bundle identity/hash; no environment
  dump, secret file discovery, handshake, DNS or time-service query. A CA hash
  identifies local bytes, not remote TLS validity or live schema.
- Run preserved counterexamples, correction tests, full suite and both disabled
  CLIs. Block/assert zero INET/DNS/HTTP calls; test single-thread fork/shared clock,
  ready/release/cancel, expired releases, blocked startup/action and cleanup.
- Limit repetitions and child count explicitly (e.g. <=10 per phase), one job at
  a time, <=8-minute offline job, <=16 KiB summarized platform evidence, no raw
  payload artifacts. Report actual observed latencies/reap results if measured,
  never infer a hard worst-case guarantee from repetition or a green result.
- Unsupported thread/fork/clock domains, missed cleanup, hangs, unavailable runtime
  or unknown image evidence are HOLD. A runner label/action/Python pin cannot
  attest scheduler behavior, UTC accuracy or immutable host/kernel/CA state.

**Decisive assessment:** B5 remains HOLD. Target-runtime execution and the above
evidence have not occurred at this head; even an eventual offline PASS would not
close B4 or prove a hard real-transport bound. No live provider should be enabled
to compensate for missing clock/runner guarantees.

## 8. Exact executed tests, inventory and smallest owner action

Commands from staged repository root, stdlib only, no installs:

```text
python -B -m unittest discover -s tests -p test_kraken_probe_corrections.py -v
Ran 33 tests in 0.086s
OK

python -B -m unittest discover -s tests -v
Ran 162 tests in 2.837s
OK

python -B -m research.kraken_probe_corrections
AUTHORIZATION_MISSING; requests=0; exit 2

python -B -m research.kraken_spot_diagnostic --live --authorize
AUTHORIZATION_MISSING; requests=0; exit 2
```

Counts: **117 main-baseline + 12 exact retained PR21 tests + 33 new correction
tests = 162 methods**, no skips here. Test assertions intentionally fail under
unsafe prototype variants and pass under the proposed gates; expected assertion
failures are caught as sensitivity evidence. This is not a claimed CI/coverage
percentage or market/network validation result. The 24 baseline Python/fixture
files and the retained PR21 test blob were checked byte-identically.

Four added paths only:

- `research/kraken_probe_corrections.py`
- `tests/test_kraken_probe_corrections.py`
- `tests/test_kraken_public_probe_review.py` (exact PR21 evidence copy)
- `docs/BOSS-TRADER-KRAKEN-CORRECTION-014.md`

All existing observer/scanner/registry/bridge/offline diagnostic, tests/fixtures,
workflows and dependency files remain unchanged. The prototypes use bounded
fixed status results and sanitized errors; no raw capture logging. Original BOSS
code/test data under repository MIT; no external implementation/dependency copied.

**Smallest safe owner action:** review this draft's narrow B1–B3 contracts and
authorize a separate pinned **offline** Actions check on the actual target Python
and Ubuntu runner. Keep live use NO-GO. A later decision must supply verifiable
B4/B5 evidence and independently review any integration; no real probe consent
is requested or implied by this report or an eventual green offline run.

No real Kraken request, DNS/HTTPS test, external clock query, workflow dispatch,
live provider/transport, monitoring, credential access, trading, signals, paid
service, ZUMERAVO access, VM migration, merge or issue closure.
**STOP FOR OWNER AND BOSS AI REVIEW.**
