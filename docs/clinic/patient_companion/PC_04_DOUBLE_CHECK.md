# PC-04 — DOUBLE CHECK

Status: COMPLETE — findings corrected, recertification required
Scope: PR #641 — Patient Companion Consent Vault
Review basis: product/closeout candidate through 9b91dc1d036bbfa314a3bbfa7c5014a0dd6f611e

## Goal reviewed
Patient-facing Consent Vault must bind patient evidence to an exact shared document version, preserve truthful state transitions, and reuse the established Patient Companion security boundary.

## Checks performed
- staff authorization and document-level permission path;
- tenant/patient isolation;
- explicit share prerequisite;
- document version/hash/size binding;
- physical file integrity check;
- signature image validation reuse from M6-C;
- encrypted remote command/ACK contract;
- duplicate/revoked/expired behavior;
- source PDF preservation;
- UI read-before-sign truth;
- exact-head CI and visual evidence from the earlier candidate.

## Finding DC-1 — document permission gap
Severity: material authorization gap.

Observed:
- share creation correctly called `require_document_permission(...)`;
- consent issue/revoke routes only called `staff_patient_or_404(...)`, which proves principal-cabinet + patients permission but does not reapply the document-type permission.

Risk:
A principal staff account with patient administration rights but without the relevant document permission could act on a consent after another authorized actor created the share.

Correction:
- consent issue now calls `require_document_permission` for the exact document type;
- consent revoke also rechecks the same document permission;
- targeted regression test added.

## Finding DC-2 — MIME/content truth gap
Severity: material product-truth gap.

Observed:
Consent Vault served `DocumentArchive` bytes with `application/pdf` but did not prove those bytes were a PDF.

Risk:
A non-PDF archive could be presented/signable as though it were a PDF.

Correction:
- consent issue requires physical bytes to begin with the PDF signature `%PDF-`;
- patient read route rechecks the same condition;
- hash/size integrity remains independently verified;
- targeted non-PDF regression test added.

## Double-check conclusion
No merge recommendation is made from the earlier green candidate.
The corrected branch requires a fresh exact-head certification after all review findings are included.
