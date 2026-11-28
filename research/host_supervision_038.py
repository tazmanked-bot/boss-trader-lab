"""Authenticated-channel operational supervision; never a hardware stability claim.

Only serve under the owner's verified SSH session. Same-UID/root/credential-holder
forgery is outside the trust model; this is not remote hardware attestation.
"""
import argparse
import hashlib
import stat
import ipaddress
import json
import math
import os
from pathlib import Path
import re
import secrets
import select
import signal
import sys
import time
from research.qualification_035 import provision as p
from research import recorder_health_037 as recorder
from research.llama_analyst_033 import Refused

POLICY='windows-operational-supervision-038-v1'
UNCERTAINTY='UNRESOLVED_NOT_HARDWARE_SAFETY'
TTL=15
INTERVAL=5
MAX_SECONDS=7500
STATE='host-evidence.json'
WINDOWS=Path(__file__).parent/'windows_038'


def canonical(value):return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False)
def digest(value):return hashlib.sha256(canonical(value).encode()).hexdigest()
def boot_clock():return time.clock_gettime(time.CLOCK_BOOTTIME)


def read(path):
    p.secure(Path(path))
    with os.fdopen(os.open(path,os.O_RDONLY|os.O_NOFOLLOW),'rb') as stream:data=stream.read(16385)
    p.need(len(data)<=16384,'HOST_EVIDENCE_LIMIT');return recorder.strict_json(data)


def policy(config):
    value=config.get('host_supervision')
    p.need(type(value) is dict and set(value)=={'policy','directory','vm_uuid','ssh_peer','review_ref'},'HOST_POLICY_SCHEMA')
    p.need(value['policy']==POLICY and type(value['review_ref']) is str and value['review_ref'].strip(),'HOST_POLICY_REVIEW_REQUIRED')
    path=Path(value['directory']);p.need(path.is_absolute() and path==path.resolve(),'HOST_DIRECTORY_PATH')
    p.secure(path);s=path.stat();p.need(s.st_uid==os.getuid() and s.st_mode&0o777==0o700,'HOST_DIRECTORY_PRIVATE')
    p.need(bool(re.fullmatch('[0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}',value['vm_uuid'])),'VM_UUID')
    ipaddress.ip_address(value['ssh_peer'])
    for other in (config['job'],config['source'],config['health_file'],*config['protected_roots']):
        other=Path(other).resolve();p.need(not path.is_relative_to(other) and not other.is_relative_to(path),'HOST_DIRECTORY_OVERLAP')
    return value


def observer_scope(value):
    observer=value['observer']
    return {key:observer[key] for key in ('pid','start_ticks','boot_id','session','code_sha256')}


def current_observer(plan):
    value=read(plan['config']['health_file'])
    recorder.validate_evidence(value,plan['config']['recorder_id'],plan['config']['collection_cadence_seconds'])
    return value


def ssh_context(config):
    fields=os.environ.get('SSH_CONNECTION','').split()
    p.need(len(fields)==4 and fields[0]==config['ssh_peer'] and fields[3]=='22','VERIFIED_SSH_CONTEXT_REQUIRED')
    # Require an actual privileged sshd ancestor, not just caller-supplied environment.
    pid=os.getppid();found=False
    for _ in range(12):
        text=Path('/proc/'+str(pid)+'/stat').read_text();name=text.split('(',1)[1].rsplit(')',1)[0]
        rest=text.rsplit(')',1)[1].split()
        status=Path('/proc/'+str(pid)+'/status').read_text()
        uid=next(line.split()[1:] for line in status.splitlines() if line.startswith('Uid:'))
        if name in ('sshd','sshd-session') and uid==['0']*4:found=True;break
        pid=int(rest[1])
        if pid<=1:break
    p.need(found,'ROOT_SSHD_ANCESTOR_REQUIRED')
    return {'kind':'EXISTING_AUTHENTICATED_SSH','peer':fields[0],'server_port':22}


