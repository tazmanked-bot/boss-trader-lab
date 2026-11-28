"""Passive target preparation only. Never copies, executes runtime, or enables AI."""
import hashlib
import json
import os
from pathlib import Path
import re
import stat
from research import llama_analyst_033 as adapter
from research import decision_loop_032 as loop

VERSION='target-validation-v1'
REPORTED={
 'cpu':'Ryzen 3 2200G AVX2/FMA','os':'Debian x86_64','vcpus':2,
 'ram_gib':5.8,'available_ram_gib':5.5,
 'runtime':{'bytes':1424080,'sha256':'daa63b89ca47f511403ad31f23d4fa9b907713a27d4d7dfa6cd01fe872a7a5c2'},
 'model':{'bytes':1117320736,'sha256':'6a1a2eb6d15622bf3c96857206351ba97e1af16c30d7a74ee38970e434e9407e'},
 'source_revision':'0978a6e9022fb9bd6874b86154ee304e81929b9f',
 'unshare_user_net_exit':0,'recorder_service':'REPORTED_RESUMED_DB_FRESHNESS_UNKNOWN',
 'desktop_failure_root_cause':'UNRESOLVED'}
CHECKS=('parent_canary_positive','network_namespace_distinct','ipv4_parent_canary_denied',
        'ipv6_parent_canary_denied','dns_egress_denied','host_private_read_denied',
        'runtime_model_write_denied','scratch_only_writable','process_tree_reaped',
        'memory_cpu_limits_enforced','ssh_and_recorder_unchanged')


def need(value,reason):
    if not value:raise adapter.Refused(reason)


def assess_containment(receipt,scope_digest):
    loop.exact(receipt,('version','scope_sha256','mode','checks','evidence_refs'))
    need(receipt['version']==VERSION and receipt['scope_sha256']==scope_digest,'SCOPE_MISMATCH')
    need(receipt['mode'] in ('SYNTHETIC_TEST','OWNER_REPORTED'),'RECEIPT_MODE')
    loop.exact(receipt['checks'],CHECKS)
    need(all(type(v) is bool for v in receipt['checks'].values()),'CHECK_TYPE')
    need(type(receipt['evidence_refs']) is list and all(type(v) is str and 0<len(v)<=200 for v in receipt['evidence_refs']),'EVIDENCE_REFS')
    missing=[name for name in CHECKS if not receipt['checks'][name]]
    return {'state':'REAL_NOT_RUN','assessment':'SIMULATED_ONLY' if receipt['mode']=='SYNTHETIC_TEST' else 'OWNER_REPORT_NOT_INDEPENDENT_ATTESTATION',
            'missing_checks':missing,'evidence_missing':not receipt['evidence_refs'],
            'real_activation':'DISABLED','buy_authorization':'NONE'}


def _ancestors(path):
    findings=[]
    for p in (path,*path.parents):
        info=p.stat()
        if info.st_mode & 0o022:findings.append(str(p))
    return findings


