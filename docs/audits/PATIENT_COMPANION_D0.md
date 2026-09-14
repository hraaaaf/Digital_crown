# Digital Crown — Patient Companion D0

Status: **CLOSEOUT HEAD CANDIDATE — realigned on latest master; exact-head certification, merge and post-merge still required**

Repository: `hraaaaf/Digital_crown`
PR: `#490`
Current runtime candidate before documentation closeout: `3119c316548d3b75c52dacd2a4e12cd9fe79a894`
Base master: `0aa34f39ca97fd3a220bc8a5d9d9ae3e5412c8`

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

- Reuse canonical `Patient`.
- Reuse canonical `Appointment`.
- Reuse `DocumentArchive`.
- Reuse Media Core / `ClinicalAsset`.
- Do not expose `mobile_patient_cockpit.py` to patients.
- Do not create a second Patient Journey.
- Do not create patient cabinet `User` accounts.
- No existing Patient, Appointment or Document model is rewritten by D0.
- Against `master@0aa34f39ca97fd3a220bc8a5d9d9ae3e5412c8`, PR #490 is restricted to 11 D0 files; prescription/cephalo work from master is not part of the PR diff.
- The only pre-existing application router changed functionally by D0 is `backend/routers/frontdesk.py`, to mount the isolated `/api/patient-companion/*` router.

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

## Evidence lineage

### Historical D0-specific candidate

Candidate `e5b841a9f22cee7d83573cb8479bd5835a728151` had:
- Cabinet Upgrade PostgreSQL #592: **SUCCESS**;
- Patient P7 #1557: **SUCCESS**;
- T2 Runtime Browser #3077: **SUCCESS**.

Those runs verify the D0-specific code before subsequent master realignments. They are retained as historical evidence only and are not final merge certification.

### Current realigned lineage

`3119c316548d3b75c52dacd2a4e12cd9fe79a894` is aligned with `master@0aa34f39ca97fd3a220bc8a5d9d9ae3e5412c8`. The master change since the preceding alignment was documentation-only in `PRESCRIPTION_INTELLIGENCE_V1.md`; the D0 overlay remains restricted to the same 11 Patient Companion files.

Verified structural facts at closeout preparation:
- PR #490 is open and mergeable;
- D0 overlay is restricted to 11 Patient Companion files, including the minimal frontdesk router composition;
- no prescription/cephalo implementation file is introduced by the PR diff;
- no PR reviews, review threads or comments were present in the pre-closeout audit.

Exact-head workflow gates are required for the documentation closeout HEAD. No pending/in-progress run is counted as success.

## Explicit non-goals / remaining Lot D work

D0 does not implement:
- patient-facing UI;
- remote secure gateway/relay for access outside the cabinet LAN;
- consent/acknowledgement UX;
- appointment mutation/self-booking;
- patient document/media byte delivery;
- employee delegation UI/RBAC for Companion administration;
- Connect Hub conversations;
- any autonomous clinical decision;
- any Vercel deployment.

## UI status

No product UI changed in D0, therefore BEFORE/AFTER responsive certification is not applicable to this sublot. It becomes mandatory for D1 patient-facing UI at 390×844, 768×1024 and 1280×900.

## Closeout gate

D0 is not CLOSED until:
1. the documentation closeout HEAD passes exact-head CI including full backend regression coverage for DB / patients / documents and all applicable current-master gates;
2. PR #490 comments/reviews/threads and mergeability are rechecked on that exact HEAD;
3. PR #490 is squash-merged with expected-HEAD protection;
4. post-merge CI on `master` is green;
5. the canonical roadmap records exact merge/post-merge evidence.

## Next exact

Certify the final documentation closeout HEAD of PR #490. If green, perform final PR audit, squash merge with expected HEAD protection, verify post-merge `master` CI, record exact closeout evidence, then start D1 from current master with mandatory UI BEFORE evidence.
