"""Real harmless subprocess watchdogs; fake cgroup tests are not kernel evidence."""
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
import time
import unittest
from unittest.mock import patch
from research import controlled_build_037 as b, portable_runtime_036 as r


class SupervisorTests(unittest.TestCase):
    def setUp(self):
        old=os.umask(0o077);self.addCleanup(os.umask,old)
        self.temp=tempfile.TemporaryDirectory(dir=Path(__file__).parent);self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name).resolve()
    def run_work(self,code,**kw):
        return b.supervise([sys.executable,'-I','-S','-B','-c',code],self.root,wall=kw.pop('wall',2),cpu=kw.pop('cpu',2),cap=kw.pop('cap',4096),**kw)
    def test_success_real_process_nice_and_no_secret(self):
        raw,receipt=self.run_work("import os,json;print(json.dumps({'nice':os.getpriority(os.PRIO_PROCESS,0),'secret':os.environ.get('OWNER_TEST_SECRET'),'cpus':len(os.sched_getaffinity(0))}))")
        value=json.loads(raw);self.assertGreaterEqual(value['nice'],10);self.assertIsNone(value['secret'])
        self.assertEqual(value['cpus'],1)
        self.assertTrue(receipt['direct_child_reaped']);self.assertEqual(receipt['cgroup_empty'],'UNVERIFIED_NO_CGROUP_SYNTHETIC_ONLY')
    def test_timeout_kills_and_reaps_real_child(self):
        start=time.monotonic()
        with self.assertRaisesRegex(ValueError,'WALL_TIMEOUT') as caught:self.run_work('import time;time.sleep(20)',wall=.15)
        self.assertTrue(caught.exception.receipt['direct_child_reaped']);self.assertLess(time.monotonic()-start,4)
    def test_output_flood_capped_and_preserved(self):
        log=self.root/'bounded.log'
        with self.assertRaisesRegex(ValueError,'OUTPUT_LIMIT'):self.run_work("import os;os.write(1,b'x'*100000)",cap=128,log=log)
        self.assertEqual(log.stat().st_size,128)
    def test_nonzero_preserves_failure_receipt(self):
        with self.assertRaisesRegex(ValueError,'NONZERO') as caught:self.run_work('raise SystemExit(4)')
        self.assertEqual(caught.exception.receipt['exit_code'],4)
    def test_cpu_rlimit_real_busy_loop(self):
        with self.assertRaisesRegex(ValueError,'NONZERO') as caught:self.run_work('while True:pass',cpu=1,wall=4)
        self.assertTrue(caught.exception.receipt['direct_child_reaped'])
    def test_health_loss_stops_running_workload(self):
        start=time.monotonic()
        def check():
            if time.monotonic()-start>.12:raise ValueError('RECORDER_LOST')
        with self.assertRaisesRegex(ValueError,'RECORDER_LOST'):self.run_work('import time;time.sleep(20)',check=check)
    def test_no_spawn_if_precheck_fails(self):
        with patch.object(b.subprocess,'Popen',side_effect=AssertionError('must not spawn')):
            with self.assertRaisesRegex(ValueError,'STOP'):self.run_work('pass',check=lambda: (_ for _ in ()).throw(ValueError('STOP')))
    def test_invalid_budgets_never_spawn(self):
        for kwargs in ({'wall':float('nan')},{'wall':0},{'wall':7201},{'cpu':0},{'cap':b.LIMITS['output_max_bytes']+1}):
            with self.subTest(kwargs=kwargs),self.assertRaises(ValueError):self.run_work('pass',**kwargs)
    def test_attach_before_release_and_kill(self):
        events=[]
        class FakeGroup:
            start_cpu=0
            def attach(self,pid):events.append('attach')
            def cpu_seconds(self):return 0
            def kill(self):events.append('kill')
            def empty(self):return True
        raw,receipt=self.run_work("print('INERT')",group=FakeGroup())
        self.assertEqual(events,['attach','kill']);self.assertTrue(receipt['cgroup_empty'])
    def test_aggregate_cpu_budget_mocked_group(self):
        class FakeGroup:
            start_cpu=0
            def attach(self,pid):pass
            def cpu_seconds(self):return 100
            def kill(self):pass
            def empty(self):return True
        with self.assertRaisesRegex(ValueError,'GROUP_CPU'):self.run_work('import time;time.sleep(10)',group=FakeGroup())
    def test_attach_failure_never_releases_payload(self):
        marker=self.root/'must-not-exist'
        class FakeGroup:
            def attach(self,pid):raise ValueError('ATTACH_FAILED')
            def kill(self):pass
            def empty(self):return True
        with self.assertRaisesRegex(ValueError,'ATTACH_FAILED'):
            self.run_work('open('+repr(str(marker))+",'w').close()",group=FakeGroup())
        self.assertFalse(marker.exists())
    def test_harmless_compiler_substitute_not_actual_compilation(self):
        out=self.root/'synthetic-output'
        raw,receipt=self.run_work("from pathlib import Path;Path("+repr(str(out))+").write_text('INERT COMPILER SUBSTITUTE');print('synthetic configure/build only')")
        self.assertEqual(out.read_text(),'INERT COMPILER SUBSTITUTE');self.assertTrue(receipt['direct_child_reaped'])


