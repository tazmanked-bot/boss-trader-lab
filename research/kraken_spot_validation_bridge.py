"""Offline supplied Kraken-shaped OHLC fixtures -> unchanged refusal registry.

No transport, wall clock, strategy, signal, persistence or execution capability.
Capture metadata is an assertion, not verified exchange provenance. See report.
"""

from decimal import Decimal, localcontext
from enum import Enum
import hashlib
import json
import math
import re

from research import spot_refusal_registry as registry


VERSION = "kraken-spot-bridge-v1"
PAIRS = {
    "BTC/USD": ("XBTUSD", ("XXBTZUSD", "XBTUSD")),
    "XRP/USD": ("XRPUSD", ("XXRPZUSD", "XRPUSD")),
    "SOL/USD": ("SOLUSD", ("SOLUSD",)),
}
DECIMAL_TEXT = re.compile(r"-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?", re.ASCII)
LIMIT = Decimal("1e100")
ROUNDING_LIMIT = Decimal("1e-15")


class Code(str, Enum):
    PARSED = "PARSED"
    CONTEXT_INVALID = "CONTEXT_INVALID"
    SOURCE_MISSING = "SOURCE_MISSING"
    JSON_INVALID = "JSON_INVALID"
    SIZE_LIMIT = "SIZE_LIMIT"
    CAPTURE_INVALID = "CAPTURE_INVALID"
    IDENTITY_MISMATCH = "IDENTITY_MISMATCH"
    SOURCE_SCHEMA = "SOURCE_SCHEMA"
    SOURCE_API_ERROR = "SOURCE_API_ERROR"
    PAIR_MISMATCH = "PAIR_MISMATCH"
    CURSOR_INVALID = "CURSOR_INVALID"
    ROW_SCHEMA = "ROW_SCHEMA"
    TIMESTAMP_INVALID = "TIMESTAMP_INVALID"
    NUMERIC_INVALID = "NUMERIC_INVALID"
    PRICE_BOUNDS = "PRICE_BOUNDS"
    COUNT_INVALID = "COUNT_INVALID"
    PRECISION_LOSS = "PRECISION_LOSS"


class _Rejected(ValueError):
    def __init__(self, code):
        self.code = code


def _output(decision, code, eligible=()):
    # Exact eligible decimal fields (including VWAP/count) are covered separately
    # from the registry's normalized OHLCV evidence. Never include raw exceptions,
    # cursor, excluded rows, or full source payload in either reference.
    evidence = {"bridge_version": VERSION, "bridge_code": code.value,
                "decision": decision, "eligible_source_rows": eligible}
    return {"bridge_version": VERSION, "source_claim": "provided_kraken_shaped_fixture",
            "bridge_code": code.value, "decision": decision,
            "evidence_ref": "sha256:" + hashlib.sha256(
                registry.canonical_json(evidence).encode("ascii")).hexdigest()}


def _failure(symbol, as_of, policy, code):
    return _output(registry.refusal(symbol, as_of=as_of, policy=policy,
                                   reason=registry.Reason.DATA_UNAVAILABLE), code)


def _valid_epoch(value, *, aligned):
    return (type(value) is int and registry.MIN_TIME <= value < registry.MAX_TIME
            and (not aligned or value % registry.HOUR == 0))


def _number(text, *, volume=False):
    # Deliberately a strict subset of decimal text, not float()/strip() guessing.
    if type(text) is not str or not 1 <= len(text) <= 128 or not DECIMAL_TEXT.fullmatch(text):
        raise _Rejected(Code.NUMERIC_INVALID)
    value = Decimal(text)
    if value.is_signed() or value > LIMIT or (not volume and value == 0):
        raise _Rejected(Code.NUMERIC_INVALID)
    return value


def _floats(values):
    floats = [float(v) for v in values]
    with localcontext() as context:
        context.prec = 200
        for exact, approximate in zip(values, floats):
            if (not math.isfinite(approximate) or (exact != 0 and approximate == 0)
                    or abs(Decimal.from_float(approximate) - exact) > abs(exact) * ROUNDING_LIMIT):
                raise _Rejected(Code.PRECISION_LOSS)
    # Distinct source prices must not collapse into the same binary float.
    for i in range(5):
        for j in range(i):
            if values[i] != values[j] and floats[i] == floats[j]:
                raise _Rejected(Code.PRECISION_LOSS)
    return floats


