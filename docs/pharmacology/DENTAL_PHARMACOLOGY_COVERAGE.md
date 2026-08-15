# Dental Pharmacology — Coverage Matrix

## Purpose
This matrix defines the functional coverage target of Digital Crown's dental pharmacology module. It separates **source-backed scope** from what is actually encoded and prevents unsupported molecules/regimens from entering the product by habit or brand recognition alone.

## Proof states
- **CODED_CORE** — deterministic source-backed rule active in the canonical R1 normalizer.
- **SOURCE_BACKED_MISSING** — relevant dental use identified in primary/official guidance, but no active R1 rule yet.
- **SEPARATE_EMERGENCY_MODULE** — relevant to dental practice emergency stock/response, not routine Ordonnance auto-prescribing.
- **REVIEW_ONLY / EXCLUDED_DEFAULT** — real medicine but not suitable for automatic/default dental proposal under current evidence/policy.
- **MOROCCO_GATE_REQUIRED** — identity or international regimen evidence exists, but current Moroccan AMM/commercialisation and/or Morocco-specific regimen evidence is not established.

## Evidence hierarchy
1. AMMPS / Moroccan official sources for current AMM, RCP/presentation and commercialisation status.
2. Current Moroccan official clinical/good-use guidance when available.
3. Current recognised product/RCP sources where Moroccan equivalent is inaccessible.
4. SDCEP/BNF/BNFC and comparable current dental guidance as international support for an explicit `MOROCCO_GUIDELINE_GAP`.
5. WHO AWaRe for antimicrobial stewardship, not as a dental prescribing guideline.

International support must never be presented as a Moroccan recommendation without a passing Morocco gate.

---

## A. Analgesia / odontogenic pain

| Molecule / intervention | R1 state | Dental evidence | Key rule / limitation |
|---|---|---|---|
| Paracetamol | CODED_CORE | SDCEP analgesics + Moroccan official good-use support | Age-banded dosing; max dose / hepatotoxicity safeguards |
| Ibuprofen | CODED_CORE | SDCEP analgesics | Age-banded dosing; NSAID contraindication context required |
| Aspirin | SOURCE_BACKED_MISSING | SDCEP analgesics | Adult option; avoid <16 and around extraction/minor surgery; not a routine first default |
| Paracetamol + ibuprofen alternating | SOURCE_BACKED_MISSING | SDCEP analgesic strategy | Only after inadequate monotherapy; duplicate-dose guard required |
| Diclofenac | SOURCE_BACKED_MISSING | SDCEP odontogenic pain overview | Exact active regimen/RCP evidence required before coding |
| Dihydrocodeine | REVIEW_ONLY / EXCLUDED_DEFAULT | SDCEP/BNF caution | Relatively ineffective for dental pain; adverse effects/misuse potential |

## B. Bacterial dental infections

| Molecule / intervention | R1 state | Dental evidence | Key rule / limitation |
|---|---|---|---|
| Phenoxymethylpenicillin | CODED_CORE | SDCEP 2026 dental abscess first-line | Narrower-spectrum first choice when antibiotic indicated |
| Amoxicillin | CODED_CORE | SDCEP 2026 dental abscess first-line | Alternative first-line where adherence makes schedule preferable |
| Metronidazole | CODED_CORE | SDCEP 2026 dental abscess first-line | Alternative in penicillin allergy / context-specific use |
| Clindamycin | CODED_CORE | SDCEP 2026 second-line | Second-line only after reassessment |
| Clarithromycin | CODED_CORE | SDCEP 2026 second-line | Second-line only after reassessment; interaction review required |
| Co-amoxiclav | REVIEW_ONLY / EXCLUDED_DEFAULT | SDCEP 2026 update | Not in current SDCEP dental abscess second-line guidance; no automatic dental regimen |
| Antibiotic indication gate | CODED_CORE | SDCEP 2026 bacterial infections | Local/source-control measures first; antibiotic only with defined indication; review ideally ~3 days |

