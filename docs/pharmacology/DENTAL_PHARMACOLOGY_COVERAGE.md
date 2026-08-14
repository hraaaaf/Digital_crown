# Dental Pharmacology — Coverage Matrix

## Purpose
This matrix defines the functional coverage target of Digital Crown's dental pharmacology module. It separates **source-backed scope** from what is actually encoded, and prevents unsupported molecules/regimens from entering the product by habit or brand recognition alone.

## Proof states
- **CODED_CORE** — deterministic rule encoded in `DentalPharmacologyArbiter.ts` with identified evidence.
- **SOURCE_BACKED_MISSING** — relevant dental use identified in primary/official guidance, but no active R1 rule yet.
- **SEPARATE_EMERGENCY_MODULE** — relevant to dental practice emergency stock/response, not routine Ordonnance auto-prescribing.
- **REVIEW_ONLY / EXCLUDED_DEFAULT** — real medicine but not suitable for automatic/default dental proposal under current evidence/policy.
- **MOROCCO_GATE_REQUIRED** — identity or international regimen evidence exists, but current Moroccan AMM/commercialisation and/or Morocco-specific regimen evidence is not yet established.

## Evidence hierarchy
1. AMMPS / Moroccan official sources for current AMM, RCP/presentation and commercialisation status.
2. Current Moroccan official clinical/good-use guidance when available.
3. Current recognised product/RCP sources where Moroccan equivalent is inaccessible.
4. SDCEP/BNF/BNFC and comparable current dental guidance as international support for an explicit `MOROCCO_GUIDELINE_GAP`.
5. WHO AWaRe for antimicrobial stewardship, not as a dental prescribing guideline.

International support must never be presented as a Moroccan recommendation without a passing Morocco gate.

---

## A. Analgesia / odontogenic pain

| Molecule / intervention | R1 state | Dental evidence | Key rule / limitation | Priority |
|---|---|---|---|---|
| Paracetamol | CODED_CORE | SDCEP analgesics + Moroccan official good-use support | Age-banded dosing; max dose / hepatotoxicity safeguards | P0 core |
| Ibuprofen | CODED_CORE | SDCEP analgesics | Age-banded dosing; NSAID contraindication context required | P0 core |
| Aspirin | SOURCE_BACKED_MISSING | SDCEP analgesics | Adult dental analgesic option; avoid <16 and around extraction/minor surgery; not a routine first default | P1 |
| Paracetamol + ibuprofen alternating | SOURCE_BACKED_MISSING | SDCEP analgesic strategy | Strategy only after inadequate monotherapy; must not create duplicate-dose risk | P1 |
| Diclofenac | SOURCE_BACKED_MISSING | Mentioned in SDCEP odontogenic pain guidance | Exact active regimen page/RCP evidence required before coding | P2 |
| Dihydrocodeine | REVIEW_ONLY / EXCLUDED_DEFAULT | SDCEP/BNF caution | Relatively ineffective for dental pain, adverse effects and misuse potential; no default proposal | Exclude default |

## B. Bacterial dental infections

| Molecule / intervention | R1 state | Dental evidence | Key rule / limitation | Priority |
|---|---|---|---|---|
| Phenoxymethylpenicillin | CODED_CORE | SDCEP 2026 dental abscess first-line | Narrower-spectrum first choice when antibiotic indicated | P0 core |
| Amoxicillin | CODED_CORE | SDCEP 2026 dental abscess first-line | Alternative first-line where adherence makes dosing schedule preferable | P0 core |
| Metronidazole | CODED_CORE | SDCEP 2026 dental abscess first-line | Alternative in penicillin allergy / context-specific use | P0 core |
| Clindamycin | CODED_CORE | SDCEP 2026 second-line | Second-line only after reassessment; not first default | P0 core |
| Clarithromycin | CODED_CORE | SDCEP 2026 second-line | Second-line only after reassessment; interaction review required | P0 core |
| Co-amoxiclav | REVIEW_ONLY / EXCLUDED_DEFAULT | SDCEP 2026 update | Real medicine, but removed from current SDCEP dental abscess second-line guidance; no automatic dental regimen | P0 review gate |
| Antibiotic indication gate | CODED_CORE | SDCEP 2026 bacterial infections | Local/source-control measures first; antibiotics only with defined clinical indication; review ideally at ~3 days | P0 core |

