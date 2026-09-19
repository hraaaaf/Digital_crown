# V1-05 Ortho Journey — F5 Closeout

Status: **MERGED — POST-MERGE CERTIFICATION PENDING**

## Scope

F5 adds a deterministic, source-first longitudinal lateral-cephalogram superimposition engineering preview.

The method family implemented is:
- clinician-confirmed anterior cranial-base ROI
- SIFT features
- L2 KNN ratio < 0.7
- robust 4-DOF 2D similarity transform only
- no shear, perspective, elastic deformation, or automatic clinical interpretation

F5 remains hidden/OFF by default and requires explicit engineering-preview flags.

## Product baseline

Parent F4 merge:
`20bfe3349399bf49a2f5ece14c5f70526e9d4a1b`

Product PR:
#620

Product candidate HEAD:
`a90d7c61ae8ff992253d28dba3b36cc5eabaa5a6`

Merged product SHA:
`2cfb0dc53b71daa9f8cbb63e966a5cab4481fc10`

Merged at:
2026-09-19T08:31:54Z

## Scientific governance

Scientific gate documents:
- `docs/clinic/audits/V1_05_F5_SCIENTIFIC_SUPERIMPOSITION_LITERATURE_REVIEW.md`
- `docs/clinic/audits/V1_05_F5_METHOD_DECISION_RECORD.md`
- `docs/clinic/audits/V1_05_F5_VALIDATION_STRATEGY.md`
- `docs/clinic/audits/V1_05_F5_ENGINE_CONTRACT.md`
- `docs/clinic/audits/V1_05_F5_SOURCE_CONTRACT.md`
- `docs/clinic/audits/V1_05_F5_INDEPENDENT_SCIENTIFIC_REVIEW_PACKET.md`

Registered source families include ABO structural superimposition guidance, Graf 2022, Jiang 2020, Zhao 2025 and OpenCV matcher implementation documentation.

Important boundary:
- source records remain candidate / needs_review only
- `clinically_validated=false`
- `acquisition_protocol_status=UNVERIFIED`
- adult-only engineering applicability
- growing patients fail closed
- no cross-machine / cross-protocol equivalence claim

## Independent scientific review status

**NOT COMPLETED.**

A real independent reviewer was not available in the connected environment at merge time.
The prepared review packet does not count as an independent review.

The product owner explicitly instructed merge despite this remaining governance gate.
This is recorded as an owner merge override, not as a successful scientific-review gate.

Clinical activation remains blocked pending:
1. independent scientific review
2. named human clinical validation of method/applicability
3. acquisition-protocol validation/provenance adequate for the intended use

## Engineering safety boundary

F5 does not automatically provide:
- diagnosis
- treatment recommendation
- improvement / worsening
- success / failure
- progress score
- growth prediction
- normative heatmap
- clinical-validity claim

Backend and frontend preview are OFF by default.

Required preview flags:
- `DIGITAL_CROWN_F5_ENGINEERING_PREVIEW=1`
- `VITE_F5_ENGINEERING_PREVIEW=1`

Permission:
- canonical `cephalo` permission required backend and frontend

Media boundary:
- canonical local cephalograms only under `api/static/uploads/radios/`

## Pre-merge certification — FINAL

Exact candidate HEAD:
`a90d7c61ae8ff992253d28dba3b36cc5eabaa5a6`

Runs:
- CI `35430755915` — SUCCESS
- T2 Runtime Browser Certification `35430755873` — SUCCESS
- Ortho F5 BEFORE `35430755892` — SUCCESS
- Ortho F5 AFTER `35430755887` — SUCCESS
- Agenda A5 Visual Evidence `35430761732` — SUCCESS
- Cephalo R15 AFTER `35430755869` — SUCCESS
- Cephalo R15bis AFTER `35430755875` — SUCCESS
- Ortho F3 AFTER `35430755858` — SUCCESS

## Visual evidence

Certified viewports:
- 390×844
- 768×1024
- 1280×900

BEFORE artifact:
- id `10580602451`
- digest `sha256:8051782eb393f0907b00742f1e25f5670ea61c8a0cb1bf4c14b30ff4c10f571f`

AFTER artifact:
- id `10580642382`
- digest `sha256:73341d19f60f45b36380724086deb2b376cf10ee8cab55b643eae630dd5a15af`

Verified:
- exact PNG dimensions
- no horizontal overflow
- no page errors
- no console errors
- no forbidden automatic clinical interpretation language
- source provenance visible
- adult engineering applicability visible
- acquisition-protocol warning visible
- keyboard initial focus / Escape close / focus restoration

## Visual score — severe

Assistant visual review:
**9.2 / 10**

The score is not 10/10 because:
- the viewer intentionally carries visible engineering/scientific metadata that adds density
- acquisition provenance is explicitly unresolved
- clinical validation is not established
- the scientific independent-review gate is still open

Human visual gate:
- product owner explicitly instructed merge after reviewing the final evidence

## Merge decision

PR #620 was merged by explicit product-owner instruction.

This merge integrates an engineering-preview implementation.
It does **not** certify clinical use.

## Post-merge certification

Pending at closeout-file creation.

Required proof:
- `master` remains at merged product SHA or a docs-only descendant
- post-merge CI green
- post-merge T2 green
- no regression in F5 BEFORE/AFTER contracts where applicable

## Next

1. obtain post-merge machine certification
2. update this file with exact runs
3. keep F5 hidden/OFF for normal users
4. perform independent scientific review before any clinical activation
5. perform named human clinical validation before any clinical activation

No F6 handover is declared here because no canonical F6 file or scope exists in the repository at this merge point.
