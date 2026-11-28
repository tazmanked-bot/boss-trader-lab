"""Inert status/systemd fixtures; genuine Linux reads are reported separately."""
import copy
import datetime as dt
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import threading
import time
import unittest
from unittest.mock import patch
from research import recorder_health_037 as r, controlled_build_037 as b, memory_headroom_037 as m

NOW=1795867200
MONO=10000.0


def iso(value):return dt.datetime.fromtimestamp(value,dt.timezone.utc).isoformat().replace('+00:00','Z')


def fixtures():
    status={'mode':'LIVE_PUBLIC_DATA','health':'RECENT_COLLECTION','generatedAt':iso(NOW-10),
            'lastAttemptAt':iso(NOW-13),'lastSuccessAt':iso(NOW-11),'pausedReason':None,'orderAuthority':'NONE'}
    timer={'Id':r.TIMER,'LoadState':'loaded','ActiveState':'active','SubState':'waiting','Result':'success'}
    service={'Id':r.SERVICE,'LoadState':'loaded','Type':'oneshot','Result':'success','ExecMainStatus':'0',
             'ActiveState':'inactive','SubState':'dead','ExecMainStartTimestampMonotonic':str(int((MONO-13)*1e6))}
    return status,timer,service


def evidence():
    return {'version':'external-recorder-health-037-v1','recorder_id':'inert','collection_cadence_seconds':900,
            'measured_at':NOW,'last_collection_at':NOW-11,'healthy':True,'desktop_stable':False,
            'host_stability':'HOLD_PHYSICAL_HOST_NOT_OBSERVED',
            'observer':{'kind':r.KIND,'live':True,'pid':os.getpid(),'start_ticks':r.process_identity(os.getpid()),
                        'boot_id':r.boot_id(),'heartbeat_monotonic':MONO,'code_sha256':r.p.hash_file(Path(r.__file__))[0]}}