def copy_plan(source_root,destination,entries):
    """Read only. Preserve relative links; never chmod/copy/write AEP originals.

    Caller supplies an explicit reviewed dependency inventory, not ldd execution.
    A complete loader dependency closure and independently trusted pins remain gates.
    """
    root=Path(source_root);dest=Path(destination)
    need(root.is_absolute() and dest.is_absolute(),'ABSOLUTE_PATH_REQUIRED')
    literal_root_unsafe=_ancestors(root)
    root=root.resolve(strict=True)
    need(root.is_dir(),'SOURCE_DIRECTORY_REQUIRED')
    need(not dest.exists() and not dest.is_symlink(),'DESTINATION_MUST_BE_NEW')
    resolved_dest=dest.resolve(strict=False)
    need(not resolved_dest.is_relative_to(root) and not root.is_relative_to(resolved_dest),'DESTINATION_OVERLAP')
    need(type(entries) is list and 1<=len(entries)<=64,'ENTRY_LIMIT')
    operations=[];holds=['DEPENDENCY_CLOSURE_UNVERIFIED','TARGET_CONTAINMENT_UNVERIFIED'];seen=set()
    root_unsafe=literal_root_unsafe+_ancestors(root)
    if root_unsafe:holds.append('SOURCE_ANCESTOR_WRITABLE')
    # Check existing destination ancestors without creating anything.
    existing=dest.parent
    while not existing.exists():existing=existing.parent
    if _ancestors(existing):holds.append('DESTINATION_ANCESTOR_WRITABLE')
    for entry in entries:
        loop.exact(entry,('path','role','reported_sha256','expected_sha256','expected_source'))
        name=entry['path'];relative=Path(name)
        need(type(name) is str and name and not relative.is_absolute() and '..' not in relative.parts and name not in seen,'ENTRY_PATH')
        need(entry['role'] in ('runtime','library','model'),'ENTRY_ROLE');seen.add(name)
        for key in ('reported_sha256','expected_sha256'):
            need(entry[key] is None or type(entry[key]) is str and re.fullmatch('[a-f0-9]{64}',entry[key]),'HASH_INVALID')
        if entry['expected_sha256'] is None or not entry['expected_source']:
            holds.append('INDEPENDENT_EXPECTATION_MISSING')
        else:need(type(entry['expected_source']) is str and len(entry['expected_source'])<=200,'EXPECTED_SOURCE_INVALID')
        path=root/relative
        need(path.exists() or path.is_symlink(),'SOURCE_MISSING')
        resolved=path.resolve(strict=True)
        need(resolved.is_relative_to(root),'RESOLVED_LIBRARY_ESCAPES_ROOT')
        if _ancestors(resolved):holds.append('RESOLVED_ANCESTOR_WRITABLE')
        # Inventory every symlink component, not just the leaf. Preserve spelling.
        cursor=root
        for part in relative.parts:
            cursor=cursor/part
            if cursor.is_symlink():
                chain=cursor;visited=set()
                while chain.is_symlink():
                    need(str(chain) not in visited and len(visited)<16,'SYMLINK_LOOP')
                    visited.add(str(chain));target=os.readlink(chain)
                    need(not Path(target).is_absolute(),'ABSOLUTE_SYMLINK_REVIEW_REQUIRED')
                    need(chain.resolve(strict=True).is_relative_to(root),'SYMLINK_ESCAPE')
                    operation={'action':'PRESERVE_RELATIVE_SYMLINK','path':str(chain.relative_to(root)),'target':target}
                    if operation not in operations:operations.append(operation)
                    chain=Path(os.path.abspath(chain.parent/target))
        info=resolved.stat();need(stat.S_ISREG(info.st_mode),'REGULAR_FILE_REQUIRED')
        cap=adapter.MAX_MODEL_BYTES if entry['role']=='model' else 128*1024**2
        need(0<info.st_size<=cap,'ARTIFACT_SIZE')
        if info.st_mode & 0o022:holds.append('SOURCE_FILE_WRITABLE')
        sha=hashlib.sha256()
        with resolved.open('rb') as stream:
            count=0
            while True:
                block=stream.read(1024*1024)
                if not block:break
                count+=len(block);need(count<=cap,'ARTIFACT_SIZE');sha.update(block)
        after=resolved.stat()
        need((info.st_ino,info.st_size,info.st_mtime_ns)==(after.st_ino,after.st_size,after.st_mtime_ns),'SOURCE_CHANGED')
        actual=sha.hexdigest()
        if entry['reported_sha256'] and actual!=entry['reported_sha256']:holds.append('REPORTED_HASH_MISMATCH')
        if entry['expected_sha256'] and actual!=entry['expected_sha256']:holds.append('EXPECTED_HASH_MISMATCH')
        operations.append({'action':'COPY_REGULAR_THEN_VERIFY','source_relative':str(resolved.relative_to(root)),
             'destination_relative':str(resolved.relative_to(root)),'sha256':actual,'bytes':count,
             'private_mode':'0500' if entry['role']=='runtime' else '0400',
             'role':entry['role'],'expectation':'SOURCE_RECORD_NOT_AUTHENTICATED' if entry['expected_sha256'] else 'UNKNOWN'})
    # Every link target must itself be inventoried and copied, including versioned libs.
    regular_paths={o['source_relative'] for o in operations if o['action']=='COPY_REGULAR_THEN_VERIFY'}
    for operation in operations:
        if operation['action']=='PRESERVE_RELATIVE_SYMLINK':
            final=str((root/operation['path']).resolve().relative_to(root))
            if final not in regular_paths:holds.append('LINK_TARGET_NOT_INVENTORIED')
    return {'version':VERSION,'state':'REAL_NOT_RUN','writes_performed':0,
            'root_mode':'0700','directory_mode':'0700','operations':operations,
            'holds':sorted(set(holds)),'dependency_inventory':'OWNER_DECLARED_NOT_COMPLETE_PROOF',
            'source_paths':'LOCAL_ONLY_DO_NOT_PUBLISH_PRIVATE_PATHS','buy_authorization':'NONE'}


