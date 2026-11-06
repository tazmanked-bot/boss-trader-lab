"""Static-source preview parity/adversarial tests. All price data is synthetic."""
import copy
from contextlib import ExitStack, redirect_stdout
import importlib
import io
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from research import spot_reversal_source_preview_023 as preview
from research import kraken_spot_reversal_bridge_prototype as prototype
from research import kraken_spot_diagnostic as diagnostic
from research import spot_reversal_candidates as candidates
from research import spot_refusal_registry as registry

ROOT = Path(__file__).parent / "fixtures"
FIXTURE = json.loads((ROOT/"kraken_reversal_groundwork_022.json").read_text())
T = FIXTURE["independent_synthetic_reference"]["as_of"]
CONTEXT = {k: FIXTURE["input"]["clock_evidence"][k] for k in prototype.CONTEXT_FIELDS}


class MockClock:
    trusted = True  # Existing TEST dependency contract, not actual attestation.

    def __init__(self):
        self.mono = 0
        self.utc = (T+2)*diagnostic.NS

    def sample(self):
        value = diagnostic.Stamp(self.utc+self.mono, self.mono)
        self.mono += 1000
        return value


def fixture():
    return copy.deepcopy(FIXTURE["input"])


def reference():
    return copy.deepcopy(FIXTURE["independent_synthetic_reference"])


def run(data=None, clock=None, verifier=None, context=None):
    return preview.preview_offline(json.dumps(fixture() if data is None else data),
        clock=MockClock() if clock is None else clock,
        clock_evidence_verifier=(lambda e,c: True) if verifier is None else verifier,
        expected_context=CONTEXT if context is None else context)


def source_rows(data,symbol="BTC/USD"):
    return data["observations"][symbol]["ohlc"]["capture"]["response"]["result"][diagnostic.IDENTITIES[symbol][1]]


def from_reference(ref):
    """Test construction only: original synthetic normalized -> invented raw rows."""
    data=fixture()
    for symbol in registry.SYMBOLS:
        rows=source_rows(data,symbol)
        current=rows[-1]
        rows[:]=[[b["open_time"],str(b["open"]),str(b["high"]),str(b["low"]),str(b["close"]),
                   str(b["close"]),str(b["volume"]),10] for b in ref["payloads"][symbol]["bars"]]+[current]
    return data


