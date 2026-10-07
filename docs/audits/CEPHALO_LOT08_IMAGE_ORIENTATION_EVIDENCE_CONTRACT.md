# LOT08 — Image Orientation Evidence Contract

Date: 2026-10-06
Scope: Atlas/33 signed Ricketts factors #4, #14, #18, #24.

## Goal

Provide a versioned, auditable anatomical image-orientation contract so signed cephalometric geometry never depends on raw screen-Y or an implicit mirror convention.

## Evidence model

`ImageOrientationEvidence` contains:
- `source_image_ref`;
- anatomical anterior axis `anterior_x/anterior_y`;
- anatomical superior axis `superior_x/superior_y`;
- explicit `is_mirrored`;
- origin: `ACQUISITION_METADATA` or `MANUAL_VERIFIED`;
- `provenance_ref`;
- `evidence_refs`;
- audit fields for manual verification.

Validation:
- all components finite;
- both axes non-degenerate;
- axes orthogonal;
- manual orientation requires validator identity and timestamp;
- graph validation requires `source_image_ref`, `provenance_ref`, and `orientation_ref` to resolve;
- multiple active orientations for one current cephalogram are rejected.

No orientation is inferred from pixel coordinates or screen-Y.

## Runtime behavior

Existing snapshots without orientation remain valid and fail closed for orientation-dependent methods.

A persisted orientation is:
1. deserialized as typed evidence;
2. required to target the exact current cephalogram source;
3. preserved through subsequent evidence revisions;
4. passed into canonical Ricketts materialization;
5. referenced by downstream `MeasurementEvidence.orientation_ref`.

## Newly conditional Atlas measurements

### #4 Overbite
`M_RICKETTS_OVERBITE_FOP_MM_V1`
- perpendicular to source-locked FOP;
- positive vertical overlap;
- anterior open bite negative;
- requires calibration + image orientation.

### #14 FOP to Xi
`M_RICKETTS_OCCLUSAL_PLANE_XI_MM_V1`
- signed perpendicular FOP/Xi distance;
- FOP above Xi positive, below negative;
- requires canonical FOP/Xi + calibration + image orientation.

### #18 Labial commissure to FOP
`M_RICKETTS_COMMISSURE_FOP_MM_V1`
- signed perpendicular relation;
- FOP below commissure negative;
- requires manual Ricketts commissure + FOP + calibration + image orientation.

### #24 Palatal plane to Frankfort
`M_RICKETTS_PALATAL_PLANE_FH_DEG_V1`
- signed angle from anatomical Frankfort to posterior→anterior palatal direction;
- anterior convergence positive;
- requires `Po_anatomic`, `Or`, ANS, manual `PNS_Ricketts`, image orientation;
- unsigned acute-angle fallback is forbidden.

## Safety boundary

Current runtime does not invent orientation evidence for existing cases. If no trusted orientation evidence is persisted, all four measurements are emitted `NOT_COMPUTABLE`.

This contract unlocks the geometry conditionally; acquisition/manual-orientation ingestion remains an explicit upstream responsibility.
