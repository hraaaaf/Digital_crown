# Digital Crown — Competitive Roadmap Post-Media

Status: **ACTIVE — canonical roadmap for the competitive gap chantier after Media closure**  
Created: **2026-09-14**  
Repository: `hraaaaf/Digital_crown`  
Baseline at creation: `master@626a14e00f010627f81f459c7126c2739ecb6b60`

> This file is the canonical restart point for this chantier. In a new window, read it first, then re-check `master`, current HEAD, relevant branches/PRs and CI before drawing conclusions. Never assume the baseline SHA is still current.

---

## 1. Goal

Turn the post-Media competitive audit into an executable roadmap that closes only real product gaps, without rebuilding capabilities Digital Crown already has.

### Success

- Media remains closed and is not reopened without a demonstrated regression or an explicitly new scope.
- Each remaining competitive gap has one bounded lot with explicit in-scope, out-of-scope, dependencies, success criteria and proof requirements.
- No lot duplicates existing Patient Journey, Media Core, notification, orthodontic, lab or analytics capabilities.
- Every lot is closed only after code, tests, observed behavior, exact-head CI, merge and post-merge evidence agree.

### Proof

For each lot, retain:

1. anti-duplication audit;
2. implementation diff;
3. automated tests and security/isolation tests;
4. UI/UX BEFORE → AFTER evidence when visual behavior changes;
5. exact-head CI result;
6. PR audit / merge evidence;
7. post-merge verification;
8. canonical closeout update in this file or a dedicated linked closeout.

---

## 2. Certified baseline — Competitive / Media

**Lot C Media Core = 50/50 EP = 100% CLOSED.**

Verified closeout baseline:

- PR #483 `feat(media): certify Competitive / Media C7`: **MERGED**.
- Certified candidate HEAD: `cf56bb69e65d0eca5b8c5a73e593a02c788cb2d7`.
- Squash merge: `fdaa969f4369c7335e9badcd9480df223f8ee30c`.
- Closeout commit: `e05ecf51da34edc40b434ec2d508340d0e1e19e9`.
- `master@626a14e00f010627f81f459c7126c2739ecb6b60` is a direct descendant of the C7 closeout at the time this canonical was created.
- Candidate CI #3941: **SUCCESS**.
- Backend: **3467 passed / 10 skipped**.
- PostgreSQL #374: **SUCCESS**.
- T2 #2859: **SUCCESS**.
- P7 #1474: **SUCCESS**.
- C4 Visual #58: **SUCCESS**.
- Post-merge CI #3942: **SUCCESS**.
- Volumetric proof: **5,000 tenant-A assets + 500 cross-tenant assets**.
- Responsive proof: **390×844, 768×1024, 1280×900**.
- Preserved visual score: **9.6/10**.

### Hard rule

Do **not** list C6 or C7 as remaining work. Do **not** reopen Media because another roadmap lot needs images, attachments or patient media. Reuse the certified Media Core / Media Hub contracts instead.

---

## 3. Anti-duplication baseline

The roadmap below starts from these already-existing product areas. Their existence does not mean the new gaps are closed; it means future lots must extend them rather than clone them.

| Existing area | Roadmap consequence |
|---|---|
| Internal Patient Journey / patient cockpit capabilities | Do not rebuild an internal cabinet journey under the name Patient Companion. |
| Notification / preference / push infrastructure | Connect Hub must reuse it; do not introduce a second notification engine. |
| Orthodontic / cephalometric clinical capabilities | Ortho Journey must focus on longitudinal treatment workflow, not reimplement diagnosis/cephalo. |
| `lab_jobs` / lab prescription workflow | Lab lot must enrich collaboration and traceability, not create a second lab order model. |
| Existing financial/analytics indicators | BI lot must add recall/outcomes/longitudinal insight, not recreate existing financial dashboards. |
| Certified Media Core / Media Hub | All future image/file workflows must integrate through the canonical media model, not dual-write. |

At the start of every lot, re-check these facts against current `master`; code moves, humans rename things, and roadmaps otherwise age like milk.

---

## 4. Roadmap lots

### Lot D — Patient Companion

**Status:** NOT STARTED  
**Priority:** P1  
**Goal:** provide a secure patient-facing companion without duplicating the internal cabinet Patient Journey.

#### In scope

- patient identity and authenticated patient access;
- strict patient + tenant authorization;
- patient-visible appointments and care follow-up;
- patient-visible documents/media through existing controlled services;
- consent and acknowledgement surfaces where applicable;
- self-service actions that are explicitly safe and bounded;
- mobile-first responsive experience.

#### Out of scope

- replacing the internal Patient Journey;
- rebuilding Media Core;
- inventing a new clinical record model;
- autonomous clinical decisions;
- Vercel deployment without explicit authorization.

#### Success

A patient can authenticate and access only the information/actions explicitly authorized for that patient, with no cross-patient or cross-tenant leakage.

#### Mandatory proof

