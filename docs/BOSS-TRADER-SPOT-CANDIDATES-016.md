# BOSS-TRADER-SPOT-CANDIDATES-016

Issue: [#26](https://github.com/tazmanked-bot/boss-trader-lab/issues/26).
Baseline: `955dbcb90207049178c94f8e6cd3a3c593ebe52d` (owner-merged PR #25).
Disposition: **PASS for isolated deterministic synthetic prototype review; HOLD for strategy validity, operational use or trading.** Operational Test Mode remains NOT APPROVED.

## Scope and provenance

Four additions only:

- `research/spot_reversal_candidates.py`: optional stdlib-only evaluator and explicit local-file CLI.
- `tests/test_spot_reversal_candidates.py`: standalone unittest regressions and deliberate negative cases.
- `tests/fixtures/spot_reversal_candidates_016.json`: explicitly `SYNTHETIC_ONLY` normalized hourly OHLCV.
- This report.

No baseline file is changed. In particular the working Kraken observer, scanner, registry, bridge, diagnostic, probe corrections, workflows and dependency files remain unchanged. No market/time-service requests, clock-service commands, workflow dispatch, installations, VM work, trading, alerts, schedules, credentials or ZUMERAVO access form part of this work. GitHub connector reads/writes are used for issue/source retrieval and publishing the research branch and draft PR only.

The fixture contains exactly 21 bars for each of BTC/USD, XRP/USD and SOL/USD, Kraken spot USD, 1h. Its explicit as_of is `1900000800` (`2030-03-17T18:00:00Z`), an arbitrary historical-replay coordinate, **not the current time**. Every last bar closes exactly at that coordinate. All three deliberately use identical invented prices/volumes to exercise deterministic ties; these are not plausible asset price claims, collected Kraken data or an authenticated exchange capture.

Fixture SHA-256: `8cd0a1900daab49b936dc5fe8f23c5839b5d60e5ee47079d1947883e735f7faa`.
This hash identifies bytes, not market provenance or a software security clearance.
The synthetic label is enforced as input vocabulary but remains a caller assertion. This evaluator cannot authenticate the provenance of supplied values and has no live-data adapter.

## Baseline source inspection

All references below are pinned to the issue baseline, not inferred from a green workflow:

| Source | Verified contract and consequence |
| --- | --- |
| [Registry](https://github.com/tazmanked-bot/boss-trader-lab/blob/955dbcb90207049178c94f8e6cd3a3c593ebe52d/research/spot_refusal_registry.py), `validate_symbol`, `validate_symbols`, `_policy` | Exact identity/rules, integer aligned UTC seconds, 21+ closed contiguous bars, no duplicate/reordered timestamps, positive finite prices, nonnegative finite volume, 512-row cap, per-symbol three-hour relative freshness, explicit reject/as_of policies. Called unchanged before features. |
| [Bridge](https://github.com/tazmanked-bot/boss-trader-lab/blob/955dbcb90207049178c94f8e6cd3a3c593ebe52d/research/kraken_spot_validation_bridge.py), `validate_capture` | Eight-field Kraken-shaped rows, exact pair metadata, decimal/precision checks, registry delegation. New fixtures already use the normalized registry schema; the new evaluator does not implement a second raw-Kraken parser, invoke a transport, or claim to validate exchange provenance. The existing bridge remains separate and unchanged. |
| [Registry design](https://github.com/tazmanked-bot/boss-trader-lab/blob/955dbcb90207049178c94f8e6cd3a3c593ebe52d/docs/BOSS-TRADER-OFFLINE-REFUSAL-009.md) | Distinct strict rejection and explicit as_of projection contracts; no repair or automatic time selection. |
| [Indicator references](https://github.com/tazmanked-bot/boss-trader-lab/blob/955dbcb90207049178c94f8e6cd3a3c593ebe52d/research/reference_indicators.py), `reference_macd`, `reference_rsi`, `reference_atr` | MACD signal/histogram first finite index 33, thus unavailable from only 21 bars. RSI/ATR have explicit initialization conventions. This prototype uses none of these indicators and makes no pandas-ta-classic or scanner-indicator compatibility claim. |
| [Indicator regressions](https://github.com/tazmanked-bot/boss-trader-lab/blob/955dbcb90207049178c94f8e6cd3a3c593ebe52d/tests/test_indicator_validation.py) | Existing initialization, warmup and nonfinite regressions remain in the full-suite verification. Passing those does not validate this new heuristic's predictive value. |
| [Actual Kraken observer](https://github.com/tazmanked-bot/boss-trader-lab/blob/955dbcb90207049178c94f8e6cd3a3c593ebe52d/kraken_public_observer.py), `parse_closed_candles`, `fetch`, `main` | Existing XBTUSD/XRPUSD/SOLUSD mappings; public-network observer with its own final-row removal, 60-second tolerance, 21-close and stale checks, OBSERVE_ONLY/SMA output. Not invoked, imported or modified by the new module. The new registry-backed contract is not represented as identical to that parser. |
| [Scanner baseline](https://github.com/tazmanked-bot/boss-trader-lab/blob/955dbcb90207049178c94f8e6cd3a3c593ebe52d/boss_trader_lab.py), `observe`, `fetch_closed_closes` | Binance USDT baseline, 21 closes, SMA5/20 and last-bar change. This research uses Kraken USD normalized candles; it neither replaces that scanner nor equates USD with USDT. |
| [B4/B5 report](https://github.com/tazmanked-bot/boss-trader-lab/blob/955dbcb90207049178c94f8e6cd3a3c593ebe52d/docs/BOSS-TRADER-B4-B5-FEASIBILITY-015.md) | Independent UTC and target-runner limitations remain. A fixture coordinate is not trusted live UTC. No clock/data policy is activated here. |

## Input, validation and refusal precedence

`evaluate(fixture)` accepts ordinary JSON-shaped builtins for offline fixture convenience. `evaluate_json(text)` is the supported bounded serialized boundary. Neither is a sandbox for arbitrary Python objects or concurrent mutation of caller-owned objects.

The envelope has exactly `version`, `label`, `as_of`, `policy`, `payloads`. Version is `spot-reversal-research-v1`; label is exactly `SYNTHETIC_ONLY`. Policy must explicitly contain exactly the registry's `version: spot-refusal-v1` and `future_mode: as_of` or `reject`. No implicit policy/default, feature configuration, user score or rank is accepted.

`payloads` is a map of the three allowlisted symbols to the existing exact registry schema (`symbol`, `venue`, `market`, `quote`, `timeframe`, `rules`, `bars`). Missing symbols independently refuse DATA_UNAVAILABLE. Unknown symbol keys or malformed map types refuse all, as defined by `validate_symbols`. No new aliases or symbol normalization are introduced.

Every symbol is processed in this order:

1. Call unchanged `registry.validate_symbols` with the exact supplied as_of and policy.
2. A REFUSED symbol becomes BLOCKED with the original registry decision/evidence; features and score are null. No feature calculation is attempted, including for malformed/stale symbols with otherwise attractive recent bars.
3. Only a VALIDATED_DATA symbol is projected to `open_time + 3600 <= as_of`, preserving input order. All eligible history, including history before the last 21, has already been validated. There is no sorting, gap filling, fabricated price, shifting as_of or tail-only validation.
4. Calculate features; all four predicates are necessary for WATCH. A valid but unqualified symbol is WAIT regardless of any positive feature score.
5. Rank WATCH symbols only; never force one candidate.

An invalid outer envelope/serialization has no trusted coordinate; `input_error` reports MALFORMED_DATA (or DATA_UNAVAILABLE on local-file read failure), all symbols BLOCKED, null scores and empty candidates. Their registry context refusal remains TIMESTAMP_INVALID with null as_of because no valid context was accepted. The evaluator does **not** invent an as_of to change that refusal. Valid envelopes retain per-symbol registry reasons; unknown policies use CONFIG_INVALID. Raw errors/input strings are not echoed.

JSON input is capped at 786432 UTF-8 bytes (three registry-sized inputs); duplicate keys, nonfinite literals, numeric overflow such as `1e999`, invalid encoding and recursive parser failures block the envelope. Each symbol retains the registry's 512-row cap and numeric bound of `1e100`. The canonical output is capped at 16384 ASCII bytes, containing only bounded numbers, booleans, fixed text, fixed symbols, context and evidence hashes, never raw candle arrays. The Python convenience API retains registry row/numeric bounds but does not promise a pre-serialization byte cap or hostile-object isolation.

## Exact research features

All indices below refer to the **eligible**, fully validated series, using Python negative indices; `-1` is the last closed bar. The registry's 21 bars exceed the largest feature history requirement (16 bars); there is no reduced warmup. Prices are `c` (close), `l` (low), `o` (open), and volumes `v`.

Calculations use stdlib `Fraction` on validated numeric values: integers are exact; floats represent their exact binary value, not a rounded decimal interpretation. There is no tolerance that changes a failed predicate into PASS. For example float `98.98` is slightly greater than the exact rational `98*101/100`, so that boundary refuses the low-hold feature; a dedicated test records this. The exact inclusive boundary is separately tested with integer prices (anchor 9800, upper band 9898). This conservative edge behavior is documented, not concealed by formula adjustment.

Let `B(x) = floor(10000 * min(1,max(0,x)))`, an integer strength in [0,10000]. It is a **shape-ranking unit, not probability, confidence, return or percentage chance**. A failed predicate has strength zero. Features are:

| Feature | Necessary predicate | Strength when passed | Research motivation |
| --- | --- | --- | --- |
| slowing_downside | `c[-6] > c[-5] > c[-4] > c[-3]` and `0 < d2 < d1`, with `d1=c[-5]-c[-4]`, `d2=c[-4]-c[-3]` | `B(1-d2/d1)` | Requires an actual preceding decline whose last measured drop slowed, rather than an uninterrupted rally. |
| low_retest_hold | `a=min(l[-6:-2])`; both `l[-2]` and `l[-1]` lie in `[a, 101*a/100]` | `B(1-100*(max(l[-2:])-a)/a)` | Last two lows revisit a prior four-bar low without breaking it, within a fixed 1% research band. No future pivot confirmation. |
| fresh_recovery | `c[-2] <= c[-3]`, `c[-2] < c[-1] <= c[-4]`, and `c[-1] > o[-1]` | `B((c[-1]-c[-2])/(c[-4]-c[-2]))` | Most recent close begins a recovery, while remaining at/below the earlier pre-slowdown close; limits momentum chasing. Denominator is strictly positive whenever this predicate holds. |
| volume_consistent | `m=sum(v[-16:-2])/14`; `0 < v[-2] <= m <= v[-1] <= 2*m`, and `v[-1] >= v[-2]` | `B(v[-1]/m-1)` | Prior-bar volume contracted versus an earlier 14-bar mean; recovery volume is not weaker and not an extreme >2x spike. Zero baseline/previous volume cannot qualify. |

The 1% band, 14-bar mean, 2x ceiling and equal-weight shape ranking are fixed **unvalidated research choices**, not empirically optimized parameters, approved scanner safety limits or evidence of an edge. They need separate scientific evaluation. No formula was changed to make library outputs agree; no library is used. No price levels derived from fixtures are presented as live levels, entry zones or targets.

WATCH requires the conjunction of all four predicates. Score is their strength sum, an integer in [0,40000]. WAIT may have a positive diagnostic score but cannot enter the candidate list. BLOCKED always has null score/features. A fresh BTC result cannot replace or rescue stale XRP/SOL.

Sorting uses `(-score, symbol)` on WATCH only, with exact fixed ASCII symbols; ties resolve BTC/USD, SOL/USD, XRP/USD. Output has 0–3 unique candidates, without a minimum. No user score override, multiplier, rank field, configuration or extra schema key is accepted. An unsupported injected score blocks at the corresponding schema boundary.

Each symbol retains validation evidence plus passed/strength evidence for every calculated feature, decision, score, catalyst_status UNVERIFIED, and (for WATCH only) a fixed why_early and invalidation_observation. The latter describes a later eligible low breaking the observed retest anchor as invalidating the **research condition**; it neither sets an order nor watches future markets. The anchor is reconstructible from the supplied fixture and registry evidence hash, not broadcast as an entry/stop price. The top-level warning states WATCH is not ENTRY READY, BUY authorization or an instruction to trade.

## Causality and projection boundary

The fixture's frozen as_of never changes. A bar closing exactly at as_of is eligible. A bar opening at as_of closes later and is ineligible. In explicit as_of mode, every row still needs exact keys and a supported aligned integer timestamp; only then are ineligible OHLCV ignored, exactly as in the registry. No future row count, ignored value, cursor or timestamp is added to the output/evidence. Neither relative staleness nor history requirements are bypassed.

For WATCH, WAIT and BLOCKED base cases, tests compare **complete canonical JSON equality**, including decisions, features, scores, candidates and hashes, after appending structurally valid future rows to all three symbols. Appended OHLCV include negative numbers, very large finite values, nulls, strings and objects. Both Python and strict JSON entry points are checked. Eligible corruption still refuses.

This invariant is conditional, not a promise for arbitrary appended bytes: malformed future structure/timestamps, exceeding the 512 total rows or serialized byte limit, duplicate JSON keys, nonfinite JSON and invalid encoding may change the output to a refusal. Strict `reject` mode intentionally refuses any future/unfinished bar. These exceptions are explicit existing projection contracts, not lookahead signals. No data is silently sorted or repaired.

## Deterministic evidence and acceptance matrix

Local runtime: CPython **3.12.14**, standard library only, no installation. Python 3.11 execution and a current-head GitHub Actions run are **UNVERIFIED**; they are owner next steps, not inferred from baseline workflow history.

Commands and final results:

```text
python -B -m unittest discover -s tests -p test_spot_reversal_candidates.py -v
Ran 32 tests in 0.179s
OK

python -B -m unittest discover -s tests -v
Ran 216 tests in 3.136s
OK

python -B -m research.spot_reversal_candidates tests/fixtures/spot_reversal_candidates_016.json
exit 0; canonical SYNTHETIC_ONLY output
candidates=["BTC/USD","SOL/USD","XRP/USD"]
each score=26666; each catalyst_status=UNVERIFIED
each strength: slowing=5000, low=10000, recovery=6666, volume=5000
```

Full suite: **184 unchanged baseline tests + 32 new tests = 216**, no skips. Timing is local elapsed unittest reporting, not a runner deadline, performance guarantee or target-host benchmark. The CLI's exit 0 means only that no symbol is BLOCKED; a valid zero-candidate/WAIT report also succeeds. Any BLOCKED symbol produces exit 2. CLI success never implies a WATCH candidate is required or actionable.

| Requirement | Test evidence (`tests/test_spot_reversal_candidates.py`) | Result |
| --- | --- | --- |
| Hand-computable features; maximum three; tie order | `test_three_watch_hand_calculated_features_and_lexical_tie` | PASS |
| Zero permitted; exact 0,1,2,3 cases; unique listing | `test_zero_one_two_three_candidates_without_minimum` | PASS |
| Score order before stable symbol tie; input-order independence | `test_rank_descending_score_then_symbol_not_input_order` | PASS |
| Flat/rally not early reversal; no chase | `test_flat_and_uninterrupted_rally_wait`, `test_no_momentum_chase_past_prior_close` | PASS |
| Every predicate required; no positive partial score override | `test_each_feature_is_required_even_with_other_high_strengths` | PASS |
| Contradictory/zero/extreme volume waits | `test_volume_contradictions_zero_and_excess_spike_wait` | PASS |
| Exact inclusive bands; binary float conservatism | `test_feature_boundary_conditions`, `test_binary_float_boundary_is_not_rounded_to_a_pass` | PASS |
| Per-symbol stale refusal, 3h boundary and no rescue | `test_stale_refusal_is_per_symbol_not_overridden_by_fresh_btc`, `test_stale_boundary_three_hours_allowed_four_refused` | PASS |
| Feature calculation never sees refused input | `test_refused_symbols_never_reach_features` (feature function raises if called) | PASS |
| Nonfinite/type/negative/zero price and price-bound failures | `test_invalid_prices_nonfinite_types_all_positions`, `test_price_bounds_refuse` | PASS |
| Duplicate/gap/reversed data refuse; no repair | `test_duplicates_gaps_and_order_refuse_no_repair` | PASS |
| 20 refused, 21 accepted, 22 checked including oldest corruption | `test_insufficient_history_and_entire_history_validation` | PASS |
| Exact identity and conflicting rules | `test_market_identity_and_rule_conflicts` | PASS |
| Score injection at envelope/payload/bar/policy; unknown symbols/policies | `test_score_injection_at_every_layer_fails`, `test_unknown_symbols_and_missing_symbols`, `test_unknown_missing_and_implicit_policy_fail` | PASS |
| Synthetic label enforced | `test_synthetic_label_required_not_live_provenance` | PASS for vocabulary; provenance remains unverified by design |
| Entire canonical output invariant after future append | `test_asof_complete_output_equality_after_adversarial_future_append` | PASS under stated contract |
| Future boundary and strict-mode refusal; no warmup bypass | `test_future_close_boundary_asof_strict_and_no_warmup_bypass` | PASS |
| Future headers cannot conceal malformed input | `test_malformed_future_headers_refuse` | PASS |
| Invalid as_of not guessed; row/JSON bounds enforced | `test_invalid_explicit_asof_never_guessed_or_shifted`, `test_row_cap_includes_excluded_future_rows`, `test_bounded_json_duplicates_nonfinite_and_no_exception_echo` | PASS |
| Finite extreme values do not overflow score arithmetic | `test_extreme_finite_values_do_not_overflow_feature_math` | PASS |
| Deterministic output, no input mutation, evidence sensitivity | `test_determinism_no_mutation_bounded_summary_and_evidence_sensitivity` | PASS |
| Import/evaluation no network, wall-clock or subprocess calls | Every new test guards socket/socket connection/DNS, urlopen, HTTPSConnection, subprocess.run/Popen and time.time; cleanup asserts zero calls. Dedicated reload test also passes. | PASS for guarded calls; no claim of hostile-code sandboxing |
| Explicit local-file CLI, canonical output, redacted failure | `test_cli_only_reads_explicit_fixture_and_prints_canonical_output`, `test_cli_read_failure_is_redacted_and_exits_blocked` | PASS |
| Existing behavior regression suite | Full 216-test command above | PASS locally |
| Predictive ranking, profit, live execution readiness | Not evaluated or authorized | HOLD |

The tests establish deterministic implementation behavior and safety contracts, not empirical feature validity. Baseline tests retain their existing offline mocks and local worker lifecycle checks; no actual Kraken/time-service transport test is introduced. No cryptographic package audit, indicator-library revalidation, clock attestation or runner guarantee is claimed.

## Remaining limitations and smallest safe owner action

1. Review the exact draft head, source formulas, synthetic fixtures and negative cases. The head commit is recorded in the PR handoff (the commit cannot self-embed its own hash). Proposed acceptance is only isolated offline research integration review.
2. Authorize a **manual offline GitHub Actions check pinned to that exact PR head**, running the two unittest commands above and the explicit synthetic CLI, under owner-reviewed network restrictions. No workflow file or dispatch is added here; avoid reusing an old pinned launcher and assuming it tests the new head. Verify actual checkout SHA, Python version, counts, no skips and unchanged protected files in that run. This is the smallest safe owner action.
3. Keep the strategy hypothesis on HOLD: no calibration, independent market dataset, liquidity/spread/slippage model, catalyst verification, backtest profitability, positions or paper trading are supplied. More varied owner-reviewed synthetic counterexamples may improve contract coverage without changing any data/safety policy. A WATCH is only a deterministic pattern in supplied synthetic data.
4. Any later supervised read-only scanner test requires a separate approval after B4/B5 are resolved or an alternative data-only clock policy is explicitly adopted. This prototype does not resolve those blockers. Operational Test Mode is NOT APPROVED.
5. Research, scientific evaluation and any eventual paper trading remain separately approved stages. No trading, order authority, credentials, targets, alerts or scheduled checks are implied by this draft.

**STOP FOR OWNER AND BOSS AI REVIEW.**
