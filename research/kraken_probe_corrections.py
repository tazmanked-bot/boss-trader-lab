"""Isolated offline B1-B3 prototypes. No real client, clock or activation path.

Injected actions/clock/job/stage evaluators are trusted test code, not a sandbox.
The parser accepts a sealed in-memory byte fixture, never a socket/file stream.
"""

from dataclasses import dataclass, field
from enum import Enum
import multiprocessing
import re
import threading

from research import kraken_spot_diagnostic as legacy
from research import spot_refusal_registry as registry


VERSION = "kraken-offline-corrections-v1"
NS = 1_000_000_000
DEADLINE_NS = 10 * NS
HEADER_LIMIT = 8192
LINE_LIMIT = 1024
HEADER_COUNT = 64
BODY_LIMIT = 262144
WIRE_LIMIT = HEADER_LIMIT + BODY_LIMIT


class Code(str, Enum):
    AUTHORIZATION_MISSING = "AUTHORIZATION_MISSING"
    CONTEXT_INVALID = "CONTEXT_INVALID"
    CLOCK_UNVERIFIED = "CLOCK_UNVERIFIED"
    CLOCK_CONFLICT = "CLOCK_CONFLICT"
    TIMEOUT = "TIMEOUT"
    PLATFORM_UNSUPPORTED = "PLATFORM_UNSUPPORTED"
    WORKER_INVALID = "WORKER_INVALID"
    WORKER_UNREAPED = "WORKER_UNREAPED"
    COMPLETED = "COMPLETED"
    HEADER_LIMIT = "HEADER_LIMIT"
    LINE_LIMIT = "LINE_LIMIT"
    HEADER_INVALID = "HEADER_INVALID"
    FRAMING_INVALID = "FRAMING_INVALID"
    INTERIM_REFUSED = "INTERIM_REFUSED"
    REDIRECT_REFUSED = "REDIRECT_REFUSED"
    HTTP_REFUSED = "HTTP_REFUSED"
    CONTENT_INVALID = "CONTENT_INVALID"
    COMPRESSION_REFUSED = "COMPRESSION_REFUSED"
    AMBIGUOUS_FRAMING = "AMBIGUOUS_FRAMING"
    UNSUPPORTED_TRANSFER = "UNSUPPORTED_TRANSFER"
    BODY_LIMIT = "BODY_LIMIT"
    PREMATURE_EOF = "PREMATURE_EOF"
    TRAILING_DATA = "TRAILING_DATA"
    JSON_INVALID = "JSON_INVALID"
    API_ERROR = "API_ERROR"
    ALIAS_CHANGED = "ALIAS_CHANGED"
    IDENTITY_UNVERIFIED = "IDENTITY_UNVERIFIED"
    NETWORK_UNAVAILABLE = "NETWORK_UNAVAILABLE"
    TLS_FAILURE = "TLS_FAILURE"
    SERVICE_TIME_CONFLICT = "SERVICE_TIME_CONFLICT"
    COMMITMENT_CONFLICT = "COMMITMENT_CONFLICT"
    BRIDGE_REFUSED = "BRIDGE_REFUSED"
    STAGE_PASSED = "STAGE_PASSED"


class Refused(ValueError):
    def __init__(self, code):
        self.code = code if type(code) is Code else Code.WORKER_INVALID
        super().__init__(self.code.value)


def _now(clock):
    value = clock.monotonic_ns()
    if type(value) is not int or not 0 <= value < 2 ** 63:
        raise Refused(Code.CLOCK_CONFLICT)
    return value


def _active(clock, deadline, cancelled=False, previous=None):
    now = _now(clock)
    if previous is not None and now < previous:
        raise Refused(Code.CLOCK_CONFLICT)
    if cancelled or now >= deadline:
        raise Refused(Code.TIMEOUT)
    return now


_CHILD_CODES = {Code.COMPLETED: 1, Code.TIMEOUT: 2, Code.CLOCK_CONFLICT: 3, Code.WORKER_INVALID: 4}


