"""Optional Issue #2 public-data comparison. No import-time network or fallback."""
from __future__ import annotations

import argparse
from decimal import Decimal, InvalidOperation
import importlib.metadata as metadata
import json
import math
from pathlib import Path
import time
from urllib.parse import parse_qs, urlencode, urlparse
from urllib.request import HTTPRedirectHandler, Request, build_opener

VERSION = "4.5.92"
HOUR = 3600
MIN_OVERLAP = 21
PAIRS = {
    "BTC/USD": {"request": "XBTUSD", "id": "XXBTZUSD", "base": "BTC"},
    "XRP/USD": {"request": "XRPUSD", "id": "XXRPZUSD", "base": "XRP"},
    "SOL/USD": {"request": "SOLUSD", "id": "SOLUSD", "base": "SOL"},
}
PUBLIC_PATHS = {"/0/public/Assets", "/0/public/AssetPairs", "/0/public/OHLC"}


class Unavailable(ValueError):
    """A failed comparison must not return usable observations."""


class PublicBudget:
    def __init__(self):
        self.calls = 0
        self.last = None

    def before(self):
        self.calls += 1
        if self.calls > 15:
            raise Unavailable("total public request budget exceeded")
        if self.last is not None:
            time.sleep(max(0, 1.0 - (time.monotonic() - self.last)))
        self.last = time.monotonic()


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise Unavailable("public request redirect blocked")


def decimal_number(value, *, positive=True):
    if isinstance(value, bool) or not isinstance(value, (str, int, float, Decimal)):
        raise Unavailable("invalid numeric type")
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError):
        raise Unavailable("invalid number") from None
    if not result.is_finite() or (result <= 0 if positive else result < 0):
        raise Unavailable("invalid numeric range")
    return result


