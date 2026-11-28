# CODEX 037 Combined Hotfix #3 — 037-A–D

Issue #69 and its owner authorization comment; existing Draft PR #70. Reviewed
parent `584d2eb34760895dfd826cdd9dc01c7f7bd245c3`. No merge. NT$0 additional spending.

Delivered: verified-root compatibility correction and an executable independent
recorder observer with deterministic tests and consolidated read-only validation.
**Physical host stability remains HOLD. No physical-host supervisor or heartbeat
protocol is implemented/qualified in this delivery. Genuine inference remains
HOLD; AEP Gate B HOLD; BUY AUTHORIZATION NONE; REAL_NOT_RUN.** No actual compilation,
install/download, system setting/unit/cgroup change, recorder modification,
AEP/model/original runtime/source change, deployment or ZUMERAVO access occurred.

## 037-A — verified root may lack cgroup.type

The previous reader inspected cgroup.type before its verified-root exception.
The actual hierarchy root may lack that file as well as memory.max/high/current.
The reader now tolerates **FileNotFoundError only at the already mapped and
verified global cgroup-v2 root**. It records `ABSENT_AT_VERIFIED_HIERARCHY_ROOT`,
rather than inventing a domain type. Permission errors, malformed/present invalid
types, absent nonroot types, unknown/partial interfaces, hidden/namespaced roots,
ambiguous mounts, ancestry/limit changes and finite ancestor constraints retain
their existing strict handling.

The exact Debian fixture has caller
`/user.slice/user-1000.slice/session-3.scope`, configured parent
`/user.slice/user-1000.slice/user@1000.service`, four nonroot nodes with unlimited
max/high, kernel availability **5,818,220,544 bytes**, and absent root type/memory
interfaces. It now passes capacity parsing with that exact value. A finite
ancestor still reduces capacity; the **4 GiB headroom floor and 3 GiB compilation
ceiling** are unchanged. Fixture values are not fresh measurements of the owner PC.

## 037-B — real independent recorder measurements

Run `research.recorder_health_037` as an ordinary, manually started process outside
the future build sandbox. The production CLI has no synthetic/source substitution
flag. It reads the current user's actual
`~/.local/share/boss-s3-recorder/status.json` and makes fixed **read-only** calls to
existing `/usr/bin/systemctl --user --no-pager --no-ask-password show` for only:

* `boss-s3-recorder.timer`
* `boss-s3-recorder.service`

No database, market endpoint, keys, order API, unit start/stop/reload/enable,
recorder file write or new scheduled unit is used. Existing systemd timer operation
is observed, not activated or modified. Queries use the current UID's fixed
`/run/user/UID/bus`, a clean environment, a **2-second process timeout**, 4 KiB
combined output cap and the existing CODEX035 process kill/reap supervisor.
Unknown units, missing user bus/tools, unsafe permissions or failed queries HOLD.

The observer validates the **actual schema supplied in Issue #69**:
`mode=LIVE_PUBLIC_DATA`, `health=RECENT_COLLECTION`, UTC ISO8601 `generatedAt`,
`lastAttemptAt`, `lastSuccessAt`, explicit null pausedReason, orderAuthority NONE.
It rejects duplicate/nonfinite/oversized/malformed JSON, naive/non-UTC/future or
inconsistent timestamps, stale success/source time and source changes during a
snapshot. One bounded remeasurement accommodates an atomic recorder update: at
most four property queries, with the retry allowed only in the first second;
observations exceeding the five-second budget are not published as healthy.

`last_collection_at` is the actual source **lastSuccessAt**, converted to epoch
seconds for the existing consumer. Its original ISO timestamp is also preserved
as measurement.last_success_at; generated/attempt timestamps are preserved too.
Independent measured_at comes from this observer's completed query cycle. Polling
never turns an old collection into a new one. The owner-confirmed cadence is
**900 seconds**, required to match config; the existing collection-age bound is
retained at `2*900+30=1830` seconds. The cadence is an explicit owner-confirmed
policy, not a claim that every possible timer schedule was independently parsed.