class SourcePreviewTests(unittest.TestCase):
    def setUp(self):
        stack=ExitStack(); self.addCleanup(stack.close)
        guards=[stack.enter_context(patch(name,side_effect=AssertionError("FORBIDDEN_IO")))
                for name in ("socket.socket","socket.create_connection","socket.getaddrinfo",
                             "urllib.request.urlopen","http.client.HTTPSConnection",
                             "subprocess.run","subprocess.Popen","time.time")]
        self.addCleanup(lambda:[g.assert_not_called() for g in guards])

    def assert_blocked(self,result):
        self.assertEqual(result["preview_status"],"BLOCKED")
        self.assertEqual(result["candidates"],[])
        self.assertEqual(result["requests"],0)
        self.assertEqual(result["live_source_admission"],"HOLD")
        self.assertTrue(all(r["decision"]=="BLOCKED" and r["score"] is None and r["features"] is None
                            for r in result["symbols"].values()))

    def parity(self,ref):
        result=run(from_reference(ref)); expected=candidates.evaluate(ref)
        self.assertEqual(result["preview_status"],"PASS")
        self.assertEqual(registry.canonical_json(result["symbols"]),registry.canonical_json(expected["symbols"]))
        self.assertEqual(registry.canonical_json(result["candidates"]),registry.canonical_json(expected["candidates"]))
        return result

    def test_positive_full_canonical_row_and_rank_parity(self):
        result=self.parity(reference())
        self.assertEqual(result["candidates"],["BTC/USD","SOL/USD","XRP/USD"])
        self.assertTrue(all(r["score"]==26666 for r in result["symbols"].values()))
        self.assertEqual(result["mode"],"STATIC_FIXTURE_EXPERIMENT_ONLY")
        self.assertEqual(result["source"],"STATIC_SYNTHETIC_KRAKEN_SHAPED")
        self.assertEqual(result["warning"],"candidate preview only; NOT LIVE; NO TRADING AUTHORITY")
        self.assertNotIn("label",result)

    def test_zero_one_two_three_watch_exact_parity(self):
        for n in range(4):
            ref=reference()
            for symbol in registry.SYMBOLS[n:]:
                for b in ref["payloads"][symbol]["bars"]:
                    b.update(open=100.0,high=100.0,low=100.0,close=100.0,volume=100.0)
            result=self.parity(ref)
            self.assertEqual(len(result["candidates"]),n)
            self.assertEqual(len(set(result["candidates"])),n)

    def test_exact_feature_function_reused_for_each_valid_symbol(self):
        original=candidates._features
        with patch.object(candidates,"_features",wraps=original) as function:
            result=run()
        self.assertEqual(result["preview_status"],"PASS")
        self.assertEqual(function.call_count,3)

    def test_never_calls_old_evaluator_or_relabels_source(self):
        with patch.object(candidates,"evaluate",side_effect=AssertionError("relabel forbidden")) as function:
            result=run()
        function.assert_not_called()
        self.assertEqual(result["source_tag"],prototype.SOURCE_TAG)
        self.assertEqual(result["fixture_origin"],prototype.FIXTURE_ORIGIN)

    def test_existing_prototype_stays_hold_and_original_evaluator_blocks_feed(self):
        before=prototype.run_offline(json.dumps(fixture()),clock=MockClock(),clock_evidence_verifier=lambda e,c:True,expected_context=CONTEXT)
        result=run()
        after=prototype.run_offline(json.dumps(fixture()),clock=MockClock(),clock_evidence_verifier=lambda e,c:True,expected_context=CONTEXT)
        self.assertEqual(before,after)
        self.assertEqual(before["overall"],"HOLD")
        self.assertEqual(before["reason"],"CANDIDATE_SOURCE_TYPE_NOT_ADMITTED")
        rejected=candidates.evaluate(before["proposed_input"])
        self.assertEqual(rejected["candidates"],[])
        self.assertTrue(all(r["decision"]=="BLOCKED" for r in rejected["symbols"].values()))
        self.assertEqual(result["source_boundary"]["overall"],"HOLD")
        self.assertEqual(result["source_boundary"]["candidate_stage"],"NOT_ADMITTED")

    def test_volume_contradiction_zero_and_spike_parity(self):
        for previous,latest in ((80.0,90.0),(120.0,150.0),(80.0,201.0),(0.0,150.0),(80.0,0.0)):
            ref=reference();bars=ref["payloads"]["BTC/USD"]["bars"]
            bars[-2]["volume"],bars[-1]["volume"]=previous,latest
            self.assertEqual(self.parity(ref)["symbols"]["BTC/USD"]["decision"],"WAIT")

    def test_each_existing_feature_failure_has_exact_canonical_parity(self):
        for name,change in (
            ("slowing_downside",lambda b:b[-3].update(close=98.0)),
            ("low_retest_hold",lambda b:b[-1].update(low=97.0)),
            ("fresh_recovery",lambda b:b[-1].update(open=101.0)),
            ("volume_consistent",lambda b:b[-1].update(volume=90.0))):
            ref=reference();change(ref["payloads"]["BTC/USD"]["bars"])
            row=self.parity(ref)["symbols"]["BTC/USD"]
            self.assertEqual(row["decision"],"WAIT")
            self.assertFalse(row["features"][name]["passed"])

    def test_rally_flat_and_no_chase_parity(self):
        for kind in ("flat","rally","chase"):
            ref=reference();bars=ref["payloads"]["BTC/USD"]["bars"]
            if kind=="chase":bars[-1].update(close=103.0,high=104.0)
            else:
                for i,b in enumerate(bars):
                    c=100.0 if kind=="flat" else 100.0+i
                    b.update(open=c,high=c,low=c,close=c)
            self.assertEqual(self.parity(ref)["symbols"]["BTC/USD"]["decision"],"WAIT")

    def test_score_order_then_symbol_tie_is_stable(self):
        ref=reference()
        ref["payloads"]["XRP/USD"]["bars"][-1]["volume"]=175.0
        ref["payloads"]["SOL/USD"]["bars"][-1]["volume"]=125.0
        self.assertEqual(self.parity(ref)["candidates"],["XRP/USD","BTC/USD","SOL/USD"])
        ref["payloads"]=dict(reversed(list(ref["payloads"].items())))
        self.assertEqual(self.parity(ref)["candidates"],["XRP/USD","BTC/USD","SOL/USD"])

    def test_existing_ascending_fixture_exact_wait_parity(self):
        original=json.loads((ROOT/"spot_refusal_v1.json").read_text())["payload"]
        ref=reference()
        # Original fixture is one hour earlier; shift only this invented test
        # construction so its known 21 closes end at the frozen fixture axis.
        shift=T-(original["bars"][-1]["open_time"]+3600)
        for symbol in registry.SYMBOLS:
            ref["payloads"][symbol]=copy.deepcopy(original)
            ref["payloads"][symbol]["symbol"]=symbol
            for b in ref["payloads"][symbol]["bars"]:
                b["open_time"]+=shift
                for k in ("open","high","low","close","volume"):b[k]=float(b[k])
        self.assertEqual(self.parity(ref)["candidates"],[])

    def test_binary_float_boundary_and_integer_exact_boundary_parity(self):
        ref=reference();ref["payloads"]["BTC/USD"]["bars"][-1]["low"]=98.98
        self.assertEqual(self.parity(ref)["symbols"]["BTC/USD"]["decision"],"WAIT")
        ref=reference();bars=ref["payloads"]["BTC/USD"]["bars"]
        for b in bars:
            for k in ("open","high","low","close"):b[k]*=100
        bars[-1]["low"]=9898.0
        self.assertEqual(self.parity(ref)["symbols"]["BTC/USD"]["decision"],"WATCH")

    def test_future_current_values_preserve_complete_preview_output(self):
        baseline=registry.canonical_json(run())
        for value in (None,-1,1e99,"DO_NOT_ECHO",{"ignored":True}):
            data=fixture()
            for symbol in registry.SYMBOLS:source_rows(data,symbol)[-1][1:]=[value]*7
            self.assertEqual(registry.canonical_json(run(data)),baseline)

    def test_future_append_beyond_clock_refuses_not_lookahead(self):
        data=fixture();source_rows(data).append([T+3600,"1","1","1","1","1","1",0])
        result=run(data);self.assert_blocked(result)
        self.assertEqual(result["source_boundary"]["reason"],"COMMITMENT_CONFLICT")

    def test_invalid_eligible_history_always_blocks_before_feature(self):
        for symbol in registry.SYMBOLS:
            data=fixture();source_rows(data,symbol)[0][4]="-1"
            with patch.object(candidates,"_features",side_effect=AssertionError("invalid input reached features")) as features:
                result=run(data)
            features.assert_not_called();self.assert_blocked(result)
            self.assertEqual(result["source_boundary"]["reason"],"BRIDGE_REFUSED")

    def test_partial_source_batch_blocks_all_preview_and_retains_stage_causes(self):
        data=fixture();data["observations"]["XRP/USD"]["ohlc"]["http_status"]=451
        result=run(data);self.assert_blocked(result)
        self.assertEqual(result["source_boundary"]["symbols"]["BTC/USD"]["status"],"VALIDATED_PROPOSED_DATA")
        self.assertEqual(result["source_boundary"]["symbols"]["XRP/USD"]["reason"],"HTTP_REFUSED")
        self.assertEqual(result["source_boundary"]["symbols"]["SOL/USD"]["status"],"NOT_ATTEMPTED")

    def test_gap_duplicate_order_and_stale_refusal_precedence(self):
        for kind,reason in (("gap","TIMESTAMP_GAP"),("duplicate","DUPLICATE_TIMESTAMP"),
                            ("order","TIMESTAMP_ORDER"),("stale","COMMITMENT_CONFLICT")):
            data=fixture();rows=source_rows(data)
            if kind=="gap":rows.pop(10)
            elif kind=="duplicate":rows.insert(10,copy.deepcopy(rows[0]))
            elif kind=="order":rows[0],rows[1]=rows[1],rows[0]
            else:
                for r in rows[:-1]:r[0]-=4*3600
            result=run(data);self.assert_blocked(result)
            if kind=="stale":self.assertEqual(result["source_boundary"]["reason"],reason)
            else:self.assertEqual(result["source_boundary"]["symbols"]["BTC/USD"]["bridge"]["decision"]["reason_code"],reason)

    def test_uncommitted_final_row_warmup_and_current_boundary(self):
        data=fixture();source_rows(data).pop()
        self.assertEqual(run(data)["source_boundary"]["reason"],"COMMITMENT_CONFLICT")
        data=fixture();source_rows(data).pop(0)
        result=run(data);self.assert_blocked(result)
        self.assertEqual(result["source_boundary"]["symbols"]["BTC/USD"]["bridge"]["decision"]["reason_code"],"WARMUP_INCOMPLETE")

    def test_eligible_ohlcv_types_values_vwap_count_refuse(self):
        for column in (1,2,3,4,5,6):
            for value in ("-1","NaN","Infinity",True,None,"1e999"):
                data=fixture();source_rows(data)[10][column]=value
                self.assert_blocked(run(data))
        for value in (-1,True,"10",2**53):
            data=fixture();source_rows(data)[10][7]=value;self.assert_blocked(run(data))

    def test_mixed_usdt_bad_metadata_and_unsupported_aliases_refuse(self):
        for location in ("capture","identity"):
            data=fixture()
            if location=="capture":data["observations"]["BTC/USD"]["ohlc"]["capture"]["quote"]="USDT"
            else:data["observations"]["BTC/USD"]["identity"]["payload"]["result"]["XXBTZUSD"]["quote"]="USDT"
            self.assert_blocked(run(data))
        data=fixture();body=data["observations"]["XRP/USD"]["identity"]["payload"]["result"]
        body["XRPUSD"]=body.pop("XXRPZUSD")
        result=run(data);self.assert_blocked(result)
        self.assertEqual(result["source_boundary"]["reason"],"ALIAS_CHANGED")

    def test_real_source_tag_and_fake_verified_markers_cannot_admit(self):
        for field,value in (("source_tag","VERIFIED_PUBLIC_SPOT_OBSERVATION"),("source_tag","SYNTHETIC_ONLY"),
                            ("fixture_origin","REAL_KRAKEN_CAPTURE"),("verified",True),("trusted",True)):
            data=fixture();data[field]=value;result=run(data);self.assert_blocked(result)
        data=fixture();data["clock_evidence"]["kind"]="REAL_TRUSTED_CLOCK"
        self.assertEqual(run(data)["source_boundary"]["reason"],"CLOCK_UNVERIFIED")

    def test_missing_provenance_context_and_false_verifier_refuse(self):
        self.assert_blocked(preview.preview_offline(json.dumps(fixture())))
        self.assert_blocked(run(context={}))
        self.assert_blocked(run(verifier=lambda e,c:False))
        for field in prototype.CONTEXT_FIELDS:
            data=fixture();data["clock_evidence"][field]="mismatch";self.assert_blocked(run(data))

    def test_copied_feed_report_or_hash_is_not_an_admission_interface(self):
        source=prototype.run_offline(json.dumps(fixture()),clock=MockClock(),clock_evidence_verifier=lambda e,c:True,expected_context=CONTEXT)
        for value in (source,source["proposed_input"],{"evidence_ref":source["evidence_ref"],"verified":True}):
            self.assert_blocked(run(value))

    def test_high_scores_cannot_bypass_schema_or_blocked_source(self):
        for location in ("root","capture","row"):
            data=fixture()
            if location=="root":data["score"]=10**9
            elif location=="capture":data["observations"]["BTC/USD"]["ohlc"]["capture"]["score"]=10**9
            else:source_rows(data)[0].append(10**9)
            with patch.object(candidates,"_features",side_effect=AssertionError("score bypass")) as features:
                self.assert_blocked(run(data))
            features.assert_not_called()

    def test_expired_clock_date_conflict_and_processing_deadline_refuse(self):
        data=fixture();data["clock_evidence"]["valid_until_mono_ns"]=10*diagnostic.NS
        self.assertEqual(run(data)["source_boundary"]["reason"],"CLOCK_UNVERIFIED")
        data=fixture();data["observations"]["BTC/USD"]["ohlc"]["service_date_utc_seconds"]=T+10
        self.assertEqual(run(data)["source_boundary"]["reason"],"SERVICE_TIME_CONFLICT")
        clock=MockClock()
        def delayed(e,c):clock.mono=10*diagnostic.NS;return True
        self.assertEqual(run(clock=clock,verifier=delayed)["source_boundary"]["reason"],"TIMEOUT")

    def test_feature_work_deadline_equality_discards_all_partial_watch(self):
        clock=MockClock();original=candidates._features
        def slow(bars):
            result=original(bars);clock.mono=diagnostic.DEADLINE_NS;return result
        with patch.object(candidates,"_features",side_effect=slow):result=run(clock=clock)
        self.assert_blocked(result)
        self.assertEqual(result["preview_blocker"],"TIMEOUT")

    def test_post_source_clock_reversal_and_jump_refuse(self):
        for kind in ("reverse","jump"):
            clock=MockClock();original=candidates._features
            def corrupt(bars):
                result=original(bars)
                if kind=="reverse":clock.mono=-1
                else:clock.utc+=2*diagnostic.NS
                return result
            with patch.object(candidates,"_features",side_effect=corrupt):result=run(clock=clock)
            self.assert_blocked(result)
            self.assertIn(result["preview_blocker"],("CLOCK_CONFLICT","CLOCK_UNVERIFIED"))

    def test_registry_revalidation_refuses_internal_feed_mutation_before_features(self):
        original=prototype.run_offline
        def mutate(*args,**kwargs):
            result=original(*args,**kwargs)
            result["proposed_input"]["payloads"]["XRP/USD"]["bars"][0]["close"]=-1
            return result
        with patch.object(prototype,"run_offline",side_effect=mutate),patch.object(candidates,"_features",side_effect=AssertionError("registry bypass")) as features:
            result=run()
        features.assert_not_called();self.assert_blocked(result)
        self.assertEqual(result["preview_blocker"],"REGISTRY_REFUSED")

    def test_copied_parity_hash_or_ineligible_normalized_row_cannot_rescue(self):
        original=prototype.run_offline
        def mutate(*args,**kwargs):
            result=original(*args,**kwargs)
            result["proposed_input"]["payloads"]["BTC/USD"]["bars"][0]["volume"]+=1
            return result
        with patch.object(prototype,"run_offline",side_effect=mutate):result=run()
        self.assert_blocked(result);self.assertEqual(result["preview_blocker"],"REGISTRY_PARITY_MISMATCH")
        def append(*args,**kwargs):
            result=original(*args,**kwargs);bars=result["proposed_input"]["payloads"]["BTC/USD"]["bars"]
            bars.append({**bars[-1],"open_time":T});return result
        with patch.object(prototype,"run_offline",side_effect=append):result=run()
        self.assert_blocked(result);self.assertEqual(result["preview_blocker"],"INELIGIBLE_NORMALIZED_ROW")

    def test_internal_source_state_cannot_be_promoted_to_live(self):
        original=prototype.run_offline
        def promote(*args,**kwargs):
            result=original(*args,**kwargs);result["overall"]="GO";return result
        with patch.object(prototype,"run_offline",side_effect=promote):result=run()
        self.assert_blocked(result);self.assertEqual(result["preview_blocker"],"SOURCE_BOUNDARY_INVALID")
        self.assertIsNone(result["source_boundary"])

    def test_parser_size_and_structural_errors_fail_closed(self):
        for text in ('{"x":1,"x":2}',"NaN","1e999","["*2000,"\ud800"," "*(prototype.MAX_INPUT_BYTES+1)):
            result=preview.preview_offline(text,clock=MockClock(),clock_evidence_verifier=lambda e,c:True,expected_context=CONTEXT)
            self.assert_blocked(result)
        for field in ("clock_evidence","observations","fixture_origin"):
            data=fixture();del data[field];self.assert_blocked(run(data))

    def test_output_is_bounded_deterministic_and_does_not_mutate_input(self):
        data=fixture();before=copy.deepcopy(data)
        first=registry.canonical_json(run(data))
        self.assertEqual(first,registry.canonical_json(run(data)))
        self.assertEqual(data,before)
        self.assertLessEqual(len(first.encode()),preview.MAX_OUTPUT_BYTES)
        self.assertNotIn("IGNORED_CURRENT",first)
        self.assertNotIn("payloads",first)

    def test_disabled_cli_flags_and_no_file_input(self):
        with patch("sys.argv",["preview","--live","--authorize"]),patch("builtins.open",side_effect=AssertionError("file activation")),redirect_stdout(io.StringIO()) as out:
            self.assertEqual(preview.main(),2)
        result=json.loads(out.getvalue());self.assert_blocked(result)
        self.assertEqual(result["preview_blocker"],"AUTHORIZATION_MISSING")

    def test_import_reload_and_default_never_start_or_admit(self):
        with patch("builtins.open",side_effect=AssertionError("file activation")):
            importlib.reload(preview)
            self.assert_blocked(preview.preview_offline())

    def test_exception_from_post_source_dependency_cannot_echo_raw_text(self):
        class FailingClock(MockClock):
            fail=False
            def sample(self):
                if self.fail:raise preview.Refused("DO_NOT_ECHO")
                return super().sample()
        clock=FailingClock();original=candidates._features
        def fail_later(bars):
            result=original(bars);clock.fail=True;return result
        with patch.object(candidates,"_features",side_effect=fail_later):result=run(clock=clock)
        self.assert_blocked(result)
        self.assertEqual(result["preview_blocker"],"PREVIEW_INVALID")
        self.assertNotIn("DO_NOT_ECHO",registry.canonical_json(result))

    def test_hashing_work_deadline_is_checked_before_return(self):
        clock=MockClock();original=preview._hash
        def slow_hash(value):
            result=original(value);clock.mono=diagnostic.DEADLINE_NS;return result
        with patch.object(preview,"_hash",side_effect=slow_hash):result=run(clock=clock)
        self.assert_blocked(result);self.assertEqual(result["preview_blocker"],"TIMEOUT")
        self.assertNotIn("preview_evidence_ref",result)

    def test_nonfinite_shared_output_cannot_leak_a_pass_or_partial_candidates(self):
        original=candidates._features
        def corrupt(bars):
            result=original(bars);result["fresh_recovery"]["strength_bps"]=float("nan");return result
        with patch.object(candidates,"_features",side_effect=corrupt):result=run()
        self.assert_blocked(result);self.assertEqual(result["preview_blocker"],"PREVIEW_INVALID")


if __name__ == "__main__":
    unittest.main()
