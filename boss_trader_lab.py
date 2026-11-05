"""BOSS Trader Lab: read-only public-market observation prototype.

No credentials, account access, trading orders, or financial advice.
Python 3.11+ standard library only.
"""
from __future__ import annotations
import argparse
import json
import sys
from datetime import datetime, timezone
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

BINANCE_KLINES = "https://api.binance.com/api/v3/klines"
DEFAULT_PAIRS = ("BTCUSDT", "XRPUSDT", "SOLUSDT")
ALLOWED_PAIRS = frozenset(DEFAULT_PAIRS + ("ETHUSDT", "LINKUSDT", "INJUSDT", "NEARUSDT"))
MAX_CANDLES = 30


def sma(values: list[float], period: int) -> float:
    if period < 1 or len(values) < period:
        raise ValueError("insufficient candles for SMA")
    return sum(values[-period:]) / period


def observe(symbol: str, closes: list[float]) -> dict:
    """Return deterministic, non-actionable observations; never trade signals."""
    if symbol not in ALLOWED_PAIRS:
        raise ValueError("symbol outside explicit spot allowlist")
    if len(closes) < 21 or any(p <= 0 for p in closes):
        raise ValueError("need 21+ positive closing prices")
    last, previous = closes[-1], closes[-2]
    short, long = sma(closes, 5), sma(closes, 20)
    change = (last / previous - 1) * 100
    return {
        "symbol": symbol, "status": "OBSERVE_ONLY",
        "last_close": round(last, 8),
        "change_last_bar_pct": round(change, 3),
        "sma_5": round(short, 8), "sma_20": round(long, 8),
        "above_sma20": last > long,
        "disclaimer": "Not an entry recommendation; manual research only.",
    }


def fetch_closed_closes(symbol: str) -> list[float]:
    if symbol not in ALLOWED_PAIRS:
        raise ValueError("symbol outside explicit spot allowlist")
    url = BINANCE_KLINES + "?" + urlencode({"symbol": symbol, "interval": "1h", "limit": MAX_CANDLES})
    request = Request(url, headers={"User-Agent": "boss-trader-lab-research/0.1"})
    with urlopen(request, timeout=12) as response:
        data = json.load(response)
    if not isinstance(data, list) or len(data) < 22:
        raise ValueError("unexpected candle payload")
    now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
    closed = [float(candle[4]) for candle in data if len(candle) > 6 and int(candle[6]) < now_ms]
    if len(closed) < 21:
        raise ValueError("not enough closed candles")
    return closed


def main() -> int:
    parser = argparse.ArgumentParser(description="Read-only BOSS Trader observation prototype")
    parser.add_argument("--live", action="store_true", help="Fetch public Binance spot candles; default is offline sample")
    parser.add_argument("--symbol", choices=sorted(ALLOWED_PAIRS), default="BTCUSDT")
    args = parser.parse_args()
    try:
        if args.live:
            closes = fetch_closed_closes(args.symbol)
            mode = "public_live_data"
        else:
            closes = [100 + i * 0.1 + ((i % 5) - 2) * 0.05 for i in range(26)]
            mode = "synthetic_offline_fixture"
        result = observe(args.symbol, closes)
        print(json.dumps({"timestamp_utc": datetime.now(timezone.utc).isoformat(), "mode": mode, **result}, indent=2))
        return 0
    except (ValueError, HTTPError, URLError, TimeoutError, OSError, json.JSONDecodeError) as exc:
        print(f"SCAN_UNAVAILABLE: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
