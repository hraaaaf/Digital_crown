# Céphalométrie R5 — Steiner scientific gate

Date: 2026-09-11

## Verified sources
1. Steiner CC. Cephalometrics for you and me. Am J Orthod. 1953;39(10):729-755. DOI: 10.1016/0002-9416(53)90082-7.
2. Steiner CC. Cephalometrics in Clinical Practice. Angle Orthod. 1959;29:8-29. DOI: 10.1043/0003-3219(1959)029<0008:CICP>2.0.CO;2.
3. Steiner CC. The use of cephalometrics as an aid to planning and assessing orthodontic treatment. Am J Orthod. 1960;46(10). DOI: 10.1016/0002-9416(60)90145-7.

## Accepted V1 geometry
- SNA: angle S-N-A, orientation preserved as a ray-angle contract and parity-bound to the existing runtime.
- SNB: angle S-N-B, orientation preserved as a ray-angle contract and parity-bound to the existing runtime.
- ANB: SNA - SNB, parity-bound to the existing runtime.
- U1-NA angular: smallest angle between the upper central-incisor long axis and N-A; axis orientation must not change the value.
- L1-NB angular: smallest angle between the lower central-incisor long axis and N-B; axis orientation must not change the value.

## Blocked linear geometry
The primary Steiner description places the relevant crown point relative to NA/NB, while the current Digital Crown landmark contract exposes U1/L1 incisal-edge and apex points rather than an explicitly versioned mesial/labial crown point.

Therefore U1-NA mm and L1-NB mm are `BLOCKED_LANDMARK_CONVENTION`. They must not be implemented from the incisal-edge point unless a separately sourced and versioned convention is adopted.

## Runtime status
- SNA / SNB / ANB: typed Steiner evidence active in R5 and parity-bound to the existing runtime fields.
- U1-NA° / L1-NB°: typed Steiner evidence active in R5 directly from versioned landmarks; no duplicate legacy clinical field is introduced.
- U1-NA° / L1-NB° are calibration-independent and fail closed on missing, degenerate or cross-image evidence.
- U1-NA mm / L1-NB mm: blocked.

## Safety
No normative evaluation, diagnosis, classification, growth projection or treatment logic is activated in this gate. ZERO LLM. No Vercel.
