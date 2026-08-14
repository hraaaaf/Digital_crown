# Dental Pharmacology — Morocco-first evidence baseline

## Status
R1 engineering foundation for Digital Crown Morocco. This file records the evidence policy used by the pharmacology arbiter.

## Non-negotiable rules
- **Morocco-first**: Moroccan official/regulatory sources outrank foreign dental guidance for market status and local recommendations.
- Molecule-first; brands are display/search identities, resolved to a DCI/substance before arbitration.
- No brand→molecule guess when the medicine dictionary cannot resolve identity.
- No dose, duration, contraindication or paediatric conversion without an identified source.
- No paediatric weight inferred from age.
- No clinical fact inferred from free-text antecedents for pharmacology arbitration.
- No automatic therapeutic substitution.
- No local “force allergy” bypass.
- Missing/conflicting evidence returns review/fail-closed; it never fabricates a regimen.
- Dental indication and drug regimen are separate gates.
- No UI claim such as “commercialisé au Maroc” without current AMMPS presentation-level verification.
- Foreign dental regimens are **supporting evidence only** when current Moroccan dental-regimen evidence is absent.
- Practitioner overrides are preserved, but remain review-required if they differ from the sourced regimen and are never silently combined into a hybrid regimen.

## Evidence hierarchy for Morocco
1. **Moroccan official sources**: AMMPS / Ministry for AMM, commercialisation status, RCP, withdrawals, pharmacovigilance and official good-use/stewardship guidance.
2. **Moroccan professional / academic references**: only when identifiable/current and non-conflicting; these do not replace the regulator.
3. **Current international regulatory/RCP evidence** where Moroccan equivalent is inaccessible.
4. **Current international dental guidance**: SDCEP/BNF, HAS and comparable sources to fill an explicitly recorded `MOROCCO_GUIDELINE_GAP` only.
5. **WHO AWaRe**: antimicrobial-stewardship support, not a dental prescribing guideline.

A lower tier must never silently override a higher/local rule.

## Morocco sources reviewed — 2026-08-15
- AMMPS medicines database: https://www.ammps.gov.ma/recherche-medicaments
  - exposes name, active substance, dosage, form/presentation, RCP and commercialisation state;
  - 9,860 medicine records were exposed at review time;
  - presence in the database is **not** equivalent to current commercialisation.
- AMMPS generic directory, project January 2026: https://www.ammps.gov.ma/repertoire-medicaments-generiques
- Ministry antimicrobial good-use/stewardship support: https://www.sante.gov.ma/Pages/Communiques.aspx?IDCom=307
- Moroccan official paracetamol good-use support: https://sehati.gov.ma/article/recommandations_pour_le_bon_usage_du_paracetamol
- Moroccan professional support: Belyamani L, Jidane S. *Antibiotiques — Antibio-choix du praticien marocain* (2020), catalogue: https://biblio.um6ss.ma/antibiotiques-antibio-choix-du-praticien-marocain/

## Important Morocco evidence gap
As of the 2026-08-15 R1 review, no current comprehensive official Moroccan **dentistry-specific prescribing guideline** equivalent to SDCEP was identified in accessible official sources.

Digital Crown records:

`MOROCCO_GUIDELINE_GAP`

It must **not** turn an SDCEP/BNF/HAS regimen into a “Moroccan recommendation” merely because no Moroccan equivalent was found.

## International dental support reviewed
- SDCEP Drug Prescribing for Dentistry: https://www.sdcepdentalprescribing.nhs.scot/guidance/
- Bacterial infections: https://www.sdcepdentalprescribing.nhs.scot/guidance/bacterial-infections/
- Dental abscess: https://www.sdcepdentalprescribing.nhs.scot/guidance/bacterial-infections/dental-abscess/
- 2026 bacterial-infection guidance separates local source control/indication from antibiotic regimen and recommends review ideally at ~3 days.
- Co-amoxiclav remains review-only for dental abscess under current SDCEP evidence.
- Core encoded support: phenoxymethylpenicillin, amoxicillin, metronidazole, clindamycin, clarithromycin, paracetamol, ibuprofen, miconazole, fluconazole, chlorhexidine, benzydamine.
- Source-backed supplement encoded: nystatin, severe-HSV aciclovir pathway, hydrocortisone oromucosal, sodium fluoride 2800 ppm, 5000 ppm and 0.05% mouthwash.

### Product identity correction
France public medicines database / ANSM may be used as secondary identity/RCP evidence where helpful.

Verified correction: **HEXTRIL 0.1% contains hexetidine, not chlorhexidine**. The old Digital Crown alias `HEXTRIL → CHLORHEXIDINE` has been removed from the R1/legacy decision path.

### Antimicrobial stewardship
WHO AWaRe: https://www.who.int/publications/i/item/9789240062382

WHO support supplements rather than replaces national/local guidance.

## R1 runtime architecture
All main Ordonnance medication entry paths route through one canonical pipeline:

1. Quick Entry;
2. line autocomplete;
3. system protocols;
4. user protocols;
5. medication library;
6. assessment/suggestion path.

Pipeline:

`displayed name → local dictionary identity lookup → resolved DCI/presentation → structured patient context → core/supplement evidence arbiter → Morocco policy gate → normalized line + visible review state`

### Runtime invariants
- local dictionary identity resolution is **not** proof of current AMMPS commercialisation;
- free-text antecedents are not converted into structured allergy/pregnancy/renal/hepatic facts;
- `DrugRow` no longer runs its own free-text penicillin-allergy block or “force” bypass;
- unsupported automatic legacy dose/posology is cleared;
- explicit practitioner values are preserved for review;
- partial override cannot silently create a hybrid regimen;
- no synthetic paediatric weight;
- no automatic allergy substitution;
- fluoride presentation details are preserved so 2800 ppm / 5000 ppm / 0.05% cannot collapse into one generic rule;
- foreign-supported regimens remain practitioner-confirmation-required unless the explicit Morocco gate passes.

## Coverage governance
See `docs/pharmacology/DENTAL_PHARMACOLOGY_COVERAGE.md` for the canonical matrix:
- `CODED_CORE`
- `SOURCE_BACKED_MISSING`
- `SEPARATE_EMERGENCY_MODULE`
- `REVIEW_ONLY / EXCLUDED_DEFAULT`
- `MOROCCO_GATE_REQUIRED`

## Remaining R1 engineering gates
- CI/frontend typecheck/tests/build must pass on the **final R1 head**.
- Targeted R1 pharmacology tests must pass on that same head.
- Current AMMPS presentation verification is not yet automated from the local app; therefore Morocco status remains explicit/review-gated unless evidence is supplied.
- Canonical roadmap closeout must record executed evidence only.

## Human clinical governance
The software arbiter is not a human dental pharmacologist. Before clinical certification/release in Morocco, the rule matrix requires formal sign-off by a qualified Moroccan dental/pharmacology reviewer plus current AMMPS verification for relevant presentations. Until then, uncertain, conflicting, unverified-Morocco or foreign-only rules remain practitioner-review/fail-closed states.
