"""Independent, offline numerical cross-check; diagnostics only, no trading.

Formula definitions are deliberately separate from pandas-ta-classic. Differences
remain review items rather than silently changing indicator definitions.
"""
from __future__ import annotations

import json
import math

import pandas_ta_classic as ta
from research.indicator_parity import synthetic_ohlc, reference_ema

PERIOD = 14
TAIL = 20
TOLERANCE = 1e-6


def adjusted_wilder(values: list[float], length: int) -> list[float]:
    """Wilder alpha=1/length with normalized exponentially weighted history.

    This is the adjusted-EWM convention; it is NOT asserted equivalent to
    SMA-seeded Wilder smoothing without comparing actual results.
    """
    alpha = 1 / length
    numerator = denominator = 0.0
    result = []
    for i, value in enumerate(values):
        numerator = value + (1 - alpha) * numerator
        denominator = 1 + (1 - alpha) * denominator
        result.append(numerator / denominator if i >= length - 1 else float("nan"))
    return result


def reference_rsi(closes: list[float], length: int = PERIOD) -> list[float]:
    delta = [closes[i] - closes[i - 1] for i in range(1, len(closes))]
    gains = [max(x, 0.0) for x in delta]
    losses = [max(-x, 0.0) for x in delta]
    avg_gains = adjusted_wilder(gains, length)
    avg_losses = adjusted_wilder(losses, length)
    result = [float("nan")]
    for gain, loss in zip(avg_gains, avg_losses):
        if not math.isfinite(gain) or not math.isfinite(loss):
            result.append(float("nan"))
        elif gain + loss == 0:
            result.append(50.0)
        else:
            result.append(100.0 * gain / (gain + loss))
    return result


def reference_atr(high: list[float], low: list[float],
                  close: list[float], length: int = PERIOD) -> list[float]:
    true_range = [float("nan")]
    for i in range(1, len(close)):
        true_range.append(max(high[i] - low[i],
                              abs(high[i] - close[i - 1]),
                              abs(low[i] - close[i - 1])))
    # First bar excluded: TA true-range implementations may vary at boundary.
    return [float("nan")] + adjusted_wilder(true_range[1:], length)


def reference_macd(close: list[float]):
    fast, slow, signal = 12, 26, 9
    fast_ema = reference_ema(close, fast)
    slow_ema = reference_ema(close, slow)
    macd = [f - s if math.isfinite(f) and math.isfinite(s) else float("nan")
            for f, s in zip(fast_ema, slow_ema)]
    non_nan = macd[slow - 1:]
    signal_line = [float("nan")] * (slow - 1) + reference_ema(non_nan, signal)
    histogram = [m - s if math.isfinite(m) and math.isfinite(s) else float("nan")
                 for m, s in zip(macd, signal_line)]
    return macd, histogram, signal_line


def discrepancy(actual, expected, label: str) -> dict:
    if len(actual) != len(expected):
        raise AssertionError(f"{label}: series length mismatch")
    a = [float(x) for x in actual[-TAIL:]]
    e = [float(x) for x in expected[-TAIL:]]
    if not all(math.isfinite(x) for x in a + e):
        raise AssertionError(f"{label}: non-finite value after warmup")
    delta = max(abs(x - y) for x, y in zip(a, e))
    return {"max_abs_diff_last_20": delta,
            "within_tolerance": delta <= TOLERANCE,
            "actual_last": a[-1],
            "reference_last": e[-1]}


def main():
    frame = synthetic_ohlc()
    close = frame["close"].tolist()
    high = frame["high"].tolist()
    low = frame["low"].tolist()
    rsi = ta.rsi(frame["close"], length=14, talib=False)
    atr = ta.atr(frame["high"], frame["low"], frame["close"],
                 length=14, talib=False)
    macd = ta.macd(frame["close"], fast=12, slow=26, signal=9, talib=False)
    if rsi is None or atr is None or macd is None:
        raise AssertionError("missing indicator output")
    ref_m, ref_h, ref_s = reference_macd(close)
    columns = {str(column).split("_")[0]: column for column in macd.columns}
    if set(columns) != {"MACD", "MACDh", "MACDs"}:
        raise AssertionError(f"unexpected MACD column identifiers: {list(macd.columns)}")
    reports = {
        "RSI_14": discrepancy(rsi.to_list(), reference_rsi(close), "RSI"),
        "ATR_14": discrepancy(atr.to_list(), reference_atr(high, low, close), "ATR"),
        "MACD_12_26_9": discrepancy(macd[columns["MACD"]].to_list(), ref_m, "MACD"),
        "MACD_HISTOGRAM": discrepancy(macd[columns["MACDh"]].to_list(), ref_h, "MACDh"),
        "MACD_SIGNAL": discrepancy(macd[columns["MACDs"]].to_list(), ref_s, "MACDs"),
    }
    passed = all(row["within_tolerance"] for row in reports.values())
    print(json.dumps({
        "mode": "SYNTHETIC_ONLY",
        "status": "CANDIDATE_PARITY" if passed else "DISCREPANCY_REQUIRES_REVIEW",
        "reference_conventions": "normalized adjusted-Wilder RSI/ATR; SMA-seeded EMA MACD",
        "warning": "Even matching values require independent warmup and library-version review.",
        "checks": reports,
        "owner_approval": "REQUIRED",
        "orders": "DISABLED"
    }, indent=2))
    # Return success to record diagnostic discrepancies without blocking evidence capture.
    # Discrepancy MUST NOT be interpreted as parity approval.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
