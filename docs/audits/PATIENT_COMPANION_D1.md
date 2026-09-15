# Digital Crown — Patient Companion D1

Status: **READY FOR PR — implementation complete; visual evidence human-validated; exact-head PR CI / merge / post-merge pending**

Repository: `hraaaaf/Digital_crown`
Branch: `feat/patient-companion-d1-ui`
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

## 3. Certified BEFORE

Workflow: `Patient Companion D1 BEFORE` run `34948914354` — **SUCCESS**.
Artifact: `patient-companion-d1-before-exact-master`.
Product baseline: `3fd0fb6ed759cff527a4524b031e6c0ab537f5d3`.

Observed baseline at 390×844 / 768×1024 / 1280×900:

- HTTP 200 on all three captures;
- zero page errors;
- zero console errors;
- `Patient Companion` absent;
- `espace patient` absent;
- patient activation absent;
- legacy landing overflow already exists at 390 and 768 and is recorded as a D0 BEFORE defect, not as D1 behavior.

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

Current backend `require_companion_admin` reserves Patient Companion administration to the principal `ADMIN` / `DENTISTE` account without an employer parent (plus superadmin). Employee delegation, including assistant administration, remains a D1 non-goal and is not silently enabled.

## 7. UI reference and final theme rule

Patient Companion remains visually separate from the staff workspace and has no cabinet sidebar. Responsive contract:

- 390×844: stacked patient shell, activation/home readable without horizontal overflow;
- 768×1024: centered patient shell with stacked content;
- 1280×900: compact two-column appointments / shares home.

Final theme decision after human review:

- consume Digital Crown native tokens only: `--glass-bg`, `--glass-border`, `--shadow-glass`, theme blur and semantic background/text/border variables;
- no D1-specific alternative palette or independent glassmorphism values;
- public landing baseline remains outside the Patient Companion themed surface.

## 8. AFTER evidence and human validation

Final themed visual proof:

- workflow: `Patient Companion D1 AFTER` run `34969236348` — **SUCCESS**;
- exact product/capture HEAD: `e92dc5e9b2459c2737e3a72587c3266ff9045bca`;
- artifact id: `10397070398`;
- artifact digest: `sha256:3147a1604bb481e6e889d96b278b95d2713f045ddeda1030721e0f17da3549af`;
- states: `public-entry`, `home`, `activation`;
- viewports: `390x844`, `768x1024`, `1280x900`;
- 9/9 captures valid;
- HTTP 200 on all captures;
- zero page errors;
- zero console errors;
- zero unexpected external egress;
- no horizontal overflow on D1 patient states;
- known legacy public landing overflow remains baseline-only at 390/768;
- native Patient Companion theme stylesheet and `data-surface='patient-companion'` are loaded by the final visual harness;
- human visual validation: **ACCEPTED by owner on 2026-09-15**.

Visual assessment after native-theme correction: **9/10**. This is not a production-readiness score and does not replace PR/non-regression proof.

## 9. Focused implementation proof already obtained

Before final documentation closeout:

- focused `Patient Companion D1 check` previously succeeded on the functional D1 candidate;
- final themed AFTER run above succeeded;
- D0 backend security workflow exists to recertify the D0 boundary;
- frontend manifest pins Firebase `12.19.0` and `@testing-library/dom` `10.4.1`;
- one-shot lock synchronization run `34970452423` succeeded;
- `frontend/package-lock.json` is synchronized with the exact manifest;
- D1 frontend and visual workflows now install with `npm ci --legacy-peer-deps`;
- temporary repair/lock helper workflows have been removed.

Exact-head PR CI is still required before merge.

## 10. D1 non-goals

No appointment create/edit/cancel, no clinical decisions, no implicit document/media access, no byte download endpoint, no remote/home gateway, no employee delegation, no second business model/store, no destructive migration, no Vercel deployment.

## 11. Required proof before CLOSED

Still required:

- PR created from `feat/patient-companion-d1-ui` to `master`;
- exact-head focused frontend check with reproducible lockfile install;
- exact-head D0 backend security/runtime recertification;
- proportional non-regression CI covering DB/patients/documents as applicable;
- PR comments/reviews/mergeability checked;
- merge;
- post-merge CI / behavior verification;
- roadmap and this canonical updated with exact merge/post-merge evidence.

## 12. Next exact

Open the D1 PR against current `master`, run exact-head certification/non-regression CI, resolve any failure without weakening D0 boundaries, then merge only if all required proof is green. No Vercel deployment is authorised.
