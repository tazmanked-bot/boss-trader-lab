"""Original synthetic artifacts/SQLite and pinned workers. No owner target or AI."""
import copy
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest
from unittest.mock import patch
from research import owner_tools_035 as tools,recorder_snapshot_034 as db,llama_analyst_033 as a,decision_loop_032 as loop
from research.qualification_035 import provision as p,synthetic,executor,containment,process


class ProvisionTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(dir=Path(__file__).parent);self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name).resolve();self.config=synthetic.bundle(self.root)
    def test_dry_run_no_writes_and_elf_closure(self):
        before={str(f.relative_to(self.root)):f.lstat().st_mode for f in self.root.rglob('*')}
        result=p.provision(self.config);self.assertEqual(result['writes'],0)
        self.assertEqual(result['elf_dependencies']['bin/runtime']['needed'],['libfake.so.1'])
        self.assertEqual(before,{str(f.relative_to(self.root)):f.lstat().st_mode for f in self.root.rglob('*')})
    def test_apply_symlinks_modes_digest_and_own_rollback(self):
        original=Path(self.config['entries'][0]['source']).read_bytes()
        result=p.provision(self.config,apply=True);pin=hashlib.sha256(loop.canonical(result).encode()).hexdigest();dest=Path(self.config['destination'])
        self.assertEqual(os.readlink(dest/'lib/libfake.so'),'libfake.so.1')
        self.assertEqual((dest/'bin/runtime').stat().st_mode&0o777,0o500)
        self.assertEqual(dest.stat().st_mode&0o777,0o700);p.verify_bundle(self.config,pin)
        self.assertEqual(p.rollback(self.config,pin)['operation'],'ROLLED_BACK_OWN_BUNDLE')
        self.assertFalse(dest.exists());self.assertEqual(Path(self.config['entries'][0]['source']).read_bytes(),original)
    def test_existing_destination_and_protected_roots_refused(self):
        dest=Path(self.config['destination']);dest.mkdir();(dest/'owner-data').write_text('preserve')
        with self.assertRaises(ValueError):p.provision(self.config,apply=True)
        self.assertEqual((dest/'owner-data').read_text(),'preserve')
        self.config['destination']=str(Path(self.config['protected_roots'][0])/'inside')
        with self.assertRaises(ValueError):p.provision(self.config)
    def test_reported_hashes_are_not_independent_expectations(self):
        self.config['entries'][0]['expectation']='REPORTED_ONLY'
        with self.assertRaisesRegex(ValueError,'INDEPENDENT'):p.provision(self.config)
    def test_digest_dependency_and_unlisted_dynamic_library_refusals(self):
        original=copy.deepcopy(self.config);self.config['entries'][0]['sha256']='0'*64
        with self.assertRaisesRegex(ValueError,'HASH'):p.provision(self.config)
        self.config=copy.deepcopy(original);self.config['entries']=[e for e in self.config['entries'] if e['role']!='library'];self.config['dynamic_source_dirs']=[]
        with self.assertRaisesRegex(ValueError,'DEPENDENCY'):p.provision(self.config)
        self.config=original;Path(self.config['dynamic_source_dirs'][0],'unlisted.so').write_bytes(b'NOT APPROVED')
        with self.assertRaisesRegex(ValueError,'DYNAMIC_LIBRARY'):p.provision(self.config)
    def test_escaping_links_permissions_acl_and_owner_refuse(self):
        alias=Path(self.config['entries'][2]['source']);alias.unlink();alias.symlink_to('/etc/passwd')
        with self.assertRaisesRegex(ValueError,'ABSOLUTE_LINK'):p.provision(self.config)
        alias.unlink();alias.symlink_to('libfake.so.1.0')
        with patch.object(p.os,'listxattr',return_value=['system.posix_acl_access']):
            with self.assertRaisesRegex(ValueError,'ACL'):p.provision(self.config)
        self.root.chmod(0o777)
        with self.assertRaisesRegex(ValueError,'PERMISSIONS'):p.provision(self.config)
        self.root.chmod(0o700)
        with patch.object(p.os,'getuid',return_value=123456):
            with self.assertRaisesRegex(ValueError,'OWNER'):p.provision(self.config)
    def test_exclusive_commit_race_never_replaces_foreign_destination(self):
        dest=Path(self.config['destination'])
        def race(*args):dest.mkdir();(dest/'foreign').write_text('owner');raise a.Refused('RACE')
        with patch.object(p,'_rename_new',side_effect=race):
            with self.assertRaises(ValueError):p.provision(self.config,apply=True)
        self.assertEqual((dest/'foreign').read_text(),'owner');self.assertFalse(list(self.root.glob('.boss-035-stage-*')))
    def test_rollback_foreign_or_modified_files_preserves_all(self):
        result=p.provision(self.config,apply=True);pin=hashlib.sha256(loop.canonical(result).encode()).hexdigest();dest=Path(self.config['destination'])
        (dest/'foreign').write_text('owner')
        with self.assertRaisesRegex(ValueError,'FOREIGN'):p.rollback(self.config,pin)
        self.assertEqual((dest/'foreign').read_text(),'owner');(dest/'foreign').unlink()
        with self.assertRaisesRegex(ValueError,'RECEIPT'):p.rollback(self.config,'0'*64)
        file=dest/'models/model.gguf';file.chmod(0o600);file.write_bytes(b'changed')
        with self.assertRaises(ValueError):p.rollback(self.config,pin)
        self.assertTrue(dest.exists())
    def test_failure_cleans_only_owned_staging(self):
        with patch.object(p,'_rename_new',side_effect=a.Refused('COMMIT_REFUSED')):
            with self.assertRaises(ValueError):p.provision(self.config,apply=True)
        self.assertFalse(list(self.root.glob('.boss-035-stage-*')));self.assertFalse(Path(self.config['destination']).exists())
    def test_foreign_staging_entry_causes_cleanup_hold_not_delete(self):
        def change(stage,*args):
            (stage/'foreign').write_text('preserve');raise a.Refused('COMMIT_REFUSED')
        with patch.object(p,'_rename_new',side_effect=change):
            with self.assertRaisesRegex(ValueError,'CLEANUP_REFUSED'):p.provision(self.config,apply=True)
        stages=list(self.root.glob('.boss-035-stage-*'));self.assertEqual(len(stages),1)
        self.assertEqual((stages[0]/'foreign').read_text(),'preserve')


class SnapshotTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.path=Path(self.temp.name)/'invented.sqlite';self.now=1900000800
    def create(self,rows):
        with sqlite3.connect(self.path) as conn:
            conn.execute('CREATE TABLE events(opened INTEGER, ingested INTEGER, stream TEXT)');conn.executemany('INSERT INTO events VALUES (?,?,?)',rows)
    def inspect(self,interval,cadence=60,**extra):
        return db.freshness(str(self.path),'events','opened','ingested',self.now,snapshot_kind='OWNER_CONSISTENT_OFFLINE_SNAPSHOT',
            stream_column='stream',stream_value='A',expected_interval=interval,collection_cadence=cadence,
            timestamp_semantics='UTC_EPOCH_SECONDS_OPEN_TIME_AND_ACTUAL_INSERT_TIME',**extra)
    def test_both_intervals_fresh_gap_and_exact_stream(self):
        for interval in (900,3600):
            if self.path.exists():self.path.unlink()
            self.create([(self.now-3*interval,self.now-2*interval,'A'),(self.now-interval,self.now,'A'),(self.now-2*interval,self.now-interval,'OTHER')])
            before=self.path.read_bytes();result=self.inspect(interval,cadence=3600)
            self.assertEqual(result['freshness'],'RECENT_RELATIVE_TO_SUPPLIED_AS_OF')
            self.assertEqual(result['historical_candle_gaps'][0]['missing_intervals'],1)
            self.assertEqual(result['collection_cadence_seconds'],3600);self.assertEqual(self.path.read_bytes(),before)
    def test_delayed_data_stale_and_cadence_not_candle_duration(self):
        self.create([(self.now-86400,self.now-5,'A'),(self.now-72000,self.now,'A')])
        for interval in (900,3600):
            result=self.inspect(interval,cadence=60);self.assertEqual(result['freshness'],'STALE')
            self.assertEqual(result['possible_delayed_or_backfilled_rows'],2)
            self.assertEqual(result['observed_recording_gaps'],[])
    def test_alignment_semantics_and_declarations_refuse(self):
        self.create([(self.now-901,self.now,'A')])
        for interval in (900,3600):
            with self.assertRaises(ValueError):self.inspect(interval)
        for interval in (None,True,60,1000):
            with self.assertRaises(ValueError):self.inspect(interval)
        with self.assertRaises(ValueError):db.freshness(str(self.path),'events','opened','ingested',self.now,snapshot_kind='OWNER_CONSISTENT_OFFLINE_SNAPSHOT')
    def test_stored_interval_column_is_checked_and_mixed_duration_refuses(self):
        self.create([(self.now-900,self.now,'A')])
        with sqlite3.connect(self.path) as conn:
            conn.execute('ALTER TABLE events ADD COLUMN duration INTEGER');conn.execute('UPDATE events SET duration=900')
        self.assertEqual(self.inspect(900,interval_column='duration')['stored_interval_validation'],'CHECKED_SECONDS_COLUMN')
        with sqlite3.connect(self.path) as conn:conn.execute('UPDATE events SET duration=3600')
        with self.assertRaisesRegex(ValueError,'STORED_INTERVAL_MISMATCH'):self.inspect(900,interval_column='duration')
    def test_readonly_schema_never_guesses_interval(self):
        self.create([(self.now-900,self.now,'A')]);before=self.path.read_bytes()
        result=tools.snapshot_schema({'snapshot':str(self.path),'snapshot_kind':'OWNER_CONSISTENT_OFFLINE_SNAPSHOT'})
        self.assertEqual(result['writes'],0);self.assertIn('OWNER_MUST_DECLARE',result['interval_semantics']);self.assertEqual(before,self.path.read_bytes())


class ExecutorTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(dir=Path(__file__).parent);self.addCleanup(self.temp.cleanup)
        self.manifest=a.stub_manifest(Path(self.temp.name).resolve());self.request=tools.request_fixture()
        self.plan=executor.plan(self.manifest,self.request);self.receipt=executor.synthetic_receipt(self.plan['binding'])
    def runner(self):return executor.DisabledExecutor(self.plan,self.receipt)
    def test_real_launch_disabled_even_with_positive_receipt_and_env(self):
        self.receipt['qualified']=True
        with patch.dict(os.environ,{'ALLOW_REAL_INFERENCE':'1'}),patch('subprocess.Popen',side_effect=AssertionError('NO_REAL')):
            with self.assertRaisesRegex(ValueError,'NO_ACTIVATION_PATH'):self.runner().infer(self.request,allow_real=True)
    def test_pinned_stub_success_and_bound_evidence(self):
        out=self.runner().stub(self.request['evidence_id'])
        self.assertEqual(out['state'],'REAL_NOT_RUN');self.assertEqual(out['real_inference_count'],0)
        self.assertEqual(out['analysis']['evidence_refs'],[self.request['evidence_id']]);self.assertIsNone(out['model_tokens'])
    def test_changed_qualification_prompt_manifest_schema_ref_bindings_refuse(self):
        for field in self.plan['binding']:
            altered=copy.deepcopy(self.plan);altered['binding'][field]='changed'
            with self.assertRaises(ValueError):executor.DisabledExecutor(altered,self.receipt).stub(self.request['evidence_id'])
        with self.assertRaises(ValueError):self.runner().stub('0'*64)
    def test_timeout_tree_cleanup_overflow_nonzero_and_invalid_json_schema(self):
        for scenario in ('hang','tree','overflow','nonzero','badref','extra'):
            with self.subTest(scenario=scenario):
                with self.assertRaises(ValueError):self.runner().stub(self.request['evidence_id'],scenario,timeout=.25 if scenario in ('hang','tree') else 2)
                self.assertFalse(process.POISONED)
    def test_concurrency_limits_and_worker_digest(self):
        process.LOCK.acquire()
        try:
            with self.assertRaisesRegex(ValueError,'BUSY'):self.runner().stub(self.request['evidence_id'])
        finally:process.LOCK.release()
        with patch.object(containment,'WORKER_SHA','0'*64):
            with self.assertRaises(ValueError):self.runner().stub(self.request['evidence_id'])
    def test_qualification_unavailable_fails_closed_without_install(self):
        state=Path(self.temp.name)/'state';state.mkdir(mode=0o700)
        with patch.object(containment.shutil,'which',return_value=None),patch('subprocess.Popen',side_effect=AssertionError('NO_EXEC')):
            result=containment.qualify(str(state),request_binding=self.plan['binding'],protected_roots=[str(Path(self.temp.name)/'synthetic-protected')])
        self.assertFalse(result['qualified']);self.assertEqual(result['blocker'],'BWRAP_UNAVAILABLE');self.assertEqual(result['state'],'REAL_NOT_RUN')
    def test_shortest_schema_valid_bytes_not_actual_tokens(self):
        result=executor.shortest_response(self.request['evidence_id'])
        self.assertGreater(result['minimum_schema_valid_bytes'],0);self.assertIsNone(result['actual_tokenizer_count'])
        self.assertEqual(result['max_generated_tokens'],64);self.assertTrue(result['likely_truncation_risk'])
    def test_original_deterministic_risk_veto_with_stub_support(self):
        fixture=json.loads((Path(__file__).parent/'fixtures/decision_loop_032.json').read_text());fixture['leads']=fixture['leads'][:1]
        fixture['leads'][0]['payload']['bars'][-1]['volume']=0
        manifest=self.manifest
        class Bridge(loop.MockAnalyst):
            def infer(self,request):
                plan=executor.plan(manifest,request)
                return executor.DisabledExecutor(plan,executor.synthetic_receipt(plan['binding'])).stub(request['evidence_id'])['analysis']
        result=loop.run(fixture,Bridge());self.assertEqual(result['candidate_count'],0)
        self.assertEqual(result['cards'][0]['reason'],'RISK_RULE_VETO');self.assertEqual(result['buy_authorization'],'NONE')


