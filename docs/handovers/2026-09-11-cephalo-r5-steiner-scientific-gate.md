# Céphalométrie R5 — Steiner scientific gate

Date: 2026-09-11

## Verified sources
1. Steiner CC. Cephalometrics for you and me. Am J Orthod. 1953;39(10):729-755. DOI: 10.1016/0002-9416(53)90082-7.
2. Steiner CC. Cephalometrics in Clinical Practice. Angle Orthod. 1959;29:8-29.
3. Steiner CC. The use of cephalometrics as an aid to planning and assessing orthodontic treatment. Am J Orthod. 1960.

## Accepted V1 geometry
- SNA: angle S-N-A.
- SNB: angle S-N-B.
- ANB: SNA - SNB, parity-bound to the existing runtime.
- U1-NA angular: upper central-incisor long axis versus N-A.
- L1-NB angular: lower central-incisor long axis versus N-B.

## Blocked linear geometry
The primary 1953 description places the most mesially positioned point of the upper/lower incisor crown relative to NA/NB. The current Digital Crown landmark contract exposes U1/L1 incisal-edge and apex points, not an explicitly versioned mesial/labial crown point.

Therefore U1-NA mm and L1-NB mm are BLOCKED_LANDMARK_CONVENTION. They must not be implemented from the incisal-edge point unless a separately sourced/versioned convention is adopted.

## Safety
No normative evaluation, diagnosis, classification, growth projection or treatment logic is activated in this gate. ZERO LLM. No Vercel.
