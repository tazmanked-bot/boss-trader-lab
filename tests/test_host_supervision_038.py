"""Synthetic protocol/host fixtures; do not qualify Windows, SSH or VirtualBox."""
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch
from research import host_supervision_038 as h, recorder_health_037 as r, controlled_build_037 as b

VM='12345678-1234-1234-1234-123456789abc'


class Clock:
    def __init__(self):self.value=1000.0
    def __call__(self):return self.value
    def advance(self,n):self.value+=n


class ProtocolTests(unittest.TestCase):
    def setUp(self):
        self.clock=Clock();self.wall=Clock();self.boot=Clock()
        self.scope={'plan_sha256':'a'*64,'guest_boot':'guest-boot','observer':{'test':'inert'},'scripts':h.code_hashes(),'vm_uuid':VM}
        self.protocol=h.Protocol(self.scope,mono=self.clock,boot=self.boot,wall=self.wall)
        self.first=None
    def frame(self):
        e=self.protocol.envelope()
        frame={k:e[k] for k in ('version','session','challenge','seq','plan_sha256','guest_boot','observer_sha256')}
        frame['measurement']={'platform':'Windows','host_boot':'SYNTHETIC_BOOT','host_session':'SYNTHETIC_PROCESS',
            'host_pid':123,'host_elapsed_ms':int(self.clock.value*1000),'host_utc_ms':int(self.clock.value*1000),
            'host_uptime_seconds':int(self.clock.value),'probe_duration_ms':100,'vm_uuid':VM,'vm_state':'running',
            'forward_host_port':2222,'forward_guest_port':22,'forward_host_ip':'127.0.0.1',
            'supervisor_sha256':self.scope['scripts']['HostSupervisor038.ps1'],
            'probe_sha256':self.scope['scripts']['HostProbe038.ps1'],
            'tool_sha256':{'ssh':'b'*64,'powershell':'c'*64,'virtualbox':'d'*64}}
        return frame
    def advance(self,n=5):
        for clock in (self.clock,self.boot,self.wall):clock.advance(n)
    def test_positive_fresh_challenges_sequence_and_independent_clocks(self):
        first=self.frame();a=self.protocol.accept(first);self.advance();second=self.frame();c=self.protocol.accept(second)
        self.assertNotEqual(first['challenge'],second['challenge']);self.assertEqual((a['accepted_seq'],c['accepted_seq']),(1,2))
    def test_replay_poison_is_terminal(self):
        old=self.frame();self.protocol.accept(old);self.advance()
        with self.assertRaisesRegex(ValueError,'REPLAY'):self.protocol.accept(old)
        with self.assertRaisesRegex(ValueError,'TERMINAL'):self.protocol.accept(self.frame())
    def test_wrong_session_plan_boot_observer_or_order_rejected(self):
        for key in ('session','plan_sha256','guest_boot','observer_sha256','seq','challenge'):
            self.setUp();value=self.frame();value[key]=99 if key=='seq' else 'foreign'
            with self.subTest(key=key),self.assertRaises(ValueError):self.protocol.accept(value)
    def test_guest_freeze_resume_and_clock_jumps_fail_before_reaccept(self):
        for change in ('all','boot','wall','reverse'):
            self.setUp();self.protocol.accept(self.frame())
            if change=='all':self.advance(16)
            elif change=='boot':self.boot.advance(20)
            elif change=='wall':self.wall.advance(20)
            else:self.clock.advance(-1)
            with self.subTest(change=change),self.assertRaises(ValueError):self.protocol.accept(self.frame())
    def test_host_reboot_or_process_change_rejected(self):
        for key,value in (('host_boot','new-boot'),('host_session','new-session'),('host_pid',124)):
            self.setUp();self.protocol.accept(self.frame());self.advance();new=self.frame();new['measurement'][key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):self.protocol.accept(new)
    def test_host_clock_jump_suspend_and_reorder(self):
        for key,delta in (('host_utc_ms',30000),('host_elapsed_ms',30000),('host_uptime_seconds',30),('host_utc_ms',-10000)):
            self.setUp();self.protocol.accept(self.frame());self.advance();new=self.frame();new['measurement'][key]+=delta
            with self.subTest(key=key,delta=delta),self.assertRaises(ValueError):self.protocol.accept(new)
    def test_non_windows_wrong_vm_forwarding_probe_budget_and_script(self):
        for key,value in (('platform','Linux'),('vm_state','paused'),('vm_uuid','foreign'),('forward_host_port',2223),('probe_duration_ms',4001),('supervisor_sha256','0'*64),('host_elapsed_ms',float('nan'))):
            self.setUp();frame=self.frame();frame['measurement'][key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):self.protocol.accept(frame)
    def test_malformed_extra_fields_and_boolean_sequence(self):
        for kind in ('missing','extra','bool'):
            self.setUp();frame=self.frame()
            if kind=='missing':frame.pop('measurement')
            elif kind=='extra':frame['desktop_stable']=True
            else:frame['seq']=True
            with self.subTest(kind=kind),self.assertRaises(ValueError):self.protocol.accept(frame)


