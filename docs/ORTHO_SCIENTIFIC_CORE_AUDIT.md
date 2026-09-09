# ORTHODONTIE — SCIENTIFIC CORE AUDIT

Date: 2026-09-09
Branch: `refactor/scientific-core-purge`
PR: #371

## Goal

Guarantee the invariant:

`measurement != diagnosis != indication != treatment`

The software may compute geometry, preserve documented observations and expose sourced normative metadata. It must not autonomously select extraction, appliance, mechanics, imaging, surgery or patient-specific growth predictions from local thresholds or unvalidated heuristics.

## Current verified state

| Area | Verified state | Disposition |
|---|---|---|
| `frontend/src/features/ortho/orthoExpertSystem.ts` | Automatic extraction/appliance/mechanics/imaging logic neutralized; descriptive fail-closed output only | KEEP temporarily as compatibility boundary |
| `frontend/src/features/ortho/components/Step3Clinical.tsx` | Generated-treatment coupling and local diagnostic/severity thresholds removed; practitioner strategy remains editable | FIXED |
| `frontend/src/features/ortho/components/Step4Documents.tsx` | Duplicate local normative table and Damon default removed; no device stored in `profil` | FIXED |
| `frontend/src/features/ortho/cephaloUtils.ts` | Age/sex -> CVM disabled; IMPA/I-F -> DDM correction disabled; missing apex fabrication removed; automatic treatment-plan generation disabled | FIXED / compatibility exports retained |
| `frontend/src/features/ortho/stores/useOrthoStore.ts` | Classe-I / permanent-dentition / Damon defaults removed; missing DDM preserved as missing | PARTIAL: `sexePatient='M'` legacy default remains to replace safely |
| `backend/services/cephalo_service.py` | Uses safe engine boundary; engine-generated treatment stripped; practitioner-authored plan preserved; no IMPA→space correction | FIXED |
| `backend/services/cephalo_safe_engine.py` | Quarantines legacy treatment, local normative semantics and T1/T2 growth projections from runtime | KEEP as defense-in-depth until internal legacy purge |
| `backend/services/cephalo_engine.py` | Legacy hardcoded norms, growth vectors and named treatment strategy still physically present | QUARANTINED / REMOVE after coverage proves safe physical purge |
| `backend/services/cephalo_consistency_validator.py` | Clinical soft/hard norm tables and ANB Class-II/III inference removed; structural algebra/unit/calibration checks retained | FIXED |
| `backend/services/cephalo_normative_service.py` | Fail-closed normative authority; no authoritative classification without validated profile/rule | KEEP |
| `backend/services/bilan_ortho_engine.py` | Legacy treatment generator neutralized fail-closed | KEEP temporarily pending dead-code proof |
| `backend/services/ai_advisor.py` | Legacy compatibility adapter now descriptive/fail-closed; no autonomous therapeutic selection | KEEP temporarily pending reachability cleanup |

## Runtime safety boundaries

Verified protections now include:

- `CephaloService` imports `cephalo_safe_engine`, not the legacy engine directly.
- AST architecture test `backend/tests/test_cephalo_engine_reachability.py` allows only `backend/services/cephalo_safe_engine.py` to import `backend.services.cephalo_engine` at runtime.
- `backend/tests/test_cephalo_treatment_boundary.py` certifies treatment stripping, practitioner-plan preservation, no IMPA→space conversion, no legacy normative metadata and no T1/T2 projection leakage.
- `backend/tests/test_cephalo_consistency_structural_only.py` prevents reintroduction of clinical normal ranges or local ANB class inference into the PDF consistency gate.
- Frontend safety contracts forbid automatic extraction, mechanics, appliance, imaging and treatment-plan generation.

The internal `CephaloEngine` is therefore quarantined, not scientifically validated. Physical removal of its legacy branches remains preferable once coverage is sufficient.

## Scientific basis checked

### CVM

CVM staging is based on morphology of C2, C3 and C4 on the lateral cephalogram, not chronological age/sex alone.

- McNamara JA Jr, Franchi L. *The cervical vertebral maturation method: A user's guide.* Angle Orthod. 2018;88(2):133-143. DOI: 10.2319/111517-787.1.
- Gabriel DB et al. *Cervical vertebrae maturation method: poor reproducibility.* Am J Orthod Dentofacial Orthop. 2009. PMID: 19815136.

Engineering consequence: age/sex-only CVM derivation fails closed.

### Extraction / non-extraction

Extraction planning is multifactorial and individual. Crowding/space discrepancy or incisor inclination alone is not a sufficient autonomous treatment rule.

- Elias KG, Sivamurthy G, Bearn DR. *Extraction vs nonextraction orthodontic treatment: a systematic review and meta-analysis.* Angle Orthod. 2024;94(1):83-106. DOI: 10.2319/021123-98.1.
- *Factors affecting treatment decisions for Class I malocclusions.* Am J Orthod Dentofacial Orthop. 2018. PMID: 30075925.

Engineering consequence: DDM/IMPA may be measurements or documented inputs, never an automatic extraction selector.

### CBCT

- AAOMR position statement: *Clinical recommendations regarding use of cone beam computed tomography in orthodontics.* Oral Surg Oral Med Oral Pathol Oral Radiol. 2013;116(2).

Engineering consequence: no automatic CBCT trigger from a single cephalometric/condylar flag.

### Population-specific cephalometric references

- Ousehal L, Lazrak L, Chafii A. *Cephalometric norms for a Moroccan population.* Int Orthod. 2012;10(1):122-134. DOI: 10.1016/j.ortho.2011.12.001. The authors caution against generalizing the sample to the whole Moroccan population without further studies.

Engineering consequence: every authoritative normative profile requires explicit population/applicability/provenance; no silent generic fallback.

### Growth prediction / T1-T2

- 2025 systematic review of 69 studies on orthodontic growth prediction reports substantial methodological variability and concludes that comprehensive individual prediction remains largely lacking; single-cephalogram prediction is not sufficiently reliable for patient-specific certainty.
- 2026 systematic review/meta-analysis of AI pubertal-growth-spurt models reports pooled accuracy around 0.83 but substantial heterogeneity, limited external validation and insufficient generalizability for routine clinical implementation.

Engineering consequence: fixed annual vectors such as those still present in legacy `_project_t1_growth/_project_t2_growth` cannot be presented as patient-specific predictions. Runtime T1/T2 legacy projections are quarantined until a separately validated prediction model, applicability contract and uncertainty output exist.

## Remaining critical sequence

1. Replace the residual synthetic frontend sex default (`sexePatient='M'`) with an explicit unknown state without breaking consumers.
2. Physically remove/quarantine internal legacy `CephaloEngine` treatment/norm/growth code once branch-wide reachability and tests prove no consumer depends on it.
3. Prove or remove residual dead imports/compatibility wrappers (`ai_advisor`, private legacy treatment helpers).
4. Wire only validated normative metadata to UI; absence of validated profile must remain non-authoritative.
5. Run CI on the current HEAD and fix every regression attributable to this lot.
6. Update `docs/SCIENTIFIC_CORE_REBUILD_ROADMAP.md` from verified state only.
7. Close out PR only after scientific tests + CI + docs are coherent; no Vercel deployment without explicit authorization.
