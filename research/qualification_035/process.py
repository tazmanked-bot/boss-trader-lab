"""Bounded supervisor for pinned synthetic programs, not a general public executor."""
import os
from pathlib import Path
import selectors
import signal
import subprocess
import threading
import time
from .provision import need
from research.llama_analyst_033 import Refused

LOCK=threading.Lock()
POISONED=False


def descendants(pid):
    found={}
    def visit(p):
        try:
            raw=Path(f'/proc/{p}/stat').read_text();found[p]=raw.rsplit(')',1)[1].split()[19]
            for c in Path(f'/proc/{p}/task/{p}/children').read_text().split():visit(int(c))
        except (FileNotFoundError,ProcessLookupError):pass
        except OSError:found[p]='UNVERIFIED'
    visit(pid);return found


def still_present(p,start):
    if start=='UNVERIFIED':return True
    try:return Path(f'/proc/{p}/stat').read_text().rsplit(')',1)[1].split()[19]==start
    except FileNotFoundError:return False
    except OSError:return True


def run(argv,*,env,cwd,timeout=30,cap=8192,pass_fds=(),release=None):
    global POISONED
    need(not POISONED,'CLEANUP_POISONED');need(LOCK.acquire(False),'EXECUTOR_BUSY')
    if not (0<timeout<=30 and 0<cap<=8192):
        LOCK.release();raise Refused('PROCESS_BUDGET')
    error_bytes=[0];process=None;tracked={};raw=bytearray();error=None;code=None;started=time.monotonic();reaped=False
    try:
        process=subprocess.Popen(argv,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
            cwd=cwd,env=env,shell=False,start_new_session=True,close_fds=True,pass_fds=pass_fds)
        if release:release(process.pid)
        selector=selectors.DefaultSelector()
        try:
            for stream in (process.stdout,process.stderr):os.set_blocking(stream.fileno(),False);selector.register(stream,selectors.EVENT_READ)
            while selector.get_map():
                tracked.update(descendants(process.pid))
                need(time.monotonic()-started<timeout,'PROCESS_TIMEOUT')
                for key,_ in selector.select(.02):
                    try:data=os.read(key.fd,1024)
                    except BlockingIOError:continue
                    if not data:selector.unregister(key.fileobj);continue
                    need(len(raw)+len(data)<=cap,'OUTPUT_LIMIT')
                    # Both streams count against one bound; stdout-only JSON returned.
                    if key.fileobj is process.stdout:raw.extend(data)
                    else:
                        error_bytes[0]+=len(data)
                    need(len(raw)+error_bytes[0]<=cap,'OUTPUT_LIMIT')
            remaining=timeout-(time.monotonic()-started);need(remaining>0,'PROCESS_TIMEOUT')
            try:code=process.wait(timeout=remaining)
            except subprocess.TimeoutExpired:raise Refused('PROCESS_TIMEOUT') from None
            need(code==0,'PROCESS_NONZERO')
        finally:selector.close()
    except (Refused,OSError) as exc:error=str(exc) if isinstance(exc,Refused) else 'PROCESS_UNAVAILABLE'
    finally:
        if process is not None:
            tracked.update(descendants(process.pid))
            try:os.killpg(process.pid,signal.SIGTERM)
            except ProcessLookupError:pass
            except OSError:error='PROCESS_CLEANUP_UNCERTAIN'
            try:process.wait(timeout=.2)
            except subprocess.TimeoutExpired:pass
            try:os.killpg(process.pid,signal.SIGKILL)
            except ProcessLookupError:pass
            except OSError:error='PROCESS_CLEANUP_UNCERTAIN'
            try:process.wait(timeout=.8);reaped=True
            except subprocess.TimeoutExpired:error='PROCESS_UNREAPED'
            for stream in (process.stdout,process.stderr):stream.close()
            deadline=time.monotonic()+1
            while time.monotonic()<deadline and any(still_present(p,s) for p,s in tracked.items()):time.sleep(.01)
            if any(still_present(p,s) for p,s in tracked.items()):error='PROCESS_TREE_NOT_REAPED'
        if error in ('PROCESS_UNREAPED','PROCESS_TREE_NOT_REAPED','PROCESS_CLEANUP_UNCERTAIN'):POISONED=True
        LOCK.release()
    receipt={'elapsed_ns':int((time.monotonic()-started)*1e9),'direct_child_reaped':reaped,
             'tracked_process_count':len(tracked),'process_tree_gone':not any(still_present(p,s) for p,s in tracked.items()),
             'stderr_bytes':error_bytes[0],'error':error,'real_inference':False}
    if error:
        exc=Refused(error);exc.receipt=receipt;raise exc
    return bytes(raw),receipt
