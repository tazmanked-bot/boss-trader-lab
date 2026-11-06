"""Single-shot STATIC HTTP-fixture integration; no real transport or live admission.

Default CLI is disabled. --offline-demo uses only an immutable packaged synthetic
fixture and a synchronous TEST job, never a real worker/network/UTC provider.
"""
import hashlib
import json

from research import kraken_probe_corrections as corrections
from research import kraken_spot_diagnostic as diagnostic
from research import kraken_spot_validation_bridge as bridge
from research import kraken_spot_reversal_bridge_prototype as groundwork
from research import spot_refusal_registry as registry
from research import spot_reversal_candidates as candidates
from research import spot_reversal_source_preview_023 as preview

VERSION = "manual-reversal-fixture-integration-v1"
SOURCE = "STATIC_SYNTHETIC_KRAKEN_HTTP_FIXTURES"
RUN_BUDGET_NS = 6*diagnostic.DEADLINE_NS
MAX_OUTPUT_BYTES = 32768
DEMO_SHA256 = "761c171e090bcfc14c8ab87ea4ce3a20b8278aa01b6445e0871438dc4fc8285b"


def _hash(value):
    return "sha256:"+hashlib.sha256(registry.canonical_json(value).encode("ascii")).hexdigest()


def _require(condition, code):
    if not condition:
        raise corrections.Refused(code)


def _request(symbol, stage, as_of):
    pair=diagnostic.IDENTITIES[symbol][0]
    if stage=="IDENTITY":
        return diagnostic.Request(symbol,"/0/public/AssetPairs",(("pair",pair),("aclass_base","currency"),("info","info")))
    return diagnostic.Request(symbol,"/0/public/OHLC",(("pair",pair),("interval",60),("since",as_of-86400)))


