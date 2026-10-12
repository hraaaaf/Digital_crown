# FUE-G04 — Windows installer: production-readiness acceptance gates

Status: **OPEN / no physical deployment authorization**. Last reviewed 2026-10-11.
Scope: an independent frozen-runtime/Windows installer qualification for the official
CODE_CERTIFIED source, *not* a revision to canonical certified production sources.

## Immutable evidence (do not confuse different hashes)

- Official master commit: `9c41d327400b8c41d8541517603d84bf9fdf9c23`
- CODE_CERTIFIED: [workflow run 38092782085](https://github.com/hraaaaf/Digital_crown/actions/runs/38092782085) and [Sigstore attestation 54694472](https://github.com/hraaaaf/Digital_crown/attestations/54694472).
- Certified Windows build (ephemeral CI): [run 38095783298](https://github.com/hraaaaf/Digital_crown/actions/runs/38095783298); source INSTALLABLE_CERTIFIED artifact [11685778900](https://github.com/hraaaaf/Digital_crown/actions/runs/38095783298/artifacts/11685778900).
- Windows installer ZIP [artifact 11685559679](https://github.com/hraaaaf/Digital_crown/actions/runs/38095783298/artifacts/11685559679), ZIP digest sha256 `d1aab4f000924b4c5ae84df5ec738f48f7180046c93ad2e7beef7f08ca4648a9`.
- INNER executable `DigitalCrownSetup-INSTALLABLE-CERTIFIED.exe` SHA256 from GitHub Windows job: `9a8e07644dde4b7eff153a84a53d4c7a81c9ea7731262e8aa1daa807f765e33d`. The outer ZIP hash is *not* the inner executable hash.
- PR #825 contains **CI-only** release/build proof changes, is **DRAFT and unmerged**.
- An additional runtime smoke [run 38097354550](https://github.com/hraaaaf/Digital_crown/actions/runs/38097354550) was triggered. Its result must be read explicitly; do not infer PASS merely from the link.

## Required gate 1 — Ephemeral, strictly isolated Windows runtime

Only use disposable GitHub-hosted Windows runner paths, a fresh artificial SQLite/SQLCipher database
and random temporary secrets. The pre-existing cabinet, local APPDATA and cloud production systems
are out of scope. All tests must bind 127.0.0.1 only and refuse real cabinet credentials.

- [ ] Download pinned installer from successful CI run; check the **inner EXE** SHA256 and attached evidence file.
- [ ] Run Inno Setup installer to RUNNER_TEMP, not any physical workstation. Verify installed EXE, SHA marker, and all seven proof files: exact parity between signed source, PyInstaller `_internal`, and installer-visible root.
- [ ] Execute the *installed frozen binary* with explicit isolated environment/database and only loopback origin. Confirm actual `GET /health` returns status/db `ok`; confirm the test database lives only in disposable temp. Ensure the process is terminated and the directory discarded.
- [ ] Verify refusal of a missing/untrusted explicit cabinet environment **before** any first-boot data writes. A nonzero exit on its own is not enough if failure cause is unknown.
- [ ] Check no real patient, Firebase, Sentry, or companion-relay traffic is emitted by this test; no real credentials are provided.

No single step above is accepted without CI log and exact commit/run/artefact evidence. If a smoke fails,
classify source runtime vs packaging/test harness separately; do not relax signed runtime guards.

## Required gate 2 — Windows-specific product capability smoke

These remain **unverified** by a successful PyInstaller/Inno Setup compilation and must not be
silently waived:

- [ ] On an isolated frozen Windows binary, render a synthetic PDF via the real WeasyPrint code path; verify bytes start with `%PDF-` and that no GTK/Pango/Fontconfig native dependency is missing. Build logs warn `Depending libraries not found - weasyprint will likely fail to work`.
- [ ] Exercise `multipart/form-data` parsing/upload with synthetic file and authenticated test role, assert preserved bytes and no exposure. Build logs include `ERROR: Hidden import 'python-multipart' not found`; determine whether this is an inaccurate import name or an actual frozen runtime missing module.
- [ ] Exercise scientific analysis path needing SRPose ONNX and optional numba TBB on a synthetic image or approved nonclinical fixture. Build log warns `tbb12.dll` unresolved; classify required vs optional CPU threading with executed test, not guess.
- [ ] Exercise safe PDF/ordonnance/certificat/notes d'honoraires, print-preview and output layout under Windows (no real patient identity).
- [ ] Confirm release guard rejects missing/tampered `release-certification.json`, missing model, altered `runtime-assets-certification.json`; no fail-open.

**Any failed required clinical capability = NO-GO even if installer CI is green.** Fix actual issues
in a reviewed source-code PR (then re-issue official CODE_CERTIFIED on new master SHA, rebuild and
re-attest), not by silently modifying an already signed package.

## Required gate 3 — Human acceptance on an explicitly approved new cabinet only

There is **no approval yet** to install onto a physical PC, alter Windows networking,
activate a device or touch patient archives. A separate owner decision and a preserved-before
snapshot are required.

- [ ] Record a read-only, off-site copy/evidence of the existing cabinet state and untouched archives:
  `C:\Users\lenovo\Documents\Cabinet\DigitalCrown-Preservation-20261010`
  (36 historical records; **never test migration/restore in-place**).
- [ ] If later authorized, select a separate **new cabinet only** root:
  `C:\Users\lenovo\DigitalCrown-NewCabinet-20261010`.
  Use an explicit environment file, separate data/config/log/runtime locations and random
  independent keys. No default APPDATA fallback. Never use patient data in test fixtures.
- [ ] Verify installer does not autorun, register unintended startup jobs or change old cabinet.
- [ ] Full after-install smoke: cold restart, licensing, isolated synthetic patient workflows,
  3 commercial packs (BASIC/GOLD/ELITE), media uploads, printing, PDF generation, backup and
  restore on a *copy of synthetic fixtures*, then independent before/after folder comparison.
- [ ] Test HTTPS certificate, phone trust and QR device pairing on the actual phone, with
  real user involvement. Do not disable TLS to obtain a green result.
- [ ] Preserve evidence: screenshots BEFORE/AFTER same viewports, logs stripped of secrets,
  signed binary/hash and CI run URLs, physical human sign-off.

## Sign-off policy

- **CODE_CERTIFIED** = PASS (exact cited master SHA).
- **INSTALLABLE_CERTIFIED assembled + installer COMPILED** = PASS in ephemeral CI only.
- **FROZEN_RUNTIME_SMOKE** = must be read from runtime smoke workflow, never inferred.
- **CLINICAL_FEATURES_VALIDATED** = OPEN until gate 2 execution evidence.
- **PHYSICAL_NEW_CABINET_APPROVED / INSTALLED** = NO / NO.
- **PRODUCTION GO** = NO until all required gates, two fresh adversarial reviews on the
  correct source SHA, and explicit final human owner sign-off.

Do not merge PR825 or trigger physical installation as a shortcut to passing the acceptance gates.
