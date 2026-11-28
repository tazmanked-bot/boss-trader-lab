# CODEX 037 — controlled build executor and runtime integration

Issue #69. Stack on unchanged Draft #68 head
`bdd88585f9719d625609834bb26a6fb7513bd502`. No previous PR or original runtime,
source, model, AEP, recorder, strategy or ZUMERAVO changes. Additional spending NT$0.
**REAL_NOT_RUN means genuine AI inference not run. No actual llama.cpp compilation
or owner desktop access occurred either.** No installations, downloads, exchange
requests, deployment, orders, merge or workflow dispatch.

## Delivery and review disposition

`research.controlled_build_037` is a functional executor: the `build` action runs
fixed configure and single-target build argv after target qualification and a
scoped explicit owner approval. It is not an unconditional HOLD stub. The shared
supervisor really launches gated processes, sets limits/affinity/priority, drains
bounded output, checks recorder/STOP conditions, enforces watchdog/aggregate CPU,
kills the private cgroup/process group and reaps the direct child. Harmless compiler
substitutes exercise success, failure, one-use approval and no-retry behavior.
The original CODEX035 inference process/worker/trust limits and CODEX036 code are
unchanged; new build controls do not authorize runtime inference.

**Owner review of this delivered executor AND the exact target plan is required
before the single actual build.** Target containment/runtime remain unqualified
here. AEP Gate B HOLD, genuine inference HOLD, BUY AUTHORIZATION NONE. Source
revision remains `0978a6e9022fb9bd6874b86154ee304e81929b9f`, tree
`5e472b707005dec79feedd0942c3814fb88b9a6d`. Source/build options reuse the exact
036 pinned recipe; CMake flags remain untested by a real compiler. This delivery
makes no forecast that the first build will finish or pass all postchecks.

## Corrections to the 036 preparation boundary

* Original group-writable source is **read input**, never executed/chmodded.
  `source_inventory` verifies the raw Git commit and recursive tree object hashes
  against the independently pinned commit/tree; every tracked blob's Git SHA-1 is
  checked, and a SHA-256 export manifest is recorded. Git plumbing is read-only,
  hooks/fsmonitor/replacement objects disabled; protocol access denied. Promisor,
  external remote-helper and protocol-enabling config is refused. Missing objects
  do not authorize fetching. Untracked files, `.git`, source symlinks/gitlinks and
  unsafe ancestors are excluded/refused. Original file identities/mtime/ctime are
  compared before/after reads and the complete manifest is re-read after export.
  New independent source files are 0400/0500 in 0700 directories; build mounts
  source read-only. Group-writable **job/config/toolchain/health/code** paths are
  still refused. This is a narrow authenticated-data exception, not a general
  relaxation of CODEX035 path security or protection from a hostile same-UID user.
* Private artifact RPATH/RUNPATH must still contain only nonempty `$ORIGIN` search
  elements resolving within the private stage. The separate reviewed system
  manifest explicitly pins loader/library physical paths, hashes, versions,
  copyright references and SONAME/transitive closure under `/usr/lib`.
  Standard system libraries need no invented private RPATH. No missing dependency
  is resolved by scanning the host or silently inheriting its loader cache.
* Build mounts `/usr` read-only as an explicitly reviewed **toolchain** profile,
  with usrmerge aliases; `/etc` contains only reconstructed compiler alternatives
  pointing directly at pinned `/usr` compiler files. No host `/etc` mount/cache; credentials/home/original source/model/
  AEP/recorder are absent. Protected roots beneath `/usr` are refused. The later
  **runtime** contract contains only explicitly pinned system **file** mounts at
  Debian x86_64 conventional library paths and the exact PT_INTERP destination,
  alongside read-only private artifacts. It never inherits the whole build `/usr`.
  Target qualification executes harmless installed `/usr/bin/true` with that
  file-only loader closure to test real loader resolution, without running llama.
  This probe is **UNVERIFIED here** because namespace creation is restricted.

