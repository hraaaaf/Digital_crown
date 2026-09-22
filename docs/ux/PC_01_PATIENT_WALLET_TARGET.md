# PC-01 — Patient Wallet Visual Target

Status: TARGET LOCKED BEFORE VISUAL CERTIFICATION

## Goal
Turn the PC-00 shell placeholders into a useful local-first patient wallet without making the interface look like a cabinet back-office.

## Reference viewports
- 360 × 800
- 390 × 844

## BEFORE
PC-00 Home:
- identity/context;
- local vault status;
- cabinet reachability;
- placeholders “Mes rendez-vous” / “Mes documents”.

## AFTER target
Same route and viewports:
1. Identity/context remains dominant.
2. One explicit “Synchroniser mon espace” action.
3. Last-sync timestamp visible but secondary.
4. Offline/expired state explains that the local copy remains readable.
5. “Mes rendez-vous” shows concise cards: motif, date/time, status.
6. “Mes documents & médias” shows only staff-shared resources.
7. No staff controls, patient numeric IDs, clinical mutation, WhatsApp clinical action, fake download action or unavailable feature button.
8. No horizontal overflow; touch targets >= 44 px for actions.
9. Long lists remain vertically scrollable; shell stays mobile-first.
10. Patient data displayed after reload must come from encrypted local wallet, not a forced network fetch.

## Visual success
- patient can answer “what is on my phone?” and “when was it last synced?” immediately;
- offline status is understandable;
- no visual suggestion that the cabinet is permanently connected;
- PC-02+ features are absent.

## Evidence
Matched BEFORE/AFTER:
- PC-00 candidate vs PC-01 candidate;
- Chromium + WebKit;
- 360×800 + 390×844;
- home wallet with representative deterministic mocked server payload;
- reload/offline wallet proof.
