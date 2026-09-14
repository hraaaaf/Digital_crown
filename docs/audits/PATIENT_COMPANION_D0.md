# Digital Crown — Patient Companion D0

Status: ACTIVE — architecture / anti-dup boundary only

Baseline audited: `master@1ce5bc8a6297c89e9b69a8b455ada576d374a6fc`

## 1. Goal

Define the smallest secure patient-facing boundary before any Patient Companion behavior is added.

Success means:
- a patient-facing identity is never represented as a cabinet `User`;
- every patient-facing read/write is constrained by both cabinet (`employer_id`) and patient (`patient_id`);
- existing Patient Journey, Media Core, appointments and document records are reused rather than duplicated;
- no authentication provider or trust claim is invented from repository state;
- implementation can proceed only from an explicit, testable patient identity contract.

Proof for D0:
- current-master anti-dup audit;
- auth/data access matrix below;
- explicit security invariants and exclusions;
- implementation/test plan bounded to missing primitives.

## 2. Verified current primitives

### 2.1 Cabinet identity is staff identity, not patient identity

`backend/models.py` defines `User` for cabinet actors with roles `ADMIN`, `DENTISTE`, `SECRETAIRE`, permissions and an `employer_id` hierarchy. `User.get_employer_id()` resolves the cabinet tenant.

`backend/routers/auth.py` currently authenticates cabinet actors through local email/password plus Digital Crown JWT/cookies (`access` / `mobile`). It does not define a patient principal.

Consequence: Patient Companion MUST NOT create a patient as a `User` merely to reuse staff authentication.

### 2.2 Patient records are already tenant-scoped

`models.Patient` has mandatory `employer_id`; `numero_dossier` uniqueness is scoped by `(numero_dossier, employer_id)`.

Consequence: patient-facing access can and must use an explicit `(employer_id, patient_id)` scope.

### 2.3 Existing mobile Patient Cockpit is staff-facing

`backend/routers/mobile_patient_cockpit.py` depends on `get_mobile_user` / `require_mobile_permission('patients')`, checks staff permissions and can expose finance/medical context according to staff rights.

It is therefore an internal practitioner/staff cockpit, not a patient portal. It must not be exposed directly to a patient principal.

### 2.4 Appointments are reusable data

`models.Appointment` already links `patient_id` and `employer_id`; the existing Patient Cockpit demonstrates a tenant + patient constrained query for the next appointment.

Patient Companion should project a safe patient-visible subset from this canonical record. It must not create a second appointment store.

### 2.5 Media Core is reusable storage, not a patient authorization surface

`backend/routers/media_core.py` uses staff `get_current_user`, requires the `patients` permission, calls `assert_patient_access`, and the service queries are scoped by `employer_id + patient_id + asset_id`.

The storage/model layer can be reused. The current HTTP router cannot be reused as a patient endpoint because its principal is a cabinet `User`.

### 2.6 Documents are canonical cabinet records

`models.Patient.documents` already points to `DocumentArchive`. Existing staff/mobile code reads `DocumentArchive` in patient context and applies document-type permissions.

Patient Companion must expose only an explicit patient-shareable projection. Absence of a patient-share policy means deny by default.

## 3. Contradiction discovered: authentication source

The project architecture context describes Firebase as the external authentication/licence boundary, but the audited `master` contains active local cabinet email/password + JWT authentication in `backend/routers/auth.py`, and no patient/Firebase principal was demonstrated by this D0 audit.

This is a security-significant contradiction. D0 therefore does **not** assume that a Firebase token, local cabinet JWT, email address, phone number, or Patient row is sufficient proof of patient identity.

Resolution rule: before patient login/token verification is implemented, the chosen patient identity provider and token-verification contract must be explicit and testable. Until then, all patient-facing endpoints remain absent / fail closed.

## 4. Required patient principal contract

The backend patient-facing dependency should resolve a principal with exactly these authoritative fields:

- `subject`: immutable identity-provider subject, never an email/phone as primary key;
- `employer_id`: cabinet tenant id;
- `patient_id`: canonical `patients.id`;
- `session_id` or equivalent replay/revocation handle when supported;
- `issued_at` / `expires_at` where provided by the credential.

