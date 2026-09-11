# Céphalométrie R5 — Steiner scientific gate

Date: 2026-09-11

## Verified sources
1. Steiner CC. Cephalometrics for you and me. Am J Orthod. 1953;39(10):729-755. DOI: 10.1016/0002-9416(53)90082-7.
2. Steiner CC. Cephalometrics in Clinical Practice. Angle Orthod. 1959;29:8-29. DOI: 10.1043/0003-3219(1959)029<0008:CICP>2.0.CO;2.
3. Steiner CC. The use of cephalometrics as an aid to planning and assessing orthodontic treatment. Am J Orthod. 1960;46(10). DOI: 10.1016/0002-9416(60)90145-7.

## Accepted V1 geometry
- SNA: angle S-N-A, orientation preserved as a ray-angle contract and parity-bound to the existing runtime.
- SNB: angle S-N-B, orientation preserved as a ray-angle contract and parity-bound to the existing runtime.
- ANB: SNA - SNB, parity-bound to the existing runtime rounding convention.
- U1-NA angular: smallest angle between the upper central-incisor long axis and N-A; axis orientation must not change the value.
- L1-NB angular: smallest angle between the lower central-incisor long axis and N-B; axis orientation must not change the value.
- SN-MP: smallest angle between S-N and Steiner mandibular plane Go-Gn. Steiner 1953 and 1959 are concordant on GoGn/SN, and S/N/Go/Gn exist in the certified SRPose38 contract.

## Explicit blockers
- U1-NA mm / L1-NB mm: `BLOCKED_LANDMARK_CONVENTION`. The primary Steiner crown-point convention must not be silently replaced by the current incisal-edge landmark.
- SN-OP: `BLOCKED_LANDMARK`. The Steiner occlusal-plane-to-SN measurement is source-supported, but the certified SRPose38 vocabulary does not expose a certified pair of occlusal-plane defining landmarks.
- Steiner S-line signed lip distances: `BLOCKED_SIGN_CONVENTION`. The S-line reference itself is source-supported as the line from the midpoint of Sn-Prn to soft-tissue Pogonion, and SRPose38 exposes Sn_soft/Prn/Pog_soft/Ls_soft/Li_soft. Activation remains blocked until the anterior/posterior signed-distance convention is explicitly versioned and source-locked.

## Runtime status
- SNA / SNB / ANB: typed Steiner evidence active and parity-bound to existing runtime fields.
- U1-NA° / L1-NB°: typed Steiner evidence active directly from versioned landmarks.
- SN-MP: typed Steiner evidence prepared on the R5 completion branch; calibration-independent, orientation-invariant and fail-closed on missing, degenerate or cross-image evidence.
- U1-NA mm / L1-NB mm, SN-OP and signed S-line distances: blocked as above.

## Safety
No normative evaluation, diagnosis, classification, growth projection or treatment logic is activated in this gate. ZERO LLM. No Vercel.
