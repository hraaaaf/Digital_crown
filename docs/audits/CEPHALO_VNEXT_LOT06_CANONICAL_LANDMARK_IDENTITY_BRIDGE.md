# Cephalo LOT06 — canonical landmark identity bridge

Status: **J1.B1 FAIL-CLOSED FIX CANDIDATE — DRAFT / NO MERGE / NONCLINICAL**

## Technical safety finding

The legacy bridge allowed `Po → Po_anatomic`, `Co → Co_anatomic`
and `Pog → Pog_hard` when it received a point carrying the *pinned
SRPose38 model hash*. This establishes artifact provenance and
numeric output parity, **not** that the neural channel refers to the
named anatomical structure. The upstream checkpoint's MMPose labels
are numeric `0..37`; the exact source-to-anatomy mapping is still
classified `LEGACY_AUTO_UNVERIFIED`.

This allowed unreviewed auto points to be projected to canonical
identities and then consumed by calculations. The baseline test
`test_certified_srpose_points_gain_only_source_locked_additive_identities`
explicitly expected that behavior.

## Proposed fail-closed candidate behavior (not activated)

- Preserve persisted legacy point IDs and all model/hash/ONNX metadata.
- Keep `Po_anatomic`, `Co_anatomic`, `Pog_hard` aliases **disabled**
  for any SRPose38 AUTO point, even if its hash is correct.
- Permit an alias only when the legacy point is **MANUAL** and
  `EvidenceStatus.CLINICIAN_VALIDATED` with operator ID and timezone-aware
  validation timestamp; the same requirement applies to
  `MANUAL_CORRECTED`.
- Additionally require corrected points to reference the same ID,
  same image, pinned numerical SRPose model provenance and unchanged
  original auto coordinates (within 1e-6 px) through the previous
  observation. Direct manual clinician attestations need no previous
  automated point.
- Reject canonical IDs supplied directly without clinician attestation,
  including explicit-only `Gn_anatomic` / `Pt_Ricketts`, rather than
  silently passing through unreviewed names.
- Keep legacy/canonical collision errors and `Gn_anatomic` and
  `Pt_Ricketts` explicit-only.
- The **scientific projection** copies every unreviewed AUTO or merely
  OBSERVED MANUAL landmark as `availability_status=NOT_COMPUTABLE`:
  no consumer of the canonical view may use numerical coordinates of
  that channel, even if another landmark on the same film is reviewed.
  MANUAL_CORRECTED must also match the original observation and film.
  This copy-on-read restriction does **not** mutate the stored legacy
  landmarks, image bytes or historical evidence graph.
- Dependent canonical analyses and constructions must now become
  `NOT_COMPUTABLE` when *any* required input is not clinician-attested;
  a single reviewed `Po_anatomic` cannot launder unreviewed
  `Or`, `Go`, or `Me` into a Tweed FMA.
  This is the intended safe failure, **not a new clinically validated
  diagnosis**. Legacy compatibility analyses are a separate code path
  and do not acquire scientific authority from this projection.

## Proportional technical tests

File: `backend/tests/test_cephalo_vnext_lot06_landmark_identity_bridge.py`

13 synthetic pytest cases cover: auto hash never sufficient; spoofed
clinical status on AUTO; missing clinician review; three explicit
manual canonical aliases; precise same-ID/image/original-coordinate
binding of corrections; wrong model SHA; unavailable and timezone-naive
evidence; direct canonical injection; manually attested explicit
canonical point; collision; mixed reviewed/unreviewed films and
unreviewed manual evidence. No source image or actual patient used. No real images or patient records.

Dedicated CI (test-only):
`.github/workflows/ceph-j1b1-canonical-identity-safety-lab.yml`.
No model download, no remote clinical inference, no DB migration,
no deployment.

## HUMAN GATES / Integration blockers

1. The isolated tests **do not prove** complete downstream workflow
   integration; the bridge is used by runtime evidence,
   manual corrections, calibration and downstream measure builders.
2. Before merging, run the broader integration/longitudinal/backup
   test suite on identical HEAD and inspect whether historical cases
   remain readable and genuinely non-evaluable calculations block
   instead of falling back to legacy aliases.
3. Independent technical review and clinical safety review are
   required for this behavior change; **no direct merge, no
   production deployment, no patient data in tests**.
4. Scientific mapping J1.B1 remains `SOURCE_LOCK_REQUIRED` pending
   external, authoritative evidence; passing CI cannot lift it.

## Source evidence

- Frozen runtime contract:
  `backend/services/srpose38_contract.py`.
- Source checkpoint:
  `5k5000/CLdetection2023@18d17d1934970016e7610c4849311900b8d1f191`,
  `mmpose_package/mmpose/configs/_base_/datasets/cephalometric.py`
  (numeric names `0..37`).
- Prior audit:
  `docs/audits/CEPHALO_SRPOSE38_PROVENANCE.md`.
