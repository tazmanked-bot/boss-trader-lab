# BOSS-TRADER-ISSUE-2-CCXT-EVALUATION

Assignment 007, 2026-11-05 UTC. Authorization: [Issue #8](https://github.com/tazmanked-bot/boss-trader-lab/issues/8);
acceptance: [Issue #2](https://github.com/tazmanked-bot/boss-trader-lab/issues/2).
**Recommendation: HOLD pending owner-run evidence. KEEP the current stdlib adapter operational.**
No concrete, verified benefit presently justifies a SWITCH proposal.

## Scope and observed baseline

Baseline main commit: `5c7b190f4657a9614491da8680c7d227ccb45d3a`.
The working `kraken_public_observer.py`, `boss_trader_lab.py`, existing Kraken
workflow and existing tests are unchanged. Research is optional and is not
imported by the scanner. No main branch change, scheduled scan, authenticated
call, execution capability, paid service or ZUMERAVO access is introduced.

The baseline uses one stdlib HTTP OHLC request per symbol, 12-second timeout,
no retry loop, and no third-party runtime dependency. It maps BTC to XBTUSD.
Its parser drops Kraken's documented unfinished final bar, rejects nonfinite or
nonpositive closes, rejects non-increasing timestamps, and permits up to three
hours' staleness. It returns closes only. It does not assert the response pair
key or hourly gap-free spacing; it also allows 60 seconds of close-boundary
slack. These are comparison observations, not changes or exploit claims.

## Candidate identity and source caveat

Reviewed candidate: **ccxt==4.5.92**, current PyPI release observed 2026-11-05,
uploaded November 4, requiring Python >=3.10, MIT license.
Evaluation target: CPython **3.11.17**, Ubuntu **24.04**, Linux x86_64.

- Wheel: `ccxt-4.5.92-py3-none-any.whl`, **6,830,983 bytes**.
- SHA-256: `004c4a9176700df6c5d4f8f7b2fd4691743040b70a2818c7afe1ad93021e62d4`.
- sdist SHA-256 (not built or installed):
  `5faa74fe17168ad8c21f34cc6286c7d771b68d0bca67ff595dcced62b98b46d5`.
- Authoritative metadata: https://pypi.org/pypi/ccxt/4.5.92/json
- Release: https://pypi.org/project/ccxt/4.5.92/
- Published provenance links source/workflow commit
  `44cc05f2dea6d7778debb05899eb0351bc444c27`.
- Reviewed source:
  https://github.com/ccxt/ccxt/blob/44cc05f2dea6d7778debb05899eb0351bc444c27/python/ccxt/kraken.py
- MIT notice:
  https://github.com/ccxt/ccxt/blob/44cc05f2dea6d7778debb05899eb0351bc444c27/LICENSE.txt

The published workflow commit's pyproject declares **4.5.91**, while wheel
metadata declares 4.5.92. The unprefixed 4.5.92 Git ref was unavailable (404).
Do not infer whole-source identity from the release label. The runner requires
the downloaded wheel's Kraken module to equal the inspected source digest in
`research/ccxt-candidate.json` (Git blob identity independently checked).
If it differs, remain HOLD and investigate; do not replace a digest just to pass.
PyPI displays provenance metadata, but cryptographic attestation verification
and complete source/build correspondence have not been performed here.

The inspected parser maps Kraken seconds to milliseconds, close from index 4
and volume from index 6. fetch_ohlcv uses public OHLC; its since conversion
subtracts one interval before filtering the unified result. It supports pagination,
but this evaluation explicitly disables it. Source rateLimit is 1000 ms.

## Dependency footprint and integrity

The candidate manifest records the full non-extra Requires-Dist list observed
in PyPI metadata, including platform conditions. It includes requests, certifi,
cryptography, typing_extensions, aiohttp, yarl, compression libraries, supported
event-loop/JSON/signing accelerators, and lower-level HTTP/CFFI dependencies.
Thus even synchronous OHLC use brings dependencies serving other capabilities.

Several requirements are ranges rather than exact pins. Source comments saying
all versions are pinned do not make that true. No exact resolved transitive
versions, aggregate installed size or security clearance is claimed before a run.

The optional evidence job:
1. Runs existing and new offline tests before network/package activity.
2. Downloads wheels only for CCXT 4.5.92 and its resolver-selected dependencies.
   Nothing downloaded is imported during this collection step.
3. Checks every wheel against exact-version PyPI filename/hash metadata, rejects
   yanked artifacts, checks wheel RECORD, collects license notices and source
   comparison evidence, and records compressed/unpacked sizes.
4. Creates an explicit `runtime.lock` containing every resolved version/hash.
   This is an **owner-run snapshot**, not a previously reviewed transitive lock.
5. Installs offline with `--require-hashes --only-binary=:all:` into an empty
   `--without-pip` venv; records pip's install report, pip check and installed
   byte/RECORD comparisons via the existing integrity helper.
6. Records dated OSV queries/responses for every resolved package and host
   pip/setuptools. API failures are UNVERIFIED; green is not security clearance.
7. Repeats tests in the installed environment before any optional market-data call.

Runtime notice obligations require retaining CCXT MIT copyright/permission text
and reviewing ALL collected dependency/bundled notices. PyPI's CCXT version JSON
reported an empty vulnerabilities array when inspected; that is a limited source
observation, not a comprehensive advisory scan. Native bundled components,
OS/CPython/Node, installer drift and unknown issues remain outside full coverage.

## Comparison contract

| Unified symbol | Baseline request | Required Kraken market ID |
| --- | --- | --- |
| BTC/USD | XBTUSD | XXBTZUSD |
| XRP/USD | XRPUSD | XXRPZUSD |
| SOL/USD | SOLUSD | SOLUSD |

Markets must be active spot, quote USD, no contract/swap/future/settlement.
Some spot markets advertise margin availability; no margin option is selected.
Unknown IDs fail for review instead of silently remapping to another market.

One fixed local UTC cutoff is captured per run. Raw seconds and CCXT milliseconds
are normalized to UTC seconds. Every row must have valid positive finite OHLC,
nonnegative finite volume, consistent OHLC bounds, and exact hourly alignment.
Rows must be strictly increasing and gap-free. The raw API must include its
documented current row; unfinished rows are excluded from comparisons. Neither
path may omit the latest completed UTC hour. This is stricter than baseline
freshness and the baseline 60-second slack, without changing the baseline.

The raw fixture/payload is also passed through the unchanged working parser,
and its entire close sequence must equal the strict parser's close sequence.
Compare ONLY overlapping closed timestamps, at least 21. Different leading
history lengths do not require equal overall counts. Missing interior/latest
bars are discrepancies, even if Kraken's general API can omit no-trade periods.

The close tolerance is `min(1e-8 USD, tick_size * 1e-6)`, based on explicit CCXT
TICK_SIZE precision. The inspected parser does not quantize prices; this permits
floating representation noise, not a half-tick price discrepancy. No tolerance
is learned from observed errors. OHLC and volume are validated for safety, but
the parity assertion compares close prices; full field-by-field parity is not
claimed.

At an hour rollover between sequential samples, the fixed cutoff can produce
a conservative failure. That is DATA_UNAVAILABLE/HOLD, never an invented price.
Local clock skew is a limitation; no server-time synchronization is claimed.

## Network safety and failure behavior

Only three CCXT capabilities are called: load_markets, market and fetch_ohlcv.
Transport guards permit HTTPS GET to api.kraken.com and only public Assets,
AssetPairs and OHLC paths; OHLC pair/interval parameters are allowlisted.
Non-public paths, credential headers, POST/body requests, other hosts and
redirects are blocked. No credentials are loaded or supplied by research code.
The library contains broader functionality, but it is not invoked.

CCXT timeout=12000 ms, enableRateLimit=True, retries=0, verbose=False.
A shared limiter spaces raw and CCXT requests at least one second apart, with
15 total requests maximum (12 CCXT maximum), no pagination and one sample per
pair. There is no retry or scheduled polling loop. Inherited proxy/TLS policy is
preserved. Public Assets/AssetPairs discovery adds calls and failure modes beyond
the stdlib OHLC-only baseline.

Any unavailable endpoint, CCXT exception, malformed payload, mapping mismatch,
gap, stale/future timestamp or comparison discrepancy exits nonzero and writes
DATA_UNAVAILABLE with exception TYPE only. Exception bodies/messages are not
logged. No partial successful result is returned as overall PASS, and there is
no synthetic price fallback. Saved raw public responses are evidence, not a
fallback data source.

## Offline tests and current evidence matrix

New dependency-free tests exercise all three mappings; malformed envelopes/rows;
NaN, infinity, negative/zero/invalid prices; duplicates, gaps, reordered, stale,
future and wrong-unit timestamps; exact UTC closed boundaries; insufficient and
missing current candles; contract/market mismaps; bounded rounding; no network at
import; allowed CCXT methods; redacted failures; redirect blocking and request
budgets. Fake exchange and payload functions ensure no real HTTP or installed
CCXT is required. Existing tests and fixtures remain unchanged.

Local verification: `python -B -m unittest discover -s tests -v` passed **56
tests** (36 existing + 20 new) without installing CCXT or calling live endpoints.
Python syntax checks also passed. These local results do not verify an installed
CCXT wheel or live Kraken availability.

| Check | Current result |
| --- | --- |
| Exact CCXT candidate/MIT metadata/published wheel hash | PASS, limited to inspected public evidence |
| Reviewed Kraken parser and API-only call design | PASS in source review |
| New offline safety tests | PASS locally; exact test count in PR/report |
| Installed CCXT behavior and full dependency inventory | HOLD pending owner run |
| Actual symbol IDs, 1h overlap and closed-price agreement | HOLD pending live public samples |
| Actual rate-limit/API availability behavior | HOLD pending owner run; deterministic failures tested |
| Complete provenance/license/security review | HOLD |
| Concrete benefit sufficient to switch production adapter | NOT ESTABLISHED; keep baseline |

## Owner execution without main changes

Only the research branch extends the already registered
`.github/workflows/manual-check.yml` with two optional boolean inputs and one
optional CCXT job. The existing offline job's contents remain unchanged.
Main and the working Kraken workflow remain untouched. The optional job pins
action SHAs, Ubuntu 24.04 and Python 3.11.17. Runner image/host installer can
still change. There are no schedules, secret inputs or write permissions.

After reviewing the draft, the owner can dispatch the registered workflow using
the research branch ref; no main merge or new default-branch launcher is needed:

```sh
gh workflow run manual-check.yml \
  --repo tazmanked-bot/boss-trader-lab \
  --ref research/issue-2-ccxt-kraken-comparison \
  -f ccxt_evaluation=true -f ccxt_live=false
```

Review/download the lock, exact dependency versions, notices, OSV coverage and
installed identity first. Artifacts have one-day retention. If acceptable, a
second owner-triggered run with `ccxt_live=true` requests only public Kraken
data. Its newly resolved snapshot must also be reviewed; no claim of identical
resolution across runs is made until a reviewed transitive lock is committed.
The comparison entry point requires an explicit --live flag and never runs at
import. No workflow was dispatched by Codex.

Cost/complexity: stdlib has no third-party install, while CCXT adds a 6.8 MB
primary wheel plus native/async/HTTP dependencies, resolver/integrity/security
work, extra discovery calls and minutes/artifact usage on public GitHub Actions.
Actual aggregate size, duration, API success and quota usage need evidence.
No paid service is needed or configured, and no paid capacity is authorized.

Smallest safe owner action: inspect the draft and run the dependency-only command
above. Keep the existing scanner. Only propose SWITCH if later concrete evidence
shows a needed benefit outweighing dependency and operational complexity.
Do not merge, close Issue #2 or activate strategies. STOP FOR OWNER/BOSS AI REVIEW.