## Budget proposed for explicit owner review

| Control | Fixed proposal / behavior |
|---|---|
| Work | One configure + `cmake --build /job/build --target llama-cli --parallel 1`; no all-target install, server execution, retry or inference |
| Wall / aggregate CPU | 7,200s wall / 5,400s CPU across configure and compilation; CPU usage read from the private cgroup, monotonic wall watchdog |
| CPU | Exactly one inherited allowed-CPU affinity, cgroup `cpu.max=100000 100000`, nice +10, parallelism 1 |
| Memory / swap / PIDs | `memory.max=3221225472`, `memory.swap.max=0`, `memory.oom.group=1`, `pids.max=64` |
| Other bounds | Core dumps zero; 256 FDs; 256 MiB maximum individual output file; 4 MiB combined stdout/stderr per step; <=128 staged candidates, <=512 MiB staging input |
| Headroom | 4 GiB currently available RAM (visible cgroup ceiling included) and 4 GiB disk before build; abort below 1 GiB free disk during build |
| Health | External measurement <=30s old, last actual collection <=2 declared collection cadences +30s; fresh identity/healthy/stable assertions; STOP marker abort |

The prior 900s wall/600s CPU proposal was not benchmark evidence. A one-job build
including GGML/server-support/CLI on an older Ryzen with two allocated vCPUs can
reasonably require far more CPU time. The new finite two-hour/90-minute proposal
is **not a measured duration or guarantee**. It does not increase memory/CPU/swap
limits, retry automatically or adjust the budget at runtime. Overrun means stop,
preserve evidence and review a new plan. Watchdog sampling is approximately 100ms;
there is scheduling/read overhead and a small CPU/time observation granularity.
The parent performs bounded source/artifact reads outside the build cgroup; allow
additional parent/OS/recorder headroom. Free-space monitoring is not a disk quota.
Hidden ancestor limits, competing processes, host-admin changes, SIGKILL/power
loss and physical desktop responsiveness cannot be guaranteed by synthetic tests.

## Target prerequisites and ownership

Use only existing Debian tools and the previously reviewed local source. Never
install, fetch, sudo, change cgroup delegation/global settings, or fix original
permissions to make a check pass. Required tools have fixed `/usr/bin` paths:
CMake, C/C++ compiler, make, linker, Python3, bubblewrap, true; their resolved files
and this supervisor/worker are hash-pinned into the plan and rechecked. Actual
`--version` outputs are captured **inside** qualification's build sandbox. The
`inputs` utility reads the installed dpkg package database/copyright files and five
explicit standard library candidates; review their actual license contents and
versions. These local reports are not upstream signatures or vulnerability
clearance. Additional actual dependency needs fail for separate review.

A pre-existing user-owned delegated cgroup directory must expose enabled cpu,
memory and pids controllers, writable private children and `cgroup.kill`. The
executor locks the delegation directory inode across jobs, refusing concurrent
build/qualification. Unsupported directory locking is a target blocker. Existing
`boss-035-*` children cause refusal instead of automatic cleanup of other scopes.
A newly created own scope is limited/read-back before releasing any gated child.
Group kill/empty verification and direct-child reap are mandatory. Qualification also
starts a harmless fork/setsid descendant, proves it reached its detached state,
then requires the actual watchdog timeout and an empty owned cgroup after cleanup.
This kernel-specific probe remains UNVERIFIED in this cloud environment. TERM/interrupt
normally unwind cleanup; hard kill/power loss cannot run Python cleanup. An
unclean scope is not automatically reused/removed; preserve evidence for review.
No namespace or cgroup fallback is allowed.

