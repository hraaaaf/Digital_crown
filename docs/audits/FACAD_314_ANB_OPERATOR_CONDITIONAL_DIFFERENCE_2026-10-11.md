# FACAD C02 / DC Master — ANB non-equivalence risk: synthetic counterexamples

**2026-10-11. STATUS: RESEARCH CONCERN; NOT FACAD NUMERIC PARITY; NOT CLINICAL-APPROVED.** No patient data, runtime code changes, or modification of clinical norms.

## Evidence actually examined

1. Live GitHub `master` **`backend/services/cephalo_engine.py`** Git blob **`240e938a6618557c9630fee8b5e9b49e18b6403c`**: `CephaloEngine._get_clinical_angle` computes `acos(dot(u,v)/(|u||v|))` in degrees, returns an *unoriented* angle from 0° to 180° (rounded to a tenth), and refuses zero-length/NaN/infinite vectors. At its calculation block (ca. lines 234–244), `SNA` and `SNB` are independent unoriented angles `angle(N→S,N→A)` and `angle(N→S,N→B)`, then `ANB = SNA - SNB` with no orientation or wrapping checks visible in this block. This is **source code**, not proof of the routed clinical product version.
2. `backend/data/cephalometry/measurement_definitions.yaml` on `master`, Git blob **`4af3ff7e2e5d24fcff288e7840c7264081e70e10`**, declares `ANB` as `SNA - SNB`, v1 requiring `[S,N,A,B]` (legacy inventory). It does not certify equivalence to the vendor definition.
3. FACAD original **UIA editor** source grid for Steiner (archive run [#37857655276](https://github.com/hraaaaf/Digital_crown/actions/runs/37857655276); **overall run FAILED, partial editor observation only**) records `ANB=Angle3p(N,A,B)`, transcribed in [operator pilot](FACAD_314_C02_MEASUREMENT_OPERATOR_PILOT_2026-10-11.md). **The semantics/sign of proprietary `Angle3p` are NOT established** by this signature. Neither a three-point geometric function nor `SNA-SNB` can yet be asserted to represent FACAD's produced ANB.

## Three exact, non-patient counterexamples for a CONDITIONAL geometric hypothesis

Conjecture only: if FACAD `Angle3p(N,A,B)` is the ordinary **unoriented** geometric angle at `N`, then it uses `angle(N→A,N→B)`. By contrast, the legacy DC snippet produces `angle(N→S,N→A) - angle(N→S,N→B)`.

All coordinates below are arbitrary synthetic units; no norms/diagnostic thresholds.

| Fixture | S | N | A | B | DC source-formula SNA | DC source-formula SNB | `DC ANB = SNA-SNB` | Candidate `Angle(A–N–B)` | Evidence |
|---|---|---|---|---|---:|---:|---:|---:|---|
| F1 reference on horizontal axis, A/B straddle | (-1,0) | (0,0) | (1,1) | (1,-1) | 135.0° | 135.0° | **0.0°** | **90.0°** | Conditional difference 90° |
| F2 reference vertical, A/B straddle | (0,1) | (0,0) | (1,1) | (1,-1) | 45.0° | 135.0° | **-90.0°** | **90.0°** | Conditional difference 180° |
| F3 A/B both same side of N→S | (0,-1) | (0,0) | (1,1) | (1,2) | 135.0° | 153.4° | **-18.4°** | **18.4°** | Conditional signed-direction difference 36.8° |

The numeric table was calculated with a standalone `math.acos` reproduction of the observed source expression, **not by executing Facad or Digital Crown clinical runtime**. The values are a **counterexample to unconditional algebraic equivalence** when angles are unsigned. They are **not** confirmation of a product defect. A signed, orientation-aware `Angle3p` could coincide with `SNA-SNB` on some image orientations, and differing wrapping rules might explain other cases.

## Safety/scientific interpretation

- **BLOCKER** before marking `ANB` vendor-parity: obtain the official C02 definition of `Angle3p` and measure the actual Facad output on a *non-patient* case, with fixed point IDs, calibration, image orientation, and rounding. `master` may route via another canonical service, which requires confirmation before any product-facing claim.
- **BLOCKER** before changing any formula: confirm intended scientific definition/landmark order, version and normative applicability. Do **not** replace vendor operator with a guessed crosswalk. The source C02 PDF SHA is `4dbd3fa8419b684529fcbc17f615f49f7486cdf037fcfff025b1b307c0c0a548`; first SHA-locked [index run #38102158028](https://github.com/hraaaaf/Digital_crown/actions/runs/38102158028) and subsequent bounded source-context extraction [run #38103228900](https://github.com/hraaaaf/Digital_crown/actions/runs/38103228900) are evidence-collection steps, **not numeric parity**.

## Adversarial internal review (two distinct perspectives)

**A / Science, severity MAJOR pending operator oracle:** an unoriented difference of magnitudes is not an unconditional three-point angle. The synthetic fixtures disprove that naive equivalence, but not actual FACAD `Angle3p` semantics. Score on *risk identification* **8/10**, score on *certified vendor parity* **0/10**.

**B / Release and clinical safety, severity BLOCKER for promotion:** source version/active routing unproven; no patient, no normative activation, no product edits; vendor computation not executed; F01.13, FAC05 remain OPEN. The same-file document-only change does not imply certification. Score on *clinical readiness* **0/10**.

**Next evidence, not optional:** verify actual `Angle3p` math/diagram, test non-patient same-point output vs DC's routed (not simply legacy) engine, record actual difference, independent human scientific review. Until then `CLINICAL_EDIT_ALLOWED=false`, `FAC03_D3=OPEN_RED`, `CONVERGED=false`. Canonical roadmap remains **39/99 (39.4%)**.
