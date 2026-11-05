"""Offline-only public-data contract tests; CCXT is not installed or imported."""
import ast
import contextlib
import copy
import importlib
import io
import json
from pathlib import Path
import tempfile
import types
import unittest
from unittest.mock import patch

from research import ccxt_kraken_comparison as c

NOW = 1_900_000_800  # exact UTC hour + 1200 seconds below
NOW = NOW // c.HOUR * c.HOUR + 1200


def fixtures(symbol="BTC/USD", count=49):
    base = NOW // c.HOUR * c.HOUR - (count - 1) * c.HOUR
    rows = [[base + i * c.HOUR, "100", "103", "99", "101.25", "101", "25", 12]
            for i in range(count)]
    raw = {"error": [], "result": {c.PAIRS[symbol]["id"]: rows, "last": str(NOW)}}
    normalized = [[r[0] * 1000, *[float(v) for v in r[1:5]], float(r[6])] for r in rows]
    market = {"symbol": symbol, "id": c.PAIRS[symbol]["id"], "base": c.PAIRS[symbol]["base"],
              "quote": "USD", "type": "spot", "spot": True, "contract": False,
              "swap": False, "future": False, "active": True, "settle": None,
              "precision": {"price": 0.01}}
    return raw, normalized, market


class ComparisonTests(unittest.TestCase):
    def test_all_three_symbol_mappings(self):
        for symbol in c.PAIRS:
            raw, rows, market = fixtures(symbol)
            report = c.compare(raw, rows, market, symbol, NOW)
            self.assertEqual(report["overlapping_closed_count"], 48)
            self.assertEqual(report["raw_counts"]["unfinished_discarded"], 1)
            self.assertEqual(report["last_utc_seconds"], (NOW // c.HOUR - 1) * c.HOUR)

    def test_unfinished_close_never_compared(self):
        raw, rows, market = fixtures()
        rows[-1][4] = 102.0
        self.assertEqual(c.compare(raw, rows, market, "BTC/USD", NOW)["max_close_delta_usd"], "0.00")

    def test_overlapping_timestamps_only(self):
        raw, rows, market = fixtures()
        report = c.compare(raw, rows[10:], market, "BTC/USD", NOW)
        self.assertEqual(report["overlapping_closed_count"], 38)

    def test_numeric_noise_is_bounded_by_tick_and_absolute_cap(self):
        raw, rows, market = fixtures()
        rows[0][4] += 1e-10
        c.compare(raw, rows, market, "BTC/USD", NOW)
        rows[0][4] += 1e-6
        with self.assertRaises(c.Unavailable):
            c.compare(raw, rows, market, "BTC/USD", NOW)

    def test_malformed_envelopes_and_wrong_pair(self):
        raw, _, _ = fixtures()
        cases = [None, [], {}, {"error": ["unavailable"], "result": {}},
                 {"error": [], "result": None},
                 {"error": [], "result": {"XETHZUSD": raw["result"]["XXBTZUSD"]}},
                 {"error": [], "result": {"XXBTZUSD": [], "SOLUSD": []}}]
        for payload in cases:
            with self.subTest(payload=payload), self.assertRaises(c.Unavailable):
                c.parse_raw(payload, "BTC/USD", NOW)

    def test_malformed_rows(self):
        for row in (None, [], [1, 2], [1] * 9):
            raw, _, _ = fixtures()
            raw["result"]["XXBTZUSD"][3] = row
            with self.assertRaises(c.Unavailable):
                c.parse_raw(raw, "BTC/USD", NOW)

    def test_nonfinite_negative_and_invalid_prices_both_paths(self):
        for value in (float("nan"), float("inf"), -float("inf"), 0, -1, None, True, "bad"):
            raw, rows, _ = fixtures()
            raw["result"]["XXBTZUSD"][5][4] = value
            rows[5][4] = value
            with self.subTest(value=value):
                with self.assertRaises(c.Unavailable):
                    c.parse_raw(raw, "BTC/USD", NOW)
                with self.assertRaises(c.Unavailable):
                    c.normalize(rows, NOW, milliseconds=True)

    def test_duplicates_gaps_and_reordering_both_paths(self):
        for mode in ("duplicate", "gap", "reorder"):
            raw, rows, _ = fixtures()
            rr = raw["result"]["XXBTZUSD"]
            for data in (rr, rows):
                if mode == "duplicate":
                    data[4] = data[3].copy()
                elif mode == "gap":
                    del data[4]
                else:
                    data[3], data[4] = data[4], data[3]
            with self.subTest(mode=mode):
                with self.assertRaises(c.Unavailable):
                    c.parse_raw(raw, "BTC/USD", NOW)
                with self.assertRaises(c.Unavailable):
                    c.normalize(rows, NOW, milliseconds=True)

    def test_stale_future_and_wrong_units(self):
        raw, rows, _ = fixtures()
        for now in (NOW + c.HOUR * 4, NOW - c.HOUR * 4):
            with self.assertRaises(c.Unavailable):
                c.parse_raw(raw, "BTC/USD", now)
            with self.assertRaises(c.Unavailable):
                c.normalize(rows, now, milliseconds=True)
        with self.assertRaises(c.Unavailable):
            c.normalize(rows, NOW, milliseconds=False)
        with self.assertRaises(c.Unavailable):
            c.normalize([[r[0] // 1000, *r[1:]] for r in rows], NOW, milliseconds=True)

    def test_exact_closed_boundary(self):
        _, rows, _ = fixtures()
        boundary = NOW // c.HOUR * c.HOUR
        closed, counts = c.normalize(rows, boundary, milliseconds=True)
        self.assertEqual(max(closed), boundary - c.HOUR)
        self.assertEqual(counts["unfinished_discarded"], 1)

    def test_missing_current_raw_row_and_too_few_candles(self):
        raw, _, _ = fixtures()
        raw["result"]["XXBTZUSD"].pop()
        with self.assertRaises(c.Unavailable):
            c.parse_raw(raw, "BTC/USD", NOW)
        raw, rows, market = fixtures(count=21)
        with self.assertRaises(c.Unavailable):
            c.compare(raw, rows, market, "BTC/USD", NOW)

    def test_market_mismaps_and_contracts_rejected(self):
        _, _, market = fixtures()
        changes = {"symbol": "BTC/USDT", "id": "XBTUSDT", "base": "ETH", "quote": "USDT",
                   "spot": False, "contract": True, "swap": True, "future": True,
                   "type": "swap", "settle": "USD", "active": False}
        for key, value in changes.items():
            changed = copy.deepcopy(market)
            changed[key] = value
            with self.subTest(key=key), self.assertRaises(c.Unavailable):
                c.market_mapping(changed, "BTC/USD")
        for symbol in ("BTC/USDT", "XBT/USD", "ETH/USD", "BTC/USD:USD"):
            with self.assertRaises(c.Unavailable):
                c.symbol_spec(symbol)

    def test_ohlc_bounds_volume_and_bad_timestamp(self):
        _, rows, _ = fixtures()
        for column, value in ((2, 1), (3, 200), (5, -1), (0, True), (0, float("nan")),
                              (0, 10 ** 1000), (0, rows[0][0] + 1)):
            changed = copy.deepcopy(rows)
            changed[0][column] = value
            with self.subTest(column=column), self.assertRaises(c.Unavailable):
                c.normalize(changed, NOW, milliseconds=True)


class NetworkSafetyTests(unittest.TestCase):
    def test_factory_public_only_guards_and_no_redirects(self):
        class Parent:
            def __init__(self, config):
                self.config = config
                self.precisionMode = 4
                self.session = types.SimpleNamespace(max_redirects=30)

            def request(self, *args):
                return args

            def fetch(self, *args):
                return args

        fake = types.SimpleNamespace(kraken=Parent, TICK_SIZE=4)
        with patch.dict("sys.modules", {"ccxt": fake}), patch.object(c.metadata, "version", return_value=c.VERSION):
            exchange = c.public_exchange()
            self.assertEqual(exchange.session.max_redirects, 0)
            self.assertEqual(exchange.config["maxRetriesOnFailure"], 0)
            self.assertEqual(exchange.config["timeout"], 12000)
            self.assertTrue(exchange.config["enableRateLimit"])
            with self.assertRaises(c.Unavailable):
                exchange.request("Balance", "private")
            with self.assertRaises(c.Unavailable):
                exchange.request("OHLC", "public", "POST")
            with self.assertRaises(c.Unavailable):
                exchange.fetch("https://example.com/")
            for _ in range(12):
                exchange.fetch("https://api.kraken.com/0/public/Assets")
            with self.assertRaises(c.Unavailable):
                exchange.fetch("https://api.kraken.com/0/public/Assets")

    def test_total_budget_and_redirect_block(self):
        with patch.object(c.time, "sleep"), patch.object(c.time, "monotonic", return_value=1):
            budget = c.PublicBudget()
            for _ in range(15):
                budget.before()
            with self.assertRaises(c.Unavailable):
                budget.before()
        with self.assertRaises(c.Unavailable):
            c.NoRedirect().redirect_request(None, None, 302, None, None, "https://example.com")

    def test_transport_allowlist(self):
        c.transport_guard("https://api.kraken.com/0/public/Assets")
        c.transport_guard("https://api.kraken.com/0/public/OHLC?pair=XBTUSD&interval=60")
        for url in ("http://api.kraken.com/0/public/Assets", "https://example.com/0/public/Assets",
                    "https://api.kraken.com/0/private/Balance", "https://api.kraken.com/0/public/Trades",
                    "https://api.kraken.com/0/public/OHLC?pair=ETHUSD&interval=60",
                    "https://api.kraken.com/0/public/OHLC?pair=XBTUSD&interval=1",
                    "https://api.kraken.com/0/public/Assets?key=secret"):
            with self.subTest(url=url), self.assertRaises(c.Unavailable):
                c.transport_guard(url)
        for kwargs in ({"method": "POST"}, {"body": "x"}, {"headers": {"API-Key": "secret"}}):
            with self.assertRaises(c.Unavailable):
                c.transport_guard("https://api.kraken.com/0/public/Assets", **kwargs)

    def test_no_network_at_import(self):
        with patch("urllib.request.urlopen", side_effect=AssertionError("network")):
            importlib.reload(c)

    def test_only_expected_ccxt_methods_called_and_exceptions_propagate(self):
        calls = []

        class FakeExchange:
            def load_markets(self):
                calls.append("load_markets")

            def market(self, symbol):
                calls.append("market")
                return fixtures(symbol)[2]

            def fetch_ohlcv(self, symbol, **kwargs):
                self.expected = kwargs
                calls.append("fetch_ohlcv")
                if kwargs != {"timeframe": "1h", "since": (NOW // c.HOUR - 48) * c.HOUR * 1000,
                              "limit": 49, "params": {"paginate": False}}:
                    raise AssertionError("unexpected fetch parameters")
                return fixtures(symbol)[1]

            def __getattr__(self, name):
                raise AssertionError("unexpected capability accessed")

        result = c.run_live(FakeExchange(), lambda symbol, since: fixtures(symbol)[0], NOW, lambda *a: None)
        self.assertEqual(result["status"], "ALL_THREE_PUBLIC_COMPARISONS_PASS")
        self.assertEqual(calls.count("fetch_ohlcv"), 3)
        with patch.object(FakeExchange, "fetch_ohlcv", side_effect=RuntimeError("sensitive body")):
            with self.assertRaises(RuntimeError):
                c.run_live(FakeExchange(), lambda symbol, since: fixtures(symbol)[0], NOW, lambda *a: None)

    def test_failure_is_redacted_and_never_returns_prices(self):
        fake = types.SimpleNamespace(load_markets=lambda: (_ for _ in ()).throw(RuntimeError("secret-response")))
        with tempfile.TemporaryDirectory() as output, patch.object(c, "public_exchange", return_value=fake), \
             patch("urllib.request.urlopen", side_effect=AssertionError("unexpected network")), \
             contextlib.redirect_stdout(io.StringIO()) as stdout:
            self.assertEqual(c.execute(Path(output)), 1)
            text = stdout.getvalue()
            self.assertNotIn("secret-response", text)
            result = json.loads((Path(output) / "comparison-result.json").read_text())
            self.assertEqual(result["status"], "DATA_UNAVAILABLE")
            self.assertNotIn("comparisons", result)

    def test_rate_limit_timeout_and_exchange_errors_are_not_retried(self):
        for name in ("RateLimitExceeded", "RequestTimeout", "ExchangeNotAvailable"):
            error = type(name, (Exception,), {})
            load = unittest.mock.Mock(side_effect=error("private diagnostic must not appear"))
            fake = types.SimpleNamespace(load_markets=load)
            with tempfile.TemporaryDirectory() as output, patch.object(c, "public_exchange", return_value=fake), \
                 contextlib.redirect_stdout(io.StringIO()) as stdout:
                self.assertEqual(c.execute(Path(output)), 1)
                load.assert_called_once()
                result = json.loads(stdout.getvalue())
                self.assertEqual(result["error_type"], name)
                self.assertEqual(result["status"], "DATA_UNAVAILABLE")
                self.assertNotIn("private diagnostic", stdout.getvalue())


if __name__ == "__main__":
    unittest.main()
