# BOSS-TRADER-SPOT-REPLAY-019

Authority: [Issue #32](https://github.com/tazmanked-bot/boss-trader-lab/issues/32).
Verified baseline main: **`436fe420d4718d2c0e0cef48e4ae9a84b0e46749`**, owner merge of PR #31.
Harness: `spot-reversal-replay-v1`; generator: `original-synthetic-regimes-v1`.

**Verdict: PASS for isolated synthetic harness validation and independent review. NO empirical strategy claims. NO REAL DATA.** Economic outcomes are NOT_COMPUTED; Operational Test Mode stays HOLD. Strict B4 UTC remains NO-GO; the alternative historical observation policy remains PROPOSED/HOLD. Offline replay neither needs nor activates either collection policy.

Four additions only:

- `research/spot_reversal_replay.py` — optional stdlib-only bounded generator, qualification, chronological replay, future labels and descriptive audit; explicit local recipe-file CLI.
- `tests/fixtures/spot_reversal_replay_019.json` — synthetic recipe and predeclared experiment plan, no provider candles.
- `tests/test_spot_reversal_replay.py` — 35 deterministic/adversarial unittest methods.
- This report.

No earlier file is modified. No real market dataset is downloaded, uploaded, fetched or admitted; no live Kraken/clock/DNS/TLS diagnostic, source-policy activation, workflow dispatch, install, credentials, positions, paper/live orders, alerts, monitoring, paid infrastructure, proxy bypass, VM or ZUMERAVO access. Repository issue/source reads and research draft publication use the GitHub connector only.

## 1. Exact source inspection and unchanged contracts

The following source and its existing regression tests were inspected at the pinned baseline. The complete existing unittest suite was staged and executed unchanged, including the bridge/registry, indicator, diagnostic/worker, candidate, clock-policy and offline-chain tests.

| Pinned source | Contract preserved |
| --- | --- |
| [Candidate evaluator](https://github.com/tazmanked-bot/boss-trader-lab/blob/436fe420d4718d2c0e0cef48e4ae9a84b0e46749/research/spot_reversal_candidates.py), `_features`, `evaluate`; [016 report](https://github.com/tazmanked-bot/boss-trader-lab/blob/436fe420d4718d2c0e0cef48e4ae9a84b0e46749/docs/BOSS-TRADER-SPOT-CANDIDATES-016.md) | Four unchanged features (slowing downside, low retest/hold, fresh recovery, volume consistency), all required; score [0,40000]; terminal BLOCKED; WATCH-only rank by `(-score,symbol)`; zero allowed, max three; SYNTHETIC_ONLY; WATCH never BUY/ENTRY READY. |
| [Registry](https://github.com/tazmanked-bot/boss-trader-lab/blob/436fe420d4718d2c0e0cef48e4ae9a84b0e46749/research/spot_refusal_registry.py), `validate_symbol`, `validate_symbols` | Exact Kraken spot USD/1h identity, aligned supported integer UTC seconds, full eligible-history validation, >=21 closed bars, finite positive prices/nonnegative volume, duplicate/order/gap refusal, latest close <=3h relative to as_of, existing row cap/projection semantics. |
| [Kraken-shaped bridge](https://github.com/tazmanked-bot/boss-trader-lab/blob/436fe420d4718d2c0e0cef48e4ae9a84b0e46749/research/kraken_spot_validation_bridge.py), `validate_capture`; [017 chain tests](https://github.com/tazmanked-bot/boss-trader-lab/blob/436fe420d4718d2c0e0cef48e4ae9a84b0e46749/tests/test_live_observation_readiness_017.py) | Bridge precision/decimal/eight-field schema and independent source/normalized evidence remain separate. New generator already emits registry-shaped bars; it does not replace the bridge, parse market captures or claim verified aliases/provenance. Existing chain regressions remain in the full suite. |
| [018 policy](https://github.com/tazmanked-bot/boss-trader-lab/blob/436fe420d4718d2c0e0cef48e4ae9a84b0e46749/docs/BOSS-TRADER-HISTORICAL-DATA-POLICY-018.md); [017 readiness](https://github.com/tazmanked-bot/boss-trader-lab/blob/436fe420d4718d2c0e0cef48e4ae9a84b0e46749/docs/BOSS-TRADER-LIVE-OBSERVATION-READINESS-017.md) | Replay coordinates do not attest UTC/publication; no real-source-to-synthetic relabeling; transport, actual global STOP integration, target runner, strict UTC and identity/schema gaps remain HOLD/NO-GO. |
| [Working Kraken observer](https://github.com/tazmanked-bot/boss-trader-lab/blob/436fe420d4718d2c0e0cef48e4ae9a84b0e46749/kraken_public_observer.py); [scanner baseline](https://github.com/tazmanked-bot/boss-trader-lab/blob/436fe420d4718d2c0e0cef48e4ae9a84b0e46749/boss_trader_lab.py) | Neither imported, invoked, integrated nor modified by the new harness. USD and Binance USDT remain distinct; close-only observer output is not the new data contract. |

No surrogate feature formula, external indicator/library, dependency or fitted model is introduced. The harness always calls the existing evaluator, which itself invokes the unchanged registry before feature calculation. It cannot force validation or supply a user score.

## 2. Synthetic generator and strict source gate

The supported dataset consists of exactly `manifest` and `series`. CLI input is even narrower: exactly a local `recipe` and `plan`; the harness constructs bars itself, without a source URL or market loader. The Python dataset API accepts only a complete exact reproduction of the declared original generator. No real-data mode exists.

Recipe fields are exact: generator version, integer seed, aligned `start_open`, a bounded ordered list of `{regime,hours}` segments, and declared `{symbol,index,kind}` faults. Seed deterministically selects integer price scale `1+seed%5`; it is not a market sample, source of independent statistical replications or a random optimizer. All three symbols deliberately share invented price/volume shapes to test stable ties and refusal isolation, not realistic BTC/XRP/SOL values/correlations.

Regimes:

- downtrend: descending closes; flat: constant OHLC; rally: uninterrupted rising closes;
- rebound: the documented 21-bar invented decline/slowing/held-low/recovery/volume shape used to exercise the fixed evaluator;
- whipsaw: alternating invented prices, including a negative outcome under the separate event rule.

Regime transitions deliberately jump. This is useful for causal/label counterexamples, **not a realistic market model**. Fault kinds are invalid_price, gap, duplicate, adjacent out_of_order and truncate (eventual stale/failure); one per symbol, up to three. Faults are generated reproducibly rather than accepted as arbitrary external data. An adjacent timestamp swap may first refuse GAP instead of ORDER according to the unchanged registry's precedence; the index-zero swap separately exercises ORDER. No repair or sorting is performed.

The strict generated manifest records:

| Field group | Current accepted value / gate |
| --- | --- |
| Source/version | SYNTHETIC_ONLY, named original generator/version and exact recipe/seed |
| Identity | venue kraken, market spot, quote USD, timeframe 1h, exactly BTC/USD/XRP/USD/SOL/USD |
| Capture | ORIGINAL_GENERATOR_NO_CAPTURE — no implied exchange observation |
| Availability/time | AT_CLOSE_SYNTHETIC, UTC_EPOCH_SECONDS; invented candle available exactly at its synthetic close |
| Backfill/corrections | NONE; only declared generator-fault recipe, no earlier-publication claim |
| Rights | MIT, ORIGINAL_GENERATOR_019, commercial_use/redistribution true for this original repository generator output; no external-data license inference |
| Range/quality | declared generation start/end coordinate range, explicit gaps/duplicates/fault recipe, deterministic dataset version |
| Byte identity | SHA-256 of canonical complete generated series; manifest and plan hashes separately recorded |

Qualification regenerates and compares **complete canonical JSON**, not only a hash or loose Python equality. Unknown/missing provenance/rights, actual/external source claims, mixed venue/USDT identity, unsupported time units, backfill assertions, missing/extra fields, injected scores or changed candle values refuse. Rehashing an externally substituted candle does not make it generator output; bool `1` cannot impersonate `true` through loose equality. Unknown/nonfinite/oversized input fails closed with fixed redacted codes and no snapshots.

This is a **synthetic reproducibility gate**, not a magical origin classifier or legal certification. Bytes coincidentally identical to the generator cannot reveal their historical origin; callers must not pass actual data under a synthetic name. No mechanism can prove market authenticity from a label/hash. The accepted input space is intentionally limited to original generated fixtures, with all other historical sources still **NO REAL DATA**. Rights statements apply to this original MIT code/fixture generation only.

## 3. Exact replay window and decision separation

For each predeclared aligned hourly coordinate t in an accepted split:

1. Construct each symbol's prefix using only rows with `open_time+3600 <= t`, in supplied order. No future OHLCV, source corrections, labels or regimes enter that snapshot's evaluator payload. A bar closing at t is eligible; a bar opening at t is not.
2. Use the complete eligible prefix, not a sliding “clean” tail. Previous invalid eligible rows continue to block later decisions even when the last few bars look attractive. Missing early history does not acquire a fabricated warmup.
3. Invoke `spot_reversal_candidates.evaluate` with the existing SYNTHETIC_ONLY envelope and explicit registry as_of policy. Record its **complete canonical output** unchanged, including per-symbol refusals/features/evidence, WATCH/WAIT/BLOCKED and 0–3 unique candidate rank.
4. Finish **all** decisions before calculating any forward labels. Future-label/metric computation cannot feed back into the evaluator.

Coordinates are experimental axes supplied by a plan, not verified market timestamps/current clocks. No wall clock, daemon, provider or historical observation policy is consulted. A valid harness run can contain every symbol BLOCKED and zero candidates; run success means the experiment was valid, not that validation or selection passed.

Qualification sees the whole generated file for source integrity before replay, but it does not supply future content to feature calculation. Thus the no-lookahead guarantee is scoped to **qualified, bounded generator-reproducible alternative datasets sharing the same eligible prefixes**. A source/serialization/size mismatch can refuse a whole run, including when corruption is in a future row; this is not represented as equality of successful replay output after arbitrary malformed bytes.

Tests change a later regime, append a future segment, or declare an invalid later candle, then compare complete earlier canonical snapshot objects. A future-invalid label becomes UNAVAILABLE without altering the earlier decision. Whole-run manifest/hash/forward labels and later metrics may properly change. Dataset/plan lineage hashes therefore live at run level, not inside earlier snapshots; global-file hashes are not used as evidence that earlier decisions depend on future prices. For fixed complete input/plan, the whole canonical run is reproducible.

## 4. Chronological holdouts, purging and preregistration

The exact plan schema contains version, fixed hypothesis `fixed-016-four-feature-conjunction`, fixed event rule, integer horizon H (1–6h), integer embargo E, and exactly train/validation/test half-open intervals `[start,end)`. Every evaluation is hourly, ordered train then validation then test; intervals must be nonempty, within declared range, nonoverlapping and chronologically separated.

Require **E >= 21+H hours**, and each next start minus previous end >= E hours. End is exclusive; the last previous coordinate is `end-1h`, whose forward horizon ends strictly before `next_start-21h` at the minimum gap. This conservatively separates the previous forward labels from the next split's 21-hour context. Also require `split_end + H <= dataset_end_close` (one extra conservative hour relative to the last actual coordinate) so no split silently truncates labels at the dataset boundary. Invalid plans refuse before any decision.

The unchanged registry validates all known historical context, so earlier training history is still present in later prefixes for safety. This protocol **does not claim disjoint full data histories or statistically independent splits**. No model is fitted: train is a descriptive development-audit partition, validation is a later protocol-check partition, test is a final held-out protocol partition. No data scaler, learned thresholds or train-state is transferred.

Example fixture, S=`1900000800`, 147 generated hours, H=3, E=24:

| Partition | Coordinates, offsets from S | Snapshots | Separation |
| --- | --- | --- | --- |
| train | [21h,25h) | 4 | Known prefix includes 21+ closed bars |
| validation | [61h,65h) | 4 | 36h after train end, >=24h |
| test | [124h,128h) | 4 | 59h after validation end, >=24h; labels fit dataset |

These deliberately designed fixtures are **not independent empirical out-of-sample market evidence**. Code validates chronology/embargo but cannot authenticate whether a human selected windows after seeing results. Freeze plan, recipe/data source versions, feature implementation, event rule, horizons, exclusion rules and sensitivity grid in an owner-reviewed exact revision **before** any future held-out study; retain every attempted plan and failure. Hashes identify plans, not trustworthy preregistration time.

No feature tuning or parameter optimizer exists. A future sensitivity study must declare a small full grid on development data, report all windows/regimes/seeds/horizons and null/negative outcomes, control multiple-testing/selection bias, freeze a final choice before untouched holdout, and commission a separate issue for any rule change. Do not cherry-pick a favorable seed/period or treat deterministic rescalings as independent samples. Current feature formulas and safeguards are immutable in this assignment.

## 5. Forward event rule, descriptive metrics and illustrative costs

The predeclared label `synthetic-close-higher-and-low-held-v1` asks only:

```text
At valid snapshot t, with an eligible candle closing exactly at t:
the close at t+H is greater than close(t), AND
all H subsequent hourly lows are >= low(t).
```

Forward context is separately registry-validated through t+H; exactly H contiguous subsequent candles and one current candle must exist. BLOCKED snapshot, stale current candle not closing at t, missing/invalid/gapped/duplicated forward context or incomplete availability yields **UNAVAILABLE**, never false/zero-filled. Labels are SYNTHETIC_EVENT_TRUE/FALSE, not BUY, fill, profit, “winner” or empirical win-rate. The event's higher close does not account for achievable execution or costs, and a held low is not an order/stop instruction. Future labels are never added to decision payloads or supplied by the user.

Per split, the harness reports:

- snapshot count and candidate-count histogram for 0/1/2/3; zero-candidate share over all snapshots;
- per-symbol WATCH/WAIT/BLOCKED counts, WATCH and refusal shares over all snapshots, fixed refusal-code counts;
- feature-pass numerators over **validated WATCH+WAIT** observations (BLOCKED excluded, with refusal rates reported separately);
- observed lengths of contiguous sampled hourly WATCH runs. Non-WATCH/missing coordinate and split boundaries break runs; edge runs are **left/right censored**, not guaranteed total pattern lifetime or positions;
- synthetic false-positive numerator (WATCH with EVENT_FALSE) divided by evaluable WATCH labels, plus WATCH labels UNAVAILABLE separately. `0/0` means unavailable, not zero-percent failure or success;
- complete-snapshot SHA-256 for reproducibility, with manifest/plan hashes separately.

Raw numerator/denominator objects avoid misleading empty percentages. Repeated/overlapping within-split horizons and shared prefixes are dependent observations; no significance, confidence, accuracy, expected return, optimality or probability is inferred. Feature strengths are unchanged ranking units, not confidence. All three fixture symbols share shapes, so these counts cannot be pooled as independent trials.

**Economic analysis is NOT_COMPUTED.** A separate callable `illustrative_cost_bps` accepts only five supplied bounded integer numbers, no bars/prices/positions, and computes additive sensitivity:

```text
illustrative net change bps = supplied gross change bps
  - 2*fee_per_side - spread_roundtrip - 2*slippage_per_side - latency_haircut
```

Examples tested: supplied gross 100bp with (10,5,2,1) costs ->70bp; with (30,20,15,10) ->-20bp. These values are **arbitrary synthetic arithmetic**, not a verified Kraken fee tier, realistic observation, execution simulation, backtested P&L or expected profitability. The additive approximation omits compounding and cost/size interaction. No candle price is manufactured into an entry/fill or economic outcome; the helper is not called by replay and cannot affect ranking.

For any separately approved future study, justify actual contemporaneous venue/tier maker/taker fees and both-side applicability, spread timing and side, size/liquidity/depth-dependent slippage, latency and execution constraints, missing/unfilled observations, changing volatility/volume and cost uncertainty. OHLCV alone cannot establish attainable spread/depth/fills; lack of such evidence forbids executable-return claims. Use preregistered conservative ranges and adverse scenarios, report every cost assumption and sensitivity, never tune to retain a positive result. Study design, hypothetical arithmetic and any actual simulated position engine remain separate approvals; no engine or orders are implemented here.

## 6. Future real-dataset qualification plan — no retrieval authorized

All real sources are currently unsupported. A future source-aware adapter/evaluator and acquisition plan require a separate owner-approved issue, without converting actual bars into SYNTHETIC_ONLY. Public availability is **not** commercial/reuse permission; repository MIT does not license vendor data. Source rights and point-in-time evidence must be independently reviewed before import, even for owner-supplied files.

Minimum real-source manifest/acceptance checklist for later independent review:

| Requirement | Necessary evidence / rejection rule |
| --- | --- |
| Named source/version | Original provider, exact immutable dataset version and source document/contract; unknown chain -> NO REAL DATA |
| Instrument identity | Exact Kraken spot BTC/USD, XRP/USD, SOL/USD mapping, base/quote/classes/status and schema versions; USD/USDT, venue or instrument mixing refuses |
| Rights/permissions | License/terms version, exact permission evidence and reviewer, research/commercial use, local storage, derived output and redistribution limits, retention/deletion obligations; missing/ambiguous rights -> NO REAL DATA, no assumption based on a public API |
| Capture method | Reviewed lawful original collection/export path and provenance; no exchange keys, paid resource or route bypass authorization inferred |
| Timestamp/availability | UTC/time scale/precision, open/close semantics, publication availability per bar/version; backfill/corrections cannot be represented as known at an earlier coordinate |
| Byte identity/range | Exact original and normalized byte hashes, range and coverage per instrument/version, normalization/precision audit and immutable corrections lineage; hashes do not establish authenticity |
| Gaps/duplicates/schema | Full quality report, no-trade intervals distinguished from missing capture, corrections/disputes/delisting and survivorship coverage; no filling/sorting away refusal, no silent alias guesses |
| Point-in-time limitations | If only final revised history exists, explicitly revised-history-only study or reject a point-in-time claim; availability unknown must not be upgraded to earlier-publication truth |
| Scientific review | Chronological preregistration, purged horizons/context, all attempts/exclusions, baselines and out-of-sample plan, honest costs/uncertainty, no profitability promise |

Potential source classes to assess later, **not approved sources**:

1. Kraken's own historical OHLCVT archives, subject to independently checked current rights, coverage, spot USD identity and CSV semantics. Earlier docs describe seven-column CSV versus eight-field REST, and no-trade gaps; current aliases/expanded schema remain unresolved. Do not download an archive now or call it an interchangeable bridge capture.
2. Existing owner-controlled historical exports with documented lawful acquisition, complete version/rights chain and publication/correction metadata. Mere possession or uploading a file is insufficient permission; none is ingested here.
3. An independently licensed lawful archive/research dataset with exact venue/instrument and commercial/derived/redistribution permission. No paid subscription or other exchange substitution is authorized. If free permitted access/evidence is absent, keep NO REAL DATA.
4. Original synthetic fixtures remain the practical current source for contract validation. CCXT or another transport library would not grant dataset rights or establish publication timing.

Short REST windows cannot establish broad historical coverage. Backfills, survivorship/delistings, varying liquidity/no-trade gaps and revision histories can dominate apparent results. A later independent review must decide whether an honest revised-history experiment is scientifically useful or whether evidence is insufficient. A green synthetic run never authorizes a download, provider request, policy change or real-world outcome claim.

## 7. Bounded resources and remaining safety HOLDs

Hard input/work bounds in the new module: <=384 nominal generated hourly bars per symbol, <=16 segments of 1–64h, <=3 faults/one per symbol (duplicate can add one row, still below unchanged 512 cap), bounded seed, <=64 total evaluation snapshots, horizon 1–6h, three nonempty splits and explicit embargo. Recipe byte cap 16KiB, plan 8KiB, dataset/JSON 512KiB, canonical result <=2MiB; CLI reads at most cap+1 bytes and rejects over-limit input. Strict JSON rejects duplicates, nonfinite/overflow/recursion/encoding errors; fixed errors never echo input/paths/provider exceptions.

No optimization search, unbounded loop, worker pool, busy wait, GPU/LLM, download, dependency or service is added. Processing is bounded by 64 decisions and 192 label validations over small histories, plus bounded regeneration. Repeating many experiments externally is not authorized optimization. Canonicalization/object graphs/copies add overhead: byte caps are **not** RSS limits. Peak RSS, target-runner timing and worst-case OS bounds are UNMEASURED. No hard time guarantee is invented; later owner offline Actions may use an independently reviewed job cap. No VM is necessary for these fixtures or accessed.

B1 actual transport/startup/deadline, B2 real header/stream allocation, B3 actual integrated global STOP, B5 target runtime, route/TLS/451 restrictions and current XRP/SOL identity/expanded schema remain unresolved. Strict B4 independent <=2s UTC remains NO-GO; historical-data policy B remains PROPOSED/HOLD. The new code never imports or activates a diagnostic client. Existing disabled diagnostic CLIs, working scanner/observer, workflows, dependencies, registry/bridge/candidate code and all safety limits remain unchanged.

## 8. Exact execution evidence and adversarial matrix

Local CPython **3.12.14**, stdlib only, no installs:

```text
python -B -m unittest discover -s tests -p test_spot_reversal_replay.py -v
Ran 35 tests in 1.063s
OK

python -B -m unittest discover -s tests -v
Ran 279 tests in 4.210s
OK

python -B -m research.spot_reversal_replay tests/fixtures/spot_reversal_replay_019.json
exit 0
status=SYNTHETIC_HARNESS_VALIDATION_ONLY; snapshots=12
economic_outcomes=NOT_COMPUTED; operational_mode=HOLD
```

**244 unchanged baseline methods + 35 new = 279, no skips.** Each new test guards socket construction/connection/DNS, urlopen, HTTPSConnection, subprocess.run/Popen and time.time and asserts zero calls. Existing full-suite fake transport/local worker lifecycle tests remain offline, not a new network/clock probe. Baseline TLS-context tests may load local public roots, without a handshake. Python 3.11 and a current-head target Actions run remain UNVERIFIED.

Exact deterministic artifacts:

| Artifact | SHA-256 |
| --- | --- |
| Checked-in recipe/plan fixture bytes | `cfb1f4f0fb0d78c2b7111da5d999b4117dab418993815c6da012269ad0270081` |
| Canonical generated series | `8ba3140299224ee247a5435215c3319cf73c51ff41a98cb122560149afa9aa90` |
| Canonical manifest | `6f78c549a81f4c3f0b8777d5e54a29b3b3f3e6589a4aa5faa361b39835a8e389` |
| Canonical plan | `96521a638fb3fe86a2e5d87bb2b528c5bd0e7e9919b437b677718909756e9a8d` |
| Complete canonical snapshot collection | `26d2a309bf170192f5d1e9446d64a1a3b8d49d73ba7c9defc66c5cf3d0ff5831` |

Default invented results (all symbols share shapes, not independent observations): train histogram zero=4; validation zero=3/three=1; test zero=3/three=1. At each WATCH snapshot tie order is BTC/USD, SOL/USD, XRP/USD. Each symbol has a one-hour sampled WATCH run in validation and test. Under the fixed synthetic event, validation WATCH has false/evaluable=1/1 and test WATCH has 0/1; train has 0/0 unavailable. These contrasts deliberately exercise counting, **not observed win/loss or a market holdout result**. Gap/stale/invalid fault variants preserve per-symbol refusal separately.

| Coverage | Exact new tests / evidence | Result |
| --- | --- | --- |
| Reproduction, seed, unchanged evaluator | `test_identical_seed_manifest_and_replay_are_canonical_reproducible`, `test_changed_seed_changes_manifest_not_hypothesis`, `test_every_snapshot_is_exact_unchanged_evaluator_output` | PASS |
| All regimes/flat/rally and 0–3 bound/ties | `test_fixture_has_all_regimes_and_descriptive_counts`, `test_all_flat_and_rally_series_never_force_watch`, `test_independent_symbol_failure_and_zero_one_two_three_bound`, `test_stable_tie_order_unchanged` | PASS |
| Future mutations/appends/invalid label data, complete earlier output | `test_future_regime_change_preserves_complete_earlier_canonical_snapshots`, `test_appended_future_regime_preserves_all_decisions_and_labels`, `test_future_invalid_row_never_changes_earlier_decision_but_label_unavailable` | PASS within qualification contract |
| Labels separated and hand-computable rule | `test_labels_are_computed_after_all_decisions`, `test_forward_rule_hand_calculated_and_not_a_price_or_trade` | PASS |
| Old invalid history/high-looking recent pattern cannot rescue | `test_invalid_eligible_history_blocks_even_when_recent_shape_would_watch`, `test_hypothesis_parameters_and_injected_scores_cannot_override` | PASS, null score/features for BLOCKED |
| Gap/duplicate/order/stale, warmup | `test_fault_matrix_gap_duplicate_order_and_stale`, `test_insufficient_history_is_blocked_no_warmup_bypass` | PASS |
| Holdout overlap/embargo/horizon, boundary and chronology | `test_overlap_wrong_chronology_and_short_embargo_refuse`, `test_exact_embargo_boundary_is_accepted`, `test_outcome_horizon_and_dataset_range_are_enforced`, `test_train_labels_end_before_next_feature_window` | PASS |
| Provenance/rights/identity/relabel/hash/backfill/contradictory labels | `test_unknown_provenance_missing_rights_or_mixed_identity_refuse`, `test_relabeling_actual_like_data_and_rehashing_does_not_pass_generator_gate`, `test_backfill_claim_or_false_labels_are_rejected`, `test_boolean_numeric_impersonation_and_unknown_symbol_refuse` | PASS synthetic gate only |
| Structure/types/limits/parser/recipe injection | `test_unexpected_types_missing_fields_and_nonfinite_refuse`, `test_excessive_history_snapshots_and_bytes_refuse_before_work`, `test_parser_duplicate_nonfinite_overflow_recursion_and_secret_errors_refuse`, `test_recipe_wrong_units_score_faults_and_seed_type_refuse` | PASS |
| Metrics denominators/censored runs/false labels/cost sensitivity | `test_descriptive_metrics_denominators_and_censored_duration`, `test_watch_run_lengths_break_at_missing_coordinates`, `test_synthetic_false_positive_is_event_failure_not_observed_loss`, `test_illustrative_cost_sensitivity_no_prices_fills_or_positions` | PASS synthetic descriptive arithmetic |
| JSON/CLI/redaction/import isolation | `test_end_to_end_json_and_bounded_canonical_output`, `test_cli_local_fixture_only_and_read_failure_redacted`, `test_import_and_reload_never_collect_or_read_clock` | PASS |

## 9. Limitations and smallest owner action

The evidence supports **only harness validation**. It establishes no empirical edge, independently held-out market outcome, realistic price process, executable return, paper position, profitability, vulnerability clearance, data license clearance for external sources or clock/runner guarantee. Shared deterministic shapes, contrived transitions, tiny partitions, dependent horizons and designed event outcomes make statistical interpretation inappropriate. No tuning/optimization is performed, but human preregistration/selection integrity still needs independent review.

**Smallest safe owner action:** review the exact draft head and authorize an independent manually triggered **offline Actions run pinned to that exact commit**, with HEAD equality, actual interpreter version, focused/full counts and no skipped safety checks verified, then independent owner/BOSS AI review. No workflow or dispatch is added here. Historical market-data qualification/retrieval remains a **separate approval with proven rights and source-aware contracts**, never inferred from green synthetic tests or a merge.

The draft/final handoff records exact commit and changed paths; a commit cannot self-embed its own hash. Main and all earlier files remain inherited unchanged. Do not merge or promote Operational Test Mode in this assignment.

**STOP FOR OWNER AND BOSS AI REVIEW.**
