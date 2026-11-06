"""Fixed package/version contract, exercised with sealed FAKE processes only.

Native execution is BLOCKED: no independently enforced no-network/no-clock
boundary, descriptor-bound exec or reviewed installed build is supplied here.
There is no subprocess/Popen implementation or real command execution route.
"""
from dataclasses import dataclass
import hashlib
import json
import re
import stat

NS=1_000_000_000
CHILD_NS=2*NS
RUN_NS=10*NS
CLEANUP_NS=250_000_000
CHILD_BYTES=16384
REPORT_BYTES=65536
MAX_EVENTS=4096
DPKG='/usr/bin/dpkg-query'
BINARIES=('/usr/sbin/chronyd','/usr/bin/chronyc')
FORMAT='${binary:Package}\t${Status}\t${Version}\t${Architecture}\t${source:Package}\t${source:Version}\n'
ENV=(('LC_ALL','C'),('LANG','C'),('DPKG_COLORS','never'))


class Refused(ValueError):pass


def require(ok,reason):
    if not ok:raise Refused(reason)


@dataclass(frozen=True)
class Command:
    argv: tuple
    env: tuple=ENV
    cwd: str='/'
    stdin: str='DEVNULL'
    close_fds: bool=True
    shell: bool=False
    new_session: bool=True
    privilege_contract: str='UNPRIVILEGED_NO_CLOCK_CAPABILITY_REQUIRED'
    identity_contract: str='VERIFIED_DESCRIPTOR_EXEC_REQUIRED_NOT_IMPLEMENTED'


def plan():
    return (Command((DPKG,'--no-pager','--show','--showformat='+FORMAT,'chrony')),
            Command((DPKG,'--no-pager','--search',*BINARIES)),
            Command((BINARIES[0],'--version')),Command((BINARIES[1],'--version')))


def check_command(index,command):
    require(type(index) is int and 0<=index<4 and type(command) is Command
            and command==plan()[index],'COMMAND_REFUSED')


def disabled(*,metadata=False,versions=False):
    return {'overall':'HOLD','B1':'HOLD','B2':'HOLD','B3':'HOLD','B4':'NO-GO','B5':'HOLD',
            'provenance':'AUTHENTIC_PROVENANCE_NOT_COLLECTED','independent_utc':False,
            'live_source_admission':'HOLD','policy':'NO ORDERS','requests':0,'process_launches':0,
            'reason':'EXECUTION_CONTAINMENT_UNAVAILABLE' if metadata is True or versions is True else 'AUTHORIZATION_MISSING',
            'actual_package_version':None,'actual_build_capability':'UNVERIFIED',
            'source_checkout':'UNAVAILABLE','target_run':'UNAVAILABLE'}


@dataclass(frozen=True)
class FileIdentity:
    path: str
    device: int
    inode: int
    mode: int
    size: int
    mtime_ns: int
    ctime_ns: int
    sha256: str
    capabilities: str='MODEL_NONE'


def check_identity(value,path):
    require(type(value) is FileIdentity and value.path==path,'IDENTITY_MISSING')
    require(stat.S_ISREG(value.mode) and value.mode & 0o111 and not value.mode & 0o6000
            and value.capabilities=='MODEL_NONE','IDENTITY_UNSAFE')
    require(all(type(getattr(value,k)) is int and getattr(value,k)>=0 for k in ('device','inode','size','mtime_ns','ctime_ns'))
            and 0<value.size<=16*1024*1024 and re.fullmatch('[0-9a-f]{64}',value.sha256) is not None,'IDENTITY_INVALID')
    return value


@dataclass(frozen=True)
class Event:
    delta_ns: int=1_000_000
    channel: str='stdout'
    data: bytes=b''


@dataclass(frozen=True)
class FakeRun:
    events: tuple=()
    exit_status: int=0
    launch_ns: int=1_000_000
    cleanup_ns: int=1_000_000
    hang: bool=False
    reaped: bool=True
    group_empty: bool=True


@dataclass(frozen=True)
class MockReview:
    """Test recipe, NEVER approval of an actual installed chrony build."""
    package_version: str
    source_version: str
    upstream_version: str
    identities: tuple
    origin: str='SYNTHETIC_REVIEW_NOT_EXECUTION_APPROVAL'