**Important:** antibiotic selection is downstream of an indication decision. A valid drug regimen does not itself establish that an antibiotic is indicated.

## C. Oral candidosis / fungal infections

| Molecule | R1 state | Dental evidence | Key rule / limitation | Priority |
|---|---|---|---|---|
| Miconazole oral gel | CODED_CORE | SDCEP fungal infections | First option for mild/localised disease when suitable; major interaction considerations, especially warfarin | P0 core |
| Fluconazole | CODED_CORE | SDCEP fungal infections | Severe/extensive disease or topical failure; interaction/hepatic review | P0 core |
| Nystatin oral suspension | SOURCE_BACKED_MISSING | SDCEP fungal infections | Alternative when miconazole unsuitable; exact regimen source identified | P1 |

## D. Mouthwashes / local symptomatic treatment

| Molecule | R1 state | Dental evidence | Key rule / limitation | Priority |
|---|---|---|---|---|
| Chlorhexidine | CODED_CORE | SDCEP oral guidance | Local antiseptic; age/context restrictions | P0 core |
| Benzydamine | CODED_CORE | SDCEP oral symptomatic guidance | Local analgesic/anti-inflammatory mouthwash; age restrictions | P0 core |
| Hexetidine / HEXTRIL | SOURCE_BACKED_MISSING | Official RCP identity verified | HEXTRIL = **hexetidine**, not chlorhexidine. Any old alias is invalid. Exact dental policy to be encoded separately if retained | P1 |
| Hydrogen peroxide mouthwash | SOURCE_BACKED_MISSING | SDCEP oral guidance | Exact current regimen page/RCP must be captured before coding | P2 |

## E. Oral ulceration / inflammatory mucosal disease

| Molecule / intervention | R1 state | Dental evidence | Key rule / limitation | Priority |
|---|---|---|---|---|
| Hydrocortisone oromucosal 2.5 mg | SOURCE_BACKED_MISSING | SDCEP oral ulceration | Topical corticosteroid; age restrictions; persistent ulcer >3 weeks requires referral/biopsy pathway | P1 |
| Beclometasone topical oral | SOURCE_BACKED_MISSING | SDCEP oral ulceration | Requires exact regimen and indication constraints before coding | P2 |
| Betamethasone mouthwash | SOURCE_BACKED_MISSING | SDCEP oral ulceration | Requires exact regimen and systemic-risk constraints before coding | P2 |

## F. Viral oral / perioral infections

| Molecule | R1 state | Dental evidence | Key rule / limitation | Priority |
|---|---|---|---|---|
| Aciclovir oral — severe HSV | SOURCE_BACKED_MISSING | SDCEP viral infections | Systemic therapy only for defined severe/immunocompromised context | P1 |
| Aciclovir cream 5% — herpes labialis | SOURCE_BACKED_MISSING | SDCEP viral infections | Local treatment for herpes labialis; benefit depends on early use | P1 |
| Aciclovir oral — herpes zoster | SOURCE_BACKED_MISSING | SDCEP viral infections | Requires medical/referral context; not a casual routine dental default | P2 / specialist gate |

## G. Dental anxiety / premedication

| Molecule | R1 state | Dental evidence | Key rule / limitation | Priority |
|---|---|---|---|---|
| Diazepam | SOURCE_BACKED_MISSING + MOROCCO_GATE_REQUIRED | SDCEP anxiety guidance | Adult premedication option in guidance; dependence/sedation/transport risks. Moroccan controlled-drug/legal rules must be verified before enabling | P2 high-risk |

**Policy:** sedatives/controlled substances require a separate legal/regulatory Morocco gate before any prescribing UI activation.

## H. Dry mouth / caries prevention / fluoride