class MeasurementTests(unittest.TestCase):
    def test_actual_schema_and_idle_success_not_service_failure(self):
        value=r.evaluate(*fixtures(),now=NOW,monotonic=MONO)
        self.assertEqual(value['service_phase'],'IDLE_SUCCESS_BETWEEN_COLLECTIONS')
        self.assertEqual(value['last_collection_at'],NOW-11)
        self.assertEqual(value['last_success_at'],fixtures()[0]['lastSuccessAt'])
        self.assertEqual(value['cadence_seconds'],900)
    def test_bounded_oneshot_start_and_start_post(self):
        for state in ('start','start-post'):
            status,timer,service=fixtures();status['lastAttemptAt']=iso(NOW-1);status['generatedAt']=iso(NOW)
            service.update(ActiveState='activating',SubState=state)
            timer['SubState']='running'
            with self.subTest(state=state):self.assertEqual(r.evaluate(status,timer,service,now=NOW,monotonic=MONO)['service_phase'],'BOUNDED_ONESHOT_RUNNING')
    def test_unfinished_attempt_while_idle_rejected(self):
        s,t,v=fixtures();s['lastAttemptAt']=iso(NOW-1);s['generatedAt']=iso(NOW)
        with self.assertRaisesRegex(ValueError,'UNFINISHED'):r.evaluate(s,t,v,now=NOW,monotonic=MONO)
    def test_service_overrun_or_missing_monotonic_start_rejected(self):
        for start in ('0','',str(int((MONO-901)*1e6)),str(int((MONO+1)*1e6))):
            s,t,v=fixtures();v.update(ActiveState='activating',SubState='start',ExecMainStartTimestampMonotonic=start)
            with self.subTest(start=start),self.assertRaises(ValueError):r.evaluate(s,t,v,now=NOW,monotonic=MONO)
    def test_stale_success_never_replaced_with_poll_time(self):
        s,t,v=fixtures();s.update(lastSuccessAt=iso(NOW-1831),lastAttemptAt=iso(NOW-1832),generatedAt=iso(NOW))
        with self.assertRaisesRegex(ValueError,'STALE'):r.evaluate(s,t,v,now=NOW,monotonic=MONO)
    def test_freshness_exact_boundary(self):
        s,t,v=fixtures();s.update(lastSuccessAt=iso(NOW-1830),lastAttemptAt=iso(NOW-1831),generatedAt=iso(NOW-1829))
        self.assertEqual(r.evaluate(s,t,v,now=NOW,monotonic=MONO)['last_collection_at'],NOW-1830)
    def test_future_inconsistent_naive_and_non_utc_timestamps(self):
        for key,value in (('lastSuccessAt',iso(NOW+1)),('generatedAt',iso(NOW-20)),('generatedAt','2026-11-28T12:00:00'),('generatedAt','2026-11-28T12:00:00+01:00'),('lastAttemptAt',True)):
            s,t,v=fixtures();s[key]=value
            with self.subTest(key=key,value=value),self.assertRaises(ValueError):r.evaluate(s,t,v,now=NOW,monotonic=MONO)
    def test_failure_pause_source_and_order_authority_rejected(self):
        for key,value in (('health','FAILED'),('pausedReason','timeout'),('mode','SYNTHETIC'),('orderAuthority','BUY')):
            s,t,v=fixtures();s[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):r.evaluate(s,t,v,now=NOW,monotonic=MONO)
    def test_timer_and_service_failures_and_wrong_unit_rejected(self):
        for unit,key,value in (('timer','ActiveState','inactive'),('timer','Result','failed'),('timer','Id','other.timer'),('service','Result','exit-code'),('service','ExecMainStatus','1'),('service','ActiveState','failed'),('service','LoadState','not-found')):
            s,t,v=fixtures();(t if unit=='timer' else v)[key]=value
            with self.subTest(unit=unit,key=key),self.assertRaises(ValueError):r.evaluate(s,t,v,now=NOW,monotonic=MONO)
    def test_collection_measures_independently_and_detects_status_race(self):
        s,t,v=fixtures();data=copy.deepcopy(s)
        def query(unit):return t if unit==r.TIMER else v
        result=r.collect('/inert',reader=lambda path:(data,'same-sha'),query=query,wall=lambda:NOW,mono=lambda:MONO)
        self.assertEqual(result['measured_at'],NOW);self.assertEqual(result['last_collection_at'],NOW-11);self.assertEqual(s,data)
        with self.assertRaisesRegex(ValueError,'CHANGED'),patch.object(r,'status_read'):
            values=iter(((s,'a'),(s,'b'),(s,'c'),(s,'d')))
            r.collect('/inert',reader=lambda path:next(values),query=query,wall=lambda:NOW,mono=lambda:MONO)
    def test_normal_atomic_update_gets_one_bounded_remeasurement(self):
        s,t,v=fixtures();values=iter(((s,'old'),(s,'new'),(s,'new'),(s,'new')));queries=[]
        def query(unit):queries.append(unit);return t if unit==r.TIMER else v
        result=r.collect('/inert',reader=lambda path:next(values),query=query,wall=lambda:NOW,mono=lambda:MONO)
        self.assertEqual(result['status_sha256'],'new');self.assertEqual(len(queries),4)
    def test_slow_changed_snapshot_never_retries_without_budget(self):
        s,t,v=fixtures();values=iter(((s,'a'),(s,'b')));ticks=iter((0,2));queries=[]
        def query(unit):queries.append(unit);return t if unit==r.TIMER else v
        with self.assertRaisesRegex(ValueError,'CHANGED'):
            r.collect('/inert',reader=lambda p:next(values),query=query,wall=lambda:NOW,mono=lambda:next(ticks))
        self.assertEqual(len(queries),2)
    def test_observation_wall_budget(self):
        s,t,v=fixtures();ticks=iter((0,6))
        with self.assertRaisesRegex(ValueError,'BUDGET'):r.collect('/inert',reader=lambda path:(s,'a'),query=lambda unit:t if unit==r.TIMER else v,wall=lambda:NOW,mono=lambda:next(ticks))
    def test_duplicate_and_nonfinite_status_json_rejected(self):
        for raw in ('{"mode":"LIVE_PUBLIC_DATA","mode":"x"}','{"x":NaN}','[]'):
            with self.subTest(raw=raw),self.assertRaises(ValueError):r.strict_json(raw)
    def test_systemctl_fixed_readonly_argv_and_timeout(self):
        raw=('Id='+r.TIMER+'\nLoadState=loaded\nActiveState=active\nSubState=waiting\n').encode()
        # Filesystem trust is injected; no actual systemctl/D-Bus request here.
        with patch.object(r.p,'secure'),patch.object(Path,'resolve',return_value=Path('/usr/bin/systemctl')),patch.object(Path,'stat',return_value=type('S',(),{'st_uid':os.getuid()})()),patch.object(r.process,'run',return_value=(raw,{'stderr_bytes':0})) as run:
            r.systemd_show(r.TIMER)
        args=run.call_args.args[0];self.assertIn('show',args);self.assertNotIn('start',args)
        self.assertEqual(run.call_args.kwargs['timeout'],2);self.assertEqual(run.call_args.kwargs['cap'],4096)
        with self.assertRaisesRegex(ValueError,'FIXED_UNIT'):r.systemd_show('other.service')
    def test_systemctl_failure_is_not_healthy(self):
        with patch.object(r.process,'run',side_effect=ValueError('PROCESS_TIMEOUT')):
            # collect exercises the failure contract without requiring a user bus.
            s,t,v=fixtures()
            with self.assertRaisesRegex(ValueError,'PROCESS_TIMEOUT'):
                r.collect('/inert',reader=lambda p:(s,'a'),query=lambda unit:r.process.run(),wall=lambda:NOW,mono=lambda:MONO)


