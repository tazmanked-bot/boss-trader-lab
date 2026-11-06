"""Offline B1-B3 regressions and unsafe-design sensitivity checks."""

from contextlib import ExitStack, redirect_stdout
from datetime import datetime, timezone
from email.utils import format_datetime
import io
import importlib
import multiprocessing
import socket
import unittest
from unittest.mock import patch
import urllib.request

from research import kraken_probe_corrections as corrected
from research import kraken_spot_diagnostic as legacy


NS = 1_000_000_000
T = 1899997200
DATE = format_datetime(datetime.fromtimestamp(T, timezone.utc), usegmt=True)
REQUEST = legacy.Request("BTC/USD", "/0/public/AssetPairs",
                         (("pair", "XBTUSD"), ("aclass_base", "currency"), ("info", "info")))


class Clock:
    def __init__(self, value=0):
        self.value = value

    def monotonic_ns(self):
        return self.value


class FakeJob:
    def __init__(self, request, action, clock, deadline):
        self.request, self.action, self.clock, self.deadline = request, action, clock, deadline
        self.started = self.released = self.killed = self.reaped = self.closed = False
        self.done, self.code = False, corrected.Code.COMPLETED
        self.start_delay = self.release_delay = self.result_delay = 0
        self.never_ready = False
        self.reap_ok = True

    def start(self):
        self.started = True
        self.clock.value += self.start_delay

    def alive(self):
        return self.started and not self.done and not self.killed

    def ready(self):
        return not self.never_ready

    def release(self):
        self.released = True
        self.clock.value += self.release_delay
        try:
            corrected._active(self.clock, self.deadline)
            self.action(self.request)
        except corrected.Refused as exc:
            self.code = exc.code
        self.done = True

    def result(self):
        self.clock.value += self.result_delay
        return self.code

    def wait(self, seconds):
        self.clock.value += max(1, int(seconds * NS))

    def cancel(self):
        pass

    def kill(self):
        self.killed = True

    def reap(self):
        self.reaped = self.reap_ok
        return self.reaped

    def close_unstarted(self):
        self.closed = True


class SharedClock:
    shared_for_fork = True

    def __init__(self, drive_event=None):
        self.value = multiprocessing.get_context("fork").RawValue("q", 0)
        self.drive_event = drive_event

    def monotonic_ns(self):
        if self.drive_event is not None and self.drive_event.is_set():
            self.value.value = 10 * NS
        return self.value.value


class Block:
    def __init__(self, entered, blocker):
        self.entered, self.blocker = entered, blocker

    def __call__(self, *args):
        self.entered.set()
        self.blocker.wait()  # Local Event only, no network or wall-clock sleep.


def wire(body=b'{"error":[],"result":{}}', *, extras=(), length=True, status=200):
    headers = [("Content-Type", "application/json"), ("Date", DATE)]
    if length:
        headers.append(("Content-Length", str(len(body))))
    headers.extend(extras)
    return (f"HTTP/1.1 {status} Synthetic\r\n".encode("ascii")
            + b"".join(f"{k}: {v}\r\n".encode("ascii") for k, v in headers)
            + b"\r\n" + body)


