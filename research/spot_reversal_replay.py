"""Bounded SYNTHETIC-only replay; no fitting, collection, fills or order authority.

Decisions use the unchanged evaluator on closed prefixes. Future event labels
live in a separate output collection and never enter decision construction.
"""
import copy
import hashlib
import json

from research import spot_refusal_registry as registry
from research import spot_reversal_candidates as candidates

VERSION = "spot-reversal-replay-v1"
GENERATOR = "original-synthetic-regimes-v1"
HYPOTHESIS = "fixed-016-four-feature-conjunction"
EVENT = "synthetic-close-higher-and-low-held-v1"
MAX_BARS = 384
MAX_SNAPSHOTS = 64
MAX_INPUT_BYTES = 524288
MAX_OUTPUT_BYTES = 2097152
HOUR = registry.HOUR
SPLITS = ("train", "validation", "test")
REGIMES = ("downtrend", "flat", "rebound", "whipsaw", "rally")
FAULTS = ("invalid_price", "gap", "duplicate", "out_of_order", "truncate")


class Refused(ValueError):
    """Fixed codes only; never include supplied exception text or data."""


def _require(condition, reason):
    if not condition:
        raise Refused(reason)


def _integer(value, low, high):
    return type(value) is int and low <= value <= high


def _epoch(value):
    return _integer(value, registry.MIN_TIME, registry.MAX_TIME-1) and value % HOUR == 0


def _digest(value):
    return hashlib.sha256(registry.canonical_json(value).encode("ascii")).hexdigest()


def _bounded(value, cap):
    try:
        encoded = registry.canonical_json(value)
        _require(len(encoded.encode("ascii")) <= cap, "SIZE_LIMIT")
    except (ValueError, TypeError, OverflowError, RecursionError, UnicodeError) as exc:
        if isinstance(exc, Refused):
            raise
        raise Refused("STRUCTURE_INVALID") from None


def _recipe(recipe):
    _require(type(recipe) is dict and set(recipe) == {"generator", "seed", "start_open", "segments", "faults"}, "RECIPE_INVALID")
    _require(recipe["generator"] == GENERATOR and _integer(recipe["seed"], 0, 2**31-1)
             and _epoch(recipe["start_open"]), "RECIPE_INVALID")
    segments, faults = recipe["segments"], recipe["faults"]
    _require(type(segments) is list and 1 <= len(segments) <= 16, "RECIPE_INVALID")
    count = 0
    for segment in segments:
        _require(type(segment) is dict and set(segment) == {"regime", "hours"}, "RECIPE_INVALID")
        _require(type(segment["regime"]) is str and segment["regime"] in REGIMES
                 and _integer(segment["hours"], 1, 64), "RECIPE_INVALID")
        count += segment["hours"]
    _require(count <= MAX_BARS and _epoch(recipe["start_open"]+count*HOUR), "HISTORY_LIMIT")
    _require(type(faults) is list and len(faults) <= 3, "RECIPE_INVALID")
    seen = set()
    for fault in faults:
        _require(type(fault) is dict and set(fault) == {"symbol", "index", "kind"}, "RECIPE_INVALID")
        _require(type(fault["symbol"]) is str and fault["symbol"] in registry.SYMBOLS
                 and fault["symbol"] not in seen and type(fault["kind"]) is str
                 and fault["kind"] in FAULTS and _integer(fault["index"], 0, count-2), "RECIPE_INVALID")
        seen.add(fault["symbol"])
    return count


