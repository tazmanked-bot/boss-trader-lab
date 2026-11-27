# BOSS Trader — CODEX 032 offline decision loop

Issue #59; owner RESEARCH GO / IMPLEMENTATION GO. Additional expenditure: **NT$0**.
Working offline implementation; genuine AI inference remains unimplemented.

## Run it

From the repository root, Python 3.11+ standard library only:

```sh
python -B -m research.decision_loop_032
# Idle: no fixture, server, network, inference or order side effects.
python -B -m research.decision_loop_032 --demo --cards
python -B -m research.decision_loop_032 --demo
python -B -m research.decision_loop_032 --demo --output new-research-archive.json
```

The last command creates a NEW evidence archive and refuses an existing destination.
No local recorder, account file, journal, provider, model server or credential is
accessed. The only demonstration input is the fixed packaged synthetic fixture.
The Python API accepts bounded in-memory synthetic fixtures and trusted test
adapters; it does not discover, install or dynamically execute plugins.

[Executed readable cards](artifacts/decision-loop-032-cards.txt) and
[matching JSON archive](artifacts/decision-loop-032-demo.json) are from the same
run. The archive's journal chain was read back and verified. Actual results:

| Lead | Decision | Reason |
| --- | --- | --- |
| BTC/USD event without candles | BLOCKED | EVIDENCE_MISSING |
| SOL/USD completed synthetic candles | WAIT / rejected | ANALYST_REJECTED |
| BTC/USD completed synthetic candles | WATCH / research accepted | SYNTHETIC_RESEARCH_ACCEPTED |
| XRP/USD completed synthetic candles | WATCH / research accepted | SYNTHETIC_RESEARCH_ACCEPTED |

Candidate count: **2**, maximum 3, zero is supported. All cards say
BUY AUTHORIZATION NONE. The MOCK hypothesis is “unchanged fixture reversal
conditions merit research review.” Its strongest objection is that synthetic
candles establish no real-world predictive performance. Invalidation is a later
eligible low below the retest anchor; no numeric entry, fill or executable quote
is invented. This mock intentionally rejects SOL to exercise the rejection path;
that rejection is fixture behavior, not an AI discovery or investment opinion.

## Baseline and nonduplication

Main verified at `457531a92df4112957d3c3744c081a15f16858ed`.
Inspected #53/#55/#57, #54/#56/#58 and latest issue comments (empty). Draft heads:

- #54 `8b801dae5c13a264167ddfe56c58c5052118c496`.
- #56 `499edbedf4c5ae7e6aa31891f01809afc373e6ef`.
- #58 `e0c098e85d66e4856efd46b062ecefc61f764be5`.

Dedicated branch `research/issue-59-offline-decision-loop`, based on the exact #58
head and stacked Draft PR targeting `research/issue-57-read-only-market-view`.
This preserves the entire pending source/dashboard/demo-journal stack without
merging or rewriting it. It is not based on parked #52. README/SECURITY and the
024/031 source-admission/evidence reports were reviewed; baseline tree has no
AGENTS.md. No existing repository file is modified by this implementation.

The verified GitHub tree has no modules named S1/S2/S3 or operational market
recorder. README explicitly says the owner's local V3.8 scanner is not migrated.
These local/external systems were neither accessed nor reconstructed. Their data
is not assumed available. This implements only the authorized independent offline
slice; it makes no claim to integrate or validate the owner's operational systems.

Git clone failed at the inherited proxy (`Failed to connect to proxy port 8080`).
The pinned text snapshot was staged through the GitHub connector and checked
against Git blob hashes. Baseline PNGs were not needed locally and remain in the
remote base tree. No proxy bypass or blocked escalation was attempted. Reported
baseline is the verified remote commit, not a fabricated local git HEAD.

## Incremental architecture

1. **Scout:** at most 12 fabricated leads, exact version/schema and 256 KiB
   canonical input cap. Source IDs normalize to lowercase; source/symbol/time
   duplicates yield one inference, and conflicting duplicates block rather than
   selecting the convenient value. A duplicate event receipt records deduplication.
