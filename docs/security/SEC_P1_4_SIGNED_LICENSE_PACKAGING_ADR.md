# SEC-P1.4 — ADR (proposal): publisher-signed licences and safe Windows packaging

**Status: PROPOSED / EXPERIMENTAL. Not an approved product change.**

**Branch:** experiment/sec-p1-4-signed-license-architecture (stacked on SEC-P1.3 #942).
**Decision owner:** Digital Crown product owner. **Gate:** explicit separate GO
before any runtime integration, key provisioning, merge, release or deployment.

## 1. Findings grounded in the repository

| Surface | Existing contract | Risk or constraint |
| --- | --- | --- |
| `backend/services/license_service.py` | Firebase `licenses` documents + locally Fernet-encrypted `license_vault.bin`, cabinet-local encryption secret and 72-hour offline grace; `active=None` represents unavailable cloud truth | A symmetric, locally encrypted cache is NOT a publisher-signed, non-forgeable licence. If the cabinet controls its local secret, it controls cache creation unless separately authenticated |
| `backend/main.py` | Middleware checks account and cabinet licence, rejects many mutations with 403 when unavailable/expired, while allowing read routes through; per-user cached results | Read-only behavior is a partial continuity contract, NOT proof every backup, export, imaging or patient view is accessible. Patient safety cannot depend on network validation |
| `backend/routers/license_portability_p4.py` | Recheck is authenticated, derives cabinet identity from `CabinetConfig` and preserves state when Firebase unavailable | Preserve canonical identity. Never let an unauthenticated client select a different cabinet to validate |
| `PORTABILITY_LAUNCHER_ROADMAP.md` P4 | Cabinet-portable data, machine-bound secrets and local vault excluded; 72h grace / clock rollback handling | Do not bind patient SQLCipher encryption keys to the publisher's commercial licence; restores must work with locally re-provisioned secrets |
| `DigitalCrown.spec` and `run.py` | Gate `INSTALLABLE_CERTIFIED` before packaged builds and verify frozen release identity | Never replace the installer with a toy Nuitka probe or remove attestations |
| `scripts/build_exe.py` | Legacy CLI builder that can add `backend/core/firebase_creds.json` if present; runs `npm install` rather than canonical `npm ci` and uses `backend/main.py` | **SECURITY BLOCKER for commercial release path** until disabled, removed or aligned with certified builder. The experiment does not edit it |
| SEC-P1.3 [PR #942](https://github.com/hraaaaf/Digital_crown/pull/942) | Non-installable Windows probe: PyInstaller 8/8 in 16.0s, 30.7MB, 0.847s startup; Nuitka 8/8 in 614.6s, 48.4MB, 0.601s startup | Not full app and **no anti-crack proof**; Nuitka lab downloaded Dependency Walker without independently pinned digest |

These findings are source-code claims, not a certification of what is installed
at any customer site. No actual customer's runtime/data was inspected.

## 2. Proposed decision (subject to owner approval)

**Keep PyInstaller/`DigitalCrown.spec` as the canonical packaging path for
now.** Do not upgrade to a Nuitka whole-backend executable on toy-probe
performance evidence. In parallel, add a **publisher-signed Ed25519 licence
envelope** behind a future opt-in integration flag and a **server-side issuer**
with no access from clinic binaries.

### Trust boundary

```text
Publisher control plane (private, least privilege)
  Licence issuance service → HSM/KMS-managed Ed25519 private key
     audit, approval, tenant/plan truth, revocation registry
                               |
                     signed short-lived lease
                               v
Clinic backend (untrusted/client-controlled)
  publisher PUBLIC verification key(s) + pin/version/channel
  signature / clinic / device / entitlement / lease / epoch checks
  locally encrypted cache (for availability, NOT authenticity)
  real API policy (server-side per route & authenticated tenant)
                               |
      commercial features only (degrade on invalid licence)
                               |
  separate patient records SQLCipher keys, backup/restore,
  emergency access and export (must remain recoverable)
```

**Private signing key NEVER** enters the repository (PUBLIC), EXE, build
artifacts, clinic server, logs, telemetry or downloadable client settings.
A public key in the EXE can verify signatures but cannot protect a hostile
client from patching executable code; license integrity is strong against
forged payloads in honest verifiers, **not cryptographic resistance against
client-controlled binaries**. Critical online entitlements can use a
publisher-hosted service where clinically safe.

Distinguish keys: release identity/provenance signing, publisher licence
signing, API authentication JWT, SQLCipher DB and cabinet backup keys MUST be
independently managed and domain separated. Do not reuse their private/public
identities interchangeably.

## 3. Envelope v1 and canonical verification

Experimental reference implementation:
`scripts/security/sec_p1_4_signed_license_reference.py` (no runtime import).
Test-only ephemeral signer:
`scripts/security/test_sec_p1_4_signed_license_reference.py`.

- Ed25519 signature over
  `DigitalCrown/licence/v1\0 || kid || \0 || canonical_json(payload)`.
  Canonical JSON sorted field names, ASCII serialization, compact separators.
  Typed/versioned **closed schema** (reject unknown/duplicate/ambiguous
  fields, wrong key ID, noncanonical signature encodings).
- Claim fields: `license_id`, `cabinet_id`, hash of a provisioned device
  identity, `pack` (BASIC/GOLD/ELITE), explicit `features`, channel,
  `issued_at`, `not_before`, `expires_at`, signed
  `last_online_at`/`offline_until`, and `revocation_epoch`.
- Verification needs an **independently trusted** cabinet/device binding,
  time source and minimum revocation epoch. Refuse future/expired claims,
  tampering, wrong tenant/device, key ID, feature/pack mismatch and clock/
  offline window violations. No algorithm agility from licence input.
- Each online refresh can issue a short-lived *new signed lease* anchored
  to publisher-side validation. Offline availability is bounded by
  `min(subscription_expiry, last_online_at + 72h)`.
- Revocation list/epoch and key rotation must be independently anchored.
  A stale or rolled-back client snapshot can replay an older signed lease;
  **an OS-controlled wall clock and a mutable local vault cannot solve
  rollback under physical adversarial control**. Require trusted counter/
  hardware + a recovery policy, or accept a documented limited offline
  anti-tamper guarantee.

This reference does NOT publish an issuing utility, generate durable keys,
provide an online refresh service, or modify `LicenseService`. The test
runner creates and discards a private key in RAM; no production public key
is defined yet. Avoid claims that any test key could activate product.

## 4. Clinical continuity contract (REQUIRED prior to activation)

Commercial expiry must not delete, overwrite, lock, rekey or prevent
authorized emergency read/export of patient data. It must not turn backups
unreadable or disable recovery. Proposed separation of authorization:

| Operation | Licence invalid / offline exhausted | Additional access requirements |
| --- | --- | --- |
| Create/edit licensed commercial workflows | deny new writes, with explicit reason and renewal path | real JWT/RBAC/tenant + Station checks remain mandatory |
| Patient records clinical view | preserve authorized read-only continuity | role, tenant, audit and patient confidentiality |
| Read/export clinic-owned data and backups | preserve owner-controlled rescue/export capability | authenticated owner/guardian, audited; no anonymous fail-open |
| Guided Restore and SQLCipher recovery | stay available with locally owned recovery keys | strong authentication and recovery audit |
| React/mobile/PWA offline | no silent premium escalation or unauthorized cached data access | entitlement + RBAC + real Station gate per transport |
| Emergency patient workflow | define medically acceptable degraded mode explicitly | clinical owner sign-off, threat modeling and field tests |

The existing middleware's method-level read-only behavior cannot, on its
own, prove these requirements; **separate full API integration E2E is a
blocking gate** before any licence activation switch.

## 5. Migration from Firebase/local vault

1. Inventory actual account/owner/tenant/pack/expiry semantics in Firebase,
   existing trial-code activation, `license_vault.bin`, staff and mobile
   entitlements; do not export real records into laboratory data.
2. Provision publisher KMS/HSM issuer and registered public key manifest,
   with two-person approval, audit, rotation and emergency compromise path.
3. Behind a disabled-by-default, versioned rollout flag, verify signed
   leases in **shadow mode** only; produce privacy-safe aggregate differences
   versus legacy decisions, with no material license state change.
4. Test offline, clock rollback, cross-tenant/device replay, trial conversion,
   expiration, wrong pack, key rotation/revocation, reinstall, restore,
   machine replacement, SQLCipher + clinical read/export continuity.
5. Authorize controlled migration only after: owner GO, independent reviews,
   real multi-client E2E, rollback plan, honest UX and signing/distribution
   gates. Old vault is not a trust anchor; do not re-sign untrusted local
   claims automatically.
6. Define support process for lost/offline machines; preserve data independent
   of commercial entitlement.

## 6. Packaging/SEC-P0 decision gates

**Immediate blocking risk to resolve separately**:
`scripts/build_exe.py` is a divergent executable builder that conditionally
bundles `firebase_creds.json`. [SEC-P0 PR #898](https://github.com/hraaaaf/Digital_crown/pull/898)
remains OPEN/DRAFT and must be rebased/requalified against current master.
Remove/disable legacy build routes or rewrite them to fail closed, including
the possibility of accidental production service credential packaging.
No assumption is made that any shipped customer EXE actually includes one.

**Retain** the existing `INSTALLABLE_CERTIFIED` provenance and release asset
checks for PyInstaller until a certified successor passes equivalent checks.
Test on clean Windows, installer, Authenticode timestamps, malware scans,
asset provisioning, rollback and data restore; macOS separately.

A third-party build tool downloaded without independently verified digest,
including Nuitka's Dependency Walker auto-fetch in SEC-P1.3, is **not
acceptable** in privileged/signed release builds. Pin/check tool hashes,
run least privilege, record SBOM, provenance and exact commit; do not rely
on the experimental CLI setting `--assume-yes-for-downloads`.

**Decision from existing evidence**: PyInstaller is CURRENT, Nuitka is
RESEARCH/EXPERIMENTAL. Neither alone prevents copying, patching or
reverse-engineering. The most meaningful licensing protection is the
publisher-controlled signing/entitlement authority plus online checks where
clinically safe, not changing the compiler.

## 7. Acceptance and no-go matrix

**EXPERIMENTAL P1.4**:
- Linux/Windows CI at same immutable HEAD, test-only Ed25519 key generated
  in memory; broad adversarial positive/negative checks must pass.
- Source review confirms zero private signing key material in committed
  files, no import from product routes and no clinical DB side effects.
- Risk/limits and no-production integration explicit.

**REQUIRED BEFORE COMMERCIAL ACTIVATION (NOT covered by this PR)**:
- independent cryptographic protocol/security review;
- issuer service and KMS/HSM lifecycle;
- trusted time/offline/revocation/anti-rollback threat acceptance;
- Firebase parity and migration tests, full clinical middleware and Station;
- backup/restore/export under expired/revoked/unavailable licence;
- attested Win installer and rebuild, no secrets, full SQLCipher/imaging and UI;
- support/rollback and explicit owner approval.

**No merge, deployment, product behaviour change, release, secrets, or
change to GitHub repository visibility is authorized by this ADR.**

## 8. Roadmap / dependency

SEC-P1.1 native extension → P1.2 / P1.2b / P1.2c / P1.2d
HTTP/JWT/Station experiments → P1.3 Windows EXE **toy** comparison → **P1.4
publisher-signed licensing ADR/reference verifier** → P1.5 independent
cryptographic threat review + SEC-P0 build fix → full Windows release
certification/installer, only after separate GO.

Portability roadmap P6 industrialized Windows packaging remains the canonical
product gate, not overridden by this laboratory.
