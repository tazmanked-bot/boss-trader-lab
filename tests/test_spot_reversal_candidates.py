"""SYNTHETIC-only deterministic research/causality/adversarial regressions."""
import copy
from contextlib import ExitStack, redirect_stdout
import importlib
import io
import json
from pathlib import Path
import unittest
from unittest.mock import patch, mock_open

from research import spot_reversal_candidates as model
from research import spot_refusal_registry as registry

FIXTURE = json.loads((Path(__file__).parent / "fixtures/spot_reversal_candidates_016.json").read_text())
T = FIXTURE["as_of"]


def fixture():
    return copy.deepcopy(FIXTURE)


def flat(data, symbol):
    for bar in data["payloads"][symbol]["bars"]:
        bar.update(open=100, high=100, low=100, close=100, volume=100)


class ReversalTests(unittest.TestCase):
    def setUp(self):
        self.guards = ExitStack()
        self.addCleanup(self.guards.close)
        self.mocks = [self.guards.enter_context(patch(target, side_effect=AssertionError("forbidden I/O")))
                      for target in ("socket.socket", "socket.create_connection", "socket.getaddrinfo",
                                     "urllib.request.urlopen", "http.client.HTTPSConnection",
                                     "subprocess.run", "subprocess.Popen", "time.time")]
        self.addCleanup(self.no_calls)

    def no_calls(self):
        for mock in self.mocks:
            mock.assert_not_called()

    def blocked(self, data, reason, symbol="BTC/USD"):
        result = model.evaluate(data)
        row = result["symbols"][symbol]
        self.assertEqual(row["decision"], "BLOCKED")
        self.assertEqual(result["input_error"] or row["validation"]["reason_code"], reason)
        self.assertIsNone(row["features"])
        self.assertIsNone(row["score"])
        self.assertNotIn(symbol, result["candidates"])
        return result

    def test_three_watch_hand_calculated_features_and_lexical_tie(self):
        result = model.evaluate(fixture())
        self.assertEqual(result["candidates"], ["BTC/USD", "SOL/USD", "XRP/USD"])
        for row in result["symbols"].values():
            self.assertEqual(row["decision"], "WATCH")
            self.assertEqual(row["score"], 26666)
            self.assertEqual([row["features"][k]["strength_bps"] for k in model.FEATURES],
                             [5000, 10000, 6666, 5000])
            self.assertTrue(all(f["passed"] for f in row["features"].values()))
            self.assertEqual(row["catalyst_status"], "UNVERIFIED")
            self.assertIsNotNone(row["why_early"])
            self.assertIn("no order", row["invalidation_observation"])

    def test_zero_one_two_three_candidates_without_minimum(self):
        for count in range(4):
            data = fixture()
            for symbol in registry.SYMBOLS[count:]:
                flat(data, symbol)
            result = model.evaluate(data)
            self.assertEqual(len(result["candidates"]), count)
            self.assertEqual(set(result["candidates"]), set(registry.SYMBOLS[:count]))
            self.assertEqual(len(result["candidates"]), len(set(result["candidates"])))

    def test_rank_descending_score_then_symbol_not_input_order(self):
        data = fixture()
        data["payloads"]["XRP/USD"]["bars"][-1]["volume"] = 175
        data["payloads"]["SOL/USD"]["bars"][-1]["volume"] = 125
        result = model.evaluate(data)
        self.assertEqual(result["candidates"], ["XRP/USD", "BTC/USD", "SOL/USD"])
        data["payloads"] = dict(reversed(list(data["payloads"].items())))
        self.assertEqual(model.evaluate(data), result)

    def test_flat_and_uninterrupted_rally_wait(self):
        for kind in ("flat", "rally"):
            data = fixture()
            for symbol in registry.SYMBOLS:
                flat(data, symbol)
                if kind == "rally":
                    for i, bar in enumerate(data["payloads"][symbol]["bars"]):
                        bar.update(open=100+i, low=100+i, close=101+i, high=102+i)
            result = model.evaluate(data)
            self.assertEqual(result["candidates"], [])
            self.assertTrue(all(r["decision"] == "WAIT" for r in result["symbols"].values()))

    def test_each_feature_is_required_even_with_other_high_strengths(self):
        for name, change in (
            ("slowing_downside", lambda b: b[-3].update(close=98)),
            ("low_retest_hold", lambda b: b[-1].update(low=97)),
            ("fresh_recovery", lambda b: b[-1].update(open=101)),
            ("volume_consistent", lambda b: b[-1].update(volume=90))):
            data = fixture()
            change(data["payloads"]["BTC/USD"]["bars"])
            row = model.evaluate(data)["symbols"]["BTC/USD"]
            self.assertEqual(row["decision"], "WAIT", name)
            self.assertFalse(row["features"][name]["passed"], name)
            self.assertIsNone(row["why_early"])

    def test_volume_contradictions_zero_and_excess_spike_wait(self):
        for previous, latest in ((80, 90), (120, 150), (80, 201), (0, 150), (80, 0)):
            data = fixture()
            bars = data["payloads"]["BTC/USD"]["bars"]
            bars[-2]["volume"], bars[-1]["volume"] = previous, latest
            row = model.evaluate(data)["symbols"]["BTC/USD"]
            self.assertEqual(row["decision"], "WAIT")
            self.assertFalse(row["features"]["volume_consistent"]["passed"])
        data = fixture()
        for b in data["payloads"]["BTC/USD"]["bars"]:
            b["volume"] = 0
        self.assertEqual(model.evaluate(data)["symbols"]["BTC/USD"]["decision"], "WAIT")

    def test_no_momentum_chase_past_prior_close(self):
        data = fixture()
        data["payloads"]["BTC/USD"]["bars"][-1].update(close=103, high=104)
        row = model.evaluate(data)["symbols"]["BTC/USD"]
        self.assertEqual(row["decision"], "WAIT")
        self.assertFalse(row["features"]["fresh_recovery"]["passed"])

    def test_feature_boundary_conditions(self):
        # Volume ceiling inclusive; low band at exactly +1% inclusive.
        data = fixture()
        bars = data["payloads"]["BTC/USD"]["bars"]
        for bar in bars:
            for key in ("open", "high", "low", "close"):
                bar[key] *= 100
        bars[-1].update(volume=200, low=9898)
        row = model.evaluate(data)["symbols"]["BTC/USD"]
        self.assertEqual(row["decision"], "WATCH")
        self.assertEqual(row["features"]["volume_consistent"]["strength_bps"], 10000)
        bars[-1]["low"] = 9898.1
        self.assertEqual(model.evaluate(data)["symbols"]["BTC/USD"]["decision"], "WAIT")

    def test_stale_refusal_is_per_symbol_not_overridden_by_fresh_btc(self):
        data = fixture()
        for symbol in ("XRP/USD", "SOL/USD"):
            for b in data["payloads"][symbol]["bars"]:
                b["open_time"] -= 4 * 3600
            self.blocked(data, "DATA_STALE", symbol)
        self.assertEqual(model.evaluate(data)["candidates"], ["BTC/USD"])

    def test_stale_boundary_three_hours_allowed_four_refused(self):
        for lag in (3, 4):
            data = fixture()
            for b in data["payloads"]["BTC/USD"]["bars"]:
                b["open_time"] -= lag * 3600
            if lag == 3:
                self.assertEqual(model.evaluate(data)["symbols"]["BTC/USD"]["decision"], "WATCH")
            else:
                self.blocked(data, "DATA_STALE")

    def test_refused_symbols_never_reach_features(self):
        data = fixture()
        for payload in data["payloads"].values():
            payload["bars"][0]["close"] = -1
        with patch.object(model, "_features", side_effect=AssertionError("validation bypass")) as features:
            result = model.evaluate(data)
            self.assertEqual(result["candidates"], [])
            features.assert_not_called()

    def test_invalid_prices_nonfinite_types_all_positions(self):
        for key in ("open", "high", "low", "close", "volume"):
            for bad in (-1, float("nan"), float("inf"), -float("inf"), True, None, "100", 10**1000):
                for index in (0, 10, 20):
                    data = fixture()
                    data["payloads"]["BTC/USD"]["bars"][index][key] = bad
                    self.blocked(data, "INVALID_VALUE")
        for key in ("open", "high", "low", "close"):
            data = fixture()
            data["payloads"]["BTC/USD"]["bars"][0][key] = 0
            self.blocked(data, "INVALID_VALUE")

    def test_price_bounds_refuse(self):
        data = fixture()
        data["payloads"]["BTC/USD"]["bars"][-1]["high"] = 1
        self.blocked(data, "INVALID_VALUE")

    def test_duplicates_gaps_and_order_refuse_no_repair(self):
        for mode, reason in (("duplicate", "DUPLICATE_TIMESTAMP"), ("gap", "TIMESTAMP_GAP"),
                             ("reverse", "TIMESTAMP_ORDER")):
            data = fixture()
            bars = data["payloads"]["BTC/USD"]["bars"]
            if mode == "duplicate":
                bars.insert(10, copy.deepcopy(bars[0]))
            elif mode == "gap":
                bars.pop(10)
            else:
                bars.reverse()
            self.blocked(data, reason)

    def test_insufficient_history_and_entire_history_validation(self):
        data = fixture()
        data["payloads"]["BTC/USD"]["bars"].pop(0)
        self.blocked(data, "WARMUP_INCOMPLETE")
        data = fixture()
        bars = data["payloads"]["BTC/USD"]["bars"]
        earlier = {**bars[0], "open_time": bars[0]["open_time"]-3600}
        bars.insert(0, earlier)
        self.assertEqual(model.evaluate(data)["symbols"]["BTC/USD"]["decision"], "WATCH")
        earlier["close"] = -1
        self.blocked(data, "INVALID_VALUE")

    def test_market_identity_and_rule_conflicts(self):
        for key, bad in (("venue", "other"), ("market", "futures"), ("quote", "USDT"),
                         ("timeframe", "5m"), ("symbol", "ETH/USD")):
            data = fixture()
            data["payloads"]["BTC/USD"][key] = bad
            self.blocked(data, "MARKET_MISMATCH")
        data = fixture()
        data["payloads"]["BTC/USD"]["rules"]["require_non_spot"] = True
        self.blocked(data, "RULE_CONFLICT")

    def test_score_injection_at_every_layer_fails(self):
        for layer in ("envelope", "payload", "bar", "policy"):
            data = fixture()
            target = {"envelope": data, "payload": data["payloads"]["BTC/USD"],
                      "bar": data["payloads"]["BTC/USD"]["bars"][-1], "policy": data["policy"]}[layer]
            target["score"] = 10**100
            self.blocked(data, "CONFIG_INVALID" if layer == "policy" else "MALFORMED_DATA")

    def test_unknown_symbols_and_missing_symbols(self):
        data = fixture()
        data["payloads"]["ETH/USD"] = data["payloads"]["BTC/USD"]
        result = self.blocked(data, "MALFORMED_DATA")
        self.assertEqual(result["candidates"], [])
        data = fixture()
        del data["payloads"]["XRP/USD"]
        result = self.blocked(data, "DATA_UNAVAILABLE", "XRP/USD")
        self.assertEqual(result["candidates"], ["BTC/USD", "SOL/USD"])

    def test_unknown_missing_and_implicit_policy_fail(self):
        for policy in (None, {}, [], True, {**FIXTURE["policy"], "future_mode": "repair"},
                       {**FIXTURE["policy"], "version": "unknown"}):
            data = fixture()
            data["policy"] = policy
            self.blocked(data, "CONFIG_INVALID")
        for key in FIXTURE:
            data = fixture()
            del data[key]
            self.blocked(data, "MALFORMED_DATA")

    def test_synthetic_label_required_not_live_provenance(self):
        for value in ("LIVE", "SYNTHETIC", None, True):
            data = fixture()
            data["label"] = value
            self.blocked(data, "MALFORMED_DATA")

    def test_asof_complete_output_equality_after_adversarial_future_append(self):
        for state in ("WATCH", "WAIT", "BLOCKED"):
            data = fixture()
            if state == "WAIT":
                flat(data, "BTC/USD")
            elif state == "BLOCKED":
                data["payloads"]["BTC/USD"]["bars"][10]["close"] = -1
            baseline = registry.canonical_json(model.evaluate(data))
            self.assertEqual(registry.canonical_json(model.evaluate_json(json.dumps(data))), baseline)
            for value in (-1, 1e99, None, "IGNORED_FUTURE_VALUE", {"private": "DO_NOT_ECHO"}):
                appended = copy.deepcopy(data)
                for payload in appended["payloads"].values():
                    for offset in range(4):
                        payload["bars"].append(dict(open_time=T+offset*3600, open=value, high=value,
                                                   low=value, close=value, volume=value))
                self.assertEqual(registry.canonical_json(model.evaluate(appended)), baseline)
                self.assertEqual(registry.canonical_json(model.evaluate_json(json.dumps(appended))), baseline)

    def test_future_close_boundary_asof_strict_and_no_warmup_bypass(self):
        data = fixture()
        # Latest close exactly as_of is eligible and necessary for 21 bars.
        self.assertEqual(model.evaluate(data)["symbols"]["BTC/USD"]["decision"], "WATCH")
        data["payloads"]["BTC/USD"]["bars"][-1]["open_time"] = T
        self.blocked(data, "WARMUP_INCOMPLETE")
        for stamp in (T, T+3600):
            data = fixture()
            data["policy"]["future_mode"] = "reject"
            future = {**data["payloads"]["BTC/USD"]["bars"][-1], "open_time": stamp}
            data["payloads"]["BTC/USD"]["bars"].append(future)
            self.blocked(data, "CANDLE_NOT_CLOSED")
        data = fixture()
        for b in data["payloads"]["BTC/USD"]["bars"]:
            b["open_time"] += 100*3600
        self.blocked(data, "WARMUP_INCOMPLETE")

    def test_malformed_future_headers_refuse(self):
        for stamp, code in ((T+1, "TIMESTAMP_INVALID"), (True, "TIMESTAMP_INVALID"),
                            (T*1000, "TIME_UNIT_MISMATCH")):
            data = fixture()
            future = {**data["payloads"]["BTC/USD"]["bars"][-1], "open_time": stamp}
            data["payloads"]["BTC/USD"]["bars"].append(future)
            self.blocked(data, code)
        data = fixture()
        data["payloads"]["BTC/USD"]["bars"].append({"open_time": T})
        self.blocked(data, "MALFORMED_DATA")

    def test_invalid_explicit_asof_never_guessed_or_shifted(self):
        for value, reason in ((None, "TIMESTAMP_INVALID"), (True, "TIMESTAMP_INVALID"),
                              (T+1, "TIMESTAMP_INVALID"), (T*1000, "TIME_UNIT_MISMATCH")):
            data = fixture()
            data["as_of"] = value
            self.blocked(data, reason)

    def test_bounded_json_duplicates_nonfinite_and_no_exception_echo(self):
        for text in ("NaN", "1e999", '{"x":1,"x":2}', "["*2000, "\ud800", None,
                     " "*(model.MAX_INPUT_BYTES+1), '{"secret":"DO_NOT_ECHO"'):
            result = model.evaluate_json(text)
            self.assertEqual(result["candidates"], [])
            self.assertTrue(all(r["decision"] == "BLOCKED" for r in result["symbols"].values()))
            self.assertNotIn("DO_NOT_ECHO", registry.canonical_json(result))
        data = fixture()
        data["payloads"]["BTC/USD"]["bars"].append(
            dict(open_time=T, open=float("nan"), high=1, low=1, close=1, volume=1))
        self.assertEqual(model.evaluate_json(json.dumps(data))["candidates"], [])

    def test_row_cap_includes_excluded_future_rows(self):
        data = fixture()
        bars = data["payloads"]["BTC/USD"]["bars"]
        bars.extend({**bars[-1], "open_time": T+i*3600} for i in range(492))
        self.blocked(data, "MALFORMED_DATA")

    def test_extreme_finite_values_do_not_overflow_feature_math(self):
        for multiplier in (1e-300, 1e95):
            data = fixture()
            for payload in data["payloads"].values():
                for bar in payload["bars"]:
                    for key in ("open", "high", "low", "close", "volume"):
                        bar[key] *= multiplier
            result = model.evaluate(data)
            self.assertEqual(len(result["candidates"]), 3)
            for row in result["symbols"].values():
                self.assertTrue(0 <= row["score"] <= 40000)

    def test_determinism_no_mutation_bounded_summary_and_evidence_sensitivity(self):
        data = fixture()
        original = copy.deepcopy(data)
        first = registry.canonical_json(model.evaluate(data))
        self.assertEqual(first, registry.canonical_json(model.evaluate(data)))
        self.assertEqual(data, original)
        self.assertLessEqual(len(first.encode("ascii")), model.MAX_OUTPUT_BYTES)
        self.assertEqual(first, registry.canonical_json(model.evaluate_json(json.dumps(data))))
        data["payloads"]["BTC/USD"]["bars"][0]["volume"] += 1
        self.assertNotEqual(first, registry.canonical_json(model.evaluate(data)))
        for row in model.evaluate(data)["symbols"].values():
            self.assertEqual(row["validation"]["as_of_utc"], "2030-03-17T18:00:00Z")
        self.assertIn("EXPLICIT_FIXTURE_COORDINATE_ONLY", first)

    def test_import_and_evaluation_no_clock_network_or_process_calls(self):
        reloaded = importlib.reload(model)
        self.assertEqual(len(reloaded.evaluate(fixture())["candidates"]), 3)

    def test_cli_only_reads_explicit_fixture_and_prints_canonical_output(self):
        expected = registry.canonical_json(model.evaluate(fixture()))
        output = io.StringIO()
        supplied = mock_open(read_data=json.dumps(fixture()).encode("utf-8"))
        with patch("sys.argv", ["spot_reversal_candidates", "synthetic.json"]), \
             patch("builtins.open", supplied), redirect_stdout(output):
            self.assertEqual(model.main(), 0)
        supplied.assert_called_once_with("synthetic.json", "rb")
        supplied().read.assert_called_once_with(model.MAX_INPUT_BYTES + 1)
        self.assertEqual(output.getvalue(), expected + "\n")

    def test_cli_read_failure_is_redacted_and_exits_blocked(self):
        output = io.StringIO()
        with patch("sys.argv", ["spot_reversal_candidates", "synthetic.json"]), \
             patch("builtins.open", side_effect=OSError("DO_NOT_ECHO")), redirect_stdout(output):
            self.assertEqual(model.main(), 2)
        result = json.loads(output.getvalue())
        self.assertEqual(result["input_error"], "DATA_UNAVAILABLE")
        self.assertEqual(result["candidates"], [])
        self.assertNotIn("DO_NOT_ECHO", output.getvalue())

    def test_binary_float_boundary_is_not_rounded_to_a_pass(self):
        data = fixture()
        # float(98.98) is slightly above the exact rational 98 * 101/100.
        data["payloads"]["BTC/USD"]["bars"][-1]["low"] = 98.98
        row = model.evaluate(data)["symbols"]["BTC/USD"]
        self.assertEqual(row["decision"], "WAIT")
        self.assertFalse(row["features"]["low_retest_hold"]["passed"])


if __name__ == "__main__":
    unittest.main()
