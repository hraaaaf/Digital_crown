# Patient Companion — PC-00 Shell & Activation

Status: APPROVED / IMPLEMENTATION START

## Goal

Deliver the patient-facing shell that exposes the already-merged Patient Companion security boundary without duplicating the clinical record.

## Success

A Firebase-authenticated invited patient can:
1. open the Patient Companion entry point;
2. activate exactly one invitation by QR token or manual code;
3. resolve only the patient contexts authorized to that Firebase identity;
4. enter a mobile-first home shell for the selected context;
5. recover safely from invalid, expired, revoked, offline, and unauthenticated states.

No self-service scheduling, questionnaire, payment, remote signature, chat, video consultation, or emergency-photo workflow is introduced in PC-00.

## Existing backend reused

- `POST /patient-companion/activate`
- `GET /patient-companion/me`
- invitation QR/manual code issued by staff UI
- Firebase patient identity verification
- SELF / PARENT / GUARDIAN / CAREGIVER access
- tenant-scoped access + revocation

## UI target before implementation

Mobile-first PWA flow:

`Welcome / Firebase identity` → `Activate invitation` → `Context picker when >1` → `Companion Home shell`

### Welcome
- Digital Crown / Patient Companion identity.
- Explicit patient-facing wording; no staff navigation.
- Primary action: continue with verified identity.
- Secondary activation entry for manual code.
- Safe-area aware, 360×800 and 390×844 baseline viewports.

### Activation
- QR/deep-link token when supplied.
- Manual code fallback.
- Loading, expired, invalid, recipient mismatch and already-consumed states.
- Never persist/display the invitation secret after successful activation.

### Context picker
- Shown only when the identity owns more than one active context.
- Patient name + relationship label only.
- No clinical data in the picker.

### Home shell
- Patient identity/context header.
- Empty navigation slots reserved for PC-01 resources and appointments.
- Sign-out / switch-context affordance.
- No fake data and no disabled controls presented as working features.

## Security invariants

- Firebase credential remains the authentication source.
- No cabinet JWT is exposed to the patient shell.
- No patient numeric identifier in public URLs.
- Access is derived from server-returned opaque `access_id`.
- Revoked access fails closed.
- No invitation secret in logs, analytics, local storage, or post-activation UI.
- No clinical mutation in PC-00.

## Required evidence

BEFORE:
- current V1 has staff-side Companion administration and patient APIs but no patient-facing route in the main frontend router.

AFTER:
- same 360×800 and 390×844 viewports for Welcome, Activation and Home;
- route/guard tests;
- activation state tests;
- revoked/invalid/offline tests;
- static secret-leak checks;
- existing Patient Companion backend tests remain green.

## Gate

PC-00 closes only with:
- code + tests;
- visual BEFORE/AFTER evidence;
- exact-head CI green;
- adversarial review;
- canonical documentation updated.

No Vercel deployment is authorized by this lot.
