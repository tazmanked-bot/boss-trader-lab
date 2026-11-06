"""Static synthetic association evidence only; no daemon or time authority."""
import copy
from contextlib import ExitStack,redirect_stdout,redirect_stderr
import hashlib
import importlib
import io
import json
import os
from pathlib import Path
import stat
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from research import nts_chrony_evidence_027 as nts
from research import utc_evidence_026 as utc

RAW=(Path(__file__).parent/'fixtures/nts_synthetic_receipt_027.json').read_bytes()
FIXTURE=json.loads(RAW)


def context():
    return nts.Expected(utc.Binding('a'*40,'synthetic-027','b'*64,'c'*64),
                        'd'*64,'synthetic-authority.invalid','f'*64,'3'*64)


def window(**changes):
    fields=dict(send_mono=1_000_000_000,recv_mono=1_100_000_000,send_boot=2_000_000_000,
                recv_boot=2_100_000_000,now_mono=1_100_000_000,now_boot=2_100_000_000,boot='b'*64)
    fields.update(changes);return utc.Window(**fields)


def evaluate(value=None,local=None,session=None):
    value=copy.deepcopy(FIXTURE) if value is None else value
    return (nts.ShapeSession(context()) if session is None else session).evaluate(
        json.dumps(value,separators=(',',':'),allow_nan=False).encode(),local_window=window() if local is None else local)


