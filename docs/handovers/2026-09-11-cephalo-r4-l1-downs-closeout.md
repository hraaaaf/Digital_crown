# Cephalometry R4 — L1 / Downs closeout

## Goal
Type the CRANIOM lower-incisor inclination to the Downs mandibular plane using an explicit, versioned geometry without conflating it with another mandibular-plane convention.

## Certified result
- PR: #412
- Certified PR HEAD: `92b90d6e1345cc23a7ad44a61e929d07fed7ebca`
- Squash merge commit: `3aab122ee0f5c845ada7b80079845336805bd80d`
- Post-merge master verified at the merge commit before this closeout.

## CI proof
- CI #3274 / run `34606096255`: SUCCESS
- T2 Runtime Browser Certification #2272 / run `34606096267`: SUCCESS
- M6-I #1072 / run `34606096232`: SKIPPED as expected

## Scientific contract
- CRANIOM source: DOI `10.1051/odfen/2011104`
- Downs source: DOI `10.1016/0002-9416(48)90015-3`
- Versioned reference frame: `DOWNS_MP_GO_ME_V1`
- Geometric convention: `CRANIOM_L1_DOWNS_ANGLE_V1`
- Construction: `CRANIOM_L1_TO_DOWNS_MP_V1`
- Measurement method: `CRANIOM_L1_DOWNS_DEG_V1`
- Runtime landmarks: `L1_apex`, `L1_incisal`, `Go`, `Me`
- Typed value is calibration-independent (`deg`).
- Runtime parity is fail-closed against legacy `IMPA` computed from the same geometry.

## Compatibility and safety
- New snapshots expose 4 linear + 2 angular CRANIOM typed measurements.
- Pre-L1 R4 snapshots with 5 constructions remain compatible.
- Pre-R4 snapshots with 4 constructions remain compatible.
- Auto/manual calibration keeps angular measurements calibration-independent.
- Landmark revisions preserve calibration semantics and rematerialize typed geometry from the active landmark set.
- No norms, diagnosis, classification, treatment logic, or therapeutic recommendation added.
- ZERO LLM preserved.
- No Vercel deployment.
- No UI impact in this slice; BEFORE/AFTER visual cycle not applicable.

## Failure/fix history
- CI #3264 exposed a stale auto-calibration 5-measurement contract.
- CI #3265 exposed a stale manual-calibration 5-measurement contract.
- Strategy changed after the second same-family failure: proactively audited remaining R4 contracts and aligned runtime chain, landmark edit, persistence fixtures, construction/measurement adapters, and compatibility tests before the final certification run.
- Final exact-head certification: CI #3274 SUCCESS + T2 #2272 SUCCESS.

## Remaining R4 work
Continue only with CRANIOM variables whose source definition, exact runtime landmarks, and formula are explicitly proven. Do not infer missing geometry from similarly named legacy metrics.
Known blocked items remain blocked unless prerequisites are added:
- Gi/Gs-dependent mandibular constructions: explicit Gi/Gs landmarks unavailable.
- A''B'': validated natural-head-position / horizontal-gaze protocol unavailable.
- Stomion-dependent variable: Stomion unavailable.

## Next exact
Audit the next CRANIOM candidate, prioritizing inter-incisal angle, then overjet/overbite, and activate only if source + geometry + runtime landmark gates all clear.
