# Prescription Pharmacology — Core-5 Qualified Review Form — 2026-09-18

Status: HUMAN_REVIEW_REQUIRED
Clinical activation authorized: NO

This form is intentionally non-prescriptive. It records review decisions only; it does not contain or generate dosing instructions.

Allowed dimension decisions: `PASS` / `FAIL` / `NEEDS_CORRECTION` / `NOT_REVIEWED`.

Allowed final recommendation:
- `KEEP_FAIL_CLOSED`
- `ELIGIBLE_FOR_TECHNICAL_ACTIVATION_REVIEW`

The second value does not activate a medicine. Any later activation requires a separate code/data change, deterministic tests, exact-HEAD CI and integration review.

## Reviewer identity

- Name:
- Professional role / qualification:
- Review date:
- Current primary source set reviewed:

## Core-5 decision matrix

| Medicine | Dental indication | Adult regimen | Pediatric / age boundary | Max dose / treatment limit | Duration / review interval | Contraindications / precautions | Interactions | Renal / hepatic boundary | Morocco exact product/form/strength/presentation | Backend ↔ UI/PDF consistency | Final recommendation | Clinical activation |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| MED-PAIN-001 — paracetamol | NOT_REVIEWED | NOT_REVIEWED | NOT_REVIEWED | NOT_REVIEWED | NOT_REVIEWED | NOT_REVIEWED | NOT_REVIEWED | NOT_REVIEWED | NOT_REVIEWED | NOT_REVIEWED | KEEP_FAIL_CLOSED | NO |
| MED-PAIN-002 — ibuprofen | NOT_REVIEWED | NOT_REVIEWED | NOT_REVIEWED | NOT_REVIEWED | NOT_REVIEWED | NOT_REVIEWED | NOT_REVIEWED | NOT_REVIEWED | NOT_REVIEWED | NOT_REVIEWED | KEEP_FAIL_CLOSED | NO |
| MED-ABX-003 — phenoxymethylpenicillin / penicillin V | NOT_REVIEWED | NOT_REVIEWED | NOT_REVIEWED | NOT_REVIEWED | NOT_REVIEWED | NOT_REVIEWED | NOT_REVIEWED | NOT_REVIEWED | NOT_REVIEWED | NOT_REVIEWED | KEEP_FAIL_CLOSED | NO |
| MED-ABX-001 — amoxicillin | NOT_REVIEWED | NOT_REVIEWED | NOT_REVIEWED | NOT_REVIEWED | NOT_REVIEWED | NOT_REVIEWED | NOT_REVIEWED | NOT_REVIEWED | NOT_REVIEWED | NOT_REVIEWED | KEEP_FAIL_CLOSED | NO |
| MED-ABX-004 — metronidazole | NOT_REVIEWED | NOT_REVIEWED | NOT_REVIEWED | NOT_REVIEWED | NOT_REVIEWED | NOT_REVIEWED | NOT_REVIEWED | NOT_REVIEWED | NOT_REVIEWED | NOT_REVIEWED | KEEP_FAIL_CLOSED | NO |

## Corrections requested

Record any correction with:
- medicine ID;
- affected dimension;
- source supporting the correction;
- exact issue;
- required change;
- whether re-review is required.

## Gate

Until every required dimension has a qualified reviewer decision and every correction is resolved, all five medicines remain fail-closed and `clinical_activation=NO`.
