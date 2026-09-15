# Digital Crown — Patient Companion D1

Status: **CLOSED — merged, human-validated and post-merge certified**

Repository: `hraaaaf/Digital_crown`
Merged PR: `#512`
Certified candidate HEAD: `26806bfc93f1ef59845002467fab45aa00a5d171`
Squash merge on `master`: `0895296867fa1b27ecbccd77ffcb8614ef83e04f`
Canonical predecessor: `docs/audits/PATIENT_COMPANION_D0.md`
Roadmap: `docs/audits/COMPETITIVE_ROADMAP_POST_MEDIA.md`

## 1. Goal

Build the smallest useful patient-facing experience on top of the certified D0 security boundary:

`secure patient activation -> dedicated Firebase patient authentication -> explicit patient-context selection when needed -> Patient Companion home -> future appointments read-only -> explicitly shared document/media metadata`

The D1 frontend must never reuse the cabinet JWT, invent a patient session, expose implicit patient data, add byte-serving fallbacks, or create a second patient/appointment/document/media source of truth.

## 2. Success criteria

D1 is successful only if observable proof shows all of the following:

1. Public patient entry exists independently from cabinet authentication.
2. Patient authentication is Firebase-specific and produces the backend-required `Authorization: Firebase <ID_TOKEN>` header.
3. Patient API traffic does not reuse the shared cabinet Axios client, does not send `Bearer <cabinet JWT>`, and omits cabinet cookies.
4. Activation accepts exactly one D0 invitation secret: QR token or manual code.
5. A Firebase identity whose verified contact does not match the invitation remains rejected by the D0 backend.
6. `/me` is used as the only source for linked patient contexts.
7. Multiple linked contexts require explicit user selection; no cross-context data is merged.
8. Future appointments are display-only.
9. Documents/media shown in D1 come only from `/contexts/{access_id}/shares` and remain metadata-only in D1; there is no patient byte download/open fallback.
10. Revoked/invalid patient access fails closed.
11. Existing DB, patient data, documents, cabinet auth, mobile PWA and validated product routes remain unchanged.
12. AFTER evidence exists at exactly 390×844, 768×1024 and 1280×900 with no D1 horizontal overflow, page errors or console errors.
13. Patient Companion visual surfaces consume the existing Digital Crown theme tokens; no parallel glassmorphism palette/system is introduced.

All 13 criteria are now covered by implementation, visual proof, exact-head certification and post-merge non-regression evidence recorded below.

## 3. Certified BEFORE

Workflow: `Patient Companion D1 BEFORE` run `34948914354` — **SUCCESS**.
Artifact: `patient-companion-d1-before-exact-master`.
Product baseline: `3fd0fb6ed759cff527a4524b031e6c0ab537f5d3`.

Observed baseline at 390×844 / 768×1024 / 1280×900:

- HTTP 200 on all three captures;
- zero page errors;
- zero console errors;
- no patient-facing Patient Companion entry existed in D0;
- the captured public landing was the dentist-facing landing and is historical BEFORE evidence only, not a semantic pixel baseline for the final patient-facing public entry.

## 4. Auth / transport implementation

D0 backend contract requires `Authorization: Firebase <ID_TOKEN>` and verifies Firebase tokens with revocation checking. The existing frontend shared `api` client injects cabinet `Bearer` tokens and is deliberately not reused by Patient Companion.

Implemented D1 rules:

- dedicated Firebase Web Auth app/client;
- Firebase session persistence scoped to session with memory fallback, never cabinet token storage;
- verified e-mail required before patient API access;
- fresh Firebase ID token on patient API calls;
- dedicated Patient Companion `fetch` transport;
- `credentials: 'omit'`;
- exact `Authorization: Firebase <ID_TOKEN>` scheme;
- 401 fails closed by signing out the patient identity and hard-returning to Patient Companion entry;
- raw QR token remains memory-only and is stripped from the URL;
- Patient Companion path excluded from existing staff Sentry Replay and mobile/service-worker persistence surfaces;
- no patient byte-serving endpoint or fallback introduced.

D1 supports verified Firebase e-mail identity. Phone-bound invitations remain a D0 backend capability and are not emulated in the D1 frontend.

## 5. Patient-visible scope

The patient can see only:

- safe linked patient context identity returned by `/me`;
- future, non-cancelled appointments for that exact authorised context, read-only;
- document/media metadata that the cabinet explicitly placed on the Patient Companion allow-list.

The patient cannot in D1:

- create, move or cancel appointments;
- browse the internal clinical record;
- see non-shared documents/media;
- download/open document or media bytes;
- cross patient contexts;
- use a cabinet employee JWT/session.

## 6. Cabinet administration boundary

D0 administration remains intentionally narrow:

- invitation creation is cabinet-admin/practitioner controlled;
- a new live invitation for the same patient invalidates previous unconsumed live invitations;
- invitations are recipient-bound and single-use;
- invitation/access/share revocation is audited;
- document/media shares are explicit allow-list grants;
- full Patient Companion access can be revoked by the practitioner principal.

Current backend `require_companion_admin` reserves Patient Companion administration to the principal `ADMIN` / `DENTISTE` account without an employer parent, plus superadmin. Employee delegation, including assistant administration, remains a D1 non-goal and is not silently enabled.

