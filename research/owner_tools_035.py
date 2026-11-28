"""Consolidated owner commands; no actual inference command exists."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import sys
from research import decision_loop_032 as loop,llama_analyst_033 as adapter,recorder_snapshot_034 as snapshot
from research.qualification_035 import provision,containment,executor


def read(path):
    with open(path,'rb') as f:return adapter.strict_json(f.read(loop.MAX_BYTES+1),loop.MAX_BYTES)


def request_fixture():
    fixture=loop.parse((Path(__file__).parent.parent/'tests/fixtures/decision_loop_032.json').read_text());found=[]
    class Capture(loop.MockAnalyst):
        def infer(self,request):found.append(request);return super().infer(request)
    loop.run({**fixture,'leads':fixture['leads'][:1]},Capture());return found[0]


def snapshot_schema(config):
    # Reuse the same strict static snapshot checks, without guessing its cadence.
    path=Path(config['snapshot'])
    provision.need(config['snapshot_kind']=='OWNER_CONSISTENT_OFFLINE_SNAPSHOT' and path.is_absolute() and path.is_file() and not path.is_symlink(),'SNAPSHOT_REQUIRED')
    provision.need(not any(Path(str(path)+s).exists() or Path(str(path)+s).is_symlink() for s in ('-wal','-shm','-journal')),'LIVE_SIDECAR_REFUSED')
    provision.need(0<path.stat().st_size<=snapshot.MAX_DB_BYTES,'SNAPSHOT_SIZE')
    before=path.stat();db=sqlite3.connect(path.as_uri()+'?mode=ro&immutable=1',uri=True)
    try:
        db.execute('PRAGMA query_only=ON');db.execute('PRAGMA trusted_schema=OFF');db.enable_load_extension(False)
        steps=[0]
        def progress():steps[0]+=1;return steps[0]>1000
        db.set_progress_handler(progress,1000)
        tables=db.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name LIMIT 129").fetchall()
        provision.need(len(tables)<=128,'SCHEMA_LIMIT')
        result={}
        for (name,) in tables:
            if name.startswith('sqlite_'):continue
            result[name]=[{'name':r[1],'declared_type':r[2]} for r in db.execute('PRAGMA table_info('+snapshot.identifier(name)+')')]
        provision.need((before.st_ino,before.st_mtime_ns,before.st_size)==(path.stat().st_ino,path.stat().st_mtime_ns,path.stat().st_size),'SNAPSHOT_CHANGED')
        return {'mode':'READ_ONLY_OFFLINE_SCHEMA_LOCAL_ONLY','tables':result,'interval_semantics':'OWNER_MUST_DECLARE_NO_INFERENCE_FROM_SCHEMA','writes':0}
    finally:db.close()


def demo():
    import tempfile
    from research.qualification_035.synthetic import bundle
    with tempfile.TemporaryDirectory(dir=Path(__file__).parent.parent/'tests') as tmp:
        root=Path(tmp);config=bundle(root);dry=provision.provision(config);applied=provision.provision(config,apply=True)
        pin=hashlib.sha256(loop.canonical(applied).encode()).hexdigest()
        verified=provision.verify_bundle(config,pin);rolled=provision.rollback(config,pin)
        manifest=adapter.stub_manifest(tmp);request=request_fixture();prepared=executor.plan(manifest,request)
        injected=executor.synthetic_receipt(prepared['binding'])
        result=executor.DisabledExecutor(prepared,injected).stub(request['evidence_id'])
        state=Path(tmp)/'state';state.mkdir(mode=0o700)
        actual_qualification=containment.qualify(str(state),request_binding=prepared['binding'],protected_roots=config['protected_roots'])
        snapshots={};now=1900000800
        for interval in (900,3600):
            dbpath=root/('snapshot-'+str(interval)+'.sqlite')
            with sqlite3.connect(dbpath) as connection:
                connection.execute('CREATE TABLE events(opened INTEGER,ingested INTEGER,stream TEXT,duration INTEGER)')
                connection.executemany('INSERT INTO events VALUES (?,?,?,?)',[(now-3*interval,now-2*interval,'SYNTHETIC',interval),(now-interval,now,'SYNTHETIC',interval)])
            snapshots[str(interval)]=snapshot.freshness(str(dbpath),'events','opened','ingested',now,snapshot_kind='OWNER_CONSISTENT_OFFLINE_SNAPSHOT',
                stream_column='stream',stream_value='SYNTHETIC',expected_interval=interval,collection_cadence=60,
                timestamp_semantics='UTC_EPOCH_SECONDS_OPEN_TIME_AND_ACTUAL_INSERT_TIME',interval_column='duration')
        return {'version':'codex-035-demo-v1','mode':'SYNTHETIC_ONLY_NOT_OWNER_TARGET','state':'REAL_NOT_RUN',
                'provision_dry_run':{'writes':dry['writes'],'files':len(dry['files'])},
                'provision_apply_verified':verified['operation'],'rollback':rolled,
                'stub':result,'actual_codex_capability_attempt':actual_qualification,
                'synthetic_snapshots':snapshots,'response_budget':executor.shortest_response(request['evidence_id']),
                'real_inference_count':0,'additional_cost_ntd':'0','buy_authorization':'NONE'}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=('snapshot','provision','qualify','plan','rollback','demo'),nargs='?')
    parser.add_argument('config',nargs='?');parser.add_argument('--apply',action='store_true')
    parser.add_argument('--schema',action='store_true');parser.add_argument('--receipt');parser.add_argument('--receipt-output')
    args=parser.parse_args()
    if args.action is None:print('REAL_NOT_RUN. No default file/process/network/database activity.');return
    if args.action=='demo':print(json.dumps(demo(),indent=2));return
    provision.need(bool(args.config),'LOCAL_CONFIG_REQUIRED');config=read(args.config)
    if args.action=='snapshot':
        result=snapshot_schema(config['snapshot']) if args.schema else snapshot.freshness(**config['snapshot'])
    elif args.action=='provision':
        if args.apply:
            provision.need(bool(args.receipt_output) and not Path(args.receipt_output).exists(),'NEW_RECEIPT_OUTPUT_REQUIRED')
            output=Path(args.receipt_output);provision.secure(output.parent)
            for protected in config['provision']['protected_roots']+[config['provision']['destination']]:
                provision.need(not output.is_relative_to(Path(protected)),'RECEIPT_IN_PROTECTED_OR_BUNDLE_PATH')
        result=provision.provision(config['provision'],apply=args.apply)
        if args.apply:
            pin=hashlib.sha256(loop.canonical(result).encode()).hexdigest();wrapper={'receipt':result,'receipt_sha256':pin}
            created=None
            try:
                path=Path(args.receipt_output)
                fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
                with os.fdopen(fd,'w') as f:
                    created=(os.fstat(f.fileno()).st_dev,os.fstat(f.fileno()).st_ino);json.dump(wrapper,f,indent=2);f.flush();os.fsync(f.fileno())
            except Exception:
                if created and path.exists() and (path.lstat().st_dev,path.lstat().st_ino)==created:path.unlink()
                provision.rollback(config['provision'],pin);raise
            result={'operation':result['operation'],'receipt_sha256':pin,'state':'REAL_NOT_RUN'}
    elif args.action=='rollback':
        receipt=read(args.receipt);result=provision.rollback(config['provision'],receipt['receipt_sha256'])
    else:
        receipt=read(args.receipt);bundle_receipt=provision.verify_bundle(config['provision'],receipt['receipt_sha256'])
        manifest=config['adapter_manifest'];request=request_fixture() if config['request_path'] is None else read(config['request_path'])
        destination=Path(config['provision']['destination'])
        for key in ('runtime_path','model_path'):provision.need(Path(manifest[key]).is_relative_to(destination),'ADAPTER_OUTSIDE_PRIVATE_BUNDLE')
        result=executor.plan(manifest,request,bundle_receipt)
        if args.action=='qualify':
            qualification=dict(config['qualification']);qualification['protected_roots']=[str(Path(p).resolve()) for p in config['provision']['protected_roots']];qualification['bundle_root']=str(destination)
            for p in qualification['protected_roots']+[str(destination)]:
                provision.need(not Path(qualification['state_directory']).is_relative_to(Path(p)),'STATE_DIRECTORY_OVERLAP')
            result=containment.qualify(**qualification,request_binding=result['binding'])
    print(json.dumps(result,indent=2))


if __name__=='__main__':
    try:main()
    except (ValueError,OSError,KeyError,TypeError) as exc:
        print(json.dumps({'state':'REAL_NOT_RUN','error':str(exc) if isinstance(exc,adapter.Refused) else type(exc).__name__,'action':'HOLD_NO_AUTOMATIC_RETRY'}));sys.exit(2)
