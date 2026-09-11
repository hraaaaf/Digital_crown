# Digital Crown — LOT C Media Core

Status: **ACTIVE — C1 CLOSED / C2 CANDIDATE**  
Roadmap: `DIGITAL_CROWN_VS_ORTHALIS_ROADMAP.md` / execution scorecard branch remains separate until reconciled.  
Baseline master for C1: `e319070b4f1b4eb6de8d26845bdc3f54ce0adf49`.

## Goal LOT C

Build a Kitview-class media foundation without weakening Digital Crown tenant isolation, local-first storage doctrine or scientific provenance.

LOT C remains **50 EP** total:

- C1 ClinicalAsset model / metadata / provenance — 8 EP — **CLOSED**
- C2 storage / hash computation / dedupe / tenant guard — 8 EP — **CANDIDATE**
- C3 secure import / derivatives / thumbnails — 8 EP
- C4 patient T0/T1/T2 timeline / viewer — 8 EP
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
- `master` remained `e319070b4f1b4eb6de8d26845bdc3f54ce0adf49` during the C1 implementation proof.
- Focused C1 tests cover shared metadata registration, metadata roundtrip, tenant-scoped read, cross-tenant patient rejection, cross-tenant creator rejection, parent cross-patient rejection, unsafe path / PHI provenance / malformed hash / malformed timepoint rejection and Alembic contract.

C1 earns **8 EP** only as execution progress. Competitive score remains **70.0/100** until LOT C closes.

## C2 exact goal

Bind `ClinicalAsset` to a physical local blob with server-computed integrity, encrypted-at-rest storage and explicit tenant-scoped deduplication, without creating a second media registry or touching Cephalo scientific interpretation.

### C2 Success

1. Storage metadata is additive on `ClinicalAsset`: `storage_key`, `storage_format`, `stored_at`.
2. SHA-256 is computed server-side from plaintext bytes when storage is bound; a client-supplied C1 digest is not trusted as storage truth.
3. Clinical bytes are encrypted before disk write using AES-GCM; plaintext media is never the persisted blob format.
4. AES-GCM AAD binds ciphertext to both tenant and plaintext digest.
5. Storage keys are relative to `MEDIA_ROOT` and use opaque HMAC-derived tenant/blob locators; they never expose patient identity, original filename, tenant numeric id, plaintext SHA-256 or an absolute filesystem path.
6. Identical content inside one tenant reuses the same physical content-addressed blob.
7. Identical content in different tenants uses different opaque tenant namespaces and cannot reuse or reveal the same storage locator.
8. Every read verifies tenant scope, storage namespace, AES-GCM authentication, plaintext SHA-256 and plaintext byte size before returning bytes.
9. Corruption or path escape fails closed and is never silently overwritten on a dedupe path.
10. Atomic-write failure occurs before DB storage metadata is bound.
11. A DB failure after a verified file write may leave only an encrypted unreferenced content-addressed blob; it must not create a committed asset pointing at an unverified write.
12. Migration `c2a55e700002` chains from C1 revision `c1a55e700001`.
13. No upload API, thumbnail, derivative, viewer/UI, deletion/GC or public media URL is introduced in C2.
14. No Cephalo implementation file is changed.
15. Exact-head CI must pass before C2 can be credited/closed.

## C2 storage format

- envelope magic: `DCM1`;
- cipher: AES-GCM;
- nonce: random 12 bytes per physical write;
- key: 32-byte HKDF-SHA256 derivation from `CABINET_MASTER_KEY_HEX` when present, otherwise the configured application `SECRET_KEY` for compatible dev/test/local runtime;
- AAD: stable domain string + `employer_id` + plaintext SHA-256;
- tenant locator: HMAC-SHA256-derived opaque token from tenant identity;
- blob locator: HMAC-SHA256-derived opaque token from tenant identity + plaintext SHA-256;
- storage key: `clinical-assets/t-<opaque-tenant-token>/<opaque-prefix>/<opaque-blob-token>.dcm`;
- original filename and plaintext SHA-256 remain DB metadata only.

The storage key is internal data and is not a public/download URL. Its deterministic HMAC locators preserve same-tenant dedupe without exposing plaintext content hashes in the filesystem.

## C2 failure doctrine

- missing encryption key → refuse storage/read;
- cross-tenant or cross-patient asset scope → behave as asset-not-found for storage operations;
- malformed/escaping storage key → refuse before filesystem read;
- symlink target/directory → refuse;
- corrupt or unauthenticated existing dedupe candidate → refuse and do not overwrite it;
- filesystem write failure → temporary file cleanup and no storage binding on the asset;
- DB rollback after a successful verified write may leave an encrypted orphan only; later GC is a separate concern and must never infer ownership from filenames.

## Safety boundaries

- Existing `CephaloAnalysis`, `PanoramicAnalysis` and `ImagingTrashRecord` behavior remains unchanged.
- `timepoint` remains a longitudinal label, not a clinical interpretation.
- No real patient data is introduced by Media Core tests.
- Current DB backup service backs up the database only; C2 does **not** falsely claim that media blobs are yet included in backup/restore. Media backup/restore remains an industrialization requirement.
- Key rotation/migration is not claimed by C2; changing the active storage key material requires a governed future migration because both locators and AES-GCM authentication depend on that material.
- No Vercel deployment.

## C2 proof targets

- encrypted roundtrip with server-computed digest;
- persisted blob is an authenticated `DCM1` envelope rather than plaintext;
- storage key exposes neither numeric tenant id nor plaintext SHA-256;
- same-tenant dedupe reuses one `.dcm` blob;
- cross-tenant same-content isolation creates distinct opaque storage keys/blobs;
- cross-tenant read denial;
- ciphertext corruption fails closed on read and subsequent dedupe attempt;
- path traversal/escape rejection;
- synthetic atomic-write failure leaves no bound storage metadata and no temp/blob residue;
- migration/model contract for storage columns + tenant/digest index;
- PR changed-file audit proving zero Cephalo implementation files;
- exact-head CI success.

## Next after C2 closes

C3 must add the secure ingestion/import boundary, MIME/content validation, controlled derivatives/thumbnails and failure cleanup while consuming the C1/C2 registry/storage contract. C3 must not expose raw filesystem paths or trust client-provided hashes.
