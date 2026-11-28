# CODEX 038 — Windows host supervision and controlled build admission

Issue #71. Stack a separate draft on **unchanged PR #70** at
`4f5cbd8dbeceee05017126b1f11071ee6d06e7d6`.

Delivered: executable PowerShell host probes/supervisor and Windows harmless
harness; an SSH-bound guest challenge/receipt service; operational supervision
proof, stop and validation utilities; scoped integration into CODEX037 admission.
**No actual Windows execution, SSH/VirtualBox qualification, compilation or inference
occurred here. Windows qualification and owner approval remain HOLD.** REAL_NOT_RUN;
AEP Gate B HOLD; BUY AUTHORIZATION NONE. NT$0 additional spending. No installs,
settings/firewall/SSH/unit changes, deployment, merge, workflow dispatch, trading,
recorder/AEP/model/original runtime/source/strategy or ZUMERAVO changes.

## Admission semantics: operational supervision is not hardware stability

The old config continues to refuse the guest-only recorder observer with
PHYSICAL_HOST_STABILITY_HOLD. Its desktop_stable=false semantics are unchanged.
An explicitly reviewed **new optional policy** may instead require all of:

1. Genuine live/fresh CODEX037 recorder observer, actual collection timestamps,
   900s cadence, no unhealthy/stale/source/unit error.
2. A fresh owner Windows process running the exact reviewed scripts, bounded
   read-only host/VM measurements, an existing verified authenticated SSH channel
   to the exact plan/guest boot/recorder-observer scope, current receipts and no STOP.
3. Harmless continuous supervision proof (>=3 accepted challenges over 16s), plus
   all existing real namespace/cgroup/toolchain/loader qualification requirements.
4. Explicit owner acceptance of `windows-operational-supervision-038-v1` and
   `UNRESOLVED_NOT_HARDWARE_SAFETY`, bound to the same qualified host session in a
   one-use approval. Policy acceptance alone cannot substitute for evidence.

The new policy never flips desktop_stable to true or calls hardware verified.
Guest/host software responsiveness does **not** establish physical hardware safety,
resolve BIOS freezes, certify UTC accuracy or predict the next freeze. The owner's
reported hardware fault remains unresolved and is carried separately in all new
host results/approvals. This is a proposed operational admission contract requiring
owner/BOSS AI review, not compilation permission from this assignment.

## Implemented protocol and trust boundary

The receiver is invoked as one existing SSH remote command; no listener, service,
new key, task or persistent deployment is created. Windows uses existing OpenSSH
on **127.0.0.1:2222**, default user tazmanked. It requires a pre-existing verified
known_hosts file, StrictHostKeyChecking=yes, UpdateHostKeys=no, BatchMode=yes,
ConnectTimeout=5, ConnectionAttempts=1, bounded server-alive checks, no agent/local
forwarding or local commands, no proxy, and no config-file fallback (`-F none`).
An existing agent/default key or explicit existing IdentityFile is required. A
password-only setup or blocked script policy is HOLD: no passwords collected,
TOFU, keyscan acceptance, credential logging, SSH reconfiguration, execution-policy
bypass or package installation is offered.

The guest requires SSH_CONNECTION matching the explicitly reviewed peer and guest
port 22, plus a real privileged sshd/sshd-session ancestor. A private current
receiver PID/start-time/boot/code identity and exact command-line plan binding are
checked by consumers. Transport context alone, a generic JSON file, an arbitrary
host boolean or a forged current nonreceiver PID does not satisfy admission.

Each session has a cryptographic random guest session/challenge. Each accepted
frame consumes its exact sequence/challenge and receives a fresh challenge. Bindings
include canonical reviewed plan SHA, guest boot, exact recorder observer PID/start/
boot/session/code, VM UUID and reviewed PowerShell script bytes. Windows checks
these bindings and every ACK. Replay, reordering, duplicate/pipelined, stale,
malformed/nonfinite, wrong plan/VM/boot/observer/script, host process/reboot/tool
change or clock-gap evidence terminates the session. Errors cannot be healed by
refreshing a timestamp. A new session is explicit and invalidates old qualification
and approval bindings; STOP/attempt markers are never automatically cleared.

