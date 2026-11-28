"""Single-shot, owner-invoked contained build. Never inference or original writes."""
import argparse
import contextlib
import fcntl
import hashlib
import json
import math
import os
from pathlib import Path
import secrets
import selectors
import signal
import stat
import struct
import subprocess
import sys
import time
from research import portable_runtime_036 as prep, memory_headroom_037 as memory
from research.qualification_035 import provision as p, process, containment
from research.llama_analyst_033 import Refused

BASE = 'bdd88585f9719d625609834bb26a6fb7513bd502'
WORKER = Path(__file__).with_name('build_worker_037.py')
LIMITS = dict(prep.LIMITS, wall_seconds=7200, cpu_seconds=5400, pids_max=64,
              disk_free_min_bytes=4*1024**3, available_ram_min_bytes=4*1024**3,
              output_max_bytes=4*1024**2)
GATES = dict(prep.GATES, desktop_build='EXPLICIT_OWNER_INVOCATION_ONLY')
CONFIG_FIELDS=frozenset({'source','job','protected_roots','cgroup_parent','health_file','recorder_id',
                         'collection_cadence_seconds','toolchain_evidence','system_libraries'})
SYSTEM_TOOLS = {'cmake': '/usr/bin/cmake', 'cc': '/usr/bin/cc', 'cxx': '/usr/bin/c++',
                'make': '/usr/bin/make', 'linker': '/usr/bin/ld', 'python': '/usr/bin/python3',
                'bwrap': '/usr/bin/bwrap', 'resolution_probe':'/usr/bin/true'}

ENVIRONMENT={'PATH':'/usr/bin:/bin','HOME':'/job/home','TMPDIR':'/job/tmp','LANG':'C','LC_ALL':'C',
             'TZ':'UTC','SOURCE_DATE_EPOCH':'1793705189','GIT_CEILING_DIRECTORIES':'/job',
             'OMP_NUM_THREADS':'1','OPENBLAS_NUM_THREADS':'1','CMAKE_BUILD_PARALLEL_LEVEL':'1'}


@contextlib.contextmanager
def single_executor(parent):
    """Lock the delegation directory inode across all job directories; no socket."""
    path=Path(parent);p.need(path.is_absolute() and path==path.resolve(),'CGROUP_LOCK_PATH')
    fd=os.open(path,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
    try:
        try:fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:raise Refused('BUILD_OR_QUALIFICATION_BUSY') from None
        yield
    finally:os.close(fd)


def read_json(path, cap=8*1024**2):
    path = p.secure(Path(path))
    with os.fdopen(os.open(path, os.O_RDONLY|os.O_NOFOLLOW), 'rb') as source:
        raw = source.read(cap+1)
    p.need(len(raw) <= cap, 'JSON_BUDGET')
    return json.loads(raw)


def new_json(path, data):
    with os.fdopen(os.open(path, os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW, 0o600), 'w') as out:
        out.write(prep.canonical(data)+'\n')


def no_links(path):
    path = Path(path); p.need(path.is_absolute() and path == Path(os.path.abspath(path)), 'ABSOLUTE_SOURCE_PATH')
    for ancestor in reversed((path, *path.parents)):
        info = ancestor.lstat()
        p.need(not stat.S_ISLNK(info.st_mode), 'SOURCE_SYMLINK')
    return path


def git_read(source,*args):
    # Even Git versions that ignore GIT_NO_LAZY_FETCH cannot contact a promisor.
    return prep.git(source,'-c','protocol.allow=never','-c','protocol.file.allow=never',
                    '-c','protocol.http.allow=never','-c','protocol.https.allow=never',
                    '-c','protocol.ssh.allow=never','-c','core.sshCommand=/bin/false',*args)


def source_inventory(source):
    """Group-write is tolerated ONLY on read input authenticated against Git objects.

    Read raw pinned tree objects and check Git object IDs independently. Never
    checkout/filter/chmod or trust untracked content. No shared original binary.
    """
    source = no_links(source); p.need(source.is_dir(), 'LOCAL_SOURCE_REQUIRED')
    config=git_read(source,'config','--null','--list','--includes')
    for item in config.split(b'\0'):
        key,_,value=item.partition(b'\n');key=key.lower()
        p.need(not (key==b'extensions.partialclone' or key.endswith(b'.promisor') or key.startswith(b'remote.') and key.endswith(b'.vcs')),'PROMISOR_OR_HELPER_CONFIG_REVIEW_REQUIRED')
        if key.startswith(b'protocol.') and key.endswith(b'.allow'):p.need(value==b'never','EXTERNAL_PROTOCOL_CONFIG_REFUSED')
    p.need(git_read(source, 'rev-parse', 'HEAD').decode().strip() == prep.COMMIT, 'WRONG_SOURCE_COMMIT')
    commit = git_read(source, 'cat-file', 'commit', prep.COMMIT)
    p.need(hashlib.sha1(b'commit '+str(len(commit)).encode()+b'\0'+commit).hexdigest() == prep.COMMIT, 'COMMIT_OBJECT_HASH')
    p.need(commit.splitlines()[0] == ('tree '+prep.TREE).encode(), 'WRONG_SOURCE_TREE')
    entries = []; total = 0
    def tree(oid, prefix='', depth=0):
        nonlocal total
        p.need(depth <= 32, 'SOURCE_DEPTH')
        raw = git_read(source, 'cat-file', 'tree', oid)
        p.need(hashlib.sha1(b'tree '+str(len(raw)).encode()+b'\0'+raw).hexdigest() == oid, 'TREE_OBJECT_HASH')
        at = 0
        while at < len(raw):
            stop = raw.index(0, at); mode, name = raw[at:stop].split(b' ', 1)
            child = raw[stop+1:stop+21]; p.need(len(child) == 20, 'TREE_TRUNCATED'); at = stop+21
            name = name.decode(); p.need('/' not in name and name not in ('.', '..', '.git'), 'SOURCE_NAME')
            path = prefix+name; prep.relative(path)
            if mode == b'40000': tree(child.hex(), path+'/', depth+1); continue
            p.need(mode in (b'100644', b'100755'), 'SOURCE_LINK_OR_GITLINK')
            f = no_links(source/path)
            with os.fdopen(os.open(f, os.O_RDONLY|os.O_NOFOLLOW), 'rb') as inp:
                before = os.fstat(inp.fileno()); p.need(stat.S_ISREG(before.st_mode) and before.st_size <= 64*1024**2, 'SOURCE_FILE_LIMIT')
                data = inp.read(64*1024**2+1); after = os.fstat(inp.fileno())
            p.need((before.st_dev,before.st_ino,before.st_size,before.st_mtime_ns,before.st_ctime_ns) ==
                   (after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns,after.st_ctime_ns), 'SOURCE_CHANGED')
            p.need(hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).digest() == child, 'DIRTY_TRACKED_SOURCE')
            p.need(bool(before.st_mode & 0o111) == (mode == b'100755'), 'DIRTY_SOURCE_MODE')
            total += len(data); p.need(total <= 1024**3 and len(entries) < 20000, 'SOURCE_TOTAL_LIMIT')
            entries.append({'path':path, 'sha256':hashlib.sha256(data).hexdigest(), 'size':len(data),
                            'mode':mode.decode(), 'identity':[before.st_dev,before.st_ino,before.st_mtime_ns,before.st_ctime_ns]})
    tree(prep.TREE)
    p.need(entries and git_read(source, 'rev-parse', 'HEAD').decode().strip() == prep.COMMIT, 'SOURCE_CHANGED')
    return {'commit':prep.COMMIT, 'tree':prep.TREE, 'entries':entries, 'bytes':total}