class PolicyTests(unittest.TestCase):
    def setUp(self):
        old=os.umask(0o077);self.addCleanup(os.umask,old)
        self.temp=tempfile.TemporaryDirectory(dir=Path(__file__).parent);self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name).resolve()
    def test_source_group_writable_authenticated_export(self):
        # Reuse CODEX036 original inert Git fixture, but exercise new raw-object reader.
        spec=importlib.util.spec_from_file_location('fixture036',Path(__file__).with_name('test_portable_runtime_036.py'))
        mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
        case=mod.PortableTests();case.setUp()
        try:
            (case.source/'LICENSE').chmod(0o660);case.source.chmod(0o770)
            manifest=b.source_inventory(case.source)
            self.assertEqual(manifest['commit'],case.commit);self.assertEqual((case.source/'LICENSE').stat().st_mode&0o777,0o660)
            (case.source/'LICENSE').write_text('corruption')
            with self.assertRaisesRegex(ValueError,'DIRTY_TRACKED'):b.source_inventory(case.source)
        finally:case.doCleanups()
    def test_source_symlink_refused_without_chmod(self):
        link=self.root/'alias';link.symlink_to('/tmp')
        with self.assertRaisesRegex(ValueError,'SYMLINK'):b.no_links(link)
    def test_fixed_recipe_and_budget(self):
        configure,compile=b.commands();self.assertIn('-DCMAKE_C_COMPILER=/usr/bin/cc',configure)
        self.assertEqual(compile[-4:],['--target','llama-cli','--parallel','1'])
        self.assertEqual(b.LIMITS['wall_seconds'],7200);self.assertEqual(b.LIMITS['cpu_seconds'],5400)
        self.assertEqual(b.LIMITS['jobs'],1);self.assertEqual(b.LIMITS['memory_max_bytes'],3*1024**3)
    def plan(self):
        health=self.root/'health.json';now=int(time.time())
        health.write_text(json.dumps({'version':'external-recorder-health-037-v1','recorder_id':'test-only',
            'measured_at':now,'last_collection_at':now,'healthy':True,'desktop_stable':True}))
        return {'job':str(self.root),'config':{'health_file':str(health),'recorder_id':'test-only','collection_cadence_seconds':60},'tools':{'bwrap':{'resolved':'/usr/bin/bwrap'}}}
    def test_fresh_health_and_stale_unchanged_collection(self):
        plan=self.plan();self.assertTrue(b.health(plan)['healthy'])
        path=Path(plan['config']['health_file']);data=json.loads(path.read_text());data['last_collection_at']-=500;path.write_text(json.dumps(data))
        with self.assertRaisesRegex(ValueError,'STALE'):b.health(plan)
    def test_health_wrong_identity_and_instability(self):
        plan=self.plan();path=Path(plan['config']['health_file']);data=json.loads(path.read_text());data['desktop_stable']=False;path.write_text(json.dumps(data))
        with self.assertRaisesRegex(ValueError,'STABILITY'):b.health(plan)
        data['desktop_stable']=True;data['recorder_id']='other';path.write_text(json.dumps(data))
        with self.assertRaisesRegex(ValueError,'IDENTITY'):b.health(plan)
    def test_future_or_invalid_health_time(self):
        plan=self.plan();path=Path(plan['config']['health_file']);data=json.loads(path.read_text())
        for value in (float('nan'),True,int(time.time())+500):
            data['measured_at']=value;path.write_text(json.dumps(data))
            with self.assertRaises(ValueError):b.health(plan)
    def test_sandbox_fixed_no_network_readonly_source_private_writes(self):
        plan=self.plan();argv=b.sandbox(plan,['/usr/bin/true'])
        self.assertIn('--unshare-all',argv);self.assertNotIn('--share-net',argv)
        self.assertIn('--clearenv',argv);self.assertIn('/job/source',argv)
        self.assertNotIn(str(self.root/'health.json'),argv)
        self.assertNotIn('--ro-bind-try',argv)
    def test_unused_flags_download_and_stale_ui_refused(self):
        for output in (b'Manually-specified variables were not used by the project',b'Downloading file',b'Performing download step',b'UI: provisioning failed; embedding stale assets'):
            with self.assertRaises(ValueError):b.warnings_check(output)
        b.warnings_check(b'UI: no assets available - building without an embedded UI.')
    def test_exact_cache_flags_required(self):
        (self.root/'build').mkdir();cache=self.root/'build/CMakeCache.txt'
        cache.write_text('\n'.join(k+':STRING='+v for k,v in r.FLAGS.items()));b.cache_check(self.root)
        cache.write_text('GGML_NATIVE:BOOL=ON')
        with self.assertRaisesRegex(ValueError,'CACHE_FLAG'):b.cache_check(self.root)
    def test_system_unreviewed_and_outside_paths_refused(self):
        with self.assertRaisesRegex(ValueError,'SYSTEM_REVIEW'):b.validate_system({})
        entry={'name':'libfake.so','path':str(self.root/'foreign'),'sha256':'0'*64,'version':'test','license':'original','license_ref':'synthetic'}
        with self.assertRaisesRegex(ValueError,'ROOT'):b.validate_system({'version':'reviewed-system-037-v1','review_ref':'test','entries':[entry]})
    def test_runtime_explicit_system_resolution_no_host_fallback(self):
        spec=importlib.util.spec_from_file_location('fixture036',Path(__file__).with_name('test_portable_runtime_036.py'));mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
        case=mod.PortableTests();case.setUp()
        try:
            root,manifest=case.stage()
            # Existing inert CLI needs private fake library and a declared system loader.
            loader={'name':'ld-inert.so','path':str(Path('/lib/ld-inert.so').resolve()),'sha256':'0'*64,'version':'SYNTHETIC','license':'original','license_ref':'test'}
            with patch.object(b,'validate_system',return_value={'ld-inert.so':loader}):
                result=b.verify_runtime(root,{})
                self.assertEqual(result['runtime_execution'],'HOLD')
                (root/'lib/libfake.so.1').unlink();(root/'lib/libfake.so.1.0').unlink()
                with self.assertRaisesRegex(ValueError,'NO_SYSTEM_FALLBACK'):b.verify_runtime(root,{})
        finally:case.doCleanups()
    def test_cgroup_required_no_disabled_success(self):
        with self.assertRaisesRegex(ValueError,'PRIVATE_CGROUP'):
            with b.BuildCgroup(None):pass


