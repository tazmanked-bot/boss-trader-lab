"""Offline candidate-client review; passing counterexamples document HOLDs.

No live factory or activation code is implemented. MemoryConnection uses the
real stdlib HTTPResponse parser over BytesIO and cannot create a socket.
"""

from contextlib import ExitStack, redirect_stdout
import copy
from datetime import datetime, timezone
from email.utils import format_datetime
import http.client
import io
import json
from pathlib import Path
import socket
import ssl
import unittest
from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit
import urllib.request

from research import kraken_spot_diagnostic as diagnostic
from research import spot_refusal_registry as registry


ROOT = Path(__file__).parent / "fixtures"
IDENTITIES = json.loads((ROOT / "kraken_diagnostic_identity_v1.json").read_text())["identities"]
OHLC = json.loads((ROOT / "kraken_spot_bridge_v1.json").read_text())
T = OHLC["as_of"]
NS = 1_000_000_000
AP = "/0/public/AssetPairs"
REVISION = "0" * 40  # Synthetic test claim only.


class Clock:
    trusted = True

    def __init__(self):
        self.ticks = 0
        self.offset = 0

    def monotonic_ns(self):
        return self.ticks

    def sample(self):
        return diagnostic.Stamp((T + 3) * NS + self.ticks + self.offset, self.ticks)


class CountedBytes(io.BytesIO):
    def __init__(self, data):
        super().__init__(data)
        self.consumed = 0
        self.body_read_sizes = []

    def readline(self, size=-1):
        value = super().readline(size)
        self.consumed += len(value)
        return value

    def read(self, size=-1):
        self.body_read_sizes.append(size)
        value = super().read(size)
        self.consumed += len(value)
        return value


class MemorySocket:
    def __init__(self, stream):
        self.stream = stream

    def makefile(self, mode):
        assert mode == "rb"
        return self.stream


class MemoryConnection:
    def __init__(self, factory):
        self.factory = factory

    def request(self, method, target, body, headers):
        assert method == "GET" and body is None
        self.factory.sent.append(target)
        self.path = urlsplit(target).path
        pair = parse_qs(urlsplit(target).query)["pair"][0]
        self.symbol = {"XBTUSD": "BTC/USD", "XRPUSD": "XRP/USD", "SOLUSD": "SOL/USD"}[pair]

    def getresponse(self):
        payload = (self.factory.identities[self.symbol] if self.path == AP
                   else self.factory.ohlc[self.symbol])
        spec = self.factory.overrides.get((self.symbol, self.path), {})
        body = spec.get("body", registry.canonical_json(payload).encode("utf-8"))
        date = format_datetime(datetime.fromtimestamp(self.factory.clock.sample().utc_ns // NS,
                                                      timezone.utc), usegmt=True)
        headers = [("Content-Type", "application/json"), ("Date", date)] + spec.get("headers", [])
        if spec.get("chunked"):
            headers += [("Transfer-Encoding", "chunked")]
            wire_body = f"{len(body):x}\r\n".encode() + body + b"\r\n0\r\n\r\n"
        else:
            headers += [("Content-Length", str(len(body)))]
            wire_body = body
        wire = (f"HTTP/1.1 {spec.get('status', 200)} Synthetic\r\n".encode()
                + b"".join(f"{k}: {v}\r\n".encode("ascii") for k, v in headers) + b"\r\n" + wire_body)
        stream = CountedBytes(wire)
        self.factory.streams.append(stream)
        response = http.client.HTTPResponse(MemorySocket(stream), method="GET", debuglevel=0)
        response.begin()  # Real stdlib header allocation precedes _exchange.getheaders().
        return response

    def close(self):
        pass


class MemoryFactory:
    def __init__(self, clock):
        self.clock = clock
        self.identities = copy.deepcopy(IDENTITIES)
        self.ohlc = {s: copy.deepcopy(v["response"]) for s, v in OHLC["captures"].items()}
        self.overrides = {}
        self.sent, self.streams = [], []

    def __call__(self, host, *, port, context, timeout):
        assert host == "api.kraken.com" and port == 443 and timeout == 10
        assert context.check_hostname and context.verify_mode == ssl.CERT_REQUIRED
        return MemoryConnection(self)


