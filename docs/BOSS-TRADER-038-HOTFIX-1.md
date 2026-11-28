# CODEX 038 Hotfix #1 — owner review

Date: 2026-11-29 Asia/Taipei. Issue #71; existing Draft PR #72.
Parent: `080c4cdce021d5b7d99123feb3a0f084708185f2`.
PR #70 and CODEX037 implementation are unchanged.

## Implementation and bounds

`HostProbe038.ps1` replaces only the unavailable performance-CIM uptime source
with `kernel32.dll!GetTickCount64`. Boot identity still comes from
`Win32_OperatingSystem.LastBootUpTime`; owned-tree cleanup still uses Win32_Process.
No WMI repair, registry edits or alternative fabricated uptime is attempted.
The return is strictly UInt64 milliseconds, floored with decimal arithmetic to
whole seconds. Signed/floating/string/zero/subsecond and protocol-overflow values
are refused. No 32-bit GetTickCount fallback is present. The receiver's existing
boot/session identity, guest clocks and host uptime/wall/elapsed consistency checks
are unchanged, including terminal refusal after suspend/gap or backwards counter.
This is operational timing evidence, not authenticated UTC or hardware stability.

The P/Invoke binding uses a run-only Reflection.Emit dynamic assembly, cached once
per worker process. There is no external C# compiler, temporary source/DLL file,
assembly save, package, persistent registration, policy change or native-library
search-path change. Normal CLR JIT and OS-managed logging/paging remain possible;
this is not a claim that Windows writes nothing. The binding is expected to need
normal full-language .NET permissions: a denied binding remains HOLD; never loosen
policy. A new worker is started each heartbeat, so cold CLR/binding cost recurs.
The harness prints actual cold/warm milliseconds when run on Windows. Those
figures alone cannot qualify the full cold worker with CIM and VBox overhead.

The existing **2,000ms VBox process** and **4,000ms outer probe worker** deadlines,
output caps, cleanup bounds, **5s heartbeat /15s expiry**, SSH host-key checking,
credential handling, session protocol and build/recorder resource controls remain.
Existing cleanup may take its previously bounded additional time after a timeout;
the four-second deadline is not a promise of total wall time including cleanup.
If cold startup does not fit, report HOLD and the sanitized stage; do not enlarge
limits or reuse a stale result. No compilation/inference/admission authority is added.

Failures now emit bounded `CODEX038|STAGE|REASON|0xHRESULT` codes. Stages distinguish
BOOT_CIM, NATIVE_BIND, NATIVE_CALL, NATIVE_UNITS, VBOX_PROCESS, VBOX_PARSE,
WORKER_PROCESS, SSH_CONNECT, SSH_PROTOCOL, SUPERVISOR and CLEANUP. Only exact-format
child diagnostics and an explicit list of internal reason codes are preserved.
Raw stderr, exception messages, paths, session tokens and credentials are not logged.
HRESULT extraction follows at most four inner exceptions; it is diagnostic context,
not authentication. Cleanup uncertainty overrides the original failure and refuses.

## Evidence provenance and tests

Owner evidence at the parent head: genuine PowerShell 5.1 and 17/17 Windows harmless
harness PASS; encrypted noninteractive SSH PASS; boot-time CIM PASS. Host probe HOLD:
missing Win32_PerfFormattedData_PerfOS_System, Invalid class 0x80041010. These are
owner-reported target results, not rerun by Codex and not evidence for this revision.

Codex Linux offline results (no Windows PowerShell present):

| Command | Result |
| --- | --- |
| `python -B -m unittest discover -s tests -p 'test_*038.py' -v` | 50 PASS; 41 existing +9 new Python cases |
| `python -B -m unittest discover -s tests -v` | 785 PASS; Python 3.12.14 |
| `/usr/bin/python3 -B -m unittest discover -s tests -v` | 785 PASS; Python 3.13.5 |
| `node tests/test_paper_029.cjs` | 26 PASS |
| `node tests/test_restore_030.cjs` | 14 PASS |
| `node tests/test_market_031.cjs` | 8 groups PASS |

Python 3.13 still emits 10 inherited SQLite unclosed-connection ResourceWarnings;
they were not suppressed. Python protocol regressions cover the DWORD rollover
boundary, backwards/rolled uptime, milliseconds erroneously sent as seconds,
invalid/NaN/infinite/oversized values, reboot and suspend/gap refusals. Source
contracts check removed performance-CIM dependency, UInt64 run-only binding,
diagnostic sanitization and unchanged budgets. They do not execute PowerShell.

The expanded Windows harness adds real harmless native cold/warm calls and cache
checks; synthetic unit/type/boundary cases; injected native invocation failure;
HRESULT preservation/sanitization; a mock missing-performance-class environment;
boot-CIM failure; bounded child diagnostic propagation and raw-stderr refusal.
**Revised Windows parsing, native API execution, runtime memory/artifact observation,
full probe timing and SSH heartbeat remain UNVERIFIED until owner execution.**
No genuine Windows test count is claimed for the new harness.

## Consolidated Debian validation