class OneShotTests(unittest.TestCase):
    """Exercise real supervisor through build orchestration with injected inert compiler.

    Source/configuration controls and cgroup filesystem are injected, not certified.
    """
    def setUp(self):
        old=os.umask(0o077);self.addCleanup(os.umask,old)
        self.temp=tempfile.TemporaryDirectory(dir=Path(__file__).parent);self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name).resolve()
        for name in ('build','stage','source','home','tmp','evidence'):(self.root/name).mkdir(mode=0o700)
        health=self.root/'external-health.json';now=int(time.time())
        health.write_text(json.dumps({'version':'external-recorder-health-037-v1','recorder_id':'inert','measured_at':now,
            'last_collection_at':now,'healthy':True,'desktop_stable':True}))
        self.tools={'python':{'resolved':sys.executable}}
        self.plan={'job':str(self.root),'commands':[['synthetic-configure'],['synthetic-compiler']],
                   'tools':self.tools,'config':{'cgroup_parent':str(self.root),
                   'health_file':str(health),'recorder_id':'inert','collection_cadence_seconds':60},'system_libraries':{}}
        self.q={'qualified':True,'plan_sha256':r.digest(self.plan),'measured_at':now,'measured_monotonic':time.monotonic()}
        (self.root/'qualification.json').write_text(json.dumps(self.q))
        self.approval={'version':'owner-build-037-v1','plan_sha256':r.digest(self.plan),'qualification_sha256':r.digest(self.q),
                       'owner_review_ref':'SYNTHETIC_NOT_OWNER_APPROVAL','expires_at':now+60,'one_attempt':True,'inference':'HOLD'}
        class FakeGroup:
            start_cpu=0
            def __init__(self,parent):pass
            def __enter__(self):return self
            def __exit__(self,*args):pass
            def attach(self,pid):pass
            def cpu_seconds(self):return 0
            def kill(self):pass
            def empty(self):return True
        self.addCleanup(patch.stopall)
        patch.object(b,'BuildCgroup',FakeGroup).start()
        patch.object(b,'revalidate',lambda plan:None).start()
        patch.object(b,'tools_inventory',return_value=self.tools).start()
        patch.object(b,'stage',return_value={'label':'SYNTHETIC_STAGE_NOT_REAL_ELF','runtime_execution':'HOLD'}).start()
        def sandbox(plan,argv):
            if argv[0]=='synthetic-configure':
                cache='\n'.join(k+':STRING='+v for k,v in r.FLAGS.items())
                code="from pathlib import Path;Path("+repr(str(self.root/'build/CMakeCache.txt'))+").write_text("+repr(cache)+");print('synthetic configure')"
            else:code="print('synthetic compiler substitute; no compilation')"
            return [sys.executable,'-I','-S','-B','-c',code]
        patch.object(b,'sandbox',side_effect=sandbox).start()
    def test_one_successful_harmless_attempt_then_reuse_refused(self):
        result=b.execute(self.plan,self.approval)
        self.assertEqual(result['operation'],'LOCAL_BUILD_PASS_INFERENCE_HOLD')
        self.assertTrue(all(s['direct_child_reaped'] for s in result['steps']))
        with self.assertRaisesRegex(ValueError,'ONE_SHOT'):b.execute(self.plan,self.approval)
    def test_expired_wrong_plan_or_inference_approval_no_attempt(self):
        for field,value in (('expires_at',0),('plan_sha256','0'*64),('qualification_sha256','0'*64),('inference','GO'),('one_attempt',False)):
            approval=dict(self.approval,**{field:value})
            with self.subTest(field=field),self.assertRaisesRegex(ValueError,'APPROVAL_SCOPE'):b.execute(self.plan,approval)
        self.assertFalse((self.root/'attempt.json').exists())
    def test_failed_compiler_spends_attempt_and_preserves_evidence(self):
        with patch.object(b,'sandbox',return_value=[sys.executable,'-c','raise SystemExit(7)']):result=b.execute(self.plan,self.approval)
        self.assertEqual(result['operation'],'BUILD_FAILED');self.assertTrue((self.root/'evidence/configure.log').exists())
        self.assertTrue((self.root/'result.json').exists());self.assertTrue((self.root/'attempt.json').exists())
        with self.assertRaisesRegex(ValueError,'ONE_SHOT'):b.execute(self.plan,self.approval)
    def test_stop_marker_refuses_before_attempt(self):
        (self.root/'STOP').touch()
        with self.assertRaisesRegex(ValueError,'ONE_SHOT_OR_STOP'):b.execute(self.plan,self.approval)
        self.assertFalse((self.root/'attempt.json').exists())
    def test_concurrent_executor_refused(self):
        with b.single_executor(self.plan['config']['cgroup_parent']):
            with self.assertRaisesRegex(ValueError,'BUSY'):b.execute(self.plan,self.approval)

