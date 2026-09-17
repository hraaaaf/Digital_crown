# Morocco para localization pass 9 — plaque disclosure, CHX gel, denture/appliance care — 2026-09-17

Status: MARKET LOCALIZATION ONLY — CLINICAL ACTIVATION NO

## Goal
Attach stronger Morocco-local evidence to canonical families that remained open after the 170→canonical reconciliation, without confusing market/family evidence with medicine authorization or patient-specific clinical validation.

## Evidence rules
- Official Morocco manufacturer/distributor/HCP surface > Morocco retailer > foreign manufacturer page.
- A Morocco retailer can corroborate market presence but does not prove regulatory status.
- A foreign/global manufacturer catalogue can clarify a product specification but cannot prove Morocco availability or authorization.
- No result in this pass changes `clinical_activation=NO`.

## 1. Plaque discloser

### Morocco evidence
TePe Maroc official local product page lists `TePe PlaqSearch` as a two-colour chewable plaque-disclosing tablet product.

Source:
- https://tepe.ma/?product=revelateur-de-plaque-tepe-plaqsearch

### Classification
- canonical: `PARA-PLAQUE-DISC-001`
- localization: `VERIFIED_MARKET_MA_OFFICIAL_LOCAL_SITE`
- activation: `NO`

This verifies a Morocco-market example for the tablet form. It does not automatically verify every dye/formulation or the separate solution form.

## 2. Chlorhexidine oral gel

### Morocco evidence
The official TePe Maroc surface lists `Gel Gingival TePe` among local products and identifies chlorhexidine plus fluoride. The global TePe catalogue independently describes the same product family with product-specific composition, but that global catalogue is specification support only, not Morocco regulatory evidence.

Sources:
- https://tepe.ma/?product=revelateur-de-plaque-tepe-plaqsearch (official local page; related-product block lists the gingival gel)
- https://prod.tepe.com/globalassets/pr7850ch_fr_product_catalogue_2024_6833.pdf (manufacturer catalogue; product specification only)

### Classification
- canonical: `PARA-GEL-CHX-001`
- localization: `VERIFIED_MARKET_MA_OFFICIAL_LOCAL_SITE_PRODUCT_SPECIFIC`
- activation: `NO`

Important: this is intentionally separate from `PARA-MR-CHX-001` mouthrinse. Gel form must not be collapsed into rinse form.

## 3. Denture cleanser

### Morocco evidence
Haleon HealthPartner exposes a Morocco (`fr-ma`) Polident professional surface with a dedicated denture-cleanser product family and product page for Polident antibacterial cleanser. A Morocco price-comparison surface also tracks a Polident/Corega antibacterial cleanser sold by a local retailer.

Sources:
- https://www.haleonhealthpartner.com/fr-ma/oral-health/brands/polident/products/cleansers/
- https://primini.ma/prix/171427/polident-corega-anti-bacterien-36-comprimes

### Classification
- canonical: `PARA-DENT-CLEAN-001`
- localization: `VERIFIED_MARKET_MA_OFFICIAL_HCP_PLUS_RETAIL_CROSSCHECK`
- activation: `NO`

No inference is made from this family evidence to every cleanser form/material compatibility.

## 4. Denture adhesive

### Morocco evidence
Haleon HealthPartner's Morocco Polident surface presents denture fixatives as a Morocco-facing product family. Separate Morocco retail surfaces list Polident/Corega adhesive and alternative denture adhesive products.

Sources:
- https://www.haleonhealthpartner.com/fr-ma/oral-health/brands/polident/overview/
- https://primini.ma/prix/147352/polident-corega-original-40gr
- https://paragroup5.com/category/Prothese-dentaire

### Classification
- canonical: `PARA-DENT-ADH-001`
- localization: `VERIFIED_MARKET_MA_OFFICIAL_HCP_PLUS_RETAIL_CROSSCHECK`
- activation: `NO`

Exact composition, zinc status, form and fit context remain product-specific.

## 5. Removable-appliance cleanser

### Morocco evidence
The Morocco Haleon/Polident HCP surface describes a cleaner family for other removable dental appliances in addition to dentures. However, this pass does not lock an exact Morocco SKU for aligner/retainer cleaner.

Source:
- https://www.haleonhealthpartner.com/fr-ma/oral-health/brands/polident/overview/

### Classification
- canonical: `PARA-APP-CLEAN-001`
- localization: `MARKET_FAMILY_EVIDENCE_MA_OFFICIAL_HCP_SITE`
- exact local SKU: `NOT_LOCKED`
- activation: `NO`

## Explicit non-promotions
No stronger Morocco-specific evidence was found in this pass for:
- water flosser / oral irrigator;
- high-fluoride 2800/5000 ppm toothpaste;
- professional fluoride varnish;
- professional fluoride gel/foam;
- SDF 38%.

Foreign or non-Morocco manufacturer pages for these categories are not promoted to Morocco verification.

## Verdict
This pass closes market-localization evidence for plaque-disclosing tablets, a product-specific CHX gel example, denture cleanser and denture adhesive; it adds only family-level Morocco evidence for removable-appliance cleanser. It does not authorize clinical use or prescription activation.
