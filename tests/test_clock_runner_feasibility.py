"""Test-only evidence/cutoff models. No clock collector or attestation authority.

All estimates and worker observations below are synthetic. No helper can return
live GO or replace the existing runtime's two-second policy.
"""

from contextlib import ExitStack, redirect_stdout
import copy
from fractions import Fraction
import http.client
import io
import json
from pathlib import Path
import socket
import subprocess
import unittest
from unittest.mock import patch
import urllib.request

from research import kraken_probe_corrections as corrections
from research import kraken_spot_diagnostic as diagnostic
from research import spot_refusal_registry as registry


ROOT = Path(__file__).parent / "fixtures"
FIXTURE = json.loads((ROOT / "clock_runner_evidence_015.json").read_text())
NS = 1_000_000_000
BINDING = {k: FIXTURE["clock_estimate"][k] for k in ("run_id", "revision", "runner_id", "boot_scope")}


def assumed_clock_model(record, binding):
    """Exact arithmetic for assumed upper bounds, NOT a chrony parser/verifier."""
    def no(reason, **facts):
        return {"decision": "NO_GO", "reason": reason, **facts}

    expected = set(FIXTURE["clock_estimate"])
    if type(record) is not dict or set(record) != expected:
        return no("SCHEMA_INVALID")
    if record["record_kind"] != "SYNTHETIC_LOCAL_ESTIMATE":
        return no("PROVENANCE_UNVERIFIED")
    if any(type(record[k]) is not str or record[k] != value for k, value in binding.items()):
        return no("BINDING_MISMATCH")
    for key in ("service_active", "synchronized", "leap_normal"):
        if type(record[key]) is not bool or not record[key]:
            return no("SYNC_UNVERIFIED")
    names = ("captured_mono_ns", "observed_mono_ns", "lease_end_mono_ns", "offset_ns",
             "root_delay_ns", "root_dispersion_ns", "sampling_ns", "holdover_ns", "drift_ppb")
    if any(type(record[k]) is not int or abs(record[k]) > 10 ** 18 for k in names):
        return no("VALUE_INVALID")
    if any(record[k] < 0 for k in names if k != "offset_ns"):
        return no("VALUE_INVALID")
    captured, observed, expiry = (record[k] for k in names[:3])
    if not captured <= observed <= expiry or expiry < captured:
        return no("STALE_OR_REVERSED")
    age = observed - captured
    # Chrony-style conditional distance, plus an explicitly assumed conservative
    # sampling/holdover contribution. Native daemon estimates are not guarantees.
    bound = (abs(record["offset_ns"]) + Fraction(record["root_delay_ns"], 2)
             + record["root_dispersion_ns"] + record["sampling_ns"]
             + Fraction((record["holdover_ns"] + age) * record["drift_ppb"], NS))
    rounded_up = -(-bound.numerator // bound.denominator)
    return no("LOCAL_ESTIMATE_NOT_ATTESTATION", modeled_bound_ns=rounded_up,
              model_within_existing_2s=(bound <= 2 * NS), status_age_ns=age)


def model_cutoff(local_utc_ns, assumed_error_ns, lag_hours=0):
    """Illustrative conservative coordinate, not a runtime policy change."""
    if (type(local_utc_ns) is not int or type(assumed_error_ns) is not int
            or type(lag_hours) is not int or assumed_error_ns < 0 or not 0 <= lag_hours <= 24):
        raise ValueError("BOUND_UNVERIFIED")
    return ((local_utc_ns - assumed_error_ns) // (3600 * NS) - lag_hours) * 3600


FACT_FIELDS = {"kind", "python_version", "openssl_version", "os_id", "os_version", "kernel_release",
               "machine", "image_os", "image_version", "start_method", "ca_bundle_sha256"}


def fact_projection(record, *, ca_hash_approved=False):
    if type(record) is not dict or set(record) != FACT_FIELDS or record["kind"] != "SYNTHETIC":
        raise ValueError("FACT_SCHEMA_INVALID")
    for key in FACT_FIELDS - {"ca_bundle_sha256"}:
        value = record[key]
        if type(value) is not str or not 1 <= len(value) <= 128 or any(not 32 <= ord(c) <= 126 for c in value):
            raise ValueError("FACT_VALUE_INVALID")
    digest = record["ca_bundle_sha256"]
    if digest is not None:
        if not ca_hash_approved:
            raise ValueError("CA_HASH_NOT_APPROVED")
        if type(digest) is not str or len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest):
            raise ValueError("CA_HASH_INVALID")
    return {"decision": "HOLD", "evidence_class": "SYNTHETIC_FACTS", "facts": dict(record)}


def worker_summary(samples):
    if type(samples) is not list or not 1 <= len(samples) <= 30:
        raise ValueError("SAMPLE_LIMIT")
    maxima, counts, failures = {}, {}, 0
    for sample in samples:
        if type(sample) is not dict or set(sample) != {"phase", "elapsed_ns", "outcome"}:
            raise ValueError("SAMPLE_SCHEMA_INVALID")
        phase, elapsed, outcome = (sample[k] for k in ("phase", "elapsed_ns", "outcome"))
        if (type(phase) is not str or phase not in ("start", "terminate", "reap")
                or type(elapsed) is not int or not 0 <= elapsed <= 60 * NS
                or type(outcome) is not str or outcome not in ("OK", "TIMEOUT", "UNREAPED")):
            raise ValueError("SAMPLE_VALUE_INVALID")
        counts[phase] = counts.get(phase, 0) + 1
        if counts[phase] > 10:
            raise ValueError("PHASE_SAMPLE_LIMIT")
        maxima[phase] = max(maxima.get(phase, 0), elapsed)
        failures += outcome != "OK"
    return {"decision": "HOLD", "evidence_class": "SYNTHETIC_OBSERVATIONS_ONLY",
            "observed_max_ns": maxima, "sample_count": len(samples), "failures": failures,
            "all_phases_present": set(maxima) == {"start", "terminate", "reap"},
            "hard_deadline_proven": False}


class ClockRunnerFeasibilityTests(unittest.TestCase):
    def setUp(self):
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        self.blocks = [self.stack.enter_context(patch.object(obj, name,
                       side_effect=AssertionError("NETWORK_OR_QUERY_FORBIDDEN")))
                       for obj, name in ((socket, "socket"), (socket, "create_connection"),
                                         (socket, "getaddrinfo"), (urllib.request, "urlopen"),
                                         (http.client, "HTTPSConnection"),
                                         (subprocess, "run"), (subprocess, "Popen"))]

    def tearDown(self):
        for block in self.blocks:
            block.assert_not_called()

    def evidence(self):
        return copy.deepcopy(FIXTURE["clock_estimate"])

    def test_small_conditional_estimate_is_not_clock_attestation(self):
        result = assumed_clock_model(self.evidence(), BINDING)
        self.assertEqual(result["modeled_bound_ns"], 151100000)
        self.assertTrue(result["model_within_existing_2s"])
        self.assertEqual(result["decision"], "NO_GO")
        self.assertEqual(result["reason"], "LOCAL_ESTIMATE_NOT_ATTESTATION")

    def test_missing_evidence_fields_are_no_go(self):
        for key in self.evidence():
            record = self.evidence()
            del record[key]
            self.assertEqual(assumed_clock_model(record, BINDING)["decision"], "NO_GO")
        self.assertEqual(assumed_clock_model(None, BINDING)["decision"], "NO_GO")

    def test_false_sync_active_and_leap_claims_are_no_go(self):
        for key in ("service_active", "synchronized", "leap_normal"):
            for value in (False, None, "yes", 1):
                record = self.evidence()
                record[key] = value
                self.assertEqual(assumed_clock_model(record, BINDING)["reason"], "SYNC_UNVERIFIED")

    def test_expired_or_reversed_monotonic_evidence_is_no_go(self):
        for key, value in (("observed_mono_ns", 161 * NS), ("observed_mono_ns", 99 * NS),
                           ("lease_end_mono_ns", 99 * NS)):
            record = self.evidence()
            record[key] = value
            self.assertEqual(assumed_clock_model(record, BINDING)["reason"], "STALE_OR_REVERSED")

    def test_run_revision_runner_and_boot_binding_mismatch_refuses(self):
        for key in BINDING:
            record = self.evidence()
            record[key] = "different"
            self.assertEqual(assumed_clock_model(record, BINDING)["reason"], "BINDING_MISMATCH")

    def test_caller_trusted_or_attested_boolean_cannot_create_go(self):
        for key in ("trusted", "attestation_verified", "owner_approved"):
            record = self.evidence()
            record[key] = True
            self.assertEqual(assumed_clock_model(record, BINDING)["reason"], "SCHEMA_INVALID")
        record = self.evidence()
        record["record_kind"] = "SIGNED_BY_SELF"
        self.assertEqual(assumed_clock_model(record, BINDING)["decision"], "NO_GO")

    def test_nonfinite_strings_boolean_units_and_negative_estimates_refuse(self):
        for key in ("root_delay_ns", "root_dispersion_ns", "sampling_ns", "holdover_ns", "drift_ppb"):
            for value in (True, "0.1", float("nan"), float("inf"), -1):
                record = self.evidence()
                record[key] = value
                self.assertEqual(assumed_clock_model(record, BINDING)["reason"], "VALUE_INVALID")

    def test_exact_two_second_model_boundary_and_one_ns_over(self):
        record = self.evidence()
        for key in ("root_delay_ns", "root_dispersion_ns", "sampling_ns", "holdover_ns", "drift_ppb"):
            record[key] = 0
        record["offset_ns"] = 2 * NS
        self.assertTrue(assumed_clock_model(record, BINDING)["model_within_existing_2s"])
        record["offset_ns"] += 1
        self.assertFalse(assumed_clock_model(record, BINDING)["model_within_existing_2s"])
        self.assertEqual(assumed_clock_model(record, BINDING)["decision"], "NO_GO")

    def test_holdover_age_and_fractional_error_are_never_rounded_down(self):
        record = self.evidence()
        before = assumed_clock_model(record, BINDING)["modeled_bound_ns"]
        record["holdover_ns"] += 10 * NS
        self.assertEqual(assumed_clock_model(record, BINDING)["modeled_bound_ns"] - before, 1000000)
        record = self.evidence()
        record.update(offset_ns=0, root_delay_ns=1, root_dispersion_ns=0, sampling_ns=0,
                      holdover_ns=0, drift_ppb=0)
        self.assertEqual(assumed_clock_model(record, BINDING)["modeled_bound_ns"], 1)

    def test_wall_reference_time_does_not_replace_monotonic_freshness(self):
        record = self.evidence()
        del record["captured_mono_ns"]
        record["reference_utc"] = "2030-03-17T17:00:00Z"
        self.assertEqual(assumed_clock_model(record, BINDING)["reason"], "SCHEMA_INVALID")

    def test_native_samples_are_not_silently_promoted_to_upper_bounds(self):
        self.assertIn("Root distance: 33ms (max: 5s)", FIXTURE["mock_timesync_selected_fields"])
        self.assertIn("Last offset", FIXTURE["mock_chrony_selected_fields"])
        record = self.evidence()
        record["RootDistanceMaxUSec"] = 5000000
        self.assertEqual(assumed_clock_model(record, BINDING)["reason"], "SCHEMA_INVALID")

    def test_fact_allowlist_rejects_unknown_secret_fields_without_echo(self):
        record = copy.deepcopy(FIXTURE["runner_facts"])
        record["GITHUB_TOKEN"] = "PRIVATE_SECRET"
        with self.assertRaises(ValueError) as error:
            fact_projection(record)
        self.assertEqual(str(error.exception), "FACT_SCHEMA_INVALID")
        self.assertNotIn("PRIVATE_SECRET", str(error.exception))

    def test_fact_values_are_bounded_and_control_characters_refused(self):
        for value in ("x" * 129, "line\nsecond", "", True):
            record = copy.deepcopy(FIXTURE["runner_facts"])
            record["image_version"] = value
            with self.assertRaises(ValueError):
                fact_projection(record)
        summary = fact_projection(copy.deepcopy(FIXTURE["runner_facts"]))
        self.assertEqual(summary["decision"], "HOLD")
        self.assertLess(len(json.dumps(summary)), 4096)

    def test_ca_hash_needs_separate_approval_and_reads_no_file(self):
        record = copy.deepcopy(FIXTURE["runner_facts"])
        record["ca_bundle_sha256"] = "a" * 64
        with self.assertRaises(ValueError):
            fact_projection(record)
        self.assertEqual(fact_projection(record, ca_hash_approved=True)["decision"], "HOLD")
        record["ca_bundle_sha256"] = "not a hash"
        with self.assertRaises(ValueError):
            fact_projection(record, ca_hash_approved=True)

    def test_synthetic_observed_maxima_do_not_prove_universal_deadlines(self):
        summary = worker_summary(copy.deepcopy(FIXTURE["worker_observations"]))
        self.assertEqual(summary["observed_max_ns"], {"start": 8000000, "terminate": 3000000, "reap": 4000000})
        self.assertEqual(summary["sample_count"], 7)
        self.assertTrue(summary["all_phases_present"])
        self.assertFalse(summary["hard_deadline_proven"])
        self.assertEqual(summary["decision"], "HOLD")

    def test_failed_missing_or_excessive_worker_samples_never_clear_hold(self):
        samples = copy.deepcopy(FIXTURE["worker_observations"])
        samples[-1]["outcome"] = "UNREAPED"
        self.assertEqual(worker_summary(samples)["failures"], 1)
        self.assertFalse(worker_summary(samples[:2])["all_phases_present"])
        for value in ([], samples * 5, [{"phase": "start", "elapsed_ns": 1, "outcome": "OK"}] * 11):
            with self.assertRaises(ValueError):
                worker_summary(value)

    def test_worker_measurement_types_and_unknown_phases_refuse(self):
        for key, value in (("phase", "DNS"), ("elapsed_ns", True), ("elapsed_ns", -1),
                           ("elapsed_ns", 61 * NS), ("outcome", "PRIVATE_SECRET")):
            samples = copy.deepcopy(FIXTURE["worker_observations"])
            samples[0][key] = value
            with self.assertRaises(ValueError) as error:
                worker_summary(samples)
            self.assertNotIn("PRIVATE_SECRET", str(error.exception))

    def test_existing_two_second_guard_is_conservative_under_assumed_bound(self):
        hour = 1899997200
        for true_delta_ns in (-NS, -1, 0, 1, NS, 2 * NS, 3599 * NS):
            true_utc_ns = hour * NS + true_delta_ns
            for error_ns in range(-2 * NS, 2 * NS + 1, 100000000):
                cutoff = model_cutoff(true_utc_ns + error_ns, 2 * NS)
                self.assertLessEqual(cutoff * NS, true_utc_ns)

    def test_proposed_data_only_lag_is_conditional_not_an_active_policy(self):
        true_utc_ns = 1899997200 * NS - 1
        for error_ns in (-60 * NS, 0, 60 * NS):
            cutoff = model_cutoff(true_utc_ns + error_ns, 60 * NS, lag_hours=1)
            self.assertLessEqual(cutoff * NS + 3600 * NS, true_utc_ns)
        self.assertEqual(diagnostic.CAPTURE_POLICY, "manual-capture-v1")
        self.assertEqual(diagnostic.DEADLINE_NS, 10 * NS)
        self.assertEqual(corrections.HEADER_LIMIT, 8192)
        self.assertEqual(corrections.BODY_LIMIT, 262144)

    def test_no_finite_guard_repairs_an_unbounded_clock_error(self):
        true_utc_ns = 1899997200 * NS
        for guard_ns in (2 * NS, 60 * NS, 3600 * NS):
            cutoff = model_cutoff(true_utc_ns + 24 * 3600 * NS, guard_ns, lag_hours=1)
            self.assertGreater(cutoff * NS, true_utc_ns)
        with self.assertRaises(ValueError):
            model_cutoff(true_utc_ns, None)

    def test_historical_declared_asof_is_a_coordinate_not_current_time(self):
        fixture = json.loads((ROOT / "spot_refusal_v1.json").read_text())
        result = registry.validate_symbol("BTC/USD", fixture["payload"], as_of=fixture["as_of"])
        self.assertEqual(result["status"], "VALIDATED_DATA")
        self.assertIn("Synthetic", result["detail"])
        self.assertEqual(result["as_of_utc"], "2030-03-17T17:00:00Z")

    def test_both_existing_clis_remain_authorization_missing_and_zero_requests(self):
        for module in (diagnostic, corrections):
            with redirect_stdout(io.StringIO()) as output:
                self.assertEqual(module.main(), 2)
            result = json.loads(output.getvalue())
            self.assertEqual(result["reason"], "AUTHORIZATION_MISSING")
            self.assertEqual(result["requests"], 0)


if __name__ == "__main__":
    unittest.main()