No role/permission inheritance from `models.User` is allowed.

A patient principal is valid only when a server-side active binding exists for the exact tuple `(provider, subject, employer_id, patient_id)` and the referenced Patient is active and belongs to that `employer_id`.

## 5. Authorization matrix

| Resource / action | Staff contract today | Patient Companion contract | D0 decision |
| --- | --- | --- | --- |
| Patient identity/profile | `User` + patient permission | own `(employer_id, patient_id)` only | new patient principal required |
| Appointments | staff agenda/patient scope | own safe projection only | reuse `Appointment` |
| Patient Journey | internal staff projection | selected patient-visible milestones only | reuse, no duplicate journey |
| Documents | staff document permissions | explicitly shareable documents only | deny by default until share state exists |
| Media | staff `patients` permission + `assert_patient_access` | explicitly shareable assets only | reuse Media Core storage/service, separate patient auth surface |
| Finance | staff accounting/payments permission | out of D0 | no patient exposure |
| Medical alerts/notes | staff patient permission | out of D0 unless separately approved | no patient exposure |
| Appointment mutation | staff/frontdesk workflows | out of D0 | no mutation |
| Consent/acknowledgement | no patient principal demonstrated | own acknowledgements only | missing primitive, later D sublot |

## 6. Security invariants

1. Deny by default.
2. Every query includes both `employer_id` and `patient_id`; never authorize by `patient_id` alone.
3. Cross-tenant and cross-patient mismatches return a non-enumerating denial (prefer 404 after authenticated principal resolution where practical).
4. Patient principal cannot call staff routers by satisfying `get_current_user`.
5. Staff JWT/mobile tokens cannot be silently accepted as patient credentials.
6. No email/phone/date-of-birth matching is authentication.
7. Documents/media are not patient-visible merely because they belong to the same Patient row.
8. No public/unscoped storage URL is introduced.
9. Mutations are separately allowlisted and audited; read access never implies write access.
10. No clinical recommendation/autonomous decision is introduced by Patient Companion.

## 7. Missing primitives proven by the audit

### D0-A — Patient identity binding
Missing: a dedicated server-side binding between external patient identity subject and canonical `(employer_id, patient_id)`.

### D0-B — Patient principal dependency
Missing: a dependency that verifies the patient credential and resolves only the bounded patient principal, distinct from staff `get_current_user`.

### D0-C — Patient share state
Missing for documents/media: an explicit patient-share/visibility state. Ownership by a Patient record is not enough.

### D0-D — Negative isolation certification
Missing: dedicated tests proving one patient cannot read another patient or another cabinet by changing URL ids, resource ids or token claims.

## 8. Minimal implementation sequence

1. Resolve the patient identity-provider/token-verification contract; do not infer it from staff auth.
2. Add the smallest patient-identity binding model/migration with uniqueness and tenant/patient foreign-key constraints.
3. Add patient-principal verification dependency, isolated from `get_current_user`.
4. Add read-only `/api/patient-companion/me` returning only non-sensitive identity/profile metadata required by the UI.
5. Add appointment read projection constrained by principal scope.
6. Add explicit document/media share state before exposing either category.
7. Add negative cross-patient/cross-tenant/replay/revocation tests proportional to the chosen provider.
8. Only then start patient-facing UI work with mandatory BEFORE → Goal → mockup/reference → implementation → AFTER at 390×844, 768×1024 and 1280×900 → comparison/tests → visual score.

## 9. Explicit non-goals for D0

- no Patient Journey replacement;
- no Media Core replacement or dual-write;
- no staff Patient Cockpit exposure to patients;
- no finance/medical-note exposure;
- no appointment mutation;
- no password/authentication system invented inside Digital Crown;
- no Vercel deployment.

## 10. D0 implementation gate

Independent architecture work is complete enough to identify the first implementation dependency: **the patient identity credential verifier/provider is not demonstrated by current repository state**.

Because this controls authentication of health data, implementation of D0-A/D0-B must not guess the provider. The safe next step is to reconcile the intended Firebase boundary with the current local staff-auth code, then implement the binding/principal against the verified patient credential contract.