Evidence is 0600 atomic private JSON in a user-owned 0700 directory with an
exclusive regular-file lock, inode checks, receipt hash/scope and live receiver
identity. EOF, disconnect, STOP, duration expiry or failed measurement revokes it.
Consumer checks use guest monotonic, CLOCK_BOOTTIME and wall receipt age, each
bounded at **15 seconds**. Guest receipt age is not an unauthenticated host UTC
claim. Host timing combines Stopwatch elapsed, UTC deltas, boot identity and fresh
Windows uptime counters. Five-second heartbeat cadence, <=4s host probe and relative
clock-delta checks are operational bounds, not a two-second trusted-UTC accuracy
claim. Existing NTS/UTC/inference gates are not cleared.

**Trust assumptions:** the owner controls and reviews the Windows process, keys,
script copies and selected VM; guest kernel/sshd and the same guest UID's private
files/code are trusted. A root/credential-holder or hostile same-UID process can
subvert measurements/code/private evidence. SSH authentication protects transport;
JSON platform/hash assertions are not remote Windows/hardware attestation. The
production receiver has no fixture/auth-bypass switch. Test injection is explicitly
synthetic and cannot qualify Windows.

## Read-only Windows observations and process bounds

The host worker reads Win32_OperatingSystem boot identity and the Windows system
uptime performance counter, then **VBoxManage showvminfo UUID --machinereadable**.
It requires the selected VM running and a unique TCP forwarding rule host 2222 to
guest 22 (loopback or existing wildcard host binding). This ties the observed VM
UUID to the existing SSH forwarding route; it never modifies the rule or VM.
Only selected nonsecret fields are transmitted; raw VirtualBox machine metadata
and SSH stderr are not logged. Source scripts and SSH/PowerShell/VirtualBox tool
hashes are fixed for the session. Changing scripts, known_hosts, boot or tools
stops the sender.

CIM commands run in a short-lived existing Windows PowerShell worker; VirtualBox
processes have a 2s timeout/output cap. The outer worker has a 4s timeout, with
bounded asynchronous stream draining. SSH hello/ACK reads have 15s bounds and a
small cap. Owned processes use no shell elevation, install or system changes.
Cleanup targets the exact owned PID/start identity and its tree with existing
taskkill /T, bounded waits and known-descendant checks; ambiguous orphaned pipes,
cleanup failure or uncertain PIDs cause terminal HOLD rather than continuation.
No arbitrary process-name killing or VM shutdown is used.

This is **not** a Windows Job Object/kernel containment guarantee. CIM/OS/storage
stalls or a host freeze can prevent timely cleanup. The guest's receipt expiry,
existing build watchdog and cgroup kill/reap remain independent controls whenever
the guest can execute. Genuine Windows process/stream/cleanup behavior is
UNVERIFIED until the supplied Windows harness is run; Linux source checks are not
Windows execution evidence. Do not proceed from a cleanup warning.

## Freeze, suspend, stop and recovery

Observed host or guest timing gaps >15s, wall/monotonic inconsistencies, uptime
regression, boot changes or lost observer/session immediately refuse continued
admission. The guest proof/build watchdog checks the same session repeatedly,
including between steps and before/after staging; loss spends an actual attempt
and preserves evidence. Guest `host_supervision_038 stop` or Windows Ctrl+C ends
supervision. Even if graceful cleanup fails, a runnable guest refuses on receiver
PID loss/receipt expiry. No retry or automatic session healing.

**If Windows and VM freeze together, the guest cannot execute abort while frozen.**
On resumption, any observable host/guest clock gap expires/poisons the session
before a fresh heartbeat can re-admit it; freeze/resume cases are tested. If all
observed clocks pause/replay coherently, software cannot prove the real elapsed
physical time or prevent the hardware fault. That limitation is not hidden by
calling a resumed guest stable. No hardware-safe guarantee is made; unresolved
physical risk and separate owner approval persist.

