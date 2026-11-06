"""Runner instrumentation measures actual workers with sealed fake network IO."""
from contextlib import ExitStack,redirect_stdout,redirect_stderr
import importlib
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from research import runner_diagnostic_026 as runner
from research import kraken_btc_transport_025 as transport


class RunnerTests(unittest.TestCase):
    def setUp(self):
        stack=ExitStack();self.addCleanup(stack.close)
        guards=[stack.enter_context(patch(name,side_effect=AssertionError('REAL_IO_FORBIDDEN'))) for name in (
            'socket.socket','socket.getaddrinfo','socket.create_connection','urllib.request.urlopen',
            'http.client.HTTPSConnection','subprocess.Popen','subprocess.run','time.time')]
        self.addCleanup(lambda:[guard.assert_not_called() for guard in guards])

    def test_import_and_default_do_not_read_files_clock_or_fork(self):
        with patch('builtins.open',side_effect=AssertionError),patch('time.monotonic_ns',side_effect=AssertionError),patch('os.fork',side_effect=AssertionError):
            importlib.reload(runner)
            self.assertEqual(runner.run_offline()['reason'],'AUTHORIZATION_MISSING')
            with patch('sys.argv',['harness']),redirect_stdout(io.StringIO()) as out:
                self.assertEqual(runner.main(),2)
            self.assertEqual(json.loads(out.getvalue())['requests'],0)

    def test_real_worker_success_observes_ready_release_reap_and_memory(self):
        value=runner.measured_case('success')
        self.assertEqual(value['reason'],'COMPLETED',value)
        self.assertTrue(value['reaped']);self.assertGreater(value['start_to_child_ready_ns'],0)
        self.assertGreaterEqual(value['start_to_release_ns'],value['start_to_ready_observed_ns'])
        self.assertGreater(value['wait4_peak_rss_bytes'],0)
        self.assertGreater(value['aggregate_sampled_peak_rss_bytes'],0)
        self.assertEqual(value['parent_fd_final'],value['parent_fd_baseline'])
        self.assertEqual(value['ipc_map_bytes'],transport.MAP_SIZE)
        self.assertEqual(value['requests'],0)

    def test_every_fake_hang_is_killed_and_reaped(self):
        for phase in ('dns','connect','tls','read'):
            with self.subTest(phase=phase):
                result=runner.measured_case(phase+'_hang',budget_ns=80_000_000)
                self.assertEqual(result['reason'],'TIMEOUT',result)
                self.assertTrue(result['reaped']);self.assertGreater(result['kill_to_reap_ns'],0)
                self.assertEqual(result['child_trace']['phase'],phase)
                self.assertGreaterEqual(result['observed_overshoot_ns'],0)

    def test_excessive_startup_never_releases(self):
        result=runner.measured_case('startup_delay',budget_ns=50_000_000)
        self.assertEqual(result['reason'],'TIMEOUT');self.assertIsNone(result['start_to_release_ns'])
        self.assertTrue(result['reaped'])

    def test_constrained_child_memory_fails_and_parent_child_pressure_is_measured(self):
        result=runner.measured_case('child_memory_refusal')
        self.assertTrue(result['child_trace']['allocation_refused'])
        self.assertEqual(result['reason'],'NETWORK_UNAVAILABLE')
        result=runner.measured_case('parent_child_pressure')
        self.assertEqual(result['reason'],'COMPLETED',result)
        self.assertEqual(result['child_trace']['controlled_child_pressure_bytes'],16*1024*1024)
        self.assertGreater(result['wait4_peak_rss_bytes'],16*1024*1024)

    def test_controlled_cpu_load_is_only_sampled_behavior(self):
        result=runner.measured_case('cpu_load')
        self.assertEqual(result['reason'],'COMPLETED',result)
        self.assertIn('NOT_WORST_CASE',result['measurement_kind'])
        result=runner.measured_case('cpu_exhaustion',budget_ns=50_000_000)
        self.assertEqual(result['reason'],'TIMEOUT');self.assertTrue(result['reaped'])

    def test_unreapable_error_stops_after_actual_test_cleanup(self):
        original=transport._reap
        def reaped_but_reported_unproved(pid,deadline):
            original(pid,deadline)
            raise transport.Refused('WORKER_UNREAPED')
        with patch.object(transport,'_reap',side_effect=reaped_but_reported_unproved):
            with self.assertRaisesRegex(transport.Refused,'WORKER_UNREAPED'):
                runner.measured_case('dns_hang',budget_ns=30_000_000)

    def test_fd_growth_is_stop_not_a_pass(self):
        original=runner.process_sample
        calls=[]
        def sample(pid):
            value=original(pid);calls.append(pid)
            if pid==os.getpid():value['fds']=len(calls)+10
            return value
        with patch.object(runner,'process_sample',side_effect=sample):
            with self.assertRaisesRegex(transport.Refused,'FD_LEAK_STOP'):runner.measured_case('success')

    def test_unsupported_cgroup_and_proc_measurements_are_unavailable(self):
        with patch.object(runner,'read_small',return_value=None):
            result=runner.cgroup_snapshot('/not-a-cgroup')
        self.assertEqual(result['status'],'UNAVAILABLE')
        self.assertFalse(result['dedicated_containment_verified'])
        self.assertTrue(all(value is None for value in result['values'].values()))
        self.assertIsNone(runner.process_sample(2147483647)['rss_bytes'])
        with patch.object(runner,'process_sample',return_value={'rss_bytes':None,'hwm_bytes':None,'fds':None}):
            case=runner.measured_case('success')
        self.assertEqual(case['reason'],'COMPLETED');self.assertEqual(case['fd_evidence'],'UNAVAILABLE')
        self.assertIsNone(case['aggregate_sampled_peak_rss_bytes'])

    def test_cgroup_values_are_bounded_and_do_not_imply_dedication(self):
        with tempfile.TemporaryDirectory() as directory:
            for name,value in [('memory.max','max'),('memory.current','123'),('memory.peak','456')]:
                (Path(directory)/name).write_text(value)
            result=runner.cgroup_snapshot(directory)
            self.assertEqual(result['values']['memory.current'],123)
            self.assertEqual(result['values']['memory.max'],'max')
            self.assertFalse(result['dedicated_containment_verified'])
            (Path(directory)/'memory.current').write_text('9'*200)
            self.assertIsNone(runner.cgroup_snapshot(directory)['values']['memory.current'])

    def test_git_head_parsing_does_not_run_git_or_follow_arbitrary_files(self):
        with tempfile.TemporaryDirectory() as directory:
            git=Path(directory)/'.git';git.mkdir();(git/'HEAD').write_text('a'*40+'\n')
            self.assertEqual(runner._git_head(directory),'a'*40)
            (git/'HEAD').write_text('ref: ../../secret')
            self.assertIsNone(runner._git_head(directory))

    def test_revision_mismatch_cannot_run_cases(self):
        with patch.object(runner,'_git_head',return_value='b'*40),patch.object(runner,'measured_case',side_effect=AssertionError):
            with self.assertRaisesRegex(transport.Refused,'REVISION_MISMATCH'):runner.run_offline(revision='a'*40)

    def test_allowlisted_runner_identity_never_dumps_environment(self):
        with patch.dict(os.environ,{'SUPER_SECRET_TOKEN':'DO_NOT_PRINT','ImageVersion':'20261101.1.0'}):
            profile=runner.runner_profile('a'*40)
        self.assertNotIn('DO_NOT_PRINT',json.dumps(profile))
        self.assertEqual(profile['runner_image']['ImageVersion'],'20261101.1.0')
        self.assertFalse(profile['target_verified'])

    def test_report_bounds_and_holds_are_not_upgraded(self):
        fake={'case':'success','requests':0,'reason':'COMPLETED'}
        with patch.object(runner,'measured_case',return_value=fake),patch.object(runner,'_git_head',return_value='a'*40):
            result=runner.run_offline(revision='a'*40)
        self.assertEqual(len(result['cases']),10)
        self.assertLess(len(json.dumps(result)),runner.MAX_REPORT_BYTES)
        self.assertEqual(result['B4'],'NO-GO');self.assertEqual(result['B5'],'HOLD')
        self.assertFalse(result['hard_containment_verified'])

    def test_parent_memory_failure_allocates_no_worker_or_ipc(self):
        with patch.object(runner,'bytearray',side_effect=MemoryError,create=True),patch.object(os,'fork',side_effect=AssertionError),patch.object(runner.mmap,'mmap',side_effect=AssertionError):
            with self.assertRaises(MemoryError):runner.measured_case('parent_child_pressure')

    def test_bad_cases_budgets_and_cli_live_options_refuse(self):
        for case,budget in [('live',50_000_000),('success',True),('success',10_000_000),('success',2*runner.NS)]:
            with self.subTest(case=case,budget=budget),self.assertRaises(transport.Refused):runner.measured_case(case,budget_ns=budget)
        with patch('sys.argv',['harness','--live']),redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit):runner.main()


if __name__=='__main__':unittest.main()
