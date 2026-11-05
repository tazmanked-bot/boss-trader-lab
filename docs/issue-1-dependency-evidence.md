# Issue #1 dependency evidence and proposed enforceable lock

**HOLD: evidence is historical; this is not vulnerability clearance or a lock.**

## Observed owner-run evidence (2026-11-05 UTC)

Both runs checked out research commit
`1e7bee81f7ad6fa8638fcf0e81b684af485a191a`:

- Parity #3: https://github.com/tazmanked-bot/boss-trader-lab/actions/runs/42023483560/job/127231813281
- Dependency #1: https://github.com/tazmanked-bot/boss-trader-lab/actions/runs/42024459760/job/127235055600

Both logs show Python 3.11.17, pandas-ta-classic 0.9.0, NumPy 2.4.6,
pandas 3.1.1, python-dateutil 4.0.0, tzdata 2026.6. The dependency run also records
pip 26.2.2 and setuptools 79.0.1. `pip check`: `No broken requirements found.`
This checks metadata consistency, not security or mathematical correctness.

Recorded primary wheel: `pandas_ta_classic-0.9.0-py3-none-any.whl`.
SHA-256 recorded at 12:07:32.7039487Z:

```text
f9792bfc478e6ab20dc67008eea748fd5f7042a986f96dbef582b270b706cc57
```

The hash was logged after a separate `pip download --no-deps --only-binary=:all:`.
It was not enforced on installation, independently recomputed during correction,
or checked against authenticated release metadata. Transitive wheel hashes,
installed-wheel/source equivalence and provenance remain unverified.

## Proposed lock process (not implemented or approved)

1. On an authorized ephemeral Actions runner, select an explicit OS/architecture
   and exact Python patch. Review wheel metadata, license notices and advisories
   for each package; include pip/setuptools in the toolchain inventory.
2. Download all selected wheels from the approved index; record exact names,
   versions, SHA-256 hashes and authoritative metadata/provenance. Include NumPy,
   pandas, python-dateutil, tzdata and any additional resolved dependencies.
3. Commit a reviewed platform-specific requirements lock with `==` for EVERY
   package and approved `--hash=sha256:...` entries for EVERY selected wheel.
   The primary hash above alone cannot form this lock. Do not invent missing
   hashes or describe `pip freeze` as a hash-enforced installation.
4. Download with `python -m pip download --require-hashes --only-binary=:all:
   -r <reviewed-lock> --dest <wheelhouse>`; install into a fresh venv using
   `python -m pip install --no-index --find-links=<wheelhouse> --require-hashes
   --only-binary=:all: -r <reviewed-lock>`. Each displayed command is one line.
   Run `pip check`, record versions, and run the complete synthetic suite.
5. Retain commit-linked logs, lock, wheel hashes and SBOM. Pin Actions to reviewed
   commit SHAs and record the runner image version. A locked wheel set reduces
   variability but does not itself prove trustworthy builds or full runner
   reproducibility. Changes require fresh owner review.

## License/security gaps

- pandas-ta-classic and BOSS Trader Lab declare MIT; preserve notices when
  redistributing. The exact wheel notices and source correspondence need review.
- Review exact installed NumPy/pandas/python-dateutil/tzdata licenses and bundled
  native/data components; do not infer a complete license inventory from one
  upstream project's license.
- No complete advisory scan was verified for these exact versions or the pip/
  setuptools toolchain. Audit-002's GitHub advisory endpoint was inaccessible.
  Record advisory source, timestamp, affected ranges, fixes and applicability;
  no search result or successful `pip check` establishes vulnerability clearance.
- Direct-only pinning permits future transitive drift. Current evaluation
  workflows deliberately remain labeled un-locked pending reviewed hashes.
- Current Actions version tags, ubuntu-latest and Python 3.11 patch selection
  are mutable. The research branch checkout is mutable but prints its SHA.
- These old green runs do not verify the corrected full-series validator.

PR #4 remains draft/unmerged; Issue #1 remains open pending actual corrected-run
evidence and owner review. No production integration or paid infrastructure is
introduced by this evidence document.
