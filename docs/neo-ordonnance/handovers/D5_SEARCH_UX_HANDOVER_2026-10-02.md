# HANDOVER — Digital Crown / Neo Ordonnance / D5 Search + UX Compatibility

Date: 2026-10-02

## 0. Reprise obligatoire

Repository: `hraaaaf/Digital_crown`

Working branch: `feat/neo-medication-search-intelligence`

Do **not** merge to `master` yet.
Do **not** deploy to Vercel.
Neo Ordonnance is still a larger open chantier.

Canonical Notion handover page:
`3ec77c66-3362-817a-a3d0-f6c05566a767`

Canonical UX compatibility roadmap:
`docs/neo-ordonnance/NEO_ORDONNANCE_UX_COMPATIBILITY_ROADMAP.md`

Historical ordonnance roadmap:
`ROADMAP_ORDONNANCE_P1.md`

Start by verifying the real branch HEAD and current GitHub Actions state before modifying anything.

---

## 1. Product decision — NON-REGRESSION CONTRACT

Neo Ordonnance must **add** national catalog + deterministic search + provenance + safety without removing the pre-Neo practitioner workflow.

Each prescription line must remain practitioner-editable.

Mandatory line capabilities:

- 💊 Medication / 🩻 Radio-Exam visual type selector and icons;
- name / DCI or exam label;
- exact catalog presentation identity when selected;
- editable pharmaceutical form;
- editable dosage;
- editable posology;
- structured composer:
  - amount / intake;
  - frequency;
  - duration or maximum;
  - timing / condition;
- free-text posology always available;
- NS / non-substitutable;
- reorder;
- delete;
- protocols / saved prescriptions hydrate editable lines, never locked lines.

The practitioner remains the author.
No automatic clinical recommendation may be invented from the national catalog.

---

## 2. What the pre-Neo audit showed

Compared:

- `PrescriptionAgenticStudioLegacy.tsx`
- `DrugRowV1.tsx`
- `PrescriptionQuickAccessBar.tsx`
- `prescriptionTypes.tsx`
- historical P1 roadmap.

Legacy had:

- medication / dosage / posology suggestions;
- doctor habits;
- presets / protocols;
- quick entry;
- radio/exam handling;
- line-by-line customization.

Neo already retains most of the good UX in `DrugRowV1`:

- Pill / Microscope icons;
- MEDICAMENT / EXAMEN toggle;
- Form;
- Dose;
- NS;
- Prise;
- Rythme;
- Durée ou limite;
- Moment ou condition;
- free text;
- reorder / delete;
- patient safety context.

`PrescriptionQuickAccessBar` already retains:

- saved protocols;
- saved prescriptions;
- favorites;
- recent / frequent medications;
- unified input label “Ajouter un médicament ou un protocole…”;
- protocol hydration into editable lines;
- persistence of:
  - name;
  - dosage;
  - forme;
  - posologie;
  - type;
  - quantite;
  - non_substituable;
  - catalog identity / provenance.

Do **not** resurrect the whole Legacy component.
Reuse only safe practitioner-scoped accelerators.

---

## 3. Medication dictionary status

D1 CLOSED — AMMPS acquisition probe.

D2 CLOSED — deterministic incremental merge.

D3 CLOSED — national coverage.

Certified national source state:

- AMMPS source rows: **9,936**
- unique normalized presentations: **9,931**
- covered pages: **828 / 828**
- source duplicate rows: **5**
- missing pages: 0
- extra pages: 0
- inter-batch normalized ID conflicts: 0
- source update date observed: **01/10/2026**

D4 CLOSED with explicit limitation:

- Wave1 RCP controls scanned: **692**
- enabled RCP controls: **0**
- disabled controls: **692**
- no fake `SNAPSHOT_VERIFIED`
- no clinical RCP extraction activated.

D5 canonical catalog promotion:

- previous canonical count: 401
- current canonical count: **9,931**
- added: 9,530
- updated: 401
- deleted: 0
- second merge: 0 add / 0 update / 0 delete
- byte-identical second pass.

Promotion exact-head certification:
run `36941773457` — SUCCESS.

The 9,931 entries are now actually present in:
`backend/data/medications_ma_ammps_current_2026.json`
on the D5 branch.

---

## 4. D5 revised roadmap — historical snapshot (superseded by §13–15)

### D5.1 — National canonical catalog
DONE.

### D5.2 — Deterministic medication ranking
ACTIVE.

Target ranking bands:

