"""Optional, pure stdlib validation of synthetic Kraken spot hourly fixtures.

No collector, strategy, signal, persistence, clock read, or execution authority.
See docs/BOSS-TRADER-OFFLINE-REFUSAL-009.md for the two time contracts.
"""

from datetime import datetime, timezone
from enum import Enum
import hashlib
import json
import math


SYMBOLS = ("BTC/USD", "XRP/USD", "SOL/USD")
VERSION = "spot-refusal-v1"
HOUR = 3600
WINDOW = 21
MAX_BARS = 512
MAX_JSON_BYTES = 262144
MIN_TIME = 946684800  # Supported epoch seconds: 2000 through 2099 UTC.
MAX_TIME = 4102444800
DEFAULT_POLICY = {"version": VERSION, "future_mode": "reject"}
IDENTITY = {"venue": "kraken", "market": "spot", "quote": "USD", "timeframe": "1h"}


class Reason(str, Enum):
    MALFORMED_DATA = "MALFORMED_DATA"
    MARKET_MISMATCH = "MARKET_MISMATCH"
    INVALID_VALUE = "INVALID_VALUE"
    TIMESTAMP_INVALID = "TIMESTAMP_INVALID"
    TIME_UNIT_MISMATCH = "TIME_UNIT_MISMATCH"
    DUPLICATE_TIMESTAMP = "DUPLICATE_TIMESTAMP"
    TIMESTAMP_ORDER = "TIMESTAMP_ORDER"
    TIMESTAMP_GAP = "TIMESTAMP_GAP"
    CANDLE_NOT_CLOSED = "CANDLE_NOT_CLOSED"
    WARMUP_INCOMPLETE = "WARMUP_INCOMPLETE"
    DATA_STALE = "DATA_STALE"
    RULE_CONFLICT = "RULE_CONFLICT"
    POLICY_REJECTED = "POLICY_REJECTED"
    CONFIG_INVALID = "CONFIG_INVALID"
    DATA_UNAVAILABLE = "DATA_UNAVAILABLE"
    UNKNOWN_REASON = "UNKNOWN_REASON"


DETAIL = {
    Reason.MALFORMED_DATA: "Payload does not match the fixture schema.",
    Reason.MARKET_MISMATCH: "Fixture identity differs from the required spot market.",
    Reason.INVALID_VALUE: "An eligible OHLCV value is invalid.",
    Reason.TIMESTAMP_INVALID: "Time must be aligned integer UTC epoch seconds.",
    Reason.TIME_UNIT_MISMATCH: "Timestamp is outside the supported seconds range; units are not converted.",
    Reason.DUPLICATE_TIMESTAMP: "An eligible timestamp is duplicated.",
    Reason.TIMESTAMP_ORDER: "Eligible bars are not strictly ordered.",
    Reason.TIMESTAMP_GAP: "Eligible hourly bars are not contiguous.",
    Reason.CANDLE_NOT_CLOSED: "Strict mode refuses unfinished or future candles.",
    Reason.WARMUP_INCOMPLETE: "Fewer than 21 closed hourly bars are available.",
    Reason.DATA_STALE: "This symbol's latest close is more than three hours old.",
    Reason.RULE_CONFLICT: "Mutually exclusive fixture rules are both required.",
    Reason.POLICY_REJECTED: "Only the required spot-only fixture policy is supported.",
    Reason.CONFIG_INVALID: "Policy fields or values are unsupported.",
    Reason.DATA_UNAVAILABLE: "No fixture payload was supplied.",
    Reason.UNKNOWN_REASON: "An unregistered refusal reason was supplied.",
}


def canonical_json(value):
    """Strict deterministic JSON text; raises for NaN/Infinity/unsupported values."""
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
                      allow_nan=False)


def _time_code(value):
    if type(value) is not int:
        return Reason.TIMESTAMP_INVALID
    if not MIN_TIME <= value < MAX_TIME:
        return Reason.TIME_UNIT_MISMATCH
    if value % HOUR:
        return Reason.TIMESTAMP_INVALID
    return None


def _policy(policy):
    return (type(policy) is dict and set(policy) == {"version", "future_mode"}
            and type(policy["version"]) is str and policy["version"] == VERSION
            and type(policy["future_mode"]) is str
            and policy["future_mode"] in ("reject", "as_of"))


def _result(symbol, as_of, policy, code, prefix):
    # Only trusted fixed vocabulary and validated data enter evidence or details.
    context = {**IDENTITY, "symbol": symbol if type(symbol) is str and symbol in SYMBOLS else None,
               "as_of_utc": (datetime.fromtimestamp(as_of, timezone.utc).isoformat().replace("+00:00", "Z")
                             if _time_code(as_of) is None else None),
               "policy_version": VERSION if _policy(policy) else "unsupported",
               "future_mode": policy["future_mode"] if _policy(policy) else None}
    code_text = code.value if code is not None else None
    evidence = canonical_json({**context, "reason_code": code_text, "validated_prefix": prefix})
    return {**context, "status": "REFUSED" if code is not None else "VALIDATED_DATA",
            "reason_code": code_text,
            "detail": DETAIL[code] if code is not None else "Synthetic data checks passed; no signal or authorization.",
            "evidence_ref": "sha256:" + hashlib.sha256(evidence.encode("ascii")).hexdigest()}


