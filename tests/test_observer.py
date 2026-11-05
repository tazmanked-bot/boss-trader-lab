"""Dependency-free deterministic checks; no network calls or financial orders."""
import unittest
from boss_trader_lab import observe, sma, ALLOWED_PAIRS


class ObserverTests(unittest.TestCase):
    def test_sma(self):
        self.assertEqual(sma([1.0, 2.0, 3.0], 2), 2.5)

    def test_observation_never_proposes_order(self):
        result = observe("BTCUSDT", [100.0 + i for i in range(25)])
        self.assertEqual(result["status"], "OBSERVE_ONLY")
        self.assertNotIn("buy", result)
        self.assertNotIn("quantity", result)
        self.assertNotIn("entry", result)

    def test_unapproved_pair_rejected(self):
        with self.assertRaises(ValueError):
            observe("DOGEUSDT", [100.0] * 25)

    def test_short_series_rejected(self):
        with self.assertRaises(ValueError):
            observe("BTCUSDT", [1.0] * 20)

    def test_allowlist_small(self):
        self.assertLessEqual(len(ALLOWED_PAIRS), 10)


if __name__ == "__main__":
    unittest.main()
