# Issue #1: corrected synthetic indicator validation

Status: corrective development for Audit-002; **integration remains HOLD**.
PR #4 stays draft and unmerged. Nothing here imports research into the observer,
changes Kraken, fetches market data, schedules work, produces signals or orders.

## Acceptance contract

All positions are zero-based on finite contiguous OHLC input. The reference
arithmetic imports neither pandas nor pandas-ta-classic. The library side uses
`talib=False`. Assertions check equal lengths, the entire preceding NaN mask,
the first valid value and **every** subsequent finite value. No tail-only gate.

| Indicator | First valid index | Definition | Absolute tolerance |
| --- | ---: | --- | ---: |
| SMA(20) | 19 | Arithmetic mean of 20 closes | 1e-8 |
| EMA(20) | 19 | First 20 closes seed; alpha=2/21 recursion | 1e-8 |
| RSI(14) | 14 | Mean gains/losses of first 14 changes; alpha=1/14 recursion | 1e-6 |
| ATR(14) | 14 | First 14 true ranges (bars 1..14) seed; alpha=1/14 recursion | 1e-6 |
| MACD(12,26,9) line | 25 | Independently seeded EMA12 minus EMA26 | 1e-6 |
| MACD signal | 33 | Mean of first nine valid line values, then alpha=2/10 | 1e-6 |
| MACD histogram | 33 | Line minus signal | 1e-6 |

These are the existing strict tolerances, now applied from initialization.
No relative tolerance or equal-NaN option can conceal an unexpected invalid value.
The finite-input scope is deliberate: missing input data is rejected by the
references. Future missing-input propagation policies need separate review.

## RSI initialization and flat-price policy

The former reference averaged 13 changes at index 13 because it included the
leading diff NaN in a 14-position slice and skipped NaN. That emits an extra RSI
one bar early. Its next step happens to equal the 14-change seed for contiguous
input, so tail agreement did not validate initialization.

The corrected reference explicitly seeds with 14 actual changes, first valid at
index 14. This follows the SMA-seeded Wilder contract and the upstream RMA source
inspected in Audit-002; it is not dynamically selected to match installed output.
The earlier claim that the 13-change seed described upstream 0.9.0 was not
established for the installed wheel. Source-tag/wheel correspondence is still
unverified. If the wheel emits index 13, the test must fail for owner review.

RSI is 100 for all gains and 0 for all losses. Flat prices make the mathematical
ratio 0/0 undefined; **0 is an explicit compatibility policy**, supported by the
upstream RSI source inspected in Audit-002, rather than a mathematical identity.
The former reference's 50 convention is no longer silently treated as equivalent.
The flat fixture asserts this decision. Any wheel discrepancy fails; do not
change the oracle automatically or widen tolerances.

Source references inspected for the audit:
- https://github.com/xgboosted/pandas-ta-classic/blob/0.9.0/pandas_ta_classic/overlap/rma.py
- https://github.com/xgboosted/pandas-ta-classic/blob/0.9.0/pandas_ta_classic/momentum/rsi.py
- https://github.com/xgboosted/pandas-ta-classic/blob/0.9.0/pandas_ta_classic/volatility/atr.py

## ATR and MACD conventions

The adjusted, normalized EWM ATR reference was a different definition; it has
been replaced by the explicit SMA-seeded recursive Wilder contract above. This
is justified by the selected ATR/RMA definition, not by the old passing tail.
True range starts at bar 1 because it requires a previous close. Gapped OHLC
fixtures exercise the previous-close terms. Flat OHLC has zero true range.

MACD fast and slow EMAs seed on their own windows. The signal seeds only after
nine finite MACD values. A different TA-Lib/native alignment is a discrepancy,
not permission to choose whichever convention produces green output.

## Tests and execution

Dependency-free regressions cover invalid actual AND reference values, warmup
corruption, wrong first-valid positions, empty/all-NaN/mismatched series, invalid
tolerances, overflowing differences and numerical corruption at seed/middle/tail.
Hand-calculated SMA/EMA/RMA/RSI/ATR examples and a rising MACD example check the
references separately. Each indicator is deliberately corrupted in regressions.

GitHub Actions must verify the installed library against five deterministic
180-bar fixtures: oscillating, flat, rising, falling and gapped. All seven output
series are checked on all five fixtures. The existing baseline tests run first.

Commands for an authorized temporary GitHub Actions runner only:

```sh
git rev-parse HEAD
python -m unittest discover -s tests -v
python -m pip install --disable-pip-version-check 'pandas-ta-classic==0.9.0'
python -m pip check
python -m pip freeze --all
python -m research.indicator_parity
python -m research.independent_indicator_review
```

The independent entry point also runs the corruption regressions, preserving
coverage when existing owner launchers invoke it. Failures exit nonzero; output
uses strict JSON (`allow_nan=False`). Missing packages fail rather than skip.
No Cloud-shell package installation or network workaround is authorized.

The existing manual launcher on main checks out
`research/issue-1-indicator-parity`; select it only after confirming the intended
commit. Record the checkout SHA, not just the launcher's main-branch SHA. Do not
rerun an old job and assume it tests a new commit. No merge is required to run the
existing owner launcher. No workflow was dispatched by this correction.

## Evidence gates

- [x] Fail-closed full-series validator and negative regressions written.
- [x] Explicit RSI/ATR/MACD initialization contracts and pure reference examples.
- [ ] Owner-run corrected GitHub Actions results tied to the new commit.
- [ ] Investigate any wheel/source or convention discrepancy without weakening tests.
- [ ] Complete distribution hash lock and license/security reviews described in
  [dependency evidence](issue-1-dependency-evidence.md).
- [ ] Owner reviews exact versions, fixtures, tolerances and actual results.
- [ ] Separate integration approval; no automatic promotion or Issue #1 closure.

Successful synthetic parity is not evidence of profitability or market performance.
