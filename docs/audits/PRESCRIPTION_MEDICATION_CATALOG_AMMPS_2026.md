# Prescription Medication Catalog — AMMPS 2026 supplement

Status: ACTIVE

## Goal

Après saisie exacte `ACIG` dans l’Ordonnance, afficher une présentation documentaire vérifiée d’ACIGAM sans sélectionner automatiquement de médicament, sans ajouter de règle clinique et sans falsifier le snapshot CNOPS 2021.

## Success

- `GET /api/medications/search?q=ACIG` retourne au moins une présentation ACIGAM documentée ;
- ACIGAM porte une provenance AMMPS explicite ;
- la source CNOPS historique reste inchangée et ses identifiants restent stables ;
- l’UI n’affiche plus un bandeau CNOPS 2021 pour une présentation provenant de l’AMMPS ;
- aucune présentation n’est sélectionnée automatiquement ;
- tests ciblés + régression générale applicables verts ;
- AFTER 1280x900 sur le même scénario que la baseline BEFORE.

## Sources vérifiées

Source primaire actuelle : AMMPS, `Répertoire Marocain des Médicaments Génériques`, édition projet janvier 2026.

Entrée intégrée :
- ACIGAM 200 MG COMPRIME SECABLE BOITE DE 20
- DCI : ACIDE TIAPROFENIQUE
- EPI : BOTTU
- EAN13 : 6118000041986
- voie : ORALE

Cross-check réglementaire : Bulletin Officiel marocain n°7262 du 4 janvier 2024, qui liste ACIGAM 100 mg et 200 mg dans l’annexe de révision des prix.

Aucune disponibilité instantanée en pharmacie n’est déduite de ces sources.

## BEFORE

Baseline dédiée : PR #506, master de départ `647f682ea71e026e7e9604fc0ca419e2ae6f7a44`.

Scénario : ouvrir Ordonnance, saisir exactement `ACIG`, ne rien sélectionner, capturer 1280x900.

État attendu et déjà observé dans le test précédent #503 : requête API 200, zéro suggestion visible car ACIGAM est absent du snapshot CNOPS 2021 embarqué.

## Mockup / référence cible

```text
MÉDICAMENT 01
[ 🔍 ACIG                                      ]
┌──────────────────────────────────────────────┐
│ Référentiels documentaires marocains         │
│ provenance indiquée par présentation         │
├──────────────────────────────────────────────┤
│ ACIGAM 200 MG COMPRIME SECABLE BOITE DE 20  │  200 MG
│ ACIDE TIAPROFENIQUE                          │  COMPRIME SECABLE
│ AMMPS · 2026-01 · statut actuel non certifié │
└──────────────────────────────────────────────┘
```

Aucun bouton d’application automatique, aucune posologie, aucune recommandation thérapeutique.

## Implementation contract

- conserver `medications_ma.json` comme snapshot CNOPS 2021 inchangé ;
- ajouter un supplément AMMPS séparé ;
- provenance par enregistrement ;
- priorité à la source AMMPS lorsqu’une présentation documentaire identique existe dans plusieurs sources ;
- identifiants CNOPS existants inchangés ;
- identifiants AMMPS avec préfixe distinct ;
- fail closed si source ou donnée absente.

## Closeout evidence

À compléter uniquement après tests, capture AFTER, comparaison BEFORE/AFTER, CI exacte et revue visuelle.
