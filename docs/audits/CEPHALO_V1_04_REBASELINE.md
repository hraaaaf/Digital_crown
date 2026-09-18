# V1-04 — Céphalométrie scientific re-baseline

Date: 2026-09-18

## Goal

Re-baseline current cephalometric runtime after the certified V1-03 closeout and correct only evidence-backed V1 blockers, without reopening the already closed R20 workbench lot or introducing new diagnosis, indication or treatment inference.

## Verified baseline

- Branch base: `master@7454215274032898d1a50659d624a5cb32aab494`.
- Base CI: `35335941911` SUCCESS.
- Base PostgreSQL certification: `35335941919` SUCCESS.
- No Céphalo/Ortho runtime file changed between the R20 canonical baseline and this V1-04 base; R20 remains closed.

## Open gap selected

The existing R18 frontend/backend concordance audit did not include the COM incisor relations `Surplomb` and `Recouvrement`, although both are computed and displayed by the product.

The extended audit produced one deterministic divergence on the same landmarks and calibration:

- case: `clinical_orientation_reference`
- frontend Surplomb: `+2.6 mm`
- backend Surplomb: `-2.6 mm`
- delta: `5.2 mm`
- Recouvrement: concordant
- run: `35338035397` — expected FAILURE exposing the gap
- artifact: `10543458942`

Root cause: the frontend converted overjet to an absolute magnitude while the backend preserved direction.

## Scientific source check

Two independent peer-reviewed sources support treating overjet as a signed horizontal incisor relation rather than an absolute-only magnitude:

1. Hong M, Kook YA, Kim MK, et al. *The Improvement and Completion of Outcome index: A new assessment system for quality of orthodontic treatment.* Korean J Orthod. 2016;46(4):199-211. DOI: 10.4041/kjod.2016.46.4.199. PMID: 27478797. The method records overjet in millimetres as a positive or negative value.
2. Zhang X, Ai-Gumaei W, Xing L, et al. *A cross-sectional study of age-related changes in the position of upper and lower lips relative to the esthetic plane.* Sci Rep. 2025;15:13833. DOI: 10.1038/s41598-025-98777-4. PMID: 40263390. Its measurement definitions explicitly distinguish positive overjet from reversed/negative overjet and positive from negative overbite.

Additional peer-reviewed literature consistently expresses overjet and overbite in millimetres and recognizes reverse/negative overjet and negative/open-bite values.

### Safety boundary

These sources support the signed relation and the millimetre unit. They do **not** independently validate Digital Crown's exact legacy Frankfort-projection construction as a universal orthodontic standard. Therefore:

- V1-04 removes the frontend absolute-value distortion so frontend and backend preserve the same signed patient geometry;
- `M_OVERBITE_V1` unit is locked to `mm`;
- `M_OVERJET_MM_V1` and `M_OVERBITE_V1` remain `LEGACY_TO_AUDIT` for construction/provenance;
- no norm, diagnostic classification, severity label, indication or treatment rule is activated.

## Implementation

- Extend R18 concordance extraction/comparison with Surplomb and Recouvrement.
- Preserve signed overjet in `computeStep3Data` instead of applying `Math.abs`.
- Add frontend regression covering positive and reverse overjet.
- Add backend runtime regression covering signed overjet/overbite and calibration fail-closed behavior.
- Lock `M_OVERBITE_V1` unit to `mm` while keeping its legacy geometry status non-authoritative.

## Success / proof required

- extended concordance: zero divergence;
- targeted frontend/backend regressions green;
- exact-head CI and Céphalo scientific gates green;
- no new clinical inference;
- BEFORE/AFTER visual evidence if the corrected signed value is user-visible in the audited Step 3 workflow;
- severe dual review before merge.
