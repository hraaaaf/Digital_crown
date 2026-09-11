# Digital Crown — LOT C Media Core

Status: **ACTIVE — C1 CLOSED / C2 CLOSED / C3 CLOSED / C4 ACTIVE**  
Roadmap: `DIGITAL_CROWN_VS_ORTHALIS_ROADMAP.md` / execution scorecard branch remains separate until reconciled.  
Baseline master for C1: `e319070b4f1b4eb6de8d26845bdc3f54ce0adf49`.

## Goal LOT C

Build a Kitview-class media foundation without weakening Digital Crown tenant isolation, local-first storage doctrine or scientific provenance.

LOT C remains **50 EP** total:

- C1 ClinicalAsset model / metadata / provenance — 8 EP — **CLOSED**
- C2 storage / hash computation / dedupe / tenant guard — 8 EP — **CLOSED**
- C3 secure import / derivatives / thumbnails — 8 EP — **CLOSED**
- C4 patient T0/T1/T2 timeline / viewer — 8 EP — **ACTIVE**
- C5 comparison / search / filters — 8 EP
- C6 controlled smartphone capture — 5 EP
- C7 volumetric / cross-tenant / responsive certification — 5 EP

No competitive score increase is credited before LOT C closes. Baseline remains **70.0/100**.

## C1 exact goal

Create an additive, storage-independent patient clinical-media registry that can later unify photos, radiographs, documents, video and audio without mutating existing cephalometric or panoramic scientific rows.

### C1 Success — VERIFIED

1. `clinical_assets` exists as an additive table/model.
2. Every asset is scoped by both `employer_id` and `patient_id`.
3. Asset creation fails closed when the patient belongs to another tenant.
4. `created_by` must belong to the same cabinet when supplied.
5. A derived asset parent must belong to the same tenant and patient.
6. Metadata supports type, provenance source, source reference, display filename, MIME type, byte size, optional SHA-256 metadata, longitudinal timepoint, capture time and optional parent asset.
7. `provenance_json` is metadata-only and rejects obvious duplicated patient-identifying keys.
8. File storage, upload routes, digest computation, deduplication, derivatives and UI remain outside C1.
9. No Cephalo implementation file is changed.
10. Exact-head CI and T2 passed on the C1 implementation HEAD before its documentation-only closeout commit.

## C1 proof

Implementation HEAD: `d38a9e0b4af2c9dbf95b15c59ed5b7c8d503cc22`.

- CI #3295 — **SUCCESS**.
- T2 Runtime Browser Certification #2290 — **SUCCESS**.
- Patient P7 Final Certification #1195 — **SUCCESS**.
- M6-I #1090 — **SKIPPED** as expected for this scope.
- PR #415 changed-file audit: 7 files; zero Cephalo implementation files.
- PR #415 review-thread audit before closeout: zero threads.
- C1 merged to `master` as `6ac1f47059b4706dd151ad0853a892f3d581c3f1`.

C1 earns **8 EP** only as execution progress.

## C2 exact goal

Bind `ClinicalAsset` to a physical local blob with server-computed integrity, encrypted-at-rest storage and explicit tenant-scoped deduplication, without creating a second media registry or touching Cephalo scientific interpretation.

### C2 Success — VERIFIED

1. Storage metadata is additive on `ClinicalAsset`: `storage_key`, `storage_format`, `stored_at`.
2. SHA-256 is computed server-side from plaintext bytes when storage is bound; a client-supplied C1 digest is not trusted as storage truth.
3. Clinical bytes are encrypted before disk write using AES-GCM; plaintext media is never the persisted blob format.
4. AES-GCM AAD binds ciphertext to tenant + plaintext digest.
5. Storage keys use opaque HMAC-derived tenant/blob locators and expose neither patient identity, original filename, tenant numeric id nor plaintext SHA-256.
6. Identical content inside one tenant reuses the same physical blob.
7. Identical content in different tenants uses distinct opaque namespaces and cannot share a storage locator.
8. Reads verify tenant scope, storage namespace, AES-GCM authentication, plaintext SHA-256 and byte size.
9. Corruption, symlink or path escape fails closed.
10. Atomic-write failure occurs before DB storage metadata binding.
11. A DB rollback after verified file write may leave only an encrypted unreferenced blob.
12. Migration `c2a55e700002` chains from C1 `c1a55e700001`.
13. No upload API, derivative, thumbnail, viewer/UI, deletion/GC or public media URL is introduced in C2.
14. No Cephalo implementation file is changed.
15. Exact-head CI, T2 and P7 all passed on the C2 implementation HEAD before this documentation-only closeout commit.

## C2 storage format

- envelope magic: `DCM1`;
- cipher: AES-GCM;
- nonce: random 12 bytes per physical write;
- key: 32-byte HKDF-SHA256 derivation from `CABINET_MASTER_KEY_HEX` when present, otherwise configured `SECRET_KEY` for compatible dev/test/local runtime;
- AAD: stable domain string + `employer_id` + plaintext SHA-256;
- tenant locator: opaque HMAC-SHA256 token from tenant identity;
- blob locator: opaque HMAC-SHA256 token from tenant identity + plaintext SHA-256;
- storage key: `clinical-assets/t-<opaque-tenant-token>/<opaque-prefix>/<opaque-blob-token>.dcm`.

## C2 proof

Implementation HEAD: `ef5974a9ac9a62906a0619f0c9697868e44ac6d9`.

