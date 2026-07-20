# Pharmacology Code Map

Audit date: 2026-07-18

This map is descriptive. It does not validate any medication, dose, protocol, or substitution.

| Path | Symbol | Purpose | Scientific data contained | Source known? | Versioned? | Duplicated? | Runtime? | Risk |
|---|---|---|---|---|---|---|---|---|
| `backend/data/medications_ma.json` | medication records | Local medication search catalog | Names, DCI candidates, forms, presentations, prices and market-like fields | No provenance or reuse license in file | No | Partly | Yes | P1: 4,234 records can appear authoritative without provenance |
| `backend/services/medication_dict.py` | dictionary loader/search | Loads the Morocco-named catalog | Normalized search over local records | No | No | Yes | Yes | P1: identity and market status are not source-gated |
| `backend/services/clinical_rules_engine.py` | `MAROC_PHARMACOPEIA` | Hardcoded medication catalog | Brands, forms, adult and pediatric dose text | No | No | Yes | Yes | P0: active unsourced rules |
| `backend/services/clinical_rules_engine.py` | `PROCEDURE_PROTOCOLS` | Procedure medication suggestions | Indications, prophylaxis and treatment-like protocols | No | No | Yes | Yes | P0: indication and dosing are conflated |
| `backend/services/clinical_rules_engine.py` | `INTERACTION_MATRIX` | Interaction warnings | Drug-class pairs and messages | No | No | Yes | Yes | P1: incomplete handwritten interaction subset |
| `backend/services/clinical_rules_engine.py` | `analyze_patient_context` | Builds safety context | Defaults age to 30 and weight to 70 kg | No | No | Yes | Yes | P0: absent data becomes invented data |
| `backend/services/clinical_rules_engine.py` | `_calculate_pediatric_dosage` | Computes pediatric dose text | Hardcoded mg/kg/day values | No | No | Yes | Yes | P0: production calculation without approved rule object |
| `backend/services/prescription_service.py` | `resolve_smart_prescription` | Resolves suggested prescription | Uses weight 70 kg and merges learned preferences | No | No | Yes | Yes | P0: defaults and preferences may override safety intent |
| `backend/services/prescription_service.py` | normalization/risk maps | Alias and risk checks | Brands, classes, duplicate and risk keywords | No | No | Yes | Yes | P1: duplicated identity and safety logic |
| `backend/routers/prescriptions.py` | `/search/web` | Remote medication search | Scrapes `medicament.ma` and guesses dose from display name | Third-party page only | No | Yes | Yes | P0: runtime scraping and inferred strength |
| `backend/services/clinical_coherence.py` | deterministic checks | Post-generation coherence | Keyword-based medication and dose checks | No | No | Yes | Yes | P1: incomplete and warning-only |
| `backend/services/ai_coherence.py` | local/cloud AI checks | Generates safety warnings | Prompt asks an LLM to judge dose and contraindications | No | Prompt only | No | Yes | P0: LLM participates in dose safety assessment; failure is silent |
| `backend/routers/documents.py` | document generation flow | Creates prescription PDF | Runs coherence after PDF generation | No | No | No | Yes | P0: unsafe output can be generated before review |
| `backend/services/generators/ordonnance_gen.py` | ordonnance renderer | Renders PDF | Prints free-text name, dose, form and instructions | No | No | No | Yes | P1: no rule/source/version provenance in output |
| `backend/models.py` | `Medication` | Medication history/frequency | Free-text name, dosage and form | No | No | Yes | Yes | P1: identity is not stable |
| `backend/models.py` | `ClinicalDrug` | Clinical medication configuration | Molecule, brands, dosages, form, active flag | No | No | Yes | Yes | P1: no source, rule version, jurisdiction or approval |
| `backend/models.py` | `ClinicalProtocolDB` | Clinical protocol configuration | Procedure, molecule list and advice | No | No | Yes | Yes | P1: no source or approval state |
| `backend/models.py` | `DoctorMedicationHabit` | Prescriber habits | Free-text dose and posology | User-origin only | No | Yes | Yes | P1: habit can be mistaken for validated rule |
| `backend/schemas/documents.py` | `MedicationItem`, `OrdonnanceData` | API/document contract | Free-text medications plus age and gender | No | No | No | Yes | P0: weight, allergy, renal/hepatic status and current medicines absent |
| `backend/seed.py` | medication/protocol seed | Seeds catalogs and protocols | Brands, classes, doses and durations | No | No | Yes | Potentially | P1: unsourced values can be activated at startup/setup |
| `frontend/src/features/admin/DocumentStudio/clinical_rules.ts` | `MEDICATION_RULES` | Client-side dosing and safety | Adult/pediatric doses, strengths, contraindications | No | No | Yes | Yes | P0: second active rule engine in browser |
| `frontend/src/features/admin/DocumentStudio/clinical_rules.ts` | `estimateWeightFromAge` | Estimates pediatric weight | Age-derived kilograms | No | No | No | Yes | P0: estimated weight drives dose calculation |
| `frontend/src/features/admin/DocumentStudio/clinical_rules.ts` | `getAgeAwareDosing` | Auto-populates dosing | Weight-based calculations and dose text | No | No | Yes | Yes | P0: no approved rule/source gate |
| `frontend/src/features/admin/DocumentStudio/Forms/PrescriptionAgenticStudio.tsx` | `applyPresetWithSafety` | Adapts presets | Silent allergy and pediatric substitutions | No | No | Yes | Yes | P0: changes medication without validated alternative pathway |
| `frontend/src/features/admin/DocumentStudio/Forms/prescriptionTypes.tsx` | presets | Quick prescription templates | Moroccan brand-like names, strengths and durations | No | No | Yes | Yes | P1: product and rule are conflated |
| `frontend/src/features/admin/DocumentStudio/Forms/PrescriptionForm.tsx` | quick prescriptions | Legacy shortcuts | Fixed medicine/dose/form/instruction tuples | No | No | Yes | Yes | P1: another unsourced catalog |
| `frontend/src/features/admin/DocumentStudio/useDocumentGenerator.ts` | coherence checks | Browser-side warnings | Regex classes and daily maximum text | No | No | Yes | Yes | P1: divergent safety copy and thresholds |
| `backend/tests/`, `frontend/src/**/*.test.*` | prescription tests | Regression tests | Expected doses, substitutions and warning text | Code-derived | No | Yes | No | P1: tests preserve implementation values rather than independent scientific oracles |

## Catalog facts

- `backend/data/medications_ma.json`: 4,234 records, 2,839 unique display names, 1,134 unique DCI strings, and 182 form strings at audit time.
- Those counts describe repository data only. They do not prove current Moroccan authorization, commercialization, price, identity accuracy, or reuse rights.

## Duplication boundaries

The active scientific logic is split across backend rules, frontend rules, quick presets, seeds, learned habits, regex coherence checks, AI prompts, and PDF free text. A future implementation must replace these with one versioned, deterministic rule service and treat UI, PDF, and AI as consumers rather than authorities.

