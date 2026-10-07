# LOT08 Steiner blocker resolution ? 2026-10-03

Status: **SOURCE-LOCK GATE SATISFIED FOR STEINER STATIC PROFILE; FINAL LOT08 GATE OPEN.**

## Resolutions

| Finding | Resolution | Runtime policy |
|---|---|---|
| U1-NA mm / L1-NB mm lacked exact crown point | explicit `U1_facial_surface` / `L1_facial_surface` identities | manual/structure anchor only; fail closed if absent |
| SND / D-line lacked authoritative D | source-lock `D_Steiner_1959`; detector `D_point` is not an alias | explicit manual identity only |
| Pog-NB implementation missing | deterministic perpendicular point-to-NB geometry added | exact `Pog_hard` + calibration |
| L1-GoGn implementation missing | deterministic axis-angle geometry added | exact `Gn_anatomic` required |
| Steiner occlusal-SN ambiguous | versioned `Occ_Steiner_Ant` / `Occ_Steiner_Post` construction | no Wits/Ricketts occlusal-plane aliasing |
| D-line linear/angular implementation missing | deterministic D-line geometry added | explicit D, exact Go/Gn; calibration for linear |
| U6/L6 semantics unresolved | removed from static required profile | auxiliary/serial only until exact semantics source-lock |
| Steiner S-line was conflated with unresolved serial SL/SE/LE semantics | separated from serial semantics using direct Facad CPH + official landmark manual evidence | `STEINER_SLINE_COMPATIBILITY_V1`; blocked on explicit `MS_Steiner`; `Cm`/`Sn_soft`/`Prn` aliases forbidden; SE/LE serial semantics remain deferred |
| historical norms not universally applicable | historical reference set made display-only | no classification authority; out-of-domain suppresses classification |
| L1-NB vs Pog-NB relation risked treatment automation | retained as protocol-derived interpretive relationship | no autonomous treatment/extraction decision |

## Scientific authority
All new deterministic geometry lives under the LOT06 authority path. LOT08 does not duplicate formulas. Sources are frozen in `ortho_lot08_steiner_protocol_profile_v1.json`.

## Gate boundary
`ORTHO_ANALYSIS_PROTOCOLS_SOURCE_LOCKED` is satisfied for the **Steiner static profile only**. This is not `ORTHO_ANALYSIS_PROTOCOLS_VERIFIED`: UI placement of explicit anchors, report rendering, end-to-end protocol presentation, responsive evidence and final adversarial confirmation remain LOT08 implementation work.


## Facad direct-definition refinement — 2026-10-07

Direct inspection of the official Facad `Steiner.cph` resolves the three previously unmapped vendor rows without weakening the historical source boundary:

- `Ii-Pog // NB` is a Facad `Sub` calculation over `Ii-NB` and `Pog-NB`. Digital Crown already has the source-locked relationship `STEINER_L1_NB_VS_POG_NB_V1`; no duplicate geometry is created.
- `Ls-SL` and `Li-SL` are perpendicular-distance rows to `SL`.
- Facad defines `SL` as the line through `PGs` and `MS`; its official landmark manual defines `PGs` as soft-tissue pogonion and `MS` as Steiner's S-point (columella tangent point).
- Digital Crown has `Pog_soft`, `Ls_soft` and `Li_soft`, but no exact `MS_Steiner` identity. Therefore the two S-line measurements remain fail-closed.
- No Facad reference value is promoted to runtime normative authority, and no same-trace numeric parity is claimed.