class FakeBackend:
    """Sealed event data: no launch callback, file reader or native runner."""
    def __init__(self,runs,identities,*,snapshots=None,root=False,context=None):
        require(type(runs) is tuple and len(runs)<=4 and all(type(r) is FakeRun for r in runs),'FAKE_INPUT_INVALID')
        for run in runs:
            require(type(run.events) is tuple and len(run.events)<=MAX_EVENTS+1,'FAKE_INPUT_INVALID')
            require(all(type(e) is Event and type(e.delta_ns) is int and 0<e.delta_ns<=CHILD_NS
                        and e.channel in ('stdout','stderr') and type(e.data) is bytes
                        and len(e.data)<=CHILD_BYTES+1 for e in run.events),'FAKE_INPUT_INVALID')
            require(type(run.exit_status) is int and all(type(v) is int and 0<=v<=RUN_NS for v in (run.launch_ns,run.cleanup_ns)),'FAKE_INPUT_INVALID')
            require(all(type(v) is bool for v in (run.hang,run.reaped,run.group_empty)),'FAKE_INPUT_INVALID')
        self.runs=runs;self.identities=dict(identities);self.snapshots=dict(snapshots or {})
        self.root=root;self.context=dict(context or {})
        self.now=0;self.launches=[];self.cleanup=[];self.identity_calls={}
        self.claimed=False

    def identity(self,path):
        index=self.identity_calls.get(path,0);self.identity_calls[path]=index+1
        changes=self.snapshots.get(path,())
        value=changes[min(index,len(changes)-1)] if changes else self.identities.get(path)
        return check_identity(value,path)

    def launch(self,index,command,identity):
        check_command(index,command)
        require(not self.root,'PRIVILEGE_REFUSED')
        require(index==len(self.launches) and index<len(self.runs),'FAKE_SEQUENCE_INVALID')
        require(identity.path==command.argv[0],'IDENTITY_MISMATCH')
        run=self.runs[index];self.launches.append(command);self.now+=run.launch_ns
        return run


def _process(backend,index,aggregate_deadline,identity,receipts):
    """Bounded streaming algorithm over fake read events, not a real poll driver."""
    begin=backend.now
    # Reserve cleanup inside both the per-command and aggregate budgets.
    deadline=min(begin+CHILD_NS,aggregate_deadline)-CLEANUP_NS
    require(begin<deadline,'TIMEOUT')
    command=plan()[index];run=None;failure=None;stdout=bytearray();stderr=bytearray()
    receipt={'index':index,'kind':'FAKE_PROCESS_ONLY','bytes':0,'cleanup':'NOT_STARTED'}
    receipts.append(receipt)
    try:
        require(backend.identity(command.argv[0])==identity,'IDENTITY_CHANGED')
        run=backend.launch(index,command,identity)
        require(backend.now<deadline,'TIMEOUT')
        for count,event in enumerate(run.events):
            require(count<MAX_EVENTS,'STREAM_EVENT_LIMIT')
            backend.now+=event.delta_ns
            require(backend.now<deadline,'TIMEOUT')
            # Cap before append, combining both output streams.
            require(len(stdout)+len(stderr)+len(event.data)<=CHILD_BYTES,'OUTPUT_OVERFLOW')
            (stdout if event.channel=='stdout' else stderr).extend(event.data)
        if run.hang:
            backend.now=deadline
            raise Refused('TIMEOUT')
        require(0<=run.exit_status,'PROCESS_SIGNAL')
        require(run.exit_status==0,'PROCESS_NONZERO')
        require(not stderr,'STDERR_REFUSED')
        require(backend.identity(command.argv[0])==identity,'IDENTITY_CHANGED')
    except Refused as exc:failure=exc
    finally:
        receipt.update(bytes=len(stdout)+len(stderr),stdout_sha256=hashlib.sha256(stdout).hexdigest(),
                       stderr_sha256=hashlib.sha256(stderr).hexdigest())
        if run is not None:
            killed=failure is not None
            backend.cleanup.append({'index':index,'kill_owned_group':killed,'reap_exact_child':True})
            backend.now+=run.cleanup_ns
            safe=run.reaped and run.group_empty and run.cleanup_ns<=CLEANUP_NS
            receipt.update(cleanup='MODEL_REAPED' if safe else 'UNCERTAIN',killed_model_group=killed)
            if not safe:failure=Refused('CLEANUP_UNCERTAIN_STOP')
        receipt['child_budget_exceeded']=backend.now-begin>=CHILD_NS
        if receipt['child_budget_exceeded'] and failure is None:failure=Refused('TIMEOUT')
        if backend.now>=aggregate_deadline and failure is None:failure=Refused('AGGREGATE_TIMEOUT')
        receipt['elapsed_ns']=backend.now-begin
    if failure:raise failure
    return bytes(stdout)


