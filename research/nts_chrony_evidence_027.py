"""Passive chrony inventory and STATIC SYNTHETIC receipt screening only.

No process, NTS client, cryptography, clock-setting or authentic UTC admission.
026's authentic_verifier remains untouched. Hashes identify bytes, not trust.
"""
from dataclasses import dataclass
import hashlib
import json
import os
import platform
import re
import stat
import time

from research import utc_evidence_026 as utc

NS=utc.NS
MAX_RECEIPT=16384
MAX_BINARY=16*1024*1024
PATHS={'chronyd':('/usr/sbin/chronyd','/usr/bin/chronyd'),
       'chronyc':('/usr/bin/chronyc','/usr/sbin/chronyc')}


class Refused(ValueError):pass


def require(ok,reason):
    if not ok:raise Refused(reason)


def hex_digest(value):
    return type(value) is str and re.fullmatch('[0-9a-f]{64}',value) is not None


def status():
    return {'overall':'HOLD','B1':'HOLD','B2':'HOLD','B3':'HOLD','B4':'B4_NO_GO','B5':'HOLD',
            'protocol':'NTS_PROTOCOL_SUPPORTED_BY_DOCS','target_client':'TARGET_CLIENT_CAPABILITY_UNVERIFIED',
            'provenance':'AUTHENTIC_PROVENANCE_NOT_COLLECTED','reason':'AUTHENTIC_NTS_PROVENANCE_UNAVAILABLE',
            'live_source_admission':'HOLD','independent_utc':False,'requests':0,'process_launches':0,'policy':'NO ORDERS'}


def _binary(path,deadline):
    """Fixed caller-selected allowlist path, regular no-follow file, bounded hash."""
    require(path in sum(PATHS.values(),()),'PATH_REFUSED')
    require(hasattr(os,'O_NOFOLLOW') and hasattr(os,'O_NONBLOCK'),'PLATFORM_UNSUPPORTED')
    fd=None
    try:
        require(time.monotonic_ns()<deadline,'INVENTORY_TIMEOUT')
        fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
        before=os.fstat(fd)
        require(stat.S_ISREG(before.st_mode) and 0<before.st_size<=MAX_BINARY,'BINARY_REFUSED')
        require(before.st_mode & 0o111 != 0 and os.access(path,os.X_OK),'NOT_EXECUTABLE')
        digest=hashlib.sha256();size=0
        while True:
            require(time.monotonic_ns()<deadline,'INVENTORY_TIMEOUT')
            chunk=os.read(fd,min(65536,MAX_BINARY-size+1))
            if not chunk:break
            size+=len(chunk);require(size<=MAX_BINARY,'BINARY_REFUSED');digest.update(chunk)
        after=os.fstat(fd)
        require(size==before.st_size and (before.st_dev,before.st_ino,before.st_size,before.st_mtime_ns,before.st_ctime_ns)==
                (after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns,after.st_ctime_ns),'BINARY_CHANGED')
        return {'path':path,'status':'PRESENT_HASHED_NOT_EXECUTED','bytes':size,'sha256':digest.hexdigest()}
    finally:
        if fd is not None:os.close(fd)


def passive_inventory(*,enabled=False):
    output={**status(),'inventory_status':'DISABLED','clients':{}}
    if enabled is not True:return output
    deadline=time.monotonic_ns()+5*NS
    output.update(actual_host={'system':platform.system(),'kernel':platform.release(),'architecture':platform.machine(),
                              'python':platform.python_version()},requested_target={'os':'ubuntu-24.04','python':'3.11.17'})
    for name,paths in PATHS.items():
        rows=[]
        for path in paths:
            try:rows.append(_binary(path,deadline))
            except FileNotFoundError:rows.append({'path':path,'status':'ABSENT'})
            except PermissionError:rows.append({'path':path,'status':'PERMISSION_DENIED'})
            except (OSError,Refused) as exc:
                rows.append({'path':path,'status':str(exc) if isinstance(exc,Refused) else 'FILE_UNAVAILABLE'})
        output['clients'][name]={'paths':rows,'version':'NOT_EXECUTED','package_build_provenance':'UNVERIFIED',
                                 'tls_nts_compiled_support':'UNVERIFIED','status_export':'NOT_QUERIED'}
    present=[any(r['status']=='PRESENT_HASHED_NOT_EXECUTED' for r in c['paths']) for c in output['clients'].values()]
    output['inventory_status']='CLIENT_CAPABILITY_UNVERIFIED' if all(present) else 'CLIENT_INCOMPLETE' if any(present) else 'CLIENT_UNAVAILABLE'
    return output