def code_hashes():
    return {name:p.hash_file(WINDOWS/name)[0] for name in ('HostSupervisor038.ps1','HostProbe038.ps1')}


def finite(value,low,high,reason):
    p.need(type(value) in (int,float) and math.isfinite(value) and low<=value<=high,reason)


class Protocol:
    """Single terminal session; each response consumes a fresh challenge."""
    def __init__(self,scope,*,mono=time.monotonic,boot=boot_clock,wall=time.time):
        self.scope=scope;self.mono=mono;self.boot=boot;self.wall=wall
        self.session=secrets.token_hex(32);self.challenge=secrets.token_hex(32);self.seq=1
        self.previous=None;self.identity=None;self.poisoned=False
        self.last=(mono(),boot(),wall())
    def envelope(self):
        return {'version':POLICY,'session':self.session,'challenge':self.challenge,'seq':self.seq,
                'plan_sha256':self.scope['plan_sha256'],'guest_boot':self.scope['guest_boot'],
                'observer_sha256':digest(self.scope['observer']), 'expected_scripts':self.scope['scripts'],
                'vm_uuid':self.scope['vm_uuid'],'interval_seconds':INTERVAL,'expiry_seconds':TTL,
                'hardware_uncertainty':UNCERTAINTY}
    def accept(self,value):
        p.need(not self.poisoned,'HOST_SESSION_TERMINAL')
        try:
            now=(self.mono(),self.boot(),self.wall())
            gaps=[a-b for a,b in zip(now,self.last)]
            p.need(all(0<=v<=TTL for v in gaps) and abs(gaps[1]-gaps[2])<=2,'GUEST_CLOCK_GAP_OR_RESUME')
            p.need(type(value) is dict and set(value)=={'version','session','challenge','seq','plan_sha256','guest_boot','observer_sha256','measurement'},'HOST_FRAME_SCHEMA')
            for key in ('version','session','challenge','seq','plan_sha256','guest_boot','observer_sha256'):
                p.need(type(value[key]) is type(self.envelope()[key]) and value[key]==self.envelope()[key],'HOST_SESSION_REPLAY_OR_SCOPE')
            measurement=value['measurement']
            keys={'platform','host_boot','host_session','host_pid','host_elapsed_ms','host_utc_ms','host_uptime_seconds',
                  'probe_duration_ms','vm_uuid','vm_state','forward_host_port','forward_guest_port','forward_host_ip','supervisor_sha256','probe_sha256','tool_sha256'}
            p.need(type(measurement) is dict and set(measurement)==keys,'HOST_MEASUREMENT_SCHEMA')
            p.need(type(measurement['vm_uuid']) is str and measurement['platform']=='Windows' and measurement['vm_state']=='running'
                   and measurement['vm_uuid'].lower()==self.scope['vm_uuid'].lower()
                   and measurement['forward_host_port']==2222 and measurement['forward_guest_port']==22
                   and measurement['forward_host_ip'] in ('','127.0.0.1'),'WINDOWS_VM_FORWARDING_REQUIRED')
            p.need(measurement['supervisor_sha256']==self.scope['scripts']['HostSupervisor038.ps1']
                   and measurement['probe_sha256']==self.scope['scripts']['HostProbe038.ps1'],'HOST_SCRIPT_REVISION')
            for key in ('host_boot','host_session'):
                p.need(type(measurement[key]) is str and 1<=len(measurement[key])<=128,'HOST_IDENTITY')
            p.need(type(measurement['host_pid']) is int and 0<measurement['host_pid']<2**32,'HOST_PID')
            finite(measurement['probe_duration_ms'],0,4000,'HOST_PROBE_BUDGET')
            for key in ('host_elapsed_ms','host_utc_ms','host_uptime_seconds'):finite(measurement[key],0,2**53,'HOST_CLOCK_VALUE')
            tools=measurement['tool_sha256']
            p.need(type(tools) is dict and set(tools)=={'ssh','powershell','virtualbox'}
                   and all(type(v) is str and re.fullmatch('[0-9a-f]{64}',v) for v in tools.values()),'HOST_TOOL_HASHES')
            identity={k:measurement[k] for k in ('host_boot','host_session','host_pid','tool_sha256','forward_host_ip','vm_uuid')}
            if self.identity is not None:p.need(identity==self.identity,'HOST_REBOOT_OR_PROCESS_CHANGE')
            if self.previous is not None:
                elapsed=(measurement['host_elapsed_ms']-self.previous['host_elapsed_ms'])/1000
                wall=(measurement['host_utc_ms']-self.previous['host_utc_ms'])/1000
                uptime=measurement['host_uptime_seconds']-self.previous['host_uptime_seconds']
                p.need(1<=elapsed<=TTL and 0<=wall<=TTL and 0<=uptime<=TTL
                       and abs(elapsed-wall)<=2 and abs(elapsed-uptime)<=2,'HOST_CLOCK_JUMP_OR_SUSPEND')
            self.identity=identity;self.previous=measurement;self.last=now
            accepted=self.seq;self.seq+=1;self.challenge=secrets.token_hex(32)
            return {'accepted_seq':accepted,'measurement':measurement,'receipt_monotonic':now[0],
                    'receipt_boottime':now[1],'receipt_wall':now[2]}
        except BaseException:self.poisoned=True;raise