An **external, owner-reviewed recorder status producer** must expose genuine UTC
integer measurement/last-collection timestamps and actual healthy/stable booleans.
The optional read-only `monitor` maps specified JSON fields to a private health
file; it preserves the producer's measurement timestamp and never substitutes the
poll time or invents healthy/stable flags. An old status remains old. This adapter
opens no recorder database, restarts no service and makes no market request.
If the current local producer lacks these semantics, **STOP and review the mapping
or provide an independent observer**. Do not fabricate a continuously fresh health
file from a one-time owner statement. The reported stable desktop is owner evidence,
not a stress-test result or an independently measured continuous health guarantee.

## Consolidated owner commands — no compilation until review

Run from the reviewed new PR checkout. Verify its exact Git head against the PR
report. Commands use the existing system Python and clear Python injection vars
for this shell invocation only; they do not change AEP/global configuration.
Set the following **real absolute paths** once, avoiding the accidental newer
source checkout. Do not point any command at ZUMERAVO.

```sh
bt037() { env -u PYTHONPATH -u PYTHONHOME PYTHONNOUSERSITE=1 /usr/bin/python3 -B -m research.controlled_build_037 "$@"; }
git rev-parse HEAD
/usr/bin/python3 --version
/usr/bin/python3 -B -m unittest discover -s tests -p test_controlled_build_037.py -v
/usr/bin/python3 -B -m unittest discover -s tests -v
```

Define `BT_PRIVATE` as a new private job-parent path (not an original directory),
`BT_SOURCE` as the exact original reviewed source, `BT_CGROUP` as the existing
private delegation, `BT_AEP`, `BT_RUNTIME`, `BT_MODEL_ROOT`, `BT_RECORDER` as protected
roots, and `BT_STATUS` as the existing external JSON status path. Fill recorder ID
and the **real** collection cadence below. Avoid sensitive details in public logs.

```sh
mkdir -m 700 "$BT_PRIVATE"
bt037 inputs --directory "$BT_PRIVATE/inputs" --review-ref 'OWNER-INPUT-REVIEW-REF'
# Review candidate versions/hashes/copyrights first; this writes NEW input JSON only:
bt037 inputs --directory "$BT_PRIVATE/inputs" --review-ref 'OWNER-INPUT-REVIEW-REF' --apply
/usr/bin/python3 - "$BT_PRIVATE" "$BT_SOURCE" "$BT_CGROUP" "$BT_AEP" "$BT_RUNTIME" "$BT_MODEL_ROOT" "$BT_RECORDER" <<'PY'
import json,sys
from pathlib import Path
private,source,cgroup,aep,runtime,model,recorder=sys.argv[1:]
p=Path(private)
config={"source":source,"job":str(p/"attempt-1"),"protected_roots":[aep,runtime,model,recorder],
        "cgroup_parent":cgroup,"health_file":str(p/"health.json"),
        "recorder_id":"REPLACE_WITH_ACTUAL_RECORDER_ID","collection_cadence_seconds":60,
        "toolchain_evidence":str(p/"inputs/toolchain.json"),"system_libraries":str(p/"inputs/system-libraries.json")}
with (p/"config.json").open("x") as f:json.dump(config,f,indent=2)
(p/"config.json").chmod(0o600)  # newly created config only
PY
```

Review/edit only the **new config** ID/cadence as necessary. In a second terminal,
run the existing independent status producer and the following mapper with its
real field names (example keys are placeholders, not an actual recorder schema):

```sh
bt037 monitor --status-file "$BT_STATUS" --health-file "$BT_PRIVATE/health.json" --recorder-id 'ACTUAL_RECORDER_ID' --measurement-key measured_at --collection-key last_collection_at --healthy-key healthy --stable-key desktop_stable --seconds 7500 --stop-file "$BT_PRIVATE/attempt-1/STOP"
```

A missing status producer, schema, true health observation, delegation or tool
means HOLD. Do not manufacture replacements merely to get a green result.

```sh
bt037 prepare --config "$BT_PRIVATE/config.json" > "$BT_PRIVATE/dry-run.json"
# Review the dry-run. This next action only exports source and writes the new plan:
bt037 prepare --config "$BT_PRIVATE/config.json" --apply
bt037 qualify --plan "$BT_PRIVATE/attempt-1/plan.json"
bt037 status --plan "$BT_PRIVATE/attempt-1/plan.json"
```

