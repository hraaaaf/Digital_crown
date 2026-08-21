# INDICATEURS PATIENT EXPLICABLES — GOAL

Date : 2026-08-21
Repo : `hraaaaf/Digital_crown`
Base BEFORE immuable : `e18597176a97805ae7839f2052340354257a0ae8`
Statut : **CERTIFIÉ PRODUIT — merge pending**

## Goal

Remplacer les jugements patient opaques ou surinterprétés par des repères factuels, sourcés et immédiatement actionnables pour le cabinet, sans dégrader Patient Journey ni les finances patient déjà fail-closed.

## Succès produit

1. La liste patients n'affiche plus de grade automatique Platinum / Gold / Silver / Bronze.
2. Aucun score numérique global ne mélange assiduité, imagerie, sécurité clinique et finance.
3. Les repères visibles disent ce qui s'est réellement passé : RDV terminés/annulés, facturé/encaissé/reste dû, absence éventuelle de RDV futur.
4. Toute donnée financière insuffisante reste `Indéterminé`, jamais convertie en faux zéro.
5. La segmentation manuelle reste possible mais est explicitement présentée comme **tag cabinet manuel**, jamais comme conclusion calculée.
6. Le hover patient conserve les faits utiles (dernière visite, prochain RDV, vigilance, informations financières) mais retire le score d'intelligence et le vocabulaire trompeur `IA` / `Analyse clinique` lorsqu'il s'agit de règles déterministes.
7. Le moteur NBA conserve les règles déterministes utiles, mais les titres/messages décrivent le fait déclencheur et sa fenêtre d'observation au lieu d'inférer un comportement (`no-show`, `perte patient`, etc.).
8. `Fantôme` devient un libellé opérationnel neutre, de type `Sans RDV futur` / `À replanifier`, avec motif explicite.
9. La variation céphalométrique IMPA peut être affichée comme variation brute, mais aucune hausse/baisse seule ne doit être qualifiée automatiquement d'`amélioration` ou `dégradation`.
10. `FlashSummary` mort (`return null`) est retiré de la page patient et de ses imports si aucun consommateur réel n'est trouvé.

## Contraintes préservées

- Tenant isolation et permissions patient inchangées.
- Patient Journey : comportement et doctrine fail-closed préservés.
- Patient Finances : comportement et doctrine fail-closed préservés.
- Aucun diagnostic clinique automatique ajouté.
- Aucun LLM requis pour ces indicateurs.
- Aucun Vercel.

## Goal visuel

Référence : `docs/settings/INDICATEURS_PATIENT_EXPLICABLES_MOCKUP.svg`.

### Liste patients

- Le nom reste visuellement dominant.
- Remplacer la couronne/grade par 2 à 3 repères compacts maximum.
- Les repères doivent être textuels et compréhensibles sans légende : ex. `3 RDV honorés · 1 annulé`, `800 / 1 000 MAD encaissés`, `Sans RDV futur`.
- Un tag manuel éventuel doit porter explicitement la mention `Tag cabinet` dans son détail.
- Aucun badge ne doit donner une valeur morale ou clinique au patient.

### Hover patient

- Titre `Repères du dossier`.
- Pas de score circulaire `/100`.
- Conserver dernière visite / prochain RDV / vigilances factuelles.
- Chaque alerte/recommandation doit exposer une justification courte ou une donnée source directement dans le texte.
- Remplacer `Alertes IA & Suggestion` par `Repères & actions`.
- Remplacer `Assistant Virtuel ODF • Temps réel` par `Données du dossier • règles déterministes`.

### Page patient

- Aucun toast silencieux prétendant une `Next Best Action` sans raison visible.
- Si une action est proposée, montrer le fait déclencheur dans le message.
- Journey et Finances ne sont pas redessinés hors nécessité.

## Viewports de preuve

Même jeu BEFORE / AFTER :
- 1440 × 1200
- 768 × 1200
- 390 × 1200
- 360 × 1200
- 320 × 1200

Surfaces :
1. liste patients ;
2. hover patient ;
3. page patient / suivi.

## Preuve acquise

### BEFORE

Patient Indicators BEFORE #12 `32497490154` — **SUCCESS**.
Artifact `9452286533`.
Digest `sha256:5db90db3c19348e65d96345d6f021d32f7a72cbe486d0fd4a80d06c768bdcd23`.

### AFTER

Patient Indicators Truth Certification #6 `32497490038` — **SUCCESS**.
Artifact `9452294425`.
Digest `sha256:7e568a5327f76bfab834bc23ea6eb4ec664eae97e3107a588d13bc879c022a14`.

- 15/15 captures AFTER ;
- 0 overflow horizontal ;
- 0 page error ;
- 0 HTTP 5xx ;
- score automatique : `null` ;
- grade automatique : `null` ;
- sous-scores assiduité/solvabilité : `null` ;
- intelligence score : `null` ;
- tag cabinet manuel préservé ;
- justification NBA visible sur 5/5 viewports ;
- hover mobile corrigé à 360/320 px ;
- score visuel : **9,3/10**.

Dette visuelle non bloquante : la liste patients conserve à 320/360 px un layout étroit/tronqué déjà présent dans le BEFORE. Le nouveau hover, lui, reste contenu dans le viewport.

## Gates de certification

HEAD de certification : `ffe2cf7546a79ea476c393a6251fc0aba2036ff1`.

- Patient Indicators Truth #6 `32497490038` — SUCCESS ;
- CI #1531 `32497490220` — SUCCESS ;
- T2 #751 `32497490136` — SUCCESS ;
- Patient P7 #50 `32497490547` — SUCCESS ;
- Patient P1 Architecture After #14 `32497490228` — SUCCESS ;
- Catalog Connected Truth #24 `32497490107` — SUCCESS.

Produit principal : `f39944aeaaf3688f496a81f1df0d7dde8aa74692`.
Le delta `f39944a… → ffe2cf7…` ne touche que le workflow de certification et des tests hérités ; aucun fichier produit n'est modifié.

## Décisions audit verrouillées

- Patient Journey : **GARDER**.
- Patient Finances : **GARDER**.
- Score VIP automatique : **SUPPRIMER DE L'UX / REFONDRE EN REPÈRES FACTUELS**.
- Intelligence score `/100` : **SUPPRIMER**.
- NBA déterministe : **GARDER / EXPLIQUER / RENOMMER**.
- Badge `Fantôme` : **GARDER LA DÉTECTION / RENOMMER**.
- Jugement IMPA `amélioration/dégradation` par signe seul : **SUPPRIMER LE JUGEMENT**.
- FlashSummary mort : **SUPPRIMER APRÈS PREUVE DE NON-CONSOMMATION**.