class Store:
    def __init__(self,directory,*,new_session=False):self.path=Path(directory);self.fd=None;self.identity=None;self.new=new_session
    def __enter__(self):
        import fcntl
        p.secure(self.path);s=self.path.stat();p.need(s.st_uid==os.getuid() and s.st_mode&0o777==0o700,'HOST_DIRECTORY_PRIVATE')
        try:
            self.fd=os.open(self.path/'.host-038.lock',os.O_RDWR|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600);os.fchmod(self.fd,0o600)
        except FileExistsError:self.fd=os.open(self.path/'.host-038.lock',os.O_RDWR|os.O_NOFOLLOW)
        try:
            s=os.fstat(self.fd);p.need(stat.S_ISREG(s.st_mode) and s.st_uid==os.getuid() and s.st_mode&0o777==0o600,'HOST_LOCK_PERMISSIONS')
            try:fcntl.flock(self.fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
            except BlockingIOError:raise Refused('HOST_RECEIVER_BUSY') from None
            target=self.path/STATE
            if target.exists() or target.is_symlink():
                p.need(self.new,'EXPLICIT_NEW_HOST_SESSION_REQUIRED');old=read(target)
                p.need(old.get('version')==POLICY,'FOREIGN_HOST_EVIDENCE')
                live=False
                try:live=old['producer']['boot_id']==recorder.boot_id() and recorder.process_identity(old['producer']['pid'])==old['producer']['start_ticks'] and old.get('valid') is True
                except (OSError,ValueError,KeyError):pass
                p.need(not live,'OLD_HOST_RECEIVER_ALIVE')
                s=target.stat();self.identity=(s.st_dev,s.st_ino)
            return self
        except BaseException:self.__exit__();raise
    def write(self,value):
        target=self.path/STATE
        if self.identity is not None:
            s=target.lstat();p.need(not target.is_symlink() and self.identity==(s.st_dev,s.st_ino),'HOST_OUTPUT_REPLACED')
        temp=self.path/('.host-038-'+secrets.token_hex(12))
        try:
            data=(canonical(value)+'\n').encode();p.need(len(data)<=16384,'HOST_EVIDENCE_LIMIT')
            with os.fdopen(os.open(temp,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600),'wb') as f:
                os.fchmod(f.fileno(),0o600);f.write(data);f.flush();os.fsync(f.fileno())
            if self.identity is None:p._rename_new(temp,target)
            else:os.replace(temp,target)
            s=target.stat();self.identity=(s.st_dev,s.st_ino)
        finally:
            if temp.exists():temp.unlink()
    def __exit__(self,*_):
        if self.fd is not None:os.close(self.fd);self.fd=None


def binding(value):return {k:value[k] for k in ('session','scope_sha256','producer')}


def receiver_command(pid,plan):
    raw=Path('/proc/'+str(pid)+'/cmdline').read_bytes()
    p.need(len(raw)<=16384,'HOST_RECEIVER_CMDLINE_LIMIT')
    args=raw.split(b'\0')
    expected=[b'-m',b'research.host_supervision_038',b'serve']
    p.need(any(args[i:i+3]==expected for i in range(len(args))),'HOST_RECEIVER_COMMAND_BINDING')
    for key,value in ((b'--plan',str(Path(plan['job'])/'plan.json').encode()),(b'--expected-plan-sha',digest(plan).encode())):
        p.need(args.count(key)==1 and args.index(key)+1<len(args) and args[args.index(key)+1]==value,'HOST_RECEIVER_COMMAND_SCOPE')


def check(plan,health):
    try:return _check(plan,health)
    except (KeyError,TypeError,AttributeError):raise Refused('HOST_EVIDENCE_SCHEMA') from None


def _check(plan,health):
    cfg=policy(plan['config']);value=read(Path(cfg['directory'])/STATE)
    p.need(value.get('version')==POLICY and value.get('valid') is True,'HOST_SUPERVISION_LOST')
    p.need(value['scope']['plan_sha256']==digest(plan) and value['scope']['guest_boot']==recorder.boot_id()
           and value['scope']['observer']==observer_scope(health) and value['scope']['vm_uuid'].lower()==cfg['vm_uuid'].lower()
           and value['scope']['scripts']==code_hashes() and value['scope']['policy']==POLICY
           and value['scope']['transport']=={'kind':'EXISTING_AUTHENTICATED_SSH','peer':cfg['ssh_peer'],'server_port':22}
           and value['scope_sha256']==digest(value['scope']),'HOST_PLAN_BOOT_OBSERVER_MISMATCH')
    producer=value['producer']
    p.need(producer['boot_id']==recorder.boot_id() and producer['code_sha256']==p.hash_file(Path(__file__))[0],'HOST_RECEIVER_REVISION_OR_BOOT')
    try:ident=recorder.process_identity(producer['pid'])
    except (OSError,ValueError):raise Refused('HOST_RECEIVER_LOST') from None
    p.need(ident==producer['start_ticks'],'HOST_RECEIVER_PID_REUSED')
    receiver_command(producer['pid'],plan)
    for clock,key in ((time.monotonic,'receipt_monotonic'),(boot_clock,'receipt_boottime'),(time.time,'receipt_wall')):
        finite(value[key],0,2**53,'HOST_RECEIPT_CLOCK');p.need(0<=clock()-value[key]<=TTL,'HOST_HEARTBEAT_STALE_OR_RESUMED')
    p.need(not ((Path(cfg['directory'])/'STOP').exists() or (Path(cfg['directory'])/'STOP').is_symlink()),'HOST_OWNER_STOP')
    return {'policy':POLICY,'binding':binding(value),'seq':value['accepted_seq'],
            'hardware_uncertainty':UNCERTAINTY,'physical_hardware_verified':False,'scope':value['scope']}


def prove(plan,seconds=16):
    p.need(type(seconds) is int and 15<=seconds<=30,'HOST_PROOF_DURATION')
    started=boot_clock();first=None;seen=set()
    while boot_clock()-started<seconds:
        health=current_observer(plan);current=check(plan,health)
        if first is None:first=current
        p.need(current['binding']==first['binding'],'HOST_SESSION_CHANGED_DURING_PROOF')
        seen.add(current['seq']);time.sleep(.2)
    p.need(len(seen)>=3,'HOST_THREE_HEARTBEATS_REQUIRED')
    return {'mode':'HARMLESS_OPERATIONAL_SUPERVISION_PROOF_NOT_COMPILATION','binding':first['binding'],
            'unique_heartbeats':len(seen),'seconds':seconds,'hardware_uncertainty':UNCERTAINTY}


def serve(plan,expected_sha,*,max_seconds=MAX_SECONDS,new_session=False):
    p.need(expected_sha==digest(plan),'EXACT_REVIEWED_PLAN_REQUIRED')
    p.need(type(max_seconds) is int and 1<=max_seconds<=MAX_SECONDS,'HOST_SESSION_BUDGET')
    cfg=policy(plan['config']);transport=ssh_context(cfg);health=current_observer(plan)
    p.need(plan['host']['boot_id']==recorder.boot_id(),'HOST_GUEST_PLAN_REBOOT')
    hashes=code_hashes()
    p.need(plan['tools']['host_protocol_038']['sha256']==p.hash_file(Path(__file__))[0]
           and plan['tools']['windows_supervisor_038']['sha256']==hashes['HostSupervisor038.ps1']
           and plan['tools']['windows_probe_038']['sha256']==hashes['HostProbe038.ps1'],'HOST_PLAN_CODE_CHANGED')
    scope={'plan_sha256':digest(plan),'guest_boot':recorder.boot_id(),'observer':observer_scope(health),
           'vm_uuid':cfg['vm_uuid'],'scripts':code_hashes(),'transport':transport,'policy':POLICY}
    protocol=Protocol(scope);producer={'pid':os.getpid(),'start_ticks':recorder.process_identity(os.getpid()),
        'boot_id':recorder.boot_id(),'code_sha256':p.hash_file(Path(__file__))[0]}
    started=boot_clock();record={'version':POLICY,'valid':False,'session':protocol.session,'scope':scope,
        'scope_sha256':digest(scope),'producer':producer,'reason':'WAITING_FOR_HOST'}
    old={}
    def stop(*_):raise Refused('HOST_RECEIVER_STOPPED')
    with Store(cfg['directory'],new_session=new_session) as store:
        try:
            for sig in (signal.SIGTERM,signal.SIGINT):old[sig]=signal.signal(sig,stop)
            store.write(record);print(canonical(protocol.envelope()),flush=True)
            pending=bytearray()
            while boot_clock()-started<max_seconds:
                p.need(not ((Path(cfg['directory'])/'STOP').exists() or (Path(cfg['directory'])/'STOP').is_symlink()),'HOST_OWNER_STOP')
                fresh=current_observer(plan);p.need(observer_scope(fresh)==scope['observer'],'HOST_OBSERVER_RESTARTED')
                p.need(recorder.boot_id()==scope['guest_boot'],'HOST_GUEST_REBOOT')
                p.need(boot_clock()-protocol.last[1]<=TTL and time.time()-protocol.last[2]<=TTL,'HOST_RESPONSE_TIMEOUT_OR_RESUME')
                if not select.select([sys.stdin.buffer],[],[],.2)[0]:continue
                chunk=os.read(sys.stdin.fileno(),4096);p.need(chunk,'HOST_TRANSPORT_EOF')
                pending.extend(chunk);p.need(len(pending)<=8192,'HOST_FRAME_LIMIT')
                if b'\n' not in pending:continue
                line,_,rest=pending.partition(b'\n');p.need(not rest,'HOST_PIPELINED_OR_REPLAYED_FRAME')
                pending.clear();value=recorder.strict_json(line)
                accepted=protocol.accept(value);record.update(accepted,valid=True,reason='OPERATIONAL_HOST_OBSERVED')
                store.write(record);print(canonical(protocol.envelope()),flush=True)
            raise Refused('HOST_SESSION_DURATION_EXPIRED')
        except Exception as exc:
            record.update(valid=False,reason=str(exc));store.write(record)
            return {'operation':'HOST_SESSION_REVOKED','reason':str(exc),'hardware_uncertainty':UNCERTAINTY}
        finally:
            for sig,handler in old.items():signal.signal(sig,handler)


def attach_config(source,output,directory,vm_uuid,peer,review_ref,*,job=None):
    from research.controlled_build_037 import read_json,new_json,CONFIG_FIELDS
    config=read_json(source);p.need('host_supervision' not in config,'HOST_CONFIG_ALREADY_PRESENT')
    p.need(set(config)==CONFIG_FIELDS,'CONFIG_FIELDS')
    if job is not None:config['job']=job
    directory=Path(directory);p.secure(directory.parent);p.need(not directory.exists(),'NEW_HOST_DIRECTORY_REQUIRED')
    p.secure(Path(output).parent);p.need(not Path(output).exists(),'NEW_CONFIG_OUTPUT_REQUIRED')
    old=os.umask(0o077)
    try:
        directory.mkdir(mode=0o700)
        config['host_supervision']={'policy':POLICY,'directory':str(directory),'vm_uuid':vm_uuid,'ssh_peer':peer,'review_ref':review_ref}
        policy(config);new_json(Path(output),config)
    finally:os.umask(old)
    return {'operation':'NEW_OPT_IN_CONFIG_CREATED','config':str(output),'old_config_unchanged':True,'hardware_uncertainty':UNCERTAINTY}


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='action',required=True)
    a=sub.add_parser('attach-config');a.add_argument('--config',required=True);a.add_argument('--output',required=True);a.add_argument('--directory',required=True)
    a.add_argument('--vm-uuid',required=True);a.add_argument('--ssh-peer',required=True);a.add_argument('--review-ref',required=True);a.add_argument('--job')
    for name in ('serve','check','prove','stop'):
        a=sub.add_parser(name);a.add_argument('--plan',required=True)
        if name=='serve':a.add_argument('--expected-plan-sha',required=True);a.add_argument('--max-seconds',type=int,default=MAX_SECONDS);a.add_argument('--new-session',action='store_true')
    args=parser.parse_args(argv)
    try:
        if args.action=='attach-config':result=attach_config(args.config,args.output,args.directory,args.vm_uuid,args.ssh_peer,args.review_ref,job=args.job)
        else:
            from research.controlled_build_037 import read_json
            plan=read_json(args.plan)
            p.need(str(Path(args.plan))==str(Path(plan['job'])/'plan.json'),'HOST_PLAN_PATH')
            if args.action=='serve':result=serve(plan,args.expected_plan_sha,max_seconds=args.max_seconds,new_session=args.new_session)
            elif args.action=='check':
                details=check(plan,current_observer(plan))
                result={'operation':'OPERATIONAL_SUPERVISION_OBSERVED','plan_sha256':digest(plan),'accepted_seq':details['seq'],
                        'session_binding_sha256':digest(details['binding']),'hardware_uncertainty':UNCERTAINTY,'physical_hardware_verified':False}
            elif args.action=='stop':
                cfg=policy(plan['config']);path=Path(cfg['directory'])/'STOP'
                with os.fdopen(os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600),'w') as f:f.write('OWNER_STOP\n')
                result={'operation':'HOST_STOP_REQUESTED','hardware_uncertainty':UNCERTAINTY}
            else:
                result=prove(plan);private_binding=result.pop('binding')
                result['session_binding_sha256']=digest(private_binding)
        if args.action!='serve':print(json.dumps(result,indent=2,sort_keys=True))
        return 0
    except (OSError,ValueError,KeyError,Refused) as exc:
        print(json.dumps({'operation':'HOLD','reason':str(exc),'hardware_uncertainty':UNCERTAINTY}),file=sys.stderr);return 2


if __name__=='__main__':raise SystemExit(main())
