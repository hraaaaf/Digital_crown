# Digital Crown — Patient Companion D1

Status: **IN PROGRESS — BEFORE certified; Goal/reference locked; implementation pending**

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
10. Revoked/invalid patient access fails closed and returns to an access-required state.
11. Existing DB, patient data, documents, cabinet auth, mobile PWA and validated product routes remain unchanged.
12. AFTER evidence is captured at exactly 390×844, 768×1024 and 1280×900 with no D1 horizontal overflow, page errors or console errors.

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

The baseline commit is two documentation-only commits after the D0 squash merge and does not alter the D0 product frontend.

## 4. Auth integration decision

D0 backend contract requires `Authorization: Firebase <ID_TOKEN>` and verifies Firebase tokens with revocation checking. The existing frontend shared `api` client automatically injects cabinet `Bearer` tokens and therefore **must not** be reused by Patient Companion.

D1 integration rule:

- dedicated Firebase Web Auth client;
- Firebase session managed by Firebase, not by Digital Crown cabinet token storage;
- dedicated Patient Companion fetch transport;
- `credentials: 'omit'` for Patient Companion API calls;
- explicit `Authorization: Firebase <fresh ID_TOKEN>` header only;
- no read/write of `token` or `refresh_token` cabinet keys;
- fail-closed UI when Firebase configuration is unavailable.

D1 initially supports the minimum verified-contact path required for useful activation: verified Firebase email identity. Phone-bound invitations remain a D0 backend capability and are not weakened or emulated by D1; no fake phone verification is introduced.

## 5. UI reference / mockup contract

Visual direction: preserve Digital Crown medical-blue identity while making Patient Companion visibly separate from the staff application. Patient surfaces use a quiet light background, white cards, large touch targets, restrained status chips and no cabinet sidebar.

### 390×844

```text
┌──────────────────────────────────┐
│ crown  Patient Companion    aide │
├──────────────────────────────────┤
│ Bonjour / Accès patient          │
│ Texte court, rassurant           │
│                                  │
│ [ Connexion / création Firebase ]│
│ or                               │
│ [ Code d'activation  ____ ]      │
│ [ Activer mon espace ]           │
│                                  │
│ After activation/auth:           │
│ [ Contexte patient ▾ ]           │
│ [ Prochain rendez-vous ]         │
│ [ Documents partagés ]           │
│ [ Médias partagés ]              │
│                                  │
│        Déconnexion               │
└──────────────────────────────────┘
```

### 768×1024

Single centered shell, maximum readable width. Context selector above two stacked data sections. Appointment and share cards remain full-width touch targets. No horizontal overflow.

### 1280×900

Centered patient shell with a compact two-column content area after authentication:

```text
┌ header / patient identity / context switcher ┐
│                                               │
│  Prochains rendez-vous   |  Partages          │
│  read-only list          |  docs/media metadata│
│                                               │
└───────────────────────────────────────────────┘
```

### State reference

- **config unavailable**: explicit unavailable state, no bypass;
- **signed out**: email/password sign-in + account creation entry;
- **email not verified**: verification-required state; activation disabled;
- **authenticated but no access**: manual activation input and optional QR token prefill from URL;
- **one context**: select automatically;
- **multiple contexts**: explicit selector, first context may be suggested but must be visibly switchable;
- **loading**: bounded skeleton/spinner, never cabinet loader copy;
- **revoked/403**: access unavailable state, clear local selected context, keep Firebase identity only until user signs out;
- **empty appointments/shares**: truthful empty state, not synthetic examples.

## 6. D1 non-goals

No appointment create/edit/cancel, no clinical decisions, no implicit document/media access, no byte download endpoint, no remote/home gateway, no employee delegation, no second business model/store, no migration, no Vercel deployment.

## 7. Required proof before closeout

- focused frontend tests for patient auth/header isolation, context selection and read-only rendering;
- existing frontend test suite + build;
- D0 backend security/runtime tests;
- proportional full non-regression CI covering DB/patients/documents;
- AFTER screenshots at the exact BEFORE viewports;
- BEFORE/AFTER comparison and visual score;
- exact-head PR CI;
- merge + post-merge verification;
- roadmap + this canonical updated with exact evidence.

## 8. Next exact

Implement the dedicated Firebase patient auth adapter, isolated Patient Companion API transport, public patient routes and minimal responsive shell exactly within the locked reference above. Then run focused tests/build and produce AFTER evidence on the same three viewports.
