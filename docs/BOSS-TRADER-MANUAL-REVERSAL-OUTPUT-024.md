# BOSS-TRADER-MANUAL-REVERSAL-OUTPUT-024

Issue: https://github.com/tazmanked-bot/boss-trader-lab/issues/43
Baseline: aa360920641d25eb8ef33e9a5c75f126df35eba6

## Verdict

PASS for the offline integration and its deterministic safety tests. HOLD for genuine live source admission and operational reversal output. This branch cannot perform market requests, even if a user supplies an approval flag: there is no real transport, independent UTC provider, or active live workflow.

The existing manual close-only observer remains AVAILABLE in its established OBSERVE_ONLY scope. It and its workflow are unchanged. Its three independent per-symbol calls, continuation after individual failures and 12-second socket timeout are not evidence that the proposed full-history reversal coordinator meets its stronger requirements.

## Changes and practical output

Three new files only:

- research/manual_kraken_reversal_024.py
- tests/test_manual_kraken_reversal_024.py
- docs/BOSS-TRADER-MANUAL-REVERSAL-OUTPUT-024.md

The integration consumes six sealed, bounded in-memory synthetic HTTP responses: identity then hourly OHLC for BTC/USD, XRP/USD and SOL/USD. It connects the existing correction supervisor, HTTP parser and global-stop coordinator to the existing source/clock checks, identity validation, OHLCV bridge, refusal registry and original candidate features. It does not relabel the prior preview as a verified live producer or substitute new scanner formulas.

Run from the repository root:

```sh
python -B -m research.manual_kraken_reversal_024
python -B -m research.manual_kraken_reversal_024 --offline-demo
python -B -m unittest tests.test_manual_kraken_reversal_024 -v
python -B -m unittest discover -s tests -v
```

Default execution exits 2 with AUTHORIZATION_MISSING, BLOCKED and zero requests. The explicitly selected offline demo exits 0 and returns three synthetic WATCH candidates ordered BTC/USD, SOL/USD, XRP/USD, each scoring 26666. It consumes six fixtures and makes zero actual network requests. Tests also exercise zero, one and two candidates and WAIT/BLOCKED outputs. Three WATCH outcomes from invented candles establish no market signal or profitability.

The immutable demo input is tests/fixtures/kraken_reversal_groundwork_022.json, 34697 bytes, SHA-256:
761c171e090bcfc14c8ab87ea4ce3a20b8278aa01b6445e0871438dc4fc8285b.
The loader accepts only that fixed packaged file, verifies its digest and bounds its read. No arbitrary input path or live CLI option is provided.

Phone-oriented JSON labels the source STATIC_SYNTHETIC_KRAKEN_HTTP_FIXTURES, the mock clock and synthetic capture time, fixture-only closed prices, source status and refusal reasons. It includes WATCH/WAIT/BLOCKED, score/features, why-early/invalidation, unverified catalyst, candidate count, actual requests and fixture attempts. Overall, live admission and operational readiness remain HOLD; trade authority is NO ORDERS. Source identity is never promoted to KRAKEN_PUBLIC_SPOT.

## Validation and bounds

The fixed modeled request manifest uses api.kraken.com public AssetPairs and OHLC paths, interval 60 and the frozen cutoff minus 86400 seconds. It is a request description, not an executed call. Six stages maximum, no retry or fallback. Exact identity, quote, aliases and supported metadata must pass the existing validator; unknown expanded schema is refused pending review.

Every stage retains the existing absolute 10-second deadline, including validation, and existing 250-ms cleanup allowance. The fixture coordinator additionally bounds total modeled processing to 60 seconds; the demo's 70-second synthetic clock lease is test setup, not permission to change a genuine clock policy. Existing uncertainty limit of two seconds remains intact.

Existing narrow parser limits remain in force: 8192-byte headers, 1024-byte header lines, 64 fields, 262144-byte body, Content-Length framing, bounded chunks and 512-row limit. Redirects, API errors, ambiguous framing, compression, malformed UTF-8/JSON, duplicate keys and non-finite numbers refuse. Source errors stop later stages and withhold all partial candidate output. Receipts preserve the reached stage and refusal without raw response bodies.

The bridge and registry require complete validated hourly history, at least 21 closed candles and strict ordering/continuity. All OHLCV values, VWAP and trade counts are checked. No volume is inferred from closes. The initial capture cutoff is frozen; the current candle is excluded using existing clock uncertainty semantics. Commitments and canonical normalized data must agree before the unchanged shared feature function runs. Registry score rules, conjunction, tie order and maximum three candidates remain unchanged.

The decision evidence digest covers cutoff, decisions and candidates. Altering ignored current-row prices cannot change those causal decisions. Raw transport receipts, byte counts and timings can legitimately differ; the entire report is not claimed invariant. A malformed future timestamp or invalid source remains a refusal, not a usable no-lookahead sample.