class MonitorTests(unittest.TestCase):
    def setUp(self):
        old=os.umask(0o077);self.addCleanup(os.umask,old)
        self.temp=tempfile.TemporaryDirectory(dir=Path(__file__).parent);self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name).resolve()
    def test_monitor_preserves_real_status_timestamps_and_original(self):
        source=self.root/'external-status.json';now=int(time.time())
        original=json.dumps({'measured_at':now-400,'collection':now-400,'healthy':True,'stable':True})
        source.write_text(original);dest=self.root/'health.json'
        b.monitor(source,dest,'inert','collection','healthy','stable',seconds=1)
        self.assertEqual(source.read_text(),original)
        self.assertEqual(json.loads(dest.read_text())['measured_at'],now-400)
        plan={'config':{'health_file':str(dest),'recorder_id':'inert','collection_cadence_seconds':60}}
        with self.assertRaisesRegex(ValueError,'STALE'):b.health(plan)
    def test_monitor_does_not_invent_healthy_or_stable_status(self):
        source=self.root/'external-status.json';source.write_text(json.dumps({'measured_at':int(time.time()),'collection':int(time.time())}))
        with self.assertRaisesRegex(ValueError,'SCHEMA'):b.monitor(source,self.root/'health.json','inert','collection','healthy','stable',seconds=1)
        self.assertFalse((self.root/'health.json').exists())
    def test_monitor_refuses_overwriting_foreign_health(self):
        source=self.root/'status.json';source.write_text('{}');dest=self.root/'health.json';dest.write_text('foreign')
        with self.assertRaisesRegex(ValueError,'NEW_HEALTH'):b.monitor(source,dest,'inert','collection','healthy','stable',seconds=1)
        self.assertEqual(dest.read_text(),'foreign')
    def test_runtime_contract_contains_only_explicit_file_mounts(self):
        loader={'name':'ld-inert.so','path':str(Path('/lib/ld-inert.so').resolve())}
        with patch.object(b,'validate_system',return_value={'ld-inert.so':loader}):
            mounts=b.runtime_mounts({},'/lib/ld-inert.so')
        self.assertTrue(all(m['mode']=='ro-file' for m in mounts))
        self.assertFalse(any(m['source']=='/usr' for m in mounts))
        self.assertTrue(any(m['destination']=='/lib/ld-inert.so' for m in mounts))


