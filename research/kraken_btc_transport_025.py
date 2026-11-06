"""Disabled transport boundary; dependency-injected OFFLINE verification only.

No DNS/socket/TLS provider or authentic UTC verifier is installed here. POSIX
fork isolates trusted test dependencies; it is not a hostile-code sandbox.
"""
from dataclasses import dataclass
import hashlib
import ipaddress
import json
import mmap
import os
import re
import select
import signal
import ssl
import threading
import time

from research import kraken_probe_corrections as corrections
from research import kraken_spot_diagnostic as diagnostic
from research import kraken_spot_reversal_bridge_prototype as groundwork
from research import kraken_spot_validation_bridge as bridge

HOST = "api.kraken.com"
SYMBOL = "BTC/USD"
NS = 1_000_000_000
DEADLINE_NS = 10 * NS
CLEANUP_NS = 250_000_000
ADDRESS_SPACE_BYTES = 512 * 1024 * 1024
FRAME_CAP = corrections.WIRE_LIMIT + 128
MAP_SIZE = FRAME_CAP + 36
ERRORS = frozenset({"TIMEOUT", "DNS_INVALID", "TLS_FAILURE", "NETWORK_UNAVAILABLE",
                    "PLATFORM_UNSUPPORTED", "WORKER_INVALID", "WORKER_UNREAPED",
                    "IPC_INVALID", "LIMIT_SETUP_FAILED", "MANIFEST_INVALID"})


class Refused(ValueError):
    def __init__(self, reason):
        self.reason = reason
        super().__init__(reason)


def require(ok, reason):
    if not ok:
        raise Refused(reason)