| Product / molecule | R1 state | Dental evidence | Key rule / limitation | Priority |
|---|---|---|---|---|
| Artificial saliva | SOURCE_BACKED_MISSING | SDCEP dry mouth | Symptomatic supportive care, product-specific composition matters | P2 |
| Sodium fluoride toothpaste 2800 ppm | SOURCE_BACKED_MISSING | SDCEP topical fluoride | Age threshold and caries-risk indication required | P1 |
| Sodium fluoride toothpaste 5000 ppm | SOURCE_BACKED_MISSING | SDCEP topical fluoride | Higher age threshold / risk profile; product/RCP verification required | P1 |
| Sodium fluoride mouthwash 0.05% | SOURCE_BACKED_MISSING | SDCEP topical fluoride | Age threshold and swallowing-risk counseling | P1 |

## I. Medical emergencies in dental practice

These belong to a **separate emergency/cabinet module**, not routine Ordonnance auto-prescribing.

| Medicine / supply | State | Evidence role |
|---|---|---|
| Adrenaline IM | SEPARATE_EMERGENCY_MODULE | Anaphylaxis emergency stock |
| Aspirin 300 mg | SEPARATE_EMERGENCY_MODULE | Suspected acute coronary syndrome emergency context |
| Glucagon | SEPARATE_EMERGENCY_MODULE | Severe hypoglycaemia |
| Glyceryl trinitrate spray | SEPARATE_EMERGENCY_MODULE | Angina / ACS emergency context |
| Midazolam oromucosal | SEPARATE_EMERGENCY_MODULE + MOROCCO_GATE_REQUIRED | Prolonged seizure; controlled-drug/legal storage rules must be verified locally |
| Oral glucose | SEPARATE_EMERGENCY_MODULE | Conscious hypoglycaemia |
| Oxygen | SEPARATE_EMERGENCY_MODULE | Emergency support |
| Salbutamol inhaler | SEPARATE_EMERGENCY_MODULE | Acute bronchospasm/asthma |
| Cetirizine / chlorphenamine / loratadine | SEPARATE_EMERGENCY_MODULE | Optional antihistamine support depending emergency protocol |

No UK controlled-drug/storage rule is automatically transferred to Morocco.

---

## J. Explicit exclusions / review-only defaults

- **No molecule without a traceable source.**
- No brand-to-DCI inference from hard-coded folklore aliases.
- No automatic pediatric weight estimation.
- No automatic therapeutic substitution for allergy/contraindication.
- No routine antibiotic proposal without an explicit infection-indication gate.
- No claim of Moroccan availability from the local dictionary alone.
- No controlled/sedative/emergency medicine activation without Morocco-specific legal/regulatory verification.
- No opioid default for odontogenic pain without a separate evidence/governance decision.
- Existing legacy presets may provide UI convenience only; therapeutic values must pass the canonical R1 pipeline.

## K. Current coverage scorecard

### Coded core
- Analgesics: paracetamol, ibuprofen.
- Dental antibiotics: phenoxymethylpenicillin, amoxicillin, metronidazole, clindamycin, clarithromycin.
- Antifungals: miconazole, fluconazole.
- Local oral agents: chlorhexidine, benzydamine.
- Antibiotic indication gate and review state.

### Next high-value source-backed additions
1. Nystatin.
2. Aspirin dental analgesia with restrictions.
3. Aciclovir oral + topical pathways.
4. Hydrocortisone oromucosal.
5. Sodium fluoride 2800 / 5000 ppm + 0.05% mouthwash.
6. Hexetidine if the product remains useful in the Moroccan formulary after AMMPS verification.

### Separate later workstream
- Emergency drug cabinet.
- Controlled/sedative medicines.
- Automated current AMMPS presentation verification.

## Source recency warning
The SDCEP bacterial-infection section was materially updated in 2026. Other sections remain current on the SDCEP site and are aligned with BNF 91 / BNFC 2025–2026, but are themselves under review. Digital Crown must therefore version evidence per rule and re-review source dates rather than treating the whole formulary as a single permanently-current snapshot.

## Release gate
This matrix is an engineering/evidence inventory, **not clinical certification**. Before clinical release in Morocco, the encoded matrix requires formal review/sign-off by a qualified Moroccan dental/pharmacology reviewer, plus current AMMPS validation for relevant presentations.