2. **Verify:** source declaration, exact spot USD identity, timestamp availability,
   age/missing fields, and the unchanged refusal registry. Full candle evidence
   is required for this hypothesis; a narrative-only event is retained as BLOCKED.
   Source strings and hashes are caller assertions, not provenance authentication.
3. **Analyst:** a narrow provider-neutral `Analyst` protocol takes a structured
   evidence request and returns exact `analyst-v1` output: hypothesis, evidence
   references, strongest objection, missing information, invalidation and
   SUPPORT/REJECT/ABSTAIN. Only the installed deterministic **MOCK** adapter is
   runnable. Wrong/missing fields, extra order fields and unknown references block.
   External prose is data, never executed instructions. The adapter receives a
   deep copy, so it cannot mutate the journal's evidence through its request.
4. **Risk:** version `research-risk-v1` uses `spot_reversal_candidates.evaluate`
   and `spot_refusal_registry` unchanged. No duplicated indicator/reversal formula.
   Existing BLOCKED/WAIT cannot be promoted by model SUPPORT. Missing information
   or abstention blocks; rejection becomes WAIT. Qualified support becomes only
   synthetic WATCH research, ranked by existing score then symbol/evidence digest,
   at most one per symbol and 0–3 total. There is no BUY or order path.
5. **Evidence journal:** append-only in-process immutable string snapshots,
   version/sequence/previous hash, source/evidence, verification age/gaps, policy,
   rule result, analyst/adapter identity, reason codes, elapsed inference timing
   and cost. No-call timing is NOT_RUN; MOCK cost is zero NTD, tokens not applicable.
   Frozen snapshots return copies on decode. `verify_journal` checks chain/version,
   sequence and canonical hashes and detects alterations or missing prefixes.

This journal is a small research evidence receipt archive, not a second trade or
accounting engine. It reuses registry canonicalization and the existing replay's
explicit as-of snapshot convention. The existing JS DEMO_ONLY paper engine,
versioned store, export/restore, positions, fees and exact decimal accounting are
unchanged. No research event becomes a paper entry or simulates a fill.
Hashes provide accidental-change detection, not signatures, authenticated source
proof, crash-safe database transactions, filesystem WORM or protection against an
actor recomputing the whole chain. A new output file is an explicit manual archive;
there is no daemon, shared store, scheduled job or Drive integration.

## Time, trust and limits

Only the supplied hourly fixture coordinate is used for decisions. Source available
at/after publication is required. Future-availability events are deferred before
reading their text/payload into analysis. Candle rows after the observed/as-of
cutoff are projected out **before** evidence hashing or inference. Existing
registry warm-up, freshness and chronological rules then apply. No future outcomes,
forecast labels or local clock time enter decisions. Timing uses local monotonic
measurement only; timing and receipt hashes can vary across reruns. Frozen-timer
regressions establish same-prefix equality, not cross-run identical runtime timing.

The public input fixture reuses completed candle prefixes from the repository's
original synthetic 016 fixture and adds original synthetic source/event wrappers.
It contains no market download, owner notes, private balances or machine identity.
Schema validity and fabricated provenance do not admit authentic market data.

Only trusted Python adapter implementations may be passed to the API. The protocol
is not a sandbox for malicious code or a bounded runtime for a hung genuine model.
The MOCK adapter has no model weights, tokens, stochastic reasoning, tool access,
network or demonstrated predictive intelligence. Schema validation does not solve
all prompt injection for a future genuine model. No REAL identity flag can activate
external/local inference in this version; such identities refuse.

B1/B2/B3/B5 HOLD; B4 NO-GO; real source admission HOLD; NO ORDERS. Existing
read-only observer availability is not expanded or tested live by this task.

## Actual verification

Python 3.12.14; existing Node v24.19.0; no dependency installations.

| Command | Actual result |
| --- | --- |
| `python -B -m unittest discover -s tests -p test_decision_loop_032.py -v` | 19 passed, 0.073s |
| `python -B -m unittest discover -s tests -v` | 517 passed, 6.827s, no skips |
| `node tests/test_paper_029.cjs` | 26 checks passed |
| `node tests/test_restore_030.cjs` | 14 checks passed |
| `node tests/test_market_031.cjs` | 8 groups passed; controlled dependencies |
| `python -B -m research.decision_loop_032 --demo` | 2 WATCH, 1 rejected WAIT, 1 BLOCKED; zero external calls/spend |
| Archive readback + `verify_journal` | passed; readable-card hashes match this same archive |