class ExportTests(unittest.TestCase):
    def setUp(self):
        spec=importlib.util.spec_from_file_location('fixture036',Path(__file__).with_name('test_portable_runtime_036.py'))
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        self.case=module.PortableTests();self.case.setUp();self.addCleanup(self.case.doCleanups)
        self.root=self.case.root
        (self.case.source/'LICENSE').chmod(0o660);self.case.source.chmod(0o770)
        toolchain=self.root/'toolchain.json';toolchain.write_text(json.dumps({'packages':{'inert':'0'},'licenses':{'inert':'original'},'review_ref':'SYNTHETIC'}))
        system=self.root/'system.json';system.write_text('{}')
        self.config={'source':str(self.case.source),'job':str(self.root/'new-job'),
            'protected_roots':[str(self.case.source),str(self.root/'original-runtime'),str(self.root/'recorder')],
            'cgroup_parent':str(self.root),'health_file':str(self.root/'health.json'),'recorder_id':'inert',
            'collection_cadence_seconds':60,'toolchain_evidence':str(toolchain),'system_libraries':str(system)}
        patch.object(b,'validate_system',return_value={}).start()
        patch.object(b,'tools_inventory',return_value={'synthetic':True}).start()
        patch.object(b,'budget_check',lambda plan:None).start()
    def test_dry_run_no_export_then_private_readonly_export_and_owned_rollback(self):
        (self.case.source/'untracked-script').write_text('MUST NOT EXECUTE OR EXPORT')
        result=b.prepare(self.config);self.assertEqual(result['operation'],'DRY_RUN_NO_WRITES')
        self.assertFalse(Path(self.config['job']).exists())
        result=b.prepare(self.config,apply=True);job=Path(self.config['job'])
        self.assertEqual((job/'source/LICENSE').stat().st_mode&0o777,0o400)
        self.assertEqual((self.case.source/'LICENSE').stat().st_mode&0o777,0o660)
        self.assertFalse((job/'source/.git').exists());self.assertFalse((job/'source/untracked-script').exists())
        self.assertNotEqual((job/'source/LICENSE').stat().st_ino,(self.case.source/'LICENSE').stat().st_ino)
        b.prep.rollback(str(job),result['rollback_receipt_sha256'],apply=True)
        self.assertFalse(job.exists());self.assertTrue(self.case.source.exists())
    def test_concurrent_source_change_refuses_export_commit(self):
        manifest=b.source_inventory(self.case.source);changed=copy.deepcopy(manifest);changed['bytes']+=1
        with patch.object(b,'source_inventory',side_effect=[manifest,changed]):
            with self.assertRaisesRegex(ValueError,'CONCURRENT_SOURCE_CHANGE'):b.prepare(self.config,apply=True)
        self.assertFalse((Path(self.config['job'])/'plan.json').exists())
    def test_protected_job_or_original_source_under_toolchain_refused(self):
        config=dict(self.config,job=str(self.case.source/'new-job'))
        with self.assertRaisesRegex(ValueError,'PROTECTED_JOB_OVERLAP|UNSAFE_OWNER_OR_PERMISSIONS'):b.prepare(config)
        config=dict(self.config,protected_roots=['/usr/private-aep'])
        with self.assertRaisesRegex(ValueError,'TOOLCHAIN_MOUNT'):b.prepare(config)


