# BOSS-TRADER-LIVE-OBSERVATION-READINESS-017

Authorization: [Issue #28](https://github.com/tazmanked-bot/boss-trader-lab/issues/28).
Reviewed baseline: owner-merged PR #27, **`e3a65a5ea4cad8a1a9184c308acded41dc208b3a`**.
Scope: **Stage A readiness assessment, experiment design and offline tests only**.

**Recommendation: REVIEW this Stage A evidence; NO-GO for a live invocation under the strict-clock specification; HOLD for any revised historical-data-only specification. Operational Test Mode remains NOT APPROVED.** Neither policy is adopted. No network transport, clock provider, workflow, runtime integration or authorization is implemented by this change.

## 1. Evidence vocabulary and exact sources

VERIFIED OFFLINE means observed local code/test behavior on supplied synthetic inputs, not platform or market truth. VERIFIED DOCS means an explicit source statement or published configuration, not observed current service behavior. UNKNOWN means evidence has not been obtained. HOLD means a gate is not accepted. NO-GO means a necessary strict gate is presently unmet. A green unittest, fixture label, commit/hash or owner intent alone cannot turn any gate into GO.

All repository references below are pinned to the baseline above. This assessment read the actual source and reports through GitHub; it did not request Kraken documentation/services, DNS/TLS diagnostics, clock-service data or live market data. Vendor-document findings are inherited, explicitly qualified evidence from the prior source review, **not a fresh independent vendor-schema verification**.

| Ref | Exact source and anchors | What this review can establish |
| --- | --- | --- |
| R1 | [Correction 014](https://github.com/tazmanked-bot/boss-trader-lab/blob/e3a65a5ea4cad8a1a9184c308acded41dc208b3a/docs/BOSS-TRADER-KRAKEN-CORRECTION-014.md), sections 1, 3–7; [correction source](https://github.com/tazmanked-bot/boss-trader-lab/blob/e3a65a5ea4cad8a1a9184c308acded41dc208b3a/research/kraken_probe_corrections.py), `supervise_offline`, `GatedProcessJob`, `parse_http_fixture`, `coordinate_global_stop_offline` | Separate bounded-memory fixture parser, paused-worker mechanism and global-stop prototype. No live stream driver or stage integration. |
| R2 | [Diagnostic source](https://github.com/tazmanked-bot/boss-trader-lab/blob/e3a65a5ea4cad8a1a9184c308acded41dc208b3a/research/kraken_spot_diagnostic.py), lines 27–45, `Request.target`, `_exchange`, `_supervise`, `CaptureClock`, `_identity`, `_commitment`, `run_offline`, `main` | Disabled entrypoint; exact fixed request/identity assumptions; injected offline behavior. A `trusted=True` object is an input contract, not an attestation verifier. |
| R3 | [B4/B5 feasibility 015](https://github.com/tazmanked-bot/boss-trader-lab/blob/e3a65a5ea4cad8a1a9184c308acded41dc208b3a/docs/BOSS-TRADER-B4-B5-FEASIBILITY-015.md), clock sources, resource plan, delayed cutoff and limitations | Strict UTC evidence absent, synthetic uncertainty/timing examples, published runner image versus actual execution distinction. Default chronyc can fall back to IP; no time-status command is run here. |
| R4 | [Schema readiness 011](https://github.com/tazmanked-bot/boss-trader-lab/blob/e3a65a5ea4cad8a1a9184c308acded41dc208b3a/docs/BOSS-TRADER-KRAKEN-LIVE-READINESS-011.md), sections 1–4 | Prior vendor prose/example retrieval: [OHLC](https://docs.kraken.com/api-reference/market-data/get-ohlc-data), [AssetPairs](https://docs.kraken.com/api-reference/market-data/get-tradable-asset-pairs), [historical OHLCVT definitions](https://support.kraken.com/articles/360047124832-downloadable-historical-ohlcvt-open-high-low-close-volume-trades-data). Expanded child schema and current XRP/SOL aliases were unresolved. Those gaps remain. |
| R5 | [Registry](https://github.com/tazmanked-bot/boss-trader-lab/blob/e3a65a5ea4cad8a1a9184c308acded41dc208b3a/research/spot_refusal_registry.py), `validate_symbol`, `validate_symbols`, `validate_json`; [bridge](https://github.com/tazmanked-bot/boss-trader-lab/blob/e3a65a5ea4cad8a1a9184c308acded41dc208b3a/research/kraken_spot_validation_bridge.py), `PAIRS`, `validate_capture` | Exact normalized/REST-shaped fixture schemas, unchanged 21-bar, finite-value, per-symbol freshness and projection checks. No capture authenticity. |
| R6 | [Candidate source](https://github.com/tazmanked-bot/boss-trader-lab/blob/e3a65a5ea4cad8a1a9184c308acded41dc208b3a/research/spot_reversal_candidates.py), `_features`, `evaluate`, `evaluate_json`; [report 016](https://github.com/tazmanked-bot/boss-trader-lab/blob/e3a65a5ea4cad8a1a9184c308acded41dc208b3a/docs/BOSS-TRADER-SPOT-CANDIDATES-016.md) | Synthetic-only four-feature heuristic, terminal refusal, deterministic 0–3 WATCH candidates; no predictive validation or live adapter. |
| R7 | [Working observer](https://github.com/tazmanked-bot/boss-trader-lab/blob/e3a65a5ea4cad8a1a9184c308acded41dc208b3a/kraken_public_observer.py), `parse_closed_candles`, `fetch`; [scanner](https://github.com/tazmanked-bot/boss-trader-lab/blob/e3a65a5ea4cad8a1a9184c308acded41dc208b3a/boss_trader_lab.py), `observe`, `fetch_closed_closes` | Separate legacy observer/scanner contracts; neither is integrated into R5/R6. Close-only observer output is not a verified OHLCV chain. |

No Actions run is dispatched or newly verified here. Prior reports/owner merge statements are evidence lineage, not a current-head CI result. The local full suite supplies the executed evidence below.

## 2. Gate-by-gate evidence ledger

All rows apply conjunctively to a possible future live experiment. Partial data success must never override a failed safety gate. Smallest closing evidence means an input to a **future review**, not permission to collect it now.

| Gate | Evidence now | Classification / disposition | Smallest plausible closing evidence |
| --- | --- | --- | --- |
| B1: construction/start/action deadline gates | R1 checks expiry before factory/start/release; paused child checks before injected action; existing tests include fake blocked local workers. | VERIFIED OFFLINE mechanisms; **HOLD real-platform guarantee** | Exact future transport and target runtime review, cancellation/start/kill/reap failure tests, observed phase measurements and explicit treatment of scheduler/uninterruptible-start limitations. If required hard guarantee cannot be supported, remain NO-GO; do not silently reinterpret it as an observed maximum. |
| B1: real <=10s request including DNS/connect/read | Python factory/start and OS scheduling can stall; no active production worker/transport. Ten seconds is not merely socket timeout; separate 250ms reap allowance is not request time. | UNKNOWN real bound; **HOLD** | Independently supported enforcement at the required boundary on reviewed target, with known limitations. Offline repetitions alone cannot prove a universal bound. No timeout extension or retry as a workaround. |
| B2: bounded parser | R1 accepts MemoryReader bytes only: 8192 header bytes, 1024-byte line, 64 fields, 262144 body bytes, Content-Length-only narrow HTTP profile. | VERIFIED OFFLINE; **HOLD network preallocation/compatibility** | Reviewed bounded stream reader protecting before allocation/materialization, heap/resource measurements and adversarial offline stream tests on target. Actual server framing remains UNKNOWN; unsupported chunking/compression must refuse. |
| B3: global STOP | R1 `coordinate_global_stop_offline` stops first failed stage in BTC/XRP/SOL order; no later stage. R2 legacy `run_offline` can continue after some per-symbol failures and is **not** that integration. | VERIFIED OFFLINE corrected sequencing; **HOLD integrated executor** | Separate future reviewed integration with mutation-sensitive tests: 451, 429, alias/API/parser/TLS/clock/timeout/cleanup failure at every stage -> no later request. Do not activate legacy coordinator. |
| B4: independently attested initial UTC <=2s | R2 checks injected clocks; R3 has estimates/conditional models but no independent current job-bound authority/verifier. HTTP Date is after first request. | **NO-GO strict policy** | Owner-approved independent authority/verifier, quantified error through whole validity horizon, actual job/boot/monotonic-domain/revision binding and expiry/step/reboot controls. No available evidence satisfies this now. |
| B5: actual target runtime | Local CPython 3.12.14 tests; published runner labels/image inventory do not establish actual host/kernel, CA, cleanup, timing or clock. | VERIFIED OFFLINE locally; **UNKNOWN target / HOLD** | Owner-approved exact-head offline run on reviewed target, minimal nonsecret facts, bounded local worker observations and cleanup evidence; retain B1/B2/B4 limitations. No universal guarantees inferred. |
| Routing / endpoint / TLS | R2 fixes host/paths/TLS policy in injected tests; no actual route, TLS or server behavior observed. 451 cannot be bypassed. | VERIFIED OFFLINE configuration; **UNKNOWN real / HOLD** | Independently reviewed permitted route, fixed-host verified TLS and bounded transport in separate scope; any restriction is terminal. No proxy/VPN/mirror/source substitution. |
| Venue/pair identity | R2 exact assumptions; R4 BTC documentation example only; current XRP/SOL keys unresolved. | VERIFIED OFFLINE allowlists; VERIFIED DOCS (prior BTC example); **UNKNOWN current / HOLD** | Review authoritative expanded metadata first; if preflight safety gates permit later experiment, bounded AssetPairs response must agree with frozen specification before that symbol's OHLC. Unknown aliases refuse; never self-approve from a response. |
| Expanded OHLC schema / units | R4 describes eight-position example, final uncommitted row, minute interval parameter; R5 enforces a stricter decimal/row profile. | VERIFIED DOCS prior prose/example; **UNKNOWN expanded/current / HOLD** | Independently reviewed expanded schema and bounded authorized response against exact profile. Undocumented/extra fields refuse pending separate issue. No schema relaxation. |
| Historical eligibility / current candle | R5 closed `open+3600<=as_of`, full eligible history, >=21, no gaps/order repairs, latest close <=3h relative to cutoff. R2 outer commitment gate is separate. | VERIFIED OFFLINE; **HOLD live commitment/time provenance** | Explicit approved cutoff and immutable clock context, current-row structural/commitment consistency and unchanged bridge checks; no positional discard or cursor-as-closure assumption. |
| Signal/data provenance | R6 accepts SYNTHETIC_ONLY; R5 source_claim says provided fixture. No live-to-candidate converter or authenticity verifier. | VERIFIED OFFLINE; **HOLD live candidate path** | Future separately reviewed source-typed data contract, normalization evidence and chain tests. Never relabel market data SYNTHETIC_ONLY to pass the current scanner. |
| Operational isolation / safety | Disabled diagnostic/correction entrypoints return AUTHORIZATION_MISSING, requests=0; synthetic chain tests have guarded I/O. | VERIFIED OFFLINE defaults; **HOLD live integration** | Exact future revision without any automatic activation, no credentials/private endpoints/orders/alerts/schedules, enforced request/global-stop/redaction gates; independent review. |
| Owner authorization | #28 authorizes design/tests only, no requests or policy changes. | VERIFIED DOCS scope; **NO-GO live authorization** | Completed exact-commit one-shot decision record below, after required evidence/revised specification review. A draft, merge, green check or “live” flag is insufficient. |

B1/B2/B5 real enforcement may be infeasible on an ordinary hosted runner at the demanded assurance level. A delayed cutoff does not remove this problem. No path is guaranteed to become runnable; continuing offline-only research is a valid final owner choice.

## 3. Kraken identity and schema acceptance specification

Current diagnostic assumptions (R2), **not confirmed current instruments**:

| Research symbol | Request `pair` | Exact diagnostic result key | `base` | `wsname` |
| --- | --- | --- | --- | --- |
| BTC/USD | XBTUSD | XXBTZUSD | XXBT | XBT/USD |
| XRP/USD | XRPUSD | XXRPZUSD | XXRP | XRP/USD |
| SOL/USD | SOLUSD | SOLUSD | SOL | SOL/USD |

All require venue Kraken, spot USD, quote ZUSD internally, `aclass_base=currency`, `aclass_quote=currency`, exact altname and `status=online`. Currency asset class alone is not proof of spot identity; the fixed public spot endpoint, allowlisted instrument and coherent metadata must agree. Leverage metadata may exist on a spot instrument; it grants no leverage/futures/short permission.

R2 `_identity` requires exactly one approved result key, empty `error` list, all seven IDENTITY_FIELDS and only OPTIONAL_METADATA extras. It permits fields such as fees/leverage metadata but does not validate their entire child schemas. Expanded current vendor metadata is not independently established here. Any new/ambiguous key or unsupported extra means refusal, not automatic learning. R5 bridge allows BTC XXBTZUSD/XBTUSD, XRP XXRPZUSD/XRPUSD, SOL SOLUSD; this broader offline allowlist cannot supersede the stricter identity gate. AssetPairs and OHLC keys must agree with the approved identity, not merely one bridge alias. No display-name `assetVersion` mode is proposed.

REST-shaped OHLC envelope: exactly `error`/`result`, empty API error list, one approved pair key plus integer seconds cursor `last`. Rows are exactly `[time, open, high, low, close, vwap, volume, count]`: aligned supported integer UTC seconds; six strict decimal strings (including VWAP/volume); positive bounded prices/VWAP, nonnegative volume; integer count in [0, 2^53-1]; valid low/high bounds and unchanged bridge precision checks. Interval request is integer 60 minutes. Prices are quote USD; volume base asset according to the prior vendor definitions, not newly observed units. No symbol aliases, timezone conversion, milliseconds guessing or unit scaling.

Vendor OHLC prose describes up to 720 rows and an always-current uncommitted last entry; local limit remains **512**, without truncation to fit. Vendor historical CSV has a different format and can omit no-trade hours; it is not an interchangeable REST source. Gaps still refuse. `since` is not an assurance of exact count, completeness or body size; `last` is a cursor, not trusted current time, finality or interval proof.

At fixed cutoff, every eligible row is validated, not just the last 21. Structurally valid excluded future rows do not contribute OHLCV/count to candidate decisions/evidence. Invalid row headers, total size/row limits and strict JSON errors can still refuse. Source commitment checks additionally compare timestamps/current final row against the approved clock/service envelope. A purported uncommitted row eligible at the cutoff is a commitment conflict; no assumption of commitment from its position or elapsed-looking age.

## 4. Two policy alternatives — neither activated

| Aspect | A: retain strict-clock specification | B: proposed delayed historical-data-only specification |
| --- | --- | --- |
| Trust claim | Independently attested absolute UTC error <=2s before first request, valid through every request. | Explicitly labeled **estimated UTC**, finite conditional uncertainty U and additional lag L; no claim of independent strict UTC attestation or real-time freshness. |
| Cutoff | Existing two-second conservative guard: `floor((floor(W0_ns/1e9)-2)/3600)*3600`; freeze once. | Proposal: `floor((W_est_seconds-U_seconds)/3600)*3600-L_hours*3600`, rounded conservatively. Freeze once; no response-end/last-cursor adjustment. |
| Evidence | Approved independent source/verifier, calibration age/drift/skew/holdover, run/host/boot/revision binding, monotonic validity and step/reboot checks. | Owner-approved **revised trust model** with source assumptions, observed estimate, finite uncertainty derivation, sample/holdover/drift age, run binding and expiry. A chosen U or “synchronized” bool is not evidence of a bound. |
| Examples | Existing <=2s guard unchanged. | U=60s and L=1h are illustrative mathematical examples from R3, **not an assertion this runner meets 60s** or a selected operational policy. |
| Closure / freshness claim | Conservative cutoff under verified clock bound, plus source consistency/finality checks. | Historical eligibility conservative **only if the finite bound is valid**. Registry <=3h remains relative to delayed cutoff, never advertised as <=3h old now. No current entry/timeliness claim. |
| HTTP Date and source time | Coarse consistency only, never first-request authority. Existing wall/monotonic disagreement check <=1s and HTTP Date envelope ±2s remain strict-path requirements. | Must be re-specified coherently before implementation; cannot feed an estimated clock into strict CaptureClock as `trusted=True`, loosen ±2s inline, or disable a conflicting check. Source timestamps/Date do not independently prove UTC/publication. |
| B1/B2/B3/B5, TLS/routing | All required; no successful synthetic test closes real enforcement. | All unresolved real transport/routing requirements still apply. B does not waive deadlines, bounds, global stop or actual target review. |
| Candidate use | Existing SYNTHETIC_ONLY evaluator cannot accept live captures. | Same restriction. A future source-typed historical research adapter needs separate owner-approved issue; no relabeling real data as synthetic. |
| Present decision | **NO-GO**: B4 absent, other live gates also HOLD. | **HOLD**: revised specification, evidence and implementation unapproved; no activation. |

The delayed-cutoff proof is conditional: with true time T, estimate W and valid `|W-T|<=U`, `W-U<=T`, so flooring and subtracting nonnegative whole-hour lag cannot move cutoff past true time. This says nothing about publication/commitment authenticity. If W is one day fast and the asserted U is only 60s, the one-hour lag still produces a future cutoff; the new deterministic test demonstrates that counterexample. An unbounded/unknown error, leap/step conflict, unverified age or inconsistent clock means HOLD, not “choose a bigger lag.”

Neither alternative changes the existing registry, bridge, CaptureClock, freshness thresholds, feature formulas or safety limits. The already safe fallback is supplied synthetic or declared-as_of historical replay offline, honestly labeled; no market collection is authorized by that fallback.

## 5. Bounded future experiment design — NOT executable or authorized

This is a conditional plan for a **separate future implementation/approval**, not a command or workflow. It is not possible to perform this experiment with the current production modules simply by passing a flag. If preflight gates cannot be met, there are zero requests and no invocation.

### Before any possible first request

Review a future immutable commit implementing the separately approved specification, including an actual bounded provider, integrated B1/B2/B3 controls, source-typed data boundary and default disabled authorization gate. Review exact target runtime facts, permissible direct egress, CA/TLS policy, clock evidence for selected path and offline fault tests. Authorize only one manual invocation within a stated expiry; invalid/absent/expired gate records mean AUTHORIZATION_MISSING and zero requests. No workflow/transport is created by this PR.

### Fixed request schedule and global STOP

One worker at a time, fixed order **BTC/USD then XRP/USD then SOL/USD**. Per symbol:

1. At most one GET `https://api.kraken.com:443/0/public/AssetPairs` with only `pair=<fixed pair>`, `aclass_base=currency`, `info=info`.
2. Only after exact identity validation passes, at most one GET `https://api.kraken.com:443/0/public/OHLC` with only `pair=<fixed pair>`, `interval=60`, `since=<frozen as_of-86400>`.

Omit assetVersion/asset_class and unsupported count parameters. Fixed query values are derived from the approved manifest, not arbitrary dispatch input or returned URLs. No POST, auth header, keys, private endpoint, order/fill/account data, venue fallback, retry, pagination, redirect, alternate host/port, VPN/proxy, mirror, paid service or source substitution. **At most six GET attempts total**; reserve/count an attempt before it could send, and never refund a failed attempt. Identity failure prevents its OHLC. Any failure at either stage globally stops all subsequent symbols/stages; remaining entries are NOT_ATTEMPTED, not WAIT or successful observations. A 451, 429, route prohibition, TLS error, timeout, parser/identity/schema/clock error or failed cleanup is terminal. No test call to discover if a blocked route can be bypassed.

Partial already-collected BTC evidence may be retained as partial, but overall result remains HOLD/REFUSED and cannot rescue XRP/SOL or turn into an actionable candidate. Per-symbol independence describes evidence/refusal semantics; global STOP limits future collection, not retroactive erasure of earlier evidence.

### Resource and measurement contract

Retain each existing **10-second absolute monotonic request deadline**, including construction/start, DNS/connect/TLS/header/body and validation before accepting success; equality expires. Child paused until checked release; cancellation before kill; failed reap refuses. Existing separate **250ms cleanup allowance** is not extra request time or authority to send after expiry. No claim Python/kernel can absolutely enforce these bounds on an unreviewed runner.

Retain corrected parser profile: 8192 total raw header bytes, 1024-byte line, 64 fields, Content-Length-only JSON UTF-8, <=262144 body bytes, <=4096 body-read chunks, strict duplicate/nonfinite/overflow handling; reject redirects, interim responses, chunking/trailers, ambiguous framing and compression. Current prototype only parses caller-owned MemoryReader bytes; a future real bounded stream/allocator must be separately implemented/reviewed. Unsupported legitimate server behavior is refusal, not a reason to widen limits here.

Six accepted bodies imply at most **1572864 bytes (1.5 MiB)** of response body budget, plus at most **49152 header bytes**. These are protocol-input limits, **not a Python heap/RSS bound**: JSON object overhead, TLS/native buffering and process startup need measured resource evidence on target before authorization. No concurrent fan-out. Since six request budgets sum to 60s and six cleanup allowances to 1.5s, neither **60s nor 61.5s is a proven invocation wall-time bound**; native startup/descheduling can exceed arithmetic sums. Owner must require an evidenced outer job/process cap and decide whether the hard constraints are feasible. A larger job timeout cannot be used to claim the unchanged 10s contract is satisfied.

For a later authorized run measure only reviewed allowlisted facts: actual checkout, OS/kernel/machine, Python/OpenSSL version, approved CA-bundle identity/hash (no contents), start/kill/reap observed intervals, per-stage monotonic elapsed, bounded byte counts, fixed status/refusal and whether the next stage was prevented. Do not collect them here. Record unmeasured values as UNMEASURED, observed maxima as observed only, no guaranteed scheduler latency. Clock provenance is separate from clock consistency; do not query status services without its own reviewed approval and no-fallback design.

## 6. Minimal redacted result design

Proposed version `spot-observation-evidence-design-v1`, **design only**, not a runtime fixture accepted as authorization. At most 16 KiB/run and 4 KiB/symbol (run must also meet aggregate limit). Retention proposal: owner-controlled bounded summary retained at most seven days unless owner explicitly selects a shorter duration; no raw response artifacts or external telemetry. Retention is an approval field, not activated by this report.

Allowlist:

- exact reviewed/observed commit and test/implementation versions; nonsecret run identifier; selected owner-approved policy version; owner decision reference and expiry status;
- fixed host/port/path, fixed pair/interval/since, attempt ordinal and total <=6; stage outcome including NOT_ATTEMPTED; fixed refusal code plus coarse HTTP status where available;
- exact allowlisted instrument identity values or explicit UNVERIFIED; bridge/registry decision references only after complete validation;
- frozen as_of and coordinate meaning (historical versus strict), estimated/attested clock classification, authority/model reference, units, U/L if approved, validity/holdover binding and fixed clock refusal category;
- bounded start/end/elapsed context as permitted by policy, byte-limit pass/failure and measured worker cleanup outcomes; no assumed null-to-zero conversion;
- overall HOLD/REFUSED or DATA_CHECKS_PASSED_REVIEW_ONLY; **never operational GO inferred from data success**.

Strictly no raw body/header/error strings, source addresses, certificate contents, account identifiers, environment dump, secrets, raw-response hash, excluded future values/counts, price targets, BUY/ENTRY READY output or P&L. Eligible source/normalized evidence hashes can bind exact fixture/capture fields but do not authenticate origin. A canonical summary digest detects byte changes, not a trusted ledger/signature. Immutable separate clock/run context means actual capture receipts can differ between invocations; full future-row invariance is asserted for fixed-context eligible bridge/candidate evidence, not fabricated equality of independently timed real runs.

## 7. Smallest offline integration proof and its limits

New file: `tests/test_live_observation_readiness_017.py` only; no executable research source. It reads the existing explicitly synthetic fixture from PR #27, constructs invented Kraken-shaped rows with strict metadata/decimal strings, and uses existing production modules unchanged:

1. Existing bridge validates each invented capture into its registry decision.
2. Standalone registry checks the supplied normalized representation. For a validated bridge result, **complete canonical registry-decision equality** with this normalized representation is required, including evidence hash. A test deliberately changes a valid source volume in only one representation; the proof fails instead of quietly pairing different data.
3. A test-only gate removes eligibility for bridge-refused symbols before invoking the existing synthetic candidate evaluator. Its normal missing-data refusal produces BLOCKED; the original bridge code/registry cause remains in a separate complete bridge record. No claim is made that DATA_UNAVAILABLE in the candidate row alone preserves the full bridge cause.
4. Candidate's revalidated per-symbol registry decisions must equal the same normalized registry decisions for successful symbols. It does not accept a caller's “validated” bool. Tests cover 0/1/2/3 candidates, independent stale XRP and invalid SOL count with BTC retained, malformed eligible prices/schema/aliases, exact closing boundary and 20-bar warmup failure.
5. Complete canonical composite output (`kind`, all bridge records/evidence and candidate output) is unchanged after structurally valid future rows are appended at fixed as_of for WATCH, WAIT and BLOCKED base states. The existing exceptions—malformed headers/JSON, row/byte limits, strict reject policy—remain documented and unchanged. No sorting/filling or relaxation.

This helper is **trusted test orchestration**, not a production normalizer, generic capture exporter, sandbox, independent market-data source, live coordinator or approved live-to-candidate integration. Both representations are built from the same known synthetic input to prove plumbing/contract consistency, not independent numerical market verification. Float normalization is explicit so `130` versus `130.0` JSON representations cannot masquerade as exact hash equality. No fixture is relabeled as actual market data. There is still no end-to-end live pipeline; future adapter work needs a distinct owner-reviewed issue.

## 8. Infrastructure versus scientific/paper evaluation acceptance

Infrastructure acceptance would require every selected-policy gate above, exact head/target evidence, identity/schema reconciliation, fail-closed streaming/worker/global-stop integration and explicit one-shot owner approval. A successful authorized DATA_CHECKS_PASSED result would establish only bounded observed data consistency, with unknowns preserved. It does not validate candidate usefulness.

Scientific evaluation is a separate future research stage, also **not authorized for implementation here**:

- Freeze and preregister feature definitions/parameters, eligible universe, decision frequency, data cutoff and missing-data handling before examining held-out outcomes. Four current features and equal-weight shape score are unvalidated hypotheses; strengths are not confidence percentages.
- Use independently sourced/provenanced historical spot USD data under separately approved acquisition and licensing, with chronology, quality exclusions and selection/delisting/missing-history bias disclosed. Do not infer Kraken/USD behavior from a different venue or USDT.
- Separate development/calibration and out-of-sample time windows; use causal walk-forward/as_of evaluation, no future-feature/normalization leakage and no retrospective best-universe selection. Track all tested variants and multiple-selection bias. Synthetic green tests cannot substitute for held-out evidence.
- Before any hypothetical execution metric, define an honest simulated fill model including fees, spread, slippage, latency, volume/liquidity constraints, failed/missing fills and uncertainty. Define horizons, baselines, sample-size/coverage and failure criteria in advance; report negative results. No arbitrary fixture-derived entry price or guaranteed return.
- Keep 0–3 as a maximum, never forced exposure. Separate data refusal, WAIT/WATCH patterns, infrastructure failures and any later simulated position logic. No portfolio, win-rate or P&L capability is added now.
- Paper evaluation, if later authorized, remains simulation-only without exchange keys, private endpoints, order authority or automatic transition to trading. Owner/BOSS AI approval is independent of infrastructure approval; no profit promise or live order follows.

## 9. Owner decision record template — default NO-GO

One record must enumerate **each gate** B1, B2, B3, B4/selected clock specification, B5, identity/schema, route/TLS, provenance, redaction/retention, and authorization. A general “approved” checkbox does not fill missing gate evidence. This template is documentary and grants nothing:

```text
record_version: owner-spot-observation-decision-v1
scope: [offline evidence review | revised-spec design | future one-shot data-only observation]
future_exact_40_hex_commit: UNSET
reviewed_diff_and_implementation_reference: UNSET
gate_rows:
  - gate: <one gate name; repeat for every gate>
    evidence_exact_commit_source_or_run: UNSET
    known_limitations_and_residual_risk: UNSET
    decision: NO-GO
    approver_and_review_reference: UNSET
clock_path_and_exact_spec_version: UNSET  # A or separately approved revised B
clock_evidence_authority_model_U_L_validity_boot_job_binding: UNSET
target_OS_kernel_image_Python_OpenSSL_CA_and_runner_evidence: UNSET
deadline_parser_worker_cleanup_outer_cap_evidence: UNSET
fixed_host_port: api.kraken.com:443
fixed_endpoints: /0/public/AssetPairs; /0/public/OHLC
fixed_pairs_and_queries: <review exact BTC/XRP/SOL manifest from section 5>
request_ceiling: 6 GET attempts; sequential; STOP first failure; no retries/redirects/fallback
data_scope: spot USD hourly historical/data checks only; no orders or synthetic relabeling
redaction_summary_bounds_and_retention: UNSET
single_manual_invocation_id_and_nonsecret_replay_control: UNSET
not_before_and_expiry_under_approved_trust_model: UNSET
owner_and_BOSS_AI_review_references: UNSET
overall_explicit_decision: NO-GO
```

The approval's expiry cannot be validated using the same untrusted wall clock without an approved trust model. A future enforcement mechanism must bind exact commit, job/boot, invocation and monotonic validity horizon and prevent reuse; no such mechanism is supplied by this template. Missing/unverifiable/expired authorization -> AUTHORIZATION_MISSING, zero requests. A clock failure also refuses even with nominal owner consent. Neither this issue nor a later offline merge supplies live permission.

## 10. Exact offline execution evidence and handoff

Local CPython **3.12.14**, no package installations, from the staged baseline plus the new test file:

```text
python -B -m unittest discover -s tests -p test_live_observation_readiness_017.py -v
Ran 9 tests in 0.065s
OK

python -B -m unittest discover -s tests -v
Ran 225 tests in 2.953s
OK
```

**216 unchanged baseline tests + 9 new tests = 225, no skips.** New tests guard socket construction/connection/DNS, urlopen, HTTPSConnection, subprocess.run/Popen and time.time, and assert zero calls. The default-entrypoint test invokes both disabled `main()` functions in-process with captured stdout: exit 2, AUTHORIZATION_MISSING, requests=0, overall HOLD. It does not pass a live flag or construct any connection. Existing suite retains its offline mocked transports and local fake-worker lifecycle tests. Local unittest elapsed times are not target-runner deadline evidence. Python 3.11, current-head Actions execution, actual transport framing, current aliases, target runtime behavior and trusted UTC remain UNVERIFIED.

Nine new methods provide exact evidence: `test_bridge_registry_candidate_exact_canonical_decision_chain`, `test_chain_zero_through_three_never_requires_candidate`, `test_independent_stale_and_bad_source_refusals_preserve_cause`, `test_complete_chain_evidence_future_projection_equality`, `test_closed_boundary_warmup_and_strict_future_refusal`, `test_schema_and_eligible_corruption_cannot_be_overridden`, `test_valid_but_different_representation_fails_test_proof`, `test_disabled_entrypoints_remain_authorization_missing_zero_requests`, `test_delayed_cutoff_is_conditional_on_finite_valid_error_bound`.

Changed paths: this report and `tests/test_live_observation_readiness_017.py`, both new. All existing runtime code, tests/fixtures, observer/scanner, workflows and dependencies remain byte-for-byte inherited from the baseline. The exact new head is reported in the draft PR/final handoff; a commit cannot self-embed its own hash.

**Smallest safe owner decision:** accept or reject this Stage A assessment and authorize only an exact-head **offline** Actions verification of these tests/full suite on the intended runtime. Separately decide whether to retain strict NO-GO or commission a revised delayed-data-only specification in a new issue. Neither choice authorizes any real request now. Do not request a live GO while required evidence remains missing; continuing synthetic research is safe and permissible.

No main update, merge, issue closure, live request, time-service query, workflow creation/dispatch, policy change, trading, scheduled monitoring, paid service, credentials, VM migration or ZUMERAVO access. **STOP FOR OWNER AND BOSS AI REVIEW. Live diagnostics and Operational Test Mode remain HOLD.**
