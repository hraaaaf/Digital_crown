# R10-A — Mon Équipe / vérité mot de passe — CLOSEOUT

Date : 2026-08-20
Repo : `hraaaaf/Digital_crown`
PR : #188

## Goal
Aligner exactement Réglages → Mon Équipe → création membre sur le contrat backend autoritaire du mot de passe, sans modifier auth, hash, quotas, RBAC ni workflow d'approbation.

## Résultat produit vérifié
- contrat backend autoritaire : `PASSWORD_MIN_LENGTH = 8`, `PASSWORD_MAX_LENGTH = 128` ;
- champ frontend : `minLength={8}`, `maxLength={128}` ;
- aide visible : `8 à 128 caractères` ;
- erreurs Pydantic short/long : `Le mot de passe doit contenir entre 8 et 128 caractères.` ;
- aucune ancienne mention `au moins 4 caractères` dans TeamManager ;
- correctif responsive mobile strictement scoped à `.settings-team-surface` pour la carte membre et ses actions ;
- aucun changement backend, hash/auth, quota, RBAC ou approbation.

## BEFORE
Run `32302270992` — SUCCESS.
Artifact `9383482194`.
Digest `sha256:ad0cddf0b5d146ffb65230f9f031b6a346032f746114a05d42f4905f20299813`.

Constats :
- frontend `minLength=4` + copie `au moins 4 caractères` ;
- overflow mobile réel : 430 → 490, 390 → 490 ;
- erreurs runtime : 0.

## Diagnostic responsive
AFTER #1 `32307831232` : failure, overflow 490 > 430.
AFTER #2 `32311479108` : failure, overflow 478 > 430.
Après deux échecs similaires, stratégie changée vers diagnostic DOM.

Run diagnostic #3 `32311695376` + artifact `9386685164` : responsable exact = groupe d'actions de la carte membre existante, invisible via `opacity-0` mais toujours présent dans le layout.

## AFTER final
HEAD produit certifié : `d174abee1ab01804ba4c4b5cadb18d3a82eb9b1c`.
Run `32311979010` — SUCCESS.
Artifact `9386785694`.
Digest `sha256:a11e6a3bd6b350ae9a463678721269fe07db565474170366872cfc9d0717aea1`.

Viewports inspectés : 1440 / 1024 / 768 / 430 / 390.
- `scrollWidth == clientWidth` : 5/5 ;
- offenders overflow : 0/5 ;
- erreurs runtime : 0/5 ;
- helper 8..128 visible ;
- carte membre responsive et actions accessibles sur 390/430.

Score visuel : **9,4/10**.

## Gates exact HEAD
- Settings R10 Team Password Visual Certification #4 `32311979010` — SUCCESS ;
- CI #1455 `32311979067` — SUCCESS ;
- T2 Runtime Browser Certification #697 `32311978966` — SUCCESS ;
- Settings Profile Team Read Truth #16 `32311978959` — SUCCESS ;
- Settings RBAC #128 `32311978981` — SUCCESS ;
- Settings Profile R2 #28 `32311979165` — SUCCESS ;
- Settings IA #22 `32311979026` — SUCCESS.

## Décision
**R10-A = CLOSED / CERTIFIÉ**, sous réserve du merge GitHub et du post-merge documentaire qui doivent être enregistrés séparément après leur preuve.

Aucun Vercel.
