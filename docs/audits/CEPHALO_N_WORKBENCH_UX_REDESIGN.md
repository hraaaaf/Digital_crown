# CÉPHALO-N — Workbench UX Redesign — Canonical Resume File

Status: IN PROGRESS — R20 UI/UX implementation underway

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
- Real display controls are grouped in a left utility rail instead of being visually scattered around the workbench.
- Narrow layouts must stack/reflow controls instead of squeezing the radiograph.
- Reduce nested-card/dashboard feeling.
- Preserve Digital Crown global theme tokens for application chrome/surfaces.
- Scientific family color is a recognition aid, never the sole carrier of clinical state.

## Approved scientific family palette direction
Families must be perceptually separated:
- skeletal: blue/cyan `#38A8FF`
- dental: orange/coral `#FF7A45`
- soft tissue: emerald direction; mockup target `#32D296`, implementation candidate `#2EC68C`
- reference: magenta/rose `#E85AAD`
- auxiliary: neutral gray

The soft-tissue base was deliberately adjusted from the mockup target after the exact semantic contrast gate proved `#32D296` insufficient in the default light theme: measured rendered contrast `4.418:1`, below the required `4.5:1`. The candidate `#2EC68C` preserves the emerald family while increasing surface contrast.

Rendering is context-aware without remapping families:
- UI/table surfaces use the Digital Crown `--text-main` anchor through the single semantic contract.
- The radiographic stage supplies `--cephalo-scientific-anchor: #f8fafc`, producing brighter variants of the same family hues on the dark X-ray surface.
- Clinical status colors remain separate from scientific family colors.

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

## Last verified pre-R20 gate state
At HEAD `c7ca2b7234e8bac24b4a3b174301fd91c3e3908d`:
- R15 AFTER: SUCCESS.
- R15bis AFTER: SUCCESS.
- T2 Runtime Browser: SUCCESS.
- R19 AFTER: FAILURE because the focused semantic-color test rejected soft-tissue contrast `4.418:1 < 4.5:1`; capture was therefore correctly skipped.
- Full frontend suite: `725 passed / 1 failed`, the same contrast assertion.
- M4-A contextual bridge also timed out waiting for `Appairage réussi`; no evidence currently links that timeout to Céphalo palette/layout code, so it remains an independent CI item to recheck on the next candidate HEAD.

## R20 implementation iteration
The next candidate commit is intended to make these presentation-only changes:
1. keep the distant cyan/coral/emerald/magenta family vocabulary;
2. adjust emerald to `#2EC68C` to clear the light-surface contrast gate;
3. allow a radiograph-local scientific anchor so tracing becomes brighter without weakening table contrast;
4. introduce a responsive three-zone workbench at wide widths: real utility controls left, radiograph center, real measures right;
5. keep existing clinical calculations, tracing geometry, analysis selector, calibration, VTO logic and measure panel behavior intact.

## Implementation sequence
1. Lock this canonical resume file and Drive reference. DONE.
2. Replace the too-close blue/violet palette with separated family directions. DONE, candidate under validation.
3. Re-run semantic contrast/mapping tests; adjust rendering strategy if any required contrast gate fails. IN PROGRESS.
4. Refactor real workbench layout toward the locked reference without inventing controls or scientific content. IN PROGRESS.
5. Capture AFTER at the same R19 viewports/states.
6. Compare Target↔Render and BEFORE↔AFTER; fix material mobile/desktop weaknesses.
7. Run impacted CI/browser gates and Perfection Pass.
8. Human visual validation.
9. Merge only after explicit user authorization on the final certified HEAD.

## Repository
Repo: `hraaaaf/Digital_crown`
Branch: `feat/cephalo-n-semantic-color-system`
PR: `#540`
R20 source HEAD before the current candidate commit: `c7ca2b7234e8bac24b4a3b174301fd91c3e3908d`

## Resume instruction
In a new window: read this file first, then verify live PR #540, branch HEAD, master HEAD and current CI before continuing. The Google Drive image above is the locked visual target. Never infer completion from this document; only current Git/CI/render evidence can establish status.
