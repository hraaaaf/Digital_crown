# V1-07 G4 — Patient tabs mobile label truth — Goal UI

Status: BEFORE CAPTURED — FIX IMPLEMENTED — AFTER CERTIFICATION PENDING

## Goal
Keep every patient dossier destination visible at 390×844 without label collision, while preserving the existing six-cell compact navigation contract and desktop labels.

## BEFORE
Exact-head evidence from T2 run #35741065778 on `85755855c13a1c535707b22600a34e261f8ebcd7`, artifact `t2-browser-evidence` #10699925409.

Observed on 390×844 in:
- `after-echeancier-footer-390x844.png`;
- `after-panoramic-trash-390x844.png`;
- `g4-panoramic-structured-report-after-390x844.png`.

The compact grid is present, but desktop labels remain visually rendered inside narrow cells and crowd/collide. This is a real mobile presentation defect even though the runtime behavior is functional.

## Reference
The existing component contract already provides short `mobileLabel` values (`Suivi`, `Clinique`, `Image`, `Docs`, `Companion`, `Finance`) and the responsive CSS intentionally keeps all destinations visible in a compact grid.

Target: render explicit mobile and desktop label spans instead of relying on a generated pseudo-element.

## Success
At 390×844:
- all patient destinations remain present;
- only short mobile labels are rendered;
- each visible label stays inside its own tab cell;
- no label collision or horizontal clipping;
- active state and icon remain unchanged;
- desktop/tablet labels remain unchanged at >= sm.

## Proof
- static responsive contract test;
- T2 exact-head browser geometry check on each affected G4 route;
- AFTER captures at the same 390×844 viewport;
- 1280×900 regression captures;
- human visual review before `visual-approved-by-achraf`.