def manifest(as_of):
    require(type(as_of) is int and diagnostic.registry.MIN_TIME+86400 <= as_of < diagnostic.registry.MAX_TIME, "MANIFEST_INVALID")
    requests = (diagnostic.Request(SYMBOL, "/0/public/AssetPairs",
                (("pair", "XBTUSD"), ("aclass_base", "currency"), ("info", "info"))),
            diagnostic.Request(SYMBOL, "/0/public/OHLC",
                (("pair", "XBTUSD"), ("interval", 60), ("since", as_of//3600*3600-86400))))
    for request in requests:
        request.target()
    return requests


class Deadline:
    """Monotonic budget only. Never evidence of independent UTC."""
    def __init__(self, end, clock):
        self.end, self.clock, self.previous = end, clock, None

    def remaining(self):
        now = self.clock()
        require(type(now) is int and 0 <= now < 2**63, "TIMEOUT")
        require(self.previous is None or now >= self.previous, "TIMEOUT")
        self.previous = now
        require(now < self.end, "TIMEOUT")
        return (self.end-now)/NS


def _receive(stream, destination, budget):
    stream.settimeout(budget.remaining())
    n = stream.recv_into(destination, len(destination))
    require(type(n) is int and 0 <= n <= len(destination), "NETWORK_UNAVAILABLE")
    budget.remaining()
    return n


def read_wire(stream, budget):
    """Fixed header allocation BEFORE first read; no buffered HTTP client.

    Read one header byte at a time, then validate header policy before allocating
    the exact bounded body. recv_into avoids peer-controlled Python read sizes.
    OpenSSL/kernel allocation bounds are a separate unresolved runner question.
    """
    header = bytearray(corrections.HEADER_LIMIT)
    used = line = 0
    while True:
        require(used < len(header), "HEADER_LIMIT")
        n = _receive(stream, memoryview(header)[used:used+1], budget)
        require(n == 1, "PREMATURE_EOF")
        used += 1
        line += 1
        require(line <= corrections.LINE_LIMIT, "LINE_LIMIT")
        if header[used-1] == 10:
            require(used >= 2 and header[used-2] == 13, "FRAMING_INVALID")
            line = 0
        if used >= 4 and header[used-4:used] == b"\r\n\r\n":
            break
    head = bytes(memoryview(header)[:used])
    # Reuse the strict header parser. PREMATURE_EOF is the only expected result
    # for a valid nonempty body not yet read; zero-length JSON is refused.
    try:
        corrections.parse_http_fixture(corrections.MemoryReader(head))
    except corrections.Refused as exc:
        require(exc.code.value == "PREMATURE_EOF", exc.code.value)
    else:
        raise Refused("FRAMING_INVALID")
    length = re.search(rb"(?im)^content-length: *([0-9]+) *\r$", head)
    require(length is not None, "FRAMING_INVALID")
    size = int(length[1])
    require(0 < size <= corrections.BODY_LIMIT, "BODY_LIMIT")
    body = bytearray(size)
    pos = 0
    while pos < size:
        n = _receive(stream, memoryview(body)[pos:pos+min(4096, size-pos)], budget)
        require(n > 0, "PREMATURE_EOF")
        pos += n
    extra = bytearray(1)
    require(_receive(stream, extra, budget) == 0, "TRAILING_DATA")
    wire = head + bytes(body)
    corrections.parse_http_fixture(corrections.MemoryReader(wire))
    budget.remaining()
    return wire


def exchange(request, as_of, dependencies, budget):
    """Raw public GET algorithm; dependencies are explicit trusted TEST code.

    No defaults, proxy discovery, retries or fallback. No production provider is
    provided. A worker deadline is still required around blocking DNS/TLS calls.
    """
    require(type(request) is diagnostic.Request and request in manifest(as_of), "MANIFEST_INVALID")
    raw = secured = None
    try:
        dns, socket_factory, context = dependencies
        require(context.check_hostname is True and context.verify_mode == ssl.CERT_REQUIRED
                and context.minimum_version >= ssl.TLSVersion.TLSv1_2, "TLS_FAILURE")
        context.set_alpn_protocols(["http/1.1"])
        budget.remaining()
        addresses = dns(HOST, 443)  # OS worker includes blocked DNS in budget.
        budget.remaining()
        require(type(addresses) is tuple and 1 <= len(addresses) <= 8, "DNS_INVALID")
        # One address only, no retry, including connection failure.
        address = addresses[0]
        require(type(address) is str, "DNS_INVALID")
        try:
            require(ipaddress.ip_address(address).is_global, "DNS_INVALID")
        except ValueError:
            raise Refused("DNS_INVALID") from None
        raw = socket_factory()
        raw.settimeout(budget.remaining())
        raw.connect((address, 443))
        budget.remaining()
        secured = context.wrap_socket(raw, server_hostname=HOST, do_handshake_on_connect=False)
        secured.settimeout(budget.remaining())
        secured.do_handshake()
        budget.remaining()
        require(secured.selected_alpn_protocol() in (None, "http/1.1"), "TLS_FAILURE")
        secured.settimeout(budget.remaining())
        target = request.target()
        secured.sendall(("GET "+target+" HTTP/1.1\r\nHost: "+HOST+
                         "\r\nAccept: application/json\r\nAccept-Encoding: identity\r\nConnection: close\r\n\r\n").encode("ascii"))
        budget.remaining()
        return read_wire(secured, budget)
    except ssl.SSLError:
        raise Refused("TLS_FAILURE") from None
    except (TimeoutError, OSError):
        raise Refused("NETWORK_UNAVAILABLE") from None
    finally:
        for stream in (secured, raw):
            if stream is not None:
                try:
                    stream.close()
                except Exception:
                    pass


def encode_frame(payload):
    require(type(payload) is bytes and 0 < len(payload) <= FRAME_CAP, "IPC_INVALID")
    return len(payload).to_bytes(4, "big") + hashlib.sha256(payload).digest() + payload


def decode_frame(storage):
    require(type(storage) is bytes and len(storage) == MAP_SIZE, "IPC_INVALID")
    size = int.from_bytes(storage[:4], "big")
    require(0 < size <= FRAME_CAP, "IPC_INVALID")
    payload = storage[36:36+size]
    require(hashlib.sha256(payload).digest() == storage[4:36]
            and not any(storage[36+size:]), "IPC_INVALID")
    require(payload[:1] in (b"W", b"E"), "IPC_INVALID")
    if payload[:1] == b"E":
        reason = payload[1:].decode("ascii", errors="strict")
        allowed = ERRORS | {c.value for c in corrections.Code}
        require(reason in allowed, "IPC_INVALID")
        raise Refused(reason)
    require(len(payload)-1 <= corrections.WIRE_LIMIT, "IPC_INVALID")
    return payload[1:]


def _child(write_fd, release_fd, storage, request, as_of, factory, deadline):
    """Close inherited descriptors, apply OS limits, announce ready, wait release."""
    try:
        import resource
        os.setsid()
        # Single-thread POSIX fork only. mmap is inherited, needs no open fd.
        upper = resource.getrlimit(resource.RLIMIT_NOFILE)[0]
        require(type(upper) is int and 0 < upper <= 1_048_576, "LIMIT_SETUP_FAILED")
        keep = sorted((write_fd, release_fd))
        start = 0
        for fd in keep:
            os.closerange(start, fd)
            start = fd+1
        os.closerange(start, upper)
        for name, cap in ((resource.RLIMIT_AS, ADDRESS_SPACE_BYTES),
                          (resource.RLIMIT_NOFILE, 32), (resource.RLIMIT_CORE, 0),
                          (resource.RLIMIT_CPU, 11)):
            soft, hard = resource.getrlimit(name)
            limit = cap if hard == resource.RLIM_INFINITY else min(hard, cap)
            resource.setrlimit(name, (limit, limit))
        budget = Deadline(deadline, time.monotonic_ns)
        budget.remaining()
        os.write(write_fd, b"R")
        require(os.read(release_fd, 1) == b"G", "WORKER_INVALID")
        budget.remaining()
        wire = exchange(request, as_of, factory(request), budget)
        payload = b"W"+wire
    except BaseException as exc:
        reason = exc.reason if isinstance(exc, Refused) else (
            exc.code.value if isinstance(exc, corrections.Refused) else "WORKER_INVALID")
        payload = b"E"+reason.encode("ascii")
    try:
        frame = encode_frame(payload)
        storage[:len(frame)] = frame
    finally:
        os._exit(0)


def _reap(pid, cleanup_deadline):
    while True:
        done, status = os.waitpid(pid, os.WNOHANG)
        if done == pid:
            return status
        if time.monotonic_ns() >= cleanup_deadline:
            raise Refused("WORKER_UNREAPED")
        time.sleep(0.001)


def isolated_exchange(request, as_of, *, dependencies_factory=None, timeout_ns=DEADLINE_NS):
    """Actual POSIX child + fixed anonymous mmap; no pickle or arbitrary IPC.

    This API is offline-only: caller supplies trusted controlled dependencies.
    Native fork/scheduler and kernel kill latency remain target-unverified.
    """
    require(dependencies_factory is not None, "AUTHORIZATION_MISSING")
    require(callable(dependencies_factory) and type(timeout_ns) is int
            and 0 < timeout_ns <= DEADLINE_NS, "MANIFEST_INVALID")
    require(type(request) is diagnostic.Request and request in manifest(as_of), "MANIFEST_INVALID")
    require(os.name == "posix" and hasattr(os, "fork") and threading.active_count() == 1,
            "PLATFORM_UNSUPPORTED")
    start = time.monotonic_ns()  # Includes allocation, pipe construction and fork.
    deadline = start+timeout_ns
    budget = Deadline(deadline, time.monotonic_ns)
    storage = None
    fds = []
    pid = None
    reaped = False
    result = None
    failure = None
    try:
        storage = mmap.mmap(-1, MAP_SIZE)
        ready_r, ready_w = os.pipe()
        fds.extend((ready_r, ready_w))
        release_r, release_w = os.pipe()
        fds.extend((release_r, release_w))
        budget.remaining()
        pid = os.fork()
        if pid == 0:
            _child(ready_w, release_r, storage, request, as_of, dependencies_factory, deadline)
            os._exit(1)
        os.close(ready_w); fds.remove(ready_w)
        os.close(release_r); fds.remove(release_r)
        budget.remaining()
        ready, _, _ = select.select([ready_r], [], [], budget.remaining())
        require(bool(ready), "TIMEOUT")
        require(os.read(ready_r, 1) == b"R", "WORKER_INVALID")
        budget.remaining()  # No release after expired launch/setup.
        os.write(release_w, b"G")
        while True:
            budget.remaining()
            done, status = os.waitpid(pid, os.WNOHANG)
            if done == pid:
                reaped = True
                require(os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0, "WORKER_INVALID")
                result = decode_frame(storage[:])
                budget.remaining()
                break
            select.select([], [], [], min(0.002, budget.remaining()))
    except BaseException as exc:
        failure = exc
    finally:
        if pid is not None and pid > 0 and not reaped:
            try:
                try:
                    os.kill(pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                _reap(pid, time.monotonic_ns()+CLEANUP_NS)
                reaped = True
            except BaseException:
                failure = Refused("WORKER_UNREAPED")
        for fd in fds:
            os.close(fd)
        if storage is not None:
            storage.close()
    if failure is not None:
        if isinstance(failure, (KeyboardInterrupt, SystemExit)):
            raise failure
        if isinstance(failure, Refused):
            raise failure
        raise Refused("WORKER_INVALID") from None
    require(reaped and result is not None, "WORKER_UNREAPED")
    return result


@dataclass(frozen=True)
class SyntheticUTC:
    """Test coordinates only; cannot clear B4 or admit real source data."""
    utc_ns: int
    uncertainty_ns: int = 2*NS


def disabled():
    return {"symbol": SYMBOL, "decision": "BLOCKED", "overall": "HOLD",
            "source": "NOT_ADMITTED", "identity": "UNVERIFIED", "clock": "B4_NO_GO",
            "completed_hourly_candles": 0, "as_of": None, "capture": None,
            "requests": 0, "offline_attempts": 0, "reason": "AUTHORIZATION_MISSING",
            "live_source_admission": "HOLD", "policy": "NO ORDERS"}


def observe_offline(*, dependencies_factory=None, synthetic_utc=None, timeout_ns=DEADLINE_NS):
    """Two-stage TEST integration, no features/candidate engine/live activation."""
    output = disabled()
    if dependencies_factory is None:
        return output
    try:
        require(type(synthetic_utc) is SyntheticUTC
                and type(synthetic_utc.utc_ns) is int
                and type(synthetic_utc.uncertainty_ns) is int
                and 0 <= synthetic_utc.uncertainty_ns <= 2*NS, "CLOCK_UNVERIFIED")
        as_of = (synthetic_utc.utc_ns-synthetic_utc.uncertainty_ns)//NS
        requests = manifest(as_of)
        output.update(source="CONTROLLED_OFFLINE_DEPENDENCIES_NOT_MARKET_DATA", as_of=as_of,
                      capture={"utc_ns":synthetic_utc.utc_ns,"uncertainty_ns":synthetic_utc.uncertainty_ns,
                               "provenance":"SYNTHETIC_TEST_ONLY"})
        for index, request in enumerate(requests):
            output["offline_attempts"] += 1
            started = time.monotonic_ns()
            wire = isolated_exchange(request, as_of, dependencies_factory=dependencies_factory, timeout_ns=timeout_ns)
            parsed = corrections.parse_http_fixture(corrections.MemoryReader(wire))
            require(abs(parsed.date_seconds*NS-synthetic_utc.utc_ns) <= 2*NS, "SERVICE_TIME_CONFLICT")
            if index == 0:
                _, output["identity_ref"] = groundwork._identity_ref(SYMBOL, parsed.payload)
                output["identity"] = "OFFLINE_SCHEMA_PASSED"
            else:
                diagnostic._commitment(parsed.payload, diagnostic.IDENTITIES[SYMBOL][1], as_of,
                                       diagnostic.Stamp(synthetic_utc.utc_ns, 0), parsed.date_seconds)
                capture = {"venue":"kraken","market":"spot","quote":"USD","symbol":SYMBOL,
                           "request_pair":"XBTUSD","interval_minutes":60,"response":parsed.payload}
                validated = bridge.validate_capture(SYMBOL,capture,as_of=as_of,policy=groundwork.POLICY)
                require(validated["decision"]["status"] == "VALIDATED_DATA", "BRIDGE_REFUSED")
                normalized = groundwork._normalize(SYMBOL,capture,validated["decision"],as_of)
                output["completed_hourly_candles"] = len(normalized["bars"])
                output["bridge_ref"] = validated["decision"]
            require(time.monotonic_ns()-started < timeout_ns, "TIMEOUT")
        output.update(decision="OBSERVE_ONLY", reason="OFFLINE_BOUNDARY_PASSED_LIVE_HOLD")
    except Exception as exc:
        reason = exc.reason if isinstance(exc, Refused) else (
            exc.code.value if isinstance(exc, corrections.Refused) else (
                exc.reason.value if isinstance(exc, diagnostic.Refused) else str(exc)
                if isinstance(exc, groundwork.Refused) else "WORKER_INVALID"))
        output.update(decision="BLOCKED", reason=reason, completed_hourly_candles=0)
        output.pop("bridge_ref",None)
    return output


def main():
    import argparse
    argparse.ArgumentParser(description="Disabled offline transport boundary; no live options").parse_args()
    print(json.dumps(disabled(),sort_keys=True))
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
