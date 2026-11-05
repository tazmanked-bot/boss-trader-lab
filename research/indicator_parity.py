"""Isolated offline pandas-ta-classic evaluation. NO MARKET DATA OR ORDERS.

Tests numerical parity of SMA and EMA against independent Python definitions.
RSI, MACD and ATR are reported with explicit finite/warmup checks; their
reference-formula parity remains a separate acceptance gate.
"""
from __future__ import annotations

import json
import math
import statistics
import importlib.metadata as metadata

import pandas as pd
import pandas_ta_classic as ta

from boss_trader_lab import sma as boss_sma


def synthetic_ohlc(n: int = 180) -> pd.DataFrame:
    # Fully synthetic deterministic data, positive with variation, no network.
    close = [100 + i * .035 + 3 * math.sin(i * .23) + 1.5 * math.cos(i * .51)
             for i in range(n)]
    return pd.DataFrame({
        "open": [c - .1 for c in close],
        "high": [c + .8 for c in close],
        "low": [c - .9 for c in close],
        "close": close,
        "volume": [1000 + 20 * (i % 7) for i in range(n)],
    })


def reference_ema(values: list[float], length: int) -> list[float]:
    # Explicit SMA-seeded EMA, as used by pandas-ta's native EMA formulation.
    output = [float("nan")] * len(values)
    seed = sum(values[:length]) / length
    output[length - 1] = seed
    alpha = 2 / (length + 1)
    for i in range(length, len(values)):
        output[i] = alpha * values[i] + (1 - alpha) * output[i - 1]
    return output


def latest(series) -> float:
    if series is None:
        raise AssertionError("indicator returned None")
    value = float(series.iloc[-1])
    if not math.isfinite(value):
        raise AssertionError("indicator last value is non-finite")
    return value


def evaluate() -> dict:
    df = synthetic_ohlc()
    closes = df["close"].tolist()
    sma20 = ta.sma(df["close"], length=20, talib=False)
    ema20 = ta.ema(df["close"], length=20, talib=False)
    rsi14 = ta.rsi(df["close"], length=14, talib=False)
    macd = ta.macd(df["close"], fast=12, slow=26, signal=9, talib=False)
    atr14 = ta.atr(df["high"], df["low"], df["close"], length=14, talib=False)
    if not isinstance(macd, pd.DataFrame) or macd.shape[1] < 3:
        raise AssertionError("MACD expected a three-column DataFrame")
    # All published indicator values must be finite after adequate warm-up.
    for name, series in [("SMA_20", sma20), ("EMA_20", ema20),
                         ("RSI_14", rsi14), ("ATR_14", atr14)]:
        latest(series)
    macd_last = {col: latest(macd[col]) for col in macd.columns}
    # Compare 20 recent completed synthetic bars. Avoid first-bar seed mismatches.
    ema_reference = reference_ema(closes, 20)
    sma_delta = max(abs(float(sma20.iloc[i]) - boss_sma(closes[:i+1], 20))
                    for i in range(len(closes) - 20, len(closes)))
    ema_delta = max(abs(float(ema20.iloc[i]) - ema_reference[i])
                    for i in range(len(closes) - 20, len(closes)))
    tol = 1e-8
    if sma_delta > tol or ema_delta > tol:
        raise AssertionError(f"indicator parity discrepancy SMA={sma_delta}, EMA={ema_delta}")
    result = {
        "mode": "OFFLINE_SYNTHETIC_ONLY",
        "status": "PARTIAL_PARITY_PASS_REVIEW_REQUIRED",
        "package": "pandas-ta-classic",
        "version": metadata.version("pandas-ta-classic"),
        "pandas_version": pd.__version__,
        "fixture_bars": len(closes),
        "sma_20_max_absolute_delta": sma_delta,
        "ema_20_max_absolute_delta": ema_delta,
        "rsi_14_last": latest(rsi14),
        "atr_14_last": latest(atr14),
        "macd_last": macd_last,
        "remaining_gates": ["RSI formula parity", "MACD series parity",
                            "ATR smoothing parity", "warmup/NaN review",
                            "reproducible transitive dependency lock"],
        "orders": "DISABLED",
        "signals": "DISABLED",
    }
    return result


if __name__ == "__main__":
    print(json.dumps(evaluate(), indent=2))
