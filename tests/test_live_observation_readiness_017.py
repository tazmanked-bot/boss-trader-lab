"""Test-only SYNTHETIC chain proof; no production converter or live pipeline."""
import copy
from contextlib import ExitStack, redirect_stdout
import io
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from research import kraken_spot_validation_bridge as bridge
from research import spot_refusal_registry as registry
from research import spot_reversal_candidates as candidates
from research import kraken_spot_diagnostic as diagnostic
from research import kraken_probe_corrections as corrections

BASE = json.loads((Path(__file__).parent / "fixtures/spot_reversal_candidates_016.json").read_text())


def supplied():
    data = copy.deepcopy(BASE)
    # Match the bridge's normalized float representation exactly, including hash
    # serialization. This is invented fixture construction, never market parsing.
    for payload in data["payloads"].values():
        for bar in payload["bars"]:
            for key in ("open", "high", "low", "close", "volume"):
                bar[key] = float(bar[key])
    return data


def capture(payload, as_of):
    symbol = payload["symbol"]
    return {"venue": "kraken", "market": "spot", "quote": "USD", "symbol": symbol,
            "request_pair": bridge.PAIRS[symbol][0], "interval_minutes": 60,
            "response": {"error": [], "result": {"last": as_of,
                bridge.PAIRS[symbol][1][0]: [
                    [b["open_time"], str(b["open"]), str(b["high"]), str(b["low"]),
                     str(b["close"]), str(b["close"]), str(b["volume"]), 1]
                    for b in payload["bars"]]}}}


def proof(data, captures=None):
    """Test-only orchestration over two already supplied synthetic representations.

    These aren't independent data sources; no live capture normalizer is added.
    Bridge refusal removes eligibility for candidate calculation; its original
    reason stays in the separate bridge record. Nothing repairs rejected rows.
    """
    captures = ({s: capture(p, data["as_of"]) for s, p in data["payloads"].items()}
                if captures is None else captures)
    validated = bridge.validate_captures(captures, as_of=data["as_of"], policy=data["policy"])
    gated = copy.deepcopy(data)
    for symbol, row in validated.items():
        if row["decision"]["status"] != "VALIDATED_DATA":
            gated["payloads"].pop(symbol, None)
        else:
            expected = registry.validate_symbol(symbol, data["payloads"].get(symbol),
                                                as_of=data["as_of"], policy=data["policy"])
            assert registry.canonical_json(row["decision"]) == registry.canonical_json(expected), \
                "Synthetic representations differ; no candidate proof permitted"
    return {"kind": "SYNTHETIC_TEST_PROOF_ONLY", "bridge": validated,
            "candidate": candidates.evaluate(gated)}


