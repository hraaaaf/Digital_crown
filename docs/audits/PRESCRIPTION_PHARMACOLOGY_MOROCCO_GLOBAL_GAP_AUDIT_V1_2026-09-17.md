# Morocco prescription + oral-care global gap audit V1 — 2026-09-17

Status: GAP AUDIT STARTED — COMPLETENESS NOT CERTIFIED — CLINICAL ACTIVATION NO

## Goal
Reconcile the historical 170-row master inventory, subsequent addenda/localization work, and the 51-row para canonical matrix before any completeness or activation claim.

## Observable success criterion
A later closeout may claim taxonomy completeness only when every historical concept is either:
1. mapped to a canonical entity/family;
2. explicitly retained as a distinct missing canonical concept; or
3. explicitly classified as duplicate/out-of-scope with rationale.

This V1 does not yet meet that criterion.

## Verified structural findings

### Historical inventory
The master inventory contains 170 original rows spanning medicines and oral-care/adjacent products. Prior audit identified exact/quasi duplicate and semantic-overlap clusters; therefore row count is not a completeness metric.

### Current para canonical layer
The canonical para matrix contains 51 data rows. It deliberately compresses several historical SKU/form variants into clinical families. This is correct only where the family retains meaningful form/active/indication distinctions.

### Confirmed canonicalization gaps still requiring disposition
The historical inventory contains concepts not represented as their own current canonical row or not yet proven safely absorbed by a canonical family. Priority examples identified from direct inventory review:

- denture brush — exact Morocco product evidence now exists; not equivalent to denture cleanser;
- orthodontic V-cut toothbrush — may be an indication/form variant of manual brush but requires explicit mapping;
- post-surgical ultrasoft toothbrush — should not be silently absorbed into generic manual brush without protocol/form mapping;
- sulcular toothbrush — needs explicit mapping or retention decision;
- floss threader and superfloss — current generic floss family may be too coarse for ortho/bridge/implant use;
- implant-safe coated interdental brush — current interdental-brush family needs material/safety attribute if absorbed;
- high-fluoride 2800 ppm vs 5000 ppm toothpaste — current high-fluoride family is intentionally broad but concentration remains a required product-level attribute;
- CHX 0.12% vs 0.2% vs CHX gel — current CHX mouthrinse family does not by itself represent gel form;
- fluoride mouthrinse 0.05% vs 0.2% — concentration/use protocol remains product-level and must not be erased;
- strontium sensitivity toothpaste and low-abrasivity erosion toothpaste — disposition still required;
- SLS-free toothpaste — disposition still required;
- saline and bicarbonate home rinses — not represented in current canonical para matrix and require scope decision;
- benzydamine rinse — medicine/para boundary must remain explicit.

## Localization gaps still open
High-priority unresolved Morocco exact-product evidence remains for:
- high-fluoride 2800/5000 ppm toothpaste;
- professional fluoride varnish;
- professional fluoride gel/foam;
- SDF 38%;
- hydroxyapatite/nano-hydroxyapatite exact Morocco product;
- stannous fluoride and arginine exact Morocco product;
- water flosser;
- appliance cleanser/storage;
- denture cleanser/adhesive/reline;
- whitening strips/home peroxide/professional systems;
- plaque disclosers;
- xerostomia gum/lozenges;
- selected mouthrinse actives (EO, peroxide, chlorine dioxide, zinc, hexetidine, povidone iodine).

## Safety / evidence gates
- Market presence != Morocco medicine authorization.
- Foreign regulatory evidence != Morocco regulatory evidence.
- Manufacturer claims != independent clinical evidence.
- Product-family evidence != exact concentration/form evidence.
- No patient-facing or prescription activation from this audit.
- No AMMPS contact.

## Verdict V1
- `COMPLETENESS_CERTIFIED = NO`
- `TAXONOMY_CLOSED = NO`
- `CLINICAL_ACTIVATION = NO`
- The next critical path is canonical mapping of the historical inventory, not additional indiscriminate SKU accumulation.