def refusal(symbol, *, as_of, reason, policy=None):
    """Registry lookup: unknown codes always produce a registered refusal."""
    policy = dict(DEFAULT_POLICY) if policy is None else policy
    code = next((r for r in Reason if type(reason) in (str, Reason) and reason == r),
                Reason.UNKNOWN_REASON)
    if not _policy(policy):
        code = Reason.CONFIG_INVALID
    elif _time_code(as_of) is not None:
        code = _time_code(as_of)
    elif type(symbol) is not str or symbol not in SYMBOLS:
        code = Reason.MARKET_MISMATCH
    return _result(symbol, as_of, policy, code, [])


def validate_symbol(symbol, payload, *, as_of, policy=None):
    """Validate every eligible bar of one supplied synthetic fixture, without I/O.

    Strict mode (default) refuses all future/unfinished bars. Explicit as_of mode
    ignores OHLCV of structurally valid rows whose open+3600 exceeds as_of.
    Every row still needs exact fields and a valid seconds/aligned timestamp.
    Eligible corrupt rows are never dropped. No sorting, filling, or fallback.
    """
    policy = dict(DEFAULT_POLICY) if policy is None else policy
    prefix = []

    def finish(code):
        return _result(symbol, as_of, policy, code, prefix)

    if not _policy(policy):
        return finish(Reason.CONFIG_INVALID)
    if _time_code(as_of) is not None:
        return finish(_time_code(as_of))
    if type(symbol) is not str or symbol not in SYMBOLS:
        return finish(Reason.MARKET_MISMATCH)
    if payload is None:
        return finish(Reason.DATA_UNAVAILABLE)
    fields = {"symbol", "venue", "market", "quote", "timeframe", "rules", "bars"}
    if type(payload) is not dict or set(payload) != fields:
        return finish(Reason.MALFORMED_DATA)
    if any(type(payload[k]) is not str or payload[k] != v
           for k, v in {**IDENTITY, "symbol": symbol}.items()):
        return finish(Reason.MARKET_MISMATCH)
    rules = payload["rules"]
    if (type(rules) is not dict or set(rules) != {"require_spot", "require_non_spot"}
            or any(type(v) is not bool for v in rules.values())):
        return finish(Reason.CONFIG_INVALID)
    if rules["require_spot"] and rules["require_non_spot"]:
        return finish(Reason.RULE_CONFLICT)
    if not rules["require_spot"] or rules["require_non_spot"]:
        return finish(Reason.POLICY_REJECTED)
    bars = payload["bars"]
    if type(bars) is not list or len(bars) > MAX_BARS:
        return finish(Reason.MALFORMED_DATA)
    seen = set()
    previous = None
    for bar in bars:
        if type(bar) is not dict or set(bar) != {"open_time", "open", "high", "low", "close", "volume"}:
            return finish(Reason.MALFORMED_DATA)
        stamp = bar["open_time"]
        if _time_code(stamp) is not None:
            return finish(_time_code(stamp))
        if stamp + HOUR > as_of:
            if policy["future_mode"] == "as_of":
                continue
            return finish(Reason.CANDLE_NOT_CLOSED)
        if stamp in seen:
            return finish(Reason.DUPLICATE_TIMESTAMP)
        if previous is not None:
            if stamp < previous:
                return finish(Reason.TIMESTAMP_ORDER)
            if stamp - previous != HOUR:
                return finish(Reason.TIMESTAMP_GAP)
        for key in ("open", "high", "low", "close", "volume"):
            value = bar[key]
            # Bound numeric representation too: huge integers must not overflow
            # float conversion or leak large data into diagnostic evidence.
            if type(value) not in (int, float) or abs(value) > 1e100 or not math.isfinite(value):
                return finish(Reason.INVALID_VALUE)
            if value < 0 or (key != "volume" and value == 0):
                return finish(Reason.INVALID_VALUE)
        if not bar["low"] <= min(bar["open"], bar["close"]) <= max(bar["open"], bar["close"]) <= bar["high"]:
            return finish(Reason.INVALID_VALUE)
        prefix.append(dict(bar))
        seen.add(stamp)
        previous = stamp
    if len(prefix) < WINDOW:
        return finish(Reason.WARMUP_INCOMPLETE)
    if as_of - (previous + HOUR) > 3 * HOUR:
        return finish(Reason.DATA_STALE)
    return finish(None)


def validate_symbols(payloads, *, as_of, policy=None):
    """Fixed three-symbol report; missing symbols refuse independently, no rank."""
    if type(payloads) is not dict or any(type(k) is not str or k not in SYMBOLS for k in payloads):
        return {s: refusal(s, as_of=as_of, reason=Reason.MALFORMED_DATA, policy=policy) for s in SYMBOLS}
    return {s: validate_symbol(s, payloads.get(s), as_of=as_of, policy=policy) for s in SYMBOLS}


def validate_json(symbol, text, *, as_of, policy=None):
    """Bounded strict JSON entry point: duplicate keys/nonfinite tokens refuse.

    Error details never include parser messages or raw input. Invalid JSON is
    refused even when a nonfinite token happens to be in a future row.
    """
    def reject_constant(_):
        raise ValueError

    def unique_object(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError
            result[key] = value
        return result

    try:
        if type(text) is not str or len(text) > MAX_JSON_BYTES or len(text.encode("utf-8")) > MAX_JSON_BYTES:
            raise ValueError
        payload = json.loads(text, parse_constant=reject_constant, object_pairs_hook=unique_object)
        # JSON's 1e999 is parsed as infinity without invoking parse_constant.
        canonical_json(payload)
    except (ValueError, TypeError, OverflowError, RecursionError, UnicodeError):
        return refusal(symbol, as_of=as_of, reason=Reason.MALFORMED_DATA, policy=policy)
    return validate_symbol(symbol, payload, as_of=as_of, policy=policy)
