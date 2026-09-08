# DIGITAL CROWN — MOB-6 Canonisation du routage mobile — Audit

## Baseline
- master : `301454a367b8b7952d0fef94e86c40e8e4a248e2`
- branche : `ux/mobile-routing-mob6`

## Goal
Supprimer l’ambiguïté entre la PWA mobile dédiée et le shell desktop responsive, sans casser l’accès desktop, l’onboarding, l’offline, la biométrie, les context bridges ni les routes publiques.

## Succès observable
- une entrée mobile ne tombe plus silencieusement dans le shell desktop pour les parcours déjà couverts par la PWA mobile ;
- les routes `/mobile/*` inconnues ne retombent pas dans le shell desktop ;
- les routes desktop restent utilisables sur desktop ;
- onboarding, appairage, cache offline et biométrie restent inchangés fonctionnellement ;
- les règles de redirection sont testées explicitement ;
- aucune régression sur les context bridges ;
- BEFORE/AFTER aux viewports 390×844, 430×932 et 768×1024 avant toute clôture visuelle.

## Faits vérifiés

### Entrée racine
`SmartRootRouter` calcule `isMobile` via `window.innerWidth <= 768` ou user-agent mobile. Depuis `/`, un mobile est redirigé vers `/mobile/dashboard`.

### Ambiguïté 1 — routes desktop directes sur mobile
La détection mobile n’est appliquée qu’à `/`. Une navigation directe vers `/patients`, `/agenda`, `/stock`, `/approvisionnement`, etc. passe par `ProtectedRoute` puis `ProtectedRoutes` et rend le shell desktop `MainLayout`, même sur un viewport/user-agent mobile.

Conséquence : le produit possède deux expériences concurrentes selon l’URL d’entrée, pas selon une politique de routage canonique.

### Ambiguïté 2 — wildcard `/mobile/*`
Les seules routes mobiles explicites sont :
- `/mobile/onboarding`
- `/mobile/dashboard`
- `/mobile/context`
- `/mobile/dentists`
- `/mobile/superadmin`

Le wildcard global `/*` reste ensuite actif. Une route `/mobile/...` non reconnue peut donc traverser le pipeline desktop `ProtectedRoute`/`ProtectedRoutes` au lieu d’être confinée au domaine mobile.

### Bootstrap mobile
`main.tsx` applique le thème/runtime mobile uniquement si `window.location.pathname.startsWith('/mobile')`.

Conséquence : un téléphone ouvrant directement une route desktop protégée ne reçoit pas le bootstrap runtime mobile et reste dans le shell desktop.

### Tests existants
`pwaApiNavigation.test.ts` protège uniquement le fallback `/api/*`. Aucun contrat de test dédié ne verrouille actuellement la séparation mobile/desktop ni le comportement des routes `/mobile/*` inconnues.

## Risques à préserver
- ne pas rediriger les routes publiques marketing/auth sans intention prouvée ;
- ne pas casser `/mobile/onboarding` ;
- ne pas contourner `MobileProtectedRoute` ;
- ne pas affaiblir `MobileBiometricGate` ;
- ne pas casser l’accès cache offline ;
- ne pas inventer une correspondance desktop→mobile pour une fonction qui n’a pas de surface mobile canonique.

## Conclusion audit
L’ambiguïté annoncée par MOB-6 est confirmée. Le correctif doit canoniser la politique d’entrée et isoler le namespace `/mobile/*`, sans faire un simple redirect global de toutes les routes desktop vers `/mobile/dashboard`.

Statut : `AUDIT VERIFIED — IMPLEMENTATION NOT STARTED`.
