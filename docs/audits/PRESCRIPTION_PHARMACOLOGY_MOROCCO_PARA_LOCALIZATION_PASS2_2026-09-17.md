# Morocco Para Localization — Pass 2 — 2026-09-17

Status: MARKET / MEDICINE-EVIDENCE SEPARATION — CLINICAL ACTIVATION CLOSED

## Goal
Localize chlorhexidine and CPC oral-care families in Morocco while preserving the boundary between medicinal mouthwash evidence and para market evidence.

## Chlorhexidine — medicinal Morocco evidence
Public Moroccan medicine databases independently identify ELUDRIL as a commercialized mouthwash containing chlorhexidine + chlorobutanol, 90 mL, with PPV 16.60 MAD. Medicament.ma explicitly warns that database listing does not guarantee instantaneous pharmacy stock.

Classification: `VERIFIED_MEDICINE_MA_SECONDARY_CROSSCHECK`
Canonical family relevance: `PARA-MR-CHX-001`, but medicinal ELUDRIL must not be silently modeled as an ordinary para SKU.
Clinical activation: `NO`

## Chlorhexidine + CPC / CPC — official Morocco para evidence
GUM Morocco official pages provide current local product evidence for:
- PAROEX mouthwash, with CPC explicitly listed on the local page;
- ORTHO mouthwash, with CPC explicitly listed;
- SensiVital+ mouthwash, with CPC explicitly listed;
- GINGIDEX/PAROEX toothpaste with chlorhexidine 0.06% + CPC and fluoride 1450 ppm.

A GUM Morocco product leaflet additionally exposes CPC concentrations for some product families. Concentration must remain SKU-specific and must not be generalized across the range.

Classification:
- CPC family: `VERIFIED_MARKET_MA_OFFICIAL_BRAND_SITE`
- CHX-containing para family: `VERIFIED_MARKET_MA_OFFICIAL_BRAND_SITE_PRODUCT_SPECIFIC`
Clinical activation: `NO`

## Important modeling correction
The canonical mouthrinse taxonomy is active-based, but Morocco evidence demonstrates that products can combine actives (e.g. CHX + CPC). Product records therefore need a many-to-many `active_or_material` mapping rather than forcing one product into one active family.

## Regulatory boundary
- ELUDRIL: medicinal evidence; do not infer para status.
- GUM local products: market/product evidence; do not infer AMMPS medicinal authorization.
- No clinical recommendation, duration, concentration substitution, or patient-specific instruction is activated from market evidence.
- No AMMPS contact performed.

## Remaining priority localization
1. high-fluoride toothpaste / high-strength home gel exact Morocco SKUs
2. professional fluoride varnish/gel
3. SDF
4. CPP-ACP / CPP-ACPF
5. hydroxyapatite / nano-HAp
6. xerostomia products
7. water flosser

## Verdict
Morocco presence is now directly supported for CPC oral-care products and product-specific CHX/CPC combinations. CHX also has separately cross-checked Moroccan medicinal mouthwash evidence. The two evidence classes remain intentionally separate.

Next exact: update only CPC and CHX family-level Morocco statuses in the canonical matrix, then continue fluoride/SDF/remineralization localization.