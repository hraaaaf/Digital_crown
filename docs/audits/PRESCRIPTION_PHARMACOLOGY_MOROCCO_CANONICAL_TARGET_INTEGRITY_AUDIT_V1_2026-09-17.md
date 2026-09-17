# Morocco pharmacology canonical-target integrity audit V1 — 2026-09-17

Status: ENUMERATED TARGET GRAPH RESOLVED — COMPLETENESS NOT CERTIFIED — CLINICAL ACTIVATION NO

## Goal
Verify that every target referenced by the 170-row historical-to-canonical map resolves deterministically to one of the allowed target classes.

Allowed target classes:
1. retained medicine identity;
2. canonical para row in the base matrix;
3. structural gap alias resolved by the 20-row canonical gap-resolution extension;
4. documented overlap/canonical entity;
5. explicit adjacent-care boundary.

## Deterministic checks
- Historical mapping source rows: 170.
- Unique historical source IDs: 170.
- Mapping file physical structure: header + 170 data rows; line 171 is `OC-SMOKE-003`.
- Mapping rows with `clinical_activation != NO`: 0.
- Mapping target references after expanding split-family targets: 173.
- Resolved as retained medicine identity: 61 target references.
- Resolved directly to base para canonical rows: 79 target references.
- Resolved through structural gap aliases: 22 target references representing 20 unique gap aliases.
- Resolved through documented overlap/adjacent entities: 11 target references.
- Unresolved target references: 0.

The difference between 170 source rows and 173 target references is expected: three source rows intentionally map to two canonical families each (`MAP_SPLIT_FAMILY`).

## Addenda integrity
The 8 post-base addendum rows are separately dispositioned:
- 2 systemic corticosteroid medicine identities retained;
- gingival-antimicrobial toothpaste represented by a product-specific canonical alias requiring exact active/material and concentration;
- barrier spray/solution mapped to the oral-mucosal barrier family;
- floss holder mapped to its dedicated canonical device family;
- high-strength home fluoride gel mapped to the dedicated home-use fluoride family;
- systemic fluoride supplement medicine identity retained;
- non-drug teether mapped to the dedicated pediatric teether family.

Addendum rows with `clinical_activation != NO`: 0.

## Integrity corrections made during this audit
Two referenced entities were conceptually valid but not yet registered as explicit canonical entities:
- `CAN-MED-MIDAZOLAM` for sedation vs emergency-rescue protocol contexts;
- `ADJ-SMOKING-CESSATION-NICOTINE` for gum/lozenge/patch adjacent medical context.

Both are now registered in the V2 canonical-entity-map extension with `auto_merge_allowed=NO` and `clinical_activation=NO`.

## What this proves
- No enumerated source row is silently dropped.
- No historical mapping target is dangling.
- Form/strength/protocol distinctions that require preservation are explicitly carried as discriminators.
- The mapping layer remains fail-closed.

## What this does not prove
- universe-level inventory exhaustiveness;
- Morocco authorization or availability for unresolved products;
- clinical appropriateness for an individual patient;
- readiness for prescription/patient-facing activation.

## Verdict
- `ENUMERATED_TARGET_GRAPH_RESOLVED = YES`
- `UNRESOLVED_TARGET_REFERENCES = 0`
- `CLINICAL_ACTIVATION = NO`
- `COMPLETENESS_CERTIFIED = NO`
- `TAXONOMY_CLOSED = NO`
