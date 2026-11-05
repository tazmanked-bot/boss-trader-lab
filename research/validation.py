"""Fail-closed numerical assertions; standard library only."""
from __future__ import annotations

import math
from numbers import Real


def number(value, label: str) -> float:
    # Do not silently coerce strings, booleans, None or complex values.
    if isinstance(value, bool) or not isinstance(value, Real):
        raise AssertionError(f"{label}: expected a real number, got {value!r}")
    try:
        return float(value)
    except (ValueError, TypeError, OverflowError) as exc:
        raise AssertionError(f"{label}: invalid real number") from exc


def finite(value, label: str) -> float:
    value = number(value, label)
    if not math.isfinite(value):
        raise AssertionError(f"{label}: non-finite value")
    return value


def compare_series(actual, expected, *, first_valid: int,
                   tolerance: float, label: str) -> dict:
    """Assert the exact NaN prefix and EVERY subsequent finite value.

    first_valid is an explicit contract, not inferred from either series.
    A successful return always means the comparison passed; errors raise.
    """
    actual, expected = list(actual), list(expected)
    tolerance = finite(tolerance, f"{label} tolerance")
    if tolerance < 0:
        raise AssertionError(f"{label}: negative tolerance")
    if len(actual) != len(expected) or not actual:
        raise AssertionError(f"{label}: empty or unequal series lengths")
    if (isinstance(first_valid, bool) or not isinstance(first_valid, int)
            or not 0 <= first_valid < len(actual)):
        raise AssertionError(f"{label}: invalid first-valid position")
    differences = []
    for i, (left, right) in enumerate(zip(actual, expected)):
        if i < first_valid:
            if not (math.isnan(number(left, f"{label} actual[{i}]"))
                    and math.isnan(number(right, f"{label} reference[{i}]"))):
                raise AssertionError(f"{label}[{i}]: expected warmup NaN")
        else:
            left = finite(left, f"{label} actual[{i}]")
            right = finite(right, f"{label} reference[{i}]")
            delta = finite(abs(left - right), f"{label} difference[{i}]")
            if delta > tolerance:
                raise AssertionError(f"{label}[{i}]: delta={delta} > {tolerance}")
            differences.append(delta)
    return {"first_valid_index": first_valid,
            "warmup_nan_count": first_valid,
            "compared_finite_values": len(differences),
            "max_absolute_delta": max(differences),
            "absolute_tolerance": tolerance,
            "within_tolerance": True,
            "actual_last": finite(actual[-1], label),
            "reference_last": finite(expected[-1], label)}
