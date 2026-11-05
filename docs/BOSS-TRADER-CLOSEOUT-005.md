# BOSS-TRADER-CLOSEOUT-005 — evidence preparation, owner run pending

Date: 2026-11-05 UTC. Authorization: [Issue #6](https://github.com/tazmanked-bot/boss-trader-lab/issues/6).
Scope: Issue #1 / Draft PR #4. **Integration remains HOLD.**

## Observed evidence, distinguished from new work

Audit-004 verified owner parity #4 and dependency #2, both actually checking out
`1d5452f98d509d0de602e3cc30a4929493a37038`:
- https://github.com/tazmanked-bot/boss-trader-lab/actions/runs/42027594747/job/127245608000
- https://github.com/tazmanked-bot/boss-trader-lab/actions/runs/42027924685/job/127246702285

Each passed 31 distinct unit tests and repeated the 18 validator regressions.
Both passed all seven indicator series over five 180-bar fixtures. The dependency
run passed pip check, but used an un-locked installation. Those runs do NOT prove
the new locked installation or installed-file identity. No new Actions run has
been dispatched during assignment 005.

## Hash lock and platform

`research/requirements-cp311-linux-x86_64.lock` pins every observed runtime
distribution. Intended evidence target: CPython **3.11.17**, Ubuntu **24.04**,
Linux x86_64, glibc >=2.28. No Windows, macOS, musl, ARM or other Python ABI
coverage is claimed. Wheels are selected explicitly, not resolved to arbitrary
platform variants. Public PyPI release-file pages were independently inspected
on 2026-11-05, and each filename/hash pair was recorded in
`research/dependency-manifest.json`.

| Runtime package | Authoritative published wheel SHA-256 |
| --- | --- |
| pandas-ta-classic 0.9.0 | `f9792bfc478e6ab20dc67008eea748fd5f7042a986f96dbef582b270b706cc57` |
| numpy 2.4.6 | `89cd468399cfd2504718f0ba50e410dca55a170b61a02ad92bb18c8a65186e93` |
| pandas 3.1.1 | `4f1602f614bb83f443381dbcbb94c4ac764b2e50c8d6c965614c5cd83e328c47` |
| python-dateutil 4.0.0 | `a5e246f79eb80475e691bf93862cead98decd8a498cf53ba0516fcdc0f50dc1c` |
| tzdata 2026.6 | `0a10eec6e13ef16b627fabed9a5f2ba61a62b1c67f327305f4e7e412a70b4aec` |

Direct dependency: pandas-ta-classic. It requires NumPy and pandas; observed
transitives are python-dateutil and tzdata. Runtime closure is asserted by an
exact installed-distribution set plus pip check. If current METADATA reveals
another required dependency, installation/check must fail, not silently extend
the lock. These are observed versions, not recommendations to adopt newer ones.

Each manifest row records the exact wheel filename and authoritative
`https://pypi.org/project/<name>/<version>/#files` URL. The runner rechecks the
PyPI JSON release endpoint and downloaded bytes against this committed manifest.

The target venv is created with `--without-pip`. pip and setuptools therefore
are NOT omitted runtime dependencies: they are not installed in that venv at all.
The host installer/toolchain is separately inventoried and is not claimed to be
a fully hash-locked build environment.

## Verifiable installation chain

The manual evidence runner performs:
1. Checkout a specific research revision without persisted credentials.
2. Fetch exact release JSON and only the five named wheels using HTTPS.
3. Reject yanked releases, wrong hosts, changed SHA-256 values, inconsistent
   wheel METADATA, unsafe ZIP paths and invalid wheel RECORD hashes.
4. Compare wheel RSI/RMA/ATR source bytes with reviewed immutable upstream source
   digests from commit `9c1e0ca16f1decf2cb39823f0e229e17d97bafb2`.
   The source digest computation was also checked against GitHub's blob SHA-1
   object identity. A source mismatch fails; do not replace the digest to get green.
5. Install into the empty venv using the host pip's `--python` option,
   `--isolated --no-index --find-links=<verified-wheelhouse> --require-hashes
   --only-binary=:all: --no-compile`; record pip's installation report.
6. Assert exactly five target distributions and compare **every wheel payload
   file** byte-for-byte against installed content. Verify installed RECORD
   SHA-256 and file sizes, including installer-created metadata.
7. Rerun baseline, corruption tests, and full-series indicator parity in that
   isolated environment. The old installation cannot satisfy this new check.
8. Retain release JSON, install report, wheel/installed inventories, source
   comparisons, notices, toolchain inventory, advisory responses and runner facts.
   The upload uses a one-day retention policy; owner must preserve reviewed
   evidence before expiry. Wheel binaries and the venv are excluded from upload.

A recorded wheel hash is not installed-artifact proof. A new successful identity
stage supplies that proof for the fresh runtime only, not retrospective proof
for earlier runs. Byte equality is not a reproducible-build or publisher-identity
attestation. PyPI reports no provenance / no Trusted Publishing for the
pandas-ta-classic 0.9.0 wheel; this remains a documented supply-chain limitation.

## License and notice inventory

Published declarations inspected during Audit-004:
- pandas-ta-classic 0.9.0: MIT.
- NumPy 2.4.6: BSD-3-Clause AND 0BSD AND MIT AND Zlib AND CC0-1.0.
- pandas 3.1.1: BSD-3-Clause.
- python-dateutil 4.0.0: BSD-3-Clause metadata; contribution history has
  BSD/Apache alternatives, so inspect the actual notice text.
- tzdata 2026.6: Apache-2.0.

Authoritative package pages are listed in the manifest. Exact runtime wheel
LICENSE / COPYING / NOTICE / COPYRIGHT / AUTHORS paths and SHA-256 values are
collected, preserving their original content, including bundled-library notices.
Wheel metadata records License-Expression, License-File and Requires-Dist.
The existing host pip/setuptools notice files are inventoried separately.

**HOLD:** declared metadata is not a completed distribution-notice review.
Review every collected notice, attribution, redistribution condition and bundled
native/data component. Do not label the entire binary distribution simply MIT.
No third-party source is vendored by this assignment; only source digests are stored.

## Security triage and coverage

Primary advisory checked on 2026-11-05:
https://github.com/pypa/setuptools/security/advisories/GHSA-h35f-9h28-mq5c

It lists setuptools <=82.0.1 as affected and no patched version. Thus historical
79.0.1 falls in the affected range. The vulnerable path concerns building sdists
and Unicode-normalization exclusion rules, especially macOS APFS/HFS+.
The observed runs installed wheels on Ubuntu; no sdist-build/publishing path was
shown. This is **affected version, vulnerable path not observed**, not a claim
that setuptools is safe. The new target runtime excludes setuptools and pip and
accepts only wheels, so no runtime sdist build is introduced. Host tools are
still recorded and require separate triage.

The prepared runner queries https://api.osv.dev/v1/query for every exact runtime
version, observed host pip/setuptools versions, and historical setuptools 79.0.1.
It retains complete responses, advisory IDs, exact requests and query timestamps.
PyPI release JSON is retained too. Endpoint failures become UNVERIFIED; findings
require owner applicability review. A successful evidence job does NOT mean no
vulnerabilities. No search result, absent advisory or pip check proves clearance.
OSV/PyPI coverage excludes unknown issues, a full source audit, and complete
OS/CPython/Node/native-bundled-component scanning. No such clearance is claimed.

## Workflow pinning and owner action

New closeout workflows pin these GitHub action commits, resolved from upstream
refs on 2026-11-05:
- actions/checkout: `11d5960a326750d5838078e36cf38b85af677262` (observed v4).
- actions/setup-python: `a26af69be951a213d495a4c3e4e4022e16d87065` (observed v5).
- actions/upload-artifact: `ea165f8d65b6e75b540449e92b4886f43607fa02` (observed v4).

References: https://api.github.com/repos/actions/checkout/git/ref/tags/v4 ,
https://api.github.com/repos/actions/setup-python/git/ref/tags/v5 ,
https://api.github.com/repos/actions/upload-artifact/git/ref/tags/v4 .
These are identity pins, not a completed security audit of each action.
The old Node 20 action migration warning may persist; upgrading action majors is
a separately reviewed change. Ubuntu 24.04 pins the OS family, not its image;
the actual image version, OS release, libc and exact Python version are recorded.

The research workflow `manual-dependency-closeout.yml` checks out its immutable
run SHA. Issue #6 explicitly permits a justified manual read-only temporary-runner
launcher on main. A **new** `launch-integrity-closeout.yml` is provided there
because GitHub normally exposes workflow_dispatch from the default branch and
the connector has no dispatch operation. It checks out the fixed research
closeout commit, not a mutable branch. It changes no existing main workflow or
scanner, has contents:read only, has no schedule, and retains no checkout token.

Smallest safe owner action: open Actions → **BOSS Trader owner-run integrity
closeout (Issue 6)** → Run workflow on main. Verify the checkout SHA against the
research closeout commit, then review/download its evidence artifact within one
day. No PR merge is required. Do not rerun the old dependency launcher and assume
it exercises this lock. Do not treat job success as automatic integration approval.

## Closeout classification before owner execution

| Check | Result |
| --- | --- |
| Full runtime lock definition and authoritative published hashes | PASS — prepared and checked |
| Actual hash-enforced install / dependency closure | HOLD — new owner-run evidence required |
| Installed wheel / RECORD / reviewed source identity | HOLD — verifier prepared, no new run yet |
| Exact distribution-notice inventory and obligations | HOLD — collection and review pending |
| setuptools advisory version/path triage | PASS scoped — affected version; vulnerable path not observed |
| Complete vulnerability assessment | HOLD — dated API coverage and owner triage pending |
| New workflow action/Python/checkout pins | PASS in definition; execution/image/toolchain limits remain |
| Full environment/build reproducibility | HOLD — not claimed |

PR #4 remains draft/unmerged. Issue #1 stays open. Working Kraken, existing
production workflows, credentials, live trading and ZUMERAVO are outside scope.
STOP FOR OWNER REVIEW.