def integer(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise Unavailable("invalid timestamp type")
    try:
        valid = math.isfinite(value) and int(value) == value
    except (ValueError, OverflowError):
        valid = False
    if not valid:
        raise Unavailable("invalid timestamp")
    return int(value)


def symbol_spec(symbol):
    if symbol not in PAIRS:
        raise Unavailable("symbol outside spot USD allowlist")
    return PAIRS[symbol]


def transport_guard(url, method="GET", headers=None, body=None):
    parsed = urlparse(url)
    if (method != "GET" or body is not None or parsed.scheme != "https"
            or parsed.hostname != "api.kraken.com" or parsed.port not in (None, 443)
            or parsed.username or parsed.password or parsed.fragment
            or parsed.path not in PUBLIC_PATHS):
        raise Unavailable("non-public transport blocked")
    for key in headers or {}:
        if key.lower() in {"authorization", "api-key", "api-sign", "cookie"}:
            raise Unavailable("credential header blocked")
    query = parse_qs(parsed.query, keep_blank_values=True)
    if parsed.path == "/0/public/OHLC":
        if (set(query) - {"pair", "interval", "since"}
                or query.get("pair") not in [[s["id"]] for s in PAIRS.values()]
                + [[s["request"]] for s in PAIRS.values()]
                or query.get("interval") != ["60"]):
            raise Unavailable("non-allowlisted OHLC request")
    elif query:
        raise Unavailable("unexpected market-discovery parameters")


def market_mapping(market, symbol):
    spec = symbol_spec(symbol)
    if not isinstance(market, dict):
        raise Unavailable("market missing")
    required = {"symbol": symbol, "id": spec["id"], "base": spec["base"],
                "quote": "USD", "type": "spot", "spot": True,
                "contract": False, "swap": False, "future": False, "active": True}
    if any(market.get(key) != value or
           (isinstance(value, bool) and type(market.get(key)) is not bool)
           for key, value in required.items()):
        raise Unavailable("market mapping mismatch")
    if market.get("settle") is not None:
        raise Unavailable("settled contract not permitted")
    # Some spot markets also advertise margin availability. No margin option
    # or method is used; the required market type remains spot.
    return decimal_number(market.get("precision", {}).get("price"))


def normalize(rows, now, *, milliseconds=False):
    now = integer(now)
    if not isinstance(rows, list) or not rows:
        raise Unavailable("missing OHLCV")
    closed = {}
    previous = None
    discarded = 0
    for row in rows:
        if not isinstance(row, list) or len(row) != 6:
            raise Unavailable("malformed OHLCV row")
        timestamp = integer(row[0])
        if milliseconds:
            if timestamp % 1000:
                raise Unavailable("fractional-second CCXT timestamp")
            timestamp //= 1000
        if timestamp < 0 or timestamp % HOUR or timestamp > now // HOUR * HOUR:
            raise Unavailable("unaligned, future or wrong-unit timestamp")
        if previous is not None and timestamp - previous != HOUR:
            raise Unavailable("duplicate, unordered or missing hourly candle")
        previous = timestamp
        opening, high, low, close = [decimal_number(v) for v in row[1:5]]
        decimal_number(row[5], positive=False)
        if low > min(opening, close) or high < max(opening, close) or low > high:
            raise Unavailable("inconsistent OHLC bounds")
        if timestamp + HOUR <= now:
            closed[timestamp] = close
        else:
            discarded += 1
    if len(closed) < MIN_OVERLAP:
        raise Unavailable("insufficient closed candles")
    if max(closed) != (now // HOUR - 1) * HOUR:
        raise Unavailable("latest completed UTC candle missing or stale")
    return closed, {"received": len(rows), "closed": len(closed),
                    "unfinished_discarded": discarded}


def parse_raw(payload, symbol, now):
    spec = symbol_spec(symbol)
    if not isinstance(payload, dict) or payload.get("error") != []:
        raise Unavailable("invalid Kraken envelope")
    result = payload.get("result")
    if not isinstance(result, dict) or set(result) - {"last"} != {spec["id"]}:
        raise Unavailable("Kraken pair response mismatch")
    rows = result[spec["id"]]
    if not isinstance(rows, list) or not rows:
        raise Unavailable("missing Kraken rows")
    converted = []
    for row in rows:
        if not isinstance(row, list) or len(row) != 8:
            raise Unavailable("malformed Kraken row")
        decimal_number(row[5], positive=False)  # VWAP is not CCXT volume.
        if integer(row[7]) < 0:
            raise Unavailable("negative trade count")
        converted.append([row[0], *row[1:5], row[6]])
    # Kraken documents a final, always-present uncommitted row.
    if integer(converted[-1][0]) != now // HOUR * HOUR:
        raise Unavailable("missing current Kraken row or sampling hour changed")
    normalized, counts = normalize(converted, now)
    from kraken_public_observer import parse_closed_candles
    baseline = parse_closed_candles(payload, now)
    if baseline != [float(v) for v in normalized.values()]:
        raise Unavailable("working-adapter close sequence differs")
    return normalized, counts


def compare(raw, ccxt_rows, market, symbol, now):
    tick = market_mapping(market, symbol)
    left, raw_counts = parse_raw(raw, symbol, now)
    right, ccxt_counts = normalize(ccxt_rows, now, milliseconds=True)
    overlap = sorted(set(left) & set(right))
    if len(overlap) < MIN_OVERLAP:
        raise Unavailable("insufficient overlapping closed timestamps")
    # CCXT's inspected parser converts strings to numbers without quantizing.
    # Allow floating representation noise only, capped at 1e-6 of one tick.
    tolerance = min(Decimal("1e-8"), tick * Decimal("0.000001"))
    differences = [abs(left[t] - right[t]) for t in overlap]
    if any(delta > tolerance for delta in differences):
        raise Unavailable("overlapping closed-price discrepancy")
    return {"symbol": symbol, "request_pair": PAIRS[symbol]["request"],
            "market_id": market["id"], "interval": "1h", "timestamp_unit": "UTC seconds",
            "raw_counts": raw_counts, "ccxt_counts": ccxt_counts,
            "overlapping_closed_count": len(overlap), "first_utc_seconds": overlap[0],
            "last_utc_seconds": overlap[-1], "tick_size_usd": str(tick),
            "absolute_close_tolerance_usd": str(tolerance),
            "max_close_delta_usd": str(max(differences)),
            "status": "PUBLIC_DATA_PARITY_PASS", "decision": "HOLD_OWNER_REVIEW"}


def public_exchange(budget=None):
    import ccxt
    if metadata.version("ccxt") != VERSION:
        raise Unavailable("unreviewed CCXT version")

    class PublicKraken(ccxt.kraken):
        calls = 0

        def request(self, path, api="public", method="GET", params=None,
                    headers=None, body=None, config=None):
            if api != "public" or path not in {"Assets", "AssetPairs", "OHLC"} or method != "GET":
                raise Unavailable("non-public API blocked")
            return super().request(path, api, method, params, headers, body, config or {})

        def fetch(self, url, method="GET", headers=None, body=None):
            transport_guard(url, method, headers, body)
            self.calls += 1
            if self.calls > 12:
                raise Unavailable("public request budget exceeded")
            if budget is not None:
                budget.before()
            return super().fetch(url, method, headers, body)

    exchange = PublicKraken({"enableRateLimit": True, "timeout": 12000, "verbose": False,
                             "maxRetriesOnFailure": 0,
                             "options": {"adjustForTimeDifference": False,
                                         "maxRetriesOnFailure": 0}})
    if exchange.precisionMode != ccxt.TICK_SIZE:
        raise Unavailable("price precision convention changed")
    # Requests raises on the first redirect rather than following a new host/path.
    exchange.session.max_redirects = 0
    return exchange


def run_live(exchange, fetch_raw, now, save):
    exchange.load_markets()
    reports = []
    since_seconds = (now // HOUR - 48) * HOUR
    for symbol in PAIRS:
        market = exchange.market(symbol)
        market_mapping(market, symbol)
        raw = fetch_raw(symbol, since_seconds)
        save(symbol.replace("/", "-") + "-raw.json", raw)
        rows = exchange.fetch_ohlcv(symbol, timeframe="1h", since=since_seconds * 1000,
                                    limit=49, params={"paginate": False})
        save(symbol.replace("/", "-") + "-ccxt.json", rows)
        report = compare(raw, rows, market, symbol, now)
        reports.append(report)
    return {"status": "ALL_THREE_PUBLIC_COMPARISONS_PASS", "observed_at_utc_seconds": now,
            "ccxt_version": VERSION, "comparisons": reports, "orders": "DISABLED",
            "recommendation": "HOLD", "production_adapter": "UNCHANGED"}


def execute(output):
    output.mkdir(parents=True, exist_ok=True)
    budget = PublicBudget()
    opener = build_opener(NoRedirect())  # retains inherited proxy/TLS policy

    def save(name, data):
        (output / name).write_text(json.dumps(data, indent=2, allow_nan=False) + "\n")

    def fetch_raw(symbol, since):
        url = "https://api.kraken.com/0/public/OHLC?" + urlencode(
            {"pair": PAIRS[symbol]["request"], "interval": 60, "since": since})
        transport_guard(url)
        budget.before()
        with opener.open(Request(url, headers={"User-Agent": "boss-trader-lab-issue-2/1"}), timeout=12) as response:
            if urlparse(response.url).netloc != "api.kraken.com":
                raise Unavailable("unexpected public response redirect")
            return json.load(response)

    try:
        result = run_live(public_exchange(budget), fetch_raw, int(time.time()), save)
        result["public_request_count"] = budget.calls
    except Exception as exc:
        # Exception messages can contain URLs, response bodies or arbitrary input.
        # Do not echo them; never substitute synthetic prices on failure.
        result = {"status": "DATA_UNAVAILABLE", "error_type": type(exc).__name__,
                  "orders": "DISABLED", "recommendation": "HOLD"}
        save("comparison-result.json", result)
        print(json.dumps(result))
        return 1
    save("comparison-result.json", result)
    print(json.dumps(result, indent=2, allow_nan=False))
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true", required=True,
                        help="Explicitly authorize public Kraken endpoints only")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    return execute(args.output)


if __name__ == "__main__":
    raise SystemExit(main())
