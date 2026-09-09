# ORTHODONTIE — SCIENTIFIC CORE AUDIT

Date: 2026-09-09
Branch: `refactor/scientific-core-purge`
PR: #371

## Goal

Guarantee the invariant:

`measurement != diagnosis != indication != treatment`

The software may compute geometry, preserve documented observations and expose sourced normative metadata. It must not autonomously select extraction, appliance, mechanics, imaging or surgery from cephalometric thresholds.

## Verified runtime risks

| Area | Verified risk | Disposition |
|---|---|---|
| `frontend/src/features/ortho/orthoExpertSystem.ts` | Active threshold-to-treatment engine: extraction, named teeth, Damon torque, elastics, distalization, bite blocks, imaging | REPLACED with descriptive fail-closed compatibility adapter |
| `frontend/src/features/ortho/components/Step3Clinical.tsx` | Calls `evaluateCase()` and writes generated descriptive text into `strategie_therapeutique`; also contains local threshold/normative UI logic | REPLACE / migrate UI semantics |
| `frontend/src/features/ortho/cephaloUtils.ts` | Age/sex -> CVM; IMPA/I-F -> DDM correction; treatment-plan generation | REPLACE / QUARANTINE |
| `backend/services/cephalo_engine.py` | Legacy strategy generation still exists internally and can generate named appliances/mechanics/surgery | REPLACE; runtime output blocked at service boundary pending internal purge |
| `backend/services/cephalo_service.py` | Previously persisted/exposed `CephaloEngine.ai_narrative.strategie_therapeutique` | FIXED: autonomous engine strategy removed before persistence/response; practitioner clinical plan preserved |
| `backend/services/cephalo_normative_service.py` | Normative service | KEEP: fail-closed; real registry currently yields no authoritative classification without validated profile/rule |
| `frontend/.../Step4Documents.tsx` | Local duplicate normative means/tolerances | ROUTE TO NORM REGISTRY |
| `backend/services/bilan_ortho_engine.py` | Legacy private treatment generator contained device/mechanics prescriptions | NEUTRALIZED fail-closed; retain temporarily until reachability proves safe deletion |

## Implemented safety boundary

Commits in this lot:

- `b9323508` — frontend expert system no longer generates treatment; descriptive output only.
- `2fbe1994` — static frontend safety contract.
- `538820c9` — initial cephalo service treatment-output boundary.
- `995220a3` — cephalo service boundary tests.
- `959fc430` — legacy `BilanOrthoEngine._generate_plan_traitement()` neutralized; no Damon/Invisalign/IPR generation remains in that compatibility method.
- `9e3ba2c5` — bilan treatment fail-closed tests.
- `9676e631` + `085f1a7d` — corrected the service boundary to preserve practitioner-authored `clinical_data.plan_traitement` while stripping only engine-generated `ai_narrative.strategie_therapeutique`, with regression test.

The internal `CephaloEngine` strategy code is not considered scientifically corrected merely because it is blocked at the service boundary. It remains technical debt to remove after coverage proves no other runtime consumer depends on it.

## Scientific basis checked

### CVM

CVM staging is based on morphology of C2, C3 and C4 on the lateral cephalogram, not on chronological age/sex alone.

- McNamara JA Jr, Franchi L. *The cervical vertebral maturation method: A user's guide.* Angle Orthod. 2018;88(2):133-143. DOI: 10.2319/111517-787.1.
- Hussain U et al. *Inter-observer and intra-observer agreement of cervical vertebral maturation staging: A systematic review and meta-analysis.* Orthod Craniofac Res. 2024;22(3):100874. DOI: 10.1016/j.ortho.2024.100874.
- Gabriel DB et al. *Cervical vertebrae maturation method: poor reproducibility.* Am J Orthod Dentofacial Orthop. 2009. PMID: 19815136.

Engineering consequence: age/sex-only CVM derivation must fail closed.

### Extraction / non-extraction

Extraction planning is multifactorial and individual. Crowding/space discrepancy or incisor inclination alone is not a sufficient autonomous treatment rule.

- Elias KG, Sivamurthy G, Bearn DR. *Extraction vs nonextraction orthodontic treatment: a systematic review and meta-analysis.* Angle Orthod. 2024;94(1):83-106. DOI: 10.2319/021123-98.1.
- *Factors affecting treatment decisions for Class I malocclusions.* Am J Orthod Dentofacial Orthop. 2018. PMID: 30075925.
- Mageet AO. *Extraction Planning in Orthodontics.* J Contemp Dent Pract. 2018. PMID: 29807975.

Engineering consequence: DDM/IMPA thresholds may be observations or documented inputs, never an automatic extraction selector.

### CBCT

- AAOMR position statement: *Clinical recommendations regarding use of cone beam computed tomography in orthodontics.* Oral Surg Oral Med Oral Pathol Oral Radiol. 2013;116(2). Orthodontic CBCT use should be justified individually from the clinical presentation.

Engineering consequence: no automatic CBCT trigger from a single cephalometric/condylar flag.

### Population-specific cephalometric references

- Ousehal L, Lazrak L, Chafii A. *Cephalometric norms for a Moroccan population.* Int Orthod. 2012;10(1):122-134. DOI: 10.1016/j.ortho.2011.12.001. The authors explicitly caution that the sample cannot be generalized to the whole Moroccan population without further studies.
- Contemporary population reviews also document meaningful ethnic/geographic variability in cephalometric references.

Engineering consequence: every authoritative normative profile needs explicit population/applicability/provenance. No silent generic fallback.

## Remaining critical sequence

1. Remove `Step3Clinical -> generated report -> strategie_therapeutique` semantic coupling while preserving practitioner-authored strategy.
2. Remove/route local frontend norms and colors through authoritative normative metadata; fail closed when unavailable.
3. Quarantine age/sex CVM and unvalidated DDM correction in `cephaloUtils.ts` and all consumers.
4. Remove internal `CephaloEngine` treatment strategy after proving the service boundary covers every runtime consumer.
5. Prove `ai_advisor.py` reachability before deletion/quarantine.
6. Add negative/golden tests for normative UI fail-closed behavior.
7. Update `SCIENTIFIC_CORE_REBUILD_ROADMAP.md`, certify CI, then close out PR only when all criteria are proven.