class EvidenceTests(unittest.TestCase):
    def setUp(self):
        old=os.umask(0o077);self.addCleanup(os.umask,old)
        self.temp=tempfile.TemporaryDirectory(dir=Path(__file__).parent);self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name).resolve();self.directory=self.root/'host';self.directory.mkdir(mode=0o700)
        self.config={'job':str(self.root/'job'),'source':'/inert-source','health_file':str(self.root/'health.json'),
            'protected_roots':['/inert-recorder'],'recorder_id':'inert','collection_cadence_seconds':900,
            'host_supervision':{'policy':h.POLICY,'directory':str(self.directory),'vm_uuid':VM,'ssh_peer':'10.0.2.2','review_ref':'SYNTHETIC_NOT_OWNER_AUTHORIZATION'}}
        self.plan={'job':self.config['job'],'config':self.config}
        self.health={'observer':{'pid':123,'start_ticks':'1','boot_id':r.boot_id(),'session':'synthetic','code_sha256':'e'*64}}
        scope={'plan_sha256':h.digest(self.plan),'guest_boot':r.boot_id(),'observer':h.observer_scope(self.health),
            'vm_uuid':VM,'scripts':h.code_hashes(),'policy':h.POLICY,
            'transport':{'kind':'EXISTING_AUTHENTICATED_SSH','peer':'10.0.2.2','server_port':22}}
        self.value={'version':h.POLICY,'valid':True,'session':'f'*64,'scope':scope,'scope_sha256':h.digest(scope),
            'producer':{'pid':os.getpid(),'start_ticks':r.process_identity(os.getpid()),'boot_id':r.boot_id(),'code_sha256':r.p.hash_file(Path(h.__file__))[0]},
            'accepted_seq':1,'receipt_monotonic':time.monotonic(),'receipt_boottime':h.boot_clock(),'receipt_wall':time.time()}
    def write(self):
        path=self.directory/h.STATE
        if path.exists():path.unlink()
        with h.Store(self.directory) as s:s.write(self.value)
    def test_private_atomic_writer_and_concurrent_exclusion(self):
        with h.Store(self.directory) as first:
            first.write(self.value);self.assertEqual((self.directory/h.STATE).stat().st_mode&0o777,0o600)
            with self.assertRaisesRegex(ValueError,'BUSY'):
                with h.Store(self.directory):pass
            self.value['accepted_seq']=2;first.write(self.value)
        self.assertEqual(h.read(self.directory/h.STATE)['accepted_seq'],2)
    def test_explicit_new_session_cannot_replace_live_receiver(self):
        self.write()
        with self.assertRaisesRegex(ValueError,'EXPLICIT_NEW'):
            with h.Store(self.directory):pass
        with self.assertRaisesRegex(ValueError,'ALIVE'):
            with h.Store(self.directory,new_session=True):pass
        self.value['valid']=False;(self.directory/h.STATE).write_text(h.canonical(self.value))
        with h.Store(self.directory,new_session=True) as s:s.write(self.value)
    def test_foreign_or_replaced_evidence_refused(self):
        with h.Store(self.directory) as s:
            s.write(self.value);path=self.directory/h.STATE
            other=self.directory/'foreign';other.write_text('foreign');os.replace(other,path)
            with self.assertRaisesRegex(ValueError,'REPLACED'):s.write(self.value)
        self.assertEqual(path.read_text(),'foreign')
    def test_positive_consumption_is_operational_not_hardware_claim(self):
        self.write()
        with patch.object(h,'receiver_command'):
            result=h.check(self.plan,self.health)
        self.assertEqual(result['policy'],h.POLICY);self.assertFalse(result['physical_hardware_verified'])
        self.assertEqual(result['hardware_uncertainty'],h.UNCERTAINTY)
    def test_fake_current_pid_without_receiver_command_is_not_authenticated_evidence(self):
        self.write()
        with self.assertRaisesRegex(ValueError,'COMMAND_BINDING'):h.check(self.plan,self.health)
    def test_stale_guest_receipts_stop_and_dead_receiver(self):
        for key in ('receipt_monotonic','receipt_boottime','receipt_wall'):
            self.setUp();self.value[key]-=16;self.write()
            with self.subTest(key=key),patch.object(h,'receiver_command'),self.assertRaisesRegex(ValueError,'STALE'):h.check(self.plan,self.health)
        self.setUp();self.value['producer']['pid']=99999999;self.write()
        with self.assertRaisesRegex(ValueError,'LOST'):h.check(self.plan,self.health)
    def test_wrong_plan_boot_observer_and_owner_stop_refused(self):
        self.write()
        with patch.object(h,'receiver_command'):
            wrong=copy.deepcopy(self.plan);wrong['new-field']='new-plan'
            with self.assertRaisesRegex(ValueError,'MISMATCH'):h.check(wrong,self.health)
            wrong=copy.deepcopy(self.health);wrong['observer']['session']='new-observer'
            with self.assertRaisesRegex(ValueError,'MISMATCH'):h.check(self.plan,wrong)
            (self.directory/'STOP').touch()
            with self.assertRaisesRegex(ValueError,'OWNER_STOP'):h.check(self.plan,self.health)
    def test_revoke_cannot_be_healed_by_fresh_timestamp(self):
        self.value['valid']=False;self.write()
        with self.assertRaisesRegex(ValueError,'SUPERVISION_LOST'):h.check(self.plan,self.health)
    def test_malformed_evidence_is_hold(self):
        self.value={'version':h.POLICY,'valid':True};self.write()
        with self.assertRaisesRegex(ValueError,'SCHEMA'):h.check(self.plan,self.health)
    def test_no_ssh_environment_cannot_launch_trusted_receiver(self):
        with patch.dict(os.environ,{},clear=True):
            with self.assertRaisesRegex(ValueError,'SSH_CONTEXT'):h.ssh_context(self.config['host_supervision'])
    def test_foreign_ssh_peer_rejected(self):
        with patch.dict(os.environ,{'SSH_CONNECTION':'127.0.0.1 123 10.0.2.15 22'}):
            with self.assertRaisesRegex(ValueError,'SSH_CONTEXT'):h.ssh_context(self.config['host_supervision'])
    def test_host_policy_paths_are_outside_originals_and_job(self):
        bad=copy.deepcopy(self.config);bad['protected_roots']=[str(self.root)]
        with self.assertRaisesRegex(ValueError,'OVERLAP'):h.policy(bad)


