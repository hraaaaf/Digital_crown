# Orthodontic Studio LOT07 — Closeout evidence

Status: CLOSEOUT EVIDENCE RECORDED — exact-HEAD confirmation required after this document is committed.

## Goal

Close LOT07 only if the Orthodontic Studio Workbench is demonstrably coherent across:
- canonical LOT06 scientific authority;
- LOT07 workbench contracts and editing state;
- canonical media record;
- canonical export / serialization / provenance;
- responsive rendering at 390×844, 430×932, 768×1024, 1280×900;
- 200% root-text scaling without hidden component overflow or clipped critical text.

Gate: `ORTHO_STUDIO_WORKBENCH_VERIFIED`.

## Product code under review

Code lineage before this closeout document:
- LOT07-G export/provenance convergence: `c6c608fb96b76407cd24c824aaf06a7f5018b317`.
- 200% reflow hardening: `4c88f8998efa9deec0d6d81e0b0702065608d1fa`.
- final rail/layer-manager reflow fix: `fbad14abe8f8ecc3ba4461a48d0fd3facdd22325`.

The final gate must be re-confirmed on the commit containing this document.

## LOT07-G export / provenance evidence

The canonical workbench export:
- is built server-side;
- does not invoke `CephaloEngine` or `calculate_metrics`;
- resolves scientific state through LOT06 typed evidence and the verified active chain;
- fails closed when LOT06 scientific prerequisites are absent or incoherent;
- includes case + timepoint, current landmarks and canonical dependency landmarks, persisted correction history, display-only traced structures, relevant layer state, LOT06 construction/measurement references, calibration provenance, media references, explicit schema/version/authority;
- rejects client measurement authority, longitudinal registration outside LOT07, calibrated display coordinates without calibration, duplicate structure ids, and invalid/tampered correction history;
- preserves patient-access / tenant isolation.

Synthetic export fixture is deterministic; prior convergence generated identical SHA-256:
`40CFFDB8AF739AB936325C4A4CD62DBF2FA24BFF1E5E0FD482837C4BB0FEAEF8`.

## Responsive / 200% BEFORE → AFTER

BEFORE reference: `ORTHO_STUDIO_LOT07_BEFORE_VISUAL_EVIDENCE.md`.

Observed BEFORE 200% defects included:
- `Céphalo...` title truncation;
- `Toute...` workbench title truncation;
- `Analyse Toutes...` panel title truncation;
- clipped or compressed controls despite document-level `horizontalOverflow=false`.

AFTER harness now explicitly rejects:
- document horizontal overflow;
- component horizontal overflow for stepper, layer manager, workbench sidebar, analysis panel;
- clipped critical text for workspace title/patient, workbench title, analysis title and stepper buttons.

The final layout uses wrapping instead of truncation and a wider desktop workbench rail. At 1280×900 / 200%, the prior overflow was localized to the layer manager and workbench sidebar and then eliminated.

## Required exact-HEAD commands

Backend:
`python -m pytest -q backend/tests/test_ortho_workbench_export_lot07g.py backend/tests/test_ortho_media_record_lot07f.py backend/tests/test_cephalo_runtime_chain.py backend/tests/test_ortho_studio_lot07_contracts.py`

Frontend:
`npm test -- --run src/features/ortho/CephaloWorkspace.g4Interactive.test.tsx src/features/ortho/components/CephaloAnalysisWorkbenchPanel.test.tsx src/features/ortho/orthoLayerRegistry.test.ts src/features/ortho/orthoLandmarkEditHistory.test.ts src/features/ortho/orthoWorkbenchExport.test.ts`

Build:
`npm run build:test`

Visual:
- `node scripts/capture-ortho-studio-lot07-layer-manager-after.mjs`
- `node scripts/capture-ortho-studio-lot07-layer-manager-after-text200.mjs`
- `node scripts/capture-ortho-studio-lot07f-media-after.mjs`

## Adversarial review perspectives

### Perspective A — accessibility / responsive / visual integrity

Search for:
- clipping hidden by document-level no-overflow;
- title truncation;
- component scroll-width overflow;
- broken 200% reflow;
- unreachable controls;
- viewport-specific regressions.

Target result for convergence: no new BLOCKER, no new MAJOR, no significant unaccepted debt.

### Perspective B — scientific authority / regression / evidence integrity

Search for:
- any new frontend scientific calculation;
- LOT06 formula duplication;
- scientific authority accepted from client;
- failure to preserve tenant/patient access;
- evidence generated from the wrong HEAD;
- visual harness false positives.

Target result for convergence: no new BLOCKER, no new MAJOR, no significant unaccepted debt.

## Severe scoring rubric

Scores are assigned only after final exact-HEAD confirmation:
- scientific-authority isolation / provenance;
- normal responsive composition;
- 200% reflow / accessibility;
- media workbench;
- evidence quality / reproducibility.

A high score does not replace the gate criteria.