- API/data-contract audit;
- authorization matrix;
- negative cross-patient and cross-tenant tests;
- patient E2E journey tests;
- responsive BEFORE/AFTER evidence at 390 / 768 / 1280 when UI is implemented;
- exact-head CI + post-merge CI.

#### First sub-lot

**D0 — architecture + anti-duplication audit**: map existing patient/cockpit/auth/document/media contracts, define the minimal patient-facing boundary, then implement only missing primitives.

---

### Lot E — Connect Hub

**Status:** NOT STARTED  
**Priority:** P1, coupled to Lot D  
**Goal:** create one patient communication hub on top of the existing notification infrastructure.

#### In scope

- patient/cabinet conversation timeline or equivalent unified communication surface;
- reuse of current notification preferences and push primitives;
- traceable message state and patient context;
- explicit permissions, auditability and tenant isolation;
- integration points for reminders and future recall workflows.

#### Out of scope

- a second notification engine;
- replacing all current notification services;
- unverified external messaging channels added without security/privacy review.

#### Success

Patient communication is visible and traceable in one canonical workflow while existing notification infrastructure remains the underlying delivery foundation.

#### Mandatory proof

- notification anti-duplication audit;
- permission and audit-log tests;
- conversation/message ordering and idempotency tests where applicable;
- cross-tenant negative tests;
- UI evidence if a new hub is introduced;
- exact-head + post-merge CI.

---

### Lot F — Ortho Journey

**Status:** NOT STARTED  
**Priority:** P2  
**Goal:** add longitudinal orthodontic treatment tracking around the already-existing orthodontic/cephalometric capabilities.

#### In scope

- treatment phases / milestones;
- longitudinal controls and progression history;
- progress media through certified Media Core;
- comparison over time;
- treatment-specific follow-up events and outcomes;
- practitioner-facing and, where safe, patient-facing progress views.

#### Out of scope

- rebuilding cephalometric analysis;
- replacing existing ortho diagnostic logic;
- storing duplicate media outside Media Core.

#### Success

An orthodontic case can be followed coherently from treatment start through controls to closure/outcome, with chronology, provenance and no duplicate clinical/media model.

#### Mandatory proof

- existing ortho capability map;
- migration/data-model proof if schema changes;
- longitudinal ordering/integrity tests;
- Media Core integration tests;
- representative treatment E2E;
- UI BEFORE/AFTER certification where applicable;
- exact-head + post-merge CI.

---

### Lot G — Assurance Maroc

**Status:** NOT STARTED  
**Priority:** P2, business-priority candidate  
**Goal:** create a Morocco-specific insurance/coverage workflow only after the applicable operational and regulatory requirements are verified.

#### In scope

- verified payer/coverage data model;
- eligibility / coverage capture as supported by reliable sources and real workflows;
- estimate/claim/supporting-document workflow where legally and operationally valid;
- traceability of status and practitioner/admin actions;
- clear distinction between patient, insurer and cabinet data responsibilities.

#### Out of scope

- guessing CNSS/CNOPS/AMO rules;
- hard-coding unverified reimbursement rules;
- presenting legal/coverage assumptions as certified facts.

#### Success

A real Morocco insurance workflow can be executed end-to-end using verified rules and source-backed data, with auditable state transitions.

#### Mandatory proof

- external regulatory/operational source pack before implementation;
- rule provenance in code/docs;
- calculation/state-machine tests if calculations are introduced;
- representative real-world workflow tests;
- exact-head + post-merge CI.

#### Gate

**Research gate:** no implementation of reimbursement/coverage logic until current Moroccan requirements have been verified against authoritative sources.

---

### Lot H — Lab / Prosthesis Collaboration

**Status:** NOT STARTED  
**Priority:** P3  
**Goal:** extend the existing lab-job workflow into a traceable cabinet ↔ lab collaboration flow.

#### In scope

- enrich existing lab jobs, not replace them;
- controlled attachments/media through Media Core;
- production/status milestones;
- due dates and delay visibility;
- remake / correction traceability;
- quality-control checkpoints;
- optional lab-facing surface only if justified by the workflow audit.

#### Out of scope

- parallel lab-order tables with duplicated ownership;
- uncontrolled external file storage;
- marketplace functionality unless explicitly opened as a new chantier.

#### Success

A prosthetic/lab case remains traceable from prescription to delivery/acceptance/remake using one canonical lab job and one canonical media layer.

#### Mandatory proof

- `lab_jobs` anti-duplication audit;
- state-transition tests;
- attachment/media integration tests;
- deadline/remake/QC tests;
- tenant and patient authorization tests;
- UI evidence if workflow surfaces change;
- exact-head + post-merge CI.

---

### Lot I — BI / Recall / Outcomes

**Status:** NOT STARTED  
**Priority:** P3  
**Goal:** add longitudinal operational/clinical insight and recall automation without recreating existing financial analytics.

#### In scope

- recall eligibility and scheduling rules;
- traceable reminder/recall lifecycle using Connect/notification foundations;
- longitudinal treatment outcomes;
- clinically meaningful cohort/operational indicators where data quality is sufficient;
- dashboards built from canonical event/data sources.

