# Digital Crown — V1-07 Global Interactive Audit — G1

Status: **IN PROGRESS — exact-head CI required before certification**

## Goal
Verify the interactive behavior of V1 shell, navigation, authentication, registration, trial activation and onboarding surfaces.

## Success
- public/auth/onboarding actions execute their intended business result;
- refusal/error paths never render false success;
- permission-gated shell controls are hidden when unauthorized;
- shared navigation controls target canonical routes;
- critical mutations are covered by behavioral tests;
- exact-head frontend test/build is green.

## Added behavioral evidence
- `LoginPage.g1Interactive.test.tsx`
- `RegisterPage.g1Interactive.test.tsx`
- `LandingPage.g1Interactive.test.tsx`
- `ActivateTrialPage.g1Interactive.test.tsx`
- `PublicNavigation.g1Interactive.test.tsx`
- `SetupWizard.g1Interactive.test.tsx`
- `OnboardingScanner.g1Interactive.test.tsx`
- `Sidebar.g1Interactive.test.tsx`
- `Header.g1Interactive.test.tsx`
- `Layout/MainLayout.g1Interactive.test.tsx`

## Behavior matrix
### Authentication
Login success, backend refusal, Google start/callback success/failure, locked-license recheck success/402, logout and register navigation.

### Registration
Required legal consents, exact register payload, pending-validation success state, backend refusal without false success, invitation prefill, return to login.

### Trial activation
Code preview/prefill, exact activation payload, activation success, preview failure and activation refusal.

### Public landing/download/legal
Demo request no-op while incomplete, exact request on success, refusal without false success, canonical login/register/download/activate/mobile/legal links. The public hero geography defect (“dentistes algériens”) is remediated to “dentistes marocains” and covered behaviorally by `LandingPage.g1Interactive.test.tsx`; visual certification is delegated to the shared `landing-geography` BEFORE/AFTER scenario and remains pending until exact-head evidence is green.

### Cabinet setup
Step-1 validation, progression, backend-first finalization, persistent theme only after ACK, no reset/navigation on failure, explicit Quitter route.

### Mobile onboarding
Six-digit manual code gating, known/fallback bridge routing, derived-key credential persistence, true pairing success, backend refusal + retry, plaintext master-key rejection.

### Shared shell
Cabinet switch, permission-gated navigation, SuperAdmin visibility, patient dossier subnav, mobile drawer close, attention center, logout confirmation, CrownBot controls, patient intelligence exact id, practitioner context routing.

## Gate
Do **not** mark G1 certified until the current PR HEAD has a green CI frontend test/build and the `landing-geography` matched BEFORE/AFTER evidence is green. If any new test fails, diagnose and fix before continuing to G2.

No Vercel deployment. V1-08 remains blocked.


## Landing geography truth
A public product-truth defect was verified: the Landing hero said “dentistes algériens” while Digital Crown targets Morocco/MAD.

Remediation:
- copy changed to “dentistes marocains” in the same hero location;
- `LandingPage.g1Interactive.test.tsx` asserts Morocco wording and absence of Algeria wording;
- `landing-geography` was added to the matched BEFORE/AFTER truth-safety visual workflow.

Status: CODE REMEDIATED — CERTIFICATION PENDING matched visual evidence + exact-head tests/build.


## Browser escalation
G1 also requires real Chromium proof: landing/auth/register/trial/setup/onboarding/navigation controls must be inventoried and action-tested with success/refusal/navigation truth. Component tests and visual evidence remain supporting proof, not the final interaction certificate.


## Deep interaction reconciliation — public/auth/mobile

The browser gate now requires both refusal truth and success ACK for critical public/auth controls where an isolated deterministic success contract is available.

### Landing demo request
- refusal must not render success;
- success HTTP ACK must render `Demande envoyée !`.

### Registration
- both legal consents remain mandatory before enablement;
- refusal must preserve an error/no false success;
- success ACK must render `Demande Envoyée`.

### Trial activation
- preview truth is required;
- refused activation must not render success;
- successful activation ACK must render the backend success message.

### Login
- refusal must not navigate;
- real isolated-runtime credential success must navigate to Dashboard.

### Mobile pairing
Success proof is not mocked around the security boundary.

The G1 isolated workflow now provides a test-only `CABINET_MASTER_KEY_HEX`; the browser gate:
1. authenticates the real T2 owner;
2. calls the real `/api/mobile/bridge-pairing` endpoint for an Agenda destination;
3. receives a real six-digit one-shot code;
4. submits that code through the actual Onboarding UI;
5. executes the real client secp256r1 ECDH handshake;
6. accepts only the server ECDH + AES-GCM encrypted master-key response;
7. reaches visible `Appairage réussi`;
8. resolves the server bridge destination and navigates to `/mobile/dashboard?tab=agenda`.

The existing refusal path remains mandatory as a separate non-false-success proof.
