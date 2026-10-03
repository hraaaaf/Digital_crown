# Orthodontic Studio LOT07-B — Contract closeout

Base: `8f266ea092a4516679319c9f8d157452e52b5482`
Branch: `feat/ortho-studio-lot07-workbench`

## Result
Two versioned contracts are frozen before visible LOT07 implementation:
- `ortho_case_record_contract_v1.json`
- `cephalo_anatomical_structure_contract_v1.json`

The case contract separates the eight-view clinical photo record from the five intra-oral views used by future photo-reconstruction R&D. Browser localStorage is explicitly forbidden as the canonical patient-media record. Legacy ambiguous photo slots fail closed. Dental meshes require mm units, coordinate space, orientation, source type and checksum.

The structure contract preserves LOT06 as scientific authority. Detector/manual landmark records begin as `CANDIDATE_INPUT` and require the audited canonical input path before measurement authority. Hard-tissue contours, soft-tissue profile and tooth templates are display-only by default. Canonical constructions require authoritative canonical inputs.

## Adversarial review A — science / clinical authority
Initial findings fixed:
- MAJOR: landmarks were initially measurement-authoritative by default.
- MAJOR: legacy `intra_profile` could not safely map to left or right.
Final from-zero review: 0 BLOCKER / 0 MAJOR.
Severe score: **9.5/10**.

## Adversarial review B — data / provenance / evidence
Initial findings fixed:
- MAJOR: model records lacked mandatory metric/coordinate/integrity metadata.
- MAJOR: five-photo reconstruction had no complete-input gate.
Final from-zero review: exact-head visual reports + 8 screenshot hashes reproducible; 0 BLOCKER / 0 MAJOR.
Severe score: **9.5/10**.

## Confirmation
- contract tests: 12/12 PASS;
- capture harness syntax: PASS;
- git diff check: PASS;
- BEFORE normal + 200% observed at 390/430/768/1280.

LOT07 remains OPEN. Next: registry-driven Layer Manager and edit-history contract.
