"""Static synthetic Kraken-shaped fixture groundwork; no live transport/admission.

Proposed public-source typing is preserved. This module never calls the candidate
engine or relabels observations SYNTHETIC_ONLY. All results remain HOLD.
"""
import hashlib
import json

from research import kraken_spot_diagnostic as diagnostic
from research import kraken_spot_validation_bridge as bridge
from research import spot_refusal_registry as registry

VERSION = "kraken-reversal-groundwork-v1"
SOURCE_TAG = "PUBLIC_SPOT_OBSERVATION_PROPOSED"
FIXTURE_ORIGIN = "SYNTHETIC_STATIC_KRAKEN_JSON"
MAX_INPUT_BYTES = 2 * 1024 * 1024
MAX_OUTPUT_BYTES = 1024 * 1024
POLICY = {"version": registry.VERSION, "future_mode": "as_of"}
CONTEXT_FIELDS = {"revision", "run_id", "boot_scope"}
EVIDENCE_FIELDS = {"kind", "authority", "utc_ns", "mono_ns", "valid_until_mono_ns",
                   "uncertainty_ns", *CONTEXT_FIELDS}


class Refused(ValueError):
    pass


def _require(condition, reason):
    if not condition:
        raise Refused(reason)


def _hash(value):
    return "sha256:" + hashlib.sha256(registry.canonical_json(value).encode("ascii")).hexdigest()


def _disabled():
    return {"version": VERSION, "overall": "HOLD", "reason": "AUTHORIZATION_MISSING",
            "requests": 0, "candidate_stage": "NOT_ADMITTED", "proposed_input": None, "symbols": {}}


def _parse(text):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result: raise ValueError
            result[key] = value
        return result
    def reject(_): raise ValueError
    try:
        _require(type(text) is str and len(text) <= MAX_INPUT_BYTES
                 and len(text.encode("utf-8")) <= MAX_INPUT_BYTES, "SIZE_LIMIT")
        value = json.loads(text, object_pairs_hook=unique, parse_constant=reject)
        registry.canonical_json(value)  # Refuse 1e999, even in excluded rows.
        return value
    except Refused:
        raise
    except (ValueError, TypeError, OverflowError, RecursionError, UnicodeError):
        raise Refused("JSON_INVALID") from None


def _context(expected):
    _require(type(expected) is dict and set(expected) == CONTEXT_FIELDS, "CONTEXT_INVALID")
    for key, value in expected.items():
        _require(type(value) is str and 1 <= len(value) <= 64
                 and all(32 <= ord(c) <= 126 for c in value), "CONTEXT_INVALID")
    _require(len(expected["revision"]) == 40 and all(c in "0123456789abcdef" for c in expected["revision"]), "CONTEXT_INVALID")


def _clock(evidence, expected, gate, verifier):
    _require(type(evidence) is dict and set(evidence) == EVIDENCE_FIELDS, "CLOCK_UNVERIFIED")
    _require(evidence["kind"] == "INDEPENDENT_ATTESTATION_SYNTHETIC_MODEL"
             and evidence["authority"] == "MOCK_AUTHORITY_NO_REAL_ATTESTATION"
             and all(type(evidence[k]) is str and evidence[k] == expected[k] for k in CONTEXT_FIELDS), "CLOCK_UNVERIFIED")
    fields = ("utc_ns", "mono_ns", "valid_until_mono_ns", "uncertainty_ns")
    _require(all(type(evidence[k]) is int for k in fields)
             and 0 <= evidence["uncertainty_ns"] <= 2*diagnostic.NS
             and 0 <= evidence["mono_ns"] < evidence["valid_until_mono_ns"] < 10**24, "CLOCK_UNVERIFIED")
    # Trusted, explicitly injected TEST dependencies, not authority discovery or
    # a real attestation verifier. A callback cannot produce live GO here.
    try:
        verified = verifier(dict(evidence), dict(expected))
    except Exception:
        raise Refused("CLOCK_UNVERIFIED") from None
    _require(verified is True, "CLOCK_UNVERIFIED")
    _require(gate.initial.utc_ns == evidence["utc_ns"] and gate.initial.mono_ns == evidence["mono_ns"], "CLOCK_UNVERIFIED")
    _require(evidence["valid_until_mono_ns"] > gate.initial.mono_ns+diagnostic.DEADLINE_NS, "CLOCK_UNVERIFIED")
    return gate


def _identity_ref(symbol, payload):
    key = diagnostic._identity(symbol, payload)
    # Narrow fixture profile. Expanded optional live schemas are not verified.
    _require(set(payload["result"][key]) == diagnostic.IDENTITY_FIELDS, "IDENTITY_UNVERIFIED")
    return key, _hash({"symbol": symbol, "key": key,
                      "verified_fields": {k: payload["result"][key][k] for k in sorted(diagnostic.IDENTITY_FIELDS)}})


def _normalize(symbol, capture, decision, as_of):
    key = diagnostic.IDENTITIES[symbol][1]
    # Existing bridge has already checked ALL eligible exact decimals, VWAP,
    # count, precision and history. Never parse a refused/partial body as data.
    bars = []
    for row in capture["response"]["result"][key]:
        if row[0]+registry.HOUR <= as_of:
            bars.append({"open_time": row[0], **dict(zip(("open", "high", "low", "close", "volume"),
                                                        (float(row[i]) for i in (1, 2, 3, 4, 6))))})
    payload = {"symbol": symbol, **registry.IDENTITY,
               "rules": {"require_spot": True, "require_non_spot": False}, "bars": bars}
    parity = registry.validate_symbol(symbol, payload, as_of=as_of, policy=POLICY)
    _require(registry.canonical_json(parity) == registry.canonical_json(decision), "NORMALIZATION_MISMATCH")
    return payload


