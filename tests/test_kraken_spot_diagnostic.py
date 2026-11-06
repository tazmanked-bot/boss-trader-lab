"""Offline-only diagnostic tests, including real child cleanup with blocked fakes."""

from contextlib import ExitStack, redirect_stdout
import copy
from datetime import datetime, timezone
from email.utils import format_datetime
import http.client
import importlib
import io
import json
import multiprocessing
from pathlib import Path
import socket
import ssl
import sys
import unittest
from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit
import urllib.request

from research import kraken_spot_diagnostic as diagnostic
from research import spot_refusal_registry as registry


FIXTURES = Path(__file__).parent / "fixtures"
OHLC = json.loads((FIXTURES / "kraken_spot_bridge_v1.json").read_text())
IDENTITY = json.loads((FIXTURES / "kraken_diagnostic_identity_v1.json").read_text())["identities"]
T = OHLC["as_of"]
REVISION = "0" * 40  # Explicit synthetic revision claim, never a real checkout assertion.
NS = 1_000_000_000


class FakeClock:
    trusted = True

    def __init__(self, start=T + 3):
        self.base = start * NS
        self.ticks = 0
        self.wall_offset = 0
        self.mono_offset = 0

    def monotonic_ns(self):
        return self.ticks + self.mono_offset

    def sample(self):
        return diagnostic.Stamp(self.base + self.ticks + self.wall_offset, self.monotonic_ns())


class FakeResponse:
    def __init__(self, spec):
        self.spec = spec
        self.status = spec.get("status", 200)
        self.read_sizes = []

    def getheaders(self):
        return self.spec["headers"]

    def read(self, size):
        self.read_sizes.append(size)
        if "read_error" in self.spec:
            raise self.spec["read_error"]
        return self.spec["body"][:size]


class FakeConnection:
    def __init__(self, factory):
        self.factory = factory
        self.closed = False

    def request(self, method, target, body, headers):
        if self.factory.request_error:
            raise self.factory.request_error
        self.factory.sent.append((method, target, body, headers))
        parsed = urlsplit(target)
        self.path = parsed.path
        pair = parse_qs(parsed.query)["pair"][0]
        self.symbol = {"XBTUSD": "BTC/USD", "XRPUSD": "XRP/USD", "SOLUSD": "SOL/USD"}[pair]

    def getresponse(self):
        spec = self.factory.response(self.symbol, self.path)
        response = FakeResponse(spec)
        self.factory.responses.append(response)
        return response

    def close(self):
        self.closed = True


