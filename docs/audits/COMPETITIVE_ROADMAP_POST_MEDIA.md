# Digital Crown — Competitive Roadmap Post-Media

Status: **ACTIVE — canonical roadmap for the competitive gap chantier after Media closure**  
Created: **2026-09-14**  
Repository: `hraaaaf/Digital_crown`

> Canonical restart point. In a new window: read this file first, then re-check current `master`, active branch/PR and exact-head CI. Never trust an old SHA merely because humans enjoy copying them into documents.

## 1. Goal

Close only real competitive gaps without duplicating capabilities Digital Crown already has.

## 2. Certified baseline — Media

**Lot C Media Core = CLOSED — 50/50 EP — 100%.**

Key evidence:
- PR #483 merged;
- certified candidate `cf56bb69e65d0eca5b8c5a73e593a02c788cb2d7`;
- squash merge `fdaa969f4369c7335e9badcd9480df223f8ee30c`;
- closeout `e05ecf51da34edc40b434ec2d508340d0e1e19e9`;
- CI #3941 success;
- backend 3467 passed / 10 skipped;
- PostgreSQL #374 success;
- T2 #2859 success;
- P7 #1474 success;
- C4 Visual #58 success;
- post-merge CI #3942 success;
- volumetric proof 5,000 tenant-A assets + 500 cross-tenant assets;
- responsive proof 390×844 / 768×1024 / 1280×900;
- visual score 9.6/10.

Do not reopen Media C6/C7 unless a real regression or new scope is demonstrated.

## 3. Anti-duplication baseline

- Internal Patient Journey / patient cockpit exists: Patient Companion must not clone it.
- Notification/push/preferences exist: Connect Hub must reuse them.
- Ortho/cephalo exists: Ortho Journey is longitudinal workflow, not a second diagnostic engine.
- `lab_jobs` exists: Lab lot extends collaboration, not greenfield lab ordering.
- Financial/operational analytics exist: BI lot targets recall/outcomes, not duplicate dashboards.
- Media Core / Media Hub is canonical for all future image/file workflows.

## 4. Lot D — Patient Companion

**Priority:** P1  
**Goal:** secure patient-facing companion without duplicating internal Patient Journey.

### D0 — identity / authorization foundation

**Status:** CLOSEOUT CANDIDATE — implementation certified; merge/post-merge remaining.

Canonical: `docs/audits/PATIENT_COMPANION_D0.md`

Certified product candidate:
`400348a8dde7c0f0e4902e657857146684c95fd1`

Base master:
`4cfa04d651a47fa0cc2c60482e5ff5729148fb86`

PR: **#490**

Verified candidate evidence:
- CI #4023 SUCCESS;
- backend **3482 passed / 10 skipped / 4 warnings**;
- Cabinet Upgrade PostgreSQL #449 SUCCESS;
- Patient P7 #1519 SUCCESS;
- T2 Runtime Browser #2934 SUCCESS;
- PR merge simulation `ce2341556ba649f3d31d034f35f2d70563d565fb` against the stated master base.

D0 implemented:
- separate Firebase patient principal;
- recipient-bound QR/manual activation;
- single-use/replay protection;
- tenant+patient authorization;
- many-to-many guardian/family access;
- appointment safe read projection;
- explicit document/media share allow-list;
- revocation and auditing;
- owner/admin-only Companion administration in D0;
- no duplicate Patient/Appointment/Document/Media stores.

D0 explicitly does **not** include patient UI, remote gateway, consent UX, appointment mutations, content byte-serving, Connect Hub or Vercel deployment.

### D1 — next sublot after D0 merge

**Status:** NOT STARTED.

Goal: patient activation/onboarding UI and minimum useful companion shell on top of D0.

Mandatory UI sequence:
1. BEFORE capture;
2. written Goal;
3. mockup/reference;
4. implementation;
5. AFTER at 390×844, 768×1024, 1280×900;
6. comparison + tests;
7. visual score backed by evidence.

D1 must not weaken D0 auth isolation. Remote/home access remains a separate gateway decision unless an existing verified secure path is found.

## 5. Remaining roadmap order

1. Lot D — Patient Companion
2. Lot E — Connect Hub
3. Lot F — Ortho Journey
4. Lot G — Assurance Maroc
5. Lot H — Lab / Prosthesis Collaboration
6. Lot I — BI / Recall / Outcomes

F/G may be swapped if Morocco insurance becomes higher commercial priority.

## 6. Lot E — Connect Hub

**Status:** NOT STARTED.

Goal: unified patient/cabinet communication surface on top of existing notification infrastructure. No second notification engine.

## 7. Lot F — Ortho Journey

**Status:** NOT STARTED.

Goal: longitudinal treatment phases, controls, progression, progress media and outcomes around existing ortho/cephalo capabilities.

## 8. Lot G — Assurance Maroc

**Status:** NOT STARTED — research gate applies.

No reimbursement/coverage logic may be implemented before current Moroccan operational/regulatory rules are verified against authoritative sources.

## 9. Lot H — Lab / Prosthesis Collaboration

**Status:** NOT STARTED.

Extend canonical `lab_jobs` with richer collaboration, media, deadlines, QC and remakes. No second lab-order model.

## 10. Lot I — BI / Recall / Outcomes

**Status:** NOT STARTED.

Add recall automation and longitudinal outcomes using canonical data/events. Do not recreate current financial analytics.

## 11. Cross-cutting rules

- Reuse before creating.
- No dual-write for UI convenience.
- Tenant + patient isolation end-to-end.
- Meaningful mutations audited.
- No patient-facing public/unscoped media/document fallback.
- No security claim without automated/observed proof.
- UI changes require BEFORE → Goal → reference/mockup → implementation → AFTER same viewports → comparison/tests → visual score.
- **No Vercel deployment without explicit user authorization.**

## 12. Definition of Done

A lot is not CLOSED until applicable steps are complete:
1. anti-dup audit;
2. bounded scope/exclusions;
3. implementation;
4. automated tests;
5. security/isolation tests;
6. UI certification if visual;
7. docs/migrations reconciled;
8. exact-head CI green;
9. PR comments/reviews/threads/mergeability checked;
10. merge;
11. post-merge CI/behavior verified;
12. canonical closeout updated with exact evidence.

## 13. Current state / Next exact

- Media C: CLOSED.
- Patient Companion D0: implementation certified, documentation closeout committed on PR #490, merge/post-merge still required.
- D1–I: not started.
- No deployment authorized.

**Next exact:** certify the documentation closeout HEAD of PR #490 → recheck comments/reviews/threads/mergeability → squash merge → verify post-merge `master` CI → mark D0 CLOSED → start D1 with mandatory UI BEFORE evidence.

End of canonical roadmap.