class ConsumerTests(unittest.TestCase):
    def test_live_fresh_recorder_evidence_does_not_clear_host_hold(self):
        result=r.validate_evidence(evidence(),'inert',900,now=NOW,monotonic=MONO)
        self.assertEqual(result['recorder'],'MEASURED_HEALTHY');self.assertEqual(result['physical_host'],'HOLD')
    def test_stale_or_missing_observer_rejected(self):
        for changes in ({'live':False},{'heartbeat_monotonic':MONO-16},{'boot_id':'different'},{'pid':99999999},{'start_ticks':'wrong'},{'code_sha256':'0'*64}):
            value=evidence();value['observer'].update(changes)
            with self.subTest(changes=changes),self.assertRaises(ValueError):r.validate_evidence(value,'inert',900,now=NOW,monotonic=MONO)
    def test_pid_loss_rejected_even_with_fresh_timestamp(self):
        with patch.object(r,'process_identity',side_effect=FileNotFoundError):
            with self.assertRaisesRegex(ValueError,'LOST'):r.validate_evidence(evidence_before_loss(),'inert',900,now=NOW,monotonic=MONO)
    def test_old_measurement_wrong_cadence_or_false_host_claim_rejected(self):
        for key,value in (('measured_at',NOW-16),('collection_cadence_seconds',60),('desktop_stable',True),('healthy',False),('last_collection_at',NOW-1831)):
            record=evidence();record[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):r.validate_evidence(record,'inert',900,now=NOW,monotonic=MONO)
    def test_malformed_health_or_observer_metadata_fails_closed(self):
        malformed=[None,[],dict(evidence(),observer=[])]
        nan=evidence();nan['observer']['heartbeat_monotonic']=float('nan');malformed.append(nan)
        for value in malformed:
            with self.subTest(value=type(value).__name__),self.assertRaises(ValueError):
                r.validate_evidence(value,'inert',900,now=NOW,monotonic=MONO)
        with patch.object(b,'read_json',return_value=[]):
            with self.assertRaisesRegex(ValueError,'HEALTH_OBJECT'):
                b.health({'config':{'health_file':'/inert','recorder_id':'inert','collection_cadence_seconds':900}},now=NOW)
    def test_consumer_reports_physical_host_hold(self):
        record=evidence()
        with patch.object(b,'read_json',return_value=record),patch.object(r.time,'monotonic',return_value=MONO):
            with self.assertRaisesRegex(ValueError,'PHYSICAL_HOST_STABILITY_HOLD'):
                b.health({'config':{'health_file':'/inert','recorder_id':'inert','collection_cadence_seconds':900}},now=NOW)


def evidence_before_loss():
    # Supply the identity without querying the process when testing disappearance.
    return {'version':'external-recorder-health-037-v1','recorder_id':'inert','collection_cadence_seconds':900,
            'measured_at':NOW,'last_collection_at':NOW-11,'healthy':True,'desktop_stable':False,
            'host_stability':'HOLD_PHYSICAL_HOST_NOT_OBSERVED','observer':{'kind':r.KIND,'live':True,'pid':123,'start_ticks':'1','boot_id':r.boot_id(),'heartbeat_monotonic':MONO,'code_sha256':r.p.hash_file(Path(r.__file__))[0]}}