**Important:** antibiotic selection is downstream of an indication decision. A valid drug regimen does not itself establish that an antibiotic is indicated.

## C. Oral candidosis / fungal infections

| Molecule | R1 state | Dental evidence | Key rule / limitation |
|---|---|---|---|
| Miconazole oral gel | CODED_CORE | SDCEP fungal infections | Mild/localised disease when suitable; major interaction review |
| Fluconazole | CODED_CORE | SDCEP fungal infections | Severe/extensive disease or topical failure; interaction/hepatic review |
| Nystatin oral suspension | CODED_CORE | SDCEP nystatin | 100,000 units/ml; 1 ml after food QID for 7 days; remains Morocco-review until local gate passes |

## D. Mouthwashes / local symptomatic treatment

| Molecule | R1 state | Dental evidence | Key rule / limitation |
|---|---|---|---|
| Chlorhexidine | CODED_CORE | SDCEP oral guidance | Local antiseptic; age/context restrictions |
| Benzydamine | CODED_CORE | SDCEP oral symptomatic guidance | Local analgesic/anti-inflammatory; age restrictions |
| Hexetidine / HEXTRIL | SOURCE_BACKED_MISSING | Official RCP identity verified | HEXTRIL = **hexetidine**, not chlorhexidine; old alias retired |
| Hydrogen peroxide mouthwash | SOURCE_BACKED_MISSING | SDCEP oral guidance | Exact current regimen/RCP required before coding |

## E. Oral ulceration / inflammatory mucosal disease

| Molecule / intervention | R1 state | Dental evidence | Key rule / limitation |
|---|---|---|---|
| Hydrocortisone oromucosal 2.5 mg | CODED_CORE | SDCEP hydrocortisone | ≥12: adult regimen; <12 review/medical advice; persistent ulcer pathway remains separate |
| Beclometasone topical oral | SOURCE_BACKED_MISSING | SDCEP oral ulceration | Exact regimen/indication constraints required |
| Betamethasone mouthwash | SOURCE_BACKED_MISSING | SDCEP oral ulceration | Exact regimen/systemic-risk constraints required |

## F. Viral oral / perioral infections

| Molecule | R1 state | Dental evidence | Key rule / limitation |
|---|---|---|---|
| Aciclovir oral — severe HSV | CODED_CORE | SDCEP aciclovir | 5-day severe/immunocompromised HSV pathway; pediatric age bands encoded |
| Aciclovir cream 5% — herpes labialis | SOURCE_BACKED_MISSING | SDCEP viral infections | Local early-treatment pathway still to encode separately |
| Aciclovir oral — herpes zoster | SOURCE_BACKED_MISSING | SDCEP viral infections | Requires medical/referral context; separate specialist gate |

## G. Dental anxiety / premedication

| Molecule | R1 state | Dental evidence | Key rule / limitation |
|---|---|---|---|
| Diazepam | SOURCE_BACKED_MISSING + MOROCCO_GATE_REQUIRED | SDCEP anxiety guidance | Sedation/dependence/transport risks; Moroccan controlled-drug/legal rules must be verified before enabling |

**Policy:** sedatives/controlled substances require a separate Morocco legal/regulatory gate before any prescribing UI activation.

## H. Dry mouth / caries prevention / fluoride

| Product / molecule | R1 state | Dental evidence | Key rule / limitation |
|---|---|---|---|
| Artificial saliva | SOURCE_BACKED_MISSING | SDCEP dry mouth | Product-specific composition matters |
| Sodium fluoride toothpaste 2800 ppm | CODED_CORE | SDCEP 2800 ppm | ≥10 only; presentation-specific rule |
| Sodium fluoride toothpaste 5000 ppm | CODED_CORE | SDCEP 5000 ppm | ≥16 only; presentation-specific rule |
| Sodium fluoride mouthwash 0.05% | CODED_CORE | SDCEP 0.05% mouthwash | ≥6 only; 10 ml for 1 min daily; swallowing-risk counseling |

The canonical pipeline preserves fluoride presentation details during DCI resolution so 2800 ppm, 5000 ppm and 0.05% mouthwash cannot collapse into one generic sodium-fluoride rule.