Review the **actual `plan.json` and `qualification.json`**, full source/tree,
toolchain/source/code hashes, exact argv/environment, system mount policy,
resource budget, checks, versions, actual recorder health and all warnings.
Dry-run and prepared plans have distinct nonces/timestamps; approval binds the
actual prepared plan. If qualification fails, don't proceed or rerun into the same
job; preserve failure evidence. This assignment does not invoke the next actions.
Only after the owner has reviewed and explicitly accepted that exact plan:

```sh
bt037 approve --plan "$BT_PRIVATE/attempt-1/plan.json" --review-ref 'OWNER-EXACT-PLAN-REVIEW-REF' --output "$BT_PRIVATE/owner-approval.json"
bt037 build --plan "$BT_PRIVATE/attempt-1/plan.json" --approval "$BT_PRIVATE/owner-approval.json"
```

Approval is a private local owner declaration, not a digital signature or trusted
UTC proof. It binds plan/source/code/toolchain/limits/host boot, qualification digest,
owner reference, inference HOLD, 15-minute expiry and one attempt. Qualification
must be <30 minutes old by wall and monotonic clocks on the same boot. The attempt
is exclusively recorded before configure launches; failed/stopped attempts are
spent. Another invocation refuses. No silent retries or budget increases.

At any time in another terminal:

```sh
bt037 stop --plan "$BT_PRIVATE/attempt-1/plan.json"
```

This writes only an own STOP request; the watchdog stops the running worker group.
Don't delete STOP/attempt/result/qualification records to rerun. Logs, CMakeCache,
partial objects and staged evidence are retained on failure. Do not delete failed
cgroups or other jobs automatically; unverified cleanup requires owner review.
For an **untouched preparation only**, the prepare response's pinned receipt permits
`bt037 rollback --job ... --receipt-sha256 ...` (dry-run; optional `--apply`). New
qualification/build/foreign/edited files cause refusal, preserving evidence; this
is deliberately not a recursive post-build data deletion command.

## Build result and remaining provenance gates

Both steps capture bounded combined logs. Unused manually specified variables,
network fetching/updating, unexpected fallback or stale embedded UI produce failure.
The known no-embedded-UI warning is retained, not repaired by downloading assets.
Every expected 036 security flag must match CMakeCache exactly after configure.
No executable install or patching occurs. Audit/filter auxiliary-loader dependency tags are rejected rather than omitted from closure.
Staging copies only new `build/bin`
CLI/shared-library candidates, relative in-tree aliases, hashes and sizes; passively
checks ELF/SONAME/DT_NEEDED/PT_INTERP/search paths and the explicit system closure.
Standard-library shadowing/ambiguity, missing local/system dependency or unsafe
search entry fails. Exact build arrays, clean environment, source/tree/tool hashes,
installed package/copyright reports, measured versions, warnings/cache and artifact
inventory remain reviewable in the private job and `result.json`.

`LOCAL_BUILD_PASS_INFERENCE_HOLD` means only that this local build and its passive
postchecks passed. It does not establish independent reproducibility, upstream
binary authenticity, vulnerability clearance, legal adequacy, full inference
containment or model provenance. Two independently witnessed clean builds still
must compare all bytes/alias chains and normalized source/toolchain/environment/
flags/logs and explain nondeterminism. CODEX035 is unchanged and does not accept
these local hashes as independent expectations. No automatic runtime admission.
The prior model SHA-256
`6a1a2eb6d15622bf3c96857206351ba97e1af16c30d7a74ee38970e434e9407e`
is **owner-reported local evidence, not independently publisher-verified**.
No model file was accessed, downloaded, copied or loaded; publisher/license
confirmation and genuine inference remain HOLD.

