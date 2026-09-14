# Digital Crown — Patient Companion D0

Status: **CLOSEOUT CANDIDATE — implementation certified on exact product HEAD; merge/post-merge still required**

Repository: `hraaaaf/Digital_crown`
PR: `#490`
Certified product candidate: `400348a8dde7c0f0e4902e657857146684c95fd1`
Base master for certification: `4cfa04d651a47fa0cc2c60482e5ff5729148fb86`

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
- No public storage URL and no document/media byte-serving endpoint was introduced in D0.

## Anti-duplication decisions

- Reuse canonical `Patient`.
- Reuse canonical `Appointment`.
- Reuse `DocumentArchive`.
- Reuse Media Core / `ClinicalAsset`.
- Do not expose `mobile_patient_cockpit.py` to patients.
- Do not create a second Patient Journey.
- Do not create patient cabinet `User` accounts.

## Security invariants proven

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

## Certified tests / CI

Exact product candidate: `400348a8dde7c0f0e4902e657857146684c95fd1`.

- CI #4023: **SUCCESS**.
- Backend suite: **3482 passed / 10 skipped / 4 warnings**.
- Cabinet Upgrade PostgreSQL #449: **SUCCESS**.
- Patient P7 #1519: **SUCCESS**.
- T2 Runtime Browser #2934: **SUCCESS**.
- M6-I biometric job: skipped as expected for this change.

The CI checkout resolved PR merge commit `ce2341556ba649f3d31d034f35f2d70563d565fb`, which merges the exact product candidate into `master@4cfa04d651a47fa0cc2c60482e5ff5729148fb86`.

## External security alignment

The implementation follows Firebase Admin server-side ID-token verification with revocation checking and OWASP principles for opaque, high-entropy, expiring, single-use tokens with server-side authorization state and no PII embedded in the token itself.

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

1. this documentation-only closeout commit passes exact-head CI;
2. PR #490 comments/reviews/threads are rechecked;
3. PR #490 is merged;
4. post-merge CI on `master` is green;
5. roadmap canonical records the merged evidence.

## Next exact

Certify this documentation closeout HEAD, merge PR #490 if all gates remain green, verify post-merge CI, then start D1 from current master with UI BEFORE evidence and the patient activation/onboarding flow.