class IntegrationTests(unittest.TestCase):
    def setUp(self):
        spec=importlib.util.spec_from_file_location('baseline_h3',Path(__file__).with_name('test_recorder_health_037.py'))
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        self.module=module;self.record=module.evidence()
    def test_legacy_config_keeps_physical_hold_new_policy_requires_real_host_check(self):
        config={'health_file':'/inert','recorder_id':'inert','collection_cadence_seconds':900}
        with patch.object(b,'read_json',return_value=self.record),patch.object(r.time,'monotonic',return_value=self.module.MONO):
            with self.assertRaisesRegex(ValueError,'PHYSICAL_HOST'):b.health({'config':config},now=self.module.NOW)
            config['host_supervision']={}
            with patch.object(h,'check',side_effect=ValueError('HOST_LOST')):
                with self.assertRaisesRegex(ValueError,'HOST_LOST'):b.health({'config':config},now=self.module.NOW)
            with patch.object(h,'check',return_value={'binding':{'session':'synthetic'}}):
                result=b.health({'config':config},now=self.module.NOW)
            self.assertFalse(result['physical_hardware_verified']);self.assertFalse(self.record['desktop_stable'])
    def test_legacy_desktop_boolean_cannot_bypass_opt_in_host_supervision(self):
        record={'version':'external-recorder-health-037-v1','recorder_id':'inert','measured_at':self.module.NOW,
                'last_collection_at':self.module.NOW,'healthy':True,'desktop_stable':True}
        config={'health_file':'/inert','recorder_id':'inert','collection_cadence_seconds':900,'host_supervision':{}}
        with patch.object(b,'read_json',return_value=record):
            with self.assertRaisesRegex(ValueError,'INDEPENDENT_RECORDER_OBSERVER_REQUIRED'):b.health({'config':config},now=self.module.NOW)
    def test_cli_diagnostics_do_not_log_session_tokens(self):
        plan={'job':'/inert'};secret='SECRET_SYNTHETIC_SESSION_TOKEN'
        details={'binding':{'session':secret},'seq':1}
        with patch.object(b,'read_json',return_value=plan),patch.object(h,'current_observer',return_value={}),patch.object(h,'check',return_value=details),patch('builtins.print') as output:
            self.assertEqual(h.main(['check','--plan','/inert/plan.json']),0)
        logged=str(output.call_args)
        self.assertNotIn(secret,logged);self.assertIn('session_binding_sha256',logged)
    def test_actual_harmless_watchdog_cleans_up_on_supervision_loss(self):
        import sys
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as root:
            start=time.monotonic()
            def guard():
                if time.monotonic()-start>.15:raise ValueError('HOST_SUPERVISION_LOST')
            with self.assertRaisesRegex(ValueError,'HOST_SUPERVISION_LOST') as caught:
                b.supervise([sys.executable,'-c','import time;time.sleep(60)'],root,wall=2,cpu=1,cap=128,check=guard)
            self.assertTrue(caught.exception.receipt['direct_child_reaped'])
    def test_harmless_proof_cannot_switch_session_or_accept_one_heartbeat(self):
        clock=Clock();current={'binding':{'session':'a'},'seq':1}
        def sleep(value):clock.advance(value)
        with patch.object(h,'boot_clock',clock),patch.object(h.time,'sleep',side_effect=sleep),patch.object(h,'current_observer',return_value={}),patch.object(h,'check',side_effect=lambda *_:copy.deepcopy(current)):
            with self.assertRaisesRegex(ValueError,'THREE_HEARTBEATS'):h.prove({},15)
        clock=Clock();calls=[0]
        def check(*_):
            calls[0]+=1;return {'binding':{'session':'a' if calls[0]<3 else 'b'},'seq':calls[0]}
        with patch.object(h,'boot_clock',clock),patch.object(h.time,'sleep',side_effect=lambda t:clock.advance(t)),patch.object(h,'current_observer',return_value={}),patch.object(h,'check',side_effect=check):
            with self.assertRaisesRegex(ValueError,'SESSION_CHANGED'):h.prove({},15)
    def test_powershell_source_safety_contract_is_not_windows_execution_evidence(self):
        source=(h.WINDOWS/'HostSupervisor038.ps1').read_text();probe=(h.WINDOWS/'HostProbe038.ps1').read_text()
        for required in ('StrictHostKeyChecking=yes','UpdateHostKeys=no','BatchMode=yes','ConnectTimeout=5','ConnectionAttempts=1','ServerAliveInterval=5','ClearAllForwardings=yes','-F'):
            self.assertIn(required,source)
        for forbidden in ('StrictHostKeyChecking=no','ExecutionPolicy Bypass','Set-ExecutionPolicy','modifyvm','Start-Service','Register-ScheduledTask','Add-Type'):
            self.assertNotIn(forbidden,source+probe)
        self.assertIn('-ProbeLibraryOnly',source);self.assertNotIn('[switch]$LibraryOnly',probe)
        self.assertIn('showvminfo',probe);self.assertIn('Get-CimInstance',probe);self.assertIn('OWNED_TREE_CLEANUP_UNVERIFIED',probe)



