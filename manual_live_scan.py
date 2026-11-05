"""Manually invoked public-data scan. Research observations only, never orders."""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from urllib.error import HTTPError, URLError

from boss_trader_lab import observe, fetch_closed_closes

UNIVERSES = {
    "core": ("BTCUSDT", "XRPUSDT", "SOLUSDT"),
    "expanded": ("BTCUSDT", "XRPUSDT", "SOLUSDT", "ETHUSDT", "LINKUSDT", "INJUSDT", "NEARUSDT"),
}


def run_scan(universe: str) -> tuple[dict, int]:
    if universe not in UNIVERSES:
        raise ValueError("unapproved universe")
    output = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "source": "Binance public spot 1h closed candles",
        "universe": universe,
        "status": "UNVERIFIED",
        "trading_authorization": "NONE",
        "research_only": True,
        "observations": [],
        "errors": [],
    }
    for symbol in UNIVERSES[universe]:
        try:
            result = observe(symbol, fetch_closed_closes(symbol))
            output["observations"].append(result)
        except (ValueError, HTTPError, URLError, TimeoutError, OSError, json.JSONDecodeError) as exc:
            output["errors"].append({"symbol": symbol, "reason": type(exc).__name__})
    # Fail closed: incomplete data invalidates the entire run; no partial success claims.
    complete = not output["errors"] and len(output["observations"]) == len(UNIVERSES[universe])
    output["status"] = "OBSERVE_ONLY" if complete else "DATA_UNAVAILABLE"
    return output, 0 if complete else 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Manual, read-only public market observations")
    parser.add_argument("--universe", choices=tuple(UNIVERSES), default="core")
    args = parser.parse_args()
    result, code = run_scan(args.universe)
    print(json.dumps(result, indent=2))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
