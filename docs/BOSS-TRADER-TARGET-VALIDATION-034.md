# CODEX 034 — Genuine AI Analyst target-validation preparation

Issue #63; owner preparation approval 2026-11-28 (Asia/Taipei).
Baseline Draft PR #62: `2fd237d9f19355a68a23ed7f5a13be1cd8b058cf`, verified
unchanged and unmerged. Separate branch `research/issue-63-target-validation`,
stacked Draft PR targeting `research/issue-61-offline-llama-adapter`.
README/SECURITY, #63, #62 and CODEX 033 code/evidence reviewed; no AGENTS.md in
baseline tree. Prior PRs and existing files are not changed.

**REAL_NOT_RUN; genuine inference HOLD.** No owner desktop access, actual model
execution, AEP environment edits, recorder access, downloads, installations,
deployment, merge or additional spending. Working passive tools and synthetic
results are delivered; no claim that the target has been validated.

## Run the delivered software

```sh
python -B -m research.target_validation_034
python -B -m research.target_validation_034 --reported-evidence
python -B -m research.target_validation_034 --synthetic-demo
python -B -m research.recorder_snapshot_034
```

Defaults are idle and do not open target files/databases or create subprocesses.
The synthetic demo creates only temporary invented sentinel files and a SQLite
test DB, uses existing CODEX 032 numerical/risk contracts and CODEX 033 preparation,
then removes its temporary fixtures. It never runs an executable or model.

[Actual synthetic demonstration](artifacts/target-validation-034-synthetic-demo.json):
private copy operations planned with **zero copy writes**, a proposed **64-token**
profile with real activation DISABLED, all-positive simulated containment claims
still nonauthoritative, failed canary positive control explicitly missing, and
fresh ingestion of old candles correctly classified **STALE**, with two possible
delayed/backfilled rows. It contains no target paths/data or real model metrics.
A /tmp-based demo may also report writable-ancestor holds; it is not proof of a
secure private runtime directory. No checker silently fixes those permissions.

## Reported target versus independently established facts