class AdmissionTests(unittest.TestCase):
    def setUp(self):
        spec=importlib.util.spec_from_file_location('baseline_execute038',Path(__file__).with_name('test_controlled_build_037.py'))
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        self.case=module.OneShotTests();self.case.setUp();self.addCleanup(self.case.doCleanups)
        self.binding={'session':'SYNTHETIC_NOT_WINDOWS_QUALIFIED','scope_sha256':'0'*64,'producer':{'fixture':True}}
        case=self.case;case.plan['config']['host_supervision']={'fixture':True}
        case.q.update(plan_sha256=h.digest(case.plan),host_supervision_proof={'binding':self.binding})
        (case.root/'qualification.json').write_text(json.dumps(case.q))
        case.approval.update(plan_sha256=h.digest(case.plan),qualification_sha256=h.digest(case.q),
            host_supervision_binding=self.binding,host_policy=h.POLICY,hardware_uncertainty=h.UNCERTAINTY)
        self.health=patch.object(b,'health',return_value={'host_supervision':{'binding':self.binding}});self.health.start()
    def test_positive_scoped_admission_uses_real_harmless_compiler_substitute_only(self):
        result=b.execute(self.case.plan,self.case.approval)
        self.assertEqual(result['operation'],'LOCAL_BUILD_PASS_INFERENCE_HOLD')
        self.assertTrue(all(v['direct_child_reaped'] for v in result['steps']))
        with self.assertRaisesRegex(ValueError,'ONE_SHOT'):b.execute(self.case.plan,self.case.approval)
    def test_approval_cannot_switch_qualified_host_session(self):
        self.case.q['host_supervision_proof']['binding']={'session':'other'}
        (self.case.root/'qualification.json').write_text(json.dumps(self.case.q))
        with self.assertRaisesRegex(ValueError,'QUALIFICATION_SESSION'):b.execute(self.case.plan,self.case.approval)
        self.assertFalse((self.case.root/'attempt.json').exists())
    def test_foreign_or_unacknowledged_approval_refuses_before_launch(self):
        for key,value in (('host_policy','fake'),('hardware_uncertainty','SAFE'),('host_supervision_binding',{'session':'other'})):
            approval=dict(self.case.approval,**{key:value})
            with self.subTest(key=key),self.assertRaisesRegex(ValueError,'HOST_APPROVAL'):b.execute(self.case.plan,approval)
        self.assertFalse((self.case.root/'attempt.json').exists())
    def test_explicit_owner_policy_acceptance_is_not_heartbeat_bypass(self):
        path=self.case.root/'new-approval.json'
        with self.assertRaisesRegex(ValueError,'ACCEPTANCE_REQUIRED'):b.approval_record(self.case.plan,'synthetic-ref',str(path))
        self.assertFalse(path.exists())
        with patch.object(b,'health',side_effect=ValueError('HOST_SUPERVISION_LOST')):
            with self.assertRaisesRegex(ValueError,'HOST_SUPERVISION_LOST'):b.approval_record(self.case.plan,'synthetic-ref',str(path),accept_host_policy=True)
        self.assertFalse(path.exists())
    def test_supervision_change_aborts_real_harmless_worker_and_spends_attempt(self):
        import sys
        started=time.monotonic()
        def health(_):
            return {'host_supervision':{'binding':self.binding if time.monotonic()-started<.2 else {'session':'new'}}}
        with patch.object(b,'health',side_effect=health),patch.object(b,'sandbox',return_value=[sys.executable,'-c','import time;time.sleep(60)']):
            result=b.execute(self.case.plan,self.case.approval)
        self.assertEqual(result['operation'],'BUILD_FAILED');self.assertEqual(result['blocker'],'HOST_BUILD_SESSION_CHANGED')
        self.assertTrue(result['failure_process']['direct_child_reaped']);self.assertTrue((self.case.root/'attempt.json').exists())
    def test_staging_cannot_report_success_under_new_session(self):
        def stage(_):
            self.health.stop();patch.object(b,'health',return_value={'host_supervision':{'binding':{'session':'new'}}}).start()
            return {'fixture':'NO_REAL_ARTIFACT'}
        with patch.object(b,'stage',side_effect=stage):result=b.execute(self.case.plan,self.case.approval)
        self.assertEqual(result['operation'],'BUILD_FAILED');self.assertEqual(result['blocker'],'HOST_BUILD_SESSION_CHANGED')


