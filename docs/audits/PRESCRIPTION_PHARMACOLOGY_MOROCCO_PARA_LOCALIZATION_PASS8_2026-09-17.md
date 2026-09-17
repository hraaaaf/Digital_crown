# Morocco para localization — Pass 8 — 2026-09-17

Status: MARKET LOCALIZATION ONLY — CLINICAL ACTIVATION NO

## Goal
Close additional low-risk Morocco market-presence gaps without converting manufacturer catalogue presence into regulatory or patient-specific clinical validation.

## Evidence rule
- Official Morocco manufacturer catalogue = `VERIFIED_MARKET_MA_OFFICIAL_BRAND_SITE` for the exact family/product surface only.
- Product marketing claims are not imported as independent clinical conclusions.
- `clinical_activation=NO` remains mandatory.
- No AMMPS contact.

## Findings

### Dental floss
GUM Morocco maintains a dedicated local dental-floss catalogue with multiple floss/tape/access-floss products and a Morocco point-of-sale surface.

Classification: `VERIFIED_MARKET_MA_OFFICIAL_BRAND_SITE`.

Canonical target: `PARA-INT-FLOSS-001`.

### Tongue scraper
GUM Morocco local catalogue exposes tongue-cleaning / halitosis accessories including the HaliControl surface previously identified in the localization sequence.

Classification: `VERIFIED_MARKET_MA_OFFICIAL_BRAND_SITE`.

Canonical target: `PARA-TONGUE-001`.

### Orthodontic hygiene ecosystem
GUM Morocco has a dedicated ORTHO catalogue including orthodontic toothbrushes, sonic ortho brush, wax, toothpaste, mouthrinse and interdental brushes.

This confirms Morocco market presence of an orthodontic hygiene ecosystem but does **not** justify collapsing appliance cleanser/storage into generic ORTHO products. `PARA-APP-CLEAN-001` and `PARA-APP-BOX-001` therefore remain unpromoted pending exact product evidence.

### Denture brush
GUM Morocco exposes an exact denture brush (`BAD Prothèse spécial dentier`, ref 201).

The current canonical matrix does not have a dedicated denture-brush row; this evidence is retained for the global gap/canonicalization audit rather than being forced into `PARA-DENT-CLEAN-001`, which represents chemical/mechanical cleanser products, not brushes.

## Fail-closed decisions
- No promotion of appliance cleanser/storage from generic orthodontic catalogue evidence.
- No promotion of denture cleanser/adhesive/reline from denture-brush evidence.
- No clinical activation.

## Sources
Public GUM Morocco official local catalogue surfaces reviewed 2026-09-17: dental floss, orthodontics, toothbrushes/denture brush, and Morocco point-of-sale pages.