## Config, plan, qualification and approval integration

No existing inventory or recorder config bytes are rewritten. `attach-config`
creates a separate new opt-in config with one extra object:

```json
"host_supervision": {
  "policy": "windows-operational-supervision-038-v1",
  "directory": "/home/tazmanked/boss-runtime-037/host-038",
  "vm_uuid": "OWNER_EXISTING_VM_UUID",
  "ssh_peer": "OWNER_VERIFIED_GUEST_SIDE_SSH_PEER",
  "review_ref": "OWNER_OPERATIONAL_POLICY_REVIEW_REF"
}
```

The directory must be private, outside job/source/recorder/health/protected roots.
A fresh unused job can be explicitly selected in the new config. Existing package,
source and library inventory formats/references are reused where hashes still
match. The plan pins guest protocol and both runtime PowerShell script files.
Changed code/policy/boot/source or observer/host sessions require fresh reviewed
plan, qualification and one-use approval; old receipts cannot be relabeled.

`health(plan)` requires the independent recorder observer for this policy, rejects
legacy desktop booleans and checks the host session without editing the recorder
health file. Old configs retain their previous physical HOLD. Config-only
preflight exposes policy and an UNVERIFIED host-session requirement; after plan
creation, `host_supervision_038 check/prove --plan ...` verifies actual supervision.
The existing qualification includes the continuous proof before the existing
namespace/cgroup/loader tests. The approval must acknowledge the operational
policy explicitly and bind the identical current qualified host session; build
monitoring rejects changes/loss throughout. No step reduces the limits below.

Unchanged: 4 GiB headroom, 3 GiB child memory, swap zero, 64 PIDs, one CPU affinity
and quota/job, nice +10, 7200s wall/5400s aggregate CPU, bounded logs, code/source/
library trust, recorder freshness, cgroup kill/reap, one attempt and no retry.
Genuine inference/AEP Gate B HOLD; orders NONE. The implementation can support a
future separately authorized attempt; none is dispatched here.

## Consolidated owner-side harmless validation sequence

Review this draft and the explicit policy first. Use an ordinary **non-elevated**
Windows PowerShell terminal, the existing known host key/SSH credentials and exact
existing VM identity. No ExecutionPolicy/SSHD/firewall/VirtualBox changes, installs,
new keys, machine restarts or compile/inference commands appear below.

### 1. Debian: keep the current genuine recorder observer running

From the reviewed new checkout, compare Git head with the final report. Keep the
CODEX037 observer alive (existing config and 900s cadence); do not restart it once
the host session is bound. If restarting is necessary, revoke the old session and
review a new plan/session/qualification. Run existing offline checks:

```sh
git rev-parse HEAD
/usr/bin/python3 -B -m unittest discover -s tests -p test_host_supervision_038.py -v
/usr/bin/python3 -B -m unittest discover -s tests -v
```

Confirm the guest-side SSH peer from an **existing verified Windows SSH session**
(`printenv SSH_CONNECTION`); do not guess it. With the existing config/inventories,
create a new config and private evidence directory. Fill actual VM UUID/peer:

```sh
/usr/bin/python3 -B -m research.host_supervision_038 attach-config --config "$BT_PRIVATE/config.json" --output "$BT_PRIVATE/config-038.json" --directory "$BT_PRIVATE/host-038" --vm-uuid ACTUAL_EXISTING_VM_UUID --ssh-peer ACTUAL_VERIFIED_PEER --review-ref OWNER_POLICY_REVIEW_REF --job "$BT_PRIVATE/attempt-038"
/usr/bin/python3 -B -m research.controlled_build_037 preflight --config "$BT_PRIVATE/config-038.json"
/usr/bin/python3 -B -m research.controlled_build_037 prepare --config "$BT_PRIVATE/config-038.json"
# Review dry-run; --apply only exports source and creates the fresh plan, not a build:
/usr/bin/python3 -B -m research.controlled_build_037 prepare --config "$BT_PRIVATE/config-038.json" --apply
/usr/bin/python3 -B -m research.controlled_build_037 status --plan "$BT_PRIVATE/attempt-038/plan.json"
```

