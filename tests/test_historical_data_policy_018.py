"""SYNTHETIC test-only mathematical policy model, never a runtime gate/collector.

Even complete modeled evidence returns HOLD. Inputs assert assumptions, not truth.
"""
import copy
from contextlib import ExitStack, redirect_stdout
from fractions import Fraction
import io
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from research import spot_refusal_registry as registry
from research import kraken_spot_diagnostic as diagnostic
from research import kraken_probe_corrections as corrections

NS = 10**9
HOUR_NS = 3600 * NS
T = 1900000800 * NS
BINDING = {"revision": "0"*40, "run": "synthetic-run-018", "boot": "synthetic-boot", "domain": "synthetic-mono"}


def cutoff(w_est_ns, u_ns, lag_hours):
    """Integer floor, not truncation; illustrative parameters only."""
    if any(type(v) is not int for v in (w_est_ns, u_ns, lag_hours)) or u_ns < 0 or not 0 <= lag_hours <= 24:
        raise ValueError("PARAMETER_INVALID")
    result = ((w_est_ns-u_ns)//HOUR_NS - lag_hours)*3600
    if not registry.MIN_TIME <= result < registry.MAX_TIME:
        raise ValueError("CUTOFF_RANGE")
    return result


def assumed_record():
    return {"kind": "SYNTHETIC_ASSUMPTIONS_ONLY", "unit": "ns", "source": "mock-local-clock",
            "source_version": "mock-v1", "provenance": "MOCK_REVIEWED_NOT_ATTESTED", **BINDING,
            "active": True, "synchronized": True, "leap_normal": True, "step_detected": False,
            "w_est_ns": T, "last_sync_mono_ns": 90*NS, "sample_mono_ns": 99*NS,
            "capture_mono_ns": 100*NS, "now_mono_ns": 101*NS, "horizon_end_mono_ns": 110*NS,
            "lease_end_mono_ns": 120*NS, "holdover_at_capture_ns": 10*NS,
            "offset_ns": 100000000, "delay_ns": 50000000, "dispersion_ns": 20000000,
            "sampling_ns": 5000000, "drift_ppb": 100000,
            "u_ns": 60*NS, "lag_hours": 1}


def model(record, expected_binding):
    """Reject inconsistent assumed records; cannot verify host/source correctness."""
    def no(reason):
        return {"decision": "NO_GO", "reason": reason}
    expected = set(assumed_record())
    if type(record) is not dict or set(record) != expected:
        return no("SCHEMA_INVALID")
    if (record["kind"] != "SYNTHETIC_ASSUMPTIONS_ONLY" or record["unit"] != "ns"
            or record["source"] != "mock-local-clock" or record["source_version"] != "mock-v1"
            or record["provenance"] != "MOCK_REVIEWED_NOT_ATTESTED"):
        return no("PROVENANCE_OR_UNIT_UNVERIFIED")
    if any(record[k] != v or type(record[k]) is not str for k, v in expected_binding.items()):
        return no("BINDING_MISMATCH")
    if any(type(record[k]) is not bool or not record[k] for k in ("active", "synchronized", "leap_normal")):
        return no("SYNC_UNVERIFIED")
    if type(record["step_detected"]) is not bool or record["step_detected"]:
        return no("CLOCK_STEP")
    numeric = expected - {"kind", "unit", "source", "source_version", "provenance", *BINDING,
                          "active", "synchronized", "leap_normal", "step_detected"}
    if any(type(record[k]) is not int or abs(record[k]) > 10**20 for k in numeric):
        return no("VALUE_INVALID")
    if any(record[k] < 0 for k in numeric - {"offset_ns"}):
        return no("VALUE_INVALID")
    last, sample, capture, now, horizon, expiry = (record[k] for k in (
        "last_sync_mono_ns", "sample_mono_ns", "capture_mono_ns", "now_mono_ns",
        "horizon_end_mono_ns", "lease_end_mono_ns"))
    if not last <= sample <= capture <= now < horizon < expiry:
        return no("AGE_LEASE_OR_MONOTONIC_INVALID")
    if record["holdover_at_capture_ns"] != capture-last:
        return no("HOLDOVER_MISMATCH")
    # Synthetic profile requires a status sample no older than one second.
    # This is not an approved production age limit or native daemon field map.
    if capture-sample > NS:
        return no("STATUS_SAMPLE_EXPIRED")
    bound = (abs(record["offset_ns"]) + Fraction(record["delay_ns"], 2)
             + record["dispersion_ns"] + record["sampling_ns"]
             + Fraction(record["drift_ppb"]*(horizon-last), NS))
    rounded = -(-bound.numerator//bound.denominator)
    if record["u_ns"] < rounded:
        return no("UNDERREPORTED_MODEL_BOUND")
    try:
        coordinate = cutoff(record["w_est_ns"], record["u_ns"], record["lag_hours"])
    except ValueError:
        return no("PARAMETER_INVALID")
    return {"decision": "HOLD", "reason": "CONDITIONAL_MODEL_NOT_AUTHORIZATION",
            "as_of": coordinate, "modeled_horizon_bound_ns": rounded}


FIXTURE = json.loads((Path(__file__).parent / "fixtures/spot_refusal_v1.json").read_text())
POLICY = {"version": registry.VERSION, "future_mode": "as_of"}


class HistoricalPolicyTests(unittest.TestCase):
    def setUp(self):
        stack = ExitStack()
        self.addCleanup(stack.close)
        guards = [stack.enter_context(patch(name, side_effect=AssertionError("FORBIDDEN_IO")))
                  for name in ("socket.socket", "socket.create_connection", "socket.getaddrinfo",
                               "urllib.request.urlopen", "http.client.HTTPSConnection",
                               "subprocess.run", "subprocess.Popen", "time.time")]
        self.addCleanup(lambda: [g.assert_not_called() for g in guards])

    def test_complete_synthetic_record_can_only_hold(self):
        result = model(assumed_record(), BINDING)
        self.assertEqual(result["decision"], "HOLD")
        self.assertEqual(result["modeled_horizon_bound_ns"], 152000000)
        self.assertEqual(result["as_of"], T//NS-7200)

    def test_exact_hour_plus_minus_u_and_one_ns_boundaries(self):
        u = 60*NS
        self.assertEqual(cutoff(T+u, u, 1), T//NS-3600)
        self.assertEqual(cutoff(T+u-1, u, 1), T//NS-7200)
        self.assertEqual(cutoff(T-u, u, 1), T//NS-7200)
        for true in (T-1, T, T+1):
            for error in (-u, -u+1, 0, u-1, u):
                self.assertLessEqual(cutoff(true+error, u, 1)*NS+HOUR_NS, true)

    def test_conditional_property_grid_and_floor_lower_bound(self):
        for true in (T-NS, T-1, T, T+1, T+NS, T+HOUR_NS-1):
            for u in (0, 1, 2*NS, 60*NS):
                for error in (-u, 0, u):
                    for lag in (0, 1, 2):
                        a = cutoff(true+error, u, lag)*NS
                        self.assertLessEqual(a+lag*HOUR_NS, true)
                        self.assertLess(true-a, 2*u+(lag+1)*HOUR_NS)

    def test_uncertainty_round_up_not_nearest(self):
        record = assumed_record()
        record.update(offset_ns=0, delay_ns=1, dispersion_ns=0, sampling_ns=0, drift_ppb=0, u_ns=0)
        self.assertEqual(model(record, BINDING)["reason"], "UNDERREPORTED_MODEL_BOUND")
        record["u_ns"] = 1
        self.assertEqual(model(record, BINDING)["modeled_horizon_bound_ns"], 1)

    def test_gross_one_day_fast_clock_defeats_lag(self):
        self.assertGreater(cutoff(T+86400*NS, 60*NS, 1)*NS, T)

    def test_underreported_real_error_is_undetectable_by_self_consistency(self):
        record = assumed_record()
        record["w_est_ns"] = T+86400*NS
        result = model(record, BINDING)
        self.assertEqual(result["decision"], "HOLD")
        self.assertGreater(result["as_of"]*NS, T)
        # Oracle T belongs only to this adversarial test, not the collector.
        self.assertGreater(abs(record["w_est_ns"]-T), record["u_ns"])

    def test_missing_false_or_wrong_type_synchronization_refuses(self):
        for key in ("active", "synchronized", "leap_normal"):
            for value in (False, None, 1, "yes"):
                r = assumed_record(); r[key] = value
                self.assertEqual(model(r, BINDING)["decision"], "NO_GO")
        for key in assumed_record():
            r = assumed_record(); del r[key]
            self.assertEqual(model(r, BINDING)["reason"], "SCHEMA_INVALID")

    def test_leap_step_and_monotonic_reversal_refuse(self):
        for key, value in (("leap_normal", False), ("step_detected", True),
                           ("now_mono_ns", 99*NS), ("capture_mono_ns", 98*NS),
                           ("last_sync_mono_ns", 101*NS)):
            r = assumed_record(); r[key] = value
            self.assertEqual(model(r, BINDING)["decision"], "NO_GO")

    def test_expired_and_insufficient_horizon_leases_refuse_at_equality(self):
        for now in (110*NS, 120*NS, 121*NS):
            r = assumed_record(); r["now_mono_ns"] = now
            self.assertEqual(model(r, BINDING)["decision"], "NO_GO")
        r = assumed_record(); r["lease_end_mono_ns"] = r["horizon_end_mono_ns"]
        self.assertEqual(model(r, BINDING)["decision"], "NO_GO")

    def test_sample_age_and_holdover_cannot_be_fabricated(self):
        r = assumed_record(); r["holdover_at_capture_ns"] = 0
        self.assertEqual(model(r, BINDING)["reason"], "HOLDOVER_MISMATCH")
        r = assumed_record(); r["sample_mono_ns"] = 98*NS
        self.assertEqual(model(r, BINDING)["reason"], "STATUS_SAMPLE_EXPIRED")

    def test_aging_horizon_increases_bound_without_moving_frozen_cutoff(self):
        first = assumed_record()
        second = assumed_record(); second["horizon_end_mono_ns"] = 115*NS
        self.assertGreater(model(second, BINDING)["modeled_horizon_bound_ns"], model(first, BINDING)["modeled_horizon_bound_ns"])
        self.assertEqual(model(second, BINDING)["as_of"], model(first, BINDING)["as_of"])
        second["now_mono_ns"] = 109*NS
        self.assertEqual(model(second, BINDING)["as_of"], model(first, BINDING)["as_of"])

    def test_untrusted_source_units_version_and_binding_refuse(self):
        for key, value in (("unit", "ms"), ("unit", None), ("source_version", "unknown"),
                           ("provenance", "self_attested"), ("source", "unverified"),
                           *[(k, "wrong") for k in BINDING]):
            r = assumed_record(); r[key] = value
            self.assertEqual(model(r, BINDING)["decision"], "NO_GO")

    def test_invalid_parameters_and_nonfinite_values_refuse(self):
        for key in ("u_ns", "drift_ppb", "delay_ns", "w_est_ns", "lag_hours"):
            for value in (None, True, float("nan"), float("inf"), "60"):
                r = assumed_record(); r[key] = value
                self.assertEqual(model(r, BINDING)["decision"], "NO_GO")
        for args in ((T, -1, 1), (T, NS, -1), (T, NS, 25), (0, 0, 1)):
            with self.assertRaises(ValueError):
                cutoff(*args)

    def test_declared_u_smaller_than_model_is_no_go(self):
        r = assumed_record(); r["u_ns"] = 151999999
        self.assertEqual(model(r, BINDING)["reason"], "UNDERREPORTED_MODEL_BOUND")

    def test_stale_relative_cutoff_is_not_fresh_relative_true_time(self):
        data = copy.deepcopy(FIXTURE["payload"])
        a = FIXTURE["as_of"]
        result = registry.validate_symbol("BTC/USD", data, as_of=a, policy=POLICY)
        self.assertEqual(result["status"], "VALIDATED_DATA")
        self.assertEqual(registry.validate_symbol("BTC/USD", data, as_of=a+4*3600, policy=POLICY)["reason_code"], "DATA_STALE")
        self.assertEqual(registry.validate_symbol("BTC/USD", data, as_of=a+3*3600, policy=POLICY)["status"], "VALIDATED_DATA")

    def test_gapped_partial_invalid_and_old_eligible_history_refuse(self):
        for mode, expected in (("gap", "TIMESTAMP_GAP"), ("partial", "WARMUP_INCOMPLETE"),
                                ("bad", "INVALID_VALUE")):
            data = copy.deepcopy(FIXTURE["payload"])
            if mode == "gap": data["bars"].pop(10)
            elif mode == "partial": data["bars"].pop(0)
            else: data["bars"][0]["close"] = -1
            self.assertEqual(registry.validate_symbol("BTC/USD", data, as_of=FIXTURE["as_of"], policy=POLICY)["reason_code"], expected)

    def test_future_appends_preserve_complete_registry_evidence(self):
        for invalid in (False, True):
            data = copy.deepcopy(FIXTURE["payload"])
            if invalid: data["bars"][0]["close"] = -1
            before = registry.canonical_json(registry.validate_symbol("BTC/USD", data, as_of=FIXTURE["as_of"], policy=POLICY))
            data["bars"].append(dict(open_time=FIXTURE["as_of"], open=None, high=-1, low="IGNORED", close=1e99, volume=0))
            self.assertEqual(before, registry.canonical_json(registry.validate_symbol("BTC/USD", data, as_of=FIXTURE["as_of"], policy=POLICY)))

    def test_age_envelope_is_historical_not_current_signal(self):
        u = 60*NS; lag = 1
        true = T; w = true-u
        a = cutoff(w, u, lag)*NS
        latest_close = a-3*HOUR_NS
        self.assertGreater(true-latest_close, 3*HOUR_NS)
        self.assertLess(true-latest_close, 2*u+(lag+4)*HOUR_NS)

    def test_clis_remain_disabled_and_limits_unchanged(self):
        for module in (diagnostic, corrections):
            with redirect_stdout(io.StringIO()) as output:
                self.assertEqual(module.main(), 2)
            result = json.loads(output.getvalue())
            self.assertEqual(result["reason"], "AUTHORIZATION_MISSING")
            self.assertEqual(result["requests"], 0)
        self.assertEqual(diagnostic.CAPTURE_POLICY, "manual-capture-v1")
        self.assertEqual(diagnostic.DEADLINE_NS, 10*NS)
        self.assertEqual(corrections.HEADER_LIMIT, 8192)
        self.assertEqual(corrections.BODY_LIMIT, 262144)


if __name__ == "__main__":
    unittest.main()
