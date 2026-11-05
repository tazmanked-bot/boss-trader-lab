# PR #4 — Owner integration decision (2026-11-05)

**Approved scope:** merge research tooling, synthetic indicator tests, integrity verifier, lock/manifest, and manual-only evidence workflows to the public repository's `main` branch. This is **not** an approval for production indicators, trading signals, orders, or automatic schedules.

## Basis
- Corrected numerical comparisons: owner GitHub Actions parity run [42027594747](https://github.com/tazmanked-bot/boss-trader-lab/actions/runs/42027594747) and dependency run [42027924685](https://github.com/tazmanked-bot/boss-trader-lab/actions/runs/42027924685), both testing `1d5452f98d509d0de602e3cc30a4929493a37038`.
- Hash-enforced installation and wheel/source/RECORD integrity: owner [integrity closeout run 42034389308](https://github.com/tazmanked-bot/boss-trader-lab/actions/runs/42034389308), testing `f0058623b32fc99a50ae27e7534c22703a3040c0`, with evidence retained separately from the public repository.
- A later research-only commit `4cbb35cedb41a4e687a3a145a5d89e024d71c267` corrects a GitHub workflow invalid job-level `runner.temp` context, equivalent to an owner-verified main-launcher fix. This last workflow edit has not been independently executed.
- The review of PR #4 showed **new research, tests, docs, and manual workflows only**. It does not modify `boss_trader_lab.py`, `kraken_public_observer.py`, or the active Kraken manual workflow.

## Explicit continuing restrictions
- No automatic trading, orders, credentials, scheduled monitoring, signal promotion, or investment-performance claim.
- No production dependency on pandas-ta-classic in the live Kraken scanner. The isolated research lock applies only to CPython 3.11.17 / Ubuntu 24.04 x86_64.
- Dependency artifact identity is verified for the tested isolated environment, **not** a publisher provenance attestation or reproducible source build.
- OSV reports recorded no listed vulnerabilities for the five runtime package versions at the recorded query time; historical setuptools host-tool advisories require platform/path-aware triage. This is not complete security clearance.
- Runtime wheel notice files were collected and hashed, but binary redistribution would require fulfilling all applicable bundled component notices. Nothing is vendored here.
- Research workflow action tags and runner images may change; manually run and review evidence before changing integration scope.
- Issue #1's *production-adoption* gate remains open pending explicit separate owner authorization and regression evidence; research-only merge does not waive that gate.
- ZUMERAVO remains separate.

## Decision
**MERGE RESEARCH ONLY** after owner-approved PR review. Track future **production scanner integration** under a separate PR and explicit safety gate. Historical evidence documents may still contain original pre-execution HOLD statements; those are preserved as point-in-time records and are superseded for research merge by this decision.
