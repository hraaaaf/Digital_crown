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

**Status: CLOSED — merged and post-merge certified.**

Canonical: `docs/audits/PATIENT_COMPANION_D0.md`
PR: **#490 — MERGED**
Certified PR head: `e57fa6f8aed2be1b6f47baad3976586ff3c603c4`
Squash merge: `f61103ee971bd6e64317d8fc0bc759246fa2fd57`
Post-merge CI #4243 / run `34943083332`: **SUCCESS**

Final evidence:
- exact-head CI #4220 **SUCCESS**, including full backend regression DB / patients / documents;
- backend exact-head result observed before merge: **3495 passed / 10 skipped**;
- PostgreSQL #632 **SUCCESS**;
- Patient P7 #1587 **SUCCESS**;
- T2 #3117 **SUCCESS**;
- final PR audit found no blocking reviews, review threads or comments;
- expected-head-protected squash merge completed;
- `master` verified on `f61103ee971bd6e64317d8fc0bc759246fa2fd57` after merge;
- post-merge CI #4243 **SUCCESS** on that exact merge SHA.

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
- owning-cabinet licence gate on Firebase activation;
- runtime route-mount certification test;
- no duplicate Patient/Appointment/Document/Media stores;
- no rewrite of existing Patient/Appointment/Document models.

D0 explicitly does **not** include patient UI, remote gateway, consent UX, appointment mutations, content byte-serving, Connect Hub or Vercel deployment.

### D1 — activation/onboarding UI + minimum useful shell

**Status: READY FOR PR — implementation complete; owner visual validation accepted; exact-head PR CI / merge pending.**

Canonical: `docs/audits/PATIENT_COMPANION_D1.md`
Branch: `feat/patient-companion-d1-ui`

Implemented scope:
- public Patient Companion entry independent from staff auth;
- dedicated Firebase patient Web Auth client;
- isolated Firebase transport using exact `Authorization: Firebase <ID_TOKEN>` and `credentials: 'omit'`;
- recipient-bound activation UX with QR token memory-only handling and manual code path;
- `/me`-driven patient context selection;
- future appointments read-only;
- explicit document/media share metadata only;
- fail-closed revoked/invalid access behavior;
- no cabinet sidebar, no shared cabinet JWT, no patient byte serving;
- native Digital Crown theme tokens consumed by the Patient Companion surface; no parallel glass system.

Visual sequence completed:
1. BEFORE capture certified;
2. Goal written;
3. mockup/reference locked;
4. implementation completed;
5. AFTER captured at 390×844, 768×1024, 1280×900;
6. comparison/tests performed;
7. final themed AFTER run `34969236348` **SUCCESS** on `e92dc5e9b2459c2737e3a72587c3266ff9045bca`;
8. 9/9 captures valid, zero D1 overflow/browser errors/unexpected egress;
9. owner human visual validation **ACCEPTED 2026-09-15**;
10. visual assessment **9/10**.

Reproducibility cleanup:
- Firebase pinned `12.19.0`;
- `@testing-library/dom` pinned `10.4.1`;
- frontend lockfile synchronized by run `34970452423` **SUCCESS**;
- D1 frontend/visual gates switched to `npm ci --legacy-peer-deps`;
- temporary repair/lock workflows removed.

D1 still requires exact-head PR certification, merge, post-merge verification and final canonical closeout before CLOSED.

## 5. Remaining roadmap order

1. Finish D1 closeout — PR / exact-head CI / merge / post-merge
2. Lot D1+ — useful patient workflows beyond the minimum shell, only after new scope is explicitly bounded
3. Lot E — Connect Hub
4. Lot F — Ortho Journey
5. Lot G — Assurance Maroc
6. Lot H — Lab / Prosthesis Collaboration
7. Lot I — BI / Recall / Outcomes

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
- Every modification must preserve existing DB, patient data, documents and already validated functionality; significant changes require proportional non-regression proof before merge.
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
8. exact-head CI green, including non-regression coverage appropriate to the change;
9. PR comments/reviews/threads/mergeability checked;
10. merge;
11. post-merge CI/behavior verified;
12. canonical closeout updated with exact evidence.

## 13. Current state / Next exact

- Media C: CLOSED.
- Patient Companion D0: CLOSED with exact merge and post-merge evidence recorded.
- Patient Companion D1: **READY FOR PR**, human visual validation accepted; exact-head PR CI / merge pending.
- E–I: not started.
- No deployment authorized.

**Next exact:** open D1 PR against current `master`, run exact-head focused + backend/non-regression CI, fix any failure without weakening D0 isolation, merge only when green, then verify post-merge and record final evidence.

End of canonical roadmap.
