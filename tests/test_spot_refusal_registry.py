"""Offline adversarial contract tests; no installed packages or market access."""

import copy
import importlib
import json
from pathlib import Path
import socket
import time
import unittest
from unittest.mock import patch
import urllib.request

from research import spot_refusal_registry as registry


FIXTURE = json.loads((Path(__file__).parent / "fixtures" / "spot_refusal_v1.json").read_text())
T = FIXTURE["as_of"]
AS_OF = {"version": "spot-refusal-v1", "future_mode": "as_of"}


def fixture(symbol="BTC/USD", shift=0):
    data = copy.deepcopy(FIXTURE["payload"])
    data["symbol"] = symbol
    for bar in data["bars"]:
        bar["open_time"] += shift
    return data


def evaluate(data, policy=None, as_of=T):
    return registry.validate_symbol("BTC/USD", data, as_of=as_of, policy=policy)


class SpotRefusalTests(unittest.TestCase):
    def assert_refused(self, result, reason):
        self.assertEqual(result["status"], "REFUSED")
        self.assertEqual(result["reason_code"], reason)
        self.assertLess(len(registry.canonical_json(result).encode("ascii")), 1024)
        self.assertRegex(result["evidence_ref"], r"^sha256:[0-9a-f]{64}$")

    def test_exact_fixture_mutation_matrix(self):
        for case in FIXTURE["cases"]:
            with self.subTest(case=case["name"]):
                data = fixture()
                if not case["path"]:
                    data = case["value"]
                else:
                    target = data
                    for key in case["path"][:-1]:
                        target = target[key]
                    target[case["path"][-1]] = case["value"]
                self.assert_refused(evaluate(data), case["reason"])

    def test_missing_fields_never_become_partial_valid_data(self):
        for key in fixture():
            data = fixture()
            del data[key]
            self.assert_refused(evaluate(data), "MALFORMED_DATA")
        for key in fixture()["bars"][0]:
            data = fixture()
            del data["bars"][0][key]
            self.assert_refused(evaluate(data), "MALFORMED_DATA")

    def test_each_ohlcv_rejects_nonfinite_wrong_types_and_oversized_numbers(self):
        for key in ("open", "high", "low", "close", "volume"):
            for value in (float("nan"), float("inf"), -float("inf"), True, "1", None, [], {}, 10 ** 1000):
                for index in (0, 10, 20):
                    with self.subTest(key=key, value_type=type(value).__name__, index=index):
                        data = fixture()
                        data["bars"][index][key] = value
                        self.assert_refused(evaluate(data), "INVALID_VALUE")

    def test_zero_prices_fail_but_zero_volume_is_valid(self):
        for key in ("open", "high", "low", "close"):
            data = fixture()
            data["bars"][10][key] = 0
            self.assert_refused(evaluate(data), "INVALID_VALUE")
        data = fixture()
        data["bars"][10]["volume"] = 0
        self.assertEqual(evaluate(data)["status"], "VALIDATED_DATA")

    def test_duplicate_order_gap_and_no_sorting_or_mutation(self):
        duplicate = fixture()
        duplicate["bars"].insert(10, copy.deepcopy(duplicate["bars"][0]))
        reverse = fixture()
        reverse["bars"].reverse()
        gap = fixture()
        del gap["bars"][10]
        for data, code in ((duplicate, "DUPLICATE_TIMESTAMP"), (reverse, "TIMESTAMP_ORDER"),
                           (gap, "TIMESTAMP_GAP")):
            original = copy.deepcopy(data)
            self.assert_refused(evaluate(data), code)
            self.assertEqual(data, original)

    def test_20_21_and_more_closed_bars(self):
        data = fixture()
        data["bars"].pop(0)
        self.assert_refused(evaluate(data), "WARMUP_INCOMPLETE")
        self.assertEqual(evaluate(fixture())["status"], "VALIDATED_DATA")
        data = fixture()
        earlier = copy.deepcopy(data["bars"][0])
        earlier["open_time"] -= 3600
        data["bars"].insert(0, earlier)
        self.assertEqual(evaluate(data)["status"], "VALIDATED_DATA")
        data["bars"][0]["close"] = -1
        self.assert_refused(evaluate(data), "INVALID_VALUE")  # Outside latest 21 still fails.

    def test_strict_closed_boundary_future_and_unfinished(self):
        self.assertEqual(evaluate(fixture())["status"], "VALIDATED_DATA")  # Close exactly T.
        for open_time in (T, T + 3600, T + 3600 * 200):
            data = fixture()
            future = copy.deepcopy(data["bars"][-1])
            future["open_time"] = open_time
            data["bars"].append(future)
            self.assert_refused(evaluate(data), "CANDLE_NOT_CLOSED")

    def test_staleness_boundary_is_per_symbol(self):
        self.assertEqual(evaluate(fixture(shift=-3 * 3600))["status"], "VALIDATED_DATA")
        self.assert_refused(evaluate(fixture(shift=-4 * 3600)), "DATA_STALE")
        payloads = {"BTC/USD": fixture(), "XRP/USD": fixture("XRP/USD", -4 * 3600),
                    "SOL/USD": fixture("SOL/USD", -5 * 3600)}
        result = registry.validate_symbols(payloads, as_of=T)
        self.assertEqual(result["BTC/USD"]["status"], "VALIDATED_DATA")
        for symbol in ("XRP/USD", "SOL/USD"):
            self.assert_refused(result[symbol], "DATA_STALE")
        payloads["BTC/USD"] = fixture(shift=-4 * 3600)
        self.assertTrue(all(r["reason_code"] == "DATA_STALE"
                            for r in registry.validate_symbols(payloads, as_of=T).values()))

    def test_missing_and_unknown_symbols_fail_closed_without_ranking(self):
        result = registry.validate_symbols({}, as_of=T)
        self.assertEqual(tuple(result), ("BTC/USD", "XRP/USD", "SOL/USD"))
        for row in result.values():
            self.assert_refused(row, "DATA_UNAVAILABLE")
        for payloads in (None, [], {"BTC/USDT": fixture()}, {"BTC/USD": fixture(), "other": fixture()}):
            for row in registry.validate_symbols(payloads, as_of=T).values():
                self.assert_refused(row, "MALFORMED_DATA")
        result = registry.validate_symbol("SECRET" * 1000, fixture(), as_of=T)
        self.assert_refused(result, "MARKET_MISMATCH")
        self.assertIsNone(result["symbol"])

    def test_unknown_policy_fields_values_and_rule_conflicts(self):
        for policy in ({}, [], True, {**AS_OF, "score": 1000000}, {**AS_OF, "version": "v2"},
                       {**AS_OF, "future_mode": "repair"}, {**AS_OF, "future_mode": []}):
            self.assert_refused(evaluate(fixture(), policy=policy), "CONFIG_INVALID")
        data = fixture()
        data["rules"]["require_non_spot"] = True
        self.assert_refused(evaluate(data), "RULE_CONFLICT")
        data["score"] = 10 ** 9  # Unknown score cannot rescue contradiction.
        self.assert_refused(evaluate(data), "MALFORMED_DATA")

    def test_registry_crosswalk_and_unknown_codes(self):
        expected = {"MALFORMED_DATA", "MARKET_MISMATCH", "INVALID_VALUE", "TIMESTAMP_INVALID",
                    "TIME_UNIT_MISMATCH", "DUPLICATE_TIMESTAMP", "TIMESTAMP_ORDER", "TIMESTAMP_GAP",
                    "CANDLE_NOT_CLOSED", "WARMUP_INCOMPLETE", "DATA_STALE", "RULE_CONFLICT",
                    "POLICY_REJECTED", "CONFIG_INVALID", "DATA_UNAVAILABLE", "UNKNOWN_REASON"}
        self.assertEqual({r.value for r in registry.Reason}, expected)
        for code in expected:
            self.assert_refused(registry.refusal("BTC/USD", as_of=T, reason=code), code)
        for code in ("PASS", "NONE", "", "DO_NOT_ECHO" * 1000, None, [], {}):
            result = registry.refusal("BTC/USD", as_of=T, reason=code)
            self.assert_refused(result, "UNKNOWN_REASON")
            self.assertNotIn("DO_NOT_ECHO", registry.canonical_json(result))

    def test_explicit_asof_contract_full_output_invariant_with_adversarial_future(self):
        original = fixture()
        reference = registry.canonical_json(evaluate(original, policy=AS_OF)).encode("ascii")
        for value in (-1, 1e99, "IGNORED_FUTURE_VALUE", None, {"secret": "DO_NOT_ECHO"}):
            data = copy.deepcopy(original)
            for offset in range(5):
                future = {"open_time": T + offset * 3600,
                          "open": value, "high": value, "low": value, "close": value, "volume": value}
                data["bars"].append(future)
            self.assertEqual(registry.canonical_json(evaluate(data, policy=AS_OF)).encode("ascii"), reference)
            # Strict JSON entry point also retains the entire output invariant.
            self.assertEqual(registry.canonical_json(registry.validate_json("BTC/USD", json.dumps(data),
                             as_of=T, policy=AS_OF)).encode("ascii"), reference)
            data["bars"][10]["close"] = -1
            self.assert_refused(evaluate(data, policy=AS_OF), "INVALID_VALUE")

    def test_invalid_future_headers_do_not_hide_malformed_eligible_data(self):
        for stamp, code in ((True, "TIMESTAMP_INVALID"), (str(T), "TIMESTAMP_INVALID"),
                            (T * 1000, "TIME_UNIT_MISMATCH"), (T + 1, "TIMESTAMP_INVALID")):
            data = fixture()
            data["bars"][10]["open_time"] = stamp
            data["bars"][10]["close"] = -1
            self.assert_refused(evaluate(data, policy=AS_OF), code)
        data = fixture()
        future = copy.deepcopy(data["bars"][-1])
        future.update(open_time=T, unknown=True)
        data["bars"].append(future)
        self.assert_refused(evaluate(data, policy=AS_OF), "MALFORMED_DATA")

    def test_eligible_refusal_output_also_invariant_after_future_append(self):
        data = fixture()
        data["bars"][20]["close"] = 0
        baseline = registry.canonical_json(evaluate(data, policy=AS_OF))
        future = copy.deepcopy(data["bars"][-1])
        future.update(open_time=T + 3600, close=1e99)
        data["bars"].append(future)
        self.assertEqual(registry.canonical_json(evaluate(data, policy=AS_OF)), baseline)
        self.assert_refused(evaluate(data, policy=AS_OF), "INVALID_VALUE")

    def test_asof_mode_does_not_fill_empty_or_incomplete_eligible_history(self):
        data = fixture()
        for bar in data["bars"]:
            bar["open_time"] += 100 * 3600
        self.assert_refused(evaluate(data, policy=AS_OF), "WARMUP_INCOMPLETE")
        data = fixture()
        data["bars"][-1]["open_time"] = T
        self.assert_refused(evaluate(data, policy=AS_OF), "WARMUP_INCOMPLETE")

    def test_clock_is_required_valid_utc_seconds_and_not_guessed(self):
        for value, code in ((True, "TIMESTAMP_INVALID"), (str(T), "TIMESTAMP_INVALID"),
                            (float("nan"), "TIMESTAMP_INVALID"), (T + 1, "TIMESTAMP_INVALID"),
                            (T * 1000, "TIME_UNIT_MISMATCH"), (None, "TIMESTAMP_INVALID")):
            result = evaluate(fixture(), as_of=value)
            self.assert_refused(result, code)
            self.assertIsNone(result["as_of_utc"])
        with self.assertRaises(TypeError):
            registry.validate_symbol("BTC/USD", fixture())

    def test_strict_json_rejects_nonfinite_duplicate_keys_and_parser_errors(self):
        valid = json.dumps(fixture())
        for raw in ("NaN", "Infinity", "-Infinity", "1e999", '{"x":1,"x":2}',
                    "{" + "DO_NOT_ECHO" * 1000, "[" * 2000, "\ud800", None):
            result = registry.validate_json("BTC/USD", raw, as_of=T)
            self.assert_refused(result, "MALFORMED_DATA")
            self.assertNotIn("DO_NOT_ECHO", registry.canonical_json(result))
        for bad in ("NaN", "Infinity", "1e999"):
            raw = valid.replace('"close": 101', '"close": ' + bad, 1)
            self.assert_refused(registry.validate_json("BTC/USD", raw, as_of=T), "MALFORMED_DATA")
        self.assertEqual(registry.validate_json("BTC/USD", valid, as_of=T), evaluate(fixture()))
        with self.assertRaises(ValueError):
            registry.canonical_json({"invalid": float("nan")})

    def test_bounded_input_output_and_redacted_exception_details(self):
        data = fixture()
        data["bars"] *= 25  # 525 exceeds documented 512 row bound.
        self.assert_refused(evaluate(data), "MALFORMED_DATA")
        for raw in (" " * (262144 + 1), '"' + "\u20ac" * 90000 + '"'):
            self.assert_refused(registry.validate_json("BTC/USD", raw, as_of=T), "MALFORMED_DATA")
        data = fixture()
        data["bars"][0]["close"] = "PRIVATE_EXCEPTION_OR_CREDENTIAL" * 10000
        result = evaluate(data)
        self.assert_refused(result, "INVALID_VALUE")
        self.assertNotIn("PRIVATE_EXCEPTION_OR_CREDENTIAL", registry.canonical_json(result))

    def test_exact_metadata_determinism_and_evidence_changes_for_eligible_data(self):
        result = evaluate(fixture())
        self.assertEqual(result["status"], "VALIDATED_DATA")
        self.assertIsNone(result["reason_code"])
        self.assertEqual(result["evidence_ref"],
                         "sha256:6c2acdf3204f563294602f36ab1f67ec186a5edbe948b5b37bc0466e2e617589")
        self.assertEqual(result["as_of_utc"], "2030-03-17T17:00:00Z")
        self.assertEqual({k: result[k] for k in ("symbol", "venue", "market", "quote", "timeframe", "policy_version")},
                         {"symbol": "BTC/USD", "venue": "kraken", "market": "spot", "quote": "USD",
                          "timeframe": "1h", "policy_version": "spot-refusal-v1"})
        data = fixture()
        original = copy.deepcopy(data)
        self.assertEqual(evaluate(data), evaluate(data))
        self.assertEqual(data, original)
        data["bars"][-1]["volume"] += 1
        self.assertNotEqual(evaluate(data)["evidence_ref"], result["evidence_ref"])
        self.assertNotEqual(evaluate(fixture(), policy=AS_OF)["evidence_ref"], result["evidence_ref"])
        self.assertEqual(set(result), {"status", "reason_code", "detail", "evidence_ref", "symbol", "venue",
                                      "market", "quote", "timeframe", "as_of_utc", "policy_version", "future_mode"})

    def test_import_and_execution_do_not_use_network_or_wall_clock(self):
        with patch.object(socket, "socket", side_effect=AssertionError("network forbidden")), \
             patch.object(socket, "create_connection", side_effect=AssertionError("network forbidden")), \
             patch.object(urllib.request, "urlopen", side_effect=AssertionError("network forbidden")), \
             patch.object(time, "time", side_effect=AssertionError("clock forbidden")):
            module = importlib.reload(registry)
            result = module.validate_symbols({s: fixture(s) for s in module.SYMBOLS}, as_of=T)
            self.assertTrue(all(row["status"] == "VALIDATED_DATA" for row in result.values()))
            module.validate_json("BTC/USD", json.dumps(fixture()), as_of=T)


if __name__ == "__main__":
    unittest.main()