class PrivateObserverTests(unittest.TestCase):
    def setUp(self):
        old=os.umask(0o077);self.addCleanup(os.umask,old)
        self.temp=tempfile.TemporaryDirectory(dir=Path(__file__).parent);self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name).resolve();self.root.chmod(0o700)
        self.dest=self.root/'health.json'
        self.config={'health_file':str(self.dest),'recorder_id':'inert','collection_cadence_seconds':900}
    def test_atomic_private_publication_and_status_unchanged(self):
        status=self.root/'status.json';status.write_text(json.dumps(fixtures()[0]));before=status.read_bytes()
        with r.Publisher(self.dest,'inert') as publisher:
            publisher.publish(evidence());self.assertEqual(self.dest.stat().st_mode&0o777,0o600)
            value=evidence();value['measured_at']+=1;publisher.publish(value)
            self.assertEqual(json.loads(self.dest.read_text())['measured_at'],NOW+1)
        self.assertEqual(status.read_bytes(),before);self.assertFalse(list(self.root.glob('.observer-037-*')))
    def test_foreign_existing_output_symlink_or_nonprivate_dir_refused(self):
        self.dest.write_text('foreign')
        with self.assertRaises(ValueError):
            with r.Publisher(self.dest,'inert'):pass
        self.assertEqual(self.dest.read_text(),'foreign');self.dest.unlink();self.dest.symlink_to('/etc/passwd')
        with self.assertRaises(ValueError):
            with r.Publisher(self.dest,'inert',replace_stale=True):pass
        self.dest.unlink();self.root.chmod(0o755)
        with self.assertRaisesRegex(ValueError,'0700'):
            with r.Publisher(self.dest,'inert'):pass
    def test_concurrent_observer_and_live_takeover_refused(self):
        with r.Publisher(self.dest,'inert') as publisher:
            publisher.publish(evidence())
            with self.assertRaisesRegex(ValueError,'ALREADY_RUNNING'):
                with r.Publisher(self.dest,'inert',replace_stale=True):pass
        with self.assertRaisesRegex(ValueError,'STILL_ALIVE'):
            with r.Publisher(self.dest,'inert',replace_stale=True):pass
    def test_explicit_restart_only_after_old_observer_stopped(self):
        value=evidence();value['observer']['live']=False
        with r.Publisher(self.dest,'inert') as publisher:publisher.publish(value)
        with self.assertRaisesRegex(ValueError,'EXISTS'):
            with r.Publisher(self.dest,'inert'):pass
        with r.Publisher(self.dest,'inert',replace_stale=True) as publisher:publisher.publish(evidence())
    def test_output_replacement_refused_without_deleting_foreign_data(self):
        with r.Publisher(self.dest,'inert') as publisher:
            publisher.publish(evidence());foreign=self.root/'foreign';foreign.write_text('owner data');os.replace(foreign,self.dest)
            with self.assertRaisesRegex(ValueError,'REPLACED'):publisher.publish(evidence())
        self.assertEqual(self.dest.read_text(),'owner data')
    def run_fake(self,collector):
        class Clock:
            value=0
            def __call__(self):return self.value
        clock=Clock()
        class Stop:
            def is_set(self):return False
            def wait(self,seconds):clock.value+=seconds
        records=[];actual=r.Publisher.publish
        def capture(publisher,value):records.append(copy.deepcopy(value));actual(publisher,value)
        with patch.object(r.Publisher,'publish',capture):
            result=r.run(self.config,status_path=self.root/'inert-status',seconds=11,collector=collector,stop=Stop(),clock=clock)
        return records,result
    def test_five_second_publication_and_clean_exit_marks_observer_stopped(self):
        value={'last_collection_at':NOW-11,'measured_at':int(time.time())}
        records,result=self.run_fake(lambda path:copy.deepcopy(value))
        self.assertEqual([v['observer']['heartbeat_monotonic'] for v in records],[0,5,10,11])
        self.assertTrue(all(v['last_collection_at']==NOW-11 for v in records))
        self.assertTrue(all(v['desktop_stable'] is False for v in records))
        self.assertTrue(all(v['healthy'] for v in records[:-1]));self.assertFalse(records[-1]['healthy'])
        self.assertFalse(records[-1]['observer']['live']);self.assertEqual(result['physical_host'],'HOLD')
    def test_query_failure_publishes_fresh_unhealthy_without_invented_collection(self):
        def fail(path):raise ValueError('SYSTEMCTL_TIMEOUT')
        records,_=self.run_fake(fail)
        self.assertTrue(all(v['healthy'] is False and v['last_collection_at'] is None for v in records))
        self.assertEqual(records[0]['recorder_reason'],'SYSTEMCTL_TIMEOUT')
    def test_collection_timestamp_regression_stops_health(self):
        values=iter((NOW-10,NOW-20,NOW-20))
        records,_=self.run_fake(lambda path:{'measured_at':int(time.time()),'last_collection_at':next(values)})
        self.assertTrue(records[0]['healthy']);self.assertFalse(records[1]['healthy'])
        self.assertEqual(records[1]['last_collection_at'],NOW-10)
    def test_config_wrong_cadence_or_status_output_overlap_refused(self):
        wrong=dict(self.config,collection_cadence_seconds=60)
        with self.assertRaisesRegex(ValueError,'900_REQUIRED'):r.run(wrong,seconds=1)
        with self.assertRaisesRegex(ValueError,'OVERLAP'):r.run(self.config,status_path=self.dest,seconds=1)
    def test_status_reader_does_not_modify_actual_fixture_file(self):
        status=self.root/'status.json';status.write_text(json.dumps(fixtures()[0]));before=status.read_bytes()
        value,sha=r.status_read(status)
        self.assertEqual(value,fixtures()[0]);self.assertEqual(sha,hashlib.sha256(before).hexdigest());self.assertEqual(status.read_bytes(),before)
        status.write_bytes(b'x'*65537)
        with self.assertRaisesRegex(ValueError,'SIZE_LIMIT'):r.status_read(status)