| Item | Evidence class / state |
| --- | --- |
| Debian x86_64; Ryzen 3 2200G AVX2/FMA; 2 vCPU | Owner reported; not measured here |
| RAM 5.8 GiB, available 5.5 GiB | Reported snapshot, not a current resource guarantee |
| GGUF 1117320736 bytes | Reported; actual target file not read |
| GGUF SHA-256 `6a1a2eb6d15622bf3c96857206351ba97e1af16c30d7a74ee38970e434e9407e` | Reported fingerprint, independently sourced expected hash UNKNOWN |
| CLI 1424080 bytes | Reported; actual target file not read |
| CLI SHA-256 `daa63b89ca47f511403ad31f23d4fa9b907713a27d4d7dfa6cd01fe872a7a5c2` | Reported fingerprint, independently sourced expected hash UNKNOWN |
| llama.cpp source `0978a6e9022fb9bd6874b86154ee304e81929b9f` | [Commit existence independently checked upstream](https://github.com/ggml-org/llama.cpp/commit/0978a6e9022fb9bd6874b86154ee304e81929b9f); binding to installed binary/build/libs remains UNKNOWN |
| ldd resolves all reported dependencies | Reported capability; actual closure, resolved paths, pins/permissions UNKNOWN |
| `unshare --user --map-root-user --net -- true` exit 0 | Reported capability only; not filesystem/network/process containment proof |
| Recorder service resumed | Reported; current DB freshness UNKNOWN |
| Desktop failure root cause | UNRESOLVED; no claim that model load caused or repaired it |

[Manifest template](../research/target_validation_034.manifest.example.json) records
reported hashes separately from null independent expectations and explicit unknowns.
Adapter hash fields reproduce reported fingerprints only; filling them cannot grant
integrity, licensing or execution clearance. No artifact digest is derived from a
source commit, filename or local repetition of the reported checksum. Obtain a
reviewed publisher/release checksum or independently reproducible build/convert
record where available; otherwise keep expected hash/source UNKNOWN. Source-code
existence is not binary reproducibility. Inspect exact model/base/conversion and
runtime/library licenses; the repository MIT license does not grant those rights.

## Private hardened runtime copy plan — preserve AEP originals

The passive `copy_plan` function and `--copy-plan local-copy-inventory.json` inspect
only explicit files under a reviewed source root and produce operations. They
never copy, chmod, relink, execute ldd, modify environment settings or create the
destination. Local inventory shape is the template's `copy_inventory` object:

```sh
python -B -m research.target_validation_034 --copy-plan local-copy-inventory.json
```

Owner-side procedure, with no edits to AEP originals:

1. Inventory the CLI, ELF interpreter, DT_NEEDED/RPATH/RUNPATH and complete resolved
   shared-library closure using existing passive tools/documentation. Existing
   `readelf -l` / `readelf -d` can inspect reviewed ELF files without executing
   the target. Do not treat reported ldd success as a full authenticated inventory
   or automatically run ldd on untrusted executables. If tools/inventory are
   unavailable, HOLD; no installation authorized. Include system libraries and
   every versioned SONAME target, not just libllama's visible alias.
2. Record literal symlink spelling and final real paths, mode/owner/ACL information,
   sizes and hashes for each file. The planner checks literal/resolved ancestors
   for group/other write bits, regular-file type/size/hash and change during read.
   Relative symlink chains are preserved in the operation list and resolved
   targets are copied as regular files. Missing/escaping/absolute links or
   dependencies outside the declared source root refuse for review; nothing is
   silently dereferenced into AEP. Use a separately reviewed inventory/root for
   OS libraries rather than pretending the custom-runtime root contains them.
3. Choose a NEW private destination unrelated to AEP/recorder paths. Overlap or an
   existing destination refuses. Planned root/directories 0700, runtime 0500,
   libraries/model 0400, owned by the intended isolated execution user. The tool
   checks existing destination ancestor write bits but does not authenticate UID,
   ACLs, mount behavior, capabilities or complete dynamic dependency closure.
   Those remain owner checks; report holds rather than chmod AEP/source parents.
4. Only after reviewing the plan, the owner may create the new private directory
   and manually copy **only inventoried files**, preserving relative symlinks
   (e.g. reviewed `cp -P`/`cp -a` for those individual paths). Do not recursively
   copy an AEP/home/recorder tree or secrets. Create needed private parents first,
   inventory/deduplicate SONAME targets, then rehash every copied regular file.
   Audit that every preserved link resolves inside the intended private bundle
   before applying private modes. Never chmod a link that resolves to an original.
5. Do not set global LD_LIBRARY_PATH, change AEP's wrapper/profile, patch originals,
   restart services or replace libraries in place. Check whether the copied CLI's
   loader/RPATH uses private `$ORIGIN` paths; an absolute AEP dependency is a HOLD,
   not permission for hidden fallback. Any private rebuild/RPATH change needs its
   own digest/build record and review. Model copy has a separately inventoried
   source, with its own provenance and permission checks; do not assume it shares
   the CLI tree or rewrite absolute symlinks without an explicit revised plan.

The planner's expected-source text is a provenance record, not an authenticated
signature. Even matching all recorded expectations leaves dependency closure and
target containment HOLD. It is not a complete ELF loader auditor or protection
against concurrent filesystem replacement; rehash/freeze private copies on the
qualified target. No actual hardened copy has been made here.

## Offline containment verification plan — no recorder/SSH effects

The exact checklist lives in `target_validation_034.CHECKS`. A receipt binds to
the proposed manifest/prompt/schema/resource scope SHA-256. Synthetic and owner
reports are labeled SIMULATED_ONLY / OWNER_REPORT_NOT_INDEPENDENT_ATTESTATION.
Wrong scope, missing/extra checks and nonboolean check values refuse. Even all true
claims cannot activate the adapter. Reported namespace capability alone satisfies
none of these independent containment requirements.

Owner validation must use a disposable **child-only** profile/namespace/cgroup
already supported on target. Do not change host routes, firewall, resolver,
SSH namespace, system cgroups, AEP settings or recorder service. No installs or
privileged global repair to get a passing check. A real qualified isolation wrapper
is not supplied/claimed by this PR; if the existing target cannot provide it, HOLD.

Exact canary protocol for a later approved owner containment check, with no model:

1. Reserve owner-controlled ephemeral loopback TCP/UDP canaries in a separate test
   session, never on SSH/recorder ports. From the parent, verify IPv4 and IPv6 TCP
   connection and a UDP synthetic DNS-like echo/response work. Record a positive
   control immediately before and after each denied child check; a dead listener
   is not containment. No public DNS/exchange/provider endpoint is contacted.
2. In the disposable child profile only, verify namespace identity differs from
   the parent and that no nonloopback interface/default route/host socket is
   exposed. Attempt only the known parent loopback canary addresses/ports with
   short deadlines: IPv4 and IPv6 parent connections and UDP echo response must
   fail, and the canary must observe no child packet. A UDP send returning success
   is not evidence of DNS access or denial. Verify the actual resolver/socket
   policy separately; do not edit the host resolv.conf or contact a real resolver.
   If required, use only a private child resolver configuration/canary, removed
   with the child. One user/net unshare success does not prove this profile.
3. Bind/mount only read-only inventoried private runtime/model/libs plus synthetic
   prompt. Test denial of reads of synthetic private-host canary files, AEP/home/
   recorder paths and credential locations by mount visibility/policy; do not read
   actual secrets. Test writes against copied runtime/model fail, while private
   scratch is the only permitted writable area. The AEP originals are never a
   write-test target. Check mount propagation is child-private.
4. Use a controlled fake worker to verify process-tree termination/reaping, timeout,
   descriptor policy, cgroup memory/CPU/swap limits and one-worker concurrency.
   Parent wait/PID namespace capability is insufficient proof of escaped descendant
   containment. Record failed/unknown controls and leave model execution disabled.
5. Confirm pre/post SSH and recorder health using existing owner observation tools,
   without stop/restart/reconfiguration or new monitoring. No service-control code
   exists in these tools. If desktop health/recorder freshness is unknown or any
   test affects them, stop and retain HOLD. Keep private paths/PIDs/logs local;
   publish only redacted conclusions and evidence references.

These are owner instructions, **not target tests executed here**. The code performs
no connection attempts, unshare, mounts, cgroup writes, canary service creation or
external/provider calls. Booleans in a JSON receipt are not independent attestation,
boot/run binding or a substitute for logs/measurement and owner review.

## Bounded first-inference protocol — future separate owner GO only

After private artifact review and qualified containment, prepare a synthetic request
using the CODEX 033 runbook and fill a LOCAL adapter manifest. The exact object is
the template's `adapter_manifest`, not the whole template. Then:

```sh
python -B -m research.target_validation_034 --first-plan local-adapter-manifest.json --request new-synthetic-request.json
```

This hashes/validates local supplied files and reuses CODEX 033 compact evidence,
prompt, grammar and command preparation. It **does not execute** the CLI. Proposed
profile: CPU only, GPU layers 0, **2 threads**, context **2048**, maximum **64 output
tokens**, 30s application timeout, 1s cleanup allowance, one process, 8192 combined
stdout/stderr bytes. Existing 4 GiB address-space/30s CPU/32-FD/zero-core/zero-file
limits are retained in the proposed scope. The required NEW PRIVATE cgroup profile
adds memory max 3 GiB, swap max 0, CPU quota at most one vCPU (still two threads)
and nice +10. These are **planned requirements**, not cgroups configured here and
not proven safe for a reported 5.8 GiB machine. Reported free RAM is not a live
reservation; recorder/SSH headroom must be checked independently before any GO.
No system-wide cgroup or recorder scheduling change is permitted.

TargetAnalyst is contract-compatible preparation but `infer` always refuses with
REAL_NOT_RUN_TARGET_VALIDATION_AND_SEPARATE_GO_REQUIRED. There is no activation
flag or identity/manifest shortcut. Actual execution requires a separate authorized
follow-up with the qualified executor, frozen scope hashes and redacted evidence;
the old CODEX 033 512-token profile is NOT this first-attempt authorization.

The first probe uses synthetic evidence only, a minimal environment without secrets,
no tools or external text instructions, no network/download fallback and strict
`analyst-v1` parsing. `validate_first_output` rejects incomplete, duplicate, extra,
wrong-reference or missing-objection responses using the existing validator.
**64 tokens may truncate the complete analyst-v1 response.** Such a result is an
honest failed output-validity measurement and must remain BLOCKED; never remove
required references/objection, repair/retry the output or silently raise the cap.
The deterministic original risk veto and BUY AUTHORIZATION NONE remain final.

Latency, peak RAM, actual token count and output validity are null/UNMEASURED until
a separately authorized real run. Only then measure first-load/warm state, process
and cgroup peak memory, wall/CPU time, exit/cleanup and strict response validity.
Record a failure/SIGILL/OOM/timeout without automatic retry, changing limits,
restarting the recorder or diagnosing the desktop failure from inference alone.
Schema validity would not establish useful reasoning or trading performance.

## Read-only recorder freshness check — never open the live WAL DB

`recorder_snapshot_034` requires an explicitly supplied **consistent offline
single-file SQLite snapshot**, exact owner-reviewed table/open/actual-insert-time
columns, a parameterized exact stream column/value and an explicit epoch-seconds
as-of. No schema/path guessing, automatic DB discovery, live connection, checkpoint,
backup, backfill, service action or recorder write. Live WAL/SHM/journal sidecars
refuse. Do not run this against a live DB by relabeling it as a snapshot.

Owner must use an already available consistent snapshot/approved recorder backup
procedure, preserving service operation. Blind copying a live DB while ignoring
WAL is not a coherent snapshot. If none exists without disturbing the recorder,
actual freshness remains UNKNOWN; do not stop the service or force a checkpoint
for this task. The tool deliberately does not automate acquisition.

Once owner has the coherent private snapshot and verified schema semantics:

```sh
python -B -m research.recorder_snapshot_034 --snapshot /OWNER_ONLY/consistent-snapshot.sqlite --snapshot-kind OWNER_CONSISTENT_OFFLINE_SNAPSHOT --table OWNER_TABLE --open-column OWNER_OPEN_SECONDS --ingest-column OWNER_ACTUAL_INSERT_SECONDS --stream-column OWNER_STREAM_COLUMN --stream-value OWNER_EXACT_STREAM --as-of OWNER_CAPTURE_EPOCH_SECONDS
```

Substitute exact reviewed names/values; placeholders are not a guessed schema.
The ingest column must be actual durable insert/observation time, not provider
candle time or an alias. Milliseconds/strings, future/unfinished bars and unknown
units refuse rather than being coerced. An exact stream filter prevents fresh rows
for another market masking selected-stream staleness; no USD/USDT conversion.

Implementation uses `mode=ro&immutable=1` **only for the declared static snapshot**,
no extension loading, trusted_schema off, query_only, in-memory temporary sorting,
validated identifiers and bound filter/limit values. It caps DB size at 2 GiB,
examines at most the latest 10000 ingestions, discloses truncation and has a SQLite
progress budget of approximately one million VM instructions. This is not a hard
kernel/CPU/RAM sandbox for malicious or concurrently changed DBs. A concurrent file
metadata change refuses. immutable mode would ignore live WAL/locking, hence the
snapshot-only restriction. Default execution opens nothing.

Metrics distinguish:

- latest ingestion time/age versus latest completed candle time/age;
- historical hourly coverage gaps versus observed gaps between insert timestamps;
- possible delayed/backfilled rows, defined by insert lag above the explicit
  default 7200s threshold, not proof of backfill or desktop outage causation.

“RECENT_RELATIVE_TO_SUPPLIED_AS_OF” is conditional on those declared fields and
unverified local as-of, not live service health or trusted B4 UTC. Historical
backfill can close a coverage gap while preserving an outage/insert gap, or create
fresh inserts of stale candles. The synthetic demo exercises the latter; separate
tests cover both gap types. It performs no automatic repair or historical fill.
Keep actual DB contents/schema/private timestamps local; committed fixtures/results
are invented, not recorder evidence. Current target freshness remains UNKNOWN.

## Exact offline evidence

| Command | Actual result |
| --- | --- |
| `python -B -m unittest discover -s tests -p test_target_validation_034.py -v` | 18 passed, 0.032s |
| `python -B -m unittest discover -s tests -v` | 552 passed, 6.768s, no skips |
| `node tests/test_paper_029.cjs` | 26 checks passed |
| `node tests/test_restore_030.cjs` | 14 checks passed |
| `node tests/test_market_031.cjs` | 8 controlled groups passed |
| `python -B -m research.target_validation_034 --synthetic-demo` | Passive synthetic plans; writes_performed 0; first cap 64; activation DISABLED; backfill example STALE |

Tests cover symlink-chain preservation/escapes, literal/resolved unsafe ancestors,
no source mode/content changes or destination creation, missing/mismatched expected
pins, scope binding and forged positive receipts, 64-token profile/no execution,
strict partial/extra/duplicate output refusal, read-only DB byte/sidecar preservation,
backfill versus insert/history gaps, exact-stream separation, WAL/unknown-kind
refusal, timestamp/SQL/schema errors, row-limit disclosure and idle no-DB behavior.
Regression execution includes prior controlled subprocess tests, never llama.cpp
or actual model inference. Earlier fixture timestamp and permission-check coding
errors were caught/corrected; the table records final passing reruns.

## Blockers and next owner action

Review this Draft. On the recovered target, first establish coherent recorder
freshness and unresolved desktop stability, record independent expected artifact
sources (or keep UNKNOWN), inventory resolved dependencies/ancestors, and review
only the passive private-copy plan. Qualified child-only containment evidence and
a fresh separate owner GO are mandatory before actual inference. Do not change
AEP originals, global libraries/environment, recorder services, SSH settings or
source/clock rules to make a check pass.

Six new files only: target planner, snapshot reader, manifest template, focused
tests, synthetic artifact and this report. Prior PRs/default MOCK/journal/strategies,
market recorder, main and workflows are unchanged. No downloads/installations,
paid services, accounts/credentials, deployments/merge/dispatch, live trading,
AEP/ZUMERAVO or other-project modifications. Additional spend NT$0.

B1/B2/B3/B5 HOLD; B4 NO-GO; real source admission HOLD; BUY AUTHORIZATION NONE.
REAL_NOT_RUN remains mandatory. STOP FOR OWNER AND BOSS AI REVIEW.
