# CODEX 035 — executable owner qualification and disabled local executor

Issue #65; implementation/synthetic tests GO, genuine inference HOLD. Baseline
Draft #64 `2ff1c36981c0e6083b7b51735f666a7f8806f9a4` and #62
`2fd237d9f19355a68a23ed7f5a13be1cd8b058cf` verified unchanged. New branch
`research/issue-65-owner-qualification` stacks on #64's branch
`research/issue-63-target-validation`. Prior branches, main and workflows unchanged.
README/SECURITY, issue and CODEX 034/033 implementation reviewed; no AGENTS.md in
baseline tree. Cloud runtime skill used for workspace/capability handling.

**REAL_NOT_RUN. NT$0.** No actual model/weights/tokenizer execution, owner desktop
access, downloads, installations, deployment, merge or trading. No AEP environment,
recorder configuration, SSH, S1/S2/S3, source/clock/risk policy or other-project edits.
Operational recorder schema/data remains unavailable to Codex.

## Working software and actual evidence

```sh
python -B -m research.owner_tools_035
python -B -m research.owner_tools_035 demo
```

Default is idle, without file/process/database/network actions. Demo uses original
inert ELF-shaped bytes and GGUF test sentinels, fabricated SQLite rows and the
pinned Python worker, never a real executable/checkpoint. It applies/verifies/
rolls back a private copy of those invented bytes; it is not a runtime build.

[Executed synthetic demonstration](artifacts/owner-qualification-035-synthetic-demo.json):

- dry-run writes zero files; explicit synthetic apply verifies before/after hashes,
  preserves relative library links, and rollback removes only that new bundle;
- bound synthetic worker output validates, with BUY AUTHORIZATION NONE and zero
  genuine inference; model token counts remain unknown;
- both 900s and 3600s snapshots validate at an independently declared 60s collection
  cadence, identify one missing candle interval, and do not turn an ordinary
  new-candle insert gap into proof of missed 60s scans;
- actual Codex capability attempt returns **HOLD / SYSTEM_PYTHON_PROFILE_REQUIRED**
  before launching Bubblewrap or local canaries. Its interpreter is outside the
  supported /usr profile. No alternate interpreter/profile, escalation or install
  was tried to force PASS. Actual owner qualification remains unperformed.

The injected test qualification used for bare stub tests is explicitly
SYNTHETIC_TEST_INJECTED_NOT_TARGET_QUALIFIED. It never claims target isolation.
The owner path can return only the response already observed inside the qualifying
child; it never starts a later unenclosed process based on a positive receipt.

## Consolidated owner commands

Use an **already installed** system Python 3.11+ under /usr, e.g. /usr/bin/python3;
do not activate/change AEP, install dependencies or run llama-cli. If unavailable,
HOLD. Run from this checked-out branch. Keep all filled configs, snapshots and
receipts private/local; template paths are deliberately nonexistent.

Prepare a new private config from
[owner_tools_035.example.json](../research/owner_tools_035.example.json). Fill:

- the exact original AEP and recorder protected directories (not an entire system
  root), NEW destination outside them, explicitly reviewed source files/relative
  bundle layout, all library aliases/targets and dynamic-loader search directories;
- independently sourced expected SHA-256 records and evidence references, existing
  build/license review; UNKNOWN/reported-only fingerprints are not sufficient;
- a coherent offline recorder snapshot and actual schema/units/interval/cadence;
- an already-owned 0700 qualification state directory outside AEP, recorder and
  bundle, and an existing delegated cgroup-v2 parent if supported. A new empty
  state directory may be created with normal owner permissions, not sudo. Do not
  change parent cgroup controls to manufacture delegation;
- adapter runtime/model paths to canonical regular files **inside the new bundle**,
  with matching pins. Preserved symlink aliases remain in the bundle, but CODEX 033
  deliberately requires canonical nonsymlink adapter paths. `request_path: null`
  explicitly selects the packaged synthetic BTC request; no manual request script
  or data download is needed. A supplied bad request path refuses without fallback.

