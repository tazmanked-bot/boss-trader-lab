"""Offline end-to-end raw-fixture sequencing, safeguards and candidate parity."""
import copy
from contextlib import ExitStack,redirect_stdout,redirect_stderr
from datetime import datetime,timezone
from email.utils import format_datetime
import importlib
import io
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from research import manual_kraken_reversal_024 as manual
from research import kraken_spot_diagnostic as diagnostic
from research import kraken_probe_corrections as corrections
from research import spot_reversal_candidates as candidates
from research import spot_refusal_registry as registry

FIXTURE=json.loads((Path(__file__).parent/"fixtures/kraken_reversal_groundwork_022.json").read_text())
T=FIXTURE["independent_synthetic_reference"]["as_of"]


class Clock:
    trusted=True
    def __init__(self):self.mono=0;self.utc=(T+2)*diagnostic.NS
    def sample(self):
        value=diagnostic.Stamp(self.utc+self.mono,self.mono);self.mono+=1000;return value
    def monotonic_ns(self):
        value=self.mono;self.mono+=1000;return value


def evidence():
    result=copy.deepcopy(FIXTURE["input"]["clock_evidence"])
    result["valid_until_mono_ns"]=manual.RUN_BUDGET_NS+10*diagnostic.NS
    return result


def wire(payload,status=200,date=T+2,extra=b"",body=None):
    body=registry.canonical_json(payload).encode("ascii") if body is None else body
    header=("HTTP/1.1 "+str(status)+" Fixture\r\nContent-Type: application/json\r\nContent-Length: "+str(len(body))+
            "\r\nDate: "+format_datetime(datetime.fromtimestamp(date,timezone.utc),usegmt=True)+"\r\n").encode("ascii")
    return header+extra+b"\r\n"+body


def payloads():
    obs=copy.deepcopy(FIXTURE["input"]["observations"])
    return [obs[s]["identity"]["payload"] if stage=="IDENTITY" else obs[s]["ohlc"]["capture"]["response"]
            for s in registry.SYMBOLS for stage in ("IDENTITY","OHLC")]


def wires(values=None):return [wire(p) for p in (payloads() if values is None else values)]


def execute(values=None,clock=None,job_factory=None,proof=None,responses=None,verifier=None):
    proof=evidence() if proof is None else proof
    return manual.run_offline(responses=manual.StaticResponses(tuple(wires() if values is None else values)) if responses is None else responses,
        clock=Clock() if clock is None else clock,clock_evidence=proof,
        clock_evidence_verifier=(lambda e,c:True) if verifier is None else verifier,
        expected_context={k:evidence()[k] for k in ("revision","run_id","boot_scope")},
        job_factory=manual.SynchronousFixtureJob if job_factory is None else job_factory)


def reference():return copy.deepcopy(FIXTURE["independent_synthetic_reference"])


def from_reference(ref):
    values=payloads()
    for i,s in enumerate(registry.SYMBOLS):
        key=diagnostic.IDENTITIES[s][1]
        current=values[2*i+1]["result"][key][-1]
        values[2*i+1]["result"][key]=[[b["open_time"],str(b["open"]),str(b["high"]),str(b["low"]),str(b["close"]),
            str(b["close"]),str(b["volume"]),10] for b in ref["payloads"][s]["bars"]]+[current]
    return wires(values)


