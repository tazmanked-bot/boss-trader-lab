"""Disabled-by-default diagnostic core. Only dependency-injected offline use.

There is deliberately no real HTTPS connection constructor, live CLI flag,
environment activation, retry, workflow or production entrypoint integration.
Injected factories are trusted test code, not an arbitrary-code sandbox.
"""

from dataclasses import dataclass
from datetime import timezone
from email.utils import parsedate_to_datetime, format_datetime
from enum import Enum
import hashlib
import json
import multiprocessing
from pathlib import Path
import re
import ssl
import struct
import threading
from urllib.parse import urlencode

from research import kraken_spot_validation_bridge as bridge
from research import spot_refusal_registry as registry


VERSION = "kraken-spot-diagnostic-v1"
CAPTURE_POLICY = "manual-capture-v1"
BASELINE = "1115eb9730100ae99c2d05ed12c50d75aef104f8"
HOST = "api.kraken.com"
NS = 1_000_000_000
DEADLINE_NS = 10 * NS
BODY_LIMIT = 262144
WIRE_LIMIT = BODY_LIMIT + 2048
BRIDGE_POLICY = {"version": "spot-refusal-v1", "future_mode": "as_of"}
IDENTITIES = {
    "BTC/USD": ("XBTUSD", "XXBTZUSD", "XXBT", "XBT/USD"),
    "XRP/USD": ("XRPUSD", "XXRPZUSD", "XXRP", "XRP/USD"),
    "SOL/USD": ("SOLUSD", "SOLUSD", "SOL", "SOL/USD"),
}
IDENTITY_FIELDS = {"altname", "wsname", "base", "quote", "aclass_base", "aclass_quote", "status"}
OPTIONAL_METADATA = {"lot", "lot_multiplier", "pair_decimals", "lot_decimals", "cost_decimals",
                     "leverage_buy", "leverage_sell", "fees", "fees_maker", "fee_volume_currency",
                     "margin_call", "margin_stop", "ordermin", "costmin", "tick_size",
                     "long_position_limit", "short_position_limit"}


class Reason(str, Enum):
    AUTHORIZATION_MISSING = "AUTHORIZATION_MISSING"
    CONTEXT_INVALID = "CONTEXT_INVALID"
    PLATFORM_UNSUPPORTED = "PLATFORM_UNSUPPORTED"
    WORKER_INVALID = "WORKER_INVALID"
    WORKER_UNREAPED = "WORKER_UNREAPED"
    TIMEOUT = "TIMEOUT"
    TLS_FAILURE = "TLS_FAILURE"
    NETWORK_UNAVAILABLE = "NETWORK_UNAVAILABLE"
    REDIRECT_REFUSED = "REDIRECT_REFUSED"
    HTTP_REFUSED = "HTTP_REFUSED"
    RESPONSE_TOO_LARGE = "RESPONSE_TOO_LARGE"
    CONTENT_INVALID = "CONTENT_INVALID"
    JSON_INVALID = "JSON_INVALID"
    API_ERROR = "API_ERROR"
    IDENTITY_UNVERIFIED = "IDENTITY_UNVERIFIED"
    ALIAS_CHANGED = "ALIAS_CHANGED"
    CLOCK_UNVERIFIED = "CLOCK_UNVERIFIED"
    CLOCK_CONFLICT = "CLOCK_CONFLICT"
    SERVICE_TIME_CONFLICT = "SERVICE_TIME_CONFLICT"
    COMMITMENT_CONFLICT = "COMMITMENT_CONFLICT"
    BRIDGE_REFUSED = "BRIDGE_REFUSED"
    DATA_CHECKS_PASSED = "DATA_CHECKS_PASSED"


class Refused(ValueError):
    def __init__(self, reason):
        self.reason = reason


TRANSPORT_FAILURES = {r.value for r in (
    Reason.CONTEXT_INVALID, Reason.TIMEOUT, Reason.TLS_FAILURE, Reason.NETWORK_UNAVAILABLE,
    Reason.REDIRECT_REFUSED, Reason.HTTP_REFUSED, Reason.RESPONSE_TOO_LARGE,
    Reason.CONTENT_INVALID, Reason.JSON_INVALID, Reason.CLOCK_UNVERIFIED,
)}


