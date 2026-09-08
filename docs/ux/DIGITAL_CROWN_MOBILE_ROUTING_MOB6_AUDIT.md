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
- aucune régression volontaire sur les context bridges ;
- BEFORE/AFTER aux viewports 390×844, 430×932 et 768×1024.

## Baseline vérifiée
`SmartRootRouter` appliquait la détection mobile uniquement à `/`. Les deep-links directs `/patients`, `/agenda`, `/stock`, etc. contournaient donc cette politique et restaient dans le pipeline desktop. Une route `/mobile/*` inconnue pouvait également atteindre le wildcard desktop.

BEFORE final :
- run `34211312980` — SUCCESS ;
- checkout detached du commit pré-implémentation `d5bf9439e8eae60c1d0c8616a92353041fb5ac9a` ;
- artifact `10049990601` ;
- digest `sha256:c89e86a107100e1596187291f9650c12bf716ffcc95c225efd4e670230b1eef4` ;
- 9/9 probes : `/patients`, `/agenda`, `/stock` × 390/430/768 restent desktop ;
- onboarding mobile absent ; 0 overflow ; 0 page error.

## Implémentation certifiée
### Canonisation au bootstrap
`main.tsx` résout avant auth et rendu :
1. la règle mobile historique ;
2. une destination mobile pour les seuls chemins top-level couverts ;
3. un fallback mobile pour un `/mobile/*` inconnu.

La transition utilise `history.replaceState`, puis le runtime normal continue.

### Source unique de routes
`mobileRouting.ts` associe uniquement des chemins desktop à des destinations logiques. Les URLs sont résolues via `MOBILE_BRIDGE_ROUTES`.

`bridge.ts` inclut `waiting-room`.

### Scope certifié
`/dashboard`, `/agenda`, `/patients`, `/accounting`, `/stock`, `/approvisionnement`, `/bibliotheque`, `/salle-attente`, `/super-admin`.

### Scope volontairement préservé desktop
Patient ID, édition/archives patient, protocole bibliothèque, partenaire et produit Marketplace restent desktop tant que l’équivalent mobile ne peut pas conserver exactement l’entité ciblée.

## Certification finale
Run `34211780896` — SUCCESS sur HEAD `e62217739c14c46747c159d9c3be9f76668c7a30` :
- routing contract SUCCESS ;
- frontend build SUCCESS ;
- browser AFTER 390/430/768 SUCCESS ;
- `/patients`, `/agenda`, `/stock` → onboarding mobile si non appairé ;
- desktop login absent ;
- 0 overflow ; 0 page error ; 0 console error ;
- artifact `10050137272` ;
- digest `sha256:dc1e5a72d02f668cf537ec9fa28341940d34df7388603da6974eeac393d82ec7`.

Un run intermédiaire `34211284167` avait détecté un test obsolète : il attendait l’ancienne URL fallback sans `?tab=agenda`, alors que le produit utilisait correctement `MOBILE_BRIDGE_ROUTES.agenda`. Le test a été corrigé, sans modification produit.

## Risques préservés
- routes publiques/auth non redirigées ;
- `/mobile/onboarding` reste hors biométrie ;
- `MobileProtectedRoute` inchangé ;
- cache offline inchangé ;
- biométrie inchangée ;
- deep-links riches préservés ;
- aucun déploiement Vercel.

## Conclusion
L’ambiguïté MOB-6 est corrigée sur le scope sûr et certifié. La clôture produit dépend désormais de la PR, de son CI et du post-merge master.

Statut : `AUDIT VERIFIED — PRE-MERGE CERTIFIED`.
