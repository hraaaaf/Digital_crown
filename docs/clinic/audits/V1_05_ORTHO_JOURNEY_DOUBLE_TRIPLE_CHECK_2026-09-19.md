# V1-05 — Ortho Journey Double / Triple Check — 2026-09-19

Status: **REMEDIATION IMPLEMENTED — EXACT-HEAD CERTIFICATION PENDING**

Audit branch: `audit/v1-05-ortho-triple-check-f5-gate`
Audit base: `master@87543ccd8515dd9cdee94495dbe7001bce22331d`

## Goal
Independently re-check the closed V1-05 engineering chantier against its original Goal / Success / Proof contract, then perform an adversarial third pass looking for a residual failure mode before V1 freeze.

## Pass 1 — documentary + merge evidence
Verified from current master and merged PR history:
- F1A merged: PR #596 / `c41f47d2eb7708d6494fd32c97814d7a968ed5e0`.
- F1B merged: PR #598 / `81535364e4f98f3f9b53fac179f2fbfd2ec261f5`.
- F2 clean rebuild merged: PR #610 / `35ccdf5ad73b403279e129c7affe2d9364c6d4cc`; exact-head CI/PostgreSQL/P7/T2/A5 green and Full Backend product-equivalent certification recorded.
- F3 merged: PR #613 / `413af20093367e43bc3c59efbaa1ad156b668ef4`; BEFORE/AFTER protocol retained; final severe visual score 9.5/10 with owner approval.
- F4 merged: PR #617 / `20bfe3349399bf49a2f5ece14c5f70526e9d4a1b`; post-merge certification PR #619 closed without merge after green checks.
- F5 engineering preview merged: PR #620 / `2cfb0dc53b71daa9f8cbb63e966a5cab4481fc10`; canonical closeout PR #621 / `455cff05de35166eed62ae58eb1ae9d9014503dd`; post-merge certification PR #622 closed without merge after CI/T2/A5/Merge Summary success.
- F5 external Scite audit remains explicit: engineering-preview support only, not clinical approval.

## Pass 2 — current-master contract re-read
Current master still contains the expected fail-closed contracts:
- F1 tenant isolation and secretary read/mutation separation are covered by current Ortho tests.
- F2 evidence is reference-only; exact-one-source, patient/tenant ownership and reuse/conflict guards are covered by current tests.
- F3 exposes raw numeric deltas only; ambiguous cephalo pairing returns no guessed measurements; uncalibrated linear values are excluded; prohibited clinical interpretation wording is tested.
- F4 keeps planned control and real appointment as distinct facts and fails closed when no OrthoCase exists.
- F5 canonical source resolver requires same patient/case/tenant, chronological distinct timepoints, adult engineering scope, exactly one cephalo per timepoint, canonical local radio paths and calibration integrity.
- F5 output schema hard-locks `ENGINE_ESTIMATE_ONLY`, `clinically_validated=false`, and `acquisition_protocol_status=UNVERIFIED`.
- F5 requires the `cephalo` permission and rejects noncanonical/external media paths.

## Pass 3 — adversarial residual finding

### MUST-FIX — F5 preview opt-in was not runtime-environment constrained
The F5 service documentation states that preview activation is for an explicit engineering environment. Before this audit, `engineering_preview_enabled()` only checked:
`DIGITAL_CROWN_F5_ENGINEERING_PREVIEW=1`.

Therefore a cabinet/production runtime with that flag accidentally enabled could expose the non-clinically-validated F5 backend preview.

### Remediation
Implemented on this audit branch:
- F5 now requires BOTH an explicit preview flag and `ENVIRONMENT` in `development | local | test`.
- `cabinet`, `production`, and missing environment fail closed even when the preview flag is `1`.
- regression tests added for explicit engineering opt-in and cabinet/production/missing-environment denial.

Code commits:
- `65359d56763497c0db9ddf25fe9eaa3fe0e106d0`
- `54d7dc1931922c0dba98a06c02f61bcc666b67f6`

## Scientific boundary retained
This audit does not upgrade F5 scientific status:
- independent named scientific review remains required;
- named human clinical validation remains required;
- Vasileiou 2026 full-text reconciliation remains required;
- acquisition-device/protocol comparability remains unverified;
- growing-patient validation remains required;
- no treatment-effect, diagnosis, improvement, success/failure, or normative claim is authorized.

## Current conclusion
F0-F4 remain supported by current code/tests/merge evidence.
F5 remains acceptable only as a hidden engineering preview.
One real pre-freeze MUST-FIX was found and remediated. V1-05 should not be considered triple-check clean until the remediation branch passes exact-head targeted/global certification and is merged/re-certified on master.
