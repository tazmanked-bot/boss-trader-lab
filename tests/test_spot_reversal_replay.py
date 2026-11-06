"""Synthetic adversarial replay audits, not market performance tests."""
import copy
from contextlib import ExitStack, redirect_stdout
import importlib
import io
import json
from pathlib import Path
import unittest
from unittest.mock import patch, mock_open

from research import spot_reversal_replay as replay
from research import spot_refusal_registry as registry
from research import spot_reversal_candidates as candidates

EXPERIMENT = json.loads((Path(__file__).parent / "fixtures/spot_reversal_replay_019.json").read_text())
S = EXPERIMENT["recipe"]["start_open"]


def experiment():
    return copy.deepcopy(EXPERIMENT)


def run(exp=None):
    exp = experiment() if exp is None else exp
    return replay.replay(replay.build_dataset(exp["recipe"]), exp["plan"])


def refault(kind, symbol="BTC/USD", index=10):
    exp = experiment()
    exp["recipe"]["faults"] = [dict(symbol=symbol, index=index, kind=kind)]
    return exp


class ReplayTests(unittest.TestCase):
    def setUp(self):
        stack = ExitStack()
        self.addCleanup(stack.close)
        self.guards = [stack.enter_context(patch(name, side_effect=AssertionError("IO_FORBIDDEN")))
                       for name in ("socket.socket", "socket.create_connection", "socket.getaddrinfo",
                                    "urllib.request.urlopen", "http.client.HTTPSConnection",
                                    "subprocess.run", "subprocess.Popen", "time.time")]
        self.addCleanup(lambda: [guard.assert_not_called() for guard in self.guards])

    def test_identical_seed_manifest_and_replay_are_canonical_reproducible(self):
        exp = experiment()
        first = replay.build_dataset(exp["recipe"])
        second = replay.build_dataset(exp["recipe"])
        self.assertEqual(registry.canonical_json(first), registry.canonical_json(second))
        original = copy.deepcopy(first)
        self.assertEqual(registry.canonical_json(replay.replay(first, exp["plan"])), registry.canonical_json(run()))
        self.assertEqual(first, original)
        self.assertEqual(exp, EXPERIMENT)

    def test_fixture_has_all_regimes_and_descriptive_counts(self):
        result = run()
        self.assertEqual(result["status"], "SYNTHETIC_HARNESS_VALIDATION_ONLY")
        self.assertEqual(set(s["regime"] for s in EXPERIMENT["recipe"]["segments"]), set(replay.REGIMES))
        self.assertEqual(len(result["snapshots"]), 12)
        for name in ("validation", "test"):
            self.assertEqual(result["metrics"][name]["candidate_count_histogram"], {"0": 3, "1": 0, "2": 0, "3": 1})
        self.assertEqual(result["metrics"]["train"]["zero_candidate_share"], {"numerator": 4, "denominator": 4})
        self.assertEqual(result["economic_outcomes"], "NOT_COMPUTED")
        self.assertEqual(result["operational_mode"], "HOLD")

    def test_every_snapshot_is_exact_unchanged_evaluator_output(self):
        exp = experiment(); dataset = replay.build_dataset(exp["recipe"])
        for snapshot in replay.replay(dataset, exp["plan"])["snapshots"]:
            a = snapshot["as_of"]
            payloads = {s: dict(symbol=s, **registry.IDENTITY,
                        rules=dict(require_spot=True, require_non_spot=False),
                        bars=[b for b in dataset["series"][s] if b["open_time"]+3600 <= a]) for s in registry.SYMBOLS}
            expected = candidates.evaluate(dict(version=candidates.VERSION, label="SYNTHETIC_ONLY",
                as_of=a, policy=dict(version=registry.VERSION, future_mode="as_of"), payloads=payloads))
            self.assertEqual(registry.canonical_json(snapshot["decision"]), registry.canonical_json(expected))

    def test_future_regime_change_preserves_complete_earlier_canonical_snapshots(self):
        first = experiment(); second = experiment()
        second["recipe"]["segments"][-1]["regime"] = "rally"
        one, two = run(first), run(second)
        boundary = S+126*3600
        self.assertEqual(registry.canonical_json([s for s in one["snapshots"] if s["as_of"] <= boundary]),
                         registry.canonical_json([s for s in two["snapshots"] if s["as_of"] <= boundary]))
        self.assertNotEqual(one["manifest_sha256"], two["manifest_sha256"])
        self.assertNotEqual(one["forward_labels"], two["forward_labels"])

    def test_appended_future_regime_preserves_all_decisions_and_labels(self):
        exp = experiment()
        exp["recipe"]["segments"].append(dict(regime="whipsaw", hours=21))
        first, second = run(), run(exp)
        self.assertEqual(registry.canonical_json(first["snapshots"]), registry.canonical_json(second["snapshots"]))
        self.assertEqual(first["forward_labels"], second["forward_labels"])
        self.assertNotEqual(first["manifest_sha256"], second["manifest_sha256"])

    def test_future_invalid_row_never_changes_earlier_decision_but_label_unavailable(self):
        clean = run()
        bad = run(refault("invalid_price", index=126))
        before = lambda rows: [s for s in rows if s["as_of"] <= S+126*3600]
        self.assertEqual(registry.canonical_json(before(clean["snapshots"])), registry.canonical_json(before(bad["snapshots"])))
        label = next(l for l in bad["forward_labels"] if l["as_of"] == S+126*3600)
        self.assertEqual(label["symbols"]["BTC/USD"], "UNAVAILABLE")

    def test_labels_are_computed_after_all_decisions(self):
        calls = []
        decision, labels = replay._decision, replay._labels
        def record_decision(*args):
            calls.append("decision"); return decision(*args)
        def record_labels(*args):
            calls.append("label"); return labels(*args)
        with patch.object(replay, "_decision", side_effect=record_decision), patch.object(replay, "_labels", side_effect=record_labels):
            run()
        self.assertEqual(calls, ["decision"]*12+["label"]*12)

    def test_forward_rule_hand_calculated_and_not_a_price_or_trade(self):
        result = run()
        # At final rebound bar 126, next flat regime is higher with lows held.
        label = next(l for l in result["forward_labels"] if l["as_of"] == S+126*3600)
        self.assertTrue(all(v == "SYNTHETIC_EVENT_TRUE" for v in label["symbols"].values()))
        self.assertNotIn("entry_price", registry.canonical_json(result))
        self.assertEqual(result["economic_outcomes"], "NOT_COMPUTED")

    def test_invalid_eligible_history_blocks_even_when_recent_shape_would_watch(self):
        exp = refault("invalid_price", index=0)
        result = run(exp)
        row = next(s for s in result["snapshots"] if s["as_of"] == S+126*3600)["decision"]["symbols"]["BTC/USD"]
        self.assertEqual(row["decision"], "BLOCKED")
        self.assertEqual(row["validation"]["reason_code"], "INVALID_VALUE")
        self.assertIsNone(row["score"])
        self.assertIsNone(row["features"])

    def test_fault_matrix_gap_duplicate_order_and_stale(self):
        for kind, reason in (("gap", "TIMESTAMP_GAP"), ("duplicate", "DUPLICATE_TIMESTAMP"),
                              ("out_of_order", "TIMESTAMP_ORDER"), ("truncate", "DATA_STALE")):
            index = 25 if kind == "truncate" else 0 if kind == "out_of_order" else 10
            result = run(refault(kind, index=index))
            row = result["snapshots"][-1]["decision"]["symbols"]["BTC/USD"]
            self.assertEqual(row["decision"], "BLOCKED")
            self.assertEqual(row["validation"]["reason_code"], reason)

    def test_independent_symbol_failure_and_zero_one_two_three_bound(self):
        for blocked in range(4):
            exp = experiment()
            exp["recipe"]["faults"] = [dict(symbol=s, index=0, kind="invalid_price") for s in registry.SYMBOLS[:blocked]]
            result = run(exp)
            snapshot = next(s for s in result["snapshots"] if s["as_of"] == S+126*3600)
            self.assertEqual(len(snapshot["decision"]["candidates"]), 3-blocked)
            self.assertEqual(len(set(snapshot["decision"]["candidates"])), 3-blocked)

    def test_stable_tie_order_unchanged(self):
        for snapshot in run()["snapshots"]:
            if snapshot["decision"]["candidates"]:
                self.assertEqual(snapshot["decision"]["candidates"], ["BTC/USD", "SOL/USD", "XRP/USD"])

    def test_insufficient_history_is_blocked_no_warmup_bypass(self):
        exp = experiment()
        exp["plan"]["splits"]["train"] = dict(start=S+19*3600, end=S+21*3600)
        result = run(exp)
        self.assertEqual([s["decision"]["symbols"]["BTC/USD"]["validation"]["reason_code"] for s in result["snapshots"][:2]],
                         ["WARMUP_INCOMPLETE", "WARMUP_INCOMPLETE"])

    def test_overlap_wrong_chronology_and_short_embargo_refuse(self):
        for start in (S+22*3600, S+48*3600, S+10*3600):
            exp = experiment(); exp["plan"]["splits"]["validation"]["start"] = start
            self.assertEqual(run(exp)["status"], "REFUSED")
        exp = experiment(); exp["plan"]["embargo_hours"] = 23
        self.assertEqual(run(exp)["reason"], "EMBARGO_INVALID")

    def test_exact_embargo_boundary_is_accepted(self):
        exp = experiment()
        exp["plan"]["splits"]["validation"] = dict(start=S+49*3600, end=S+53*3600)
        self.assertEqual(run(exp)["status"], "SYNTHETIC_HARNESS_VALIDATION_ONLY")

    def test_outcome_horizon_and_dataset_range_are_enforced(self):
        for value in (0, 7, True, "3"):
            exp = experiment(); exp["plan"]["horizon_hours"] = value
            self.assertEqual(run(exp)["status"], "REFUSED")
        exp = experiment(); exp["plan"]["splits"]["test"]["end"] = S+146*3600
        self.assertEqual(run(exp)["reason"], "SPLITS_INVALID")

    def test_hypothesis_parameters_and_injected_scores_cannot_override(self):
        for layer in ("plan", "recipe"):
            exp = experiment(); exp[layer]["score"] = 10**9
            self.assertEqual(replay.run_experiment_json(json.dumps(exp))["status"], "REFUSED")
        exp = experiment(); exp["plan"]["hypothesis"] = "tuned-on-test"
        self.assertEqual(run(exp)["status"], "REFUSED")
        ds = replay.build_dataset(EXPERIMENT["recipe"]); ds["series"]["BTC/USD"][0]["score"] = 10**9
        self.assertEqual(replay.replay(ds, EXPERIMENT["plan"])["reason"], "PROVENANCE_REJECTED")

    def test_unknown_provenance_missing_rights_or_mixed_identity_refuse(self):
        for key, value in (("source_name", "unknown"), ("source_kind", "KRAKEN_REAL_DATA"),
                           ("quote", "USDT"), ("venue", "binance"), ("timeframe", "5m")):
            ds = replay.build_dataset(EXPERIMENT["recipe"]); ds["manifest"][key] = value
            self.assertEqual(replay.replay(ds, EXPERIMENT["plan"])["reason"], "PROVENANCE_REJECTED")
        ds = replay.build_dataset(EXPERIMENT["recipe"]); del ds["manifest"]["rights"]
        self.assertEqual(replay.replay(ds, EXPERIMENT["plan"])["status"], "REFUSED")
        for key in ("commercial_use", "redistribution", "evidence", "license"):
            ds = replay.build_dataset(EXPERIMENT["recipe"]); ds["manifest"]["rights"][key] = None
            self.assertEqual(replay.replay(ds, EXPERIMENT["plan"])["status"], "REFUSED")

    def test_relabeling_actual_like_data_and_rehashing_does_not_pass_generator_gate(self):
        ds = replay.build_dataset(EXPERIMENT["recipe"])
        ds["series"]["BTC/USD"][0].update(open=70000, close=70001, low=69999, high=70002)
        ds["manifest"]["data_sha256"] = replay._digest(ds["series"])
        self.assertEqual(replay.replay(ds, EXPERIMENT["plan"])["reason"], "PROVENANCE_REJECTED")

    def test_backfill_claim_or_false_labels_are_rejected(self):
        ds = replay.build_dataset(EXPERIMENT["recipe"])
        ds["manifest"]["availability"]["backfill"] = "EARLIER_PUBLICATION_ASSUMED"
        self.assertEqual(replay.replay(ds, EXPERIMENT["plan"])["status"], "REFUSED")
        ds = replay.build_dataset(EXPERIMENT["recipe"]); ds["labels"] = {"win": True}
        self.assertEqual(replay.replay(ds, EXPERIMENT["plan"])["reason"], "DATASET_INVALID")
        exp = experiment(); exp["plan"]["event_rule"] = "every-WATCH-is-a-win"
        self.assertEqual(run(exp)["reason"], "PLAN_INVALID")

    def test_boolean_numeric_impersonation_and_unknown_symbol_refuse(self):
        ds = replay.build_dataset(EXPERIMENT["recipe"])
        ds["manifest"]["rights"]["commercial_use"] = 1
        self.assertEqual(replay.replay(ds, EXPERIMENT["plan"])["status"], "REFUSED")
        ds = replay.build_dataset(EXPERIMENT["recipe"]); ds["series"]["ETH/USD"] = []
        self.assertEqual(replay.replay(ds, EXPERIMENT["plan"])["status"], "REFUSED")

    def test_unexpected_types_missing_fields_and_nonfinite_refuse(self):
        for dataset in (None, [], {}, {"manifest": None, "series": []}, {"manifest": {"recipe": []}, "series": {}}):
            self.assertEqual(replay.replay(dataset, EXPERIMENT["plan"])["status"], "REFUSED")
        ds = replay.build_dataset(EXPERIMENT["recipe"]); ds["series"]["BTC/USD"][0]["close"] = float("nan")
        self.assertEqual(replay.replay(ds, EXPERIMENT["plan"])["status"], "REFUSED")
        for plan in (None, {}, [], {**EXPERIMENT["plan"], "extra": 1}):
            self.assertEqual(replay.replay(replay.build_dataset(EXPERIMENT["recipe"]), plan)["status"], "REFUSED")

    def test_excessive_history_snapshots_and_bytes_refuse_before_work(self):
        exp = experiment(); exp["recipe"]["segments"] = [dict(regime="flat", hours=64)]*7
        self.assertEqual(replay.run_experiment_json(json.dumps(exp))["reason"], "HISTORY_LIMIT")
        exp = experiment(); exp["recipe"]["segments"] = [dict(regime="flat", hours=64)]*6
        exp["plan"]["splits"] = {name:dict(start=S+a*3600,end=S+b*3600) for name,a,b in (
            ("train",21,51),("validation",80,110),("test",140,170))}
        self.assertEqual(run(exp)["reason"], "SNAPSHOT_LIMIT")
        ds = replay.build_dataset(EXPERIMENT["recipe"]); ds["oversized"] = "X"*replay.MAX_INPUT_BYTES
        self.assertEqual(replay.replay(ds, EXPERIMENT["plan"])["reason"], "SIZE_LIMIT")

    def test_parser_duplicate_nonfinite_overflow_recursion_and_secret_errors_refuse(self):
        for text in ('{"recipe":{},"recipe":{}}', "NaN", "1e999", "["*2000, "\ud800", None,
                     " "*(replay.MAX_INPUT_BYTES+1), "PRIVATE_SECRET{"):
            result = replay.run_experiment_json(text)
            self.assertEqual(result["status"], "REFUSED")
            self.assertNotIn("PRIVATE_SECRET", registry.canonical_json(result))

    def test_descriptive_metrics_denominators_and_censored_duration(self):
        result = run()
        metrics = result["metrics"]["test"]["per_symbol"]["BTC/USD"]
        self.assertEqual(metrics["decisions"], {"WATCH":1,"WAIT":3,"BLOCKED":0})
        self.assertEqual(metrics["observed_watch_run_lengths_hours"], [1])
        self.assertEqual(metrics["watch_share_all_snapshots"], dict(numerator=1, denominator=4))
        self.assertEqual(metrics["synthetic_false_positive_share_labeled_watch"], dict(numerator=0, denominator=1))
        bad = run(refault("invalid_price"))["metrics"]["test"]["per_symbol"]["BTC/USD"]
        self.assertEqual(bad["feature_pass_share_validated"]["fresh_recovery"], dict(numerator=0,denominator=0))
        self.assertEqual(bad["refusal_share_all_snapshots"], dict(numerator=4,denominator=4))

    def test_synthetic_false_positive_is_event_failure_not_observed_loss(self):
        exp = experiment(); exp["recipe"]["segments"][-1]["regime"] = "whipsaw"
        result = run(exp)
        metric = result["metrics"]["test"]["per_symbol"]["BTC/USD"]
        self.assertEqual(metric["synthetic_false_positive_share_labeled_watch"], dict(numerator=1,denominator=1))
        # Invalid future history is unavailable, not a false event.
        bad = run(refault("invalid_price", index=126))
        metric = bad["metrics"]["test"]["per_symbol"]["BTC/USD"]
        self.assertEqual(metric["watch_labels_unavailable"], 1)
        self.assertEqual(metric["synthetic_false_positive_share_labeled_watch"], dict(numerator=0,denominator=0))
        # Hand-constructed audit rows isolate count arithmetic, not market data.
        snapshot = next(s for s in run()["snapshots"] if s["decision"]["candidates"])
        label = dict(split=snapshot["split"],as_of=snapshot["as_of"],symbols={s:"SYNTHETIC_EVENT_FALSE" for s in registry.SYMBOLS})
        metric = replay._metrics([snapshot],[label])["per_symbol"]["BTC/USD"]
        self.assertEqual(metric["synthetic_false_positive_share_labeled_watch"], dict(numerator=1,denominator=1))

    def test_illustrative_cost_sensitivity_no_prices_fills_or_positions(self):
        low = replay.illustrative_cost_bps(100, 10, 5, 2, 1)
        high = replay.illustrative_cost_bps(100, 30, 20, 15, 10)
        self.assertEqual(low["net_change_bps"], 70)
        self.assertEqual(high["net_change_bps"], -20)
        self.assertEqual(low["kind"], "ILLUSTRATIVE_SYNTHETIC_ARITHMETIC_NOT_PNL")
        for bad in (-1, True, float("nan"), "10"):
            with self.assertRaises(replay.Refused): replay.illustrative_cost_bps(100,bad,0,0,0)

    def test_end_to_end_json_and_bounded_canonical_output(self):
        result = replay.run_experiment_json(json.dumps(EXPERIMENT))
        self.assertEqual(registry.canonical_json(result), registry.canonical_json(run()))
        self.assertLess(len(registry.canonical_json(result)), replay.MAX_OUTPUT_BYTES)

    def test_cli_local_fixture_only_and_read_failure_redacted(self):
        text = json.dumps(EXPERIMENT).encode()
        output = io.StringIO()
        with patch("sys.argv", ["replay", "synthetic.json"]), patch("builtins.open", mock_open(read_data=text)) as opened, redirect_stdout(output):
            self.assertEqual(replay.main(), 0)
            opened.assert_called_once_with("synthetic.json", "rb")
            opened().read.assert_called_once_with(replay.MAX_INPUT_BYTES+1)
        self.assertEqual(json.loads(output.getvalue()), run())
        with patch("sys.argv", ["replay", "synthetic.json"]), patch("builtins.open", side_effect=OSError("PRIVATE_SECRET")), redirect_stdout(io.StringIO()) as out:
            self.assertEqual(replay.main(), 2)
        self.assertNotIn("PRIVATE_SECRET", out.getvalue())

    def test_import_and_reload_never_collect_or_read_clock(self):
        importlib.reload(replay)
        self.assertEqual(run()["status"], "SYNTHETIC_HARNESS_VALIDATION_ONLY")

    def test_all_flat_and_rally_series_never_force_watch(self):
        for regime in ("flat", "rally"):
            exp = experiment()
            exp["recipe"]["segments"] = [dict(regime=regime,hours=49)]*3
            result = run(exp)
            self.assertEqual(result["status"], "SYNTHETIC_HARNESS_VALIDATION_ONLY")
            self.assertTrue(all(s["decision"]["candidates"] == [] for s in result["snapshots"]))

    def test_train_labels_end_before_next_feature_window(self):
        exp = experiment(); horizon = exp["plan"]["horizon_hours"]
        for left,right in (("train","validation"),("validation","test")):
            last_coordinate = exp["plan"]["splits"][left]["end"]-3600
            self.assertLess(last_coordinate+horizon*3600,
                            exp["plan"]["splits"][right]["start"]-registry.WINDOW*3600)

    def test_watch_run_lengths_break_at_missing_coordinates(self):
        snapshot = next(s for s in run()["snapshots"] if s["decision"]["candidates"])
        later = copy.deepcopy(snapshot); later["as_of"] += 7200
        labels = [dict(symbols={s:"UNAVAILABLE" for s in registry.SYMBOLS})]*2
        result = replay._metrics([snapshot,later],labels)
        self.assertEqual(result["per_symbol"]["BTC/USD"]["observed_watch_run_lengths_hours"], [1,1])

    def test_changed_seed_changes_manifest_not_hypothesis(self):
        exp = experiment(); exp["recipe"]["seed"] += 1
        first,second = run(),run(exp)
        self.assertNotEqual(first["manifest_sha256"],second["manifest_sha256"])
        self.assertEqual(first["plan_sha256"],second["plan_sha256"])

    def test_recipe_wrong_units_score_faults_and_seed_type_refuse(self):
        for key,value in (("seed",True),("start_open",S*1000),("generator","real-loader"),
                           ("faults",[dict(symbol="ETH/USD",index=0,kind="gap")])):
            exp = experiment(); exp["recipe"][key] = value
            self.assertEqual(replay.run_experiment_json(json.dumps(exp))["status"],"REFUSED")
        exp = experiment(); exp["recipe"]["faults"] = [dict(symbol="BTC/USD",index=0,kind="gap")]*2
        self.assertEqual(replay.run_experiment_json(json.dumps(exp))["status"],"REFUSED")


if __name__ == "__main__":
    unittest.main()
