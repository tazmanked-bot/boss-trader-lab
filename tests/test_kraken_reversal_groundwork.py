"""Deterministic static fixture tests; no network, real clocks or market files."""
import copy
from contextlib import ExitStack, redirect_stdout
import importlib
import io
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from research import kraken_spot_reversal_bridge_prototype as prototype
from research import kraken_spot_diagnostic as diagnostic
from research import spot_refusal_registry as registry
from research import spot_reversal_candidates as candidates

FIXTURE = json.loads((Path(__file__).parent / "fixtures/kraken_reversal_groundwork_022.json").read_text())
T = FIXTURE["independent_synthetic_reference"]["as_of"]
CONTEXT = {k: FIXTURE["input"]["clock_evidence"][k] for k in prototype.CONTEXT_FIELDS}


class MockClock:
    trusted = True  # Existing CaptureClock TEST contract, never attestation.

    def __init__(self, utc_ns=(T+2)*diagnostic.NS):
        self.utc_ns, self.mono_ns = utc_ns, 0

    def sample(self):
        result = diagnostic.Stamp(self.utc_ns+self.mono_ns, self.mono_ns)
        self.mono_ns += 1000
        return result


def fixture():
    return copy.deepcopy(FIXTURE["input"])


def run(value=None, clock=None, verifier=None, context=None):
    value = fixture() if value is None else value
    return prototype.run_offline(json.dumps(value), clock=MockClock() if clock is None else clock,
        clock_evidence_verifier=(lambda e, c: True) if verifier is None else verifier,
        expected_context=CONTEXT if context is None else context)


def rows(value, symbol="BTC/USD"):
    return value["observations"][symbol]["ohlc"]["capture"]["response"]["result"][diagnostic.IDENTITIES[symbol][1]]


