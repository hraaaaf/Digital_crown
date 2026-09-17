# Prescription / Pharmacology Morocco — Pending Status Audit V1

Date: 2026-09-17
Branch: `docs/pharmacology-m1-handover-20260915`
Baseline HEAD audited before this file: `5f2ce8c7a1ad9a287b822743d4435d9a89dc48e8`
Status: AUDIT / FAIL-CLOSED
Clinical activation: NO
AMMPS contact: NONE

## Goal

Establish a defensible denominator for the remaining Morocco localization / regulatory / protocol work without treating stale `TO_VERIFY` fields in the early master dataset as the current truth.

Success criteria for this audit:

1. distinguish canonical current layers from historical/stale summary fields;
2. count unresolved Morocco-status concepts in canonical para and protocol layers;
3. identify the remaining blocker to a global certified percentage;
4. preserve fail-closed clinical activation.

## 1. Source-of-truth hierarchy used for this audit

Current status precedence for closure accounting:

1. canonical para matrix;
2. canonical structural-gap extension;
3. canonical para addenda extension;
4. protocol localization layer;
5. dedicated localization / clinical passes as provenance;
6. early `MASTER_DATASET_V1` only as a historical aggregation layer, not as the current closure denominator.

Reason: later localization passes intentionally upgraded multiple Morocco statuses without rewriting every older summary row. Counting the old master statuses directly would therefore double-count or falsely report already-localized concepts as unresolved.

## 2. Canonical para matrix denominator

File: `PRESCRIPTION_PHARMACOLOGY_MOROCCO_PARA_CANONICAL_MATRIX_V1_2026-09-17.csv`

Total canonical para concepts: **52**.

Morocco-status accounting:

- **21 / 52** have a positive Morocco market/form evidence status that is not itself flagged `TO_VERIFY` or `REGULATORY_PENDING`.
- **31 / 52** remain unresolved for Morocco product/form/regulatory closure.

Important: a positive market-status is not regulatory approval and is not clinical activation.

High-priority unresolved para groups include:

- high-fluoride toothpaste;
- stannous-fluoride and arginine desensitization products;
- hydroxyapatite / nano-hydroxyapatite products;
- professional fluoride varnish;
- professional fluoride gel / foam;
- high-strength home fluoride — market evidence exists but regulatory status remains pending;
- SDF exact 38% product / concentration;
- essential-oil, peroxide, chlorine-dioxide, zinc, hexetidine and povidone-iodine mouthrinses;
- water flosser;
- plaque disclosers;
- xerostomia gum / lozenges;
- appliance cleansers / storage;
- denture cleansers / adhesives / OTC reline;
- whitening strips / home gel / professional systems;
- post-op products;
- stock/custom mouthguards;
- medicated teething product.

## 3. Structural-gap extension denominator

File: `PRESCRIPTION_PHARMACOLOGY_MOROCCO_PARA_CANONICAL_GAP_RESOLUTION_V1_2026-09-17.csv`

Total structural gaps materialized: **20 / 20**.

Status:

- **18 / 20** remain `TO_VERIFY_BY_PRODUCT` for Morocco/product localization.
- **2 / 20** are generic home-care concepts (`saline rinse`, `bicarbonate rinse`) where product-localization is not the primary closure target; both still require evidence review before any clinical recommendation.
- **20 / 20** remain `clinical_activation=NO`.

This means the structural taxonomy gap is closed as a mapping problem, but not as a clinical / Morocco-evidence problem.

## 4. Para addenda canonical extension

File: `PRESCRIPTION_PHARMACOLOGY_MOROCCO_PARA_ADDENDA_CANONICAL_EXTENSION_V1_2026-09-17.csv`

- 1 canonical product-specific gingival antimicrobial toothpaste concept.
- Morocco example evidence exists.
- Exact active / product-specific clinical interpretation is still required.
- `clinical_activation=NO`.

## 5. Protocol localization denominator

File: `PRESCRIPTION_PHARMACOLOGY_MOROCCO_PROTOCOL_LOCALIZATION_LAYER_2026-09-17.csv`

Total protocol/localization lines: **15**.

Morocco evidence status:

- **4 / 15** have some concrete Morocco form/market evidence:
  - midazolam injectable 5 mg/mL;
  - diazepam oral forms;
  - hydroxyzine oral market evidence (secondary, not primary AMMPS form-level closure);
  - salbutamol 100 microgram/dose inhaler.
- **11 / 15** remain unresolved for exact Morocco form/strength/supply/regulatory closure.

Protocol validation status:

- **15 / 15 are not clinically activated**.
- **15 / 15 are not closed as deployable clinical protocols**.
- concentration/form mismatches remain explicit for epinephrine and glyceryl trinitrate;
- injectable midazolam must not be substituted for the unproven oromucosal target form.

High-priority protocol gaps:

1. epinephrine 1 mg/mL IM exact Morocco product/form;
2. aspirin 300 mg dispersible exact product/form;
3. glucagon 1 mg IM;
4. GTN 400 microgram/dose exact spray strength;
5. standardized oral emergency glucose;
6. medical oxygen supply/regulatory framework;
7. exact antihistamine DCI/forms;
8. midazolam oromucosal exact form;
9. nitrous oxide + oxygen Morocco dental regulatory framework;
10. pilocarpine / cevimeline Morocco product evidence.

## 6. What is NOT yet a valid global completion percentage

A global completion percentage is still **not certifiable** because the medicine clinical evidence is distributed across narrative clinical/localization passes and is not yet normalized into one row-level current-status registry equivalent to the para canonical matrix.

The early master dataset contains many stale `TO_VERIFY` / `TO_VALIDATE` placeholders that have since been partially superseded by dedicated evidence passes. It cannot safely be used as the final medicine denominator without a projection/reconciliation step.

Therefore:

- historical coverage denominator: known and mapped;
- para canonical denominator: known;
- protocol denominator: known;
- medicine row-level current clinical/regulatory denominator: **not yet normalized**.

## 7. Critical next action

Build a **Medicine Current Status Projection V1** that reconciles the medicine inventory against all later clinical and Morocco-localization passes.

Minimum fields:

- canonical medicine entity / DCI;
- source historical IDs;
- intended dental role;
- exact form / strength target;
- current Morocco status;
- current clinical evidence status;
- regulatory evidence status;
- protocol / specialist boundary;
- unresolved critical fields;
- clinical activation (`NO` unless explicitly and independently certified later).

Only after that projection exists can a global denominator and a defensible completion percentage be calculated.

## 8. Safety conclusion

No clinical activation is authorized by this audit.

Market presence != regulatory approval.
Foreign clinical guidance != Morocco regulatory proof.
Form-level availability != dental indication.
Pending / mismatched / product-specific status must fail closed.

No AMMPS contact was performed.
