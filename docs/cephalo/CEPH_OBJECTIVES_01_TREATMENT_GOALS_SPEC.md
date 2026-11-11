# CEPH-OBJECTIVES-01 — Objectifs orthodontiques individualisés

**Status:** CANDIDATE / DOCUMENTARY FUE-0 ONLY — NO CLINICAL ACTIVATION  
**Date:** 2026-11-11  
**Source branch:** `docs/ceph-objectives-01-spec-20261111` from `master@093e89390d0e4b934d478485ea1ef28a7ce95de4`  
**Upstream dependency:** CEPH J1.B1 S3/S4 integration and exact-HEAD gates unresolved; PR #1288 DRAFT is NOT merged.  
**Scope:** functional/data contract and acceptance criteria only; no runtime, schema, patient data, model, install, merge or deployment.

## 1. Goal / Success / Proof

**Goal:** let an authorized clinician record, edit, prioritize, track, reassess and explicitly confirm individualized orthodontic treatment objectives in the **local patient record**, without equating a cephalometric observation with a diagnosis, objective or approved treatment.

**Success of this DOCUMENTARY phase:** a bounded, inspectable candidate specification defining clinical-authority boundaries, data shape, UX, negative cases and the required future FUE.

**Proof of later IMPLEMENTATION:** an executed clinician workflow on synthetic local fixtures — create → edit → follow → review → explicitly confirm result — with evidence at the same exact HEAD across UI/API/persistence/PDF, access restrictions, audit trail, relevant negative cases, and BEFORE/AFTER captures. Documentation alone never proves implementation.

## 2. Product placement and workflow

Place an **« Objectifs du traitement »** section in the orthodontic clinical workflow, reachable from the case alongside examination/occlusion and cephalometric review. It is not part of the SRPose38 landmark detector, not an auto-diagnosis engine and does not alter the cephalometry mathematical contract.

User path: clinician enters an existing authorized case → reviews recorded findings (distinct) → manually selects or writes an objective → specifies tooth/sector and measurable or observable target **when clinically applicable** → saves as draft → revisits during treatment → records observation/evidence → explicitly verifies an outcome → audit history retained.

The checklist is a productivity aid, **not** a treatment suggestion. No objective is preselected from ANB/Wits, image inference, model confidence or any other signal.

## 3. Editable candidate catalogue (examples, never defaults)

| Category | Example FR | Scope details |
| --- | --- | --- |
| Dental / tooth | Déroter la 25 | Tooth FDI 25; baseline/target and observation clinician-entered |
| Transverse | Corriger l’articulé croisé postérieur | Right/left/bilateral; teeth or sectors; functional shift if assessed |
| Sagittal | Corriger le surplomb incisif | Target only if clinician defined; unit and method if measured |
| Sagittal | Améliorer les relations canine/molaire | Dental relationships and side documented |
| Vertical | Corriger une supraclusion / une béance | Segment and clinical observations |
| Alignment | Aligner les deux arcades | Upper/lower, crowding and tracking separately |
| Space | Gérer ou fermer un diastème | Teeth/sector, approach selected only by clinician |
| Midlines | Corriger le décalage des lignes médianes | Referential and direction recorded |
| Functional / maintenance | Objectif fonctionnel ou de contention | Clinician-documented goal and follow-up; no inferred pathology |

Catalogue labels are editable and translatable FR/EN. Clinicians may enter an objective not in this catalogue. Do not imply all objectives are appropriate for every patient or age.

## 4. Candidate information model (requires implementation review)

- `objective_id`, `case_id`, `patient_id` linked by authorized local backend; no cross-patient copying.
- `category`, `label_fr` or clinician-entered text, optional `label_en`, `dent_fdi[]`, `arch`, `sector`, `laterality` (all context-specific and nullable when genuinely not applicable).
- `baseline_observation`, `intended_outcome`, `measurement_unit`, `measurement_method`, `target_value` **optional** and never machine-invented.
- `priority`: clinician-set; `workflow_state`: DRAFT / PLANNED / IN_PROGRESS / REASSESSMENT_NEEDED / COMPLETED / NOT_ACHIEVED / CANCELLED.
- `result_observation`, `evidence_refs`, `reviewed_by`, `reviewed_at` for explicit outcome verification.
- `created_by`, `created_at`, `updated_by`, `updated_at`, `revision`; append-only audit events where supported by canonical backend architecture.
- `treatment_method` or `intervention` if eventually supported must be a **separate clinician-authored concept**, never silently identical to the objective.