- CI #3304 — **SUCCESS**.
- T2 Runtime Browser Certification #2298 — **SUCCESS**.
- Patient P7 Final Certification #1202 — **SUCCESS**.
- M6-I #1098 — **SKIPPED** as expected for this scope.
- PR #416 changed-file audit before closeout: 7 C2 files; zero Cephalo implementation files.
- PR #416 review-thread audit before closeout: zero threads.
- focused tests prove encrypted roundtrip, opaque locator, same-tenant dedupe, cross-tenant isolation, corruption refusal, path escape refusal, atomic-write cleanup, server hash authority, missing-key refusal and migration contract.
- current DB backup service still does **not** claim media blob backup/restore; that remains an industrialization requirement.
- key rotation/migration is not claimed by C2.

C2 earns **8 EP** only as execution progress. Competitive score remains **70.0/100** until LOT C closes.

## C3 exact goal

Add one authenticated clinical-media ingestion boundary that validates payload content before persistence, consumes C1/C2 as the only registry/storage truth, and creates controlled thumbnails without leaking internal storage metadata.

### C3 Success — VERIFIED

1. Canonical API is `POST /api/patients/{patient_id}/assets/import`; tenant identity is derived from the authenticated user and is never accepted from multipart input.
2. Existing patient access control and `patients` permission are enforced before reading/persisting media.
3. C3 supports only payloads with a real parser contract: JPEG, PNG, WebP and PDF. Unsupported audio/video/container formats fail closed rather than trusting extensions.
4. Maximum import size is 50 MiB; over-limit API payloads return 413 before parser/storage work.
5. Content type is detected from bytes/signature and then verified by Pillow or PyMuPDF; a claimed MIME mismatch or incompatible filename extension is rejected.
6. Images are bounded to <=12,000 px per edge and <=80 megapixels; decompression-bomb warnings/errors are rejected.
7. PDFs must be readable, unencrypted and contain 1..500 pages.
8. `asset_type` must match validated content: image -> PHOTO/RADIOGRAPH; PDF -> DOCUMENT.
9. External ingestion cannot claim `DERIVED`; only UPLOAD/IMPORT/DEVICE_CAPTURE are accepted at the C3 boundary.
10. Validation and thumbnail generation complete in memory before the first encrypted C2 blob write.
11. Every accepted image/PDF creates a controlled JPEG thumbnail <=512 px max edge as a `DERIVED` child `ClinicalAsset` linked by `parent_asset_id`.
12. Thumbnail pixels are re-encoded without EXIF/original embedded metadata.
13. C2 remains storage authority: SHA-256 is server-computed, blobs are AES-GCM encrypted, and opaque tenant-scoped locators remain internal.
14. API response exposes asset identifiers/clinical metadata only; neither `storage_key` nor SHA-256 is returned.
15. Validation failure creates no asset row and no C2 blob.
16. Cross-tenant patient import is rejected by existing access control.
17. No Cephalo/Panoramic scientific implementation file is changed and no Vercel deployment occurs.
18. Exact-head CI, T2, P7 and portability certification passed on the implementation HEAD.

## C3 implementation boundaries

- No viewer/timeline UI in C3. That begins in C4 and follows the mandatory BEFORE -> visual Goal -> implementation -> AFTER 390/768/1280 workflow.
- No video/audio ingestion until deterministic content validation and derivative policy are designed.
- No delete/GC policy is introduced. As established in C2, a DB rollback after a verified encrypted write can leave an encrypted unreferenced blob for future governed GC.
- No raw filesystem path or public blob URL is exposed.
- Existing document, panoramic and cephalometric media flows are not silently migrated in C3.

## C3 proof

Implementation HEAD: `8d4252a6d8213128d4dc3d4fbf63025a09963cc8`.

- CI #3330 — **SUCCESS**.
- T2 Runtime Browser Certification #2322 — **SUCCESS**.
- Patient P7 Final Certification #1209 — **SUCCESS**.
- Portability Runtime Certification #506 — **SUCCESS**.
- Onboarding Settings P2 Visual Certification #315 — **SUCCESS**.
- M6-I #1122 — **SKIPPED** as expected for this scope.
- PR #418 changed-file audit: 6 files; zero Cephalo/Panoramic scientific implementation files.
- PR #418 review-thread audit before closeout: zero threads.
- focused tests prove signature/parser validation, MIME/extension mismatch refusal, corrupt content refusal before storage, encrypted image/PDF roundtrip, controlled thumbnail derivation, cross-tenant denial, 413 pre-storage refusal and filesystem-failure rollback.

C3 earns **8 EP** only as execution progress. C1-C3 therefore account for **24/50 EP** of LOT C, without changing the competitive score.

## C4 UI protocol already established

C4 is developed on a separate stacked branch and remains outside this C3 PR.

BEFORE proof comes from Patient P7 #1209 on the C3 implementation HEAD. Its `patient-p7-final-certification` artifact includes the patient Imagerie surfaces at 390x844, 768x1024 and 1280x900 with no overflow, page error or HTTP 5xx. The artifact digest recorded during C4 kickoff is `sha256:9dabbe78235569c8c27b0f7b1b43f67bda9f3c08b78e12c02a33a59a6aa94bc0`.

C4 visual Goal: add a patient media timeline/viewer inside the existing Imagerie surface, preserve RVG as the default imaging workflow, keep Panoramique/Cephalometrie behavior unchanged, and certify AFTER at the same 390 / 768 / 1280 viewports.

## Safety boundaries

- Existing `CephaloAnalysis`, `PanoramicAnalysis` and `ImagingTrashRecord` behavior remains unchanged.
- `timepoint` remains a longitudinal label, not a clinical interpretation.
- No real patient data is introduced by Media Core tests.
- No Vercel deployment.

## Next after C3 closes

Merge C3 only after the documentation-closeout HEAD passes its exact-head gates. Then rebuild/retarget C4 onto the resulting `master` so the C4 PR remains a clean Media Core delta and does not absorb parallel Cephalo history.
