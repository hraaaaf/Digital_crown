# Digital Crown — Patient Companion D2 Handover

Status: **READY FOR NEW CONVERSATION — SCOPE GATE**

Repository: `hraaaaf/Digital_crown`
Prepared: `2026-09-15`
Master verified when this handover was prepared: `497e56738166c2a4344858a5251a487a17e54f2f`
Canonical roadmap: `docs/audits/COMPETITIVE_ROADMAP_POST_MEDIA.md`
Predecessors:
- `docs/audits/PATIENT_COMPANION_D0.md`
- `docs/audits/PATIENT_COMPANION_D1.md`

> Restart rule: in a new conversation, read this file first, then re-check current `master`, branch/PR state and exact CI before acting. Never assume the SHA above is still current.

## 1. Grand chantier state at handover

Verified roadmap state:

- Lot C — Media Core: **CLOSED — 100%**.
- Lot D0 — Patient Companion identity / authorization foundation: **CLOSED**.
- Lot D1 — Patient Companion patient UI + minimum useful shell: **CLOSED**.
- Lot D2 — next Patient Companion operational lot: **SCOPE GATE / NOT STARTED**.
- Lot E — Connect Hub: **NOT STARTED**.
- Lot F — Ortho Journey: **NOT STARTED**.
- Lot G — Assurance Maroc: **NOT STARTED — research gate**.
- Lot H — Lab / Prosthesis Collaboration: **NOT STARTED**.
- Lot I — BI / Recall / Outcomes: **NOT STARTED**.

The roadmap previously called the next bounded Patient Companion work `D1+`. For restart purposes, the user has chosen the name **D2**. This handover treats `D2` as that next bounded Patient Companion lot; it does not silently redefine any other roadmap lot.

No honest global percentage is recorded because the roadmap has no canonical weighting across C/D/E/F/G/H/I. Do not invent one. Report closed/not-started state unless a weighting method is explicitly adopted.

## 2. Certified predecessor — D0

D0 is the security/business boundary D2 must inherit, not rewrite.

Evidence recorded in the canonical roadmap:

- PR `#490` merged;
- certified PR head: `e57fa6f8aed2be1b6f47baad3976586ff3c603c4`;
- squash merge: `f61103ee971bd6e64317d8fc0bc759246fa2fd57`;
- post-merge CI `#4243` / run `34943083332`: **SUCCESS**.

D0 provides:

- separate Firebase patient principal;
- recipient-bound QR/manual activation;
- single-use/replay protection;
- tenant + patient authorization;
- many-to-many guardian/family access;
- safe appointment read projection;
- explicit document/media share allow-list;
- access/share revocation and auditing;
- owning-cabinet licence gate;
- cabinet administration restricted by `require_companion_admin`;
- no duplicate Patient/Appointment/Document/Media stores.

## 3. Certified predecessor — D1

D1 is **CLOSED**.

Final product evidence:

- PR `#512` merged;
- certified candidate HEAD: `26806bfc93f1ef59845002467fab45aa00a5d171`;
- exact-head CI `#4393` / run `34999973162`: **SUCCESS**;
- final AFTER run `34999967279`: **SUCCESS**;
- visual artifact `10408724608`;
- artifact digest `sha256:c9e349e0a7f2324a9608f26b23f867c0fcbaaf8e853a5b30fd85c9efd46eca51`;
- 9/9 valid captures for `public-entry`, `home`, `activation` at 390x844 / 768x1024 / 1280x900;
- zero D1 horizontal overflow, page errors, console errors or unexpected external egress;
- human visual validation accepted on `2026-09-15` for the exact candidate;
- squash merge: `0895296867fa1b27ecbccd77ffcb8614ef83e04f`;
- post-merge CI `#4404` / run `35003086120`, attempt 2: **SUCCESS**;
- post-merge backend regression: **3541 passed / 10 skipped / 4 warnings**;
- post-merge frontend tests + build: **SUCCESS**;
- production negative guard: **SUCCESS**;
- canonical/roadmap closeout HEAD: `497e56738166c2a4344858a5251a487a17e54f2f`;
- final closeout CI `#4419` / run `35013527308`: **SUCCESS**.

D1 patient surface currently supports:

- public patient entry independent from staff authentication;
- dedicated Firebase Web Auth;
- isolated patient transport using `Authorization: Firebase <ID_TOKEN>` and `credentials: 'omit'`;
- activation with QR secret kept memory-only and manual-code path;
- `/me` as the source of linked patient contexts;
- explicit context selection when several contexts exist;
- future appointments read-only;
- explicitly shared document/media metadata only;
- fail-closed revoked/invalid access behavior;
- no cabinet sidebar / staff session reuse / byte-serving fallback;
- existing Digital Crown theme tokens only.

## 4. D2 anti-duplication audit already performed

Backend source checked on the verified master:

- `backend/routers/patient_companion.py`
- `backend/routers/patient_companion_activation.py`
- `backend/routers/patient_companion_shares.py`

Verified existing capabilities:

1. `/me` returns safe linked patient contexts.
2. `/contexts/{access_id}/appointments` exposes future non-cancelled appointments read-only.
3. Cabinet admin backend can create recipient-bound invitations.
4. New live invitations invalidate previous pending invitations for the same patient.
5. Activation is single-use and checks the verified Firebase recipient plus cabinet licence.
6. Cabinet admin backend can explicitly share/revoke existing document/media metadata.
7. Patient share endpoint returns metadata only, not bytes.
8. Cabinet admin backend can revoke Patient Companion access.
9. Tenant / patient / licence / revocation checks are already enforced server-side.

Frontend search on master found **no consumption of `patient-companion/admin/*` routes**. Therefore the clearest non-duplicative D2 opportunity is to expose the already-certified D0 cabinet administration capabilities in the staff UI rather than create a new backend business engine.

This audit does **not** authorize appointment mutation, remote document download, employee delegation or a second messaging engine.

## 5. Recommended D2 scope

### Goal

Make Patient Companion operational from the cabinet UI by exposing the existing certified D0 administration capabilities, without adding a second source of truth or weakening D0/D1 isolation.

### Recommended bounded flow

`Patient record -> Patient Companion panel -> access status -> create/reissue invitation -> QR/manual handoff -> explicit document/media share/revoke -> revoke Companion access`

### Success criteria

D2 is successful only if observable proof shows:

1. An authorized cabinet principal can open a Patient Companion administration surface from the existing staff workflow without creating a duplicate patient record/workspace.
2. Access status is derived from existing Patient Companion backend state, not a parallel frontend store.
3. Invitation creation/reissue calls the existing D0 admin endpoint and does not persist the raw secret beyond the minimum UI handoff lifetime.
4. QR/manual activation material is displayed deliberately and is not written to localStorage, cabinet patient notes, logs, analytics or unrelated document stores.
5. Existing Document/Media entities can be explicitly shared and revoked using the existing allow-list endpoints.
6. The UI never implies that sharing grants raw-byte access; D1 remains metadata-only.
7. Full Patient Companion access can be revoked using the existing audited backend endpoint.
8. Unauthorized employee roles fail closed according to the current backend `require_companion_admin` contract; frontend hiding is not treated as authorization.
9. No direct appointment create/reschedule/cancel mutation is introduced.
10. No second Patient/Appointment/Document/Media model or dual-write is introduced.
11. D1 patient authentication, transport and patient-visible behavior remain unchanged unless a separately justified D2 requirement needs a change.
12. Existing DB, patient data, documents, cabinet auth, mobile/PWA and validated routes remain compatible.
13. If the staff UI changes visually, BEFORE and AFTER evidence exists at the exact agreed viewports with no new overflow/runtime errors and owner visual validation before merge.

### Proof required

- focused frontend tests for D2 admin surface;
- transport tests proving the intended existing admin endpoints are used;
- role/fail-closed behavior tests;
- raw invitation secret non-persistence test;
- D0 Patient Companion backend security/runtime tests rerun;
- proportional full regression covering DB / patients / documents;
- visual BEFORE -> Goal -> reference/mockup -> implementation -> AFTER same viewports -> comparison/tests -> visual score -> human validation;
- exact-head CI;
- PR comments/reviews/threads/mergeability audit;
- merge only after explicit user approval;
- post-merge CI / behavior verification;
- D2 canonical closeout + roadmap update.

## 6. Explicit D2 non-goals

Unless separately scoped and approved, D2 must NOT add:

- direct patient appointment create / reschedule / cancel;
- appointment-request workflow that duplicates Connect Hub / notifications before an anti-dup audit;
- patient raw document/media byte download/open endpoint;
- remote/home cabinet gateway;
- second Patient / Appointment / Document / Media source of truth;
- implicit document/media sharing;
- clinical decisions or treatment-plan mutation from Patient Companion;
- assistant/employee delegation beyond the current backend authorization contract;
- new messaging/notification engine;
- destructive migration or artificial data backfill;
- Vercel deployment.

## 7. Strategic items deliberately deferred

These are valid future questions, but not part of the recommended first D2 slice:

- assistant delegation for invitation handling;
- appointment change/cancel **requests**;
- consent workflows;
- patient document byte delivery;
- messaging / reminders / two-way communication.

Before any of those, audit overlap with existing RBAC, Agenda, notifications/push/preferences, DocumentArchive and Media Core. Connect Hub is already a dedicated future roadmap lot, so D2 must not casually swallow it because humans enjoy scope creep when nobody is looking.

## 8. UI/UX execution contract

For any D2 visual change:

1. capture **BEFORE** from the current certified product;
2. write the exact D2 UI Goal;
3. lock a mockup/reference;
4. implement using existing Digital Crown design/theme tokens;
5. capture **AFTER** on the same viewports;
6. compare BEFORE/AFTER and run responsive/runtime tests;
7. assign a visual score with reasons;
8. obtain explicit owner visual validation for the exact candidate HEAD;
9. any subsequent UI-affecting commit invalidates that visual approval and requires recertification.

Do not create an independent D2 design system.

## 9. Safety / architecture invariants

Preserve throughout D2:

- local/on-premise product architecture;
- Firebase boundary already used for Patient Companion identity;
- no cabinet JWT reuse by the patient surface;
- no patient Firebase token reuse in the staff surface;
- no raw invitation secret persistence beyond deliberate short-lived handoff;
- no tenant/patient authorization inferred only from frontend state;
- backend remains final authority;
- all meaningful share/access revocations remain audited;
- current DB / patient / document compatibility is mandatory;
- no Vercel deployment without explicit authorization.

## 10. First actions in the new conversation

Execute in this order:

1. Read `docs/audits/PATIENT_COMPANION_D2_HANDOVER.md`.
2. Read `docs/audits/COMPETITIVE_ROADMAP_POST_MEDIA.md`, then D1 and D0 canonicals.
3. Re-check current `master`, active D2 branch/PR, divergence and CI. Do not trust the handover SHA as current truth.
4. Reconfirm the anti-dup audit against current code, especially staff patient-detail UI, RBAC, Agenda, DocumentArchive, Media Core and notification/push/preferences infrastructure.
5. Identify the smallest existing staff insertion point for a Patient Companion admin panel. Do not create a parallel staff workspace unless current architecture proves necessary.
6. Lock D2 Goal / Success / Proof / exclusions in the D2 canonical before implementation.
7. For UI work, capture BEFORE at the exact target viewports and produce the reference/mockup before code.
8. Implement the smallest cabinet-side operational slice using existing D0 APIs.
9. Test security, role gating, secret lifetime, non-regression and responsive behavior.
10. Produce AFTER evidence on the same viewports and request human visual approval for the exact candidate.
11. Run exact-head CI and PR audit.
12. Do **not** merge without explicit user approval.
13. After approved merge, verify post-merge CI, update canonical + roadmap and only then declare D2 CLOSED.

## 11. New-conversation starter prompt

Use the following prompt verbatim or near-verbatim:

> HANDOVER — Digital Crown / Patient Companion D2
>
> Repo: `hraaaaf/Digital_crown`
>
> Read first: `docs/audits/PATIENT_COMPANION_D2_HANDOVER.md`
> Then read: `docs/audits/COMPETITIVE_ROADMAP_POST_MEDIA.md`, `docs/audits/PATIENT_COMPANION_D1.md`, `docs/audits/PATIENT_COMPANION_D0.md`.
>
> D0 and D1 are CLOSED and certified. Do not reopen or rewrite their boundaries without demonstrated need.
>
> First verify current `master`, any D2 branch/PR and exact CI. The SHA recorded in the handover is historical evidence, not assumed current truth.
>
> Recommended D2 Goal: make Patient Companion operational from the existing cabinet UI by exposing already-certified D0 admin capabilities: access status, invitation create/reissue + short-lived QR/manual handoff, explicit existing Document/Media share/revoke, and full Companion access revoke. Reuse existing models and endpoints.
>
> Hard exclusions unless separately scoped: no direct appointment mutation, no patient bytes/download endpoint, no remote gateway, no second Patient/Appointment/Document/Media store, no employee delegation, no second messaging/notification engine, no Vercel deployment.
>
> Mandatory UI flow for visual changes: BEFORE -> written Goal -> mockup/reference -> implementation -> AFTER same viewports -> comparison/tests -> visual score -> my explicit visual validation on the exact candidate HEAD.
>
> Mandatory engineering flow: anti-dup audit -> bounded scope -> implementation -> focused/security/non-regression tests -> exact-head CI -> PR audit -> ask my approval before merge -> post-merge CI -> canonical/roadmap closeout.
>
> Start by verifying repository truth and finishing the anti-dup audit of the exact staff insertion point. Then execute autonomously until a real human gate is reached.

## 12. Closeout definition for D2

D2 is not CLOSED until all applicable items are proven:

1. anti-dup audit complete;
2. bounded scope + exclusions canonicalized;
3. implementation complete;
4. automated/security/isolation tests green;
5. UI certification + human approval if visual;
6. DB/patient/document non-regression proof green;
7. exact-head CI green;
8. PR discussions/mergeability audited;
9. explicit user merge approval obtained;
10. merge completed with expected-head protection;
11. post-merge CI/behavior verified;
12. D2 canonical + roadmap reconciled with exact evidence.

Until those proofs exist, use precise states such as `SCOPE GATE`, `IMPLEMENTED`, `READY FOR REVIEW`, or `POST-MERGE PENDING`; never call it CLOSED for decorative morale.