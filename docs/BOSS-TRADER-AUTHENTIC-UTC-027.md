# BOSS-TRADER-AUTHENTIC-UTC-027

Issue: https://github.com/tazmanked-bot/boss-trader-lab/issues/49
Inspected main: 7043e1715d12406c2ae59bfe25f99c45731466b8 (merged PR #48).
Documentation checked: 2026-11-06. Existing [026 model/report](BOSS-TRADER-RUNNER-UTC-026.md) and utc_evidence_026.py were inspected and remain unchanged.

## Decision

NTS-capable chrony is a practical candidate for authenticating a time association, conditional on an independently available, reviewed client and trust bootstrap. The reviewed status exports alone do not establish an independently verifiable UTC bound <=2s. No authentic provenance was collected, no target client was verified, and no authority/client was invoked.

| Required status | Finding |
| --- | --- |
| NTS_PROTOCOL_SUPPORTED_BY_DOCS | Supported by authoritative protocol/client documentation |
| TARGET_CLIENT_CAPABILITY_UNVERIFIED | Ubuntu24/Python3.11.17 not checked; local presence does not transfer |
| AUTHENTIC_PROVENANCE_NOT_COLLECTED | No TLS/NTS-KE/NTP association, authentic packet proof or controlled collector receipt |
| B4_NO_GO | Independent bootstrap, accuracy, timestamp acquisition and provenance remain missing |
| B1/B2/B3/B5 | HOLD; no real network/source or hard containment clearance |
| Real Kraken admission / trading authority | HOLD / NO ORDERS |

Four additions only: research/nts_chrony_evidence_027.py, tests/test_nts_chrony_evidence_027.py, tests/fixtures/nts_synthetic_receipt_027.json and this report. No observer/scanner/transport, existing UTC policy, tests or workflow changes. No installations, time setting, keys, time queries, Kraken requests or merge.

## Version-specific source evidence

All links below are documentation reads, not approval of a provider or a claim of service availability.

| Source | Verified behavior and implication |
| --- | --- |
| [RFC 8915](https://www.rfc-editor.org/rfc/rfc8915.html), §§3–5, 8.5–8.7 | TLS-authenticated NTS-KE and authenticated NTP are separate stages. Certificate bootstrap and asymmetric delay remain security concerns; no unapproved plain-NTP fallback. |
| [chronyd 4.6](https://chrony-project.org/doc/4.6/chronyd.html), OPTIONS; cross-checked [4.9](https://chrony-project.org/doc/4.9/chronyd.html) | -Q prints an offset without correcting the clock; -q sets it. -Q can operate without root only with an appropriate limited configuration. It still performs time-service operations; neither option was run. -t is a process timeout, not a proof of all OS/network resource bounds. |
| [chrony.conf 4.6](https://chrony-project.org/doc/4.6/chrony.conf.html), nts, certset, ntstrustedcerts, nosystemcert, nocerttimecheck; cross-checked [4.9](https://chrony-project.org/doc/4.9/chrony.conf.html) | NTS and trust-store selection are documented. nocerttimecheck disables certificate date checks and carries security implications; default is zero. This project does not adopt that workaround. Pinning a CA alone does not establish current UTC. |
| [chronyc 4.6](https://chrony-project.org/doc/4.6/chronyc.html), tracking/authdata/ntpdata; cross-checked [4.9](https://chrony-project.org/doc/4.9/chronyc.html) | authdata reports mode, establishment/cookie status; ntpdata reports authentication and timestamps; tracking reports clock error terms. These are client reports, not a documented publicly verifiable signed receipt. Default chronyc may contact a Unix socket then loopback IP; even tracking is not this assignment's passive inventory. |
| [chrony documentation index](https://chrony-project.org/documentation.html) and [release history](https://chrony-project.org/news.html) | Current published release is 4.9 (2026-08-27). 4.6 is the issue's pinned reference, not the current release or a recommended installed build. The 4.6.1 history notes NTS AEAD key compatibility changes. Review the actual build and negotiated algorithm; do not generalize a 4.6 fixture to a deployed binary. |
| [Cloudflare NTS description](https://developers.cloudflare.com/time-services/nts/) | Publishes NTS/client support. No provider identity, key, endpoint, availability or accuracy is approved or invented here. |

NTS uses symmetric association keys after authenticated key establishment. A third party cannot establish packet authenticity merely from a packet hash or copied status text. Exporting session keys would expose authentication material and is not this design. A signed attestation from a separately trusted collector would prove only that collector's assertions unless its client/source/time acquisition is also independently justified.

## Passive capability prerequisite implemented

Default import/CLI launches no process, samples no clock and reads no files. Explicit opt-in:

```sh
python -B -m research.nts_chrony_evidence_027 --offline-inventory
```

The inventory checks exactly /usr/sbin/chronyd, /usr/bin/chronyd, /usr/bin/chronyc and /usr/sbin/chronyc. No PATH search, daemon startup, version subprocess, chronyc command, package-manager operation, configuration/certificate/key read, DNS or network call exists.

For a present file, it requires a no-follow regular executable, hashes at most 16 MiB in 64 KiB chunks, checks metadata before/after and closes its descriptor. Four paths maximum; a shared five-second monotonic budget is checked between file operations. Kernel/filesystem calls are not hard-preemptible, so this is an input/read cap, not a worst-case OS time guarantee. Symlinks/special files, permission failures, changed files and unsupported capabilities refuse or remain unavailable. Nonstandard locations are unsearched, not evidence that the entire host lacks chrony.

Version is NOT_EXECUTED; package/build provenance and compiled TLS/NTS capability remain UNVERIFIED even for a hashed file. No version/capability execution adapter is implemented, so no subprocess command can be enabled by a flag. A future bounded version-only allowlist would need separate review against the exact actual build. Binary hash or a claimed +NTS banner would identify an observation, not authenticate an association.

### Actual local result

Debian 13.6, Linux 6.18.57 x86_64, Python 3.12.14:
- All four checked paths: ABSENT.
- inventory_status: CLIENT_UNAVAILABLE.
- requests=0; process_launches=0; all HOLD/NO-GO states retained.

This is not an Ubuntu24/Python3.11.17 inventory. No assertion is made about packages, executable versions, TLS support or permissions on that target. Inventory exit 0 means the passive check completed, not that a client or B4 passed.

## Future authentic receipt contract — not implemented trust

A future receipt must be immutable, strictly bounded, bound to an approved collector/format and integrity-protected across its trust boundary. Unknown evidence or schema must refuse. Redacted hashes identify artifacts; they are not signatures or trust anchors.

| Field group | Required source and verification |
| --- | --- |
| Context / freshness | Exact reviewed revision, run ID, boot identity, fresh challenge nonce and association/measurement ID; independently acquired local send/receive monotonic + suspend-inclusive boottime windows, trusted receipt time, age and finite lease; one-time consumption and persistent restart/replay rules |
| Client/build | Exact binary/version/build/hash, package provenance, TLS/NTS compile capability, reviewed dependency/configuration hashes, isolated process identity and OS permissions; source-controlled reader cannot substitute its own client or local IPC endpoint |
| Approved authority/bootstrap | Separately approved authority identity and trust-anchor/certificate fingerprints, service identity, certificate chain and date-validation evidence under independently justified bootstrap time; missing/uncertain bootstrap refuses |
| NTS association | Verified TLS >=1.3/NTS-KE success, negotiated NTP identity and reviewed AEAD, authenticated NTP extension checks, matching unpredictable unique identifier, successful packet validation, no plain fallback, association continuity and freshness |
| Cookies/replay | Redacted association/cookie references and provenance from the verified client; no raw cookie/key export. Missing/invalid/NAK/stale association refuses. Protocol cookie reuse is not by itself a replay attack: RFC 8915 §5.7 permits it. Reject replayed measurements/receipts via challenge/UID/local ledger, not a fabricated global cookie-uniqueness rule |
| Accuracy | Independent authority UTC accuracy assumptions, root delay/dispersion and offset terms tied to the same measurement, raw local interval/delay evidence, conservative asymmetry/capture/drift bounds, uncertainty growth, lease and leap/UTC convention. Missing assumptions cannot be replaced by a precise-looking number |
| Collector provenance | An independently controlled reviewed NTS client verifies TLS/AEAD internally. A separately controlled read-only collector binds that verified event and local timestamps over authenticated, access-controlled IPC to the verifier. Its identity/permissions/boot/configuration, evidence integrity and any attestation trust root require independent validation; a JSON tls=true or text Authenticated: Yes is insufficient |

The collector/IPC/attestation boundary does not exist here. The consumer must not author its own proof. Reading client status may support a future trusted-host design but does not automatically produce externally verifiable authentication, persistent freshness or an independent accuracy guarantee.

Certificate bootstrap remains unresolved when initial wall time is uncertain. No time.time(), HTTP Date, TLS connection alone or disabled date check clears it. A future deployment needs independently justified coarse time/trust bootstrap and then full association/accuracy evidence. No certificate or key value is supplied here.

## Conservative screening calculus and synthetic validator

The chronyc manual's conditional clock-error expression is:
abs(system offset) + root dispersion + root delay/2, assuming the root clock is correct. This assumption and reported statistics must be independently defended before treating them as safety bounds.

The new model deliberately uses a stricter screening budget:
E0 = abs(offset) + ceil(root_delay/2) + root_dispersion + authority_error
     + full local RTT + 2*capture_error + ceil((RTT + 2*capture_error)*drift_ppm/1e6).
E(age) = E0 + ceil(age*drift_ppm/1e6).

Full local RTT is added without a symmetric-path assumption; possible double counting is conservative. This is a proposed screening rule, not a new NTS offset estimator or proof that the stated inputs are correct. Both initial and grown bounds must be <=2 seconds. Drift/capture assumptions need independent runner evidence; no local wall time is promoted to UTC. Model leases are capped at the unchanged 026 model's 30 seconds; equality at expiration refuses.

The module accepts only explicitly labeled STATIC_SYNTHETIC_NOT_AUTHENTIC_NTS bytes (maximum 16384), exact nested schemas and a narrow chronyd 4.6 fixture profile. It reuses 026 binding/window checks; it does not modify authentic_verifier(). Receipt fields, host .invalid identity, fingerprints and flags are invented test values, not a deployed client or certificate. No crypto is implemented and no fake signature is introduced. The static fixture SHA-256 is 229d786599a81927cc613a2b8e5968c9658d2fa4829ac6d51fde613c9a57537d.

One ShapeSession consumes one challenge, even after a failed receipt. It checks expected client/authority/session, NTS-shaped extension and TLS/bootstrap fields, cookie-association lease, local windows, restart/suspend/rollback and error terms. Unknown fields/NaN/bool-as-integer/oversized JSON refuse. Contexts and numeric acquisition are trusted test inputs only; the session is not persistent anti-replay storage.

Valid fixture screening yields OFFLINE_SHAPE_VALID and 262010200ns initial screening uncertainty, while still returning AUTHENTIC_NTS_PROVENANCE_UNAVAILABLE, AUTHENTIC_PROVENANCE_NOT_COLLECTED, B4_NO_GO and independent_utc=false. A small synthetic number is not authentic time evidence. Refused shapes return specific diagnostics without raw data or secrets. No UTC epoch or usable clock provider is returned.

## Operator choices

Ranked for the next practical prerequisite, not asserted trust:

| Rank / option | Provenance + <=2s prospect | Burden / decision |
| --- | --- | --- |
| 1. Existing packaged NTS chrony on tightly scoped owner host | Best immediate feasibility if present with reviewable build/permissions and a collector capable of associating authenticated measurements with trusted local timestamps; ordinary status alone remains insufficient | First establish presence offline; actual version/build/export review still required. Offset-only capability avoids privileged clock setting but does not authorize time traffic |
| 2. Separately approved NTS client deployment | Can deliberately supply reviewed client/provenance/export boundaries, but none is currently approved or installed | More deployment/containment work and explicit dependency/network authorization. No installation in this assignment |
| 3. Independently signed-time alternative | Asymmetric receipts can aid independent verification, conditional on a genuinely anchored authority and <=2s accuracy/freshness bounds | New authority/key/client/bootstrap review; signatures alone do not establish accuracy. No alternative service or key is invented or provisioned |

Exactly one smallest future owner action: on a clean checkout of the reviewed PR head, manually run the passive --offline-inventory command above on the intended Ubuntu 24.04/Python 3.11.17 runner and retain its output with the checkout SHA. That gathers a missing prerequisite without process launch, time traffic or market data. No workflow is created or dispatched. If unavailable, the later owner must choose an approved environment/deployment; nothing installs automatically. Any genuine NTS-KE/NTP traffic requires separate explicit owner consent and a reviewed bounded manifest beforehand.

## Exact validation and limits

```sh
python -B -m unittest tests.test_nts_chrony_evidence_027 -v
python -B -m unittest discover -s tests -v
```

Python 3.12.14: focused 26 tests in 0.041s, OK; full 475 tests in 7.115s, OK, no skips.

Tests cover default/import no file/network/process/clock effects; passive absence/permission/presence/partial/unsupported metadata; exact file allowlist, no-follow, size/change/deadline/FD cleanup; unsupported client profile; missing extensions, plain fallback, failed TLS/bootstrap, changed authority; missing/expired/replayed association evidence; stale/reused receipt; all bindings; rollback/suspend; excessive RTT/asymmetry/error/dispersion; growth/expiry; mocked green status, unknown/secret fields and strict JSON. Real network/process/time-setting interfaces are guarded; no binaries run. Existing regression tests retain their real local offline worker tests, not genuine network or UTC evidence.

Remaining blockers: actual target client/build/export capability; independent trust bootstrap; authenticated collector provenance and persistent replay protection; authority accuracy and calibrated local capture/drift; target containment and real source/transport evidence. B4 NO-GO, B1/B2/B3/B5 HOLD, source admission HOLD and NO ORDERS remain intact. The working manual close-only observer stays available unchanged. No data-rights policy, external API or ZUMERAVO changes.

STOP FOR OWNER AND BOSS AI REVIEW.