def _released_worker(request, action, clock, deadline, ready, release, cancel, status, bootstrap):
    try:
        before = _active(clock, deadline, cancel.is_set())
        if bootstrap is not None:
            bootstrap()  # Offline startup-block fixture only, never a client.
        before = _active(clock, deadline, cancel.is_set(), previous=before)
        ready.set()
        release.wait()  # Parent deadline kills a worker that never gets released.
        before = _active(clock, deadline, cancel.is_set(), previous=before)
        action(request)  # First injected operation, representing pre-DNS entry.
        _active(clock, deadline, cancel.is_set(), previous=before)
        status.value = _CHILD_CODES[Code.COMPLETED]
    except Refused as exc:
        status.value = _CHILD_CODES.get(exc.code, _CHILD_CODES[Code.WORKER_INVALID])
    except BaseException:
        status.value = _CHILD_CODES[Code.WORKER_INVALID]


class GatedProcessJob:
    """Single-thread POSIX offline worker, initially paused; no network provider."""
    def __init__(self, request, action, clock, deadline, *, bootstrap=None):
        if (threading.active_count() != 1 or "fork" not in multiprocessing.get_all_start_methods()
                or getattr(clock, "shared_for_fork", False) is not True):
            raise Refused(Code.PLATFORM_UNSUPPORTED)
        context = multiprocessing.get_context("fork")
        self.ready_event, self.release_event, self.cancel_event = (context.Event() for _ in range(3))
        self.status = context.RawValue("i", 0)
        self.process = context.Process(target=_released_worker,
            args=(request, action, clock, deadline, self.ready_event, self.release_event,
                  self.cancel_event, self.status, bootstrap), daemon=True)
        self.started = self.reaped = False

    def start(self):
        self.started = True  # Cleanup must also handle a partial native start.
        self.process.start()

    def ready(self):
        return self.ready_event.is_set()

    def release(self):
        self.release_event.set()

    def cancel(self):
        self.cancel_event.set()

    def alive(self):
        return self.process.is_alive()

    def wait(self, seconds):
        self.process.join(timeout=seconds)

    def result(self):
        if self.process.exitcode != 0:
            raise Refused(Code.WORKER_INVALID)
        return next((code for code, value in _CHILD_CODES.items() if value == self.status.value), Code.WORKER_INVALID)

    def kill(self):
        self.process.kill()

    def reap(self):
        self.process.join(timeout=0.25)
        if self.process.is_alive():
            return False
        self.process.close()
        self.reaped = True
        return True

    def close_unstarted(self):
        self.process.close()


def supervise_offline(*, request=None, action=None, clock=None, job_factory=GatedProcessJob, deadline_ns=None):
    """B1: check before construction/start/release; child checks same deadline.

    Native factory/start and kernel scheduling are not preemptible here: these
    gates prevent release of an expired action, not a hard wall-time guarantee.
    """
    if action is None:
        return {"overall": "HOLD", "reason": Code.AUTHORIZATION_MISSING.value, "started": False, "released": False}
    job, started, released, cleanup = None, False, False, "UNSTARTED"
    reason = Code.WORKER_INVALID
    try:
        if type(request) is not legacy.Request:
            raise Refused(Code.CONTEXT_INVALID)
        request.target()
        if clock is None:
            raise Refused(Code.CLOCK_UNVERIFIED)
        begin = _now(clock)
        deadline = begin + DEADLINE_NS if deadline_ns is None else deadline_ns
        if type(deadline) is not int or not 0 <= deadline < 2 ** 63 or deadline > begin + DEADLINE_NS:
            raise Refused(Code.CONTEXT_INVALID)
        previous = _active(clock, deadline)
        job = job_factory(request, action, clock, deadline)
        previous = _active(clock, deadline, previous=previous)
        started = True
        job.start()  # Must start PAUSED. Slow start never grants action release.
        previous = _active(clock, deadline, previous=previous)
        while True:
            previous = _active(clock, deadline, previous=previous)
            if not job.alive():
                reason = job.result()
                previous = _active(clock, deadline, previous=previous)
                if type(reason) is not Code or reason not in _CHILD_CODES:
                    raise Refused(Code.WORKER_INVALID)
                if not released and reason == Code.COMPLETED:
                    raise Refused(Code.WORKER_INVALID)
                break
            if not released and job.ready():
                previous = _active(clock, deadline, previous=previous)
                job.release()
                released = True
            else:
                job.wait(min((deadline - previous) / NS, 0.01))
    except Refused as exc:
        reason = exc.code
    except legacy.Refused:
        reason = Code.CONTEXT_INVALID
    except Exception:
        reason = Code.WORKER_INVALID
    finally:
        if job is not None:
            try:
                job.cancel()
                if started:
                    if job.alive():
                        job.kill()
                    cleanup = "REAPED" if job.reap() else "UNREAPED"
                    if cleanup == "UNREAPED":
                        reason = Code.WORKER_UNREAPED
                else:
                    job.close_unstarted()
            except Exception:
                cleanup, reason = "UNREAPED", Code.WORKER_UNREAPED
    return {"overall": "HOLD", "reason": reason.value, "started": started,
            "released": released, "cleanup": cleanup}