class CorrectionTests(unittest.TestCase):
    def setUp(self):
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        self.blocks = [self.stack.enter_context(patch.object(obj, name,
                       side_effect=AssertionError("REAL NETWORK FORBIDDEN")))
                       for obj, name in ((socket, "socket"), (socket, "create_connection"),
                                         (socket, "getaddrinfo"), (urllib.request, "urlopen"))]
        self.clock, self.calls, self.jobs = Clock(), [], []

    def tearDown(self):
        for block in self.blocks:
            block.assert_not_called()

    def action(self, request):
        self.calls.append(request.target())

    def job(self, request, action, clock, deadline):
        job = FakeJob(request, action, clock, deadline)
        self.jobs.append(job)
        return job

    def run_supervisor(self, factory=None, deadline=None):
        return corrected.supervise_offline(request=REQUEST, action=self.action, clock=self.clock,
                    job_factory=self.job if factory is None else factory, deadline_ns=deadline)

    def assert_expired_launch_blocked(self, result):
        self.assertEqual(result["reason"], "TIMEOUT")
        self.assertFalse(result["started"])
        self.assertFalse(result["released"])
        self.assertEqual(self.calls, [])

    def test_expired_before_factory_has_no_job_or_operation(self):
        self.assert_expired_launch_blocked(self.run_supervisor(deadline=0))
        self.assertEqual(self.jobs, [])

    def test_slow_factory_cannot_launch_after_expiry_pr21_b1(self):
        def slow(*args):
            self.clock.value += 11 * NS
            return self.job(*args)

        self.assert_expired_launch_blocked(self.run_supervisor(slow))
        self.assertFalse(self.jobs[0].started)
        self.assertTrue(self.jobs[0].closed)

    def test_b1_contract_rejects_intentionally_disabled_deadline_guards(self):
        def slow(*args):
            self.clock.value += 11 * NS
            return self.job(*args)

        with patch.object(corrected, "_active", side_effect=lambda clock, *a, **k: clock.monotonic_ns()):
            unsafe = self.run_supervisor(slow)
        with self.assertRaises(AssertionError):
            self.assert_expired_launch_blocked(unsafe)
        self.assertTrue(self.calls)  # The same contract assertion detects unsafe action entry.

    def test_slow_start_stays_paused_and_is_killed_without_release(self):
        def slow(*args):
            job = self.job(*args)
            job.start_delay = 11 * NS
            return job

        result = self.run_supervisor(slow)
        self.assertEqual(result["reason"], "TIMEOUT")
        self.assertTrue(result["started"])
        self.assertFalse(result["released"])
        self.assertTrue(self.jobs[0].killed and self.jobs[0].reaped)
        self.assertEqual(self.calls, [])

    def test_child_rechecks_expiry_after_parent_release_race(self):
        def race(*args):
            job = self.job(*args)
            job.release_delay = 10 * NS
            return job

        result = self.run_supervisor(race)
        self.assertEqual(result["reason"], "TIMEOUT")
        self.assertEqual(self.calls, [])
        self.assertTrue(self.jobs[0].reaped)

    def test_timeout_at_exact_edge_and_late_result_are_not_completed(self):
        for elapsed, expected in ((9 * NS, "COMPLETED"), (10 * NS, "TIMEOUT"), (11 * NS, "TIMEOUT")):
            self.clock = Clock()

            def delayed(*args):
                job = self.job(*args)
                job.result_delay = elapsed
                return job

            self.assertEqual(self.run_supervisor(delayed)["reason"], expected)

    def test_never_ready_bootstrap_times_out_with_zero_release(self):
        def never(*args):
            job = self.job(*args)
            job.never_ready = True
            return job

        result = self.run_supervisor(never)
        self.assertEqual(result["reason"], "TIMEOUT")
        self.assertFalse(result["released"])
        self.assertEqual(self.calls, [])
        self.assertTrue(self.jobs[0].killed and self.jobs[0].reaped)

    def test_unreaped_process_is_reported_instead_of_success(self):
        def unreaped(*args):
            job = self.job(*args)
            job.reap_ok = False
            return job

        self.assertEqual(self.run_supervisor(unreaped)["reason"], "WORKER_UNREAPED")

    def test_clock_invalid_backwards_and_nonfinite_never_grant_release(self):
        for value in (True, float("nan"), -1, 2 ** 63):
            self.clock.value = value
            self.assertEqual(self.run_supervisor()["reason"], "CLOCK_CONFLICT")
        self.clock.value = 2

        def backwards(*args):
            self.clock.value = 1
            return self.job(*args)

        self.assertEqual(self.run_supervisor(backwards)["reason"], "CLOCK_CONFLICT")
        self.assertEqual(self.calls, [])

    @unittest.skipUnless("fork" in multiprocessing.get_all_start_methods(), "POSIX offline prototype")
    def test_real_child_release_after_expiry_does_not_enter_action(self):
        ctx = multiprocessing.get_context("fork")
        entered, blocker = ctx.Event(), ctx.Event()
        clock = SharedClock()
        job = corrected.GatedProcessJob(REQUEST, Block(entered, blocker), clock, 10 * NS)
        job.start()
        try:
            self.assertTrue(job.ready_event.wait(5))
            self.assertFalse(entered.is_set())
            clock.value.value = 10 * NS
            job.release()
            job.wait(5)
            self.assertFalse(job.alive())
            self.assertEqual(job.result(), corrected.Code.TIMEOUT)
            self.assertFalse(entered.is_set())
        finally:
            job.cancel()
            if job.alive():
                job.kill()
            self.assertTrue(job.reap())

    @unittest.skipUnless("fork" in multiprocessing.get_all_start_methods(), "POSIX offline prototype")
    def test_actual_blocked_bootstrap_and_action_workers_are_killed_and_reaped(self):
        ctx = multiprocessing.get_context("fork")
        for phase in ("BOOTSTRAP", "ACTION"):
            entered, blocker, action_entered = ctx.Event(), ctx.Event(), ctx.Event()
            clock = SharedClock(entered)
            jobs = []

            def factory(request, action, clock, deadline):
                job = corrected.GatedProcessJob(request,
                    Block(entered, blocker) if phase == "ACTION" else lambda _: action_entered.set(),
                    clock, deadline, bootstrap=Block(entered, blocker) if phase == "BOOTSTRAP" else None)
                jobs.append(job)
                return job

            result = corrected.supervise_offline(request=REQUEST, action=lambda _: None,
                                                clock=clock, job_factory=factory)
            self.assertEqual(result["reason"], "TIMEOUT")
            self.assertTrue(entered.is_set())
            self.assertTrue(jobs[0].reaped)
            if phase == "BOOTSTRAP":
                self.assertFalse(result["released"])
                self.assertFalse(action_entered.is_set())

    def test_platform_shared_clock_requirement_is_fail_closed(self):
        result = corrected.supervise_offline(request=REQUEST, action=self.action, clock=self.clock)
        self.assertEqual(result["reason"], "PLATFORM_UNSUPPORTED")
        self.assertEqual(self.calls, [])

    def parse(self, raw):
        self.reader = corrected.MemoryReader(raw)
        return corrected.parse_http_fixture(self.reader)

    def assert_parse_refused(self, raw, code):
        with self.assertRaises(corrected.Refused) as error:
            self.parse(raw)
        self.assertEqual(error.exception.code.value, code)

    def test_valid_narrow_profile_without_library_header_materialization(self):
        parsed = self.parse(wire())
        self.assertEqual(parsed.date_seconds, T)
        self.assertEqual(parsed.payload, {"error": [], "result": {}})
        self.assertLessEqual(self.reader.max_request, 4096)
        self.assertNotIn("payload", repr(parsed))

    def test_pr21_b2_large_headers_are_blocked_before_large_line_allocation(self):
        raw = wire(extras=(("X-Large-A", "a" * 6000), ("X-Large-B", "b" * 6000)))
        self.assert_parse_refused(raw, "LINE_LIMIT")
        self.assertLessEqual(self.reader.position, 8193)

    def test_b2_same_contract_detects_intentionally_unsafe_limits(self):
        raw = wire(extras=(("X-Large-A", "a" * 6000), ("X-Large-B", "b" * 6000)))
        with patch.object(corrected, "HEADER_LIMIT", 100000), patch.object(corrected, "LINE_LIMIT", 65536):
            with self.assertRaises(AssertionError):
                self.assert_parse_refused(raw, "LINE_LIMIT")
        self.assertGreater(self.reader.position, 12000)

    def test_aggregate_header_limit_detects_byte_8193(self):
        raw = wire(extras=tuple((f"X-{i}", "a" * 990) for i in range(10)))
        self.assert_parse_refused(raw, "HEADER_LIMIT")
        self.assertEqual(self.reader.position, 8193)

    def test_line_and_header_count_limits(self):
        self.assert_parse_refused(b"HTTP/1.1 200 " + b"x" * 2000 + b"\r\n\r\n", "LINE_LIMIT")
        self.assertEqual(self.reader.position, 1025)
        self.assert_parse_refused(wire(extras=tuple((f"X-{i}", "a") for i in range(65))), "HEADER_LIMIT")

    def test_crlf_bare_lf_obs_fold_controls_and_duplicate_framing_refuse(self):
        for raw, code in ((wire().replace(b"\r\n", b"\n", 1), "FRAMING_INVALID"),
                          (wire(extras=(("X", "a\rb"),)), "FRAMING_INVALID"),
                          (wire(extras=((" X", "a"),)), "HEADER_INVALID"),
                          (wire(extras=(("X", "a\tb"),)), "HEADER_INVALID"),
                          (wire(extras=(("X", "ok\r\nContent-Length: 99"),)), "HEADER_INVALID")):
            self.assert_parse_refused(raw, code)

    def test_interim_upgrade_redirect_and_http_failure_profiles_refuse(self):
        for code in (100, 101, 103):
            self.assert_parse_refused(wire(status=code), "INTERIM_REFUSED")
        for code in (301, 302, 307):
            self.assert_parse_refused(wire(status=code), "REDIRECT_REFUSED")
        for code in (429, 451, 500):
            self.assert_parse_refused(wire(status=code), "HTTP_REFUSED")

    def test_import_reload_is_side_effect_free_with_network_blocked(self):
        importlib.reload(corrected)
        self.assertEqual(corrected.supervise_offline()["reason"], "AUTHORIZATION_MISSING")
        self.assertEqual(self.calls, [])

    def test_transfer_encoding_chunked_and_content_length_conflicts_refuse(self):
        self.assert_parse_refused(wire(length=False, extras=(("Transfer-Encoding", "chunked"),)), "UNSUPPORTED_TRANSFER")
        self.assert_parse_refused(wire(extras=(("Transfer-Encoding", "chunked"),)), "AMBIGUOUS_FRAMING")
        self.assert_parse_refused(wire(extras=(("Content-Length", "2"),)), "HEADER_INVALID")
        for value in ("01", "-1", "+2", "2,2", "0x10", "9999999"):
            self.assert_parse_refused(wire(length=False, extras=(("Content-Length", value),)), "FRAMING_INVALID")

    def test_trailers_pipelining_premature_eof_and_missing_length_refuse(self):
        self.assert_parse_refused(wire() + b"X-Trailer: no\r\n", "TRAILING_DATA")
        self.assert_parse_refused(wire() + wire(), "TRAILING_DATA")
        self.assert_parse_refused(wire()[:-1], "PREMATURE_EOF")
        self.assert_parse_refused(b"HTTP/1.1 200 OK\r\nDate: ", "PREMATURE_EOF")
        self.assert_parse_refused(wire(length=False), "FRAMING_INVALID")

    def test_body_exact_limit_plus_one_and_input_wire_cap(self):
        body = b'{"x":"' + b"a" * (262144 - 8) + b'"}'
        self.assertEqual(len(body), 262144)
        self.assertEqual(len(self.parse(wire(body)).payload["x"]), 262144 - 8)
        self.assert_parse_refused(wire(body + b" "), "BODY_LIMIT")
        self.assert_parse_refused(b"x" * (corrected.WIRE_LIMIT + 1), "BODY_LIMIT")
        self.assertEqual(self.reader.position, 0)

    def test_compression_content_and_json_utf8_fail_before_approval(self):
        for encoding in ("gzip", "br", "deflate"):
            self.assert_parse_refused(wire(extras=(("Content-Encoding", encoding),)), "COMPRESSION_REFUSED")
        for body in (b"\xff", b"NaN", b"1e999", b'{"x":1,"x":2}', b"[]", b"[" * 2000):
            self.assert_parse_refused(wire(body), "JSON_INVALID")
        self.assert_parse_refused(wire().replace(b"application/json", b"text/html"), "CONTENT_INVALID")
        self.assert_parse_refused(wire().replace(DATE.encode(), b"bad Date"), "CLOCK_UNVERIFIED")

    def test_memory_reader_cannot_accept_a_socket_or_arbitrary_read_adapter(self):
        with self.assertRaises(corrected.Refused):
            corrected.parse_http_fixture(io.BytesIO(wire()))
        with self.assertRaises(corrected.Refused):
            corrected.MemoryReader("not bytes")
        with self.assertRaises(AttributeError):
            corrected.MemoryReader(wire()).read = lambda _: b""

    def assert_global_stop(self, output, calls, expected):
        self.assertEqual(output["reason"], expected.value)
        self.assertEqual(len(calls), 1)
        self.assertEqual(len(output["attempts"]), 1)
        self.assertEqual(output["overall"], "HOLD")

    def test_global_stop_after_every_failure_category(self):
        failures = (corrected.Code.HTTP_REFUSED, corrected.Code.API_ERROR, corrected.Code.ALIAS_CHANGED,
                    corrected.Code.IDENTITY_UNVERIFIED, corrected.Code.CLOCK_CONFLICT,
                    corrected.Code.CLOCK_UNVERIFIED, corrected.Code.SERVICE_TIME_CONFLICT,
                    corrected.Code.WORKER_UNREAPED, corrected.Code.NETWORK_UNAVAILABLE,
                    corrected.Code.TLS_FAILURE, corrected.Code.TIMEOUT)
        for failure in failures:
            calls = []

            def evaluator(symbol, stage):
                calls.append((symbol, stage))
                return corrected.StageResult(failure)

            self.assert_global_stop(corrected.coordinate_global_stop_offline(evaluator), calls, failure)

    def test_status_451_429_api_and_alias_errors_feed_global_stop(self):
        for status in (451, 429):
            calls = []

            def evaluator(symbol, stage):
                calls.append((symbol, stage))
                try:
                    self.parse(wire(status=status))
                except corrected.Refused as exc:
                    return corrected.StageResult(exc.code)

            self.assert_global_stop(corrected.coordinate_global_stop_offline(evaluator), calls, corrected.Code.HTTP_REFUSED)
        for payload, expected in (({"error": ["PRIVATE_SECRET"], "result": {}}, corrected.Code.API_ERROR),
                                   ({"error": [], "result": {"new_alias": {}}}, corrected.Code.ALIAS_CHANGED)):
            calls = []

            def identity(symbol, stage):
                calls.append((symbol, stage))
                try:
                    legacy._identity(symbol, payload)
                except legacy.Refused as exc:
                    return corrected.StageResult(corrected.Code(exc.reason.value))

            self.assert_global_stop(corrected.coordinate_global_stop_offline(identity), calls, expected)

    def test_b3_contract_fails_under_intentionally_unsafe_no_stop_policy(self):
        calls = []

        def failure(symbol, stage):
            calls.append((symbol, stage))
            return corrected.StageResult(corrected.Code.HTTP_REFUSED)

        with patch.object(corrected, "_should_stop", return_value=False):
            unsafe = corrected.coordinate_global_stop_offline(failure)
        with self.assertRaises(AssertionError):
            self.assert_global_stop(unsafe, calls, corrected.Code.HTTP_REFUSED)
        self.assertEqual(len(calls), 6)

    def test_failure_after_partial_success_never_attempts_next_symbol(self):
        calls = []

        def evaluator(symbol, stage):
            calls.append((symbol, stage))
            return corrected.StageResult(corrected.Code.STAGE_PASSED if symbol == "BTC/USD" else corrected.Code.ALIAS_CHANGED)

        result = corrected.coordinate_global_stop_offline(evaluator)
        self.assertEqual(calls, [("BTC/USD", "IDENTITY"), ("BTC/USD", "OHLC"), ("XRP/USD", "IDENTITY")])
        self.assertEqual(result["reason"], "ALIAS_CHANGED")

    def test_all_stage_passes_have_fixed_order_and_still_hold(self):
        result = corrected.coordinate_global_stop_offline(lambda *_: corrected.StageResult(corrected.Code.STAGE_PASSED))
        self.assertEqual(result["reason"], "ALL_STAGE_CHECKS_PASSED")
        self.assertEqual(len(result["attempts"]), 6)
        self.assertEqual(result["overall"], "HOLD")

    def test_unknown_stage_result_or_exception_stops_and_redacts(self):
        for value in (None, "STAGE_PASSED", corrected.StageResult("STAGE_PASSED"),
                      corrected.StageResult(corrected.Code.COMPLETED)):
            result = corrected.coordinate_global_stop_offline(lambda *_: value)
            self.assertEqual(result["reason"], "WORKER_INVALID")
            self.assertEqual(len(result["attempts"]), 1)

        def error(*_):
            raise ValueError("PRIVATE_SECRET")

        self.assertNotIn("PRIVATE_SECRET", str(corrected.coordinate_global_stop_offline(error)))

    def test_unknown_refusal_codes_are_fixed_and_redacted(self):
        for value in ("PRIVATE_SECRET", [], None, "STAGE_PASSED"):
            error = corrected.Refused(value)
            self.assertEqual(error.code, corrected.Code.WORKER_INVALID)
            self.assertEqual(str(error), "WORKER_INVALID")

    def test_new_and_original_default_cli_remain_disabled(self):
        for module in (legacy, corrected):
            with redirect_stdout(io.StringIO()) as output:
                self.assertEqual(module.main(), 2)
            self.assertIn("AUTHORIZATION_MISSING", output.getvalue())
            self.assertIn('"requests":0', output.getvalue())
        self.assertEqual(corrected.supervise_offline()["reason"], "AUTHORIZATION_MISSING")
        self.assertEqual(corrected.coordinate_global_stop_offline()["reason"], "AUTHORIZATION_MISSING")


if __name__ == "__main__":
    unittest.main()