def _tls_context():
    # Avoid create_default_context's optional SSLKEYLOGFILE environment hook.
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    context.load_default_certs()
    return context


@dataclass(frozen=True)
class Request:
    symbol: str
    path: str
    params: tuple

    def target(self):
        if type(self.symbol) is not str or self.symbol not in IDENTITIES:
            raise Refused(Reason.CONTEXT_INVALID)
        if (type(self.path) is not str or type(self.params) is not tuple
                or any(type(p) is not tuple or len(p) != 2 or type(p[0]) is not str for p in self.params)):
            raise Refused(Reason.CONTEXT_INVALID)
        pair = IDENTITIES[self.symbol][0]
        if self.path == "/0/public/AssetPairs":
            expected = (("pair", pair), ("aclass_base", "currency"), ("info", "info"))
            if self.params != expected or any(type(p[1]) is not str for p in self.params):
                raise Refused(Reason.CONTEXT_INVALID)
        elif self.path == "/0/public/OHLC":
            if (type(self.params) is not tuple or len(self.params) != 3
                    or self.params[:2] != (("pair", pair), ("interval", 60))
                    or type(self.params[0][1]) is not str or type(self.params[1][1]) is not int
                    or type(self.params[2]) is not tuple or len(self.params[2]) != 2
                    or self.params[2][0] != "since" or type(self.params[2][1]) is not int
                    or not registry.MIN_TIME <= self.params[2][1] < registry.MAX_TIME
                    or self.params[2][1] % 3600):
                raise Refused(Reason.CONTEXT_INVALID)
        else:
            raise Refused(Reason.CONTEXT_INVALID)
        return self.path + "?" + urlencode(self.params)


def _strict_json(body):
    def constant(_):
        raise ValueError

    def unique(pairs):
        obj = {}
        for key, value in pairs:
            if key in obj:
                raise ValueError
            obj[key] = value
        return obj

    try:
        if type(body) is not bytes or len(body) > BODY_LIMIT:
            raise ValueError
        obj = json.loads(body.decode("utf-8"), parse_constant=constant, object_pairs_hook=unique)
        registry.canonical_json(obj)  # Reject 1e999 even though parse_constant is not invoked.
        return obj
    except (ValueError, TypeError, UnicodeError, RecursionError, OverflowError):
        raise Refused(Reason.JSON_INVALID) from None


def _date(value):
    try:
        if type(value) is not str or len(value) > 64:
            raise ValueError
        dt = parsedate_to_datetime(value)
        if dt.tzinfo != timezone.utc or format_datetime(dt, usegmt=True) != value:
            raise ValueError
        seconds = int(dt.timestamp())
        if not registry.MIN_TIME <= seconds < registry.MAX_TIME:
            raise ValueError
        return seconds
    except (ValueError, TypeError, OverflowError):
        raise Refused(Reason.CLOCK_UNVERIFIED) from None