def validate_capture(symbol, capture, *, as_of, policy=None):
    """Validate one supplied capture with exact metadata and response schema.

    Policy is the registry's version/future_mode dict, defaulting to reject.
    as_of mode filters ineligible rows after row shape/time checks but before
    price/VWAP/volume/count parsing. Strict mode returns the existing registry's
    CANDLE_NOT_CLOSED refusal; no last-row exception or repair.
    """
    policy = dict(registry.DEFAULT_POLICY) if policy is None else policy
    gate = registry.refusal(symbol, as_of=as_of, policy=policy,
                            reason=registry.Reason.DATA_UNAVAILABLE)
    if gate["reason_code"] != "DATA_UNAVAILABLE":
        return _output(gate, Code.CONTEXT_INVALID)
    if capture is None:
        return _failure(symbol, as_of, policy, Code.SOURCE_MISSING)
    try:
        # Python objects are a fixture convenience, not arbitrary-object execution
        # isolation. JSON is the supported serialized input boundary.
        encoded = registry.canonical_json(capture)
        if len(encoded) > registry.MAX_JSON_BYTES:
            raise _Rejected(Code.SIZE_LIMIT)
        fields = {"venue", "market", "quote", "symbol", "request_pair", "interval_minutes", "response"}
        if type(capture) is not dict or set(capture) != fields:
            raise _Rejected(Code.CAPTURE_INVALID)
        expected = {"venue": "kraken", "market": "spot", "quote": "USD", "symbol": symbol,
                    "request_pair": PAIRS[symbol][0]}
        if any(type(capture[k]) is not str or capture[k] != v for k, v in expected.items()):
            raise _Rejected(Code.IDENTITY_MISMATCH)
        if type(capture["interval_minutes"]) is not int or capture["interval_minutes"] != 60:
            raise _Rejected(Code.IDENTITY_MISMATCH)
        response = capture["response"]
        if type(response) is not dict or set(response) != {"error", "result"}:
            raise _Rejected(Code.SOURCE_SCHEMA)
        if type(response["error"]) is not list:
            raise _Rejected(Code.SOURCE_SCHEMA)
        if response["error"]:
            raise _Rejected(Code.SOURCE_API_ERROR)
        result = response["result"]
        if type(result) is not dict or "last" not in result or len(result) != 2:
            raise _Rejected(Code.SOURCE_SCHEMA)
        pair = next(k for k in result if k != "last")
        if type(pair) is not str or pair not in PAIRS[symbol][1]:
            raise _Rejected(Code.PAIR_MISMATCH)
        if not _valid_epoch(result["last"], aligned=False):
            raise _Rejected(Code.CURSOR_INVALID)
        rows = result[pair]
        if type(rows) is not list or len(rows) > registry.MAX_BARS:
            raise _Rejected(Code.SIZE_LIMIT if type(rows) is list else Code.ROW_SCHEMA)
        bars, eligible = [], []
        for row in rows:
            if type(row) is not list or len(row) != 8:
                raise _Rejected(Code.ROW_SCHEMA)
            stamp = row[0]
            if not _valid_epoch(stamp, aligned=True):
                raise _Rejected(Code.TIMESTAMP_INVALID)
            if stamp + registry.HOUR > as_of:
                if policy["future_mode"] == "as_of":
                    continue
                # No numeric value from an uncommitted/future row enters evidence.
                return _output(registry.refusal(symbol, as_of=as_of, policy=policy,
                               reason=registry.Reason.CANDLE_NOT_CLOSED), Code.PARSED)
            numbers = [_number(v, volume=(index == 5)) for index, v in enumerate(row[1:7])]
            op, high, low, close, vwap, volume = numbers
            if not low <= min(op, close, vwap) <= max(op, close, vwap) <= high:
                raise _Rejected(Code.PRICE_BOUNDS)
            if type(row[7]) is not int or not 0 <= row[7] <= 2 ** 53 - 1:
                raise _Rejected(Code.COUNT_INVALID)
            fop, fhigh, flow, fclose, _, fvolume = _floats(numbers)
            bars.append({"open_time": stamp, "open": fop, "high": fhigh, "low": flow,
                         "close": fclose, "volume": fvolume})
            eligible.append(list(row))
        envelope = {"symbol": symbol, **registry.IDENTITY,
                    "rules": {"require_spot": True, "require_non_spot": False}, "bars": bars}
        decision = registry.validate_symbol(symbol, envelope, as_of=as_of, policy=policy)
        return _output(decision, Code.PARSED, eligible)
    except _Rejected as exc:
        return _failure(symbol, as_of, policy, exc.code)
    except (ValueError, TypeError, OverflowError, RecursionError, UnicodeError):
        return _failure(symbol, as_of, policy, Code.JSON_INVALID)


def validate_captures(captures, *, as_of, policy=None):
    """Fixed three-symbol independent report, without selection or aggregate PASS."""
    if type(captures) is not dict or any(type(k) is not str or k not in PAIRS for k in captures):
        return {s: _failure(s, as_of, policy, Code.CAPTURE_INVALID) for s in registry.SYMBOLS}
    return {s: validate_capture(s, captures.get(s), as_of=as_of, policy=policy) for s in registry.SYMBOLS}


def validate_capture_json(symbol, text, *, as_of, policy=None):
    """Bounded strict JSON; duplicate keys and nonfinite literals always refuse."""
    def no_constant(_):
        raise ValueError

    def unique(pairs):
        obj = {}
        for key, value in pairs:
            if key in obj:
                raise ValueError
            obj[key] = value
        return obj

    try:
        if type(text) is not str:
            raise ValueError
        if len(text) > registry.MAX_JSON_BYTES or len(text.encode("utf-8")) > registry.MAX_JSON_BYTES:
            return _failure(symbol, as_of, policy, Code.SIZE_LIMIT)
        capture = json.loads(text, parse_constant=no_constant, object_pairs_hook=unique)
    except (ValueError, TypeError, OverflowError, RecursionError, UnicodeError):
        return _failure(symbol, as_of, policy, Code.JSON_INVALID)
    return validate_capture(symbol, capture, as_of=as_of, policy=policy)
