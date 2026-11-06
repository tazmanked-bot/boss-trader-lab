"""Optional bounded OFFLINE runner measurements of the unchanged 025 worker.

No real DNS/socket/TLS dependencies. Default CLI is disabled. Linux proc/cgroup
reads and monotonic timing are observations, never UTC or hard containment proof.
"""
import hashlib
from contextlib import ExitStack
import json
import mmap
import os
from pathlib import Path
import platform
import re
import resource
import ssl
import time
from unittest.mock import patch

from research import kraken_btc_transport_025 as transport

NS=1_000_000_000
CASE_NAMES=('success','dns_hang','connect_hang','tls_hang','read_hang',
            'startup_delay','child_memory_refusal','parent_child_pressure','cpu_load','cpu_exhaustion')
MAX_REPORT_BYTES=65536
TRACE_SIZE=4096
AS_OF=1900000800
BODY=b'{"offline_fixture":"'+b'x'*16384+b'"}'
WIRE=(b'HTTP/1.1 200 Offline\r\nContent-Type: application/json\r\nDate: Mon, 01 Jan 2024 00:00:00 GMT\r\nContent-Length: '+str(len(BODY)).encode()+b'\r\n\r\n'+BODY)


def read_small(path,limit=8192):
    try:
        with open(path,'rb') as handle:value=handle.read(limit+1)
        if len(value)>limit:return None
        return value.decode('ascii')
    except (OSError,UnicodeError):return None


def process_sample(pid):
    status=read_small(f'/proc/{pid}/status')
    def amount(name):
        match=re.search(r'^'+name+r':\s+(\d+) kB$',status or '',re.M)
        return int(match[1])*1024 if match else None
    try:
        with os.scandir(f'/proc/{pid}/fd') as entries:
            fds=0
            for _ in entries:
                fds+=1
                if fds>1024:return {'rss_bytes':amount('VmRSS'),'hwm_bytes':amount('VmHWM'),'fds':None}
    except OSError:fds=None
    return {'rss_bytes':amount('VmRSS'),'hwm_bytes':amount('VmHWM'),'fds':fds}


def cgroup_snapshot(root='/sys/fs/cgroup'):
    """Read visible v2 root only; not assumed to be the workload's leaf cgroup."""
    values={}
    for name in ('memory.max','memory.current','memory.peak'):
        raw=read_small(Path(root)/name,128)
        text=raw.strip() if raw is not None else ''
        values[name]=int(text) if re.fullmatch(r'[0-9]{1,24}',text) else 'max' if text=='max' else None
    membership=read_small('/proc/self/cgroup',4096)
    return {'status':'OBSERVED_VISIBLE_ROOT' if any(v is not None for v in values.values()) else 'UNAVAILABLE',
            'scope':'VISIBLE_ROOT_MAY_BE_SHARED_OR_ANCESTOR_NOT_DEDICATED',
            'membership_sha256':hashlib.sha256(membership.encode()).hexdigest() if membership else None,
            'values':values,'dedicated_containment_verified':False}


def _git_head(root):
    # Read detached HEAD or loose ref only; never run git, hooks, shell or network.
    head=read_small(Path(root)/'.git/HEAD',256)
    if head is None:return None
    head=head.strip()
    if head.startswith('ref: refs/heads/'):
        ref=head[5:]
        if not re.fullmatch(r'refs/heads/[A-Za-z0-9/_-]{1,128}',ref):return None
        head=read_small(Path(root)/'.git'/ref,128)
        head=head.strip() if head else ''
    return head if re.fullmatch('[0-9a-f]{40}',head) else None


def runner_profile(revision):
    transport.require(type(revision) is str and re.fullmatch('[0-9a-f]{40}',revision) is not None,'MANIFEST_INVALID')
    root=Path(__file__).resolve().parent.parent
    os_fields={}
    release=read_small('/etc/os-release') or ''
    for key in ('ID','VERSION_ID'):
        match=re.search(r'^'+key+r'="?([a-zA-Z0-9._-]{1,64})"?$',release,re.M)
        os_fields[key]=match[1] if match else None
    image={}
    for key in ('ImageOS','ImageVersion','RUNNER_OS','RUNNER_ARCH'):
        value=os.environ.get(key)
        image[key]=value if value and re.fullmatch('[a-zA-Z0-9._ -]{1,128}',value) else None
    hashes={}
    for name in ('kraken_btc_transport_025.py','runner_diagnostic_026.py','utc_evidence_026.py'):
        raw=read_small(root/'research'/name,262144)
        hashes[name]=hashlib.sha256(raw.encode()).hexdigest() if raw is not None else None
    observed=_git_head(root)
    return {'revision_claim':revision,'git_head_observed':observed,
            'revision_status':'MATCH' if observed==revision else 'MISMATCH' if observed else 'UNAVAILABLE',
            'source_sha256':hashes,'python':platform.python_version(),'python_build':list(platform.python_build()),
            'kernel':platform.release(),'architecture':platform.machine(),'os':os_fields,'runner_image':image,
            'requested_target':{'os':'ubuntu-24.04','python':'3.11.17'},
            'target_verified':False,'clock_boottime_available':hasattr(time,'CLOCK_BOOTTIME')}


