# Cephalometry R4 — U1 / Frankfort closeout

Date: 2026-09-11

## Goal
Extend the authoritative typed CRANIOM runtime with the first additional measure that clears source, landmark, geometric-convention and formula gates: upper-incisor inclination to Frankfort (`I_Francfort`).

## Certified product head
- PR: #410
- Certified PR HEAD: `4e58d926a8ee0b3f5b5a76fa9a82c6e3dc9417f9`
- Squash merge commit on `master`: `e9ef3b41eed047c8142cbdaf709aa48c62eec15f`
- `master` verified at the merge commit after merge.

## Certification
- CI #3261, run `34598595484`: SUCCESS
- T2 Runtime Browser Certification #2261, run `34598595514`: SUCCESS
- M6-I #1061, run `34598595503`: skipped as expected

## Scientific sources
Primary CRANIOM sources used for the active U1 / Frankfort fact:
- Bonnefont, Casteigt, Ernoult, Sorel — DOI `10.1051/odfen/2010406`
- Bonnefont, Ernoult, Sorel — DOI `10.1051/odfen/2011104`

The active slice does not activate norms, diagnosis or treatment logic.

## Versioned scientific contract
- Geometric convention: `CRANIOM_U1_FRANKFORT_ANGLE_V1`
- Construction definition: `CRANIOM_U1_TO_FRANKFORT_V1`
- Measurement method: `CRANIOM_U1_FRANKFORT_DEG_V1`
- Legacy runtime metric checked for parity: `I_Francfort`
- Tooth axis: `U1_apex → U1_incisal`
- Frankfort axis: `Po → Or`
- Unit: `deg`
- Linear calibration required: no

## Runtime evidence guarantees
- New R4 snapshots materialize 5 typed CRANIOM constructions / measurements.
- U1 / Frankfort is computed from the same typed U1, Po and Or coordinates used by the evidence graph.
- The measurement adapter rejects drift between typed construction geometry and runtime `I_Francfort`.
- The angular measure remains computable without verified linear calibration.
- Clinician confirmation preserves calibration-independent angular measurements and only repoints calibration-dependent measurement references.
- Auto-calibration transition preserves the 4 calibrated linear measures + 1 calibration-independent angular measure split.
- Landmark-edit transitions preserve the same calibration semantics.
- Persisted pre-R4 snapshots with 4 constructions remain valid and calibratable; the fifth construction is not fabricated during calibration-only revisions.
- Typed-read incompleteness tests now remove a mandatory R3 measurement by identity instead of relying on list position, preserving deliberate R4 compatibility-optional behaviour.

## Failure / fix history before certification
- CI #3253: clinician calibration confirmation incorrectly required a calibration ref for every measurement. Fixed to preserve calibration-independent measurements.
- CI #3255: stale test assumed 4 measurements. Updated to explicit 4 calibrated + 1 independent angular evidence.
- CI #3256: landmark-correction test assumed every measurement referenced calibration. Updated to split by requirement.
- CI #3257: service fixture used mismatched U1 coordinates between runtime and typed evidence. Fixture aligned; parity guard retained unchanged.
- CI #3259: typed-read incompleteness test dropped the last measurement, which is the intentionally compatibility-optional R4 U1 measure. Test changed to remove mandatory `Situation_A`.
- CI #3260: route-level typed-read test had the same positional assumption. Test changed to remove mandatory `CRANIOM_SITUATION_A_MM_V1` by identity.
- CI #3261: SUCCESS.

## Gates intentionally still closed
- Lower-incisor / Downs cannot reuse current Go-Me IMPA without exact CRANIOM Downs construction.
- SN / Downs plane remains blocked pending exact versioned source-supported construction.
- Gi/Gs mandibular frame remains blocked because explicit Gi/Gs landmarks are absent.
- A''B'' remains blocked pending validated NHP / horizontal-gaze protocol.
- Stomion-dependent variable remains blocked because Stomion is absent.
- Overjet / overbite / inter-incisal activation remains gated pending stronger CRANIOM-specific primary-source confirmation.

## Safety / deployment
- ZERO LLM preserved.
- No classification, diagnosis or treatment logic added.
- No Vercel deployment.
- No UI/UX change in this slice; BEFORE / AFTER visual cycle not applicable.

## Next exact
Continue R4 with a primary-source audit of the next scientifically provable CRANIOM variable, prioritising measures already supported by exact runtime landmarks and formulas without inventing geometric equivalence.