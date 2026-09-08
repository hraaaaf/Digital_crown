# DIGITAL CROWN — MOB-6 Canonisation du routage mobile — Proof

## Goal
Supprimer l’ambiguïté entre la PWA mobile dédiée et le shell desktop responsive sans casser desktop, onboarding, offline/cache, biométrie, context bridges ni routes publiques.

## Baseline
- master : `301454a367b8b7952d0fef94e86c40e8e4a248e2` ;
- branche : `ux/mobile-routing-mob6` ;
- commit pré-implémentation figé pour BEFORE : `d5bf9439e8eae60c1d0c8616a92353041fb5ac9a`.

## BEFORE — VERIFIED
Premier run `34210241473` : artifact produit mais run FAILURE à cause d’une assertion de harness trop stricte qui attendait `/login`.

Le report brut avait déjà établi sur 9/9 probes (3 routes × 3 viewports) :
- routes : `/patients`, `/agenda`, `/stock` ;
- viewports : 390×844 / 430×932 / 768×1024 ;
- HTTP 200 ;
- pathname inchangé sur la route desktop d’entrée ;
- onboarding mobile absent ;
- horizontal overflow absent ;
- page errors = 0.

Le harness a été corrigé puis rejoué en checkout detached du commit pré-implémentation exact.

Recertification finale BEFORE :
- run `34211312980` — SUCCESS ;
- code testé : `d5bf9439e8eae60c1d0c8616a92353041fb5ac9a` ;
- artifact `10049990601` ;
- digest `sha256:c89e86a107100e1596187291f9650c12bf716ffcc95c225efd4e670230b1eef4` ;
- 9/9 probes conformes au comportement BEFORE ;
- 0 overflow ;
- 0 page error.

## Implémentation
- détection mobile réutilise la règle historique `width <= 768 || mobile user-agent` ;
- canonisation exécutée dans `main.tsx` avant auth et rendu ;
- `history.replaceState` bascule les seules routes desktop top-level disposant d’un équivalent mobile prouvé ;
- destinations résolues via `MOBILE_BRIDGE_ROUTES` ;
- `waiting-room` ajouté au bridge canonique ;
- `/mobile/*` inconnu reste dans le namespace mobile et retombe vers Agenda mobile ;
- routes mobiles connues inchangées ;
- `MobileProtectedRoute`, cache offline et `MobileBiometricGate` inchangés ;
- routes publiques/auth non redirigées ;
- deep-links riches non redirigés si leur contexte exact ne peut pas être préservé.

## Scope top-level
- `/dashboard` → Agenda mobile ;
- `/agenda` → Agenda mobile ;
- `/patients` → Patients mobile ;
- `/accounting` → Finance mobile ;
- `/stock` → Stock mobile ;
- `/approvisionnement` → Marketplace mobile ;
- `/bibliotheque` → Bibliothèque mobile ;
- `/salle-attente` → Salle d’attente mobile ;
- `/super-admin` → SuperAdmin mobile.

## Deep-links riches préservés desktop
Exemples : `/patients/:id`, édition/archives patient, `/bibliotheque/:code`, partenaire ou produit Marketplace. Aucun redirect n’est revendiqué tant que l’entité ciblée ne peut pas être conservée exactement côté mobile.

## AFTER initial certifié
Run `34210579881` sur HEAD `fcbdb8afb590f29c7d923743ca75b7eec017885f` :
- routing contract SUCCESS ;
- frontend build SUCCESS ;
- browser AFTER 390/430/768 SUCCESS ;
- `/patients`, `/agenda`, `/stock` → `/mobile/onboarding` en état non appairé ;
- desktop login absent ;
- onboarding mobile présent ;
- overflow = 0 ; page errors = 0 ; console errors = 0.

Artifact `10049662623` ; digest `sha256:aa08739d1f5430588d0c9587f69d7ed36bcef28e00041edabc1e90d5c2298edd`.

## Certification finale AFTER
Le refactor vers la source unique `MOBILE_BRIDGE_ROUTES` a révélé un test obsolète : le produit renvoyait correctement `MOBILE_BRIDGE_ROUTES.agenda` (`/mobile/dashboard?tab=agenda`) mais le test attendait encore `/mobile/dashboard`. Le test, pas le produit, a été corrigé au commit `e62217739c14c46747c159d9c3be9f76668c7a30`.

Run final : `34211780896` — **QUEUED au dernier contrôle**.

## Comparaison visuelle
BEFORE : entrée mobile directe sur une route desktop → surface/loader desktop, sans bascule vers le parcours mobile.

AFTER : même entrée → onboarding mobile canonique en état non appairé, sans chevauchement aux trois viewports.

Score visuel/comportemental provisoire : **9.4/10**, à confirmer sur la certification finale.

## Déploiement
Aucun déploiement Vercel.

## Gate pré-merge
BEFORE final est satisfait. MOB-6 ne devient `PRE-MERGE CERTIFIED` qu’après :
1. SUCCESS du run AFTER final `34211780896` ;
2. artifact/digest final AFTER relevés.

Statut : `IMPLEMENTED — BEFORE VERIFIED — FINAL AFTER CERTIFICATION PENDING — NOT YET PRE-MERGE CERTIFIED`.
