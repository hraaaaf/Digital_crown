# Radiology review

## Verdict

V2 safely structures imaging work, but model/data provenance and a validated panoramic taxonomy remain P1 blockers.

Required chain: image observation -> machine candidate -> clinician pending -> clinician validated/rejected finding -> differential link -> clinical diagnosis.

Non-detection is not absence. Non-evaluable and partially evaluable regions are explicit states.

| Area | Status | Review |
|---|---|---|
| Authenticated media | VALID_BASELINE | Preserve tenant-scoped authenticated routes |
| DICOM scope | VALID | WG-22 covers acquisition through reporting |
| Panoramic storage mapping | NEEDS_SOURCE_VERIFICATION | Exact modality/IOD profile requires device testing |
| Finding taxonomy | BLOCKING_GAP | No approved comprehensive taxonomy exists |
| Quality/evaluability | VALID | Structured in V2 |
| Confidence | VALID | Model-specific provenance, never diagnostic certainty |
| Model/data license | BLOCKING_GAP | Dentex-derived provenance and licenses need reconstruction |
| Structured report | NEEDS_EXPERT_REVIEW | 2026 study supports templates but not a universal taxonomy |
| Dataset use | LICENSE_UNCERTAIN | Candidates exist; none downloaded |

Mandatory tests: tenant authorization, content validation, path safety, metadata stripping, orientation/laterality, mirroring, localization, missing/included teeth, superposition, insufficient quality, non-evaluable anatomy, model/version provenance, review transitions and PDF parity.