def tools_inventory():
    result = {}
    for name, original in SYSTEM_TOOLS.items():
        resolved = Path(original).resolve(strict=True); p.secure(resolved)
        p.need(resolved.is_relative_to('/usr'), 'SYSTEM_TOOL_PROFILE')
        sha, size = p.hash_file(resolved)
        result[name] = {'path':original, 'resolved':str(resolved), 'sha256':sha, 'size':size}
    p.secure(WORKER);p.secure(Path(__file__))
    result['worker'] = {'path':str(WORKER), 'sha256':p.hash_file(WORKER)[0]}
    result['supervisor'] = {'path':str(Path(__file__)), 'sha256':p.hash_file(Path(__file__))[0]}
    p.secure(Path(memory.__file__))
    result['memory_headroom']={'path':str(Path(memory.__file__)),'sha256':p.hash_file(Path(memory.__file__))[0]}
    return result


def commands():
    args = prep.recipe('/job')
    args[0] += ['-DCMAKE_C_COMPILER=/usr/bin/cc', '-DCMAKE_CXX_COMPILER=/usr/bin/c++',
                '-DCMAKE_MAKE_PROGRAM=/usr/bin/make', '-G', 'Unix Makefiles']
    return args


def budget_check(plan):
    p.need(plan['limits'] == LIMITS, 'FIXED_REVIEWED_BUDGET_REQUIRED')
    prep.compatibility()
    parent=plan['config']['cgroup_parent']
    p.need(type(parent) is str and parent.startswith('/'),'DELEGATED_CGROUP_REQUIRED')
    capacity=memory.snapshot(parent)
    p.need(capacity['status']=='PASS' and capacity['available_bytes'] >= LIMITS['available_ram_min_bytes'], 'RAM_HEADROOM_HOLD')
    p.need(__import__('shutil').disk_usage(plan['job']).free >= LIMITS['disk_free_min_bytes'], 'DISK_HEADROOM_HOLD')
    return capacity


def prepare(config, *, apply=False):
    required = CONFIG_FIELDS
    p.need(set(config) == required, 'CONFIG_FIELDS')
    job = Path(config['job']); p.secure(job.parent)
    p.need(job.is_absolute() and job == job.resolve() and not job.exists() and not job.is_symlink(), 'NEW_PRIVATE_JOB_REQUIRED')
    p.need(config['protected_roots'] and config['recorder_id'] and type(config['collection_cadence_seconds']) is int
           and 1 <= config['collection_cadence_seconds'] <= 3600, 'RECORDER_AND_PROTECTED_REQUIRED')
    for value in [config['source'], config['health_file'], *config['protected_roots']]:
        path = Path(value); p.need(path.is_absolute(), 'ABSOLUTE_INPUT_REQUIRED')
        resolved = path.resolve(); p.need(not job.is_relative_to(resolved) and not resolved.is_relative_to(job), 'PROTECTED_JOB_OVERLAP')
    for value in [config['source'],*config['protected_roots']]:
        p.need(not Path(value).resolve().is_relative_to('/usr'), 'PROTECTED_UNDER_TOOLCHAIN_MOUNT')
    manifest = source_inventory(config['source']); tools = tools_inventory()
    evidence = read_json(config['toolchain_evidence']); p.need(evidence.get('packages') and evidence.get('licenses') and evidence.get('review_ref'), 'TOOLCHAIN_REVIEW_REQUIRED')
    system = read_json(config['system_libraries']); validate_system(system)
    plan = {'version':'controlled-build-037-v1','base':BASE,'config':config,'job':str(job),
            'source':manifest,'tools':tools,'toolchain_evidence_sha256':p.hash_file(Path(config['toolchain_evidence']))[0],
            'system_libraries':system,'commands':commands(),'limits':LIMITS,'gates':GATES,
            'toolchain_evidence':evidence,'environment':ENVIRONMENT,
            'host':{'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),'uid':os.getuid(),
                    'kernel':os.uname().release},'created_at':int(time.time()),'nonce':secrets.token_hex(24)}
    # No workspace writes for dry-run. Check current free space on the existing parent.
    observed_job = plan['job']; plan['job'] = str(job.parent)
    plan['memory_evidence']=budget_check(plan); plan['job'] = observed_job
    if not apply: return dict(plan, operation='DRY_RUN_NO_WRITES')
    old = os.umask(0o077)
    try:
        job.mkdir(mode=0o700)
        for name in ('source','build','stage','home','tmp','evidence'):(job/name).mkdir(mode=0o700)
        for entry in manifest['entries']:
            target = job/'source'/entry['path']; target.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
            original = no_links(Path(config['source'])/entry['path'])
            with os.fdopen(os.open(original, os.O_RDONLY|os.O_NOFOLLOW), 'rb') as inp:
                with target.open('xb') as out:
                    __import__('shutil').copyfileobj(inp,out,1024**2)
            target.chmod(0o500 if entry['mode']=='100755' else 0o400)
            p.need(hashlib.sha256(target.read_bytes()).hexdigest()==entry['sha256'], 'COPY_HASH')
        p.need(source_inventory(config['source']) == manifest, 'CONCURRENT_SOURCE_CHANGE')
        new_json(job/'plan.json',plan)
        # Receipt reuses CODEX036's inode/hash guarded rollback for untouched preparation.
        owned={}; hashes={}
        for path in [job,*job.rglob('*')]:
            s=path.lstat();key=str(path.relative_to(job));owned[key]=[s.st_dev,s.st_ino,stat.S_IFMT(s.st_mode)]
            if path.is_file(): hashes[key]=hashlib.sha256(path.read_bytes()).hexdigest()
        receipt={'destination':str(job),'owned':owned,'owned_hashes':hashes}
        new_json(job/prep.RECEIPT,receipt)
        return {'operation':'PREPARED','plan_sha256':prep.digest(plan),'plan':str(job/'plan.json'),
                'rollback_receipt_sha256':p.hash_file(job/prep.RECEIPT)[0], 'gates':GATES}
    finally:os.umask(old)


def passive_elf(path,sha):
    meta=p.elf(path,sha)
    with os.fdopen(os.open(path,os.O_RDONLY|os.O_NOFOLLOW),'rb') as f:data=f.read(128*1024**2+1)
    p.need(len(data)<=128*1024**2 and hashlib.sha256(data).hexdigest()==sha,'ELF_HASH_CHANGED')
    fields=struct.unpack_from('<16sHHIQQQIHHHHHH',data)
    for index in range(fields[10]):
        h=struct.unpack_from('<IIQQQQQQ',data,fields[5]+index*56)
        if h[0]!=2:continue
        for at in range(h[2],h[2]+h[5],16):
            tag,_=struct.unpack_from('<qQ',data,at)
            if tag==0:break
            p.need(tag not in (0x6ffffefb,0x6ffffefc,0x7ffffffd,0x7fffffff),'ELF_AUDIT_FILTER_DEPENDENCY_REFUSED')
    meta['soname']=prep.soname(path)
    p.need(p.hash_file(path)[0]==sha,'ELF_HASH_CHANGED');return meta


