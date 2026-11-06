"""Explicit static-fixture preview, never public live admission or trade authority.

Reuses the existing exact feature function. It never calls the synthetic
evaluator with a public feed and never accepts a caller's validated result/hash.
"""
import hashlib
import json
import re

from research import kraken_spot_reversal_bridge_prototype as prototype
from research import kraken_spot_diagnostic as diagnostic
from research import spot_refusal_registry as registry
from research import spot_reversal_candidates as candidates

VERSION = "source-preview-023-v1"
MODE = "STATIC_FIXTURE_EXPERIMENT_ONLY"
SOURCE = "STATIC_SYNTHETIC_KRAKEN_SHAPED"
MAX_OUTPUT_BYTES = 32768
WARNING = "candidate preview only; NOT LIVE; NO TRADING AUTHORITY"
WHY_EARLY = "Downside slowed, low retest held, fresh bounded recovery with consistent volume."
INVALIDATION = "A later eligible low below the observed retest anchor would invalidate this research condition; no order."
REFUSALS = {"CLOCK_UNVERIFIED", "CLOCK_CONFLICT", "TIMEOUT", "SOURCE_BOUNDARY_INVALID",
            "REGISTRY_REFUSED", "REGISTRY_PARITY_MISMATCH", "INELIGIBLE_NORMALIZED_ROW", "OUTPUT_LIMIT"}


class Refused(ValueError):
    pass


def _require(condition, reason):
    if not condition:
        raise Refused(reason)


def _hash(value):
    return "sha256:" + hashlib.sha256(registry.canonical_json(value).encode("ascii")).hexdigest()


def _reference(value):
    return type(value) is str and re.fullmatch(r"sha256:[0-9a-f]{64}", value) is not None


def _empty_rows():
    return {s: {"decision": "BLOCKED", "validation": None, "features": None, "score": None,
                "why_early": None, "invalidation_observation": None, "catalyst_status": "UNVERIFIED"}
            for s in registry.SYMBOLS}


def _base():
    return {"version": VERSION, "mode": MODE, "source": SOURCE,
            "source_tag": prototype.SOURCE_TAG, "fixture_origin": prototype.FIXTURE_ORIGIN,
            "preview_status": "BLOCKED", "preview_blocker": "AUTHORIZATION_MISSING",
            "live_source_admission": "HOLD", "operational_mode": "HOLD", "trade_authority": "NONE",
            "requests": 0, "warning": WARNING, "as_of": None,
            "as_of_meaning": "SYNTHETIC_EXPERIMENT_COORDINATE_NOT_CURRENT_TIME",
            "source_boundary": None, "symbols": _empty_rows(), "candidates": []}


class _ObservedClock:
    """Forward injected TEST clock unchanged; record anchors for final checkpoints."""
    def __init__(self, delegate):
        self.delegate = delegate
        self.initial = self.last = None

    @property
    def trusted(self):
        return getattr(self.delegate, "trusted", False)

    def sample(self):
        value = self.delegate.sample()
        if self.initial is None:
            self.initial = value
        self.last = value
        return value

    def check(self):
        previous = self.last
        value = self.sample()
        _require(all(type(s) is diagnostic.Stamp for s in (self.initial, previous, value)), "CLOCK_UNVERIFIED")
        _require(type(value.utc_ns) is int and type(value.mono_ns) is int
                 and registry.MIN_TIME*diagnostic.NS <= value.utc_ns < registry.MAX_TIME*diagnostic.NS
                 and 0 <= value.mono_ns < 10**24, "CLOCK_UNVERIFIED")
        for anchor in (self.initial, previous):
            wall = value.utc_ns-anchor.utc_ns
            mono = value.mono_ns-anchor.mono_ns
            _require(wall >= 0 and mono >= 0 and abs(wall-mono) <= diagnostic.NS, "CLOCK_CONFLICT")
        _require(value.mono_ns-self.initial.mono_ns < diagnostic.DEADLINE_NS, "TIMEOUT")


def _source_summary(report):
    # Preserve the original HOLD / NOT_ADMITTED and cause records, but do not
    # echo normalized price arrays or fabricate a verified-live source receipt.
    _require(report["overall"] == "HOLD" and report["candidate_stage"] == "NOT_ADMITTED"
             and type(report["requests"]) is int and report["requests"] == 0, "SOURCE_BOUNDARY_INVALID")
    fields = ("version", "overall", "reason", "requests", "candidate_stage", "source_tag",
              "fixture_origin", "clock_provenance", "symbols", "evidence_ref")
    return {k: report[k] for k in fields if k in report}


