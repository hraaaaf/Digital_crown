# Indicateurs patient explicables — CLOSEOUT

Date : 2026-08-21
Repo : `hraaaaf/Digital_crown`
PR : #199 — **MERGED**
Merge : `b22e7bc9e7981eef54916c4e1412fa69ad612bf5`

## Goal

Remplacer les scores et jugements automatiques opaques par des repères patient factuels, sourcés et actionnables, sans dégrader Patient Journey ni les finances patient fail-closed.

## Résultat produit vérifié

- suppression du grade automatique Platinum / Gold / Silver / Bronze dans l'UX ;
- suppression du score patient global et des sous-scores assiduité / solvabilité comme jugements ;
- conservation des faits bruts : RDV honorés/annulés, montants facturés/encaissés/reste dû ;
- segmentation manuelle conservée comme tag cabinet explicite ;
- suppression du `intelligence_score /100` ;
- hover renommé `Repères du dossier`, sans vocabulaire `IA` trompeur ;
- provenance visible : `Données du dossier • règles déterministes` ;
- NBA déterministe conservé avec message factuel visible ;
- `Fantôme` remplacé par `Sans RDV futur` / formulation opérationnelle ;
- variation IMPA exposée comme delta brut, sans jugement automatique `amélioration/dégradation` ;
- `FlashSummary` mort retiré après preuve de non-consommation ;
- Patient Journey et Patient Finances restent hors refonte visuelle et conservent leur doctrine fail-closed.

## BEFORE

Base immuable : `e18597176a97805ae7839f2052340354257a0ae8`.

Patient Indicators BEFORE #12 `32497490154` — **SUCCESS**.
Artifact `9452286533`.
Digest `sha256:5db90db3c19348e65d96345d6f021d32f7a72cbe486d0fd4a80d06c768bdcd23`.

Surfaces × viewports :
- liste patients ;
- hover patient ;
- page patient / suivi ;
- 1440 / 768 / 390 / 360 / 320 px.

BEFORE : 15/15 captures. Défaut objectivé : hover trop large à 360/320 px et jugements `Fantôme`, score `/100`, `Alertes IA & Suggestion`, `Assistant Virtuel ODF`.

## Mockup

Référence créée avant implémentation : `docs/settings/INDICATEURS_PATIENT_EXPLICABLES_MOCKUP.svg`.

Doctrine : faits visibles, 2–3 repères compacts, aucun jugement moral/clinique, provenance déterministe explicite, action NBA accompagnée de son déclencheur.

## Produit certifié

Commit produit principal : `f39944aeaaf3688f496a81f1df0d7dde8aa74692`.
HEAD de certification : `ffe2cf7546a79ea476c393a6251fc0aba2036ff1`.

Le delta entre les deux comprend uniquement :
- `.github/workflows/patient-indicators-cert.yml` ;
- `backend/tests/test_patient_indicators_explainable.py` ;
- `backend/tests/test_services_unit3.py` ;
- `backend/tests/test_services_unit4.py`.

Aucun fichier produit n'a changé après le commit produit principal.

## AFTER final

Patient Indicators Truth Certification #6 `32497490038` — **SUCCESS**.
Artifact `9452294425`.
Digest `sha256:7e568a5327f76bfab834bc23ea6eb4ec664eae97e3107a588d13bc879c022a14`.

Preuve runtime :
- captures AFTER : **15/15** ;
- overflow : **0/15** ;
- page errors : **0/15** ;
- HTTP 5xx : **0/15** ;
- `automatic_score = null` ;
- `automatic_grade = null` ;
- `assiduite_score = null` ;
- `solvabilite_score = null` ;
- `intelligence_score = null` ;
- tag cabinet manuel set/reset : contrat conservé ;
- justification NBA visible sur les 5 viewports ;
- hover mobile contenu à 360 et 320 px.

Exemple certifié runtime : situation financière `1 000 MAD`, source `Actes + paiements`, et message NBA `Antécédents médicaux non renseignés dans le dossier.` affiché au praticien.

## Inspection visuelle

BEFORE → mockup → AFTER inspecté sur les 15 captures.

### Améliorations validées

- disparition du cercle `/100` ;
- disparition de `Fantôme` ;
- repères factuels compacts dans la ligne patient ;
- hover plus lisible et contenu dans les petits viewports ;
- `Repères & actions` + provenance déterministe ;
- toast/action patient donne désormais la raison factuelle.

### Dette non bloquante

À 320/360 px, la liste patients conserve son layout étroit préexistant : certains contenus de ligne et boutons d'en-tête restent visuellement tronqués. Ce défaut était déjà visible dans le BEFORE et n'est pas créé par ce lot. Le nouveau hover ne déborde plus.

Score visuel final : **9,3/10**.

## Gates de certification produit

- Patient Indicators Truth #6 `32497490038` — SUCCESS ;
- CI #1531 `32497490220` — SUCCESS ;
- T2 Runtime Browser Certification #751 `32497490136` — SUCCESS ;
- Patient P7 Final Certification #50 `32497490547` — SUCCESS ;
- Patient P1 Architecture After #14 `32497490228` — SUCCESS ;
- Catalog Connected Truth Certification #24 `32497490107` — SUCCESS ;
- Patient Indicators BEFORE #12 `32497490154` — SUCCESS.

## Gates du HEAD closeout

HEAD closeout pré-merge : `bc1137011438b26bad7f340699c9f1b6f3e378c8`.

- Patient Indicators Truth #7 `32498981650` — SUCCESS ;
- CI #1533 `32498981685` — SUCCESS ;
- T2 #753 `32498981646` — SUCCESS ;
- Patient P7 #52 `32498981617` — SUCCESS ;
- Patient P1 Architecture After #15 `32498981643` — SUCCESS ;
- Catalog Connected Truth #26 `32498981615` — SUCCESS ;
- Patient Indicators BEFORE #13 `32498981616` — SUCCESS.

## Historique de diagnostic utile

- premiers runs : tests hérités continuaient d'exiger les anciens grades automatiques ;
- tests céphalométriques hérités continuaient d'exiger `stable/amélioration/dégradation` ; ils ont été réalignés ensemble sur le delta IMPA brut ;
- Truth #5 : backend ciblé 10/10, frontend ciblé 4/4, build vert ; l'AFTER a échoué uniquement parce que le harness cherchait la provenance via `body.innerText()` alors que le texte était bien monté dans le composant ;
- harness final corrigé pour cibler directement le texte de provenance ; Truth #6 est entièrement vert.

Après répétition des faux négatifs de tests hérités, la stratégie a été consolidée avant le run final afin d'éviter les micro-pushes successifs.

## Post-merge

PR #199 squash-mergée dans `master` : `b22e7bc9e7981eef54916c4e1412fa69ad612bf5`.

État canonique post-merge également consigné dans `docs/settings/INDICATEURS_PATIENT_EXPLICABLES_POSTMERGE.md`.

## Décision finale

**Indicateurs patient explicables = CLOSED — CERTIFIÉ — MERGED.**

Le chantier Réglages est crédité à **13/15 = 86,7 %**. Lot suivant : **Restauration guidée**, audit uniquement.

Aucun Vercel.