def validate_system(system):
    """Explicit trusted host loader/library contract; no directory scanning fallback."""
    p.need(system.get('version')=='reviewed-system-037-v1' and system.get('review_ref'), 'SYSTEM_REVIEW_REQUIRED')
    entries=system.get('entries',[]); p.need(1<=len(entries)<=128, 'SYSTEM_INVENTORY_LIMIT')
    names=set();paths=set()
    for entry in entries:
        p.need(set(entry)=={'name','path','sha256','version','license','license_ref'}, 'SYSTEM_ENTRY_FIELDS')
        path=Path(entry['path']);p.need(path.is_absolute() and path==path.resolve() and path.is_relative_to('/usr/lib'), 'SYSTEM_LIBRARY_ROOT')
        p.secure(path); p.need(entry['name'] not in names and str(path) not in paths and '/' not in entry['name'] and entry['name'] not in ('','.','..'), 'SYSTEM_DUPLICATE_OR_NAME')
        p.need(entry['version'] and entry['license'] and entry['license_ref'], 'SYSTEM_LICENSE_VERSION')
        p.need(p.hash_file(path)[0]==entry['sha256'], 'SYSTEM_HASH'); names.add(entry['name']);paths.add(str(path))
    for entry in entries:
        meta=passive_elf(Path(entry['path']),entry['sha256'])
        p.need(not meta['paths'], 'SYSTEM_SEARCH_PATH_REVIEW_REQUIRED')
        declared=meta['soname']
        p.need(declared==entry['name'] or declared is None and Path(entry['path']).name==entry['name'], 'SYSTEM_SONAME_MISMATCH')
        p.need(set(meta['needed'])<=names, 'SYSTEM_TRANSITIVE_CLOSURE')
    return {e['name']:e for e in entries}


class BuildCgroup(containment.Cgroup):
    def __enter__(self):
        # Refuse any earlier unclean private scope rather than kill foreign work.
        if self.parent is not None:p.need(not list(self.parent.glob('boss-035-*')),'PREVIOUS_PRIVATE_SCOPE_REVIEW_REQUIRED')
        # Reuse reviewed ownership/delegation validation, then widen only build PID limit.
        super().__enter__(); p.need(self.path is not None, 'PRIVATE_CGROUP_REQUIRED')
        try:
            (self.path/'pids.max').write_text('64')
            for key,value in {'memory.max':str(3*1024**3),'memory.swap.max':'0','cpu.max':'100000 100000','pids.max':'64','memory.oom.group':'1'}.items():
                p.need((self.path/key).read_text().strip()==value, 'CGROUP_LIMIT_MISMATCH')
            p.need((self.path/'cgroup.kill').exists(), 'CGROUP_KILL_REQUIRED')
            self.start_cpu=self.cpu_seconds();return self
        except Exception:
            super().__exit__();raise
    def cpu_seconds(self):
        stat=dict(line.split() for line in (self.path/'cpu.stat').read_text().splitlines())
        return int(stat['usage_usec'])/1e6
    def kill(self):
        if self.path is not None:(self.path/'cgroup.kill').write_text('1')
    def empty(self):return not (self.path/'cgroup.procs').read_text().strip()


def health(plan, now=None):
    now=time.time() if now is None else now; config=plan['config']; value=read_json(config['health_file'],4096)
    cadence=config['collection_cadence_seconds']
    p.need(value.get('version')=='external-recorder-health-037-v1' and value.get('recorder_id')==config['recorder_id'], 'HEALTH_IDENTITY')
    for key in ('measured_at','last_collection_at'):
        p.need(type(value.get(key)) is int and value[key]<=now+2, 'HEALTH_CLOCK_OR_TYPE')
    p.need(value.get('healthy') is True and value.get('desktop_stable') is True, 'RECORDER_OR_STABILITY_STOP')
    p.need(0<=now-value['measured_at']<=30 and 0<=now-value['last_collection_at']<=2*cadence+30, 'RECORDER_COLLECTION_STALE')
    return value


def compiler_aliases(plan):
    """Reconstruct only known Debian alternatives pointing at pinned /usr tools."""
    aliases=[]
    for name in ('cc','cxx'):
        if name not in plan['tools']:continue
        original=Path(plan['tools'][name]['path'])
        if original.is_symlink():
            first=os.readlink(original)
            if first.startswith('/etc/'):
                p.need(Path(first).parent==Path('/etc/alternatives'),'TOOL_ALIAS_PROFILE')
                aliases.append((plan['tools'][name]['resolved'],first))
    return aliases


def sandbox(plan, argv):
    job=Path(plan['job']); bwrap=plan['tools']['bwrap']['resolved']
    out=[bwrap,'--unshare-all','--die-with-parent','--new-session','--cap-drop','ALL','--clearenv',
         '--ro-bind','/usr','/usr','--proc','/proc','--dev','/dev','--dir','/etc',
         '--dir','/job','--ro-bind',str(job/'source'),'/job/source']
    for name in ('build','stage','home','tmp'):out+=['--bind',str(job/name),'/job/'+name]
    aliases=compiler_aliases(plan)
    if aliases:out+=['--dir','/etc/alternatives']
    for resolved,alias in aliases:out+=['--symlink',resolved,alias]
    # tmp is disk-backed and inside new job, not an unbounded host tmpfs.
    out+=['--symlink','/job/tmp','/tmp']
    for name in ('lib','lib64','bin','sbin'):
        path=Path('/'+name)
        if path.is_symlink():out+=['--symlink',os.readlink(path),'/'+name]
        else:p.need(not path.exists(),'NON_USRMERGE_PROFILE_REVIEW_REQUIRED')
    env=ENVIRONMENT
    for key,value in env.items():out+=['--setenv',key,value]
    return out+['--chdir','/job/build','--',*argv]


def runtime_mounts(system,interpreter):
    trusted=validate_system(system);mounts=[]
    for entry in trusted.values():
        # Explicit conventional Debian x86_64 default resolution, never a host directory bind.
        for directory in ('/lib/x86_64-linux-gnu','/usr/lib/x86_64-linux-gnu'):
            mounts.append({'source':entry['path'],'destination':directory+'/'+entry['name'],'mode':'ro-file'})
    if interpreter:
        p.need(Path(interpreter).is_absolute() and '..' not in Path(interpreter).parts,'INTERPRETER_PATH')
        resolved=str(Path(interpreter).resolve());entry=next((e for e in trusted.values() if e['path']==resolved),None)
        p.need(entry is not None,'INTERPRETER_NOT_EXPLICIT')
        mounts.append({'source':entry['path'],'destination':interpreter,'mode':'ro-file'})
    return mounts


