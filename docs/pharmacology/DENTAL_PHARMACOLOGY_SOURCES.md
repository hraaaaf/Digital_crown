# Dental Pharmacology — Morocco-first evidence baseline

## Status
R1 engineering foundation for Digital Crown Morocco. This file records the evidence policy used by the pharmacology arbiter.

## Non-negotiable rules
- **Morocco-first**: Moroccan official/regulatory sources outrank foreign dental guidance for market status and local recommendations.
- Molecule-first; brands are display/search identities, resolved to a DCI/substance before arbitration.
- No brand→molecule guess when the medicine dictionary cannot resolve the identity.
- No dose, duration, contraindication or paediatric conversion without an identified source.
- No paediatric weight is inferred from age.
- No automatic therapeutic substitution.
- Missing or conflicting evidence returns a review/fail-closed state; it never fabricates a regimen.
- Dental indication and drug regimen are separate gates.
- No UI claim such as “commercialisé au Maroc” without current AMMPS presentation-level verification.
- A foreign dental regimen is **supporting evidence only** when no current Moroccan dental regimen is identified. It must not be silently presented as a Moroccan recommendation.
- An explicit practitioner override is preserved, but if it differs from the sourced regimen it remains visibly review-required and is never silently paired with the other half of a different regimen.

## Evidence hierarchy for the Moroccan market
1. **Moroccan official sources**: AMMPS / Ministry for AMM, commercialisation status, RCP, withdrawals, pharmacovigilance, essential medicines, official good-use or antimicrobial-stewardship guidance.
2. **Moroccan professional / academic references**: only when identifiable, current enough, and not conflicting with official Moroccan sources. These do not replace the regulator.
3. **Current international product/regulatory evidence**: RCP/SmPC from recognised regulators for pharmacology details when Morocco does not publish an accessible equivalent.
4. **Current international dental guidance**: SDCEP/BNF, HAS and comparable sources to fill an explicitly recorded `MOROCCO_GUIDELINE_GAP` only.
5. **WHO AWaRe**: antimicrobial-stewardship classification and global support, not a substitute for Moroccan dental guidance.

A lower tier must never silently override a higher/local rule.

## Morocco sources reviewed — 2026-08-15

### Official regulator
- AMMPS — Base de données des médicaments: https://www.ammps.gov.ma/recherche-medicaments
  - current search exposes name, active substance, dosage, form/presentation, EPI, RCP and commercialisation state;
  - 9,860 medicine records were exposed by the official database at review time;
  - a medicine can be `Commercialisé`, `Non Commercialisé`, `Retiré du Marché`, `AMM Sans Prix`, etc.; therefore **presence in the database is not equivalent to current commercialisation**.
- AMMPS — Répertoire Marocain des Médicaments Génériques, projet janvier 2026: https://www.ammps.gov.ma/repertoire-medicaments-generiques
- Ministry antimicrobial good-use / stewardship support: https://www.sante.gov.ma/Pages/Communiques.aspx?IDCom=307
- Official Moroccan paracetamol good-use support: https://sehati.gov.ma/article/recommandations_pour_le_bon_usage_du_paracetamol

### Moroccan professional / academic support
- Belyamani L, Jidane S. *Antibiotiques — Antibio-choix du praticien marocain* (2020), catalogue: https://biblio.um6ss.ma/antibiotiques-antibio-choix-du-praticien-marocain/
- Moroccan prescribing-pattern studies may identify practice gaps, **not** establish dosing authority.

## Important evidence gap
As of the 2026-08-15 R1 evidence review, no current, comprehensive, official Moroccan **dentistry-specific prescribing guideline** equivalent to SDCEP was identified in the accessible official sources.

Digital Crown therefore records:

`MOROCCO_GUIDELINE_GAP`

It must **not** turn an SDCEP/BNF/HAS regimen into a “Moroccan recommendation” merely because no Moroccan equivalent was found.

## International support reviewed — secondary only

### Dental prescribing
- SDCEP Drug Prescribing for Dentistry: https://www.sdcepdentalprescribing.nhs.scot/guidance/
- Bacterial infections: https://www.sdcepdentalprescribing.nhs.scot/guidance/bacterial-infections/
- Dental abscess: https://www.sdcepdentalprescribing.nhs.scot/guidance/bacterial-infections/dental-abscess/
- Current SDCEP dental pages are used for phenoxymethylpenicillin, amoxicillin, metronidazole, clindamycin, clarithromycin, paracetamol, ibuprofen, miconazole, fluconazole, chlorhexidine and benzydamine where explicitly encoded.
- 2026 bacterial-infection guidance separates local source control/indication from antibiotic regimen and recommends review ideally at 3 days.
- Co-amoxiclav is not auto-proposed by R1 for dental abscess; it remains review-only under the current SDCEP evidence state.

### Product identity cross-check
- France public medicines database / ANSM may be used as secondary identity/RCP evidence where helpful.
- Verified correction: **HEXTRIL 0.1% contains hexetidine**, not chlorhexidine. Any historical Digital Crown alias `HEXTRIL → CHLORHEXIDINE` is invalid and must not be used by the R1 arbiter.

### Antimicrobial stewardship
- WHO AWaRe antibiotic book: https://www.who.int/publications/i/item/9789240062382
- WHO support supplements rather than replaces national/local guidance.

## R1 runtime architecture
All main Ordonnance medication entry paths are now routed through the same normalization/arbitration foundation on the R1 branch:

1. Quick Entry;
2. line autocomplete;
3. system protocols;
4. user protocols;
5. medication library;
6. assessment/suggestion path.

### Pipeline
`displayed name → local dictionary identity lookup → resolved DCI when available → structured patient context → evidence arbiter → normalized line + review state`

Rules:
- local dictionary identity resolution is **not** proof of current AMMPS commercialisation;
- free-text antecedents are not converted into structured allergies/pregnancy/renal/hepatic facts by R1;
- unsupported automatic legacy dose/posology is cleared;
- explicit practitioner therapeutic values are preserved for review;
- partial practitioner override cannot silently create a hybrid regimen;
- no synthetic paediatric weight;
- no automatic allergy substitution.

## Remaining R1 gates
- CI/frontend typecheck/tests/build must pass on the final R1 head.
- Legacy `clinical_rules.ts` is no longer the Guide dosing engine, but a residual compatibility consumer remains in `DrugRow`; it must not be treated as the canonical arbiter and its known false historical aliases must be neutralised.
- Morocco market-policy state must be surfaced clearly enough that foreign-only support is never labelled as a Moroccan recommendation.
- Current AMMPS presentation verification is not yet automated from the local app.
- Formal qualified human dental/pharmacology review remains required before clinical certification.

## Human clinical governance
The software arbiter is not a human dental pharmacologist. Before declaring this module clinically certified for Morocco, the source matrix and rule set require formal sign-off by a qualified Moroccan dental/pharmacology reviewer. Until then, uncertain, conflicting, unverified-Morocco or foreign-only rules remain practitioner-review/fail-closed states.
