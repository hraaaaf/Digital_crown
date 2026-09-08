# DIGITAL CROWN — MOB-6 Canonisation du routage mobile — Référence

## Référence comportementale
La règle UX cible est simple : une URL doit ouvrir la surface canonique correspondant au contexte, pas une version concurrente selon la manière dont l’utilisateur est arrivé.

### Mobile
- namespace canonique : `/mobile/*` ;
- dashboard mobile : `/mobile/dashboard?tab=<tab>` ;
- onboarding : `/mobile/onboarding` ;
- SuperAdmin : `/mobile/superadmin` ;
- route mobile inconnue : fallback mobile explicite vers `/mobile/dashboard`, jamais vers le shell desktop.

### Desktop
- les routes historiques restent inchangées ;
- aucun redirect mobile n’est appliqué sur desktop ;
- les routes sans équivalent mobile démontré restent sur leur surface desktop.

### Préservation du contexte
La redirection mobile doit utiliser la destination déjà matérialisée dans `MOBILE_BRIDGE_ROUTES` quand elle existe, afin d’éviter de recréer une seconde table divergente.

## Critère visuel
AFTER doit montrer la même bottom-nav canonique et le même shell mobile aux viewports 390×844, 430×932 et 768×1024, sans apparition transitoire du shell desktop, sans overflow, sans erreur page/console.

Statut : `REFERENCE LOCKED — IMPLEMENTATION PENDING`.