def resolution_probe(plan):
    program=plan['tools']['resolution_probe']['resolved'];meta=passive_elf(Path(program),plan['tools']['resolution_probe']['sha256'])
    trusted=validate_system(plan['system_libraries']);p.need(set(meta['needed'])<=set(trusted),'PROBE_SYSTEM_CLOSURE')
    out=[plan['tools']['bwrap']['resolved'],'--unshare-all','--die-with-parent','--new-session','--cap-drop','ALL','--clearenv',
         '--proc','/proc','--dev','/dev','--ro-bind',program,'/runtime/bin/probe']
    for mount in runtime_mounts(plan['system_libraries'],meta['interpreter']):out+=['--ro-bind',mount['source'],mount['destination']]
    return out+['--','/runtime/bin/probe']


def supervise(argv, cwd, *, wall, cpu, cap, check=lambda:None, group=None, log=None, launch=None):
    """Actual watchdog, output/CPU bounds, nice, gated attachment, kill and reap.

    group=None is useful for harmless unit workloads only. Production calls always
    pass the measured private cgroup; it kills even reparented/setsid descendants.
    """
    p.need(type(wall) in (int,float) and math.isfinite(wall) and 0<wall<=LIMITS['wall_seconds'], 'WALL_BUDGET')
    p.need(type(cpu) is int and 1<=cpu<=LIMITS['cpu_seconds'] and 1<=cap<=LIMITS['output_max_bytes'], 'CPU_OUTPUT_BUDGET')
    check(); start=time.monotonic(); output=bytearray(); tracked={}; child=None;error=None;code=None
    read_gate,write_gate=os.pipe(); old=os.umask(0o077)
    try:
        child=subprocess.Popen([launch or sys.executable,'-I','-S','-B',str(WORKER),str(read_gate),str(cpu),*argv],
            cwd=cwd,env={'PATH':'/usr/bin:/bin','LC_ALL':'C','HOME':'/nonexistent'},
            stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,
            start_new_session=True,close_fds=True,pass_fds=(read_gate,))
        os.close(read_gate);read_gate=None
        if group:group.attach(child.pid)
        os.write(write_gate,b'1');os.close(write_gate);write_gate=None
        with selectors.DefaultSelector() as selector:
            os.set_blocking(child.stdout.fileno(),False);selector.register(child.stdout,selectors.EVENT_READ)
            while selector.get_map() or child.poll() is None:
                tracked.update(process.descendants(child.pid));check()
                p.need(time.monotonic()-start<wall,'WALL_TIMEOUT')
                if group:p.need(group.cpu_seconds()-group.start_cpu<cpu,'GROUP_CPU_BUDGET')
                for key,_ in selector.select(.1):
                    data=os.read(key.fd,16384)
                    if not data:selector.unregister(key.fileobj);continue
                    available=cap-len(output);output.extend(data[:available])
                    p.need(len(data)<=available,'OUTPUT_LIMIT')
            code=child.wait(timeout=1);p.need(code==0,'BUILD_PROCESS_NONZERO')
    except BaseException as exc:error=exc
    finally:
        os.umask(old)
        for fd in (read_gate,write_gate):
            if fd is not None:os.close(fd)
        if child:
            tracked.update(process.descendants(child.pid))
            if group:
                try:group.kill()
                except OSError:error=Refused('CGROUP_KILL_UNVERIFIED')
            with contextlib.suppress(ProcessLookupError):os.killpg(child.pid,signal.SIGKILL)
            for pid,stamp in tracked.items():
                if pid!=child.pid and process.still_present(pid,stamp):
                    with contextlib.suppress(ProcessLookupError):os.kill(pid,signal.SIGKILL)
            child.wait(timeout=3);child.stdout.close()
            deadline=time.monotonic()+3
            while group and not group.empty() and time.monotonic()<deadline:time.sleep(.02)
            if group and not group.empty():error=Refused('CGROUP_CLEANUP_UNVERIFIED')
        if log is not None:
            with os.fdopen(os.open(log,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600),'wb') as f:f.write(output)
    receipt={'elapsed_seconds':time.monotonic()-start,'bytes':len(output),'exit_code':code,
             'direct_child_reaped':child is not None and child.poll() is not None,
             'cgroup_empty':group.empty() if group else 'UNVERIFIED_NO_CGROUP_SYNTHETIC_ONLY',
             'error':str(error) if error else None}
    if error:
        error.receipt=receipt;raise error
    return bytes(output),receipt


def revalidate(plan):
    p.need(plan['version']=='controlled-build-037-v1' and plan['base']==BASE and plan['commands']==commands()
           and plan['source']['commit']==prep.COMMIT and plan['source']['tree']==prep.TREE, 'PLAN_SCOPE')
    p.need(plan['limits']==LIMITS and plan['environment']==ENVIRONMENT, 'FIXED_REVIEWED_BUDGET_REQUIRED')
    p.need(plan['tools']==tools_inventory(), 'TOOLCHAIN_CHANGED')
    p.need(plan['host']['boot_id']==Path('/proc/sys/kernel/random/boot_id').read_text().strip()
           and plan['host']['uid']==os.getuid(), 'HOST_CHANGED')
    p.need(p.hash_file(Path(plan['config']['toolchain_evidence']))[0]==plan['toolchain_evidence_sha256'], 'TOOLCHAIN_REVIEW_CHANGED')
    validate_system(plan['system_libraries']);budget_check(plan);health(plan)
    root=Path(plan['job']);p.secure(root)
    for name in ('source','build','stage','home','tmp','evidence'):p.secure(root/name)
    for protected in [plan['config']['source'],plan['config']['health_file'],*plan['config']['protected_roots']]:
        path=Path(protected).resolve();p.need(not path.is_relative_to(root) and not root.is_relative_to(path),'PROTECTED_JOB_OVERLAP')
    for protected in [plan['config']['source'],*plan['config']['protected_roots']]:p.need(not Path(protected).resolve().is_relative_to('/usr'),'PROTECTED_UNDER_TOOLCHAIN_MOUNT')
    for e in plan['source']['entries']:
        path=p.secure(root/'source'/e['path']);p.need(hashlib.sha256(path.read_bytes()).hexdigest()==e['sha256'], 'EXPORTED_SOURCE_CHANGED')
    p.need({str(f.relative_to(root/'source')) for f in (root/'source').rglob('*') if f.is_file()}=={e['path'] for e in plan['source']['entries']}, 'FOREIGN_EXPORTED_SOURCE')


def qualify(plan):
    with single_executor(plan['config']['cgroup_parent']):return _qualify(plan)


def execute(plan,approval):
    with single_executor(plan['config']['cgroup_parent']):return _execute(plan,approval)