class ReadinessProofTests(unittest.TestCase):
    def setUp(self):
        stack = ExitStack()
        self.addCleanup(stack.close)
        guards = [stack.enter_context(patch(name, side_effect=AssertionError("forbidden I/O")))
                  for name in ("socket.socket", "socket.create_connection", "socket.getaddrinfo",
                               "urllib.request.urlopen", "http.client.HTTPSConnection",
                               "subprocess.Popen", "subprocess.run", "time.time")]
        self.addCleanup(lambda: [g.assert_not_called() for g in guards])

    def test_bridge_registry_candidate_exact_canonical_decision_chain(self):
        data = supplied()
        result = proof(data)
        standalone = registry.validate_symbols(data["payloads"], as_of=data["as_of"], policy=data["policy"])
        for s in registry.SYMBOLS:
            self.assertEqual(registry.canonical_json(result["bridge"][s]["decision"]),
                             registry.canonical_json(standalone[s]))
            self.assertEqual(registry.canonical_json(result["candidate"]["symbols"][s]["validation"]),
                             registry.canonical_json(standalone[s]))
        self.assertEqual(result["candidate"]["candidates"], ["BTC/USD", "SOL/USD", "XRP/USD"])
        self.assertEqual(result["candidate"]["label"], "SYNTHETIC_ONLY")
        self.assertTrue(all(b["source_claim"] == "provided_kraken_shaped_fixture" for b in result["bridge"].values()))

    def test_chain_zero_through_three_never_requires_candidate(self):
        for count in range(4):
            data = supplied()
            for s in registry.SYMBOLS[count:]:
                for b in data["payloads"][s]["bars"]:
                    b.update(open=100.0, high=100.0, low=100.0, close=100.0, volume=100.0)
            result = proof(data)
            self.assertEqual(len(result["candidate"]["candidates"]), count)
            self.assertEqual(len(set(result["candidate"]["candidates"])), count)

    def test_independent_stale_and_bad_source_refusals_preserve_cause(self):
        data = supplied()
        for b in data["payloads"]["XRP/USD"]["bars"]:
            b["open_time"] -= 4 * 3600
        captures = {s: capture(p, data["as_of"]) for s, p in data["payloads"].items()}
        captures["SOL/USD"]["response"]["result"]["SOLUSD"][-1][7] = -1
        result = proof(data, captures)
        self.assertEqual(result["bridge"]["XRP/USD"]["decision"]["reason_code"], "DATA_STALE")
        self.assertEqual(result["bridge"]["SOL/USD"]["bridge_code"], "COUNT_INVALID")
        self.assertEqual(result["candidate"]["candidates"], ["BTC/USD"])
        for s in ("XRP/USD", "SOL/USD"):
            self.assertEqual(result["candidate"]["symbols"][s]["decision"], "BLOCKED")
            self.assertIsNone(result["candidate"]["symbols"][s]["features"])

    def test_complete_chain_evidence_future_projection_equality(self):
        for state in ("WATCH", "WAIT", "BLOCKED"):
            data = supplied()
            if state == "WAIT":
                data["payloads"]["BTC/USD"]["bars"][-1]["volume"] = 90.0
            elif state == "BLOCKED":
                data["payloads"]["BTC/USD"]["bars"][0]["close"] = -1.0
            before = registry.canonical_json(proof(data))
            original = copy.deepcopy(data)
            for p in data["payloads"].values():
                for i in range(3):
                    p["bars"].append(dict(open_time=data["as_of"]+i*3600, open="IGNORED",
                                          high=None, low=-1, close=1e99, volume="IGNORED"))
            self.assertEqual(registry.canonical_json(proof(data)), before)
            self.assertEqual(registry.canonical_json(proof(original)), before)

    def test_closed_boundary_warmup_and_strict_future_refusal(self):
        data = supplied()
        self.assertEqual(len(proof(data)["candidate"]["candidates"]), 3)
        data["payloads"]["BTC/USD"]["bars"][-1]["open_time"] = data["as_of"]
        result = proof(data)
        self.assertEqual(result["bridge"]["BTC/USD"]["decision"]["reason_code"], "WARMUP_INCOMPLETE")
        self.assertNotIn("BTC/USD", result["candidate"]["candidates"])
        data["policy"]["future_mode"] = "reject"
        self.assertEqual(proof(data)["bridge"]["BTC/USD"]["decision"]["reason_code"], "CANDLE_NOT_CLOSED")

    def test_schema_and_eligible_corruption_cannot_be_overridden(self):
        for mode in ("alias", "width", "price"):
            data = supplied()
            captures = {s: capture(p, data["as_of"]) for s, p in data["payloads"].items()}
            source = captures["BTC/USD"]["response"]["result"]
            if mode == "alias":
                source["UNAPPROVED"] = source.pop("XXBTZUSD")
            elif mode == "width":
                source["XXBTZUSD"][0].pop()
            else:
                source["XXBTZUSD"][0][4] = "-1"
            result = proof(data, captures)
            self.assertNotEqual(result["bridge"]["BTC/USD"]["decision"]["status"], "VALIDATED_DATA")
            self.assertEqual(result["candidate"]["symbols"]["BTC/USD"]["decision"], "BLOCKED")

    def test_valid_but_different_representation_fails_test_proof(self):
        data = supplied()
        captures = {s: capture(p, data["as_of"]) for s, p in data["payloads"].items()}
        captures["BTC/USD"]["response"]["result"]["XXBTZUSD"][0][6] = "101.0"
        with self.assertRaisesRegex(AssertionError, "Synthetic representations differ"):
            proof(data, captures)

    def test_disabled_entrypoints_remain_authorization_missing_zero_requests(self):
        for module in (diagnostic, corrections):
            output = io.StringIO()
            with redirect_stdout(output):
                self.assertEqual(module.main(), 2)
            result = json.loads(output.getvalue())
            self.assertEqual(result["reason"], "AUTHORIZATION_MISSING")
            self.assertEqual(result["requests"], 0)
            self.assertEqual(result["overall"], "HOLD")

    def test_delayed_cutoff_is_conditional_on_finite_valid_error_bound(self):
        # Mathematical proposal ONLY; not a policy implementation or activation.
        true_time = BASE["as_of"] + 1800
        for error in (-60, 0, 60):
            estimate = true_time + error
            proposed = ((estimate - 60) // 3600) * 3600 - 3600
            self.assertLessEqual(proposed, true_time - 3600)
        grossly_wrong_estimate = true_time + 86400
        proposed = ((grossly_wrong_estimate - 60) // 3600) * 3600 - 3600
        self.assertGreater(proposed, true_time)  # Lag cannot cure an unbounded error.


if __name__ == "__main__":
    unittest.main()
