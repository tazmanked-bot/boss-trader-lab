"""PINNED SYNTHETIC WORKER ONLY. No GGUF/model loading or order paths."""
import json
import os
import resource
import signal
import socket
import sys
import time


def limits(filesystem_probe=False):
    os.umask(0o077);os.nice(10)
    for key,cap in ((resource.RLIMIT_AS,4*1024**3),(resource.RLIMIT_CPU,30),(resource.RLIMIT_NOFILE,32),(resource.RLIMIT_CORE,0),(resource.RLIMIT_FSIZE,4096 if filesystem_probe else 0)):
        _,hard=resource.getrlimit(key);cap=cap if hard<0 else min(cap,hard);resource.setrlimit(key,(cap,cap))


def denied_tcp(address,port,family):
    try:
        with socket.socket(family,socket.SOCK_STREAM) as s:s.settimeout(.3);s.connect((address,port))
        return False
    except OSError:return True


def analysis(reference):
    return {'version':'analyst-v1','hypothesis':'SYNTHETIC STUB; no AI inference.',
            'evidence_refs':[reference],'strongest_objection':'No genuine reasoning was executed.',
            'missing_information':[],'invalidation':'Eligible retest low breached','disposition':'SUPPORT'}


def probe(config):
    checks={}
    checks['network_namespace_distinct']=os.readlink('/proc/self/ns/net')!=config['parent_netns']
    interfaces=[line.split(':')[0].strip() for line in open('/proc/net/dev') if ':' in line]
    checks['only_loopback_interface']=set(interfaces)<= {'lo'}
    checks['ipv4_denied']=denied_tcp('127.0.0.1',config['ipv4_port'],socket.AF_INET)
    checks['ipv6_denied']=denied_tcp('::1',config['ipv6_port'],socket.AF_INET6)
    try:
        with socket.socket(socket.AF_INET,socket.SOCK_DGRAM) as s:
            s.settimeout(.3);s.sendto(config['challenge'].encode(),('127.0.0.1',config['dns_port']));s.recvfrom(256)
        checks['dns_canary_denied']=False
    except OSError:checks['dns_canary_denied']=True
    try:socket.getaddrinfo('boss-035.invalid',443);checks['resolver_denied']=False
    except OSError:checks['resolver_denied']=True
    try:open(config['forbidden_file']).read();checks['private_host_read_denied']=False
    except OSError:checks['private_host_read_denied']=True
    if os.path.exists('/bundle'):
        checks['bundle_readonly_mount']=any(line.split()[4]=='/bundle' and 'ro' in line.split()[5].split(',') for line in open('/proc/self/mountinfo'))
    checks['readonly_positive']=open('/readonly').read()==config['challenge']
    try:
        with open('/readonly','a') as f:f.write('MUST_NOT_WRITE')
        checks['readonly_write_denied']=False
    except OSError:checks['readonly_write_denied']=True
    with open('/work/scratch-test','x') as f:f.write(config['challenge'])
    checks['scratch_writable']=open('/work/scratch-test').read()==config['challenge'];os.unlink('/work/scratch-test')
    resource.setrlimit(resource.RLIMIT_FSIZE,(0,0));signal.signal(signal.SIGXFSZ,signal.SIG_IGN)
    try:
        with open('/work/limit-test','x') as f:f.write('x')
        checks['zero_file_limit_enforced']=False
    except OSError:checks['zero_file_limit_enforced']=True
    if os.path.exists('/work/limit-test'):os.unlink('/work/limit-test')
    child=os.fork()
    if child==0:time.sleep(2);os._exit(0)
    os.kill(child,signal.SIGTERM);waited,_=os.waitpid(child,0)
    checks['child_descendant_reaped']=waited==child
    checks['protected_roots_hidden']=all(not os.path.exists(p) or os.path.isdir(p) and not os.listdir(p) for p in config['protected_roots'])
    checks['no_secret_env']='OWNER_TEST_SECRET' not in os.environ
    checks['nice_at_least_10']=os.getpriority(os.PRIO_PROCESS,0)>=10
    checks['limits']=resource.getrlimit(resource.RLIMIT_AS)[0]<=4*1024**3 and resource.getrlimit(resource.RLIMIT_NOFILE)[0]<=32 and resource.getrlimit(resource.RLIMIT_CORE)[0]==0
    return {'mode':'ACTUAL_LOCAL_SYNTHETIC_WORKER_NOT_MODEL','checks':checks,'scope_sha256':config['scope_sha256'],
            'analysis':analysis(config['reference'])}


mode=sys.argv[1]
if mode=='limit-exec':
    # Parent attaches only this fresh child to its own delegated cgroup, then releases.
    fd=int(sys.argv[2]);os.set_blocking(fd,True)
    import select
    if not select.select([fd],[],[],2)[0] or os.read(fd,1)!=b'1':sys.exit(9)
    os.close(fd);limits(filesystem_probe=True)
    argv=sys.argv[3:]
    if os.path.basename(argv[0])!='bwrap':sys.exit(10)
    os.execve(argv[0],argv,dict(os.environ))
limits(filesystem_probe=mode=='probe')
if mode=='probe':print(json.dumps(probe(json.load(open('/config.json')))));sys.exit(0)
if mode=='hang':time.sleep(60)
if mode=='overflow':sys.stdout.write('x'*10000);sys.exit(0)
if mode=='nonzero':sys.exit(7)
if mode=='tree':
    child=os.fork()
    if child==0:time.sleep(60);sys.exit(0)
    def stop(*_):
        try:os.kill(child,signal.SIGTERM)
        except ProcessLookupError:pass
        os.waitpid(child,0);sys.exit(0)
    signal.signal(signal.SIGTERM,stop);print('child ready',flush=True);time.sleep(60)
value=analysis(sys.argv[2])
if mode=='badref':value['evidence_refs']=['invalid']
if mode=='extra':value['order']='BUY'
print(json.dumps(value))
