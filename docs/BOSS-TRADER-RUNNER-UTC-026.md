# BOSS-TRADER-RUNNER-UTC-026

Issue: https://github.com/tazmanked-bot/boss-trader-lab/issues/47
Baseline inspected: f19c26815956c4f1aeabf28712ab3d4938c1f404, owner-merged PR #46.
Baseline design: [025 report](BOSS-TRADER-REAL-KRAKEN-BTC-TRANSPORT-025.md).

## Verdict and changed scope

Practical progress: OFFLINE MEASURED worker timing, cleanup and memory/descriptor observations; offline-tested UTC-envelope binding and conservative interval arithmetic. Overall HOLD; independent UTC B4 remains NO-GO. The requested Ubuntu 24.04 / Python 3.11.17 runner has not been executed by this assignment.

Six added files: research/runner_diagnostic_026.py, research/utc_evidence_026.py, their two matching tests/test_*.py files, this report and [local measurement JSON](evidence/runner-utc-026-local.json). The 025 transport, observer/Action, existing tests, registry, calculations, 024 preview and live gates are unchanged. No new workflow is created or dispatched. No authority, Kraken, NTP or external diagnostic request occurred. Published documentation was read through the web connector only.

## B5 executable diagnostic

The optional stdlib harness exercises the unchanged isolated_exchange with controlled fake DNS/socket/TLS/HTTP. It instruments fork, ready/release bytes, SIGKILL, select and waitpid using scoped patches. Actual wait4 reaps the exact child and supplies its ru_maxrss. A separate fixed 4096-byte anonymous mapping carries bounded child timing notes. There is no pickle or telemetry upload.

Ten fixed cases: success; stalled DNS/connect/TLS/read; pre-ready startup delay; refused child allocation; simultaneous bounded parent/child pressure; successful bounded CPU work; CPU budget exhaustion. Each case uses a 200ms test deadline by default (allowed 20ms–1s, never above the existing 10s stage maximum). No production limit is increased. At most one child exists at a time. Default entrypoint is disabled. Enabled runs install network-denial guards inherited by children; fake dependencies contain no real socket or resolver.

Parent pressure is limited to 8 MiB, child retained pressure to 16 MiB. The constrained-child test requests 512 MiB under the existing 512 MiB address-space cap and records MemoryError; it does not exhaust the host or claim a cgroup OOM test. Parent allocation failure is tested before IPC/worker creation. CPU work is bounded within the one child, not a host stress workload.

A genuine unreaped/unprovable child is STOP, with no next case. The harness has an independent SIGKILL/reap cleanup backstop. Proven parent FD growth is also STOP. Unavailable proc/cgroup fields remain null/UNAVAILABLE; missing observations do not become successful measurements. Modeled unreapable/FD-leak tests clean actual test resources before asserting refusal.

Output is capped at 65536 bytes. The fixed 025 result map remains 270500 bytes; this sample's synthetic HTTP result is 16522 bytes. Reads of proc/cgroup/OS metadata are capped; descriptor enumeration stops after 1024 entries. Only ImageOS, ImageVersion, RUNNER_OS and RUNNER_ARCH are allowlisted from environment; no environment or credential dump occurs. The visible cgroup root is deliberately labeled possibly shared/ancestor, never dedicated containment. No cgroup is changed or privilege requested.

Instrumentation itself consumes resources and perturbs timing. Report start includes wrapper setup immediately before the transport call; transport's actual deadline starts internally before its allocations/fork. Observed overshoot therefore includes wrapper/cleanup/scheduler overhead, not an isolated DNS latency estimate. Ready-before-write, parent-ready observation and release are distinct timestamps. Sampling may miss memory/FD peaks; summed RSS counts shared pages twice. wait4 high water and proc counters have different accounting semantics.

### Local measurement evidence

