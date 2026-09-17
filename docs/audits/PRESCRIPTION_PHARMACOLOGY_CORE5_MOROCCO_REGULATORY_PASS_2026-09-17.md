# Prescription Pharmacology — Core-5 Morocco regulatory pass — 2026-09-17

Status: REGULATORY PASS / FAIL-CLOSED
Clinical activation: NO

## Goal
Separate official Moroccan AMM evidence from commercial presence and from clinical activation for the five Core-5 medicines.

## Verified official AMMPS evidence

### Paracetamol — MED-PAIN-001
AMMPS Liste Marocaine des médicaments shows single-active paracetamol products with `Statut AMM: AMM ENREGISTREE`, including CLARADOL 500 mg effervescent tablet and APYROL oral solution. Commercialisation is product/presentation-specific.

Regulatory dimension: VERIFIED_MA_AMM_REGISTERED_FOR_AT_LEAST_ONE_RELEVANT_SINGLE_ACTIVE_PRODUCT.
Clinical activation: NO.

### Ibuprofen — MED-PAIN-002
AMMPS lists ibuprofen products/forms (e.g. ALGANTIL oral 200 mg presentations and ADFENE oral strengths). The official database demonstrates Moroccan product presence; exact target product/form/strength must remain product-specific before an automated prescription template is activated.

Regulatory dimension: VERIFIED_MA_OFFICIAL_DATABASE_PRESENCE; EXACT_AUTOMATION_PRODUCT_FORM_STRENGTH_PENDING.
Clinical activation: NO.

### Amoxicillin — MED-ABX-001
AMMPS Liste Marocaine shows CLAMOXYL 500 mg oral suspension with `AMM ENREGISTREE` and Commercialisé, while another presentation is `AMM RETIREE`. AMOXICILLINE SP also has marketed oral presentations. This proves why status must be attached to the exact product/presentation, not merely the molecule.

Regulatory dimension: VERIFIED_MA_AMM_REGISTERED_FOR_RELEVANT_ORAL_PRODUCTS; EXACT_AUTOMATION_PRODUCT_PRESENTATION_PENDING.
Clinical activation: NO.

### Metronidazole — MED-ABX-004
No sufficiently specific official AMMPS row was captured in this pass to close the exact Moroccan product/form/strength dimension.

Regulatory dimension: OPEN.
Clinical activation: NO.

### Phenoxymethylpenicillin / Penicillin V — MED-ABX-003
No sufficiently specific official AMMPS row was captured in this pass to close the exact Moroccan product/form/strength dimension.

Regulatory dimension: OPEN.
Clinical activation: NO.

## Interpretation rule
`AMM ENREGISTREE` is regulatory evidence for the exact listed Moroccan medicinal product/presentation. `Commercialisé`, `Commercialisé AO`, `AMM sans prix`, `Non Commercialisé`, `AMM RETIREE` and similar fields are distinct commercial/administrative states and MUST NOT be collapsed into clinical validation.

An AMMPS listing does not by itself certify the dental indication, dose, duration, pediatric rule, contraindication screen, interaction screen, or automatic prescription logic.

## Current Core-5 closure
- Regulatory evidence materially advanced: paracetamol, ibuprofen, amoxicillin.
- Exact regulatory closure still open in this pass: metronidazole, phenoxymethylpenicillin/penicillin V.
- Automatic clinical activation: 0/5.

## Sources
Primary source: Agence Marocaine du Médicament et des Produits de Santé (AMMPS), Liste Marocaine des médicaments / Base de données des médicaments, consulted 2026-09-17.

Clinical/scientific evidence remains governed by the existing Core clinical passes and requires independent scientific/clinical review before activation.
