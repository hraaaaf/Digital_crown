# DIGITAL CROWN — CEPH J1.B2 Desktop authenticated scientific revision / SQLCipher FUE-I

**Date:** 2026-11-11  
**Status:** DRAFT / UNVERIFIED UNTIL EXACT-HEAD CI / NO MERGE / NO DEPLOY  
**Base:** J1.B1 technical source-lock branch `safety/ceph-j1b1-canonical-alias-failclosed-20261110` HEAD `77e37ffff4029a56d1dca155777ee5454e9fc7b9`.

## One decision — GOAL / SUCCESS / PROOF

**Goal:** prove that an authorized local Desktop HTTP user can revise a synthetic cephalometric landmark while unauthorized users, foreign cabinets, stale writers and spoofed operator identities cannot manufacture or overwrite clinician evidence; prove encrypted persistence and restore on native Windows.

**Scope:** only two synthetic backend regression modules and one CI workflow. No production code change, no ONNX download, no patient data, schema/migration, desktop installer, merge, release or cloud deployment.

**HTTP FUE-I** (real FastAPI app with TestClient, bcrypt JWT login, isolated in-memory SQLite):
- real unauthenticated PUT must yield 401; foreign cabinet authenticated PUT/GET must yield 403 and not change graph revision;
- authorized owner updates one SRPose38 source point and is cryptographically/session-bound through the server-authenticated clinician ID;
- resulting `MANUAL_CORRECTED` revision increments from 1 to 2, retains AUTO predecessor coordinates and records the authenticated user, not a spoofed client `ai_diagnostic.validated_by`;
- GET reread and identical PUT replay must preserve exact revision, current-landmark references and history;
- other source landmark IDs stay automatic and unreviewed, no automatic canonical anatomical certification.

**Native Windows SQLCipher FUE-I** (real `sqlcipher3` encrypted file and SQLAlchemy CAS writer):
- create only a disposable synthetic study, in a temporary directory; WAL; assert no plaintext SQLite header/read;
- write source-controlled synthetic clinician-audit snapshot revision 2 with exact clinician receipt; inject forged client clinical R14 receipt and require retention of the previously signed digest;
- two loaded sessions: winner commits, stale competing scientific revision must fail HTTP 409;
- checkpoint WAL explicitly, hash encrypted DB, byte-copy into an isolated restore location, independently reopen both encrypted files and assert exact graph, active source, original and corrected coordinates, revision and historic receipt;
- run existing three native Windows `TerminateProcess` interrupted-archive proofs in the same job to retain the crash/replay oracle.

**Important limitation:** the native SQLCipher test verifies encrypted CAS and a **synthetic** clinician receipt, not authentic user authentication inside the separate SQLCipher engine. Only the HTTP FUE-I test binds the real authenticated identity. Both are necessary, neither is itself a real Windows installed Desktop, signed installer or a physical clinic backup/restore.

**Success criteria:** every HTTP negative gate passes; native Windows SQLCipher save/CAS/restore passes; existing crash/replay cases remain green; complete exact-head suite and risk-specific CI finish without failure. Preserve clinical `SOURCE_LOCK_REQUIRED`.

## Evidence

- GitHub workflow: `.github/workflows/ceph-j1b2-desktop-auth-sqlcipher-fue.yml`; exact HEAD and run URLs to be populated **only after** GitHub Actions executes.
- Tests: `backend/tests/test_ceph_j1b2_desktop_auth_lineage_fue.py`, `backend/tests/test_ceph_j1b2_native_sqlcipher_revision.py`.
- Previous J1.B1 source: [PR #1277](https://github.com/hraaaaf/Digital_crown/pull/1277), exact source HEAD `77e37ffff4029a56d1dca155777ee5454e9fc7b9`.

## Explicit gates / Next

This FUE exercises a source-locked **nonclinical** scientific record. It does **not** certify anatomical SRPose38 channel semantics, permit autonomous diagnosis or treatment, grant usage rights to weights, certify an `INSTALLABLE_CERTIFIED` signed executable, authorize a real-patient database or grant merge to master.

If tests fail, read logs and repair the actual issue without weakening the 401/403/409, identity, audit or encryption oracle. Stop if a dangerous production change, actual patient data or critical gate is necessary. Keep the J1.B2 PR DRAFT and leave J1.B1 #1277 unchanged.
