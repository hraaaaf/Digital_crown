# Cephalometry R5 — Steiner audit

Date: 2026-09-11
Status: ACTIVE PREPARATION
Branch: `feat/cephalo-r5-steiner-skeletal`
Stacked base: R4 interincisal branch head `c93fab0082a7885422a5fc58bfc44d9e79b865d5`

## Goal
Add Steiner as a separate typed analysis without reusing CRANIOM labels, without activating norms, and without silently aliasing Ricketts or generic measurements.

## Scientific sources
Primary:
- C. C. Steiner, *Cephalometrics for you and me*, American Journal of Orthodontics 39(10), 1953, DOI `10.1016/0002-9416(53)90082-7`.
- C. C. Steiner, *Cephalometrics in Clinical Practice*, Angle Orthodontist 29, 1959.

Cross-checks:
- Modern Steiner-analysis validation literature explicitly lists SNA, SNB, ANB, U1-NA angular/linear, L1-NB angular/linear, interincisal angle and S-line.
- Modern measurement-definition literature explicitly defines U1-NA/L1-NB angular relationships and perpendicular linear distances from incisal tips to NA/NB.

## Runtime inventory
Already available raw geometry:
- `SNA`
- `SNB`
- `ANB`
- interincisal angle (`Inter_Incisif`), though currently typed under CRANIOM and must receive separate Steiner provenance if used in Steiner.

Not yet available as Steiner runtime fields:
- U1-NA angle
- U1-NA mm
- L1-NB angle
- L1-NB mm
- SN / mandibular plane
- SN / occlusal plane
- upper/lower lip to Steiner S-line

## Implemented preparation
### Skeletal
Versioned pure geometry exists for:
- `STEINER_SNA_V1`
- `STEINER_SNB_V1`
- `STEINER_ANB_V1`

Typed isolated construction/measurement adapter exists with strict parity against current raw `SNA/SNB/ANB`, no calibration dependency, fail-closed missing/cross-image/degenerate handling.

### Dental geometry
Pure versioned geometry exists for:
- U1 long axis / NA angle
- L1 long axis / NB angle
- perpendicular U1 incisal-tip distance to NA
- perpendicular L1 incisal-tip distance to NB

Linear dental distances require verified mm calibration; angular dental measures do not.

## Remaining gates
### Dental runtime integration
Need explicit schema fields and runtime output for U1-NA/L1-NB before typed evidence can be bound to the active runtime chain. Preserve backward compatibility and do not overload CRANIOM field names.

### Steiner interincisal
Geometry is already available, but R5 must either materialize its own Steiner-source-bound construction or refactor to an analysis-neutral construction. Do not point a Steiner measurement at a construction whose provenance is labeled CRANIOM without an explicit design decision.

### SN / mandibular plane
Source gate still required for the exact Steiner mandibular-plane construction before coding.

### SN / occlusal plane
Source and runtime landmark/construction gate required. Existing runtime aliases `Occ_Ant/Occ_Post` are not automatically a certified Steiner occlusal plane.

### S-line
BLOCKED_LANDMARK/CONSTRUCTION until the exact Steiner nasal midpoint/columellar point is represented. Current Ricketts E-line (`Prn` to soft-tissue Pog) is a different construction and must not be relabeled. `Sn` is not silently accepted as the Steiner S-line nasal point.

## Safety
ZERO LLM. No norms, z-scores, diagnosis, classification, treatment planning or Vercel deployment.
