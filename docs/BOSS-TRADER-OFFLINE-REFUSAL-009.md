# BOSS TRADER LAB — Offline Refusal Registry 009

2026-11-05 UTC. Authorization: [Issue #12](https://github.com/tazmanked-bot/boss-trader-lab/issues/12).
Decision: **REVIEW**, isolated synthetic research only. No observer integration.
Base: `d2a176c251ec1b684a369d3a1416fa7eb0ade289` (main after documentation PR #11).
Branch: `research/issue-3-offline-refusal-registry`; draft PR required, owner review before any merge.

## Interface and data policy

Optional module: `research/spot_refusal_registry.py`. Pure functions accept supplied
fixture objects or bounded JSON; nothing imports this module into the existing
observer. No I/O, network, wall-clock reads, dependency installation, strategy,
ranking, candidate generation, signal, order, or authorization state is added.
`VALIDATED_DATA` describes synthetic data checks only. Zero to three future
candidates remains a conceptual maximum, never a quota; no such selector exists.

The application fixture envelope is **not a Kraken API response parser**. Exact
fields are `symbol`, `venue`, `market`, `quote`, `timeframe`, `rules`, `bars`.
Identity is exactly Kraken, spot, USD, 1h and BTC/USD, XRP/USD or SOL/USD. Each
bar has exactly `open_time`, `open`, `high`, `low`, `close`, `volume`.
`open_time` and injected `as_of` are integer epoch **seconds**, aligned to UTC
hours, in [2000-01-01, 2100-01-01). Booleans, strings, milliseconds, guessed unit
conversions, misalignment and unsupported dates refuse. No independent
`close_time` is accepted: close is defined as open + 3600; an extra close-time
field refuses as unknown schema. Arbitrarily forged but plausible timestamps
cannot be authenticated by a synthetic validator.

Every eligible OHLCV must be a native int/float, finite, magnitude <= 1e100;
prices positive, volume nonnegative, low <= open/close <= high. Every eligible
bar must be unique and consecutive in its supplied order. Validate all eligible
bars, including those preceding the latest 21; do not silently drop corrupt
older history. Require at least 21 closed hourly bars. Latest-close age <= three
hours passes this data policy; greater age refuses independently per symbol.
This threshold is an explicit research policy, not proof of trading freshness.
No reordering, gap fill, partial-data approval or synthetic/live fallback.

`rules` has exactly boolean `require_spot` and `require_non_spot`: both true
refuses RULE_CONFLICT, only true/false is supported. No score is accepted;
unknown score/config fields refuse rather than influence the decision.
Policy has exactly `version="spot-refusal-v1"` and `future_mode` below. Its
21-bar, 1h, three-hour and identity requirements are fixed, not tunable keys.
Missing policy selects the strict default. Unknown policy versions/keys/values
refuse; future changes require a reviewed version.

## Explicit time contracts and causal limits

- **Default `future_mode="reject"`:** any supplied bar with open + 3600 > as_of
  refuses CANDLE_NOT_CLOSED. A close exactly at as_of is closed.
- **Opt-in `future_mode="as_of"`:** the caller explicitly requests historical
  projection. All rows must still have exact known fields and aligned supported
  seconds timestamps. Only then are bars with open + 3600 > as_of excluded,
  before OHLCV inspection, ordering/continuity, warmup, freshness and hashing.
  Unfinished-at-cutoff bars are excluded too. No excluded count, future price,
  time or detail is returned. Never fall back to future bars when history is empty.

For identical valid context, an existing eligible-history decision and its entire
canonical JSON remain byte-identical after structurally valid future rows are
appended, even if their prices/volume are extreme, invalid or secret strings.
This guarantee covers both valid-data and refused eligible-history results,
within the 512-row / 256 KiB input limits. It does **not** authorize malformed
headers, unknown fields, bad units, unsupported timestamp range or unlimited
future appends. Such input refuses. An eligible corrupt price refuses; an invalid
timestamp is never guessed to be future. A syntactically valid forged future
timestamp is indistinguishable from a real future timestamp without provenance.

`validate_json` enforces strict JSON **before projection**: NaN, Infinity,
overflowing exponents, duplicate object keys, excessive size, invalid encoding,
excessive nesting/parser errors refuse MALFORMED_DATA, including in future rows.
Thus future nonfinite JSON is outside the invariance contract. Direct Python
objects are for trusted synthetic fixture construction; eligible nonfinite
values refuse INVALID_VALUE. Excluded Python values are neither serialized nor
used. Hostile custom Python classes / arbitrary execution are not a supported
input boundary; use the JSON entry point for untrusted serialized input.

## Result and evidence contract

Stable `Reason` enum and constant human detail are separate. `refusal()` maps
unknown external codes to UNKNOWN_REASON, always REFUSED. Output has fixed
identity/context, exact UTC ISO as-of, policy version and future mode, status,
reason code (null only for VALIDATED_DATA), redacted fixed detail, SHA-256 reference.
Unknown symbol or invalid clock is represented as null rather than echoed.
Identity fields describe the required market, not authenticated payload origin;
MARKET_MISMATCH must never be read as evidence that the input was Kraken spot.

Canonical JSON is ASCII, sorted keys, compact separators, allow_nan=False.
Evidence hashes canonical context + reason code + **validated eligible prefix**.
On failure, the prefix stops before the offending bar. This is a deterministic
diagnostic reference, **not a unique full-input hash**, authenticated market
source, signature, tamper-evident ledger, or persisted artifact. Different bad
payloads can intentionally share a refusal reference. Excluded future values,
raw error messages and invalid values never enter details or the digest.
Policy mode is included, so reject/as_of contexts have different references.

`validate_symbols` produces a fixed BTC/XRP/SOL report in that order, with each
symbol evaluated independently. Missing input refuses DATA_UNAVAILABLE for that
symbol. Unknown batch keys invalidate the batch with per-symbol refusals; no
partial unknown-universe acceptance. Caller-owned input is not mutated.
At most 512 bars/symbol, JSON at most 262144 UTF-8 bytes, each result <1024 ASCII
bytes in adversarial tests. This is not a resource-exhaustion security clearance.

## Independent crosswalk against the original audit table

Compared against section 6 of `docs/BOSS-TRADER-ISSUE-3-ARCHITECTURE-AUDIT.md`
at the base above; vocabulary was not copied from third-party source code.

| Proposed audit case / code | This implementation / evidence |
| --- | --- |
| MALFORMED_DATA / MARKET_MISMATCH | Exact envelope/bar fields and market identity; fixture mutation matrix, missing-field tests. Missing payload specifically DATA_UNAVAILABLE. No raw error/result Kraken envelope support. |
| INVALID_VALUE / TIMESTAMP_INVALID | All eligible OHLCV fields at first/middle/last positions, nonfinite/types/oversized values, bounds, bool/string/unaligned time tests. No threshold relaxation. |
| DUPLICATE_TIMESTAMP / TIMESTAMP_ORDER / TIMESTAMP_GAP | Separate duplicate (including nonadjacent), reversed and missing-bar fixtures; input unchanged after refusal. |
| TIME_UNIT_MISMATCH | Unsupported seconds range including milliseconds refuses, no conversion. Also covers dates outside the deliberately supported range; not proof of actual source units. |
| CANDLE_NOT_CLOSED | Strict future/current-open fixtures refuse; explicit as_of projection is separately tested and documented above. No independently supplied close-time field. |
| DATA_STALE | Three-hour boundary, four-hour refusal, fresh BTC/stale XRP and SOL, all-stale batch. No cross-symbol rescue. |
| WARMUP_INCOMPLETE | Empty, 20 vs 21/22 closed bars, future-only and incomplete eligible history tests. |
| INDICATOR_UNAVAILABLE | **Deferred:** no indicators or strategy in this module; 21-bar requirement is only an observation-window policy. |
| RULE_CONFLICT / POLICY_REJECTED / CONFIG_INVALID | Contradictory boolean rules, non-spot policy, unknown keys/version/mode/type. Extreme score field cannot override refusal. |
| UNKNOWN_REASON | Every registered refusal exercised; unknown/null/container/oversized external codes fail closed and are redacted. |
| DATA_UNAVAILABLE | Missing supplied fixture only. HTTP 451, timeout, network routing are not executed or simulated as real operational evidence. |
| Future append invariant | Entire canonical result compared as ASCII bytes, including evidence, context and detail, for valid history; refused-history output invariant also checked. Eligible corruption still refuses. |
| DUPLICATE_OBSERVATION / COOLDOWN_ACTIVE / STATE_INVALID | **Deferred:** pattern 2, no state/persistence. Duplicate bar timestamps remain in scope above. |
| IMMUTABILITY_VIOLATION / EVIDENCE_ALIAS / EVIDENCE_WRITE_FAILED | **Deferred:** pattern 3 ledger/storage absent. Input nonmutation is tested but is not a persistent immutability guarantee. |
| AMBIGUOUS / unresolved metrics / candidate cap | **Deferred:** no outcome model, performance metrics, selector or promotion states. Maximum three/no forced minimum is only a future contract. |

## Verification and acceptance matrix

Python 3.12.14, local Cloud staging copied through the GitHub connector from the
exact base above. Existing source/tests remain byte-identical. Commands from
repository root, no packages installed:

```text
python -B -m unittest discover -s tests -p test_spot_refusal_registry.py -v
Ran 20 tests ... OK

python -B -m unittest discover -s tests -v
Ran 56 tests ... OK
```

Counts are named unittest methods, not coverage percentages: 20 new + 36 existing.
The committed JSON has 27 explicit mutation cases, exercised as subtests; OHLCV
corruption and future mutations use further deterministic subtests. No live or
third-party test run, profitability, vulnerability clearance or future CI result
is implied. A pinned golden valid-data digest is checked along with metadata.
Network socket/connect/urlopen and wall-clock time are patched to raise during
module reload and evaluation; static review confirms only datetime/enum/hashlib/
json/math imports and no I/O. This targeted test is not a general sandbox proof.

| Requirement | Result |
| --- | --- |
| Stable codes/context, unknown-code/config refusal, bounded/redacted outputs | PASS — enum/crosswalk, mutation, JSON, output-bound tests |
| OHLCV/time/order/warmup/market refusals, no repair | PASS — deterministic fixtures and adversarial tests |
| Per-symbol stale refusal, no score rescue or ranking | PASS — mixed/all-stale reports, unknown-score refusal, fixed result schema |
| Explicit as-of future invariance and invalid eligible fail-closed | PASS — full canonical bytes and refusal checks, subject to stated structural/resource boundary |
| Offline/import safety and existing tests preserved | PASS — 56 local tests; connector diff must contain only the four new paths |
| Real Kraken integration, live behavior, performance/security clearance | HOLD / outside scope — no such evidence or authorization |
| Owner integration/merge | HOLD — draft PR, separate owner review required |

## Provenance, limitations and next action

Original BOSS implementation and fixtures, under repository MIT license
(copyright 2026 tazmanked-bot). Architecture inspiration only:
Acekiller88/crypto-signal-scanner at
`431c79bb45fb31ca9609c48ccc0f17376731b9da`, examined by the prior audit.
No upstream code, strategy, futures thresholds, data or dependencies copied or
vendored. Its MIT notice obligations would need separate handling if code were
copied in a future assignment. MIT provides no security warranty.

This module adds no third-party dependency; it does not clear existing research
dependencies, Python/stdlib vulnerabilities, all hostile resource usage or live
data provenance. No market access, external security scan or package install
occurred. Do not turn a synthetic PASS into profitability, signal or approval.
The working Kraken adapter, core, workflows, existing tests and dependency files
remain unchanged. No state, ledger, alerts, paid service, orders or ZUMERAVO work.

**Smallest safe owner action:** review this draft and the strict-versus-as_of,
freshness and diagnostic-hash contracts, then independently rerun the exact
stdlib test commands at the PR head. Keep the PR draft and unmerged pending
owner/BOSS AI review. No automatic issue closure or observer integration.

STOP FOR OWNER AND BOSS AI REVIEW.
