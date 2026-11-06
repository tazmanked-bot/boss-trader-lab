"""Offline characterization and executable design examples, NOT a live runner.

The test-only clock model illustrates the proposed 011 capture policy. It does
not add or test an implemented transport/clock gate. All response data is from
the existing synthetic fixture; no current exchange behavior is asserted.
"""

import copy
import json
from pathlib import Path
import unittest

from research import kraken_spot_validation_bridge as bridge
from research import spot_refusal_registry as registry


FIXTURE = json.loads((Path(__file__).parent / "fixtures" / "kraken_spot_bridge_v1.json").read_text())
T = FIXTURE["as_of"]
NS = 1_000_000_000
POLICY = {"version": "spot-refusal-v1", "future_mode": "as_of"}


def proposed_first_capture_cutoff(start_ns, end_ns, monotonic_elapsed_ns, service_date_s):
    """Test-only first-request policy model: 2s guard, 10s total, 1s drift.

    Future requests would retain this frozen cutoff and independently check their
    own clock envelopes. These design examples are not production clock code.
    """
    if any(type(v) is not int for v in (start_ns, end_ns, monotonic_elapsed_ns, service_date_s)):
        raise ValueError("CLOCK_UNVERIFIED")
    if not 946684800 * NS <= start_ns <= end_ns < 4102444800 * NS:
        raise ValueError("CLOCK_CONFLICT")
    if not 0 <= monotonic_elapsed_ns <= 10 * NS:
        raise ValueError("TIMEOUT")
    if abs((end_ns - start_ns) - monotonic_elapsed_ns) > NS:
        raise ValueError("CLOCK_CONFLICT")
    if not start_ns // NS - 2 <= service_date_s <= end_ns // NS + 2:
        raise ValueError("SERVICE_TIME_CONFLICT")
    return ((start_ns // NS - 2) // 3600) * 3600


def capture(symbol="BTC/USD"):
    return copy.deepcopy(FIXTURE["captures"][symbol])


def rows(obj):
    data = obj["response"]["result"]
    return data[next(k for k in data if k != "last")]


def evaluate(obj, as_of=T):
    return bridge.validate_capture("BTC/USD", obj, as_of=as_of, policy=POLICY)


class ReadinessContractTests(unittest.TestCase):
    def test_proposed_cutoff_examples_at_hour_boundary(self):
        # Literal expectations: no clock lookup, no end-time-derived advancement.
        examples = ((T - 1, T + 1, 2, T, T - 3600),
                    (T, T + 2, 2, T, T - 3600),
                    (T + 1, T + 3, 2, T + 1, T - 3600),
                    (T + 2, T + 4, 2, T + 2, T),
                    (T + 3599, T + 3601, 2, T + 3600, T))
        for start, end, elapsed, service, expected in examples:
            with self.subTest(start=start):
                actual = proposed_first_capture_cutoff(start * NS, end * NS, elapsed * NS, service)
                self.assertEqual(actual, expected)
                self.assertLessEqual(actual, start - 2)
        self.assertEqual(proposed_first_capture_cutoff(T * NS - 1, (T + 1) * NS,
                         NS + 1, T), T - 3600)

    def test_proposed_clock_model_refuses_skew_jumps_timeouts_and_unverified_time(self):
        cases = ((T * NS, (T - 1) * NS, NS, T),  # Backward wall clock.
                 (T * NS, (T + 20) * NS, NS, T),  # Wall/monotonic discrepancy.
                 (T * NS, (T + 11) * NS, 11 * NS, T),  # Total deadline.
                 (T * NS, (T + 1) * NS, NS, T - 3),  # Service clock too early.
                 (T * NS, (T + 1) * NS, NS, T + 4),  # Service clock too late.
                 (T * NS, (T + 1) * NS, NS, None),  # Missing Date is not approval.
                 (True, (T + 1) * NS, NS, T),
                 (T * NS, (T + 1) * NS, NS, float("nan")))
        for args in cases:
            with self.subTest(args=args):
                with self.assertRaises(ValueError):
                    proposed_first_capture_cutoff(*args)

    def test_boundary_race_end_clock_would_include_an_extra_hour(self):
        cutoff = proposed_first_capture_cutoff((T - 1) * NS, (T + 1) * NS, 2 * NS, T)
        early = evaluate(capture(), as_of=cutoff)
        self.assertEqual(early["decision"]["reason_code"], "WARMUP_INCOMPLETE")
        # A response ending after T must not make the 21st close knowable before T.
        self.assertEqual(evaluate(capture(), as_of=T)["decision"]["status"], "VALIDATED_DATA")
        self.assertEqual(early["decision"]["as_of_utc"], "2030-03-17T16:00:00Z")

    def test_new_display_or_changed_alias_is_not_automatically_trusted(self):
        for symbol, new_key in (("BTC/USD", "BTC/USD"), ("XRP/USD", "XRP/USD"),
                                ("SOL/USD", "SOLUSD_v2")):
            obj = capture(symbol)
            data = obj["response"]["result"]
            key = next(k for k in data if k != "last")
            data[new_key] = data.pop(key)
            result = bridge.validate_capture(symbol, obj, as_of=T, policy=POLICY)
            self.assertEqual(result["bridge_code"], "PAIR_MISMATCH")
            self.assertEqual(result["decision"]["reason_code"], "DATA_UNAVAILABLE")

    def test_isolated_btc_success_xrp_alias_failure_sol_api_error(self):
        inputs = {s: capture(s) for s in FIXTURE["captures"]}
        result = inputs["XRP/USD"]["response"]["result"]
        result["unknown"] = result.pop("XXRPZUSD")
        inputs["SOL/USD"]["response"]["error"] = ["DO_NOT_ECHO service error"]
        actual = bridge.validate_captures(inputs, as_of=T, policy=POLICY)
        self.assertEqual(actual["BTC/USD"]["decision"]["status"], "VALIDATED_DATA")
        self.assertEqual(actual["XRP/USD"]["bridge_code"], "PAIR_MISMATCH")
        self.assertEqual(actual["SOL/USD"]["bridge_code"], "SOURCE_API_ERROR")
        self.assertNotIn("DO_NOT_ECHO", registry.canonical_json(actual))

    def test_eligible_row_array_type_width_and_count_changes_refuse(self):
        for replacement, code in (({}, "ROW_SCHEMA"), ([T] * 7, "ROW_SCHEMA"),
                                   ([T] * 9, "ROW_SCHEMA")):
            obj = capture()
            rows(obj)[10] = replacement
            self.assertEqual(evaluate(obj)["bridge_code"], code)
        for count in ("20", 20.0, True, -1):
            obj = capture()
            rows(obj)[10][7] = count
            self.assertEqual(evaluate(obj)["bridge_code"], "COUNT_INVALID")

    def test_whole_result_refusal_invariance_after_future_append(self):
        failures = []
        gap = capture()
        rows(gap).pop(10)
        failures.append((gap, "TIMESTAMP_GAP"))
        duplicate = capture()
        rows(duplicate).insert(1, copy.deepcopy(rows(duplicate)[0]))
        failures.append((duplicate, "DUPLICATE_TIMESTAMP"))
        stale = capture()
        rows(stale).pop()  # Synthetic fixture adjustment, not a production drop.
        for row in rows(stale):
            row[0] -= 4 * 3600
        failures.append((stale, "DATA_STALE"))
        malformed = capture()
        rows(malformed)[10][1] = "NaN"
        failures.append((malformed, "DATA_UNAVAILABLE"))
        for obj, reason in failures:
            expected = evaluate(obj)
            self.assertEqual(expected["decision"]["reason_code"], reason)
            before = registry.canonical_json(expected).encode("ascii")
            rows(obj).append([T + 3600] + ["DO_NOT_ECHO future"] * 7)
            self.assertEqual(registry.canonical_json(evaluate(obj)).encode("ascii"), before)
            self.assertEqual(evaluate(obj)["decision"]["status"], "REFUSED")

    def test_projection_does_not_ignore_malformed_future_headers(self):
        for stamp in (str(T), True, T * 1000, T + 1):
            obj = capture()
            rows(obj).append([stamp] + ["ignored"] * 7)
            self.assertEqual(evaluate(obj)["bridge_code"], "TIMESTAMP_INVALID")
            self.assertEqual(evaluate(obj)["decision"]["status"], "REFUSED")


if __name__ == "__main__":
    unittest.main()