def _exchange(request, connection_factory):
    """Internal injected connection only. Never constructs a real client here."""
    connection = None
    try:
        target = request.target()
        context = _tls_context()
        if context.verify_mode != ssl.CERT_REQUIRED or not context.check_hostname:
            raise Refused(Reason.TLS_FAILURE)
        # A test factory receives the fixed host/port/TLS policy. No proxy handler,
        # urllib opener, cookies, auth or redirect-following behavior is used.
        connection = connection_factory(HOST, port=443, context=context, timeout=10)
        connection.request("GET", target, body=None,
                           headers={"Accept": "application/json", "Accept-Encoding": "identity",
                                    "User-Agent": "BOSS-offline-diagnostic-research/1"})
        response = connection.getresponse()
        if type(response.status) is not int:
            raise Refused(Reason.CONTENT_INVALID)
        if 300 <= response.status < 400:
            raise Refused(Reason.REDIRECT_REFUSED)
        if response.status != 200:
            raise Refused(Reason.HTTP_REFUSED)
        headers = {}
        header_size = 0
        for index, (name, value) in enumerate(response.getheaders()):
            if type(name) is not str or type(value) is not str or len(name) > 64 or len(value) > 1024:
                raise Refused(Reason.CONTENT_INVALID)
            header_size += len(name) + len(value)
            if index >= 64 or header_size > 8192:
                raise Refused(Reason.CONTENT_INVALID)
            key = name.lower()
            if key in ("content-type", "content-encoding", "date", "content-length"):
                if key in headers:
                    raise Refused(Reason.CONTENT_INVALID)
                headers[key] = value
        if not re.fullmatch(r"application/json(?:;\s*charset=utf-8)?", headers.get("content-type", "").lower()):
            raise Refused(Reason.CONTENT_INVALID)
        if headers.get("content-encoding", "identity").lower() != "identity":
            raise Refused(Reason.CONTENT_INVALID)
        date = _date(headers.get("date"))
        body = response.read(BODY_LIMIT + 1)
        if type(body) is not bytes:
            raise Refused(Reason.CONTENT_INVALID)
        if len(body) > BODY_LIMIT:
            raise Refused(Reason.RESPONSE_TOO_LARGE)
        _strict_json(body)
        return {"reason": None, "date": date}, body
    except Refused as exc:
        return {"reason": exc.reason.value}, b""
    except TimeoutError:
        return {"reason": Reason.TIMEOUT.value}, b""
    except ssl.SSLError:
        return {"reason": Reason.TLS_FAILURE.value}, b""
    except Exception:
        return {"reason": Reason.NETWORK_UNAVAILABLE.value}, b""
    finally:
        if connection is not None:
            try:
                connection.close()
            except Exception:
                pass


def _worker(request, connection_factory, buffer):
    try:
        meta, body = _exchange(request, connection_factory)
        header = registry.canonical_json(meta).encode("ascii")
        wire = struct.pack("!I", len(header)) + header + body
        if len(wire) > WIRE_LIMIT:
            return
        buffer[4:4 + len(wire)] = wire
        buffer[:4] = struct.pack("!I", len(wire))  # Publish length last.
    except BaseException:
        pass  # Parent observes WORKER_INVALID, never a raw exception/body log.


class ProcessJob:
    """POSIX single-thread fork worker with fixed shared memory, no pipe recv."""
    def __init__(self, request, connection_factory):
        if threading.active_count() != 1 or "fork" not in multiprocessing.get_all_start_methods():
            raise Refused(Reason.PLATFORM_UNSUPPORTED)
        context = multiprocessing.get_context("fork")
        self.buffer = context.RawArray("B", WIRE_LIMIT + 4)
        self.process = context.Process(target=_worker, args=(request, connection_factory, self.buffer), daemon=True)
        self.reaped = False

    def start(self):
        self.process.start()

    def alive(self):
        return self.process.is_alive()

    def wait(self, seconds):
        self.process.join(timeout=seconds)

    def kill(self):
        self.process.kill()

    def reap(self):
        self.process.join(timeout=0.25)
        dead = not self.process.is_alive()
        if dead:
            self.process.close()
            self.reaped = True
        return dead

    def result(self):
        if self.process.exitcode != 0:
            raise Refused(Reason.WORKER_INVALID)
        length = struct.unpack("!I", bytes(self.buffer[:4]))[0]
        if not 4 < length <= WIRE_LIMIT:
            raise Refused(Reason.WORKER_INVALID)
        wire = bytes(self.buffer[4:4 + length])
        count = struct.unpack("!I", wire[:4])[0]
        if not 0 < count <= 1024 or 4 + count > len(wire):
            raise Refused(Reason.WORKER_INVALID)
        meta = _strict_json(wire[4:4 + count])
        body = wire[4 + count:]
        return meta, body


