"""Read-only Kraken spot USD candles for manual GitHub Actions diagnostics.

Not equivalent to Binance USDT candles. No order endpoints, credentials or signals.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from boss_trader_lab import sma

API = "https://api.kraken.com/0/public/OHLC"
PAIRS = {"BTC": "XBTUSD", "XRP": "XRPUSD", "SOL": "SOLUSD"}
INTERVAL_SECONDS = 3600


def parse_closed_candles(payload: object, now_seconds: int) -> list[float]:
    """Validate Kraken payload and discard the uncommitted final candle."""
    if not isinstance(payload, dict) or payload.get("error") != []:
        raise ValueError("Kraken API returned errors or invalid envelope")
    result = payload.get("result")
    if not isinstance(result, dict):
        raise ValueError("Kraken result missing")
    keys = [key for key in result if key != "last"]
    if len(keys) != 1 or not isinstance(result[keys[0]], list):
        raise ValueError("Kraken OHLC pair response invalid")
    candles = result[keys[0]]
    if len(candles) < 22:
        raise ValueError("fewer than 21 closed OHLC candles")
    # Kraken always includes the current uncommitted candle as the final item.
    completed = candles[:-1]
    if len(completed) < 21:
        raise ValueError("insufficient completed candles")
    closes: list[float] = []
    previous_timestamp: int | None = None
    for candle in completed:
        if not isinstance(candle, list) or len(candle) < 5:
            raise ValueError("malformed candle")
        timestamp = int(candle[0])
        close = float(candle[4])
        if not math.isfinite(close) or close <= 0:
            raise ValueError("nonpositive or nonfinite candle close")
        if previous_timestamp is not None and timestamp <= previous_timestamp:
            raise ValueError("out-of-order or duplicate timestamps")
        if timestamp + INTERVAL_SECONDS > now_seconds + 60:
            raise ValueError("uncommitted candle in completed series")
        previous_timestamp = timestamp
        closes.append(close)
    if now_seconds - (previous_timestamp + INTERVAL_SECONDS) > 3 * INTERVAL_SECONDS:
        raise ValueError("latest closed candle is stale")
    return closes


def fetch(symbol: str) -> list[float]:
    if symbol not in PAIRS:
        raise ValueError("symbol not on allowlist")
    url = API + "?" + urlencode({"pair": PAIRS[symbol], "interval": 60})
    request = Request(url, headers={"User-Agent": "boss-trader-lab-public-research/0.1"})
    with urlopen(request, timeout=12) as response:
        payload = json.load(response)
    return parse_closed_candles(payload, int(time.time()))


def main() -> int:
    parser = argparse.ArgumentParser(description="Manual Kraken public USD observation")
    parser.add_argument("--symbol", choices=sorted(PAIRS), required=True)
    args = parser.parse_args()
    try:
        candles = fetch(args.symbol)
        last = candles[-1]
        output = {
            "source": "Kraken public spot OHLC",
            "pair": f"{args.symbol}/USD",
            "source_pair": PAIRS[args.symbol],
            "interval": "1h",
            "status": "OBSERVE_ONLY",
            "last_closed_price_usd": round(last, 8),
            "change_last_bar_pct": round((last / candles[-2] - 1) * 100, 3),
            "sma_5_usd": round(sma(candles, 5), 8),
            "sma_20_usd": round(sma(candles, 20), 8),
            "warning": "Kraken USD differs from Binance USDT; not a trading entry.",
        }
        print(json.dumps(output, indent=2))
        return 0
    except (ValueError, TypeError, KeyError, OverflowError, HTTPError, URLError,
            TimeoutError, OSError, json.JSONDecodeError) as exc:
        print(f"DATA_UNAVAILABLE: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