class AdditionalProtocolTests(unittest.TestCase):
    setUp=ProtocolTests.setUp
    frame=ProtocolTests.frame
    advance=ProtocolTests.advance
    def test_missing_heartbeat_never_resumes_same_session(self):
        self.protocol.accept(self.frame());self.advance(60)
        with self.assertRaises(ValueError):self.protocol.accept(self.frame())
        self.protocol.last=(self.clock(),self.boot(),self.wall())
        with self.assertRaisesRegex(ValueError,'TERMINAL'):self.protocol.accept(self.frame())
    def test_guest_boottime_jump_is_not_masked_by_frozen_monotonic(self):
        self.protocol.accept(self.frame());self.boot.advance(16)
        with self.assertRaisesRegex(ValueError,'GUEST_CLOCK'):self.protocol.accept(self.frame())
    def test_tools_vm_forward_identity_cannot_change_mid_session(self):
        self.protocol.accept(self.frame());self.advance();value=self.frame();value['measurement']['tool_sha256']['ssh']='0'*64
        with self.assertRaisesRegex(ValueError,'PROCESS_CHANGE'):self.protocol.accept(value)




class ReceiverPipeTests(unittest.TestCase):
    setUp=EvidenceTests.setUp
    def spawn(self,ttl=1):
        import subprocess,sys
        plan=copy.deepcopy(self.plan)
        plan['host']={'boot_id':r.boot_id()}
        hashes=h.code_hashes()
        plan['tools']={'host_protocol_038':{'sha256':h.p.hash_file(Path(h.__file__))[0]},
            'windows_supervisor_038':{'sha256':hashes['HostSupervisor038.ps1']},
            'windows_probe_038':{'sha256':hashes['HostProbe038.ps1']}}
        path=self.root/'fixture-plan.json';path.write_text(json.dumps(plan))
        script="""import json,sys
from research import host_supervision_038 as h
plan=json.load(open(sys.argv[1]))
h.TTL=float(sys.argv[2])
h.ssh_context=lambda cfg:{'kind':'EXISTING_AUTHENTICATED_SSH','peer':cfg['ssh_peer'],'server_port':22}
h.current_observer=lambda plan:{'observer':{'pid':123,'start_ticks':'1','boot_id':h.recorder.boot_id(),'session':'inert','code_sha256':'e'*64}}
h.serve(plan,h.digest(plan),max_seconds=3)
"""
        child=subprocess.Popen([sys.executable,'-u','-B','-c',script,str(path),str(ttl)],cwd=Path(__file__).resolve().parents[1],
            stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        self.addCleanup(self.reap,child)
        import select
        self.assertTrue(select.select([child.stdout],[],[],3)[0],'fixture receiver did not emit hello')
        hello=json.loads(child.stdout.readline());return child,hello
    def reap(self,child):
        if child.poll() is None:child.kill()
        child.communicate(timeout=3)
    def test_actual_pipe_timeout_revokes_fixture_session(self):
        child,hello=self.spawn(.2);child.wait(timeout=3)
        state=h.read(self.directory/h.STATE)
        self.assertFalse(state['valid']);self.assertIn('TIMEOUT',state['reason'])
    def test_actual_pipe_eof_revokes_fixture_session(self):
        child,hello=self.spawn();child.stdin.close();child.stdin=None;child.wait(timeout=3)
        self.assertEqual(h.read(self.directory/h.STATE)['reason'],'HOST_TRANSPORT_EOF')
    def test_actual_owner_stop_revokes_fixture_session(self):
        child,hello=self.spawn();(self.directory/'STOP').touch();child.wait(timeout=3)
        self.assertEqual(h.read(self.directory/h.STATE)['reason'],'HOST_OWNER_STOP')
    def test_malformed_transport_cannot_remain_valid(self):
        child,hello=self.spawn();child.stdin.write(b'{not-json}\n');child.stdin.flush();child.wait(timeout=3)
        self.assertFalse(h.read(self.directory/h.STATE)['valid'])


class ConfigProofTests(unittest.TestCase):
    setUp=EvidenceTests.setUp
    def test_new_config_keeps_original_inventory_references_and_bytes(self):
        source=self.root/'original.json';original={k:v for k,v in self.config.items() if k!='host_supervision'}
        original.update(cgroup_parent='/inert-cgroup',toolchain_evidence='/inert-tools.json',system_libraries='/inert-libraries.json')
        source.write_text(json.dumps(original));before=source.read_bytes()
        output=self.root/'new-config.json';directory=self.root/'fresh-host'
        result=h.attach_config(str(source),str(output),str(directory),VM,'10.0.2.2','SYNTHETIC_OWNER_REVIEW')
        self.assertEqual(source.read_bytes(),before);new=json.loads(output.read_text())
        for key,value in original.items():self.assertEqual(new[key],value)
        self.assertEqual(directory.stat().st_mode&0o777,0o700);self.assertTrue(result['old_config_unchanged'])
    def test_positive_harmless_proof_needs_multiple_fresh_challenges(self):
        clock=Clock()
        def check(*_):return {'binding':{'session':'same'},'seq':1+int((clock.value-1000)/5)}
        with patch.object(h,'boot_clock',clock),patch.object(h.time,'sleep',side_effect=lambda n:clock.advance(n)),patch.object(h,'current_observer',return_value={}),patch.object(h,'check',side_effect=check):
            proof=h.prove({},16)
        self.assertGreaterEqual(proof['unique_heartbeats'],3);self.assertEqual(proof['hardware_uncertainty'],h.UNCERTAINTY)


if __name__=='__main__':unittest.main()