Smallest owner action: review this draft, then run only offline regression,
input inventory, source preparation and harmless target qualification. Review
that actual plan/proof before deciding on the single controlled compilation.
STOP FOR OWNER AND BOSS AI REVIEW.

## Recorded offline evidence (2026-11-28)

| Exact command / observation | Result |
|---|---|
| `/usr/bin/python3 --version` | Python 3.13.5 |
| `/usr/bin/python3 -B -m unittest discover -s tests -p test_controlled_build_037.py -v` | 39 passed, 3.784s |
| `/usr/bin/python3 -B -m unittest discover -s tests -v` | 647 passed, 11.585s; 608 baseline +39 new, no skips |
| `python -B -m unittest discover -s tests -v` (Python 3.12.14) | 647 passed, 11.355s; no skips |
| `node tests/test_paper_029.cjs` | 26 checks passed |
| `node tests/test_restore_030.cjs` | 14 checks passed |
| `node tests/test_market_031.cjs` | 8 controlled groups passed |
| Existing `bwrap --unshare-all --die-with-parent --ro-bind /usr /usr --symlink usr/lib /lib --symlink usr/lib64 /lib64 --proc /proc --dev /dev -- /usr/bin/true` | exit 1: `loopback: Failed to create NETLINK_ROUTE socket: Operation not permitted` |
| Delegation visibility | `/sys/fs/cgroup/cgroup.controllers` lists `cpuset cpu io memory hugetlb pids`; delegation writes unavailable to this cloud user. No cgroup creation/limit/stress guarantee claimed. |
| `/usr/bin/cmake` | Absent here; no installation attempted. Target availability is a prerequisite. |

Python 3.13 emitted **10 inherited `ResourceWarning: unclosed database` warnings**
from existing SQLite test/demo connection lifetimes (garbage collection reports
some in mock/test cleanup). All assertions passed; warnings were not suppressed,
reclassified or claimed fixed. The five added files do not change existing SQLite
code/fixtures. A warning-free legacy fixture cleanup remains separate bounded
maintenance, not evidence of recorder access or a live database operation here.

New tests cover real harmless success/nice/one-CPU affinity, wall timeout, CPU
rlimit exhaustion, log flood/cap, nonzero exit, direct-child reap, health-loss stop,
no spawn after failed precheck, attachment-before-release and failure, mocked
aggregate cgroup CPU accounting, source group-write/data corruption/symlink
refusal, private independent read-only export/untracked exclusion, concurrent
source change, protected overlap, Debian compiler aliases, cache/security-flag
checks, explicit system policy/missing fallback, health timestamps/identity/
stability, monitor no fabricated freshness, one-shot approval/expiry/inference
scope, concurrency exclusion, failure evidence and scope-cleanup failure.

The orchestration success test **injects** cgroup, namespace/toolchain validation
and staging dependencies; it still executes the real process supervisor and fixed
inert compiler substitutes. It is not an actual contained compiler qualification.
`docs/evidence/controlled-build-037-synthetic.json` distinguishes these injected
controls from measured subprocess behavior and records an expected refusal on
second invocation. No real compilation, target guarantee, market or AI output was
fabricated. Kernel memory/PID/swap limits, descendant-cgroup kill/empty behavior,
no-network namespace, read-only mounts and file-only loader resolution must still
be measured by the owner's exact `qualify` command; unavailable capabilities cause
refusal, never fallback. Installed toolchain closure completeness, publisher/model
identity/licensing and reproducibility remain independently unverified.

## Authorized ELF string-table compatibility hotfix (2026-11-28)

The owner reported Debian `libstdc++.so.6` with DT_STRSZ **308,098** bytes,
exceeding CODEX035's old 65,536-byte dynamic string-table limit. The shared passive
reader now permits **at most 1,048,576 bytes (1 MiB) for DT_STRTAB/DT_STRSZ only**.
PT_INTERP and PT_DYNAMIC entry metadata reads remain capped at **65,536 bytes**.
The 128 MiB full-ELF cap and SHA-256 binding remain unchanged. The selected
PT_LOAD must contain the complete table, fit within the actual file, and have
p_filesz <= p_memsz. Reads explicitly reject offsets/spans outside the file;
invalid string offsets, missing terminators, absent/zero/oversized tables,
misaligned dynamic entries and truncated metadata still refuse. This is no
change to library trust, source permissions, containment, budgets or inference.