New tests cover valid lead, normalized/exact duplicates and conflicts, stale/missing
provenance/evidence, quote mismatch, invalid analyst schema/references, extra order
field, missing objection/information, deterministic risk veto, unavailable provider,
adapter mutation isolation, future-candle/event no-lookahead, untrusted instructions,
immutable snapshots and chain tampering, empty/0–3 outcomes, size/duplicate JSON/
nonfinite refusal, default no-I/O, explicit MOCK identity and no-overwrite export.
Network/DNS/urllib/subprocess guards surround new focused tests. No genuine model,
provider, time authority or order interface was called. Prior browser/loopback
failures in #58 remain unresolved; this CLI/JSON slice needs neither, and makes no
new browser or native-persistence claim. No dashboard artifacts were replaced.

## Research deltas — primary sources checked 2026-11-27

No upstream package/code/weights were installed or integrated. Licenses below are
those inspected at the cited upstream revision, not a blanket data-rights clearance.
CPU/RAM are **not benchmarked** on this target. Vendor datasets/services retain
separate terms; source-code permission never grants market-data rights.

| Project / pinned primary source | Incremental value and resource/cost judgment | License/data boundary and decision |
| --- | --- | --- |
| [TradingAgents](https://github.com/TauricResearch/TradingAgents/blob/121265d18d467ac717f7af99cb0d669c15d2e73c/README.md) | Analyst/objection role separation; local vLLM/Ollama or vendor providers documented. Runtime CPU/RAM depends on selected model; multiple agents multiply calls. No fit/latency measured. | Apache-2.0 at inspected source. Default provider/data routes need API keys and may incur charges; no NT$0 hosted-call assumption. Borrow structured objection pattern only, not framework or performance claims. |
| [OpenBB current canonical repository](https://github.com/openbq-org/OpenBB/blob/f0f1852b96dd3fc4d5868f8863cbe053ff49c6cd/README.md) and [LICENSE](https://github.com/openbq-org/OpenBB/blob/f0f1852b96dd3fc4d5868f8863cbe053ff49c6cd/LICENSE) | Provider-neutral data contracts useful later, not an inference engine. Normal Python data workloads can use CPU; dataset/dependency footprint and target minimum RAM unmeasured. | Original OpenBB-finance path returned Moved Permanently; repository search resolved the same ID 323048702. Current pinned LICENSE says Apache-2.0; do not extrapolate historical licensing or ownership guarantees. Vendor keys/data/Workspace terms separate. No integration for this small slice. |
| [TimesFM 2.5 / 3.0](https://github.com/google-research/timesfm/blob/918df02c9d366b2145bc5876135fa2131d3ed2a6/README.md) | A forecasting baseline, not a narrative analyst. 2.5 documented as 200M parameters; float32 parameter storage alone is ~0.8 GB decimal, not total RAM/CPU requirement. 3.0 supports multivariate forecasting. Target latency, working RAM and CPU feasibility unverified; no weights available here. | Source Apache-2.0; upstream notice says weights through 2.5 Apache-2.0, but 3.0 downloaded/self-hosted weights noncommercial/nonproduction under separate terms. Authorized Google Cloud commercial route is outside NT$0 scope. Prefer a later licensed local 2.5-vs-naive test, not installed now. |
| [GS Quant](https://github.com/goldmansachs/gs-quant/blob/0e3cc8e894ce1cc9574db9de03da2a31d07f1978/README.md) | Risk/scenario vocabulary; Python >=3.10. Pure local analytics could run on CPU, but target requirements and service entitlements unverified. Large dependency/data surface exceeds this slice. | Apache-2.0 at inspected repo. Platform/data access may require permissions and commercial arrangements; code license is not data/service access. Defer; no credentials or service calls. |
| [Vibe-Trading](https://github.com/HKUDS/Vibe-Trading/blob/a7ea2328337ee435fc7c25c0378d130dd038b63b/README.md) | Evidence grounding, skill boundaries and invalid/missing outcome treatment. Model/provider and data integrations could duplicate existing recorder/journal. CPU/model RAM and total costs unverified; setup documents provider keys. | MIT at inspected repo. Do not enable execution/connectors/swarm/scheduling. Treat upstream backtest/viral metrics as unverified claims, not evidence for BOSS. Borrow ideas only; no framework adoption. |
| [Qlib](https://github.com/microsoft/qlib/blob/54355232463878d2eebb91fe0ee5fa7fa1f5976c/README.md) | Train/validation/test and reproducible benchmark organization. CPU/LightGBM examples and upstream CPU benchmarks exist, but are not our target measurements or crypto results. Dataset prep and dependencies required. | MIT at inspected repo; datasets/vendor rights separate. Existing 019 replay already provides chronological synthetic evaluation, so reuse it before introducing Qlib. No dataset download. |

Exact `agent_skills` upstream identified as
[Jane Street's janestreet/agent_skills](https://github.com/janestreet/agent_skills/blob/469868f4489cbdbe178c775a0af05bb6bef63689/README.md):
a SKILL.md collection whose inspected README lists **socratic-tutor**, not a trading
strategy or privileged institutional signal. Similar hyphenated repositories are
not silently substituted. LICENSE at that pin returned 404; reuse permission is
UNVERIFIED, so nothing is copied/installed. Attribution or a public repo alone is
not permission to incorporate its prompt text. Alpaca MCP is explicitly deferred;
no account, credential, order route or MCP broker integration.

## Next bounded milestones (design only)

- **Genuine AI adapter first:** passive inventory found no installed
  llama-cpp-python, Torch, Transformers or Ollama Python package, and no reviewed
  local checkpoint was provided. Next implementation task: pin one permissively
  licensed, already available offline text model/runtime; implement one local
  adapter with exact same schema, no tools/network, input/output/token/time limits,
  timeout isolation, JSON/ref checks and objection/hallucination tests. Measure
  actual CPU/RAM and record model/license/hash before calling its outputs AI.
  Keep MOCK explicitly labeled and all deterministic vetoes. If no existing local
  checkpoint/runtime is available, retain MOCK until a separately reviewed NT$0
  provisioning decision; no paid fallback or installation is performed here.
- **S4 hypothesis discovery:** propose one falsifiable new hypothesis with evidence
  refs, counterargument, invalidation and owner review. No replacement of S1/S2/S3;
  their specifications/data must be supplied before any integration/parity claim.
- **Naive vs forecast:** extend existing 019 walk-forward splits with an immutable
  last-close/persistence baseline, then one eligible TimesFM forecast. Same closed
  prefix, horizon, held-out metrics and cost assumptions; no future labels in the
  request, no profitability or simulated-fill claim from forecast error alone.
- **On-chain/narrative moonshot track:** separate untrusted event provenance,
  publication/availability time, token/chain identity, conflicting claims and
  absent independent corroboration. Stay BLOCKED on critical gaps; no wallet
  connection, new collector, fabricated catalyst, market admission or automatic
  trade in this assignment.
- **Optional Dots coordination:** persist research task ID, input/model/policy
  hashes, status, evidence archive reference and explicit owner-review checkpoint;
  never portfolio/order authority or autonomous scheduling. A canonical Dots
  upstream/API/license is not pinned by this issue, so third-party integration is
  deferred rather than invented. The local receipt archive already supports
  manually resuming evidence review without another coordination framework.

## Next owner action / limitations

Review the new Draft PR and execute the fixed offline demo/tests. Then commission
only the bounded genuine local-adapter milestone above, with a pinned existing
runtime/checkpoint and independently verified license/resources. This is the next
implementation step, not approval to download weights, contact inference providers,
activate genuine market admission or operational trading.

No existing file changed: new loop, new tests/fixture, two synthetic demonstration
artifacts and this report only. Existing journal, recorder boundaries, S1/S2/S3,
source admission, clock policy, main, workflows and draft branches are preserved.
No installations, external inference, live provider/network diagnostics, credentials,
accounts, wallet access, paid APIs, additional spend, scheduled jobs, dispatch,
orders, deployment, merge, ZUMERAVO or other-project changes.

STOP FOR OWNER AND BOSS AI REVIEW.
