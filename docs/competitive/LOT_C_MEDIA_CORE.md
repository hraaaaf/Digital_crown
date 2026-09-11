# Digital Crown — LOT C Media Core

Status: **ACTIVE — C1 CLOSED / C2 NEXT**  
Roadmap: `DIGITAL_CROWN_VS_ORTHALIS_ROADMAP.md` / execution scorecard branch remains separate until reconciled.  
Baseline master for C1: `e319070b4f1b4eb6de8d26845bdc3f54ce0adf49`.

## Goal LOT C

Build a Kitview-class media foundation without weakening Digital Crown tenant isolation, local-first storage doctrine or scientific provenance.

LOT C remains **50 EP** total:

- C1 ClinicalAsset model / metadata / provenance — 8 EP — **CLOSED**
- C2 storage / hash computation / dedupe / tenant guard — 8 EP — **NEXT**
- C3 secure import / derivatives / thumbnails — 8 EP
- C4 patient T0/T1/T2 timeline / viewer — 8 EP
- C5 comparison / search / filters — 8 EP
- C6 controlled smartphone capture — 5 EP
- C7 volumetric / cross-tenant / responsive certification — 5 EP

No competitive score increase is credited before LOT C closes. Baseline remains **70.0/100**.

## C1 exact goal

Create an additive, storage-independent patient clinical-media registry that can later unify photos, radiographs, documents, video and audio without mutating existing cephalometric or panoramic scientific rows.

### Success — VERIFIED

1. `clinical_assets` exists as an additive table/model.
2. Every asset is scoped by both `employer_id` and `patient_id`.
3. Asset creation fails closed when the patient belongs to another tenant.
4. `created_by` must belong to the same cabinet when supplied.
5. A derived asset parent must belong to the same tenant and patient.
6. Metadata supports type, provenance source, source reference, display filename, MIME type, byte size, optional SHA-256 metadata, longitudinal timepoint, capture time and optional parent asset.
7. `provenance_json` is metadata-only and rejects obvious duplicated patient-identifying keys.
8. File storage, upload routes, digest computation, deduplication, derivatives and UI remain outside C1.
9. No Cephalo implementation file is changed.
10. Exact-head CI and T2 passed on the C1 implementation HEAD before this documentation-only closeout commit.

## Safety boundaries

- `ClinicalAsset` is not a storage authority. `original_filename` is display metadata, never a path.
- C1 accepts an optional SHA-256 value only as supplied metadata. **C2 owns digest computation, integrity proof and deduplication semantics.**
- `timepoint` is a longitudinal label (`T0`...`T999`), not a clinical interpretation.
- Existing `CephaloAnalysis`, `PanoramicAnalysis` and `ImagingTrashRecord` behavior is unchanged.
- No real patient data is introduced by C1 tests.
- No Vercel deployment.

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

## C2 exact next goal

Introduce the physical storage contract consumed by `ClinicalAsset`, with server-computed SHA-256, integrity verification, explicit dedupe semantics, tenant-safe storage keys and defined failure/rollback behavior.

C2 must consume C1 rather than create a second media registry. It must remain independent of Cephalo scientific interpretation and must not expose anonymous or cross-tenant media paths.
