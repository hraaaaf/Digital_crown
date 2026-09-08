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
- aucun deep-link riche n’est redirigé si son contexte ne peut pas être préservé ;
- aucune régression sur les context bridges ;
- BEFORE/AFTER aux viewports 390×844, 430×932 et 768×1024 avant clôture.

## Faits baseline vérifiés

### Entrée racine
`SmartRootRouter` calcule `isMobile` via `window.innerWidth <= 768` ou user-agent mobile. Depuis `/`, un mobile est redirigé vers `/mobile/dashboard`.

### Ambiguïté 1 — routes desktop directes sur mobile
La détection mobile n’était appliquée qu’à `/`. Une navigation directe vers `/patients`, `/agenda`, `/stock`, `/approvisionnement`, etc. passait par le pipeline desktop au lieu d’une politique d’entrée mobile canonique.

BEFORE final :
- run `34211312980` — SUCCESS ;
- checkout detached du commit pré-implémentation exact `d5bf9439e8eae60c1d0c8616a92353041fb5ac9a` ;
- artifact `10049990601` ;
- digest `sha256:c89e86a107100e1596187291f9650c12bf716ffcc95c225efd4e670230b1eef4` ;
- 9/9 probes : `/patients`, `/agenda`, `/stock` restent sur leurs chemins desktop aux viewports 390/430/768 ;
- onboarding mobile absent ;
- zéro overflow ;
- zéro page error.

Le run initial `34210241473` avait échoué uniquement sur une assertion de harness erronée (`/login`) malgré le même comportement brut observé ; il n’est pas utilisé comme preuve finale.

### Ambiguïté 2 — wildcard `/mobile/*`
Les routes mobiles explicites sont `/mobile/onboarding`, `/mobile/dashboard`, `/mobile/context`, `/mobile/dentists`, `/mobile/superadmin`. Une route `/mobile/...` inconnue pouvait auparavant traverser le wildcard global desktop.

### Bootstrap mobile
`main.tsx` appliquait le thème/runtime mobile uniquement si le pathname initial commençait déjà par `/mobile`.

### Tests existants
`pwaApiNavigation.test.ts` protège le fallback `/api/*`, mais aucun contrat dédié ne verrouillait la séparation mobile/desktop.

## Implémentation

### Politique canonique au bootstrap
`main.tsx` résout maintenant, avant auth et avant rendu :
1. si le device correspond à la règle mobile existante ;
2. si le pathname desktop top-level possède un équivalent mobile prouvé ;
3. si un pathname `/mobile/*` inconnu doit être normalisé.

Le changement utilise `history.replaceState`, puis poursuit le bootstrap normal. `MobileProtectedRoute`, cache offline et `MobileBiometricGate` restent inchangés.

### Source de vérité unique
`mobileRouting.ts` associe des routes desktop top-level à des destinations logiques puis résout l’URL via `MOBILE_BRIDGE_ROUTES`. Il n’existe pas de seconde table d’URLs mobiles.

`bridge.ts` inclut désormais `waiting-room`, ce qui couvre `/salle-attente` sans URL parallèle.

### Scope volontairement limité
Redirections top-level : `/dashboard`, `/agenda`, `/patients`, `/accounting`, `/stock`, `/approvisionnement`, `/bibliotheque`, `/salle-attente`, `/super-admin`.

Deep-links non redirigés tant que leur contexte exact ne peut pas être conservé : patient ID, archives/édition patient, protocole, partenaire, produit.

## Certification AFTER
Run initial `34210579881` : contrat, build et AFTER 390/430/768 SUCCESS, artifact `10049662623`, digest `sha256:aa08739d1f5430588d0c9587f69d7ed36bcef28e00041edabc1e90d5c2298edd`.

Après refactor vers `MOBILE_BRIDGE_ROUTES`, le run `34211284167` a confirmé build + browser AFTER mais a détecté un test obsolète : le fallback produit retournait correctement la route Agenda canonique avec `?tab=agenda`, alors que le test attendait l’ancienne URL sans query. Le test a été corrigé au commit `e62217739c14c46747c159d9c3be9f76668c7a30`.

Certification finale : run `34211780896` ; contrat et build SUCCESS au dernier contrôle, browser AFTER encore en cours.

## Risques préservés
- routes publiques/auth non redirigées ;
- `/mobile/onboarding` non protégé par biométrie ;
- `MobileProtectedRoute` inchangé ;
- cache offline inchangé ;
- biométrie inchangée ;
- deep-links riches préservés ;
- aucun déploiement Vercel.

Statut : `AUDIT VERIFIED — BEFORE VERIFIED — IMPLEMENTED — FINAL AFTER BROWSER PENDING`.
