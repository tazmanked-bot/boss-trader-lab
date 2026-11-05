"""Deterministic offline bridge tests; independent expected envelope and refusals."""

import copy
from decimal import Decimal
import importlib
import json
from pathlib import Path
import socket
import time
import unittest
from unittest.mock import patch
import urllib.request

from research import kraken_spot_validation_bridge as bridge
from research import spot_refusal_registry as registry


FIXTURE = json.loads((Path(__file__).parent / "fixtures" / "kraken_spot_bridge_v1.json").read_text())
T = FIXTURE["as_of"]
PROJECTION = {"version": "spot-refusal-v1", "future_mode": "as_of"}


def capture(symbol="BTC/USD", closed_only=False):
    obj = copy.deepcopy(FIXTURE["captures"][symbol])
    if closed_only:
        rows(obj).pop()
    return obj


def rows(obj):
    result = obj["response"]["result"]
    return result[next(k for k in result if k != "last")]


def evaluate(obj, *, policy=PROJECTION, as_of=T, symbol="BTC/USD"):
    return bridge.validate_capture(symbol, obj, as_of=as_of, policy=policy)


class KrakenBridgeTests(unittest.TestCase):
    def assert_parser_refusal(self, result, code):
        self.assertEqual(result["bridge_code"], code)
        self.assertEqual(result["decision"]["status"], "REFUSED")
        self.assertEqual(result["decision"]["reason_code"], "DATA_UNAVAILABLE")
        text = registry.canonical_json(result)
        self.assertLess(len(text), 1600)
        self.assertNotIn("PRIVATE_SECRET", text)

    def assert_registry_refusal(self, result, code):
        self.assertEqual(result["decision"]["status"], "REFUSED")
        self.assertEqual(result["decision"]["reason_code"], code)

    def test_complete_three_symbol_projection_and_missing_isolation(self):
        inputs = copy.deepcopy(FIXTURE["captures"])
        result = bridge.validate_captures(inputs, as_of=T, policy=PROJECTION)
        self.assertEqual(tuple(result), ("BTC/USD", "XRP/USD", "SOL/USD"))
        self.assertTrue(all(r["decision"]["status"] == "VALIDATED_DATA" for r in result.values()))
        del inputs["XRP/USD"]
        inputs["SOL/USD"]["response"]["error"] = ["PRIVATE_SECRET API error"]
        result = bridge.validate_captures(inputs, as_of=T, policy=PROJECTION)
        self.assertEqual(result["BTC/USD"]["decision"]["status"], "VALIDATED_DATA")
        self.assert_parser_refusal(result["XRP/USD"], "SOURCE_MISSING")
        self.assert_parser_refusal(result["SOL/USD"], "SOURCE_API_ERROR")
        self.assertEqual(len(result), 3)  # No aggregate approval or candidate list.

    def test_hand_expected_envelope_preserves_all_ohlcv_fields(self):
        expected = {"symbol": "BTC/USD", "venue": "kraken", "market": "spot", "quote": "USD",
                    "timeframe": "1h", "rules": {"require_spot": True, "require_non_spot": False},
                    "bars": [{"open_time": T - (21 - i) * 3600, "open": float(100 + i),
                              "high": float(102 + i), "low": float(99 + i), "close": float(101 + i),
                              "volume": 1000.125 + i} for i in range(21)]}
        with patch.object(registry, "validate_symbol", wraps=registry.validate_symbol) as validate:
            result = evaluate(capture())
            self.assertEqual(validate.call_count, 1)
            self.assertEqual(validate.call_args.args, ("BTC/USD", expected))
            self.assertEqual(validate.call_args.kwargs, {"as_of": T, "policy": PROJECTION})
        self.assertEqual(result["decision"], registry.validate_symbol("BTC/USD", expected, as_of=T, policy=PROJECTION))
        self.assertEqual(result["evidence_ref"],
                         "sha256:46ca2039bc768216a95f504ff93070745b3dea2370f490d2e9d0530d0a468e2d")

    def test_strict_mode_does_not_silently_drop_uncommitted_final_row(self):
        self.assert_registry_refusal(evaluate(capture(), policy=None), "CANDLE_NOT_CLOSED")
        closed = capture(closed_only=True)
        self.assertEqual(evaluate(closed, policy=None)["decision"]["status"], "VALIDATED_DATA")
        # The last closed row is required; position-based dropping would leave 20.
        self.assertEqual(len(rows(closed)), 21)
        for stamp in (T, T + 3600):
            obj = copy.deepcopy(closed)
            rows(obj).append([stamp] + ["PRIVATE_SECRET"] * 6 + ["PRIVATE_SECRET"])
            result = evaluate(obj, policy=None)
            self.assert_registry_refusal(result, "CANDLE_NOT_CLOSED")
            self.assertNotIn("PRIVATE_SECRET", registry.canonical_json(result))

    def test_projection_full_canonical_bytes_invariant_after_future_append(self):
        for base in (capture(), capture(closed_only=True)):
            reference = registry.canonical_json(evaluate(base)).encode("ascii")
            for value in ("1e999", "NaN", "-999999", "PRIVATE_SECRET", "0", "9999999999999999999999"):
                obj = copy.deepcopy(base)
                for offset in range(1, 5):
                    rows(obj).append([T + offset * 3600] + [value] * 6 + ["PRIVATE_SECRET"])
                obj["response"]["result"]["last"] = T + 4 * 3600 + 17
                self.assertEqual(registry.canonical_json(evaluate(obj)).encode("ascii"), reference)
                serialized = json.dumps(obj)
                actual = bridge.validate_capture_json("BTC/USD", serialized, as_of=T, policy=PROJECTION)
                self.assertEqual(registry.canonical_json(actual).encode("ascii"), reference)

    def test_projection_invariant_for_eligible_refusal_and_empty_history(self):
        obj = capture()
        del rows(obj)[5]
        before = registry.canonical_json(evaluate(obj))
        rows(obj).append([T + 3600] + ["PRIVATE_SECRET"] * 7)
        self.assertEqual(registry.canonical_json(evaluate(obj)), before)
        self.assert_registry_refusal(evaluate(obj), "TIMESTAMP_GAP")
        obj = capture()
        obj["response"]["result"]["XXBTZUSD"] = rows(obj)[-1:]
        self.assert_registry_refusal(evaluate(obj), "WARMUP_INCOMPLETE")

    def test_eligible_values_are_never_hidden_by_projection(self):
        for position in (0, 10, 20):
            for column in range(1, 7):
                obj = capture()
                rows(obj)[position][column] = "NaN"
                self.assert_parser_refusal(evaluate(obj), "NUMERIC_INVALID")
        obj = capture()
        rows(obj)[20][0] = T  # Known valid future header can be projected, leaving 20.
        self.assert_registry_refusal(evaluate(obj), "WARMUP_INCOMPLETE")

    def test_timestamp_type_units_alignment_and_row_width(self):
        for position in (0, 10, 21):  # Includes ineligible row: header still checked.
            for stamp in (True, str(T), float(T), T * 1000, T + 1, -1, 0, 4102444800):
                obj = capture()
                rows(obj)[position][0] = stamp
                self.assert_parser_refusal(evaluate(obj), "TIMESTAMP_INVALID")
            for length in (0, 1, 7, 9):
                obj = capture()
                rows(obj)[position] = [T] * length
                self.assert_parser_refusal(evaluate(obj), "ROW_SCHEMA")

    def test_clock_and_unknown_policy_fail_before_parsing(self):
        for clock in (True, str(T), T * 1000, T + 1, None):
            result = evaluate(None, as_of=clock)
            self.assertEqual(result["bridge_code"], "CONTEXT_INVALID")
            self.assertEqual(result["decision"]["status"], "REFUSED")
            self.assertIsNone(result["decision"]["as_of_utc"])
        for policy in ({}, {**PROJECTION, "future_mode": "drop_last"}, {**PROJECTION, "score": 999}, []):
            self.assert_registry_refusal(evaluate(capture(), policy=policy), "CONFIG_INVALID")
        with self.assertRaises(TypeError):
            bridge.validate_capture("BTC/USD", capture())

    def test_market_metadata_exact_fields_and_no_substitution(self):
        for field, bad in (("venue", "binance"), ("market", "perpetual"), ("quote", "USDT"),
                           ("request_pair", "BTCUSD"), ("symbol", "SOL/USD"), ("interval_minutes", 1),
                           ("interval_minutes", "60"), ("interval_minutes", True)):
            obj = capture()
            obj[field] = bad
            self.assert_parser_refusal(evaluate(obj), "IDENTITY_MISMATCH")
        for field in capture():
            obj = capture()
            del obj[field]
            self.assert_parser_refusal(evaluate(obj), "CAPTURE_INVALID")
        obj = capture()
        obj["score"] = 100000000
        self.assert_parser_refusal(evaluate(obj), "CAPTURE_INVALID")

    def test_allowed_aliases_and_ambiguous_unknown_keys(self):
        for symbol, allowed in (("BTC/USD", ("XXBTZUSD", "XBTUSD")),
                                ("XRP/USD", ("XXRPZUSD", "XRPUSD")), ("SOL/USD", ("SOLUSD",))):
            original = capture(symbol)
            original_key = next(k for k in original["response"]["result"] if k != "last")
            baseline = evaluate(original, symbol=symbol)
            for alias in allowed:
                obj = copy.deepcopy(original)
                obj["response"]["result"][alias] = obj["response"]["result"].pop(original_key)
                self.assertEqual(evaluate(obj, symbol=symbol), baseline)
            for bad in ("BTC/USDT", "BTC/USD", "XXBTZUSD.d", "XBTUSDT", "SOLUSDT", "unknown"):
                obj = copy.deepcopy(original)
                obj["response"]["result"][bad] = obj["response"]["result"].pop(original_key)
                self.assert_parser_refusal(evaluate(obj, symbol=symbol), "PAIR_MISMATCH")
            obj = copy.deepcopy(original)
            obj["response"]["result"]["other"] = []
            self.assert_parser_refusal(evaluate(obj, symbol=symbol), "SOURCE_SCHEMA")

    def test_source_errors_schema_cursor_and_redaction(self):
        for response in (None, [], {}, {"error": []}, {"error": {}, "result": {}},
                         {"error": [], "result": {"last": T}},
                         {"error": [], "result": {"XXBTZUSD": [], "last": T, "extra": []}},
                         {"error": [], "result": {}, "extra": "PRIVATE_SECRET"}):
            obj = capture()
            obj["response"] = response
            self.assert_parser_refusal(evaluate(obj), "SOURCE_SCHEMA")
        obj = capture()
        obj["response"]["error"] = ["PRIVATE_SECRET HTTP 451 no retry"]
        self.assert_parser_refusal(evaluate(obj), "SOURCE_API_ERROR")
        for cursor in (True, str(T), -1, T * 1000):
            obj = capture()
            obj["response"]["result"]["last"] = cursor
            self.assert_parser_refusal(evaluate(obj), "CURSOR_INVALID")

    def test_every_numeric_column_rejects_bad_strings_and_native_numbers(self):
        for column in range(1, 7):
            for value in ("", " 100", "100 ", "+100", "01", "1_00", "1,000", "1e2", "NaN", "Infinity",
                          "-1", "-0", "9" * 129, True, 100, 100.0, None, [], {}):
                with self.subTest(column=column, value_type=type(value).__name__):
                    obj = capture()
                    rows(obj)[10][column] = value
                    self.assert_parser_refusal(evaluate(obj), "NUMERIC_INVALID")
        for column in range(1, 6):
            obj = capture()
            rows(obj)[0][column] = "0"
            self.assert_parser_refusal(evaluate(obj), "NUMERIC_INVALID")

    def test_exact_bounds_checked_before_binary_rounding(self):
        for col in (1, 4, 5):
            obj = capture()
            rows(obj)[0][2] = "100.00000000000000001"
            rows(obj)[0][col] = "100.00000000000000002"
            self.assert_parser_refusal(evaluate(obj), "PRICE_BOUNDS")
        obj = capture()
        rows(obj)[0][1] = "100.00000000000000001"
        rows(obj)[0][4] = "100.00000000000000002"
        self.assert_parser_refusal(evaluate(obj), "PRECISION_LOSS")

    def test_normal_decimal_rounding_allowed_and_source_precision_hashed(self):
        obj = capture()
        rows(obj)[0][6] = "0.1"
        result = evaluate(obj)
        self.assertEqual(result["decision"]["status"], "VALIDATED_DATA")
        self.assertNotEqual(Decimal.from_float(float("0.1")), Decimal("0.1"))
        changed = copy.deepcopy(obj)
        rows(changed)[0][6] = "0.100000000000000001"
        other = evaluate(changed)
        self.assertEqual(other["decision"], result["decision"])
        self.assertNotEqual(other["evidence_ref"], result["evidence_ref"])

    def test_vwap_and_trade_count_validated_not_silently_ignored(self):
        for count in (True, "10", 10.0, -1, 2 ** 53):
            obj = capture()
            rows(obj)[0][7] = count
            self.assert_parser_refusal(evaluate(obj), "COUNT_INVALID")
        baseline = evaluate(capture())
        for column, value in ((5, "100.75"), (7, 111)):
            obj = capture()
            rows(obj)[0][column] = value
            result = evaluate(obj)
            self.assertEqual(result["decision"], baseline["decision"])
            self.assertNotEqual(result["evidence_ref"], baseline["evidence_ref"])
        obj = capture()
        rows(obj)[0][6] = "0"
        rows(obj)[0][7] = 0
        self.assertEqual(evaluate(obj)["decision"]["status"], "VALIDATED_DATA")

    def test_eligible_order_duplicate_gap_history_and_staleness_unrelaxed(self):
        for mode, code in (("duplicate", "DUPLICATE_TIMESTAMP"), ("order", "TIMESTAMP_ORDER"),
                           ("gap", "TIMESTAMP_GAP"), ("short", "WARMUP_INCOMPLETE")):
            obj = capture(closed_only=True)
            if mode == "duplicate":
                rows(obj).insert(10, copy.deepcopy(rows(obj)[0]))
            elif mode == "order":
                rows(obj).reverse()
            elif mode == "gap":
                rows(obj).pop(10)
            else:
                rows(obj).pop(0)
            original = copy.deepcopy(obj)
            self.assert_registry_refusal(evaluate(obj), code)
            self.assertEqual(obj, original)
        for hours, expected in ((3, None), (4, "DATA_STALE")):
            obj = capture(closed_only=True)
            for row in rows(obj):
                row[0] -= hours * 3600
            result = evaluate(obj)
            if expected:
                self.assert_registry_refusal(result, expected)
            else:
                self.assertEqual(result["decision"]["status"], "VALIDATED_DATA")

    def test_fresh_btc_cannot_rescue_stale_xrp_and_sol(self):
        inputs = {s: capture(s, closed_only=True) for s in FIXTURE["captures"]}
        for symbol in ("XRP/USD", "SOL/USD"):
            for row in rows(inputs[symbol]):
                row[0] -= 4 * 3600
        result = bridge.validate_captures(inputs, as_of=T, policy=PROJECTION)
        self.assertEqual(result["BTC/USD"]["decision"]["status"], "VALIDATED_DATA")
        for symbol in ("XRP/USD", "SOL/USD"):
            self.assert_registry_refusal(result[symbol], "DATA_STALE")

    def test_input_output_size_limits_and_unknown_batch_keys(self):
        obj = capture()
        rows(obj).extend(copy.deepcopy(rows(obj)) * 24)
        self.assert_parser_refusal(evaluate(obj), "SIZE_LIMIT")
        self.assert_parser_refusal(bridge.validate_capture_json("BTC/USD", " " * 262145, as_of=T), "SIZE_LIMIT")
        self.assert_parser_refusal(bridge.validate_capture_json("BTC/USD", '"' + "\u20ac" * 90000 + '"', as_of=T), "SIZE_LIMIT")
        for value in ({"BTC/USDT": capture()}, [], None):
            for result in bridge.validate_captures(value, as_of=T).values():
                self.assert_parser_refusal(result, "CAPTURE_INVALID")

    def test_strict_json_duplicate_nonfinite_and_errors_are_redacted(self):
        for text in ('{"response":1,"response":2}', "NaN", "Infinity", "1e999", "[" * 2000,
                     "{PRIVATE_SECRET", "\ud800", None):
            self.assert_parser_refusal(bridge.validate_capture_json("BTC/USD", text, as_of=T), "JSON_INVALID")
        obj = capture()
        rows(obj)[-1][1] = float("nan")
        self.assert_parser_refusal(evaluate(obj), "JSON_INVALID")
        valid = json.dumps(capture())
        self.assertEqual(bridge.validate_capture_json("BTC/USD", valid, as_of=T, policy=PROJECTION), evaluate(capture()))

    def test_no_input_mutation_no_network_no_wall_clock_at_import_or_execution(self):
        inputs = copy.deepcopy(FIXTURE["captures"])
        original = copy.deepcopy(inputs)
        with patch.object(socket, "socket", side_effect=AssertionError("network forbidden")), \
             patch.object(socket, "create_connection", side_effect=AssertionError("network forbidden")), \
             patch.object(urllib.request, "urlopen", side_effect=AssertionError("network forbidden")), \
             patch.object(time, "time", side_effect=AssertionError("clock forbidden")):
            importlib.reload(bridge)
            result = bridge.validate_captures(inputs, as_of=T, policy=PROJECTION)
            self.assertTrue(all(r["decision"]["status"] == "VALIDATED_DATA" for r in result.values()))
            bridge.validate_capture_json("BTC/USD", json.dumps(capture()), as_of=T, policy=PROJECTION)
        self.assertEqual(inputs, original)


if __name__ == "__main__":
    unittest.main()
