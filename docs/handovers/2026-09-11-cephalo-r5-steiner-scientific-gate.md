# Céphalométrie R5 — Steiner scientific gate

Date: 2026-09-11

## Verified sources
1. Steiner CC. Cephalometrics for you and me. Am J Orthod. 1953;39(10):729-755. DOI: 10.1016/0002-9416(53)90082-7.
2. Steiner CC. Cephalometrics in Clinical Practice. Angle Orthod. 1959;29:8-29. DOI: 10.1043/0003-3219(1959)029<0008:CICP>2.0.CO;2.
3. Steiner CC. The use of cephalometrics as an aid to planning and assessing orthodontic treatment. Am J Orthod. 1960;46(10). DOI: 10.1016/0002-9416(60)90145-7.

## Accepted V1 geometry
- SNA: angle S-N-A, orientation preserved as a ray-angle contract and parity-bound to the existing runtime.
- SNB: angle S-N-B, orientation preserved as a ray-angle contract and parity-bound to the existing runtime.
- ANB: SNA - SNB, avec parité comportementale exacte au runtime historique: arrondir SNA à 0,1°, arrondir SNB à 0,1°, puis soustraire.
- U1-NA angular: smallest angle between the upper central-incisor long axis and N-A; axis orientation must not change the value.
- L1-NB angular: smallest angle between the lower central-incisor long axis and N-B; axis orientation must not change the value.
- SN-MP: smallest orientation-invariant angle between S-N and mandibular plane Go-Gn; landmarks S, N, Go, Gn; calibration-independent. L’implémentation `STEINER_SN_MP_V1` / `STEINER_SN_MP_DEG_V1` est dans PR #420 et reste soumise à la certification exact-head avant activation sur master.

## Explicit blockers
### U1-NA mm / L1-NB mm — `BLOCKED_LANDMARK_CONVENTION`
The primary Steiner description places the relevant crown point relative to NA/NB, while the current Digital Crown landmark contract exposes U1/L1 incisal-edge and apex points rather than an explicitly versioned mesial/labial crown point. The incisal edge must not be silently substituted.

### SN-OP — `BLOCKED_LANDMARK_CONVENTION`
The occlusal-plane / S-N measurement is scientifically supported, but the current SRPose38 names `U6`, `L6` and incisor points are not, by themselves, a clinically certified versioned occlusal-plane convention. The SRPose implementation explicitly treats clinical nomenclature validation as a separate scientific gate. No `Occ_Ant` / `Occ_Post` or cusp identity is inferred silently.

### Steiner S-line — `BLOCKED_LANDMARK_CONVENTION`
SRPose38 exposes `Sn_soft`, `Prn`, `Pog_soft`, `Ls_soft` and `Li_soft`, so raw point absence is not the blocker. The exact S-curve/midpoint construction and signed lip-distance convention, including mirrored-image orientation, still require an explicit sourced and versioned contract before activation.

## Runtime status
- SNA / SNB / ANB: typed Steiner evidence active via merged PR #417 and parity-bound to the existing runtime fields.
- U1-NA° / L1-NB°: typed Steiner evidence active via merged PR #417 directly from versioned landmarks; no duplicate legacy clinical field is introduced.
- SN-MP: typed-only patient geometry in PR #420; no duplicate legacy runtime field; landmark edits rematerialize it through the existing Steiner skeletal adapter and calibration transitions preserve it because it is calibration-independent.
- all accepted angular evidence fails closed on missing, degenerate or cross-image geometry according to its landmark contract.

## Mandatory dual validation
For every R5 and later cephalometric measurement:
1. science check: exact definition, landmarks, geometry, primary source plus corroboration;
2. runtime check: actual formula, orientation semantics, units, rounding and operation order;
3. transition check across successive runtime states, not only a clean static fixture;
4. fail-closed missing / degenerate / cross-image;
5. no tolerance widening or approximate landmark substitution to hide a divergence.

## Safety
No normative evaluation, diagnosis, classification, growth projection or treatment logic is activated in this gate. ZERO LLM. No Vercel.
