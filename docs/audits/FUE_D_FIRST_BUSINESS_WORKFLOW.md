# FUE-D — First Business Workflow — Patient creation (lab protocol)

Status: OPEN / NOT RUNTIME CERTIFIED. Source: master@c3b094d8e5e8ba52ca40e7521927c0c5d60326a9. Lab: PR #783. No product change in this document.

## Scope and persona
Authorized dentist (owner or secondary dentist with patients permission) in an **already configured** isolated T2 cabinet with an enrolled workstation and a newly authenticated session. The tested entity is strictly synthetic: name FUE-D-TEST, first name MOBILE or DESKTOP, birthdate 1990-01-01, sex explicitly F, distinct deterministic test dossier numbers. Do not use production records or external services. Appointment creation is out of scope; separate next scenario.

## First Value and truthful success
First Value is a **persisted and retrievable new patient**, not discovery of the Create button and not mere navigation. Gate requires all of:
1. authorized and configured cabinet verified via /api/auth/me, /api/clinics/init-status; denied users must receive 403 from patient endpoints;
2. BEFORE screenshot of entry and blank form in viewport;
3. frontend required-fields refusal: nom, prenom, date_naissance, sexe; check no POST is emitted on invalid form;
4. duplicate-check POST /api/patients/check-duplicate returns a real response, and a duplicate is blocked or explicitly confirmed with applicable rules; failed preflight must fail closed;
5. observe actual browser-origin POST /api/patients/ (not mocked); 2xx with positive numeric id, identity, tenant and dossier consistent with submitted fixture; correlate timing, status, payload-safe metadata;
6. independent authenticated GET /api/patients/{id} after POST, matching id/identity and same tenant; ideally reload the dossier and find the patient again using patient list/search;
7. AFTER screenshots after persisted record is visible; no fake optimistic success; if any read fails, no success verdict;
8. record per viewport wall time to First Value, user interactions, decisions, API wait, 4xx/5xx, console/page errors and horizontal overflow.

## Viewports
- mobile 390×844;
- desktop 1280×900;
- test separate synthetic identities and isolated DB fixture; do not count direct URL entry as discoverability proof.

## Safety and failure paths
- No real patient data or identifiable user names in artifacts/logs.
- Reject unauthorized creation (403) and cross-cabinet retrieval (403/404) without disclosure.
- Create must not succeed if duplicate preflight is unreachable; prevent duplicate POST on rapid double-submit, check race and retry behavior.
- 409 duplicate, 422 invalid payload and 5xx/timeouts must not navigate to fabricated patient route or announce success.
- Backend contract observed in master: `create_patient` uses `require_permission("patients")`, tenant-scoped duplicates, `db.commit(); db.refresh(db_patient)` and returns `PatientOut`. Browser UI currently navigates after POST response to /patients/{data.id}; persistence and retrievability remain unproven until runtime checks.
- Treat screenshots as patient-data surfaces, even when fixtures are synthetic. Do not log credentials or full auth headers.
- Fail if evidence artifact is missing or if actual evaluated SHA differs from recorded source SHA.

## Scoring (weighted, severe)
| Dimension | Weight |
| --- | ---: |
| Entry and discoverability | 10% |
| Form and required fields | 25% |
| Error prevention and truthfulness | 20% |
| Server ACK and persisted result | 30% |
| Continuity: reload/search/find | 15% |

A score is **UNASSIGNED** until browser and API evidence exists. An unproven server ACK/persistence is a blocking gate regardless of numerical score.

## Adversarial reviews and closure
A. UX/accessibility: path to action, accessible labels, keyboard/focus, errors, mobile reflow at 390, text 200%, state feedback, fatigue and discoverability.
B. Truth/safety: session/permission, false 2xx, 409/422/5xx, duplicate racing, cross-tenant, tenant filtering, persistence after reload, audit log and secret-safe evidence.
Review exact HEAD independently from test author's assertion, fix demonstrated defects on separate product PR, and repeat both reviews plus clean confirmation on the same new HEAD. Preserve FUE-B P2 debt: misleading "Praticien principal" label for secretary, not a FUE-D fix by default.

## Baseline observation (static only; NOT browser evidence)
Files: frontend/src/features/patients/AddPatientForm.tsx, PatientIdentityContract.ts, backend/routers/patients.py. Form validation and duplicate preflight exist; on 2xx frontend navigates to returned id; backend commits before response. Error text "Erreur serveur. Vérifiez la console." is a UX concern to verify at runtime, not a runtime finding. Desktop Commander offline at previous check; no FUE-D browser evidence, execution timings, scored dimensions, independent reviews or certification yet.

## Next exact
Run new dedicated isolated FUE-D browser certification in GitHub Actions or restored local T2 runtime; collect raw screenshots and request/response summary per viewport; evaluate P0/P1/P2; create separate product PR only for demonstrated defects, without merge or deploy.
