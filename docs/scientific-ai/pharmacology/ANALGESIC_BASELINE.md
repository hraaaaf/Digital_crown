# Analgesic and NSAID Baseline

Status: architecture baseline; no dose is approved or active.

## Scope

The current repository includes paracetamol/acetaminophen, NSAIDs (ibuprofen, ketoprofen, flurbiprofen, tiaprofenic acid, diclofenac, naproxen), codeine combinations and corticosteroid presets. Each substance and fixed combination needs a separate reviewed rule.

## Candidate decisions

| Decision | Candidate source | Population | Required data | Status |
|---|---|---|---|---|
| Acute dental pain treatment hierarchy | ADA 2024 acute pain guideline | adolescents/adults and pediatric source-defined groups | age, indication, contraindications, current medicines | candidate |
| Pediatric pain rule architecture | AAPD pain/useful medications | pediatric | measured weight, age, formulation, caps | candidate |
| Ibuprofen formulation safety | Product RCP/SmPC plus dental guideline | product-specific | age, weight, renal/GI/asthma/pregnancy/current medicines | candidate |
| Paracetamol formulation and total exposure | Product RCP/SmPC plus dental guideline | product-specific | hepatic context, weight, all active ingredients | candidate |
| Combination/opioid restrictions | Jurisdiction-specific authoritative source | source-defined | age, formulation, current medicines and legal context | needs_review |

## Required safety representation

- Dose basis and whether values are per administration or per day.
- Maximum per administration and maximum total from all products.
- Minimum age/weight and formulation-specific restrictions.
- Renal and hepatic decision paths.
- GI ulcer/bleeding history, anticoagulants and relevant interactions.
- Pregnancy and breastfeeding source-specific constraints.
- Relevant asthma/NSAID reaction history.
- Duplicate active ingredient detection across brands and combinations.
- Duration and review/escalation boundaries.

## Prohibited assumptions

- A brand determines a unique strength.
- A tablet can safely be split without product evidence.
- `paracetamol 1 g` is appropriate because the patient is an adult.
- An age-derived weight is sufficient for pediatric dosing.
- Absence from the handwritten interaction matrix means no interaction.
- One guideline's maximum applies to every product, route, population or jurisdiction.

## Sources

- ADA acute dental pain guideline: <https://www.ada.org/resources/research/science/evidence-based-dental-research/pain-management-guideline>
- ADA living acute-pain resource: <https://www.ada.org/infographics/acute-dental-pain/index.html>
- AAPD Useful Medications: <https://www.aapd.org/research/oral-health-policies--recommendations/useful-medications-for-oral-conditions/>
- AAPD pain management: <https://www.aapd.org/globalassets/media/policies_guidelines/bp_pain.pdf>
- EMA ibuprofen/dexibuprofen safety review: <https://www.ema.europa.eu/en/medicines/human/referrals/ibuprofen-dexibuprofen-containing-medicines>

## Readiness

The architecture is defined, but no analgesic/NSAID rule is ready for production until Moroccan applicability, exact products, contraindication pathways, interaction source and human clinical approval are complete.