class InlineJob:
    def __init__(self, request, factory):
        self.request, self.factory = request, factory
        self.started = self.killed = self.reaped = False

    def start(self):
        self.started = True

    def alive(self):
        return False

    def result(self):
        return diagnostic._exchange(self.request, self.factory)

    def wait(self, seconds):
        raise AssertionError("completed memory worker cannot wait")

    def kill(self):
        self.killed = True

    def reap(self):
        self.reaped = True
        return True


class PublicProbeReviewTests(unittest.TestCase):
    def setUp(self):
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        self.network_blocks = [self.stack.enter_context(patch.object(obj, name,
                               side_effect=AssertionError("NETWORK FORBIDDEN")))
                               for obj, name in ((socket, "socket"), (socket, "create_connection"),
                                                 (socket, "getaddrinfo"), (urllib.request, "urlopen"))]
        self.clock = Clock()
        self.factory = MemoryFactory(self.clock)

    def tearDown(self):
        for blocked in self.network_blocks:
            blocked.assert_not_called()

    def run_memory(self):
        return diagnostic.run_offline(connection_factory=self.factory, clock=self.clock,
                                      reviewed_revision=REVISION, job_factory=InlineJob)

    def test_candidate_stdlib_parser_handles_synthetic_identity_first_flow(self):
        result = self.run_memory()
        self.assertEqual(result["requests"], 6)
        self.assertEqual(result["data_checks"], "ALL_PASSED")
        self.assertEqual(result["overall"], "HOLD")
        for i in (0, 2, 4):
            self.assertTrue(self.factory.sent[i].startswith(AP + "?"))
            self.assertTrue(self.factory.sent[i + 1].startswith("/0/public/OHLC?"))

    def test_counterexample_stdlib_allocates_headers_before_diagnostic_8192_guard(self):
        self.factory.overrides[("BTC/USD", AP)] = {"headers": [("X-Large-A", "a" * 6000),
                                                                             ("X-Large-B", "b" * 6000)]}
        result = self.run_memory()
        self.assertEqual(result["symbols"]["BTC/USD"]["reason"], "CONTENT_INVALID")
        self.assertGreater(self.factory.streams[0].consumed, 12000)
        self.assertEqual(self.factory.streams[0].body_read_sizes, [])
        # Characterization PASS proves the proposed preallocation safeguard FAILS.

    def test_real_parser_content_length_and_chunked_body_cap_limit_plus_one(self):
        for chunked in (False, True):
            self.factory = MemoryFactory(self.clock)
            self.factory.overrides[("BTC/USD", AP)] = {"body": b" " * 262145, "chunked": chunked}
            result = self.run_memory()
            self.assertEqual(result["symbols"]["BTC/USD"]["reason"], "RESPONSE_TOO_LARGE")
            self.assertNotIn("body", result["symbols"]["BTC/USD"])

    def test_real_parser_redirect_and_compression_do_not_read_response_body(self):
        for override, expected in (({"status": 302}, "REDIRECT_REFUSED"),
                                   ({"headers": [("Content-Encoding", "gzip")]}, "CONTENT_INVALID")):
            self.factory = MemoryFactory(self.clock)
            self.factory.overrides[("BTC/USD", AP)] = {**override, "body": b"DO_NOT_ECHO"}
            result = self.run_memory()
            self.assertEqual(result["symbols"]["BTC/USD"]["reason"], expected)
            self.assertEqual(self.factory.streams[0].body_read_sizes, [])
            self.assertNotIn("DO_NOT_ECHO", registry.canonical_json(result))

    def test_real_parser_malformed_json_and_duplicate_keys_refuse(self):
        for body in (b"NaN", b"1e999", b'{"error":[],"error":[]}', b"\xff"):
            self.factory = MemoryFactory(self.clock)
            self.factory.overrides[("BTC/USD", AP)] = {"body": body}
            result = self.run_memory()
            self.assertEqual(result["symbols"]["BTC/USD"]["reason"], "JSON_INVALID")

    def test_actual_https_constructor_keeps_strict_context_and_does_not_use_env_proxy(self):
        context = diagnostic._tls_context()
        with patch.dict("os.environ", {"HTTPS_PROXY": "http://not-a-route.invalid:1",
                                       "HTTP_PROXY": "http://not-a-route.invalid:1"}):
            client = http.client.HTTPSConnection("api.kraken.com", port=443, timeout=10, context=context)
            try:
                self.assertEqual(client.host, "api.kraken.com")
                self.assertIsNone(client._tunnel_host)
                self.assertIs(client._context, context)
                self.assertTrue(client._context.check_hostname)
                self.assertEqual(client._context.verify_mode, ssl.CERT_REQUIRED)
                self.assertIsNone(client.sock)  # Construction only; never connect/request.
            finally:
                client.close()

    def test_counterexample_slow_factory_can_start_worker_after_deadline(self):
        jobs = []

        class DelayedJob(InlineJob):
            def alive(self):
                return not self.killed

        def slow_factory(request, factory):
            self.clock.ticks += 11 * NS
            job = DelayedJob(request, factory)
            jobs.append(job)
            return job

        request = diagnostic.Request("BTC/USD", AP,
                                     (("pair", "XBTUSD"), ("aclass_base", "currency"), ("info", "info")))
        with self.assertRaises(diagnostic.Refused) as error:
            diagnostic._supervise(request, self.factory, self.clock, slow_factory)
        self.assertEqual(error.exception.reason, diagnostic.Reason.TIMEOUT)
        self.assertTrue(jobs[0].started)  # Verified unmet pre-start deadline condition.
        self.assertTrue(jobs[0].killed)
        self.assertTrue(jobs[0].reaped)
        self.assertEqual(self.factory.sent, [])

    def test_counterexample_blocking_start_is_only_checked_after_it_returns(self):
        class SlowStart(InlineJob):
            def start(job):
                self.clock.ticks += 11 * NS
                job.started = True

        request = diagnostic.Request("BTC/USD", AP,
                                     (("pair", "XBTUSD"), ("aclass_base", "currency"), ("info", "info")))
        with self.assertRaises(diagnostic.Refused) as error:
            diagnostic._supervise(request, self.factory, self.clock, SlowStart)
        self.assertEqual(error.exception.reason, diagnostic.Reason.TIMEOUT)
        self.assertEqual(self.clock.ticks, 11 * NS)
        self.assertEqual(self.factory.sent, [])

    def test_counterexample_offline_451_does_not_stop_all_other_symbol_attempts(self):
        self.factory.overrides[("BTC/USD", AP)] = {"status": 451}
        result = self.run_memory()
        self.assertEqual(result["symbols"]["BTC/USD"]["reason"], "HTTP_REFUSED")
        self.assertEqual(result["requests"], 5)
        self.assertEqual(result["symbols"]["XRP/USD"]["reason"], "DATA_CHECKS_PASSED")
        self.assertEqual(result["overall"], "HOLD")
        # Valid existing offline isolation, incompatible with proposed global STOP.

    def test_changed_alias_still_prevents_ohlc_with_real_memory_parser(self):
        payload = self.factory.identities["XRP/USD"]["result"]
        payload["XRPUSD_NEW"] = payload.pop("XXRPZUSD")
        result = self.run_memory()
        self.assertEqual(result["symbols"]["XRP/USD"]["reason"], "ALIAS_CHANGED")
        self.assertEqual(sum("pair=XRPUSD" in target for target in self.factory.sent), 1)

    def test_clock_trusted_flag_is_not_absolute_utc_attestation(self):
        self.clock.offset = 86400 * NS
        gate = diagnostic.CaptureClock(self.clock)
        self.assertEqual(gate.as_of, T + 86400)
        self.clock.offset += 2 * NS
        with self.assertRaises(diagnostic.Refused) as error:
            gate.sample()
        self.assertEqual(error.exception.reason, diagnostic.Reason.CLOCK_CONFLICT)
        # Constant initial offset is unknowable here; subsequent drift is checked.

    def test_no_activation_or_environment_flag_changes_default_zero_request_behavior(self):
        with patch.dict("os.environ", {"BOSS_LIVE": "true", "OWNER_APPROVED": "true"}):
            with redirect_stdout(io.StringIO()) as output:
                self.assertEqual(diagnostic.main(), 2)
            disabled = json.loads(output.getvalue())
            self.assertEqual(disabled["reason"], "AUTHORIZATION_MISSING")
            self.assertEqual(disabled["requests"], 0)
            self.assertEqual(diagnostic.run_offline()["requests"], 0)
        self.assertEqual(self.factory.sent, [])


if __name__ == "__main__":
    unittest.main()
