# Current Prescription Risk Audit

Audit date: 2026-07-18
Method: locked `audit-prescription-flow` contract; code inspection only; no clinical behavior changed.

## Flow

Clinical context -> medication selection -> dose generation -> browser/backend warnings -> persistence -> PDF.

The current flow has multiple independent authorities. It does not preserve a single approved rule identifier, version, source set, formulation, calculation trace, or approval state from selection through PDF.

## Findings

| Priority | Finding | Evidence | Required future action |
|---|---|---|---|
| P0 | Missing age/weight is replaced by defaults | `clinical_rules_engine.py` defaults age 30 and weight 70; `prescription_service.py` sends weight 70 | Refuse weight-dependent calculation when verified weight is missing |
| P0 | Pediatric weight can be estimated from age and used for dosing | `clinical_rules.ts` `estimateWeightFromAge` and `getAgeAwareDosing` | Remove estimated weight from clinical calculation; require measured, dated weight |
| P0 | Medication substitutions occur silently | `PrescriptionAgenticStudio.tsx` substitutes allergy/pediatric presets | Require an approved alternative rule, explicit rationale and prescriber confirmation |
| P0 | Unsourced dose engines are active in backend and frontend | `clinical_rules_engine.py`; `clinical_rules.ts` | Replace with one deterministic, versioned rule engine gated by approved sources |
| P0 | Infective-endocarditis prophylaxis includes outdated clindamycin alternative | `clinical_rules_engine.py` | Disable that candidate in a future safety mission and reconcile against current guidance plus Moroccan review |
| P0 | Brand/formulation identity is ambiguous or wrong | `HEXTRIL` mapped to chlorhexidine; `AUGMENTIN 1 g` lacks explicit components | Introduce substance/product/formulation identifiers before rules execute |
| P0 | Runtime web search scrapes a third-party page and infers dose from names | `backend/routers/prescriptions.py` `/search/web` | Remove inference; use licensed, structured and provenance-preserving source integration |
| P0 | PDF is generated before coherence checks and warnings do not block | `backend/routers/documents.py` | Run deterministic blocking validation before persistence/PDF |
| P0 | LLM is asked to assess dosing and contraindications; failure returns no warning | `backend/services/ai_coherence.py` | Keep LLM outside dose calculation/validation authority and fail closed for required deterministic checks |
| P0 | API prescription context lacks critical conditional data | `MedicationItem`, `OrdonnanceData` omit weight, allergy detail, renal/hepatic state, pregnancy and current medicines | Add an explicit context completeness contract before implementing rules |
| P1 | Interaction matrix is small, handwritten and unversioned | `clinical_rules_engine.py` | Adopt licensed interaction source or tightly governed dental subset |
| P1 | Product, rule, habit and protocol are conflated | Models and seeds store free-text dosage/posology | Separate identity, formulation, rule, user preference and rendered instruction |
| P1 | Learned habits can override protocol suggestions | `prescription_service.py` | Never allow usage frequency to override safety or approved rule constraints |
| P1 | Missing dosage is informational rather than blocking | coherence services | Define per-rule missing-data behavior and blockers |
| P1 | Frontend/backend/PDF can diverge | Multiple hardcoded lists and free-text rendering | Store and render an immutable calculation/provenance snapshot |
| P1 | Existing tests encode current hardcoded outputs | prescription tests | Replace expected values with clinician-approved golden cases and independent calculations |
| P2 | Free-text aliases and accents affect matching | keyword maps and regexes | Introduce stable IDs plus controlled aliases |
| P2 | Market status and price-like data have no refresh/version policy | `medications_ma.json` | Record source snapshot, retrieval time, license and current-market status |
| P3 | Duplicate catalog/preset labels increase maintenance cost | seeds, presets, quick forms | Consolidate after safety model is active |

## Immediate architecture gates for future work

1. No dose or product recommendation may execute without stable substance, formulation, route, population, indication, source and rule version.
2. Missing required context must block rather than default.
3. No automatic allergy substitution may be generated from a brand string.
4. No LLM output may be a dose, calculation, contraindication decision, interaction decision, or approval.
5. Validation must occur before persistence and PDF generation.

## Audit verdict

`blocked`: the current prescription feature contains unresolved P0 safety architecture blockers. This mission documents them and does not modify clinical behavior.

