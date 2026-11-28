param([switch]$IncludeHarmlessProcesses)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
if ($env:OS -cne 'Windows_NT') { throw 'REAL_WINDOWS_REQUIRED_NO_LINUX_QUALIFICATION' }
$checks=0
foreach ($name in @('HostSupervisor038.ps1','HostProbe038.ps1','Test-HostSupervisor038.ps1')) {
    $tokens=$null;$errors=$null
    [void][System.Management.Automation.Language.Parser]::ParseFile((Join-Path $PSScriptRoot $name),[ref]$tokens,[ref]$errors)
    if ($errors.Count -ne 0) { throw 'POWERSHELL_PARSE_FAILED' };$checks++
}
. (Join-Path $PSScriptRoot 'HostSupervisor038.ps1') -LibraryOnly
foreach ($path in @('/home/tazmanked/boss-trader-lab','/home/tazmanked/plan.json')) { Assert-SafeGuestPath038 $path;$checks++ }
foreach ($path in @('/home/a b','/home/a;touch_bad','/home/../bad')) {
    $refused=$false;try { Assert-SafeGuestPath038 $path } catch { $refused=$true }
    if (-not $refused) { throw 'UNSAFE_PATH_ACCEPTED' };$checks++
}
$args038=New-SshArguments038 'true' 'C:\Users\Owner Name\.ssh\known_hosts' 'tazmanked' ''
foreach ($required in @('StrictHostKeyChecking=yes','UpdateHostKeys=no','BatchMode=yes','ConnectionAttempts=1','ClearAllForwardings=yes')) {
    if ($args038 -notcontains $required) { throw 'SSH_OPTION_MISSING' };$checks++
}
if ($args038 -contains 'StrictHostKeyChecking=no') { throw 'HOST_KEY_BYPASS' }
$hello=@{version='windows-operational-supervision-038-v1';plan_sha256=('a'*64);vm_uuid='12345678-1234-1234-1234-123456789abc';
    session=('b'*64);challenge=('c'*64);seq=1;interval_seconds=5;expiry_seconds=15}
Assert-Envelope038 $hello ('a'*64) $hello.vm_uuid;$checks++
$failed=$false;try { Assert-Envelope038 $hello ('d'*64) $hello.vm_uuid } catch { $failed=$true }
if (-not $failed) { throw 'FOREIGN_PLAN_ACCEPTED' };$checks++
if ($IncludeHarmlessProcesses) {
    $ps=Join-Path $env:SystemRoot 'System32\WindowsPowerShell\v1.0\powershell.exe'
    $text=Invoke-Bounded038 $ps @('-NoProfile','-NonInteractive','-Command','[Console]::WriteLine("INERT_038")') 4000 4096
    if ($text.Trim() -cne 'INERT_038') { throw 'ARGUMENT_QUOTING_OR_PROCESS_FAILED' };$checks++
    $refused=$false
    try { [void](Invoke-Bounded038 $ps @('-NoProfile','-NonInteractive','-Command','Start-Sleep -Seconds 30') 200 4096) }
    catch { if ($_.Exception.Message -cne 'PROCESS_TIMEOUT') { throw };$refused=$true }
    if (-not $refused) { throw 'WATCHDOG_DID_NOT_FIRE' };$checks++
}
[Console]::Out.WriteLine('WINDOWS_HARMLESS_HARNESS_PASS '+$checks+'; NO_SSH_VM_OR_BUILD_QUALIFICATION')
