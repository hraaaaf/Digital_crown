# Antibiotic Baseline

Status: architecture baseline; all clinical rules remain `candidate`.

## Source hierarchy

1. Moroccan authority/product information for authorization, exact formulation and contraindications.
2. Current dental guideline for indication, no-indication, regimen architecture and stewardship.
3. Product RCP/SmPC for formulation-specific safety.
4. Systematic or primary evidence only when an authoritative guideline does not answer the exact question.

Candidate sources include SDCEP Drug Prescribing for Dentistry, ADA 2019 urgent dental pain/swelling guidance, AAPD 2026 antibiotic therapy guidance, CDC stewardship resources, AHA 2021 infective-endocarditis prevention and ESC 2023 endocarditis guidance.

## Required separation

- Definitive dental treatment and source control are separate from antimicrobial prescribing.
- Localized conditions and systemic involvement require separate indication rules.
- Treatment and prophylaxis are different rule families.
- Adult, pediatric, pregnancy, renal and hepatic populations are separate profiles.
- Allergy status does not directly select an alternative.
- A product identity/formulation is resolved only after substance-level candidacy.

## Candidate rule records

| Candidate rule | Source | Population | Indication | Contraindication | Dose form/unit/frequency/duration/maximum | Confidence | Conflicts | Status |
|---|---|---|---|---|---|---|---|---|
| systemic-antibiotic-indication-dental-pain-swelling | `ada-antibiotics-2019`, `sdcep-drug-prescribing` | adult, guideline-defined | Narrow dental pain/swelling scenarios | Requires full source extraction | Not transcribed in this mission | medium | Jurisdiction and update differences | candidate |
| pediatric-antibiotic-indication | `aapd-antibiotics-2026` | pediatric | Guideline-defined oral/dental infections | Requires age/weight/formulation review | Not transcribed in this mission | medium | Morocco applicability unknown | candidate |
| dental-antibiotic-stewardship-no-indication | `ada-antibiotics-2019`, `cdc-dental-antibiotic-stewardship` | source-defined | Conditions where definitive dental treatment is preferred | Not applicable | No dose action permitted | medium | Local care pathways need review | candidate |
| infective-endocarditis-prophylaxis-eligibility | `aha-ie-2021`, `esc-ie-2023` | selected cardiac-risk groups | Source-defined invasive dental procedures | Requires cardiac history and allergy pathway | Treatment regimens excluded | medium | AHA/ESC and Morocco adoption require reconciliation | candidate |
| infective-endocarditis-clindamycin-exclusion | `aha-ie-2021`, `ada-antibiotic-prophylaxis` | source-defined | Prophylaxis alternative selection | Clindamycin not recommended by current AHA statement | No dose action permitted | high for detecting current-code conflict | Existing code includes clindamycin | candidate |

## Mandatory rule fields before activation

- Exact guideline edition and recommendation location.
- Jurisdiction and Moroccan clinical-review decision.
- Condition/diagnosis criteria and certainty.
- Systemic signs and source-control status.
- Population, age, measured weight and organ-function prerequisites.
- Substance and formulation constraints.
- Per-dose versus per-day semantics, route, frequency, duration and maxima.
- Allergy and interaction pathway references.
- Stop/reassessment/escalation conditions.
- Stewardship rationale and no-antibiotic outcome.

## Explicit no-action behavior

If indication, allergy status, required weight, formulation, route, renal/hepatic context, interaction data or source approval is missing, the system must not generate a dose or substitute a medicine. It returns a structured blocker.

## Sources

- SDCEP: <https://www.sdcep.org.uk/published-guidance/drug-prescribing/>
- ADA antibiotic guideline: <https://www.ada.org/resources/research/science/evidence-based-dental-research/antibiotics-for-dental-pain-and-swelling/>
- AAPD antibiotic therapy: <https://www.aapd.org/research/oral-health-policies--recommendations/use-of-antibiotic-therapy-for-pediatric-dental-patients/>
- CDC stewardship: <https://www.cdc.gov/antibiotic-use/hcp/educational-resources/stewardship/index.html>
- ADA/AHA prophylaxis summary: <https://www.ada.org/resources/ada-library/oral-health-topics/antibiotic-prophylaxis>
- AHA 2021 statement summary: <https://professional.heart.org/en/science-news/prevention-of-viridans-group-streptococcal-infective-endocarditis/top-things-to-know>
- ESC 2023 essential messages: <https://www.escardio.org/static-file/Escardio/Guidelines/Products/Slide%20sets/2023%20Gls/Essential%20Messages_2023%20Endocarditis.pdf>