def _validated_rows(report):
    """Called only on the fresh result of the unchanged source prototype."""
    _require(report["overall"] == "HOLD" and report["candidate_stage"] == "NOT_ADMITTED"
             and type(report["requests"]) is int and report["requests"] == 0
             and report.get("source_tag") == prototype.SOURCE_TAG
             and report.get("fixture_origin") == prototype.FIXTURE_ORIGIN
             and report.get("clock_provenance") == "SYNTHETIC_MODEL_ONLY_REAL_B4_UNRESOLVED"
             and _reference(report.get("evidence_ref")), "SOURCE_BOUNDARY_INVALID")
    feed = report["proposed_input"]
    fields = {"source_tag", "fixture_origin", "as_of", "policy", "payloads", "clock_evidence_ref"}
    _require(type(feed) is dict and set(feed) == fields
             and feed["source_tag"] == prototype.SOURCE_TAG and feed["fixture_origin"] == prototype.FIXTURE_ORIGIN
             and registry.canonical_json(feed["policy"]) == registry.canonical_json(prototype.POLICY)
             and _reference(feed["clock_evidence_ref"]), "SOURCE_BOUNDARY_INVALID")
    _require(type(feed["payloads"]) is dict and set(feed["payloads"]) == set(registry.SYMBOLS)
             and type(report["symbols"]) is dict and set(report["symbols"]) == set(registry.SYMBOLS), "SOURCE_BOUNDARY_INVALID")
    decisions = registry.validate_symbols(feed["payloads"], as_of=feed["as_of"], policy=feed["policy"])
    for symbol in registry.SYMBOLS:
        source_row = report["symbols"][symbol]
        _require(source_row["status"] == "VALIDATED_PROPOSED_DATA" and source_row["reason"] is None
                 and _reference(source_row["identity_ref"]), "SOURCE_BOUNDARY_INVALID")
        # Full history must validate before ANY feature is called. Unknown or
        # partial/parity-mismatched source evidence blocks the whole experiment.
        _require(decisions[symbol]["status"] == "VALIDATED_DATA", "REGISTRY_REFUSED")
        _require(registry.canonical_json(decisions[symbol]) == registry.canonical_json(source_row["bridge"]["decision"]), "REGISTRY_PARITY_MISMATCH")
        _require(all(b["open_time"]+registry.HOUR <= feed["as_of"] for b in feed["payloads"][symbol]["bars"]), "INELIGIBLE_NORMALIZED_ROW")
    return feed, decisions


def preview_offline(text=None, *, clock=None, clock_evidence_verifier=None, expected_context=None):
    """Only explicit fixture JSON + injected TEST dependencies, no cached feed API.

    Source tags/booleans/hashes are not authenticators. Even accepted fixture
    preview output never upgrades the prototype or admits a verified live source.
    """
    result = _base()
    if text is None:
        return result
    try:
        observed = _ObservedClock(clock) if clock is not None else None
        report = prototype.run_offline(text, clock=observed, clock_evidence_verifier=clock_evidence_verifier,
                                       expected_context=expected_context)
        result["source_boundary"] = _source_summary(report)
        if report.get("reason") != "CANDIDATE_SOURCE_TYPE_NOT_ADMITTED" or report.get("proposed_input") is None:
            result["preview_blocker"] = "SOURCE_BATCH_REFUSED"
            return result
        feed, decisions = _validated_rows(report)
        observed.check()
        rows = {}
        for symbol in registry.SYMBOLS:
            observed.check()
            # EXACT existing formula function; no source relabeling or surrogate.
            features = candidates._features(feed["payloads"][symbol]["bars"])
            qualified = all(f["passed"] for f in features.values())
            rows[symbol] = {"decision": "WATCH" if qualified else "WAIT", "validation": decisions[symbol],
                            "features": features, "score": sum(f["strength_bps"] for f in features.values()),
                            "why_early": WHY_EARLY if qualified else None,
                            "invalidation_observation": INVALIDATION if qualified else None,
                            "catalyst_status": "UNVERIFIED"}
            observed.check()
        ranked = sorted((s for s in registry.SYMBOLS if rows[s]["decision"] == "WATCH"),
                        key=lambda s: (-rows[s]["score"], s))[:3]
        observed.check()
        result.update(preview_status="PASS", preview_blocker=None, as_of=feed["as_of"], symbols=rows, candidates=ranked)
        result["preview_evidence_ref"] = _hash(result)
        _require(len(registry.canonical_json(result).encode("ascii")) <= MAX_OUTPUT_BYTES, "OUTPUT_LIMIT")
        observed.check()  # Includes preview construction/hash/serialization work.
        return result
    except Refused as exc:
        reason = str(exc) if str(exc) in REFUSALS else "PREVIEW_INVALID"
    except Exception:
        reason = "PREVIEW_INVALID"
    # Failed post-validation/feature/deadline checks cannot leak partial WATCH.
    result.update(preview_status="BLOCKED", preview_blocker=reason, as_of=None, symbols=_empty_rows(), candidates=[])
    result.pop("preview_evidence_ref", None)
    return result


def main():
    print(registry.canonical_json(_base()))
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
