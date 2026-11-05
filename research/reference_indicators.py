"""Independent arithmetic references on finite, contiguous synthetic inputs.

No pandas or pandas-ta-classic calls. Flat RSI=0 is an explicit compatibility
policy for the undefined 0/0 case; see docs/issue-1-test-plan.md.
"""
from __future__ import annotations

import math

from research.validation import finite


def _input(values, length):
    if isinstance(length, bool) or not isinstance(length, int) or length < 1:
        raise ValueError("length must be a positive integer")
    return [finite(value, f"input[{i}]") for i, value in enumerate(values)]


def reference_sma(values, length):
    values = _input(values, length)
    return [float("nan") if i < length - 1 else
            sum(values[i - length + 1:i + 1]) / length
            for i in range(len(values))]


def _seeded_average(values, length, alpha):
    values = _input(values, length)
    output = [float("nan")] * len(values)
    if len(values) < length:
        return output
    output[length - 1] = sum(values[:length]) / length
    for i in range(length, len(values)):
        output[i] = (1 - alpha) * output[i - 1] + alpha * values[i]
    return output


def reference_ema(values, length):
    _input([], length)
    return _seeded_average(values, length, 2 / (length + 1))


def reference_wilder(values, length):
    _input([], length)
    return _seeded_average(values, length, 1 / length)


def reference_rsi(closes, length=14):
    closes = _input(closes, length)
    delta = [closes[i] - closes[i - 1] for i in range(1, len(closes))]
    gains = reference_wilder([max(value, 0.0) for value in delta], length)
    losses = reference_wilder([max(-value, 0.0) for value in delta], length)
    output = [float("nan")] * len(closes)
    for i in range(length, len(closes)):
        gain, loss = gains[i - 1], losses[i - 1]
        output[i] = 0.0 if gain + loss == 0 else 100 * gain / (gain + loss)
    return output


def reference_atr(high, low, close, length=14):
    high, low, close = (_input(values, length) for values in (high, low, close))
    if not len(high) == len(low) == len(close):
        raise ValueError("OHLC lengths differ")
    for h, l, c in zip(high, low, close):
        if not l <= c <= h:
            raise ValueError("invalid synthetic OHLC bar")
    ranges = [max(high[i] - low[i], abs(high[i] - close[i - 1]),
                  abs(low[i] - close[i - 1])) for i in range(1, len(close))]
    return ([float("nan")] + reference_wilder(ranges, length)) if close else []


def reference_macd(close):
    close = _input(close, 26)
    fast, slow = reference_ema(close, 12), reference_ema(close, 26)
    line = [f - s for f, s in zip(fast, slow)]
    signal = ([float("nan")] * min(25, len(close))
              + reference_ema(line[25:], 9))
    histogram = [m - s for m, s in zip(line, signal)]
    return line, signal, histogram


def synthetic_values(n=180, kind="oscillating"):
    if kind == "oscillating":
        close = [100 + i * .035 + 3 * math.sin(i * .23)
                 + 1.5 * math.cos(i * .51) for i in range(n)]
    elif kind == "flat":
        close = [100.0] * n
    elif kind == "rising":
        close = [100.0 + i for i in range(n)]
    elif kind == "falling":
        close = [300.0 - i for i in range(n)]
    elif kind == "gaps":
        close = [100 + (12 if i % 4 < 2 else -12) + (i % 7) for i in range(n)]
    else:
        raise ValueError(f"unknown fixture: {kind}")
    # Flat bars deliberately have zero true range (including high-low).
    high = close.copy() if kind == "flat" else [c + .8 for c in close]
    low = close.copy() if kind == "flat" else [c - .9 for c in close]
    opening = close.copy() if kind == "flat" else [c - .1 for c in close]
    return {"open": opening, "high": high, "low": low, "close": close,
            "volume": [1000 + 20 * (i % 7) for i in range(n)]}
