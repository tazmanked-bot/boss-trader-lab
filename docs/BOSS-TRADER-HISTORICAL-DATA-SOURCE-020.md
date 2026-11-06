# BOSS-TRADER-HISTORICAL-DATA-SOURCE-020

Research date: **2026-11-06 UTC**. Authorization: [Issue #34](https://github.com/tazmanked-bot/boss-trader-lab/issues/34), documentation/terms research only.
Exact verified main: **`1db658673993a7e45ccfaba3d62eca2cac1b58ea`**, owner squash merge of PR #33.

**Verdict: HOLD / NO REAL DATA.** Prioritize Kraken's official archive for a further rights/applicability and sample-access decision, not acquisition. No reviewed source currently clears the combined intended identity, rights, bounded acquisition and scientific provenance gates. CryptoDataDownload commercial use is expressly restricted; community availability/license labels do not cure upstream permission or timing gaps. A revised-history descriptive pilot could be useful after separate approval, but point-in-time market evaluation remains unsupported without publication/correction evidence.

This is one new documentation file. No code, tests, fixtures, observer/scanner, registry/bridge/candidate/replay module, clock policy, workflow, dependency or main ref is changed. No market dataset/CSV/archive/checksum file was fetched, opened, imported, uploaded or ingested; no exchange endpoint, clock service, private API or numerical market response was requested. Web research was limited to public terms, documentation, catalog prose, repository metadata and README/license references. Static documentation may contain examples; no price values or actual historical OHLCV records are copied into this deliverable. No outreach, subscriptions, credentials, orders, paper positions, paid infrastructure, proxy bypass, VM or ZUMERAVO work occurred.

## 1. Evidence method and exact existing contracts

The source-policy and qualification requirements in [019 replay report §6](https://github.com/tazmanked-bot/boss-trader-lab/blob/1db658673993a7e45ccfaba3d62eca2cac1b58ea/docs/BOSS-TRADER-SPOT-REPLAY-019.md) and [018 historical policy](https://github.com/tazmanked-bot/boss-trader-lab/blob/1db658673993a7e45ccfaba3d62eca2cac1b58ea/docs/BOSS-TRADER-HISTORICAL-DATA-POLICY-018.md) were read at this baseline, alongside [011 schema findings](https://github.com/tazmanked-bot/boss-trader-lab/blob/1db658673993a7e45ccfaba3d62eca2cac1b58ea/docs/BOSS-TRADER-KRAKEN-LIVE-READINESS-011.md) and [016 candidate limitations](https://github.com/tazmanked-bot/boss-trader-lab/blob/1db658673993a7e45ccfaba3d62eca2cac1b58ea/docs/BOSS-TRADER-SPOT-CANDIDATES-016.md).

Actual source inspected: [replay `_qualify`, `_plan`, `_decision`](https://github.com/tazmanked-bot/boss-trader-lab/blob/1db658673993a7e45ccfaba3d62eca2cac1b58ea/research/spot_reversal_replay.py), [candidate evaluator](https://github.com/tazmanked-bot/boss-trader-lab/blob/1db658673993a7e45ccfaba3d62eca2cac1b58ea/research/spot_reversal_candidates.py), [registry](https://github.com/tazmanked-bot/boss-trader-lab/blob/1db658673993a7e45ccfaba3d62eca2cac1b58ea/research/spot_refusal_registry.py), [bridge](https://github.com/tazmanked-bot/boss-trader-lab/blob/1db658673993a7e45ccfaba3d62eca2cac1b58ea/research/kraken_spot_validation_bridge.py). The current replay accepts only exact original-generator reproduction; candidate input is SYNTHETIC_ONLY. Neither can admit real history by adding a source label or changing a manifest hash. This work does not weaken or bypass that gate.

Evidence classes:

- **VERIFIED DOCS:** accessible primary publisher documentation/terms or uploader README text, only for what the publisher actually states.
- **UNVERIFIED:** no accessible or sufficient evidence for the particular right, coverage, semantics or claim. UNKNOWN is retained rather than guessed.
- **AMBIGUOUS:** relevant statements exist but scope/applicability, conflicts or required permission are unresolved. This is not permission.
- **PERMITTED / PROHIBITED:** the cited text expressly supports the narrow classification, subject to stated conditions and rights the publisher actually controls. It is not an owner approval or jurisdiction-specific legal determination.

The owner's legal entity, jurisdiction, account/terms applicability and commercial purpose have not been established from timezone or repository identity. Do not presume Global terms govern every owner or that private research is noncommercial. Applicable regional terms and any separate data agreement need independent owner review. No provider is contacted here to resolve ambiguity.

## 2. Primary-source evidence register

Links below are documentation/terms/README pages, not dataset downloads. Retrieval date is the research date above; page-specific dates are separate from retrieval. Search snippets alone do not establish permission. Quotes are deliberately short and not a substitute for full terms review.

| ID | Primary source and version/date | Quote-sized evidence / direct finding | Boundary |
| --- | --- | --- | --- |
| K1 | [Kraken official OHLCVT support page](https://support.kraken.com/articles/360047124832-downloadable-historical-ohlcvt-open-high-low-close-volume-trades-data), updated **2026-11-02**; definitions, Complete Data, Incremental Updates | Says files can be **“used in code”**; volume **“qty in the base asset”**; data **“only includes entries for intervals when trades happened”**. Lists 60-minute archives, history through September 2026, multipart roughly 2GB downloads and quarterly updates. | Technical invitation to use files, not a complete commercial/redistribution license or proof of any particular file's quality. No parts, ZIPs or checksum files opened. |
| K2 | [Kraken legal routing page](https://www.kraken.com/legal), current regional applicability text | Global versus Canada/EEA/Brazil routing is explicit. | Owner jurisdiction and applicable agreement remain UNKNOWN; securities/derivatives agreements found in searches are not applied to spot archives. |
| K3 | [Kraken Global Terms](https://www.kraken.com/legal/global-terms), **last updated 2026-10-30**, §§8–9 | §8 says **“but only for your own benefit”**. §9 restricts **“otherwise commercially exploit or make available to any third party”**, and separately restricts extraction/automation and third-party applications without prior consent. | General content restrictions need reconciliation with K1 and applicable terms/permissions for the proposed dataset use. No archive-specific commercial grant was verified. |
| K4 | [Kraken OHLC REST documentation](https://docs.kraken.com/api-reference/market-data/get-ohlc-data), description; no displayed terms effective date | States **“older data cannot be retrieved”** beyond the most recent 720 entries; final entry is the current uncommitted interval regardless of since. | Documentation read only; no Try-it/API request. API access documentation is not a reuse license. Expanded current child schema remains unverified. |
| C1 | [CryptoDataDownload Terms](https://www.cryptodatadownload.com/terms-of-use/), **last updated 2023-09-20**, Use of Information | **“does not consent to any use of the information contained herein for commercial purposes”**. Also disclaims verification and warns of third-party IP/use restrictions. | Restriction is affirmative, not inferred from price/free tier. A different paid/API agreement is not purchased, reviewed or assumed to override it. |
| C2 | [CryptoDataDownload Kraken catalog/documentation](https://www.cryptodatadownload.com/data/kraken/), no effective date displayed | **“Currently unavailable.”** Describes separate epoch/display Date and two volume measures; the Date is NY EST and the crypto-volume example is BTC rather than USD. | No current full three-instrument offering or file schema was verified. No data links, tutorial downloads, API tokens or provider referrals followed. |
| R1 | [Rearc README](https://github.com/rearc-data/kraken-crypto-exchange/blob/a0510b8c39719648d1ff8b5a9d747d21fbad5ca7/README.md), exact commit **`a0510b8c39719648d1ff8b5a9d747d21fbad5ca7`** | Update marked **1/04/2021** says **“currently archived”**; links CryptoDataDownload as source and CC BY-NC-SA 4.0 as data license; describes an AWS Data Exchange product. | Numeric date format not resolved. Repository tree/API metadata show no LICENSE file/license object; README data-license link is not a software license or proof of upstream authority. No AWS subscription or data opened. |
| L1 | [CC BY-NC-SA 4.0 legal code](https://creativecommons.org/licenses/by-nc-sa/4.0/legalcode.en), version **4.0**, §§1(k), 2–4 | NonCommercial means **“not primarily intended for or directed towards commercial advantage or monetary compensation”**. The grant is limited to rights the licensor controls; noncommercial sharing/adaptation has attribution/share-alike conditions. | Explains R1's asserted license, not an independent grant from Kraken. Business-related private analysis is not automatically noncommercial. |
| G1 | [BTC_Historical_Data README](https://github.com/barbaraalfieri/BTC_Historical_Data/blob/8245853c661d0b4452e924badbab181b2df2d94a/README.md), exact commit **`8245853c661d0b4452e924badbab181b2df2d94a`** | Claims BTC/USD hourly history 2015–September 2025, obtained through Kraken/CCXT. Only README was read; tree/API license metadata returned no license. | README is the uploader's claim, not independently verified historical completeness or permission. XRP/SOL and the proposed October pilot are not documented coverage. No CSV or example data loaded. |

Availability/error log: the guessed Kraken `/legal/website-terms` path was inaccessible via the web tool; no legal conclusion relies on it. Hugging Face raw/resolve README paths for `tppetrov/kraken-ohlcvt-close-prices` and `GotThatData/kraken-trading-data` were inaccessible; their licenses/quality remain UNVERIFIED and they are not cleared alternatives. No alternate route/proxy or data preview was used to work around these failures. Search results about other exchanges, stocks, derivatives and unrelated similarly named businesses were excluded.

Web pages can change; an eventual approval must freeze the actual applicable terms text/version using lawful document evidence and independently review it at acquisition time. This research records no fabricated dataset hash, rights affidavit or provider confirmation.

## 3. Source comparison and permissions matrix

Source candidates: **A** official Kraken archive (K1–K3); **B** Kraken public OHLC REST (K2–K4); **C** direct CryptoDataDownload Kraken offering (C1–C2); **D** Rearc archived CDD-derived listing (R1/L1); **E** independent public GitHub BTC dataset (G1). D and E are different publisher claims, not independent measurements of market truth.

Each cell classifies the specific use **on accessible evidence**, not whether this owner may proceed. “PERMITTED*” is narrowly conditional publisher permission, not full chain-of-title clearance. All acquisition remains HOLD.

| Use | A: official archive | B: REST | C: CDD direct | D: Rearc listing | E: community BTC |
| --- | --- | --- | --- | --- | --- |
| Personal noncommercial evaluation | **AMBIGUOUS** K1/K3 reconciliation | **AMBIGUOUS** K3 scope | **PERMITTED*** C1 noncommercial scope, upstream caveat | **PERMITTED*** R1/L1 noncommercial licensed rights | **UNVERIFIED** G1 |
| Internal/private research | **AMBIGUOUS** K3 purpose/applicability | **AMBIGUOUS** K3 | **AMBIGUOUS** commercial purpose not decided by privacy | **AMBIGUOUS** same NC purpose question | **UNVERIFIED** G1 |
| Provider code reuse | **UNVERIFIED** no separate source-code grant identified | **UNVERIFIED** examples aren't a verified software license | **UNVERIFIED** C1/C2 do not establish software rights | **UNVERIFIED** no repository software license found | **UNVERIFIED** no repository license found |
| Commercial analysis | **AMBIGUOUS** restrictive K3, no archive exception verified | **AMBIGUOUS** restrictive K3, no grant verified | **PROHIBITED** C1 absent a separately proven grant | **PROHIBITED** asserted NC license, no separate grant | **UNVERIFIED** G1, not permission |
| Redistribution of data/derivatives | **AMBIGUOUS** K3 restrictions/no exception verified | **AMBIGUOUS** K3 | **AMBIGUOUS** no direct distribution grant established | **PERMITTED*** only within valid NC/attribution/SA rights; not commercial | **UNVERIFIED** G1 |
| Storage/retention | **AMBIGUOUS** download invitation not an archival retention agreement | **AMBIGUOUS** no reviewed retention grant | **AMBIGUOUS** duration/conditions unresolved | **PERMITTED*** noncommercial reproduction within valid licensed rights; other subscription/upstream obligations UNKNOWN | **UNVERIFIED** G1 |
| Attribution/notice obligations | **AMBIGUOUS** K3 preserves notices, archive-specific wording UNKNOWN | **AMBIGUOUS** K3 notice duties | **UNVERIFIED** exact direct-data attribution not established | **PERMITTED*** sharing requires credit/license/change notices and applicable SA; omitting required notices not permitted | **UNVERIFIED** G1 |
| Bulk acquisition/download | **AMBIGUOUS** explicit K1 mechanism versus K3 automation/consent scope | **UNVERIFIED** bulk rights; technically unsuitable for deep history | **AMBIGUOUS** C2 unavailable, scope not cleared | **UNVERIFIED** acquisition platform/permission and cost not reviewed | **UNVERIFIED** public hosting not a bulk grant |

Attribution is a compliance condition rather than an independent right: that row records whether the necessary rule is established, not permission to remove credit. R1's linked license cannot be transferred to C's entire current website or expand any upstream rights. A repository or transport-library license cannot license underlying exchange observations. No external code is copied or reused in this assignment.

Selection outcome:

- **A — priority for further review, HOLD acquisition.** Best direct source lineage of the candidates, but rights/applicability and a genuinely small lawful sample path are unresolved.
- **B — reject as the first deep historical source.** Its bounded recent window cannot establish the proposed older sample; no since-pagination workaround, trade crawl or live request is authorized.
- **C — do not select for commercial-purpose research on current terms; currently unavailable.** Do not seek an alternate product/referral in this task.
- **D — reject this archived product for the first pilot.** Its NC/asserted upstream license and older archived coverage do not establish a current suitable three-asset sample. No subscription.
- **E — HOLD/reject as sufficient three-asset evidence.** Missing rights and documented coverage gaps; a CCXT acquisition claim does not explain how a long backfill overcame the REST limitation or establish point-in-time publication.

These are source-selection decisions for a proposed study, not legal clearance. No “free” or “public” label is upgraded into commercial rights, redistribution, retention or source authenticity.

## 4. Market identity, measurement and quality audit

The following are **acceptance questions for future metadata/sample review**, not measured dataset defects or claims of coverage. Current source files were not inspected.

| Area | Required future evidence / refusal rule |
| --- | --- |
| Exact market | Kraken spot BTC/USD, XRP/USD, SOL/USD only; official historical instrument metadata and versioned USD/ZUSD mapping, no Binance USDT, perpetual, margin or other venue substitution |
| Naming | Treat BTC/XBT, XBTUSD/XXBTZUSD and XRP/SOL aliases as explicit mapping hypotheses, never string replacement. Existing bridge's accepted aliases do not independently verify current AssetPairs or historical file identities. Exact current XRP/SOL identities remain UNKNOWN. |
| Base versus quote volume | Require exact per-column units. K1 supports base-quantity volume; C2's two differently described volume columns must not be silently collapsed or chosen by a misleading header. Do not feed USD turnover into a base-volume feature. |
| Time | Prove UTC epoch precision/scale, alignment, open versus close timestamp and interval semantics from exact file/version documentation. C2 display Date's NY EST notation is not UTC or an established daylight-saving rule; prefer verified epoch semantics, never guess. |
| Schema | Establish actual archive column order/types/headers/delimiter/encoding. Prior local research described a seven-column time/OHLC/volume/trades CSV versus REST's eight positions including VWAP; exact member schema remains unverified until an authorized review. Do not infer it solely from the archive title. |
| Gaps | Missing hourly rows may represent legitimate no-trade periods or missing capture; source documentation and quality lineage must distinguish them. Existing no-gap refusal remains terminal. No forward filling, zero-volume candles, price fabrication or “zero-gap” replacement product to force eligibility. |
| Duplicates/order | Preserve original sequence and version. Duplicate, reversed or overlapping update records refuse; no silent sort/dedup. Corrections require separately reviewed immutable version selection before replay, not a per-snapshot repair. |
| Precision/values | Strict bounded decimal lexing, finite positive prices, correct OHLC bounds, nonnegative base volume/trade counts, overflow/underflow and precision-collapse checks, no guessing units. Preserve raw decimal evidence; a float hash alone cannot represent original precision. |
| Coverage/universe | Exact first/last available hours per symbol, missing/delisted/renamed markets, outages and source selection; fixed three-asset universe is not a representative market-wide or survivorship-free sample. Never add only the assets/periods that validate or appear favorable. |
| Backfill/revisions | Separate candle event time, original publication time, capture/export time and correction/release time. Final revised history is not evidence that final values were knowable at that earlier close. Unknown availability blocks a point-in-time claim. |
| Quality claims | Provider descriptions are assertions, not an independently verified completeness/correction log. Record unavailable metadata, all exclusions and refusals, rather than inventing a cleaned source history. |

### REST versus archive incompatibility

K4 documents a recent-window endpoint with an uncommitted final row. K1 describes downloadable history, quarterly release packaging and gaps. These are distinct publication/capture contexts. The fact that both are called OHLCV does not make them the same schema, correction version, timestamp convention or historical availability guarantee.

The current bridge requires exact REST-shaped metadata, six numeric strings including VWAP and integer count. Historical CSV must **not** be wrapped as a fabricated REST response: no invented VWAP/count/cursor/service Date or simulated AssetPairs receipt. If CSV lacks VWAP, preserve that absence; the existing normalized registry doesn't require VWAP, so a separately approved original CSV-to-normalized contract may be feasible with an independent source-quality record. That is a future design/implementation question, not permission to skip any actual source field validation or weaken the existing bridge.

No-trade gaps, unsupported fields, unknown time semantics or a malformed member can make a legitimate source REFUSED/HOLD without a software defect. Review incompatibility in a new issue; do not change safety rules until a sample passes. No timestamp or capture/publication record may be manufactured from a replay coordinate.

## 5. Separate source-typed ingestion proposal — not implemented

Proposed ID: `historical-kraken-source-qualification-design-v1`, status PROPOSED/HOLD. The first stage would qualify **metadata/rights only**, then a separately approved bounded sample, then an independently reviewed offline adapter/evaluator. No executable collector, source record, rights affidavit or market fixture is supplied here.

Documentary manifest template (all data-specific facts deliberately UNSET):

```text
contract_version: historical-kraken-source-qualification-design-v1
status: PROPOSED/HOLD
source_kind: REAL_HISTORICAL_KRAKEN_SPOT   # proposed typed boundary, not current runtime input
source_publisher_and_exact_release: UNSET
applicable_terms_version_region_entity_and_permission_evidence: UNSET
commercial_internal_storage_derived_redistribution_rights_review: UNSET
license_attribution_notices_and_retention_deletion_obligations: UNSET
owner_approval_exact_future_revision_and_review_refs: UNSET
immutable_symbols: BTC/USD; XRP/USD; SOL/USD
venue_market_quote_timeframe: Kraken; spot; USD; 1h
historical_instrument_mapping_and_schema_version: UNSET
source_member_names_and_immutable_range: UNSET
original_bytes_sha256_and_independent_expected_digest: UNSET
normalized_bytes_sha256_adapter_version_decimal_precision_audit: UNSET
timestamp_scale_unit_timezone_open_close_semantics: UNSET
event_time_original_available_at_captured_at_released_at_corrected_at: UNSET
availability_class: UNKNOWN   # point-in-time proven OR revised-history-only, explicitly reviewed
quality_counts_gaps_duplicates_order_corrections_missing_assets: UNSET
declared_non_live_evaluation_axis_and_plan_hash: UNSET
retention_location_owner_access_and_expiry: UNSET
acquisition_authorization: NOT_GRANTED
evaluation_authorization: NOT_GRANTED
```

Hashes prove byte identity only. An expected digest must be independently obtained and version-bound later, not copied from a new download and called independent. The archive support page's checksum availability was read as documentation; no checksum file/data digest was obtained and no dataset hash is populated here. Byte/range/version approval must precede use; if publisher hashes are absent, disclose the weaker identity evidence and require explicit independent review rather than forge one.

A future adapter must be original, source-aware and separately reviewed; retain source identity, exact decimal fields/quality evidence and corrections lineage, use strict bounded parsing, expose eligible normalized bars without sorting/filling, preserve registry refusal, and keep source evidence distinct from decision summaries. It must not use source assertions as a validated bool, reconstruct bars from report hashes or feed actual data under SYNTHETIC_ONLY. The current generator-only replay harness is unchanged and **will refuse** real history; there is no approved real-data evaluation route today.

Proposed future parsing envelope, subject to source rights/actual member schema review: <=1MiB per uncompressed sample member, <=4MiB total private sample bytes, <=168 hourly records per symbol in the proposed pilot, bounded field length/decimal magnitude and line/column count, exact allowlisted encoding/column mapping, no formulas or executable serialization. Compressed archives require separately approved compressed/uncompressed/member-count limits, allowlisted members, no path traversal/symlinks, no external references or decompression bombs. Unknown packaging/expansion budget -> STOP, not an automatic large download. These are future sample limits, not modifications to current registry/bridge/parser safeguards or a measured memory guarantee.

## 6. First real-data pilot proposal — no authority to fetch

**Purpose:** determine whether legitimate, source-qualified history can support refusal-preserving descriptive evaluation. It is not a profitability study, paper trading or a live diagnostic.

Proposed calendar range, selected without inspecting any market values: **2025-10-01 00:00:00 UTC through 2025-10-08 00:00:00 UTC, exclusive end**, three fixed spot USD instruments, hourly. Target **168 nominal hours per asset / 504 nominal rows total**; actual coverage is UNVERIFIED. This is an owner-review proposal, not a claim a suitable sample exists. Do not replace the interval/assets after looking at outcomes. Missing hours must be reported/refused, not filled or the date window moved to hide them.

Acquisition feasibility is a separate blocker: the documented complete official archive is multipart/large, not an established tiny three-file slice. **Do not fetch the multi-GB full package to obtain this pilot under a small-sample approval.** Require a documented lawful bounded subset mechanism or an already lawfully held, versioned source with independently verified rights and approved private extraction. No HTTP-range workaround, mirror, subscription, new provider contact or alternate exchange is authorized here. If small access cannot be established, the pilot stays metadata-only HOLD. C2 is unavailable, R1 archived, and G1 does not document this period/three assets; none is a fallback.

Required publication metadata request for a **future owner-controlled process**, not outreach now: release/version date; source/member hashes; exact schemas, timestamp and volume units; original availability/correction lineage; whether timestamps are event-time only; coverage/gaps per instrument; rights governing internal/commercial research, storage, derived aggregates and redistribution. If only final history exists, choose explicitly between rejecting point-in-time evaluation or a labeled **REVISED_HISTORY_DESCRIPTIVE_ONLY** pilot. Never infer earlier publication from a final CSV or archive release.

Proposed preregistered replay axis S = start of approved sample, horizon H=3h, embargo E=24h (21+H), <=64 evaluation snapshots:

| Partition | Evaluation coordinates, half-open offsets from S | Number | Rule |
| --- | --- | --- | --- |
| Context | First 21 closed hours | Not scored | No feature/warmup bypass |
| Train/development audit | [21h,45h) | 24 | No fitting or threshold search |
| Validation/protocol audit | [69h,93h) | 24 | 24h gap after previous end |
| Test/held-out audit | [117h,133h) | 16 | 24h gap; last outcome horizon fits sample |

The 168h target leaves unused tail/context; it is a QC pilot, too small for robustness or statistical conclusions. Earlier full history remains known validation context; embargo does not assert independent/disjoint full prefixes. Fixed 016 candidate formulas, terminal per-symbol refusal, 21+ bars, <=3h age relative to replay as_of, no gaps/duplicates/order repair and causal prefixes stay unchanged. An archive's last historical row is not the REST current-row observation and must not acquire fabricated live time attestation. All coordinates are experimental, not actual publication receipts.

Before real-data evaluation, a separate source-aware evaluator must be designed/tested without altering generator-only admission. Preserving rule behavior requires independent canonical parity against the existing evaluator on synthetic eligible inputs, future-mutation invariance, refusal precedence and event-label separation. No implementation is authorized by this plan. If the source-aware parity/admission boundary cannot be approved, no pilot evaluation occurs even with licensed files.

## 7. Descriptive evaluation evidence and economic limits

Future accepted outputs would report decision frequency and zero-candidate share, per-symbol WATCH/WAIT/BLOCKED/refusal reasons, feature pass denominators, censored WATCH duration, missing/unavailable labels and complete reproducibility hashes. Retain failed symbols/windows in the denominator/report; a fresh BTC cannot rescue XRP/SOL. WATCH remains a research observation, not an order or current opportunity.

Preregister a descriptive event rule before held-out outcomes: for an eligible candle closing exactly at t, terminal close at t+H higher than close(t) and all H intervening lows >= low(t), otherwise false; missing/stale/invalid forward context -> UNAVAILABLE. This is a price-pattern label, **not profit/loss, realized win rate or an executable fill**. Future labels must be calculated separately after all causal decisions. In revised-history-only mode, invariance proves computational causality on the supplied version, not historical availability of final corrected values.

For a later scientific study, extend coverage only through a separately preregistered plan spanning disjoint calendar periods and market regimes, fixed universe and meaningful sample sizes; disclose survivorship, selection, repeated overlapping horizons and multiple testing. Report all periods/assets including adverse/zero/refused cases, not the best week. Small pilot partitions, common market dependence and human window selection cannot establish edge or out-of-sample profitability.

Fee evidence would need the actual contemporaneous venue/tier and maker/taker rules; spread, latency and slippage need contemporaneous quote/depth/size/liquidity evidence. OHLCV alone cannot supply these. Predeclare conservative ranges, low-liquidity/adverse assumptions and missing-evidence outcomes; if evidence is absent, limit results to descriptive labels, not returns. 019's supplied-number cost helper is illustrative arithmetic only, not a cost calibration or permission for a simulated execution engine. No entry prices, fills, portfolio positions, catalysts, stops, leverage or paper/live orders are proposed here.

## 8. Owner acceptance checklist and staged decision

All choices remain unfilled. This is not approval on the owner's behalf:

1. Confirm the intended legal entity/jurisdiction and whether the research is directed toward commercial benefit. Review exact applicable terms and any archive-specific permission; reconcile K1/K3 before asserting rights. If unclear, retain HOLD. Decide separately whether future permission clarification/outreach is appropriate; none is sent now.
2. Select a source only after internal/personal/commercial use, storage/retention, derived aggregates, redistribution, attribution and bulk/extraction scope are supported by primary evidence. A no-redistribution/private-only plan cannot cure missing analysis rights. Reject an NC source for a commercial-purpose use unless a proven applicable separate grant exists.
3. Approve exact release, member/schema/identity mappings, immutable period/asset list, byte/row/compression limits and a genuinely bounded lawful acquisition method. No source file/hash/availability may remain invented or unknown at ingestion.
4. Approve point-in-time evidence or explicitly restrict the study to revised-history descriptive findings. Reject backfilled final values represented as earlier truth. Unknown metadata must remain visible; no automatic downgrade/upgrade based on favorable results.
5. Independently review a **separate future** original source-aware adapter/evaluator revision and synthetic safety tests, preserving current modules/refusals. No current replay-gate bypass or market data mislabeled SYNTHETIC_ONLY.
6. Freeze plan/event/horizon/embargo/exclusions before opening outcomes; exact future commit, independent review refs, private storage location/access, lawful retention/deletion and safe output scope. Proposed private raw sample retention **<=7 days only if rights allow**, otherwise shorter/none; public PR/report must contain no raw dataset or derived value series without separate redistribution permission. These are not claims of a permitted retention term.
7. Only then consider separate acquisition and evaluation authorizations with expiry, resource bounds and explicit refusals. No paid service, exchange request, live workflow or actual data access follows from accepting/merging this research document.

Suggested decision record:

```text
record: source-review-020-owner-decision-v1
status: PROPOSED/HOLD
owner_and_BOSS_AI_review: UNSET
legal_entity_jurisdiction_intended_use: UNSET
selected_source_exact_terms_version_and_permission_evidence: UNSET
rights_by_all_eight_categories_and_remaining_restrictions: UNSET
immutable_release_members_hashes_period_symbols: UNSET
bounded_lawful_sample_path_and_private_retention: UNSET
publication_class_and_correction_evidence: UNSET
future_adapter_evaluator_plan_exact_commit: UNSET
independent_review_and_expiry: UNSET
source_selection_decision: UNSET
acquisition_authorization: NOT_GRANTED
evaluation_authorization: NOT_GRANTED
network_live_trading_permission: NOT_GRANTED
```

If rights, schema/units, exact instrument, publication claim, safe packaging, byte limits or independent review fails, STOP/REFUSED/HOLD; no retry through another source or rule relaxation. A lawful source is not automatically scientifically adequate; a clean parser is not legal permission.

## 9. Verification, remaining blockers and recommendation

Documentation-only change: **no new executable code, tests or fixtures**. No unittest suite is run for this report; the baseline 019 report's test counts are historical evidence, not claimed as a new run or licensing verification. Verification here consists of exact main/issue/source reads, primary-page terms/date/section comparison, fixed README commit references and final Git diff/readback. No external-link checker, live source probe or dataset parser is executed.

Remaining blockers: applicable owner terms/rights; archive commercial and redistribution scope; bounded subset acquisition; actual three-asset coverage; full CSV/REST schema and volume/time semantics; source corrections/publication timing; original real-data adapter/evaluator; resource/retention approval. B1/B2 real transport/startup/headers, B3 actual global STOP integration and B5 target runner remain HOLD. Strict B4 independent UTC remains NO-GO; alternate historical observation policy PROPOSED/HOLD; live Kraken diagnostic and Operational Test Mode HOLD. A later approved offline dataset study is distinct from live collection/trading and cannot close those gates.

**Smallest safe owner choice:** review this exact draft, then commission only the official-archive rights/applicability and bounded-sample-metadata clarification stage, or retain synthetic-only replay. No actual acquisition is recommended until rights and sample access are independently supported. Any future outreach or acquisition needs its own explicit authorization; this assignment grants neither.

Only `docs/BOSS-TRADER-HISTORICAL-DATA-SOURCE-020.md` is added. Exact head/branch/draft PR are in the handoff; main and every prior file remain inherited unchanged. No merge or issue closure.

**STOP FOR OWNER AND BOSS AI REVIEW.**
