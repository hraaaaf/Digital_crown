# Digital Crown — LOT C Media Core

Status: **ACTIVE — C1 CLOSED / C2 CLOSED / C3 NEXT**  
Roadmap: `DIGITAL_CROWN_VS_ORTHALIS_ROADMAP.md` / execution scorecard branch remains separate until reconciled.  
Baseline master for C1: `e319070b4f1b4eb6de8d26845bdc3f54ce0adf49`.

## Goal LOT C

Build a Kitview-class media foundation without weakening Digital Crown tenant isolation, local-first storage doctrine or scientific provenance.

LOT C remains **50 EP** total:

- C1 ClinicalAsset model / metadata / provenance — 8 EP — **CLOSED**
- C2 storage / hash computation / dedupe / tenant guard — 8 EP — **CLOSED**
- C3 secure import / derivatives / thumbnails — 8 EP — **NEXT**
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

## Safety boundaries

- Existing `CephaloAnalysis`, `PanoramicAnalysis` and `ImagingTrashRecord` behavior remains unchanged.
- `timepoint` remains a longitudinal label, not a clinical interpretation.
- No real patient data is introduced by Media Core tests.
- No Vercel deployment.

## C3 exact next goal

Add the secure ingestion/import boundary, MIME/content validation, controlled derivatives/thumbnails and failure cleanup while consuming the C1/C2 registry/storage contract. C3 must not expose raw filesystem paths or trust client-provided hashes.