1. exact brand
2. brand prefix
3. brand token prefix
4. exact DCI
5. DCI prefix
6. DCI token prefix
7. brand substring
8. DCI substring
9. fuzzy later, only if needed

Doctor habits / popularity may be tie-breakers only.
They must never override better lexical relevance.

Golden queries:
- DOL
- DOLIPRANE
- AMOX
- IBUPROFENE

Important historical defect:
`DOL` previously returned noisy items such as ANDOL / CLARADOL / SEVREDOL before the intended DOLIPRANE result because search was substring + file-order.

Current latest ranking code change:
`a74c2ca6d33c01769eb7aaa63950634e226ff671`
message:
`fix(rx-search): remove arbitrary name-length tie breaker`

At handover creation time:
run `36944452104` — **in_progress**
workflow: `D5 Medication Search Ranking`

Do not claim D5.2 closed until this is green on the exact evaluated HEAD and golden outputs are inspected.

### D5.3 — Pre-Neo line UX compatibility
ACTIVE.

Canonical contract:
`docs/neo-ordonnance/NEO_ORDONNANCE_UX_COMPATIBILITY_ROADMAP.md`

Tests live in:
- `DrugRow.r5.test.tsx`
- `PrescriptionQuickAccessBar.test.tsx`
- workflow `.github/workflows/neo-ordonnance-line-ux-contract.yml`

### D5.4 — Unified Medication + Protocol search
NEXT after D5.2/D5.3 stability.

Typing e.g. `extraction` must surface a protocol.
Typing medication text must surface medication presentations.
Results must remain explicitly typed and selectable.

### D5.5 — Practitioner habits / personalization
ACTIVE PARTIAL IMPLEMENTATION.

### D5.6 — Safety + provenance without friction
OPEN.

### D5.7 — UX certification
OPEN.
Requires real AFTER evidence at:
- 390×844
- 430×932
- 768×900
- 1280×900
and 200% text scaling if harness supports it.

---

## 5. Current DOLIPRANE 1G personalization implementation

User requirement:

When the practitioner chooses e.g. **DOLIPRANE 1G** from Quick Access, keep the exact national catalog presentation but reuse the practitioner's exact historical posology when one exists.

Implemented commit:

`7397441f66a2e010949710a52d27ef84adf9909c`
`feat(rx-habits): hydrate selected presentation from practitioner habit`

Current behavior in `PrescriptionQuickAccessBar.applyPresentation()`:

1. exact selected presentation comes from `/medications/neo/search`;
2. request:
   `GET /prescriptions/habits/details`
   params:
   - `med_name = row.nom`
   - `dosage = presentationStrength(row)`
3. if `preferred_posology` exists, hydrate selected line with it;
4. if habit lookup fails or returns no exact habit, keep posology empty;
5. catalog selection must still work if habit API fails.

This is an accelerator based on the doctor's own history, **not a clinical recommendation engine**.

Tests added in:

`9980a9f175d9741e6dc77f5c3a79f58a1f0b2d8c`
`test(rx-habits): cover exact-dose practitioner hydration`

Specific tests that PASSED in run `36944398781`:

- “hydrates DOLIPRANE 1G with the exact practitioner posology habit”
- “keeps posology empty when no exact practitioner habit exists”

Example validated in test:

DOLIPRANE / 1 G / COMPRIMES
+
doctor habit:
`1 comprimé x 3 / jour pendant 4 jours`

=> selected editable line contains:
- name DOLIPRANE
- dosage 1 G
- forme COMPRIMES
- posologie `1 comprimé x 3 / jour pendant 4 jours`
- exact `catalogPresentationId`.

Important remaining nuance:
current habit hydration explicitly hydrates **posology**.
Form + dose come from the exact AMMPS catalog presentation.
Do not claim practitioner-specific form/duration fields are separately modeled yet.
Duration currently comes through the posology string and is parsed by `PrescriptionComposer`.

---

## 6. Current UX workflow failure — exact findings

Latest inspected UX run:
`36944398781` — FAILURE
HEAD:
`9980a9f175d9741e6dc77f5c3a79f58a1f0b2d8c`

This run executed:
- `DrugRow.r5.test.tsx`
- `PrescriptionQuickAccessBar.test.tsx`

Most tests passed, including both new exact-dose habit tests.

Two demonstrated failures remain:

### Finding A — NS accessibility assertion mismatch

Test:
“conserve tous les contrôles de personnalisation praticien sur une ligne médicament identifiée”

Current UI button accessible name is:
`NS`