class FakeFactory:
    def __init__(self, clock):
        self.clock = clock
        self.identities = copy.deepcopy(IDENTITY)
        self.ohlc = {s: copy.deepcopy(v["response"]) for s, v in OHLC["captures"].items()}
        self.overrides = {}
        self.sent = []
        self.constructed = []
        self.connections = []
        self.responses = []
        self.request_error = None
        self.delays = {}
        self.after_result = None
        self.reap_ok = True

    def __call__(self, host, *, port, context, timeout):
        assert host == "api.kraken.com" and port == 443 and timeout == 10
        assert context.verify_mode == ssl.CERT_REQUIRED and context.check_hostname
        self.constructed.append(host)
        obj = FakeConnection(self)
        self.connections.append(obj)
        return obj

    def response(self, symbol, path):
        payload = self.identities[symbol] if path.endswith("AssetPairs") else self.ohlc[symbol]
        date = format_datetime(datetime.fromtimestamp(self.clock.sample().utc_ns // NS, timezone.utc), usegmt=True)
        return {"body": registry.canonical_json(payload).encode("utf-8"),
                "headers": [("Content-Type", "application/json; charset=utf-8"), ("Date", date)],
                **self.overrides.get((symbol, path), {})}


class FakeJob:
    def __init__(self, request, factory):
        self.request = request
        self.factory = factory
        self.start_ns = factory.clock.monotonic_ns()
        self.delay = factory.delays.get((request.symbol, request.path), 0)
        self.killed = self.reaped = False

    def start(self):
        pass

    def alive(self):
        return not self.killed and self.factory.clock.monotonic_ns() - self.start_ns < self.delay

    def wait(self, seconds):
        self.factory.clock.ticks += max(1, int(seconds * NS))

    def kill(self):
        self.killed = True

    def reap(self):
        self.reaped = self.factory.reap_ok
        return self.reaped

    def result(self):
        packet = diagnostic._exchange(self.request, self.factory)
        if self.factory.after_result:
            self.factory.after_result(self.request)
        return packet


def ohlc_rows(factory, symbol="BTC/USD"):
    result = factory.ohlc[symbol]["result"]
    return result[next(k for k in result if k != "last")]


class EventClock(FakeClock):
    """Advance the deterministic parent deadline once the child reaches a phase."""
    def __init__(self, event):
        super().__init__()
        self.event = event

    def monotonic_ns(self):
        return 10 * NS if self.event.is_set() else 0

    def sample(self):
        tick = self.monotonic_ns()
        return diagnostic.Stamp(self.base + tick, tick)


class BlockingFactory:
    """All phases block on an OS event, never DNS/socket/HTTP."""
    def __init__(self, phase, entered, blocker):
        self.phase, self.entered, self.blocker = phase, entered, blocker

    def block(self):
        self.entered.set()
        self.blocker.wait()

    def __call__(self, host, **kwargs):
        if self.phase == "DNS":
            self.block()
        return self

    def request(self, *args, **kwargs):
        if self.phase == "CONNECT":
            self.block()

    def getresponse(self):
        self.status = 200
        return self

    def getheaders(self):
        date = format_datetime(datetime.fromtimestamp(T + 3, timezone.utc), usegmt=True)
        return [("Content-Type", "application/json"), ("Date", date)]

    def read(self, size):
        self.block()

    def close(self):
        pass


class DiagnosticTests(unittest.TestCase):
    def setUp(self):
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        for obj, name in ((socket, "socket"), (socket, "create_connection"), (socket, "getaddrinfo"),
                          (urllib.request, "urlopen"), (http.client, "HTTPSConnection")):
            self.stack.enter_context(patch.object(obj, name, side_effect=AssertionError("REAL NETWORK FORBIDDEN")))
        self.clock = FakeClock()
        self.factory = FakeFactory(self.clock)
        self.jobs = []

    def job(self, request, factory):
        job = FakeJob(request, factory)
        self.jobs.append(job)
        return job

    def run_diagnostic(self):
        return diagnostic.run_offline(connection_factory=self.factory, clock=self.clock,
                                      reviewed_revision=REVISION, job_factory=self.job)

    def first_reason(self, output):
        return output["symbols"]["BTC/USD"]["reason"]

    def test_import_and_normal_cli_are_disabled_even_with_live_arguments(self):
        importlib.reload(diagnostic)
        with patch.object(sys, "argv", ["kraken_spot_diagnostic", "--live", "--authorize"]):
            out = io.StringIO()
            with redirect_stdout(out):
                self.assertEqual(diagnostic.main(), 2)
            result = json.loads(out.getvalue())
            self.assertEqual(result["reason"], "AUTHORIZATION_MISSING")
            self.assertEqual(result["requests"], 0)
        self.assertEqual(diagnostic.run_offline()["reason"], "AUTHORIZATION_MISSING")
        self.assertEqual(self.factory.sent, [])

    def test_all_three_metadata_matches_have_six_fixed_requests_but_overall_hold(self):
        output = self.run_diagnostic()
        self.assertEqual(output["overall"], "HOLD")
        self.assertEqual(output["data_checks"], "ALL_PASSED")
        self.assertEqual(output["requests"], 6)
        self.assertEqual(output["as_of_utc_seconds"], T)
        for symbol, result in output["symbols"].items():
            self.assertEqual(result["reason"], "DATA_CHECKS_PASSED")
            self.assertTrue(result["identity_consistent"])
            self.assertEqual(result["clock_status"], "CONSISTENT")
            self.assertEqual(result["bridge"]["decision"]["status"], "VALIDATED_DATA")
            self.assertEqual(len(result["receipts"]), 2)
            self.assertLess(len(registry.canonical_json(result)), 4096)
        self.assertLess(len(registry.canonical_json(output)), 16384)
        self.assertRegex(output["implementation_sha256"], r"^[0-9a-f]{64}$")
        for method, target, body, headers in self.factory.sent:
            self.assertEqual(method, "GET")
            self.assertIsNone(body)
            self.assertNotIn("Authorization", headers)
            self.assertNotIn("Cookie", headers)
            query = parse_qs(urlsplit(target).query)
            if target.startswith("/0/public/OHLC?"):
                self.assertEqual(query["interval"], ["60"])
                self.assertEqual(query["since"], [str(T - 86400)])
            self.assertNotIn("assetVersion", query)
        self.assertTrue(all(c.closed for c in self.factory.connections))

    def test_unverified_identity_blocks_ohlc_and_preserves_symbol_isolation(self):
        self.factory.identities["XRP/USD"]["result"] = {"NEW_XRPUSD": {}}
        self.factory.identities["SOL/USD"]["error"] = ["PRIVATE_SECRET source message"]
        result = self.run_diagnostic()
        self.assertEqual(result["data_checks"], "REFUSED")
        self.assertEqual(result["requests"], 4)
        self.assertEqual(result["symbols"]["BTC/USD"]["reason"], "DATA_CHECKS_PASSED")
        self.assertEqual(result["symbols"]["XRP/USD"]["reason"], "ALIAS_CHANGED")
        self.assertEqual(result["symbols"]["SOL/USD"]["reason"], "API_ERROR")
        self.assertNotIn("PRIVATE_SECRET", registry.canonical_json(result))
        self.assertEqual(sum("/OHLC?" in row[1] for row in self.factory.sent), 1)

    def test_zero_valid_symbols_still_no_forced_ohlc(self):
        for payload in self.factory.identities.values():
            payload["result"] = {}
        result = self.run_diagnostic()
        self.assertEqual(result["requests"], 3)
        self.assertTrue(all(r["reason"] == "ALIAS_CHANGED" for r in result["symbols"].values()))

    def test_identity_fields_and_unknown_metadata_never_auto_learn(self):
        mutations = (("quote", "USDT"), ("base", "XRP"), ("aclass_base", "future"),
                     ("aclass_quote", "other"), ("altname", "BTCUSD"), ("wsname", "BTC/USDT"),
                     ("status", "maintenance"), ("new_field", "PRIVATE_SECRET"))
        for field, value in mutations:
            with self.subTest(field=field):
                self.set_factory()
                self.factory.identities["BTC/USD"]["result"]["XXBTZUSD"][field] = value
                self.assertEqual(self.first_reason(self.run_diagnostic()), "IDENTITY_UNVERIFIED")
        self.set_factory()
        record = self.factory.identities["BTC/USD"]["result"].pop("XXBTZUSD")
        self.factory.identities["BTC/USD"]["result"]["XBTUSD"] = record
        self.assertEqual(self.first_reason(self.run_diagnostic()), "ALIAS_CHANGED")

    def set_factory(self, start=T + 3):
        self.clock = FakeClock(start)
        self.factory = FakeFactory(self.clock)
        self.jobs = []

    def test_ohlc_alias_must_equal_verified_instrument_key(self):
        result = self.factory.ohlc["BTC/USD"]["result"]
        result["XBTUSD"] = result.pop("XXBTZUSD")  # R3 alone accepts this alias.
        self.assertEqual(self.first_reason(self.run_diagnostic()), "ALIAS_CHANGED")

    def test_arbitrary_hosts_paths_parameters_and_float_interval_refuse_before_factory(self):
        Request = diagnostic.Request
        invalid = (Request("BTC/USD", "https://evil.invalid/0/public/OHLC", ()),
                   Request("BTC/USD", "/0/private/Balance", ()),
                   Request("ETH/USD", "/0/public/AssetPairs", ()),
                   Request("BTC/USD", "/0/public/AssetPairs", (("pair", "XBTUSD"),)),
                   Request("BTC/USD", "/0/public/OHLC", (("pair", "XBTUSDT"), ("interval", 60), ("since", T))),
                   Request("BTC/USD", "/0/public/OHLC", (("pair", "XBTUSD"), ("interval", 60.0), ("since", T))),
                   Request("BTC/USD", "/0/public/OHLC", (("pair", "XBTUSD"), ("interval", 60), ("since", str(T)))))
        for request in invalid:
            meta, body = diagnostic._exchange(request, self.factory)
            self.assertEqual(meta["reason"], "CONTEXT_INVALID")
            self.assertEqual(body, b"")
        self.assertEqual(self.factory.constructed, [])

    def test_tls_verification_cannot_be_disabled_by_context(self):
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        with patch.object(diagnostic, "_tls_context", return_value=context):
            self.assertEqual(self.first_reason(self.run_diagnostic()), "TLS_FAILURE")
        self.assertEqual(self.factory.constructed, [])
        self.set_factory()
        self.factory.request_error = ssl.SSLError("PRIVATE_SECRET certificate error")
        result = self.run_diagnostic()
        self.assertEqual(self.first_reason(result), "TLS_FAILURE")
        self.assertNotIn("PRIVATE_SECRET", registry.canonical_json(result))

    def test_worker_cannot_report_success_or_unknown_reason_as_a_transport_error(self):
        for reason in ("DATA_CHECKS_PASSED", "PRIVATE_SECRET", "BRIDGE_REFUSED"):
            with patch.object(FakeJob, "result", return_value=({"reason": reason}, b"")):
                result = self.run_diagnostic()
            self.assertEqual(self.first_reason(result), "WORKER_INVALID")
            self.assertEqual(result["data_checks"], "REFUSED")
            self.assertNotIn("PRIVATE_SECRET", registry.canonical_json(result))

    def test_tls_context_has_no_environment_key_logging_hook(self):
        with patch.dict("os.environ", {"SSLKEYLOGFILE": "/nonexistent/offline-no-keylog"}):
            context = diagnostic._tls_context()
        self.assertIsNone(context.keylog_filename)
        self.assertTrue(context.check_hostname)
        self.assertEqual(context.verify_mode, ssl.CERT_REQUIRED)

    def test_redirect_451_and_other_http_errors_never_read_error_body_or_retry(self):
        for status, expected in ((301, "REDIRECT_REFUSED"), (307, "REDIRECT_REFUSED"),
                                 (451, "HTTP_REFUSED"), (429, "HTTP_REFUSED"), (500, "HTTP_REFUSED")):
            self.set_factory()
            self.factory.overrides[("BTC/USD", "/0/public/AssetPairs")] = {"status": status, "body": b"PRIVATE_SECRET"}
            output = self.run_diagnostic()
            self.assertEqual(self.first_reason(output), expected)
            self.assertEqual(self.factory.responses[0].read_sizes, [])
            self.assertEqual(sum("pair=XBTUSD" in r[1] for r in self.factory.sent), 1)
            self.assertNotIn("PRIVATE_SECRET", registry.canonical_json(output))

    def test_payload_limit_plus_one_and_false_content_length(self):
        self.factory.overrides[("BTC/USD", "/0/public/AssetPairs")] = {
            "body": b" " * 262145,
            "headers": [("Date", self.date()), ("Content-Type", "application/json"), ("Content-Length", "1")]}
        self.assertEqual(self.first_reason(self.run_diagnostic()), "RESPONSE_TOO_LARGE")
        self.assertEqual(self.factory.responses[0].read_sizes, [262145])

    def date(self):
        return format_datetime(datetime.fromtimestamp(self.clock.sample().utc_ns // NS, timezone.utc), usegmt=True)

    def test_compression_wrong_content_types_and_duplicate_headers_refuse(self):
        cases = ([('Content-Type', 'text/html'), ('Date', self.date())],
                 [('Content-Type', 'application/json'), ('Date', self.date()), ('Content-Encoding', 'gzip')],
                 [('Content-Type', 'application/json'), ('Date', self.date()), ('Date', self.date())],
                 [('Content-Type', 'application/json'), ('Date', self.date())] + [('X-A', 'a')] * 65)
        for headers in cases:
            self.set_factory()
            self.factory.overrides[("BTC/USD", "/0/public/AssetPairs")] = {"headers": headers, "body": b"PRIVATE_SECRET"}
            self.assertEqual(self.first_reason(self.run_diagnostic()), "CONTENT_INVALID")
            self.assertEqual(self.factory.responses[0].read_sizes, [])

    def test_utf8_json_duplicate_keys_nonfinite_and_malformed_body(self):
        for body in (b"\xff", b'{"error":[],"error":[]}', b"NaN", b"1e999", b"[" * 2000,
                     b'{"PRIVATE_SECRET":', b"Infinity"):
            self.set_factory()
            self.factory.overrides[("BTC/USD", "/0/public/AssetPairs")] = {"body": body}
            output = self.run_diagnostic()
            self.assertEqual(self.first_reason(output), "JSON_INVALID")
            self.assertNotIn("PRIVATE_SECRET", registry.canonical_json(output))

    def test_date_malformed_missing_and_wrong_weekday_stop_all_later_requests(self):
        for value in (None, "bad date", "Sun, 17 Mar 2030 17:00:03 +0000", "Mon, 17 Mar 2030 17:00:03 GMT"):
            self.set_factory()
            headers = [("Content-Type", "application/json")]
            if value is not None:
                headers.append(("Date", value))
            self.factory.overrides[("BTC/USD", "/0/public/AssetPairs")] = {"headers": headers}
            output = self.run_diagnostic()
            self.assertEqual(self.first_reason(output), "CLOCK_UNVERIFIED")
            self.assertEqual(output["requests"], 1)

    def test_service_date_outside_envelope_stops_invocation(self):
        for seconds in (T, T + 6):  # start=T+3, interval [T+1,T+5].
            self.set_factory()
            date = format_datetime(datetime.fromtimestamp(seconds, timezone.utc), usegmt=True)
            self.factory.overrides[("BTC/USD", "/0/public/AssetPairs")] = {
                "headers": [("Content-Type", "application/json"), ("Date", date)]}
            output = self.run_diagnostic()
            self.assertEqual(self.first_reason(output), "SERVICE_TIME_CONFLICT")
            self.assertEqual(output["requests"], 1)

    def test_clock_guard_boundaries_and_no_forward_cutoff_on_crossing(self):
        for offset, expected in ((-1, T - 3600), (0, T - 3600), (1, T - 3600), (2, T)):
            self.set_factory(T + offset)
            self.factory.delays[("BTC/USD", "/0/public/AssetPairs")] = 2 * NS
            output = self.run_diagnostic()
            self.assertEqual(output["as_of_utc_seconds"], expected)
            if offset < 2:
                self.assertEqual(self.first_reason(output), "BRIDGE_REFUSED")
                self.assertEqual(output["symbols"]["BTC/USD"]["bridge"]["decision"]["reason_code"], "WARMUP_INCOMPLETE")

    def test_clock_untrusted_invalid_revision_and_exceptions_make_zero_jobs(self):
        self.clock.trusted = False
        self.assertEqual(self.run_diagnostic()["reason"], "CLOCK_UNVERIFIED")
        self.assertEqual(self.jobs, [])
        self.assertEqual(diagnostic.run_offline(connection_factory=self.factory, clock=self.clock,
                         reviewed_revision="main", job_factory=self.job)["reason"], "CONTEXT_INVALID")
        self.set_factory()
        self.clock.sample = lambda: (_ for _ in ()).throw(ValueError("PRIVATE_SECRET"))
        self.assertEqual(self.run_diagnostic()["reason"], "CLOCK_UNVERIFIED")
        self.assertEqual(self.jobs, [])

    def test_backward_wall_and_monotonic_jumps_stop_before_ohlc(self):
        for field in ("wall_offset", "mono_offset"):
            self.set_factory()
            self.factory.after_result = lambda _, f=field: setattr(self.clock, f, -1)
            output = self.run_diagnostic()
            self.assertEqual(self.first_reason(output), "CLOCK_CONFLICT")
            self.assertEqual(output["requests"], 1)

    def test_cumulative_drift_checks_initial_pair_not_only_previous_request(self):
        self.factory.after_result = lambda _: setattr(self.clock, "wall_offset", self.clock.wall_offset + 600_000_000)
        output = self.run_diagnostic()
        self.assertEqual(output["requests"], 2)
        self.assertEqual(self.first_reason(output), "CLOCK_CONFLICT")

    def test_deadline_kills_reaps_worker_still_running_at_ten_seconds(self):
        self.factory.delays[("BTC/USD", "/0/public/AssetPairs")] = 11 * NS
        result = self.run_diagnostic()
        self.assertEqual(self.first_reason(result), "TIMEOUT")
        self.assertTrue(self.jobs[0].killed)
        self.assertTrue(self.jobs[0].reaped)
        self.assertFalse(any("pair=XBTUSD" in r[1] for r in self.factory.sent))

    def test_completion_exactly_at_deadline_is_discarded_without_reading_packet(self):
        self.factory.delays[("BTC/USD", "/0/public/AssetPairs")] = 10 * NS
        result = self.run_diagnostic()
        self.assertEqual(self.first_reason(result), "TIMEOUT")
        self.assertTrue(self.jobs[0].reaped)
        self.assertFalse(any("pair=XBTUSD" in r[1] for r in self.factory.sent))

    def test_under_deadline_completes_and_socket_timeout_is_fixed_category(self):
        self.factory.delays[("BTC/USD", "/0/public/AssetPairs")] = 9 * NS
        self.assertEqual(self.first_reason(self.run_diagnostic()), "DATA_CHECKS_PASSED")
        self.set_factory()
        self.factory.request_error = TimeoutError("PRIVATE_SECRET")
        output = self.run_diagnostic()
        self.assertEqual(self.first_reason(output), "TIMEOUT")
        self.assertNotIn("PRIVATE_SECRET", registry.canonical_json(output))

    def test_unreaped_worker_stops_any_further_requests(self):
        self.factory.reap_ok = False
        output = self.run_diagnostic()
        self.assertEqual(self.first_reason(output), "WORKER_UNREAPED")
        self.assertEqual(output["requests"], 1)
        self.assertEqual(len(self.jobs), 1)

    @unittest.skipUnless("fork" in multiprocessing.get_all_start_methods(), "POSIX fork mechanism only")
    def test_real_os_workers_in_blocked_fake_dns_connect_read_are_killed_and_reaped(self):
        for phase in ("DNS", "CONNECT", "READ"):
            context = multiprocessing.get_context("fork")
            entered, blocker = context.Event(), context.Event()
            clock = EventClock(entered)
            jobs = []

            def job_factory(request, factory):
                job = diagnostic.ProcessJob(request, factory)
                jobs.append(job)
                return job

            request = diagnostic.Request("BTC/USD", "/0/public/AssetPairs",
                                         (("pair", "XBTUSD"), ("aclass_base", "currency"), ("info", "info")))
            with self.assertRaises(diagnostic.Refused) as error:
                diagnostic._supervise(request, BlockingFactory(phase, entered, blocker), clock, job_factory)
            self.assertEqual(error.exception.reason, diagnostic.Reason.TIMEOUT)
            self.assertTrue(entered.is_set())
            self.assertTrue(jobs[0].reaped)

    @unittest.skipUnless("fork" in multiprocessing.get_all_start_methods(), "POSIX fork mechanism only")
    def test_real_os_successful_fake_worker_packet_is_bounded_and_reaped(self):
        request = diagnostic.Request("BTC/USD", "/0/public/AssetPairs",
                                     (("pair", "XBTUSD"), ("aclass_base", "currency"), ("info", "info")))
        jobs = []

        def make(request, factory):
            job = diagnostic.ProcessJob(request, factory)
            jobs.append(job)
            return job

        meta, body = diagnostic._supervise(request, self.factory, self.clock, make)
        self.assertIsNone(meta["reason"])
        self.assertEqual(json.loads(body), IDENTITY["BTC/USD"])
        self.assertLessEqual(len(body), 262144)
        self.assertTrue(jobs[0].reaped)

    def test_platform_without_single_thread_fork_is_fail_closed(self):
        with patch.object(diagnostic.threading, "active_count", return_value=2):
            output = diagnostic.run_offline(connection_factory=self.factory, clock=self.clock,
                                            reviewed_revision=REVISION)
        self.assertEqual(self.first_reason(output), "PLATFORM_UNSUPPORTED")
        self.assertEqual(output["requests"], 1)
        self.assertEqual(self.factory.sent, [])

    def test_commitment_old_uncommitted_and_beyond_capture_future_headers_refuse(self):
        for last in (T - 3600, T + 3600):
            self.set_factory()
            ohlc_rows(self.factory)[-1][0] = last
            self.assertEqual(self.first_reason(self.run_diagnostic()), "COMMITMENT_CONFLICT")
        for bad in (True, str(T), T * 1000, T + 1):
            self.set_factory()
            ohlc_rows(self.factory)[-1][0] = bad
            self.assertEqual(self.first_reason(self.run_diagnostic()), "COMMITMENT_CONFLICT")

    def test_eligible_gap_duplicate_invalid_price_and_stale_fail_whole_symbol(self):
        for kind in ("gap", "duplicate", "invalid", "stale"):
            self.set_factory()
            rows = ohlc_rows(self.factory)
            if kind == "gap":
                rows.pop(10)
            elif kind == "duplicate":
                rows.insert(1, copy.deepcopy(rows[0]))
            elif kind == "invalid":
                rows[10][4] = "NaN"
            else:
                for row in rows[:-1]:
                    row[0] -= 4 * 3600
            result = self.run_diagnostic()
            self.assertNotEqual(self.first_reason(result), "DATA_CHECKS_PASSED")
            self.assertEqual(result["data_checks"], "REFUSED")

    def test_entire_summary_equal_when_excluded_current_prices_change(self):
        reference = registry.canonical_json(self.run_diagnostic())
        for value in ("NaN", "-1", "1e999", "PRIVATE_SECRET", "0"):
            self.set_factory()
            for symbol in self.factory.ohlc:
                row = ohlc_rows(self.factory, symbol)[-1]
                row[1:] = [value] * 7
            actual = registry.canonical_json(self.run_diagnostic())
            self.assertEqual(actual, reference)
            self.assertNotIn("PRIVATE_SECRET", actual)

    def test_future_append_invariant_within_captured_time_and_projection_contract(self):
        self.set_factory(T + 1)  # Frozen cutoff is T-3600; transport upper hour is T.
        for symbol in self.factory.ohlc:
            for row in ohlc_rows(self.factory, symbol):
                row[0] -= 3600
        reference = registry.canonical_json(self.run_diagnostic())
        for symbol in self.factory.ohlc:
            ohlc_rows(self.factory, symbol).append([T] + ["PRIVATE_SECRET"] * 7)
        self.assertEqual(registry.canonical_json(self.run_diagnostic()), reference)

    def test_refused_summary_also_invariant_to_excluded_future_values(self):
        ohlc_rows(self.factory)[10][4] = "0"
        reference = registry.canonical_json(self.run_diagnostic())
        ohlc_rows(self.factory)[-1][1:] = ["PRIVATE_SECRET"] * 7
        self.assertEqual(registry.canonical_json(self.run_diagnostic()), reference)
        self.assertEqual(self.first_reason(self.run_diagnostic()), "BRIDGE_REFUSED")

    def test_summary_hashes_cover_safe_context_without_raw_capture_hashes(self):
        result = self.run_diagnostic()
        digest = result.pop("diagnostic_hash")
        import hashlib
        self.assertEqual(digest, hashlib.sha256(registry.canonical_json(result).encode("ascii")).hexdigest())
        text = registry.canonical_json(result)
        for forbidden in ("last_closed_price", "volume", "vwap", "raw_response", "excluded_count", "Authorization"):
            self.assertNotIn('"' + forbidden + '"', text)
        self.assertEqual(result["reviewed_revision_claim"], REVISION)


if __name__ == "__main__":
    unittest.main()
