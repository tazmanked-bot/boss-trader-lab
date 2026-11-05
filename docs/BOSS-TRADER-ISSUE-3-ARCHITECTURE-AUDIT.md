# BOSS-TRADER-ISSUE-3-ARCHITECTURE-AUDIT

Date: 2026-11-05 UTC. Authorization: [Issue #10](https://github.com/tazmanked-bot/boss-trader-lab/issues/10).
Parent [Issue #3](https://github.com/tazmanked-bot/boss-trader-lab/issues/3) remains open.

**Recommendation: ADAPT LATER — keep the current Kraken observer; NO IMPORT / NO
IMPLEMENTATION now.** Consider only the three original, limited patterns ranked
below after separate owner authorization. Reject direct integration of the
upstream strategy, market-data failover, deployment and derivatives assumptions.

## 1. Provenance, scope and limits

Upstream: Acekiller88/crypto-signal-scanner, inspected at exact commit
**`431c79bb45fb31ca9609c48ccc0f17376731b9da`**. The complete recursive tree was returned without truncation.
Latest five returned commits end at **2026-08-30 11:56:01 UTC**; activity inspected
was concentrated on August 30. This establishes a last-observed change, not
ongoing support, a vulnerability SLA or future maintainer availability.
Repository metadata was public and not archived. The GitHub Actions run listing
returned **total_count=0** at inspection.

BOSS baseline: **`1abf48e19aeae7328f78f3bfe7ec99112227dc97`**, especially
[kraken_public_observer.py](https://github.com/tazmanked-bot/boss-trader-lab/blob/1abf48e19aeae7328f78f3bfe7ec99112227dc97/kraken_public_observer.py#L23).
It is Kraken BTC/XRP/SOL spot USD, hourly, OBSERVE_ONLY. Its existing parser
drops the final Kraken row, checks positive finite closes and increasing
timestamps, permits 60-second close-boundary slack, and rejects latest-close
staleness beyond three hours. It does not assert exact hourly continuity or a
specific response pair key. These are baseline observations, not modifications
or a proposal to import upstream code.

Method: GitHub connector read-only inspection of license, README, configuration,
all scanner Python files, test source, staged workflows, frontend freshness
logic, and committed JSON. No upstream program or test suite was executed.
No packages were installed, credentials accessed, external market API called,
workflow launched, source code copied into BOSS or profitability verified.
Only this original documentation and a proposed assignment may be committed.

## 2. License, claims and independently supported facts

| Item | Finding |
| --- | --- |
| License | **PASS:** [LICENSE:1](https://github.com/Acekiller88/crypto-signal-scanner/blob/431c79bb45fb31ca9609c48ccc0f17376731b9da/LICENSE#L1) contains MIT, copyright 2026 Acekiller88; it also includes a financial-use disclaimer. If code is ever copied later, preserve the original copyright and permission notice and record source commit/modifications. Current research does not copy implementation. |
| Market and direction | **PASS, incompatible with our scope:** [scanner/universe.py:47](https://github.com/Acekiller88/crypto-signal-scanner/blob/431c79bb45fb31ca9609c48ccc0f17376731b9da/scanner/universe.py#L47) filters USDT and PERPETUAL when using futures; [scanner/signals.py:386](https://github.com/Acekiller88/crypto-signal-scanner/blob/431c79bb45fb31ca9609c48ccc0f17376731b9da/scanner/signals.py#L386) evaluates long and short. This is not Kraken USD spot. |
| Zero runtime dependencies | **Supported statically:** scanner imports inspected were stdlib/internal modules; [requirements.txt:1](https://github.com/Acekiller88/crypto-signal-scanner/blob/431c79bb45fb31ca9609c48ccc0f17376731b9da/requirements.txt#L1) declares pytest>=8.0 for QA only. Not an executed clean-environment verification or dependency security clearance. |
| 191 tests / 195 in commit message | README cites 191. Independent static counting found **191 named test functions in 12 test files**. Parameterized collection can differ; no pytest collection or execution occurred. Neither count is independently verified as passing. See [README.md:358](https://github.com/Acekiller88/crypto-signal-scanner/blob/431c79bb45fb31ca9609c48ccc0f17376731b9da/README.md#L358) and [scanner/check_docs.py:26](https://github.com/Acekiller88/crypto-signal-scanner/blob/431c79bb45fb31ca9609c48ccc0f17376731b9da/scanner/check_docs.py#L26). |
| Automated operation | **Not active at inspected revision:** workflows exist under ops/github-workflows only; no .github/workflows directory exists in the inspected tree. [ops/github-workflows/README.md:1](https://github.com/Acekiller88/crypto-signal-scanner/blob/431c79bb45fb31ca9609c48ccc0f17376731b9da/ops/github-workflows/README.md#L1) explicitly requires installation. A staged YAML or a docs test accepting it is not proof of an operating scheduler. |
| Production-ready, zero-cost, performance language | README assertions, not audit conclusions: [README.md:6](https://github.com/Acekiller88/crypto-signal-scanner/blob/431c79bb45fb31ca9609c48ccc0f17376731b9da/README.md#L6) and [README.md:49](https://github.com/Acekiller88/crypto-signal-scanner/blob/431c79bb45fb31ca9609c48ccc0f17376731b9da/README.md#L49). No account billing, availability, profitability or operational readiness was independently tested. |
| Committed performance evidence | [data/signals.json:1](https://github.com/Acekiller88/crypto-signal-scanner/blob/431c79bb45fb31ca9609c48ccc0f17376731b9da/data/signals.json#L1) contains zero signals; [data/performance.json:1](https://github.com/Acekiller88/crypto-signal-scanner/blob/431c79bb45fb31ca9609c48ccc0f17376731b9da/data/performance.json#L1) reports zero resolved trades and null win rate/expectancy. Snapshot timestamp is 2026-08-30T05:16:43.291Z. No validated reversal edge or performance comparison follows from it. |

The upstream itself says scores are rankings, not probabilities, and does not
claim trade execution. The inspected client builds public GET data requests;
no order submission path was found in those inspected scanner paths. This is
not a complete security audit or permission to use derivatives.

## 3. Source-anchored architecture comparison

| Concern | Verified upstream behavior / limitation | BOSS implication |
| --- | --- | --- |
| Hard rejects and explainability | [scanner/signals.py:60](https://github.com/Acekiller88/crypto-signal-scanner/blob/431c79bb45fb31ca9609c48ccc0f17376731b9da/scanner/signals.py#L60) defines stable reason codes; try_setup applies structural/indicator/risk gates; [scanner/main.py:218](https://github.com/Acekiller88/crypto-signal-scanner/blob/431c79bb45fb31ca9609c48ccc0f17376731b9da/scanner/main.py#L218) aggregates ordered rejection counts and human detail. Some duplicate gates execute earlier than the listed funnel order, so it is not automatically a conserved population funnel. | A stable code/detail distinction is useful. Do not import futures thresholds, scores, sequencing or assume a high score overrides refusal. |
| Missing and malformed data | [scanner/market_data.py:67](https://github.com/Acekiller88/crypto-signal-scanner/blob/431c79bb45fb31ca9609c48ccc0f17376731b9da/scanner/market_data.py#L67) skips malformed rows and sorts the remainder; [scanner/analysis.py:105](https://github.com/Acekiller88/crypto-signal-scanner/blob/431c79bb45fb31ca9609c48ccc0f17376731b9da/scanner/analysis.py#L105) checks history length/warmup. [scanner/main.py:187](https://github.com/Acekiller88/crypto-signal-scanner/blob/431c79bb45fb31ca9609c48ccc0f17376731b9da/scanner/main.py#L187) returns failure when universe/data is unavailable. | Prefer whole-symbol refusal for corrupt data. Do not silently discard/reorder rows and then infer continuous valid history. |
| Stale data | Signal generation occurs at main:218; freshness is computed later at main:282. [scanner/main.py:426](https://github.com/Acekiller88/crypto-signal-scanner/blob/431c79bb45fb31ca9609c48ccc0f17376731b9da/scanner/main.py#L426) uses the newest close across analyses, not a per-symbol veto. [scanner/analysis.py:94](https://github.com/Acekiller88/crypto-signal-scanner/blob/431c79bb45fb31ca9609c48ccc0f17376731b9da/scanner/analysis.py#L94) does not enforce age from now_ms. | **Claim gap:** stale data is documented as a hard reject but the inspected path can still publish qualifying setups while labeling the scan DEGRADED. A fresh symbol can mask another stale symbol in aggregate freshness. Require per-symbol refusal before any candidate. |
| Closed candles and gaps | [scanner/market_data.py:94](https://github.com/Acekiller88/crypto-signal-scanner/blob/431c79bb45fb31ca9609c48ccc0f17376731b9da/scanner/market_data.py#L94) filters closeTime < now. The parser does not require exact timeframe spacing or uniqueness after sorting. | Strict closed-data filtering is a useful principle, not complete validation. Require explicit time units, aligned boundaries, unique sorted timestamps and no gaps; never fill missing market bars synthetically. |
| Signal lifecycle | [scanner/signals.py:38](https://github.com/Acekiller88/crypto-signal-scanner/blob/431c79bb45fb31ca9609c48ccc0f17376731b9da/scanner/signals.py#L38) defines WAITING_TRIGGER/TRIGGERED and terminal outcomes; [scanner/outcomes.py:72](https://github.com/Acekiller88/crypto-signal-scanner/blob/431c79bb45fb31ca9609c48ccc0f17376731b9da/scanner/outcomes.py#L72) advances simulated levels, expiry and holding time. | Not equivalent to WATCH / ENTRY READY / owner authorization. Do not translate simulated trigger hits into approval or actual fills. |
| Dedupe/cooldown | [scanner/signals.py:363](https://github.com/Acekiller88/crypto-signal-scanner/blob/431c79bb45fb31ca9609c48ccc0f17376731b9da/scanner/signals.py#L363) uses existing active records, last-by-key time and setup hashes; sameDirectionOnly is read but unused. After new_signals append at line 471, existing-key/hash sets are not updated. [scanner/main.py:273](https://github.com/Acekiller88/crypto-signal-scanner/blob/431c79bb45fb31ca9609c48ccc0f17376731b9da/scanner/main.py#L273) logs payload errors but still reaches writes at line 374. | Historical suppression exists, but in-batch duplicate inputs can evade generation checks and subsequent validation is not a hard publication veto. Do not copy the state logic or its four-hour cooldown/12-active cap. |
| No-lookahead | [scanner/structure.py:70](https://github.com/Acekiller88/crypto-signal-scanner/blob/431c79bb45fb31ca9609c48ccc0f17376731b9da/scanner/structure.py#L70) records delayed swing confirmation; [scanner/structure.py:165](https://github.com/Acekiller88/crypto-signal-scanner/blob/431c79bb45fb31ca9609c48ccc0f17376731b9da/scanner/structure.py#L165) activates levels by confirmIndex; [scanner/replay.py:45](https://github.com/Acekiller88/crypto-signal-scanner/blob/431c79bb45fb31ca9609c48ccc0f17376731b9da/scanner/replay.py#L45) slices by closed time. | Useful causal design intent. Tests must append adversarial future data and compare the entire same-as-of output, not just a few indicator prefixes. |
| Residual future-price exposure | [scanner/outcomes.py:77](https://github.com/Acekiller88/crypto-signal-scanner/blob/431c79bb45fb31ca9609c48ccc0f17376731b9da/scanner/outcomes.py#L77) refreshes resolved records from the last supplied candle without an as-of filter. At [scanner/outcomes.py:168](https://github.com/Acekiller88/crypto-signal-scanner/blob/431c79bb45fb31ca9609c48ccc0f17376731b9da/scanner/outcomes.py#L168), an empty closed subset falls back to the full candle list. Replay passes the full 15m list at [scanner/replay.py:75](https://github.com/Acekiller88/crypto-signal-scanner/blob/431c79bb45fb31ca9609c48ccc0f17376731b9da/scanner/replay.py#L75). | Future currentPrice metadata can be exposed when full-history inputs are supplied, even though the lifecycle transition loop stops at now_ms. Do not inherit a universal no-lookahead claim. |
| Outcome ambiguity and metrics | [scanner/outcomes.py:118](https://github.com/Acekiller88/crypto-signal-scanner/blob/431c79bb45fb31ca9609c48ccc0f17376731b9da/scanner/outcomes.py#L118) leaves same-bar TP/SL ambiguous absent resolution; [scanner/outcomes.py:49](https://github.com/Acekiller88/crypto-signal-scanner/blob/431c79bb45fb31ca9609c48ccc0f17376731b9da/scanner/outcomes.py#L49) checks SL first if both touch within one minute. [scanner/performance.py:191](https://github.com/Acekiller88/crypto-signal-scanner/blob/431c79bb45fb31ca9609c48ccc0f17376731b9da/scanner/performance.py#L191) excludes unresolved states from win-rate denominator. Net fields can mix costed and gross fallback records at lines 166-180. | Preserve uncertainty and explicit denominators, not this derivatives fill/cost model. A stop-first convention is a convention, not observed intrabar ordering. No unknown cost may silently become zero-cost/net performance. |
| Evidence and immutability | [scanner/main.py:243](https://github.com/Acekiller88/crypto-signal-scanner/blob/431c79bb45fb31ca9609c48ccc0f17376731b9da/scanner/main.py#L243) deep-copies history before mutation; [scanner/validation.py:124](https://github.com/Acekiller88/crypto-signal-scanner/blob/431c79bb45fb31ca9609c48ccc0f17376731b9da/scanner/validation.py#L124) detects same-object aliasing and changed frozen fields. [scanner/persist.py:35](https://github.com/Acekiller88/crypto-signal-scanner/blob/431c79bb45fb31ca9609c48ccc0f17376731b9da/scanner/persist.py#L35) replaces JSON files atomically. | Useful basis for a tiny future evidence ledger, with schema/version/as-of and bounded retention. Not proof that every field is causally protected or storage is tamper-evident. |
| UI freshness | [frontend/app.js:142](https://github.com/Acekiller88/crypto-signal-scanner/blob/431c79bb45fb31ca9609c48ccc0f17376731b9da/frontend/app.js#L142) downgrades stored health using wall-clock age. Live ticker fetches and repeating timers also exist in the frontend. | Show age and source honestly in future reports, but reject browser polling/live dashboard deployment for this assignment. A stale badge fix cannot repair strategy-time stale input. |
| Actions permissions and resource use | [ops/github-workflows/scanner.yml:15](https://github.com/Acekiller88/crypto-signal-scanner/blob/431c79bb45fb31ca9609c48ccc0f17376731b9da/ops/github-workflows/scanner.yml#L15) includes cron/push/manual triggers, contents:write, a 20-minute job and git commit/push. Test workflow is contents:read with two Python versions and unpinned pytest. | Reject scan automation and repo-write tokens. A future manual offline report should use contents:read, no secrets/schedules/pushes, and bounded temporary artifacts. |

These findings are static source-path deductions, not reproduced runtime defects
or an upstream security disclosure. They are sufficient reasons not to import
the implementation, but do not prove any real trading loss or exploit.

## 4. Spot-versus-futures exclusion matrix

| Upstream concept | Decision for BOSS spot-first research |
| --- | --- |
| Binance USDT perpetual universe / Bybit linear fallback | REJECT; fixed Kraken BTC/USD, XRP/USD, SOL/USD remain distinct market identities. USD is not USDT; spot data is not a substitute for perp data or vice versa. |
| LONG/SHORT strategy, short selling, margin, leverage | REJECT; no short selling, borrowing, leverage or automatic approvals. A bearish observation is a reason to withhold a spot candidate, not a short instruction. |
| Liquidation, funding, open interest and derivatives-oriented sizing/cost assumptions | REJECT regardless of whether every feature has an execution implementation upstream. No funding/liquidation model is needed for this scope. |
| 4H/1H/15m entry sequence and optional daily bias | Do not adopt. Current BOSS hourly observer stays unchanged; new timeframes or strategy gates require separate owner specification and evidence. |
| Score >=80 and minimum RR 2.5 / preferred 3 | Do not adopt as predictive thresholds or profitability proof. A score is not a probability. |
| Trigger/SL/TP simulated execution and 1-minute intrabar resolution | Do not activate or borrow as execution authority. Any later synthetic observation ledger must distinguish hypothetical outcomes, unavailable evidence and ambiguity. |
| Mirrors, proxies, spot fallback, cross-venue substitution and HTTP 451 failover | REJECT. [config/strategy.json:8](https://github.com/Acekiller88/crypto-signal-scanner/blob/431c79bb45fb31ca9609c48ccc0f17376731b9da/config/strategy.json#L8) and [scanner/market_data.py:200](https://github.com/Acekiller88/crypto-signal-scanner/blob/431c79bb45fb31ca9609c48ccc0f17376731b9da/scanner/market_data.py#L200) demonstrate these paths. Respect network restrictions and return DATA_UNAVAILABLE; do not emulate evasive routing or substitute venues. |
| Automatic orders, signing, keys, scheduled polling, external scheduler or dashboard deployment | REJECT / outside scope. Upstream's absence of order execution does not authorize adding it here. |
| Best-effort cron and automatic JSON commits | REJECT; manual owner-triggered offline evidence only is the appropriate default. |

## 5. At most three original patterns to consider later

These are design proposals inspired by observations, not imported code. None is
implemented or approved by this audit.

| Rank / pattern | Benefit | Effort / safety / testability | Proposed spot-only boundary |
| --- | --- | --- | --- |
| **1. Stable refusal registry before ranking** | Highest: explain why zero candidates is correct without high-cardinality text keys or forced trades. | Small; lowest implementation risk; deterministic input-to-code tests. | Separate stable reason code, human detail and evidence reference. Hard data/policy refusal precedes any ranking. Unknown code/config fails closed. Implement only after owner approval. |
| **2. Observation dedupe and cooldown state** | Prevent repeated WATCH events for the same evidence and make transitions reviewable. | Medium; persistence, replay and race/expiry risks. High testability using injected clocks and immutable snapshots. | Identity includes venue, market=spot, USD, symbol, 1h close and policy version. Update same-run keys as well as retained state. No notifications, trade state or order authority. |
| **3. Offline synthetic observation ledger** | Preserve what was knowable at an as-of time and distinguish later observations from original evidence. | Medium; strongest causal/metric review needed. Testable with append-future invariance, aliasing and ambiguity fixtures. | Immutable original evidence plus separate later observations; synthetic-only, no real fills or profitability labels. Missing/ambiguous outcomes remain explicit. No derivatives funding or hidden zero-cost assumptions. |

The simplest immediate solution is **NO IMPORT / NO IMPLEMENTATION**. Registry
pattern 1 is the only suggested next coding candidate, and only through the
separate proposed assignment. Options 2 and 3 remain deferred.

**Candidate and approval gates:** 0-3 early-reversal candidates is a maximum,
never a quota or forced minimum. Missing/invalid evidence may produce zero.
WATCH means research attention only. ENTRY READY needs a separately defined and
tested spot rule set; this audit does not create one. Owner authorization stays
a separate decision, and neither state grants execution capability. Scores,
cooldown expiry and an empty candidate list cannot auto-promote a record.

## 6. Offline deterministic test design — not executed

Use a fixed UTC hour boundary T=1,899,997,200 seconds and a fixed policy version.
Construct integer-indexed hourly bars ending at T, with positive consistent
OHLC and deterministic volume. Keep all expected outputs as plain fixture data;
no downloads, synthetic-to-live fallback, fees/profit inference or signal tuning.
For the existing observation-window example, declare a 21-close requirement;
future indicator profiles must declare their own warmup rather than inheriting
the upstream EMA200/multiframe choices.

| Fixture / mutation | Expected refusal or invariant |
| --- | --- |
| Non-dict envelope, missing error/result, wrong pair/venue/quote | MALFORMED_DATA or MARKET_MISMATCH; zero candidates and no state advancement |
| NaN/inf/zero/negative close, boolean/string timestamp, invalid OHLC bounds | INVALID_VALUE or TIMESTAMP_INVALID; refuse whole symbol |
| Duplicate, reversed, skipped hourly bar; millisecond data presented as seconds | DUPLICATE_TIMESTAMP / TIMESTAMP_ORDER / TIMESTAMP_GAP / TIME_UNIT_MISMATCH; do not sort, fill or guess units |
| Close before open, crossing intervals, future/unclosed bar | TIMESTAMP_INVALID / CANDLE_NOT_CLOSED; no use of unfinished high/low/close |
| One fresh symbol and one stale symbol, then all stale | Per-symbol DATA_STALE veto before ranking; aggregate freshness cannot rescue stale input |
| 20 versus 21 required closes; null indicator after declared warmup | WARMUP_INCOMPLETE / INDICATOR_UNAVAILABLE; no threshold relaxation |
| Contradictory spot rules, forbidden market type or unknown policy key | RULE_CONFLICT / POLICY_REJECTED / CONFIG_INVALID; fail closed regardless of score |
| Same event twice in one batch, on another manual run, or after reload | One logical observation, DUPLICATE_OBSERVATION for repeats; idempotent evidence and no duplicate alerts |
| Before / exactly at cooldown boundary; invalid input at expiry | COOLDOWN_ACTIVE before boundary; expiry alone never creates eligibility; invalid data still refuses |
| Zero, one, three or four otherwise eligible fixture records | Preserve zero, cap at three deterministically, never manufacture a fourth or promote WATCH to ENTRY READY |
| Append extreme future bars; run again at the identical as-of cutoff | Byte-equivalent canonical decision/evidence for that cutoff, including currentPrice and timestamps |
| Mutate original fields; pass aliased old/new snapshots | IMMUTABILITY_VIOLATION / EVIDENCE_ALIAS; refuse publication rather than silently repair and continue |
| Synthetic later path touches conflicting hypothetical bounds in one bar | AMBIGUOUS, not a win; no later finer data silently rewriting original evidence |
| Empty/insufficient outcome book, unknown costs | Count=0 or UNRESOLVED; rates/net returns null, not invented zero-risk performance |
| HTTP 451, timeout, unavailable API, malformed persisted state or disk-write failure | DATA_UNAVAILABLE / STATE_INVALID / EVIDENCE_WRITE_FAILED; no mirrors, retries-to-evade, partial approval or synthetic fallback |
| Score extreme but hard refusal present; injected unknown reason code | Refusal takes precedence; UNKNOWN_REASON is itself failure, not an unclassified PASS |

These refusal names are original proposed BOSS vocabulary, not a copied upstream
registry. The table defines future tests, not claims that new code or tests ran.

## 7. Resources and security for a free manual-only approach

Upstream configured scale is 100 symbols, 4H/1H/15m plus optional 1d, up to
700 HTTP attempts/scan, 12-second per-request timeout and three retries. It
collects derivatives context and may request additional 1m data. See
[config/strategy.json:32](https://github.com/Acekiller88/crypto-signal-scanner/blob/431c79bb45fb31ca9609c48ccc0f17376731b9da/config/strategy.json#L32) and [scanner/main.py:84](https://github.com/Acekiller88/crypto-signal-scanner/blob/431c79bb45fb31ca9609c48ccc0f17376731b9da/scanner/main.py#L84).
The committed snapshot's 427 requests / 67,914 ms is a historical JSON value,
not an independently measured benchmark. A 15-minute cadence implies 96
nominal fires/day if installed, but no scheduler is installed at the inspected
revision and GitHub scheduling is not a latency guarantee.

Signal history is retained indefinitely; JSON is mirrored to frontend data,
and generated dashboards and automatic commits add storage/history/deploy
churn. Backend logs/snapshots are bounded, but signal history is not. Browser
timers add network activity. None is needed for this BOSS documentation audit.

For any later approved pattern-1 experiment: stdlib-only offline fixtures,
one owner-triggered run, contents:read, no secrets or checkout write credentials,
no schedules, repo commits, browser fetches, paid APIs or hosting. Pin supported
Python/action identities if a workflow is later authorized; use short timeouts
and bounded JSON/Markdown evidence artifacts with owner-controlled preservation.
No workflow or dependency change is authorized by this report.

MIT is not a security warranty. Inspection found no operational evidence for
general security, comprehensive test coverage or profitability. Do not expose
raw exception bodies, credentials or private data in public JSON/logs. Do not
interpret source hashes or deterministic fixtures as authenticated market truth.

## 8. Decision and smallest safe next action

**ADAPT LATER**, limited to the ranked original patterns. **Keep current BOSS
Kraken spot observation unchanged; reject importing or activating the upstream
scanner.** No upstream strategy, code, derivatives assumption, data bypass,
scheduler or performance claim should enter production through this audit.

Smallest safe owner action: review this report and either keep the no-change
position or explicitly authorize only the proposed offline refusal-registry
assignment in the companion document. It is a proposal, not a queued task.
Do not authorize all three patterns implicitly. Issue #3 remains open until
owner review; no PR may merge under this assignment.

STOP FOR OWNER AND BOSS AI REVIEW.