Late time expiry, invalid/non-finite feature output or expiry during output hashing discards prepared WATCH results and decision evidence. Serialized output is capped at 32768 bytes; the phone report is tested below 16 KiB on the demo.

## Verified local evidence

Python 3.12.14; standard-library offline execution, no packages installed.

| Check | Result |
| --- | --- |
| Focused command above | 37 tests, 0.188 seconds, OK |
| Full discovery command above | 384 tests, 4.863 seconds, OK; no skips |
| Default CLI | exit 2, BLOCKED, zero requests |
| Offline demo | exit 0, six fixture attempts, zero requests, three synthetic WATCH |
| Live CLI option | rejected |
| Existing scanner/observer/workflows | unchanged |

Tests cover canonical parity with existing features, 0–3 selection, ranking/ties and volume WAIT; each of the six failure positions; global stop and partial-result suppression; strict HTTP/JSON limits and API-error redaction; market identity and unknown metadata; clock uncertainty, lease, monotonic reversal and service Date; never-ready/unreaped/no-payload jobs; slow factory/start and validation deadlines; invalid OHLCV, gaps, duplicate/unsorted rows, warm-up and commitments; current-row invariance; late feature/hash expiry; non-finite feature output; deterministic formatting and default refusal.

Tests guard socket creation, DNS, urllib/HTTPS, subprocess execution and wall-clock access. The import/default path additionally rejects file reads. Demo reading is limited to the fixed synthetic fixture. No genuine market data or real market request was used.

Full-suite integration initially exposed a stale cached enum after existing tests reloaded the corrections module. Dynamic module lookups and an explicit reload regression correct that defect; the figures above are the final successful runs.

## Remaining B1–B5 evidence and limitations

| Area | Current finding | Required before a genuine producer |
| --- | --- | --- |
| B1 network bounds | Offline malformed-stream and refusal evidence only | Actual bounded DNS/connect/TLS/read behavior and target-runner evidence |
| B2 cancellation/reaping | Existing supervisor exercised with deterministic jobs | Genuine isolated worker termination, reaping and resource measurements |
| B3 integration/identity | Raw fixtures traverse parser through original decisions | Real bounded transport and payload handoff, verified actual Kraken identity/schema |
| B4 trusted clock | Mock evidence only; genuine strict-clock NO-GO | Independently anchored UTC evidence with conservative uncertainty at most two seconds |
| B5 target runner | No measured hard runner guarantees | Target-specific startup/deadline/cleanup/memory evidence |

SynchronousFixtureJob is explicitly a TEST job. It cannot preempt a blocking action or prove process isolation, TLS, OS cleanup or a real absolute network deadline. Payload handoff uses local memory; a real worker IPC design is absent. Static bytes have already been allocated by the caller, so parser bounds do not establish target RSS limits. Fixtures cannot establish real schema availability, freshness, pair status or independent UTC accuracy. No successful synthetic receipt clears these gaps.

If the intended runner cannot supply the strict UTC or process guarantees, preserve HOLD for the proposed producer and retain the existing narrower close-only OBSERVE_ONLY operation. The historical-data-only alternative remains a separate unactivated proposal; this change adopts neither policy.

## Acceptance and smallest owner decision

Stage A: independently inspect the three-file diff and run the focused/full offline commands against the exact PR head SHA. Record the tested SHA, Python version, full test counts, no skips, module/fixture hashes, disabled default and explicit demo with six fixture attempts and zero network requests. No workflow was added or dispatched by this assignment. A green workflow alone is insufficient without the actual logs and head reference.

Smallest safe owner action: authorize that pinned offline verification and review this Draft PR. Keep live source admission HOLD. This head does not contain a genuine driver that can be activated.

Any Stage B needs a separately reviewed implementation/head and fresh Stage A evidence, explicit bounded single-shot owner GO and independently supported B1–B5 evidence. Freeze exact approved symbols, request count, identity/schema and limits before execution. An initial BTC-only two-request identity/OHLC experiment could be proposed separately; three symbols would require the explicit six-request manifest. No experiment or workflow dispatch is authorized or performed here. Any failed source must yield refusal rather than a market WATCH.

A future verified producer must distinguish actual source observations from calculated research decisions, label capture/cutoff and freshness evidence, retain catalyst UNKNOWN and NO ORDERS, and show zero candidates where warranted. An unknown schema must return for review rather than be dynamically accepted.

README policy remains applicable: individual users are responsible for their own provider data-use rights. This assignment introduces no blanket licensing gate.

No real Kraken requests, keys, scheduled monitoring, trading, orders, Kraken CLI, Binance Agent OS, scanner modification, merge or ZUMERAVO access. STOP FOR OWNER AND BOSS AI REVIEW.

