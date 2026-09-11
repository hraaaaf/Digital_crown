# Digital Crown — LOT C Media Core

Status: **ACTIVE — C1 ClinicalAsset metadata/provenance candidate**  
Roadmap: `DIGITAL_CROWN_VS_ORTHALIS_ROADMAP.md` / execution scorecard branch remains separate until reconciled.  
Baseline master for C1: `e319070b4f1b4eb6de8d26845bdc3f54ce0adf49`.

## Goal LOT C

Build a Kitview-class media foundation without weakening Digital Crown tenant isolation, local-first storage doctrine or scientific provenance.

LOT C remains **50 EP** total:

- C1 ClinicalAsset model / metadata / provenance — 8 EP
- C2 storage / hash computation / dedupe / tenant guard — 8 EP
- C3 secure import / derivatives / thumbnails — 8 EP
- C4 patient T0/T1/T2 timeline / viewer — 8 EP
- C5 comparison / search / filters — 8 EP
- C6 controlled smartphone capture — 5 EP
- C7 volumetric / cross-tenant / responsive certification — 5 EP

No competitive score increase is credited before LOT C closes. Baseline remains **70.0/100**.

## C1 exact goal

Create an additive, storage-independent patient clinical-media registry that can later unify photos, radiographs, documents, video and audio without mutating existing cephalometric or panoramic scientific rows.

### Success

1. `clinical_assets` exists as an additive table/model.
2. Every asset is scoped by both `employer_id` and `patient_id`.
3. Asset creation fails closed when the patient belongs to another tenant.
4. `created_by` must belong to the same cabinet when supplied.
5. A derived asset parent must belong to the same tenant and patient.
6. Metadata supports type, provenance source, source reference, display filename, MIME type, byte size, optional SHA-256 metadata, longitudinal timepoint, capture time and optional parent asset.
7. `provenance_json` is metadata-only and rejects obvious duplicated patient-identifying keys.
8. File storage, upload routes, digest computation, deduplication, derivatives and UI remain outside C1.
9. No Cephalo implementation file is changed.
10. Exact-head CI must pass before C1 can be credited/closed.

## Safety boundaries

- `ClinicalAsset` is not a storage authority. `original_filename` is display metadata, never a path.
- C1 accepts an optional SHA-256 value only as supplied metadata. **C2 owns digest computation, integrity proof and deduplication semantics.**
- `timepoint` is a longitudinal label (`T0`...`T999`), not a clinical interpretation.
- Existing `CephaloAnalysis`, `PanoramicAnalysis` and `ImagingTrashRecord` behavior is unchanged.
- No real patient data is introduced by C1 tests.
- No Vercel deployment.

## C1 proof targets

- model registration in shared SQLAlchemy metadata;
- metadata roundtrip + tenant-scoped read;
- cross-tenant patient creation rejection;
- cross-tenant `created_by` rejection;
- parent cross-patient rejection;
- unsafe display path / PHI provenance key / malformed hash / malformed timepoint rejection;
- Alembic revision `c1a55e700001` chained from current head `f7a8b9c0d1e2`;
- exact-head CI success;
- PR changed-file audit proving zero Cephalo files.

## Next after C1 closes

C2 must introduce the physical storage contract, server-computed SHA-256, integrity checks, dedupe semantics, tenant-safe storage keys and failure behavior. C2 must consume C1 rather than add a second media registry.