Commands (substitute reviewed private config/receipt paths):

```sh
# 1. Read-only schema, then metrics after declaring the actual stored semantics.
/usr/bin/python3 -B -m research.owner_tools_035 snapshot /PRIVATE/owner-035.json --schema
/usr/bin/python3 -B -m research.owner_tools_035 snapshot /PRIVATE/owner-035.json

# 2. Dry-run; no destination or source writes. Stop on any refusal/unknown.
/usr/bin/python3 -B -m research.owner_tools_035 provision /PRIVATE/owner-035.json

# 3. Only after reviewing a successful dry-run, explicit NEW private-copy apply.
/usr/bin/python3 -B -m research.owner_tools_035 provision /PRIVATE/owner-035.json --apply --receipt-output /PRIVATE/new-035-receipt.json

# 4. Child-only SYNTHETIC qualification, never model inference.
/usr/bin/python3 -B -m research.owner_tools_035 qualify /PRIVATE/owner-035.json --receipt /PRIVATE/new-035-receipt.json

# 5. Review bound, disabled first-inference plan. No execution flag exists.
/usr/bin/python3 -B -m research.owner_tools_035 plan /PRIVATE/owner-035.json --receipt /PRIVATE/new-035-receipt.json
```

Explicit rollback, if desired, is one command:

```sh
/usr/bin/python3 -B -m research.owner_tools_035 rollback /PRIVATE/owner-035.json --receipt /PRIVATE/new-035-receipt.json
```

Expected outcomes: schema without guessing interval, conditional snapshot metrics;
DRY_RUN/writes=0; APPLIED_PRIVATE_COPY plus exclusive 0600 receipt; qualification
false/HOLD if any capability/check is unavailable; plan REAL_NOT_RUN with a 64-token
ceiling. Even `qualified: true` is **only the measured synthetic profile**, not
permission or full qualification for Qwen. Errors exit without auto-retry/repair.
Do not replace existing receipt files or edit the provisioning portion of a config
used for a receipt. Archive it locally: hashes bind that exact config.

Rollback requires the matching receipt/config/root identity and exact unchanged
file/link tree. Foreign, modified or missing files/directories refuse before
routine deletion. Cleanup iterates only recorded own paths/inodes; a concurrent
foreign insertion stops removal rather than being recursively deleted. Partial
cleanup/poison markers require independent owner review, never global cleanup.
Receipts are retained after successful rollback. No original AEP/recorder path is
an authorized output, receipt or rollback destination.

## Recorder correction: candle interval is not collection cadence

`recorder_snapshot_034` now requires explicit `expected_interval` (900 or 3600),
`collection_cadence` and
UTC_EPOCH_SECONDS_OPEN_TIME_AND_ACTUAL_INSERT_TIME. No default hourly inference
remains. Timestamp alignment, completed-candle boundaries, freshness and coverage
count use the declared candle interval. Collection cadence is separately reported.
The observed insert-gap diagnostic threshold is 2×max(cadence,candle duration),
not a claim that each collection scan inserts a new candle. It is not a heartbeat
or outage detector. The configurable max_ingest_age threshold is separately shown.
Response version is recorder-snapshot-v2; gaps use missing_intervals, not hours.

If stored rows have an interval-seconds column, set `interval_column`; every selected
row must match the declared interval, with no coercion. Mixed/incorrect durations
refuse. Without that column the output explicitly says OWNER_DECLARED_SINGLE_INTERVAL_
STREAM_NOT_AUTHENTICATED. Owner must verify a single-interval stream/view from the
existing recorder's source/metadata. Do not infer candle duration from collection
frequency, missing rows or multiples of timestamps. Unknown schema/seconds versus
milliseconds/ingest meaning is a HOLD, not a guessed conversion.

