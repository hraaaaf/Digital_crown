# Cephalo vNext — LOT05 Canonical Extended Schema

Status: DRAFT — isolated schema/migration contract; no product activation
Parent: LOT04 HEAD ddb6178babebf31510bf815f0c4a692faeb1bd3a
Canonical gate: CEPH_SCHEMA_V2_VERIFIED

## Goal
Define a versioned Cephalo 2.0 envelope that extends the existing typed evidence graph without breaking or silently reinterpreting V1 patient records.

## Existing persisted truth
Digital Crown already persists typed cephalometric evidence under `_evidence_graph_v1` in `CephaloAnalysis.angles_data`. Existing behavior that MUST survive:
- immutable automatic SRPose evidence;
- explicit `current_landmark_refs`;
- audited `MANUAL_CORRECTED` lineage with original auto coordinates, operator and timestamp;
- calibration provenance and revision transitions;
- fail-closed behavior for ambiguous legacy graphs;
- no silent resurrection of omitted landmarks;
- no generic save changing calibration.

LOT05 therefore does not create a competing clinical truth model.

## V2 envelope
The isolated V2 contract is `CEPHALO_CANONICAL_SCHEMA_V2` and contains:
- schema version and case identity;
- source/evidence graph version reference;
- landmark registry entries with canonical ID, explicit aliases and semantic status;\n- active landmark states with evidence ref, origin, coordinates and source lineage/audit fields;
- active landmark refs separate from historical evidence;
- coordinate space and calibration metadata;
- detector/model quality metadata as metadata, never as anatomical authorization;
- migration metadata binding the source V1 snapshot hash and migration policy.

## Landmark identity
An alias is compatibility metadata, not equivalence authorization.

Every landmark entry declares:
- `canonical_id`;
- zero or more `aliases`;
- `semantic_status`: `CLINICAL_CANONICAL | TRACING_CANONICAL | RESEARCH_ONLY | LEGACY_AMBIGUOUS`;
- `identity_version`;
- hard/soft tissue domain;
- optional source-analysis scope.

Generic Gn/Go/Po cannot silently become analysis-specific constructions. U6/L6 remain research/legacy molar identities until exact source semantics are proven. `Occ_Ant`/`Occ_Post` are compatibility construction anchors, not SRPose channels.

## Provenance states
V2 preserves the existing V1 origins and adds no fake history:
- `SRPOSE38_AUTO`
- `MANUAL`
- `MANUAL_CORRECTED`

Clinical validation is represented as validation evidence/state, not by rewriting origin.

## Coordinates and calibration
Every active coordinate set declares:
- coordinate system/version;
- source image dimensions;
- units (`px` for raw landmark coordinates);
- calibration reference when physical units are used downstream;
- finite coordinates only.

A migration MUST NOT infer missing calibration, detector confidence, anatomical identity, validation state, or operator identity.

## Quality/confidence metadata
The quality metadata envelope is mandatory, while detector score values remain optional and typed separately from anatomy:
- raw model score may be stored;
- `score_semantics` must identify the score as raw/uncalibrated unless calibration evidence exists;
- no missing score may be synthesized;
- no score threshold may promote a landmark to clinical canonical status.

## V1 → V2 migration
Migration is deterministic and lossless with respect to known V1 evidence:
1. hash the canonicalized source V1 snapshot;
2. preserve every evidence object and evidence_id;
3. preserve `current_landmark_refs` exactly when present;
4. if current refs are ambiguous/missing and cannot be proven uniquely, migration fails closed;
5. preserve calibration source/decision/status without upgrading it;
6. map runtime IDs only through the explicit compatibility registry;
7. preserve unknown/legacy fields in an opaque compatibility payload when needed for round-trip;
8. never recalculate patient measurements during schema migration;
9. record migration version, source schema, source hash and timestamp;
10. round-trip back to V1 must reproduce the canonicalized source snapshot for supported V1 records.

## Compatibility classes
- `LOSSLESS_V1` is the only compatibility class accepted by the LOT05 executable migration schema.
- `FAIL_CLOSED_AMBIGUOUS` is an outcome concept: ambiguous V1 raises an error and no V2 artifact is emitted.
- `OPAQUE_LEGACY_PRESERVED` describes preservation inside a `LOSSLESS_V1` artifact; it is not a separate accepted artifact class in LOT05.
- `V2_NATIVE` is reserved for a future dedicated native-creation contract and is not machine-valid under the V1→V2 migration gate.

## Required verification
Gate `CEPH_SCHEMA_V2_VERIFIED` requires executable fixtures proving:
- V1 → V2 → V1 canonical round-trip;
- current landmark refs unchanged;
- corrected landmark lineage unchanged;
- omitted landmark does not resurrect;
- calibration provenance unchanged;
- aliases do not rewrite canonical identity;
- unknown legacy data is preserved or migration fails explicitly;
- no patient measurement is recomputed;
- malformed/ambiguous V1 fails closed.

## Non-goals
LOT05 does not activate V2 persistence/read-path, migrate the database, replace runtime models, execute G1/G2, or modify master. Product integration remains LOT12.