def _qualify(plan):
    """Measure exact build mounts/controls with harmless Python, never compiler."""
    revalidate(plan);job=Path(plan['job']);proof={};scope=prep.digest(plan)
    # Probe actual namespace, read-only source, inaccessible host sentinel, no credentials.
    secret=job/'evidence'/('host-only-'+secrets.token_hex(6));secret.write_text('HOST_ONLY');secret.chmod(0o600)
    probe="""import json,os,socket,resource
checks={}
checks['network_namespace_distinct']=os.readlink('/proc/self/ns/net')!=PARENT
checks['pid_namespace_distinct']=os.readlink('/proc/self/ns/pid')!=PARENTPID
checks['readonly_toolchain']=any(l.split()[4]=='/usr' and 'ro' in l.split()[5].split(',') for l in open('/proc/self/mountinfo'))
checks['protected_roots_hidden']=all(not os.path.exists(p) for p in PROTECTED)
checks['only_loopback']=all(l.split(':')[0].strip()=='lo' for l in open('/proc/net/dev') if ':' in l)
checks['host_file_hidden']=not os.path.exists(SECRET)
checks['no_credentials']='OWNER_TEST_SECRET' not in os.environ and not os.path.exists('/home') and not os.path.exists('/root')
checks['source_readonly']=any(l.split()[4]=='/job/source' and 'ro' in l.split()[5].split(',') for l in open('/proc/self/mountinfo'))
checks['nice']=os.getpriority(os.PRIO_PROCESS,0)>=10
checks['single_cpu_affinity']=len(os.sched_getaffinity(0))==1
for d in ('build','stage','home','tmp'):
 p='/job/'+d+'/probe';open(p,'x').close();os.unlink(p)
checks['private_writes']=True
for family,address,key in ((socket.AF_INET,'127.0.0.1','ipv4'),(socket.AF_INET6,'::1','ipv6')):
 try:
  s=socket.socket(family);s.settimeout(.1);s.connect((address,9));s.close();checks[key]=False
 except OSError:checks[key]=True
print(json.dumps(checks))
"""
    probe='PARENT='+repr(os.readlink('/proc/self/ns/net'))+'\nPARENTPID='+repr(os.readlink('/proc/self/ns/pid'))+'\nPROTECTED='+repr([plan['config']['source'],*plan['config']['protected_roots']])+'\nSECRET='+repr(str(secret))+'\n'+probe
    result={'version':'build-qualification-037-v1','plan_sha256':scope,'qualified':False,'gates':GATES,'measured_at':int(time.time()),'measured_monotonic':time.monotonic()}
    try:
        with containment.Canaries(secrets.token_hex(24)) as canary, BuildCgroup(plan['config']['cgroup_parent']) as group:
            canary.positive(); counts=list(canary.counts)
            probe += '\nPORTS='+repr([s.getsockname()[1] for s in canary.sockets])+'\nCHALLENGE='+repr(canary.challenge)+'''
for family,kind,address,index in ((socket.AF_INET,socket.SOCK_STREAM,'127.0.0.1',0),(socket.AF_INET6,socket.SOCK_STREAM,'::1',1),(socket.AF_INET,socket.SOCK_DGRAM,'127.0.0.1',2)):
 try:
  with socket.socket(family,kind) as s:
   s.settimeout(.2);s.connect((address,PORTS[index]));s.sendall(CHALLENGE);s.recv(256)
  raise SystemExit(91)
 except OSError:pass
'''
            raw,receipt=supervise(sandbox(plan,['/usr/bin/python3','-I','-S','-B','-c',probe]),job,wall=30,cpu=10,cap=16384,
                check=lambda:health(plan),group=group,log=job/'evidence'/'qualification-probe.log',launch=plan['tools']['python']['resolved'])
            proof=json.loads(raw);p.need(all(v is True for v in proof.values()),'SANDBOX_PROBE_FAILED')
            p.need(canary.counts==counts,'PARENT_CANARY_REACHED');canary.positive()
            p.need(all(b-a==1 for a,b in zip(counts,canary.counts)),'CANARY_POST_CONTROL')
            proof['local_canaries_parent_positive_child_denied']=True
            result.update(checks=proof,process=receipt,cgroup=group.evidence())
            # Real contained tool versions, not user-supplied version assertions.
            versions={}
            for name in ('cmake','cc','cxx','make','linker','python','bwrap'):
                raw,_=supervise(sandbox(plan,[plan['tools'][name]['path'],'--version']),job,wall=10,cpu=5,cap=32768,
                    check=lambda:health(plan),group=group,launch=plan['tools']['python']['resolved'])
                versions[name]=raw.decode(errors='replace')
            _,runtime_receipt=supervise(resolution_probe(plan),job,wall=10,cpu=5,cap=4096,check=lambda:health(plan),group=group,launch=plan['tools']['python']['resolved'])
            proof['explicit_file_only_system_resolution']=runtime_receipt['exit_code']==0
            # Harmless setsid child: timeout must kill/reap the whole owned scope.
            detached="""import os,time
r,w=os.pipe()
pid=os.fork()
if pid==0:
 os.close(r);os.setsid();os.write(w,b'1');os.close(w);time.sleep(60);os._exit(0)
os.close(w)
assert os.read(r,1)==b'1'
os.close(r)
print('DETACHED_CHILD_READY',flush=True)
time.sleep(60)
"""
            try:
                supervise(sandbox(plan,['/usr/bin/python3','-I','-S','-B','-c',detached]),job,wall=2,cpu=5,cap=4096,
                    check=lambda:health(plan),group=group,log=job/'evidence'/'qualification-descendant.log',launch=plan['tools']['python']['resolved'])
                raise Refused('EXPECTED_WATCHDOG_NOT_TRIGGERED')
            except Refused as exc:
                p.need(str(exc)=='WALL_TIMEOUT' and exc.receipt['direct_child_reaped'] and exc.receipt['cgroup_empty'] is True,
                       'DESCENDANT_CLEANUP_PROBE_FAILED')
                p.need((job/'evidence'/'qualification-descendant.log').read_bytes()==b'DETACHED_CHILD_READY\n','DETACHED_CHILD_NOT_PROVEN')
                result['descendant_timeout_probe']=exc.receipt
                proof['setsid_descendant_timeout_and_cgroup_empty']=True
            result.update(qualified=True,versions=versions,runtime_resolution_probe=runtime_receipt)
    except (OSError,Refused,ValueError) as exc:result.update(qualified=False,blocker=str(exc))
    finally:secret.unlink()
    # Keep failures too; never replace a previous qualification/run silently.
    new_json(job/'qualification.json',result);return result


def warnings_check(raw):
    text=raw.decode('utf-8',errors='replace')
    p.need('Manually-specified variables were not used' not in text and
           'Downloading' not in text and 'Performing download step' not in text and 'Fetching ' not in text and
           'Performing update step' not in text and 'falling back' not in text.lower() and
           'provisioning failed; embedding stale' not in text, 'CONFIGURE_UNUSED_SECURITY_FLAG_OR_FALLBACK')


def cache_check(job):
    cache=Path(job)/'build/CMakeCache.txt'
    with cache.open('rb') as f:data=f.read(2*1024**2+1)
    p.need(len(data)<=2*1024**2,'CACHE_SIZE_LIMIT');text=data.decode();values={}
    for line in text.splitlines():
        if not line or line.startswith(('#','//')) or '=' not in line or ':' not in line:continue
        key,value=line.split('=',1);values[key.split(':',1)[0]]=value
    for key,value in prep.FLAGS.items():p.need(values.get(key)==value,'CACHE_FLAG_MISMATCH:'+key)


