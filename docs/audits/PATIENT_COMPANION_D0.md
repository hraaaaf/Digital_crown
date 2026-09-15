# Digital Crown — Patient Companion D0

Status: **CLOSED — merged and post-merge certified**

Repository: `hraaaaf/Digital_crown`
PR: `#490` — MERGED
Certified PR head: `e57fa6f8aed2be1b6f47baad3976586ff3c603c4`
Squash merge / certified runtime master: `f61103ee971bd6e64317d8fc0bc759246fa2fd57`
Post-merge CI: `#4243` / run `34943083332` — **SUCCESS**

## Goal

Create the smallest secure patient-facing identity and access boundary without reusing cabinet staff identities or duplicating Patient Journey, appointments, documents or Media Core.

## Implemented boundary

- Dedicated Firebase patient credential verification with `check_revoked=True`.
- Patient authentication namespace is distinct from cabinet JWTs: `Authorization: Firebase <ID_TOKEN>`.
- `PatientCompanionIdentity` is not a cabinet `User`.
- Many-to-many `PatientCompanionAccess` supports SELF / PARENT / GUARDIAN / CAREGIVER.
- Invitation contains opaque random QR token plus manual code; neither secret is persisted in clear text.
- Invitation is bound to a verified Firebase email or E.164 phone recipient through an HMAC fingerprint only.
- A photographed/stolen QR used by a different Firebase identity is rejected and does not consume the invitation.
- Invitation consumption uses compare-and-set semantics to prevent replay even where row locking is unavailable or ignored.
- Every patient-facing read is constrained by identity + tenant (`employer_id`) + patient (`patient_id`).
- `/api/patient-companion/me` returns only bounded patient context.
- Future appointments are a read-only projection from canonical `Appointment` rows.
- Documents/media require explicit `PatientCompanionShareGrant`; ownership alone never makes them patient-visible.
- Document sharing reuses canonical document-type RBAC as defense in depth.
- Invitation/access/share revocation is implemented and audited.
- D0 administration is reserved to practice owner / admin; employee delegation is intentionally deferred.
- Firebase activation enforces the owning cabinet licence before any identity/access binding is created. Suspended, archived, unlicensed or expired owner state fails closed.
- No public storage URL and no document/media byte-serving endpoint was introduced in D0.

## Anti-duplication / non-regression decisions

- Reuse canonical `Patient`, `Appointment`, `DocumentArchive` and Media Core / `ClinicalAsset`.
- Do not expose `mobile_patient_cockpit.py` to patients.
- Do not create a second Patient Journey or patient cabinet `User` accounts.
- No existing Patient, Appointment or Document model is rewritten by D0.
- The only pre-existing application router changed functionally by D0 is `backend/routers/frontdesk.py`, to mount the isolated `/api/patient-companion/*` router.
- Final D0 PR overlay was 12 files after latest-master realignment; the concurrent Prescription C2 master change was verified disjoint before the final realignment.

## Security invariants covered by D0 tests

1. Staff bearer JWT is not accepted as patient authentication.
2. Invalid/revoked Firebase patient credential fails closed.
3. Wrong Firebase identity cannot consume an invitation addressed to another verified contact.
4. Invitation is single-use and replay is rejected.
5. Cross-tenant patient invitation is denied.
6. One patient identity cannot read another identity's patient context.
7. Parent/guardian identity can hold multiple explicitly granted patient accesses.
8. Revocation takes effect immediately.
9. Cross-patient media sharing is denied.
10. Staff document RBAC remains enforced before patient publication.
11. D0 administrative operations are owner/admin-only.
12. Patient Companion routes are mounted in the real FastAPI application.
13. Firebase activation with an inactive cabinet licence returns 403 before consuming the invitation or creating `PatientCompanionIdentity` / `PatientCompanionAccess`.

## Final certification evidence

- Final realigned PR head: `e57fa6f8aed2be1b6f47baad3976586ff3c603c4`.
- Exact-head CI #4220: **SUCCESS**, including full backend regression for DB / patients / documents.
- Exact-head backend result observed before merge: **3495 passed / 10 skipped**.
- Exact-head Cabinet Upgrade PostgreSQL #632: **SUCCESS**.
- Exact-head Patient P7 #1587: **SUCCESS**.
- Exact-head T2 Runtime Browser #3117: **SUCCESS**.
- M6-I #1917: skipped as expected / not applicable.
- Final PR audit: no blocking reviews, review threads or comments; PR mergeable before merge.
- PR #490 squash-merged with expected-head protection.
- Squash merge SHA: `f61103ee971bd6e64317d8fc0bc759246fa2fd57`.
- `master` was verified on that exact SHA after merge.
- Post-merge CI #4243 / run `34943083332`: **SUCCESS** on `f61103ee971bd6e64317d8fc0bc759246fa2fd57`.

## Explicit non-goals / remaining Lot D work

D0 does not implement patient-facing UI, remote secure gateway/relay, consent/acknowledgement UX, appointment mutation/self-booking, patient document/media byte delivery, employee delegation UI/RBAC, Connect Hub conversations, autonomous clinical decisions or Vercel deployment.

## UI status

No product UI changed in D0, therefore BEFORE/AFTER responsive certification was not applicable. It is mandatory for D1 patient-facing UI at 390×844, 768×1024 and 1280×900.

## Closeout

D0 is CLOSED. Its secure identity/authorization foundation is merged and post-merge certified. Any future regression must preserve the existing DB, patient data, documents, validated functionality and the D0 isolation invariants above.

## Next exact

Start D1 from current `master`: capture BEFORE evidence, write the D1 UI Goal, establish mockup/reference, then implement patient activation/onboarding UI and the minimum useful Patient Companion shell without weakening D0 security. No Vercel deployment without explicit authorization.