Review that actual plan SHA/boot/source/tools/scripts/budgets; copy only its SHA
for the next step. If any HOLD/refusal appears, stop rather than altering data or
limits. No source export or actual target plan was created by Codex on the owner
machine. Config-only preflight is not proof of the host channel.

### 2. Windows: obtain the exact reviewed scripts, parse and test harmlessly

Use byte-preserving copies from the reviewed guest checkout to a **new local task
folder**, not copy/paste that changes line endings. Example with existing OpenSSH:

```powershell
$Ssh="$env:SystemRoot\System32\OpenSSH\ssh.exe"
$Scp="$env:SystemRoot\System32\OpenSSH\scp.exe"
$VBox='C:\Program Files\Oracle\VirtualBox\VBoxManage.exe'
$KnownHosts=Join-Path $HOME '.ssh\known_hosts'
$Task=Join-Path $HOME 'boss-038-review'
New-Item -ItemType Directory -Path $Task -ErrorAction Stop | Out-Null
# Replace guest repo path with the actual reviewed checkout; no spaces/control chars in this protocol profile.
$GuestRepo='/home/tazmanked/boss-trader-lab'
foreach ($File in @('HostSupervisor038.ps1','HostProbe038.ps1','Test-HostSupervisor038.ps1')) {
  & $Scp -F none -P 2222 -o StrictHostKeyChecking=yes -o UpdateHostKeys=no -o BatchMode=yes "tazmanked@127.0.0.1:$GuestRepo/research/windows_038/$File" $Task
  if ($LASTEXITCODE -ne 0) { throw 'Verified source copy failed; no key/policy bypass' }
}
& "$Task\Test-HostSupervisor038.ps1" -IncludeHarmlessProcesses
```

The harness parses PowerShell, tests argument quoting/SSH policy and bounded
harmless child timeout/cleanup; it does not qualify VirtualBox, SSH or a build.
If script policy prevents execution, **HOLD**; do not bypass it. If credentials
are not available in the existing agent/default keys, HOLD; an existing identity
file may be explicitly supplied to the supervisor, never stored in this repo.
The example source copy assumes that same existing authentication already works.

Supply the existing VM UUID (read-only lookup of the **specific known Debian VM**
is possible with existing VBoxManage showvminfo; do not modify/register/start it).
Then make an actual bounded host/VM observation, still without any SSH heartbeat:

```powershell
$VmUuid='ACTUAL_EXISTING_VM_UUID'
& "$Task\HostSupervisor038.ps1" -ProbeOnly -VmUuid $VmUuid -VBoxManagePath $VBox
```

Review real output, timings and cleanup. Failure is HOLD, not permission to raise
limits or install dependencies. This step is **not run/qualified by Linux tests**.

### 3. Windows + Debian: one bounded authenticated observation session

After reviewing the prepared plan, set the exact path and SHA printed by Debian:

```powershell
$GuestPlan='/home/tazmanked/boss-runtime-037/attempt-038/plan.json'
$PlanSha='ACTUAL_REVIEWED_64_HEX_PLAN_SHA'
& "$Task\HostSupervisor038.ps1" -GuestRepo $GuestRepo -GuestPlan $GuestPlan -PlanSha256 $PlanSha -VmUuid $VmUuid -KnownHosts $KnownHosts -VBoxManagePath $VBox -Seconds 120
```

During that session in a second Debian terminal:

```sh
/usr/bin/python3 -B -m research.host_supervision_038 check --plan "$BT_PRIVATE/attempt-038/plan.json"
/usr/bin/python3 -B -m research.host_supervision_038 prove --plan "$BT_PRIVATE/attempt-038/plan.json"
```

Expected only with genuine evidence: fresh operational session, same reviewed plan
and observer, >=3 heartbeats, hardware uncertainty UNRESOLVED. This does not run
full containment qualification or authorize compilation. Source/helper bytes must
match exactly; Windows CRLF rewriting is refused, not patched around.