The --schema command reads only the explicit snapshot's schema, not market values,
and does not infer interval. Prefer an existing documented recorder snapshot/export
procedure if the owner has one; no such operational tool is present in this GitHub
baseline, so no command for an unknown recorder is invented. Do not stop/restart it,
checkpoint, alter schema/indexes, copy a live DB while ignoring WAL, or run backup
repair for this task. If a coherent offline snapshot is unavailable, actual freshness
stays UNKNOWN. mode=ro&immutable=1 is limited to that owner-declared static snapshot;
WAL/SHM/journal sidecars refuse, extensions are disabled, query-only/in-memory temp
storage, row/size/VM-step limits and explicit stream filtering remain intact.

A fresh insert of an old candle can be backfill while latest market coverage remains
stale. Historical candle gaps, observed insert gaps and possible delayed rows are
separate metrics, not a root-cause conclusion. Other streams cannot mask the chosen
stream's staleness. UTC/as-of is owner supplied, not B4-authenticated. No live DB is
opened, no automatic backfill occurs, and no DB metrics enter source admission or AI.
Prior CODEX 034 tests/demo now declare their hourly semantics explicitly; prior PR
branches are unchanged. Old hourly-only command examples are superseded here.

## Provisioner behavior and trust limits

The Linux provisioner is executable, not merely a plan. It requires explicit
independent expectation categories (UPSTREAM_PUBLISHED or REPRODUCIBLE_BUILD;
SYNTHETIC_TEST only for invented fixtures), a nonempty evidence reference and
owner build/license review. It refuses REPORTED_ONLY/UNKNOWN, mismatched hashes,
unsafe/relative/traversing/duplicate paths, overlapping sources/destinations,
existing destinations, untrusted owners, writable ancestors or access/default
POSIX ACLs. No permissions/ACLs are repaired in source/AEP paths. Unsupported ACL
inspection fails closed. The namespace's filesystem-root owner is the trusted root
UID anchor (supports mapped-root environments), plus the invoking owner UID; other
ownership refuses. ACL/mount/NFS/hostile same-UID caveats still require owner review.

Passive ELF64 little-endian x86_64 parsing checks PT_INTERP and transitive DT_NEEDED
against inventoried regular files/relative aliases, with metadata bound to the same
expected ELF bytes. Unresolved loader/library dependencies or escaping RPATH/RUNPATH
refuse. Reviewed dynamic source directories are scanned for unlisted .so candidates;
all require pins. This is **not proof of arbitrary runtime-computed dlopen/plugin or
configuration behavior**. Owner build/source evidence must cover dynamic search
paths; uncertainty stays HOLD. No ldd or target executable is run to collect this
information, no binary rebuild or RPATH patch is performed, and no code/data license
is inferred from a digest or the repository MIT license. Current target independent
expected hashes/licensing/build binding are still UNKNOWN; reported fingerprints
are not promoted into trusted expectations by this delivery.

Apply stages under the already-secure destination parent, creates only new files,
streams expected bytes, hashes before/during/after copy, preserves relative symlinks
and sets private 0700 directories / 0500 runtime / 0400 model/libs. Read-only copies
are separate inodes, not source hardlinks. Directory-FD-bound Linux renameat2
RENAME_NOREPLACE commits atomically without replacing anything. No permissive rename
fallback exists. Source mutation, disk headroom, exclusive-receipt or commit failure
stops and cleans only its recorded new staging entries. Unexpected entries are
preserved with cleanup HOLD. The external receipt is exclusive 0600 and cannot be
inside AEP/recorder/bundle. Receipt-write failure rolls back only the newly created
bundle; it never deletes a racing pre-existing receipt.

Receipt config/hash/inode/nonce bindings detect accidental wrong-tree or changed
bundle operations, not malicious owner forgery, authenticated upstream provenance,
crash-consistent transactional recovery across power loss, or a hostile-user kernel
sandbox. A hard interruption may leave its private staging directory for owner
review. Hashes/receipts are not permission to activate inference.

