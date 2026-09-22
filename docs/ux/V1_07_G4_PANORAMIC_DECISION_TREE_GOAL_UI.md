# V1-07 G4 — Panoramic Structured Report Decision Tree — Goal UI

Status: BEFORE + AFTER VERIFIED — HUMAN VISUAL APPROVAL PENDING

## Goal
Expose the corpus-grounded Panoramic report context as a fast practitioner decision tree without changing automatic tooth localization or inventing clinical findings.

## Reference
Primary reference: Schnitzer et al., Frontiers in Dental Medicine (2026), structured reporting of 50 dental panoramic images. The reported template used a clickable decision tree with dropdown menus, yes/no questions and free-text fields, and systematically covered dental anomalies, restorations, caries, periodontal structures, apical changes, jawbone, TMJ and paranasal sinuses.

## BEFORE
Capture from the unchanged Panoramic UI at:
- 390×844: `g4-panoramic-structured-report-before-390x844.png`
- 1280×900: `g4-panoramic-structured-report-before-1280x900.png`

BEFORE artifacts were captured on exact-head runtime at 390×844 and 1280×900 before implementation.

## Target interaction
Inside the existing `Constatations` sidebar, add a compact collapsible section: `Revue structurée`.

Order:
1. Question clinique — optional free text.
2. Qualité de l'examen — Non évaluée / Interprétable / Limitée / Non interprétable.
3. Eight domains, each with exactly:
   - Non évalué
   - Sans anomalie documentée
   - Anomalie documentée
4. When `Anomalie documentée` is selected, reveal one optional concise note field.
5. Optional `Réponse à la question clinique` field.
6. Existing tooth-level annotations and global findings remain unchanged.
7. `VALIDER ET GÉNÉRER` sends the structured context together with existing findings.

## Clinical truth rules
- default is always `Non évalué`;
- no automatic normal state;
- no auto-diagnosis from tooth localization;
- no hidden inference from absence of annotations;
- practitioner-entered abnormal notes are persisted verbatim;
- UI terminology stays at radiographic finding level.

## Responsive target
### 390×844
- no horizontal overflow;
- controls usable without zoom;
- domain rows stack vertically;
- radio/segmented controls remain at least touch-usable;
- note fields wrap naturally;
- final generation button remains reachable.

### 1280×900
- sidebar remains 400 px class target without crowding;
- all domain controls fit the sidebar width;
- no extra page-level horizontal scroll;
- sticky generation action remains visible/reachable.

## AFTER acceptance
Capture the same two viewports after implementation and compare:
- no overflow;
- all 8 domains reachable;
- default state is visibly non-evaluated;
- changing one domain to normal generates only its explicit negative statement;
- changing another domain to abnormal + note persists and appears in report;
- untouched domains remain listed as non-evaluated in the generated report;
- question and explicit answer persist and render;
- browser has zero page errors / HTTP 5xx.

## Visual score rubric
- 3 pts clinical truth / state clarity
- 2 pts information hierarchy
- 2 pts responsive / touch usability
- 2 pts behavioral consistency / persistence
- 1 pt runtime cleanliness

Target score is evidence-based only; do not claim 10/10 without AFTER artifacts and browser proof.


## 2026-09-22 — Implementation state
Implemented on the active G4 branch:
- compact `Revue structurée` section in the existing Panoramic findings sidebar;
- optional clinical question;
- explicit image-quality state;
- 8 tri-state review domains with default `not_assessed`;
- abnormal-only note field;
- optional explicit clinical answer;
- payload wired to `report_context` without changing tooth-level findings;
- persisted flat backend context rehydrated into the UI domain state;
- AFTER runtime script checks 390×844 and 1280×900, payload truth, persistence, report rendering, overflow, page errors and HTTP 5xx.

Exact-head AFTER is now verified on run #35746764171 at `bb44d3b94315910b764ea0ac45c9c99b3869e458`, artifact #10703605760 (digest `sha256:ad51df192867f85d319af87a2fcf1077318a958c67e60866116876de39dc1d85`).

Observed AFTER evidence at 390×844 and 1280×900:
- 8 review domains reachable;
- explicit normal, abnormal and untouched `not_assessed` states verified;
- abnormal note, clinical question and clinical answer persist and appear in the generated report;
- no horizontal overflow, page errors or HTTP 5xx from the AFTER harness;
- responsive hierarchy remains readable in top and bottom captures.

Evidence-based visual score before human approval: **9.5/10**.
- clinical truth/state clarity: 3/3
- information hierarchy: 1.8/2
- responsive/touch usability: 1.8/2
- behavioral consistency/persistence: 2/2
- runtime cleanliness: 0.9/1

Remaining gate: explicit human visual approval only.
