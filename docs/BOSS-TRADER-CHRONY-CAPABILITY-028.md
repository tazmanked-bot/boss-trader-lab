# BOSS-TRADER-CHRONY-CAPABILITY-028

Issue: https://github.com/tazmanked-bot/boss-trader-lab/issues/51
Baseline: 457531a92df4112957d3c3744c081a15f16858ed.
Reviewed 2026-11-06: full issue, current README.md and SECURITY.md. No AGENTS.md exists in the repository tree.

## Result

Offline implementation complete: fixed package/version command contract, strict metadata/ownership/banner parsers, bounded streaming and cleanup control tested using sealed fake-process events. **Actual execution BLOCKED** under Issue #51 item 5: independently enforced no-network/no-clock-mutation containment, descriptor-bound execution and matching installed-build approval are unavailable.

No real dpkg-query or chrony process is implemented or launched. Actual installed package version, package authenticity, compiled NTS capability and B4 progress remain UNVERIFIED. This is an honest blocked execution boundary with executable negative tests, not a completed target package/version collection.

Three additions: research/chrony_capability_028.py, tests/test_chrony_capability_028.py and this report. Existing 027 inventory, 026 authentic_verifier(), observer/scanner/transport, existing tests and workflows remain unchanged. No merge, dispatch, installations, market/time queries or ZUMERAVO access.

## Independently inspected prior target evidence

