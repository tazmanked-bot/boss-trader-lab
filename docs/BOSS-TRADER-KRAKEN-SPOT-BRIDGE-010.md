# BOSS TRADER LAB — Offline Kraken spot validation bridge 010

Authorization: [Issue #14](https://github.com/tazmanked-bot/boss-trader-lab/issues/14).
Research base: `4c70a6332152f1e67a381dade5aa7c042a019c46` (owner's PR #13 merge).
Review date: 2026-11-05 UTC. **Decision: REVIEW; operational/live use HOLD.**
Branch: `research/issue-3-kraken-spot-validation-bridge`; draft PR only.

## Source evidence and contract mismatches

Inspected baseline `kraken_public_observer.py` and `research/spot_refusal_registry.py`
at the exact base. The former returns closes after dropping the final row;
it cannot supply verified OHLCV and is not imported or modified by this bridge.
The latter remains byte-identical and receives an exact normalized envelope.

Primary documentation inspected through the web connector, without any live
market endpoint request:

- [Kraken REST OHLC](https://docs.kraken.com/api-reference/market-data/get-ohlc-data):
  response example has integer time/count and six numeric strings, a pair key
  and `last`; interval is minutes (60 supported), maximum history is 720 rows,
  and the final row is uncommitted. Its sample uses minute-spaced rows, so that
  sample is not accepted as hourly evidence. Default internal naming differs
  from the optional assetVersion=1 display naming.
- [Kraken AssetPairs documentation](https://docs.kraken.com/api-reference/market-data/get-tradable-asset-pairs):
  example associates XXBTZUSD with XBTUSD, base XXBT and quote ZUSD. This is
  documentation evidence, not a current instrument inventory query.
- [Kraken OHLCVT unit definitions](https://support.kraken.com/in/articles/360047124832-downloadable-historical-ohlcvt-open-high-low-close-volume-trades-data):
  prices are in the quote asset and volume is quantity of the base asset. The
  historical CSV format is not this REST parser's eight-field format.

The rendered REST page exposed its example but not expanded child-schema field
descriptions. The implementation fixes the conventional REST ordering below as
an explicit reviewed research contract; it does not claim machine-validated
OpenAPI conformance. The attempted Markdown rendering was unsupported, the legacy
page was inaccessible, and a guessed krakenfx/api-specs repository returned 404.
No bypass or package download followed. The precise current XRP/SOL alias inventory
and expanded REST schema still need independent confirmation before any future
live authorization. Search snippets are not accepted as live-schema proof.

| Schema concern | Bridge contract / evidence / limitation |
| --- | --- |
| Observer closes vs complete registry bars | No observer reuse or OHLC fabrication. Independent expected-envelope test asserts every converted field and all 21 timestamps. |
| REST row positions | Exactly `[time, open, high, low, close, vwap, volume, count]`; exact width eight, no extra positional fields. VWAP/count validated but not part of the registry envelope; covered by a separate bridge digest. |
| Source identity | Exact supplied metadata plus one allowed response key. Request XBTUSD -> XXBTZUSD or XBTUSD; XRPUSD -> XXRPZUSD or XRPUSD; SOLUSD -> SOLUSD. Alias tests exercise all accepted/rejected combinations. Only BTC internal/alt names independently supported by the inspected AssetPairs example; others are conservative research allowlist assumptions, not live verification. |
| Additional/display aliases | BTC/USD display key, dark-pool suffixes, USDT, other pairs and multiple/ambiguous response keys refuse. assetVersion=1 capture metadata is not supported; no fuzzy normalization. |
| Interval/units not in response rows | Capture must assert interval_minutes=60; seconds/hour alignment and exact 3600-second eligible spacing are checked. An asserted interval or venue cannot authenticate source or aggregation. No resampling or scaling. |
| Final uncommitted row | Strict mode refuses it if unfinished/future; never blindly drops the last position. Projection is explicit and timestamp-based, not proof of capture-time commitment. |
| `last` cursor | Required bounded integer seconds, need not be hour-aligned; never a close/price/freshness signal. Valid cursor changes are excluded from output/evidence; malformed cursors refuse. No incremental fetch. |
| History cap | Bridge accepts <=512 source rows (including excluded ones), stricter than the documented 720. No truncation/repair; excessive capture refuses. |
| Registry 21 bars / 3h freshness | Unchanged. Every eligible bar must pass, including older-than-window bars. Gap, duplicate/order, warmup and per-symbol staleness refusals remain registry decisions. |

## Exact input/output contract

Optional pure module: `research/kraken_spot_validation_bridge.py`.
`validate_capture(symbol, capture, *, as_of, policy=None)` is the Python fixture
entry point; `validate_capture_json` is the bounded serialized input boundary.
`validate_captures` returns fixed BTC/USD, XRP/USD, SOL/USD results independently,
with no aggregate approval, selection, fallback or candidate list. Unknown batch
keys invalidate all three entries; missing capture refuses only that symbol.

Capture has exactly these fields (metadata is an assertion, not provenance):

```json
{"venue":"kraken","market":"spot","quote":"USD","symbol":"BTC/USD",
 "request_pair":"XBTUSD","interval_minutes":60,
 "response":{"error":[],"result":{"XXBTZUSD":[],"last":1899997200}}}
```

The empty example refuses warmup. Synthetic fixtures contain 21 closed rows and
one unfinished-at-cutoff row for each symbol; all values are original test data,
not market captures, account data or profitability observations.

Response must have exactly `error,result`, error must be an empty list, result
exactly one allowed pair key plus `last`. API error content is never echoed.
Source time/count must be native ints, excluding booleans. Time is aligned UTC
epoch seconds in [2000-01-01,2100-01-01); as_of is mandatory and hour-aligned.
Do not int() strings/floats, guess milliseconds, sort, fill gaps or infer bars.

Eligible price/VWAP/volume fields must be decimal strings, at most 128 characters,
ASCII grammar `-?(0|[1-9][0-9]*)(\.[0-9]+)?`. No exponent, whitespace, plus,
underscore, comma, NaN/Infinity, native numeric substitutes or negative sign
(including negative zero). OHLC/VWAP positive; volume nonnegative; magnitude
<=1e100. Exact Decimal bounds require low <= open/close/VWAP <= high **before**
conversion. Count is an integer in [0,2^53-1]. Zero volume/count is permitted;
the parser does not prove consistency against underlying trades. Zero VWAP is
deliberately unsupported even for no-trade bars; unknown source conventions
refuse rather than receive fabricated prices.

Prices remain USD per base unit; volume remains base units. No lot multiplier,
quote-volume invention, stablecoin conversion or venue substitution. Decimal ->
float is required by the existing registry. Relative conversion error must be
<=1e-15, with no underflow-to-zero, nonfinite result, or distinct source prices
collapsing to the same float. Ordinary 0.1 rounding is permitted and tested;
this is bounded approximation, not exact decimal preservation in the registry.

Output: bridge version, fixed source_claim=provided_kraken_shaped_fixture,
stable bridge_code, **unchanged registry decision**, separate SHA-256 evidence_ref.
Registry `VALIDATED_DATA` means only data checks, never a signal or permission.
Bridge evidence hashes version/code, entire registry decision and exact eligible
eight-field source rows (including original decimal strings, VWAP and count).
Alias alternatives normalize to the same contract; source aliases/cursor and
excluded future rows are not in the digest. Changes to VWAP/count/source precision
can change bridge evidence while leaving normalized registry evidence unchanged.
Parser failures have no partial rows in evidence. Hashes are diagnostic references,
not signatures, whole-capture hashes, authenticated origin or an audit ledger.

## Two explicit time policies; no position-based discard

Policy is the existing registry dict: version=spot-refusal-v1 and future_mode
`reject` (default) or `as_of`. Both are recorded inside the returned decision;
bridge version records these conversion/transport rules. Unknown policy refuses.

**Strict:** any row whose open+3600 > as_of yields the registry's
CANDLE_NOT_CLOSED refusal, including the normal Kraken uncommitted last row.
Its numeric fields never enter evidence. A full current raw response is therefore
expected to refuse; the bridge has no exception that quietly grants validation.
Closed-only synthetic subsets can pass strict mode; no final closed row is dropped.
This differs intentionally from the operational observer's positional drop.

**Explicit historical projection:** all rows still need exact width and valid
timestamp type/unit/alignment/range. Ineligible rows are then excluded before
numeric/VWAP/count parsing, order/continuity, registry validation and hashing.
No excluded count, latest price, cursor or future timestamp is reported. Within
the schema and resource boundaries, append-only future rows (even adversarial
price/count strings) leave the **entire canonical JSON bytes** unchanged at fixed
as_of. Tests cover both valid and refused eligible history and changed cursors.
No empty-history fallback; invalid eligible values or timestamps always refuse.

The serialized boundary rejects duplicate keys, nonfinite JSON literals and
overflowing JSON numeric exponents globally, even in excluded rows. Malformed
headers, oversized input and unsupported units are outside the invariance
contract and refuse. Native Python objects are a fixture convenience, not a
sandbox for hostile classes. Projection cannot authenticate a plausible forged
timestamp, prove a historical row had committed at capture time, detect later
revision of an eligible row, or establish what an exchange actually published.
Use only supplied deterministic fixtures here; future real captures need their
own capture-time/source integrity specification and owner approval.

## Fixed refusal taxonomy

| Layer | Codes / behavior |
| --- | --- |
| Invalid context | CONTEXT_INVALID; registry returns its own CONFIG_INVALID / timestamp / market refusal. No source parsing. |
| Missing or excessive input | SOURCE_MISSING, SIZE_LIMIT; DATA_UNAVAILABLE, no partial normalized bars. Bound: 262144 serialized bytes, <=512 source rows. |
| Serialized/schema failure | JSON_INVALID, CAPTURE_INVALID, SOURCE_SCHEMA, ROW_SCHEMA; DATA_UNAVAILABLE. Duplicate keys, unknown fields, bad JSON, nonfinite literals and parser exceptions are redacted. |
| Source/API identity | IDENTITY_MISMATCH, SOURCE_API_ERROR, PAIR_MISMATCH, CURSOR_INVALID; DATA_UNAVAILABLE, no mirrors or retries. |
| Eligible conversion | TIMESTAMP_INVALID, NUMERIC_INVALID, PRICE_BOUNDS, COUNT_INVALID, PRECISION_LOSS; DATA_UNAVAILABLE, no partial result. |
| Registry stage | PARSED means registry-stage result, **not PASS**; includes CANDLE_NOT_CLOSED or gap/order/duplicate/warmup/stale refusal as well as VALIDATED_DATA. |

No raw exception/body/credential strings are returned. Bridge outputs remain
<1600 ASCII bytes in adversarial refusal tests. Unknown output codes cannot be
injected through input. First detected parser failure has priority; refusal-code
precedence across multiple simultaneous defects is not a completeness report.

## Exact test evidence and acceptance

Local Python **3.12.14**, stdlib only; no installations. From staged repository root:

```text
python -B -m unittest discover -s tests -p test_kraken_spot_validation_bridge.py -v
Ran 20 tests in 0.105s
OK

python -B -m unittest discover -s tests -v
Ran 76 tests in 0.168s
OK
```

Counts are unittest methods: **20 new + all 56 existing**, with deterministic
adversarial subtests, not a coverage percentage. Existing 17 Python/fixture files
match base Git blob hashes. Only the four new paths below belong in this PR.
Network socket/create_connection/urlopen and wall-clock time calls are patched
to raise during module reload/execution; source imports are stdlib and the
existing registry. This focused test is not a general security certification.

| Acceptance | Evidence / status |
| --- | --- |
| Complete original OHLCV translation, no fabricated closes | PASS — independent hand-expected 21-bar envelope and actual registry call assertion. |
| Identity, schema, errors, bounds, types, units and rounding refusal | PASS — alias/metadata/source/column/time/precision adversarial tests. |
| Unchanged continuity, 21-bar warmup and 3h per-symbol stale rules | PASS — boundary, missing, all-three, fresh BTC with stale XRP/SOL cases. |
| Strict uncommitted refusal and historical no-lookahead | PASS — current/future refusal and complete canonical-byte equality under the documented projection policy. |
| Existing regression tests preserved | PASS — 76 local tests, baseline hash comparisons; no existing file edits. |
| Current real Kraken schema/aliases/capture provenance | HOLD — partial documentation evidence only, no live request or fresh capture. |
| GitHub CI, live exchange, operational readiness, security/performance | HOLD — no run or clearance claimed. No trading evidence can follow from these fixtures. |

## Review gate and smallest safe follow-up

New files: `research/kraken_spot_validation_bridge.py`,
`tests/test_kraken_spot_validation_bridge.py`,
`tests/fixtures/kraken_spot_bridge_v1.json`, this report.
Original BOSS code/test data under the repository's MIT license; no third-party
implementation copied, no dependencies added. Existing registry, observer,
core, tests, workflows and dependency files remain unchanged.

**Smallest owner action:** inspect the draft at its exact commit, then authorize
a **manual offline Actions run pinned to that commit**, using only these unittest
commands, contents:read, no secrets/write credentials/network-dependent steps,
short timeout and bounded output. No workflow is added/changed/launched here.
An existing launcher named for PR #13 must not be assumed to test this new head.

A later live probe is a **proposal only**, not implemented or authorized:
separate owner decision, exact source/request/alias and capture-time specification,
one bounded public spot request per approved symbol, strict response size/timeouts,
no credentials, retries-to-evade, fallbacks, schedule or observer replacement.
Its handling of the known uncommitted row must be separately reviewed; projection
does not grant operational acceptance. Keep present work draft and unmerged.

No live requests, orders, paper execution, alerts, rankings, recommendations,
opportunity calculations, paid services, futures, ZUMERAVO or desktop migration.
No issues closed. **STOP FOR OWNER AND BOSS AI REVIEW.**