`COMPLETED` requires explicit clinician authority, a dated observation and the associated evidence/justification; a UI checkbox alone must not finalize it. Keep clinical status distinct from a visual selected checkbox.

Use current repository conventions for identifiers, local DB tables, permissions and audit transactions after examining the actual model. **This is not an approved schema or migration.** Confirm deletion/archiving behavior, compatibility, backup/restore and export requirements before implementation.

## 5. Risk and fail-closed acceptance cases

1. Invalid FDI tooth code / contradictory arch-laterality → reject or require correction, do not silently normalize.
2. An objective with absent context may be saved as **DRAFT** only if safe; cannot be automatically declared clinically confirmed.
3. LLM, model, cephalometric calculation or imported radiology text must **never** create, validate, complete or prescribe an objective autonomously.
4. Unauthorized clinician or cross-patient/cross-clinic read/write → denied, no information leak through errors or audit/logs.
5. Stale concurrent editing → version conflict, no silent lost update; history remains inspectable.
6. Missing evidence/author/timestamp for outcome completion → fail closed; only explicit approved clinician can complete it.
7. Manual modification of a finding or cephalo measurement → no implicit treatment objective or silent overwrite.
8. PDF reflects the last persisted authorized clinical state, with visible author/date/status and unverified draft designation.
9. Missing unit/calibration → no fabricated numeric precision or mandatory numerical target.
10. Restore/export/reopen preserves objectives, revisions, patient linkage and state; test only with synthetic fixtures.

## 6. UX and FUE proof required for implementation

- Desktop local first, predictable keyboard navigation and accessible status text; compact categorized checklist with search/add/edit and a longitudinal timeline.
- BEFORE → Goal/target → implementation → AFTER, same 390×844, 430×, 768×1024, 1280×900 viewports when applicable; 200% text scaling, focus and error display.
- FUE-I/G executable on synthetic case: new objective for tooth 25; unilateral posterior crossbite; revisit, change priority, append observation, attempt premature completion and explicit clinician-approved completion; reload to prove persistence and produce a faithful PDF.
- Independent expected-outcome oracle for authorization, association and audit; negative cases and API-to-UI-to-DB-to-PDF consistency tied to exact commit.
- Clinical design approval (scope, phrasing, misuse risk) and human visual approval remain separate from CI passing.

## 7. Non-goals and gates

NO treatment recommendation, extraction decision, surgery indication, auto-diagnosis, autonomous cephalometric-to-objective translation, cloud patient storage or runtime LLM. No real patient fixtures or unapproved medical activation.

**Gate 1:** finish S3-CI integration with separately authorized PR #1288 merge, exact merged HEAD checks and applicable visual evidence. This document does NOT grant permission to merge it.

**Gate 2:** examine existing ortho workflow, UI, backend local schema/RBAC and PDF contracts; approve scoped implementation slices.

**Gate 3:** implement isolated candidate UI/API/persistence and synthetic tests, report FUE outcome and remaining clinical human gate on its own DRAFT PR. No merge/deployment without explicit authorization.

**Canonical project references:** `STATE.md`, `AGENTS.md`, `docs/clinic/DIGITALCROWN_V1_CONSOLIDATED_ROADMAP.md`, `docs/CEPHALO_DIAGNOSTIC_SPEC.md`, `docs/SRPOSE38_LANDMARK_CONTRACT.md`, `docs/audits/CEPHALO_J1B1_S3_38_LANDMARKS_REVIEW.md`.

**NEXT exact:** complete S3-CI parent integration under separate GO, then inspect current orthodontic data/UI contracts and split implementation of this module into a bounded non-clinically-active DRAFT PR.
