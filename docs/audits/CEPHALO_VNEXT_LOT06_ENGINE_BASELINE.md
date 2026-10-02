# Cephalo 2.0 — LOT06 Engine Concordance Baseline

Status: BASELINE — BEFORE runtime change
Gate target: `CEPH_ENGINE_CONCORDANT`
Branch: `feat/cephalo-vnext-lot06-engine-concordance`
Base HEAD: `35fbd613b519e25373570486b697e364b7690006`

## Goal
Prove measurement-level concordance between the approved scientific contracts and the executable cephalometric engine, without relying on detector validity.

A measurement is concordant only when all of the following are explicit and mutually consistent:
`measurement identity → required landmarks/constructions → formula/operation → unit/sign → source contract → availability/fail-closed behavior → runtime/read/report exposure`.

## Current authority layers

### 1. Canonical measurement identity registry
`backend/services/cephalo_measure_registry.py`

Strengths:
- versioned `M_*` IDs;
- explicit units;
- source-state classification such as `GEOMETRY_COVERED`, `PRIMITIVE_AVAILABLE`, `IMPLEMENTATION_MISSING`, `BLOCKED_LANDMARK`, `BLOCKED_MODALITY_PA`, `SOURCE_LOCK_REQUIRED`, `LEGACY_TO_AUDIT`;
- known false-equivalent pairs are tested as distinct.

Current limitation:
- the registry stores identity/unit/status only. It does **not** itself bind exact required landmarks, construction IDs, formula symbol, source references or runtime implementation symbol.

### 2. Legacy measurement definitions
`backend/data/cephalometry/measurement_definitions.yaml`

Observed inventory:
- 25 legacy measurement IDs across Steiner, Tweed, Downs, COM, McNamara, Ricketts, Wits and Esthetic families;
- active and quarantined definitions coexist;
- some measurements are frontend-only or have backend/frontend naming divergence;
- Wits, nasolabial angle and some McNamara-adjacent measures remain quarantined/fail-closed.

Important: this file is a legacy inventory, not the complete canonical measurement registry.

### 3. Geometry-only runtime engine
`backend/services/cephalo_engine.py`

Verified architectural properties:
- computes observed geometry only;
- accepts age/sex/CVM only for compatibility and does not use them for norms/diagnosis;
- no growth/treatment output;
- uses explicit calibration for millimetric measurements;
- missing/degenerate geometry generally resolves to `None`;
- exposes legacy aliases through `key_mapping`.

Risk:
- legacy aliases such as generic `Gn`, `Go`, `Po` remain compatible runtime names although LOT03 requires versioned scientific identities for new consumers.
- therefore legacy runtime availability cannot itself prove canonical identity concordance.

### 4. Versioned geometry modules
Existing modules include:
- `cephalo_steiner_geometry.py`
- `cephalo_tweed_merrifield_geometry.py`
- `cephalo_downs_geometry.py`
- `cephalo_mcnamara_geometry.py`
- `cephalo_ricketts_geometry.py`
- `cephalo_constructions.py`
- `cephalo_geometric_conventions.py`

These are the preferred scientific primitives for LOT06 because their names and source contracts are more explicit than the legacy all-in-one engine.

### 5. Normative / interpretation layer
`normative_profiles.yaml`, `classification_rules.yaml`, normative services.

This layer must remain downstream of geometry. Legacy contradictory norms are evidence of historical state, not permission to choose one silently.

## Baseline concordance classes

### A — geometry already source-locked / executable
High-value examples already covered by versioned geometry or engine primitives:
- SNA / SNB / ANB
- FH–GoMe / FMA
- IMPA
- U1–FH
- inter-incisal angle
- S–N / N-perpendicular CRANIOM constructions
- A′B′ CRANIOM construction
- A→N-perp
- Co–A
- Co–Gn anatomical candidate
- ANS–Me
- facial depth / facial convexity primitives
- Ricketts E-line V2 source-strict geometry
- Ricketts facial depth
- Ricketts constructed Gn and facial axis geometry when exact identities exist
- SN–GoGn geometry where the exact Gn identity is supplied.

LOT06 task: bind each to one canonical `M_*` identity and executable evidence.

