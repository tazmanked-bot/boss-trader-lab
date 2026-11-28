param([string]$ProbeVmUuid,[string]$ProbeVBoxManagePath='C:\Program Files\Oracle\VirtualBox\VBoxManage.exe',[switch]$ProbeLibraryOnly)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
# Run-only Reflection.Emit: no external compiler, source file or saved assembly.
$script:TickMethod038=$null
function Diagnostic038([string]$Stage,[string]$Reason,$Failure) {
    $message='';$hr='0x00000000'
    if ($null -ne $Failure) {
        $message=$Failure.Message
        $inner=$Failure
        for ($depth=0;$depth -lt 4 -and $null -ne $inner.InnerException;$depth++) { $inner=$inner.InnerException }
        $hr='0x'+([BitConverter]::ToUInt32([BitConverter]::GetBytes([int]$inner.HResult),0)).ToString('X8')
    }
    if ($message -cmatch '^CODEX038\|[A-Z_]{1,32}\|[A-Z_]{1,48}\|0x[0-9A-F]{8}\z') { return $message }
    if ($message -cin @('PROCESS_TIMEOUT','PROCESS_OUTPUT_LIMIT','SSH_STDERR_REQUIRES_REVIEW','PIPELINED_SSH_RESPONSE',
        'SSH_DISCONNECTED','SSH_RESPONSE_TIMEOUT','HOST_CLOCK_GAP_OR_RESUME','HOST_INPUT_CHANGED',
        'VM_IDENTITY_METADATA','VM_NOT_RUNNING_OR_FOREIGN','REVIEWED_VM_SSH_FORWARD_NOT_FOUND',
        'REVIEWED_SCRIPT_BYTES_MISMATCH','FOREIGN_PLAN_OR_VM','PROTOCOL_ENVELOPE','SSH_ACK_SESSION_OR_REPLAY')) { $Reason=$message }
    if ($Stage -cnotmatch '^[A-Z_]{1,32}$' -or $Reason -cnotmatch '^[A-Z_]{1,48}$') { return 'CODEX038|DIAGNOSTIC|INVALID_CODE|0x00000000' }
    return 'CODEX038|'+$Stage+'|'+$Reason+'|'+$hr
}
function Convert-Tick038($Milliseconds) {
    # Reject signed, floating, string, null and zero inputs; never truncate a DWORD.
    if ($Milliseconds -isnot [UInt64] -or $Milliseconds -lt 1000) { throw (Diagnostic038 NATIVE_UNITS INVALID_TICKS $null) }
    $seconds=[decimal]::Floor(([decimal]$Milliseconds)/1000)
    if ($seconds -gt 9007199254740991) { throw (Diagnostic038 NATIVE_UNITS OUT_OF_RANGE $null) }
    return [long]$seconds
}
function Get-NativeUptime038 {
    if ($null -eq $script:TickMethod038) {
        try {
            $name=New-Object Reflection.AssemblyName ('BossTraderTick038_'+[guid]::NewGuid().ToString('N'))
            $assembly=[AppDomain]::CurrentDomain.DefineDynamicAssembly($name,[Reflection.Emit.AssemblyBuilderAccess]::Run)
            $module=$assembly.DefineDynamicModule('Native038')
            $type=$module.DefineType('BossTrader.Native038.Tick',[Reflection.TypeAttributes]'Public, Sealed, Abstract')
            $method=$type.DefinePInvokeMethod('ReadTickCount64','kernel32.dll','GetTickCount64',
                [Reflection.MethodAttributes]'Public, Static, PinvokeImpl',[Reflection.CallingConventions]::Standard,
                [UInt64],[Type[]]@(),[Runtime.InteropServices.CallingConvention]::Winapi,[Runtime.InteropServices.CharSet]::None)
            $method.SetImplementationFlags($method.GetMethodImplementationFlags() -bor [Reflection.MethodImplAttributes]::PreserveSig)
            $script:TickMethod038=$type.CreateType().GetMethod('ReadTickCount64')
        } catch { throw (Diagnostic038 NATIVE_BIND BIND_FAILED $_.Exception) }
    }
    try { $ticks=$script:TickMethod038.Invoke($null,$null) }
    catch { throw (Diagnostic038 NATIVE_CALL CALL_FAILED $_.Exception) }
    return (Convert-Tick038 $ticks)
}
function Quote-Arg038([string]$Value) {
    if ($Value -match '[\r\n\x00]') { throw 'UNSUPPORTED_ARGUMENT' }
    $text=New-Object Text.StringBuilder;[void]$text.Append('"');$slashes=0
    foreach ($char in $Value.ToCharArray()) {
        if ($char -eq '\') { $slashes++;continue }
        if ($char -eq '"') { [void]$text.Append(('\' * (2*$slashes+1)));[void]$text.Append('"') }
        else { [void]$text.Append(('\' * $slashes));[void]$text.Append($char) }
        $slashes=0
    }
    [void]$text.Append(('\' * (2*$slashes)));[void]$text.Append('"');return $text.ToString()
}
function New-Pump038($Reader,[int]$Cap) {
    return @{Reader=$Reader;Cap=$Cap;Text='';Task=$null;Buffer=(New-Object char[] 512);Done=$false}
}
function Pump038($Pump) {
    if ($Pump.Done) { return }
    if ($null -eq $Pump.Task) { $Pump.Task=$Pump.Reader.ReadAsync($Pump.Buffer,0,$Pump.Buffer.Length) }
    if ($Pump.Task.IsCompleted) {
        $count=$Pump.Task.GetAwaiter().GetResult();$Pump.Task=$null
        if ($count -eq 0) { $Pump.Done=$true;return }
        $Pump.Text += [string]::new($Pump.Buffer,0,$count)
        if ($Pump.Text.Length -gt $Pump.Cap) { throw 'PROCESS_OUTPUT_LIMIT' }
    }
}
function Start-Owned038([string]$File,[string[]]$Arguments,[int]$Cap=8192) {
    if (-not (Test-Path -LiteralPath $File -PathType Leaf)) { throw 'EXISTING_TOOL_REQUIRED' }
    $info=New-Object Diagnostics.ProcessStartInfo
    $info.FileName=$File;$info.Arguments=(($Arguments | ForEach-Object { Quote-Arg038 $_ }) -join ' ')
    $info.UseShellExecute=$false;$info.CreateNoWindow=$true
    $info.RedirectStandardInput=$true;$info.RedirectStandardOutput=$true;$info.RedirectStandardError=$true
    $process=New-Object Diagnostics.Process;$process.StartInfo=$info
    if (-not $process.Start()) { throw 'PROCESS_START_FAILED' }
    return @{Process=$process;Start=$process.StartTime.ToUniversalTime();Out=(New-Pump038 $process.StandardOutput $Cap);Err=(New-Pump038 $process.StandardError 4096)}
}
function Stop-Owned038($Owned) {
    $process=$Owned.Process;$known=@();$clean=$true
    try {
        if ($process.HasExited) {
            $drain=[Diagnostics.Stopwatch]::StartNew()
            while ((-not $Owned.Out.Done -or -not $Owned.Err.Done) -and $drain.ElapsedMilliseconds -lt 200) {
                Pump038 $Owned.Out;Pump038 $Owned.Err;Start-Sleep -Milliseconds 10
            }
            if (-not $Owned.Out.Done -or -not $Owned.Err.Done) { throw 'ORPHANED_PIPE_CLEANUP_UNVERIFIED' }
        }
        if (-not $process.HasExited) {
            if ($process.StartTime.ToUniversalTime() -ne $Owned.Start) { throw 'PID_REUSED' }
            # Bound enumeration, then taskkill the owned tree; never kill by image/name.
            $queue=New-Object Collections.Generic.Queue[int];$queue.Enqueue($process.Id)
            $watch=[Diagnostics.Stopwatch]::StartNew()
            while ($queue.Count -gt 0) {
                if ($known.Count -gt 32 -or $watch.Elapsed.TotalSeconds -gt 3) { throw 'TREE_ENUMERATION_BUDGET' }
                $parent=$queue.Dequeue()
                $children=@(Get-CimInstance Win32_Process -Filter ('ParentProcessId = '+$parent) -OperationTimeoutSec 1)
                foreach ($child in $children) {
                    $known+=@{Pid=[int]$child.ProcessId;Created=$child.CreationDate.ToUniversalTime()};$queue.Enqueue([int]$child.ProcessId)
                }
            }
            $info=New-Object Diagnostics.ProcessStartInfo
            $info.FileName=Join-Path $env:SystemRoot 'System32\taskkill.exe'
            $info.Arguments='/PID '+$process.Id+' /T /F';$info.UseShellExecute=$false;$info.CreateNoWindow=$true
            $info.RedirectStandardOutput=$true;$info.RedirectStandardError=$true
            $killer=[Diagnostics.Process]::Start($info)
            try { if (-not $killer.WaitForExit(2000)) { $killer.Kill();throw 'TASKKILL_TIMEOUT' } }
            finally { $killer.Dispose() }
        }
        if (-not $process.WaitForExit(1000)) { throw 'OWNED_PROCESS_UNREAPED' }
        foreach ($item in $known) {
            try {
                $left=[Diagnostics.Process]::GetProcessById($item.Pid)
                if (-not $left.HasExited -and [Math]::Abs(($left.StartTime.ToUniversalTime()-$item.Created).TotalSeconds) -lt 1) { $clean=$false }
                $left.Dispose()
            } catch [ArgumentException] { }
        }
    } catch { $clean=$false;try { if (-not $process.HasExited) { $process.Kill();[void]$process.WaitForExit(1000) } } catch { } }
    finally { $process.Dispose() }
    if (-not $clean) { throw 'OWNED_TREE_CLEANUP_UNVERIFIED' }
}
function Invoke-Bounded038([string]$File,[string[]]$Arguments,[int]$TimeoutMs=2000,[int]$Cap=262144,[string]$Stage='WORKER_PROCESS') {
    try { $owned=Start-Owned038 $File $Arguments $Cap } catch { throw (Diagnostic038 $Stage START_FAILED $_.Exception) };$watch=[Diagnostics.Stopwatch]::StartNew()
    try {
        while (-not $owned.Process.HasExited -or -not $owned.Out.Done -or -not $owned.Err.Done) {
            if ($watch.ElapsedMilliseconds -gt $TimeoutMs) { throw (Diagnostic038 $Stage PROCESS_TIMEOUT $null) }
            Pump038 $owned.Out;Pump038 $owned.Err;Start-Sleep -Milliseconds 10
        }
        if ($owned.Process.ExitCode -ne 0 -or $owned.Err.Text.Length -ne 0) {
            $diagnostic=$owned.Err.Text.TrimEnd("`r","`n")
            if ($diagnostic -cmatch '^CODEX038\|[A-Z_]{1,32}\|[A-Z_]{1,48}\|0x[0-9A-F]{8}\z') { throw $diagnostic }
            throw (Diagnostic038 $Stage NONZERO_OR_STDERR $null)
        }
        return $owned.Out.Text
    } catch { throw (Diagnostic038 $Stage PROCESS_FAILED $_.Exception) }
    finally { try { Stop-Owned038 $owned } catch { throw (Diagnostic038 CLEANUP TREE_UNVERIFIED $_.Exception) } }
}
function Read-Line038($Owned,[int]$TimeoutMs=15000) {
    $watch=[Diagnostics.Stopwatch]::StartNew()
    while ($true) {
        Pump038 $Owned.Out;Pump038 $Owned.Err
        if ($Owned.Err.Text.Length -gt 0) { throw 'SSH_STDERR_REQUIRES_REVIEW' }
        $index=$Owned.Out.Text.IndexOf("`n")
        if ($index -ge 0) {
            $line=$Owned.Out.Text.Substring(0,$index).TrimEnd("`r")
            $rest=$Owned.Out.Text.Substring($index+1)
            if ($rest.Length -ne 0) { throw 'PIPELINED_SSH_RESPONSE' }
            $Owned.Out.Text='';return $line
        }
        if ($Owned.Process.HasExited -or $Owned.Out.Done) { throw 'SSH_DISCONNECTED' }
        if ($watch.ElapsedMilliseconds -gt $TimeoutMs) { throw 'SSH_RESPONSE_TIMEOUT' }
        Start-Sleep -Milliseconds 10
    }
}
function Get-HostProbe038([string]$Uuid,[string]$VBox) {
    if ($env:OS -cne 'Windows_NT') { throw 'REAL_WINDOWS_REQUIRED' }
    $id=([guid]$Uuid).ToString().ToLowerInvariant();$watch=[Diagnostics.Stopwatch]::StartNew()
    try {
        $os=Get-CimInstance Win32_OperatingSystem -OperationTimeoutSec 2
        $boot=$os.LastBootUpTime.ToUniversalTime().ToString('o')
    } catch { throw (Diagnostic038 BOOT_CIM QUERY_FAILED $_.Exception) }
    $uptime=Get-NativeUptime038
    try { $raw=Invoke-Bounded038 $VBox @('showvminfo',$id,'--machinereadable') 2000 262144 'VBOX_PROCESS' }
    catch { throw (Diagnostic038 VBOX_PROCESS QUERY_FAILED $_.Exception) }
    try {
    $uuidMatches=@([regex]::Matches($raw,'(?m)^UUID="([^"]+)"\r?$'))
    $stateMatches=@([regex]::Matches($raw,'(?m)^VMState="([^"]+)"\r?$'))
    if ($uuidMatches.Count -ne 1 -or $stateMatches.Count -ne 1) { throw 'VM_IDENTITY_METADATA' }
    if (([guid]$uuidMatches[0].Groups[1].Value).ToString().ToLowerInvariant() -ne $id -or $stateMatches[0].Groups[1].Value -cne 'running') { throw 'VM_NOT_RUNNING_OR_FOREIGN' }
    $forward=@()
    foreach ($match in [regex]::Matches($raw,'(?m)^Forwarding\([0-9]+\)="([^"]+)"\r?$')) {
        $parts=$match.Groups[1].Value.Split(',')
        if ($parts.Count -eq 6 -and $parts[1] -ceq 'tcp' -and $parts[3] -ceq '2222' -and $parts[5] -ceq '22' -and $parts[2] -in @('','127.0.0.1')) { $forward+=,$parts }
    }
    if ($forward.Count -ne 1) { throw 'REVIEWED_VM_SSH_FORWARD_NOT_FOUND' }
    } catch { throw (Diagnostic038 VBOX_PARSE IDENTITY_OR_FORWARD_FAILED $_.Exception) }
    return @{platform='Windows';host_boot=$boot;host_uptime_seconds=$uptime;
        probe_duration_ms=[long]$watch.ElapsedMilliseconds;vm_uuid=$id;vm_state='running';forward_host_port=2222;forward_guest_port=22;forward_host_ip=$forward[0][2]}
}
if ($ProbeLibraryOnly) { return }
try {
    $result=Get-HostProbe038 $ProbeVmUuid $ProbeVBoxManagePath
    [Console]::Out.WriteLine(($result | ConvertTo-Json -Compress -Depth 8));exit 0
} catch { [Console]::Error.WriteLine((Diagnostic038 HOST_PROBE VALIDATION_FAILED $_.Exception));exit 2 }
