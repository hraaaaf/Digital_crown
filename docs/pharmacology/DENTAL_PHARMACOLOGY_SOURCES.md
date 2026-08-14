# Dental Pharmacology — Morocco-first evidence baseline

## Status
R1 foundation for Digital Crown Morocco. This file records the evidence policy used by the pharmacology arbiter.

## Non-negotiable rules
- **Morocco-first**: Moroccan official/regulatory sources outrank foreign dental guidance for market status and local recommendations.
- Molecule-first; brands are display/search aliases only.
- No dose, duration, contraindication or paediatric conversion without an identified source.
- No paediatric weight is inferred from age.
- No automatic therapeutic substitution.
- Missing or conflicting evidence returns `requires_review`; it never fabricates a regimen.
- Dental indication and drug regimen are separate gates.
- No UI claim such as “available in Morocco” without Moroccan AMM verification.
- A foreign dental regimen is **supporting evidence only** when no current Moroccan dental regimen is identified. It must not be silently presented as a Moroccan recommendation.

## Evidence hierarchy for the Moroccan market
1. **Moroccan official sources**: AMMPS / Ministry-DMP for AMM, withdrawals, pharmacovigilance, essential medicines, official good-use or antimicrobial-stewardship guidance.
2. **Moroccan professional / academic references**: only when identifiable, current enough, and not conflicting with official Moroccan sources. These do not replace the regulator.
3. **Current international product/regulatory evidence**: SmPC/RCP from recognised regulators for pharmacology details when Morocco does not publish an accessible equivalent.
4. **Current international dental guidance**: SDCEP/BNF, HAS and comparable sources to fill an explicitly recorded `MOROCCO_GUIDELINE_GAP` only.
5. **WHO AWaRe**: antimicrobial-stewardship classification and global support, not a substitute for Moroccan dental guidance.

A lower tier must never silently override a higher/local rule.

## Morocco sources reviewed — 2026-08-14

### Official regulator / Ministry
- DMP mission and medicines governance: https://www.sante.gov.ma/Pages/ADM_Centrale/DMP.aspx
- Moroccan authorised medicines (AMM) search: https://www.sante.gov.ma/medicaments/amm/default.aspx
- Medicines/products regulation: https://www.sante.gov.ma/Reglementation/Pages/REGLEMENTATION-APPLICABLE-AU-PRODUITS-DE-SANTE.aspx
- National medicines / essential-products lists: https://www.sante.gov.ma/Medicaments/PHCS/pages/default.aspx
- Ministry antimicrobial good-use campaign / stewardship: https://www.sante.gov.ma/Pages/Communiques.aspx?IDCom=307
- Official Moroccan paracetamol good-use recommendations: https://sehati.gov.ma/article/recommandations_pour_le_bon_usage_du_paracetamol

### Moroccan professional / academic support
- Belyamani L, Jidane S. *Antibiotiques — Antibio-choix du praticien marocain* (2020), Moroccan academic/practitioner reference; catalogue record: https://biblio.um6ss.ma/antibiotiques-antibio-choix-du-praticien-marocain/
- Published Moroccan dentistry prescribing-pattern literature may be used to identify practice gaps, **not** as a dosing authority.

## Important evidence gap found
As of the 2026-08-14 search performed for R1, no current, comprehensive, official Moroccan **dentistry-specific prescribing guideline** equivalent to SDCEP was identified on the accessible Ministry/AMMPS sources.

Therefore Digital Crown must represent this as an explicit evidence state:

`MOROCCO_GUIDELINE_GAP`

It must **not** convert an SDCEP/BNF/HAS regimen into a “Moroccan recommendation” merely because no Moroccan document was found.

## International support reviewed — secondary only

### Dental prescribing
- SDCEP guidance: https://www.sdcepdentalprescribing.nhs.scot/guidance/
- Bacterial infections: https://www.sdcepdentalprescribing.nhs.scot/guidance/bacterial-infections/
- Dental abscess: https://www.sdcepdentalprescribing.nhs.scot/guidance/bacterial-infections/dental-abscess/
- Phenoxymethylpenicillin, amoxicillin, metronidazole, clindamycin, clarithromycin dental pages under SDCEP
- Paracetamol, ibuprofen, miconazole, fluconazole, chlorhexidine, benzydamine dental pages under SDCEP
- HAS dentistry antibiotic work may be used as secondary francophone dental guidance when current and applicable.

### Antimicrobial stewardship
- WHO AWaRe antibiotic book: https://www.who.int/publications/i/item/9789240062382

## Consequence for R1 implementation
For a medication/regimen to be auto-proposed in Digital Crown Morocco, the R1 target is now:

1. molecule identity resolved;
2. Moroccan AMM/market status verified where applicable;
3. Moroccan official or accepted Moroccan regimen evidence present;
4. patient context sufficient;
5. no higher-priority conflict;
6. only then may the deterministic arbiter return an automatic regimen.

If step 3 is missing, international guidance may be shown as **support for practitioner review**, not auto-labelled as a Moroccan rule.

## R1 integration status
- Morocco-first evidence policy: created.
- Morocco market policy gate: created.
- Morocco policy unit tests: created, not yet executed in this session.
- Deterministic DentalPharmacologyArbiter: created but still needs Morocco gate integration.
- Unified `normalizeMedicationForPatient()` invariant: created but still needs Morocco gate integration.
- Cross-path unit tests: created.
- Existing Ordonnance entry points are NOT yet wired to this canonical pipeline.
- Existing hard-coded `clinical_rules.ts` and presets remain legacy until R1 wiring/removal is completed.

## Human clinical governance
The software arbiter is not a human dental pharmacologist. Before declaring this module clinically certified for Morocco, the source matrix and rule set require formal sign-off by a qualified Moroccan dental/pharmacology reviewer. Until then, uncertain or foreign-only rules remain review-only/fail-closed.
