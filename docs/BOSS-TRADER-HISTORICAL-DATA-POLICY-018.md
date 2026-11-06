# BOSS-TRADER-HISTORICAL-DATA-POLICY-018

Specification ID: **historical-observation-policy-proposal-v1**.
Status: **PROPOSED / HOLD — NOT ADOPTED, NOT IMPLEMENTED**.
Authority: [Issue #30](https://github.com/tazmanked-bot/boss-trader-lab/issues/30), design and offline tests only.
Exact reviewed main: **`f4cff99bbec4d94909f8ef8ba3367833b903ad6d`**, owner merge of PR #29.

**Verdict:** a delayed cutoff is mathematically defensible for conditional historical eligibility **if** a defensible finite error bound genuinely holds. No available evidence establishes that bound for an actual intended host, and no cutoff proof establishes safe transport. Retain strict-path B4 **NO-GO** and alternative-policy **HOLD**. Recommend declared-as_of offline replay now, not a Kraken observation. No policy parameter is approved here.

This specification adds only this document and `tests/test_historical_data_policy_018.py`. It changes no runtime code, schema, registry, bridge, candidate evaluator, workflow, dependency, safety limit or main ref. All clock/network collection, live activation, dispatch, merge, trading, secrets, orders, futures, scheduling, paid services, VM deployment and ZUMERAVO access remain outside scope. GitHub connector issue/source reads and research-branch/draft-PR publication are repository work, not provider/network diagnostics.

## 1. Source of truth and evidence matrix

Both mandated merged reports were read from the exact baseline, especially readiness §§2–6 and feasibility's clock model/delayed proposal. Their conclusions are preserved, not overwritten by this proposal. No new vendor-current identity/schema, clock, runner, route or market measurement was obtained.

| Evidence / exact baseline source | Supported classification | Not established |
| --- | --- | --- |
| [Readiness 017 §§2–6](https://github.com/tazmanked-bot/boss-trader-lab/blob/f4cff99bbec4d94909f8ef8ba3367833b903ad6d/docs/BOSS-TRADER-LIVE-OBSERVATION-READINESS-017.md) | VERIFIED DOCS: B1–B5 ledger, proposed requests, identity assumptions, existing safeguards and distinct policy paths | Implemented end-to-end live pipeline, authorized invocation or current server behavior |
| [Feasibility 015 §§2–5](https://github.com/tazmanked-bot/boss-trader-lab/blob/f4cff99bbec4d94909f8ef8ba3367833b903ad6d/docs/BOSS-TRADER-B4-B5-FEASIBILITY-015.md) | VERIFIED DOCS / OFFLINE: conditional uncertainty model, clock source semantics, synthetic timing/estimates, replay alternative | Independent UTC attestation, actual daemon setup, hard runner/OS bounds |
| [Registry](https://github.com/tazmanked-bot/boss-trader-lab/blob/f4cff99bbec4d94909f8ef8ba3367833b903ad6d/research/spot_refusal_registry.py), `validate_symbol`, `validate_json`; [bridge](https://github.com/tazmanked-bot/boss-trader-lab/blob/f4cff99bbec4d94909f8ef8ba3367833b903ad6d/research/kraken_spot_validation_bridge.py), `validate_capture` | VERIFIED OFFLINE: exact identity/schema, 21 bars, full eligible history, 3h relative staleness, 512-row and precision/projection constraints | Exchange publication/finality/authenticity or current XRP/SOL aliases |
| [Diagnostic](https://github.com/tazmanked-bot/boss-trader-lab/blob/f4cff99bbec4d94909f8ef8ba3367833b903ad6d/research/kraken_spot_diagnostic.py), `CaptureClock`, `_identity`, `_commitment`, `main`; [corrections](https://github.com/tazmanked-bot/boss-trader-lab/blob/f4cff99bbec4d94909f8ef8ba3367833b903ad6d/research/kraken_probe_corrections.py), `supervise_offline`, `parse_http_fixture`, `coordinate_global_stop_offline` | VERIFIED OFFLINE: injected-clock checks, memory parser and isolated global-stop/worker mechanisms; disabled defaults | Real stream preallocation, true UTC, actual integrated global STOP or universal startup/kill bounds |
| [Candidate source](https://github.com/tazmanked-bot/boss-trader-lab/blob/f4cff99bbec4d94909f8ef8ba3367833b903ad6d/research/spot_reversal_candidates.py); [016 report](https://github.com/tazmanked-bot/boss-trader-lab/blob/f4cff99bbec4d94909f8ef8ba3367833b903ad6d/docs/BOSS-TRADER-SPOT-CANDIDATES-016.md) | VERIFIED OFFLINE: SYNTHETIC_ONLY, causal deterministic 0–3 WATCH research candidates with terminal refusal | Market-data adapter, current WATCH eligibility, useful trading strategy or profitability |
| New test-only arithmetic/adversarial model | VERIFIED OFFLINE: exact conditional inequalities and specified failure sensitivity; complete modeled evidence still yields HOLD | Evidence that any supplied local claim is true, production verifier or policy switch |
| Current host clock/collector, target runner, transport/TLS/route, expanded schema and XRP/SOL instrument inventory | UNKNOWN / HOLD | Nothing in a fixture or green test closes these gaps |

015 pins the underlying chrony/systemd documentation: chrony `c97d8083cf9a9edc64d53236565916d326d8a109/doc/chronyc.adoc` and systemd `7c6c0851f1dad9d61b823b2ee1a37cf494a0385d/man/` references. These are inherited documented semantics, not installed-version checks. 017 carries prior Kraken documentation examples/limitations; this task did not refresh them or infer expanded schema from examples.

## 2. Definitions and exact cutoff contract

This is normative language **for the proposed future specification only**, not authority to change existing code.

- `T0`: unknown true UTC capture instant, used only to state the hypothesis/proof. A test oracle may provide T0; a real local collector cannot simply observe it.
- `W_est`: estimated local UTC at a bracketed capture instant **before the first possible request**, represented as integer Unix epoch nanoseconds. Unix UTC/POSIX scale and leap/step handling must be documented. Unsupported scale, unknown unit, smeared/leap-conflicted interpretation or ambiguous conversion refuses.
- `U`: finite nonnegative upper absolute error bound at capture, conservatively covering sampling/representation and the owner-reviewed run validity horizon under a documented source/host model. Required hypothesis: **`|W_est - T0| <= U`**. A daemon point estimate, selected constant, statistical confidence interval or “synchronized” flag is not automatically such a bound.
- `L`: additional whole-hour lag, an explicitly reviewed nonnegative integer. Zero is mathematically meaningful but adds no extra lag; recommend considering a positive lag for historical-only scope. Neither zero, one nor any other value is selected here. A lag cannot replace U.
- `h=3600s`: hourly candle duration. `as_of` is an aligned UTC-seconds research cutoff, not a claim of current time, exchange publication time or entry readiness.

Exact proposed formula:

```text
as_of_seconds = floor((W_est_seconds - U_seconds)/3600)*3600 - L*3600

Integer-nanosecond implementation-equivalent mathematics:
as_of_seconds = ((W_est_ns - U_ns) // (3600*10^9) - L)*3600
```

Do not independently round W up, round U down, use floating nearest-hour rounding, truncate a signed result toward zero or subtract L in the wrong unit. Represent uncertain conversions rationally; round W conservatively downward if unavoidable, U upward to whole nanoseconds, and perform floor division. If numerical/domain bounds are exceeded, refuse. The unchanged registry supports aligned epoch seconds from 2000 through 2099; a cutoff/since outside supported range refuses rather than clamps.

Freeze the same cutoff, W/U/L, source/model versions, approved parameter caps and independently checked run/boot/monotonic-domain binding **once** before the first request. Later wall readings, cursor, newest symbol, response-end time, missing warmup or a better-looking result must never advance it. If evidence expires, uncertainty outgrows the approved U, a bound is corrected, or the clock steps/reverses, abort the invocation; do not silently recompute or widen the bound/lag to rescue it. A new separately authorized invocation is separate evidence.

**Unselected decisions:** 60s U and 1h L remain illustrative only. Owner must explicitly review U derivation plus maximum acceptable U, actual L, maximum acceptable historical age, sample-age/holdover/lease limits and collection model. No production maximum or native source-unit mapping is inferred from test constants. The test model's 1s sample-age threshold, 24h lag-domain cap, 60s illustrative U and short synthetic lease exist only to exercise failures, not to select operating settings.

## 3. Conditional proof, boundary examples and staleness

If `|W_est-T0|<=U`, then `W_est-U<=T0`. Flooring cannot increase that lower time bound, so:

```text
as_of + L*h <= T0
L*h <= T0-as_of < 2*U + (L+1)*h
```

An eligible candle with `open+h <= as_of` is therefore not later than T0 under the clock hypothesis. This is a **timestamp eligibility** statement, not proof that the provider had published/committed that candle at T0, that timestamps are honest, or that values will never be revised.

Illustrative exact-hour cases, with H an aligned true UTC hour, assumed U=60s and L=1h:

| Estimated W | Proposed cutoff | Meaning |
| --- | --- | --- |
| H+U | H-1h | Fast-bound endpoint remains at least the lag behind H |
| H+U-1ns | H-2h | One nanosecond below boundary excludes another hour |
| H-U | H-2h | Slow-bound endpoint is conservative, less available |
| H+1 day when true T0=H but asserted U=60s | Cutoff later than H | Hypothesis is false; lag fails to prevent false eligibility |

The last example can be internally self-consistent with a local daemon/status record. Without independent evidence, a verifier cannot discover the missing true-error oracle from local assertions alone. This is why even a complete synthetic record yields HOLD and why an underreported model bound can be detected arithmetically while an underreported **actual** error may remain undetected. Unknown/unbounded/untrusted error is NO-GO, never a reason to select a large arbitrary lag.

For the latest eligible close S, unchanged registry acceptance is `0 <= as_of-S <= 3h`. This is **freshness relative to the delayed coordinate**, not wall/current freshness. Under the valid capture hypothesis:

```text
L*h <= T0-S < 2*U + (L+4)*h
```

For illustrative U=60s/L=1h, this allows a latest close almost **5h+2min old at capture**, despite passing the 3h registry rule. Report that honestly. At response completion the true age may be greater by the actual elapsed duration E, provided E itself has a justified relation to true time; add E to the age envelope rather than advancing cutoff. A monotonic elapsed value alone is not independent absolute UTC or a universal OS timing guarantee.

Larger U/L deliberately reduce timeliness, may remove needed history and may make `since=as_of-24h` too old for the provider's bounded response. There is no promised availability. Require an explicit owner-approved maximum age budget; if no finite age envelope fits it, refuse. Never weaken 21-bar, gap, row-size or stale checks to compensate. No current/real-time WATCH, ENTRY READY, BUY, target, alert or trading-safety claim is permitted.

## 4. Minimum clock evidence and fail-closed lifecycle

A future estimate record must identify source/interface version, exact units/time scale, the meaning of every numeric component, calibration/source trust assumptions, capture bracket, status sample age, last genuine synchronization age, synchronization/holdover state, leap/step status and quantified error growth. Expected revision/run/host/boot/monotonic-domain binding must come from a separately checked context, not only strings in the record being checked. Hashes identify bytes, not truthful provenance or independent attestation.

Necessary future acceptance evidence, all currently UNVERIFIED:

1. Reviewed source/host threat model and provenance, including why finite U is defensible for the limited historical claim. Missing/untrusted source, unsigned self-assertion without reviewed environmental evidence, unknown daemon semantics or unsupported units -> NO-GO. Ordinary host estimates are explicitly conditional; policy B does not satisfy strict B4.
2. Active and synchronized state affirmatively evidenced, leap normal, no step/smear conflict, no boot/domain change. Missing/false/malformed status refuses. Freshly reading a status snapshot does not make its last source synchronization fresh.
3. Independently justified monotonic last-sync age, sample-age bracket and holdover. A wall Ref time/file mtime alone is circular evidence. `holdover_at_capture` must agree with the capture-minus-last-sync age in the same justified domain; contradictions refuse. No invention of daemon fields absent from its actual interface.
4. An approved finite upper bound through a monotonic validity horizon covering every planned request/acceptance, including drift/holdover growth and sampling skew. Lease expiry at equality is expired; a horizon reaching the expiry is not acceptable. A future collector must establish a positive supported monotonic rate/domain model and bounded acquisition; reset/rollback, negative elapsed, inconsistent anchor progression or expired evidence aborts.
5. Preserve initial and previous wall/monotonic comparisons; retain the existing relative <=1s disagreement safeguard unless a separate future specification review explicitly changes it. That relative check cannot establish initial UTC truth. No in-place `trusted=True` injection into existing CaptureClock is permitted.
6. Minimal redacted evidence with owner-approved retention; no server addresses, IDs/keys/cookies, raw daemon output, machine identifiers or environment dumps. No authorization can be established solely by a self-dated unverified wall clock; validity/replay binding needs its own justified mechanism.

015's illustrative conditional model was:

```text
|system offset| + root delay/2 + root dispersion + sampling margin
  + drift_ppb * justified elapsed/holdover nanoseconds / 10^9
```

Chrony System time is not Last offset/RMS offset; a configured systemd RootDistanceMaxUSec is not observed uncertainty. Chrony's documented bound is conditional on correct reference time. Native dispersion may already incorporate age: a future version-specific derivation must avoid missing growth or claiming independence from correlated/double-counted terms. A conservative extra margin cannot repair an invalid source assumption. U must be rounded upward and not be smaller than any justified modeled contribution, but passing that arithmetic is not authentication.

The test-only profile calculates horizon growth over `horizon_end-last_sync` with offset/delay/dispersion/sampling and ceiling. It assumes metadata correctness, admits no real records and always returns HOLD even when all checks pass. It is neither a proposed chrony parser nor an acceptable evidence authority.

### Later no-network collector feasibility review — no query now

First review an actual installed-version interface, source and environment offline. Prefer a separately approved pre-exported local snapshot if freshness/binding can be established; otherwise HOLD. Any future collector requires explicit approval, read-only bounded local IPC/file access, no external lookups, no privilege change/config mutation, no service start/activation and no IP fallback. Default chronyc can fall back from Unix socket to IPv4/IPv6 and resolve names: it must not be invoked. An explicit Unix-only path/numeric mode is only a candidate after its real behavior is audited. Local systemd D-Bus queries can activate services; their safety is not assumed. Do not enable sync, trigger online/burst/reselection or start a daemon to obtain a PASS.

An existing daemon or hosted runner may independently network in the background. “Collector makes no network call” does not prove whole-host no-egress; if the latter is required and cannot be established, remain HOLD. No actual status command, collector, synchronization or time-service query is executed or added here.

## 5. Candle, response and no-lookahead rules preserved

Only Kraken BTC/USD, XRP/USD, SOL/USD **spot USD hourly** observations are in the proposed future scope. Exact current XRP/SOL AssetPairs identities and expanded REST child schema remain UNKNOWN. No alias guesses/automatic allowlist growth. Retain the exact identity-first requirements in readiness 017 §3 and the stricter agreement between AssetPairs and OHLC; bridge alias acceptance alone is insufficient.

For each symbol, unchanged bridge/registry rules require exact metadata, eight-field REST-shaped rows, integer aligned supported UTC seconds, strict decimal/precision and price/VWAP/count checks, finite positive prices, nonnegative volume, full eligible-history ordering/duplicates/gaps and **21+** closed contiguous hourly bars. All eligible history is checked, not just the latest window. Missing/partial/malformed/stale data refuses terminally; no score or another symbol can rescue it. No sorting, filling, clipping/truncation, fabricated price, positional last-row deletion, repeated request or shifting as_of.

Total rows remain <=512 including excluded future rows, although prior vendor prose described up to 720. Body/JSON limits remain unchanged; `since` does not guarantee count/completeness or bounded actual framing. A legitimate no-trade gap still refuses. Unsupported current server representation/extra fields needs a distinct issue, not runtime relaxation.

Kraken's always-uncommitted final row is a documented provider assertion carried from the earlier schema review, not newly measured behavior. Delaying cutoff normally excludes current data but does not authenticate publication/finality. Retain an outer current-row/commitment check: if a purported uncommitted final row would be eligible at frozen cutoff, or timestamps conflict with approved capture/service intervals, refuse. Do not use cursor `last`, last position, elapsed-looking age or HTTP Date to declare it committed.

HTTP Date is coarse, source-controlled and received after first request; it cannot authorize that request or authenticate absolute UTC. For a future B specification, require independently reviewed service-uncertainty semantics before implementing an interval check: e.g. overlap of the local estimated start/end uncertainty envelope with a **justified** service-Date uncertainty interval is at most a consistency check. No numerical service bound is selected here. Unavailable bound, missing Date, conflicting interval, old cached/commitment ambiguity or unknown freshness semantics -> HOLD. **Do not simply widen the existing ±2s check to U, discard it, or call strict CaptureClock with an estimated clock.** Coherent service/current-row semantics are an explicit unresolved acceptance item.

Projection invariance holds at fixed cutoff/context under the existing contract: structurally valid future rows are excluded before their OHLCV/count affects eligible evidence. Appended prices must not change same-as_of calculations. Every row still needs exact shape and valid timestamp; total row/byte caps, malformed JSON/nonfinite serialization and strict reject-mode refusals can change output to refusal. Real request receipts vary across captures and are not falsely asserted equal. Preserve separate clock/capture evidence versus causal eligible-data evidence.

## 6. Option A/B comparison and defensibility decision

| Dimension | A: retain independent <=2s UTC | B: conditional delayed historical only |
| --- | --- | --- |
| Absolute time claim | Requires independent current authenticated/job-bound UTC evidence, not merely daemon synchronization | Finite reviewed environmental estimate with explicit assumptions/residual risk; cannot claim true UTC without valid evidence |
| Cutoff/timeliness | Existing 2s guard, potentially one extra excluded hour near boundary | Explicit U and L; greater unavoidable age and history shortages; no timely signals |
| Epistemic guarantee | Stronger specified initial-time assurance, currently unsupported | Conditional timestamp eligibility, not publication/finality/authenticity; hidden actual bound failures remain possible |
| Availability | Presently NO-GO; no verified authority supplied | Could be more feasible if reviewed local evidence exists, but expected availability is UNKNOWN; cannot promise higher uptime |
| Tests | Authority/verifier/binding/expiry/relative checks plus all transport/data gates | Additional U derivation/rounding, age/holdover/lease, interval consistency, staleness and provenance cases; not simpler merely because lag is added |
| Maintenance | Authority lifecycle and target/runtime review | Version-specific daemon semantics, uncertainty/age models, revised source-typed adapter and labels, continued target/runtime review |
| B1/B2/B3/B5 and route/TLS | All mandatory, unresolved | Same; mathematical cutoff does not permit any GET or remove hard-limit feasibility questions |
| Scientific outcome | No profitability or strategy evidence | Same; historical validation success is not WATCH, signals, return, portfolio or order authority |
| Owner decision now | Retain **strict NO-GO** | **PROPOSED/HOLD**; actual U/L/caps/service rules and evidence UNSET |

B is scientifically defensible as a clearly conditional coordinate model; it is **not operationally defensible for actual collection on present evidence**. Better access to local status on an owner-controlled machine would not itself supply independent truth or universal kernel guarantees, and no VM is proposed. Prefer narrower offline replay while these gaps remain.

## 7. Unresolved transport and approval gates — unchanged

| Gate | Present status | Required future closing evidence, not collected now |
| --- | --- | --- |
| B1 real construction/start/DNS/connect/read and cleanup | HOLD | Actual reviewed provider/target enforcement of existing 10s request deadline and separate 250ms reap allowance. Native startup, scheduling and kernel kill/reap may prevent a hard guarantee; observed maxima alone are insufficient. |
| B2 actual allocation/headers/stream | HOLD | Real bounded stream driver reviewed before unbounded allocation; unchanged 8192 header bytes, 1024-byte lines, 64 fields, 262144 body bytes/4096 read chunks, narrow Content-Length JSON profile. MemoryReader success is not socket proof. Unsupported chunked/compressed/trailer/framing cases refuse. |
| B3 global STOP integration | HOLD | Corrected isolated controller integrated/reviewed separately; first failure stops all later stages, no legacy per-symbol continuation. Mutation-sensitive offline tests first. |
| B4 strict attestation | NO-GO | Independent verified <=2s authority/horizon/domain binding unavailable. B would be a different reviewed specification, not evidence that B4 passed. |
| B5 target host/runtime | UNKNOWN/HOLD | Exact future head and Python/OS/kernel/OpenSSL/approved CA facts, offline worker/resource evidence with honest measured-only limits. Current local test timing is not target attestation. |
| Route/TLS/provider behavior | UNKNOWN/HOLD | Permitted direct fixed-host TLS route and reviewed bounded transport. 451/429/error/restriction terminal; no proxy, VPN, paid service, mirror, alternate host/exchange or bypass. |
| Identity/expanded schema | UNKNOWN/HOLD | Independently reviewed exact current XRP/SOL keys, base/quote/classes/status and full schema; no guessing from synthetic examples. |
| Source-typed adapter/service timing | NOT IMPLEMENTED/HOLD | Original separately reviewed adapter and exact specification/interval acceptance; no market-to-synthetic relabeling. |
| One-shot owner authorization | MISSING/NO-GO | Exact future commit, full gate evidence and reviewed invocation/expiry/replay control. A design merge or green check is not run permission. |

The future bounded request plan stays readiness 017 §5: sequential BTC/XRP/SOL, at most one AssetPairs then identity-gated OHLC per symbol, **<=6 GET attempts**, fixed api.kraken.com:443 public paths/queries, no retries/redirects/pagination/fallback, global STOP first failure. No actual transport or live workflow exists to activate here. Neither policy is runnable simply by dispatching a workflow or setting a flag. Arithmetic sums of request/cleanup budgets are not a proven total OS wall-time cap; outer cap and actual enforceability need separate evidence.

## 8. Proposed source-typed historical observation boundary — no adapter implementation

Proposed future document/data contract ID: `kraken-spot-historical-observation-design-v1`. It is **separate** from accepted registry/bridge payload schemas; never inject new unknown fields into those schemas. No source-type value is accepted by current runtime merely because it is written here.

Outer envelope fields for separate review:

- contract and adapter/spec versions, exact reviewed implementation revision/run binding;
- source_kind `KRAKEN_PUBLIC_SPOT_HISTORICAL_OBSERVATION` (asserted origin), provenance_status describing verified collection steps and remaining uncertainty; **never SYNTHETIC_ONLY** for actual captures;
- capture clock evidence reference, `ESTIMATED_UTC_CONDITIONAL`, exact W_est_ns/U_ns/L_hours/frozen as_of, source/model versions, age/holdover/monotonic validity and assumptions;
- fixed request manifest and minimal redacted receipts, allowed identity fields and per-stage refusal/NOT_ATTEMPTED record, overall HOLD/REFUSED or proposed `HISTORICAL_DATA_VALIDATED_CONDITIONALLY`;
- normalized-data/eligible-source evidence references from the unchanged bridge/registry, source schema version and normalization/precision evidence, with clock provenance recorded separately;
- label `HISTORICAL_DATA_ONLY_NOT_CURRENT_SIGNAL`, no candidate rank, WATCH, BUY, ENTRY READY or execution fields.

This asserted source_kind is not a cryptographic origin guarantee. TLS route verification can support connection provenance, not independent timestamp/market-content truth or publication finality. Missing/unverified provenance must remain visible and can refuse according to approved policy; hashes alone never clear it.

A future original adapter must be reviewed in its own issue, accept only approved bounded captures, preserve exact decimals/metadata into bridge, expose validated normalized eligible bars without sorting/filling, preserve precision/source references and terminal refusal causes, and demonstrate canonical equality for unchanged bridge/registry decisions. It must not parse a summarized hash as data, reconstruct prices from logs, trust a caller-supplied validated bool or use a second unreviewed converter. Current bridge returns decisions/evidence, not a ready-made public normalized-bar export. This design does not pretend that export exists.

The current candidate evaluator remains synthetic-only and unchanged. Even a future historical data-validation success cannot be mapped to WATCH or a signal automatically. Any historical scientific candidate evaluation requires a separate source-aware research contract, causal/out-of-sample design and approval; paper evaluation and trading remain distinct stages without order authority.

Minimal retention proposal inherits 017: <=4KiB/symbol and <=16KiB/run redacted summaries; owner must explicitly set a retention period no longer than the earlier proposed 7 days or reject the proposal. No retention is activated. No raw bodies, headers/errors, daemon output, source addresses/IDs, secrets, certificates, full environment, raw-response hashes, excluded future-value/count artifacts or market price levels are to be logged. A separate future historical dataset/retention project requires its own licensing, provenance and approval; a bounded summary cannot substitute for data.

## 9. Acceptance/rejection criteria and owner decision form

Acceptance of **this document for further research** requires correct conditional math, explicit unknowns, unchanged runtime, deterministic negative evidence and no false live/strategy claims. It does not imply acceptance of B or permission to gather missing evidence.

Any future policy-B adoption decision must explicitly resolve all of the following, otherwise PROPOSED/HOLD remains:

1. Choose reject B/retain A, continue replay, or commission a revised B implementation specification. If pursuing B, record exact independently reviewed future revision and normative specification version; no approval for a moving branch or unspecified diff.
2. Fill actual U derivation/source+version+units and maximum U, actual L and maximum historical-age budget, age/holdover/lease/drift/sampling/step assumptions; show numerical margins for each anticipated request through its horizon. None can remain illustrative. Reject unsupported or circular provenance, unknown units and underreported contributions.
3. Approve the narrower truth claim and residual hidden-clock/source error risk in writing. Never record strict B4 PASS for environmental estimates. Unknown/unbounded/expired/untrusted evidence remains NO-GO even if owner prefers availability.
4. Resolve service-Date/current-row commitment rules coherently without changing existing code in place. Unknown service uncertainty/finality/expanded schema is a blocking specification gap, not an optional skipped check.
5. Review the original source-typed adapter and retention labels; prohibit real-data SYNTHETIC_ONLY use, success-to-WATCH mapping and claims of current freshness. Validate canonical same-context eligible evidence, independent symbol failure and all refusal precedence offline.
6. Independently close every remaining network/transport/target/identity gate listed above before any separate network authorization. If hard constraints cannot be substantiated, explicitly reject live retrieval and continue replay.
7. Approve a separately implemented, disabled-by-default enforcement mechanism only after offline review: exact revision/run/boot binding, expiry/replay protection, global STOP and all unchanged safeguards. Test passing or document adoption must not auto-activate it.

Unfilled decision form — **not an approval record**:

```text
record: historical-policy-owner-decision-v1
status: PROPOSED/HOLD
decision_requested: [REJECT_B_RETAIN_A | CONTINUE_OFFLINE_REPLAY | REVIEW_REVISED_B_SPEC]
owner_decision: UNSET
owner_and_BOSS_AI_independent_review_refs: UNSET
future_exact_revision_and_spec_version: UNSET
reviewed_source_host_model_and_residual_risk: UNSET
W_est_scale_units_capture_bracket_source_version: UNSET
U_actual_derivation_maximum_units_and_evidence_refs: UNSET
L_actual_whole_hours_and_age_budget: UNSET
sample_age_last_sync_holdover_drift_sampling_limits: UNSET
boot_domain_run_binding_and_monotonic_validity_horizon: UNSET
service_time_uncertainty_current_row_finality_acceptance: UNSET
historical_source_type_label_adapter_and_retention: UNSET
gate_rows_B1_B2_B3_B4_strict_B5_route_TLS_identity_schema_authorization:
  exact_evidence_refs_per_gate: UNSET
  unresolved_risks_and_rejection_conditions: UNSET
network_execution_approval: NOT_GRANTED
single_invocation_future_revision_replay_control_expiry: UNSET
rollback: abort/disable; preserve bounded redacted refusal; no fallback policy/retry
```

Expiry cannot be trusted solely to an unverified wall clock; a future approval/enforcer must specify justified relative lifetime and independently bound context. Reboot/domain mismatch, backward step, lease equality/expiry, drift/bound growth, stale status, false sync, missing provenance, parameter/identity/schema mismatch, unsupported framing, 451/route restriction or any cleanup failure aborts, prevents all subsequent requests and invalidates a potential acceptance. Never roll back into another clock policy, advance cutoff or preserve partial candidates. Re-review new code/source/runtime evidence before a new authorization; no automatic renewal.

**No GO is recorded on the owner's behalf.** Policy review, implementation authorization and one-shot network permission are three separate decisions. All existing diagnostic entrypoints retain AUTHORIZATION_MISSING/requests=0.

## 10. Offline adversarial evidence

New file `tests/test_historical_data_policy_018.py` contains only a synthetic model and unittest methods. It does not collect evidence, import into runtime, parse native daemon output, implement a market adapter, select a policy or return GO. An internally complete modeled record returns HOLD/CONDITIONAL_MODEL_NOT_AUTHORIZATION; invalid assumed records return NO_GO. Both are test vocabulary, not new production registry enums.

| Cases | Exact new tests | Result / interpretation |
| --- | --- | --- |
| ±U at exact hour and ±1ns, grid of U/L/errors; correct age envelope | `test_exact_hour_plus_minus_u_and_one_ns_boundaries`, `test_conditional_property_grid_and_floor_lower_bound`, `test_age_envelope_is_historical_not_current_signal` | PASS conditional inequalities only |
| Fractional uncertainty rounded up, declared U below model | `test_uncertainty_round_up_not_nearest`, `test_declared_u_smaller_than_model_is_no_go` | PASS detection of model inconsistency |
| One-day-fast clock, undetectable true-bound understatement | `test_gross_one_day_fast_clock_defeats_lag`, `test_underreported_real_error_is_undetectable_by_self_consistency` | PASS counterexamples; not proof of real-clock correctness |
| Complete synthetic record never GO | `test_complete_synthetic_record_can_only_hold` | PASS; synthetic modeled horizon bound 152ms is not observed clock data |
| Missing/false sync, leap/step, reversed monotonic, expired/insufficient leases | `test_missing_false_or_wrong_type_synchronization_refuses`, `test_leap_step_and_monotonic_reversal_refuse`, `test_expired_and_insufficient_horizon_leases_refuse_at_equality` | PASS fail-closed model |
| Holdover mismatch, stale sample, growing horizon, frozen cutoff | `test_sample_age_and_holdover_cannot_be_fabricated`, `test_aging_horizon_increases_bound_without_moving_frozen_cutoff` | PASS assumed age logic, not authenticated native field semantics |
| Untrusted source/version, unknown units/binding, invalid/nonfinite types | `test_untrusted_source_units_version_and_binding_refuse`, `test_invalid_parameters_and_nonfinite_values_refuse` | PASS model rejection |
| Stale relative to actual later coordinate, gap/partial/invalid eligible bars | `test_stale_relative_cutoff_is_not_fresh_relative_true_time`, `test_gapped_partial_invalid_and_old_eligible_history_refuse` | PASS unchanged registry refusals |
| Future append, entire canonical validated/refused registry evidence | `test_future_appends_preserve_complete_registry_evidence` | PASS within unchanged structural/size projection contract |
| Existing defaults/limits unchanged | `test_clis_remain_disabled_and_limits_unchanged` | PASS in-process mains: exit 2, AUTHORIZATION_MISSING, requests=0 |

Local CPython **3.12.14**, standard library, no installs:

```text
python -B -m unittest discover -s tests -p test_historical_data_policy_018.py -v
Ran 19 tests in 0.029s
OK

python -B -m unittest discover -s tests -v
Ran 244 tests in 3.080s
OK
```

**225 unchanged baseline tests + 19 new = 244, no skips.** Every new test blocks socket construction/connect/DNS, urlopen, HTTPSConnection, subprocess.run/Popen and time.time and asserts zero guarded calls. Existing offline chain/candidate/bridge/worker regressions remain in the full suite. Local elapsed times are not worker latency/target guarantees. No new current-head Actions run or Python 3.11 execution was obtained. Baseline TLS-context tests may load default local public trust roots; no handshake, CA hash collection or network measurement occurred.

## 11. Practical next step and final recommendation

Declared-as_of replay over existing supplied synthetic fixtures is practical now: no current-clock claim, collector, provider, actual network transport, source-typed market adapter or target timing assumption is needed to test causal/refusal behavior. Keep the label synthetic and do not infer market authenticity/publication or profitable ranking. Any later non-synthetic historical dataset still needs separate provenance/licensing/source-aware review; replay is not permission to disguise market data as a fixture.

**Smallest safe owner action:** review this exact draft head and choose continued offline replay or request specific revisions to the proposed B evidence/parameter/service-time specification. If useful, separately authorize a pinned-head offline Actions check; do not dispatch it as part of this assignment. No actual U/L values should be adopted without the completed evidence and decision record. Keep real retrieval on HOLD and strict B4 NO-GO.

Report handoff includes exact commit and changed paths in the draft PR/final response; the commit cannot contain its own hash. Only this new report and the new test file are proposed. Existing working observer/scanner, all production/research runtime, registry/bridge/candidate, workflows and dependencies remain inherited unchanged. No merge, main modification or issue closure.

**STOP FOR OWNER AND BOSS AI REVIEW. Neither policy, live diagnostics nor Operational Test Mode is approved.**