## Executable child-only qualification

Requires an existing trusted Bubblewrap, system Python under /usr, Linux namespaces,
IPv4/IPv6 loopback, /proc process visibility and a secure owner state directory.
No sudo, installs, global networking/firewall/resolver/cgroup changes or service
commands. A stable state lock prevents concurrent qualification processes in the
same configured domain; the supervisor also has a one-job in-process lock. Changing
the domain is a new scope, not proof of machine-wide concurrency control.

The tool starts ephemeral-port IPv4/IPv6 TCP and UDP DNS-like canaries on parent
loopback only, proves echo before and after, then executes the pinned Python worker
in a disposable Bubblewrap user/mount/net/PID namespace with clear environment.
No public address or real provider/DNS server is contacted. A private resolver file
points only to child loopback. Checks cover namespace distinction/no nonloopback
interfaces, denial of parent IPv4/IPv6/UDP canaries and resolver calls, absence of
child packets at parent canaries, host canary reads denied, protected roots hidden,
read-only mount write denial and private scratch controls. Positive parent controls
prevent a dead listener from counting as denial. Host private/recorder files are
never used as write-test targets; only newly created synthetic canaries are tested.

Only /usr/system loader directories required for the synthetic Python profile are
read-only exposed; configured protected roots are resolved and hidden, including
masking them if under an exposed system directory. If hiding them would hide the
interpreter itself, the profile refuses. The private bundle is mounted read-only
for observation, never executed. This broader **synthetic Python profile is not a
minimal qualified model sandbox**. A real activation change must review its loader,
mounts, filesystem types, dynamic behavior and artifact set independently.

A fresh launcher waits on a private parent gate; only its own PID may be attached to
an already-delegated NEW private cgroup. Parent controls are never enabled/changed.
Memory 3 GiB, swap 0, one-vCPU quota, pids 8, oom-group 1; RLIMIT_AS 4 GiB, CPU 30s,
FDs 32, core 0, two-thread environment and lower priority apply to the child only.
To avoid false-positive read-only tests, the synthetic filesystem phase first allows
4 KiB file output and proves scratch writes work while a host-writable canary's
read-only mount denies writes; it then lowers FSIZE to 0 and tests that limit.
This phase is labeled in scope and is not a model run. A controlled descendant is
terminated and reaped; supervisor checks tracked host processes/start times and
kills/waits only its own group. Missing process visibility or uncertain cleanup
poisons the gate; an owner state marker blocks later qualification attempts. No
reset/repair flag exists. Own-cgroup cleanup failure records a local review resource;
no global or foreign group is removed.

No delegated controllers => partial checks may run but qualification stays false.
A missing tool, unsupported interpreter/ACL/namespace/proc/canary/cgroup feature =>
HOLD, never a weaker fallback. Time/read/output limits and cleanup are application
controls; kernel stalls, escaped/unobserved malicious descendants and hostile code
are not proven bounded. This worker is pinned trusted test code. Actual owner
limits/latency/RAM and full model containment remain unverified.

## Disabled executor and output budget

Bindings include exact artifact manifest and pins, **full bundle/library/link/ELF
inventory and receipt**, prompt, schema, 034 target scope, worker and evidence ID.
Qualification additionally binds protected-root/concurrency-domain hashes, exact
profile/tool fingerprints and filesystem-test phase. Corrupt or mismatched receipts
refuse. Injected test receipts cannot masquerade as measured owner qualification.
Actual owner-path stub analysis is returned only from the qualifying child itself,
not a later process launched with less containment. Only the pinned synthetic
worker is dispatchable through this API; runtime/model paths never become a command.

`DisabledExecutor.infer` unconditionally raises REAL_NOT_RUN_NO_ACTIVATION_PATH.
No receipt, manifest, environment or flag can override it. Real launch requires a
fresh separate owner GO AND subsequent reviewed activation code. CPU-only 2 threads,
2048 context, 64 generated tokens, 30s wall budget, bounded streams/cleanup and 034
resource assumptions remain proposed real limits, not measured model performance.
The synthetic bare-process test path is explicitly injected/not target qualified.

