"""Bounded UTC-envelope POLICY MODEL. Authentic authority adapter is disabled.

Deterministic mock signatures exercise binding/arithmetic only, never crypto.
No clock reads, authority requests, keys, HMAC or live admission are implemented.
"""
from dataclasses import dataclass
import json
import re

NS = 1_000_000_000
MAX_BYTES = 8192
DRIFT_PPM = 100  # Test assumption; must be independently justified in production.
STAMP_ERROR_NS = 1_000_000
MAX_LEASE_NS = 30*NS
FIELDS = {'version','authority','key_id','algorithm','revision','run','boot','nonce',
          'utc_ns','accuracy_ns','lease_ns','signature'}


class Refused(ValueError):
    pass


def require(ok, reason):
    if not ok:raise Refused(reason)


def integer(value):
    return type(value) is int and 0 <= value < 2**63


def canonical(value):
    return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False).encode('ascii')


def parse(raw):
    require(type(raw) is bytes and 0 < len(raw) <= MAX_BYTES,'ENVELOPE_SIZE')
    def unique(pairs):
        out={}
        for key,value in pairs:
            require(key not in out,'DUPLICATE_FIELD');out[key]=value
        return out
    def reject(_):raise Refused('INVALID_JSON')
    try:
        value=json.loads(raw.decode('ascii'),object_pairs_hook=unique,parse_constant=reject)
        require(type(value) is dict and set(value)==FIELDS,'ENVELOPE_SCHEMA')
        for key in FIELDS-{'utc_ns','accuracy_ns','lease_ns'}:
            require(type(value[key]) is str and 1 <= len(value[key]) <= 128
                    and all(32 <= ord(c) <= 126 for c in value[key]),'ENVELOPE_SCHEMA')
        require(all(integer(value[k]) for k in ('utc_ns','accuracy_ns','lease_ns')),'ENVELOPE_SCHEMA')
        require(value['version']=='utc-envelope-model-v1' and value['algorithm']=='MOCK_ONLY'
                and value['authority']=='NOT_A_TIME_AUTHORITY' and value['key_id']=='NO_REAL_KEY','MODEL_ONLY')
        require(re.fullmatch('[0-9a-f]{40}',value['revision']) is not None
                and all(re.fullmatch('[0-9a-f]{64}',value[k]) is not None for k in ('boot','nonce')),'ENVELOPE_SCHEMA')
        require(value['utc_ns']>0 and value['accuracy_ns']<=2*NS
                and 0 < value['lease_ns']<=MAX_LEASE_NS,'UNCERTAINTY_OR_LEASE')
        return value
    except (ValueError,TypeError,UnicodeError,RecursionError,OverflowError) as exc:
        if isinstance(exc,Refused):raise
        raise Refused('INVALID_JSON') from None


@dataclass(frozen=True)
class Binding:
    revision: str
    run: str
    boot: str
    nonce: str


@dataclass(frozen=True)
class Window:
    send_mono: int
    recv_mono: int
    send_boot: int
    recv_boot: int
    now_mono: int
    now_boot: int
    boot: str


class MockSignature:
    """Explicit byte equality fixture, NOT an asymmetric signature verifier."""
    def __init__(self,expected_message):
        require(type(expected_message) is bytes and len(expected_message)<=MAX_BYTES,'MOCK_SCHEMA')
        self.expected_message=expected_message

    def check(self,message,signature):
        return message==self.expected_message and signature=='MOCK_SIGNATURE_NOT_CRYPTOGRAPHY'


def authentic_verifier(*_args,**_kwargs):
    return {'B4':'NO-GO','reason':'AUTHORITY_ADAPTER_DISABLED','independent_utc':False}


