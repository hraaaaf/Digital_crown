# CÉPHALO-N — Workbench UX Redesign — Canonical Resume File

Status: IN PROGRESS — UI/UX implementation started

## Goal
Rebuild the Céphalo-N workbench presentation around the approved UX direction while preserving the existing scientific/calculation architecture.

Success = the real product presents a clearer clinical hierarchy (controls/navigation → radiograph/tracing → measures), a larger radiographic work area, a compact measures panel, and scientifically consistent color families that are immediately distinguishable on both light UI surfaces and dark radiographic imagery.

Proof required = BEFORE → locked reference → implementation → AFTER at 390x844 / 768x1024 / 1280x900 using the deterministic R19 fixture → Target↔Render comparison → impacted tests/CI → visual scoring → human validation.

## Locked visual reference
Google Drive file: `CEPHALO_N_WORKBENCH_UX_REFERENCE_V2.png`
Drive file ID: `1XBZC4BM_H0xuvJl1v3i6T-pvVj0thOSH`
Drive URL: https://drive.google.com/file/d/1XBZC4BM_H0xuvJl1v3i6T-pvVj0thOSH/view?usp=drivesdk

The image is a visual direction, not a scientific specification. Generated labels, measurements, controls and geometry MUST NOT be copied unless they already exist in the real product contract.

## Approved visual direction
- Prefer the second generated mockup as the UX reference.
- Radiograph/tracing is the dominant work surface.
- Measures panel is compact and readable to the right on wide layouts.
- Navigation and display controls are grouped instead of scattered around the radiograph.
- Reduce nested-card/dashboard feeling.
- Preserve Digital Crown global theme tokens for application chrome/surfaces.
- Scientific family color is a recognition aid, never the sole carrier of clinical state.

## Approved scientific family palette direction
Families must be perceptually separated:
- skeletal: blue/cyan direction, target base `#38A8FF`
- dental: orange/coral direction, target base `#FF7A45`
- soft tissue: emerald direction, target base `#32D296`
- reference: magenta/rose direction, target base `#E85AAD`
- auxiliary: neutral gray

Exact rendered values remain subject to contrast tests on both Digital Crown surfaces and the radiographic viewer. Do not weaken accessibility merely to match the mockup hex values.

## Locked non-regression boundaries
- No backend change.
- No DB/migration change.
- No canonical measure/norm/formula change.
- No scientific alias/equivalence change.
- No patient evidence mutation.
- Preserve the single canonical `cephaloVisualSemantics.ts` presentation contract.
- Preserve separate clinical status colors and non-color status cues.

## BEFORE proof
Current certified default-light R19 BEFORE/AFTER evidence exists for the pre-redesign workbench at the same 390x844 / 768x1024 / 1280x900 viewports. The semantic-color PR is #540.

## Implementation sequence
1. Lock this canonical resume file and Drive reference. DONE.
2. Replace the too-close blue/violet palette with the approved separated family directions in the single semantic contract.
3. Re-run semantic contrast/mapping tests; adjust rendering strategy if any required contrast gate fails.
4. Refactor real workbench layout toward the locked reference without inventing controls or scientific content.
5. Capture AFTER at the same R19 viewports/states.
6. Compare Target↔Render and BEFORE↔AFTER; fix material mobile/desktop weaknesses.
7. Run impacted CI/browser gates and Perfection Pass.
8. Human visual validation.
9. Merge only after explicit user authorization on the final certified HEAD.

## Current repository state at start
Repo: `hraaaaf/Digital_crown`
Branch: `feat/cephalo-n-semantic-color-system`
PR: `#540`
Start HEAD before this canonical file: `4a6bfee31e1c4b799bafcfc60cfd20d80f8d4364`

## Resume instruction
In a new window: read this file first, then verify live PR #540, branch HEAD, master HEAD and current CI before continuing. The Google Drive image above is the locked visual target. Never infer completion from this document; only current Git/CI/render evidence can establish status.
