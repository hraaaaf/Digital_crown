# HANDOVER — Digital Crown / Mutuelles dentaires — FAR

Date: 2026-09-17
Repository: `hraaaaf/Digital_crown`
Branch: `master`
Global PR: `#559` — MERGED
Merge SHA: `20d2e01aa1f097ca93dd0a5a6699a596a392d7d8`
Status: `FAR_GLOBAL_CLOSEOUT_COMPLETE`

## Goal

Implement FAR dental support inside the existing single Mutuelles engine from the exact cabinet-accepted derived reference, while keeping prescription content clinically separate and fail-closed.

## Source gate

`docs/audits/MUTUELLES_DENTAIRES_FAR_GATE.md`

Status: `SOURCE_GATE_PASSED`.

Frozen application reference:

- filename `FAR_CABINET_VALIDATED_DERIVED_REFERENCE_FINAL.pdf`
- SHA-256 `c953d74f25ee5e3160683f16c45783448d55ea89640c710653a3e2cbf782bf42`
- size `759862` bytes
- `2` physical pages
- A4 landscape `841.8897705 x 595.2755737 pt`
- physical page 1 = logical Page 4 | Page 1
- physical page 2 = logical Page 2 ORDONNANCE | Page 3

Trust is `CABINET_VALIDATED_DERIVED_REFERENCE`, never `OFFICIAL_PRIMARY`.

## Architecture lock

One engine only:

`Patient -> Honoraires -> Preparer organisme -> Revue praticien -> Validation -> PDF -> DocumentArchive`

The Digital Crown ordonnance remains the single clinical prescription truth. FAR only copies explicit archived prescription fields; no medication fact is inferred from acts or NGAP.

## Implemented and verified

- FAR derived-reference trust and exact SHA binding.
- FAR administrative facts, relationship and claim-context validation.
- FAR overlay/profile integrated into the existing Mutuelles engine.
- Logical Page 2 ORDONNANCE remains clinically separate from dental-act mapping.
- Automatic bridge after successful archived Digital Crown ordonnance for FAR patients.
- Dedicated deterministic FAR prescription renderer with fixed PDF typography independent from the application theme.
- Explicit medication name/dosage/form/posology copied without inference.
- Fail-closed template SHA, page-count, capacity and printable-width checks.
- Derived FAR archive linked to `source_ordonnance_document_id`.
- No generated signature, cachet or insurer-decision content.
- FAR review UI and deterministic visual certification harness.

## Visual proof

Cabinet visual calibration V4 was explicitly accepted on 2026-09-17.

Automated AFTER evidence:

- workflow: `Mutuelles FAR Visual Certification`
- run: `35255531577`
- conclusion: `SUCCESS`
- artifact: `10511859997`
- artifact size: `313777` bytes
- artifact digest: `sha256:44530836575a5740b752597bea9835b3ffb966945440a7931e9f6784974d140b`
- viewports: `390x844`, `768x1024`, `1280x900`

The harness uses deterministic Vite build + preview rather than the former brittle development-server dependency optimization path.

## Merge history

Prescription renderer PR `#581` was explicitly authorized and merged into the FAR integration branch.

- certified head before merge: `da49fc183ff578c8434c40e3844d7ec0a769702c`
- merge SHA: `6c6cc7ae00bf476a6b133784da4a6b70f442d1be`

Global FAR PR `#559` was explicitly authorized, moved from draft to ready, and merged into `master` with an expected-head guard.

- certified PR head: `44781f601b9835d06f5d59a84303eb39418fa426`
- global merge SHA: `20d2e01aa1f097ca93dd0a5a6699a596a392d7d8`

No Vercel deployment and no production DB mutation occurred.

## Final post-merge proof

Post-merge checks were inspected on the exact master merge SHA `20d2e01aa1f097ca93dd0a5a6699a596a392d7d8`.

Observed executed checks include:

- `Frontend (tests & build)` — `SUCCESS`
- `PostgreSQL 18 + immutable release invariants` — `SUCCESS`
- contextual M4 checks not applicable to this merge — `SKIPPED`

No observed post-merge check failure was present in the inspected check set.

## Closeout

The FAR global implementation is merged on `master` and its source trust, architecture boundary, prescription bridge, deterministic renderer, archive linkage, visual evidence, pre-merge certification and observed post-merge checks are recorded above.

No further FAR functional development is part of this closeout.

## Next exact

Return to the next authorized Digital Crown V1 chantier. Any future FAR change starts from `master` and must preserve the single Mutuelles/Honoraires engine and the no-inference prescription boundary.

## Sequence remaining

`none for FAR global closeout`