The normal between-collection oneshot state **inactive/dead + Result success +
ExecMainStatus 0** is healthy. Loaded/exact unit identity and active waiting timer
are required. `activating/start` and `activating/start-post` are accepted as
bounded in-progress phases with a genuine monotonic ExecMainStart timestamp and
runtime <=900s; no new success is inferred. Service/timer failure, inactive timer,
unfinished idle attempt, overrun or failed/missing identity evidence is unhealthy.
Read-only status/unit snapshots are not a transactional guarantee that all unit
properties remain unchanged after the query, or proof of candle/database contents.

### Publication, loss and host boundary

Evidence is published atomically about every **five seconds**, with a maximum
manual process duration of **7,500 seconds** (no restart daemon). It uses the
existing config health_file and recorder_id. Parent directory must be owned/private
0700; health/lock/temp files are 0600. Publication is exclusive initially, inode
checked thereafter, with flush/fsync/atomic rename. A held private lock prevents
another publisher; the recorder status file is untouched. Existing foreign output
is refused. Explicit `--replace-stale` only replaces a recognized own-recorder
observer record whose previous process has stopped/disappeared. Do not use it to
replace a still-running or unrelated producer. Same-UID hostile concurrent file
writers remain outside this owner-side trust model.

Consumers validate boot ID, observer PID and Linux start ticks, pinned observer
code hash, live flag, monotonic heartbeat and measurement age **<=15 seconds**.
A dead/reused PID or stopped observer refuses immediately; a hung observer's old
heartbeat expires. Graceful TERM/INT or duration expiry publishes unhealthy/stopped
evidence. Hard kill cannot run finalizers, so PID/TTL checks are essential. Query
or source errors publish fresh **unhealthy** evidence and preserve only the last
actually known collection timestamp, or null if none was established. No timestamp
or healthy/stable value is invented to obtain PASS.

**Guest responsiveness is not physical host stability.** Every new observer record
sets `desktop_stable=false` and `host_stability=HOLD_PHYSICAL_HOST_NOT_OBSERVED`.
The new observer contract rejects manually flipping that boolean to true. There
is no `--desktop-stable`, owner assertion or heartbeat bypass. A genuine guest
recorder measurement may produce `recorder_observation: PASS` while the unchanged
build admission reports **PHYSICAL_HOST_STABILITY_HOLD**. Closing that HOLD needs
separately reviewed, bounded physical-host supervision; it is not supplied here.
Local guest wall/monotonic timestamps are not authenticated UTC/NTS evidence, and
VM/host freezes/suspend cannot be certified by in-guest polling. Source I/O stalls
are detected through stale consumer evidence when the consumer can run; no
whole-physical-host liveness guarantee is claimed.

The earlier generic `monitor` was a mapper for an already adequate external
status contract. It cannot manufacture the absent host evidence in the real
recorder JSON. Use this independent observer for the owner-described recorder;
do not add fake desktop_stable or continuously refreshed timestamps to that source.

## 037-C — evidence separated by origin

`docs/evidence/controlled-build-037-combined-hotfix.json` includes:

* **Synthetic exact Debian root/recorder/systemd fixtures**, including normal
  oneshot transitions, health failures and physical-host HOLD. These are not
  genuine target recorder observations.
* **Actual read-only Linux interface observations on the cloud runner**: its root
  cgroup.type exists as domain, memory.max is 8 GiB and other interfaces are
  readable. This differs from the owner's root. Its full memory snapshot remains
  HOLD (`CGROUP_PATH`) under its restricted namespace; no unknown scope is waived.
  No cgroup, file under /sys, unit or system setting was changed.
* **Actual production observer TERM/KILL tests** run with a deliberately missing
  source in a private fixture HOME. They prove atomic output/stop/loss handling,
  not real recorder/systemd health. Source failure occurs before a unit query;
  these tests make no real recorder or systemd requests.

Actual owner recorder/unit measurement remains **UNVERIFIED until local execution**.
No genuine healthy target output was fabricated. The test seams inject inert
readers/query results only in tests; production collection uses the actual file
and fixed systemd queries. Ordinary status observations cannot certify market
performance, independent data provenance or system/host security.