Stop from Debian, or Ctrl+C the Windows supervisor:

```sh
/usr/bin/python3 -B -m research.host_supervision_038 stop --plan "$BT_PRIVATE/attempt-038/plan.json"
/usr/bin/python3 -B -m research.host_supervision_038 check --plan "$BT_PRIVATE/attempt-038/plan.json"
```

The second command must refuse. Planned duration/EOF also revokes; a final Windows
HOLD/EOF on the bounded session's end is expected. Do not remove STOP or attempt
markers to revive it. An explicit later `-NewSession` can replace only a recognized
stopped/dead receiver; it cannot replace a live one, and still requires a fresh
qualified binding/approval. Prefer a newly reviewed config/plan when recovering
from STOP, reboot, observer restart or uncertainty. No automatic reconnect/retry.

No `approve`, `build`, CMake, model/tokenizer, VM-setting or service-control command
is in this validation sequence. A future authorized build would additionally need
real containment/loader qualification, a matching session proof and the new
explicit approval-policy acknowledgement; that decision is outside this run.

## Verification and remaining blockers

See `docs/evidence/windows-host-supervision-038.json` for provenance. Protocol
fixtures and shortened-TTL anonymous-pipe receiver tests **inject SSH/observer
context**; they are not authenticated SSH or Windows proof. Real local harmless
workers demonstrate timeout/supervision-loss kill and direct-child reap; kernel
cgroup behavior is not certified by injected fake groups. Windows tests, host/VM
measurements and real verified SSH remain UNVERIFIED because no Windows runtime
is available here. PowerShell source inspection is not a Windows syntax/runtime
qualification. Owner must run the supplied harness/probe/transport sequence.

Full baseline CODEX037 tests remain included. Inherited SQLite ResourceWarnings
are recorded, not suppressed. No physical fault diagnosis, trusted UTC, package
vulnerability/license clearance, model publisher identity or reproducible runtime
build is established. Smallest safe owner action: review the draft/policy and run
only this harmless two-machine sequence; keep compilation/inference HOLD.

STOP FOR OWNER AND BOSS AI REVIEW.

### Recorded offline verification (2026-11-28)

| Exact command / observation | Actual result |
|---|---|
| `/usr/bin/python3 -B -m unittest discover -s tests -p test_host_supervision_038.py -v` | 41 passed, 1.731s |
| `/usr/bin/python3 -B -m unittest discover -s tests -v` (Python 3.13.5) | 776 passed, 13.325s; 735 baseline +41 new; no skips |
| `python -B -m unittest discover -s tests -v` (Python 3.12.14) | 776 passed, 14.187s; no skips |
| `command -v pwsh` / `command -v powershell` | neither executable available; Windows harness NOT RUN |
| Actual Windows/CIM/VirtualBox/verified-SSH channel | UNVERIFIED, no owner-host access |

Ten inherited Python 3.13 SQLite ResourceWarnings remain unsuppressed. New tests
exercise positive/negative challenges, replay/sequence/scope/boot/script/VM/tool
identity, malformed/foreign/stale evidence, clocks/freeze/resume and terminal
recovery, PID/command binding, private atomic/concurrent publication, STOP/EOF/
timeout pipe revocation, config preservation, multiple-heartbeat proof and loss
cleanup, scoped approvals/one attempt, staging loss and no session-token logging.
Anonymous-pipe tests use shortened test-only TTL and **injected SSH/observer trust**;
production TTL is fixed at 15s and CLI has no injection option. Windows source
safety assertions are structural checks only. No Windows or hardware PASS is
inferred from these tests. Consolidated owner validation above is the next step.

Existing offline Node regressions also passed: `node tests/test_paper_029.cjs`
26 checks; `node tests/test_restore_030.cjs` 14 checks; `node tests/test_market_031.cjs`
8 controlled groups. These are controlled dependency tests, not native browser
persistence or actual market requests.
