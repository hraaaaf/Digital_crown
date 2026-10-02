# Neo-Ordonnance — Existing Pharmacology Reuse & Gap Map

Date: 2026-09-30
Branch: `feat/neo-ordonnance-github`

## Goal
Improve the existing prescription/pharmacology system in place. Do not build a parallel pharmacology engine from scratch.

## Existing components to preserve

### Evidence and Morocco governance
Reuse:
- `docs/pharmacology/DENTAL_PHARMACOLOGY_SOURCES.md`
- `docs/pharmacology/DENTAL_PHARMACOLOGY_COVERAGE.md`
- `frontend/src/features/admin/DocumentStudio/MoroccoPharmacologyPolicy.ts`

Existing invariants already worth keeping:
- Morocco-first evidence hierarchy.
- Medication identity is not proof of current commercialisation.
- Dental indication and drug regimen are separate gates.
- Missing/conflicting evidence fails closed.
- No automatic therapeutic substitution.
- Foreign dental guidance remains support when local evidence is absent.

### Canonical pharmacology pipeline
Reuse:
- `PrescriptionPharmacologyPipeline.ts`
- `normalizeMedicationForPatient.ts`
- `DentalPharmacologyArbiter.ts`
- `DentalPharmacologySupplement.ts`
- `PrescriptionPharmacologyWeightSafety.ts`
- `PrescriptionAmoxicillinSevereSafety.ts`

Current intended path:
`displayed drug -> dictionary identity -> DCI/presentation -> structured patient context -> dental pharmacology arbitration -> safety gates -> Morocco policy -> normalized prescription line + review state`

### Neo components to preserve
N1:
- unified medication identity;
- AMMPS current overlay;
- historical/documentary separation.

N2:
- structured allergy, renal, hepatic, pregnancy, breastfeeding and current-medication state;
- explicit UNKNOWN semantics.

N3/N5:
- read-only backend safety evaluation;
- tenant isolation;
- explicit blockers;
- fail-closed incomplete evidence.

N4.2:
- keep as a bounded interaction/contraindication supplement only.

## Proven overlap

### 1. Duplicate safety ownership
The existing pharmacology pipeline already owns therapeutic/dosing arbitration for several dental medicines.
Neo N4.2 separately evaluates selected medication-risk signals.

Decision:
- do not copy existing regimen logic into N4.2;
- do not replace the existing arbiter with N4.2;
- N4.2 should run as a bounded safety supplement after indication/therapeutic arbitration.

### 2. Two patient-context shapes
Existing frontend context uses nullable structured values and dedicated medication-risk fields.
Neo N2 uses explicit tri-state/status fields and a current-medication list.

Minimal improvement:
create an adapter from Neo structured context to the existing pharmacology context rather than maintaining two independent truth models.

### 3. Legacy context guard
`backend/services/prescription_context_guard.py` still depends partly on legacy context assumptions.

Decision:
keep it for compatibility if needed, but do not use it as Neo's source of truth.
Neo should consume the structured N2 context.

## Source-backed gaps to close in the existing model

### Acute dental pain
The current coverage matrix already identifies a missing combined-analgesia pathway.

Action:
extend the existing analgesia arbiter after source review; do not create a Neo-only dosing engine.

### Antibiotic indication
The existing system already separates antibiotic indication from drug selection.

Action:
ensure Neo command/protocol entry cannot bypass that existing indication gate.

### Anticoagulant / antiplatelet management
Current dental guidance is procedure-sensitive, not just drug-interaction-sensitive.

Gap:
planned dental procedure / bleeding-risk class is not part of the Neo safety contract.

Action:
add procedure-risk context around the existing medication model instead of treating these cases as generic drug-drug contraindications.

### Infective endocarditis prophylaxis
A backend IE prophylaxis rule already exists in `prescription_clinical_rules.py`.

Action:
reuse and audit it before adding any Neo-specific IE rule.

### MRONJ
No active MRONJ-specific gate was identified in this first GitHub audit.

Action:
search/reuse any existing antiresorptive/MRONJ implementation first; only add a bounded clinical-rule gate if genuinely absent.

## Do not rebuild
Do not rebuild:
- medication dictionary;
- AMMPS overlay;
- RCP provenance;
- Morocco policy;
- dental indication gate;
- source-backed pharmacology arbiter;
- paediatric weight safety;
- severe-infection safety;
- prescription composer;
- presets/habits;
- PDF/archive flow.

## Runtime documentation warning
`PRESCRIPTION_RUNTIME_CALL_GRAPH.md` is dated 2026-07-18 and documents an older runtime path.
It must not be treated as proof of the current runtime without a fresh runtime check.

## Recommended minimal sequence

### N4.3A — integration, not expansion
1. Add a structured context adapter from Neo N2 to the existing pharmacology context.
2. Reuse the existing indication/therapeutic arbitration before N4.2 safety supplementation.
3. Keep N4.2 bounded to interaction/contraindication evidence.
4. Preserve fail-closed behavior when therapeutic evidence, Morocco status or interaction knowledge is incomplete.
5. Add tests proving there is one therapeutic source of truth and no antibiotic-indication bypass.

### N4.3B — procedure-sensitive safety
After N4.3A:
1. add procedure bleeding-risk context;
2. audit/reuse IE prophylaxis;
3. locate/reuse or add MRONJ gate;
4. only then expand further medication interaction coverage.

## Release boundary
This is an engineering reuse plan, not clinical certification.
Clinical release still requires source review, Morocco-specific validation where relevant, and qualified clinical/pharmacology sign-off.
