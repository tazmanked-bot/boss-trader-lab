# CODEX 033 — offline llama.cpp analyst preparation

Issue #61. Baseline: Draft PR #60 at
`189b851e8a3f2ffd50b3e29003ee318186e08dce`, verified unchanged. CODEX 032 is
conditionally accepted as a synthetic prototype, not merged. Dedicated branch
`research/issue-61-offline-llama-adapter`, stacked Draft PR targeting
`research/issue-59-offline-decision-loop`. README/SECURITY, #59/#61 and the prior
implementation/evidence reviewed. No AGENTS.md in the baseline tree.

**Implemented and offline-tested; genuine inference REAL_NOT_RUN.** No model or
runtime downloaded, installed or executed. No owner desktop access. Additional
expenditure NT$0. Operational local strategies/recorder remain unavailable and
untouched; no integration claim. Existing source/clock gates and BUY AUTHORIZATION
NONE are unchanged.

## Working commands

```sh
python -B -m research.llama_analyst_033
# REAL_NOT_RUN; no file access or subprocess.
python -B -m research.llama_analyst_033 --stub-demo
# ONLY the packaged controlled fake Python program; not llama.cpp or AI.
python -B -m unittest discover -s tests -p test_llama_analyst_033.py -v
```

[Executed stub demonstration](artifacts/llama-analyst-033-stub-demo.json):

| Case | Actual controlled result |
| --- | --- |
| Valid stub JSON | 3 synthetic WATCH research candidates, 1 missing-evidence BLOCKED event; three direct processes reaped |
| Stub exit 7 | 0 candidates, all three eligible leads BLOCKED / PROVIDER_UNAVAILABLE; three failure receipts, processes reaped |
| Real runtime/checkpoint execution | **0**; REAL_NOT_RUN |

The valid stub deliberately returns SUPPORT for all three qualified symbols;
this is not a change to the original MOCK's SOL rejection or a discovery by Qwen.
A separate regression changes one volume condition: SUPPORT still produces WAIT /
RISK_RULE_VETO and zero candidates. The unchanged journal chain verifies.
All demo runtime/model files are fabricated 39-byte sentinels, never executable
llama.cpp/GGUF weights. Even the fake executable path from the manifest is never
launched; only the digest-pinned packaged Python stub is launched via the current
Python interpreter. The GGUF magic in the sentinel is a test, not model validity.
Receipts explicitly say SIMULATED_STUB_NOT_AI, real_inference false, no measured
model tokens, zero additional cost, and no order authority. Raw stderr and private
paths/environment values are not published.

## Adapter preparation API

`PreparedAnalyst(manifest).plan(request)` validates an owner-supplied manifest,
rehashes local files without executing them, recomputes original rule evidence,
builds a compact prompt and strict JSON schema, and returns an immutable Plan.
`PreparedAnalyst.infer(...)` **always refuses** with
REAL_NOT_RUN_CONTAINMENT_AND_OWNER_GO_REQUIRED. There is no --real flag, trust
boolean, identity string or manifest value that enables real execution. CODEX 032
still defaults to its existing MOCK adapter; a REAL_NOT_RUN identity is not an
accepted inference provider. Relabeling the prepared adapter as MOCK still cannot
make its infer method execute anything or produce a candidate.

`command(manifest, plan, prompt_path)` returns argv only, rechecks manifest identity
and file pins, and never launches it. `simulate(plan, scenario)` invokes only the
fixed test stub. `StubLoopAnalyst` is an explicitly MOCK regression bridge into the
unchanged CODEX 032 schema/risk/journal; it is never a real model wrapper.

Manifest template:
[llama_analyst_033.manifest.example.json](../research/llama_analyst_033.manifest.example.json).
It is intentionally invalid until owner paths/digests/revision are filled in.
Required: absolute runtime and GGUF paths, lowercase SHA-256 pins, declared
Qwen2.5-1.5B-Instruct-Q4_K_M, pinned llama.cpp source commit, and explicit pending
license review. No URLs, cache/model identifiers, account keys, environment-path
search or provider endpoints are accepted. Unknown fields refuse.

