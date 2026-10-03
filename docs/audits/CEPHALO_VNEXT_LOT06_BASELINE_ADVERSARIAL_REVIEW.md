# Cephalo 2.0 — LOT06 Baseline Contract Adversarial Review

Status: LOT06 OPEN — baseline contract reviewed; CEPH_ENGINE_CONCORDANT NOT SATISFIED
Reviewed HEAD: `f35ccc7386372d107ef8e31e1debb8ed2e75af2d`

## Scope reviewed
- LOT06 baseline documentation;
- canonical measurement registry;
- executable measurement contract V1;
- construction registry bindings;
- G0 synthetic fixtures;
- legacy geometry-only engine;
- typed evidence adapter/read path.

## Perspective A — orthodontic science / anatomy / construction identity

### Findings found and corrected
1. **MAJOR — phantom construction IDs**: early LOT06 contract referenced `MP_GO_ME_V1` and `N_PERP_FH_V1`, which did not exist in the canonical construction registry.
   - Fixed by binding to real/versioned constructions and adding:
     - `STEINER_MP_GO_GN_V1`
     - `TWEED_DC_MP_GO_ME_V1`
     - existing `NASION_VERTICAL_FH_V1`
     - existing `FH_PO_OR_V1`.
2. **MAJOR — historical Tweed wording conflict**: older construction-registry text still described FMA/IMPA as legacy/non-certified while later source-lock documents had already selected Digital Crown's explicit `Po-Or + Go-Me` geometry.
   - Fixed by versioning `TWEED_DC_MP_GO_ME_V1` and preserving the distinction from strict historical Tweed ear-rod Frankfort.
   - No historical norm was activated.
3. **MAJOR — A→N-perp registry drift**: `M_A_NPERP_MM_V1` remained `PRIMITIVE_AVAILABLE` despite an existing typed/source-locked construction and runtime evidence path.
   - Corrected to `GEOMETRY_COVERED`.
4. **Coverage omission risk**: every registry entry containing `GEOMETRY_COVERED` is now required to be either promoted or explicitly non-promoted by test.

### Current scientific state
Promoted direct executable subset: 19 canonical measurements.

Explicit non-promoted covered geometry:
- `M_MAXILLARY_CONVEXITY_A_NPOG_MM_V1` — legacy typed identity bridge required.
- `M_LI_EPLANE_MM_V1` — legacy typed identity bridge required.
- `M_LS_EPLANE_MM_V1` — legacy typed identity bridge required.
- `M_FACIAL_AXIS_RICKETTS_DEG_V1` — blocked landmark identity (Ricketts Pt).

No blocked landmark, PA measure, Wits construction, nasolabial measure, facial-surface dental distance, or source-unlocked molar identity is promoted.

### Score
**9.4/10 — clean for the baseline/executable-contract scope.**

Residual: detector-derived landmark identity remains an upstream concern; LOT06 only certifies deterministic/manual geometry where exact identity is supplied.

## Perspective B — architecture / reproducibility / fail-closed authority

### Evidence
Exact reviewed HEAD:
`f35ccc7386372d107ef8e31e1debb8ed2e75af2d`

Targeted test execution:
- executable measurement contract;
- G0 measurement fixtures;
- canonical measure registry;
- geometry-only engine.

Result: **20/20 PASS**, no skip reported.

The G0 fixtures prove:
- deterministic angular geometry;
- deterministic calibrated linear geometry;
- missing/degenerate/calibration-invalid inputs fail closed.

The exhaustive coverage test prevents a future `GEOMETRY_COVERED` registry entry from disappearing silently from LOT06.

The `source_status` correction has no demonstrated runtime consumer outside the registry/tests, so it does not change patient behavior.

### Remaining MAJOR
The active typed read path still exposes a limited historical authority surface:
- four CRANIOM linear values are authoritative in `cephalo_typed_read.py`;
- adapters use historical `method_id` values rather than the new canonical `M_*` IDs;
- Ricketts typed constructions still use legacy landmark keys such as `Po`/`Pog`, while LOT03 requires explicit new-consumer identities such as `Po_anatomic`/`Pog_hard`.

Therefore the new canonical contract is **not yet the runtime/read authority**.

This is a MAJOR for the full LOT06 gate, not a defect hidden by the baseline tests.

### Score
**8.8/10 — baseline reproducible, but full engine concordance not yet achieved.**

## Gate decision
`CEPH_ENGINE_CONCORDANT` = **NOT SATISFIED**.

No merge, deployment, DB migration, patient-data mutation or detector/runtime replacement is authorized by this review.

## Next exact
Build a typed-authority bridge that maps existing typed evidence methods to canonical `M_*` measurement identities, preserves legacy persisted snapshots, and refuses ambiguous `Po/Gn/Go/Pog` identity promotion. Then extend the authoritative read/report projection measurement by measurement with executable regression tests.