The same failure was independently reproduced by **read-only inspection of this
cloud runner's installed library**, not the owner's desktop:

* `/usr/lib/x86_64-linux-gnu/libstdc++.so.6.0.33`, 2,497,768 bytes.
* SHA-256 `972bb2a18b71140dab0240f8a1f68ab3fb1d56bcd4c4f824a91b70888faf5a00`.
* Measured DT_STRSZ 308,098 bytes. Original parser: `ELF_STRING_TABLE`.
  Corrected CODEX037 passive consumer: PASS; SONAME `libstdc++.so.6`, dependencies
  `libm.so.6`, `libc.so.6`, `ld-linux-x86-64.so.2`, `libgcc_s.so.1`.

This read did not load/execute or modify the library. It is parser compatibility
proof, not authentication of the owner's library or toolchain/license clearance.
See `docs/evidence/controlled-build-037-elf-hotfix.json` for exact recorded evidence.

| Command | Actual result |
|---|---|
| `/usr/bin/python3 -B -m unittest discover -s tests -p test_elf_string_table_037.py -v` | 15 passed, 0.041s |
| `/usr/bin/python3 -B -m unittest discover -s tests -p test_owner_qualification_035.py -v` | 26 passed, 0.793s |
| `/usr/bin/python3 -B -m unittest discover -s tests -p test_controlled_build_037.py -v` | 39 passed, 2.785s |
| `/usr/bin/python3 -B -m unittest discover -s tests -v` (3.13.5) | 662 passed, 12.067s; no skips |
| `python -B -m unittest discover -s tests -v` (3.12.14) | 662 passed, 11.432s; no skips |

The 15 new synthetic regressions use end-of-table names beyond 64 KiB, the actual
Debian-sized table, 64 KiB/64 KiB+1/exact 1 MiB success and 1 MiB+1 refusal. They
also cover full-file/segment boundaries, invalid p_filesz/p_memsz, absent metadata,
invalid offsets/termination, hash corruption, dynamic-entry alignment and unchanged
64 KiB limits for unrelated interpreter/dynamic metadata. The inherited Python
3.13 SQLite ResourceWarnings remain recorded; they were not suppressed or fixed.

Owner next action: review the revised draft, update the reviewed local checkout,
rerun these tests and regenerate/review the target inventory and exact plan before
any separately approved build attempt. All target-containment, recorder-health,
model publisher/license and independent-reproducibility gaps above remain.
No actual compilation, inference, system-library modifications, merge or workflow
dispatch. Additional spending NT$0. STOP FOR OWNER AND BOSS AI REVIEW.

## Authorized Hotfix #2 — process/build cgroup memory headroom (2026-11-28)

Reviewed parent `048c2e89a1f79ee56ff2c3730379d64a36c10ed0`. Owner reports 662/662
local tests and successful toolchain inventory, then `RAM_HEADROOM_HOLD` despite
kernel `MemAvailable: 5678440 kB`, absent root memory.max/current and unlimited
configured delegation memory.max/high. These are **owner observations**, not new
Codex desktop measurements. The old detector assumed memory.max existed directly
at `/sys/fs/cgroup` and returned zero on its absence.

