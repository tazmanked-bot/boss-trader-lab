# BOSS-TRADER-REAL-KRAKEN-BTC-TRANSPORT-025

Issue: https://github.com/tazmanked-bot/boss-trader-lab/issues/45
Inspected main: d43b54981d87cdf2dd28c35b1af6c258ab4e05e5 (owner merge of PR #44).

## Result and scope

OFFLINE TESTED: a raw public-request algorithm, a real POSIX isolated child, fixed-size result framing, preallocated header reads, strict source validation and BTC-only identity → OHLC sequencing.

Operational verdict: HOLD. B4 is NO-GO. No authentic Kraken transport invocation, production DNS/socket/TLS provider, independent UTC verifier or live admission switch is installed. The callable dependencies are explicitly trusted controlled TEST code. The process is isolation for blocking operations, not a hostile-code security sandbox.

The implementation is research/kraken_btc_transport_025.py; new tests are tests/test_kraken_btc_transport_025.py. This document is the third added file. Existing code, tests and workflows remain unchanged, including the available manual close-only observer, 024 synthetic pipeline, registry and reversal calculations. No reversal feature function is called by this prototype.

## Concrete transport and process boundary

manifest() fixes the authority to api.kraken.com:443 and exactly these modeled GETs:

1. /0/public/AssetPairs?pair=XBTUSD&aclass_base=currency&info=info
2. /0/public/OHLC?pair=XBTUSD&interval=60&since=<frozen-cutoff-hour minus 86400>

The cutoff is UTC minus the conservative uncertainty. Only the since parameter is rounded down to an hour to meet the existing Request validator; OHLC eligibility uses the original frozen cutoff. Both requests validate before DNS. No caller hostname, URL, endpoint, symbol, conversion, credentials or auth fields are accepted. observe_offline() reserves at most two attempts, with no retry; verified identity is required before creating the OHLC worker. Any failure globally stops. Counters distinguish two modeled offline attempts from zero actual requests. There is no real-run counter or invocation in this revision.

exchange() executes explicit DNS → one selected global IP → connect → TLS handshake with exact SNI → fixed GET → raw recv_into. It requires hostname/certificate checking and TLS >=1.2, advertises only HTTP/1.1 and rejects negotiated h2. One selected IP only; no address fallback. Private, loopback and link-local selected addresses refuse. Tests use a dummy global IP solely as an assertion value, never a destination. No environment proxy/mirror discovery occurs. There is no installed real direct-network or proxy adapter; this code is not permission or a means to bypass the Cloud network policy. Any future real adapter must also satisfy the owner's network policy; a conflict means STOP.

read_wire() allocates an 8192-byte header buffer before the first read. Header reads use one-byte memoryviews; lines are limited to 1024 bytes. Existing strict parser validates all headers before body allocation. Body allocation is exactly the approved Content-Length, maximum 262144 bytes; recv_into views are at most 4096 bytes. One extra byte checks EOF after Connection: close; a peer that never closes times out. There is no buffered HTTP parser, chunked response, EOF-length body, compression, redirect, interim response or duplicate-header acceptance. Existing 64-field and strict JSON checks apply. Unsupported legitimate responses deliberately BLOCK. Header/body copies and parsed JSON have bounded input sizes but are not a measurement of OpenSSL/kernel RSS.

isolated_exchange() is an actual single-thread POSIX fork implementation, not 024's synchronous test job:

- The monotonic 10-second maximum stage deadline begins before allocation, pipes and fork. Parent and child check it before release, DNS, connect, handshake, send, reads and return.
- The child creates its own session, closes inherited descriptors except two control pipe descriptors, applies limits and announces readiness. Parent sends a one-byte release only before expiry. Native allocation/fork and kernel scheduling cannot be preempted by these Python checks; an expired startup never grants release.
- Child limits: RLIMIT_AS at most 512 MiB, RLIMIT_NOFILE 32, RLIMIT_CORE 0, RLIMIT_CPU 11 seconds; lower inherited hard limits stay lower. CPU limit is a secondary backstop, not the wall deadline.
- Results use fixed anonymous mmap of 270500 bytes, inherited without a pickle channel. Payload cap 270464 bytes, four-byte length and SHA-256 checksum. Parent requires a valid frame, zero unused tail, supported type/error code and normal child exit. The checksum detects corruption; it is not an authentication boundary against trusted injected Python.
- Small pipes carry ready/release only. A 100KB result test exceeds ordinary pipe capacity without blocking result delivery.
- On failure the parent sends SIGKILL and waits for the exact PID, with a 250ms cleanup budget. Actual local tests confirm that killed children are reaped. An unreapable worker produces WORKER_UNREAPED and stops; cleanup success is never fabricated. No retry follows. Uninterruptible kernel states can exceed these budgets or prevent timely reaping, so no hard target latency guarantee is claimed.
- The child receives no CLI URL, shell command, keys or arbitrary serialized objects. There is no subprocess shell and no automatic network/provider construction. Factory callbacks are trusted test dependencies and could themselves execute arbitrary Python; this is not a sandbox for untrusted callbacks.

Child setup failure prevents readiness/release and fails closed (currently WORKER_INVALID). Unsupported platform/thread configuration also refuses. FD closure assumes inherited descriptors lie below the observed soft descriptor ceiling; that assumption needs target measurement or a stronger OS allowlist before production use. An address-space cap bounds virtual mappings after setup, not pre-fork parent memory, startup RSS, total process-tree RSS, TLS/kernel allocations or scheduler/kill latency. Those unresolved resource conditions explicitly prevent production admission.

## Source, time and operator handling

Existing pinned baseline validation is reused, not rewritten:

- research/kraken_spot_diagnostic.py: Request.target, _identity, _commitment, _strict_json and _date.
- research/kraken_probe_corrections.py: strict header/JSON parser and constants.
- research/kraken_spot_reversal_bridge_prototype.py: exact seven-field identity profile, normalization/parity and existing policy.
- research/kraken_spot_validation_bridge.py and research/spot_refusal_registry.py: eight fields, USD spot identity, OHLCV/VWAP/count constraints, complete consecutive eligible hourly history and 21+ bar warm-up.

Unknown actual expanded Kraken identity/schema remains BLOCK pending review. No closes are converted into volume or OHLCV. The unfinished final candle is excluded; changing its prices does not change the validated observation. Invalid projected row structure, missing current commitment, short/gapped/stale/duplicate closed history, source/API errors and service Date conflicts refuse. No raw API error text leaks into output.

SyntheticUTC is explicitly a test coordinate. A dictionary saying trusted=True cannot satisfy it or B4. HTTP Date is only a consistency check against that coordinate. Real monotonic time controls worker timeouts; it is not UTC. The synthetic fixture clock is frozen for the two-stage test and is not a viable live capture/elapsed-uncertainty implementation.

The default CLI:

```sh
python -B -m research.kraken_btc_transport_025
```

returns exit 2, BTC/USD BLOCKED, AUTHORIZATION_MISSING, source NOT_ADMITTED, clock B4_NO_GO, zero attempts/requests and NO ORDERS. Import/default creates no worker, network request, file read or clock sample. CLI rejects live flags, URLs and key arguments.

Controlled test integration produces:

BTC/USD • OBSERVE_ONLY • OFFLINE_SCHEMA_PASSED • CONTROLLED_OFFLINE_DEPENDENCIES_NOT_MARKET_DATA • clock B4_NO_GO • 21 completed 1h candles • as_of 1900000800 • synthetic capture UTC 1900000802000000000ns ±2000000000ns • 2 offline attempts / 0 actual requests • OFFLINE_BOUNDARY_PASSED_LIVE_HOLD • NO ORDERS.

This is invented fixture data, not an authentic live observation or a market signal. No WATCH, candidate list or trading permission can be emitted by this module. A future genuine manual report must retain source/identity/clock validity, completion count, cutoff/capture evidence, request counts and refusal, using OBSERVE_ONLY or BLOCKED until independently permitted. Existing reversal admission HOLD remains intact.

## B4 independent-clock design — NO-GO

No available verified independent UTC source was supplied. time.time(), a mock provider, HTTP Date, an unproven NTP offset or a boolean marker do not solve this.

A concrete future design would provision a pinned-key authenticated UTC authority, independently justified accuracy/error bounds and replay protection. A challenge-response envelope must bind nonce/run, exact code revision, boot identity, UTC interval, monotonic receipt interval and expiry. Trusted local receipt timestamps and conservative request/response transport-delay bounds must widen the authority interval, not assume symmetric network latency. Uncertainty propagated through capture/processing must remain <=2s initially and within an explicit lease. Monotonic rollback, reboot/suspend ambiguity, stale or reused envelopes, missing signatures or inadequate uncertainty must refuse.

The signature verifier, authority trust provisioning, boot binding, measured local timestamp path, delay/error bounds and runner lease are absent. Python's standard library does not supply the proposed public-key verifier; no cryptography dependency or authority was installed or invented. Authenticated NTS could be investigated only with verified trust bootstrap and error provenance; protocol authentication alone would not demonstrate the required bound. No service was contacted. This is a design proposal, not a working clock adapter. B4 remains NO-GO and the delayed historical alternative is not adopted.

## Evidence matrix

| Blocker | Independently supported in this assignment | Remaining live/target condition |
| --- | --- | --- |
| B1 | OFFLINE TESTED: one shared monotonic budget, 10s maximum, launch/release gates, real child killed during controlled DNS/connect/TLS/read hangs, fixed manifest, no fallback | UNKNOWN: actual resolver/TLS/proxy behavior and non-preemptible startup/kernel latency. Hard total wall guarantee not established |
| B2 | OFFLINE TESTED: real child/session, descriptor cleanup, applied resource limits, preallocated headers, fixed mmap framing, corruption rejection, exact PID reap and parent FD cleanup | UNKNOWN: total RSS including parent/TLS/kernel, target FD assumptions and hard kill/reap bounds. RLIMIT_AS is not RSS |
| B3 | OFFLINE TESTED: identity-first global STOP, 429/451/API/TLS handling, exact source schema, full-history bridge and no-lookahead | UNKNOWN: actual Kraken schema/status/availability, authentic provider composition and live capture evidence. No live admission |
| B4 | NO-GO: independent UTC authority and verifier absent | Required independent trust, freshness, boot/run binding and <=2s initial uncertainty unverified |
| B5 | OFFLINE TESTED locally on Linux 6.18.57 x86_64 / Python 3.12.14 | UNKNOWN on the owner's intended deployment image; no target-runner measurements made |

## Exact local tests and verification

```sh
python -B -m unittest tests.test_kraken_btc_transport_025 -v
python -B -m unittest discover -s tests -v
```

Final focused: 35 tests in 0.976s, OK.
Final full suite: 419 tests in 5.892s, OK, no skips.
Python 3.12.14; no packages installed.

New adversarial tests cover import/default/no file/network/worker, CLI refusal, exact host/path/parameters/header bytes, bad symbol/private endpoint, proxy-environment independence, DNS address refusal/no fallback, TLS policy/errors/ALPN, all blocking phases, decreasing total budget and monotonic rollback, 429/451/redirect, malformed/oversized headers, duplicate/TE+CL/compressed framing, premature EOF/trailer, invalid UTF-8/NaN/overflow/duplicate JSON, large result IPC, actual child session/limits, inherited FD closure, expired startup, resource setup failure, exact killed-PID reap, simulated unprovable reap failure, corrupt shared frame, identity/status/quote/unknown schema, UTC/Date refusals, eight-field violations, stale/short/gapped/duplicate history and unfinished candle exclusion.

Guards replace real socket creation/DNS, urllib/HTTPS, subprocess and wall-clock calls, including inherited guards in forked workers. Controlled dependencies use bytes/memoryviews; genuine network primitives never run. Import/default also guard file reads, fork and monotonic sampling. The fake unreapable test actually reaps the local child before reporting the modeled failure, avoiding leaked test workers. Local hang tests require completion under one second for a 100ms modeled budget; this is a local regression criterion, not a target worst-case claim.

The initial focused run caught a cached SyntheticUTC test object invalidated by import-reload; the test now constructs the current class explicitly. Final counts above are successful runs. Existing tests were not edited.

## Exact target and smallest owner action

The working observer's existing .github/workflows/manual-kraken-observation.yml selects ubuntu-latest and Python 3.11; these are mutable labels, not an exact runner identity. The prior pinned-offline launcher for PR #44 selects ubuntu-24.04 / Python 3.11.17. Neither establishes a target image for a future real transport. B5 cannot be called cleared from this local container.

Smallest safe owner action: independently review the three-file diff and execute the two offline commands on the exact Draft PR commit using an owner-approved Linux single-thread process environment. Record commit SHA, file hashes, Python build, kernel/architecture, immutable image identifier, runner image release, cgroup limits and runtime policy. An offline Ubuntu 24.04/Python 3.11.17 job is a reasonable compatibility target, subject to owner selection; no workflow is created or dispatched here.

Additional owner-run offline acceptance should record monotonic startup-to-ready/release, per-phase injected block times, deadline overshoot, forced-kill-to-reap time and exact PID, parent/child peak RSS and cgroup total memory (including TLS), FD baseline/peak/cleanup, maximum result length and resource-setup failures. Test under constrained memory/load and refused capabilities, with no skipped safety tests. Any unreaped process or missing hard containment is STOP. Sample timing maxima do not alone prove hard guarantees; an OS containment contract and measurements are both needed.

Keep live invocation HOLD after that verification. Next implementation decision is whether the chosen runner can furnish total-memory/worker containment and independently trusted UTC; if not, retain the working close-only observer's established OBSERVE_ONLY scope and stop promotion. Genuine adapter composition, clock proof and any public BTC two-GET experiment require separate review and explicit owner authorization. No current head can be enabled merely by a live flag.

No real Kraken request, network diagnostic, keys, scheduled scan, workflow change/dispatch, installation, live admission, scanner modification, order, merge or ZUMERAVO access occurred. README individual-user data-rights policy is preserved with no new blanket restriction.

STOP FOR OWNER AND BOSS AI REVIEW.