## 037-D — consolidated local validation, preserving existing inputs

Existing inventory and configuration schema remain unchanged. Reuse existing
reviewed toolchain/system-library inventory files when hashes/review still match.
The observer uses existing health_file and recorder_id. **Cadence must be 900**;
if an old illustrative config retained 60, that single value is incompatible and
needs explicit owner correction/review, not automatic rewriting. No code alters
config/inventory bytes. New observer code is hash-pinned into fresh plans; old
plan/qualification/approval artifacts cannot stand in for this changed code.

From the reviewed updated PR checkout, match `git rev-parse HEAD` to the final
report's exact revised head. Use the existing system Python; no install commands:

```sh
git rev-parse HEAD
/usr/bin/python3 --version
/usr/bin/python3 -B -m unittest discover -s tests -p test_recorder_health_037.py -v
/usr/bin/python3 -B -m unittest discover -s tests -p test_memory_headroom_037.py -v
/usr/bin/python3 -B -m unittest discover -s tests -v
```

In terminal A, use the **existing config path**, not a regenerated inventory:

```sh
/usr/bin/python3 -B -m research.recorder_health_037 --config "$BT_PRIVATE/config.json" --seconds 120
```

The default source is the actual current-user recorder status path above. Do not
run as root or substitute HOME to impersonate a different recorder. Source paths
must satisfy the existing no-symlink/owner/permissions/ACL read policy. If the
private output directory is incompatible, review a new private evidence location;
do not chmod original recorder/AEP/model directories or overwrite unrelated data.
For a later explicit restart of this recognized stopped observer only, append
`--replace-stale`; no old file deletion or status editing is required.

While it runs, in terminal B:

```sh
/usr/bin/python3 -B -m research.controlled_build_037 preflight --config "$BT_PRIVATE/config.json"
```

Expected only if genuine local inputs support it: memory PASS; recorder_observation
PASS for a live fresh healthy observer; recorder_health **HOLD with
PHYSICAL_HOST_STABILITY_HOLD**. Other genuine unit/source/permissions problems
remain HOLD with their reason. Exit 2 is expected while any HOLD remains.
The survey remains unqualified and read-only. After 120 seconds the observer
publishes stopped evidence; subsequent preflight must reject it. A console time
change, stale/future/failed recorder, observer loss or unsupported profile must
not be repaired with a hardcoded healthy/stable flag.

Do **not** run approve/build/compile from this sequence. The local validation does
not close physical-host, full containment, independent UTC, model-publisher/
license or independent reproducibility gaps. Fresh preparation and harmless
qualification remain future reviewed steps; no cgroup/namespace/system changes
were made for this hotfix. Continue HOLD pending owner/BOSS AI review.

### Recorded offline results (2026-11-28)

| Command / scope | Result |
|---|---|
| `/usr/bin/python3 -B -m unittest discover -s tests -p test_recorder_health_037.py -v` | 40 passed, 0.370s |
| `/usr/bin/python3 -B -m unittest discover -s tests -p test_memory_headroom_037.py -v` | 33 passed, 0.015s |
| `/usr/bin/python3 -B -m unittest discover -s tests -p test_controlled_build_037.py -v` | 39 passed, 2.838s |
| `/usr/bin/python3 -B -m unittest discover -s tests -v` (3.13.5) | 735 passed, 12.044s; 695 baseline +40 new; no skips |
| `python -B -m unittest discover -s tests -v` (3.12.14) | 735 passed, 11.435s; no skips |

Ten inherited Python 3.13 SQLite ResourceWarnings remain unsuppressed. New cases
cover root type absence/nonroot refusal/ancestor constraints, exact recorder
schema/900s cadence, idle/running transitions, stale/future/inconsistent data,
failed units/timeout, source races/bounded remeasurement, PID/boot/code/staleness
loss, false host claims, atomic private output, competing publishers, controlled
restart, malformed inputs, fixture/source immutability, five-second cadence,
collection-time regression, genuine process TERM/KILL, and consolidated preflight's
separation of recorder PASS from physical-host HOLD.

STOP FOR OWNER AND BOSS AI REVIEW.