def _supervise(request, factory, clock, job_factory):
    """Parent deadline covers start, DNS, connection, response and body read.

    Cleanup has its own bounded 250ms reap allowance. OS scheduling/kernel kill
    guarantees are not established by this Python mechanism or offline tests.
    """
    request.target()
    job = None
    started = False
    finished = False
    try:
        begin = clock.monotonic_ns()
        if type(begin) is not int or not 0 <= begin < 10 ** 24:
            raise Refused(Reason.CLOCK_CONFLICT)
        deadline = begin + DEADLINE_NS
        job = job_factory(request, factory)
        started = True
        job.start()
        previous = begin
        while True:
            now = clock.monotonic_ns()
            if type(now) is not int or not previous <= now < 10 ** 24:
                raise Refused(Reason.CLOCK_CONFLICT)
            previous = now
            if now >= deadline:
                raise Refused(Reason.TIMEOUT)
            if not job.alive():
                meta, body = job.result()
                after = clock.monotonic_ns()
                if type(after) is not int or not now <= after < 10 ** 24:
                    raise Refused(Reason.CLOCK_CONFLICT)
                if after >= deadline:
                    raise Refused(Reason.TIMEOUT)
                if not job.reap():
                    raise Refused(Reason.WORKER_UNREAPED)
                finished = True
                return meta, body
            job.wait(min((deadline - now) / NS, 0.01))
    except Refused:
        raise
    except Exception:
        raise Refused(Reason.WORKER_INVALID) from None
    finally:
        if job is not None and started and not finished:
            try:
                if job.alive():
                    job.kill()  # No grace period consuming the request deadline.
                if not job.reap():
                    raise RuntimeError
            except Exception:
                raise Refused(Reason.WORKER_UNREAPED) from None


@dataclass(frozen=True)
class Stamp:
    utc_ns: int
    mono_ns: int


