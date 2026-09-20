# PC-04 — Consent Vault patient-facing — CLOSEOUT

Status: RECERTIFICATION REQUIRED AFTER DOUBLE/TRIPLE CHECK
Branch: feature/patient-companion-pc04-consent-vault
PR: #641
Previously certified product HEAD: 614256f33f33bec88ba96654ae028f9c131cb280 (superseded for merge decision by double/triple-check corrections)
Base: master@86fc61a572f303c812f1999c887e35574df0bb49
Deployment: none

## Goal
Expose a patient-facing Consent Vault that lets an authorized Patient Companion identity read and sign an exact cabinet-issued document version while preserving an auditable application-level evidence chain.

## Verified architecture
- explicit document sharing remains the admission gate through PatientCompanionShareGrant;
- consent request binds document group, version, SHA-256 and byte size;
- patient read route rechecks active share, exact version/hash/size and physical file integrity;
- patient must read the exact document snapshot before the signature UI is exposed;
- patient signature PNG uses the shared M6-C validation primitive;
- consent signature evidence is detached from the PDF source and stored transactionally;
- source PDF bytes are not silently rewritten by PC-04;
- encrypted Patient Companion remote transport/relay is reused through a shared generic command transport;
- consent.sign is accepted only after cabinet-side validation;
- UI does not display SIGNED before durable cabinet ACK;
- relay pending remains visibly non-signed;
- revoked share, changed document version, expired/revoked consent and duplicate signature fail closed;
- no qualified electronic signature, eIDAS, PKI or legal-retention claim is made.

## Exact-head certification — 614256f33f33bec88ba96654ae028f9c131cb280
- CI: 35535738532 — SUCCESS
- Patient P7 Final Certification: 35535738407 — SUCCESS
- T2 Runtime Browser Certification: 35535738419 — SUCCESS
- PostgreSQL Alembic Schema Certification: 35535738367 — SUCCESS
- Patient Companion Remote Transport Gate: 35535738483 — SUCCESS
- PC-00 Patient Companion Visual Certification: 35535738417 — SUCCESS
- PC-02 BEFORE Visual Evidence: 35535738458 — SUCCESS
- PC-02 AFTER Visual Evidence: 35535738418 — SUCCESS
- PC-03 AFTER Visual Evidence: 35535738377 — SUCCESS
- Agenda A5 Visual Evidence: 35535738400 — SUCCESS
- PC-04 BEFORE Visual Evidence: 35535738385 — SUCCESS
- PC-04 AFTER Visual Evidence: 35535738413 — SUCCESS
- PC-03 BEFORE Visual Evidence: skipped as expected outside PC-03 branches
- M6-I Biometric Passkey Certification: skipped as expected
- PR Merge Summary: skipped as expected

## Visual evidence
BEFORE artifact:
- id: 10612801028
- digest: sha256:194b6c7111556d4f1973c7fb1aa6d0823b344f80b26a97922f29cb72cbf1f7ba

AFTER artifact:
- id: 10613086053
- digest: sha256:4d55086bdd9b7b5b18e4cee754589dd24f597c04d106a47f31275f66bd081073

Matrix:
- Chromium 360x800
- Chromium 390x844
- WebKit 360x800
- WebKit 390x844
- horizontalOverflow=false on all four BEFORE and all four AFTER captures.

Manual visual review:
- Consent Vault card is consistent with the Patient Companion visual language;
- read-before-sign flow is understandable and explicit;
- application-level signature boundary is visible;
- signature controls are touch-sized and readable;
- no clipping or horizontal overflow observed;
- main reserve is vertical length when the signature panel is open.

Severe visual score: 9.0/10.

The vertical-density reserve is explicitly deferred to PC-FINAL — Polish & Visual Consistency, which is already present in the Patient Companion roadmap.

## Certification defect corrected
The historical PC-03 BEFORE workflow used the current PR base as its BEFORE snapshot. On PC-04, that base necessarily already contains PC-03, making the assertion “PC-03 absent” impossible. The gate is now N/A outside PC-03 feature branches. This is a CI-governance correction only and does not change PC-04 product behavior.

## Success criterion
Met for product HEAD 614256f33f33bec88ba96654ae028f9c131cb280 with the exact-head runs and artifacts above.

## Merge rule
This closeout commit itself must be recertified on its exact HEAD before PR #641 is marked ready and merged.


## Double / triple check reopening — 2026-09-20
The initial closeout was deliberately reopened after independent double and adversarial triple checks identified material findings.

Canonical review evidence:
- `docs/clinic/patient_companion/PC_04_DOUBLE_CHECK.md`
- `docs/clinic/patient_companion/PC_04_TRIPLE_CHECK.md`

Corrections now included:
- document-type permission rechecked when issuing/revoking consent;
- only real PDF bytes are eligible/served as Consent Vault documents;
- revoked/expired consent requests are preserved and reissue creates a new historical row;
- consent revoke produces a dedicated audit event;
- malformed signatures stay inside the encrypted remote-domain ACK contract;
- remote consent payload is exact and consent UUID is validated;
- targeted regressions cover these findings.

The prior exact-head green evidence remains historical proof for the earlier candidate only.
It MUST NOT be used to authorize merge of the corrected branch.

## Current merge gate
Fresh exact-head certification is mandatory after all double/triple-check corrections and documentation are committed.
