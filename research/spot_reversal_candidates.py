"""Optional pure-stdlib SYNTHETIC-only spot research. No market/clock I/O.

WATCH is a fixture observation, never entry readiness or order authority.
See docs/BOSS-TRADER-SPOT-CANDIDATES-016.md for exact formulas and time contract.
"""
from fractions import Fraction
import json

from research import spot_refusal_registry as registry

VERSION = "spot-reversal-research-v1"
LABEL = "SYNTHETIC_ONLY"
MAX_INPUT_BYTES = 3 * registry.MAX_JSON_BYTES
MAX_OUTPUT_BYTES = 16384
FEATURES = ("slowing_downside", "low_retest_hold", "fresh_recovery", "volume_consistent")
WARNING = "WATCH is research only; not ENTRY READY, BUY authorization or an instruction to trade."


def _bps(value):
    """Exact floor with explicit [0,10000] clipping; never floating arithmetic."""
    return int(max(Fraction(0), min(Fraction(1), value)) * 10000)


def _features(bars):
    # Called only after the complete unchanged registry validates this symbol.
    c = [Fraction(b["close"]) for b in bars]
    low = [Fraction(b["low"]) for b in bars]
    volume = [Fraction(b["volume"]) for b in bars]
    first_drop, last_drop = c[-5] - c[-4], c[-4] - c[-3]
    slowing = c[-6] > c[-5] > c[-4] > c[-3] and last_drop < first_drop
    anchor = min(low[-6:-2])
    retest = all(anchor <= value <= anchor * Fraction(101, 100) for value in low[-2:])
    recovery = (c[-2] <= c[-3] and c[-2] < c[-1] <= c[-4]
                and c[-1] > Fraction(bars[-1]["open"]))
    mean_volume = sum(volume[-16:-2], Fraction(0)) / 14
    consistent = (0 < volume[-2] <= mean_volume <= volume[-1] <= 2 * mean_volume
                  and volume[-1] >= volume[-2])
    flags = dict(zip(FEATURES, (slowing, retest, recovery, consistent)))
    strengths = {
        "slowing_downside": _bps(1 - last_drop / first_drop) if slowing else 0,
        "low_retest_hold": _bps(1 - (max(low[-2:]) - anchor) * 100 / anchor) if retest else 0,
        "fresh_recovery": _bps((c[-1] - c[-2]) / (c[-4] - c[-2])) if recovery else 0,
        "volume_consistent": _bps(volume[-1] / mean_volume - 1) if consistent else 0,
    }
    return {name: {"passed": flags[name], "strength_bps": strengths[name]} for name in FEATURES}


def _report(decisions):
    rows = {}
    for symbol in registry.SYMBOLS:
        decision = decisions[symbol]
        rows[symbol] = {"decision": "BLOCKED", "validation": decision,
                        "features": None, "score": None, "why_early": None,
                        "invalidation_observation": None, "catalyst_status": "UNVERIFIED"}
    return {"version": VERSION, "label": LABEL, "as_of_policy": "EXPLICIT_FIXTURE_COORDINATE_ONLY",
            "warning": WARNING, "input_error": None, "symbols": rows, "candidates": []}


def _blocked(reason):
    result = _report({s: registry.refusal(s, as_of=None, reason=reason) for s in registry.SYMBOLS})
    # No trustworthy envelope coordinate exists. Preserve the registry's
    # TIMESTAMP_INVALID context refusal and report the boundary error separately.
    result["input_error"] = reason.value
    return result


def evaluate(fixture):
    """Evaluate an ordinary JSON-shaped fixture; never trust supplied scores.

    Label is a caller assertion, not verified source provenance. No live adapter.
    Unknown envelope fields block all; valid envelope uses per-symbol refusals.
    Future projection is exactly the registry contract, including its row cap.
    """
    fields = {"version", "label", "as_of", "policy", "payloads"}
    if (type(fixture) is not dict or set(fixture) != fields
            or type(fixture["version"]) is not str or fixture["version"] != VERSION
            or type(fixture["label"]) is not str or fixture["label"] != LABEL):
        return _blocked(registry.Reason.MALFORMED_DATA)
    # Policy must be explicit; None must not silently select the registry default.
    policy = fixture["policy"]
    if policy is None:
        policy = {}
    as_of, payloads = fixture["as_of"], fixture["payloads"]
    decisions = registry.validate_symbols(payloads, as_of=as_of, policy=policy)
    result = _report(decisions)
    for symbol, row in result["symbols"].items():
        if row["validation"]["status"] != "VALIDATED_DATA":
            continue
        # Preserve input order; no sorting, filling, tail-only validation or shifts.
        bars = [bar for bar in payloads[symbol]["bars"] if bar["open_time"] + registry.HOUR <= as_of]
        features = _features(bars)
        qualified = all(feature["passed"] for feature in features.values())
        row.update(decision="WATCH" if qualified else "WAIT", features=features,
                   score=sum(f["strength_bps"] for f in features.values()))
        if qualified:
            row.update(why_early="Downside slowed, low retest held, fresh bounded recovery with consistent volume.",
                       invalidation_observation="A later eligible low below the observed retest anchor would invalidate this research condition; no order.")
    result["candidates"] = sorted(
        (s for s, row in result["symbols"].items() if row["decision"] == "WATCH"),
        key=lambda s: (-result["symbols"][s]["score"], s))[:3]
    # Output has fixed vocabulary, three symbols, bounded integers and hashes.
    assert len(registry.canonical_json(result).encode("ascii")) <= MAX_OUTPUT_BYTES
    return result


def evaluate_json(text):
    """Bounded JSON boundary; duplicate keys/nonfinite tokens always refuse.

    Like registry.validate_json, malformed serialization is rejected even in a
    future row. Projection equality applies only to well-formed bounded input.
    """
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError
            result[key] = value
        return result

    def reject(_):
        raise ValueError

    try:
        if type(text) is not str or len(text) > MAX_INPUT_BYTES or len(text.encode("utf-8")) > MAX_INPUT_BYTES:
            raise ValueError
        fixture = json.loads(text, object_pairs_hook=unique, parse_constant=reject)
        registry.canonical_json(fixture)  # Also refuses numeric overflow 1e999.
        return evaluate(fixture)
    except (ValueError, TypeError, OverflowError, RecursionError, UnicodeError):
        return _blocked(registry.Reason.MALFORMED_DATA)


def main():
    """Explicit local fixture file only; never read the system clock."""
    import argparse
    parser = argparse.ArgumentParser(description="SYNTHETIC offline WATCH/WAIT/BLOCKED research only")
    parser.add_argument("fixture", help="local synthetic JSON fixture")
    args = parser.parse_args()
    try:
        with open(args.fixture, "rb") as source:
            text = source.read(MAX_INPUT_BYTES + 1).decode("utf-8")
        result = evaluate_json(text)
    except (OSError, UnicodeError):
        result = _blocked(registry.Reason.DATA_UNAVAILABLE)
    print(registry.canonical_json(result))
    return 0 if all(r["decision"] != "BLOCKED" for r in result["symbols"].values()) else 2


if __name__ == "__main__":
    raise SystemExit(main())