#### Out of scope

- duplicating current financial dashboards;
- opaque scores without sourceable inputs;
- outcome claims unsupported by collected data.

#### Success

The cabinet can identify who needs follow-up, why, when and what happened after recall/treatment, with metrics traceable to canonical data.

#### Mandatory proof

- source-data completeness audit;
- recall rule tests;
- deduplication/idempotency tests for reminders;
- outcome metric definitions + calculation tests;
- dashboard data reconciliation tests;
- exact-head + post-merge CI.

---

## 5. Default execution order

Technical default:

1. **Lot D — Patient Companion**
2. **Lot E — Connect Hub foundation**, developed with D where contracts overlap
3. **Lot F — Ortho Journey**
4. **Lot G — Assurance Maroc**
5. **Lot H — Lab / Prosthesis Collaboration**
6. **Lot I — BI / Recall / Outcomes**

Business override allowed: **F and G may be inverted** if Morocco insurance becomes the higher commercial priority. That reprioritization does not change the anti-duplication rules or Definition of Done.

Rationale: D + E create the patient-facing identity/communication substrate. F can then reuse Patient Companion + Media. I benefits from the event/history generated by D/E/F/H rather than inventing analytics over incomplete workflows.

---

## 6. Cross-cutting rules

These apply to every lot.

### Architecture

- Reuse canonical services and data models before adding new ones.
- No dual-write merely to satisfy a new UI.
- Preserve tenant isolation and patient scoping end-to-end.
- Preserve auditability for meaningful clinical/admin state changes.
- Digital Crown remains local/on-premise in product architecture; do not quietly turn a roadmap lot into a SaaS dependency.
- Do not reintroduce LLM features into this chantier without an explicit new product decision.

### UI/UX

For any visual change:

1. BEFORE capture;
2. written Goal;
3. mockup/reference;
4. implementation;
5. AFTER at the same viewports;
6. comparison + tests;
7. visual score supported by evidence.

Default responsive certification viewports: **390 / 768 / 1280** unless the feature requires an additional device-specific viewport.

### Security / privacy

- deny by default;
- explicit patient + tenant authorization;
- negative cross-tenant tests for all patient-facing or external collaboration surfaces;
- no public/unscoped media or document fallback;
- no security claim without automated/observed evidence.

### Deployment

**No Vercel deployment without explicit user authorization.**

---

## 7. Definition of Done for each lot

A lot is not CLOSED until all applicable steps are complete:

1. anti-duplication audit against current `master`;
2. bounded scope and explicit exclusions;
3. implementation;
4. proportional automated tests;
5. security/tenant isolation tests;
6. UI/UX certification if visual change;
7. documentation and migrations reconciled;
8. exact-head CI green;
9. PR review state checked: comments / threads / mergeability;
10. merge;
11. post-merge CI/behavior check;
12. canonical closeout update with exact commit/PR/run evidence.

A queued/in-progress CI alone is never a reason to idle; perform independent work first. If no independent work remains and the CI result is indispensable, record the exact run and state as the external asynchronous blocker.

---

## 8. Current state

- Competitive / Media Lot C: **CLOSED — 50/50 EP — 100%**.
- Remaining roadmap axes classified: **6/6**.
- Lots D–I: **NOT STARTED** at creation of this canonical.
- No implementation from D–I should be inferred from this document alone.
- No deployment is authorized by this roadmap.

### Next exact

**Start Lot D0 — Patient Companion architecture + anti-duplication audit on the latest `master`; map existing patient/auth/cockpit/document/media contracts, identify only missing patient-facing primitives, and write the D0 implementation plan with tests and UI proof requirements before changing product behavior.**

---

## 9. Restart checklist

When resuming this chantier:

1. read this file completely;
2. fetch current `master` HEAD;
3. inspect relevant open PRs/branches;
4. inspect current CI state only where relevant;
5. verify the lot status against code/tests, not memory;
6. do not reopen Media C6/C7;
7. continue from `Next exact` unless newer verified evidence in this file supersedes it.

---

## 10. Repères at creation

- chantier: Competitive roadmap post-Media
- canonical: `docs/audits/COMPETITIVE_ROADMAP_POST_MEDIA.md`
- repository: `hraaaaf/Digital_crown`
- baseline master: `626a14e00f010627f81f459c7126c2739ecb6b60`
- Media C7 PR: #483 MERGED
- Media certified candidate: `cf56bb69e65d0eca5b8c5a73e593a02c788cb2d7`
- Media squash merge: `fdaa969f4369c7335e9badcd9480df223f8ee30c`
- Media closeout: `e05ecf51da34edc40b434ec2d508340d0e1e19e9`
- Media candidate CI: #3941 SUCCESS
- Media post-merge CI: #3942 SUCCESS
- real blocker: none for D0 analysis
- next exact: Lot D0 architecture + anti-duplication audit

---

End of canonical roadmap.