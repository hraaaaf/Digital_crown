# DIGITAL CROWN — J1.B3 / Windows installable acceptance: certified release gate

**Date:** 2026-11-11  
**Decision:** EXPLICIT USER GO to validate a real Windows installer, with synthetic data and BEFORE/AFTER screenshot evidence.  
**Actual technical scope:** read-only source and fail-closed native-Windows preflight **until an admissible, exact-SHA `INSTALLABLE_CERTIFIED` binary is supplied and verified**.  
**Status:** **BLOCKED / NO INSTALL** (not a certification; not a simulated installation).

## GOAL → SUCCESS → PROOF

**Goal:** eventually exercise the *real, trusted* Windows installer and genuine Desktop workflow, with a synthetic database, isolated user profile, before/after captures at identical viewports, encrypted backup/restore, recovery and cleanup. Never execute an unsigned or ad hoc EXE.

**Presently provable on the DRAFT PR candidate:** source policy and negative Authenticode guards. This gate is a separate, test-only FUE-0; it cannot make J1.B2 installable. The previous J1.B2 combined Windows HTTP+SQLCipher FUE-I was GREEN on HEAD `ed8ee15f2056a27d5d939f3122bd4daa27fd4fdc` ([run #42995997721](https://github.com/hraaaaf/Digital_crown/actions/runs/42995997721)) but is **not** a signed installer.

## Immutable release identity and hard stop

Canonical [release policy](../../docs/CABINET_CERTIFIED_RELEASE_POLICY.md) and `AGENTS.md` prohibit installation or packaging from a branch, PR, working tree, tag, moving `master`, or a simple CODE_CERTIFIED artifact.

For the J1.B2 candidate:
- Source is [PR #1283](https://github.com/hraaaaf/Digital_crown/pull/1283), OPEN / DRAFT at `ed8ee15f2056a27d5d939f3122bd4daa27fd4fdc`, stacked on [PR #1277](https://github.com/hraaaaf/Digital_crown/pull/1277). **Not merged**.
- [Prior installed V1 baseline](../clinic/DIGITALCROWN_V1_INSTALLED_BASELINE.md) is `bce60b26059054ba43cf8ec13cd210098e648ea4`, certification run `36628947897`. It is *a different SHA* and cannot certify J1.B2.
- The available J1.B2 workflow artifacts are **test logs**, not `CODE_CERTIFIED`, `INSTALLABLE_CERTIFIED` or Windows Inno Setup artifacts.
- A genuine installer also needs an externally authenticated publisher-certificate SHA-256 pin. A made-up pin is strictly **negative-test input**, never authority to install.

**STOP:** no exact-current-master code attestation, matching certified scientific assets or sealed release, signed installer and independent publisher trust pin for J1.B2; thus no installer may run and no BEFORE/AFTER installer screenshot can truthfully exist.

## Safe Windows test now (source and negative signature only)

Files:
- `scripts/quality/ceph_j1b3_installable_windows_readiness.ps1` is a read-only source preflight and negative fake-EXE signature probe.
- `.github/workflows/ceph-j1b3-windows-installer-readiness.yml` executes it on a hosted **Windows 2022** ephemeral runner with an immutable PR head SHA.
- Existing `queue_core/tests/test_installable_source_preflight_08_2_b.py` validates the canonical 10-marker source policy and negative HEAD/coupling behavior.

**Proof expectations (no installed program):**
1. Exact SHA checkout; 10/10 source guards = PRESENT; `installable_ready=false`, `clinical_go=false`.
2. Purposefully forged unsigned MZ-shaped `DigitalCrownSetup-INSTALLABLE-CERTIFIED.exe` and `DigitalCrown.exe`, plus a fake pin outside the stub directory, must be rejected by the real Windows `Get-AuthenticodeSignature` verifier with a nonzero exit code. **A negative-test PASS is not positive publisher validation.**
3. Remove all negative test stubs and fake pin from `RUNNER_TEMP` and create a JSON gate report with explicit `NOT_PROVIDED` / `NOT_RUN` for certification, install, screenshots, app startup and restore.
4. Keep PR DRAFT, do not merge/deploy/activate, and never touch patient data or an actual cabinet workstation.

**Expected safe verdict:** `J1B3_WINDOWS_SOURCE_CONTRACT_10_OF_10_PASS` and `J1B3_UNSIGNED_AUTHENTICODE_FAIL_CLOSED_PASS`, **but** `NO_INSTALLABLE_CERTIFIED_FOR_THIS_PR_TEST_STOP`.

## Separate future acceptance steps (not executed in this scope)

After an owner-authorized **merge decision**, conduct the official exact-master `Cabinet Certified Release` workflow and verify backend/frontend/PostgreSQL 18, Patient/Documents preservation and GitHub/Sigstore. After separate asset rights and integrity verification, build `INSTALLABLE_CERTIFIED` for the same SHA; then authorized PyInstaller/Inno Setup build and external Authenticode issuer verification. Only after these preflight gates may a disposable Windows profile execute the genuine installer.

Actual installable Desktop FUE-I/G needs:
- BEFORE captures of pristine *test* user profile at 1280×900 and 1600×1000; record Windows build and SHA of the signed package.
- Actual installer GUI, no unattended auto-start or clinical seed, no leakage of credentials, models, DB or media into installer; verify signature and all release manifests.
- Start frozen exe on isolated test root with fake patient(s). Assert JWT/tenant 401/403, clinician identity integrity, revision + idempotency, SQLCipher encrypted paths, persisted media.
- Encrypted backup of fake DB+media, shutdown/restart, isolated restore to a second **synthetic** root and integrity compare using record IDs/hashes, injected corruption and rollback, then AFTER captures at the **same viewports**.
- Clean all test accounts, fake files, processes and installer from the ephemeral environment; report SHA, checks, screenshots and actual remaining artifacts.

No screenshot or installed application is claimed until that FUE actually runs. A GitHub-hosted Windows runner is **not** a real clinic workstation. Medical `SOURCE_LOCK_REQUIRED`, licensing and human clinical checks are separate. A signed installer would not certify anatomical measurements.

## Evidence / NEXT exact

- PR and exact SHA of the *source-only* preflight will be recorded after GitHub creates them.
- Check GitHub Actions Windows job and artifact JSON; do not conflate a green source guard with a green installer acceptance.
- **Next external dependency:** authorized merge and exact-master CODE_CERTIFIED, matching runtime assets and INSTALLABLE_CERTIFIED package, plus independently authenticated Windows signing certificate. This gate cannot be skipped in response to a generic GO to test.

**Canonical earlier J1.B2 evidence:** `docs/audits/CEPHALO_J1B2_DESKTOP_AUTH_SQLCIPHER_FUE_20261111.md`.