## I. Medical emergencies in dental practice

These belong to a **separate emergency/cabinet module**, not routine Ordonnance auto-prescribing.

| Medicine / supply | State | Evidence role |
|---|---|---|
| Adrenaline IM | SEPARATE_EMERGENCY_MODULE | Anaphylaxis emergency stock |
| Aspirin 300 mg | SEPARATE_EMERGENCY_MODULE | Suspected acute coronary syndrome context |
| Glucagon | SEPARATE_EMERGENCY_MODULE | Severe hypoglycaemia |
| Glyceryl trinitrate spray | SEPARATE_EMERGENCY_MODULE | Angina / ACS context |
| Midazolam oromucosal | SEPARATE_EMERGENCY_MODULE + MOROCCO_GATE_REQUIRED | Prolonged seizure; local controlled-drug/storage rules required |
| Oral glucose | SEPARATE_EMERGENCY_MODULE | Conscious hypoglycaemia |
| Oxygen | SEPARATE_EMERGENCY_MODULE | Emergency support |
| Salbutamol inhaler | SEPARATE_EMERGENCY_MODULE | Acute bronchospasm/asthma |
| Cetirizine / chlorphenamine / loratadine | SEPARATE_EMERGENCY_MODULE | Optional antihistamine support by emergency protocol |

No UK controlled-drug/storage rule is automatically transferred to Morocco.

---

## J. Explicit exclusions / review-only defaults

- **No molecule without a traceable source.**
- No brand-to-DCI inference from hard-coded aliases.
- No automatic pediatric weight estimation.
- No clinical fact inferred from free-text antecedents for pharmacology arbitration.
- No automatic therapeutic substitution for allergy/contraindication.
- No local “force allergy” bypass in `DrugRow`.
- No routine antibiotic proposal without an explicit infection-indication gate.
- No claim of Moroccan availability from the local dictionary alone.
- No controlled/sedative/emergency medicine activation without Morocco-specific legal/regulatory verification.
- No opioid default for odontogenic pain without a separate evidence/governance decision.
- Existing legacy presets may provide UI convenience only; therapeutic values must pass the canonical R1 pipeline.

## K. Current coded coverage

### Active source-backed R1 rules
- Analgesics: paracetamol, ibuprofen.
- Dental antibiotics: phenoxymethylpenicillin, amoxicillin, metronidazole, clindamycin, clarithromycin.
- Antifungals: miconazole, fluconazole, nystatin.
- Local oral agents: chlorhexidine, benzydamine.
- Viral: aciclovir severe-HSV systemic pathway.
- Oral ulceration: hydrocortisone oromucosal.
- Fluoride: sodium fluoride 2800 ppm, 5000 ppm and 0.05% mouthwash.
- Antibiotic indication gate and per-line review state.

All remain subject to the Morocco policy gate. A foreign-supported regimen can be displayed as support but remains practitioner-confirmation-required unless the Morocco gate explicitly passes.

### Next high-value source-backed additions
1. Aspirin dental analgesia with restrictions.
2. Aciclovir cream 5% herpes labialis pathway.
3. Hexetidine if useful after AMMPS presentation verification.
4. Beclometasone / betamethasone oral-inflammatory pathways.
5. Artificial saliva.

### Separate later workstream
- Emergency drug cabinet.
- Controlled/sedative medicines.
- Automated current AMMPS presentation verification.

## Source recency warning
The SDCEP bacterial-infection section was materially updated in 2026. Other sections remain current on the SDCEP site and aligned with BNF 91 / BNFC 2025–2026, but are themselves under review. Digital Crown must version evidence per rule and re-review source dates rather than treating the whole formulary as one permanently-current snapshot.

## Release gate
This matrix is an engineering/evidence inventory, **not clinical certification**. Before clinical release in Morocco, the encoded matrix requires formal review/sign-off by a qualified Moroccan dental/pharmacology reviewer, plus current AMMPS validation for relevant presentations.