class GroundworkTests(unittest.TestCase):
    def setUp(self):
        stack = ExitStack()
        self.addCleanup(stack.close)
        guards = [stack.enter_context(patch(name, side_effect=AssertionError("FORBIDDEN_IO")))
                  for name in ("socket.socket", "socket.create_connection", "socket.getaddrinfo",
                               "urllib.request.urlopen", "http.client.HTTPSConnection",
                               "subprocess.run", "subprocess.Popen", "time.time")]
        self.addCleanup(lambda: [g.assert_not_called() for g in guards])

    def assert_stop(self, result, reason):
        self.assertEqual(result["overall"], "HOLD")
        self.assertEqual(result["reason"], reason)
        self.assertEqual(result["requests"], 0)
        self.assertIsNone(result["proposed_input"])

    def test_positive_source_normalization_and_independent_synthetic_parity(self):
        result = run()
        self.assertEqual(result["reason"], "CANDIDATE_SOURCE_TYPE_NOT_ADMITTED")
        self.assertEqual(result["overall"], "HOLD")
        self.assertEqual(result["requests"], 0)
        feed = result["proposed_input"]
        self.assertEqual(feed["source_tag"], "PUBLIC_SPOT_OBSERVATION_PROPOSED")
        self.assertNotIn("label", feed)
        reference = copy.deepcopy(FIXTURE["independent_synthetic_reference"])
        self.assertEqual(registry.canonical_json(feed["payloads"]), registry.canonical_json(reference["payloads"]))
        expected = candidates.evaluate(reference)  # Genuinely separate synthetic data, not a relabeled feed.
        self.assertEqual(expected["candidates"], ["BTC/USD", "SOL/USD", "XRP/USD"])
        for symbol in registry.SYMBOLS:
            self.assertEqual(result["symbols"][symbol]["bridge"]["decision"], expected["symbols"][symbol]["validation"])
            self.assertEqual(expected["symbols"][symbol]["score"], 26666)

    def test_adapter_never_calls_candidate_engine(self):
        with patch.object(candidates, "evaluate", side_effect=AssertionError("engine admission forbidden")) as engine:
            self.assertIsNotNone(run()["proposed_input"])
            engine.assert_not_called()

    def test_proposed_feed_is_rejected_by_unchanged_candidate_contract(self):
        result = candidates.evaluate(run()["proposed_input"])
        self.assertEqual(result["candidates"], [])
        self.assertTrue(all(r["decision"] == "BLOCKED" for r in result["symbols"].values()))

    def test_disabled_default_cli_and_flags_never_activate(self):
        self.assertEqual(prototype.run_offline()["reason"], "AUTHORIZATION_MISSING")
        with patch("sys.argv", ["prototype", "--live", "--authorize"]), redirect_stdout(io.StringIO()) as out:
            self.assertEqual(prototype.main(), 2)
        result = json.loads(out.getvalue())
        self.assertEqual(result["reason"], "AUTHORIZATION_MISSING")
        self.assertEqual(result["requests"], 0)

    def test_missing_or_unresolved_clock_evidence_refuses(self):
        text = json.dumps(fixture())
        self.assert_stop(prototype.run_offline(text), "CLOCK_UNVERIFIED")
        self.assert_stop(run(verifier=lambda e,c: False), "CLOCK_UNVERIFIED")
        self.assert_stop(run(verifier=lambda e,c: "trusted"), "CLOCK_UNVERIFIED")
        def failing(e,c): raise RuntimeError("DO_NOT_ECHO")
        self.assert_stop(run(verifier=failing), "CLOCK_UNVERIFIED")

    def test_clock_units_types_error_and_self_attested_boolean_fail(self):
        for field, value in (("uncertainty_ns", 2*diagnostic.NS+1), ("uncertainty_ns", -1),
                             ("utc_ns", True), ("mono_ns", "0"), ("authority", "self-signed"),
                             ("kind", "REAL_CLOCK")):
            data = fixture(); data["clock_evidence"][field] = value
            self.assert_stop(run(data), "CLOCK_UNVERIFIED")
        data = fixture(); data["clock_evidence"]["trusted"] = True
        self.assert_stop(run(data), "CLOCK_UNVERIFIED")

    def test_expired_or_insufficient_lease_and_binding_refuse(self):
        for expiry in (0, diagnostic.DEADLINE_NS):
            data = fixture(); data["clock_evidence"]["valid_until_mono_ns"] = expiry
            self.assert_stop(run(data), "CLOCK_UNVERIFIED")
        for field in prototype.CONTEXT_FIELDS:
            data = fixture(); data["clock_evidence"][field] = "different"
            self.assert_stop(run(data), "CLOCK_UNVERIFIED")

    def test_deadline_includes_parsing_and_verifier_at_equality(self):
        clock = MockClock()
        def delayed(e,c): clock.mono_ns = diagnostic.DEADLINE_NS; return True
        self.assert_stop(run(clock=clock, verifier=delayed), "TIMEOUT")
        self.assertEqual(clock.mono_ns, diagnostic.DEADLINE_NS+1000)

    def test_clock_reversal_and_wall_jump_refuse(self):
        class Reverse(MockClock):
            def sample(self):
                if self.mono_ns: return diagnostic.Stamp(self.utc_ns-1, -1)
                return super().sample()
        self.assert_stop(run(clock=Reverse()), "CLOCK_UNVERIFIED")
        class Jump(MockClock):
            def sample(self):
                if self.mono_ns: return diagnostic.Stamp(self.utc_ns+2*diagnostic.NS, self.mono_ns)
                return super().sample()
        self.assert_stop(run(clock=Jump()), "CLOCK_CONFLICT")

    def test_two_second_hour_boundary_and_twenty_bar_warmup(self):
        self.assertEqual(run()["proposed_input"]["as_of"], T)
        data = fixture(); data["clock_evidence"]["utc_ns"] = (T+1)*diagnostic.NS
        for observation in data["observations"].values():
            for stage in ("identity", "ohlc"): observation[stage]["service_date_utc_seconds"] = T+1
        result = run(data, clock=MockClock((T+1)*diagnostic.NS))
        self.assert_stop(result, "BRIDGE_REFUSED")
        self.assertEqual(result["symbols"]["BTC/USD"]["bridge"]["decision"]["reason_code"], "WARMUP_INCOMPLETE")

    def test_uncommitted_current_row_is_excluded_without_positional_repair(self):
        result = run()
        for payload in result["proposed_input"]["payloads"].values():
            self.assertEqual(len(payload["bars"]), 21)
            self.assertTrue(all(b["open_time"]+3600 <= T for b in payload["bars"]))
        data = fixture(); rows(data).pop()
        self.assert_stop(run(data), "COMMITMENT_CONFLICT")

    def test_excluded_current_values_cannot_change_complete_output(self):
        expected = registry.canonical_json(run())
        for value in (None, "DO_NOT_ECHO", -1, 1e99, {"ignored":True}):
            data = fixture()
            for symbol in registry.SYMBOLS:
                rows(data,symbol)[-1][1:] = [value]*7
            self.assertEqual(registry.canonical_json(run(data)), expected)

    def test_unjustified_future_timestamp_cannot_enter_or_extend_capture(self):
        data = fixture(); rows(data).append([T+3600, "1", "1", "1", "1", "1", "1", 0])
        self.assert_stop(run(data), "COMMITMENT_CONFLICT")
        data = fixture(); rows(data)[-1][0] = T+1
        self.assert_stop(run(data), "COMMITMENT_CONFLICT")

    def test_invalid_eligible_prices_volume_vwap_and_count_refuse(self):
        for index in (1,2,3,4,5,6):
            for bad in ("-1", "NaN", "Infinity", None, True, "1e999", "0" if index != 6 else "-0"):
                data = fixture(); rows(data)[10][index] = bad
                result = run(data)
                self.assert_stop(result, "BRIDGE_REFUSED")
                self.assertEqual(result["symbols"]["BTC/USD"]["status"], "BLOCKED")
        for bad in (-1, True, "10", 2**53):
            data = fixture(); rows(data)[10][7] = bad
            self.assert_stop(run(data), "BRIDGE_REFUSED")

    def test_zero_volume_valid_data_but_not_a_forced_candidate(self):
        data = fixture(); rows(data)[-2][6] = "0"
        self.assertIsNotNone(run(data)["proposed_input"])
        reference = copy.deepcopy(FIXTURE["independent_synthetic_reference"])
        reference["payloads"]["BTC/USD"]["bars"][-1]["volume"] = 0.0
        self.assertEqual(candidates.evaluate(reference)["symbols"]["BTC/USD"]["decision"], "WAIT")

    def test_stale_per_symbol_and_global_stop_preserve_partial_evidence(self):
        data = fixture()
        for row in rows(data,"XRP/USD")[:-1]: row[0] -= 4*3600
        source = rows(data,"XRP/USD")
        source[-1][0] = source[-2][0]+3600
        # This purported uncommitted row is eligible: commitment must win.
        result = run(data)
        self.assert_stop(result, "COMMITMENT_CONFLICT")
        self.assertEqual(result["symbols"]["BTC/USD"]["status"], "VALIDATED_PROPOSED_DATA")
        self.assertEqual(result["symbols"]["SOL/USD"]["status"], "NOT_ATTEMPTED")
        # Old eligible history plus a modern current row still has a gap into
        # that row. Existing outer commitment refuses BEFORE registry staleness.
        data = fixture()
        for row in rows(data,"XRP/USD")[:-1]: row[0] -= 4*3600
        result = run(data)
        self.assert_stop(result, "COMMITMENT_CONFLICT")
        self.assertIsNone(result["symbols"]["XRP/USD"]["bridge"])
        reference=copy.deepcopy(FIXTURE["independent_synthetic_reference"]["payloads"]["XRP/USD"])
        for b in reference["bars"]:b["open_time"]-=4*3600
        self.assertEqual(registry.validate_symbol("XRP/USD",reference,as_of=T,policy=prototype.POLICY)["reason_code"],"DATA_STALE")

    def test_gap_duplicate_and_out_of_order_are_not_repaired(self):
        for mode, reason in (("gap","TIMESTAMP_GAP"),("duplicate","DUPLICATE_TIMESTAMP"),("order","TIMESTAMP_ORDER")):
            data = fixture(); source = rows(data)
            if mode == "gap": source.pop(10)
            elif mode == "duplicate": source.insert(10,copy.deepcopy(source[0]))
            else: source[0],source[1] = source[1],source[0]
            result = run(data)
            self.assert_stop(result, "BRIDGE_REFUSED")
            self.assertEqual(result["symbols"]["BTC/USD"]["bridge"]["decision"]["reason_code"],reason)

    def test_entire_history_is_checked_not_just_last_twenty_one(self):
        data = fixture(); source = rows(data)
        source.insert(0,copy.deepcopy(source[0])); source[0][0] -= 3600
        self.assertIsNotNone(run(data)["proposed_input"])
        source[0][4] = "-1"
        self.assert_stop(run(data), "BRIDGE_REFUSED")

    def test_wrong_or_unknown_identity_and_optional_metadata_refuse(self):
        for field,bad in (("quote","USDT"),("base","BTC"),("status","cancel_only"),("wsname","BTC/USD"),("aclass_base","futures")):
            data = fixture(); data["observations"]["BTC/USD"]["identity"]["payload"]["result"]["XXBTZUSD"][field] = bad
            self.assert_stop(run(data),"IDENTITY_UNVERIFIED")
        data = fixture(); data["observations"]["BTC/USD"]["identity"]["payload"]["result"]["XXBTZUSD"]["fees"] = "unsupported"
        self.assert_stop(run(data),"IDENTITY_UNVERIFIED")
        data = fixture(); body=data["observations"]["BTC/USD"]["identity"]["payload"]["result"]
        body["XBTUSD"] = body.pop("XXBTZUSD")
        self.assert_stop(run(data),"ALIAS_CHANGED")

    def test_capture_identity_timeframe_alias_and_schema_refuse(self):
        for field,bad in (("venue","other"),("market","futures"),("quote","USDT"),("interval_minutes",1),("request_pair","BTCUSD")):
            data=fixture();data["observations"]["BTC/USD"]["ohlc"]["capture"][field]=bad
            self.assert_stop(run(data),"BRIDGE_REFUSED")
        data=fixture(); body=data["observations"]["BTC/USD"]["ohlc"]["capture"]["response"]["result"]
        body["XBTUSD"] = body.pop("XXBTZUSD")
        self.assert_stop(run(data),"ALIAS_CHANGED")

    def test_http_failures_api_errors_and_redirect_stop_all_later_stages(self):
        for stage in ("identity","ohlc"):
            for status in (451,429,301,500):
                data=fixture();data["observations"]["BTC/USD"][stage]["http_status"]=status
                result=run(data);self.assert_stop(result,"HTTP_REFUSED")
                self.assertTrue(all(result["symbols"][s]["status"]=="NOT_ATTEMPTED" for s in ("XRP/USD","SOL/USD")))
        data=fixture();data["observations"]["BTC/USD"]["identity"]["payload"]["error"]=["DO_NOT_ECHO"]
        result=run(data);self.assert_stop(result,"API_ERROR")
        self.assertNotIn("DO_NOT_ECHO",registry.canonical_json(result))

    def test_clock_date_conflict_is_terminal(self):
        data=fixture();data["observations"]["BTC/USD"]["ohlc"]["service_date_utc_seconds"] = T+10
        self.assert_stop(run(data),"SERVICE_TIME_CONFLICT")
        data=fixture();data["observations"]["BTC/USD"]["identity"]["service_date_utc_seconds"] = None
        self.assert_stop(run(data),"CLOCK_UNVERIFIED")

    def test_score_injection_at_envelope_capture_and_row_never_rescues(self):
        for layer in ("root","capture","row"):
            data=fixture()
            if layer=="root":data["score"]=10**9
            elif layer=="capture":data["observations"]["BTC/USD"]["ohlc"]["capture"]["score"]=10**9
            else:rows(data)[10].append(10**9)
            self.assertIsNone(run(data)["proposed_input"])

    def test_origin_source_tag_missing_symbols_and_extra_fields_fail_closed(self):
        for field,bad in (("source_tag","SYNTHETIC_ONLY"),("fixture_origin","REAL_MARKET_CAPTURE"),("version","unknown")):
            data=fixture();data[field]=bad
            self.assert_stop(run(data),"CONTRACT_INVALID")
        for symbol in ("BTC/USD","ETH/USD"):
            data=fixture()
            if symbol=="BTC/USD":del data["observations"][symbol]
            else:data["observations"][symbol]={}
            self.assert_stop(run(data),"CONTRACT_INVALID")

    def test_size_row_and_parser_limits_are_bounded(self):
        result=prototype.run_offline(" "*(prototype.MAX_INPUT_BYTES+1),clock=MockClock(),clock_evidence_verifier=lambda e,c:True,expected_context=CONTEXT)
        self.assert_stop(result,"SIZE_LIMIT")
        data=fixture();data["observations"]["BTC/USD"]["identity"]["payload"]={"oversized":"x"*diagnostic.BODY_LIMIT}
        self.assert_stop(run(data),"RESPONSE_TOO_LARGE")
        data=fixture();source=rows(data);source[0:0]=[copy.deepcopy(source[0])]*512
        self.assert_stop(run(data),"COMMITMENT_CONFLICT")
        for text in ('{"x":1,"x":2}',"NaN","1e999","["*2000,"\ud800"):
            result=prototype.run_offline(text,clock=MockClock(),clock_evidence_verifier=lambda e,c:True,expected_context=CONTEXT)
            self.assert_stop(result,"JSON_INVALID")

    def test_normalization_mismatch_refuses_without_candidate_admission(self):
        original=registry.validate_symbol
        count=0
        def corrupt_second(*args,**kwargs):
            nonlocal count
            count+=1
            result=original(*args,**kwargs)
            if count==2:result["evidence_ref"]="sha256:"+"0"*64
            return result
        with patch.object(registry,"validate_symbol",side_effect=corrupt_second):
            self.assert_stop(run(),"NORMALIZATION_MISMATCH")
        self.assertEqual(count,2)

    def test_determinism_no_input_mutation_bounded_evidence_and_no_raw_current(self):
        data=fixture();original=copy.deepcopy(data)
        first=registry.canonical_json(run(data))
        self.assertEqual(first,registry.canonical_json(run(data)))
        self.assertEqual(data,original)
        self.assertNotIn("IGNORED_CURRENT",first)
        self.assertLess(len(first),prototype.MAX_OUTPUT_BYTES)

    def test_zero_through_three_watch_on_separate_synthetic_references(self):
        for n in range(4):
            data=fixture();reference=copy.deepcopy(FIXTURE["independent_synthetic_reference"])
            for symbol in registry.SYMBOLS[n:]:
                for r in rows(data,symbol)[:-1]:r[1:7]=["100"]*6
                for b in reference["payloads"][symbol]["bars"]:b.update(open=100.0,high=100.0,low=100.0,close=100.0,volume=100.0)
            feed=run(data)["proposed_input"]
            self.assertIsNotNone(feed)
            self.assertEqual(feed["payloads"],reference["payloads"])
            result=candidates.evaluate(reference)
            self.assertEqual(len(result["candidates"]),n)
            self.assertTrue(all(r["decision"] in ("WATCH","WAIT") for r in result["symbols"].values()))

    def test_import_reload_has_no_transport_clock_or_file_activation(self):
        with patch("builtins.open",side_effect=AssertionError("unexpected file read")):
            importlib.reload(prototype)
            self.assertEqual(prototype.run_offline()["reason"],"AUTHORIZATION_MISSING")

    def test_verifier_exception_of_internal_type_is_also_redacted(self):
        def failing(e,c):raise prototype.Refused("DO_NOT_ECHO")
        result=run(verifier=failing)
        self.assert_stop(result,"CLOCK_UNVERIFIED")
        self.assertNotIn("DO_NOT_ECHO",registry.canonical_json(result))

    def test_service_metadata_unknown_fields_or_missing_stage_refuse(self):
        data=fixture();data["observations"]["BTC/USD"]["identity"]["redirect_url"]="https://example.invalid"
        self.assert_stop(run(data),"CONTRACT_INVALID")
        data=fixture();del data["observations"]["BTC/USD"]["ohlc"]
        self.assert_stop(run(data),"CONTRACT_INVALID")

    def test_no_extra_symbol_is_evaluated_after_xrp_failure(self):
        data=fixture();data["observations"]["XRP/USD"]["ohlc"]["http_status"]=451
        original=prototype._identity_ref
        seen=[]
        def traced(symbol,payload):
            seen.append(symbol);return original(symbol,payload)
        with patch.object(prototype,"_identity_ref",side_effect=traced):
            result=run(data)
        self.assertEqual(seen,["BTC/USD","XRP/USD"])
        self.assert_stop(result,"HTTP_REFUSED")
        self.assertEqual(result["symbols"]["SOL/USD"]["status"],"NOT_ATTEMPTED")


if __name__ == "__main__":
    unittest.main()
