# Morocco para localization — dentin hypersensitivity / desensitization

Date: 2026-09-17
Status: RESEARCH / FAIL-CLOSED
Clinical activation: NO
AMMPS contact: NONE

## Goal

Localize the desensitization families without converting brand availability or foreign formulation data into a Morocco regulatory claim.

## Clinical evidence cross-check

- ADA toothpaste evidence summary reports that twice-daily self-applied stannous, potassium +/- stannous, or arginine formulations can reduce dentin hypersensitivity pain, based on the 2023 network meta-analysis by Pollard et al.
- PubMed-indexed 2023 network meta-analysis (32 studies, 4,638 participants) supports stannous, potassium +/- stannous, and arginine formulations for dentin hypersensitivity pain reduction.
- A newer PubMed-indexed network meta-analysis reports the most consistent clinically meaningful reductions for stannous fluoride and arginine dentifrices, while certainty varies by formulation/outcome.

Decision: retain stannous fluoride, potassium salts, and arginine as distinct canonical active families. Do not rank them as universally superior for an individual patient and do not infer product interchangeability.

## Morocco evidence

### Potassium family

Official GUM Morocco evidence:
- GUM Morocco has a dedicated sensitive-teeth range and lists SensiVital toothpaste.
- The official Morocco SensiVital brochure/formulation surface identifies potassium nitrate 5% together with hydroxyapatite/copolymer and fluoride/isomalt.

Classification:
- `PARA-DH-K-001`: `VERIFIED_MARKET_MA_OFFICIAL_BRAND_SITE_PRODUCT_SPECIFIC`
- This verifies a Morocco-market potassium desensitizing product example; it does not validate every potassium formulation.

### Stannous fluoride family

No sufficiently clean Morocco-specific official product/formulation evidence was locked in this pass.

Classification:
- `PARA-DH-SN-001`: remain `TO_VERIFY_BY_PRODUCT`

### Arginine family

International manufacturer evidence confirms arginine/Pro-Argin sensitivity products, but the surfaced official pages were not Morocco-specific.

Classification:
- `PARA-DH-ARG-001`: remain `TO_VERIFY_BY_PRODUCT`
- Foreign manufacturer evidence must not be treated as Morocco availability evidence.

## Safety / data rules

1. Diagnose/exclude alternative causes of dental pain before treating a symptom as dentin hypersensitivity.
2. Product concentration, fluoride content, age limits and instructions remain product-specific.
3. Market evidence does not equal Morocco regulatory validation.
4. No automatic substitution between potassium, stannous fluoride, arginine or hydroxyapatite products.
5. `clinical_activation=NO` remains mandatory until downstream clinical/regulatory gates are satisfied.

## Result

One canonical family receives stronger Morocco localization: potassium-based desensitizing toothpaste. Stannous fluoride and arginine remain open for Morocco product-level verification. No clinical activation is authorized.