class CleanupFailureTests(unittest.TestCase):
    setUp=OneShotTests.setUp
    def test_failed_scope_cleanup_cannot_report_success(self):
        class BadExit:
            start_cpu=0
            def __init__(self,parent):pass
            def __enter__(self):return self
            def attach(self,pid):pass
            def cpu_seconds(self):return 0
            def kill(self):pass
            def empty(self):return True
            def __exit__(self,*args):raise ValueError('SCOPE_CLEANUP_UNVERIFIED')
        with patch.object(b,'BuildCgroup',BadExit):result=b.execute(self.plan,self.approval)
        self.assertEqual(result['operation'],'BUILD_FAILED');self.assertEqual(result['blocker'],'SCOPE_CLEANUP_UNVERIFIED')


class AliasTests(unittest.TestCase):
    def test_debian_alternatives_are_reconstructed_from_pinned_targets_only(self):
        plan={'tools':{'cc':{'path':'/usr/bin/cc','resolved':'/usr/bin/PINNED-INERT-COMPILER'}}}
        readlink=os.readlink
        def links(path):
            if str(path)=='/usr/bin/cc':return '/etc/alternatives/cc'
            return readlink(path)
        with patch.object(b.os,'readlink',side_effect=links):
            aliases=b.compiler_aliases(plan)
        self.assertEqual(aliases,[('/usr/bin/PINNED-INERT-COMPILER','/etc/alternatives/cc')])


class LoaderTagTests(unittest.TestCase):
    def test_extra_loader_audit_dependencies_refused(self):
        spec=importlib.util.spec_from_file_location('fixture036',Path(__file__).with_name('test_portable_runtime_036.py'))
        mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
        old=os.umask(0o077)
        try:
            with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as directory:
                path=Path(directory)/'inert.so'
                for tag in (0x6ffffefb,0x6ffffefc,0x7ffffffd,0x7fffffff):
                    data=bytearray(mod.inert(needed=('unreviewed.so',)))
                    __import__('struct').pack_into('<q',data,512,tag);path.write_bytes(data)
                    with self.subTest(tag=tag),self.assertRaisesRegex(ValueError,'AUDIT_FILTER'):
                        b.passive_elf(path,hashlib.sha256(data).hexdigest())
        finally:os.umask(old)


if __name__=='__main__':unittest.main()
