# BOSS TRADER — B4/B5 feasibility audit 015

**Decision: REVIEW evidence and an offline runner-probe proposal. B4 strict clock
trust remains NO-GO; B5 target-runner evidence remains HOLD. No active policy change.**

Authorization: [Issue #24](https://github.com/tazmanked-bot/boss-trader-lab/issues/24).
Baseline: `c6ec0a66d06caf54c5426233b0a977513eb54e63` (owner's PR23 squash merge).
Prior [correction report](BOSS-TRADER-KRAKEN-CORRECTION-014.md) read in full.
Date/source retrieval: **2026-11-06 UTC**.
Branch: `research/issue-3-clock-runner-feasibility`; draft PR only.

Only this document, one synthetic fixture and one test file are added. No earlier
file, safety limit, workflow, runtime/provider or environment configuration changes.
No Kraken/time-provider request, diagnostic DNS/socket/TLS operation, clock-service
query, daemon activation, package installation or VM access occurred. Research
used repository and public documentation snapshots through the GitHub connector;
that source retrieval is not a provider/clock/network test. No local clock-service
manual pages were present at the three checked standard paths; this does not
prove any service/binary is absent or a clock is unsynchronized.

## 1. Necessity: data validation and execution have different claims

Hourly historical OHLCV validation needs an explicit eligible-data cutoff and
honest uncertainty about capture/closure. It does not need order placement,
execution latency, fill timing or trading authority. A declared-as_of replay can
test causal calculations entirely offline without claiming it is the current
time or that the exchange actually published those values then.

The existing strict <=2s independently trusted UTC requirement was a proposed
live preflight condition, not a prerequisite for validating a synthetic series.
Ordinary synchronized hosts can report estimates comfortably below two seconds;
documentation examples illustrate this, but they do not certify any actual host.
**A small offset estimate, an authenticated source, a trustworthy host observation
and a universal guarantee are different evidence.** Requiring independent
bounded UTC attestation and hard-real-time kernel behavior from an ordinary free
host cannot be satisfied by the evidence available here.

That does not justify silently weakening either requirement. Keep strict live
mode NO-GO. If the owner wants a more practical **data-validation-only** contract,
review the separate proposal in section 5; it remains inactive and gives no
execution or market-readiness guarantee. B1 real timing and B2 real-stream HOLDs
also remain; resolving a clock policy question cannot close them automatically.

## 2. Exact source/evidence classification

Primary documentation snapshots, not installed-version or runtime attestations:

| Source pinned on 2026-11-06 UTC | What can be inspected | What it cannot establish |
| --- | --- | --- |
| [systemd timedatectl](https://github.com/systemd/systemd/blob/7c6c0851f1dad9d61b823b2ee1a37cf494a0385d/man/timedatectl.xml#L151), commit `7c6c0851f1dad9d61b823b2ee1a37cf494a0385d` | timesync-status/show-timesync, machine-readable status; example offset, delay, root distance, packet count/frequency | Actual local service, actual synchronization or <=2s authenticated error bound |
| [systemd timesync1 interface](https://github.com/systemd/systemd/blob/7c6c0851f1dad9d61b823b2ee1a37cf494a0385d/man/org.freedesktop.timesync1.xml#L41) | Read-only RootDistanceMaxUSec, NTPMessage, frequency/poll properties | RootDistanceMaxUSec is a configuration threshold, not current measured UTC error; undocumented tuple positions must not be guessed |
| [timesyncd service](https://github.com/systemd/systemd/blob/7c6c0851f1dad9d61b823b2ee1a37cf494a0385d/man/systemd-timesyncd.service.xml#L31) | SNTP service, saved-clock behavior and synchronization marker semantics | File presence/mtime or roughly advancing reboot time is not a fresh bounded/authenticated calibration |
| [chronyc access modes](https://github.com/mlichvar/chrony/blob/c97d8083cf9a9edc64d53236565916d326d8a109/doc/chronyc.adoc#L43), maintainer documentation commit `c97d8083cf9a9edc64d53236565916d326d8a109` | Default Unix socket **then IPv4/IPv6 fallback**; -h accepts explicit local socket; numeric output options avoid name lookups | A command named tracking is not proof of zero network use or safe invocation on an unknown installation |
| [chronyc tracking](https://github.com/mlichvar/chrony/blob/c97d8083cf9a9edc64d53236565916d326d8a109/doc/chronyc.adoc#L202) and [conditional clock bound](https://github.com/mlichvar/chrony/blob/c97d8083cf9a9edc64d53236565916d326d8a109/doc/chronyc.adoc#L245) | System time vs NTP clock, last/RMS offset, skew, root delay/dispersion, leap state; formula explicitly assumes correct stratum-1 time | A statistical estimate or conditional formula is not independent authentication of UTC/server/host correctness |
| [chronyc LastRx](https://github.com/mlichvar/chrony/blob/c97d8083cf9a9edc64d53236565916d326d8a109/doc/chronyc.adoc#L391) | Daemon-reported age of last good sample | Independently attested monotonic age or truth of the source time |
| [GitHub Ubuntu2404 image README](https://github.com/actions/runner-images/blob/42d27e4a2c1232e5640a88ed42a974c8918ecd28/images/ubuntu/Ubuntu2404-Readme.md), commit `42d27e4a2c1232e5640a88ed42a974c8918ecd28` | Published image `20261026.354.1`, OS 24.04.5, kernel 7.0.0-1017-azure, systemd version; Python 3.11.17 listed in toolcache | That a particular job used those bytes, a configured time daemon, UTC error, latency bound or trusted attestation |

The image snapshot lists system Python 3.12.3 separately from cached interpreters;
the owner launcher pins **3.11.17**. A label, cache listing and successful setup
are not interchangeable with observed runtime identity. Source version must also
match the installed daemon/interface before parsing its fields. No source query
here contacted an NTP server, used a status socket or accessed an actual Debian VM.

## 3. B4: realistic local evidence and its trust ceiling

| Candidate evidence | Useful local observation | Required qualification / safe collection boundary |
| --- | --- | --- |
| Service active/synchronized, leap normal | Whether the daemon reports an acceptable state | Necessary estimate evidence, never sufficient attestation; missing/false => NO-GO |
| Chrony System time | Remaining difference between OS clock and chronyd's NTP clock | Do not substitute Last offset or RMS offset as a worst-case bound |
| Root delay/dispersion, systemd root distance | Conditional path/clock uncertainty estimate | Need units, source assumptions, package/version semantics; maximum configured threshold is not the observation |
| Last sync/sample age, update interval, skew/frequency | Holdover and growth of estimated uncertainty | Wall-only Ref time and file mtime are circular if wall time itself is in doubt; LastRx is still daemon-reported, not authenticated |
| Numeric source/auth state | Whether an expected mechanism is reported | Do not log server addresses, reference IDs, keys, cookies or raw authdata; authenticated source identity does not prove source time is correct |
| Run/commit/image/boot-domain binding | Which exact execution produced a record | A canonical hash binds bits, not truthful time; avoid persistent machine identifiers and secret discovery |

**No status command was run.** Default chronyc can use an IP socket and name
resolution; it is unsuitable under this assignment's no-network rule. A future
local collector would need an audited, explicit Unix-socket-only, numeric,
read-only path with no fallback, service start, privilege change or configuration
command. systemd status queries use local D-Bus and may involve activation; actual
installation behavior has not been proven harmless here. If a query could start
network activity or its transport is uncertain, do not run it. Use mocked outputs
or separately approved pre-exported local snapshots. Never invoke time setting,
sync enabling, online/burst/reselection or external synchronization commands.

The fixture's mock selected fields omit source addresses/identifiers. Its
normalized monotonic lease/binding/holdover fields are **test-model metadata**, not
claims that chronyc/timedatectl natively export them. Fresh acquisition of a status
snapshot is different from fresh source synchronization. Last-sync age cannot be
invented by subtracting two untrusted wall timestamps.

### Conditional arithmetic, not an attestation implementation

The test model uses exact rational nanoseconds for:

`U_model = |assumed_system_offset| + root_delay/2 + root_dispersion + sampling_margin + drift_ppb * (assumed_holdover + status_age) / 1e9`.

It conservatively rounds up. The chrony documentation's core expression is
conditional on correct reference time. Sampling/aging here are explicitly assumed
upper bounds; a production interpretation would need daemon-version review,
including possible double-counting of dispersion aging. Additional margin cannot
turn an unsupported source assumption into a guarantee.

The synthetic example yields **151100000 ns (151.1 ms)** and is numerically within
two seconds, yet the model still returns **NO_GO / LOCAL_ESTIMATE_NOT_ATTESTATION**.
Even exactly two seconds is only a modeled boundary; one nanosecond above fails
that arithmetic criterion. Missing/false/expired/bad-unit/reversed/binding-mismatch
evidence refuses. A trusted/attested/owner-approved boolean cannot produce GO.
No real evidence verifier, policy switch or collector is added.

### Binding without circular trust

A future record should identify reviewed commit and run ID, observed interpreter/
image, a per-run boot/monotonic-domain scope, selected numeric source estimates,
capture bracket, relative age provenance and validity horizon. Its expected
binding must come from an independently checked execution context, not solely
the record itself. Use monotonic elapsed time for acquisition/lease freshness;
independently justify the last-sync age and uncertainty assumptions. Do not read
credential files or persistent machine IDs to manufacture identity.

Strict current B4 additionally needs trusted calibration provenance, a verified
authority/host/source model, <=2s total uncertainty through the run, and protection
against replay, rollback, reboot/domain mismatch and step/holdover failures.
Ordinary unsigned daemon status and GitHub job timestamps do not supply this.
**No such independent attestation interface/evidence is available in this task.**

GitHub-hosted ephemeral Ubuntu may offer useful local estimates, but availability,
permissions and freshness vary by image/job. An owner-controlled future Debian VM
could expose better auditability/retention and configured local IPC, not magically
independent UTC or hard-real-time guarantees. No VM was inspected or deployed;
no package/service/configuration change is proposed for execution here.

**B4 verdict:** strict existing policy is NO-GO on both environments *on current
evidence*. This is not a proof that ordinary hosts are inaccurate or that trusted
time is impossible in principle. It is a refusal to claim the required guarantee
from estimates. No existing two-second bound is relaxed.

## 4. B5: manual offline runner probe design, not installed

This is a bounded **proposal only**. No collector executable or workflow is added,
and no GitHub dispatch or local timing benchmark was run by 015. Current local
passive facts: Python 3.12.14, Linux 6.18.57 x86_64/glibc 2.41, OpenSSL 3.5.8.
Python 3.11 was not available locally and was not installed.

The existing [PR23 launcher](https://github.com/tazmanked-bot/boss-trader-lab/blob/c6ec0a66d06caf54c5426233b0a977513eb54e63/.github/workflows/launch-offline-probe-corrections-pr23.yml)
checks out `b1572f7dff09a1cc8355ca89e067c2f1ef7bdd3d`, not this head. It specifies
ubuntu-24.04/Python 3.11.17, manual dispatch, pinned actions and eight minutes.
Its source is not a newly inspected run/log, and its earlier success cannot
establish B4 or a kernel guarantee at a different revision/image.

Proposed phase-one probe collects **no time-service status at all**:

| Area | Strict non-secret allowlist / bound |
| --- | --- |
| Runtime | Python version, OpenSSL version, OS ID/version, kernel release, machine, chosen process start method |
| Hosted image | Only specifically approved ImageOS/ImageVersion facts, bounded strings <=128 printable ASCII chars; missing facts => UNKNOWN |
| Code/run binding | Independently asserted immutable HEAD and approved run ID; no full environment, hostname/user/home/IP or persistent machine ID dump |
| CA | Omitted/null by default. Hash only after separate explicit permission for a fixed public system bundle, bounded size (proposal <=2 MiB), no certificate/key discovery or raw contents. Hash is local byte identity, not TLS success. No audit CA hash/contents were collected; existing baseline TLS-context tests may load default public roots. |
| Synthetic workers | One child at a time, <=10 samples per start/terminate/reap phase, <=30 observations; local Events/shared clocks only, no connection or transport action |
| Measurement | Monotonic startup/exit/termination/reap elapsed values, sample count and failures; observed maximum per phase, **not** universal bound |
| Failure handling | Local child readiness/cleanup waits bounded by reviewed supervisor, unreaped/timeout => stop, no additional workers. Unsupported platform/domain => HOLD. Existing 10s/250ms acceptance/cleanup semantics unchanged. |
| Output | <=4 KiB per safe summary, <=16 KiB total; fixed categories, no raw captures, server identity, environment dump or telemetry/artifacts |

Worker tests should exercise paused readiness, expired release, blocked local
bootstrap/action and reap. A hung kernel task may outlive even a parent kill;
the probe must report that limitation, not hide it behind job cancellation.
No new busy-loop benchmark, disk workload, market payload or concurrency fan-out
is necessary. Peak RSS and actual runner timing maxima remain **UNMEASURED**.

### Observed maxima: measured vs supplied synthetic observations

| Quantity | Evidence in this assignment |
| --- | --- |
| Target-runner start/terminate/reap maximum | **UNKNOWN / UNMEASURED** — no target probe dispatched |
| Local real per-operation maximum | **UNMEASURED** — whole-suite elapsed time is not worker timing evidence |
| Synthetic fixture start maximum | 8 ms from 3 supplied model observations |
| Synthetic fixture terminate maximum | 3 ms from 2 supplied model observations |
| Synthetic fixture reap maximum | 4 ms from 2 supplied model observations |

The seven model observations are explicitly synthetic, not a hardware benchmark.
Tests verify maxima aggregation, invalid/failed/excess samples and the persistent
HOLD classification. A fast observed maximum on a future job would describe
only those samples, not prove an interruptible startup or hard OS upper bound.

### Low-resource workflow proposal (documentation only)

Owner review first, then a separate manual-only workflow_dispatch artifact with
immutable checkout/HEAD assertion; reviewed SHA-pinned actions; actual approved
Python 3.11.17 from an approved image/toolcache (refuse if absent, no install or
download in the probe); contents:read; persist-credentials:false; no named secrets,
write token, schedule, on-push/on-PR or chaining; eight-minute cap and concurrency
one. The known checkout/setup action pins in the PR23 launcher are candidates for
renewed review, not automatic clearance or a reason to fetch a missing runtime.

Checkout/runner infrastructure itself communicates with GitHub; an offline
**probe** does not mean a universally disconnected hosted machine. Probe/test
code must make zero network/provider/time-service calls and block/assert INET,
DNS, HTTPS and subprocess clock queries. Do not claim Python mocks silence all
host agents/background services. If whole-host zero-egress is the requirement,
ordinary GitHub-hosted setup cannot establish that here: HOLD.

Resource envelope: <=30 sequential local worker observations, <=8-minute job,
small stdlib fixtures and <=16 KiB safe summary; no external data, packages,
paid services or extra infrastructure. Actual memory/CPU/latency are to be
observed, not guaranteed. Owner must confirm free-quota/billing conditions;
this report grants no paid-resource authorization. A Debian VM is not needed
to run an offline model and no migration/deployment is authorized.

## 5. Alternatives and separate owner decision

| Alternative | Benefit / resources | Residual risk / decision |
| --- | --- | --- |
| **Keep current strict policy** | No new code/service, no live requests; strongest refusal position | B4 independent <=2s attestation absent, real hard deadline/runner bounds unproven: **NO-GO live** |
| **Declared-as_of offline historical replay** | Existing fixtures/validator, no clock query or network; useful deterministic evidence | As_of is a research coordinate, not current UTC or authenticated publication/market freshness. **Feasible now within existing offline scope** |
| **Manual offline fact/worker probe** | Small phase-one proposal above; can establish version identity and observed lifecycle results | Cannot authenticate absolute UTC or prove universal timing. **Owner approval needed for a separate probe artifact/run** |
| **Delayed data-validation-only cutoff** | Proposed below; may make ordinary-host estimates usable for explicitly limited historical research | Changes the trust model and timeliness claim; not trading safety, no live consent. **Separate policy approval required** |
| **Future owner Debian VM** | Better operator access/retention may make local evidence easier to inspect | Unknown host/time setup, admin burden, no inherent certified UTC/kernel deadline. **Not accessed, not approved, not required as next step** |

### Proposal for review only: delayed historical cutoff

For a separately approved **data-only** policy, the owner could accept a documented
finite *environmental estimate* U and its assumptions rather than claiming
independent attestation. An illustrative coordinate is:

`as_of_proposed = floor((capture_utc_estimate - U)/3600)*3600 - 3600`.

The test-only example uses U=60 seconds and one extra closed-hour lag. Those values
are illustrative, **not** selected/authorized runtime settings or an assertion
that a real host meets 60 seconds. Evidence must still show service active, no
leap/step conflict, finite conservative uncertainty/holdover, run binding and
freshness; missing/false/expired/unknown evidence remains NO-GO. No source may be
substituted, no incomplete candles repaired, no clock advanced to obtain a PASS.

Tests show this cutoff is conservative **if** the assumed finite bound is valid.
They also show a one-day clock error defeats finite 2s/60s/1h guards plus a lag:
**delay is not a cure for unbounded unknown time.** Status estimates can be wrong;
the owner must explicitly accept or reject that residual data-only risk. Do not
present conditional mathematics as observed clock correctness.

Any report under such a future policy must label capture UTC as estimated,
declared cutoff and lag, bound assumptions/source age, and data-only scope.
The existing 21 closed bars, hourly continuity, parser limits and 3h per-symbol
age rule would remain unchanged; that age is relative to cutoff and must not be
misrepresented as present-time freshness when an additional lag is introduced.
The ten-second request bound is not revised by this proposal; its real-platform
HOLD remains. It grants no execution, entry, paper/live order or Operational Test
Mode authority. Any broader timing-policy revision would need separate review.

**No revision is implemented.** Current manual-capture-v1/two-second guard,
deadline, framing/body limits, identity/refusal rules and all prior code stay
byte-identical. The generic cutoff helper lives only in the new test module;
it cannot be selected by a runtime flag or environment variable.

## 6. Tests, evidence matrix and final recommendation

New fixture `tests/fixtures/clock_runner_evidence_015.json` is marked SYNTHETIC_ONLY.
Native-looking selected fields are mock strings; normalized evidence and worker
samples are model data. New test-only helpers are not daemon parsers, a collector,
attestation verifier or approved safety gate. They never return live GO.

| Gate | Evidence result |
| --- | --- |
| B4 conditional arithmetic, freshness/binding refusal | **PASS tests**: exact fractions, upward rounding, age/drift, exact 2s/+1ns, false/missing/expired/type/binding failures |
| B4 current independently trusted UTC | **NO-GO / HOLD**: provenance not authenticated, no actual local time-service observation or approved verifier |
| Historical cutoff logic under explicit assumptions | **PASS mathematical tests**; real source/publication/UTC correctness **UNKNOWN** |
| B5 bounded fact/sample handling | **PASS test models**: allowlist, redaction, sample caps, synthetic maxima; no actual collector or runner attestation |
| B5 actual target runtime/lifecycle maxima | **HOLD**: published image/cache documentation only; no new target run, actual maxima unmeasured |
| Hard OS timing guarantee | **Not established**; finite experiments cannot certify a universal bound |
| Existing disabled defaults/safety limits preserved | **PASS**: both CLI checks, baseline hashes, no earlier-file changes |

Actual local commands, Python **3.12.14**, stdlib only:

```text
python -B -m unittest discover -s tests -p test_clock_runner_feasibility.py -v
Ran 22 tests in 0.020s
OK

python -B -m unittest discover -s tests -v
Ran 184 tests in 2.858s
OK

python -B -m research.kraken_spot_diagnostic --live --authorize
AUTHORIZATION_MISSING; requests=0; exit 2

python -B -m research.kraken_probe_corrections
AUTHORIZATION_MISSING; requests=0; exit 2
```

**162 baseline + 22 new = 184 methods**, no skips here, no invented coverage/CI
or live endpoint claim. New tests block and assert no socket/connect/DNS/urlopen/
HTTPS constructor or subprocess service-query calls. No NTP/status command or
CA hash collection occurred; baseline TLS-context tests retain local trust-root
loading without a handshake. The existing full suite's local fake-worker lifecycle
tests remain offline; they are not a new real-time benchmark. All 27 baseline
Python/fixture files matched their Git blob hashes.

Three added paths only: this report,
`tests/test_clock_runner_feasibility.py`,
`tests/fixtures/clock_runner_evidence_015.json`. Original BOSS test models and
synthetic data under repository MIT; external documentation is cited, not code
vendored. PR21 remains distinct; no duplicate merge or evidence rewrite.

**Recommended smallest owner decision:** review and, if useful, authorize a
separate **phase-one offline-only fact/worker probe** at the exact reviewed commit
on the target runner, with no clock-service queries. This can improve B5 evidence
without pretending to close B4. Independently decide whether to retain strict
NO-GO or commission the separate data-only cutoff-policy review; do not treat
this draft or a green probe as permission to change policy or contact Kraken.

No earlier file modification, real provider/time/DNS/TLS probe, active workflow,
dispatch, credentials, orders, trading, ranking, futures, monitoring, paid API,
VM deployment/migration, ZUMERAVO access, merge or issue closure.
**STOP FOR OWNER AND BOSS AI REVIEW.**