### B — primitive exists but canonical executable binding is incomplete
Examples:
- A→N-perp / Pog→N-perp primitive vs canonical registry identity;
- Co–Gn minus Co–A;
- palatal-plane/FH;
- L1 edge→A-Pog;
- several analysis-specific formulas implemented in geometry modules but not exposed through one canonical runtime measurement contract.

LOT06 task: materialize canonical bindings, not duplicate formulas.

### C — implementation missing although scientific identity is defined
Examples:
- Pog→NB
- FH–SubGo–M
- facial-axis McNamara variant
- L1–GoGn
- serial/growth-change measures.

LOT06 task: implement only when all exact landmarks/constructions are available and source-locked.

### D — blocked by exact landmark identity
Examples:
- SND/D
- U1/L1 facial-surface linear measures
- source-specific U6/L6 measures
- airway measures
- Xi/Pm-dependent measures.

LOT06 rule: remain `NOT_COMPUTABLE`; no substitution with incisal edge, generic molar or neighboring landmark.

### E — blocked by modality or source contract
- all PA/frontal measurements remain blocked without PA imaging;
- Wits/occlusal-plane consumers remain fail-closed until exact versioned plane construction is authorized;
- nasolabial angle remains source-contract gated.

## Demonstrated baseline risks

### R1 — Canonical registry is metadata-only
A canonical ID can say `GEOMETRY_COVERED` without a machine-enforced pointer to:
- exact landmarks;
- exact construction;
- implementation symbol;
- source reference.

Severity: MAJOR for `CEPH_ENGINE_CONCORDANT` because drift can occur independently.

### R2 — Generic legacy aliases can cross scientific identities
LOT03 explicitly distinguishes:
- `Gn_anatomic` vs `Gn_constructed`;
- `Po_anatomic` vs machine/ear-rod Porion;
- analysis-specific Gonion conventions.

The legacy engine accepts generic `Gn`, `Po`, `Go`.

Severity: MAJOR for new canonical consumers; acceptable only as legacy compatibility with provenance preserved.

### R3 — Frontend/backend split authority still exists
Legacy inventory records several measures historically computed or presented only in frontend code (for example U1/NA, L1/NB variants, FMIA in prior layers).

Severity: MAJOR until one backend typed authority owns every promoted Cephalo 2.0 measurement.

### R4 — legacy norm conflicts must not contaminate geometry
Historical files preserve conflicting norm values for some measures.

Severity: MAJOR if geometry and interpretation are coupled; LOT06 must prove geometry remains norm-independent.

## Market-parity relevance
The competitive benchmark changes the implementation priority but not scientific gates.

Digital Crown should target:
1. a stable canonical engine;
2. tracing workbench over the existing landmark contract;
3. coherent analysis packs;
4. longitudinal superimposition;
5. premium reporting;
6. VTO/growth later.

Adding detector landmarks is not a LOT06 objective.

## LOT06 implementation order

1. Create a machine-readable canonical measurement contract that binds each promoted `M_*` measure to:
   - required canonical landmark identities;
   - required construction IDs;
   - implementation symbol;
   - unit/sign convention;
   - source references;
   - availability gate.
2. Cover all existing `GEOMETRY_COVERED` measurements first.
3. Add executable G0 fixtures per measurement.
4. Make the typed backend read/report path consume canonical IDs instead of deriving scientific meaning from legacy display names.
5. Keep blocked/ambiguous measures explicitly unavailable.
6. Only then expose coherent Steiner/Tweed/Downs/McNamara/Ricketts/COM analysis packs.

## Gate evidence required
`CEPH_ENGINE_CONCORDANT` cannot be granted until:
- every promoted measurement has one canonical executable contract;
- required identities/constructions are exact;
- units/signs/formulas match source-locked definitions;
- blocked inputs fail closed;
- no frontend-only clinical geometry remains authoritative;
- deterministic fixtures execute on the exact HEAD;
- two adversarial perspectives converge on one HEAD;
- extra confirmation pass is clean.

## Immediate next implementation target
Build the machine-readable **canonical executable measurement contract** for the currently `GEOMETRY_COVERED` subset only. Do not activate missing/blocked measurements and do not change norms or product UI in the same batch.
