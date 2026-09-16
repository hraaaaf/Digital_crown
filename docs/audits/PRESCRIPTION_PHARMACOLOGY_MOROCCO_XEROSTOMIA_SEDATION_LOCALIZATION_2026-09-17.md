# Digital Crown — Maroc — Xérostomie systémique & sédation — localisation

Date: 2026-09-17
Status: RESEARCH ONLY — FAIL-CLOSED — NOT FOR CLINICAL ACTIVATION

## Goal
Localiser les familles xérostomie systémique et sédation déjà décrites cliniquement, sans transformer une preuve de marché en recommandation thérapeutique.

## Xérostomie systémique

### Pilocarpine
- Preuve clinique internationale déjà documentée dans `PRESCRIPTION_PHARMACOLOGY_MOROCCO_REMAINING_MEDICINES_PASS_2026-09-16.md` (ADA + SmPC/DailyMed).
- Recherche publique Maroc du 2026-09-17 : aucune spécialité/commercialisation marocaine suffisamment prouvée dans les sources publiques consultées.
- Maroc status: `TO_VERIFY_MA`.
- Clinical role: `SPECIALIST_OR_EXCEPTION`.
- Clinical activation: `NO`.

### Cevimeline
- Citée par l'ADA comme sialogogue oral dans la xérostomie, mais aucune autorisation/disponibilité Maroc suffisamment prouvée dans la recherche publique du 2026-09-17.
- Maroc status: `TO_VERIFY_MA`.
- Clinical role: `SPECIALIST_OR_EXCEPTION`.
- Clinical activation: `NO`.

## Sédation / anxiolyse

### Midazolam
- AMMPS RMMG 2026 confirme `MIDAZOLAM MYLAN 5 MG/ML` solution injectable IM/IV/rectale, flacons 1 mL et 10 mL, dans le répertoire marocain des génériques.
- Medicament.ma recense aussi des présentations midazolam 1 mg/mL et 5 mg/mL comme commercialisées au Maroc.
- Cette preuve confirme une présence de formes injectables; elle ne valide pas une forme buccale/oromucosale ni un protocole dentaire.
- Maroc status: `VERIFIED_FORM_MA_INJECTABLE_ONLY`.
- Clinical role: `PROTOCOL_ONLY` / `SPECIALIST_OR_EXCEPTION`.
- Clinical activation: `NO`.

### Diazepam
- Base publique AMMPS : VALIUM 5 mg comprimé, 10 mg comprimé et solution buvable 1% sont listés avec statut commercialisé/commercialisé AO selon présentation.
- Medicament.ma confirme la solution buvable VALIUM 1% comme commercialisée.
- Aucune indication dentaire n'est inférée de cette disponibilité.
- Maroc status: `VERIFIED_FORMS_MA_ORAL`.
- Clinical role: `SPECIALIST_OR_EXCEPTION`.
- Clinical activation: `NO`.

### Hydroxyzine
- Medicament.ma liste TARAXET 25 mg comprimé et TARAXET 2 mg/mL sirop comme commercialisés au Maroc.
- L'ancienne observation d'une forme injectable retirée ne doit donc pas être extrapolée à toutes les formes d'hydroxyzine.
- Maroc status: `MARKET_EVIDENCE_MA_ORAL` (secondary-source evidence; primary AMMPS form-level proof still desirable before any activation).
- Clinical role: `SPECIALIST_OR_EXCEPTION`.
- Clinical activation: `NO`.

### Protoxyde d'azote / oxygène
- Reste un acte/protocole de sédation avec exigences de sélection, équipement, monitoring, compétences et secours, pas une prescription simple.
- Recherche publique Maroc de cette passe : cadre réglementaire dentaire spécifique non suffisamment verrouillé.
- Maroc status: `TO_VERIFY_MA_REGULATORY_FRAMEWORK`.
- Clinical role: `PROTOCOL_ONLY`.
- Clinical activation: `NO`.

## Sources Morocco/public
- AMMPS RMMG: https://ammps.gov.ma/repertoire-medicaments-generiques
- AMMPS RMMG midazolam page 11: https://ammps.gov.ma/repertoire-medicaments-generiques?page=11
- AMMPS medication database VALIUM page: https://www.ammps.gov.ma/recherche-medicaments?page=758
- Medicament.ma MIDAZOLAM 1 mg/mL: https://medicament.ma/medicament/midazolam-mylan-1mgml-soluttion-injectable-imiv-rectale/
- Medicament.ma MIDAZOLAM 5 mg/mL: https://medicament.ma/medicament/midizolam-mylan-solution-injectable-5mg5ml/
- Medicament.ma VALIUM gouttes 1%: https://medicament.ma/medicament/valium-gouttes-1-solution-buvable/
- Medicament.ma TARAXET 25 mg: https://medicament.ma/medicament/taraxet-25-mg-comprime-pellicule/
- Medicament.ma TARAXET 2 mg/mL: https://medicament.ma/medicament/taraxet-2-mg-ml-sirop-p/

## Guardrails
- `Commercialisé` / RMMG presence ≠ indication dentaire.
- Aucun dosage de sédation n'est activé dans Digital Crown.
- Aucune forme non prouvée n'est dérivée par analogie d'une autre forme.
- `TO_VERIFY_MA` reste fail-closed.
- Aucun contact AMMPS n'a été effectué.

## Next exact
Localiser séparément le kit d'urgence cabinet (adrénaline, aspirine, glucagon, trinitrine, salbutamol, midazolam oromucosal, glucose, oxygène, antihistaminiques) puis intégrer seulement les formes Maroc prouvées dans la couche structurée fail-closed.