Preparation refuses missing/nonregular/empty/oversized files, group/world-writable
artifacts, nonexecutable runtime, symlink path components and mismatched digests.
Runtime cap 128 MiB; model cap 2 GiB, streaming hashes in <=1 MiB chunks; metadata
is checked around hashing. GGUF magic is checked. These are size/type/pin controls,
not proof of model architecture, quantization, tokenizer, publisher or license.
Owner-write/race, filesystem replacement and dynamic-library provenance remain
reasons for read-only target mounts and containment; path checks alone do not
eliminate TOCTOU. Preparation hashing is size-bounded, not a hard-time guarantee.

## Compact request and context

The existing `analyst-request-v1` must have exact fields, matching evidence digest,
source/symbol/time, complete validated candle prefix and unchanged rule result.
The adapter independently recomputes the existing evaluator to reject supplied
score/features or reference tampering. It preserves all four passed/strength
features, score, symbol, source kind, as-of and evidence reference in the prompt.
Full candles and original untrusted prose remain in the journal referenced by the
digest; they are not silently tail-truncated to fit. This narrow analyst consumes
validated numerical features, not full-history analysis. It may explicitly abstain
or report missing information. Raw external prose is excluded entirely and replaced
by its hash, preventing literal instruction/ChatML injection through that field.
This is not a general proof against semantic/model prompt injection or hallucination.

Prompt: explicit Qwen ChatML-style system/user/assistant delimiters; ASCII canonical
JSON; no conversation history, tools or arbitrary extra prompt. A BTC fixture prompt
measured **988 bytes**. Input cap 1408 ASCII bytes, template/tokenizer allowance 128,
output ceiling 512 tokens, context 2048. Preparation refuses excess rather than
truncating critical evidence. Byte-plus-reserve is a conservative **assumption**, not
an actual tokenizer count: reviewed tokenizer behavior, BOS/special tokens and the
real budget must be checked on target before activation. No actual token count or
model latency has been measured here.

Grammar schema fixes `analyst-v1`, exact evidence reference array, disposition enum,
required nonempty hypothesis/objection/invalidation and bounded missing-information
strings, with no extra fields. Independently validate UTF-8, one complete JSON
object, duplicate fields, exact schema/references and nonempty objection after
runtime output. No code fences, log stripping, repair retries or fallback. A valid
schema does not establish factual reasoning or correct objections. Existing
missing-information/abstention handling and deterministic risk veto remain final.

## Exact proposed CLI compatibility profile