def first_inference_plan(manifest,request,containment=None):
    prepared=adapter.prepare(manifest,request)
    argv=adapter.command(manifest,prepared,'/isolated/synthetic-prompt.txt')
    argv[argv.index('--n-predict')+1]='64'
    # No dispatch to any executor; none can be activated in this revision.
    scope={'manifest_sha256':prepared.manifest_sha256,'prompt_sha256':prepared.prompt_sha256,
           'schema_sha256':hashlib.sha256(prepared.schema_json.encode()).hexdigest(),
           'context':2048,'max_output_tokens':64,'threads':2,'cpu_only':True,
           'wall_budget_seconds':30,'cleanup_allowance_seconds':1,'rlimit_as_bytes':4*1024**3,
           'rlimit_cpu_seconds':30,'rlimit_nofile':32,'rlimit_core':0,'rlimit_fsize':0,
           'processes':1,'required_private_cgroup':{'memory_max_bytes':3*1024**3,'memory_swap_max_bytes':0,'cpu_max_vcpus':1,'nice':10,'status':'NOT_CONFIGURED_OR_VERIFIED'},'combined_output_bytes':8192,'environment':'033_ALLOWLIST_NO_SECRETS'}
    scope_sha=loop.digest(scope)
    assessment=assess_containment(containment,scope_sha) if containment is not None else None
    return {'version':VERSION,'state':'REAL_NOT_RUN','scope':scope,'scope_sha256':scope_sha,
            'argv_profile':argv[1:],'containment':assessment,'measurements':{'latency_ns':None,'peak_ram_bytes':None,'output_valid':None,'model_tokens':None},
            'holds':['SEPARATE_OWNER_GO_REQUIRED','INDEPENDENT_INTEGRITY_UNKNOWN','LICENSE_AND_COMPATIBILITY_UNKNOWN',
                     'TARGET_CONTAINMENT_UNVERIFIED','RECORDER_FRESHNESS_UNKNOWN','DESKTOP_ROOT_CAUSE_UNRESOLVED'],
            'real_activation':'DISABLED','buy_authorization':'NONE'}


def validate_first_output(raw,evidence_id):
    """Offline validation only. A 64-token truncated response must refuse."""
    return loop.analyst_result(adapter.strict_json(raw),evidence_id)


class TargetAnalyst(adapter.PreparedAnalyst):
    """Contract-compatible preparation, always refusing genuine inference."""
    identity={'provider':'target-validation-prepared','model':adapter.MODEL,'kind':'REAL_NOT_RUN'}
    def validation_plan(self,request,containment=None):return first_inference_plan(self.manifest,request,containment)
    def infer(self,request):raise adapter.Refused('REAL_NOT_RUN_TARGET_VALIDATION_AND_SEPARATE_GO_REQUIRED')


