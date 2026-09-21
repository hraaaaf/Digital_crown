# V1-07 G4 — Treasury modal layer UI goal

## BEFORE
Exact-head T2 run `#35563816645` on `7f2e1d518d706f1c8ced5719b2342219831f4b46` proves the Treasury modal top-close button is visually present but not normally clickable: the sticky application header `z-[300]` intercepts pointer events above the modal wrapper `z-[200]`.

The same failed T2 artifact `t2-browser-evidence` (artifact `10623451847`) contains the matched Treasury screenshots at 390×844 and 1280×900 captured before the blocked top-close interaction.

## Goal
A modal must own the interaction layer while open. Every visible Treasury control, including the top-right close button, must receive pointer input without interference from the application header.

## Target
- Raise only the Treasury modal wrapper above the known sticky header layer.
- Keep modal content/layout/copy/behavior otherwise unchanged.
- No backend or persistence behavior change.
- Do not alter the header stacking contract.

## AFTER acceptance
Matched 390×844 and 1280×900:
1. Treasury modal opens normally;
2. top-right close control owns its hit target and closes normally;
3. footer `Fermer` and `Appliquer à la note` still close normally;
4. partial-payment guard remains usable;
5. no horizontal overflow or page error;
6. no unexpected persistence request from `Appliquer à la note`;
7. screenshot AFTER captured on both viewports.

Visual score rubric: 4 interaction ownership + 2 responsive layout + 2 hierarchy/readability + 1 no-overflow + 1 runtime cleanliness. Target 10/10 only with browser proof.
