# Dental Pharmacology — evidence baseline

## Status
R1 foundation. This file records the evidence policy used by `DentalPharmacologyArbiter.ts`.

## Non-negotiable rules
- Molecule-first; brands are display/search aliases only.
- No dose, duration, contraindication or paediatric conversion without an identified source.
- No paediatric weight is inferred from age.
- No automatic therapeutic substitution.
- Missing or conflicting evidence returns `requires_review`; it never fabricates a regimen.
- Dental indication and drug regimen are separate gates.
- Morocco availability/AMM must be verified against the Moroccan Ministry/DMP AMM source before UI claims such as “available in Morocco”.

## Evidence hierarchy
1. Moroccan national regulator / Ministry-DMP for local AMM, withdrawals and local regulatory status.
2. Current dental prescribing guidance: SDCEP Drug Prescribing for Dentistry, currently aligned with BNF 91 (March 2026) and BNFC 2025-2026.
3. WHO AWaRe for antibiotic stewardship/global classification where relevant.
4. Product RCP/SmPC from a national medicines regulator for product composition, licensed indications, warnings and formulation details.

A lower level must not silently override a higher/local rule.

## Current primary sources reviewed — 2026-08-14

### Dental prescribing
- SDCEP guidance: https://www.sdcepdentalprescribing.nhs.scot/guidance/
- Bacterial infections: https://www.sdcepdentalprescribing.nhs.scot/guidance/bacterial-infections/
- Dental abscess: https://www.sdcepdentalprescribing.nhs.scot/guidance/bacterial-infections/dental-abscess/
- Phenoxymethylpenicillin: https://www.sdcepdentalprescribing.nhs.scot/guidance/bacterial-infections/dental-abscess/first-line-antibiotics/phenoxymethylpenicillin/
- Amoxicillin: https://www.sdcepdentalprescribing.nhs.scot/guidance/bacterial-infections/dental-abscess/first-line-antibiotics/amoxicillin/
- Metronidazole: https://www.sdcepdentalprescribing.nhs.scot/guidance/bacterial-infections/dental-abscess/first-line-antibiotics/metronidazole/
- Clindamycin: https://www.sdcepdentalprescribing.nhs.scot/guidance/bacterial-infections/dental-abscess/second-line-antibiotics/clindamycin/
- Clarithromycin: https://www.sdcepdentalprescribing.nhs.scot/guidance/bacterial-infections/dental-abscess/second-line-antibiotics/clarithromycin/
- Paracetamol: https://www.sdcepdentalprescribing.nhs.scot/guidance/odontogenic-pain/analgesics/paracetamol/
- Ibuprofen: https://www.sdcepdentalprescribing.nhs.scot/guidance/odontogenic-pain/analgesics/ibuprofen/
- Miconazole: https://www.sdcepdentalprescribing.nhs.scot/guidance/fungal-infections/candidosis/miconazole/
- Fluconazole: https://www.sdcepdentalprescribing.nhs.scot/guidance/fungal-infections/candidosis/fluconazole/
- Chlorhexidine mouthwash: https://www.sdcepdentalprescribing.nhs.scot/guidance/ulceration-inflammation/antimicrobial-mouthwashes/chlorhexidine-mouthwash/
- Benzydamine mouthwash: https://www.sdcepdentalprescribing.nhs.scot/guidance/ulceration-inflammation/local-analgesics/benzydamine-mouthwash/
- Contraindications/cautions antibiotics: https://www.sdcepdentalprescribing.nhs.scot/guidance/supporting-tools/contraindications-cautions/contraindications-cautions-antibiotics/

### Antimicrobial stewardship
- WHO AWaRe antibiotic book: https://www.who.int/publications/i/item/9789240062382

### Morocco regulatory baseline
- Ministry/DMP mission: https://www.sante.gov.ma/Pages/ADM_Centrale/DMP.aspx
- Moroccan authorised medicines (AMM) search: https://www.sante.gov.ma/medicaments/amm/default.aspx
- Pharmacovigilance/withdrawals: https://www.sante.gov.ma/Medicaments/Pharmacovigilance/Pages/default.aspx

## 2026 changes that invalidate old Digital Crown defaults
- SDCEP bacterial guidance was updated in May 2026.
- Review of antibiotic treatment should ideally occur at 3 days (clarified June 2026).
- Co-amoxiclav was removed from the SDCEP second-line dental-abscess recommendation in May 2026.
- Second-line clindamycin/clarithromycin should be restricted to severe infection after first-line failure/review or specialist discussion.
- Antibiotics are not a default treatment for inflammatory dental pain and are not routine prophylaxis after routine dental surgery.

## R1 integration status
- Evidence registry: created.
- Deterministic DentalPharmacologyArbiter: created.
- Unified `normalizeMedicationForPatient()` invariant: created.
- Cross-path unit tests: created.
- Existing Ordonnance entry points are NOT yet wired to this canonical pipeline.
- Existing hard-coded `clinical_rules.ts` and presets remain legacy until R1 wiring/removal is completed.

## Human clinical governance
This software-side arbiter is not a human dental pharmacologist. Before declaring the pharmacology module clinically certified, the source matrix and rule set require formal review/sign-off by a qualified clinician/pharmacology reviewer under the project governance process.