def metadata(raw):
    require(type(raw) is bytes and 0<len(raw)<=CHILD_BYTES,'PACKAGE_METADATA_INVALID')
    try:text=raw.decode('ascii')
    except UnicodeError:raise Refused('PACKAGE_METADATA_INVALID') from None
    require(text.endswith('\n') and text.count('\n')==1,'PACKAGE_METADATA_INVALID')
    fields=text[:-1].split('\t');require(len(fields)==6,'PACKAGE_METADATA_INVALID')
    package,status,version,arch,source,source_version=fields
    require(package in ('chrony','chrony:amd64') and source=='chrony','PACKAGE_MISMATCH')
    require(status in ('install ok installed','hold ok installed'),'PACKAGE_NOT_INSTALLED')
    require(arch=='amd64','ARCHITECTURE_UNREVIEWED')
    require(all(0<len(v)<=128 and re.fullmatch('[0-9][A-Za-z0-9.+:~_-]*',v) for v in (version,source_version)),'PACKAGE_VERSION_UNKNOWN')
    return {'package':package,'status':status,'version':version,'architecture':arch,'source_package':source,
            'source_version':source_version,'provenance':'LOCAL_METADATA_ONLY'}


def ownership(raw):
    try:lines=raw.decode('ascii').splitlines()
    except UnicodeError:raise Refused('OWNERSHIP_INVALID') from None
    require(len(lines)==2,'OWNERSHIP_INVALID')
    paths=set()
    for line in lines:
        match=re.fullmatch(r'(chrony(?::amd64)?): (/usr/sbin/chronyd|/usr/bin/chronyc)',line)
        require(match is not None,'BINARY_UNOWNED_OR_DIVERTED')
        require(match[2] not in paths,'OWNERSHIP_INVALID');paths.add(match[2])
    require(paths==set(BINARIES),'BINARY_UNOWNED_OR_DIVERTED')


def banner(raw,name,expected_version):
    try:text=raw.decode('ascii')
    except UnicodeError:raise Refused('VERSION_BANNER_INVALID') from None
    require(len(text)<=1024,'VERSION_BANNER_INVALID')
    match=re.fullmatch(re.escape(name)+r' \(chrony\) version ([0-9][A-Za-z0-9.+:~_-]{0,63}) \(([^\n\r]*)\)\n',text)
    require(match is not None,'VERSION_BANNER_INVALID')
    require(match[1]==expected_version,'VERSION_MISMATCH')
    tokens=match[2].split()
    require(len(tokens)<=32 and len(tokens)==len(set(tokens))
            and all(re.fullmatch('[+-][A-Z0-9_]{1,24}',t) for t in tokens),'VERSION_BANNER_INVALID')
    nts='CLIENT_REPORTED_NTS_BUILD_FLAG' if '+NTS' in tokens and '-NTS' not in tokens else 'UNSUPPORTED' if '-NTS' in tokens else 'UNKNOWN'
    return {'version':match[1],'status':'CLIENT_REPORTED_VERSION','nts_flag':nts}


