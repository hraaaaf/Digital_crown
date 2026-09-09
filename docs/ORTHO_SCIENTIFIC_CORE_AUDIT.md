# ORTHODONTIE — SCIENTIFIC CORE AUDIT

Date: 2026-09-09
Branch: `refactor/scientific-core-purge`
PR: #371

## Goal

Guarantee the invariant:

`measurement != diagnosis != indication != treatment`

The software may compute geometry, preserve documented observations and expose sourced/versioned normative metadata. It must not autonomously select diagnosis, extraction, appliance, mechanics, imaging, surgery or patient-specific growth predictions from local thresholds or unvalidated heuristics.

## Current verified state

| Area | Verified state | Disposition |
|---|---|---|
| `frontend/src/features/ortho/orthoExpertSystem.ts` | Automatic extraction/appliance/mechanics/imaging logic neutralized; descriptive fail-closed output only | KEEP temporarily as compatibility boundary |
| `frontend/src/features/ortho/components/Step3Clinical.tsx` | Generated-treatment coupling and local diagnostic/severity thresholds removed; practitioner strategy remains editable | FIXED |
| `frontend/src/features/ortho/components/Step4Documents.tsx` | Duplicate local normative table and Damon default removed; raw values only | FIXED |
| `frontend/src/features/ortho/cephaloUtils.ts` | Age/sex→CVM disabled; IMPA/I-F→DDM correction disabled; missing apex fabrication removed; automatic treatment-plan generation disabled | FIXED |
| `frontend/src/features/ortho/stores/useOrthoStore.ts` | `sexePatient` is nullable, defaults/resets to `null`, restores only explicit `M/F` | FIXED + regression guard |
| `backend/services/cephalo_service.py` | Uses safe engine boundary; practitioner-authored data preserved; no IMPA→space correction | FIXED |
| `backend/services/cephalo_safe_engine.py` | Defense-in-depth strips treatment, legacy normative metadata and T1/T2 if ever reintroduced | KEEP |
| `backend/services/cephalo_engine.py` | Rewritten as geometry-only engine: no local norms/z-scores, no growth projection, no DDM/IMPA empirical correction, no diagnosis/treatment generation | PURGED |
| `backend/services/cephalo_consistency_validator.py` | Structural algebra/unit/calibration checks only; no clinical ranges or ANB class inference | FIXED |
| `backend/services/cephalo_normative_service.py` | Fail-closed infrastructure for future explicitly validated profiles | KEEP |
| `backend/services/bilan_ortho_engine.py` | Raw-measurement restatement + practitioner data only; no class/typology/severity/diagnosis/treatment inference | FIXED / fail-closed |
| `backend/services/ai_advisor.py` | Legacy compatibility adapter is descriptive/fail-closed | KEEP temporarily; runtime import cleanup remains |

## Runtime safety boundaries

Verified protections include:

- `CephaloService` imports `cephalo_safe_engine`, not `cephalo_engine` directly.
- `backend/tests/test_cephalo_engine_reachability.py` forbids direct runtime imports of the geometry engine outside the adapter boundary.
- `backend/tests/test_cephalo_geometry_only.py` locks geometry-only behavior: normative metadata absent, T1/T2 empty, no treatment/narrative inference.
- `backend/tests/test_cephalo_treatment_boundary.py` certifies practitioner-plan preservation and no IMPA→space conversion.
- `backend/tests/test_cephalo_consistency_structural_only.py` prevents clinical ranges/class inference from returning to the PDF consistency gate.
- `backend/tests/test_bilan_ortho_fail_closed.py` prevents skeletal class, vertical typology, DDM severity or alveolar diagnosis from being inferred automatically.
- `backend/tests/test_ortho_frontend_fail_closed_contract.py` now also locks the nullable/reset patient-sex contract and forbids fallback to `M`.

### Reachability note — `ai_advisor`

PR-wide audit shows no remaining cephalometric runtime consumer. `cephalo_service.py` removed its import. The remaining non-test runtime reference is an unused import in `elite_manager.py`; the wrapper's own compatibility tests remain. Do not delete the module until that import is removed safely.

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

- Ousehal L, Lazrak L, Chafii A. *Cephalometric norms for a Moroccan population.* Int Orthod. 2012;10(1):122-134. DOI: 10.1016/j.ortho.2011.12.001.

Engineering consequence: authoritative normative profiles require explicit population/applicability/provenance; no silent generic fallback.

### Growth prediction / T1-T2

The Scientific Core does not present fixed annual displacement vectors as patient-specific growth prediction. Legacy T1/T2 growth vectors have been physically removed from `CephaloEngine`; contractual projection fields remain empty until a separately validated model with applicability and uncertainty exists.

## Verification state before this documentation commit

- Product/code HEAD: `951d13fcbd4c336a3a5741d220eb0dc62c6b7576`.
- Previous CI `34343612583`: frontend tests/build and contextual bridges were progressing green; backend job had not yet completed at the last useful check.
- Earlier backend run `34340987448` reached `277 passed, 1 skipped` before failing on one stale assertion requiring the phrase `référence normative non validée`; that test was corrected to the stricter raw-measurement-only contract.
- Final certification must be performed on the documentation HEAD created after this file update, not on historical runs.

## Remaining critical sequence

1. obtain CI on the final documentation HEAD and fix every regression attributable to the lot;
2. remove the dead `elite_manager → ai_advisor` import when a safe file edit is available, then decide whether to delete the compatibility wrapper/tests;
3. verify all required PR checks on the same HEAD;
4. update PR status/body consistently;
5. leave draft/merge untouched until all closeout criteria are proven;
6. no Vercel deployment without explicit authorization.