class WorkflowTests(unittest.TestCase):
    def test_consolidated_cli_dry_apply_plan_qualify_and_rollback(self):
        import contextlib,io
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as tmp:
            root=Path(tmp).resolve();provision=synthetic.bundle(root);destination=Path(provision['destination'])
            request_path=root/'request.json';request_path.write_text(loop.canonical(tools.request_fixture()))
            config={'provision':provision,'request_path':str(request_path),
                    'adapter_manifest':{'version':a.VERSION,'runtime_path':str(destination/'bin/runtime'),
                       'runtime_sha256':provision['entries'][0]['sha256'],'model_path':str(destination/'models/model.gguf'),
                       'model_sha256':provision['entries'][-1]['sha256'],'model':a.MODEL,'llama_cpp_commit':'0'*40,'license_review':'OWNER_TARGET_REVIEW_REQUIRED'},
                    'qualification':{'state_directory':str(root/'state'),'cgroup_parent':None}}
            (root/'state').mkdir(mode=0o700);path=root/'owner.json';path.write_text(json.dumps(config));receipt=root/'receipt.json'
            def call(*args):
                with patch.object(sys,'argv',['owner',*args]),contextlib.redirect_stdout(io.StringIO()) as out:tools.main()
                return json.loads(out.getvalue())
            self.assertEqual(call('provision',str(path))['writes'],0)
            applied=call('provision',str(path),'--apply','--receipt-output',str(receipt));self.assertEqual(applied['state'],'REAL_NOT_RUN')
            self.assertEqual(receipt.stat().st_mode&0o777,0o600)
            planned=call('plan',str(path),'--receipt',str(receipt));self.assertEqual(planned['profile']['scope']['max_output_tokens'],64)
            with patch.object(containment.shutil,'which',return_value=None):
                self.assertFalse(call('qualify',str(path),'--receipt',str(receipt))['qualified'])
            self.assertEqual(call('rollback',str(path),'--receipt',str(receipt))['operation'],'ROLLED_BACK_OWN_BUNDLE')
            self.assertTrue(receipt.exists());self.assertFalse(destination.exists())
    def test_complete_synthetic_demo_has_both_intervals_and_no_real_inference(self):
        with patch.object(containment,'qualify',return_value={'qualified':False,'mode':'CONTROLLED_TEST_NOT_TARGET','state':'REAL_NOT_RUN'}):result=tools.demo()
        self.assertEqual(result['real_inference_count'],0)
        self.assertEqual(set(result['synthetic_snapshots']),{'900','3600'})
        for interval,row in result['synthetic_snapshots'].items():
            self.assertEqual(row['candle_interval_seconds'],int(interval));self.assertEqual(row['collection_cadence_seconds'],60)
            self.assertEqual(row['historical_candle_gaps'][0]['missing_intervals'],1)
            self.assertEqual(row['observed_recording_gaps'],[])
    def test_no_action_no_default_io(self):
        with patch.object(sys,'argv',['owner']),patch('builtins.open',side_effect=AssertionError('NO_FILE')),patch('subprocess.Popen',side_effect=AssertionError('NO_PROCESS')):tools.main()


if __name__=='__main__':unittest.main()
