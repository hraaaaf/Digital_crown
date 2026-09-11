# Cephalometry R4 — CRANIOM inventory

Date: 2026-09-11
Status: ACTIVE — residual audit complete, interincisal merge pending

## Goal
Extend typed CRANIOM evidence only when source, landmarks, geometric convention and formula are explicit. Unsupported variables remain explicitly blocked rather than approximated.

## Source set
- CRANIOM Part 1: DOI `10.1051/odfen/2010406`
- CRANIOM Part 2: DOI `10.1051/odfen/2011104`
- CRANIOM technical teaching material by Jean-François Ernoult / Slot Concept as secondary source for variable inventory and explicit construction details not exposed in publisher abstracts.
- Original Downs paper for the historical mandibular-plane convention: DOI `10.1016/0002-9416(48)90015-3`.

Primary publisher material is used for active scientific facts when available. Secondary CRANIOM material is never promoted to primary evidence; where exact geometry remains unresolved, the variable stays blocked.

## Runtime landmark coverage
Relevant SRPose38 points include `S`, `N`, `Or`, `Po`, `A`, `B`, `Pog`, `Me`, `Gn`, `Go`, `PNS`, `ANS`, `Ar`, `Ptm`, `Co`, `Ba`, `U1_incisal`, `U1_apex`, `L1_incisal`, `L1_apex`, `U6`, `L6`.

Absent: `Gi`, `Gs`, `Stomion`.

## Classification

| Variable | State |
|---|---|
| Situation A / Nasion vertical | DONE: typed R3 |
| Situation B / Nasion vertical | DONE: typed R3 |
| A'B' on Frankfort | DONE: typed R3 |
| Facial depth S / Nasion vertical | DONE: typed R3 |
| Upper incisor / Frankfort | DONE: typed R4 |
| Lower incisor / Downs mandibular plane | DONE: typed R4 as explicit `DOWNS_MP_GO_ME_V1`; nomenclature inconsistency acknowledged |
| Interincisal U1/L1 | IMPLEMENTED: PR #413 pending final certification/merge |
| Overjet | BLOCKED_SOURCE_FRAME: CRANIOM variable confirmed, but current Frankfort-axis runtime frame not CRANIOM-source-verified |
| Overbite | BLOCKED_SOURCE_FRAME: CRANIOM variable confirmed, but current Frankfort-perpendicular runtime frame not CRANIOM-source-verified |
| SN / mandibular plane | BLOCKED_CONSTRUCTION_SOURCE: CRANIOM variable confirmed, exact mandibular-plane construction not sufficiently source-locked |
| Ar-Gs / Gi-Me mandibular form | BLOCKED_LANDMARK: Gi/Gs absent; no substitution allowed |
| A''B'' horizontal-gaze/NHP | BLOCKED_PROTOCOL: certified horizontal-gaze / natural-head-position protocol absent |
| Upper incisal edge / Stomion | BLOCKED_LANDMARK: Stomion absent |

## R4 closure condition
R4 is closable once the interincisal slice is certified and merged, provided no residual variable above passes both its scientific source gate and runtime-data gate. Blocked variables are explicit future prerequisites, not candidates for approximation.

## Safety
ZERO LLM. No normative activation. No diagnosis, classification or treatment. Unsupported conventions stay blocked. No Vercel deployment.
