"""Executable, child-only synthetic qualification. No genuine model invocation."""
import contextlib
import fcntl
import hashlib
import json
import os
from pathlib import Path
import secrets
import shutil
import socket
import stat
import sys
import tempfile
import threading
from . import process
from .provision import need,secure,hash_file
from research.decision_loop_032 import digest
from research.llama_analyst_033 import Refused

WORKER=Path(__file__).with_name('worker.py')
WORKER_SHA='21df83767120a3b236fe9cfa1597b35ebe61f8f3117236b3c0257db0ac218fc5'


def pinned_worker():
    need(hash_file(WORKER)[0]==WORKER_SHA,'WORKER_PIN_MISMATCH');return str(WORKER)


def environment(home):
    return {'PATH':'/nonexistent','HOME':str(home),'TMPDIR':str(home),'LANG':'C','LC_ALL':'C',
            'OMP_NUM_THREADS':'2','OPENBLAS_NUM_THREADS':'2'}


class Cgroup:
    def __init__(self,parent):self.path=None;self.parent=Path(parent) if parent else None
    def __enter__(self):
        if self.parent is None:return self
        root=Path('/sys/fs/cgroup').resolve()
        need(self.parent.is_absolute() and self.parent.resolve().is_relative_to(root) and self.parent.resolve()!=root,'DELEGATED_CGROUP_REQUIRED')
        need(self.parent.stat().st_uid==os.getuid(),'CGROUP_OWNERSHIP')
        need({'memory','cpu','pids'}<=set((self.parent/'cgroup.subtree_control').read_text().split()),'CONTROLLERS_NOT_DELEGATED')
        self.path=self.parent/('boss-035-'+secrets.token_hex(12));self.path.mkdir()
        try:
            for name,value in {'memory.max':str(3*1024**3),'memory.swap.max':'0','cpu.max':'100000 100000','pids.max':'8','memory.oom.group':'1'}.items():
                (self.path/name).write_text(value)
                need((self.path/name).read_text().strip()==value,'CGROUP_LIMIT_MISMATCH')
        except Exception:
            self.path.rmdir();self.path=None;raise
        return self
    def attach(self,pid):
        if self.path is not None:(self.path/'cgroup.procs').write_text(str(pid))
    def evidence(self):
        return {'private_limits_configured':self.path is not None,
                'memory_peak_bytes':int((self.path/'memory.peak').read_text()) if self.path and (self.path/'memory.peak').exists() else None}
    def __exit__(self,*_):
        if self.path is None:return
        if (self.path/'cgroup.procs').read_text().strip():
            if (self.path/'cgroup.kill').exists():(self.path/'cgroup.kill').write_text('1')
            need(not (self.path/'cgroup.procs').read_text().strip(),'OWN_CGROUP_CLEANUP_UNVERIFIED')
        self.path.rmdir()


class Canaries:
    def __init__(self,challenge):self.challenge=challenge.encode();self.sockets=[];self.threads=[];self.stop=threading.Event();self.counts=[0,0,0]
    def __enter__(self):
        try:
            for index,(family,kind,address) in enumerate(((socket.AF_INET,socket.SOCK_STREAM,'127.0.0.1'),(socket.AF_INET6,socket.SOCK_STREAM,'::1'),(socket.AF_INET,socket.SOCK_DGRAM,'127.0.0.1'))):
                s=socket.socket(family,kind);self.sockets.append(s)
                if family==socket.AF_INET6:s.setsockopt(socket.IPPROTO_IPV6,socket.IPV6_V6ONLY,1)
                s.bind((address,0));s.settimeout(.1)
                if kind==socket.SOCK_STREAM:s.listen(2)
                def serve(s=s,index=index,kind=kind):
                    while not self.stop.is_set():
                        try:
                            if kind==socket.SOCK_STREAM:
                                conn,_=s.accept()
                                with conn:
                                    conn.settimeout(.3);data=conn.recv(256)
                                    if data==self.challenge:self.counts[index]+=1
                                    conn.sendall(data)
                            else:
                                data,peer=s.recvfrom(256)
                                if data==self.challenge:self.counts[index]+=1
                                s.sendto(data,peer)
                        except (TimeoutError,OSError):continue
                thread=threading.Thread(target=serve,daemon=True);thread.start();self.threads.append(thread)
            return self
        except Exception:self.__exit__();raise
    def positive(self):
        for index,s in enumerate(self.sockets):
            with socket.socket(s.family,s.type) as client:
                client.settimeout(1);client.connect(s.getsockname());client.sendall(self.challenge)
                need(client.recv(256)==self.challenge,'PARENT_POSITIVE_CONTROL_FAILED')
    def __exit__(self,*_):
        self.stop.set()
        for s in self.sockets:s.close()
        for t in self.threads:t.join(timeout=1)


