"""Full-series, boundary-sensitive library comparisons. Synthetic data only."""
from __future__ import annotations

import importlib.metadata as metadata
import json
import platform
import unittest

from research.reference_indicators import (
    reference_atr, reference_ema, reference_macd, reference_rsi, reference_sma,
)
from research.indicator_parity import synthetic_ohlc
from research.validation import compare_series

TOLERANCE = 1e-6  # Audit-002 tolerance retained, applied to every valid bar.


def evaluate_case(kind):
    import pandas_ta_classic as ta

    frame = synthetic_ohlc(kind=kind)
    close = frame["close"].tolist()
    rsi = ta.rsi(frame["close"], length=14, talib=False)
    atr = ta.atr(frame["high"], frame["low"], frame["close"],
                 length=14, mamode="rma", talib=False)
    macd = ta.macd(frame["close"], fast=12, slow=26, signal=9, talib=False)
    if rsi is None or atr is None or macd is None:
        raise AssertionError(f"{kind}: missing indicator output")
    if list(macd.columns) != ["MACD_12_26_9", "MACDh_12_26_9", "MACDs_12_26_9"]:
        raise AssertionError(f"{kind}: unexpected MACD columns {list(macd.columns)}")
    line, signal, histogram = reference_macd(close)
    comparisons = {
        "SMA_20": (ta.sma(frame["close"], length=20, talib=False),
                   reference_sma(close, 20), 19),
        "EMA_20": (ta.ema(frame["close"], length=20, talib=False),
                   reference_ema(close, 20), 19),
        "RSI_14": (rsi.tolist(), reference_rsi(close), 14),
        "ATR_14": (atr.tolist(), reference_atr(frame["high"].tolist(),
                   frame["low"].tolist(), close), 14),
        "MACD_LINE": (macd.iloc[:, 0].tolist(), line, 25),
        "MACD_SIGNAL": (macd.iloc[:, 2].tolist(), signal, 33),
        "MACD_HISTOGRAM": (macd.iloc[:, 1].tolist(), histogram, 33),
    }
    return {label: compare_series(actual, expected, first_valid=first,
                                  tolerance=1e-8 if label in {"SMA_20", "EMA_20"}
                                  else TOLERANCE, label=f"{kind} {label}")
            for label, (actual, expected, first) in comparisons.items()}


def evaluate():
    version = metadata.version("pandas-ta-classic")
    if version != "0.9.0":
        raise AssertionError(f"unreviewed pandas-ta-classic version: {version}")
    checks = {kind: evaluate_case(kind) for kind in
              ("oscillating", "flat", "rising", "falling", "gaps")}
    packages = {name: metadata.version(name) for name in
                ("pandas-ta-classic", "pandas", "numpy", "python-dateutil", "tzdata")}
    return {"status": "FULL_SERIES_SYNTHETIC_PARITY_PASS",
            "python_version": platform.python_version(), "packages": packages,
            "checks": checks, "mode": "SYNTHETIC_ONLY", "orders": "DISABLED",
            "owner_approval": "REQUIRED", "integration_readiness": "HOLD"}


def main():
    # Existing owner launchers already invoke this entry point. Run negative
    # tests here as well so they cannot accidentally omit the regression gate.
    suite = unittest.defaultTestLoader.discover(
        "tests", pattern="test_indicator_validation.py")
    if suite.countTestCases() == 0:
        raise AssertionError("validator regression tests were not discovered")
    if not unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful():
        return 1
    try:
        result = evaluate()
    except AssertionError as exc:
        print(json.dumps({"status": "FAIL", "reason": str(exc)}, allow_nan=False))
        return 1
    print(json.dumps(result, indent=2, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
