# Céphalométrie R7 — closeout Wits / Downs

Date: 2026-09-11

## Goal
Clore R7 avec uniquement les mesures Downs effectivement certifiées et conserver les conventions non résolues en blockers explicites.

## Résultat produit vérifié
- PR #425 fusionnée.
- HEAD exact certifié avant merge: `f53343ff3bf6f70735e97b081447af2d8ed70e01`.
- CI #3368: SUCCESS.
- T2 #2354: SUCCESS.
- squash merge master: `3439e7b2927c624c039084c122fe6ecd0fedf0a2`.

## Activé en R7
- `DOWNS_FACIAL_ANGLE_DEG_V1`.
- `DOWNS_Y_AXIS_DEG_V1`.
- evidence typée `analysis_id=DOWNS`.
- aucune calibration requise pour ces deux angles.
- fail-closed missing / degenerate / cross-image.
- preuve multi-états: création -> edit landmark -> calibration -> recalcul -> typed read path.

## Réutilisation sans duplication
- FMA reste fourni par le contrat R6 `TWEED_FMA_DEG_V1`.
- IMPA reste fourni par R6 `TWEED_IMPA_DEG_V1`.
- interincisal reste fourni par R4 `CRANIOM_INTERINCISAL_DEG_V1`.

## Blockers résiduels R7
- angle de convexité Downs: `BLOCKED_SIGN_CONVENTION`.
- angle A-B plane: `BLOCKED_SIGN_CONVENTION`.
- Wits / AO-BO: `BLOCKED_LANDMARK_CONVENTION` sur le plan occlusal.
- Downs occlusal plane / FH: `BLOCKED_LANDMARK_CONVENTION`.
- Downs L1 / occlusal plane: `BLOCKED_LANDMARK_CONVENTION`.
- U1 vers A-Pog linéaire: `BLOCKED_SOURCE_LANDMARK_CONVENTION`.

Le fichier `2026-09-11-cephalo-r7-wits-downs-scientific-gate.md` reste une trace du gate initial. Le présent closeout fait foi pour l'état final R7 et corrige notamment le statut final Convexity / A-B plane.

## Invariants
- ZERO LLM.
- Aucun Vercel.
- aucune norme, classification, diagnostic ou traitement ajoutés.

## Next exact
Passer à R8 McNamara depuis le master `3439e7b2927c624c039084c122fe6ecd0fedf0a2`, avec gate science + audit runtime avant code.