The shortest ASCII schema-valid analyst-v1 response for a 64-hex evidence reference
is **219 bytes**, using semantically useless one-character hypothesis/objection/
invalidation and REJECT. A representative synthetic response is **381 bytes**.
Byte/4 heuristics are 55 and 96 respectively, **not actual tokenizer counts or hard
bounds**. Actual Qwen counts remain null; likely truncation is flagged, not fixed
by raising 64, removing required fields, stripping logs, repairing or retrying.
Partial/extra/duplicate/reference/objection errors refuse. Genuine inference and
reasoning quality have not been tested. Original deterministic risk veto and
BUY AUTHORIZATION NONE remain final; supporting stub output cannot promote WAIT.

## Actual tests and scope

| Check | Result |
| --- | --- |
| `python -B -m unittest discover -s tests -p test_owner_qualification_035.py -v` | 26 passed, 0.806s |
| `python -B -m unittest discover -s tests -v` | 578 passed, 7.541s, no skips |
| `node tests/test_paper_029.cjs` | 26 checks passed |
| `node tests/test_restore_030.cjs` | 14 checks passed |
| `node tests/test_market_031.cjs` | 8 controlled groups passed |
| `python -B -m research.owner_tools_035 demo` | Synthetic dry/apply/verify/rollback, bound worker, both intervals; REAL_NOT_RUN |

Tests cover source preservation, hashes/ACL/owner/ELF/closure/dynamic-library
refusals, exclusive-commit races, foreign staging/rollback preservation, receipt
pins and modified bundles, interval/cadence/alignment/mixed-duration/filter/backfill/
freshness/schema/read-only regressions for 900 and 3600, scope tampering, unavailable
qualification, pinned-worker timeout/tree cleanup/overflow/nonzero/schema errors,
concurrency, minimum response estimate, deterministic veto, default no-I/O and the
consolidated owner CLI workflow. Original 552 tests remain passing, with explicit
hourly declarations in prior fixtures. Controlled process tests are not target
qualification. This Codex environment's actual qualification attempt stopped at
SYSTEM_PYTHON_PROFILE_REQUIRED; namespace/canary/cgroup target claims are NOT MADE.

Changed existing files: recorder_snapshot_034.py (interval/semantics correction),
target_validation_034.py and test_target_validation_034.py (explicit existing hourly
call sites). Added owner_tools_035.py, its local template, qualification_035 package,
focused tests, this report and original synthetic artifact. No operating recorder,
S1/S2/S3, MOCK/risk/source admission, AEP/ZUMERAVO, prior branch, main or workflow edit.
No model downloads/installations, paid APIs/accounts, actual tokenization/inference,
orders, auto-backfill, deployment, merge or dispatch. Additional spend NT$0.

## Remaining blockers / next owner action

Fill reviewed local inventory and coherent-snapshot declarations, then run schema/
freshness and dry-run first. Preserve UNKNOWN where independent expected sources,
licenses/build binding, complete dynamic closure or target capabilities are absent.
Do not chmod/reconfigure AEP/recorder/global libraries, enable parent cgroup controls,
install Bubblewrap/Python or suppress refusal to get a passing run. Desktop freezing
cause remains unresolved; recorder service resume is not DB freshness proof.

Actual target qualification, stable resources/cleanup and recorder health remain
unperformed until the owner runs reviewed commands. Even a successful synthetic
qualification does not authorize model inference; obtain fresh separate approval
and a reviewed activation change after those evidence gaps are closed.
B1/B2/B3/B5 HOLD; B4 NO-GO; real source admission HOLD; REAL_NOT_RUN;
BUY AUTHORIZATION NONE. STOP FOR OWNER AND BOSS AI REVIEW.