def _execute(plan, approval):
    """One exact plan invocation, consumed before first configure. No retries."""
    job=Path(plan['job']);p.secure(job)
    lock=os.open(job/'.executor.lock',os.O_WRONLY|os.O_CREAT|os.O_NOFOLLOW,0o600)
    try:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);revalidate(plan)
        q=read_json(job/'qualification.json')
        p.need(q.get('qualified') is True and q['plan_sha256']==prep.digest(plan) and 0<=time.time()-q['measured_at']<=1800
               and 0<=time.monotonic()-q['measured_monotonic']<=1800,'FRESH_QUALIFICATION_REQUIRED')
        p.need(set(approval)=={'version','plan_sha256','qualification_sha256','owner_review_ref','expires_at','one_attempt','inference'},'APPROVAL_FIELDS')
        p.need(approval['version']=='owner-build-037-v1' and approval['plan_sha256']==prep.digest(plan)
               and approval['qualification_sha256']==prep.digest(q) and approval['owner_review_ref']
               and approval['one_attempt'] is True and approval['inference']=='HOLD'
               and type(approval['expires_at']) is int and 0<approval['expires_at']-time.time()<=1800, 'OWNER_APPROVAL_SCOPE')
        p.need(not (job/'STOP').exists() and not any((job/n).exists() for n in ('attempt.json','result.json')), 'ONE_SHOT_OR_STOP')
        p.need(not any((job/'build').iterdir()) and not any((job/'stage').iterdir()), 'CLEAN_BUILD_STAGE_REQUIRED')
        # Spend attempt only after containment creation, but before any configure exec.
        result={'gates':GATES,'plan_sha256':prep.digest(plan),'operation':'BUILD_FAILED','steps':[]}
        started=time.monotonic()
        try:
            with BuildCgroup(plan['config']['cgroup_parent']) as group:
                new_json(job/'attempt.json',{'approval':approval,'started_at':int(time.time())})
                def guard():
                    p.need(not (job/'STOP').exists(),'OWNER_STOP');health(plan)
                    p.need(__import__('shutil').disk_usage(job).free>=1024**3,'DISK_RESERVE_STOP')
                for index,argv in enumerate(plan['commands']):
                    p.need(plan['tools']==tools_inventory(),'TOOLCHAIN_CHANGED')
                    remaining=LIMITS['wall_seconds']-(time.monotonic()-started)
                    p.need(remaining>0,'TOTAL_WALL_BUDGET')
                    raw,receipt=supervise(sandbox(plan,argv),job,wall=remaining,cpu=LIMITS['cpu_seconds'],
                        cap=LIMITS['output_max_bytes'],check=guard,group=group,
                        log=job/'evidence'/('configure.log' if index==0 else 'build.log'),launch=plan['tools']['python']['resolved'])
                    result['steps'].append(receipt);warnings_check(raw)
                    if index==0:cache_check(job)
                result['artifacts']=stage(plan);result['operation']='LOCAL_BUILD_PASS_INFERENCE_HOLD'
        except (OSError,Refused,ValueError) as exc:
            result['operation']='BUILD_FAILED';result['blocker']=str(exc)
            if hasattr(exc,'receipt'):result['failure_process']=exc.receipt
        finally:
            result['elapsed_seconds']=time.monotonic()-started;new_json(job/'result.json',result)
        return result
    finally:os.close(lock)


def stage(plan):
    """Copy only newly compiled ELF library candidates; no original binaries."""
    root=Path(plan['job']);build=root/'build/bin';dest=root/'stage'
    p.need(build.is_dir() and not any(dest.iterdir()),'NEW_ARTIFACT_STAGE_REQUIRED')
    (dest/'bin').mkdir(mode=0o700);(dest/'lib').mkdir(mode=0o700)
    candidates=sorted(build.iterdir());p.need(len(candidates)<=128,'BUILD_ARTIFACT_COUNT')
    p.need(sum(f.stat().st_size for f in candidates if f.is_file())<=512*1024**2,'STAGE_SIZE_BUDGET')
    for path in candidates:
        health(plan)
        if path.name!='llama-cli' and '.so' not in path.name:continue
        target=dest/('bin' if path.name=='llama-cli' else 'lib')/path.name
        if path.is_symlink():
            link=os.readlink(path);p.need('/' not in link and link not in ('.','..'),'ARTIFACT_LINK_ESCAPE')
            p.need(path.resolve().parent==build.resolve(),'ARTIFACT_LINK_ESCAPE');target.symlink_to(link)
        else:
            p.secure(path);sha,_=p.hash_file(path);p.elf(path,sha)
            with path.open('rb') as src:
                with target.open('xb') as out:__import__('shutil').copyfileobj(src,out,1024**2)
            target.chmod(0o500 if path.name=='llama-cli' else 0o400)
            p.need(p.hash_file(target)[0]==sha,'STAGE_HASH')
    return verify_runtime(dest,plan['system_libraries'])


def verify_runtime(root,system):
    """Separate explicit reviewed system mounts from $ORIGIN private closure."""
    root=p.secure(Path(root));trusted=validate_system(system);local={};aliases={}
    for path in sorted(root.rglob('*')):
        if path.is_symlink():
            p.need(not Path(os.readlink(path)).is_absolute(),'ABSOLUTE_ARTIFACT_LINK')
            target=path.resolve(strict=True);p.need(target.is_relative_to(root),'ARTIFACT_LINK_ESCAPE')
            aliases[str(path.relative_to(root))]=str(target.relative_to(root));continue
        if path.is_dir():continue
        p.secure(path);sha,size=p.hash_file(path);meta=passive_elf(path,sha);prep.check_search(root,path,meta['paths'])
        meta.update(sha256=sha,size=size);local[str(path.relative_to(root))]=meta
    p.need('bin/llama-cli' in local,'CLI_MISSING')
    for name,target in aliases.items():p.need(target in local,'UNKNOWN_LINK_TARGET')
    for name,meta in local.items():
        for dependency in meta['needed']:
            p.need('/' not in dependency and dependency not in ('','.','..'),'NEEDED_NAME')
            matches=[]
            for paths in meta['paths']:
                for search in paths.split(':'):
                    candidate=(root/name).parent/search[len('$ORIGIN'):].lstrip('/')/dependency
                    if candidate.exists():
                        key=str(candidate.resolve().relative_to(root));p.need(key in local,'UNKNOWN_PRIVATE_DEPENDENCY');matches.append(key)
            if matches:
                p.need(len(set(matches))==1 and dependency not in trusted,'AMBIGUOUS_SYSTEM_PRIVATE')
                p.need(local[matches[0]]['soname']==dependency,'PRIVATE_SONAME_MISMATCH')
            else:p.need(dependency in trusted,'NO_SYSTEM_FALLBACK:'+dependency)
        if meta['interpreter']:
            loader=Path(meta['interpreter']).resolve();p.need(any(str(loader)==e['path'] for e in trusted.values()),'INTERPRETER_NOT_EXPLICIT')
    p.need(local['bin/llama-cli']['interpreter'],'DYNAMIC_INTERPRETER_REQUIRED')
    return {'local':local,'aliases':aliases,'explicit_system_mounts':list(trusted.values()),
            'provenance':'LOCAL_BUILD_ATTESTATION_NOT_REPRODUCIBLE_OR_UPSTREAM',
            'runtime_system_mount_contract':runtime_mounts(system,local['bin/llama-cli']['interpreter']),
            'runtime_execution':'HOLD','model_publisher_evidence':'UNVERIFIED','gates':GATES}


