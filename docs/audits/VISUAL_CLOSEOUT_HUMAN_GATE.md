# Visual Closeout Human Gate

## Goal

Aucun lot modifiant l'UI/UX ou un rendu visuel produit ne peut être déclaré validé ou clos sans validation humaine explicite des captures AFTER par le propriétaire du projet.

## Succès

Pour chaque lot visuel :

1. captures BEFORE pertinentes conservées ;
2. Goal visuel et référence/mockup explicités ;
3. implémentation terminée ;
4. tests techniques adaptés exécutés ;
5. captures AFTER produites aux mêmes viewports et mêmes états ;
6. comparaison BEFORE / AFTER + score visuel fournis ;
7. captures remises au propriétaire ;
8. propriétaire valide explicitement ;
9. closeout seulement ensuite.

## Gate humain

Avant validation du propriétaire :

`BLOQUÉ HUMAIN — VALIDATION CAPTURES`

Cet état n'est pas un échec CI. Il signifie que la preuve visuelle est prête mais que le closeout attend la validation humaine.

Un test CI vert, un build vert ou un smoke vert ne remplacent jamais cette validation visuelle.

Toute nouvelle modification visuelle après validation invalide la validation précédente et exige de nouvelles captures AFTER.

## Preuve minimale

- BEFORE ;
- AFTER ;
- mêmes viewports / mêmes états ;
- tests techniques ;
- comparaison et écarts ;
- score visuel ;
- validation explicite du propriétaire.

## Implémentation

La règle d'exécution canonique est `.claude/rules/visual-closeout-human-validation.md`.

Il n'existe volontairement aucun branch-protection gate ou label GitHub obligatoire pour cette règle : c'est un human gate de closeout piloté par l'agent et le propriétaire.
