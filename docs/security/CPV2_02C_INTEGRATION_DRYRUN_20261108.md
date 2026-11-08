# CPV2-02C — Integrated-master DRAFT rehearsal (NEVER MERGE)

This branch copies the exact changed Pocket product + test-only safety files from `3490c6a3c0d817e925762e0e1a8831e3c4a77072` onto `master@7e821dff1112249d0bda25c5708f9b37cca7082b` and resolves the single same-path conflict `backend/main.py` by preserving both branches' CORS headers. It is **NOT an authorized merge into master**. Source branches remain untouched.

## Sources / scope

- Product PR #1201 HEAD: `d7852f25c3f4b69f8f8ad4b4e2d58ffbae5cefb1`
- Pocket safety PR #1224 HEAD: `3490c6a3c0d817e925762e0e1a8831e3c4a77072`
- Master snapshot: `7e821dff1112249d0bda25c5708f9b37cca7082b`
- Merge-base before integration: `3a4a8941d287ad9726f56f58e5a12bd9e253b30d`
- Total changed candidate paths: 46; concurrent master changes: 70 paths; same-path collision: only `backend/main.py`.
- The integrated CORS authorization list includes `Idempotency-Key`; its exposed headers preserve master `Content-Disposition` and Pocket `X-Document-Id`, `X-Idempotent-Replay`.

## Evidence and gates

The dedicated `tests/test_cpv2_02c_integration_cors_lab.py` checks the actual parsed CORSMiddleware configuration, and the G04 matrix runs this check on Windows and Ubuntu. The new DRAFT PR against master must pass independent CI/FUE on its **own exact SHA**. Existing standalone success on #1224 does **not** transfer automatically.

Synthetic-only tests. No clinic database or media, no real patient data, no restoration or auto-reassociation. No migration, clinical deployment, PR merge, or production activation. Final clinical NO-GO until separately approved operational restore, security/integrity review or documented risk acceptance, and human authorizations.