It has:
`title="Non substituable"`
but no `aria-label="Non substituable"`.

The test currently searches:
role button name `/non substituable/i`.

Decision to make:
prefer improving accessibility by giving the NS button an explicit accessible label rather than weakening the test.

Expected safe fix:
add `aria-label="Non substituable"` to the NS button, preserving visible “NS”.

Then test exact accessible name.

### Finding B — homonymous medication Enter test became async-sensitive

Test:
“prioritizes a medication presentation over a homonymous reusable on Enter”

After `applyPresentation` became async because it queries the doctor habit endpoint, the old test expects `setDrugs` immediately after Enter.

Failure:
`expected spy to be called at least once`.

The production behavior now awaits the optional habit lookup before `setDrugs`.

Safe correction choices:
- preferably keep user behavior responsive and investigate whether catalog selection should set the line immediately, then asynchronously enrich exact doctor habit only if the line is still the same selection;
- or minimally update test to await `setDrugs`, but first evaluate UX latency and race safety.

Do not blindly change the test without deciding this interaction behavior.

---

## 7. Quantity field debt

`DrugItem.quantite` still exists.

It is preserved by:
- saved protocols;
- saved prescriptions;
- backend doctor preference persistence.

But `DrugRowV1` currently has no visible quantity editor.

Do not add a fake UI control yet.

First verify:
- document generation contract;
- PDF output;
- persistence behavior;
- whether quantity is actually represented in the final ordonnance document.

Then either restore it end-to-end or explicitly retire/document it.

---

## 8. Safety / clinical constraints

Digital Crown remains:

- local / on-prem product;
- ZERO LLM runtime in the application;
- deterministic Crown Bot only.

Medication rules:

- national catalog = regulatory/documentary presentation source;
- catalog must not invent clinical posology;
- doctor habits are doctor-scoped accelerators only;
- no simple impression event counts as training;
- popularity cannot override lexical relevance;
- if manual edits invalidate exact catalog identity, relink or invalidate identity explicitly;
- never silently erase practitioner intent;
- safety checks remain read-only/contextual;
- RCP clinical fields remain unavailable unless an official source is actually verified and human clinical review occurs.

---

## 9. Git / merge / deploy constraints

- Work branch only: `feat/neo-medication-search-intelligence`
- `master` must remain untouched until the whole Neo Ordonnance chantier is globally finished and explicitly authorized.
- No Vercel deployment without explicit authorization.
- No merge just because D5 becomes green.
- CI green alone is insufficient for closeout.

---

## 10. Mandatory adversarial closeout doctrine

For a meaningful D5 closeout:

At least two distinct adversarial perspectives are required on the **same HEAD**.

Perspective 1 — Search / data integrity:
- ranking bands;
- 9,931 catalog access;
- deterministic ordering;
- no hidden popularity override;
- provenance;
- duplicate behavior;
- latency.

Perspective 2 — Prescription UX / safety:
- full line editability;
- Medication / Radio-Exam icons and type;
- Form / Dose / Posology / Duration / NS;
- protocol hydration remains editable;
- doctor habit hydration does not become auto-prescription;
- manual edits preserved;
- accessibility;
- fail-closed safety.

Then fix findings, create a new HEAD, and rerun reviews from zero.
After convergence, run one additional confirmation pass.

Do not declare CLOSED / VERIFIED / READY unless the project convergence rule is satisfied.

---

## 11. Historical restart sequence — superseded by §13–15

1. Read this handover.
2. Fetch actual branch HEAD and latest workflow state.
3. Inspect run `36944452104`.
4. If ranking failed:
   diagnose + correct ranking/harness, run golden queries.
5. Fix UX Finding A:
   explicit accessible label for NS, then rerun line UX tests.
6. Resolve UX Finding B:
   choose and test correct async behavior for Quick Access + optional doctor habit enrichment.
7. Rerun exact-head:
   - D5 Medication Search Ranking
   - Neo Ordonnance Line UX Contract
8. Verify DOLIPRANE 1G:
   - exact catalog presentation;
   - catalog form/dose;
   - exact doctor posology when existing;
   - empty posology when no exact habit;
   - line remains fully editable.
9. Continue D5.4 unified Medication + Protocol search.
10. Do not merge or deploy.

---

## 12. Historical restart prompt — superseded by §13–15

Continue Digital Crown / Neo Ordonnance from:

`docs/neo-ordonnance/handovers/D5_SEARCH_UX_HANDOVER_2026-10-02.md`

