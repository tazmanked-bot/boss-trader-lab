# BOSS Trader CODEX 036 — portable runtime preparation

Status: **REAL_NOT_RUN**. Desktop build HOLD; full containment HOLD; genuine AI
inference HOLD; AEP Gate B HOLD; BUY AUTHORIZATION NONE. NT$0 additional spending.
No original runtime/source/model permissions, observer, recorder, strategy,
ZUMERAVO or earlier PR changes. No compilation, tokenizer/model execution,
installation, download, real exchange/time request or workflow dispatch occurred.

This is a preparation-only delivery for [Issue #67](https://github.com/tazmanked-bot/boss-trader-lab/issues/67),
stacked on unchanged Draft #66, base
`66b4f17c560a1b4220daf17a9ccdb99b75e72c3d`.

## Executable tools delivered

`python -B -m research.portable_runtime_036` provides:

* `status`: pinned revision, fixed proposed limits, all gates; no compiler probing.
* `prepare`: read-only dry-run by default. Requires the exact clean local source,
  private trusted destination parent, explicit protected paths and headroom.
  `--apply` exports tracked, hash/mode-verified regular files into a **new**
  private `source/`, alongside empty `build/`, `stage/`, `home/`. It never runs
  checkout/filter/build commands, copies original binaries or uses untracked files.
  It checks source again after copying; no `.git` is copied. Empty tracked files
  are supported. Symlinks/submodules require further review and are refused.
* `verify`: passive ELF64-LE x86_64 checks, bound hashes/sizes, RPATH/RUNPATH,
  interpreter, DT_NEEDED, SONAME, transitive dependencies, exact staged file list
  and relative alias chains. Does **not** run `ldd`, loader, runtime or model.
* `compare`: compares two recorded artifact maps/aliases and recorded input digests;
  reports differences without promoting either report to independent provenance.
* `handoff`: creates an intentionally **unqualified** CODEX035 inventory. It keeps
  `LOCAL_BUILD_ATTESTATION` and `licenses_reviewed: false`. The unchanged provisioner
  refuses it. Independent expectations, reviewed licensing and a separately
  qualified existing model must be supplied in a separately reviewed configuration.
* `rollback`: dry-run default, pinned receipt, exact own inode/type/path ledger and
  file hashes. Refuses added foreign files, replaced paths, edited contents and
  symlinks. `--apply` removes only recorded own paths; never recursive foreign
  deletion. Stop all writers before rollback; hostile concurrent same-UID writers
  are outside this preparation utility's guarantees. After any preparation error,
  preserve leftovers for review; do not use `rm -rf`. An interrupted/failed prepare
  without a complete pinned receipt is not eligible for automated rollback.
* `build`: returns exit 2 and
  `SEPARATE_OWNER_APPROVAL_AND_CONTAINMENT_REQUIRED_BUILD_HOLD`.
  **There is no active build executor or approval bypass in this PR.** This is
  intentional while actual desktop compilation remains unauthorized. The commands
  in a preparation plan are a recipe for a later approved executor, not commands
  to paste into an uncontained shell. A future approved execution action remains
  a blocker, rather than an unverified security claim.

`--apply` on **prepare** only copies source and creates directories. It is not
compilation approval. Nothing changes CODEX035's worker, process limits, independent
hash requirements, containment or inference gates.

## Source-anchored recipe review

Official reviewed source:
[`0978a6e9022fb9bd6874b86154ee304e81929b9f`](https://github.com/ggml-org/llama.cpp/commit/0978a6e9022fb9bd6874b86154ee304e81929b9f),
tree `5e472b707005dec79feedd0942c3814fb88b9a6d`, commit epoch `1793705189`.
GitHub commit metadata and the complete recursive tree were read through the
connector on 2026-11-28. The tree has 4,421 entries and no symlinks/gitlinks.
The owner-reported original clean checkout and target hardware were **not accessed
or requalified** here. The unrelated newer checkout is not acceptable input.

| Exact pinned source | Consequence |
|---|---|
| [root CMakeLists](https://github.com/ggml-org/llama.cpp/blob/0978a6e9022fb9bd6874b86154ee304e81929b9f/CMakeLists.txt) | Build/library outputs under `build/bin`; `LLAMA_CURL` deprecated, not used as a network-disable guarantee. |
| [tools/CMakeLists](https://github.com/ggml-org/llama.cpp/blob/0978a6e9022fb9bd6874b86154ee304e81929b9f/tools/CMakeLists.txt), [CLI](https://github.com/ggml-org/llama.cpp/blob/0978a6e9022fb9bd6874b86154ee304e81929b9f/tools/cli/CMakeLists.txt), [server](https://github.com/ggml-org/llama.cpp/blob/0978a6e9022fb9bd6874b86154ee304e81929b9f/tools/server/CMakeLists.txt) | `LLAMA_BUILD_SERVER=ON` required to define CLI; CLI links server-support code. Build **only** target `llama-cli`; do not run/build standalone server, all-target install or network tools. |
| [UI](https://github.com/ggml-org/llama.cpp/blob/0978a6e9022fb9bd6874b86154ee304e81929b9f/tools/ui/CMakeLists.txt), [asset script](https://github.com/ggml-org/llama.cpp/blob/0978a6e9022fb9bd6874b86154ee304e81929b9f/scripts/ui-assets.cmake) | Both `LLAMA_BUILD_UI=OFF` and `LLAMA_USE_PREBUILT_UI=OFF`; missing assets emit a warning/stub without npm/HF provisioning. Capture the warning; don't download assets to silence it. |
| [vendor HTTP library](https://github.com/ggml-org/llama.cpp/blob/0978a6e9022fb9bd6874b86154ee304e81929b9f/vendor/cpp-httplib/CMakeLists.txt) | OpenSSL, BoringSSL/LibreSSL builds OFF; HTTP code still exists. No network-free binary claim. |
| [GGML options](https://github.com/ggml-org/llama.cpp/blob/0978a6e9022fb9bd6874b86154ee304e81929b9f/ggml/CMakeLists.txt) | CPU ON, native OFF; AVX/AVX2/FMA ON, optional F16C/BMI2/SSE42/AVX512/AMX OFF. GPU/accelerators, RPC, dynamic backends, optional OpenMP/BLAS/KleidiAI/llamafile/ccache OFF. |
| [build information](https://github.com/ggml-org/llama.cpp/blob/0978a6e9022fb9bd6874b86154ee304e81929b9f/cmake/build-info.cmake) | Export lacks `.git`; use `GIT_CEILING_DIRECTORIES` in the proposed clean environment to prevent accidentally reporting a parent repository's version. External attestation records the real commit/tree; embedded build info may be unknown. |

Exact proposed CMake argument arrays are emitted by `prepare`; no shell expansion
of `$ORIGIN`. `CMAKE_BUILD_WITH_INSTALL_RPATH=ON` avoids build-directory search
paths/padding, `CMAKE_INSTALL_RPATH=$ORIGIN;$ORIGIN/../lib`, link-path injection OFF,
build-origin handling ON. Every produced ELF still must pass verification; a flag
is not evidence that a linker honored it. **All configure/build flags remain
untested against a real compiler in this assignment.** No original ELF is patched.

Static linkage or replacing the CLI with a minimal runner may reduce dependencies,
but neither is reviewed, implemented or qualified here. Don't switch silently.

## Few owner commands — preparation only

Run from the reviewed new PR checkout, using the existing Python environment.
Fill in real absolute paths yourself. Do not use a guessed/newer source location.
The destination's parent must already be a private trusted directory, without
symlink ancestors, untrusted writers or POSIX ACLs. The tool does not fix original
permissions. List all original runtime/source/model, AEP and recorder roots as
protected paths. Do not point it at ZUMERAVO; this assignment does not access it.

```sh
python -B -m research.portable_runtime_036 status
python -B -m research.portable_runtime_036 prepare --source "$REVIEWED_SOURCE" --destination "$NEW_PRIVATE_JOB" --protected "$ORIGINAL_RUNTIME_ROOT" --protected "$EXISTING_MODEL_ROOT" --protected "$AEP_ROOT" --protected "$RECORDER_ROOT" > portable-036-plan.json
```

Expected: exact pinned source commit/tree, `writes: 0`, `SOURCE_REVIEWED_BUILD_UNTESTED`,
`execution_enforcement: NOT_ACTIVE_BUILD_DISABLED`, all gates HOLD. Source not
available, dirty tracked content/mode, wrong revision, path overlap, unsupported
CPU, unavailable memory-controller evidence or insufficient resources: exit 2,
STOP. Do not fetch, chmod, install or delete to work around a refusal.

After reviewing the plan, the **same preparation command plus `--apply`** creates
only the separate private source/build/stage/home and returns `PREPARED_ONLY` and
`receipt_sha256`. Save the printed receipt digest outside that new job directory.
Do not run its CMake arrays yet. No real preparation of the owner's source was
performed during this assignment.

For optional rollback of an untouched preparation (dry-run first):

```sh
python -B -m research.portable_runtime_036 rollback --destination "$NEW_PRIVATE_JOB" --receipt-sha256 "$RECEIPT_SHA256"
```

Only add `--apply` after it reports `ROLLBACK_DRY_RUN` and all writers are stopped.
Any foreign/edited/replaced path means STOP; preserve it for owner review.

## Separately approved future build conditions — not active instructions

The plan proposes one build job, nice +10, cgroup CPU quota 100% of **one** core,
3 GiB memory hard ceiling, zero swap, 64 PIDs, wall 900s, CPU 600s, capped output
1 MiB, at least 8 GiB free disk plus source bytes and 4 GiB available RAM.
Preparation reads `/proc/meminfo` and visible cgroup-v2 memory headroom; hidden
ancestor limits, disk quotas, competing processes and future free space remain
unverified. CPU flags must include AVX/AVX2/FMA on every visible processor.
These observations do not prove instruction execution or system stability.
**No CPU/memory/time enforcement is active because compilation cannot start.**

Before a separate approved build executor can be enabled, owner review must cover:

1. Desktop-freeze cause and recorder impact remain unresolved. Confirm sufficient
   headroom and independent recorder-health observation; stop immediately on
   slowdown, freezes, missing collection, resource refusal or supervisor failure.
2. Hash/version-pin existing compiler, linker, CMake (review modern RPATH option
   support), make/ninja, bwrap, Python, loader and entire transitive toolchain;
   no auto-install. Configure itself executes compiler probes and counts as build.
3. A measured no-network mount/PID/user namespace, no credentials/model/original
   runtime/AEP/recorder mounts, read-only exported source and host toolchain,
   isolated writable build/stage/home, private tmp, clean fixed environment;
   no host network fallback. CMake download switches alone are insufficient.
4. Pre-existing delegated private cgroup with measured CPU/memory/swap/PID limits;
   wall/output watchdog, stop/kill/reap of the whole group including escaped
   descendants. No global sysctl, cgroup delegation, sudo or desktop time changes.
5. Scope-bound separate owner approval identifying source/plan/toolchain hashes,
   target, budget and one run. No inference permission. Generate a fresh plan if
   any input, limits, machine or state changes. This PR accepts no approval file
   or boolean as a substitute for containment evidence.
6. Use the two emitted arrays (`cmake -S ... -B ...`, then `--target llama-cli
   --parallel 1`) **inside that reviewed executor only**. Capture both exit codes,
   warnings, unused manually specified options, full CMakeCache and build logs.
   Unexpected configure fallback or unused security options must stop the build.

## Artifact/provenance contract and later verification

The verifier takes an explicit owner-prepared JSON manifest. This PR deliberately
has no staging operation that searches/copies host/original runtime libraries:
first review the build's actual dependency closure. A missing dependency is a
refusal, not permission to use the dynamic loader's default search directories.
Capture all required local build outputs plus independently reviewed system
libraries/loader in the **new stage** with their alias chains. Preserve originals.
Record every required ELF, not only the CLI. Interpreter path must be present in
the inventory under its root-relative path; future sandbox mount wiring to that
absolute interpreter remains unverified. No host loader fallback is accepted.
All search elements must start `$ORIGIN` and resolve within stage; empty, absolute,
escaping or unknown token elements fail, even with matching artifact hashes.

Manifest fields (`portable-artifacts-036-v1`):

```json
{
  "version": "portable-artifacts-036-v1",
  "source_commit": "0978a6e9022fb9bd6874b86154ee304e81929b9f",
  "source_tree": "5e472b707005dec79feedd0942c3814fb88b9a6d",
  "compiler": {"path": "REQUIRED", "sha256": "REQUIRED", "version": "REQUIRED"},
  "cmake": {"path": "REQUIRED", "sha256": "REQUIRED", "version": "REQUIRED"},
  "build_flags": "REPLACE WITH EXACT FLAGS OBJECT FROM research.portable_runtime_036.FLAGS",
  "environment": {"exact_clean_environment": "REQUIRED"},
  "commands": ["REPLACE WITH EXACT EXECUTED ARGV ARRAYS"],
  "dependencies": [{"name": "REQUIRED", "version": "REQUIRED", "license": "REQUIRED", "evidence": "REQUIRED"}],
  "license_evidence": {"source_MIT": "REQUIRED", "bundled_vendor_and_system_dependencies": "REQUIRED"},
  "build_record": {"approval_ref": "REQUIRED", "logs_and_cache_hashes": "REQUIRED", "containment_measurements": "REQUIRED"},
  "entries": [
    {"path": "bin/llama-cli", "sha256": "REQUIRED", "size": 1},
    {"path": "lib/libexample.so", "link": "libexample.so.1"}
  ]
}
```

The example is **not usable evidence** or an actual artifact manifest. Required
metadata presence is checked, not its truth/authenticity, package-vulnerability
clearance or legal adequacy. Dependency names/SONAMEs are not package versions.
Runtime `dlopen` outside DT_NEEDED cannot be established solely from ELF metadata;
source review and contained runtime qualification remain required. Compiler
provenance and the full toolchain dependency/licensing closure are still missing.

After a separately approved build/staging/review, these passive commands are
available (not run on real artifacts here):

```sh
python -B -m research.portable_runtime_036 verify --stage "$NEW_PRIVATE_JOB/stage" --manifest artifacts-036.json > verification-036.json
python -B -m research.portable_runtime_036 compare independent-first.json independent-second.json
python -B -m research.portable_runtime_036 handoff --stage "$NEW_PRIVATE_JOB/stage" --manifest artifacts-036.json --destination "$FUTURE_PRIVATE_BUNDLE" --protected "$ORIGINAL_RUNTIME_ROOT" > unqualified-035-inventory.json
```

`PASSIVE_ARTIFACT_CHECK` means structural checks only. Hashes and sizes are local
attestation, not publisher authenticity or reproducibility. Repeat builds must use
separate clean directories, compare all artifact bytes/aliases, exact normalized
inputs, flags, compiler/linker dependencies, environment and logs. Investigate
build paths/timestamps/build-info/debug sections if bytes differ; do not strip,
patch or relax checks to manufacture equality. Identical self-reports don't prove
independent builds; trusted independent witnesses/attestation remain required.

No model is exported or admitted. The existing Qwen2.5-1.5B-Instruct Q4_K_M must
first have **independently confirmed publisher SHA-256 and license/redistribution
review**. Self-hashing its existing file is not publisher confirmation. No download,
model/tokenizer execution, copying or permission change is authorized here.

## Evidence and acceptance disposition

Synthetic fixtures are original inert non-runnable ELF-shaped bytes, original
local Git text fixtures, controlled resource readings and no real model. Fixture
Git IDs in the JSON demonstration are **not** the reviewed upstream source.
`docs/evidence/portable-runtime-036-synthetic.json` records positive structural
checks and a deliberately corrupted-hash refusal, with all gates retained.

Focused tests cover wrong commit/tree, dirty contents/mode, missing source/symlink,
empty source file, untracked exclusion, dry-run no writes, private copies, umask
restoration, unsafe/existing/overlapping destinations, headroom/compatibility,
owned/foreign/modified rollback, receipt tampering, exact recipe, absolute/empty/
escaping RUNPATH, hash corruption, unlisted/transitive/interpreter/SONAME failures,
provenance presence, flags mismatch, repeat-report differences, CODEX035 rejection
and disabled build execution. Synthetic successes qualify none of the target gates.

Python 3.12.14 is available here, not 3.13. Existing SQLite ResourceWarning behavior
on 3.13 remains **UNVERIFIED**; no unrelated maintenance was made. New test fixtures
use a scoped restrictive umask and restore it; an inherited umask 0002 focused run
is included below. This does not certify all old fixtures on every platform.

Smallest safe owner action: review this draft and source/resource plan, then
separately decide whether to authorize development/qualification of the bounded
build executor on the actual desktop. **Do not compile yet.** Lack of a measured
executor, original freeze diagnosis, real toolchain/artifact/license provenance,
repeat-build witness, full containment and model publisher evidence are explicit
remaining blockers. No automatic inference activation follows a future build.

STOP FOR OWNER AND BOSS AI REVIEW.

## Recorded offline verification (2026-11-28)

Environment: Linux, Python 3.12.14. Commands ran from the isolated local CODEX036
source snapshot, using existing dependencies only. No skips in Python suites.

| Exact command | Actual result |
|---|---|
| `python -B -m unittest discover -s tests -p test_portable_runtime_036.py -v` | 30 passed, 0.670s |
| `python -B -m unittest discover -s tests -v` | 608 passed, 8.231s (578 existing + 30 new) |
| Focused same discovery via `unittest.TextTestRunner`, scoped `os.umask(0o002)` | 30 passed, 0.582s; prior umask restored |
| `node tests/test_paper_029.cjs` | 26 checks passed |
| `node tests/test_restore_030.cjs` | 14 checks passed, controlled storage dependencies |
| `node tests/test_market_031.cjs` | 8 groups passed, controlled dependencies |
| `python -B -m research.portable_runtime_036 status` | exit 0; executor DISABLED, exact source/base, all gates retained |
| `python -B -m research.portable_runtime_036 build` | expected exit 2; `SEPARATE_OWNER_APPROVAL_AND_CONTAINMENT_REQUIRED_BUILD_HOLD`; no subprocess started |

No native browser persistence, owner desktop, real LLVM/GCC/CMake build, target
cgroup, runtime instruction or genuine inference success is claimed. The local
cloud filesystem has only about 7.5 GiB free; a genuine preparation would refuse
the proposed 8 GiB headroom policy. Synthetic resource fixtures do not establish
real target capacity. Four files are added, zero baseline files modified.
