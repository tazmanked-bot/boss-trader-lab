"""Fabricated tree/DB and controlled stubs only; never owner target, AEP or recorder."""
import copy
import hashlib
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch
from research import target_validation_034 as t, recorder_snapshot_034 as db
from research import llama_analyst_033 as a, decision_loop_032 as d
from research import spot_reversal_candidates as rules,spot_refusal_registry as registry


class TargetTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parent);self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name);self.src=self.root/'source';self.src.mkdir(mode=0o700)
        self.dest=self.root/'new-private'
        (self.src/'lib').mkdir(mode=0o700);(self.src/'bin').mkdir(mode=0o700)
        (self.src/'bin/llama-cli').write_bytes(b'NOT A REAL RUNTIME');(self.src/'bin/llama-cli').chmod(0o500)
        (self.src/'lib/libfake.so.1.0').write_bytes(b'ORIGINAL SYNTHETIC LIBRARY')
        (self.src/'lib/libfake.so.1').symlink_to('libfake.so.1.0');(self.src/'lib/libfake.so').symlink_to('libfake.so.1')
        self.entries=[self.entry('bin/llama-cli','runtime'),self.entry('lib/libfake.so','library')]
        self.guards=[]
        for name in ('socket.socket','socket.getaddrinfo','urllib.request.urlopen'):
            guard=patch(name,side_effect=AssertionError('NO_TARGET_NETWORK'));guard.start();self.addCleanup(guard.stop)
    def entry(self,path,role):
        return {'path':path,'role':role,'reported_sha256':hashlib.sha256((self.src/path).read_bytes()).hexdigest(),'expected_sha256':None,'expected_source':None}
    def request(self):
        f=json.loads((Path(__file__).parent/'fixtures/decision_loop_032.json').read_text())
        e=d.normalize(f['leads'][0],f['as_of']);row=rules.evaluate({'version':rules.VERSION,'label':rules.LABEL,'as_of':f['as_of'],
            'policy':{'version':registry.VERSION,'future_mode':'reject'},'payloads':{e['symbol']:e['payload']}})['symbols'][e['symbol']]
        return {'version':'analyst-request-v1','symbol':e['symbol'],'as_of':f['as_of'],'evidence_id':d.digest(e),'evidence':e,'rules':row,'untrusted_text_policy':'DATA_ONLY_NOT_INSTRUCTIONS'}
    def test_private_copy_plan_preserves_symlink_chain_and_originals(self):
        before={(str(p.relative_to(self.src))):p.lstat().st_mode for p in self.src.rglob('*')}
        with patch('subprocess.Popen',side_effect=AssertionError('NO_EXEC')):
            result=t.copy_plan(str(self.src),str(self.dest),self.entries)
        links=[o for o in result['operations'] if o['action']=='PRESERVE_RELATIVE_SYMLINK']
        self.assertEqual({o['target'] for o in links},{'libfake.so.1','libfake.so.1.0'})
        self.assertFalse(self.dest.exists());self.assertEqual(result['writes_performed'],0)
        self.assertEqual(before,{str(p.relative_to(self.src)):p.lstat().st_mode for p in self.src.rglob('*')})
        self.assertIn('INDEPENDENT_EXPECTATION_MISSING',result['holds'])
    def test_expectations_never_promote_reported_hash_to_integrity_proof(self):
        for e in self.entries:e.update(expected_sha256=e['reported_sha256'],expected_source='SYNTHETIC_TEST_ONLY')
        result=t.copy_plan(str(self.src),str(self.dest),self.entries)
        self.assertIn('TARGET_CONTAINMENT_UNVERIFIED',result['holds']);self.assertEqual(result['state'],'REAL_NOT_RUN')
        self.entries[0]['expected_sha256']='0'*64
        self.assertIn('EXPECTED_HASH_MISMATCH',t.copy_plan(str(self.src),str(self.dest),self.entries)['holds'])
    def test_unsafe_ancestor_permissions_are_not_fixed_in_place(self):
        (self.src/'lib').chmod(0o777)
        result=t.copy_plan(str(self.src),str(self.dest),self.entries)
        self.assertIn('RESOLVED_ANCESTOR_WRITABLE',result['holds']);self.assertEqual((self.src/'lib').stat().st_mode&0o777,0o777)
    def test_link_escape_absolute_links_and_destination_overlap_refuse(self):
        with self.assertRaises(ValueError):t.copy_plan(str(self.src),str(self.src/'new'),self.entries)
        (self.src/'lib/bad').symlink_to('/etc/passwd')
        with self.assertRaises(ValueError):t.copy_plan(str(self.src),str(self.dest),[{'path':'lib/bad','role':'library','reported_sha256':None,'expected_sha256':None,'expected_source':None}])
        self.entries[0]['path']='../outside'
        with self.assertRaises(ValueError):t.copy_plan(str(self.src),str(self.dest),self.entries)
    def test_first_plan_uses_64_tokens_and_never_launches(self):
        manifest=a.stub_manifest(self.root)
        with patch('subprocess.Popen',side_effect=AssertionError('NO_MODEL')):
            plan=t.first_inference_plan(manifest,self.request())
        argv=plan['argv_profile'];self.assertEqual(argv[argv.index('--n-predict')+1],'64')
        self.assertEqual(plan['scope']['context'],2048);self.assertEqual(plan['scope']['threads'],2)
        self.assertTrue(plan['scope']['cpu_only']);self.assertEqual(plan['state'],'REAL_NOT_RUN')
        self.assertIsNone(plan['measurements']['peak_ram_bytes'])
        with self.assertRaisesRegex(ValueError,'REAL_NOT_RUN'):t.TargetAnalyst(manifest).infer(self.request())
    def test_containment_positive_claims_do_not_activate_and_scope_binding(self):
        manifest=a.stub_manifest(self.root);p=t.first_inference_plan(manifest,self.request())
        receipt={'version':t.VERSION,'scope_sha256':p['scope_sha256'],'mode':'SYNTHETIC_TEST','checks':dict.fromkeys(t.CHECKS,True),'evidence_refs':['invented-not-target-proof']}
        result=t.first_inference_plan(manifest,self.request(),receipt)
        self.assertEqual(result['real_activation'],'DISABLED');self.assertIn('TARGET_CONTAINMENT_UNVERIFIED',result['holds'])
        receipt['checks']['parent_canary_positive']=False
        self.assertIn('parent_canary_positive',t.assess_containment(receipt,p['scope_sha256'])['missing_checks'])
        with self.assertRaises(ValueError):t.assess_containment(receipt,'other-scope')
    def test_truncated_first_output_and_extra_order_fields_fail_closed(self):
        ref='a'*64
        for raw in (b'{"version":"analyst-v1",',b'{"order":"BUY"}',b'{"a":1,"a":2}'):
            with self.assertRaises(ValueError):t.validate_first_output(raw,ref)
        value={'version':'analyst-v1','hypothesis':'SYNTHETIC validator test, not AI',
               'evidence_refs':[ref],'strongest_objection':'No genuine evidence',
               'missing_information':[],'invalidation':'Eligible low breach','disposition':'ABSTAIN'}
        self.assertEqual(t.validate_first_output(json.dumps(value).encode(),ref)['disposition'],'ABSTAIN')
    def test_reported_target_fingerprints_remain_reported_only(self):
        self.assertEqual(t.REPORTED['model']['bytes'],1117320736)
        self.assertEqual(t.REPORTED['runtime']['bytes'],1424080)
        self.assertEqual(t.REPORTED['recorder_service'],'REPORTED_RESUMED_DB_FRESHNESS_UNKNOWN')
    def test_plan_default_no_io_or_subprocess(self):
        import sys
        with patch.object(sys,'argv',['target']),patch('builtins.open',side_effect=AssertionError('NO_FILE')),patch('subprocess.Popen',side_effect=AssertionError('NO_EXEC')):t.main()


class RecorderTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.path=Path(self.tmp.name)/'synthetic.sqlite';self.now=1900000800
    def create(self,rows):
        connection=sqlite3.connect(self.path);connection.execute('CREATE TABLE events(open_time INTEGER, recorded_at INTEGER,stream TEXT)')
        connection.executemany('INSERT INTO events VALUES (?,?,?)',[(*row,'SYNTHETIC_BTC_USD') for row in rows]);connection.commit();connection.close()
    def inspect(self,**kwargs):
        return db.freshness(str(self.path),'events','open_time','recorded_at',self.now,snapshot_kind='OWNER_CONSISTENT_OFFLINE_SNAPSHOT',stream_column='stream',stream_value='SYNTHETIC_BTC_USD',**kwargs)
    def test_read_only_recent_metrics_and_no_file_or_sidecar_change(self):
        self.create([(self.now-7200,self.now-3590),(self.now-3600,self.now)])
        before=self.path.read_bytes();files=set(self.path.parent.iterdir());result=self.inspect()
        self.assertEqual(result['freshness'],'RECENT_RELATIVE_TO_SUPPLIED_AS_OF')
        self.assertEqual(result['database_writes'],0);self.assertEqual(self.path.read_bytes(),before)
        self.assertEqual(set(self.path.parent.iterdir()),files)
    def test_backfill_and_recent_ingestion_do_not_establish_current_candles(self):
        self.create([(self.now-86400,self.now-10),(self.now-72000,self.now-5)])
        result=self.inspect();self.assertEqual(result['freshness'],'STALE')
        self.assertEqual(result['possible_delayed_or_backfilled_rows'],2)
        self.assertTrue(result['historical_candle_gaps']);self.assertEqual(result['observed_recording_gaps'],[])
        self.assertEqual(result['outage_cause'],'NOT_ESTABLISHED')
    def test_insert_gap_is_not_historical_coverage_or_outage_proof(self):
        self.create([(self.now-18000,self.now-14400),(self.now-3600,self.now)])
        result=self.inspect();self.assertTrue(result['observed_recording_gaps']);self.assertTrue(result['historical_candle_gaps'])
    def test_live_wal_and_unknown_snapshot_kind_refuse(self):
        self.create([(self.now-3600,self.now)]);Path(str(self.path)+'-wal').write_bytes(b'fake-sidecar')
        with self.assertRaisesRegex(ValueError,'SIDECAR'):self.inspect()
        with self.assertRaises(ValueError):db.freshness(str(self.path),'events','open_time','recorded_at',self.now,snapshot_kind='LIVE')
    def test_future_milliseconds_incomplete_and_sql_injection_refuse(self):
        for row in [(self.now,self.now),(self.now-3600,(self.now-1)*1000)]:
            if self.path.exists():self.path.unlink()
            self.create([row])
            with self.assertRaises(ValueError):self.inspect()
        with self.assertRaisesRegex(ValueError,'SQL_IDENTIFIER'):db.freshness(str(self.path),'events;DROP TABLE events','open_time','recorded_at',self.now,snapshot_kind='OWNER_CONSISTENT_OFFLINE_SNAPSHOT',stream_column='stream',stream_value='SYNTHETIC_BTC_USD')
    def test_other_stream_cannot_hide_selected_stream_staleness(self):
        self.create([(self.now-86400,self.now-10)])
        connection=sqlite3.connect(self.path)
        connection.execute('INSERT INTO events VALUES (?,?,?)',(self.now-3600,self.now,'OTHER_STREAM'))
        connection.commit();connection.close()
        self.assertEqual(self.inspect()['freshness'],'STALE')
    def test_bounded_window_is_disclosed(self):
        self.create([(self.now-10800,self.now-7200),(self.now-7200,self.now-3600),(self.now-3600,self.now)])
        with patch.object(db,'MAX_ROWS',2):
            result=self.inspect()
        self.assertEqual(result['rows_examined'],2);self.assertEqual(result['history_scope'],'LATEST_2_INGESTIONS_ONLY')
    def test_recorder_default_does_not_open_database(self):
        import sys
        with patch.object(sys,'argv',['freshness']),patch.object(db.sqlite3,'connect',side_effect=AssertionError('NO_DATABASE')):db.main()
    def test_empty_and_missing_schema_refuse_without_mutation(self):
        self.create([])
        with self.assertRaisesRegex(ValueError,'EMPTY'):self.inspect()
        before=self.path.read_bytes()
        with self.assertRaises(ValueError):db.freshness(str(self.path),'missing','open_time','recorded_at',self.now,snapshot_kind='OWNER_CONSISTENT_OFFLINE_SNAPSHOT',stream_column='stream',stream_value='SYNTHETIC_BTC_USD')
        self.assertEqual(self.path.read_bytes(),before)


if __name__=='__main__':unittest.main()
