# FACAD P4 — six definition-level landmark correspondences; production identity still gated

**Status:** PUBLIC ROBERT EDUCATIONAL CASE / SOURCE-COMPATIBILITY AUDIT / **CLINICAL NO-GO**.
Research PR #1065 remains DRAFT. No deployment or merge is authorized.

## Primary evidence, scope and version boundary

1. **FACAD original public user guide** (FACAD Tracing **3.8**, 7 May 2014):
   https://www.facad.com/dox/dox38/FacadTracingUsersGuide_ENG.pdf —
   printed **page 2**, “FACAD – Overview of Landmarks”.
   This supplies the six vendor-name descriptions, including four explicit
   upper/lower incisor root-apex and incisal-tip roles. The vendor guide is an
   **earlier version**; it is *not* a direct, independent placement certification
   for the running FACAD **3.14.1.1111** case.
2. **Actual operator exports in private Drive**: `32F_Analysis_Properties.txt`
   (factor definitions, e.g. `Iia–Ii`, `Isa–Is`, `A–Pog`) and
   `32F_Object_Values.txt` (30 original sagittal/vertical **mm** landmark
   coordinates). Their raw bytes have been SHA256-checked by the prior P1
   audit. This repository contains only the de-identified, rounded public
   educational fixture, not the original files, case ID or demographics.
3. **Digital Crown canonical docs**:
   `docs/SRPOSE38_LANDMARK_CONTRACT.md` (incisor tips/root apexes/A),
   `docs/audits/CEPHALO_VNEXT_LOT06_CANONICAL_LANDMARK_IDENTITY_BRIDGE.md`
   (Pog hard vs soft identity and authorization rules), and actual
   `backend/services/cephalo_landmark_identity_bridge.py`.
4. **FACAD 32F source-specific factor signatures** already locked in
   `docs/audits/CEPHALO_LOT08_RICKETTS32_FACAD_DENTAL_CLUSTER_RESOLUTION.md`:
   `ILi/A-Pog = Angle4p(Pog,A,Iia,Ii)`,
   `ILs/A-Pog = Angle4p(Isa,Is,A,Pog)`.

## Six research-vocabulary correspondences

| Vendor | Vendor meaning | DC target | Definition-level finding | Clinical case identity |
|---|---|---|---|---|
| `Ii` | Lower incisor tip | `L1_incisal` | Concordant anatomical role | **Unverified** |
| `Iia` | Lower incisor root apex | `L1_apex` | Concordant anatomical role | **Unverified** |
| `Is` | Upper incisor tip | `U1_incisal` | Concordant anatomical role | **Unverified** |
| `Isa` | Upper incisor root apex | `U1_apex` | Concordant anatomical role | **Unverified** |
| `A` | Downs A / Subspinale | `A` | Concordant point-family description | **Unverified** |
| `Pog` | Pogonion; distinct from FACAD soft-tissue `PGs` | `Pog_hard` | Bony-chin family *hypothesis* | **Not authorized by DC identity bridge** |

This list is **a terminology crosswalk**, not a qualified per-image
landmark projection. It does not establish the selected incisor's tooth
identity under overlapping structures, operator precision, orientation,
or actual root apex/edge location. Hard and soft Pog must not be
substituted. No `P`/`Po`/`Or`/Frankfort points have been manufactured.

## Key P4 experiment: execute REAL DC certified identity gate

The earlier P3 exploratory geometry deliberately instantiated
`Pog_hard` directly from a FACAD point in order to run two canonical
math-only angular methods. **That research bypass is not itself the
production clinical identity pipeline.**

P4 instead constructs **unproven manual generic `Pog`** and calls the
real `project_canonical_landmark_identities` method. That bridge only
authorizes `Pog → Pog_hard` when provenance comes from the certified
SRPose38 model/pipeline, or a manual revision can be traced to an earlier
certified SRPose38 observation. Robert's public FACAD export supplies
neither credential. Therefore the correct result is:

- `Pog_hard` **is not projected**, while legacy `Pog` remains intact.
- The **two Ricketts V2 typed canonical incisor/APog angles** must be
  `NOT_COMPUTABLE` with no values (because their canonical `Pog_hard`
  identity is unavailable).
- The independently defined **typed CRANIOM interincisal construction**
  can still be `AVAILABLE` as **educational math-only geometry** based
  on four provisional tooth endpoints; this is not proof of case-specific
  tooth selection or complete clinical runtime execution.
- **0/45 FACAD–Digital Crown clinical parity results** remain validated.

The code `audit/cephalo_facad_robert_p4_identity_gate.py` and test suite
`audit/test_cephalo_facad_robert_p4_identity_gate.py` are the executable,
fail-closed audit. The six source definitions and explicit nonauthority
status are stored separately in
`audit/fixtures/facad_robert_p4_six_landmark_definition_crosswalk_v1.json`.

## What is required to unblock the real clinical crosswalk

A qualified source-image annotation review must compare the six
identically observed landmarks against the FACAD trace, **same case,
same selected tooth, same hard-tissue point**, with an independently
reviewed orientation and coordinate transform. Canonical `Pog_hard`
can only be supplied by evidence satisfying the production certified
identity bridge, not by manually renaming a vendor point.

That is a separate task from the **P2 0.1-mm coordinate quantization
envelope** and **P3 typed geometry check**. Neither should be silently
upgraded to a clinical PASS.

No patent, regulatory, treatment, norms, deployment or clinical release
claims are made here.
