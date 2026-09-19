# V1-05 / F5 — Scientific Superimposition — Start / Recovery Prompt

**Canonical base:** `master@20bfe3349399bf49a2f5ece14c5f70526e9d4a1b`  
**F4 post-merge:** certified; PR #619 closed without merge.  
**F5 branch:** `feat/v1-05-f5-scientific-superimposition`

## Goal
Create a longitudinal cephalometric superimposition that is scientifically justified, deterministic, source-first, reproducible and non-interpretative.

## Scientific decision
Read first:
1. `docs/clinic/audits/V1_05_F5_SCIENTIFIC_SUPERIMPOSITION_LITERATURE_REVIEW.md`
2. `docs/clinic/audits/V1_05_F5_METHOD_DECISION_RECORD.md`
3. `docs/clinic/audits/V1_05_F5_VALIDATION_STRATEGY.md`

F5-MDR-001 selects anterior-cranial-base structural feature registration with a clinician-confirmed stable ROI and a 4-DOF 2D similarity transform. S-N-only registration and unrestricted affine/projective warping are rejected.

## Existing canonical inputs
- OrthoCase;
- OrthoTimepoint;
- OrthoTimepointEvidence;
- CephaloAnalysis;
- original cephalogram path;
- SRPose38 landmarks/evidence provenance;
- calibration provenance.

## Safety boundary
No diagnosis, recommendation, success/failure, improvement/aggravation, growth prediction, normative heatmap or progress score.

## Next exact
Implement the pure deterministic registration primitive and synthetic numerical tests first. Do not persist a new database table yet. Expose raw/reproducible transform metadata, fail closed, and keep clinical activation blocked pending independent scientific + clinician validation.

## UI sequence
No visual integration before engine contract/tests:
BEFORE -> Goal -> mockup -> implementation -> AFTER same viewports -> accessibility/runtime/overflow -> severe visual review -> human gate.

## Recovery note
The Notion handover previously referenced this path before the file existed on `master`. This file is now the canonical repository recovery point for F5.