def build_dataset(recipe):
    """Original reproducible integer-valued fixtures, not a real-data importer."""
    _bounded(recipe, 16384)
    count = _recipe(recipe)
    bars = []
    scale = 1 + recipe["seed"] % 5
    for segment in recipe["segments"]:
        for j in range(segment["hours"]):
            regime = segment["regime"]
            volume = 100
            if regime == "rebound":
                k = j % 21
                close = (list(range(130, 115, -1)) + [110, 106, 102, 100, 99, 101])[k]
                opening = close-1 if k == 20 else close+1
                low = 98 if k >= 18 else close-1
                high = max(opening, close)+1
                volume = 80 if k == 19 else 150 if k == 20 else 100
            else:
                close = (1000-j if regime == "downtrend" else 1000+j if regime == "rally"
                         else 100+20*(j % 2) if regime == "whipsaw" else 1000)
                opening = close if regime == "flat" else close-1
                low = min(opening, close) if regime == "flat" else min(opening, close)-1
                high = max(opening, close) if regime == "flat" else max(opening, close)+1
            bars.append({"open_time": recipe["start_open"]+len(bars)*HOUR,
                         "open": opening*scale, "high": high*scale, "low": low*scale,
                         "close": close*scale, "volume": volume})
    series = {s: copy.deepcopy(bars) for s in registry.SYMBOLS}
    for fault in recipe["faults"]:
        target, i, kind = series[fault["symbol"]], fault["index"], fault["kind"]
        if kind == "invalid_price": target[i]["close"] = -1
        elif kind == "gap": target.pop(i)
        elif kind == "duplicate": target.insert(i, dict(target[i]))
        elif kind == "out_of_order": target[i], target[i+1] = target[i+1], target[i]
        else: del target[i:]
    manifest = {"version": VERSION, "source_kind": "SYNTHETIC_ONLY", "source_name": GENERATOR,
                **registry.IDENTITY, "symbols": list(registry.SYMBOLS), "recipe": copy.deepcopy(recipe),
                "capture_method": "ORIGINAL_GENERATOR_NO_CAPTURE",
                "availability": {"rule": "AT_CLOSE_SYNTHETIC", "timestamp": "UTC_EPOCH_SECONDS",
                                 "backfill": "NONE", "corrections": "DECLARED_GENERATOR_FAULTS_ONLY"},
                "rights": {"license": "MIT", "evidence": "ORIGINAL_GENERATOR_019",
                           "commercial_use": True, "redistribution": True},
                "range": {"start_open": recipe["start_open"], "end_close": recipe["start_open"]+count*HOUR},
                "gaps_duplicates": copy.deepcopy(recipe["faults"]), "data_sha256": _digest(series)}
    return {"manifest": manifest, "series": series}


def _qualify(dataset):
    _bounded(dataset, MAX_INPUT_BYTES)
    _require(type(dataset) is dict and set(dataset) == {"manifest", "series"}, "DATASET_INVALID")
    manifest = dataset["manifest"]
    _require(type(manifest) is dict and "recipe" in manifest, "PROVENANCE_REJECTED")
    expected = build_dataset(manifest["recipe"])
    # Compare canonical types too: True must not impersonate 1 in Python equality.
    _require(registry.canonical_json(dataset) == registry.canonical_json(expected), "PROVENANCE_REJECTED")
    return expected


def _plan(plan, dataset):
    _bounded(plan, 8192)
    fields = {"version", "hypothesis", "event_rule", "horizon_hours", "embargo_hours", "splits"}
    _require(type(plan) is dict and set(plan) == fields, "PLAN_INVALID")
    _require(plan["version"] == VERSION and plan["hypothesis"] == HYPOTHESIS
             and plan["event_rule"] == EVENT and _integer(plan["horizon_hours"], 1, 6), "PLAN_INVALID")
    horizon = plan["horizon_hours"]
    _require(_integer(plan["embargo_hours"], registry.WINDOW+horizon, MAX_BARS), "EMBARGO_INVALID")
    splits = plan["splits"]
    _require(type(splits) is dict and set(splits) == set(SPLITS), "SPLITS_INVALID")
    lower = dataset["manifest"]["range"]["start_open"]
    upper = dataset["manifest"]["range"]["end_close"]
    previous = None
    coordinates = []
    for name in SPLITS:
        interval = splits[name]
        _require(type(interval) is dict and set(interval) == {"start", "end"}, "SPLITS_INVALID")
        start, end = interval["start"], interval["end"]
        _require(_epoch(start) and _epoch(end) and lower+HOUR <= start < end
                 and end+horizon*HOUR <= upper, "SPLITS_INVALID")
        _require(previous is None or start-previous >= plan["embargo_hours"]*HOUR, "EMBARGO_INVALID")
        count = (end-start)//HOUR
        _require(len(coordinates)+count <= MAX_SNAPSHOTS, "SNAPSHOT_LIMIT")
        coordinates.extend((name, t) for t in range(start, end, HOUR))
        previous = end
    return coordinates