def demo():
    """Creates only ephemeral invented files/DB; does not touch target or AEP."""
    import sqlite3
    import tempfile
    from research import recorder_snapshot_034 as snapshots
    fixture_path=Path(__file__).resolve().parents[1]/'tests/fixtures/decision_loop_032.json'
    fixture=loop.parse(fixture_path.read_text());captured=[]
    class Capture(loop.MockAnalyst):
        def infer(self,request):captured.append(request);return super().infer(request)
    loop.run({**fixture,'leads':fixture['leads'][:1]},Capture())
    with tempfile.TemporaryDirectory(prefix='boss-034-test-') as work:
        root=Path(work);source=root/'synthetic-source';source.mkdir(mode=0o700)
        manifest=adapter.stub_manifest(source)
        inventory=[{'path':Path(manifest[key+'_path']).name,'role':key,'reported_sha256':manifest[key+'_sha256'],
                    'expected_sha256':None,'expected_source':None} for key in ('runtime','model')]
        copying=copy_plan(str(source),str(root/'not-created'),inventory)
        plan=first_inference_plan(manifest,captured[0])
        # Public artifact contains no actual target paths or local directory names.
        argv=plan['argv_profile'];argv[argv.index('--model')+1]='/SYNTHETIC/model.gguf'
        receipt={'version':VERSION,'scope_sha256':plan['scope_sha256'],'mode':'SYNTHETIC_TEST',
                 'checks':dict.fromkeys(CHECKS,True),'evidence_refs':['SYNTHETIC_NOT_TARGET_PROOF']}
        all_claimed=assess_containment(receipt,plan['scope_sha256'])
        receipt['checks']['parent_canary_positive']=False
        failed_control=assess_containment(receipt,plan['scope_sha256'])
        db=root/'invented.sqlite';connection=sqlite3.connect(db)
        connection.execute('CREATE TABLE events(open_time INTEGER, recorded_at INTEGER,stream TEXT)')
        now=fixture['as_of']
        connection.executemany('INSERT INTO events VALUES (?,?,?)',[(now-86400,now-10,'SYNTHETIC_BTC_USD'),(now-72000,now-5,'SYNTHETIC_BTC_USD')])
        connection.commit();connection.close()
        freshness=snapshots.freshness(str(db),'events','open_time','recorded_at',now,snapshot_kind='OWNER_CONSISTENT_OFFLINE_SNAPSHOT',stream_column='stream',stream_value='SYNTHETIC_BTC_USD')
    return {'version':VERSION,'mode':'SYNTHETIC_TEST_NOT_TARGET_EXECUTION','state':'REAL_NOT_RUN',
            'copy_plan':copying,'first_inference_plan':plan,'all_checks_claimed_still_disabled':all_claimed,
            'negative_control_missing':failed_control,'synthetic_backfill_snapshot':freshness,
            'actual_model_inference_count':0,'target_service_operations':0,'additional_cost_ntd':'0','buy_authorization':'NONE'}


def main():
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--reported-evidence',action='store_true')
    parser.add_argument('--synthetic-demo',action='store_true')
    parser.add_argument('--copy-plan',metavar='LOCAL_INVENTORY_JSON')
    parser.add_argument('--first-plan',metavar='LOCAL_MANIFEST_JSON');parser.add_argument('--request')
    args=parser.parse_args()
    def read(path):
        with open(path,'rb') as source:return adapter.strict_json(source.read(loop.MAX_BYTES+1),loop.MAX_BYTES)
    if args.synthetic_demo:
        print(json.dumps(demo(),indent=2));return
    if args.reported_evidence:
        print(json.dumps({'state':'REAL_NOT_RUN','reported_only':REPORTED,'independent_expected_hashes':{'runtime':None,'model':None}},indent=2));return
    if args.copy_plan:
        value=read(args.copy_plan);loop.exact(value,('source_root','destination','entries'))
        print(json.dumps(copy_plan(**value),indent=2));return
    if args.first_plan:
        need(bool(args.request),'REQUEST_REQUIRED')
        print(json.dumps(first_inference_plan(read(args.first_plan),read(args.request)),indent=2));return
    print('REAL_NOT_RUN. Passive plans only; no copy, namespace changes, runtime or inference.')


if __name__=='__main__':main()
