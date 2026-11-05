"""Strict SMA/EMA comparison on synthetic data only; no network or orders."""
from __future__ import annotations

import importlib.metadata as metadata
import json

from research.reference_indicators import reference_ema, reference_sma, synthetic_values
from research.validation import compare_series


def synthetic_ohlc(n=180, kind="oscillating"):
    import pandas as pd
    return pd.DataFrame(synthetic_values(n, kind))


def evaluate():
    import pandas_ta_classic as ta
    from boss_trader_lab import sma as boss_sma

    version = metadata.version("pandas-ta-classic")
    if version != "0.9.0":
        raise AssertionError(f"unreviewed pandas-ta-classic version: {version}")
    frame = synthetic_ohlc()
    close = frame["close"].tolist()
    expected_sma = reference_sma(close, 20)
    boss = [float("nan")] * 19 + [boss_sma(close[:i + 1], 20)
                                    for i in range(19, len(close))]
    checks = {
        "SMA_20_BOSS": compare_series(boss, expected_sma, first_valid=19,
                                      tolerance=1e-8, label="BOSS SMA"),
        "SMA_20": compare_series(ta.sma(frame["close"], length=20, talib=False),
                                 expected_sma, first_valid=19,
                                 tolerance=1e-8, label="SMA"),
        "EMA_20": compare_series(ta.ema(frame["close"], length=20, talib=False),
                                 reference_ema(close, 20), first_valid=19,
                                 tolerance=1e-8, label="EMA"),
    }
    return {"mode": "OFFLINE_SYNTHETIC_ONLY", "status": "SMA_EMA_PARITY_PASS",
            "package_version": version, "fixture_bars": len(close),
            "checks": checks, "owner_approval": "REQUIRED", "orders": "DISABLED"}


if __name__ == "__main__":
    print(json.dumps(evaluate(), indent=2, allow_nan=False))
