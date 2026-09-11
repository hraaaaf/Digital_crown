# Cephalometry R3 closeout — geometric conventions

Date: 2026-09-11
Status: CLOSED / MERGED

## Goal
Make current CRANIOM geometric conventions explicit, versioned and fail-closed before extending COM/CRANIOM.

## Certified implementation
- PR: #409 `feat(cephalo): lock R3 geometric conventions`
- Certified exact head: `c14abd6369df8cd6b4c64162147c514ffd118e2e`
- Squash merge: `b12f9323380999b6b5c92d2a0a4c1f03e2e06d7f`
- Post-merge master verified at the squash merge commit; GitHub signature valid.

## CI proof
- CI #3243 / run `34587694835`: SUCCESS
- T2 Runtime Browser Certification #2245 / run `34587694848`: SUCCESS
- M6-I #1045 / run `34587694847`: skipped as expected
- PR audit before merge: mergeable=true, 0 reviews, 0 review threads

## R3 contract now enforced
- every executable CRANIOM construction resolves to one explicit versioned geometric convention
- active CRANIOM linear frame is explicit Frankfort `FH_PO_OR_V1` using Po→Or orientation
- `A'B'` is explicitly distinct from `A''B''`
- `A''B''` horizontal-gaze/NHP construction remains blocked until a validated runtime protocol exists
- Gi/Gs-dependent mandibular constructions remain blocked while Gi/Gs are absent from the runtime landmark vocabulary
- Go/Ar are never substituted for Gi/Gs
- unknown CRANIOM constructions fail closed
- immutable convention provenance is preserved even when patient geometry is `NOT_COMPUTABLE` or `INVALID`; executable patient geometry is withheld
- source references registered: `doi:10.1051/odfen/2010406`, `doi:10.1051/odfen/2011104`

## Regression fixed during certification
CI #3242 exposed one stale legacy assertion expecting `geometry == {}` for `NOT_COMPUTABLE` constructions. The contract was corrected by updating the legacy test to require convention provenance only, with no fabricated `source_image_ref`. Final exact-head certification then passed.

## Safety
- ZERO LLM preserved
- no norms activated
- no diagnosis or treatment logic added
- no Vercel deployment

## Known limits carried forward
R3 intentionally does not invent unresolved CRANIOM geometry. `A''B''`, Gi/Gs-dependent constructions and any analysis-specific mandibular-plane conventions remain blocked until independently sourced and represented in runtime landmarks/constructions.

## Next exact — R4
R4 = COM / CRANIOM complet.
Goal: extend the runtime only with CRANIOM constructions and measurements whose landmarks, geometric convention, formula and source can be made explicit under the R3 contract.
Success: each added measure is traversable through typed evidence, versioned, source-bound and fail-closed; unsupported measures remain explicitly blocked.
First action: inventory the remaining COM/CRANIOM measures against the 38-landmark runtime and classify each as directly implementable, derivable only with new constructions, or blocked by missing landmarks/protocol.

## Expert opinion
R3 closes the dangerous ambiguity layer before feature expansion. The correct next move is an evidence-backed R4 inventory, not bulk-porting legacy COM labels and hoping the geometry means the same thing.
