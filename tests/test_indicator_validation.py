"""Dependency-free regressions for fail-closed indicator validation."""
import math
import unittest

from research.reference_indicators import (
    reference_atr, reference_ema, reference_macd, reference_rsi,
    reference_sma, reference_wilder, synthetic_values,
)
from research.validation import compare_series


class ValidatorTests(unittest.TestCase):
    def check(self, actual, expected, first=2, tolerance=1e-8):
        return compare_series(actual, expected, first_valid=first,
                              tolerance=tolerance, label="regression")

    def test_valid_series(self):
        values = [math.nan, math.nan, 1.0, 2.0, 3.0]
        self.assertEqual(self.check(values, values)["compared_finite_values"], 3)

    def test_corruption_at_every_valid_position_on_both_sides(self):
        values = [math.nan, math.nan, 1.0, 2.0, 3.0]
        for side in ("actual", "reference"):
            for position in range(2, len(values)):
                for bad in (math.nan, math.inf, -math.inf, None, "1", True,
                            1 + 0j, object(), 10 ** 1000):
                    with self.subTest(side=side, position=position, bad=repr(bad)):
                        corrupted = values.copy()
                        corrupted[position] = bad
                        args = (corrupted, values) if side == "actual" else (values, corrupted)
                        with self.assertRaises(AssertionError):
                            self.check(*args)

    def test_warmup_corruption_and_wrong_first_valid(self):
        values = [math.nan, math.nan, 1.0, 2.0]
        for position in (0, 1):
            for bad in (0.0, math.inf, None, "nan", False):
                corrupted = values.copy()
                corrupted[position] = bad
                with self.subTest(position=position, bad=bad):
                    with self.assertRaises(AssertionError):
                        self.check(corrupted, values)
                    with self.assertRaises(AssertionError):
                        self.check(values, corrupted)
        for first in (0, 1, 3):
            with self.assertRaises(AssertionError):
                self.check(values, values, first=first)

    def test_all_nan_empty_and_length_mismatch(self):
        for actual, expected in (([], []), ([math.nan] * 4, [math.nan] * 4),
                                 ([math.nan] * 3, [math.nan] * 4)):
            with self.assertRaises(AssertionError):
                self.check(actual, expected)

    def test_errors_in_initialization_middle_and_tail_fail(self):
        values = [math.nan] * 19 + [100.0] * 161
        for position in (19, 20, 90, 160, 179):
            corrupted = values.copy()
            corrupted[position] += 1e-5
            with self.assertRaises(AssertionError):
                self.check(corrupted, values, first=19)

    def test_invalid_tolerance_and_position(self):
        for tolerance in (math.nan, math.inf, -1.0, "0.1", True):
            with self.assertRaises(AssertionError):
                self.check([1.0], [1.0], first=0, tolerance=tolerance)
        for first in (-1, 1, True, 0.0):
            with self.assertRaises(AssertionError):
                self.check([1.0], [1.0], first=first)

    def test_overflowed_difference_fails(self):
        with self.assertRaises(AssertionError):
            self.check([1e308], [-1e308], first=0)