class CaptureClock:
    def __init__(self, clock):
        if getattr(clock, "trusted", False) is not True:
            raise Refused(Reason.CLOCK_UNVERIFIED)
        self.clock = clock
        self.initial = self.previous = self._sample()
        self.as_of = ((self.initial.utc_ns // NS - 2) // 3600) * 3600
        if not registry.MIN_TIME + 24 * 3600 <= self.as_of < registry.MAX_TIME:
            raise Refused(Reason.CLOCK_UNVERIFIED)

    def _sample(self):
        value = self.clock.sample()
        if (type(value) is not Stamp or type(value.utc_ns) is not int or type(value.mono_ns) is not int
                or not registry.MIN_TIME * NS <= value.utc_ns < registry.MAX_TIME * NS
                or not 0 <= value.mono_ns < 10 ** 24):
            raise Refused(Reason.CLOCK_UNVERIFIED)
        return value

    def sample(self):
        value = self._sample()
        for anchor in (self.initial, self.previous):
            wall = value.utc_ns - anchor.utc_ns
            mono = value.mono_ns - anchor.mono_ns
            if wall < 0 or mono < 0 or abs(wall - mono) > NS:
                raise Refused(Reason.CLOCK_CONFLICT)
        self.previous = value
        return value

    def envelope(self, start, end, date):
        elapsed = end.mono_ns - start.mono_ns
        if not 0 <= elapsed < DEADLINE_NS:
            raise Refused(Reason.TIMEOUT)
        if abs((end.utc_ns - start.utc_ns) - elapsed) > NS:
            raise Refused(Reason.CLOCK_CONFLICT)
        if type(date) is not int:
            raise Refused(Reason.CLOCK_UNVERIFIED)
        if not start.utc_ns // NS - 2 <= date <= end.utc_ns // NS + 2:
            raise Refused(Reason.SERVICE_TIME_CONFLICT)


def _identity(symbol, payload):
    if type(payload) is not dict or set(payload) != {"error", "result"} or type(payload["error"]) is not list:
        raise Refused(Reason.IDENTITY_UNVERIFIED)
    if payload["error"]:
        raise Refused(Reason.API_ERROR)
    alt, key, base, wsname = IDENTITIES[symbol]
    result = payload["result"]
    if type(result) is not dict or set(result) != {key}:
        raise Refused(Reason.ALIAS_CHANGED)
    data = result[key]
    if (type(data) is not dict or not IDENTITY_FIELDS <= set(data)
            or not set(data) <= IDENTITY_FIELDS | OPTIONAL_METADATA):
        raise Refused(Reason.IDENTITY_UNVERIFIED)
    expected = {"altname": alt, "wsname": wsname, "base": base, "quote": "ZUSD",
                "aclass_base": "currency", "aclass_quote": "currency", "status": "online"}
    if any(type(data[k]) is not str or data[k] != v for k, v in expected.items()):
        raise Refused(Reason.IDENTITY_UNVERIFIED)
    return key


def _commitment(payload, key, as_of, end, service_date):
    if type(payload) is not dict or set(payload) != {"error", "result"} or type(payload["error"]) is not list:
        raise Refused(Reason.COMMITMENT_CONFLICT)
    if payload["error"]:
        raise Refused(Reason.API_ERROR)
    result = payload["result"]
    if type(result) is not dict or set(result) != {key, "last"}:
        raise Refused(Reason.ALIAS_CHANGED)
    rows = result[key]
    if type(rows) is not list or not 1 <= len(rows) <= 512:
        raise Refused(Reason.COMMITMENT_CONFLICT)
    latest_possible = (min(end.utc_ns // NS + 2, service_date + 2) // 3600) * 3600
    previous = None
    for row in rows:
        if type(row) is not list or len(row) != 8:
            raise Refused(Reason.COMMITMENT_CONFLICT)
        stamp = row[0]
        if (type(stamp) is not int or not registry.MIN_TIME <= stamp < registry.MAX_TIME
                or stamp % 3600 or stamp > latest_possible):
            raise Refused(Reason.COMMITMENT_CONFLICT)
        # Eligible continuity remains the registry's responsibility. Structurally
        # invalid projected headers cannot hide behind the projection contract.
        if previous is not None and stamp + 3600 > as_of and stamp - previous != 3600:
            raise Refused(Reason.COMMITMENT_CONFLICT)
        previous = stamp
    if rows[-1][0] + 3600 <= as_of:
        raise Refused(Reason.COMMITMENT_CONFLICT)  # Claimed uncommitted row would be eligible.


def _code_hash():
    with Path(__file__).open("rb") as source:
        data = source.read(65537)
    if len(data) > 65536:
        raise Refused(Reason.CONTEXT_INVALID)
    return hashlib.sha256(data).hexdigest()


def _seal(value, bound):
    value = {**value, "diagnostic_hash": hashlib.sha256(registry.canonical_json(value).encode("ascii")).hexdigest()}
    if len(registry.canonical_json(value)) > bound:
        raise Refused(Reason.CONTEXT_INVALID)
    return value


def _disabled():
    return _seal({"mode": "DISABLED", "version": VERSION, "overall": "HOLD",
                  "reason": Reason.AUTHORIZATION_MISSING.value, "requests": 0}, 4096)


def run_offline(*, connection_factory=None, clock=None, reviewed_revision=None, job_factory=ProcessJob):
    """Trusted injected offline fakes only. No activation bool or live default.

    reviewed_revision is a recorded claim; the future owner workflow must verify
    checkout identity independently. Code content hash identifies this module.
    """
    if connection_factory is None:
        return _disabled()
    if type(reviewed_revision) is not str or not re.fullmatch(r"[0-9a-f]{40}", reviewed_revision):
        return _seal({"mode": "OFFLINE_INJECTED", "overall": "HOLD", "reason": "CONTEXT_INVALID", "requests": 0}, 4096)
    try:
        gate = CaptureClock(clock)
        code_hash = _code_hash()
    except Refused as exc:
        return _seal({"mode": "OFFLINE_INJECTED", "overall": "HOLD", "reason": exc.reason.value, "requests": 0}, 4096)
    except Exception:
        return _seal({"mode": "OFFLINE_INJECTED", "overall": "HOLD", "reason": "CLOCK_UNVERIFIED", "requests": 0}, 4096)
    results = {}
    stop = None
    attempts = 0
    for symbol in registry.SYMBOLS:
        receipts = []
        key = None
        decision = None
        stage = "IDENTITY"
        reason = stop
        try:
            if stop is not None:
                raise Refused(stop)
            alt = IDENTITIES[symbol][0]
            for stage, request in (
                ("IDENTITY", Request(symbol, "/0/public/AssetPairs", (("pair", alt), ("aclass_base", "currency"), ("info", "info")))),
                ("OHLC", Request(symbol, "/0/public/OHLC", (("pair", alt), ("interval", 60), ("since", gate.as_of - 86400)))),
            ):
                start = gate.sample()
                attempts += 1
                receipt = {"path": request.path, "params": dict(request.params),
                           "start_utc_ns": start.utc_ns, "start_mono_ns": start.mono_ns}
                receipts.append(receipt)
                meta, body = _supervise(request, connection_factory, clock, job_factory)
                end = gate.sample()
                receipt.update(end_utc_ns=end.utc_ns, elapsed_ns=end.mono_ns - start.mono_ns)
                if type(meta) is not dict or "reason" not in meta:
                    raise Refused(Reason.WORKER_INVALID)
                if meta["reason"] is not None:
                    if (set(meta) != {"reason"} or type(meta["reason"]) is not str
                            or meta["reason"] not in TRANSPORT_FAILURES or body):
                        raise Refused(Reason.WORKER_INVALID)
                    raise Refused(Reason(meta["reason"]))
                if set(meta) != {"reason", "date"}:
                    raise Refused(Reason.WORKER_INVALID)
                gate.envelope(start, end, meta["date"])
                receipt["service_date_utc_seconds"] = meta["date"]
                receipt["clock_consistent"] = True
                payload = _strict_json(body)
                if stage == "IDENTITY":
                    key = _identity(symbol, payload)
                else:
                    _commitment(payload, key, gate.as_of, end, meta["date"])
                    capture = {"venue": "kraken", "market": "spot", "quote": "USD", "symbol": symbol,
                               "request_pair": alt, "interval_minutes": 60, "response": payload}
                    decision = bridge.validate_capture(symbol, capture, as_of=gate.as_of, policy=BRIDGE_POLICY)
                    if decision["decision"]["status"] != "VALIDATED_DATA":
                        raise Refused(Reason.BRIDGE_REFUSED)
            reason = Reason.DATA_CHECKS_PASSED
        except Refused as exc:
            reason = exc.reason
            if reason in (Reason.CLOCK_UNVERIFIED, Reason.CLOCK_CONFLICT, Reason.SERVICE_TIME_CONFLICT,
                          Reason.WORKER_UNREAPED, Reason.PLATFORM_UNSUPPORTED):
                stop = reason  # Clock/process failure prevents subsequent requests.
        except Exception:
            reason = Reason.WORKER_INVALID
            stop = reason
        # Attempt failure still records a safe end envelope when available.
        if receipts and "end_utc_ns" not in receipts[-1]:
            try:
                end = gate.sample()
                receipts[-1].update(end_utc_ns=end.utc_ns,
                                    elapsed_ns=end.mono_ns - receipts[-1]["start_mono_ns"])
            except Exception:
                stop = Reason.CLOCK_CONFLICT
        results[symbol] = _seal({"symbol": symbol, "venue": "kraken", "market": "spot", "quote": "USD",
                                 "as_of_utc_seconds": gate.as_of, "stage": stage, "reason": reason.value,
                                 "identity_consistent": key is not None, "source_pair_key": key,
                                 "clock_status": ("CONSISTENT" if receipts and all(r.get("clock_consistent") for r in receipts)
                                                  else "UNVERIFIED"),
                                 "clock_reason": (stop.value if stop in (Reason.CLOCK_UNVERIFIED, Reason.CLOCK_CONFLICT,
                                                                         Reason.SERVICE_TIME_CONFLICT) else None),
                                 "receipts": receipts, "bridge": decision}, 4096)
    return _seal({"mode": "OFFLINE_INJECTED", "version": VERSION, "capture_policy": CAPTURE_POLICY,
                  "bridge_policy": dict(BRIDGE_POLICY), "reviewed_revision_claim": reviewed_revision,
                  "implementation_sha256": code_hash, "baseline": BASELINE, "overall": "HOLD",
                  "data_checks": "ALL_PASSED" if all(r["reason"] == "DATA_CHECKS_PASSED" and r["identity_consistent"]
                                                     and r["clock_status"] == "CONSISTENT" and r["bridge"]
                                                     and r["bridge"]["decision"]["status"] == "VALIDATED_DATA"
                                                     for r in results.values()) else "REFUSED",
                  "as_of_utc_seconds": gate.as_of, "requests": attempts, "symbols": results}, 16384)


def main():
    print(registry.canonical_json(_disabled()))
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
