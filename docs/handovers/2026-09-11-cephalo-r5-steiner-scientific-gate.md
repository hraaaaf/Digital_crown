# Céphalométrie R5 — Steiner scientific gate

Date: 2026-09-11

## Verified sources
1. Steiner CC. Cephalometrics for you and me. Am J Orthod. 1953;39(10):729-755. DOI: 10.1016/0002-9416(53)90082-7.
2. Steiner CC. Cephalometrics in Clinical Practice. Angle Orthod. 1959;29:8-29. DOI: 10.1043/0003-3219(1959)029<0008:CICP>2.0.CO;2.
3. Steiner CC. The use of cephalometrics as an aid to planning and assessing orthodontic treatment. Am J Orthod. 1960;46(10). DOI: 10.1016/0002-9416(60)90145-7.

## Accepted V1 geometry
- SNA: angle S-N-A, orientation preserved as a ray-angle contract and parity-bound to the existing runtime.
- SNB: angle S-N-B, orientation preserved as a ray-angle contract and parity-bound to the existing runtime.
- ANB: SNA - SNB with exact legacy runtime rounding parity: runtime-rounded SNA minus runtime-rounded SNB.
- U1-NA angular: smallest angle between the upper central-incisor long axis and N-A; axis orientation must not change the value.
- L1-NB angular: smallest angle between the lower central-incisor long axis and N-B; axis orientation must not change the value.
- SN-MP: smallest orientation-invariant angle between S-N and Go-Gn; calibration-independent, source-bound, fail-closed.

## Runtime status
- SNA / SNB / ANB: typed Steiner evidence active and parity-bound to the existing runtime fields.
- U1-NA° / L1-NB°: typed Steiner evidence active directly from versioned landmarks; no duplicate legacy clinical field.
- SN-MP: typed-only patient geometry active as `STEINER_SN_MP_V1` / `STEINER_SN_MP_DEG_V1`; landmark edits rematerialize it and calibration transitions preserve it.
- all active R5 Steiner angular measurements are calibration-independent and fail closed on missing, degenerate or cross-image evidence.

## Explicit blockers
- U1-NA mm / L1-NB mm: `BLOCKED_LANDMARK_CONVENTION`. The current incisal-edge landmark must not silently replace the crown-point convention described in the primary Steiner source.
- SN-OP: `BLOCKED_LANDMARK_CONVENTION`. U6/L6/incisal landmarks exist, but their exact occlusal-plane semantic roles are not versioned strongly enough to derive Steiner’s occlusal plane without an explicit convention.
- Steiner S-line signed lip distances: `BLOCKED_LANDMARK_CONVENTION`. Soft-tissue landmarks exist, but the exact S-line construction and signed anterior/posterior convention must be explicitly sourced and versioned before activation.

## Mandatory double-check rule for subsequent analyses
For every new cephalometric measurement:
1. science check: definition, landmarks, geometry, primary source + corroboration;
2. runtime check: actual formula, orientation semantics, units, rounding, operation order, transitions/calibration/revisions;
3. behavioral parity across multiple successive states, not only a static fixture;
4. fail-closed tests for missing / degenerate / cross-image evidence.

## Certification proof
- PR #417 merged R5 core Steiner evidence on master as `b1c36bfb6a57b25c6ae290fdb0dd690d8f5d0b70` after exact-head CI #3349 and T2 #2340 SUCCESS.
- PR #420 merged SN-MP on master as `981c721c939cbd01ffcaee43adbfaf5a5f6d3ce8` after exact-head CI #3352 and T2 #2342 SUCCESS.

## Safety
No normative evaluation, diagnosis, classification, growth projection or treatment logic is activated in R5. ZERO LLM. No Vercel.
