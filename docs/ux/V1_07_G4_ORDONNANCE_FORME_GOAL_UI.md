# V1-07 G4 — Ordonnance manual form chooser UI goal

## BEFORE
Verified source defect on pre-fix HEAD `e46bb2587acbb8435bee364d63e1d6b4c4b2d3a5`:
- the visible manual-form trigger in `DrugRowV1.tsx` advertises `Choisir la forme manuellement`;
- `PrescriptionAgenticStudioV1.tsx` wires that trigger to `onFormeOpen={() => undefined}`;
- therefore the enabled control has no product action.

Browser inventory proof from run `#35468756588` confirms the Ordonnance surface is rendered in Chromium. The action-level proof is the next G4 gate.

## Goal
Clicking the enabled manual-form trigger must open an explicit form chooser without fabricating medication identity or clinical guidance.

## Reference / target
Reuse the already-existing deterministic legacy interaction pattern from `PrescriptionAgenticStudioLegacy.tsx`:
- fixed-position chooser anchored to the trigger;
- canonical `FORMES` list;
- explicit practitioner click to select;
- closes after selection;
- no automatic recommendation.

No new visual language is introduced.

## AFTER acceptance
At matched 390×844 and 1280×900:
1. trigger is reachable;
2. chooser opens;
3. all 11 canonical forms are visible as explicit options;
4. selecting `COMPRIMÉS` updates the row;
5. minimum option height is ≥44 px;
6. no horizontal overflow;
7. no page error.

Visual score rubric: 2.5 points each for chooser visibility, complete option set, applied selection, responsive/touch integrity. Target = 10/10 only with direct browser proof.

## Safety / product truth
This control selects document presentation form only. It must not infer a drug, dose, indication, diagnosis, or treatment.
