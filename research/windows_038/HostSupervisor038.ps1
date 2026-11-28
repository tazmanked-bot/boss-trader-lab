param([string]$GuestRepo,[string]$GuestPlan,[string]$PlanSha256,[string]$VmUuid,
      [string]$KnownHosts=(Join-Path $HOME '.ssh\known_hosts'),[string]$GuestUser='tazmanked',
      [string]$VBoxManagePath='C:\Program Files\Oracle\VirtualBox\VBoxManage.exe',
      [string]$IdentityFile,[int]$Seconds=7500,[switch]$NewSession,[switch]$ProbeOnly,[switch]$LibraryOnly)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$SupervisorScript038=$PSCommandPath;$SupervisorRoot038=$PSScriptRoot
. (Join-Path $SupervisorRoot038 'HostProbe038.ps1') -ProbeLibraryOnly
function Assert-SafeGuestPath038([string]$Value) {
    if ($Value -notmatch '^/[A-Za-z0-9._/-]+$' -or $Value.Split('/') -contains '..') { throw 'UNSUPPORTED_GUEST_PATH' }
}
function Assert-Envelope038($Value,[string]$ExpectedPlan,[string]$ExpectedVm) {
    if ($Value.version -cne 'windows-operational-supervision-038-v1' -or $Value.plan_sha256 -cne $ExpectedPlan -or $Value.vm_uuid.ToLowerInvariant() -cne $ExpectedVm.ToLowerInvariant()) { throw 'FOREIGN_PLAN_OR_VM' }
    if ($Value.session -notmatch '^[0-9a-f]{64}$' -or $Value.challenge -notmatch '^[0-9a-f]{64}$' -or $Value.seq -lt 1 -or $Value.interval_seconds -ne 5 -or $Value.expiry_seconds -ne 15) { throw 'PROTOCOL_ENVELOPE' }
}
function New-SshArguments038([string]$Remote,[string]$Hosts,[string]$User,[string]$Key) {
    $arguments=@('-F','none','-T','-p','2222','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes',
        '-o',('UserKnownHostsFile="'+$Hosts+'"'),'-o','UpdateHostKeys=no','-o','ConnectionAttempts=1','-o','ConnectTimeout=5',
        '-o','ServerAliveInterval=5','-o','ServerAliveCountMax=1','-o','NumberOfPasswordPrompts=0',
        '-o','ClearAllForwardings=yes','-o','ForwardAgent=no','-o','PermitLocalCommand=no','-o','AddKeysToAgent=no',
        '-o','ProxyCommand=none','-o','ProxyJump=none')
    if ($Key) { $arguments+=@('-i',$Key,'-o','IdentitiesOnly=yes') }
    return $arguments+@(($User+'@127.0.0.1'),$Remote)
}
if ($LibraryOnly) { return }
$sshOwned=$null
try {
    if ($env:OS -cne 'Windows_NT' -or $Seconds -lt 1 -or $Seconds -gt 7500) { throw 'WINDOWS_OR_DURATION_REQUIRED' }
    $vm=([guid]$VmUuid).ToString().ToLowerInvariant()
    $ps=Join-Path $env:SystemRoot 'System32\WindowsPowerShell\v1.0\powershell.exe'
    $ssh=Join-Path $env:SystemRoot 'System32\OpenSSH\ssh.exe'
    $probe=Join-Path $SupervisorRoot038 'HostProbe038.ps1'
    $self=$SupervisorScript038
    $hashes=@{ssh=(Get-FileHash -LiteralPath $ssh -Algorithm SHA256).Hash.ToLowerInvariant();
        powershell=(Get-FileHash -LiteralPath $ps -Algorithm SHA256).Hash.ToLowerInvariant();
        virtualbox=(Get-FileHash -LiteralPath $VBoxManagePath -Algorithm SHA256).Hash.ToLowerInvariant()}
    $selfSha=(Get-FileHash -LiteralPath $self -Algorithm SHA256).Hash.ToLowerInvariant()
    $probeSha=(Get-FileHash -LiteralPath $probe -Algorithm SHA256).Hash.ToLowerInvariant()
    $probeArgs=@('-NoProfile','-NonInteractive','-File',$probe,'-ProbeVmUuid',$vm,'-ProbeVBoxManagePath',$VBoxManagePath)
    if ($ProbeOnly) {
        $actual=Invoke-Bounded038 $ps $probeArgs 4000 8192
        [Console]::Out.WriteLine($actual);exit 0
    }
    Assert-SafeGuestPath038 $GuestRepo;Assert-SafeGuestPath038 $GuestPlan
    if ($PlanSha256 -notmatch '^[0-9a-f]{64}$' -or $GuestUser -notmatch '^[a-z_][a-z0-9_-]*$') { throw 'PLAN_OR_USER_FORMAT' }
    if (-not (Test-Path -LiteralPath $KnownHosts -PathType Leaf)) { throw 'PREEXISTING_VERIFIED_KNOWN_HOSTS_REQUIRED' }
    $knownSha=(Get-FileHash -LiteralPath $KnownHosts -Algorithm SHA256).Hash
    $remote='cd -- '+$GuestRepo+' && exec /usr/bin/python3 -u -B -m research.host_supervision_038 serve --plan '+$GuestPlan+' --expected-plan-sha '+$PlanSha256+' --max-seconds '+$Seconds
    if ($NewSession) { $remote+=' --new-session' }
    $sshOwned=Start-Owned038 $ssh (New-SshArguments038 $remote $KnownHosts $GuestUser $IdentityFile) 8192
    $hello=(Read-Line038 $sshOwned 15000 | ConvertFrom-Json)
    Assert-Envelope038 $hello $PlanSha256 $vm
    if ($hello.expected_scripts.'HostSupervisor038.ps1' -cne $selfSha -or $hello.expected_scripts.'HostProbe038.ps1' -cne $probeSha) { throw 'REVIEWED_SCRIPT_BYTES_MISMATCH' }
    $session=$hello.session;$boot=$hello.guest_boot;$observer=$hello.observer_sha256
    $watch=[Diagnostics.Stopwatch]::StartNew();$hostSession=[guid]::NewGuid().ToString();$previous=$null
    while ($watch.Elapsed.TotalSeconds -lt $Seconds) {
        $cycle=$watch.ElapsedMilliseconds
        $measurement=(Invoke-Bounded038 $ps $probeArgs 4000 8192 | ConvertFrom-Json)
        $measurement | Add-Member -NotePropertyName host_session -NotePropertyValue $hostSession
        $measurement | Add-Member -NotePropertyName host_pid -NotePropertyValue $PID
        $measurement | Add-Member -NotePropertyName host_elapsed_ms -NotePropertyValue ([long]$watch.ElapsedMilliseconds)
        $measurement | Add-Member -NotePropertyName host_utc_ms -NotePropertyValue ([DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds())
        $measurement | Add-Member -NotePropertyName supervisor_sha256 -NotePropertyValue $selfSha
        $measurement | Add-Member -NotePropertyName probe_sha256 -NotePropertyValue $probeSha
        $measurement | Add-Member -NotePropertyName tool_sha256 -NotePropertyValue $hashes
        if ($null -ne $previous) {
            $gap=$measurement.host_elapsed_ms-$previous.host_elapsed_ms
            $wall=$measurement.host_utc_ms-$previous.host_utc_ms
            if ($gap -lt 1000 -or $gap -gt 15000 -or [Math]::Abs($wall-$gap) -gt 2000 -or $measurement.host_boot -cne $previous.host_boot) { throw 'HOST_CLOCK_GAP_OR_RESUME' }
        }
        if ((Get-FileHash -LiteralPath $self -Algorithm SHA256).Hash.ToLowerInvariant() -cne $selfSha -or
            (Get-FileHash -LiteralPath $probe -Algorithm SHA256).Hash.ToLowerInvariant() -cne $probeSha -or
            (Get-FileHash -LiteralPath $KnownHosts -Algorithm SHA256).Hash -cne $knownSha -or
            (Get-FileHash -LiteralPath $ssh -Algorithm SHA256).Hash.ToLowerInvariant() -cne $hashes.ssh -or
            (Get-FileHash -LiteralPath $ps -Algorithm SHA256).Hash.ToLowerInvariant() -cne $hashes.powershell -or
            (Get-FileHash -LiteralPath $VBoxManagePath -Algorithm SHA256).Hash.ToLowerInvariant() -cne $hashes.virtualbox) { throw 'HOST_INPUT_CHANGED' }
        $message=@{version=$hello.version;session=$session;challenge=$hello.challenge;seq=$hello.seq;
            plan_sha256=$PlanSha256;guest_boot=$boot;observer_sha256=$observer;measurement=$measurement}
        $sshOwned.Process.StandardInput.WriteLine(($message | ConvertTo-Json -Compress -Depth 8));$sshOwned.Process.StandardInput.Flush()
        $next=(Read-Line038 $sshOwned 15000 | ConvertFrom-Json)
        Assert-Envelope038 $next $PlanSha256 $vm
        if ($next.session -cne $session -or $next.guest_boot -cne $boot -or $next.observer_sha256 -cne $observer -or
            $next.seq -ne ($hello.seq+1) -or $next.challenge -ceq $hello.challenge) { throw 'SSH_ACK_SESSION_OR_REPLAY' }
        $hello=$next;$previous=$measurement
        [Console]::Out.WriteLine('OPERATIONAL_HEARTBEAT_ACK '+($hello.seq-1)+'; HARDWARE_UNCERTAINTY_UNRESOLVED')
        $sleep=5000-($watch.ElapsedMilliseconds-$cycle)
        if ($sleep -gt 0) { Start-Sleep -Milliseconds ([int]$sleep) }
    }
} catch { [Console]::Error.WriteLine('HOST_SUPERVISION_HOLD: '+$_.Exception.Message);exit 2 }
finally {
    if ($null -ne $sshOwned) {
        try { $sshOwned.Process.StandardInput.Close();Stop-Owned038 $sshOwned }
        catch { [Console]::Error.WriteLine('SSH_CLEANUP_UNVERIFIED; GUEST MUST REFUSE BY EOF/PID/EXPIRY');exit 3 }
    }
}