`research.memory_headroom_037.snapshot` now reads actual unified process membership
from `/proc/self/cgroup` and maps it through `/proc/self/mountinfo`. It walks both
the process and configured build-parent ancestor chains to the visible global
cgroup-v2 root, deduplicating shared ancestors. For each applicable finite
memory.max **and memory.high**, remaining capacity is `max(0, limit-current)`.
Effective available memory is the minimum of all such capacities and kernel
MemAvailable. `max` means unlimited and causes no extra subtraction. Linux kB is
converted using 1024 bytes. Root memory interfaces may legitimately all be absent;
this is not zero physical memory. The synthetic reproduction of the reported
Debian hierarchy yields **5,814,722,560 bytes**, above **4,294,967,296 bytes (4 GiB)**.

The configured build **parent** is inspected; the future child **3 GiB compilation
ceiling** is neither increased nor subtracted as if it were host headroom. The
supervisor's own cgroup constraints are checked too. Finite sibling/ancestor
constraints can still yield RAM_HEADROOM_HOLD even when global RAM is plentiful.

No optimistic fallback: unreadable values, partial/nonroot missing interfaces,
invalid/negative/overflowing numbers, unknown scope, ambiguous mounts, cgroup-v1
memory profiles, hidden mount ancestors and changing membership/limits fail
closed. Nonroot all-absent interfaces are accepted only with readable proof the
parent has not enabled memory, and the ancestors still constrain capacity.
The node must exist and have readable cgroup.type. A nominal mount root that
exposes nonroot-style memory interfaces requires namespace/hidden-ancestor review
and returns HOLD rather than assuming no outer ceiling. Unsupported profiles are
reported, never repaired by changing system state. Snapshots are point-in-time
observations, not reservations or a guarantee of future free RAM.

CODEX036's integer `resources()` API delegates to the new detector and stays
compatible; CODEX037 passes the existing config's `cgroup_parent`, records the
memory evidence in the new plan and rechecks before qualification/build. The
4 GiB available-memory floor, 3 GiB child memory.max, zero swap, one CPU, PIDs,
watchdogs, source/ELF/trust and all containment checks remain unchanged. The new
memory module is included in the plan's pinned code inventory.

### Preserve existing inputs; inspect before another attempt

No new configuration keys or inventory format changes are required. Existing
config/toolchain/system-library JSON can be reused if their paths, versions,
hashes and license review remain valid. The hotfix does not edit, regenerate or
overwrite them. Their historical code hashes remain historical evidence; the new
plan independently binds the current supervisor/worker/memory-module code. Do not
reuse old plan approvals or qualification receipts for changed code.

Run from the reviewed updated checkout using the existing `bt037` shell helper:

```sh
bt037 preflight --config "$BT_PRIVATE/config.json"
```

This is a new **read-only** survey using the existing config. It reports checks
individually instead of hiding later issues behind the first failed check. It
reads memory hierarchy evidence, CPU flags, current tool hashes, existing input
review/hashes, library closure, destination/path/disk compatibility, delegated
controller readiness and recorder health. It creates no source/build directories,
processes, namespaces, cgroups, locks or report files. Exit 2 means a reported
HOLD; exit 0 means only readiness to review harmless qualification. `qualified`
remains false in either case. It does not grant compilation or inference authority.

Then review the report. Existing `prepare --config ...` remains dry-run by default.
If the earlier failure was RAM_HEADROOM_HOLD, that check occurred before job
creation, so the same still-unused destination normally remains compatible.
An existing destination or partial evidence is not automatically removed or
resumed. Preserve it for review; do not delete or rewrite inventory/config to
silence a refusal. Source content is still authenticated again by prepare; the
survey explicitly defers that expensive check instead of claiming fresh source
verification from the owner's previous run.

### Remaining target-specific assumptions inspected