[Run 42229089804 / job 127930031581](https://github.com/tazmanked-bot/boss-trader-lab/actions/runs/42229089804/job/127930031581) was inspected through GitHub run metadata and decoded job logs.

| Evidence | Exact finding |
| --- | --- |
| Workflow revision | API head_sha=37d88543fb3d6ea1d10cb59267d651f75ec9d03f |
| Tested checkout | Logs fetch/checkout and later HEAD check identify 990c1a1039da36f3034c321f0f58038e9b4a0530; initial git status --porcelain was checked empty |
| Target | Ubuntu 24.04.5; image 20261101.360.1; Linux 7.0.0-1017-azure x86_64; Python 3.11.17 |
| Prior tests | 26 focused / 0.048s; 475 full / 9.490s, OK |
| /usr/sbin/chronyd | 306232 bytes; SHA-256 7a834e478d8a904c39a348606a5d0ac58fd1ccbca24f333a8170c786af8ca508 |
| /usr/bin/chronyc | 93392 bytes; SHA-256 271ea54c67206559437bd299d0e08c9e3d42ee6be322b1722e76311cd5d9df8d |
| Other two 027 paths | ABSENT |
| What inventory established | PRESENT_HASHED_NOT_EXECUTED / CLIENT_CAPABILITY_UNVERIFIED; versions NOT_EXECUTED; package/build/NTS support UNVERIFIED |
| Setup network | Logs show action/source fetch, Python archive download and pip 26.3 download/upgrade; the entire job was not network-free |
| Probe scope | Inventory's own requests=0/process_launches=0; that counter does not cover Actions bootstrap |

These hashes are historical observations for that image/run, not permanent execution approval. The [published matching image manifest](https://github.com/actions/runner-images/blob/ubuntu24/20261101.360/images/ubuntu/Ubuntu2404-Readme.md) lists dpkg 1.22.6ubuntu6.6. That is an image-manifest claim, not a fresh dpkg-query binary/version measurement. It does not establish the installed chrony version.

The connector-staged local workspace remains separate: Debian 13 / Linux 6.18.57 x86_64 / Python 3.12.14, without .git metadata. Source was staged from the exact baseline and checked against its Git blob hashes. No Ubuntu target run of new 028 code occurred.

## Fixed two-stage contract

The module has no arbitrary command, binary path, argument, environment or runner callback interface. Default import/CLI performs no file reads, clock sampling or process launch.

The immutable proposed argv sequences are:

1. /usr/bin/dpkg-query --no-pager --show --showformat=<fixed format> chrony
2. /usr/bin/dpkg-query --no-pager --search /usr/sbin/chronyd /usr/bin/chronyc
3. /usr/sbin/chronyd --version
4. /usr/bin/chronyc --version

The fixed format is six tab-separated fields plus newline:
binary:Package, Status, Version, Architecture, source:Package, source:Version.
It uses dpkg's literal field syntax and introduces no shell. Both metadata queries are chrony-specific; no broad package list, apt operation, maintainer script or remote package metadata is involved.

Launch intent fixes cwd=/, stdin=DEVNULL, shell=false, close_fds=true, new session/process group and an unprivileged/no-clock-capability requirement. Environment is newly constructed with only LC_ALL=C, LANG=C and DPKG_COLORS=never. No PATH, HOME, pager, loader/Python/proxy/listen variables are inherited or caller-configurable. These are specified requirements, not evidence that a native launcher enforced them.

Stage A requires one exact installed chrony package row, installed/healthy status, reviewed amd64 architecture, bounded version/source fields and exact ownership of both absolute paths. Diversions, multiple owners, duplicates, extra paths or missing package data refuse. Parsed DB facts are labeled LOCAL_METADATA_ONLY: they do not cryptographically authenticate package origin or file contents.

Stage B requires a separate opt-in, established package/source versions and an exact reviewed build/file identity. **There are no real build approvals.** MockReview is explicitly SYNTHETIC_REVIEW_NOT_EXECUTION_APPROVAL and works only inside an exact FakeBackend. Unknown versions stop before any modeled version launch. The invented 4.6-0synthetic028 fixture is not an installed package version or target approval.

Identity fields include path/device/inode/mode/size/timestamps/hash and modeled absence of file capabilities. Symlinks, set-ID files and clock capabilities refuse. Fresh identity checks precede and follow each modeled operation and version approval must match the same-run identities. Native TOCTOU closure is not implemented; repeated path hashes do not solve it.

A banner is parsed only as CLIENT_REPORTED_VERSION. A positive daemon NTS flag is CLIENT_REPORTED_NTS_BUILD_FLAG, never authenticated association evidence. Missing/negative/contradictory daemon flags stop; chronyc's own feature list is not required to claim NTS-client authentication. No raw unrecognized banner/error text is returned.

## Finite limits and tests of failure handling

The fake event controller implements four sequential launches maximum, 16 KiB combined stdout+stderr per child, 64 KiB report and 4096 events per child. It rejects overflow before appending the next chunk; it does not use unbounded communicate/capture_output. Events are already caller-owned fake bytes, not an actual streaming pipe implementation.

Per-command budget is two seconds, with 250ms reserved inside it for cleanup; ordinary work gets at most 1.75s. Aggregate budget is ten seconds including modeled cleanup. Expired launch/read cannot produce success. A deliberately late, unpreemptible-start model reports timeout/overshoot rather than a fictional hard deadline. Any timeout/overflow/error requests owned-group kill and exact-child reap in the model. Reaping, empty descendant group and cleanup timing must all be certain before another command. Uncertainty is STOP. Reports retain bounded lengths and output hashes; secret/error text is discarded.

No fake result establishes native kill/reap, pipe handling, total RSS or scheduler guarantees. A future native implementation must handle partial startup, simultaneous stdout/stderr readiness and EOF, inherited FDs, descendant escape, PID/group identity and exact wait/reap. A subprocess timeout or Python socket mock cannot supply those properties.

## Why native execution is blocked

A safe future execution boundary must independently deny network creation/use, including local daemon IPC and inherited descriptors, and clock mutations. It must also enforce unprivileged execution without clock capabilities, no privilege gain, restricted device/filesystem access and bounded process-tree/output resources. No such reviewed target boundary is available here. No privileged setup, namespace/seccomp configuration, container installation or sandbox claim is introduced.

Binding execution to reviewed bytes needs an open, no-follow descriptor with stable identity/hash and an approved descriptor-based exec mechanism, or a genuinely immutable independently controlled executable store. Path rechecks alone retain a replacement race. Even fd execution does not freeze the ELF interpreter, shared libraries, loader cache, system configuration or constructors before main. Those dependencies and privileges need matching package/build provenance and review; environment sanitization alone is insufficient.

Consequently:
- Native --metadata and --versions always return EXECUTION_CONTAINMENT_UNAVAILABLE, exit 2, with zero operations.
- --plan prints the exact fixed contract/caps but never executes it.
- evaluate_offline accepts only sealed FakeBackend data, never subprocess or a user factory.
- No real UID, file, package DB, environment, timestamp or runner data is collected by the adapter. All fake context is labeled SYNTHETIC_CONTEXT, while real source/target fields remain UNAVAILABLE.
- Existing UTC authenticity and source-admission gates do not change.

## Primary source review and version gap

Documentation/source reviewed on 2026-11-06:

- [Ubuntu Noble dpkg-query manual](https://manpages.ubuntu.com/manpages/noble/man1/dpkg-query.1.html), published for dpkg 1.22.6ubuntu6.6: --show/--showformat, source/binary fields, exact-path --search, --no-pager and environment behavior support the fixed local metadata design. Installed status and ownership are local DB claims, not package signature verification.
- [chronyd 4.6 manual](https://chrony-project.org/doc/4.6/chronyd.html) and [chronyc 4.6 manual](https://chrony-project.org/doc/4.6/chronyc.html): --version prints and exits; ordinary daemon/client operations are excluded. No -Q/-q/-p/-x, bare binary, status query or service control is allowed.
- [Upstream 4.6 main.c](https://github.com/mlichvar/chrony/blob/4.6/main.c): --version calls print_version and returns before daemon/configuration setup, but platform/log initialization and the dynamic loader precede that branch. This is not proof of side-effect-free execution.
- [Upstream 4.6 client.c](https://github.com/mlichvar/chrony/blob/4.6/client.c): early long-option --version branch prints version/features and returns before normal client processing. It is candidate behavior only.
- [Ubuntu Noble chronyd](https://manpages.ubuntu.com/manpages/noble/man8/chronyd.8.html) and [chronyc](https://manpages.ubuntu.com/manpages/noble/man1/chronyc.1.html) manuals currently identify their published package as 4.5-1ubuntu4.2. **That does not establish the runner's installed package.** It demonstrates why assuming 4.6 from earlier documentation is invalid.

Actual matching Ubuntu source/patch/build and library review cannot be completed until fresh Stage A facts exist. Neither the historical binary hashes nor a generic upstream tag closes that gap. Unreviewed installed versions remain blocked. No package provenance, vulnerability clearance, cryptographic NTS support or independently verifiable UTC is claimed.

## Exact offline validation

Python 3.12.14:

```sh
python -B -m unittest tests.test_chrony_capability_028 -v
python -B -m unittest discover -s tests -v
```

Focused: 23 tests, 0.071s, OK.
Full: 498 tests, 7.578s, OK, no skips.

The positive fake recipe uses four modeled launches, zero actual launches/requests and 12000000ns synthetic elapsed time; actual_package_version remains null. This timing is invented test data, not a measurement.

Tests deny real process, exec/fork/shell, socket/DNS/HTTP and wall-clock APIs. Import/default/all native opt-ins additionally deny file reads and monotonic sampling. Negative tests cover exact argv/path/option/environment contracts; absent/unhealthy/unowned/wrong-architecture package data; unsupported builds; symlink/set-ID/capability/replacement/hash failures; banners and flags; streaming overflow; all four hang positions; nonzero/signal/stderr; launch overshoot; aggregate/event caps; uncertain group/reap/cleanup STOP; reused context and redaction. Existing offline regression worker tests run as before; no real package/version query is used.

## Local versus target gaps / owner decision

| Evidence | Status |
| --- | --- |
| Prior Ubuntu binary presence/hash, source checkout and image | VERIFIED HISTORICAL LOG EVIDENCE at run/job above |
| Actual chrony installed package/source version/ownership | NOT COLLECTED |
| Matching Ubuntu source, patches, binary/dependency provenance | UNVERIFIED; generic documentation is insufficient |
| New bounded controller/parsers/refusal cases | OFFLINE FAKE-PROCESS TESTED |
| Native streaming/group/reap and fd-bound exec | NOT IMPLEMENTED / UNVERIFIED |
| Independently enforced network/clock denial | UNAVAILABLE; actual execution BLOCKED |
| New target source cleanliness, image, tool/binary identities and raw query output | NOT COLLECTED |
| B1/B2/B3/B5 | HOLD |
| B4 / authentic UTC / trading | NO-GO / AUTHENTIC_PROVENANCE_NOT_COLLECTED / NO ORDERS |

Smallest owner action: review the Draft PR and decide whether an independently enforced, pre-provisioned unprivileged containment boundary can be supplied for Stage A. No real metadata/version command is authorized or enabled by accepting the fake-process tests. If it cannot be supplied, retain BLOCKED; do not replace it with a trusted=True marker.

No new workflow is proposed as an active file: the probe cannot safely collect native evidence yet. The existing PR50 launcher remains unchanged at its reviewed pin. If the owner later requests a launcher, it needs separate Draft review with literal reviewed source/checkout/setup action pins, workflow_dispatch only, ubuntu-24.04 and Python 3.11.17, source/hash cleanliness and fresh identity/raw-result recording. Bootstrap fetches/downloads must be accounted separately; no whole-job zero-network claim or additional setup-download recipe is introduced here.

STOP FOR OWNER AND BOSS AI REVIEW. No merge, dispatch, installation, NTS/NTP/Kraken request, clock adjustment, keys, orders, rights-policy changes or ZUMERAVO changes.