Repository: `hraaaaf/Digital_crown`
Branch: `feat/neo-medication-search-intelligence`

First verify the real branch HEAD and current GitHub Actions state.

The main product constraint is strict:
Neo must preserve the pre-Neo practitioner line-by-line prescription workflow while adding national catalog, deterministic Search Intelligence, provenance and safety.

Do not merge to master.
Do not deploy.
Continue automatically on safe/reversible work.

Follow the handover's Exact restart sequence and the project's adversarial review doctrine.


---

## 13. D5 closeout — certified implementation state

Functional certification HEAD:
`4dc606ee13366a0a3072c3f38220b5d26051dfdf`

D5.2 — Deterministic medication ranking:
CLOSED / CONVERGED on exact-head evidence.

D5.3 — Pre-Neo line UX compatibility:
CLOSED / CONVERGED.

D5.4 — Unified Medication + Protocol search:
CLOSED within the D5 scope covered by the certified tests.

D5.5 — Practitioner habits / personalization:
CLOSED for the demonstrated contract:
- exact catalog presentation is preserved;
- exact-dose practitioner posology habit is reused when present;
- no exact habit leaves posology empty;
- practitioner line remains editable.

D5.6 — Safety + provenance without friction:
CONVERGED.
Certified exact-head evidence:
- manual identity edits invalidate catalog provenance without erasing practitioner-authored dose/form/posology;
- named medication without exact catalog presentation fails closed with “Présentation à confirmer avant validation.”;
- exact tests passed with no unexpected skips or React act warnings.

D5.7 — UX certification:
CONVERGED on exact implementation HEAD `4dc606ee13366a0a3072c3f38220b5d26051dfdf`.

Visual run:
`36994829437` — SUCCESS.

Artifact:
`ordonnance-composer-visual-evidence`
id `11221182790`
digest:
`sha256:6e69ca308cc093c0b8341104f30eef3e2c5bf0ce98bfd09479b572b8718360ab`

Observed evidence:
- 390×844;
- 430×932;
- 768×900;
- 1280×900;
- 390×844 at 200% text scaling;
- `themeMode=tokens-default`;
- no forced `dark` theme in the canonical scenario;
- resolved default tokens:
  - background `#f8fafc`;
  - card `white`;
  - text `#0f172a`;
  - primary `#003380`;
- zero horizontal overflow;
- zero page errors;
- minimum control height 44 px, 88 px at 200%.

Adversarial review — UX / accessibility / workflow:
- BLOCKER: 0
- MAJOR: 0
- significant debt: 0
- strict score: 9.3 / 10

Adversarial review — visual fidelity / safety / practitioner intent:
- BLOCKER: 0
- MAJOR: 0
- significant debt: 0
- strict score: 9.4 / 10

Confirmation pass:
- all 9 visual captures re-inspected;
- metrics and screenshots cross-checked;
- no new BLOCKER or MAJOR demonstrated.

Minor remaining note:
at 200% some compact controls / medication name values are not fully visible at once, without demonstrated functional loss. This is documented as non-blocking.

---

## 14. Merge state at D5 closeout

Do **not** merge D5 directly to `master`.

Verified on 2026-10-02:
- working branch: `feat/neo-medication-search-intelligence`;
- certified implementation HEAD: `4dc606ee13366a0a3072c3f38220b5d26051dfdf`;
- compared with `master`: branch is **diverged**;
- ahead by 315 commits;
- behind by 93 commits.

A direct merge would mix D5 with a large amount of unrelated historical branch state and is therefore not an acceptable closeout action.

This also matches the pre-existing project constraint:
`master` remains untouched until the larger Neo Ordonnance chantier is globally finished and explicitly authorized.

No Vercel deployment is authorized or required for this D5 closeout.

---

## 15. D5 closeout status and next exact action

D5 functional scope:
**CLOSED / CONVERGED** at implementation SHA
`4dc606ee13366a0a3072c3f38220b5d26051dfdf`.

The Git integration of the larger Neo Ordonnance chantier remains OPEN.

Next exact:
continue the next Neo Ordonnance lot from a clean integration strategy rather than merging the long-lived divergent branch wholesale. Before any future merge to `master`, reconcile the 93 commits currently ahead on `master`, isolate the intended Neo Ordonnance changes, rerun the relevant exact-head gates on the integration candidate, then perform the normal adversarial convergence cycle.


---

## 16. D5.8 — UX Polish closeout

D5.8 was opened after a fresh two-reviewer UX/UI audit of the D5 composer.