def _trace_read(storage):
    size=int.from_bytes(storage[:4],'big')
    if not 0<size<=TRACE_SIZE-4:return {}
    try:return json.loads(storage[4:4+size])
    except (ValueError,UnicodeError):return {}


def _trace_update(storage,**fields):
    values=_trace_read(storage);values.update(fields)
    raw=json.dumps(values,sort_keys=True).encode('ascii')
    if len(raw)>TRACE_SIZE-4:raise RuntimeError('TRACE_LIMIT')
    storage[4:4+len(raw)]=raw;storage[:4]=len(raw).to_bytes(4,'big')


class FakeStream:
    def __init__(self,case,storage):self.case,self.storage,self.position=case,storage,0
    def settimeout(self,seconds):
        transport.require(0<seconds<=10,'TIMEOUT')
    def _phase(self,name):
        _trace_update(self.storage,phase=name,phase_started_ns=time.monotonic_ns())
        if self.case==name+'_hang':
            while True:time.sleep(1)
    def connect(self,address):
        transport.require(address==('8.8.8.8',443),'DNS_INVALID');self._phase('connect')
    def do_handshake(self):self._phase('tls')
    def selected_alpn_protocol(self):return 'http/1.1'
    def sendall(self,value):
        transport.require(value.startswith(b'GET /0/public/AssetPairs?pair=XBTUSD&')
                          and b'Host: api.kraken.com\r\n' in value,'MANIFEST_INVALID')
    def recv_into(self,view,size):
        if self.position==0:self._phase('read')
        count=min(size,len(WIRE)-self.position)
        view[:count]=WIRE[self.position:self.position+count];self.position+=count;return count
    def close(self):pass


class FakeTLS:
    check_hostname=True
    verify_mode=ssl.CERT_REQUIRED
    minimum_version=ssl.TLSVersion.TLSv1_2
    def set_alpn_protocols(self,value):transport.require(value==['http/1.1'],'TLS_FAILURE')
    def wrap_socket(self,stream,*,server_hostname,do_handshake_on_connect):
        transport.require(server_hostname=='api.kraken.com' and do_handshake_on_connect is False,'TLS_FAILURE')
        return stream