class NTSEvidenceTests(unittest.TestCase):
    def setUp(self):
        stack=ExitStack();self.addCleanup(stack.close)
        guards=[stack.enter_context(patch(name,side_effect=AssertionError('FORBIDDEN_IO'))) for name in (
            'socket.socket','socket.getaddrinfo','socket.create_connection','urllib.request.urlopen',
            'http.client.HTTPSConnection','subprocess.Popen','subprocess.run','os.system','time.time')]
        self.addCleanup(lambda:[g.assert_not_called() for g in guards])

    def blocked(self,value,reason=None):
        self.assertEqual(value['B4'],'B4_NO_GO');self.assertFalse(value['independent_utc'])
        self.assertEqual(value['provenance'],'AUTHENTIC_PROVENANCE_NOT_COLLECTED')
        self.assertEqual(value['live_source_admission'],'HOLD')
        self.assertEqual(value['policy'],'NO ORDERS');self.assertEqual(value['requests'],0)
        self.assertEqual(value['process_launches'],0)
        self.assertTrue(all(value[k]=='HOLD' for k in ('B1','B2','B3','B5')))
        if reason:self.assertEqual(value['reason'],reason)

    def test_import_default_inventory_and_cli_do_not_launch_read_or_sample(self):
        with patch('builtins.open',side_effect=AssertionError),patch('os.open',side_effect=AssertionError),patch('time.monotonic_ns',side_effect=AssertionError):
            importlib.reload(nts)
            self.blocked(nts.passive_inventory())
            self.blocked(nts.ShapeSession(context()).evaluate())
            with patch('sys.argv',['nts']),redirect_stdout(io.StringIO()) as out:
                self.assertEqual(nts.main(),2)
            self.blocked(json.loads(out.getvalue()))

    def test_cli_accepts_only_passive_inventory_option(self):
        for option in ('--live','--query','--version-command','--server=example.invalid','--set-time'):
            with self.subTest(option=option),patch('sys.argv',['nts',option]),redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit):nts.main()

    def test_absent_clients_return_unavailable_not_target_capability(self):
        with patch.object(nts,'_binary',side_effect=FileNotFoundError):result=nts.passive_inventory(enabled=True)
        self.assertEqual(result['inventory_status'],'CLIENT_UNAVAILABLE');self.blocked(result)
        self.assertEqual(result['target_client'],'TARGET_CLIENT_CAPABILITY_UNVERIFIED')
        self.assertEqual(result['requested_target'],{'os':'ubuntu-24.04','python':'3.11.17'})

    def test_missing_permission_is_explicit_and_not_executable(self):
        with patch.object(nts,'_binary',side_effect=PermissionError):result=nts.passive_inventory(enabled=True)
        self.assertTrue(all(r['status']=='PERMISSION_DENIED' for c in result['clients'].values() for r in c['paths']))
        self.assertEqual(result['inventory_status'],'CLIENT_UNAVAILABLE');self.blocked(result)

    def test_present_files_do_not_imply_versions_tls_nts_or_package_provenance(self):
        def probe(path,deadline):return {'path':path,'status':'PRESENT_HASHED_NOT_EXECUTED','bytes':4,'sha256':'1'*64}
        with patch.object(nts,'_binary',side_effect=probe) as probe_mock:result=nts.passive_inventory(enabled=True)
        self.assertEqual(probe_mock.call_count,4)
        self.assertEqual(result['inventory_status'],'CLIENT_CAPABILITY_UNVERIFIED')
        for client in result['clients'].values():
            self.assertEqual(client['version'],'NOT_EXECUTED');self.assertEqual(client['tls_nts_compiled_support'],'UNVERIFIED')
            self.assertEqual(client['package_build_provenance'],'UNVERIFIED')
        self.blocked(result)

    def test_partial_client_installation_is_explicit(self):
        def probe(path,deadline):
            if path.endswith('chronyc'):raise FileNotFoundError
            return {'path':path,'status':'PRESENT_HASHED_NOT_EXECUTED'}
        with patch.object(nts,'_binary',side_effect=probe):result=nts.passive_inventory(enabled=True)
        self.assertEqual(result['inventory_status'],'CLIENT_INCOMPLETE')

    def test_probe_uses_fixed_regular_no_follow_bounded_file_and_closes(self):
        metadata=SimpleNamespace(st_mode=stat.S_IFREG|0o755,st_size=4,st_dev=1,st_ino=2,st_mtime_ns=3,st_ctime_ns=4)
        with patch.object(os,'open',return_value=99) as opened,patch.object(os,'fstat',return_value=metadata),\
             patch.object(os,'access',return_value=True),patch.object(os,'read',side_effect=[b'test',b'']),patch.object(os,'close') as closed:
            result=nts._binary('/usr/sbin/chronyd',nts.time.monotonic_ns()+nts.NS)
        self.assertEqual(result['sha256'],hashlib.sha256(b'test').hexdigest())
        self.assertTrue(opened.call_args.args[1]&os.O_NOFOLLOW);closed.assert_called_once_with(99)
        with self.assertRaisesRegex(nts.Refused,'PATH_REFUSED'):nts._binary('/tmp/chronyd',0)

    def test_oversized_nonregular_nonexecutable_or_changed_binary_fails_closed(self):
        cases=[(stat.S_IFREG|0o755,nts.MAX_BINARY+1),(stat.S_IFIFO|0o755,4),(stat.S_IFREG|0o644,4)]
        for mode,size in cases:
            meta=SimpleNamespace(st_mode=mode,st_size=size)
            with self.subTest(mode=mode,size=size),patch.object(os,'open',return_value=99),patch.object(os,'fstat',return_value=meta),patch.object(os,'close') as close:
                with self.assertRaises(nts.Refused):nts._binary('/usr/sbin/chronyd',nts.time.monotonic_ns()+nts.NS)
            close.assert_called_once_with(99)
        before=SimpleNamespace(st_mode=stat.S_IFREG|0o755,st_size=4,st_dev=1,st_ino=2,st_mtime_ns=3,st_ctime_ns=4)
        after=copy.copy(before);after.st_ino=5
        with patch.object(os,'open',return_value=99),patch.object(os,'fstat',side_effect=[before,after]),patch.object(os,'access',return_value=True),\
             patch.object(os,'read',side_effect=[b'test',b'']),patch.object(os,'close'):
            with self.assertRaisesRegex(nts.Refused,'BINARY_CHANGED'):nts._binary('/usr/sbin/chronyd',nts.time.monotonic_ns()+nts.NS)

    def test_inventory_deadline_and_os_errors_are_redacted(self):
        with patch.object(nts.time,'monotonic_ns',return_value=10):
            with self.assertRaisesRegex(nts.Refused,'INVENTORY_TIMEOUT'):nts._binary('/usr/sbin/chronyd',10)
        with patch.object(nts,'_binary',side_effect=OSError('SECRET_ERROR')):
            result=nts.passive_inventory(enabled=True)
        self.assertNotIn('SECRET_ERROR',json.dumps(result))

    def test_synthetic_good_shape_still_refuses_authentic_b4(self):
        result=evaluate();self.blocked(result,'AUTHENTIC_NTS_PROVENANCE_UNAVAILABLE')
        self.assertEqual(result['shape_status'],'OFFLINE_SHAPE_VALID')
        self.assertEqual(result['synthetic_screen_initial_ns'],262010200)
        self.assertLess(len(json.dumps(result)),4096)
        self.assertEqual(utc.authentic_verifier()['B4'],'NO-GO')

    def test_client_missing_or_unsupported_and_build_unknown_refuse(self):
        for field,value,reason in [('name','other','CLIENT_PROFILE_UNSUPPORTED'),('version','unknown','CLIENT_PROFILE_UNSUPPORTED'),
                                   ('binary_sha256','1'*64,'CLIENT_CAPABILITY_UNVERIFIED'),('nts_support','UNVERIFIED','CLIENT_CAPABILITY_UNVERIFIED')]:
            source=copy.deepcopy(FIXTURE);source['client'][field]=value
            self.blocked(evaluate(source),reason)

    def test_missing_extensions_plain_ntp_and_tls_trust_failures(self):
        cases=[('ntp_extensions',[],'NTS_EXTENSION_EVIDENCE_MISSING'),('aead','false','NTS_EXTENSION_EVIDENCE_MISSING'),
               ('plain_ntp_fallback',True,'UNAUTHENTICATED_FALLBACK'),('tls','FAILED','TLS_NTS_KE_UNVERIFIED'),
               ('nts_ke','MISSING','TLS_NTS_KE_UNVERIFIED'),('bootstrap','UNVERIFIED_SYSTEM_TIME','BOOTSTRAP_UNVERIFIED')]
        for field,value,reason in cases:
            with self.subTest(field=field):
                source=copy.deepcopy(FIXTURE);source['association'][field]=value;self.blocked(evaluate(source),reason)

    def test_changed_authority_anchor_or_session_refuses(self):
        for field,value in [('authority','different.invalid'),('anchor_sha256','0'*64),('session_ref','0'*64)]:
            source=copy.deepcopy(FIXTURE);source['association'][field]=value
            self.blocked(evaluate(source),'AUTHORITY_OR_SESSION_CHANGED')

    def test_cookie_absent_expired_or_replayed_association_is_not_evidence(self):
        for state in ('MISSING','EXPIRED','REPLAYED_RECEIPT'):
            source=copy.deepcopy(FIXTURE);source['association']['cookie_state']=state
            self.blocked(evaluate(source),'COOKIE_ASSOCIATION_REFUSED')
        source=copy.deepcopy(FIXTURE);source['association']['cookie_ref']=''
        self.blocked(evaluate(source),'ASSOCIATION_EVIDENCE_MISSING')
        source=copy.deepcopy(FIXTURE);source['association']['cookie_lease_ns']=0
        self.blocked(evaluate(source),'COOKIE_ASSOCIATION_REFUSED')

    def test_reused_receipt_burned_challenge_even_after_failure(self):
        for value in (FIXTURE,{'bad':'receipt'}):
            session=nts.ShapeSession(context());evaluate(value,session=session)
            self.blocked(evaluate(session=session),'REPLAYED_RECEIPT')

    def test_nonce_boot_run_revision_binding_and_replay_identifier(self):
        for field,value in [('nonce','0'*64),('boot','0'*64),('run','changed'),('revision','0'*40)]:
            source=copy.deepcopy(FIXTURE);source['binding'][field]=value
            self.blocked(evaluate(source),'BINDING_MISMATCH')
        source=copy.deepcopy(FIXTURE);source['association']['unique_id']='0'*64
        self.blocked(evaluate(source),'FRESHNESS_BINDING_MISMATCH')

    def test_monotonic_rollback_and_suspend_discrepancy_refuse(self):
        for local in (window(now_mono=1),window(recv_boot=1),window(now_boot=3_100_000_000),window(boot='0'*64)):
            result=evaluate(local=local);self.blocked(result);self.assertEqual(result['shape_status'],'REFUSED')

    def test_receipt_window_cannot_replace_local_capture(self):
        source=copy.deepcopy(FIXTURE);source['window']['send_mono']+=1
        self.blocked(evaluate(source),'LOCAL_WINDOW_MISMATCH')

    def test_excessive_rtt_and_asymmetric_delay_budget_refuse(self):
        local=window(recv_mono=4*nts.NS,now_mono=4*nts.NS,recv_boot=5*nts.NS,now_boot=5*nts.NS)
        self.blocked(evaluate(local=local),'RTT_EXCESSIVE')
        local=window(recv_mono=2_900_000_000,now_mono=2_900_000_000,recv_boot=3_900_000_000,now_boot=3_900_000_000)
        source=copy.deepcopy(FIXTURE)
        for k in source['window']:source['window'][k]=getattr(local,k)
        source['bounds']['root_dispersion_ns']=200_000_000
        self.blocked(evaluate(source,local),'INITIAL_UNCERTAINTY_EXCESSIVE')

    def test_root_delay_dispersion_offset_authority_accuracy_must_fit_cap(self):
        for field,value in [('root_delay_ns',4*nts.NS),('root_dispersion_ns',2*nts.NS),('authority_error_ns',2*nts.NS),('offset_ns',-2*nts.NS)]:
            with self.subTest(field=field):
                source=copy.deepcopy(FIXTURE);source['bounds'][field]=value
                self.blocked(evaluate(source),'INITIAL_UNCERTAINTY_EXCESSIVE')

    def test_negative_boolean_nan_unknown_bounds_refuse(self):
        for field,value in [('root_delay_ns',-1),('root_dispersion_ns',True),('drift_ppm',0),('local_capture_error_ns',0)]:
            source=copy.deepcopy(FIXTURE);source['bounds'][field]=value
            self.blocked(evaluate(source),'BOUNDS_INVALID')
        self.blocked(nts.ShapeSession(context()).evaluate(b'{"x":NaN}',local_window=window()),'JSON_INVALID')

    def test_expired_receipt_cookie_lease_or_grown_uncertainty_refuse(self):
        self.blocked(evaluate(local=window(now_mono=11_100_000_000,now_boot=12_100_000_000)),'LEASE_EXPIRED')
        source=copy.deepcopy(FIXTURE);source['association']['cookie_lease_ns']=1
        self.blocked(evaluate(source,window(now_mono=1_100_000_001,now_boot=2_100_000_001)),'LEASE_EXPIRED')
        source=copy.deepcopy(FIXTURE);source['bounds']['root_dispersion_ns']+=1_737_900_000
        self.blocked(evaluate(source,window(now_mono=3_100_000_000,now_boot=4_100_000_000)),'GROWN_UNCERTAINTY_EXCESSIVE')

    def test_fresh_synthetic_age_is_arithmetic_only(self):
        result=evaluate(local=window(now_mono=2_100_000_001,now_boot=3_100_000_001))
        self.blocked(result);self.assertEqual(result['synthetic_screen_current_ns']-result['synthetic_screen_initial_ns'],100001)

    def test_green_chronyc_output_or_auth_booleans_cannot_clear_provenance(self):
        values=[{'tracking':'Leap status: Normal','authdata':'NTS Cook 8','ntpdata':'Authenticated: Yes','trusted':True}]
        altered=copy.deepcopy(FIXTURE);altered['association']['aead']=True;values.append(altered)
        altered=copy.deepcopy(FIXTURE);altered['origin']='AUTHENTIC_NTS';values.append(altered)
        for value in values:
            result=evaluate(value);self.blocked(result);self.assertEqual(result['shape_status'],'REFUSED')

    def test_shape_validation_does_not_mutate_fixture_or_read_clock_files(self):
        value=copy.deepcopy(FIXTURE)
        with patch('builtins.open',side_effect=AssertionError),patch('time.monotonic_ns',side_effect=AssertionError):
            self.blocked(evaluate(value))
        self.assertEqual(value,FIXTURE)

    def test_strict_size_duplicate_nested_keys_and_secret_fields(self):
        for raw in (b'x'*(nts.MAX_RECEIPT+1),b'{"a":1,"a":2}',b'\xff',b'[]'):
            result=nts.ShapeSession(context()).evaluate(raw,local_window=window());self.blocked(result)
            self.assertEqual(result['shape_status'],'REFUSED')
        value=copy.deepcopy(FIXTURE);value['association']['cookie_secret']='DO_NOT_PRINT'
        result=evaluate(value);self.blocked(result,'RECEIPT_SCHEMA');self.assertNotIn('DO_NOT_PRINT',json.dumps(result))


if __name__=='__main__':unittest.main()