def evaluate_offline(backend=None,*,metadata_opt_in=False,version_opt_in=False,review=None):
    output={**disabled(),'evidence_origin':'STATIC_FAKE_PROCESS_EVENTS','fake_launches':0,'receipts':[],'model_status':'DISABLED'}
    if metadata_opt_in is not True:return output
    try:
        require(type(backend) is FakeBackend,'REAL_EXECUTION_BLOCKED')
        require(not backend.claimed and backend.now==0 and not backend.launches,'FAKE_CONTEXT_REUSED')
        backend.claimed=True
        # Context is fixture data, never a real verified HEAD/image assertion.
        context=backend.context
        require(set(context)=={'origin','source_head','clean','os','python','kernel','image','run_id','job_id'}
                and context['origin']=='SYNTHETIC_CONTEXT' and context['clean'] is True
                and type(context['source_head']) is str and re.fullmatch('[0-9a-f]{40}',context['source_head'])
                and all(type(context[k]) is str and 1<=len(context[k])<=128 and all(32<=ord(c)<=126 for c in context[k])
                        for k in ('os','python','kernel','image','run_id','job_id')),'CONTEXT_UNVERIFIED')
        require(context['os']=='ubuntu-24.04' and context['python']=='3.11.17','TARGET_PROFILE_UNREVIEWED')
        output['model_context']=dict(context)
        require(not backend.root,'PRIVILEGE_REFUSED')
        deadline=backend.now+RUN_NS
        identities={path:backend.identity(path) for path in (DPKG,*BINARIES)}
        package=metadata(_process(backend,0,deadline,identities[DPKG],output['receipts']))
        output['model_package']=package
        ownership(_process(backend,1,deadline,identities[DPKG],output['receipts']))
        output.update(model_status='METADATA_SHAPE_VALID',reason='REAL_EXECUTION_BLOCKED')
        if version_opt_in is True:
            require(type(review) is MockReview and review.origin=='SYNTHETIC_REVIEW_NOT_EXECUTION_APPROVAL','BUILD_UNREVIEWED')
            require(package['version']==review.package_version and package['source_version']==review.source_version
                    and tuple(identities[p] for p in BINARIES)==review.identities,'BUILD_UNREVIEWED')
            results={}
            for index,path in enumerate(BINARIES,2):
                # Fresh check immediately before the modeled launch. The real
                # fd-based exec/loader race is unresolved, never claimed closed.
                require(backend.identity(path)==identities[path],'IDENTITY_CHANGED')
                parsed=banner(_process(backend,index,deadline,identities[path],output['receipts']),path.rsplit('/',1)[1],review.upstream_version)
                results[path]=parsed
                if index==2:require(parsed['nts_flag']=='CLIENT_REPORTED_NTS_BUILD_FLAG','NTS_BUILD_FLAG_UNSUPPORTED_OR_UNKNOWN')
            output.update(model_versions=results,model_status='FAKE_VERSION_RECIPE_PASSED',reason='REAL_EXECUTION_BLOCKED')
    except (Refused,ValueError,TypeError,AttributeError) as exc:
        output.update(model_status='REFUSED',reason=str(exc) if isinstance(exc,Refused) else 'FAKE_INPUT_INVALID')
    if type(backend) is FakeBackend:
        output['fake_launches']=len(backend.launches);output['model_elapsed_ns']=backend.now
    require(len(json.dumps(output,sort_keys=True).encode('ascii'))<=REPORT_BYTES,'REPORT_LIMIT')
    return output


def main():
    import argparse
    from dataclasses import asdict
    parser=argparse.ArgumentParser(description='Blocked native execution; fixed offline package/version plan only')
    parser.add_argument('--plan',action='store_true')
    parser.add_argument('--metadata',action='store_true')
    parser.add_argument('--versions',action='store_true')
    args=parser.parse_args()
    output=disabled(metadata=args.metadata,versions=args.versions)
    if args.plan:
        output['proposed_commands']=[asdict(c) for c in plan()]
        output['caps']={'children':4,'child_ns':CHILD_NS,'aggregate_ns':RUN_NS,'cleanup_ns':CLEANUP_NS,
                        'combined_child_bytes':CHILD_BYTES,'report_bytes':REPORT_BYTES}
    print(json.dumps(output,sort_keys=True));return 2


if __name__=='__main__':raise SystemExit(main())