def run_offline(text=None, *, clock=None, clock_evidence_verifier=None, expected_context=None):
    """Dependency-injected STATIC SYNTHETIC JSON only; requests always zero.

    No file/network/clock provider is supplied by default. The proposed feed is
    intentionally incompatible with the unchanged candidate engine. Labels and
    injected callbacks are test assertions, not authentic market/time evidence.
    """
    if text is None:
        return _disabled()
    result = {**_disabled(), "reason": None, "source_tag": SOURCE_TAG,
              "fixture_origin": FIXTURE_ORIGIN, "clock_provenance": "UNVERIFIED",
              "symbols": {s: {"status": "NOT_ATTEMPTED", "reason": "GLOBAL_STOP",
                               "identity_ref": None, "bridge": None} for s in registry.SYMBOLS}}
    try:
        # Reject missing clock dependencies BEFORE parsing source data.
        _require(clock is not None and callable(clock_evidence_verifier), "CLOCK_UNVERIFIED")
        _context(expected_context)
        gate = diagnostic.CaptureClock(clock)  # Anchor before JSON/verifier work.
        value = _parse(text)
        fields = {"version", "source_tag", "fixture_origin", "clock_evidence", "observations"}
        _require(type(value) is dict and set(value) == fields and value["version"] == VERSION
                 and value["source_tag"] == SOURCE_TAG and value["fixture_origin"] == FIXTURE_ORIGIN, "CONTRACT_INVALID")
        gate = _clock(value["clock_evidence"], expected_context, gate, clock_evidence_verifier)
        result["clock_provenance"] = "SYNTHETIC_MODEL_ONLY_REAL_B4_UNRESOLVED"
        evidence = value["clock_evidence"]
        deadline = gate.initial.mono_ns+diagnostic.DEADLINE_NS

        def check():
            now = gate.sample()
            _require(now.mono_ns < deadline, "TIMEOUT")
            _require(now.mono_ns < evidence["valid_until_mono_ns"], "CLOCK_UNVERIFIED")
            return now

        check()  # Construction/JSON parsing is bounded by bytes, not preemptible.
        observations = value["observations"]
        _require(type(observations) is dict and set(observations) == set(registry.SYMBOLS), "CONTRACT_INVALID")
        payloads = {}
        for symbol in registry.SYMBOLS:
            row = result["symbols"][symbol]
            row.update(status="BLOCKED", reason="CONTRACT_INVALID")
            observation = observations[symbol]
            _require(type(observation) is dict and set(observation) == {"identity", "ohlc"}, "CONTRACT_INVALID")
            for stage in ("identity", "ohlc"):
                receipt = observation[stage]
                body_field = "payload" if stage == "identity" else "capture"
                _require(type(receipt) is dict and set(receipt) == {"http_status", "service_date_utc_seconds", body_field}, "CONTRACT_INVALID")
                _require(type(receipt["http_status"]) is int, "CONTRACT_INVALID")
                _require(receipt["http_status"] == 200, "HTTP_REFUSED")
                _require(len(registry.canonical_json(receipt[body_field]).encode("ascii")) <= diagnostic.BODY_LIMIT, "RESPONSE_TOO_LARGE")
                start = check()
                end = check()
                gate.envelope(start, end, receipt["service_date_utc_seconds"])
                if stage == "identity":
                    key, identity_ref = _identity_ref(symbol, receipt["payload"])
                    row["identity_ref"] = identity_ref
                else:
                    capture = receipt["capture"]
                    _require(type(capture) is dict and "response" in capture, "CONTRACT_INVALID")
                    diagnostic._commitment(capture["response"], key, gate.as_of, end, receipt["service_date_utc_seconds"])
                    validated = bridge.validate_capture(symbol, capture, as_of=gate.as_of, policy=POLICY)
                    row["bridge"] = validated
                    _require(validated["decision"]["status"] == "VALIDATED_DATA", "BRIDGE_REFUSED")
                    payloads[symbol] = _normalize(symbol, capture, validated["decision"], gate.as_of)
                check()
            row.update(status="VALIDATED_PROPOSED_DATA", reason=None)
        check()
        result["proposed_input"] = {"source_tag": SOURCE_TAG, "fixture_origin": FIXTURE_ORIGIN,
                                    "as_of": gate.as_of, "policy": dict(POLICY), "payloads": payloads,
                                    "clock_evidence_ref": _hash(evidence)}
        result["reason"] = "CANDIDATE_SOURCE_TYPE_NOT_ADMITTED"
        _require(len(registry.canonical_json(result).encode("ascii")) <= MAX_OUTPUT_BYTES-128, "OUTPUT_LIMIT")
    except (Refused, diagnostic.Refused) as exc:
        reason = str(exc) if type(exc) is Refused else exc.reason.value
        result["reason"] = reason
        result["proposed_input"] = None
        for row in result["symbols"].values():
            if row["status"] == "BLOCKED": row["reason"] = reason
    except Exception:
        result["reason"] = "CONTRACT_INVALID"
        result["proposed_input"] = None
        for row in result["symbols"].values():
            if row["status"] == "BLOCKED": row["reason"] = "CONTRACT_INVALID"
    result["evidence_ref"] = _hash(result)
    return result


def main():
    print(registry.canonical_json(_disabled()))
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