## 7. UI reference and final theme rule

Patient Companion remains visually separate from the staff workspace and has no cabinet sidebar. Responsive contract:

- 390×844: stacked patient shell, activation/home readable without horizontal overflow;
- 768×1024: centered patient shell with stacked content;
- 1280×900: compact two-column appointments / shares home.

Final theme decision after human review:

- consume Digital Crown native tokens only: `--glass-bg`, `--glass-border`, `--shadow-glass`, theme blur and semantic background/text/border variables;
- no D1-specific alternative palette or independent glassmorphism values;
- patient-facing public entry, activation and home all render inside the Patient Companion themed surface.

## 8. Final AFTER evidence and human validation

Final exact-head visual proof:

- workflow: `Patient Companion D1 AFTER` run `34999967279` — **SUCCESS**;
- exact product/capture HEAD: `26806bfc93f1ef59845002467fab45aa00a5d171`;
- artifact id: `10408724608`;
- artifact digest: `sha256:c9e349e0a7f2324a9608f26b23f867c0fcbaaf8e853a5b30fd85c9efd46eca51`;
- states: `public-entry`, `home`, `activation`;
- viewports: `390x844`, `768x1024`, `1280x900`;
- 9/9 captures valid;
- HTTP 200 on all captures;
- zero page errors;
- zero console errors;
- zero unexpected external egress;
- zero horizontal overflow on all 9 captures;
- public-entry confirmed patient-facing, with no staff navigation and no dentist marketing hero;
- native Patient Companion theme tokens loaded by the final visual harness;
- owner human visual validation: **ACCEPTED 2026-09-15**;
- PR label `ui-human-visual-approved` applied only after that exact-head validation.

Visual assessment after final patient-facing correction: **9.2/10**. This is a visual score only, not a production-readiness claim.

## 9. Exact-head PR proof

Certified candidate: `26806bfc93f1ef59845002467fab45aa00a5d171`.

Observed exact-head evidence before merge:

- `Patient Companion D1 AFTER` run `34999967279`: **SUCCESS**;
- general CI run `34999973162` / CI `#4393`: **SUCCESS**;
- Cabinet Upgrade PostgreSQL Certification `34999973302` / `#791`: **SUCCESS**;
- Mobile SuperAdmin MOB-5H `34999973202` / `#103`: **SUCCESS**;
- Patient UX1-C Overlay Visual `34999973190` / `#133`: **SUCCESS**;
- Media C4 Visual `34999973220` / `#70`: **SUCCESS**;
- Catalog Connected Truth `34999973268` / `#1286`: **SUCCESS**;
- T2 Runtime Browser `34999973185` / `#3276`: **SUCCESS**;
- Patient P7 Final `34999973243` / `#1683`: **SUCCESS**;
- Marketplace Final Certification `34999973277` / `#261`: **SUCCESS**;
- M6-I Biometric Passkey was skipped as expected;
- PR #512 was mergeable, non-draft, with no blocking comments/reviews/threads observed before merge.

Reproducibility controls retained:

- Firebase pinned `12.19.0`;
- `@testing-library/dom` pinned `10.4.1`;
- `react-is` declared explicitly for frontend runtime reproducibility;
- frontend lockfile synchronized;
- D1 frontend/visual gates use `npm ci --legacy-peer-deps`;
- temporary repair helpers removed.

## 10. Merge and post-merge proof

PR `#512 — Patient Companion D1: secure patient UI and native theme` was squash-merged with expected-head protection.

- certified PR head: `26806bfc93f1ef59845002467fab45aa00a5d171`;
- squash merge commit: `0895296867fa1b27ecbccd77ffcb8614ef83e04f`;
- `master` verified on that merge SHA after merge;
- merge commit signature: verified;
- post-merge CI run `35003086120` / CI `#4404`, attempt 2: **SUCCESS**;
- post-merge frontend tests + build: **SUCCESS**;
- post-merge production negative guard: **SUCCESS**;
- post-merge backend regression including DB / patients / documents: **3541 passed / 10 skipped / 4 warnings**;
- the first attempt of #4404 was cancelled after its substantive test steps had succeeded; only the cancelled job was rerun, and attempt 2 completed successfully.

This is the final non-regression proof for D1 closeout.

## 11. D1 non-goals

No appointment create/edit/cancel, no clinical decisions, no implicit document/media access, no byte download endpoint, no remote/home gateway, no employee delegation, no second business model/store, no destructive migration, no Vercel deployment.

## 12. Closure decision

**D1 = CLOSED.**

Closure basis:

- bounded scope implemented;
- D0 security boundary preserved;
- exact-head functional and visual certification obtained;
- human visual validation obtained on the final exact head;
- proportional non-regression checks green;
- PR merged with exact expected head;
- post-merge CI green on the exact merge SHA;
- canonical and roadmap reconciled with final evidence.

No Vercel deployment was performed or authorised.

## 13. Next exact

Do not reopen D1 unless a demonstrated regression or new bounded scope requires it.

Next product work is either:

- define and bound `D1+` patient workflows without weakening D0/D1 isolation; or
- proceed to Lot E `Connect Hub` and first run an anti-duplication audit against the existing notification/push/preferences infrastructure.
