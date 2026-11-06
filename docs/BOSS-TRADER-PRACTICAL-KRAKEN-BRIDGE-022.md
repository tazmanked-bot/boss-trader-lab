# BOSS-TRADER-PRACTICAL-KRAKEN-BRIDGE-022

[Issue #38](https://github.com/tazmanked-bot/boss-trader-lab/issues/38), exact baseline **`00135bd27bd36dad3c044a4274dc03612a21ee64`**.
**Result: offline source-normalization groundwork PASS; new full-OHLCV live reversal feed HOLD.** No trading or profitability claim.

The [updated README policy](https://github.com/tazmanked-bot/boss-trader-lab/blob/00135bd27bd36dad3c044a4274dc03612a21ee64/README.md#data-source-responsibility-public-repository) controls: **each individual user is responsible for their provider terms/data-use rights**. Previous archive-rights reports are historical assessments, not a universal licensing-clearance or outreach prerequisite. This prototype adds no such gate. Technical clock/transport/source-admission safeguards remain separate and unchanged.

## What works now

| Component | Current status / boundary |
| --- | --- |
| Existing `kraken_public_observer.py` and manual Kraken workflow | **AVAILABLE, unchanged** within documented public close-only OBSERVE_ONLY scope; not run here. They do not supply the full verified OHLCV/volume evidence needed by reversal features. |
| Existing synthetic reversal engine | **PASS offline**, unchanged 0–3 WATCH/WAIT/BLOCKED, terminal registry refusal. WATCH is not BUY, ENTRY READY or an order. |
| New optional prototype | **PASS offline normalization/parity**, static synthetic JSON + injected test clocks only; zero requests and overall HOLD even on success. |
| Proposed public-source candidate admission | **HOLD / NOT_ADMITTED**. The engine rejects the proposed source type. No data is relabeled SYNTHETIC_ONLY to make it run. |
| B1/B2/B3/B5 new live path | **HOLD** for real startup/deadline/stream/header, integrated executor and actual target-runner evidence. Offline call sequencing is not live enforcement. |
| Strict B4 UTC / alternate clock policy | **NO-GO** for independent real <=2s attestation on present evidence; alternate policy remains unadopted. Mock provenance never closes B4. |

The existing manual workflow makes three close-only OHLC attempts and can continue per-symbol after failures; its observer uses its own timeout/current-row rules. It is not the new full-feed global-stop path. This work neither disables that available feature nor upgrades it into a validated reversal pipeline.

## New input contract and exact processing

`research.kraken_spot_reversal_bridge_prototype.run_offline(text, clock=..., clock_evidence_verifier=..., expected_context=...)` accepts an explicitly supplied JSON **string**, not a URL, filename, transport or market loader. All dependencies are trusted injected test code, not sandboxed arbitrary callbacks.

Envelope has exactly:

```text
version: kraken-reversal-groundwork-v1
source_tag: PUBLIC_SPOT_OBSERVATION_PROPOSED
fixture_origin: SYNTHETIC_STATIC_KRAKEN_JSON
clock_evidence: <exact synthetic clock model, below>
observations:
  BTC/USD, XRP/USD, SOL/USD:
    identity: {http_status, service_date_utc_seconds, payload: <AssetPairs-shaped JSON>}
    ohlc: {http_status, service_date_utc_seconds, capture: <existing bridge capture>}
```

There is no `label: SYNTHETIC_ONLY`, score, authorization flag, licensing approval, extra symbol or unknown field in this contract. Fixture origin truth remains a caller assertion; this is not authentic-market admission. Public-source typing stays visible in output.

The identity profile reuses the existing diagnostic's `_identity` checks and requires **exactly the seven required fields** (altname, wsname, base, quote, aclass_base, aclass_quote, status). Optional expanded metadata is deliberately unsupported and refuses; the prototype does not claim its types or current server compatibility are verified. Required values include online status, currency classes and quote ZUSD:

| Symbol | Request pair | Exact identity/OHLC key | Base / display |
| --- | --- | --- | --- |
| BTC/USD | XBTUSD | XXBTZUSD | XXBT / XBT/USD |
| XRP/USD | XRPUSD | XXRPZUSD | XXRP / XRP/USD |
| SOL/USD | SOLUSD | SOLUSD | SOL / SOL/USD |

These are existing local assumptions tested synthetically, **not verified current live instruments/aliases**. The broader bridge alias list cannot override exact identity agreement.

Capture schema remains the existing bridge's exact venue/market/quote/symbol/request_pair/interval_minutes/response envelope. Interval is integer 60. Response is empty error list plus one matching pair key and integer seconds cursor. Rows retain all eight raw positions:

`[open_time, open, high, low, close, vwap, base_volume, trade_count]`.

Aligned supported UTC epoch **seconds** are required. The six numeric fields are strict decimal strings; count is a bounded native integer. Existing price/VWAP bounds, precision-loss, positive finite price/nonnegative base-volume, >=21 closed contiguous bars, full eligible history, <=3h relative staleness and 512-row limits are unchanged. No sort/fill/tail repair, invented VWAP/volume or positional deletion.

Processing is fixed BTC→XRP→SOL, identity then OHLC per symbol, **global STOP on first failure**, even though no real request occurs. Partial earlier bridge evidence is retained; subsequent symbols are NOT_ATTEMPTED. No proposed batch feed is returned unless all three fully validate. HTTP 451/429/redirects/non-200, API errors and schema/identity/clock/normalization failures are terminal; no retries or alternate routes.

Outer `_commitment` rejects source timestamps beyond the capture/service envelope and requires the purported current final row to remain ineligible. Thus an old “current” row that would enter the cutoff, or an old prefix with a gap into the current row, refuses **COMMITMENT_CONFLICT before registry staleness**. The underlying registry's DATA_STALE rule is independently retained/tested; refusal precedence is not changed to manufacture a specific reason.

Only after full existing bridge validation does the prototype convert eligible OHLC/base-volume decimals to normalized floats. It revalidates that payload using the unchanged registry and requires **complete canonical registry-decision/evidence equality** with the bridge result; mismatch refuses. The bridge's eligible exact-source reference retains VWAP/count/decimal evidence separately. Current excluded OHLCV/count never enter the normalized payload or evidence hashes; malformed JSON/header/timestamp and total-size limits still refuse.

On success output contains a `PUBLIC_SPOT_OBSERVATION_PROPOSED` feed with the 21+ eligible bars, source/clock references and explicit fixture origin. **It is intentionally rejected by the current candidate evaluator**, which is never called by the prototype. Status stays HOLD / CANDIDATE_SOURCE_TYPE_NOT_ADMITTED. This is useful validated adapter groundwork; source-aware candidate integration needs a distinct technical review without changing formulas or existing admission rules.

## Clock and resource limits

Only an injected clock and explicit synthetic evidence verifier are supported; no system/time-service clock provider exists. Evidence fields are exactly kind, authority, utc_ns, mono_ns, valid_until_mono_ns, uncertainty_ns, revision/run_id/boot_scope. Kind/authority must explicitly denote the synthetic independent-attestation model, not a real attestation. The expected context is supplied separately; revision is 40 hex, bounded nonsecret context strings, native integer units, uncertainty <=2 seconds, matching initial anchor and lease strictly beyond the modeled processing deadline. Missing/false/exceptional verifier, mismatched/self-attested/expired evidence refuses.

Existing `CaptureClock` is reused unchanged: freeze `as_of=floor((initial_UTC_seconds-2)/3600)*3600`, relative wall/monotonic consistency <=1s, service Date ±2s consistency and <10s stage elapsed. An initial test anchor is taken **before JSON/verifier work**; checkpoints enforce the additional whole-fixture <10s processing budget and lease, equality expired. Injected synthetic time proves control-flow refusal, not measured elapsed CPU time or actual independently trusted UTC. Booleans/callbacks cannot produce live GO.

JSON input <=2MiB, each stage supplied payload/capture <=262144 bytes and existing bridge's own stricter serialized cap applies. Output <=1MiB with fixed error categories; eligible arrays are returned only in-process, not printed by the CLI. Parser rejects duplicate keys, nonfinite/overflow numbers, invalid encoding and recursion failures, including serialized errors in an excluded row. Repeated input/copies and JSON heap overhead are not RSS guarantees. Parsing/callback/native work cannot be preempted by Python checkpoint tests; B1 real deadline and B2 live preallocation/header constraints remain HOLD. No header parser, HTTPS constructor, dynamic import, file loader, subprocess, monitoring or network path is added.

The synthetic fixture is `tests/fixtures/kraken_reversal_groundwork_022.json`, explicitly labeled SYNTHETIC_TEST_ONLY_NOT_MARKET_CAPTURE. It has invented 21 closed bars plus one current excluded row per symbol, and a **separate genuinely synthetic reference** for tests. Reference evaluation yields 0–3 WATCH as fixtures vary; the proposed public feed itself is never reclassified or evaluated. Fixture byte SHA-256: `761c171e090bcfc14c8ab87ea4ce3a20b8278aa01b6445e0871438dc4fc8285b`. This identifies invented bytes, not provenance/authenticity of actual market data.

## Exact offline tests and next usable step

Local CPython **3.12.14**, stdlib only, no installs:

```text
python -B -m unittest discover -s tests -p test_kraken_reversal_groundwork.py -v
Ran 32 tests in 0.162s
OK

python -B -m unittest discover -s tests -v
Ran 311 tests in 4.280s
OK

python -B -m research.kraken_spot_reversal_bridge_prototype --live --authorize
AUTHORIZATION_MISSING; requests=0; proposed_input=null; overall=HOLD; exit 2
```

**279 unchanged baseline +32 new =311 methods, no skips.** New tests guard/assert zero socket/connect/DNS/urlopen/HTTPSConnection/subprocess/time.time calls; reload also guards file opening. No real endpoint test or clock query occurred. Existing full-suite mocked transports/local child lifecycle checks remain offline; local public trust-root loading in baseline tests is not a handshake. Python 3.11/current-head Actions and actual runner performance remain unverified.

Coverage: complete synthetic normalization/registry parity; separate 0/1/2/3 candidate references and stable tie; unchanged engine rejecting proposed feed; default/flag refusal; missing/bad/expired/binding-mismatched clocks, reversal/jump/deadline equality and Date conflict; exact hour/warmup boundary; excluded-current complete-output invariance; future timestamps; eligible invalid price/volume/VWAP/count; zero volume; stale/commitment precedence; gaps/duplicates/order/old invalid history; identity/optional metadata/aliases; HTTP/API global STOP; size/row/JSON bounds; score injection; actual parity sensitivity by corrupting the second registry evidence result; deterministic output and redacted exceptions.

Four additions only: the prototype, fixture, `tests/test_kraken_reversal_groundwork.py` and this report. All existing code/tests/workflows/dependencies/README stay byte-identical to the baseline, including the working observer, refusal registry, reversal formulas and generator-only replay gate.

**Smallest next owner action:** run a separately owner-triggered **offline** check pinned to this exact draft head on the intended Python/runner, then review its normalization/source boundary and current unresolved technical evidence. No new workflow or dispatch is added here. Individual data-use responsibility remains with the user; no archive-license/outreach step is imposed.

## Later smallest public-observation proposal — NOT implemented or executed

The existing close-only manual feature retains its documented scope. A **new full-OHLCV** preview is a separate future implementation/review, not a flag on this prototype. Once its technical gates are actually supported and separately approved, the smallest initial observation could be BTC/USD only: **at most two GET attempts**, one fixed-host public AssetPairs request, then one identity-gated hourly OHLC request, global STOP at first failure. This would review data/identity consistency only, not produce a WATCH batch. This prototype requires all three fixture symbols and does not implement that proposed single-symbol transport.

A later three-symbol batch, if separately approved, is **at most six GETs** in fixed BTC/XRP/SOL order, one identity then one OHLC each. Fixed `api.kraken.com:443`, approved public paths/queries/interval/since, no server-time extra call, retries, redirects, alternate hosts/proxies, schedules, alerts or orders. Before the first request require exact reviewed future commit, disabled-by-default one-shot authorization, real clock provenance/validity, target runtime/cleanup and B1/B2 bounded provider evidence, coherent current schema/identity, same strict cutoff and global STOP. No green synthetic test supplies these facts; if unavailable, **zero new requests**. Do not substitute a larger timeout or broaden schemas to obtain PASS. Strict B4 remains NO-GO; no alternative clock policy is activated.

For owner review send only the approved minimal evidence: exact checkout and runtime, policy/cutoff and independently supported clock reference, fixed attempted stages/count, bounded byte/timing/cleanup observations with honest limitations, verified identity subset, eligible source/registry references, per-symbol refusal/NOT_ATTEMPTED and overall HOLD. No keys, raw body/header/errors, excluded current values or unapproved capture files. Such receipts do not authenticate profitability or grant trade authority.

**STOP FOR OWNER AND BOSS AI REVIEW.**