def target_inputs(directory,review_ref,*,apply=False):
    """Read installed package DB and existing files only; never install/download."""
    root=Path(directory);p.secure(root.parent)
    p.need(root.is_absolute() and not root.exists() and not root.is_symlink(),'NEW_INPUT_DIRECTORY')
    packages=('gcc','g++','cmake','make','binutils','libc6','libstdc++6','libgcc-s1','python3','bubblewrap')
    raw,_=process.run(['/usr/bin/dpkg-query','-W','-f=${Package}\t${Version}\n',*packages],
                      env={'PATH':'/usr/bin:/bin','LC_ALL':'C','HOME':'/nonexistent'},cwd=root.parent,timeout=10,cap=8192)
    versions=dict(line.split('\t',1) for line in raw.decode().splitlines())
    licenses={}
    for package in packages:
        copyright=Path('/usr/share/doc')/package/'copyright'
        p.need(copyright.exists(),'PACKAGE_COPYRIGHT_MISSING:'+package)
        copyright=copyright.resolve();p.secure(copyright)
        licenses[package]={'path':str(copyright),'sha256':p.hash_file(copyright)[0],
                           'status':'LOCAL_DOCUMENT_REQUIRES_OWNER_REVIEW'}
    evidence={'packages':versions,'licenses':licenses,'review_ref':review_ref,
              'tools':tools_inventory(),'origin':'LOCAL_PACKAGE_DATABASE_NOT_UPSTREAM_AUTHENTICATION'}
    entries=[]
    for name,package in (('libc.so.6','libc6'),('libm.so.6','libc6'),('libstdc++.so.6','libstdc++6'),
                         ('libgcc_s.so.1','libgcc-s1'),('ld-linux-x86-64.so.2','libc6')):
        path=(Path('/usr/lib/x86_64-linux-gnu')/name).resolve(strict=True)
        entries.append({'name':name,'path':str(path),'sha256':p.hash_file(path)[0],
                        'version':versions[package],'license':'SEE_LOCAL_COPYRIGHT_REVIEW',
                        'license_ref':licenses[package]['path']+'#sha256='+licenses[package]['sha256']})
    system={'version':'reviewed-system-037-v1','review_ref':review_ref,'entries':entries}
    validate_system(system)
    output={'toolchain.json':evidence,'system-libraries.json':system}
    if apply:
        old=os.umask(0o077)
        try:
            root.mkdir(mode=0o700)
            for name,value in output.items():new_json(root/name,value)
        finally:os.umask(old)
    return {'operation':'INPUTS_WRITTEN' if apply else 'INPUTS_DRY_RUN','directory':str(root),
            'files':output,'review_semantics':'OWNER_DECLARATION_NOT_INDEPENDENT_REPRODUCIBILITY','gates':GATES}


def monitor(status_file,health_file,recorder_id,collection_key,healthy_key,stable_key,*,seconds=7500,stop_file=None,measurement_key='measured_at'):
    """Read-only adapter for an existing owner-reviewed external status JSON.

    Never invent collection timestamps or stable/healthy booleans. Stale last
    collection stays stale even when measured_at advances. No recorder DB access.
    """
    p.need(type(seconds) is int and 1<=seconds<=7500,'MONITOR_BUDGET')
    source=p.secure(Path(status_file));dest=Path(health_file);p.secure(dest.parent)
    p.need(not dest.exists() and not dest.is_symlink() and source!=dest,'NEW_HEALTH_FILE_REQUIRED')
    start=time.monotonic();identity=None
    while True:
        if stop_file and Path(stop_file).exists():break
        status=read_json(source,16384)
        p.need(type(status.get(collection_key)) is int and type(status.get(healthy_key)) is bool
               and type(status.get(stable_key)) is bool and type(status.get(measurement_key)) is int,'EXTERNAL_STATUS_SCHEMA')
        value={'version':'external-recorder-health-037-v1','recorder_id':recorder_id,
               'measured_at':status[measurement_key],'last_collection_at':status[collection_key],
               'healthy':status[healthy_key],'desktop_stable':status[stable_key],
               'origin':'READ_ONLY_OWNER_DECLARED_STATUS_FIELD_MAPPING'}
        if identity is None:
            new_json(dest,value);st=dest.lstat();identity=(st.st_dev,st.st_ino)
        else:
            st=dest.lstat();p.need(not dest.is_symlink() and (st.st_dev,st.st_ino)==identity,'HEALTH_FILE_REPLACED')
            temp=dest.parent/('.health-037-'+secrets.token_hex(12));new_json(temp,value)
            # Same-UID hostile concurrent writers remain outside the owner-side model.
            os.replace(temp,dest);st=dest.lstat();identity=(st.st_dev,st.st_ino)
        if time.monotonic()-start>=seconds:break
        time.sleep(min(5,max(0,seconds-(time.monotonic()-start))))
    return {'operation':'MONITOR_STOPPED_HEALTH_WILL_EXPIRE','gates':GATES}


def approval_record(plan,review_ref,output):
    """Explicit OWNER action after review; no digital-signature/authenticity claim."""
    revalidate(plan);q=read_json(Path(plan['job'])/'qualification.json')
    p.need(q.get('qualified') is True and q.get('plan_sha256')==prep.digest(plan),'QUALIFICATION_REQUIRED')
    p.need(type(review_ref) is str and review_ref.strip(),'EXPLICIT_OWNER_REVIEW_REF')
    value={'version':'owner-build-037-v1','plan_sha256':prep.digest(plan),
           'qualification_sha256':prep.digest(q),'owner_review_ref':review_ref,
           'expires_at':int(time.time())+900,'one_attempt':True,'inference':'HOLD'}
    path=Path(output);p.secure(path.parent);new_json(path,value)
    return {'operation':'EXPLICIT_OWNER_APPROVAL_RECORDED_NOT_EXECUTED','approval':str(path),**value}