| Assumption / possible blocker | Survey or next mandatory evidence |
|---|---|
| True global cgroup-v2 hierarchy is visible; other ancestor limits may constrain the process or build parent | New memory report lists exact paths, max/high/current and effective bytes. Hidden/namespaced or ambiguous roots HOLD. |
| Existing private delegation is user-owned, below `/sys/fs/cgroup`, with cpu/memory/pids already enabled and writable | Read-only survey checks ownership/controller/access flags and leftovers. No auto-enable, sudo or chown. Nonstandard mount profiles may still fail existing containment. |
| Child limits, zero-swap interface, cgroup.kill, directory flock, aggregate CPU/PID ancestor capacity and detached-descendant cleanup work | **UNVERIFIED until existing harmless qualify.** Read-only metadata/access flags do not prove child writes/readback/kill. Lower ancestor CPU quotas or PID limits may throttle/fail an attempt; no limit is raised. |
| Installed tools use supported fixed `/usr/bin` paths and resolve under `/usr`; Debian compiler alternatives and usrmerge profile are supported | Survey reuses tools_inventory; prior successful local inventory is owner evidence, not an excuse to skip current hashes. Non-usrmerge/other tool profiles require review. |
| Reviewed loader/library manifest still matches hashes, SONAME and transitive closure; DT_STRSZ <=1 MiB | Survey reuses existing corrected passive verifier. File-only loader execution remains the harmless qualification probe, not inference. |
| Job parent/config/code/health paths meet existing strict ownership/ACL/symlink policy; job unused; 4 GiB disk free before build | Survey checks existing path/disk rules. Original group-writable source remains only the authenticated read-input exception. No automatic permission changes. |
| Recorder producer reports actual healthy/stable status, fresh measurement <=30s and actual collection <=2 cadences+30s | Survey reads existing health input. Missing feed is a qualification/build HOLD, not proof the operational recorder failed and not a new restriction on harmless source export. Cadence is actual collection cadence, not candle length. |
| CMake recognizes every security flag and emits the expected cache; no downloading or unexpected fallback | Still requires separately reviewed controlled configure. No flags relaxed, no install/download or configure performed to predict success. |
| All gates can be closed solely from metadata/synthetic success | False. Qualification, actual target behavior, runtime/model publisher/license evidence and independent reproducibility remain separate HOLDs. |

The survey does not promise no further target-specific blocker. It exposes current
read-only incompatibilities and separates them from the kernel/namespace/loader
behavior that cannot be verified without the already designed harmless target
qualification. No actual compilation or genuine inference was performed here.

### Hotfix #2 verification

| Exact command | Actual result |
|---|---|
| `/usr/bin/python3 -B -m unittest discover -s tests -p test_memory_headroom_037.py -v` | 33 passed, 0.013s |
| `/usr/bin/python3 -B -m unittest discover -s tests -p test_controlled_build_037.py -v` | 39 passed, 2.859s |
| `/usr/bin/python3 -B -m unittest discover -s tests -p test_portable_runtime_036.py -v` | 30 passed, 0.618s |
| `/usr/bin/python3 -B -m unittest discover -s tests -v` (Python 3.13.5) | 695 passed, 12.212s; 662 baseline +33 new; no skips |
| `python -B -m unittest discover -s tests -v` (Python 3.12.14) | 695 passed, 11.093s; no skips |

The new deterministic cases reproduce missing global-root interfaces/unlimited
Debian delegation, root process membership, finite process/sibling build and
shared ancestors, memory.high, exhausted limits, exact 4 GiB boundary/one byte
below, unreadable/partial/invalid/missing data, disabled controllers, migration,
changing limits, escaped/ambiguous/subtree mounts and namespace-root ambiguity.
Survey tests prove multiple holds are reported without writes/spawns or config/
inventory byte changes; READY survey does not become qualified containment.
See `docs/evidence/controlled-build-037-memory-hotfix.json` for labeled synthetic
results. Python 3.13's 10 inherited SQLite ResourceWarnings remain unsuppressed.

Next owner action: review this revised draft and run the single read-only preflight
against the **existing** config. Review all HOLD/UNVERIFIED results, then review
fresh preparation/qualification evidence before any separately authorized build.
No actual compilation, inference, system modifications, merge, workflow dispatch
or additional expenditure. AEP Gate B HOLD; BUY AUTHORIZATION NONE. STOP FOR OWNER
AND BOSS AI REVIEW.
