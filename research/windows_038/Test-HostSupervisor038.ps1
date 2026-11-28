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
# Real harmless API calls here are Windows evidence only when this harness runs there.
$cold=[Diagnostics.Stopwatch]::StartNew();$native=Get-NativeUptime038;$cold.Stop()
$cached=$script:TickMethod038
$warm=[Diagnostics.Stopwatch]::StartNew();$again=Get-NativeUptime038;$warm.Stop()
if ($native -le 0 -or $again -lt $native -or $cached -ne $script:TickMethod038) { throw 'NATIVE_UPTIME_OR_CACHE_FAILED' };$checks++
[Console]::Out.WriteLine('NATIVE_BIND_COLD_MS '+$cold.ElapsedMilliseconds+'; WARM_MS '+$warm.ElapsedMilliseconds+'; NOT_FULL_PROBE_QUALIFICATION')
foreach ($case in @(@([UInt64]1000,1),@([UInt64]1999,1),@([UInt64]4294967295,4294967),@([UInt64]4294967296,4294967),@([UInt64]4294968000,4294968))) {
    if ((Convert-Tick038 $case[0]) -ne $case[1]) { throw 'NATIVE_UNITS_OR_DWORD_ROLLOVER' };$checks++
}
foreach ($invalid in @($null,0,-1,1000,1000.0,'1000',[UInt64]0,[UInt64]999,[UInt64]::MaxValue)) {
    $failed=$false;try { [void](Convert-Tick038 $invalid) } catch { $failed=$true }
    if (-not $failed) { throw 'INVALID_NATIVE_TICKS_ACCEPTED' };$checks++
}
# Inject native invocation failure; restore the genuine cached binding afterwards.
try {
    $script:TickMethod038=New-Object PSObject
    $script:TickMethod038 | Add-Member -MemberType ScriptMethod -Name Invoke -Value { param($a,$b) throw 'PRIVATE_NATIVE_ERROR' }
    $failed=$false;try { [void](Get-NativeUptime038) } catch { $failed=$_.Exception.Message -cmatch '^CODEX038\|NATIVE_CALL\|CALL_FAILED\|0x[0-9A-F]{8}$' }
    if (-not $failed) { throw 'NATIVE_FAILURE_NOT_SANITIZED' };$checks++
} finally { $script:TickMethod038=$cached }
$com=New-Object Runtime.InteropServices.COMException ('PRIVATE_INVALID_CLASS',-2147217392)
if ((Diagnostic038 BOOT_CIM QUERY_FAILED $com) -cne 'CODEX038|BOOT_CIM|QUERY_FAILED|0x80041010') { throw 'HRESULT_NOT_PRESERVED' };$checks++
$private=New-Object Exception 'PRIVATE_PATH_KEY_STDERR'
$code=Diagnostic038 BOOT_CIM QUERY_FAILED $private
if ($code -cnotmatch '^CODEX038\|BOOT_CIM\|QUERY_FAILED\|0x[0-9A-F]{8}$' -or $code.Contains('PRIVATE')) { throw 'DIAGNOSTIC_LEAK' };$checks++
if ((Diagnostic038 SUPERVISOR FAILED (New-Object Exception $code)) -cne $code) { throw 'DIAGNOSTIC_STAGE_LOST' };$checks++
# Synthetic missing-class regression, without requiring or querying performance CIM.
$boundedSaved=(Get-Item Function:Invoke-Bounded038).ScriptBlock
$uptimeSaved=(Get-Item Function:Get-NativeUptime038).ScriptBlock
try {
    function Get-CimInstance { param($ClassName,$OperationTimeoutSec)
        if ($ClassName -cne 'Win32_OperatingSystem') { throw 'INVALID_CLASS_0x80041010' }
        return [pscustomobject]@{LastBootUpTime=[DateTime]::UtcNow.AddHours(-1)}
    }
    function Get-NativeUptime038 { return [long]3600 }
    function Invoke-Bounded038 { param($File,$Arguments,$TimeoutMs,$Cap,$Stage)
        return 'UUID="12345678-1234-1234-1234-123456789abc"'+"`n"+'VMState="running"'+"`n"+'Forwarding(0)="ssh,tcp,127.0.0.1,2222,,22"'
    }
    $fake=Get-HostProbe038 '12345678-1234-1234-1234-123456789abc' 'SYNTHETIC_NO_PROCESS'
    if ($fake.host_uptime_seconds -ne 3600 -or $fake.vm_state -cne 'running') { throw 'MISSING_PERFORMANCE_CLASS_REGRESSION' };$checks++
    function Get-CimInstance { param($ClassName,$OperationTimeoutSec) throw 'PRIVATE_BOOT_CIM_FAILURE' }
    $failed=$false;try { [void](Get-HostProbe038 '12345678-1234-1234-1234-123456789abc' 'SYNTHETIC_NO_PROCESS') }
    catch { $failed=$_.Exception.Message -cmatch '^CODEX038\|BOOT_CIM\|QUERY_FAILED\|0x[0-9A-F]{8}$' }
    if (-not $failed) { throw 'BOOT_CIM_FAILURE_NOT_SANITIZED' };$checks++
} finally {
    Remove-Item Function:Get-CimInstance
    Set-Item Function:Invoke-Bounded038 $boundedSaved
    Set-Item Function:Get-NativeUptime038 $uptimeSaved
}
if ($IncludeHarmlessProcesses) {
    $ps=Join-Path $env:SystemRoot 'System32\WindowsPowerShell\v1.0\powershell.exe'
    $text=Invoke-Bounded038 $ps @('-NoProfile','-NonInteractive','-Command','[Console]::WriteLine("INERT_038")') 4000 4096
    if ($text.Trim() -cne 'INERT_038') { throw 'ARGUMENT_QUOTING_OR_PROCESS_FAILED' };$checks++
    $refused=$false
    try { [void](Invoke-Bounded038 $ps @('-NoProfile','-NonInteractive','-Command','Start-Sleep -Seconds 30') 200 4096) }
    catch { if ($_.Exception.Message -cnotmatch '^CODEX038\|WORKER_PROCESS\|PROCESS_TIMEOUT\|0x00000000$') { throw };$refused=$true }
    if (-not $refused) { throw 'WATCHDOG_DID_NOT_FIRE' };$checks++
    foreach ($case in @(@('CODEX038|NATIVE_BIND|BIND_FAILED|0x80041010','NATIVE_BIND'),@('PRIVATE_RAW_STDERR','WORKER_PROCESS'))) {
        $failed=$false
        try { [void](Invoke-Bounded038 $ps @('-NoProfile','-NonInteractive','-Command',('[Console]::Error.WriteLine("'+$case[0]+'");exit 2')) 4000 4096) }
        catch { $failed=$_.Exception.Message.StartsWith('CODEX038|'+$case[1]+'|') -and -not $_.Exception.Message.Contains('PRIVATE') }
        if (-not $failed) { throw 'CHILD_DIAGNOSTIC_NOT_SANITIZED' };$checks++
    }
}
[Console]::Out.WriteLine('WINDOWS_HARMLESS_HARNESS_PASS '+$checks+'; NO_SSH_VM_OR_BUILD_QUALIFICATION')
