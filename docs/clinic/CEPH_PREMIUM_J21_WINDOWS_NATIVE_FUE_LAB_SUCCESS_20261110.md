# DIGITAL CROWN — 2026-11-10 — CEPH-PREMIUM J2.1 Windows native FUE LAB
## Verified SUCCESS on exact source, clinical Desktop product HOLD

**Decision / Goal:** Build a GitHub Actions Windows-only, nonclinical standalone FUE executable and prove a real Chromium workflow: JWT login, verified source image, SVG practitioner landmark correction, CAS persistence, full executable shutdown/relaunch, identical verified image/scene digests, and SHA-checked screenshots. Do not register the scene UI/API in the production clinical application.

### Source identity and CI evidence
- Repository: `hraaaaf/Digital_crown`, PR [#1253](https://github.com/hraaaaf/Digital_crown/pull/1253), OPEN / DRAFT / UNMERGED when verified.
- **Exact tested source SHA:** `36a454cfb499fa2c3d15aeafc272c6ec69ad4916`. Later documentation commits **are not** silently represented as tested by that run.
- [GitHub Actions #42836380198](https://github.com/hraaaaf/Digital_crown/actions/runs/42836380198): **COMPLETED SUCCESS 9/9 jobs** (8 contract/API/React/LAB + 1 real Windows native test-only EXE + Chromium).
- Other same-SHA checks: CI Scope Gate, PostgreSQL Alembic Schema Certification, Theme Wave09/10/11 **SUCCESS**, no clinical migration or deploy; Biometric **SKIPPED**, out of scope.
- Windows job evidence markers: `CEPH_NATIVE_FUE_EDIT_PASS`, `CEPH_NATIVE_FUE_REOPEN_PASS`, `WINDOWS_NONCLINICAL_NATIVE_EXE_REAL_BROWSER_CAS_RESTART_SHA_PASS`, `SYNTHETIC_TEST_DB_MEDIA_KEYS_CLEANED_AND_NATIVE_EXE_STOPPED`.

### Native proof, verified from CI logs **and** archived JSON/PNG
- Native PyInstaller binary `DigitalCrown-J21-FUE-LAB.exe`, SHA256 `13e1f9615969c193576071b6d2c5a0d3521c3040ec8fbc15bd86364c536b2faa`; 9/9 bundled static cephalometry resource filenames and SHA256 values matched version-controlled originals.
- Fail-closed launch outside explicit GitHub Windows synthetic flags: PASS. Only loopback `http://127.0.0.1:8879`; outbound browser requests outside this origin blocked. Existing clinic port `8005` unaffected.
- Fresh disposable synthetic **SQLCipher** app DB; no plaintext SQLite header; same actual native backend DB engine on both processes. Synthetic licensed dentist JWT; synthetic AES-GCM PNG source and real study media binding.
- Image SHA256 before/after process restart: `d18e1f863c91a2876cbb2c979951ec0117ddcd039bc6f3d91011213292429787`. SVG viewBox `0 0 800 600`; 38 synthetic landmarks. Landmark `A` x=45 → x=46, new origin `PRACTITIONER_EDIT`, measurements invalidated.
- CAS revision 2 read-back SHA256: `90ab75fcf639d18dfd01b423500c975adc3d01e14b21fa19e73cf92af8d68f85`. Full shutdown of first EXE and reopening same SQLCipher DB from second EXE produced **the same revision, point and scene SHA**.
- Anonymous API: HTTP 401. Wrong patient: HTTP 404. A/B/X full native clinical access-control test still pending; no claim of clinic certification.
- Chromium captures: **BEFORE / AFTER** at 390, 430, 768, 1280 px (8 images) plus **REOPENED-1280** (1 image). Independently rehashed **all 9 PNG** against archival JSON metadata; all matched. The film is a plain synthetic 800×600 color image with artificial diagonal points, **not** a plausible patient radiograph or anatomy certification.
- Cleanup PASS: native process and port stopped; disposable DB, sample media, config/keys and temporary scripts deleted. No real patient data, production registration, clinical release, migration, merge, deploy or forged certification.

### Artifacts and expiry
- [Synthetic FUE screenshots + JSON ZIP (7-day retention)](https://github.com/hraaaaf/Digital_crown/actions/runs/42836380198/artifacts/13773568367); verified ZIP SHA256 `e76dfa900d6851d6f70dba87eae977e54f1321cdf11a56d1b742bc8eac509353`.
- [Windows LAB-only, NOT installable/certified executable archive (1-day retention)](https://github.com/hraaaaf/Digital_crown/actions/runs/42836380198/artifacts/13774852067); archive SHA256 `b158e81b42cd033f14beca42f3a1240c5fd591e950e3c10d5e45117f97ab9a2a`. Not signed, not released, not for clinical deployment.

### Milestone gates and next exact decision
- **M1 🟢** contract closed. **M2–M5 🟡** isolated laboratory/API evidence complete within tested scope; application/native clinical integration remains unproven.
- **Windows FUE LAB 🟢 SUCCESS**. **M6 product/native clinical Desktop 🔴 HOLD**: scene remains outside Digital Crown official installed UI/API, no certified release; scientific SRPose38 channel-to-anatomy mapping and mm calibration still not independently validated.
- **Next:** design an explicitly isolated nonclinical integration into the real Desktop packaging and get a provenance-certified exact-source candidate. Then prove native clinical shell login, film editing/CAS/close/reopen, local DB/backup and A/B/X access denial, screenshots at the same viewports. Independent anatomy/medical review is a separate human gate.
- **Human gate:** no merge to master, production routing, migration of clinical patient data or deployment without explicit user approval. Keep M2–M6 checklist unchecked until the product-level gates are evidenced.

**Handover:** this document + [PR Draft #1253](https://github.com/hraaaaf/Digital_crown/pull/1253) + Notion checklist/roadmap. The tested commit above, not any later documentation-only commit, is the immutable successful CI source.