Pinned documentation/code inspected, not executed:
[llama.cpp CLI README](https://github.com/ggml-org/llama.cpp/blob/6d8a8886fa44a4a404c58ace93052ea680193981/tools/cli/README.md)
and [argument implementation](https://github.com/ggml-org/llama.cpp/blob/6d8a8886fa44a4a404c58ace93052ea680193981/common/arg.cpp).
This is a reference for the following flags, **not a pin of the owner's unknown
binary**, build options, shared libraries or tokenizer.

Prepared argv (not executed): explicit owner runtime, `--offline`, explicit `--model`,
`--ctx-size 2048`, `--n-predict 512`, `--threads 2`, `--batch-size 128`,
`--gpu-layers 0`, `--temp 0`, `--seed 0`, `--no-conversation`, `--no-display-prompt`,
`--simple-io`, `--log-disable`, `--no-perf`, `--no-warmup`, `--json-schema` with the
exact schema and `--file` with a prepared prompt. No shell, server, remote model
flag, automatic download, cache fallback, credentials or tools. Manual ChatML prompt
plus no-conversation mode is an explicit compatibility assumption. Target must
verify flags, special-token/template behavior, grammar support, deterministic
sampling caveats and JSON-only stdout. Unsupported warnings/banners on stdout
refuse; they are not heuristically removed.

Qwen2.5-1.5B-Instruct Q4_K_M is the requested candidate, previously used by the owner;
its actual availability, format, publisher/conversion provenance, license/notices,
digest, tokenizer and runtime compatibility are **UNVERIFIED**. Model-family names
or previous usage are not permission/identity evidence. The legacy QwenLM/Qwen2.5
GitHub endpoint returned Moved Permanently in this review; no model/license clearance
is inferred from that response. No weights/model card were downloaded. Review the
specific supplied GGUF and its upstream base/conversion licenses on target. The
public repository's MIT license does not license third-party weights or data.

## Implemented controls versus target isolation

| Area | Implemented/tested with controlled program | Still unverified for real inference |
| --- | --- | --- |
| Lifetime | 30s application budget includes setup/read/wait checks; selector loop, nonblocking stdin/stdout/stderr; no retry | Popen/kernel startup or stalls cannot be preempted by Python; no hard target deadline claimed |
| Output/input | Combined stdout+stderr <=8192 bytes, <=1024-byte reads; prompt <=1408; exact flags/token ceiling | Real tokenizer count, context clipping behavior and compliant JSON output |
| Cleanup | Fresh POSIX session, group SIGKILL on completion/failure, direct-child wait/reap <=1s application allowance; uncertain cleanup poisons process-wide lock | Escaped descendants, kernel kill/reap latency, cgroup/process-tree containment |
| Concurrency | Nonblocking lock, one launch per Python process; POSIX single-main-thread required | Cross-process coordination and owner runner-wide quota |
| Environment | Explicit small allowlist, empty temporary HOME/cwd, PATH=/nonexistent, no inherited model flags, proxy/API credentials or LD_PRELOAD; descriptors closed | Dynamic loader/library trust; full OS sandbox and inherited kernel permissions |
| CPU/memory | Stub child RLIMIT_AS <=4 GiB, CPU <=30s, NOFILE <=32, CORE=0, FSIZE=0; threads flags 2 | Qwen RSS, total process-tree memory, KV/model mappings, actual CPU/latency, cgroup limits |
| Filesystem/network | Private temp workdir, umask 077, file-size write limit, fixed executable stub and digest | **Not** a filesystem or network jail: network namespace/seccomp and read-only allowlist mounts needed |

The controlled environment probe actually read child address-space/FD limits and
zero core/file-size limits and confirmed no inherited test secret/model flag.
Limits tests also verify setup parameters. This does not measure real model peak
RAM or prove no filesystem/network access by an arbitrary runtime. `--offline` is
an application flag, not an OS network block. FSIZE=0 does not stop reads or creation
of all filesystem object types. Real execution remains disabled for these reasons.
The subprocess helper is private trusted preparation code, not an exposed command
runner or sandbox for hostile code. Supported stub process-control behavior cannot
clear B1–B5 for genuine market/model operations.

## Target verification runbook — desktop recovery required

**Preparation only; actual model invocation needs a separate owner GO after
containment is independently verified. Do not infer permission from this runbook.**

1. Owner identifies existing local llama-cli and checkpoint; do not download,
   install, search private directories automatically or access accounts. Record
   exact SHA-256, source/build commit, build options, shared-library provenance,
   file size, model publisher/conversion provenance, GGUF architecture/quantization,
   tokenizer/template and license/notices. Keep private paths/desktop IDs local.
2. Fill the example manifest locally. Hash commands such as
   `sha256sum /OWNER_SUPPLIED/llama-cli /OWNER_SUPPLIED/model.gguf` read local bytes
   only; the owner must substitute reviewed paths. The template's placeholders
   intentionally fail. Do not substitute a mirror or infer pins from filenames.
3. Produce a synthetic request with the existing loop (no genuine model):

   ```python
   import json
   from pathlib import Path
   from research import decision_loop_032 as loop
   fixture = json.loads(Path('tests/fixtures/decision_loop_032.json').read_text())
   class Capture(loop.MockAnalyst):
       def infer(self, request):
           with open('new-synthetic-request.json', 'x') as out:
               out.write(loop.canonical(request))
           return super().infer(request)
   loop.run({**fixture, 'leads': fixture['leads'][:1]}, Capture())
   ```

4. Run preparation, **not inference**:

   ```sh
   python -B -m research.llama_analyst_033 --prepare owner-manifest.json --request new-synthetic-request.json
   ```

   Expected REAL_NOT_RUN, matching hashes/byte sizes, bounded prompt and activation
   DISABLED_PENDING_TARGET_CONTAINMENT_AND_OWNER_GO. This CLI smoke was tested here
   with fabricated sentinels, not real owner artifacts. It never runs --help,
   --version or any checkpoint code, even if paths/digests are valid.
5. Independently qualify a target isolation profile: deny network at OS level;
   read-only runtime/model/library mounts with minimal filesystem visibility;
   writable private scratch only, no home/recorder/journal/credentials; process
   namespace/cgroup cleanup, memory/CPU/FD limits, cross-process concurrency one
   and measured timeout/reaping. Verify libraries and environment. Preserve
   disabled real mode if any containment property is unknown/unsupported. This
   PR supplies no trust flag that can waive this requirement.
6. After a **new owner authorization**, a follow-up implementation may wire the
   prepared argv to that independently verified executor. Before evaluating any
   model output, confirm exact prompt token count plus output/template margin,
   GGUF/template/grammar compatibility and no downloads/network access. Measure
   startup, peak RSS/process-tree memory, CPU/latency and cleanup on target; verify
   the proposed 4 GiB/30s profile fits or fail closed for review. Do not silently
   relax limits or drop critical evidence to get a passing run.
7. Fixed cases for that future real validation: qualified candidate, rule-only
   WAIT, missing/stale data, unknown refs/extra fields, empty objection, prompt
   injection, conflicting evidence, output/context limit, timeout/nonzero/error,
   repeated deterministic input. Compare real outputs with unchanged MOCK and
   rule-only baseline using the same closed evidence prefixes. Report actual
   token usage if measured, otherwise null; no fictitious token/cost figures.
   Schema-valid but factually unsupported hypotheses must not be treated as
   validated reasoning or better returns. Record model/runtime/prompt/policy
   hashes, objections, abstentions, gaps and timing; never grant BUY authority.

## Exact offline results

| Command | Actual result |
| --- | --- |
| `python -B -m unittest discover -s tests -p test_llama_analyst_033.py -v` | 17 passed, 0.456s |
| `python -B -m unittest discover -s tests -v` | 534 passed, 7.137s, no skips |
| `node tests/test_paper_029.cjs` | 26 checks passed |
| `node tests/test_restore_030.cjs` | 14 checks passed |
| `node tests/test_market_031.cjs` | 8 controlled groups passed |
| Default adapter CLI | REAL_NOT_RUN; no file or process |
| Preparation CLI with fabricated sentinels | REAL_NOT_RUN; 988-byte prompt; no model execution |
| `--stub-demo` | success and nonzero cases above; journal chains verify |

New tests cover pins/unavailable paths, symlinks/type/permissions/magic/size,
manifest changes, compact context/ref/numerical tampering, excluded injection
prose, fixed argv, malformed/extra/duplicate/unknown-ref/no-objection output,
timeout, both stream byte limits, direct process reaping, poisoned cleanup state,
concurrency, environment/resource profile, default no-I/O, stub digest pin and
unchanged risk veto/immutable journal. The uncertain-cleanup test actually reaps
the child before simulating an unprovable cleanup result, so it leaks no process.
No GGUF executable/model inference, server, downloads, provider calls, runtime
installations or external inference occurred.

## Scope, blockers and next owner step

New preparation module, manifest template, pinned fake program, focused tests,
synthetic stub artifact and this report only. Existing decision loop/risk/schema,
MOCK default, strategies, recorder, dashboard/journal, source/clock safeguards,
main, prior PRs and workflows stay unchanged. No personal data, account balances,
private notes, machine IDs or real weight bytes are committed.

Blockers: recovered owner target; reviewed executable/checkpoint pins and licenses;
compatibility/tokenizer and true resource measurements; independently verified
filesystem/network/process isolation; separate authorization and follow-up wiring
for genuine inference. Current preparation is usable without those by remaining
REAL_NOT_RUN. Next actionable owner step is inspect the Draft PR and retain the
manifest/runbook for passive target verification after desktop recovery. Do not
activate a real model now.

B1/B2/B3/B5 HOLD; B4 NO-GO; real source admission HOLD; BUY AUTHORIZATION NONE.
NT$0 additional spend. No trading, credentials, accounts, paid APIs, deployment,
merge, dispatch, scheduled work, ZUMERAVO or other-project changes.

STOP FOR OWNER AND BOSS AI REVIEW.
