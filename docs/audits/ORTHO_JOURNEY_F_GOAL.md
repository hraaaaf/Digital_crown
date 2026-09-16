# Lot F — Ortho Journey

## Goal

Créer, dans le dossier patient existant, une synthèse orthodontique longitudinale pour les patients avec `dossier.is_ortho_active=true`, sans créer un second moteur diagnostique ni une nouvelle source de vérité clinique.

La synthèse doit réutiliser les vérités déjà présentes :

- phases/progression : plan de traitement et étapes existantes ;
- contrôles : rendez-vous existants ;
- médias de progression : Media Core et timepoints T0/T1/T2 existants ;
- résultats : analyses céphalométriques existantes, sans recalcul ni nouvelle interprétation diagnostique.

## Succès observable

1. Un patient ortho actif voit une section `Parcours orthodontique` dans `Vue d’ensemble`.
2. La section expose uniquement des informations dérivées des API existantes et reste explicite quand une donnée manque.
3. Les raccourcis renvoient vers les surfaces existantes (média/céphalo/clinique) au lieu de les dupliquer.
4. Aucun modèle/table/migration DB n’est ajouté pour ce lot sauf preuve ultérieure qu’une donnée indispensable n’est pas dérivable.
5. BEFORE et AFTER sont capturés aux mêmes viewports : 390×844, 430×932, 768×1024, 1280×900 ; absence d’overflow horizontal, d’erreur runtime et de HTTP 5xx.
6. Les tests ciblés et les gates CI applicables sont verts avant closeout.

## Hors scope

- Ortho Diagnostic Builder V2 ;
- nouveaux calculs céphalométriques ;
- nouvelle vérité diagnostique ;
- nouvelle table média ;
- mutation du schéma ou des données cabinet ;
- déploiement.

## Référence / mockup fonctionnel

La nouvelle section reste compacte et s’insère au-dessus du `PatientJourney` existant dans `Vue d’ensemble` uniquement quand l’ortho est active.

```text
┌ Parcours orthodontique ──────────────────────────────────────────┐
│ Phase actuelle        Progression        Prochain contrôle       │
│ <phase ou indispo>    <x/y ou indispo>  <date ou non planifié>  │
│                                                                  │
│ Médias progression    Dernier résultat                           │
│ T0 · T1 · T2          Céphalo <date/statut ou indisponible>      │
│                                                                  │
│ [Voir médias]  [Voir céphalo]                                   │
└──────────────────────────────────────────────────────────────────┘

[Parcours patient existant — inchangé]
```

### Règles UX

- vérité > remplissage décoratif : aucun faux `0/0`, faux pourcentage ou faux statut ;
- `Indisponible` / `Non planifié` quand la source ne permet pas une conclusion ;
- mobile : cartes empilées, aucun scroll horizontal ;
- desktop/tablette : densité compacte, sans pousser la chronologie hors contexte ;
- aucune couleur de sévérité ou conclusion clinique inventée.

## Preuve attendue

- workflow visuel déterministe Lot F, avec BEFORE enregistré avant toute modification produit ;
- AFTER sur les mêmes viewports après implémentation ;
- comparaison explicite Target ↔ Render ;
- tests ciblés du composant et non-régression PatientDetails/PatientJourney ;
- scores `EXECUTION_SCORE` et `ADVERSARIAL_SCORE` appliqués selon la politique globale du repo.
