# CEPH-PREMIUM J2.1 — M3/M4 scene application API FUE (2026-11-10)

**Decision:** add a FUE-only, unregistered HTTP/ORM layer that uses actual Digital Crown authentication, study/media authorization, and a disposable file-backed application SQLite database. No migration and no production activation.

## Goal
Prove on an executable FastAPI TestClient: authenticated fictional clinician → fictional study → encrypted original upload and DC-DOS-05 binding → create canonical scene → change a landmark → invalidate dependent measure → CAS save → close the first SQLAlchemy session → open another session on the same **application** test DB → read the same SHA/bytes/scene and reject unauthorized or tampered content.

## Scope and implementation
- `backend/models_ceph_premium_scene_fue.py`: standalone candidate SQLAlchemy table in the existing Base metadata, imported only by the test-only module, absent from normal backend registration. Unique study/revision and scene SHA, actor and scoped foreign keys. No Alembic migration.
- `backend/services/ceph_premium_scene_app_fue.py`: authorize only exact file name `ceph-j21-scene-app-fue.sqlite3` under an OS-temp descendant path identified by `CEPH_J21_SCENE_APP_FUE_ROOT`, when `ENVIRONMENT=test`, `DIGITALCROWN_ISOLATED_RUNTIME=true`, `CEPH_J21_SCENE_APP_FUE_ONLY=1`, and `DC_DOS05_FUE_ONLY=1`. Reject non-SQLite, unexpected path, symlinks and missing flags. Read and write must call DC-DOS-05 verified original bytes.
- `backend/routers/ceph_premium_scene_app_fue.py`: not imported in backend/main.py or backend/routers/__init__.py, mounted only inside TestClient fixture; same real JWT and `require_permission("cephalo")` + patient-level access as clinical routes.
- `backend/tests/test_ceph_j21_scene_app_fue.py`: independent DB file/session, cookies cleared to prove anonymous denial, tenant/patient scope, stale revision, source SHA and media AES-GCM tamper, scene payload tamper, wrong origin after manual edit, stale measurement invalidation, missing-gate 503. Both DB and encrypted synthetic media removed by test cleanup.

## Claims expressly NOT made
- Does NOT modify or migrate any clinic DB or media, run ONNX inference, activate six automatic contours, certify the 38 channel/anatomic mapping, approve calibrated mm, issue diagnosis or treatment, or merge/deploy.
- The JPEG/PNG association proves **the saved scene points at verified bytes**, not that SRPose38 inference was executed from that particular file. `scientific_digest_source_certified=false` and `clinical_release=false`.
- A passing API FUE is **not** the real Digital Crown Desktop FUE: React/SVG scene still lacks this integration and authenticated app packaging/save/reopen evidence. Keep J2.1 M2–M6 full checklist unchecked until their individual product gates are demonstrably met.

## Verification
- Local Windows Python 3.12 targeted JWT/test application FUE: **2/2 PASS** on the final changed tests, including invalidation of a cached nonclinical SNA angular value after landmark edit, forged automatic provenance refusal and actual ciphertext/payload tamper denial. Earlier joint API regression was 4/4 PASS (before the final assertions).
- GitHub exact HEAD and run not yet pinned for this new change. CI workflow job `m3-authenticated-scene-app-fue` runs two isolated API tests, publishes only JUnit and proof JSON (no image, no DB, no patient names).

## NEXT
1. Run final Windows tests, YAML validation and no-production-registration static checks; fix any failure.
2. Commit/push on the same Draft PR #1253; inspect exact-HEAD GitHub CI and JUnit artifact, then update Notion.
3. Integrate real scene-to-React/SVG with explicit isolated FUE, execute BEFORE/ACTION/AFTER matching viewports, and negative HTTP access checks. Do not claim Desktop proof without a real screenshot.
