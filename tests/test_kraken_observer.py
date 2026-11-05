"""Offline fixture tests for the Kraken public USD adapter."""
import unittest
from kraken_public_observer import parse_closed_candles, INTERVAL_SECONDS

NOW = 1_900_000_000
BASE = (NOW // INTERVAL_SECONDS - 30) * INTERVAL_SECONDS


def fixture():
    candles = [[BASE + i * INTERVAL_SECONDS, "1", "1", "1", str(100 + i), "1", "1", 1]
               for i in range(30)]
    return {"error": [], "result": {"XXBTZUSD": candles, "last": "0"}}


class KrakenPublicDataTests(unittest.TestCase):
    def test_closed_candles_only(self):
        # Bring fixture close to NOW so last completed candle passes freshness guard.
        base = (NOW // INTERVAL_SECONDS - 29) * INTERVAL_SECONDS
        rows = [[base + i * INTERVAL_SECONDS, "1", "1", "1", str(100 + i), "1", "1", 1]
                for i in range(30)]
        payload = {"error": [], "result": {"XXBTZUSD": rows, "last": "0"}}
        closes = parse_closed_candles(payload, NOW)
        self.assertEqual(len(closes), 29)
        self.assertEqual(closes[-1], 128.0)

    def test_api_error_rejected(self):
        with self.assertRaises(ValueError):
            parse_closed_candles({"error": ["EService:Unavailable"], "result": {}}, NOW)

    def test_stale_data_rejected(self):
        with self.assertRaises(ValueError):
            parse_closed_candles(fixture(), NOW + 86400)

    def test_out_of_order_rejected(self):
        base = (NOW // INTERVAL_SECONDS - 29) * INTERVAL_SECONDS
        rows = [[base + i * INTERVAL_SECONDS, "1", "1", "1", str(100 + i)]
                for i in range(30)]
        rows[10][0] = rows[9][0]
        with self.assertRaises(ValueError):
            parse_closed_candles({"error": [], "result": {"XXBTZUSD": rows}}, NOW)


if __name__ == "__main__":
    unittest.main()
