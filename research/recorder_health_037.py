"""Independent read-only recorder observer. Physical host stability always HOLD.

Reads status JSON and fixed systemd-user show properties, never a DB or exchange.
Only its own private health/lock files are written; no service/timer operations.
"""
import argparse
import contextlib
import datetime as dt
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import signal
import stat
import threading
import time
from research.qualification_035 import provision as p, process
from research.llama_analyst_033 import Refused

KIND='independent-recorder-observer-037-v1'
TIMER='boss-s3-recorder.timer'
SERVICE='boss-s3-recorder.service'
CADENCE=900
INTERVAL=5
TTL=15
MAX_SECONDS=7500
PROPERTIES=('Id','LoadState','ActiveState','SubState','Result','Type','ExecMainStatus','ExecMainStartTimestampMonotonic')


def strict_json(raw):
    def pairs(items):
        out={}
        for key,value in items:
            p.need(key not in out,'DUPLICATE_JSON_KEY');out[key]=value
        return out
    def invalid(value):raise Refused('NONFINITE_JSON')
    value=json.loads(raw,object_pairs_hook=pairs,parse_constant=invalid)
    p.need(type(value) is dict,'STATUS_OBJECT');return value


def status_read(path):
    path=p.secure(Path(path))
    with os.fdopen(os.open(path,os.O_RDONLY|os.O_NOFOLLOW),'rb') as f:
        before=os.fstat(f.fileno());p.need(stat.S_ISREG(before.st_mode),'STATUS_REGULAR_FILE')
        raw=f.read(65537);after=os.fstat(f.fileno())
    p.need(len(raw)<=65536,'STATUS_SIZE_LIMIT')
    fields=lambda s:(s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns)
    p.need(fields(before)==fields(after)==fields(path.lstat()),'STATUS_CHANGED_DURING_READ')
    return strict_json(raw),hashlib.sha256(raw).hexdigest()