def parse(raw):
    require(type(raw) is bytes and 0<len(raw)<=MAX_RECEIPT,'RECEIPT_SIZE')
    def unique(pairs):
        out={}
        for key,value in pairs:
            require(key not in out,'DUPLICATE_FIELD');out[key]=value
        return out
    def reject(_):raise Refused('JSON_INVALID')
    try:
        value=json.loads(raw.decode('ascii'),object_pairs_hook=unique,parse_constant=reject)
        require(type(value) is dict,'RECEIPT_SCHEMA')
        return value
    except (ValueError,TypeError,UnicodeError,RecursionError) as exc:
        if isinstance(exc,Refused):raise
        raise Refused('JSON_INVALID') from None


def exact(value,fields):
    require(type(value) is dict and set(value)==set(fields.split()),'RECEIPT_SCHEMA')


@dataclass(frozen=True)
class Expected:
    binding: utc.Binding
    client_sha256: str
    authority: str
    anchor_sha256: str
    session_ref: str
    drift_ppm: int=100


class ShapeSession:
    """Single-use TEST receipt context; no cryptographic or persistent replay state."""
    def __init__(self,expected):
        require(type(expected) is Expected,'CONTEXT_INVALID')
        try:utc.EnvelopeModel(expected.binding) # Existing strict local binding checks.
        except utc.Refused:raise Refused('CONTEXT_INVALID') from None
        require(all(hex_digest(getattr(expected,k)) for k in ('client_sha256','anchor_sha256','session_ref')),'CONTEXT_INVALID')
        require(expected.authority=='synthetic-authority.invalid' and type(expected.drift_ppm) is int
                and 0<=expected.drift_ppm<=1000,'SYNTHETIC_CONTEXT_ONLY')
        self.expected=expected;self.used=False

    def evaluate(self,raw=None,*,local_window=None):
        output={**status(),'shape_status':'NOT_CHECKED'}
        if raw is None:return output
        try:
            require(not self.used,'REPLAYED_RECEIPT');self.used=True
            value=parse(raw)
            exact(value,'schema origin binding client association bounds window')
            require(value['schema']=='synthetic-nts-receipt-v1' and value['origin']=='STATIC_SYNTHETIC_NOT_AUTHENTIC_NTS','SYNTHETIC_ONLY')
            expected=self.expected
            exact(value['binding'],'revision run boot nonce')
            require(all(value['binding'][k]==getattr(expected.binding,k) and type(value['binding'][k]) is str
                        for k in ('revision','run','boot','nonce')),'BINDING_MISMATCH')
            client=value['client'];exact(client,'name version binary_sha256 build_ref nts_support')
            require(client['name']=='chronyd' and client['version']=='4.6','CLIENT_PROFILE_UNSUPPORTED')
            require(client['binary_sha256']==expected.client_sha256 and hex_digest(client['build_ref'])
                    and client['nts_support']=='MODEL_NTS_ENABLED','CLIENT_CAPABILITY_UNVERIFIED')
            association=value['association']
            exact(association,'authority anchor_sha256 certificate_sha256 bootstrap tls nts_ke aead unique_id cookie_ref cookie_state cookie_lease_ns session_ref ntp_extensions plain_ntp_fallback')
            require(association['authority']==expected.authority and association['anchor_sha256']==expected.anchor_sha256
                    and association['session_ref']==expected.session_ref,'AUTHORITY_OR_SESSION_CHANGED')
            require(all(hex_digest(association[k]) for k in ('certificate_sha256','unique_id','cookie_ref')),'ASSOCIATION_EVIDENCE_MISSING')
            require(association['unique_id']==expected.binding.nonce,'FRESHNESS_BINDING_MISMATCH')
            require(association['bootstrap']=='MODEL_INDEPENDENT_BOOTSTRAP','BOOTSTRAP_UNVERIFIED')
            require(association['tls']=='MODEL_CHAIN_NAME_TIME_VERIFIED' and association['nts_ke']=='MODEL_NTS_KE','TLS_NTS_KE_UNVERIFIED')
            require(association['plain_ntp_fallback'] is False,'UNAUTHENTICATED_FALLBACK')
            require(association['aead']=='MODEL_AEAD_VERIFIED' and association['ntp_extensions']==['UID','COOKIE','AUTHENTICATOR'],'NTS_EXTENSION_EVIDENCE_MISSING')
            require(association['cookie_state']=='MODEL_AVAILABLE','COOKIE_ASSOCIATION_REFUSED')
            require(utc.integer(association['cookie_lease_ns']) and 0<association['cookie_lease_ns']<=utc.MAX_LEASE_NS,'COOKIE_ASSOCIATION_REFUSED')
            exact(value['window'],'send_mono recv_mono send_boot recv_boot')
            try:
                utc.EnvelopeModel(expected.binding)._window(local_window)
            except utc.Refused as exc:raise Refused(str(exc)) from None
            require(all(type(value['window'][k]) is int and value['window'][k]==getattr(local_window,k)
                        for k in value['window']),'LOCAL_WINDOW_MISMATCH')
            rtt=local_window.recv_mono-local_window.send_mono
            age=local_window.now_mono-local_window.recv_mono
            bounds=value['bounds']
            exact(bounds,'reference_utc_ns offset_ns root_delay_ns root_dispersion_ns authority_error_ns local_capture_error_ns drift_ppm lease_ns')
            require(all(utc.integer(bounds[k]) for k in bounds if k!='offset_ns')
                    and type(bounds['offset_ns']) is int and abs(bounds['offset_ns'])<2**63,'BOUNDS_INVALID')
            require(bounds['reference_utc_ns']>0 and bounds['drift_ppm']==expected.drift_ppm
                    and 0<bounds['local_capture_error_ns']<=utc.STAMP_ERROR_NS
                    and 0<bounds['lease_ns']<=utc.MAX_LEASE_NS,'BOUNDS_INVALID')
            require(age<bounds['lease_ns'] and age<association['cookie_lease_ns'],'LEASE_EXPIRED')
            # Screening budget only. Use full local RTT on top of root distance
            # instead of trusting symmetric paths or treating auth as accuracy.
            ceil_ppm=lambda elapsed:(elapsed*expected.drift_ppm+999999)//1_000_000
            initial=(abs(bounds['offset_ns'])+(bounds['root_delay_ns']+1)//2+
                     bounds['root_dispersion_ns']+bounds['authority_error_ns']+rtt+
                     2*bounds['local_capture_error_ns']+ceil_ppm(rtt+2*bounds['local_capture_error_ns']))
            require(initial<=2*NS,'INITIAL_UNCERTAINTY_EXCESSIVE')
            current=initial+ceil_ppm(age)
            require(current<=2*NS,'GROWN_UNCERTAINTY_EXCESSIVE')
            output.update(shape_status='OFFLINE_SHAPE_VALID',synthetic_screen_initial_ns=initial,
                          synthetic_screen_current_ns=current,synthetic_age_ns=age,
                          receipt_sha256=hashlib.sha256(raw).hexdigest())
        except (Refused,TypeError,ValueError,AttributeError,OverflowError) as exc:
            output.update(shape_status='REFUSED',reason=str(exc) if isinstance(exc,Refused) else 'RECEIPT_SCHEMA')
        # Never promote self-asserted JSON, hashes, mock flags or process output.
        return output


def main():
    import argparse
    parser=argparse.ArgumentParser(description='Passive offline chrony file inventory only; no execution or time queries')
    parser.add_argument('--offline-inventory',action='store_true')
    args=parser.parse_args()
    output=passive_inventory(enabled=args.offline_inventory)
    print(json.dumps(output,sort_keys=True));return 0 if args.offline_inventory else 2


if __name__=='__main__':raise SystemExit(main())