def qualify(state_directory,*,request_binding,protected_roots,cgroup_parent=None,bundle_root=None,timeout=10):
    """Existing bwrap required. Never sudo/install/change global namespace settings."""
    result={'version':'qualification-v1','mode':'ACTUAL_LOCAL_SYNTHETIC_PROFILE_ONLY','state':'REAL_NOT_RUN',
            'qualified':False,'request_binding':request_binding,'checks':{},'real_model_launch':'TECHNICALLY_DISABLED','owner_target_executed_by_codex':False}
    try:
        need(sys.platform=='linux','LINUX_REQUIRED');worker=pinned_worker()
        need(type(protected_roots) is list and protected_roots and all(Path(p).is_absolute() for p in protected_roots),'PROTECTED_ROOTS_REQUIRED')
        bwrap=shutil.which('bwrap');need(bool(bwrap),'BWRAP_UNAVAILABLE')
        bwrap=str(Path(bwrap).resolve());secure(Path(bwrap));bwrap_sha=hash_file(bwrap)[0]
        python=str(Path(sys.executable).resolve());need(python.startswith('/usr/'),'SYSTEM_PYTHON_PROFILE_REQUIRED')
        for p in protected_roots:need(not Path(python).is_relative_to(Path(p)),'PROTECTED_INTERPRETER_PROFILE_UNSUPPORTED')
        if bundle_root is not None:
            bundle=secure(Path(bundle_root));need(bundle.is_dir() and bundle.stat().st_mode&0o777==0o700,'PRIVATE_BUNDLE_REQUIRED')
        state=secure(Path(state_directory));need(state.is_dir() and state.stat().st_uid==os.getuid() and state.stat().st_mode&0o777==0o700,'PRIVATE_STATE_DIRECTORY_REQUIRED')
        fd=os.open(state/'.boss-035.lock',os.O_RDWR|os.O_CREAT|os.O_NOFOLLOW|os.O_NONBLOCK,0o600)
        group=None
        try:
            need(os.fstat(fd).st_uid==os.getuid() and stat.S_ISREG(os.fstat(fd).st_mode) and os.fstat(fd).st_mode&0o077==0,'LOCK_OWNERSHIP')
            need(not (state/'.cleanup-poison').exists() and not (state/'.cleanup-poison').is_symlink(),'CLEANUP_POISONED')
            try:fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
            except BlockingIOError:raise Refused('QUALIFICATION_BUSY') from None
            group=Cgroup(cgroup_parent)
            with tempfile.TemporaryDirectory(prefix='qualification-',dir=state) as tmp,group as cg:
                root=Path(tmp);scratch=root/'scratch';scratch.mkdir(mode=0o700)
                challenge=secrets.token_hex(24);private=root/'host-only';private.write_text(challenge);private.chmod(0o600)
                readonly=root/'readonly';readonly.write_text(challenge);readonly.chmod(0o600)
                resolv=root/'resolv.conf';resolv.write_text('nameserver 127.0.0.1\noptions attempts:1 timeout:1\n')
                scope={'worker_sha256':WORKER_SHA,'bwrap_sha256':bwrap_sha,'python_sha256':hash_file(python)[0],
                       'profile':'bwrap-unshare-all-synthetic-v1','cgroup_required':True,'limits':'034-CPU1-MEM3G-THREADS2','request_binding':request_binding,'protected_roots_sha256':digest(protected_roots),'concurrency_domain_sha256':hashlib.sha256(str(state.resolve()).encode()).hexdigest(),'filesystem_probe_fsize_bytes':4096,'final_fsize_bytes':0}
                scope_sha=digest(scope)
                with Canaries(challenge) as canary:
                    canary.positive();counts=list(canary.counts)
                    cfg={'scope_sha256':scope_sha,'parent_netns':os.readlink('/proc/self/ns/net'),
                         'ipv4_port':canary.sockets[0].getsockname()[1],'ipv6_port':canary.sockets[1].getsockname()[1],
                         'dns_port':canary.sockets[2].getsockname()[1],'challenge':challenge,'forbidden_file':str(private),'reference':request_binding['evidence_id'],'protected_roots':protected_roots}
                    config=root/'config.json';config.write_text(json.dumps(cfg));config.chmod(0o400)
                    argv=[bwrap,'--unshare-all','--die-with-parent','--new-session','--clearenv',
                          '--ro-bind','/usr','/usr','--proc','/proc','--dev','/dev','--dir','/etc',
                          '--ro-bind',str(resolv),'/etc/resolv.conf','--tmpfs','/tmp',
                          '--bind',str(scratch),'/work','--ro-bind',str(readonly),'/readonly',
                          '--ro-bind',str(config),'/config.json','--ro-bind',worker,'/worker.py',
                          '--setenv','HOME','/work','--setenv','LANG','C','--setenv','OMP_NUM_THREADS','2']
                    if bundle_root is not None:argv+=['--ro-bind',str(bundle),'/bundle']
                    for directory in ('/lib','/lib64','/bin'):
                        p=Path(directory)
                        if p.is_symlink():argv.extend(['--symlink',os.readlink(p),directory])
                        elif p.exists():argv.extend(['--ro-bind',directory,directory])
                    for protected in protected_roots:
                        path=Path(protected)
                        if any(path.is_relative_to(base) for base in (Path('/usr'),Path('/lib'),Path('/lib64'),Path('/bin'))):
                            need(path.is_dir(),'PROTECTED_MASK_REQUIRES_DIRECTORY');argv+=['--tmpfs',str(path)]
                    argv+=['--chdir','/work',python,'-I','-S','-B','/worker.py','probe']
                    read_gate,write_gate=os.pipe()
                    try:
                        def release(pid):
                            nonlocal write_gate
                            gate=write_gate;write_gate=None
                            try:cg.attach(pid);os.write(gate,b'1')
                            finally:os.close(gate)
                        data,process_receipt=process.run([python,'-I','-S','-B',worker,'limit-exec',str(read_gate),*argv],
                            env=environment(root),cwd=root,timeout=timeout,pass_fds=(read_gate,),release=release)
                    finally:
                        os.close(read_gate)
                        if write_gate is not None:
                            with contextlib.suppress(OSError):os.close(write_gate)
                    need(process_receipt['stderr_bytes']==0,'UNEXPECTED_SANDBOX_STDERR')
                    child=json.loads(data)
                    need(child['scope_sha256']==scope_sha,'CHILD_SCOPE_MISMATCH')
                    need(canary.counts==counts,'CHILD_REACHED_PARENT_CANARY')
                    canary.positive();need(all(b-a==1 for a,b in zip(counts,canary.counts)),'POST_POSITIVE_FAILED')
                    need(private.read_text()==challenge and readonly.read_text()==challenge,'HOST_CANARY_MODIFIED')
                    result.update(scope=scope,scope_sha256=scope_sha,checks=child['checks'],process=process_receipt,cgroup=cg.evidence(),analysis=child['analysis'])
                    result['checks']['parent_positive_controls']=True
                    result['checks']['no_child_packets']=True
                    result['checks']['process_tree_gone']=process_receipt['process_tree_gone']
                    result['checks']['cgroup_limits']=cg.path is not None
                    result['checks']['artifact_bundle_bound']=bundle_root is not None and request_binding.get('bundle_inventory_sha256') is not None
                    result['qualified']=all(v is True for v in result['checks'].values())
        finally:
            if process.POISONED or group is not None and group.path is not None and group.path.exists():
                with contextlib.suppress(FileExistsError):
                    with (state/'.cleanup-poison').open('x') as f:f.write('Cleanup unverified; independent owner review required. No automatic retry.')
            os.close(fd)
    except (Refused,OSError,ValueError,KeyError) as exc:
        result['blocker']=str(exc) if isinstance(exc,Refused) else type(exc).__name__
        result['qualified']=False
        if 'group' in locals() and group is not None and group.path is not None and group.path.exists():
            result['private_cleanup_required']={'own_cgroup_for_owner_review':str(group.path),'policy':'NO_AUTOMATIC_GLOBAL_CLEANUP'}
    result['receipt_sha256']=digest(result)
    return result