class MemoryReader:
    """Sealed byte-fixture source. No socket/file adapter or arbitrary read hook."""
    __slots__ = ("_wire", "position", "max_request")
    def __init__(self, wire):
        if type(wire) is not bytes:
            raise Refused(Code.CONTEXT_INVALID)
        self._wire, self.position, self.max_request = wire, 0, 0

    @property
    def remaining(self):
        return len(self._wire) - self.position

    def read(self, count):
        if type(count) is not int or not 0 < count <= 4096:
            raise Refused(Code.CONTEXT_INVALID)
        self.max_request = max(self.max_request, count)
        data = self._wire[self.position:self.position + count]
        self.position += len(data)
        return data


@dataclass(frozen=True)
class ParsedFixture:
    date_seconds: int
    payload: dict = field(repr=False)


def _line(reader, consumed):
    line = bytearray()
    while True:
        char = reader.read(1)
        if not char:
            raise Refused(Code.PREMATURE_EOF)
        consumed += 1
        if consumed > HEADER_LIMIT:
            raise Refused(Code.HEADER_LIMIT)
        if len(line) + 1 > LINE_LIMIT:
            raise Refused(Code.LINE_LIMIT)
        line.extend(char)
        if char == b"\n":
            if len(line) < 2 or line[-2:] != b"\r\n":
                raise Refused(Code.FRAMING_INVALID)
            return bytes(line[:-2]), consumed
        if len(line) > 1 and line[-2] == 13:
            raise Refused(Code.FRAMING_INVALID)