class EnvelopeModel:
    """One challenge per instance. No real nonce generator or persistent replay DB.

    Context and time samples must come from trusted local code in a future design;
    this model only checks supplied values. Instances cannot authenticate anything.
    """
    def __init__(self,binding):
        require(type(binding) is Binding,'BINDING_INVALID')
        require(type(binding.run) is str and 1<=len(binding.run)<=64
                and all(32<=ord(c)<=126 for c in binding.run),'BINDING_INVALID')
        for key,size in (('revision',40),('boot',64),('nonce',64)):
            value=getattr(binding,key)
            require(type(value) is str and re.fullmatch('[0-9a-f]{'+str(size)+'}',value) is not None,'BINDING_INVALID')
        self.binding=binding
        self.used=False
        self.proof=None
        self.previous=None

    def _window(self,window):
        require(type(window) is Window and window.boot==self.binding.boot,'BOOT_CHANGED')
        require(all(integer(getattr(window,k)) for k in ('send_mono','recv_mono','send_boot','recv_boot','now_mono','now_boot')),'CLOCK_INVALID')
        require(window.send_mono<=window.recv_mono<=window.now_mono
                and window.send_boot<=window.recv_boot<=window.now_boot,'MONOTONIC_ROLLBACK')
        for elapsed_mono,elapsed_boot in ((window.recv_mono-window.send_mono,window.recv_boot-window.send_boot),
                                         (window.now_mono-window.recv_mono,window.now_boot-window.recv_boot)):
            require(abs(elapsed_boot-elapsed_mono)<=STAMP_ERROR_NS,'SUSPEND_OR_CLOCK_CONFLICT')
        require(window.recv_mono-window.send_mono<=2*NS,'RTT_EXCESSIVE')
        if self.previous is not None:
            require(window.now_mono>=self.previous[0] and window.now_boot>=self.previous[1],'MONOTONIC_ROLLBACK')
        self.previous=(window.now_mono,window.now_boot)

    def enroll(self,raw,window,*,signature_verifier=None):
        require(not self.used,'REPLAY_OR_CONFLICT')
        self.used=True  # Failed challenge is burned, never retried in this run.
        proof=parse(raw)
        require(all(proof[k]==getattr(self.binding,k) for k in ('revision','run','boot','nonce')),'BINDING_MISMATCH')
        require(type(signature_verifier) is MockSignature,'AUTHORITY_ADAPTER_DISABLED')
        message=canonical({k:v for k,v in proof.items() if k!='signature'})
        require(signature_verifier.check(message,proof['signature']),'FORGED_MOCK_EVIDENCE')
        self._window(window)
        self.proof=(proof,window)
        try:return self.estimate(window)
        except Exception:
            self.proof=None
            raise

    def estimate(self,window):
        require(self.proof is not None,'NO_ENROLLED_MODEL')
        proof,original=self.proof
        try:
            self._window(window)
            require((window.send_mono,window.recv_mono,window.send_boot,window.recv_boot)==
                    (original.send_mono,original.recv_mono,original.send_boot,original.recv_boot),'WINDOW_REBOUND')
            rtt=window.recv_mono-window.send_mono
            age=window.now_mono-window.recv_mono
            require(age<proof['lease_ns'],'LEASE_EXPIRED')
            # Authority event lies somewhere inside the WHOLE send/receive
            # window. Add full RTT to upper bound; no symmetric path assumption.
            initial_drift=(rtt*DRIFT_PPM+999999)//1_000_000
            initial_low=proof['utc_ns']-proof['accuracy_ns']-2*STAMP_ERROR_NS
            initial_high=proof['utc_ns']+proof['accuracy_ns']+rtt+initial_drift+2*STAMP_ERROR_NS
            initial_uncertainty=(initial_high-initial_low+1)//2
            require(initial_uncertainty<=2*NS,'INITIAL_UNCERTAINTY_EXCESSIVE')
            growth=(age*DRIFT_PPM+999999)//1_000_000
            low=initial_low+age-growth
            high=initial_high+age+growth
            uncertainty=(high-low+1)//2
            require(uncertainty<=2*NS,'GROWN_UNCERTAINTY_EXCESSIVE')
            return {'B4':'NO-GO','authentication':'DETERMINISTIC_MOCK_ONLY','independent_utc':False,
                    'utc_low_ns':low,'utc_high_ns':high,'uncertainty_ns':uncertainty,
                    'initial_uncertainty_ns':initial_uncertainty,'age_ns':age,
                    'remaining_lease_ns':proof['lease_ns']-age,'live_admission':'HOLD'}
        except Exception:
            self.proof=None  # Conflict/expiry permanently invalidates this model.
            raise