class StaticResponses:
    """Sealed bounded bytes, fixed six-slot plan, one claim only. Never a client."""
    __slots__=("_responses","_claimed","_index","_as_of")

    def __init__(self, responses):
        _require(type(responses) is tuple and len(responses)==6,corrections.Code.CONTEXT_INVALID)
        _require(all(type(r) is bytes and len(r)<=corrections.WIRE_LIMIT for r in responses),corrections.Code.BODY_LIMIT)
        self._responses=responses
        self._claimed=False
        self._index=0
        self._as_of=None

    def claim(self,as_of):
        _require(not self._claimed,corrections.Code.CONTEXT_INVALID)
        self._claimed=True
        self._as_of=as_of

    @property
    def consumed(self):
        return self._index

    def take(self,request):
        _require(self._claimed and self._index<6,corrections.Code.CONTEXT_INVALID)
        symbol=registry.SYMBOLS[self._index//2]
        stage=("IDENTITY","OHLC")[self._index%2]
        expected=_request(symbol,stage,self._as_of)
        _require(type(request) is diagnostic.Request and request==expected,corrections.Code.CONTEXT_INVALID)
        response=self._responses[self._index]
        self._index+=1
        return response


class SynchronousFixtureJob:
    """TEST job: paused/released synchronous action, no process/isolation guarantee."""
    def __init__(self,request,action,clock,deadline):
        self.request,self.action,self.clock,self.deadline=request,action,clock,deadline
        self.started=False
        self.done=False
        self.cancelled=False
        self.code=corrections.Code.WORKER_INVALID

    def start(self): self.started=True
    def alive(self): return self.started and not self.done
    def ready(self): return self.started and not self.done
    def release(self):
        try:
            _require(not self.cancelled and self.clock.monotonic_ns()<self.deadline,corrections.Code.TIMEOUT)
            self.action(self.request)
            self.code=corrections.Code.COMPLETED
        except corrections.Refused as exc:
            self.code=exc.code
        except Exception:
            self.code=corrections.Code.WORKER_INVALID
        self.done=True
    def wait(self,seconds): pass
    def result(self): return self.code
    def cancel(self): self.cancelled=True
    def kill(self): self.done=True
    def reap(self): return self.done
    def close_unstarted(self): self.done=True


def _base():
    return {"version":VERSION,"overall":"HOLD","offline_status":"BLOCKED","reason":"AUTHORIZATION_MISSING",
            "source":SOURCE,"mode":"STATIC_FIXTURE_EXPERIMENT_ONLY","live_source_admission":"HOLD",
            "operational_mode":"HOLD","trade_authority":"NO ORDERS","requests":0,
            "fixture_attempts":0,"fixtures_consumed":0,"run_id":None,"capture":None,
            "source_rows":{s:{"status":"NOT_ATTEMPTED","reason":"GLOBAL_STOP","identity_ref":None,"bridge":None}
                           for s in registry.SYMBOLS},"receipts":[],"decisions":preview._empty_rows(),
            "synthetic_closed_prices":{},"candidates":[],"total_candidates":0}


def run_offline(*, responses=None, clock=None, clock_evidence=None, clock_evidence_verifier=None,
                expected_context=None, job_factory=None):
    """All dependencies must be explicit TEST inputs. No real source type accepted.

    Authentic source admission is absent. Injected Python is trusted test code,
    not sandboxed; only sealed fixture bytes can reach this integration's parser.
    """
    result=_base()
    if responses is None:
        return result
    consumed_before=responses.consumed if type(responses) is StaticResponses else 0
    current=None
    try:
        _require(type(responses) is StaticResponses,corrections.Code.CONTEXT_INVALID)
        _require(clock is not None and callable(clock_evidence_verifier),corrections.Code.CLOCK_UNVERIFIED)
        _require(callable(job_factory),corrections.Code.PLATFORM_UNSUPPORTED)
        groundwork._context(expected_context)
        gate=diagnostic.CaptureClock(clock)
        groundwork._clock(clock_evidence,expected_context,gate,clock_evidence_verifier)
        _require(clock_evidence["valid_until_mono_ns"]>gate.initial.mono_ns+RUN_BUDGET_NS
                 and gate.initial.mono_ns+RUN_BUDGET_NS<2**63,corrections.Code.CLOCK_UNVERIFIED)
        responses.claim(gate.as_of)
        result["run_id"]=expected_context["run_id"]
        result["capture"]={"utc_ns":gate.initial.utc_ns,"as_of":gate.as_of,
            "clock":"SYNTHETIC_MODEL_NOT_ATTESTATION","meaning":"SYNTHETIC_COORDINATE_NOT_CURRENT_UTC",
            "clock_evidence_ref":_hash(clock_evidence)}
        payloads={}

        def check():
            now=gate.sample()
            _require(now.mono_ns<gate.initial.mono_ns+RUN_BUDGET_NS,corrections.Code.TIMEOUT)
            _require(now.mono_ns<clock_evidence["valid_until_mono_ns"],corrections.Code.CLOCK_UNVERIFIED)
            return now

        def stage_evaluator(symbol,stage):
            nonlocal current
            current=symbol
            row=result["source_rows"][symbol]
            row.update(status="BLOCKED",reason="WORKER_INVALID")
            receipt={"pair":symbol,"stage":stage,"reason":"WORKER_INVALID"}
            result["receipts"].append(receipt)
            try:
                request=_request(symbol,stage,gate.as_of)
                request.target()
                start=check()
                deadline=start.mono_ns+diagnostic.DEADLINE_NS
                _require(deadline<clock_evidence["valid_until_mono_ns"],corrections.Code.CLOCK_UNVERIFIED)
                result["fixture_attempts"]+=1  # Reserved before construction/release, never refunded.
                box={}
                def action(req):
                    wire=responses.take(req)
                    box["wire_bytes"]=len(wire)
                    try:
                        box["parsed"]=corrections.parse_http_fixture(corrections.MemoryReader(wire))
                    except corrections.Refused as exc:
                        box["parse_error"]=exc.code
                supervised=corrections.supervise_offline(request=request,action=action,clock=clock,
                    job_factory=job_factory,deadline_ns=deadline)
                receipt["supervisor"]=supervised
                _require(supervised["overall"]=="HOLD" and supervised["reason"]=="COMPLETED"
                         and supervised["cleanup"]=="REAPED" and supervised["released"] is True,
                         corrections.Code(supervised["reason"]) if supervised["reason"]!="COMPLETED" else corrections.Code.WORKER_INVALID)
                if "parse_error" in box:
                    raise corrections.Refused(box["parse_error"])
                _require(type(box.get("parsed")) is corrections.ParsedFixture,corrections.Code.WORKER_INVALID)
                end=check()
                _require(end.mono_ns<deadline,corrections.Code.TIMEOUT)
                parsed=box["parsed"]
                gate.envelope(start,end,parsed.date_seconds)
                receipt.update(wire_bytes=box["wire_bytes"],elapsed_ns=end.mono_ns-start.mono_ns,
                               service_date_seconds=parsed.date_seconds)
                if stage=="IDENTITY":
                    key,ref=groundwork._identity_ref(symbol,parsed.payload)
                    row.update(identity_ref=ref,source_pair_key=key,status="IDENTITY_MODEL_PASSED")
                else:
                    key=diagnostic.IDENTITIES[symbol][1]
                    diagnostic._commitment(parsed.payload,key,gate.as_of,end,parsed.date_seconds)
                    capture={"venue":"kraken","market":"spot","quote":"USD","symbol":symbol,
                        "request_pair":diagnostic.IDENTITIES[symbol][0],"interval_minutes":60,"response":parsed.payload}
                    validated=bridge.validate_capture(symbol,capture,as_of=gate.as_of,policy=groundwork.POLICY)
                    row["bridge"]=validated
                    _require(validated["decision"]["status"]=="VALIDATED_DATA",corrections.Code.BRIDGE_REFUSED)
                    payloads[symbol]=groundwork._normalize(symbol,capture,validated["decision"],gate.as_of)
                    row["status"]="VALIDATED_STATIC_DATA"
                _require(check().mono_ns<deadline,corrections.Code.TIMEOUT)
                row["reason"]=None
                receipt["reason"]="STAGE_PASSED"
                return corrections.StageResult(corrections.Code.STAGE_PASSED)
            except corrections.Refused as exc:
                code=exc.code
            except diagnostic.Refused as exc:
                code=corrections.Code(exc.reason.value) if exc.reason.value in corrections.Code._value2member_map_ else corrections.Code.WORKER_INVALID
            except groundwork.Refused as exc:
                code=corrections.Code(str(exc)) if str(exc) in corrections.Code._value2member_map_ else corrections.Code.BRIDGE_REFUSED
            except Exception:
                code=corrections.Code.WORKER_INVALID
            row.update(status="BLOCKED",reason=code.value)
            receipt["reason"]=code.value
            return corrections.StageResult(code)

        control=corrections.coordinate_global_stop_offline(stage_evaluator)
        result["coordinator_reason"]=control["reason"]
        if control["reason"]!="ALL_STAGE_CHECKS_PASSED":
            result["reason"]=control["reason"]
        else:
            _require(result["fixture_attempts"]==6 and responses.consumed==6,corrections.Code.WORKER_INVALID)
            decisions=registry.validate_symbols(payloads,as_of=gate.as_of,policy=groundwork.POLICY)
            for symbol in registry.SYMBOLS:
                _require(decisions[symbol]["status"]=="VALIDATED_DATA"
                         and registry.canonical_json(decisions[symbol])==registry.canonical_json(result["source_rows"][symbol]["bridge"]["decision"]),corrections.Code.BRIDGE_REFUSED)
            computed={}
            for symbol in registry.SYMBOLS:
                check()
                features=candidates._features(payloads[symbol]["bars"])
                qualified=all(f["passed"] for f in features.values())
                computed[symbol]={"decision":"WATCH" if qualified else "WAIT","validation":decisions[symbol],
                    "features":features,"score":sum(f["strength_bps"] for f in features.values()),
                    "why_early":preview.WHY_EARLY if qualified else None,
                    "invalidation_observation":preview.INVALIDATION if qualified else None,"catalyst_status":"UNVERIFIED"}
                check()
            ranked=sorted((s for s in registry.SYMBOLS if computed[s]["decision"]=="WATCH"),
                          key=lambda s:(-computed[s]["score"],s))[:3]
            causal={"as_of":gate.as_of,"decisions":computed,"candidates":ranked}
            result.update(offline_status="PASS",reason="OFFLINE_VALIDATED_RESEARCH_PREVIEW",decisions=computed,
                candidates=ranked,total_candidates=len(ranked),decision_evidence_ref=_hash(causal),
                synthetic_closed_prices={s:payloads[s]["bars"][-1]["close"] for s in registry.SYMBOLS})
            _require(len(registry.canonical_json(result).encode("ascii"))<=MAX_OUTPUT_BYTES,corrections.Code.CONTEXT_INVALID)
            check()
    except corrections.Refused as exc:
        result["reason"]=exc.code.value
    except diagnostic.Refused as exc:
        result["reason"]=exc.reason.value
    except groundwork.Refused:
        result["reason"]="CLOCK_UNVERIFIED"
    except Exception:
        result["reason"]="WORKER_INVALID"
    if result["reason"]!="OFFLINE_VALIDATED_RESEARCH_PREVIEW":
        result.update(offline_status="BLOCKED",decisions=preview._empty_rows(),candidates=[],total_candidates=0,synthetic_closed_prices={})
        result.pop("decision_evidence_ref",None)
    if type(responses) is StaticResponses:
        result["fixtures_consumed"]=responses.consumed-consumed_before
    return result


def operator_report(result):
    """Bounded phone report, every observed price explicitly synthetic, no order fields."""
    rows={}
    for symbol in registry.SYMBOLS:
        row=result["decisions"][symbol]
        rows[symbol]={"decision":row["decision"],"features":row["features"],"score":row["score"],
            "why_early":row["why_early"],"invalidation_observation":row["invalidation_observation"],
            "catalyst":"UNVERIFIED","fixture_only_closed_price_usd":result["synthetic_closed_prices"].get(symbol),
            "source_status":result["source_rows"][symbol]["status"],"refusal":result["source_rows"][symbol]["reason"]}
    return {"run_id":result["run_id"],"source":SOURCE,"capture":result["capture"],
        "offline_status":result["offline_status"],"reason":result["reason"],"pairs":rows,
        "requests":0,"fixture_attempts":result["fixture_attempts"],"candidates":result["candidates"],
        "total_candidates":result["total_candidates"],"live_source_admission":"HOLD",
        "operational_mode":"HOLD","warning":"STATIC SYNTHETIC DEMO; NOT LIVE; NO ORDERS"}


def offline_demo():
    """One fixed immutable synthetic fixture; never loads arbitrary market files."""
    from pathlib import Path
    from datetime import datetime, timezone
    from email.utils import format_datetime
    path=Path(__file__).resolve().parent.parent/"tests/fixtures/kraken_reversal_groundwork_022.json"
    with path.open("rb") as source:
        raw=source.read(65537)
    _require(hashlib.sha256(raw).hexdigest()==DEMO_SHA256,corrections.Code.CONTEXT_INVALID)
    fixture=json.loads(raw)
    _require(fixture["label"]=="SYNTHETIC_TEST_ONLY_NOT_MARKET_CAPTURE",corrections.Code.CONTEXT_INVALID)
    value=fixture["input"]
    evidence=dict(value["clock_evidence"])
    evidence["valid_until_mono_ns"]=evidence["mono_ns"]+RUN_BUDGET_NS+10*diagnostic.NS
    class DemoClock:
        trusted=True  # Explicit synthetic test contract, never true UTC evidence.
        def __init__(self):self.mono=evidence["mono_ns"]
        def sample(self):
            value=diagnostic.Stamp(evidence["utc_ns"]+self.mono-evidence["mono_ns"],self.mono)
            self.mono+=1000;return value
        def monotonic_ns(self):
            value=self.mono;self.mono+=1000;return value
    wires=[]
    for symbol in registry.SYMBOLS:
        for stage in ("identity","ohlc"):
            observation=value["observations"][symbol][stage]
            payload=observation["payload"] if stage=="identity" else observation["capture"]["response"]
            body=registry.canonical_json(payload).encode("ascii")
            date=format_datetime(datetime.fromtimestamp(observation["service_date_utc_seconds"],timezone.utc),usegmt=True)
            wires.append(("HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nContent-Length: "+str(len(body))+"\r\nDate: "+date+"\r\n\r\n").encode("ascii")+body)
    return run_offline(responses=StaticResponses(tuple(wires)),clock=DemoClock(),clock_evidence=evidence,
        clock_evidence_verifier=lambda e,c:True,expected_context={k:evidence[k] for k in groundwork.CONTEXT_FIELDS},
        job_factory=SynchronousFixtureJob)


def main():
    import argparse
    parser=argparse.ArgumentParser(description="Static offline Kraken reversal integration demo; NO live option")
    parser.add_argument("--offline-demo",action="store_true")
    args=parser.parse_args()
    if not args.offline_demo:
        result=_base()
    else:
        try:result=offline_demo()
        except Exception:
            result=_base();result["reason"]="DEMO_INVALID"
    print(registry.canonical_json(operator_report(result)))
    return 0 if result["offline_status"]=="PASS" else 2


if __name__=="__main__":
    raise SystemExit(main())