class ManualIntegrationTests(unittest.TestCase):
    def setUp(self):
        stack=ExitStack();self.addCleanup(stack.close)
        guards=[stack.enter_context(patch(name,side_effect=AssertionError("FORBIDDEN_IO"))) for name in (
            "socket.socket","socket.create_connection","socket.getaddrinfo","urllib.request.urlopen",
            "http.client.HTTPSConnection","subprocess.run","subprocess.Popen","time.time")]
        self.addCleanup(lambda:[g.assert_not_called() for g in guards])

    def blocked(self,result):
        self.assertEqual(result["overall"],"HOLD")
        self.assertEqual(result["offline_status"],"BLOCKED")
        self.assertEqual(result["requests"],0)
        self.assertEqual(result["total_candidates"],0)
        self.assertEqual(result["candidates"],[])
        self.assertEqual(result["synthetic_closed_prices"],{})
        self.assertTrue(all(r["decision"]=="BLOCKED" and r["features"] is None for r in result["decisions"].values()))

    def test_full_six_stage_pipeline_exact_canonical_candidate_parity(self):
        result=execute();expected=candidates.evaluate(reference())
        self.assertEqual(result["offline_status"],"PASS")
        self.assertEqual(registry.canonical_json(result["decisions"]),registry.canonical_json(expected["symbols"]))
        self.assertEqual(result["candidates"],expected["candidates"])
        self.assertEqual(result["fixture_attempts"],6)
        self.assertEqual(result["fixtures_consumed"],6)
        self.assertEqual([(r["pair"],r["stage"]) for r in result["receipts"]],
            [(s,t) for s in registry.SYMBOLS for t in ("IDENTITY","OHLC")])
        self.assertEqual(result["requests"],0)
        self.assertTrue(all(r["supervisor"]["cleanup"]=="REAPED" for r in result["receipts"]))

    def test_zero_one_two_three_and_ties_without_forced_candidate(self):
        for n in range(4):
            ref=reference()
            for s in registry.SYMBOLS[n:]:
                for b in ref["payloads"][s]["bars"]:b.update(open=100.0,high=100.0,low=100.0,close=100.0,volume=100.0)
            result=execute(from_reference(ref));expected=candidates.evaluate(ref)
            self.assertEqual(result["offline_status"],"PASS")
            self.assertEqual(result["candidates"],expected["candidates"])
            self.assertEqual(len(result["candidates"]),n)
            self.assertEqual(registry.canonical_json(result["decisions"]),registry.canonical_json(expected["symbols"]))

    def test_different_scores_and_partial_feature_wait_parity(self):
        ref=reference();ref["payloads"]["XRP/USD"]["bars"][-1]["volume"]=175.0
        ref["payloads"]["SOL/USD"]["bars"][-1]["volume"]=90.0
        result=execute(from_reference(ref));expected=candidates.evaluate(ref)
        self.assertEqual(result["candidates"],["XRP/USD","BTC/USD"])
        self.assertEqual(result["decisions"],expected["symbols"])

    def test_existing_shared_feature_function_is_used_without_evaluator_relabel(self):
        original=candidates._features
        with patch.object(candidates,"_features",wraps=original) as features,patch.object(candidates,"evaluate",side_effect=AssertionError("relabel")) as evaluate:
            result=execute()
        self.assertEqual(result["offline_status"],"PASS")
        self.assertEqual(features.call_count,3);evaluate.assert_not_called()

    def test_each_http_failure_slot_globally_stops_no_retry(self):
        for index in range(6):
            for status in (451,429,301):
                responses=wires();responses[index]=wire({},status=status)
                result=execute(responses);self.blocked(result)
                self.assertEqual(result["fixture_attempts"],index+1)
                self.assertEqual(result["fixtures_consumed"],index+1)
                self.assertEqual(result["reason"],"REDIRECT_REFUSED" if status==301 else "HTTP_REFUSED")
                self.assertEqual(len(result["receipts"]),index+1)

    def test_source_error_before_identity_cannot_attempt_ohlc(self):
        values=payloads();values[0]["error"]=["DO_NOT_ECHO"]
        result=execute(wires(values));self.blocked(result)
        self.assertEqual(result["reason"],"API_ERROR")
        self.assertEqual(result["fixtures_consumed"],1)
        self.assertNotIn("DO_NOT_ECHO",registry.canonical_json(result))

    def test_xrp_failure_retains_btc_source_but_no_partial_watch(self):
        responses=wires();responses[3]=wire({},451)
        result=execute(responses);self.blocked(result)
        self.assertEqual(result["source_rows"]["BTC/USD"]["status"],"VALIDATED_STATIC_DATA")
        self.assertEqual(result["source_rows"]["SOL/USD"]["status"],"NOT_ATTEMPTED")

    def test_identity_alias_quote_status_and_optional_schema_refuse(self):
        for field,value in (("quote","USDT"),("status","cancel_only"),("wsname","BTC/USD"),("fees","unsupported")):
            values=payloads();values[0]["result"]["XXBTZUSD"][field]=value
            result=execute(wires(values));self.blocked(result)
            self.assertEqual(result["reason"],"IDENTITY_UNVERIFIED")
            self.assertEqual(result["fixtures_consumed"],1)
        values=payloads();values[0]["result"]["XBTUSD"]=values[0]["result"].pop("XXBTZUSD")
        self.assertEqual(execute(wires(values))["reason"],"ALIAS_CHANGED")

    def test_bounded_header_line_count_framing_and_body_failures(self):
        invalid=[wire({},extra=b"X-Long: "+b"x"*1024+b"\r\n"),
                 wire({},extra=b"X-A: a\r\nX-A: b\r\n"),
                 wire({},extra=b"Transfer-Encoding: chunked\r\n"),
                 wire({},extra=b"Content-Encoding: gzip\r\n"),
                 wire({})+b"trailer",wire({})[:-1],wire({}).replace(b"\r\n",b"\n")]
        expected=("LINE_LIMIT","HEADER_INVALID","AMBIGUOUS_FRAMING","COMPRESSION_REFUSED",
                  "TRAILING_DATA","PREMATURE_EOF","FRAMING_INVALID")
        for response,reason in zip(invalid,expected):
            responses=wires();responses[0]=response
            result=execute(responses);self.blocked(result);self.assertEqual(result["reason"],reason)

    def test_bad_json_utf8_duplicate_overflow_and_non_object_refuse(self):
        for body in (b'{"a":1,"a":2}',b'{"x":NaN}',b'{"x":1e999}',b'\xff',b'[]',b'{'*2000):
            responses=wires();responses[0]=wire({},body=body)
            result=execute(responses);self.blocked(result);self.assertEqual(result["reason"],"JSON_INVALID")

    def test_real_driver_or_subclass_and_invalid_response_sizes_refuse(self):
        class FakeNetwork:
            def take(self,request):raise AssertionError("must not be called")
        result=execute(responses=FakeNetwork());self.blocked(result)
        self.assertEqual(result["reason"],"CONTEXT_INVALID")
        class Subclass(manual.StaticResponses):pass
        self.blocked(execute(responses=Subclass(tuple(wires()))))
        with self.assertRaises(corrections.Refused):manual.StaticResponses(tuple(wires()[:5]))
        with self.assertRaises(corrections.Refused):manual.StaticResponses((b"x"*(corrections.WIRE_LIMIT+1),)*6)

    def test_single_shot_responses_cannot_be_reused_even_after_failure(self):
        for status in (200,451):
            responses=wires()
            if status!=200:responses[0]=wire({},status)
            sealed=manual.StaticResponses(tuple(responses))
            execute(responses=sealed)
            again=execute(responses=sealed);self.blocked(again)
            self.assertEqual(again["reason"],"CONTEXT_INVALID")
            self.assertEqual(again["fixture_attempts"],0)
            self.assertEqual(again["fixtures_consumed"],0)

    def test_request_plan_identity_pair_path_since_and_budget_are_fixed(self):
        response=manual.StaticResponses(tuple(wires()));response.claim(T)
        bad=diagnostic.Request("BTC/USD","/0/public/OHLC",(("pair","XBTUSD"),("interval",60),("since",T-86400)))
        with self.assertRaises(corrections.Refused):response.take(bad)
        self.assertEqual(response.consumed,0)
        self.assertIn("pair=XBTUSD",manual._request("BTC/USD","IDENTITY",T).target())

    def test_missing_context_verifier_and_real_clock_marker_never_admit(self):
        proof=evidence();proof["kind"]="REAL_ATTESTATION"
        result=execute(proof=proof);self.blocked(result);self.assertEqual(result["fixture_attempts"],0)
        self.blocked(execute(verifier=lambda e,c:False))
        proof=evidence();proof["trusted"]=True;self.blocked(execute(proof=proof))
        self.blocked(manual.run_offline(responses=manual.StaticResponses(tuple(wires()))))

    def test_full_run_clock_horizon_and_two_second_bound_are_required(self):
        for field,value in (("uncertainty_ns",2*diagnostic.NS+1),("valid_until_mono_ns",manual.RUN_BUDGET_NS),
                            ("utc_ns",True),("run_id","wrong")):
            proof=evidence();proof[field]=value
            result=execute(proof=proof);self.blocked(result)
            self.assertEqual(result["fixture_attempts"],0)

    def test_delayed_factory_cannot_release_after_ten_second_expiry(self):
        clock=Clock();jobs=[]
        def delayed(request,action,c,deadline):
            job=manual.SynchronousFixtureJob(request,action,c,deadline);jobs.append(job)
            clock.mono=deadline;return job
        result=execute(clock=clock,job_factory=delayed);self.blocked(result)
        self.assertEqual(result["reason"],"TIMEOUT")
        self.assertEqual(result["fixtures_consumed"],0)
        self.assertFalse(jobs[0].started)

    def test_slow_start_cannot_release_and_is_reaped(self):
        class SlowStart(manual.SynchronousFixtureJob):
            def start(self):super().start();self.clock.mono=self.deadline
        result=execute(job_factory=SlowStart);self.blocked(result)
        self.assertEqual(result["reason"],"TIMEOUT")
        self.assertEqual(result["fixtures_consumed"],0)
        self.assertFalse(result["receipts"][0]["supervisor"]["released"])
        self.assertEqual(result["receipts"][0]["supervisor"]["cleanup"],"REAPED")

    def test_not_ready_job_and_unreaped_cleanup_are_global_failures(self):
        class NeverReady(manual.SynchronousFixtureJob):
            def ready(self):return False
            def wait(self,seconds):self.clock.mono=self.deadline
        result=execute(job_factory=NeverReady);self.blocked(result);self.assertEqual(result["reason"],"TIMEOUT")
        class Unreaped(manual.SynchronousFixtureJob):
            def reap(self):return False
        result=execute(job_factory=Unreaped);self.blocked(result)
        self.assertEqual(result["reason"],"WORKER_UNREAPED")
        self.assertEqual(result["fixture_attempts"],1)

    def test_completed_without_payload_cannot_be_trusted(self):
        class NoPayload(manual.SynchronousFixtureJob):
            def release(self):self.code=corrections.Code.COMPLETED;self.done=True
        result=execute(job_factory=NoPayload);self.blocked(result)
        self.assertEqual(result["reason"],"WORKER_INVALID")
        self.assertEqual(result["fixtures_consumed"],0)

    def test_request_payload_validation_and_normalization_in_deadline(self):
        original=manual.groundwork._normalize
        clock=Clock()
        def slow(*args):
            result=original(*args);clock.mono+=diagnostic.DEADLINE_NS;return result
        with patch.object(manual.groundwork,"_normalize",side_effect=slow):result=execute(clock=clock)
        self.blocked(result);self.assertEqual(result["reason"],"TIMEOUT")
        self.assertEqual(result["fixture_attempts"],2)

    def test_clock_jump_reversal_and_http_date_conflict_refuse(self):
        class Jump(Clock):
            def sample(self):
                if self.mono:self.utc+=2*diagnostic.NS
                return super().sample()
        result=execute(clock=Jump());self.blocked(result)
        self.assertEqual(result["reason"],"CLOCK_CONFLICT")
        responses=wires();responses[0]=wire({},date=T+10)
        self.assertEqual(execute(responses)["reason"],"SERVICE_TIME_CONFLICT")

    def test_eligible_prices_volume_vwap_count_and_high_score_refuse(self):
        for column,value in ((1,"-1"),(3,"0"),(4,"NaN"),(5,"999999"),(6,"-1"),(7,-1)):
            values=payloads();values[1]["result"]["XXBTZUSD"][0][column]=value
            result=execute(wires(values));self.blocked(result);self.assertEqual(result["reason"],"BRIDGE_REFUSED")
        values=payloads();values[1]["result"]["XXBTZUSD"][0].append(10**9)
        self.assertEqual(execute(wires(values))["reason"],"COMMITMENT_CONFLICT")

    def test_full_history_and_warmup_cannot_be_bypassed_by_favorable_recent_rows(self):
        values=payloads();rows=values[1]["result"]["XXBTZUSD"]
        rows.insert(0,copy.deepcopy(rows[0]));rows[0][0]-=3600;rows[0][4]="-1"
        with patch.object(candidates,"_features",side_effect=AssertionError("invalid reached features")) as feature:
            result=execute(wires(values))
        feature.assert_not_called();self.blocked(result)
        values=payloads();values[1]["result"]["XXBTZUSD"].pop(0)
        result=execute(wires(values));self.blocked(result)
        self.assertEqual(result["source_rows"]["BTC/USD"]["bridge"]["decision"]["reason_code"],"WARMUP_INCOMPLETE")

    def test_gap_duplicate_order_stale_and_uncommitted_precedence(self):
        for mode,reason in (("gap","TIMESTAMP_GAP"),("duplicate","DUPLICATE_TIMESTAMP"),("order","TIMESTAMP_ORDER"),
                            ("stale","COMMITMENT_CONFLICT"),("last","COMMITMENT_CONFLICT")):
            values=payloads();rows=values[1]["result"]["XXBTZUSD"]
            if mode=="gap":rows.pop(10)
            elif mode=="duplicate":rows.insert(10,copy.deepcopy(rows[0]))
            elif mode=="order":rows[0],rows[1]=rows[1],rows[0]
            elif mode=="stale":
                for r in rows[:-1]:r[0]-=4*3600
            else:rows.pop()
            result=execute(wires(values));self.blocked(result)
            if mode in ("stale","last"):self.assertEqual(result["reason"],reason)
            else:self.assertEqual(result["source_rows"]["BTC/USD"]["bridge"]["decision"]["reason_code"],reason)

    def test_current_bar_values_do_not_change_complete_causal_decisions_or_refs(self):
        baseline=execute()
        for value in (None,"IGNORED",-1,1e99,{"future":True}):
            values=payloads()
            for index,symbol in enumerate(registry.SYMBOLS):
                values[2*index+1]["result"][diagnostic.IDENTITIES[symbol][1]][-1][1:]=[value]*7
            result=execute(wires(values))
            self.assertEqual(result["decisions"],baseline["decisions"])
            self.assertEqual(result["decision_evidence_ref"],baseline["decision_evidence_ref"])
            self.assertEqual(result["candidates"],baseline["candidates"])
            self.assertTrue(all(result["source_rows"][s]["bridge"]["evidence_ref"]==baseline["source_rows"][s]["bridge"]["evidence_ref"] for s in registry.SYMBOLS))

    def test_future_timestamp_boundary_and_nonfinite_json_refuse(self):
        values=payloads();rows=values[1]["result"]["XXBTZUSD"]
        rows.append([T+3600,"1","1","1","1","1","1",0])
        self.assertEqual(execute(wires(values))["reason"],"COMMITMENT_CONFLICT")
        responses=wires();responses[1]=wire({},body=b'{"x":NaN}')
        self.assertEqual(execute(responses)["reason"],"JSON_INVALID")

    def test_late_feature_failure_cannot_publish_partial_candidates(self):
        clock=Clock();original=candidates._features
        def late(bars):
            value=original(bars);clock.mono=manual.RUN_BUDGET_NS;return value
        with patch.object(candidates,"_features",side_effect=late):result=execute(clock=clock)
        self.blocked(result);self.assertEqual(result["reason"],"TIMEOUT")
        self.assertNotIn("decision_evidence_ref",result)

    def test_nonfinite_shared_output_never_reports_pass(self):
        original=candidates._features
        def corrupt(bars):
            result=original(bars);result["fresh_recovery"]["strength_bps"]=float("nan");return result
        with patch.object(candidates,"_features",side_effect=corrupt):result=execute()
        self.blocked(result);self.assertEqual(result["reason"],"WORKER_INVALID")

    def test_operator_report_is_phone_friendly_typed_and_has_no_order_authority(self):
        result=manual.operator_report(execute())
        self.assertEqual(result["source"],"STATIC_SYNTHETIC_KRAKEN_HTTP_FIXTURES")
        self.assertEqual(result["requests"],0)
        self.assertEqual(result["total_candidates"],3)
        self.assertEqual(result["live_source_admission"],"HOLD")
        self.assertIn("NO ORDERS",result["warning"])
        self.assertEqual(result["pairs"]["BTC/USD"]["fixture_only_closed_price_usd"],101.0)
        self.assertNotIn("payload",registry.canonical_json(result))
        self.assertLess(len(registry.canonical_json(result)),16384)

    def test_identical_inputs_are_reproducible_and_original_fixture_untouched(self):
        before=copy.deepcopy(FIXTURE)
        self.assertEqual(registry.canonical_json(execute()),registry.canonical_json(execute()))
        self.assertEqual(FIXTURE,before)

    def test_default_and_live_flags_cannot_activate_any_source(self):
        self.blocked(manual.run_offline())
        with patch("sys.argv",["manual"]),patch("builtins.open",side_effect=AssertionError("activation")),redirect_stdout(io.StringIO()) as out:
            self.assertEqual(manual.main(),2)
        self.assertEqual(json.loads(out.getvalue())["reason"],"AUTHORIZATION_MISSING")
        with patch("sys.argv",["manual","--live"]),redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as exc:manual.main()
        self.assertEqual(exc.exception.code,2)

    def test_explicit_offline_demo_uses_only_immutable_packaged_synthetic_fixture(self):
        with patch("sys.argv",["manual","--offline-demo"]),redirect_stdout(io.StringIO()) as out:
            self.assertEqual(manual.main(),0)
        result=json.loads(out.getvalue());self.assertEqual(result["requests"],0)
        self.assertEqual(result["fixture_attempts"],6)
        self.assertEqual(result["total_candidates"],3)
        with patch.object(manual,"DEMO_SHA256","0"*64):
            with self.assertRaises(corrections.Refused):manual.offline_demo()

    def test_demo_failure_redacts_paths_and_exceptions(self):
        with patch.object(manual,"offline_demo",side_effect=OSError("DO_NOT_ECHO")),patch("sys.argv",["manual","--offline-demo"]),redirect_stdout(io.StringIO()) as out:
            self.assertEqual(manual.main(),2)
        self.assertNotIn("DO_NOT_ECHO",out.getvalue())

    def test_import_and_default_have_no_file_or_clock_activation(self):
        with patch("builtins.open",side_effect=AssertionError("activation")):
            importlib.reload(manual);self.blocked(manual.run_offline())

    def test_existing_correction_module_reload_does_not_stale_enum_identity(self):
        importlib.reload(corrections)
        result=execute()
        self.assertEqual(result["offline_status"],"PASS")
        self.assertEqual(result["fixture_attempts"],6)
        self.assertEqual(result["coordinator_reason"],"ALL_STAGE_CHECKS_PASSED")

    def test_monotonic_reversal_in_supervision_prevents_fixture_consumption(self):
        class Reverse(Clock):
            def monotonic_ns(self):return -1
        result=execute(clock=Reverse());self.blocked(result)
        self.assertEqual(result["reason"],"CLOCK_CONFLICT")
        self.assertEqual(result["fixtures_consumed"],0)

    def test_output_hashing_expiry_discards_prepared_watch_rows(self):
        clock=Clock();original=manual._hash
        def delayed(value):
            result=original(value)
            if "decisions" in value:clock.mono=manual.RUN_BUDGET_NS
            return result
        with patch.object(manual,"_hash",side_effect=delayed):result=execute(clock=clock)
        self.blocked(result);self.assertEqual(result["reason"],"TIMEOUT")
        self.assertNotIn("decision_evidence_ref",result)


if __name__=="__main__":unittest.main()