class RootCompatibilityTests(unittest.TestCase):
    def hierarchy(self):
        spec=importlib.util.spec_from_file_location('memory_fixtures',Path(__file__).with_name('test_memory_headroom_037.py'))
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        h=module.Hierarchy(process='/user.slice/user-1000.slice/session-3.scope')
        h.files['/proc/meminfo']='MemAvailable: 5681856 kB\n'
        h.files.pop('/sys/fs/cgroup/cgroup.type')
        h.node('/user.slice/user-1000.slice',current=79650816)
        h.node('/user.slice/user-1000.slice/session-3.scope')
        h.node('/user.slice/user-1000.slice/user@1000.service',current=79650816)
        # Remove earlier generic fixture leaves so the reported scope has exactly four nonroot nodes.
        return h
    def test_exact_debian_four_nodes_missing_root_type(self):
        h=self.hierarchy();value=h.snapshot('/sys/fs/cgroup/user.slice/user-1000.slice/user@1000.service')
        self.assertEqual(value['status'],'PASS');self.assertEqual(value['available_bytes'],5818220544)
        self.assertEqual(len(value['limits']),5)
        self.assertEqual(value['limits'][-1]['type'],'ABSENT_AT_VERIFIED_HIERARCHY_ROOT')
    def test_missing_nonroot_type_is_still_hold(self):
        h=self.hierarchy();h.files.pop('/sys/fs/cgroup/user.slice/cgroup.type')
        self.assertEqual(h.snapshot('/sys/fs/cgroup/user.slice/user-1000.slice/user@1000.service')['status'],'HOLD')
    def test_unreadable_or_malformed_root_type_is_not_absence(self):
        for value in (PermissionError('denied'),'garbage',''):
            h=self.hierarchy();h.files['/sys/fs/cgroup/cgroup.type']=value
            with self.subTest(value=value):self.assertEqual(h.snapshot('/sys/fs/cgroup/user.slice/user-1000.slice/user@1000.service')['status'],'HOLD')
    def test_ancestor_limit_still_applies_without_root_type(self):
        h=self.hierarchy();h.node('/user.slice',maximum=4*1024**3,current=1024**3)
        value=h.snapshot('/sys/fs/cgroup/user.slice/user-1000.slice/user@1000.service')
        self.assertEqual(value['available_bytes'],3*1024**3)
    def test_root_exception_never_applies_to_partial_or_hidden_limits(self):
        h=self.hierarchy();h.files['/sys/fs/cgroup/memory.max']='max'
        self.assertEqual(h.snapshot('/sys/fs/cgroup/user.slice/user-1000.slice/user@1000.service')['status'],'HOLD')