Use a separate review worktree; leave the current recorder/checkout/config intact.
Set REVIEWED_HEAD to the exact revised hash from the delivery report. Stop on any
failure or local conflict. Repository fetching is only source update, not a package
or model download. These commands do not prepare or execute a build:

```sh
cd /home/tazmanked/boss-trader-lab
REVIEWED_HEAD=PASTE_EXACT_REVISED_HEAD_FROM_REPORT
git fetch origin research/issue-71-windows-host-supervision
test "$(git rev-parse FETCH_HEAD)" = "$REVIEWED_HEAD" || exit 1
git worktree add --detach "$HOME/boss-trader-038-hotfix-review" "$REVIEWED_HEAD" || exit 1
cd "$HOME/boss-trader-038-hotfix-review"
test "$(git rev-parse HEAD)" = "$REVIEWED_HEAD" || exit 1
/usr/bin/python3 -B -m unittest discover -s tests -p 'test_*038.py' -v &&
/usr/bin/python3 -B -m unittest discover -s tests -v
sha256sum research/windows_038/*.ps1
```

## Consolidated Windows validation

Use the existing approved non-elevated PowerShell 5.1 session and existing verified
SSH credentials/agent. This does not change execution policy. If blocked, STOP/HOLD.
The actual reviewed VM UUID below is owner-supplied evidence, not discovered here.
Use a new task folder; if it already exists stop and inspect it rather than overwrite.

```powershell
$Scp="$env:SystemRoot\System32\OpenSSH\scp.exe"
$VBox='C:\Program Files\Oracle\VirtualBox\VBoxManage.exe'
$KnownHosts=Join-Path $HOME '.ssh\known_hosts'
$GuestRepo='/home/tazmanked/boss-trader-038-hotfix-review'
$Task=Join-Path $HOME 'boss-038-hotfix1-review'
New-Item -ItemType Directory -Path $Task -ErrorAction Stop | Out-Null
$Expected=@{
  'HostProbe038.ps1'='15f6008afe14ed4de61362202f308ec81305c216f5231ae7ae07a6b0ab1c7fe8'
  'HostSupervisor038.ps1'='44225ea26c3cf9a23e84454b7551e1c3dd5644ea326835166393438001a887be'
  'Test-HostSupervisor038.ps1'='264fa1cf4e1f12f8a496cbbca8d778a2997c26c5cddfd0814d13035a703a1357'
}
foreach ($File in $Expected.Keys) {
  & $Scp -F none -P 2222 -o StrictHostKeyChecking=yes -o UpdateHostKeys=no -o BatchMode=yes -o ('UserKnownHostsFile="'+$KnownHosts+'"') "tazmanked@127.0.0.1:$GuestRepo/research/windows_038/$File" $Task
  if ($LASTEXITCODE -ne 0) { throw 'SOURCE_COPY_HOLD' }
  if ((Get-FileHash -LiteralPath (Join-Path $Task $File) -Algorithm SHA256).Hash.ToLowerInvariant() -cne $Expected[$File]) { throw 'SCRIPT_HASH_HOLD' }
}
& "$Task\Test-HostSupervisor038.ps1" -IncludeHarmlessProcesses
if (-not $?) { throw 'HARNESS_HOLD' }
$VmUuid='dd0913eb-2b74-44a9-912d-2ee562bbd104'
# Three independent cold probes, each inside the existing 4-second worker deadline.
1..3 | ForEach-Object {
  & "$Task\HostSupervisor038.ps1" -ProbeOnly -VmUuid $VmUuid -VBoxManagePath $VBox
  if (-not $? -or $LASTEXITCODE -ne 0) { throw 'HOST_PROBE_HOLD' }
  Start-Sleep -Seconds 5
}
```

Retain private output: exact head/script hashes, PS version, harness count,
cold/warm native times, each probe JSON/duration or sanitized failure code.
No raw SSH logs or private paths need publication. No ssh heartbeat/session or
build is started by this sequence. Baseline verified SSH/boot measurements remain
historical evidence; this sequence does not requalify an authenticated heartbeat.

## Compatibility and next decision

Existing configuration and inventory schemas are unchanged. Preserve genuine
inventory/evidence and existing config files; do not rerun attach-config over an
existing host_supervision config. Script hashes changed: an old prepared plan,
qualification or approval **cannot authorize this revision**. After review and
successful harmless probes, any later session needs a fresh reviewed plan bound
to these scripts and the correct checkout/observer, a fresh qualification and
separate exact owner approval; use a new job/config output instead of overwriting
an existing attempt. The current worktree path alone is not runtime authorization.

Smallest owner action: review this patch, run only the harmless sequence above and
return private timing/stage evidence. If it refuses, retain HOLD and investigate
that stage without WMI repair or budget changes. Native API/PS5.1 target execution,
end-to-end supervisor/SSH/recorder/containment qualification, unresolved physical
freezes and trusted UTC evidence remain gaps. Existing B4/other technical gates,
AEP Gate B and genuine inference HOLD, REAL_NOT_RUN, and NO ORDERS are unchanged.
No actual llama.cpp compilation, inference, host configuration change, installation,
recorder modification, merge or spending occurred. STOP FOR OWNER AND BOSS AI REVIEW.
