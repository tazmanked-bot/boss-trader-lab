"""Offline-only tests; mock the public network call."""
import unittest
from unittest.mock import patch

from manual_live_scan import UNIVERSES, run_scan


class ManualLiveScanTests(unittest.TestCase):
    def setUp(self):
        self.closes = [100.0 + i for i in range(26)]

    @patch("manual_live_scan.fetch_closed_closes")
    def test_core_returns_only_observations(self, fetch):
        fetch.return_value = self.closes
        report, exit_code = run_scan("core")
        self.assertEqual(exit_code, 0)
        self.assertEqual(report["status"], "OBSERVE_ONLY")
        self.assertEqual(report["trading_authorization"], "NONE")
        self.assertEqual(len(report["observations"]), 3)
        self.assertEqual(fetch.call_count, 3)
        for item in report["observations"]:
            self.assertEqual(item["status"], "OBSERVE_ONLY")
            self.assertNotIn("entry", item)
            self.assertNotIn("order", item)

    @patch("manual_live_scan.fetch_closed_closes")
    def test_api_failure_fails_closed(self, fetch):
        fetch.side_effect = OSError("simulated block")
        report, exit_code = run_scan("core")
        self.assertEqual(exit_code, 1)
        self.assertEqual(report["status"], "DATA_UNAVAILABLE")
        self.assertEqual(len(report["errors"]), 3)
        self.assertEqual(report["observations"], [])

    def test_unapproved_universe_rejected(self):
        with self.assertRaises(ValueError):
            run_scan("arbitrary")

    def test_universes_bound(self):
        self.assertLessEqual(len(UNIVERSES["expanded"]), 7)


if __name__ == "__main__":
    unittest.main()
