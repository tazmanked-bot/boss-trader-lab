"""Offline protocol regressions and source contracts; no Windows execution claim."""
import importlib.util
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('protocol_fixture038',Path(__file__).with_name('test_host_supervision_038.py'))
fixture=importlib.util.module_from_spec(spec);spec.loader.exec_module(fixture)

class NativeUptimeContracts(unittest.TestCase):
    def protocol(self):
        case=fixture.ProtocolTests();case.setUp();return case
    def test_missing_performance_class_cannot_be_queried(self):
        source=(ROOT/'research/windows_038/HostProbe038.ps1').read_text()
        self.assertNotIn('Win32_PerfFormattedData',source)
        self.assertIn('Get-CimInstance Win32_OperatingSystem -OperationTimeoutSec 2',source)
        self.assertIn('Get-CimInstance Win32_Process',source) # unchanged owned-tree containment
    def test_native_binding_is_run_only_uint64_and_cached(self):
        source=(ROOT/'research/windows_038/HostProbe038.ps1').read_text()
        for required in ('GetTickCount64','[UInt64],[Type[]]@()','AssemblyBuilderAccess]::Run)',
                         'if ($null -eq $script:TickMethod038)','NATIVE_BIND BIND_FAILED','NATIVE_CALL CALL_FAILED',
                         '$Milliseconds -isnot [UInt64]','[decimal]::Floor','/1000'):
            self.assertIn(required,source)
        for forbidden in ('Add-Type','AssemblyBuilderAccess]::RunAndSave','GetTempFileName','WriteAllText','GetTickCount\''):
            self.assertNotIn(forbidden,source)
    def test_diagnostic_sources_never_emit_raw_exception_or_stderr(self):
        probe=(ROOT/'research/windows_038/HostProbe038.ps1').read_text()
        supervisor=(ROOT/'research/windows_038/HostSupervisor038.ps1').read_text()
        self.assertIn('BOOT_CIM QUERY_FAILED',probe)
        self.assertIn('VBOX_PROCESS QUERY_FAILED',probe)
        self.assertIn("$stage038='SSH_PROTOCOL'",supervisor)
        self.assertNotIn("'HOST_SUPERVISION_HOLD: '+$_.Exception.Message",supervisor)
        for line in (probe+supervisor).splitlines():
            if '[Console]::Error.WriteLine' in line:
                self.assertIn('Diagnostic038',line)
    def test_wrap_boundary_is_not_32_bit_uptime(self):
        c=self.protocol();first=c.frame();first['measurement']['host_uptime_seconds']=4294967
        c.protocol.accept(first);c.advance();second=c.frame();second['measurement']['host_uptime_seconds']=4294972
        self.assertEqual(c.protocol.accept(second)['accepted_seq'],2)
    def test_dword_rollover_regression_fails(self):
        c=self.protocol();first=c.frame();first['measurement']['host_uptime_seconds']=4294967
        c.protocol.accept(first);c.advance();second=c.frame();second['measurement']['host_uptime_seconds']=4
        with self.assertRaisesRegex(ValueError,'HOST_CLOCK_JUMP_OR_SUSPEND'):c.protocol.accept(second)
    def test_milliseconds_in_seconds_field_fail_consistency(self):
        c=self.protocol();first=c.frame();first['measurement']['host_uptime_seconds']*=1000
        c.protocol.accept(first);c.advance();second=c.frame();second['measurement']['host_uptime_seconds']*=1000
        with self.assertRaisesRegex(ValueError,'HOST_CLOCK_JUMP_OR_SUSPEND'):c.protocol.accept(second)
    def test_invalid_values_fail_closed(self):
        for value in (None,True,-1,float('nan'),float('inf'),2**64,'1000'):
            with self.subTest(value=value):
                c=self.protocol();frame=c.frame();frame['measurement']['host_uptime_seconds']=value
                with self.assertRaises(ValueError):c.protocol.accept(frame)
    def test_suspend_boot_change_and_uptime_regression_remain_refusals(self):
        for key,value in (('host_boot','NEW_BOOT'),('host_uptime_seconds',999),('host_uptime_seconds',1030)):
            with self.subTest(key=key,value=value):
                c=self.protocol();c.protocol.accept(c.frame());c.advance();frame=c.frame();frame['measurement'][key]=value
                with self.assertRaises(ValueError):c.protocol.accept(frame)
    def test_budgets_and_heartbeat_are_unchanged(self):
        supervisor=(ROOT/'research/windows_038/HostSupervisor038.ps1').read_text()
        probe=(ROOT/'research/windows_038/HostProbe038.ps1').read_text()
        self.assertIn('$probeArgs 4000 8192',supervisor)
        self.assertIn("2000 262144 'VBOX_PROCESS'",probe)
        self.assertIn('$sleep=5000-',supervisor)
        self.assertIn('expiry_seconds -ne 15',supervisor)

if __name__=='__main__':unittest.main()
