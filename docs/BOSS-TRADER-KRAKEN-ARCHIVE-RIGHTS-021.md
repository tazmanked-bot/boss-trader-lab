# BOSS-TRADER-KRAKEN-ARCHIVE-RIGHTS-021

Version: **archive-rights-review-v1**. Research/retrieval date: **2026-11-06 UTC**.
Authority: [Issue #36](https://github.com/tazmanked-bot/boss-trader-lab/issues/36), documentation/rights clarification only.
Verified baseline main: **`9d51d72489d40852d7ccf7362f4147c2d5c7460c`**, owner merge of PR #35.

**Judgment: HOLD / NO REAL DATA. Remain SYNTHETIC_ONLY.** Unambiguous applicable archive rights, source provenance and an officially documented bounded sample path have not all been established. The owner has not authorized acquisition, outreach, evaluation or a live run. Neither a technical download instruction nor a draft/merge is a data license.

Only this new document is proposed. No archive, CSV, checksum file, market manifest, dataset preview, exchange response or actual historical record was retrieved. No GET/HEAD/range request to a data URL, provider message/form/email draft, payment/subscription, scanner change, network diagnostic, clock-service query, workflow dispatch, credentials, paper/live trading, VM or ZUMERAVO access. Public legal/support/developer documentation was read through the web tool; repository instructions/prior report were read through GitHub. No market values or fabricated dataset/rights record are included.

## 1. Scope, source hierarchy and applicability

The retained [020 audit](https://github.com/tazmanked-bot/boss-trader-lab/blob/9d51d72489d40852d7ccf7362f4147c2d5c7460c/docs/BOSS-TRADER-HISTORICAL-DATA-SOURCE-020.md) was read at this exact baseline. This report narrows its official-archive questions and refines documentary schema evidence; it does not amend that report or clear its remaining gates.

| Ref | Authoritative source / scope | Version and exact anchor | Evidence boundary |
| --- | --- | --- | --- |
| S1 | [Official Kraken OHLCVT archive description](https://support.kraken.com/articles/360047124832-downloadable-historical-ohlcvt-open-high-low-close-volume-trades-data) | Displayed update **2026-11-02**; definitions, Complete Data, Incremental Updates, About the data | Product/support documentation, including the phrase **“used in code”**; not an independently identified archive-specific license. No linked data assets opened. |
| S2 | [Kraken legal routing](https://www.kraken.com/legal) | Current routing paragraph; no separate effective date displayed | Routes to Global with Canada/EEA/Brazil exceptions. This is routing evidence, not proof of this owner's residence/contract. |
| S3 | [Global Terms of Service](https://www.kraken.com/legal/global-terms) | Displayed update **2026-10-30**; introduction, §1/entity scope, §8 content, §9 restrictions | Applies to platforms/services under its stated conditions; actual owner/account/archive applicability remains unresolved. Summary is not substituted for operative terms. |
| S4 | [Kraken legal disclosures](https://www.kraken.com/legal/disclosures) | Accessible current public page; no Taiwan match in reviewed text | General disclosures, not an archive-use license. No Taiwan-specific dataset grant established. |
| S5 | [OHLC REST documentation](https://docs.kraken.com/api-reference/market-data/get-ohlc-data) | Description; no effective terms date displayed | Endpoint documentation only; no exchange call. Recent-window limitation and current uncommitted final entry remain. |

S3 §8 grants limited revocable use **“only for your own benefit”**. §9 contains restrictions on commercial exploitation/distribution, copying/modification, extraction/automation, third-party applications and removal of proprietary notices, with applicable exceptions/consent language. These are general content terms, **not a verified archive-commercial-use grant**. S1's processing invitation and S3's restrictions require reconciliation; no support-page exception is assumed.

### Taiwan-region investigation

Owner legal identity, contracting entity, residence/domicile, account status and commercial/internal purpose are **UNKNOWN**. Asia/Taipei timezone, Chinese-language presentation, project name or personal GitHub ownership cannot fill these facts. Conditional on actual residence and service scope, S2 may point to Global; that inference does not select a contract on the owner's behalf.

Attempts to read `https://www.kraken.com/zh-tw/legal` and `https://www.kraken.com/zh-tw/legal/global-terms` returned web-tool **not accessible** errors. The accessible S3/S4 text had no Taiwan match. **Taiwan-specific terms/version or special archive permission: UNKNOWN**, not “none exists.” Search results about promotions, derivatives eligibility and general regulatory licenses were not used to grant spot-data rights. No alternate route/proxy or inaccessible account material was pursued.

No separate archive-specific license, product agreement or special permission was established from the reviewed official public pages. A missing keyword/search result is not proof that no private or regional agreement exists. Future owner review must identify the actual applicable document, version, parties and any written grant; none is invented here.

## 2. Narrow rights evidence matrix

The required vocabulary below distinguishes explicit published restrictions from unresolved application. **EXPLICITLY RESTRICTED** means the general clause is express; it does not decide disputed archive/owner coverage. **AMBIGUOUS** means relevant language exists but cannot establish the proposed use. **UNKNOWN** means necessary evidence is absent. No row supplies owner authorization.

| Proposed use | Classification on present evidence | Source anchor | Evidence needed to decide the actual archive use |
| --- | --- | --- | --- |
| Private personal research | **AMBIGUOUS** | S1 processing invitation; S3 §8 | Confirm archive scope, applicable owner agreement and permitted private analysis. |
| Commercial internal research | **AMBIGUOUS** | S3 §§8–9 | Express coverage of the intended commercial purpose; private handling alone is not clearance. |
| Commercial derived summary / strategy evaluation use | **AMBIGUOUS** | S3 §§8–9 | Define permissible aggregate/evaluation outputs, ownership and any commercial limitations; do not equate original code with data rights. |
| Storage / retention | **UNKNOWN** for archive-specific duration/conditions | S1 download mechanism; S3 §8 revocability | Lawful storage, backups, retention, deletion and revocation obligations. |
| Redistributing raw data | **EXPLICITLY RESTRICTED** under general content terms absent applicable permission/exception | S3 §9 distribution clause | Archive-specific grant covering recipients/method and any conditions; none verified. |
| Redistributing derived data / metrics | **AMBIGUOUS** | S3 §§8–9 | Distinguish non-reconstructive metrics from recoverable data and resolve scope of any grant/restriction. |
| Automated / bulk acquisition | **EXPLICITLY RESTRICTED** by general extraction/automation clauses; archive-specific reconciliation **AMBIGUOUS** | S3 §9 versus S1 instructions | Approved lawful method and any necessary consent; technical instructions do not settle legal scope. |
| Attribution / notices | **EXPLICITLY RESTRICTED**: general notice removal/obscuring; archive-specific attribution format **UNKNOWN** | S3 §9 notices | Required copyright/license/source/change notices and any attribution wording. Attribution alone cannot cure missing rights. |

No unconditional **EXPLICITLY ALLOWED** classification for the complete proposed owner/project use is supported. This is not a conclusion that all internal research is inherently prohibited; it is insufficient evidence to clear this particular use. Exceptions, facts/database rights and whether non-reconstructive metrics fall within restricted material need independent review rather than speculative legal assumptions. No third-party summary, open-source code license or community rights label is applied to Kraken's archive.

## 3. Fixed pilot and bounded-access feasibility

Requested pilot remains **2025-10-01 00:00 UTC to 2025-10-08 00:00 UTC, exclusive end**, BTC/USD, XRP/USD, SOL/USD, Kraken **spot USD**, 1h. The design anticipates 168 nominal hours per asset / 504 nominal rows; these are arithmetic targets, **not observed coverage**. No substitution, price inspection or source-derived sample record exists.

The following S1 metadata was checked **only in documentation text**. Its availability does not mean corresponding bytes, integrity or rights were verified.

| Question | Documentation evidence | Classification / unresolved fact |
| --- | --- | --- |
| Aggregate history | Through **2026-09-30** advertised | **VERIFIED DOCS**; exact pilot coverage per asset **UNVERIFIED** |
| Complete packaging | Parts **00–04**, roughly **2GB** each, reassembly described | **VERIFIED DOCS**; exact sizes/total/expanded size **UNVERIFIED**, no headers queried |
| Incremental packages | **2026Q1/Q2/Q3** listed | **VERIFIED DOCS**; byte sizes/contents **UNVERIFIED**; not a proven October-2025 subset |
| Per-pair files/hourly option | Per-pair CSV sets; **60-minute** option | **VERIFIED DOCS**; exact BTC/XRP/SOL member names/ranges **UNVERIFIED** |
| Schema/header | Headerless seven-column CSV described | **VERIFIED DOCS**; actual member conformance **UNVERIFIED** |
| Build manifest | Internal **`MANIFEST.json`** described | **VERIFIED DOCS** for described existence; fields/content/version/digests **UNVERIFIED**; not fetched |
| Published integrity metadata | Part-checksum link and reassembled expected SHA-256 displayed | **VERIFIED DOCS** for publication; checksum-file bytes, target-member digests and actual integrity **UNVERIFIED** |
| Standalone member index | No usable external target-member index established | **UNVERIFIED**; internal manifest is not an inspected index |
| Small subset/sample method | None established in reviewed official documentation | **UNVERIFIED**; no supported byte-range/subset method or lawful bounded slice verified |
| Archive-specific rights | No grant established | **UNKNOWN / HOLD**; size reduction would not resolve rights |

**Pilot feasibility: HOLD.** Only large complete packs and quarterly package descriptions are established, not an already documented small lawful sample meeting all constraints. A multipart ZIP is not three tiny member downloads. Do not retrieve a central directory, manifest, checksum or partial ZIP via HEAD/Range to investigate; do not fetch the full pack under a small-sample approval. No mirror, API workaround or community upload is an alternative in this issue.

S1's broad programmatic-availability statement does not establish an older-history subset service. S5 specifically limits OHLC to the most recent 720 entries, regardless of since, and retains a current uncommitted row. Treat these differing levels of description as unresolved access scope, **not permission to paginate old candles or crawl another endpoint**. The specific REST constraint defeats its use as the documented route for this old pilot.

Refinement from 020: documentary column order/header and an internal build-manifest claim can now be classified VERIFIED DOCS. File inspection, publication timing, small-slice access and rights have **not** advanced to verified data evidence. No checksum value is copied into a putative dataset record; no actual dataset hash exists in this work.

## 4. Schema, provenance and scientific limits

S1's reported order is `timestamp, open, high, low, close, volume, trades`; timestamps are described as UNIX/POSIX and volume as base quantity. The reviewed description does not settle exact timestamp precision/unit or open-versus-close convention for each target member. Those facts require authoritative schema/version evidence before parsing, not guesses from a plausible number.

The existing strict REST bridge uses eight positions including VWAP plus metadata/cursor constraints. The archive must not be disguised as a REST capture: no fabricated VWAP, count, cursor, AssetPairs identity or service time. A distinct original CSV-to-normalized adapter might eventually preserve source fields/precision/evidence while calling unchanged refusal rules, but requires its own approval and synthetic parity tests. It is not implemented here.

Acceptance questions for that future review:

- Confirm historical BTC/XBT, USD/ZUSD and exact XRP/SOL file/instrument identity; current aliases and expanded market schema remain unverified. No string-replacement guesses, Binance USDT, perpetuals or other providers.
- Preserve legitimate no-trade gaps as gaps. The unchanged validator still refuses discontinuous history; never fill or sort/deduplicate to force a candidate. Record missing/corrected/duplicated/out-of-order records honestly.
- Specify strict bounded decimal parsing, positive finite prices/OHLC bounds, base-volume/count validity, overflow/underflow and normalization precision; preserve exact eligible-source evidence separately from normalized decisions.
- Separate bar event time from original availability, capture/export, build/release and correction times. Internal build metadata is not automatically per-bar first-publication evidence.
- If only final revised history is supportable, retain a **REVISED_HISTORY_DESCRIPTIVE_ONLY** study label after explicit owner acceptance; no assertion that final values were knowable at the earlier replay coordinate. Unknown publication lineage cannot support point-in-time claims.
- Keep source identity/rights metadata outside existing exact registry/bridge schemas. Current replay requires original generator reproduction and candidates require SYNTHETIC_ONLY. **Never apply SYNTHETIC_ONLY to real exchange history** or bypass that admission gate.

The proposed week is a bounded QC/evaluation-design sample, not a statistically defensible estimate of edge. Chronological holdout/embargo and future-price mutation tests can prove computational causality on a supplied version, not its real publication history, fills, profitability or trading readiness.

## 5. Precise owner evidence gates before any acquisition decision

Every item must have an independently reviewed source/reference; a general owner preference does not fill unknown facts:

1. **Applicability:** actual owner/legal entity, relevant jurisdiction, account/contract status and internal/commercial intent. Identify exact governing terms, effective version, service/party scope and any archive-specific grant. Taiwan timezone is not evidence.
2. **Use rights:** explicit permission or independently reviewed applicable basis for private/internal/commercial evaluation, derived summaries/strategy evaluation, storage/backup/retention/deletion, raw/derived redistribution and required notices. Resolve S1/S3 tension. If no adequate basis, remain HOLD; do not invent a rights affidavit or silently classify internal use as personal.
3. **Bounded lawful source:** officially supported fixed sample or approved extraction from already lawfully held, versioned files, with proven rights. Exact immutable period/instruments/member identifiers and byte/compression/row caps; no implied full multi-GB acquisition. If no safe small path exists, remain SYNTHETIC_ONLY.
4. **Provenance/integrity:** exact source release/build identity, independently sourced expected digest where possible, original/normalized hashes only after later authorization, metadata lineage and quality counts. Missing independent digest must be disclosed for review, not manufactured or substituted with a self-hash claimed independent.
5. **Time/schema limitations:** authoritative units/precision/open-close schema, exact spot identity, gap/correction policy, availability class and limitations. Explicitly choose rejection versus revised-history-only scope if point-in-time evidence is unavailable.
6. **Private handling:** owner-approved storage location/access, lawful retention period and deletion/backup handling, permitted redacted outputs; no dataset or recoverable value series in a public PR without an express redistribution basis. Earlier <=7-day retention was a proposal, not a granted right; leave the actual period UNSET.
7. **Separate future code review:** exact future original source-aware adapter/evaluator revision, strict parser/resource bounds, unchanged candidate/refusal rules, parity/no-lookahead/negative tests and immutable study plan. No existing scanner/replay changes in this issue.
8. **Distinct authorizations:** a rights-review decision, a provider-outreach decision, an acquisition decision and an evaluation decision must be separately scoped. Exact future commit/expiry/review references, no live collection or trading authority. Unmet gate -> STOP/HOLD, no automatic retry/fallback.

Unfilled owner record:

```text
record_version: archive-owner-decision-021-v1
status: PROPOSED/HOLD
owner_and_BOSS_AI_review_refs: UNSET
legal_identity_jurisdiction_contract_and_intended_purpose: UNSET
applicable_terms_and_archive_permission_version: UNSET
eight_rights_categories_and_permission_evidence: UNSET
official_small_sample_method_and_safe_limits: UNSET
exact_release_members_window_symbols_and_expected_integrity_evidence: UNSET
schema_timestamp_availability_correction_class: UNSET
private_storage_retention_deletion_and_public_output_scope: UNSET
future_adapter_evaluator_exact_revision_and_independent_review: UNSET
owner_decision: UNSET
provider_outreach: NOT_AUTHORIZED
acquisition: NOT_AUTHORIZED
evaluation: NOT_AUTHORIZED
network_diagnostic_or_trading: NOT_AUTHORIZED
```

No GO or applicable legal permission is recorded on the owner's behalf. No sample metadata field is populated with invented observations.

## 6. Optional clarification message — UNSENT TEXT ONLY

This is a reusable question template **inside this document only**. It has not been sent, pasted into a support form or created as a draft in any external account. No recipient/channel is selected and no response or willingness to provide data is assumed. The owner must separately authorize any use after supplying accurate scope; no keys/account secrets are needed.

> Subject: Clarification of official historical spot OHLCVT archive use and bounded sample access
>
> We are considering a private offline research study, not trading or live monitoring. Before any acquisition, please identify the applicable archive license/terms for [owner legal entity/jurisdiction and accurate internal/commercial purpose], including whether an account or separate agreement is required.
>
> 1. Does permitted use include commercial internal research and commercially used non-reconstructive descriptive/strategy-evaluation summaries? What is restricted for derived data versus raw redistribution?
> 2. What storage, retention, backup/deletion, attribution and notice conditions apply? How do archive code-processing/download instructions interact with Global content and automation restrictions?
> 3. Is there an officially supported lawful bounded sample for 2025-10-01 00:00 UTC–2025-10-08 00:00 UTC, BTC/USD, XRP/USD, SOL/USD, spot USD, 60-minute candles, without retrieving the complete multipart pack? Please identify documentation and size limits; no sample should be sent before separate approval.
> 4. What exact release/member names, compressed/expanded sizes, externally accessible index/build metadata and independently published member digests describe that scope? Does MANIFEST.json supply these or different fields?
> 5. Please specify timestamp unit/precision, open-versus-close convention, volume/count schema, no-trade gaps, historical aliases and correction/release lineage. Is original per-bar publication timing evidenced, or only final revised history?
> 6. Please identify the version/effective date and scope of any answer or formal permission, and any limitations requiring a different agreement. We will not infer a grant from technical availability.

The template is a request for clarification, not a contract, admission of eligibility, permission record or promise of an eventual reply. Continue without outreach unless separately instructed by the owner.

## 7. Verification and final recommendation

Documentation only: no new executable tests or fixtures, and no unittest suite run. The retained 019 counts are not represented as fresh evidence. Static checks cover all eight rights categories, all metadata classifications, exact window, NOT_AUTHORIZED defaults, unsent-template warning, citation URL syntax and STOP text; no network link checker is used. Final Git diff/readback verifies this one addition and unchanged main/base inheritance.

Outstanding gaps remain **rights/applicability, actual small lawful subset, target members/sizes/manifest contents/integrity, exact temporal semantics/publication/corrections and a separately approved real-data adapter**. B1/B2 real transport/startup/headers, B3 actual global STOP integration and B5 target runner stay HOLD; strict B4 independent UTC stays NO-GO. The alternate historical observation policy remains PROPOSED/HOLD, live Kraken observation and Operational Test Mode HOLD. Offline licensing research cannot close any of these gates.

**Smallest safe owner decision:** keep SYNTHETIC_ONLY and review this exact draft. Decide whether to authorize only a narrowly scoped clarification using the unsent template after supplying correct applicability/purpose facts, or decline outreach and continue synthetic research. Neither choice grants data acquisition. With no unambiguous rights/provenance/bounded subset evidence, the fixed pilot remains **HOLD / NO REAL DATA**.

Only `docs/BOSS-TRADER-KRAKEN-ARCHIVE-RIGHTS-021.md` is added; exact head/branch/Draft PR are in the handoff. No main update, existing-file change, merge or issue closure.

**STOP FOR OWNER AND BOSS AI REVIEW.**
