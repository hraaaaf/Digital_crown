# M6-D1 — Centre de notifications mobile — Goal

## Goal

Donner au mobile Digital Crown un centre de notifications tactile, lisible et réellement alimenté par la source `ProactiveAlert`, sans créer de nouvelle vérité métier.

## Succès

- une entrée Notifications est visible dans le header mobile avec badge non-lu ;
- le panneau affiche les alertes non lues du cabinet via une façade JWT mobile sécurisée ;
- aucune alerte d'un autre tenant n'est lisible ou modifiable ;
- lecture et report 24 h utilisent la même ligne `ProactiveAlert` ;
- targets critiques >= 48 px ;
- états loading / vide / erreur explicites ;
- aucune donnée clinique n'est inventée ;
- 390 / 430 / 768 sans overflow ni erreur runtime ;
- le transport OS reste séparé de la source de vérité et sera traité en M6-D2 après résolution du HTTPS cabinet.

## Preuve attendue

Tests backend tenant/mobile + build frontend + AFTER 390/430/768 + inspection visuelle + CI exact-head.
