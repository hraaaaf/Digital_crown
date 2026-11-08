# DIGITAL CROWN V1.5 — 08.2-A Local admin/bootstrap contract

**Status:** implementation candidate; owner GO for 08.2-A only, no merge/release GO.

## Goal
An independent Queue Core Windows server can provision its FIRST local administrator
once, using a short-lived random challenge at the physically local elevated console,
and later recover admin access with an independent offline secret. No clinical patient
data, Digital Crown account, Firebase, Internet, QR or LAN service is involved.

## Boundaries and safety requirements
- `queue_core/security/` is standalone; do not import clinical database models.
- `windows_console.require_local_windows_admin_console` checks Windows, elevated
  UAC token, actual interactive console, server console session and WTS protocol=0.
  Remote Desktop / redirected terminal / non-admin sessions fail closed.
- Only `windows_cli` chooses the runtime database location, using HKLM's
  `Common AppData`; no user-configurable `--db` in production CLI. Dedicated
  `ProgramData\DigitalCrownQueueCore\local_auth.sqlite`. Parent DACL accepts
  only Local SYSTEM and BUILTIN Administrators full control; database file ACL
  is verified (including permitted inherited grants from restricted parent).
  Junctions/symlinks are refused. **No test in 08.2-A modifies this real location.**
- Bootstrap code: `secrets.token_urlsafe(32)` (at least 256-bit entropy), single
  challenge active, 10-minute TTL, at most 5 failed claims until reissue from
  elevated local console. Only a verifier is stored; concurrent claims serialize
  via SQLite `BEGIN IMMEDIATE` and only one admin row is allowed.
- Admin username: restricted ASCII ID, 3–64; strong secret: 14–128 chars,
  max 256 UTF-8 bytes. Password verifiers: random 128-bit salt and
  `hashlib.scrypt(N=32768,r=8,p=1)`; never plaintext passwords in DB.
- First successful enrollment emits an independent 256-bit random recovery
  secret *once*; the operator must save it on paper/offline storage **outside
  Windows server and normal backups**. Only its SHA-256 domain-separated digest
  is stored; never expose it in logs, audit, GUI or normal app exports.
- `login()` issues an opaque random session token, persists only a domain-separated
  SHA-256 digest; eight-hour expiry, explicit revocation, five wrong attempts
  trigger a 15-minute lock. **No HTTP/session cookie/API route is exposed in A.**
- `recover_admin()` is local-elevated-console-only, requires the offline secret,
  rotates it atomically, changes the password and revokes *all* sessions.
  Five recovery failures trigger a 15-minute lock. No universal backdoor,
  no reset solely by local Administrator without the offline secret.
- Minimal audit: action, result, epoch; no passwords, codes, recovery secrets,
  tokens or patient data. SQLite `synchronous=FULL`, `secure_delete=ON`;
  backup encryption, audit retention/purge executor and Windows service lifecycle
  remain later delivery gates and are not certified by this document.

## Evidence 08.2-A, synthetic only
- Python 3.12 direct Windows pytest + compilation + diff check at source SHA.
- Expiry/replay, concurrent enroll, wrong challenge, admin uniqueness,
  password policy, login rate lock, session expiry/revoke, offline recovery
  one-time rotation and total revocation, secret non-disclosure, no clinical tables.
- Windows gate negative test via redirected Remote Desktop Commander shell:
  `python -m queue_core.security.windows_cli status` MUST deny without
  creating/altering real ProgramData local auth DB.
- Full FUE-I physical elevated console + ACL real Windows smoke, actual
  installer, service account and restore remain **NOT_RUN**. Do not claim
  a physical desktop install from Python mocks. This is a candidate until
  security review and human merge gate.

## Rollback
Entire feature is new isolated Python package + tests + this contract.
No migration to clinical tables or existing data, no runtime activation.
Rollback PR or delete only *synthetic* test sqlite files; never remove
a real local auth store without an approved recovery/restore plan.

## Next
08.2-B future: tenant-scoped RBAC, authorization checks and session lifecycle
integration. 08.2-C devices; 08.2-D QR; 08.2-E installation/FUE-I. Each
requires separate validated sublot scope. Physical Windows service packaging
and real patient/production usage are not authorized.