def parse_http_fixture(reader):
    """B2 narrow HTTP/1.1 JSON profile, bounded before header materialization.

    No interim, transfer coding/chunking, compression, obs-fold, duplicate fields,
    pipeline or EOF-framed body. Unsupported valid HTTP is a deliberate HOLD.
    The caller-owned input bytes already exist; this is not a real stream driver.
    """
    if type(reader) is not MemoryReader:
        raise Refused(Code.CONTEXT_INVALID)
    if reader.position != 0 or reader.remaining > WIRE_LIMIT:
        raise Refused(Code.BODY_LIMIT)
    status, consumed = _line(reader, 0)
    match = re.fullmatch(rb"HTTP/1\.1 ([1-5][0-9]{2}) [\x20-\x7e]*", status)
    if match is None:
        raise Refused(Code.FRAMING_INVALID)
    code = int(match[1])
    if code < 200:
        raise Refused(Code.INTERIM_REFUSED)
    if 300 <= code < 400:
        raise Refused(Code.REDIRECT_REFUSED)
    if code != 200:
        raise Refused(Code.HTTP_REFUSED)
    headers, seen = {}, set()
    for count in range(HEADER_COUNT + 1):
        line, consumed = _line(reader, consumed)
        if not line:
            break
        if count >= HEADER_COUNT:
            raise Refused(Code.HEADER_LIMIT)
        if b":" not in line or line.startswith((b" ", b"\t")):
            raise Refused(Code.HEADER_INVALID)
        name, value = line.split(b":", 1)
        if (not 1 <= len(name) <= 64 or not re.fullmatch(rb"[!#$%&'*+.^_`|~0-9A-Za-z-]+", name)
                or any(c < 32 or c > 126 for c in value)):
            raise Refused(Code.HEADER_INVALID)
        key = name.decode("ascii").lower()
        if key in seen:
            raise Refused(Code.HEADER_INVALID)
        seen.add(key)
        if key in {"date", "content-type", "content-encoding", "transfer-encoding", "content-length"}:
            headers[key] = value.strip(b" ").decode("ascii")
    else:
        raise Refused(Code.HEADER_LIMIT)
    if "transfer-encoding" in headers:
        raise Refused(Code.AMBIGUOUS_FRAMING if "content-length" in headers else Code.UNSUPPORTED_TRANSFER)
    if headers.get("content-encoding", "identity").lower() != "identity":
        raise Refused(Code.COMPRESSION_REFUSED)
    if not re.fullmatch(r"application/json(?:;\s*charset=utf-8)?", headers.get("content-type", "").lower()):
        raise Refused(Code.CONTENT_INVALID)
    try:
        date = legacy._date(headers.get("date"))
    except legacy.Refused:
        raise Refused(Code.CLOCK_UNVERIFIED) from None
    length = headers.get("content-length", "")
    if not re.fullmatch(r"0|[1-9][0-9]{0,5}", length):
        raise Refused(Code.FRAMING_INVALID)
    size = int(length)
    if size > BODY_LIMIT:
        raise Refused(Code.BODY_LIMIT)
    if reader.remaining < size:
        raise Refused(Code.PREMATURE_EOF)
    if reader.remaining > size:
        raise Refused(Code.TRAILING_DATA)
    body = bytearray()
    while len(body) < size:
        data = reader.read(min(4096, size - len(body)))
        if not data:
            raise Refused(Code.PREMATURE_EOF)
        body.extend(data)
    try:
        payload = legacy._strict_json(bytes(body))
    except legacy.Refused:
        raise Refused(Code.JSON_INVALID) from None
    if type(payload) is not dict:
        raise Refused(Code.JSON_INVALID)
    return ParsedFixture(date, payload)


@dataclass(frozen=True)
class StageResult:
    code: Code


def _should_stop(code):
    return code != Code.STAGE_PASSED


def coordinate_global_stop_offline(stage_evaluator=None):
    """B3 explicit global-stop control-flow contract, not a transport/validator.

    Trusted injected evaluator performs a stage's offline checks; STAGE_PASSED
    is not proof of real identity/clock/data or an authorization credential.
    """
    if stage_evaluator is None:
        return {"overall": "HOLD", "reason": Code.AUTHORIZATION_MISSING.value, "attempts": []}
    attempts = []
    for symbol in registry.SYMBOLS:
        for stage in ("IDENTITY", "OHLC"):
            try:
                result = stage_evaluator(symbol, stage)
                if type(result) is not StageResult or type(result.code) is not Code or result.code == Code.COMPLETED:
                    raise Refused(Code.WORKER_INVALID)
                code = result.code
            except Exception:
                code = Code.WORKER_INVALID
            attempts.append({"symbol": symbol, "stage": stage, "reason": code.value})
            if _should_stop(code):
                return {"overall": "HOLD", "reason": code.value, "attempts": attempts}
    return {"overall": "HOLD", "reason": "ALL_STAGE_CHECKS_PASSED", "attempts": attempts}


def main():
    print(registry.canonical_json({"version": VERSION, "overall": "HOLD",
                                  "reason": Code.AUTHORIZATION_MISSING.value, "requests": 0}))
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