def _payload(symbol, rows):
    return {"symbol": symbol, **registry.IDENTITY,
            "rules": {"require_spot": True, "require_non_spot": False}, "bars": rows}


def _decision(dataset, as_of):
    payloads = {s: _payload(s, [dict(b) for b in dataset["series"][s] if b["open_time"]+HOUR <= as_of])
                for s in registry.SYMBOLS}
    return candidates.evaluate({"version": candidates.VERSION, "label": "SYNTHETIC_ONLY",
                                "as_of": as_of, "policy": {"version": registry.VERSION, "future_mode": "as_of"},
                                "payloads": payloads})


def _labels(dataset, as_of, horizon, decision):
    result = {}
    for symbol in registry.SYMBOLS:
        status = "UNAVAILABLE"
        if decision["symbols"][symbol]["decision"] != "BLOCKED":
            end = as_of+horizon*HOUR
            prefix = [b for b in dataset["series"][symbol] if b["open_time"]+HOUR <= end]
            gate = registry.validate_symbol(symbol, _payload(symbol, prefix), as_of=end,
                                           policy={"version": registry.VERSION, "future_mode": "as_of"})
            now = [b for b in prefix if b["open_time"]+HOUR == as_of]
            future = [b for b in prefix if as_of < b["open_time"]+HOUR <= end]
            if gate["status"] == "VALIDATED_DATA" and len(now) == 1 and len(future) == horizon:
                event = future[-1]["close"] > now[0]["close"] and min(b["low"] for b in future) >= now[0]["low"]
                status = "SYNTHETIC_EVENT_TRUE" if event else "SYNTHETIC_EVENT_FALSE"
        result[symbol] = status
    return result


def _share(numerator, denominator):
    return {"numerator": numerator, "denominator": denominator}  # 0/0 is unavailable, never 0%.


def _metrics(snapshots, labels):
    counts = {str(i): 0 for i in range(4)}
    per_symbol = {}
    for snapshot in snapshots:
        counts[str(len(snapshot["decision"]["candidates"]))] += 1
    for symbol in registry.SYMBOLS:
        states = {s: 0 for s in ("WATCH", "WAIT", "BLOCKED")}
        refusals, passes, runs = {}, {f: 0 for f in candidates.FEATURES}, []
        length = 0
        last = None
        false, labeled, unknown = 0, 0, 0
        for snapshot, label in zip(snapshots, labels):
            row = snapshot["decision"]["symbols"][symbol]
            state = row["decision"]
            states[state] += 1
            if row["features"] is not None:
                for feature in candidates.FEATURES:
                    passes[feature] += row["features"][feature]["passed"]
            reason = row["validation"]["reason_code"]
            if reason is not None: refusals[reason] = refusals.get(reason, 0)+1
            if state == "WATCH":
                if length and snapshot["as_of"] != last+HOUR:
                    runs.append(length); length = 0
                length += 1
                status = label["symbols"][symbol]
                if status == "UNAVAILABLE": unknown += 1
                else:
                    labeled += 1
                    false += status == "SYNTHETIC_EVENT_FALSE"
            elif length:
                runs.append(length); length = 0
            last = snapshot["as_of"]
        if length: runs.append(length)
        per_symbol[symbol] = {"decisions": states, "refusals": refusals,
            "watch_share_all_snapshots": _share(states["WATCH"], len(snapshots)),
            "refusal_share_all_snapshots": _share(states["BLOCKED"], len(snapshots)),
            "feature_pass_share_validated": {f: _share(n, states["WATCH"]+states["WAIT"]) for f, n in passes.items()},
            "observed_watch_run_lengths_hours": runs,
            "synthetic_false_positive_share_labeled_watch": _share(false, labeled),
            "watch_labels_unavailable": unknown}
    return {"snapshots": len(snapshots), "candidate_count_histogram": counts,
            "zero_candidate_share": _share(counts["0"], len(snapshots)), "per_symbol": per_symbol}