class LiveObserverFailureTests(unittest.TestCase):
    setUp=PrivateObserverTests.setUp
    def spawn(self):
        import subprocess,sys
        config=self.root/'config.json';config.write_text(json.dumps(self.config))
        child=subprocess.Popen([sys.executable,'-B','-m','research.recorder_health_037','--config',str(config),'--seconds','60'],
            cwd=Path(__file__).resolve().parents[1],env={'PATH':'/usr/bin:/bin','HOME':str(self.root),'LC_ALL':'C'},
            stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True)
        self.addCleanup(self.reap,child)
        deadline=time.monotonic()+4
        while not self.dest.exists() and child.poll() is None and time.monotonic()<deadline:time.sleep(.01)
        self.assertTrue(self.dest.exists(),'observer failed to publish missing-source HOLD')
        return child
    def reap(self,child):
        if child.poll() is None:child.kill()
        child.communicate(timeout=3)
    def test_real_observer_term_publishes_stopped_without_systemd_or_recorder_access(self):
        import signal
        child=self.spawn();first=json.loads(self.dest.read_text());self.assertFalse(first['healthy'])
        self.assertFalse((self.root/'.local/share/boss-s3-recorder/status.json').exists())
        child.send_signal(signal.SIGTERM);out,err=child.communicate(timeout=3)
        self.assertEqual(child.returncode,0,err);final=json.loads(self.dest.read_text())
        self.assertFalse(final['observer']['live']);self.assertFalse(final['desktop_stable']);self.assertEqual(final['recorder_reason'],'OBSERVER_STOPPED')
    def test_real_observer_loss_rejected_even_before_heartbeat_ttl(self):
        child=self.spawn();first=json.loads(self.dest.read_text());child.kill();child.communicate(timeout=3)
        self.assertTrue(first['observer']['live'])
        with self.assertRaisesRegex(ValueError,'OBSERVER_LOST'):
            r.validate_evidence(first,'inert',900)


class ConsolidatedPreflightTests(unittest.TestCase):
    def test_genuine_contract_recorder_pass_and_physical_host_hold_are_separate(self):
        old=os.umask(0o077)
        try:
            with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as directory:
                root=Path(directory).resolve();health=root/'health.json';health.write_text(json.dumps(evidence()))
                tools=root/'tools.json';tools.write_text(json.dumps({'packages':{'inert':'0'},'licenses':{'inert':'original'},'review_ref':'SYNTHETIC'}))
                system=root/'system.json';system.write_text('{}')
                config={'source':'/inert-source','job':str(root/'new'),'protected_roots':['/inert-recorder'],
                    'health_file':str(health),'recorder_id':'inert','collection_cadence_seconds':900,
                    'cgroup_parent':'/sys/fs/cgroup','toolchain_evidence':str(tools),'system_libraries':str(system)}
                before=copy.deepcopy(config)
                with patch.object(b.memory,'snapshot',return_value={'status':'PASS','available_bytes':5818220544}),patch.object(b.prep,'compatibility',return_value={'fixture':True}),patch.object(b,'tools_inventory',return_value={'fixture':True}),patch.object(b,'validate_system',return_value={}),patch.object(r.time,'time',return_value=NOW),patch.object(r.time,'monotonic',return_value=MONO):
                    report=b.preflight(config)
                self.assertEqual(report['checks']['recorder_observation']['status'],'PASS')
                self.assertEqual(report['checks']['recorder_health']['status'],'HOLD')
                self.assertEqual(report['checks']['recorder_health']['reason'],'PHYSICAL_HOST_STABILITY_HOLD')
                self.assertEqual(config,before);self.assertEqual(report['writes'],0);self.assertFalse(report['qualified'])
        finally:os.umask(old)


if __name__=='__main__':unittest.main()