class ReferenceTests(unittest.TestCase):
    def test_hand_calculated_sma_ema_wilder(self):
        self.assertEqual(reference_sma([1, 2, 3, 7], 3)[2:], [2.0, 4.0])
        self.assertEqual(reference_ema([1, 2, 3, 7], 3)[2:], [2.0, 4.5])
        self.assertAlmostEqual(reference_wilder([1, 2, 3, 7], 3)[3], 11 / 3)

    def test_rsi_hand_calculated_seed_and_recursion(self):
        # Changes +2,-1,+2,-1: two-change seed gain=1, loss=.5.
        result = reference_rsi([10, 12, 11, 13, 12], 2)
        self.assertTrue(all(math.isnan(x) for x in result[:2]))
        self.assertAlmostEqual(result[2], 100 * 1 / 1.5)
        self.assertAlmostEqual(result[3], 100 * 1.5 / 1.75)
        self.assertAlmostEqual(result[4], 100 * .75 / 1.375)

    def test_rsi_flat_rising_falling(self):
        for kind, expected in (("flat", 0.0), ("rising", 100.0), ("falling", 0.0)):
            values = reference_rsi(synthetic_values(kind=kind)["close"])
            self.assertTrue(all(math.isnan(x) for x in values[:14]))
            self.assertTrue(all(x == expected for x in values[14:]))

    def test_legacy_rsi_early_value_fails_even_with_identical_tail(self):
        reference = reference_rsi(synthetic_values()["close"])
        legacy = reference.copy()
        legacy[13] = 60.78833338291324
        with self.assertRaises(AssertionError):
            compare_series(legacy, reference, first_valid=14,
                           tolerance=1e-6, label="legacy RSI warmup")

    def test_adjusted_atr_convention_cannot_pass_seed_comparison(self):
        # For TR=[3,6,2] and length=2, adjusted EWM first value=5,
        # unlike the required SMA seed=4.5. Later convergence cannot hide it.
        reference = reference_atr([11, 13, 18, 17], [9, 11, 16, 15], [10, 12, 17, 16], 2)
        adjusted = [math.nan, math.nan, 5.0, 23 / 7]
        with self.assertRaises(AssertionError):
            compare_series(adjusted, reference, first_valid=2,
                           tolerance=1e-6, label="adjusted ATR")

    def test_atr_hand_calculated_gap_seed_and_smoothing(self):
        # TR bars 1..3 = 3, 6, 2. Seed after two TRs=4.5, next RMA=3.25.
        result = reference_atr([11, 13, 18, 17], [9, 11, 16, 15], [10, 12, 17, 16], 2)
        self.assertTrue(all(math.isnan(x) for x in result[:2]))
        self.assertEqual(result[2:], [4.5, 3.25])

    def test_all_indicator_first_valid_positions(self):
        fixture = synthetic_values()
        close = fixture["close"]
        line, signal, histogram = reference_macd(close)
        series = [(reference_sma(close, 20), 19), (reference_ema(close, 20), 19),
                  (reference_rsi(close), 14),
                  (reference_atr(fixture["high"], fixture["low"], close), 14),
                  (line, 25), (signal, 33), (histogram, 33)]
        for values, first in series:
            with self.subTest(first=first):
                self.assertEqual(next(i for i, v in enumerate(values) if math.isfinite(v)), first)
                compare_series(values, values, first_valid=first, tolerance=1e-8, label="reference")

    def test_macd_rising_hand_calculated_and_histogram_identity(self):
        line, signal, histogram = reference_macd(list(range(180)))
        for values, first, expected in ((line, 25, 7.0), (signal, 33, 7.0),
                                         (histogram, 33, 0.0)):
            for value in values[first:]:
                self.assertAlmostEqual(value, expected, delta=1e-12)

    def test_corrupt_each_indicator_at_seed_middle_and_last(self):
        fixture = synthetic_values()
        close = fixture["close"]
        line, signal, histogram = reference_macd(close)
        cases = [("SMA", reference_sma(close, 20), 19, 1e-8),
                 ("EMA", reference_ema(close, 20), 19, 1e-8),
                 ("RSI", reference_rsi(close), 14, 1e-6),
                 ("ATR", reference_atr(fixture["high"], fixture["low"], close), 14, 1e-6),
                 ("MACD", line, 25, 1e-6), ("SIGNAL", signal, 33, 1e-6),
                 ("HISTOGRAM", histogram, 33, 1e-6)]
        for label, values, first, tolerance in cases:
            for position in (first, 90, 179):
                for bad in (math.nan, math.inf, -math.inf, None, "bad",
                            values[position] + 10 * tolerance):
                    with self.subTest(indicator=label, position=position, bad=bad):
                        corrupted = values.copy()
                        corrupted[position] = bad
                        with self.assertRaises(AssertionError):
                            compare_series(corrupted, values, first_valid=first,
                                           tolerance=tolerance, label=label)

    def test_short_inputs_do_not_invent_seeds(self):
        for size in (0, 1, 13):
            close = [100.0] * size
            for values in (reference_sma(close, 20), reference_ema(close, 20),
                           reference_rsi(close), reference_atr(close, close, close),
                           *reference_macd(close)):
                self.assertEqual(len(values), size)
                self.assertTrue(all(math.isnan(value) for value in values))

    def test_reference_inputs_reject_nonfinite(self):
        for value in (math.nan, math.inf, None, "100", True):
            with self.assertRaises(AssertionError):
                reference_rsi([100.0, value])


if __name__ == "__main__":
    unittest.main()