Final implementation HEAD before D6:
`6814fbf4f36d03230a6ca7384e8228a5f5176735`

Certified outcomes:
- duplicate `Phrase persistée` representation removed;
- single primary posology text representation retained;
- catalog instruction rewritten to request exact presentation confirmation instead of falsely implying no medication was selected;
- desktop composer width expanded;
- contextual values wrap instead of truncating;
- responsive grid uses 1 column mobile / 2 tablet / 4 desktop;
- 200% text scaling no longer clips the medication identity.

Exact-head visual run:
`37005066182` — SUCCESS.

Artifact:
`11224833134`
digest:
`sha256:4649c67d47d333a99ebea113cc81c30f366cf90e86fcd0356180d8d25a11c016`

Final adversarial scores:
- practitioner flow / cognitive load: **9.4 / 10**;
- UI / accessibility / responsive: **9.3 / 10**.

Status:
**D5.8 CONVERGED**.

---

## 17. D6 — Quantity end-to-end & document fidelity closeout

Final certified HEAD:
`65f7875ef7f6d66f6157e0927e0de439a5818bc9`

D6 restores medication quantity only when it is explicitly authored by the practitioner.

Canonical contract:
- `quantite`: optional positive integer value;
- `quantiteExplicit` / `quantite_explicit`: documentary-authoring marker;
- historical/default `quantite=1` without the explicit marker is **not** considered a prescribed quantity;
- no inferred unit is invented;
- clinical ordonnance renders `Quantité : N`;
- FAR derived ordonnance renders `Qté N` only for explicit quantity.

End-to-end coverage now includes:
- DrugRow UI;
- practitioner edit / clear behavior;
- document generation payload;
- backend schema validation;
- archived clinical data;
- document reopening / rehydration;
- saved protocols / saved prescriptions;
- dirty-state;
- real clinical PDF generation;
- FAR bridge + renderer;
- responsive / 200% visual contract.

Critical adversarial finding fixed before certification:
legacy presets could contain `quantite=1` by historical default without practitioner intent.
D6 therefore introduced the explicit marker so those values remain invisible and are not printed.

Exact-head D6 gate:
`37008012126` — SUCCESS.
- backend: **48 passed**;
- frontend: **4 files / 36 tests passed**;
- frontend build: SUCCESS;
- exact build manifest commit:
  `65f7875ef7f6d66f6157e0927e0de439a5818bc9`.

Exact-head visual gate:
`37008012133` — SUCCESS.

Artifact:
`11227425801`
digest:
`sha256:397754a160b298d67ae71f87957e0c5a4fa4b02899d9dd0f8be0a8ea0833366b`

Observed:
- 390×844;
- 430×932;
- 768×900;
- 1280×900;
- 390×844 at 200%;
- quantity control visible;
- medication identity fits at 200%;
- zero horizontal overflow;
- zero page errors.

Adversarial closeout:
- data/document integrity: **9.4 / 10**, 0 BLOCKER, 0 MAJOR;
- practitioner UX / backward compatibility: **9.3 / 10**, 0 BLOCKER, 0 MAJOR;
- extra confirmation pass on same HEAD: clean.

Status:
**D6 CONVERGED**.

---

## 18. Canonical next lot after D6

No pre-existing canonical `D7` definition exists in the current Neo Ordonnance roadmap.

The historical P1 roadmap explicitly leaves one engineering/runtime gate open that the screenshot harness cannot prove:

**authenticated interaction in the real local cabinet application.**

Therefore the recommended next Neo Ordonnance lot is:

### D7 — Authenticated Local Runtime Validation

Goal:
prove the certified Neo Ordonnance workflow inside the real authenticated local application, not only in isolated fixtures.

Minimum scope:
- open a real patient context in the local app;
- create an ordonnance;
- search/select an exact national catalog presentation;
- edit form, dose, structured/free posology, NS and explicit quantity;
- add / reorder / delete a line;
- apply a saved protocol and edit the hydrated line;
- exercise Radio / Exam line behavior;
- preview the ordonnance;
- archive it;
- reopen the archived ordonnance;
- prove practitioner-authored values are preserved exactly;
- inspect the generated clinical PDF;
- verify legacy implicit quantity is not surfaced as authored quantity;
- confirm no unexpected network/LLM dependency is introduced.

This lot is an engineering/runtime validation gate.
It is **not** a clinical/pharmacological certification.

Do not merge to `master` before the complete Neo Ordonnance chantier is finished and explicitly authorized.
Do not deploy to Vercel.