def preflight(config):
    """Read-only compatibility survey. Never qualifies namespaces or changes system state."""
    checks={}
    def check(name,operation):
        try:checks[name]={'status':'PASS','evidence':operation()}
        except (OSError,ValueError,TypeError,KeyError,Refused,struct.error) as exc:
            checks[name]={'status':'HOLD','reason':str(exc)}
    def schema():
        p.need(set(config)==CONFIG_FIELDS,'CONFIG_FIELDS');return 'UNCHANGED_CONFIG_SCHEMA'
    check('config_schema',schema)
    check('memory',lambda:memory.snapshot(config['cgroup_parent']))
    if checks['memory']['status']=='PASS':
        capacity=checks['memory']['evidence']
        if capacity['status']!='PASS' or capacity['available_bytes']<LIMITS['available_ram_min_bytes']:
            checks['memory']['status']='HOLD';checks['memory']['reason']='RAM_HEADROOM_HOLD'
    check('cpu',prep.compatibility)
    check('toolchain',tools_inventory)
    check('system_libraries',lambda:validate_system(read_json(config['system_libraries'])))
    def inputs():
        value=read_json(config['toolchain_evidence'])
        p.need(value.get('packages') and value.get('licenses') and value.get('review_ref'),'TOOLCHAIN_REVIEW_REQUIRED')
        return {'review_ref':value['review_ref'],'sha256':p.hash_file(Path(config['toolchain_evidence']))[0]}
    check('existing_toolchain_evidence',inputs)
    def paths():
        job=Path(config['job']);p.secure(job.parent)
        p.need(job.is_absolute() and job==job.resolve() and not job.exists() and not job.is_symlink(),'NEW_PRIVATE_JOB_REQUIRED')
        for value in [config['source'],config['health_file'],*config['protected_roots']]:
            path=Path(value);p.need(path.is_absolute(),'ABSOLUTE_INPUT_REQUIRED');path=path.resolve()
            p.need(not job.is_relative_to(path) and not path.is_relative_to(job),'PROTECTED_JOB_OVERLAP')
        for value in [config['source'],*config['protected_roots']]:
            p.need(not Path(value).resolve().is_relative_to('/usr'),'PROTECTED_UNDER_TOOLCHAIN_MOUNT')
        free=__import__('shutil').disk_usage(job.parent).free
        p.need(free>=LIMITS['disk_free_min_bytes'],'DISK_HEADROOM_HOLD')
        return {'job':str(job),'disk_free_bytes':free,'source_content_verification':'DEFERRED_TO_PREPARE'}
    check('paths_and_disk',paths)
    def delegation():
        parent=Path(config['cgroup_parent']);root=Path('/sys/fs/cgroup').resolve()
        p.need(parent.is_absolute() and parent==parent.resolve() and parent.is_relative_to(root) and parent!=root,'DELEGATED_CGROUP_REQUIRED')
        p.need(parent.stat().st_uid==os.getuid(),'CGROUP_OWNERSHIP')
        enabled=set((parent/'cgroup.subtree_control').read_text().split())
        p.need({'cpu','memory','pids'}<=enabled,'CONTROLLERS_NOT_DELEGATED')
        p.need(os.access(parent,os.W_OK),'CGROUP_NOT_WRITABLE')
        p.need(not list(parent.glob('boss-035-*')),'PREVIOUS_PRIVATE_SCOPE_REVIEW_REQUIRED')
        return {'enabled':sorted(enabled),'write_access_flag':True,'child_creation_limit_readback_kill_and_lock':'UNVERIFIED_UNTIL_QUALIFY'}
    check('delegation_readiness',delegation)
    check('recorder_health',lambda:health({'config':config}))
    checks['actual_containment']={'status':'UNVERIFIED','reason':'REQUIRES_EXISTING_HARMLESS_QUALIFY_NO_STATE_CHANGED'}
    checks['configure_flags_and_runtime_loader']={'status':'UNVERIFIED','reason':'SOURCE_REVIEWED_FLAGS_REQUIRE_APPROVED_CONFIGURE_AND_CONTAINED_LOADER_PROBE'}
    return {'operation':'READ_ONLY_PREFLIGHT','checks':checks,
            'readiness':'HOLD' if any(v['status']=='HOLD' for v in checks.values()) else 'READY_FOR_HARMLESS_QUALIFICATION_REVIEW',
            'qualified':False,'writes':0,'limits':LIMITS,'gates':GATES}


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='action',required=True)
    a=sub.add_parser('approve');a.add_argument('--plan',required=True);a.add_argument('--review-ref',required=True);a.add_argument('--output',required=True)
    a=sub.add_parser('monitor');a.add_argument('--status-file',required=True);a.add_argument('--health-file',required=True);a.add_argument('--recorder-id',required=True)
    a.add_argument('--collection-key',required=True);a.add_argument('--healthy-key',required=True);a.add_argument('--stable-key',required=True);a.add_argument('--seconds',type=int,default=7500);a.add_argument('--stop-file');a.add_argument('--measurement-key',default='measured_at')
    a=sub.add_parser('inputs');a.add_argument('--directory',required=True);a.add_argument('--review-ref',required=True);a.add_argument('--apply',action='store_true')
    a=sub.add_parser('preflight');a.add_argument('--config',required=True)
    a=sub.add_parser('prepare');a.add_argument('--config',required=True);a.add_argument('--apply',action='store_true')
    for action in ('qualify','build','stop','status'):
        a=sub.add_parser(action);a.add_argument('--plan',required=True)
        if action=='build':a.add_argument('--approval',required=True)
    a=sub.add_parser('rollback');a.add_argument('--job',required=True);a.add_argument('--receipt-sha256',required=True);a.add_argument('--apply',action='store_true')
    args=parser.parse_args(argv)
    previous=signal.getsignal(signal.SIGTERM)
    def interrupted(signum,frame):raise Refused('SUPERVISOR_TERMINATED')
    signal.signal(signal.SIGTERM,interrupted)
    try:
        if args.action=='approve':result=approval_record(read_json(args.plan),args.review_ref,args.output)
        elif args.action=='monitor':result=monitor(args.status_file,args.health_file,args.recorder_id,args.collection_key,args.healthy_key,args.stable_key,seconds=args.seconds,stop_file=args.stop_file,measurement_key=args.measurement_key)
        elif args.action=='inputs':result=target_inputs(args.directory,args.review_ref,apply=args.apply)
        elif args.action=='preflight':result=preflight(read_json(args.config))
        elif args.action=='prepare':result=prepare(read_json(args.config),apply=args.apply)
        elif args.action=='rollback':result=prep.rollback(args.job,args.receipt_sha256,apply=args.apply)
        else:
            plan=read_json(args.plan);p.need(str(Path(args.plan))==str(Path(plan['job'])/'plan.json'),'PLAN_PATH_BINDING')
            if args.action=='qualify':result=qualify(plan)
            elif args.action=='build':result=execute(plan,read_json(args.approval))
            elif args.action=='stop':new_json(Path(plan['job'])/'STOP',{'owner_stop':True});result={'operation':'STOP_REQUESTED'}
            else:result={'plan_sha256':prep.digest(plan),'gates':GATES,'source_commit':plan['source']['commit'],'limits':plan['limits']}
        print(json.dumps(result,indent=2,sort_keys=True))
        failed=(result.get('operation')=='BUILD_FAILED' or result.get('readiness')=='HOLD'
                or result.get('qualified') is False and result.get('operation')!='READ_ONLY_PREFLIGHT')
        return 2 if failed else 0
    except (OSError,ValueError,KeyError,Refused,struct.error) as exc:
        print(json.dumps({'operation':'REFUSED','reason':str(exc),'gates':GATES},sort_keys=True));return 2
    finally:signal.signal(signal.SIGTERM,previous)


if __name__=='__main__':raise SystemExit(main())
