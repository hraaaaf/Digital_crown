# Scientific agent system V1

This infrastructure guides future scientific engineering; it is not a clinically validated subsystem.

## Route a task

| Task | Primary agent | Primary skill |
|---|---|---|
| Cross-domain contract or scientific persistence design | @scientific-architect | implement-scientific-rule or scientific-database-migration |
| Prescription/pharmacology | @pharmacology-engineer | audit-prescription-flow or implement-scientific-rule |
| Examination/diagnosis/odontogram | @clinical-diagnosis-engineer | audit-clinical-diagnosis-flow |
| Cephalometric measurement | @cephalometry-engineer | implement-cephalo-measurement |
| Cephalometric pipeline audit | @cephalometry-engineer | validate-cephalo-pipeline |
| Radiology finding | @radiology-engineer | implement-radiology-finding |
| Panoramic pipeline audit | @radiology-engineer | audit-panoramic-report-pipeline |
| Independent tests | @scientific-test-engineer | generate-scientific-golden-tests |
| Independent final review | @scientific-reviewer | review-scientific-pull-request |

Invoke the architect only for shared contracts, cross-domain dependencies or migrations. Cosmetic work does not trigger scientific skills merely because a label contains ordonnance, diagnostic, cephalo or panoramic.

## Source and activation rules

Sources start as candidate. Only a named human clinical reviewer may assign approved-by-clinician with date and evidence. A rule activates only when every claim has applicable approved evidence, explicit units/population/version/missing-data behavior, independent tests and independent review.

Formula approval and norm-profile approval are separate. INN is not product authorization. DDD is not a dose. Brand is not concentration. Non-detection is not absence. An observation is not a diagnosis.

## Forbidden

No LLM dose or cephalometric calculation, automatic confirmed diagnosis, patient data/media in tests or research, unlicensed dataset/product ingestion, production migration, bypass permissions, or claim of clinical/regulatory validation.

Run python scripts/validate_scientific_ai_assets.py and targeted validator tests after any infrastructure change.

