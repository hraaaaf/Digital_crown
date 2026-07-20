# Scientific review backlog V2

## P0 - blocks infrastructure use

None after V2 corrections. The infrastructure may guide audits and gated implementation, but it does not validate existing clinical behavior.

## P1 - blocks the affected domain before implementation or activation

1. Pharmacology product authority: obtain an official AMMPS export/API or written data-use agreement that exposes Moroccan authorization status, DCI, brand, form, strength, concentration, holder, version and withdrawal state. Reviewer: Moroccan pharmacist/regulatory specialist.
2. Existing dose constants: trace every value in backend/services/clinical_rules_engine.py to current jurisdiction/population-specific sources and human review before refactoring or activation. Reviewer: dentist plus pharmacist.
3. Moroccan medication file: establish provenance, acquisition date, update process, authorization semantics and license for backend/data/medications_ma.json; quarantine it from clinical decisions if any item cannot be verified.
4. Cephalometry formulas: verify exact landmarks, directed formula and sign for every currently computed metric against original/method publications before changing cephalo_engine.py.
5. Cephalometry norm profiles: review the 2012 Casablanca Steiner study and vertical-dimension study for inclusion criteria, sex/age stratification, measurement definitions and representativeness; do not create a universal Moroccan default.
6. Cephalometry dependency graph: inventory every landmark-to-measurement-to-interpretation-to-PDF dependency and prove transitive invalidation after manual point movement.
7. Panoramic model provenance: reconstruct training dataset identity, consent/privacy basis, license, classes, preprocessing and model version for panoramic_model.onnx and related artifacts.
8. Radiology taxonomy: define and clinician-review a versioned panoramic observation taxonomy with localization, evaluability, uncertainty and explicit separation from diagnosis.
9. Diagnostic state audit: trace current UI/API/DB/PDF paths to prove that findings or LLM output cannot become confirmed diagnoses without clinician identity.
10. Terminology versions/licenses: select and document exact AAE/ESE, EFP/AAP, IADT, ISO 3950 and SNOMED editions and reuse rights before coding mappings.

## P2 - important quality improvements

- Build an executable routing-eval runner against Claude Code invocation logs.
- Add a schema validator using JSON Schema semantics rather than only structural YAML checks.
- Add a source URL freshness check that records redirects and access failures without promoting status.
- Create a scientific change manifest consumed by CI to require reviewer and version fields.
- Define device-specific DICOM conformance fixtures using synthetic metadata.

## P3 - future research

- Review Ricketts, McNamara, Holdaway, Jarabak/Bjork and Sassouni original method sets.
- Review additional Moroccan/North-African cephalometric studies by age, sex and region.
- Evaluate public panoramic datasets only after license, consent and privacy review.
- Map future interoperability to FHIR Observation, Condition, MedicationRequest, DiagnosticReport, ImagingStudy and Provenance.

## Recommended next missions

- PHARMACOLOGY-SOURCE-AND-RULE-AUDIT-1
- CEPHALOMETRY-MEASUREMENT-CONTRACTS-1
- PANORAMIC-PROVENANCE-AND-TAXONOMY-AUDIT-1
- CLINICAL-DIAGNOSIS-STATE-MACHINE-AUDIT-1

## Prescription runtime fact-check history (2026-07-18)

Previous finding: `LLM involved in pharmacological evaluation`.

New evidence: the active release's `/api/documents/generate` route awaits `ClinicalCoherenceService.analyze_coherence()`, which directly awaits `AICoherenceService.analyze_with_ia()` and posts the masked clinical/document context to local Ollama. A no-network spy confirmed the invocation for `doc_type=ordonnance`. Ollama is reachable but currently has no installed `llama3.2` model. Cloud fallback is disabled and no Gemini key is configured.

New classification: **P0 CONFIRMED WITH NARROWED SCOPE**. The LLM does not select medicines or calculate doses; it creates post-generation, non-blocking semantic warnings. The separately named `prescription_agentic_service.py` is deterministic and contains no LLM call.

Action: retain as a prescription safety-architecture item for a future `PRESCRIPTION-SAFETY-GATES-1` mission. Decide whether semantic LLM warnings should be removed from the ordonnance path or made explicitly optional and non-authoritative. Do not treat successful LLM output as deterministic validation.
