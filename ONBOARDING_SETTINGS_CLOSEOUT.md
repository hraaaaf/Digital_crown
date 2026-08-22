# Digital Crown — Onboarding ↔ Réglages — FINAL CLOSEOUT

Status: **CLOSED ✅ — 9/9 lots certified — 100 %**

Final certification HEAD: `86d7715c8aec922f4a2bc11a04a26d3e5f37f3b0`
Final CI: `32576110099` / #1630 — **SUCCESS**
PR: `#214`

## Goal

One coherent truth across:

`signup / trial activation → onboarding → backend / DB → Settings → consumers → reload / restart`

**Settings is the canonical configuration surface. Onboarding is its guided projection.**

## Canonical ownership

- `User` = account + practitioner identity.
- `CabinetConfig` = organization identity/configuration.
- `employer_id` = mono-organization membership boundary.
- owner ≠ actor ≠ signer.
- `User.inpe_professionnel` ≠ `CabinetConfig.inpe_etablissement`.
- legacy `CabinetConfig.inpe` remains ambiguous and is never auto-classified.
- `contacts_json` is canonical; `footer_phones` remains compatibility projection.

## Roadmap

- P0 Audit & Truth Map — CLOSED ✅
- P1 Canonical Data Model — CLOSED ✅
- P2 Onboarding Product Reconciliation — CLOSED ✅
- P3 Settings Reconciliation — CLOSED ✅
- P4 Backend / Persistence / Permissions — CLOSED ✅
- P5 Legacy Migration — CLOSED ✅
- P6 Consumer Reconciliation — CLOSED ✅
- P7 UX Certification — CLOSED ✅
- P8 Regression & Closeout — CLOSED ✅

## Key functional results

### Account entry
- frontend/backend password minimum aligned to 8 characters;
- classic signup no longer claims a cabinet was pre-created;
- trial creates a structure draft without duplicating practitioner identity.

### Onboarding
- 7 guided steps retained;
- desktop rail + compact mobile `Étape X / 7`;
- practitioner and organization fields share the Settings contract;
- professional and establishment INPE are separate;
- backend draft can rehydrate the wizard;
- persistence is two-phase: draft → optional uploads → `complete-setup`;
- only completion ACK sets `is_initialized=true`;
- theme preview is non-persistent until final ACK;
- QR semantics/defaults match Settings.

### Settings
- Profile visually separates `Praticien principal` / `Structure d’exercice`;
- one atomic `/clinics/me` transaction saves User + CabinetConfig;
- backend `settings` permission is enforced;
- permitted subaccounts may edit organization config but not principal practitioner identity;
- strict payloads, IF round-trip and custom specialty persistence are covered.

### Existing installations / legacy
- additive identity columns are startup-migrated idempotently;
- practitioner names backfill only when canonical target is empty;
- conflicts never overwrite;
- ambiguous legacy INPE is not guessed;
- legal-ID JSON, custom headers, contacts and footer are preserved without speculative migration.

### Financial/document consumers
- notes/devis resolve organization through the actor's employer;
- real actor remains separate from organization owner;
- installment preview uses employer config;
- final installment uses real `CabinetConfig`, never nonexistent `models.Clinic`;
- cross-tenant plan is rejected before rendering;
- installment renderer uses real organization/contact fields;
- archive uses the real `ArchiveService` / `DocumentArchive` contract;
- preview does not archive.

## UX proof

### BEFORE
P0 run `32560178433`:
- artifact `9472575193`;
- digest `sha256:4b80b57fd7d0dd5f33d98c04fbbb78cb5623b51056fef6df1227054e0cbefa95`;
- 70 captures, onboarding 7 steps + Settings 7 tabs × 1440/1024/768/430/390;
- 14 SetupWizard overflows at 430/390;
- measured `scrollWidth=569`.

### AFTER
P2 visual product proof `32575117173`:
- artifact `9476356608`;
- digest `sha256:89181d283afb4983df05f5988980572a7e31fb314668f3346ebfa26a3fa1c94e`;
- 35/35 captures = 7 steps × 1440/1024/768/430/390;
- zero overflow/runtime error.

Settings Profile proof `32575117272`:
- artifact `9476349963`;
- digest `sha256:2fcc4bd6977834d989e8803914e1b3de21bce34ee0e96f6aed29ebfd620b3a71`;
- 12/12 captures = ADMIN + SUPERADMIN × collapsed/advanced × 1440/768/390.

Exact-head visual/runtime gates remained green on the final certification lineage.

**Final visual score: 9.3/10.**

Non-blocking reserve: the Design step is vertically dense on 390 px, but has no horizontal overflow, guide overlap or blocked action.

## T1–T30 regression matrix

| ID | Invariant | Proof |
|---|---|---|
| T1 | fresh install | `test_clinic_setup_p4.py` |
| T2 | reload | T2 Runtime Browser |
| T3 | restart / existing install | identity migration wiring + startup hook |
| T4 | Settings edit → reload | `test_clinic_profile_p4.py` + store tests |
| T5 | GET/SAVE fail-closed | rollback/error tests + P0 gate |
| T6 | validation + Unicode FR/AR | setup/profile tests |
| T7 | permissions | access-control tests + RBAC visual gate |
| T8 | multi-user isolation | config/access/P6 tenant tests |
| T9 | consumer truth | P6 consumer tests |
| T10 | legacy | identity legacy migration tests |
| T11 | anonymous clinic create refused | clinic router tests |
| T12 | exact owner binding | clinic router tests |
| T13 | IF round-trip | config/router tests |
| T14 | custom specialty round-trip | clinic router tests |
| T15 | Settings payload whitelist | store + strict schema tests |
| T16 | subaccount without settings refused | access-control tests |
| T17 | explicitly allowed subaccount | access/profile tests |
| T18 | partial upload cannot claim completion | two-phase setup + P2 submit-order proof |
| T19 | init-status error cannot invent persisted setup | fail-closed contract/P0 gate |
| T20 | offline mutation cannot fake persisted success | API truth guard/P0 gate |
| T21 | subaccount docs use employer config | P6 accounting adapter tests |
| T22 | no `models.Clinic` installment fantasy | P6 runtime/static test |
| T23 | password frontend/backend identical | Account Entry + auth tests |
| T24 | classic/trial converge before onboarding | trial identity + setup tests |
| T25 | SetupWizard 390/430 no overflow | P2 35-view proof |
| T26 | onboarding fields map to canonical Settings | P2 contract/visual harness |
| T27 | onboarding → complete → Settings reload exact equality | `test_onboarding_settings_roundtrip_p8.py` |
| T28 | template/font/theme defaults identical | setup store + P2 contract |
| T29 | QR labels/types/destinations aligned | P2 + QR route tests |
| T30 | no theme persistence before final ACK | setup store + P2 submit-order proof |

## Final certification

- CI #1629 on P6 compatibility seam: backend/frontend/negative guard SUCCESS.
- P8 CI #1630 on `86d7715c...`: backend/frontend/negative guard SUCCESS.
- P0/P2/Profile/RBAC/Branding/Account Entry/T2 gates: SUCCESS on final certification lineage.
- PR remained mergeable during certification.

## Vercel

No deployment performed. No Vercel deployment is authorized or required for this closeout.
