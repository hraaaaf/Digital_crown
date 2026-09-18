# Prescription Pharmacology — Core-5 Morocco regulatory pass — 2026-09-17

Status: REGULATORY EVIDENCE PASS / FAIL-CLOSED
Clinical activation: NO

## Goal
Separate official Moroccan regulatory/catalogue evidence from commercial presence and from clinical activation for the five Core-5 medicines.

## Verified official AMMPS evidence

### Paracetamol — MED-PAIN-001
AMMPS Liste Marocaine des médicaments shows single-active paracetamol products with `Statut AMM: AMM ENREGISTREE`, including CLARADOL 500 mg effervescent tablet and APYROL oral solution. Commercialisation is product/presentation-specific.

Regulatory evidence: VERIFIED_MA_AMM_REGISTERED_FOR_AT_LEAST_ONE_RELEVANT_SINGLE_ACTIVE_PRODUCT.
Exact automation product/form/strength: PENDING.
Clinical activation: NO.

### Ibuprofen — MED-PAIN-002
AMMPS official databases list oral ibuprofen products/forms, including ALGANTIL 200 mg oral presentations and ADFENE oral strengths. Exact product/form/strength remains product-specific before an automated prescription template is activated.

Regulatory/catalogue evidence: VERIFIED_MA_OFFICIAL_DATABASE_PRESENCE.
Exact automation product/form/strength: PENDING.
Clinical activation: NO.

### Amoxicillin — MED-ABX-001
AMMPS Liste Marocaine shows CLAMOXYL 500 mg oral suspension with `AMM ENREGISTREE` and Commercialisé, while another presentation is `AMM RETIREE`. AMOXICILLINE SP also has marketed oral presentations. Status therefore remains attached to the exact product/presentation, not merely the molecule.

Regulatory evidence: VERIFIED_MA_AMM_REGISTERED_FOR_RELEVANT_ORAL_PRODUCTS.
Exact automation product/presentation: PENDING.
Clinical activation: NO.

### Metronidazole — MED-ABX-004
AMMPS Répertoire Marocain des Médicaments Génériques (édition projet janvier 2026) lists oral metronidazole groups including 500 mg tablets: METROZAL 500 mg, NIDAZOL 500 mg, ZYRDOL 500 mg, and FLAGYL/METROGYL 500 mg film-coated tablets. This is official Moroccan catalogue evidence, but this pass does not upgrade it to an exact AMM-status claim for a selected automated product/presentation.

Regulatory/catalogue evidence: VERIFIED_MA_OFFICIAL_RMMG_ORAL_500MG_PRESENCE.
Exact selected product AMM status/form/presentation for automation: PENDING.
Clinical activation: NO.

### Phenoxymethylpenicillin / Penicillin V — MED-ABX-003
AMMPS Base de données des médicaments lists ANGIPEN, active substance PHENOXYMETHYLPENICILLINE: 1 MUI tablet (Commercialisé AO / Export) and 250 000 UI/5 mL oral suspension (`AMM sans prix`). This proves official Moroccan database presence while also demonstrating that commercial/administrative status must remain presentation-specific.

Regulatory/catalogue evidence: VERIFIED_MA_OFFICIAL_DATABASE_PRESENCE.
Exact selected product AMM status/form/presentation for automation: PENDING.
Clinical activation: NO.

## Interpretation rule
`AMM ENREGISTREE` is regulatory evidence for the exact listed Moroccan medicinal product/presentation. `Commercialisé`, `Commercialisé AO`, `Commercialisé AO / Export`, `AMM sans prix`, `Non Commercialisé`, `AMM RETIREE` and similar fields are distinct commercial/administrative states and MUST NOT be collapsed into clinical validation.

An AMMPS listing or RMMG entry does not by itself certify the dental indication, dose, duration, pediatric rule, contraindication screen, interaction screen, or automatic prescription logic.

## Current Core-5 closure
- Official Morocco evidence of relevant molecule/product presence: 5/5.
- Exact automation product/form/strength/presentation regulatory closure: 0/5 in this pass.
- Automatic clinical activation: 0/5.

## Sources
Primary source: Agence Marocaine du Médicament et des Produits de Santé (AMMPS), Liste Marocaine des médicaments / Base de données des médicaments / Répertoire Marocain des Médicaments Génériques, consulted 2026-09-17.

Clinical/scientific evidence remains governed by the existing Core clinical passes and requires independent scientific/clinical review before activation.