def illustrative_cost_bps(gross_change_bps, fee_per_side_bps, spread_roundtrip_bps,
                          slippage_per_side_bps, latency_haircut_bps):
    """Standalone supplied-number sensitivity arithmetic, never fills or P&L."""
    _require(_integer(gross_change_bps, -10000, 10000), "COST_INVALID")
    costs = (fee_per_side_bps, spread_roundtrip_bps, slippage_per_side_bps, latency_haircut_bps)
    _require(all(_integer(v, 0, 10000) for v in costs), "COST_INVALID")
    return {"kind": "ILLUSTRATIVE_SYNTHETIC_ARITHMETIC_NOT_PNL",
            "net_change_bps": gross_change_bps-2*fee_per_side_bps-spread_roundtrip_bps-2*slippage_per_side_bps-latency_haircut_bps}


def replay(dataset, plan):
    """Strict synthetic qualification; complete canonical decisions exclude future lineage.

    Dataset/plan hashes belong to run-level lineage, not earlier snapshots. A
    modified but reproducible future dataset can change labels/run hashes while
    leaving every same-prefix decision byte-identical. No training is performed.
    """
    try:
        dataset = _qualify(dataset)
        coordinates = _plan(plan, dataset)
        snapshots, labels = [], []
        for split, as_of in coordinates:
            decision = _decision(dataset, as_of)
            snapshots.append({"split": split, "as_of": as_of, "decision": decision})
        # Future labels are calculated only after the decision audit is complete.
        for snapshot in snapshots:
            labels.append({"split": snapshot["split"], "as_of": snapshot["as_of"],
                           "symbols": _labels(dataset, snapshot["as_of"], plan["horizon_hours"], snapshot["decision"])})
        metrics = {split: _metrics([s for s in snapshots if s["split"] == split],
                                   [l for l in labels if l["split"] == split]) for split in SPLITS}
        result = {"version": VERSION, "status": "SYNTHETIC_HARNESS_VALIDATION_ONLY", "reason": None,
                  "manifest_sha256": _digest(dataset["manifest"]), "plan_sha256": _digest(plan),
                  "decision_sha256": _digest(snapshots), "snapshots": snapshots,
                  "forward_labels": labels, "metrics": metrics,
                  "economic_outcomes": "NOT_COMPUTED", "operational_mode": "HOLD"}
        _bounded(result, MAX_OUTPUT_BYTES)
        return result
    except Refused as exc:
        return {"version": VERSION, "status": "REFUSED", "reason": str(exc), "snapshots": [],
                "forward_labels": [], "operational_mode": "HOLD"}


def _parse(text):
    def unique(pairs):
        obj = {}
        for key, value in pairs:
            if key in obj: raise ValueError
            obj[key] = value
        return obj
    def reject(_): raise ValueError
    try:
        _require(type(text) is str and len(text) <= MAX_INPUT_BYTES
                 and len(text.encode("utf-8")) <= MAX_INPUT_BYTES, "SIZE_LIMIT")
        result = json.loads(text, object_pairs_hook=unique, parse_constant=reject)
        _bounded(result, MAX_INPUT_BYTES)
        return result
    except (ValueError, TypeError, OverflowError, RecursionError, UnicodeError):
        raise Refused("JSON_INVALID") from None


def run_experiment_json(text):
    """Local recipe+plan boundary; no dataset/source URL or arbitrary input loader."""
    try:
        experiment = _parse(text)
        _require(type(experiment) is dict and set(experiment) == {"recipe", "plan"}, "EXPERIMENT_INVALID")
        return replay(build_dataset(experiment["recipe"]), experiment["plan"])
    except Refused as exc:
        return {"version": VERSION, "status": "REFUSED", "reason": str(exc), "snapshots": [],
                "forward_labels": [], "operational_mode": "HOLD"}


def main():
    import argparse
    parser = argparse.ArgumentParser(description="SYNTHETIC-only offline research replay; no orders")
    parser.add_argument("experiment", help="local synthetic recipe/plan JSON")
    args = parser.parse_args()
    try:
        with open(args.experiment, "rb") as source:
            text = source.read(MAX_INPUT_BYTES+1).decode("utf-8")
        result = run_experiment_json(text)
    except (OSError, UnicodeError):
        result = {"version": VERSION, "status": "REFUSED", "reason": "FILE_UNAVAILABLE",
                  "snapshots": [], "forward_labels": [], "operational_mode": "HOLD"}
    print(registry.canonical_json(result))
    return 2 if result["status"] == "REFUSED" else 0


if __name__ == "__main__":
    raise SystemExit(main())