The committed JSON was generated from the new source snapshot over the pinned baseline; source SHA-256 values bind the exact modules. Its supplied revision identifies the baseline, not a claim that new 026 files existed in that commit. Local Git metadata was absent: git_head_observed=null and revision_status=UNAVAILABLE. This is explicitly not a pinned target-runner artifact. The Draft PR identifies the final code commit; remote file readback is used to verify it matches tested sources.

Local profile: Debian 13, Linux 6.18.57, x86_64, Python 3.12.14 (build main / Aug 25 2026 14:00:49). GitHub image fields unavailable. CLOCK_BOOTTIME symbol available; availability alone does not prove calibration or suspend handling.

| Case | Result | Elapsed ms | Observed overshoot ms | SIGKILL→reap ms |
| --- | --- | ---: | ---: | ---: |
| success | COMPLETED | 8.368 | 0 | n/a |
| DNS stall | TIMEOUT | 201.599 | 1.599 | 1.175 |
| connect stall | TIMEOUT | 201.608 | 1.608 | 1.157 |
| TLS stall | TIMEOUT | 201.775 | 1.775 | 1.350 |
| read stall | TIMEOUT | 201.781 | 1.781 | 1.127 |
| startup delay | TIMEOUT, no release | 202.278 | 2.278 | 1.371 |
| child allocation refusal | NETWORK_UNAVAILABLE, allocation_refused=true | 7.269 | 0 | n/a |
| parent + child pressure | COMPLETED | 13.147 | 0 | n/a |
| bounded CPU work | COMPLETED | 58.426 | 0 | n/a |
| CPU exhaustion | TIMEOUT | 201.578 | 1.578 | 1.137 |

All ten children reaped. Successful first-case parent readiness observed at 2.439ms and release at 2.447ms. Every parent FD baseline/final was 4/4; sampled parent peak 6, child peak 7 (includes startup before child FD closure). Across cases, sampled parent RSS maximum 30605312 bytes, child 43659264 bytes and simultaneous sum 74264576 bytes. These are observations, not hard maxima.

Visible cgroup memory.max=8589934592, final memory.current=98467840, historical memory.peak=139075584 bytes. The historical peak is not attributed to this harness and includes earlier activity. Shared/ancestor scope and total containment remain unverified. RLIMIT_AS does not substitute for RSS, process-tree or cgroup proof.

## B4 feasible routes, supported by published documents

Primary recommendation: assess an existing NTS-capable chrony client on the selected owner runner before developing a custom authority service. No package presence is assumed. Moderate operational burden: approved client/build and trust bootstrap, bounded one-shot configuration, authenticated evidence export, then local run/boot/nonce binding and uncertainty review. No client was installed or invoked.