def measured_case(case,*,budget_ns=200_000_000):
    """One bounded child only; instrumentation patches restored in all paths."""
    transport.require(case in CASE_NAMES and type(budget_ns) is int
                      and 20_000_000<=budget_ns<=NS,'MANIFEST_INVALID')
    transport.require(hasattr(os,'wait4'),'PLATFORM_UNSUPPORTED')
    baseline=process_sample(os.getpid())
    parent_pressure=bytearray(8*1024*1024) if case=='parent_child_pressure' else None
    storage=mmap.mmap(-1,TRACE_SIZE)
    state={'pid':None,'kill_ns':None,'reaped':False,'wait4_peak_rss_bytes':None,
           'ready_observed_ns':None,'release_ns':None,'reap_ns':None,
           'parent_sampled_peak_rss_bytes':baseline['rss_bytes'],
           'child_sampled_peak_rss_bytes':None,'aggregate_sampled_peak_rss_bytes':None,
           'parent_fd_peak':baseline['fds'],'child_fd_peak':None,'samples':0}
    original_fork,original_write,original_kill=os.fork,os.write,os.kill
    original_waitpid,original_select,original_setsid=os.waitpid,transport.select.select,os.setsid
    start=time.monotonic_ns()
    reason='WORKER_INVALID';result_size=0
    child_retained=[]
    def peak(key,value):
        if value is not None:state[key]=max(state[key] or 0,value)
    def sample():
        parent=process_sample(os.getpid());child=process_sample(state['pid']) if state['pid'] else {}
        peak('parent_sampled_peak_rss_bytes',parent.get('rss_bytes'));peak('child_sampled_peak_rss_bytes',child.get('rss_bytes'))
        peak('parent_fd_peak',parent.get('fds'));peak('child_fd_peak',child.get('fds'))
        if parent.get('rss_bytes') is not None and child.get('rss_bytes') is not None:
            peak('aggregate_sampled_peak_rss_bytes',parent['rss_bytes']+child['rss_bytes'])
        state['samples']+=1
    def fork():
        pid=original_fork()
        if pid:state['pid']=pid
        return pid
    def setsid():
        result=original_setsid()
        if case=='startup_delay':
            _trace_update(storage,phase='startup',phase_started_ns=time.monotonic_ns())
            time.sleep(2*budget_ns/NS)
        return result
    def write(fd,value):
        if value==b'R':_trace_update(storage,child_ready_ns=time.monotonic_ns())
        if value==b'G':state['release_ns']=time.monotonic_ns()
        return original_write(fd,value)
    def select(read,write,exception,timeout):
        sample()
        result=original_select(read,write,exception,timeout)
        if read and result[0]:state['ready_observed_ns']=time.monotonic_ns()
        return result
    def kill(pid,sig):
        state['kill_ns']=time.monotonic_ns();return original_kill(pid,sig)
    def waitpid(pid,flags):
        # wait4 has exactly the required waitpid result plus per-child rusage.
        done,status,usage=os.wait4(pid,flags)
        if done==pid:
            state.update(reaped=True,reap_ns=time.monotonic_ns(),wait4_peak_rss_bytes=int(usage.ru_maxrss)*1024)
        return done,status
    def factory(request):
        _trace_update(storage,factory_ns=time.monotonic_ns(),child_pid=os.getpid())
        if case=='child_memory_refusal':
            try:bytearray(transport.ADDRESS_SPACE_BYTES)
            except MemoryError:
                _trace_update(storage,allocation_refused=True)
                raise transport.Refused('NETWORK_UNAVAILABLE')
            raise transport.Refused('WORKER_INVALID')
        if case=='parent_child_pressure':
            child_retained.append(bytearray(16*1024*1024))
            _trace_update(storage,controlled_child_pressure_bytes=16*1024*1024)
        if case in ('cpu_load','cpu_exhaustion'):
            _trace_update(storage,phase='controlled_cpu_load',phase_started_ns=time.monotonic_ns())
            finish=time.monotonic_ns()+(budget_ns//4 if case=='cpu_load' else 2*budget_ns)
            while time.monotonic_ns()<finish:pass
        stream=FakeStream(case,storage)
        def dns(host,port):
            transport.require((host,port)==('api.kraken.com',443),'DNS_INVALID')
            _trace_update(storage,phase='dns',phase_started_ns=time.monotonic_ns())
            if case=='dns_hang':
                while True:time.sleep(1)
            return ('8.8.8.8',)
        return dns,lambda:stream,FakeTLS()
    try:
        with patch.object(os,'fork',fork),patch.object(os,'setsid',setsid),patch.object(os,'write',write),\
             patch.object(os,'kill',kill),patch.object(os,'waitpid',waitpid),patch.object(transport.select,'select',select):
            try:
                result=transport.isolated_exchange(transport.manifest(AS_OF)[0],AS_OF,
                    dependencies_factory=factory,timeout_ns=budget_ns)
                transport.require(result==WIRE,'IPC_INVALID');result_size=len(result);reason='COMPLETED'
            except transport.Refused as exc:reason=exc.reason
        end=time.monotonic_ns()
        trace=_trace_read(storage)
    finally:
        # Independent cleanup backstop, even if the transport raises unexpectedly.
        if state['pid'] and not state['reaped']:
            try:
                original_kill(state['pid'],9)
            except ProcessLookupError:pass
            until=time.monotonic_ns()+transport.CLEANUP_NS
            while True:
                try:done,_=original_waitpid(state['pid'],os.WNOHANG)
                except ChildProcessError:break
                if done:break
                if time.monotonic_ns()>=until:
                    raise transport.Refused('WORKER_UNREAPED')
                time.sleep(.001)
        storage.close()
        parent_pressure=None
    final=process_sample(os.getpid())
    if not state['reaped'] or reason=='WORKER_UNREAPED':
        raise transport.Refused('WORKER_UNREAPED') # STOP, never next case.
    fd_available=final['fds'] is not None and baseline['fds'] is not None
    transport.require(not fd_available or final['fds']<=baseline['fds'],'FD_LEAK_STOP')
    def elapsed(value):return value-start if value is not None else None
    return {'case':case,'reason':reason,'requests':0,'budget_ns':budget_ns,'elapsed_ns':end-start,
            'observed_overshoot_ns':max(0,end-start-budget_ns),
            'start_to_child_ready_ns':elapsed(trace.get('child_ready_ns')),
            'start_to_ready_observed_ns':elapsed(state['ready_observed_ns']),
            'start_to_release_ns':elapsed(state['release_ns']),
            'kill_to_reap_ns':state['reap_ns']-state['kill_ns'] if state['kill_ns'] and state['reap_ns'] else None,
            'reaped':state['reaped'],'result_bytes':result_size,'ipc_map_bytes':transport.MAP_SIZE,
            'parent_fd_baseline':baseline['fds'],'parent_fd_final':final['fds'],
            'fd_evidence':'BASELINE_RESTORED' if fd_available else 'UNAVAILABLE',
            **{k:state[k] for k in ('parent_fd_peak','child_fd_peak','parent_sampled_peak_rss_bytes',
               'child_sampled_peak_rss_bytes','aggregate_sampled_peak_rss_bytes','wait4_peak_rss_bytes','samples')},
            'child_trace':trace,'measurement_kind':'SAMPLED_LOCAL_OBSERVATION_NOT_WORST_CASE',
            'rss_caveat':'SUM_COUNTS_SHARED_PAGES_TWICE; POLLING_CAN_MISS_PEAKS; WAIT4_IS_CHILD_HIGH_WATER'}


def run_offline(*,revision=None,budget_ns=200_000_000):
    if revision is None:return {'overall':'HOLD','reason':'AUTHORIZATION_MISSING','requests':0,'B4':'NO-GO','B5':'HOLD'}
    profile=runner_profile(revision)
    transport.require(profile['revision_status']!='MISMATCH','REVISION_MISMATCH')
    before=cgroup_snapshot()
    # Defense against accidental future networking, inherited by real children.
    with ExitStack() as guards:
        for name in ('socket.socket','socket.create_connection','socket.getaddrinfo',
                     'urllib.request.urlopen','http.client.HTTPSConnection','subprocess.Popen'):
            guards.enter_context(patch(name,side_effect=transport.Refused('NETWORK_UNAVAILABLE')))
        cases=[measured_case(name,budget_ns=budget_ns) for name in CASE_NAMES]
    expected=lambda name:'TIMEOUT' if name.endswith('_hang') or name in ('startup_delay','cpu_exhaustion') else 'NETWORK_UNAVAILABLE' if name=='child_memory_refusal' else 'COMPLETED'
    output={'overall':'HOLD','mode':'MANUAL_OFFLINE_ONLY','requests':0,'B1':'HOLD','B2':'HOLD',
            'B3':'HOLD','B4':'NO-GO','B5':'HOLD','policy':'NO ORDERS','profile':profile,
            'cgroup_before':before,'cgroup_after':cgroup_snapshot(),'cases':cases,
            'offline_diagnostic_status':'EXPECTED_RESULTS' if all(c['reason']==expected(c['case']) for c in cases) else 'UNEXPECTED_RESULTS',
            'real_network_guard':'DENY',
            'hard_containment_verified':False,'independent_utc_verified':False}
    transport.require(len(json.dumps(output).encode())<=MAX_REPORT_BYTES,'OUTPUT_LIMIT')
    return output


def main():
    import argparse
    parser=argparse.ArgumentParser(description='Manual offline worker measurements; no live option')
    parser.add_argument('--offline-run',action='store_true')
    parser.add_argument('--revision')
    args=parser.parse_args()
    if not args.offline_run:
        print(json.dumps(run_offline()));return 2
    try:
        transport.require(args.revision is not None,'MANIFEST_INVALID')
        result=run_offline(revision=args.revision)
        print(json.dumps(result,sort_keys=True));return 0 if result['offline_diagnostic_status']=='EXPECTED_RESULTS' else 2
    except Exception as exc:
        print(json.dumps({'overall':'HOLD','reason':exc.reason if isinstance(exc,transport.Refused) else 'DIAGNOSTIC_FAILED',
                          'requests':0,'B4':'NO-GO','B5':'HOLD','policy':'NO ORDERS'}));return 2


if __name__=='__main__':raise SystemExit(main())
