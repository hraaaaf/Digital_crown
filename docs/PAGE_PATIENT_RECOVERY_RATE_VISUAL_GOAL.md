# Page Patient — P0-E taux de recouvrement sans base facturée

## Goal visuel
Conserver strictement la carte KPI « Taux Recouvrement » et sa place, mais ne jamais afficher `100 %` lorsqu'aucun montant n'est facturé.

## Critères
- `total_billed > 0` : pourcentage calculé normalement.
- `total_billed == 0` : valeur principale `—` et sous-libellé `Non applicable`.
- Aucun nouveau badge, couleur d'alerte ou carte.
- Les cartes Facturé / Encaissé / Reste dû restent inchangées.
- 390, 430, 768 et 1280 px : aucun overflow nouveau.

## Wireframe
```text
┌─────────────────────────┐
│ TAUX RECOUVREMENT       │
│ —                       │
│ Non applicable          │
└─────────────────────────┘
```

## Preuve attendue
Avant : état synthétique 0 MAD facturé / 800 MAD encaissé montrant le comportement actuel.
Après : mêmes données et mêmes quatre viewports montrant `— / Non applicable`.
