# DIGITAL CROWN — 2026-11-09 — LOT08.2-B / B-7 — Candidate CODE_CERTIFIED regression repair (RED)

**Single decision / owner trigger:** « Red » to resolve the **three demonstrable failed assertions** in the exact-SHA [Cabinet CODE_CERTIFIED candidate (no package) #42644548911](https://github.com/hraaaaf/Digital_crown/actions/runs/42644548911). Baseline PR [#1239](https://github.com/hraaaaf/Digital_crown/pull/1239) OPEN/DRAFT, SHA `c64d9e94077fb63bb6c37e3b80cf24d477dab3dc`, base `master` SHA `324afd13487acf7ff29223f077451927b54b8178`. No master merge, package, clinic install, patient data or deployment allowed.

## BEFORE — CI findings, verified from raw logs

- **Frontend job `129254318723` FAILED**: Vitest **2022 PASSED / 1 FAILED** in `src/test/mobileM4CDocumentContext.test.ts`, which was looking for `handleView(doc.id)`. The actual `PatientDocuments.tsx` handler already accepts `(docId, filename)` and the live button invokes `handleView(doc.id, doc.name)`; that filename is required to show the correctly identified PDF preview. Existing server endpoint `/documents/${encodeURIComponent(docId)}/download` and `belongsToActivePatient(patientAtRequest)` before/after the blob read already enforce patient-bound state.
- **Backend job `129254319111` FAILED**: pytest **5918 PASSED / 2 FAILED / 30 SKIPPED**. `test_cephalo_v1_l3_a4_document.py::test_media_reader_is_tenant_scoped_and_uses_only_verifiable_slots` mocked an incomplete old media record omitting `patient_id`, `timepoint`, slot/source, provenance schema and capture date. The production `load_cephalo_pdf_media` rightly refuses a mismatched identity **before any byte read**, and rightly rejects images lacking verified upload provenance.
- Same backend job: `test_ortho_frontend_fail_closed_contract.py::test_step4_has_no_local_normative_ranges_or_default_appliance` expected the explicit message `Prévisualiser ou archiver un PDF ne constitue pas une validation clinique.` on the real `Step4Documents` user interface; the component had only similar but non-identical explanatory wording.
- Independent PostgreSQL/JWT rehearsal job passed. Separately red CEPH experimental and Mobile Pocket workflows are **tracked as different work streams**, not silently declared fixed by this change.

## ACTION — no reduction in clinical safety or test coverage

1. **Document viewing** — update the static frontend contract test to require the actual two-argument authenticated preview call `handleView(doc.id, doc.name)`, explicitly check its patient-bound callback and `setPreview({patientId: patientAtRequest!, blob, filename})`. Keep the canonical authenticated download URL and forbidden URL-based paths tested. No change to actual patient document code.
2. **Cephalometry** — update the positive fixture with exact `patient_id=42`, `timepoint=T0`, `source_kind=UPLOAD`, correct photo slot, `ORTHO_MEDIA_SCHEMA_VERSION` and real UTC `captured_at`. Keep real service's fail-closed checks unchanged. Add **two** new negative tests rejecting foreign-patient and wrong-timepoint media **before any byte read**, plus **one** negative test that a derived / unverifiable image never becomes printable media. No genuine patient records.
3. **Orthodontic safety** — put the exact mandated warning visibly next to the PDF actions on `Step4Documents.tsx`. Keep official archiving disabled for unsigned drafts and the original no-autonomous-diagnosis guard intact.

## SUCCESS / PROOF — factual checkpoints

- Targeted Windows (synthetic process-local `ENVIRONMENT=test`, `sqlite:///:memory:`): frontend M4-C **6/6 PASS**; backend Cephalo + Ortho **14/14 PASS** including three added fail-closed negative tests.
- Full frontend Vitest, frontend TypeScript/build, full Queue Core and CI candidate at **new exact HEAD** must be separately verified before declaring B-7 green. The historical candidate `#42644548911` remains **FAILURE**.
- The prior B-6 source-only preflight is unaffected and remains **NO_INSTALLABLE_GO**, regardless of CI outcomes.

## STOP / next exact

Git diff check, full/targeted tests, commit/push *only to the same DRAFT PR* followed by CI Queue/Scope and **the full candidate workflow** on the new SHA. If candidate is red again, analyze its new logs and correct code/tests from proof, without skipping or weakening clinical checks. FUE-G human clinic acceptance, native installed Windows app, exact-master `CODE_CERTIFIED`, `INSTALLABLE_CERTIFIED`, real `/appointments` migration and LOT10 physical acceptance all **NOT_RUN/NOT_AUTHORIZED**. PR #1239 remains OPEN/DRAFT, no merge or production.
