# BOSS-TRADER-SOURCE-AWARE-CANDIDATES-023

[Issue #40](https://github.com/tazmanked-bot/boss-trader-lab/issues/40); exact baseline **`f7081a3a51f7a80917cd03256d0d57eec26fd390`**, owner merge of PR #39.

**OFFLINE PREVIEW PASS; PUBLIC LIVE SOURCE ADMISSION / OPERATIONAL MODE HOLD.** This adds a separate static-fixture WATCH/WAIT/BLOCKED experiment, not a public-data admission mechanism. WATCH is not BUY, ENTRY READY, a signal to execute or trading permission. No empirical performance claim.

The [README responsibility policy](https://github.com/tazmanked-bot/boss-trader-lab/blob/f7081a3a51f7a80917cd03256d0d57eec26fd390/README.md#data-source-responsibility-public-repository) remains controlling: individual users assess their own provider data-use rights. No blanket licensing approval or outreach prerequisite is added. Technical safeguards remain separate. ZUMERAVO stays separate.

## What is available

| Layer | Status |
| --- | --- |
| Existing manual public close-only Kraken observer/workflow | **AVAILABLE, unchanged**, not invoked here; not the full-OHLCV reversal feed |
| Merged 022 static Kraken-shaped normalization prototype | **Unchanged HOLD / CANDIDATE_SOURCE_TYPE_NOT_ADMITTED**, requests=0; no candidate evaluator call |
| New optional source-aware experiment | **PASS offline** on qualified static synthetic Kraken-shaped fixtures; 0–3 WATCH, WAIT or BLOCKED, explicit NOT LIVE label |
| Existing SYNTHETIC_ONLY evaluator | **Unchanged**; still rejects proposed public feeds as all BLOCKED |
| Any actual trusted public/live candidate admission | **HOLD / not implemented**, including the hypothetical VERIFIED_PUBLIC_SPOT_OBSERVATION type |
| Trade authority | **NONE**, regardless of preview or data-check success |

## Exact contracts and implementation

Inspected pinned sources: [022 prototype](https://github.com/tazmanked-bot/boss-trader-lab/blob/f7081a3a51f7a80917cd03256d0d57eec26fd390/research/kraken_spot_reversal_bridge_prototype.py) and [report](https://github.com/tazmanked-bot/boss-trader-lab/blob/f7081a3a51f7a80917cd03256d0d57eec26fd390/docs/BOSS-TRADER-PRACTICAL-KRAKEN-BRIDGE-022.md), [candidate `_features`/`evaluate`](https://github.com/tazmanked-bot/boss-trader-lab/blob/f7081a3a51f7a80917cd03256d0d57eec26fd390/research/spot_reversal_candidates.py), [registry](https://github.com/tazmanked-bot/boss-trader-lab/blob/f7081a3a51f7a80917cd03256d0d57eec26fd390/research/spot_refusal_registry.py), [REST-shaped bridge](https://github.com/tazmanked-bot/boss-trader-lab/blob/f7081a3a51f7a80917cd03256d0d57eec26fd390/research/kraken_spot_validation_bridge.py), existing synthetic candidate/groundwork tests and README. No source is extracted or modified.

New API: `research.spot_reversal_source_preview_023.preview_offline(text, clock=..., clock_evidence_verifier=..., expected_context=...)`. It accepts only explicitly supplied static JSON and trusted injected **test** dependencies. No URL/file loader, transport/provider, live flag, real-clock collector, keys or prevalidated-report argument exists.

### Proposed static observation contract, supported now

Input is **exactly the existing 022 raw fixture envelope**, with `source_tag=PUBLIC_SPOT_OBSERVATION_PROPOSED`, `fixture_origin=SYNTHETIC_STATIC_KRAKEN_JSON`, its exact version, synthetic clock-model evidence and all three identity/OHLC fixture observations. The new API calls that prototype itself, every invocation. It does not accept copied normalized feeds, earlier source reports, `verified=True`, a hash or a label as an admission token. The prototype performs the same identity/metadata/commitment/clock/complete-history checks and global STOP.

Only a fresh complete result with all three VALIDATED_PROPOSED_DATA rows, original HOLD/NOT_ADMITTED state, exact source/origin/model-clock types and expected feed schema can reach research calculation. The preview then independently revalidates **all supplied eligible history** through the original registry, requires canonical equality with every original bridge decision and checks no normalized row closes after as_of. All three revalidations must pass before **any** feature call. No sorting, warmup bypass, tail cleaning, filling, deduplication or changing the cutoff.

It calls the **exact existing `spot_reversal_candidates._features`** on those validated bars. There is no surrogate formula or call to `evaluate` with a relabeled source. The four predicates, exact Fraction arithmetic and scores are unchanged. Qualification remains their conjunction; sort is `(-score,symbol)`, maximum three and minimum zero. The new module repeats only the two fixed presentation strings (why-early/invalidation); complete canonical row/rank parity tests protect them too. Any later change to that private shared API requires renewed parity review, not an unreviewed rule fork.

All data/clock provenance here is explicitly a **synthetic model**. A declared tag/fixture origin/callback cannot authenticate real records or UTC. Actual exchange data must not be supplied under a synthetic origin. Even if someone falsely asserts an origin, the output cannot become a verified/live signal: live admission and operational state stay HOLD, authority NONE. This API is not a sandbox for arbitrary injected Python code or an authentic-origin detector.

### Future verified public observation contract, design only

`VERIFIED_PUBLIC_SPOT_OBSERVATION` is **unsupported and refused now**. A future separately reviewed contract would need genuine bounded transport/capture receipts bound to exact revision/run/host/clock domain, independently supported initial UTC and validity horizon, verified current instrument/expanded schema, immutable eligibility cutoff, real byte/deadline/cleanup/global-stop evidence and a source producer/verifier boundary distinct from user-supplied dictionaries. Source strings, copied hashes, `trusted=True`, HTTP Date or green tests cannot establish those facts. No verifier/collector or admission implementation is supplied here.

Keep these claims separate: source typing declares a category; authentic source provenance is not established by the fixture; registry validation establishes modeled data quality; the mock clock establishes only test consistency; the shared calculation establishes deterministic candidate logic; none grants trade authority.

## Refusal and clock precedence

If the prototype fails or stops partway, the **whole preview is BLOCKED with zero candidates**, no features/scores and no accepted as_of. `source_boundary` retains the original per-symbol data/stage causes, including earlier validated BTC evidence and later NOT_ATTEMPTED symbols. Earlier source success cannot yield a partial WATCH batch after an XRP/SOL failure. Null preview validation fields mean the preview did not calculate, not that earlier source evidence was erased.

Preserved conditions include exact Kraken spot USD identity/base volume; 21+ closed 1h bars; all eligible history; source precision/VWAP/count checks; finite positive prices/nonnegative volume; gap/order/duplicate/staleness and raw-current-row commitment rules. A malformed current timestamp/future append beyond the capture envelope refuses. Stale captures can hit COMMITMENT_CONFLICT before the registry's DATA_STALE rule, exactly as in 022. No false PASS is obtained by changing refusal precedence.

Modifying only excluded current OHLCV/count preserves **complete canonical preview output** under the same static context. An appended timestamp beyond the approved capture hour, malformed serialization/header, row/byte overflow or invalid eligible data intentionally refuses; this is not an unconditional append-anything invariant. No current values, raw arrays or raw exception strings are emitted in the preview.

The injected clock is forwarded unchanged while recording initial/previous anchors; no `trusted` value is invented. Extra checkpoints cover registry/features/output hashing/serialization within the same modeled <10s processing budget, equality expired, monotonic progression and <=1s wall/monotonic disagreement. Source lease requirements remain unchanged. Failed late checks discard **all** partial WATCH rows and evidence. These are deterministic mock-time control-flow checks, not preemptive Python parsing or hard OS/UTC guarantees.

## Operator-facing sample

This abbreviated sample reflects the existing invented 022 fixture and passing tests; it is **not an actual market record or current timestamp**:

```text
mode: STATIC_FIXTURE_EXPERIMENT_ONLY
source: STATIC_SYNTHETIC_KRAKEN_SHAPED
source_tag: PUBLIC_SPOT_OBSERVATION_PROPOSED
as_of: 1900000800 (synthetic coordinate, NOT current UTC)
BTC/USD: WATCH; XRP/USD: WATCH; SOL/USD: WATCH
rank: BTC/USD, SOL/USD, XRP/USD; each shape score=26666
why_early: Downside slowed, low retest held, fresh bounded recovery with consistent volume.
invalidation_observation: a later eligible low below the observed retest anchor
  would invalidate the research condition; no order or stop price.
catalyst_status: UNVERIFIED
source_boundary: HOLD / CANDIDATE_SOURCE_TYPE_NOT_ADMITTED / NOT_ADMITTED
live_source_admission: HOLD; operational_mode: HOLD; trade_authority: NONE
warning: candidate preview only; NOT LIVE; NO TRADING AUTHORITY
```

Valid but unqualified data produces WAIT; source/clock/data failures produce BLOCKED and no candidate list. No market price, entry/stop level, fabricated catalyst or confidence probability is displayed. Feature strengths are descriptive ranking units, not a profitability estimate.

## Exact tests and resource bounds

Three additions only:

- `research/spot_reversal_source_preview_023.py`
- `tests/test_spot_reversal_source_preview_023.py`
- This report.

The existing clearly labeled `tests/fixtures/kraken_reversal_groundwork_022.json` is reused unchanged; no duplicate dataset or actual candles are introduced. For parity, tests construct genuinely synthetic references separately from raw synthetic fixtures. They never relabel a proposed public feed as synthetic for evaluation.

Local CPython **3.12.14**, stdlib only, no installs:

```text
python -B -m unittest discover -s tests -p test_spot_reversal_source_preview_023.py -v
Ran 36 tests in 0.257s
OK

python -B -m unittest discover -s tests -v
Ran 347 tests in 4.942s
OK

python -B -m research.spot_reversal_source_preview_023 --live --authorize
AUTHORIZATION_MISSING; requests=0; preview_status=BLOCKED;
live_source_admission=HOLD; trade_authority=NONE; exit 2
```

**311 preserved baseline +36 new =347 methods, no skips.** Coverage: complete canonical rows/ranks for 0/1/2/3 WATCH and ties, each failed feature, flat/rally/chase, contradictory/zero/spike volume, exact/binary boundary and existing rising synthetic fixture; source/evaluator rejection unchanged; copied report/feed/hash and fake verified/real-clock markers rejected; incomplete global-stop batch; stale/gap/order/duplicate/warmup/full-history/value/identity refusals; excluded-current no-lookahead; internal source/registry mutation sensitivity; feature/output deadline expiry, clock reversal/jump, nonfinite shared output and redaction; bounded parser/output, deterministic/no mutation, disabled CLI/import.

Every new test guards/asserts zero socket/connect/DNS/urlopen/HTTPSConnection/subprocess/time.time calls. Import/default/CLI tests also block file opening. Existing full-suite transports are mocked; local fake-worker lifecycle tests remain offline and baseline TLS-context tests may load public roots without a handshake. No provider request, time-service query or live diagnostic occurred. Python 3.11/current-head Actions and actual target-runner performance remain unverified.

Inherited source JSON cap is 2MiB, per-stage supplied body/capture <=262144 bytes and 512 rows per symbol; new preview output <=32768 ASCII bytes, no raw price arrays. Work is bounded to three registry revalidations and three calls over at most 512 bars to the same pure feature calculation, plus bounded serialization. CPU time/peak RSS on target are UNMEASURED; byte caps/mock timing are not heap or universal deadline guarantees. No optimization, worker pool, polling, busy wait, network loader, dynamic imports, dependencies or service installation is added.

## Next owner action and later live test

**Smallest next owner action:** independently run focused/full **offline** checks pinned to this exact draft head, confirm immutable checkout/runtime/counts, then review source-boundary and parity evidence. No workflow or dispatch is created here. Existing observer, registry, evaluator/formulas, bridge/prototype, historical replay, README, tests, workflows and dependencies are byte-identical to the baseline. No licensing-clearance/outreach prerequisite is introduced.

A smallest **subsequent**, separately technically approved full-OHLCV observation could be one BTC/USD AssetPairs GET then one identity-gated OHLC GET: **at most two attempts**, single invocation, global STOP at the first failure. A later approved three-symbol batch is **at most six GETs** in BTC/XRP/SOL order. Neither mode exists in this new preview, and neither is executed now.

Before any new real request: exact reviewed future source-aware implementation and immutable head; independent <=2s UTC provenance, clock-domain/lease/cutoff validity; actual runner/start/kill/reap evidence; bounded HTTP streaming before header/body allocation; existing 10s total request/250ms cleanup semantics; strict JSON/framing/byte limits; fixed `api.kraken.com:443` public paths/query allowlist; real identity/schema acceptance and global STOP. Unknown optional schemas or aliases fail closed; no discovery response automatically expands an allowlist. No retries, redirects, alternative hosts/proxies, server-time extra call, schedules, alerts or orders. Collect only approved redacted stage/count/identity/clock/resource/refusal references for owner review, not raw candles/headers/keys/current values.

B1/B2 real transport/startup/headers and B3 actual live executor/global STOP remain HOLD; B5 target runner remains HOLD. Strict B4 independent UTC is NO-GO, alternate historical clock policy PROPOSED/HOLD. If required evidence is absent, zero new full-feed requests; the existing documented close-only observer scope is unchanged. No prototype/preview PASS or owner merge self-promotes public live source admission or Operational Test Mode.

Exact head/branch/Draft PR are in the final handoff; no main modification, merge, issue closure, real data fetch, API keys, notifications, paper/live orders, futures/leverage, paid infrastructure, VM or ZUMERAVO work.

**STOP FOR OWNER AND BOSS AI REVIEW.**
