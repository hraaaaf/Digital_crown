# Cephalometry R4 — CRANIOM inventory

Date: 2026-09-11
Status: ACTIVE
Branch: `feat/cephalo-r4-craniom-complete`
Base: `baa2ab81cf2382b7eacacca1fd1b3e56470dbdf1`

## Goal
Extend typed CRANIOM evidence only when source, landmarks, geometric convention and formula are explicit.

## Source set
- CRANIOM Part 1: DOI `10.1051/odfen/2010406`
- CRANIOM Part 2: DOI `10.1051/odfen/2011104`
- CRANIOM/ODRADE technical teaching reproduction is secondary cross-check only.

Primary publisher HTML explicitly identifies lower-incisor inclination to Downs mandibular plane and upper-incisor inclination to Frankfort. PDF binaries could not be fetched by the audit client, so unavailable figures are not treated as verified geometry.

## Runtime landmark coverage
Available SRPose38 points relevant here include `S`, `N`, `Or`, `Po`, `A`, `B`, `Pog`, `Me`, `Gn`, `Go`, `PNS`, `ANS`, `Ar`, `Ptm`, `Co`, `Ba`, `U1_incisal`, `U1_apex`, `L1_incisal`, `L1_apex`, `U6`, `L6`.

Absent: `Gi`, `Gs`, `Stomion`.

## Classification

| Variable | State |
|---|---|
| Situation A / Nasion vertical | DONE: typed R3 |
| Situation B / Nasion vertical | DONE: typed R3 |
| A'B' on Frankfort | DONE: typed R3 |
| Facial depth S / Nasion vertical | DONE: typed R3 |
| Upper incisor / Frankfort | DIRECT: source explicit; U1 apex/incisal + Po/Or available; raw engine value already exists |
| Lower incisor / Downs mandibular plane | NEEDS CONSTRUCTION: current raw IMPA uses Go-Me; do not equate with Downs silently |
| SN / Downs mandibular plane | NEEDS CONSTRUCTION: exact Downs convention must be versioned first |
| Ar-Gs / Gi-Me mandibular form | BLOCKED: Gi/Gs absent; no substitution allowed |
| A''B'' horizontal-gaze/NHP | BLOCKED: validated horizontal reference protocol absent |
| Overjet / overbite / interincisal | SOURCE GATE: raw geometry exists but CRANIOM-specific convention not yet primary-verified |
| Upper incisal edge / Stomion | BLOCKED: Stomion absent |

## First executable R4 slice
Add typed evidence for `U1_TO_FRANKFORT_ANGLE` only. Keep any reference interval inert. Wire the versioned construction and raw measurement into the runtime evidence graph and prove parity with the existing engine output.

## Safety
ZERO LLM. No normative activation. Unsupported convention stays blocked. No Vercel deployment.