| Route | Obtainable support / evidence | Prerequisites and remaining limits |
| --- | --- | --- |
| NTS client, primary feasibility route | [RFC 8915](https://www.rfc-editor.org/rfc/rfc8915.html) specifies authenticated NTP with TLS key establishment. [chrony 4.6 configuration](https://chrony-project.org/doc/4.6/chrony.conf.html) documents nts and certificate trust sets. [chronyd options](https://chrony-project.org/doc/4.6/chronyd.html) document bounded-duration, offset-only -Q operation without clock correction, potentially without root under a restricted configuration. [Cloudflare NTS docs](https://developers.cloudflare.com/time-services/nts/) publish client/service support; availability was not probed. | Requires approved installed binary/build, independent pinned trust bootstrap, future authorized network access and conservative error bounds. Authenticating packets does not prove clock accuracy; RFC 8915 §§8.5–8.6 address bootstrap and delay attacks. An offset printout or chronyc status alone is not independent B4 evidence. No fallback to unauthenticated NTP. |
| Pinned asymmetric signed time / Roughtime | [Google's protocol project](https://roughtime.googlesource.com/roughtime) documents signed nonce-bound replies and C++/Go clients. This is a real documented implementation model, not an invented running custom token service. | Moderate-to-high burden: reviewed protocol/client and crypto, current pinned operator key, nonce/response validation, verified accuracy radius and local timing bounds. Original design targets rough time, so <=2s is not assured. The old Cloudflare port/key is [deprecated](https://developers.cloudflare.com/time-services/roughtime/deprecation/); no such endpoint is recommended as available. Owner-provisioned custom signed tokens need an actual independent authority, not merely a signer. |
| Owner-controlled GNSS/PPS/PHC authority | [chrony refclock documentation](https://chrony-project.org/doc/4.6/chrony.conf.html#refclock) documents PPS, SOCK and hardware-clock support. | High provisioning burden; existing owned hardware/host access, calibrated UTC source/UTC–TAI treatment, local sample provenance and independent accuracy bounds. PPS alone does not provide full UTC. Hosted Actions hardware access is unverified. No purchase, host configuration or local authority is assumed. |

Primary route is a feasibility choice, not B4 clearance. If the target cannot expose authenticated source evidence and justified error bounds without privileged or unsupported changes, B4 remains NO-GO. A pinned owner authority is a fallback only after actual provisioning; the mock envelope does not create that authority.

Smallest future on-runner B4 step: owner selects the intended runner and checks an already-installed client's version/build and documented NTS capability offline. If unavailable, stop and decide separately about an approved dependency/runner. Any later authority interaction needs separate explicit authorization, exact authority/trust bootstrap, finite request/time bounds and archived authenticated evidence. No time query command or active adapter is supplied here.

## Strict offline UTC proof model

utc_evidence_026.py accepts a maximum 8192-byte exact schema, rejects duplicate/unknown fields and type/size errors. Binding is exact revision, run, boot token and 256-bit nonce. Monotonic send/receive and suspend-inclusive boot-clock samples must be ordered, from the same binding and consistent within the model's 1ms sample tolerance. Reboot, suspend disagreement, rollback, replay, stale lease and conflicting re-enrollment fail closed. Each instance burns one challenge, including on failure.

Only MockSignature byte-equality fixtures are accepted. They are openly labeled NOT_CRYPTOGRAPHY; a boolean or callback cannot masquerade as a verifier. Forged/altered mock content refuses against its fixed expected fixture. No SHA/HMAC is used as an authority signature. authentic_verifier remains disabled and always returns B4 NO-GO. Mock acceptance always says independent_utc=false and live_admission=HOLD.

At receipt, a signed authority event known to lie within the whole send/receive window would yield conservative bounds:
- low = authority UTC − accuracy − twice the local timestamp error;
- high = authority UTC + accuracy + full RTT + RTT drift allowance + twice the timestamp error.

The midpoint radius is rounded upward. This adds the entire RTT to the possible event-to-receipt delay without assuming symmetric paths. Later bounds advance by monotonic age and widen by an upward-rounded drift allowance. Initial and grown uncertainty must both stay <=2s. Lease is at most 30s; equality at expiration refuses. These are explicitly model choices, not modifications to existing live gates. Drift=100ppm and timestamp error=1ms are test assumptions needing independent target justification.

Tests give a 100ms RTT / 100ms authority accuracy example with 152005000ns initial uncertainty. The example is synthetic arithmetic only. No authenticated time or calibrated clock was obtained. The model consumes supplied sample values; it does not attest their acquisition, generate production nonces, implement persistent replay storage or perform real signature verification. A new instance is not a persistent anti-replay database. A future adapter must create fresh unpredictable challenges, bind trusted local samples, prevent replay across runs/restarts, verify reviewed asymmetric signatures/pinned keys or authenticated NTS provenance, and justify authority error/drift/suspend bounds. Real public-key crypto/client support requires separate review; no homegrown asymmetric implementation is introduced.

Python's [CLOCK_BOOTTIME documentation](https://docs.python.org/3.11/library/time.html#time.CLOCK_BOOTTIME) explains its suspend-inclusive semantics. Symbol presence is not evidence that supplied samples were acquired correctly. Linux's [cgroup v2 documentation](https://www.kernel.org/doc/html/latest/admin-guide/cgroup-v2.html) describes memory controls/accounting; reading a visible limit does not prove a dedicated containment contract.

## Tests and manual owner acceptance

Final commands, Python 3.12.14:

```sh
python -B -m unittest tests.test_utc_evidence_026 tests.test_runner_diagnostic_026 -v
python -B -m unittest discover -s tests -v
```

Focused: 30 tests in 0.616s, OK.
Full: 449 tests in 6.486s, OK, no skips.
The executable ten-case harness returned EXPECTED_RESULTS, requests=0, all children reaped. No installations. Tests deny real network/subprocess/wall-clock APIs; UTC policy tests also deny file reads and clock sampling. New tests include rollback/restart/suspend, replays/conflicts/forgeries, stale/growing uncertainty, real stalled phases, startup/CPU exhaustion, cleanup/error STOP, unavailable counters, parent/child memory failures and FD-growth refusal.

For a manual owner run, first detach a clean checkout at the exact reviewed Draft PR head and set REVIEWED_SHA to that literal 40-character SHA. Verify source hashes against that commit; a matching HEAD label alone does not prove a clean worktree. Then run the two test commands and:

```sh
test "$(git rev-parse HEAD)" = "$REVIEWED_SHA"
python -B -m research.runner_diagnostic_026 --offline-run --revision "$REVIEWED_SHA" > runner-026.json
```

No workflow file is necessary for these manual commands. If the owner elects a GitHub Actions launcher later, it must be workflow_dispatch only, pin the literal reviewed commit, pin reviewed checkout/setup-python actions, target ubuntu-24.04 and Python 3.11.17, and run offline commands only. The existing PR46 launcher stays pinned to its older commit and cannot establish evidence for this new code. No workflow has been added, changed or dispatched.

Accept the target artifact only with revision_status=MATCH, independently clean source/hash match, exact Python/kernel/OS and GitHub ImageVersion, expected cases, zero real requests, successful reap and no FD growth. Archive raw bounded JSON and complete test summaries. Missing image/cgroup/FD/memory fields remain unavailable and block corresponding containment conclusions. Review startup/release, hang overshoot, cleanup and memory under a separately approved dedicated OS containment profile. Native fork/kill, scheduler stalls, proc reads and kernel states still prevent a Python-only hard worst-case promise; the harness is observable and bounded in inputs, not a hard real-time service.

## B1–B5 matrix and owner decision

| Blocker | New evidence | Live status |
| --- | --- | --- |
| B1 | OFFLINE MEASURED: real worker controlled hangs, launch/release and observed overshoot | HOLD: genuine resolver/TLS/network and hard deadline contract unverified |
| B2 | OFFLINE MEASURED: actual reap, descriptors, fixed result map, sampled RSS, controlled allocation refusal | HOLD: dedicated total-memory/OS containment and worst-case kill/reap not established |
| B3 | Existing offline identity/OHLCV tests retained and passing; no new genuine-source evidence | HOLD: actual provider/schema/admission unverified |
| B4 | DOCS-ONLY authority feasibility; mock policy arithmetic/negative tests | NO-GO: no independently verified authority/key/accuracy/target samples |
| B5 | OFFLINE MEASURED on identified local Debian/Python environment | HOLD: requested Ubuntu24/Python3.11.17 and exact image not run |

Smallest safe next owner action: review this Draft PR, then manually reproduce the pinned-head offline tests and harness on Ubuntu24/Python3.11.17. Keep source admission HOLD. Separately choose whether an existing NTS client can supply verifiable evidence on that runner; do not authorize Kraken observation from this report. No live WATCH, scheduling, keys, orders, paper/live trading, installation, merge, blanket rights gate or ZUMERAVO changes. Existing close-only manual OBSERVE_ONLY remains available unchanged.

STOP FOR OWNER AND BOSS AI REVIEW.