def timestamp(value):
    p.need(type(value) is str and re.fullmatch(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?(?:Z|\+00:00)',value),'STATUS_UTC_TIMESTAMP')
    parsed=dt.datetime.fromisoformat(value.replace('Z','+00:00')).timestamp()
    p.need(946684800<=parsed<4102444800,'STATUS_TIMESTAMP_RANGE');return parsed


def systemd_show(unit):
    p.need(unit in (TIMER,SERVICE),'FIXED_UNIT_REQUIRED')
    binary=Path('/usr/bin/systemctl').resolve(strict=True);p.secure(binary)
    runtime=Path('/run/user')/str(os.getuid());p.secure(runtime)
    p.need(runtime.stat().st_uid==os.getuid(),'USER_BUS_OWNERSHIP')
    env={'PATH':'/usr/bin:/bin','HOME':'/nonexistent','LC_ALL':'C',
         'XDG_RUNTIME_DIR':str(runtime),'DBUS_SESSION_BUS_ADDRESS':'unix:path='+str(runtime/'bus'),
         'SYSTEMD_PAGER':'cat','SYSTEMD_COLORS':'0'}
    argv=[str(binary),'--user','--no-pager','--no-ask-password','show',unit,'--property='+','.join(PROPERTIES)]
    raw,receipt=process.run(argv,env=env,cwd=runtime,timeout=2,cap=4096)
    p.need(receipt['stderr_bytes']==0,'SYSTEMCTL_STDERR')
    result={}
    for line in raw.decode('utf-8').splitlines():
        key,sep,value=line.partition('=')
        p.need(sep and key in PROPERTIES and key not in result,'SYSTEMCTL_PROPERTIES')
        result[key]=value
    return result


def evaluate(status,timer,service,*,now,monotonic):
    """Status timestamps are collection evidence, not independent UTC/host proof."""
    p.need(type(status) is dict and type(timer) is dict and type(service) is dict,'OBSERVATION_SCHEMA')
    p.need(status.get('mode')=='LIVE_PUBLIC_DATA' and status.get('health')=='RECENT_COLLECTION'
           and 'pausedReason' in status and status['pausedReason'] is None
           and status.get('orderAuthority')=='NONE','RECORDER_STATUS_UNHEALTHY')
    times={key:timestamp(status.get(key)) for key in ('generatedAt','lastAttemptAt','lastSuccessAt')}
    p.need(all(value<=now for value in times.values()),'RECORDER_FUTURE_TIMESTAMP')
    p.need(times['generatedAt']>=max(times['lastAttemptAt'],times['lastSuccessAt']),'RECORDER_TIMESTAMP_ORDER')
    p.need(now-times['lastSuccessAt']<=2*CADENCE+30 and now-times['generatedAt']<=2*CADENCE+30,'RECORDER_COLLECTION_STALE')
    for data,unit in ((timer,TIMER),(service,SERVICE)):
        p.need(data.get('Id')==unit and data.get('LoadState')=='loaded','SYSTEMD_UNIT_IDENTITY')
    p.need(timer.get('ActiveState')=='active' and timer.get('SubState') in ('waiting','running','elapsed')
           and timer.get('Result','') in ('','success'),'RECORDER_TIMER_FAILURE')
    p.need(service.get('Type')=='oneshot' and service.get('Result')=='success'
           and service.get('ExecMainStatus')=='0','RECORDER_SERVICE_FAILURE')
    state=(service.get('ActiveState'),service.get('SubState'))
    idle=state==('inactive','dead')
    running=state in (('activating','start'),('activating','start-post'))
    p.need(idle or running,'RECORDER_SERVICE_STATE')
    if idle:
        p.need(times['lastAttemptAt']<=times['lastSuccessAt'],'RECORDER_IDLE_WITH_UNFINISHED_ATTEMPT')
        p.need(timer.get('SubState')=='waiting','RECORDER_TIMER_NOT_WAITING')
    else:
        start=service.get('ExecMainStartTimestampMonotonic','')
        p.need(type(start) is str and bool(re.fullmatch('[0-9]{1,20}',start)),'SERVICE_START_EVIDENCE_REQUIRED')
        age=monotonic-int(start)/1e6
        p.need(int(start)>0 and 0<=age<=CADENCE,'RECORDER_SERVICE_OVERRUN')
    return {'last_collection_at':int(times['lastSuccessAt']),
            'source_generated_at':status['generatedAt'],'last_attempt_at':status['lastAttemptAt'],'last_success_at':status['lastSuccessAt'],
            'service_phase':'IDLE_SUCCESS_BETWEEN_COLLECTIONS' if idle else 'BOUNDED_ONESHOT_RUNNING',
            'service':{key:service.get(key) for key in PROPERTIES if key in service},
            'timer':{key:timer.get(key) for key in ('Id','LoadState','ActiveState','SubState','Result') if key in timer},
            'cadence_seconds':CADENCE,'collection_time_source':'ACTUAL_STATUS_LAST_SUCCESS_NOT_OBSERVER_POLL'}


def collect(status_path,*,reader=status_read,query=systemd_show,wall=time.time,mono=time.monotonic):
    started=mono()
    for attempt in range(2):
        first,sha=reader(status_path)
        timer=query(TIMER);service=query(SERVICE)
        _,again=reader(status_path)
        if sha==again:break
        # One bounded remeasurement accommodates a normal atomic status transition.
        # Two additional 2s queries fit only when <=1s has elapsed so far.
        p.need(attempt==0 and mono()-started<=1,'RECORDER_STATUS_CHANGED_DURING_OBSERVATION')
    else:raise Refused('RECORDER_STATUS_CHANGED_DURING_OBSERVATION')
    end=wall();elapsed=mono()-started
    p.need(0<=elapsed<=INTERVAL,'OBSERVATION_BUDGET_EXCEEDED')
    result=evaluate(first,timer,service,now=end,monotonic=mono())
    result.update(measured_at=int(end),status_sha256=sha,observation_elapsed_seconds=elapsed,
                  semantics='LOCAL_GUEST_STATUS_AND_SYSTEMD_OBSERVATION_NOT_TRUSTED_UTC_OR_PHYSICAL_HOST_PROOF')
    return result


def process_identity(pid):
    p.need(type(pid) is int and pid>0,'OBSERVER_PID')
    text=Path('/proc/'+str(pid)+'/stat').read_text();fields=text.rsplit(')',1)[1].split()
    p.need(fields[0] not in ('Z','X'),'OBSERVER_NOT_RUNNING')
    return fields[19]


def boot_id():return Path('/proc/sys/kernel/random/boot_id').read_text().strip()


def validate_evidence(value,recorder_id,cadence,*,now=None,monotonic=None):
    """Detect stale/dead observers even when their last measurement was healthy."""
    now=time.time() if now is None else now;monotonic=time.monotonic() if monotonic is None else monotonic
    p.need(type(value) is dict,'HEALTH_OBJECT')
    p.need(value.get('version')=='external-recorder-health-037-v1' and value.get('recorder_id')==recorder_id,'HEALTH_IDENTITY')
    p.need(type(cadence) is int and cadence==CADENCE and type(value.get('collection_cadence_seconds')) is int and value.get('collection_cadence_seconds')==CADENCE,'RECORDER_CADENCE_900_REQUIRED')
    observer=value.get('observer',{})
    p.need(type(observer) is dict,'OBSERVER_SCHEMA')
    p.need(observer.get('kind')==KIND and observer.get('live') is True,'OBSERVER_STOPPED_OR_UNKNOWN')
    p.need(observer.get('boot_id')==boot_id(),'OBSERVER_BOOT_CHANGED')
    p.need(observer.get('code_sha256')==p.hash_file(Path(__file__))[0],'OBSERVER_CODE_CHANGED')
    heartbeat=observer.get('heartbeat_monotonic')
    p.need(type(heartbeat) in (int,float) and __import__('math').isfinite(heartbeat)
           and 0<=monotonic-heartbeat<=TTL,'OBSERVER_HEARTBEAT_STALE')
    try:identity=process_identity(observer.get('pid'))
    except (OSError,ValueError):raise Refused('OBSERVER_LOST') from None
    p.need(identity==observer.get('start_ticks'),'OBSERVER_PID_REUSED')
    p.need(type(value.get('measured_at')) is int and 0<=now-value['measured_at']<=TTL,'OBSERVER_MEASUREMENT_STALE')
    p.need(value.get('healthy') is True,'RECORDER_UNHEALTHY:'+str(value.get('recorder_reason','UNKNOWN')))
    stamp=value.get('last_collection_at')
    p.need(type(stamp) is int and 0<=now-stamp<=2*CADENCE+30,'RECORDER_COLLECTION_STALE')
    # No physical-host authority exists in this delivery; manually flipping it is rejected.
    p.need(value.get('desktop_stable') is False and value.get('host_stability')=='HOLD_PHYSICAL_HOST_NOT_OBSERVED','OBSERVER_CANNOT_ATTEST_HOST_STABILITY')
    return {'recorder':'MEASURED_HEALTHY','observer':'LIVE_FRESH','physical_host':'HOLD',
            'last_collection_at':stamp,'cadence_seconds':CADENCE,'measurement':value.get('measurement')}


class Publisher:
    """Atomic own-output publication in a private directory; never edits status.json."""
    def __init__(self,path,recorder_id,*,replace_stale=False):
        self.path=Path(path);self.recorder_id=recorder_id;self.replace_stale=replace_stale
        self.identity=None;self.lock=None;self.directory=None
    def __enter__(self):
        p.secure(self.path.parent);info=self.path.parent.stat()
        p.need(info.st_uid==os.getuid() and stat.S_IMODE(info.st_mode)==0o700,'PRIVATE_HEALTH_DIRECTORY_0700_REQUIRED')
        self.directory=os.open(self.path.parent,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
        try:
            lockpath=self.path.parent/('.'+self.path.name+'.observer.lock')
            try:
                self.lock=os.open(lockpath,os.O_RDWR|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
                os.fchmod(self.lock,0o600)
            except FileExistsError:self.lock=os.open(lockpath,os.O_RDWR|os.O_NOFOLLOW)
            s=os.fstat(self.lock);p.need(stat.S_ISREG(s.st_mode) and s.st_uid==os.getuid() and stat.S_IMODE(s.st_mode)==0o600,'OBSERVER_LOCK_OWNERSHIP')
            try:fcntl.flock(self.lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
            except BlockingIOError:raise Refused('OBSERVER_ALREADY_RUNNING') from None
            if self.path.exists() or self.path.is_symlink():
                p.need(self.replace_stale,'HEALTH_OUTPUT_EXISTS')
                old=self._current();obs=old.get('observer')
                p.need(type(obs) is dict and old.get('recorder_id')==self.recorder_id and obs.get('kind')==KIND,'FOREIGN_HEALTH_OUTPUT')
                alive=False
                try:alive=obs.get('boot_id')==boot_id() and process_identity(obs.get('pid'))==obs.get('start_ticks') and obs.get('live') is True
                except (OSError,ValueError):pass
                p.need(not alive,'OLD_OBSERVER_STILL_ALIVE')
            return self
        except BaseException:self.__exit__();raise
    def _current(self):
        p.secure(self.path);s=self.path.lstat()
        p.need(stat.S_ISREG(s.st_mode) and s.st_uid==os.getuid() and stat.S_IMODE(s.st_mode)==0o600,'PRIVATE_HEALTH_FILE_0600_REQUIRED')
        with os.fdopen(os.open(self.path,os.O_RDONLY|os.O_NOFOLLOW),'rb') as f:raw=f.read(4097)
        p.need(len(raw)<=4096,'HEALTH_SIZE_LIMIT');value=strict_json(raw)
        self.identity=(s.st_dev,s.st_ino);return value
    def publish(self,value):
        raw=json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()+b'\n'
        p.need(len(raw)<=4096,'HEALTH_SIZE_LIMIT')
        if self.identity is not None:
            s=self.path.lstat();p.need((s.st_dev,s.st_ino)==self.identity and not self.path.is_symlink(),'HEALTH_OUTPUT_REPLACED')
        temp=self.path.parent/('.observer-037-'+secrets.token_hex(12))
        try:
            with os.fdopen(os.open(temp,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600),'wb') as f:
                os.fchmod(f.fileno(),0o600);f.write(raw);f.flush();os.fsync(f.fileno())
            if self.identity is None:p._rename_new(temp,self.path,parent_fd=self.directory)
            else:os.replace(temp.name,self.path.name,src_dir_fd=self.directory,dst_dir_fd=self.directory)
            os.fsync(self.directory);s=self.path.lstat();self.identity=(s.st_dev,s.st_ino)
        finally:
            if temp.exists():temp.unlink()
    def __exit__(self,*_):
        if self.lock is not None:os.close(self.lock);self.lock=None
        if self.directory is not None:os.close(self.directory);self.directory=None


def run(config,*,status_path=None,seconds=MAX_SECONDS,replace_stale=False,collector=collect,stop=None,clock=time.monotonic):
    p.need(type(seconds) is int and 1<=seconds<=MAX_SECONDS,'OBSERVER_RUNTIME_BUDGET')
    p.need(type(config['collection_cadence_seconds']) is int and config['collection_cadence_seconds']==CADENCE,'RECORDER_CADENCE_900_REQUIRED')
    stop=threading.Event() if stop is None else stop
    status_path=Path.home()/'.local/share/boss-s3-recorder/status.json' if status_path is None else Path(status_path)
    p.need(status_path.is_absolute(),'ABSOLUTE_STATUS_REQUIRED')
    dest=Path(config['health_file']);p.need(dest.resolve()!=status_path.resolve(),'STATUS_OUTPUT_OVERLAP')
    start=clock();last_collection=None;last_value=None;session=secrets.token_hex(16)
    code_sha=p.hash_file(Path(__file__))[0]
    def base(live):
        return {'version':'external-recorder-health-037-v1','recorder_id':config['recorder_id'],
                'collection_cadence_seconds':CADENCE,'measured_at':int(time.time()),
                'last_collection_at':last_collection,'healthy':False,'desktop_stable':False,
                'host_stability':'HOLD_PHYSICAL_HOST_NOT_OBSERVED',
                'observer':{'kind':KIND,'live':live,'pid':os.getpid(),'start_ticks':process_identity(os.getpid()),
                            'boot_id':boot_id(),'heartbeat_monotonic':clock(),'interval_seconds':INTERVAL,'session':session,'code_sha256':code_sha}}
    with Publisher(dest,config['recorder_id'],replace_stale=replace_stale) as publisher:
        try:
            while not stop.is_set() and clock()-start<seconds:
                cycle=clock();value=base(True)
                try:
                    measured=collector(status_path)
                    p.need(last_collection is None or measured['last_collection_at']>=last_collection,'RECORDER_COLLECTION_TIME_REGRESSED')
                    last_collection=measured['last_collection_at']
                    value.update(measured_at=measured['measured_at'],last_collection_at=last_collection,healthy=True,
                                 recorder_reason='MEASURED_RECENT_COLLECTION',measurement=measured)
                except (OSError,ValueError,KeyError,Refused) as exc:
                    value.update(last_collection_at=last_collection,recorder_reason=str(exc))
                if stop.is_set():break
                publisher.publish(value);last_value=value
                remaining=min(INTERVAL-max(0,clock()-cycle),seconds-(clock()-start))
                if remaining>0:stop.wait(remaining)
        finally:
            value=base(False);value.update(recorder_reason='OBSERVER_STOPPED',last_successful_measurement=last_value.get('measured_at') if last_value else None)
            publisher.publish(value)
    return {'operation':'OBSERVER_STOPPED','physical_host':'HOLD','genuine_inference':'HOLD','compilation':'NOT_RUN'}


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config',required=True)
    parser.add_argument('--seconds',type=int,default=MAX_SECONDS);parser.add_argument('--replace-stale',action='store_true')
    args=parser.parse_args(argv);stop=threading.Event();old={}
    try:
        from research.controlled_build_037 import read_json
        config=read_json(args.config)
        for sig in (signal.SIGTERM,signal.SIGINT):old[sig]=signal.signal(sig,lambda *_:stop.set())
        result=run(config,seconds=args.seconds,replace_stale=args.replace_stale,stop=stop)
        print(json.dumps(result,sort_keys=True));return 0
    except (OSError,ValueError,KeyError,Refused) as exc:
        print(json.dumps({'operation':'REFUSED','reason':str(exc),'physical_host':'HOLD'},sort_keys=True));return 2
    finally:
        for sig,handler in old.items():signal.signal(sig,handler)


if __name__=='__main__':raise SystemExit(main())
