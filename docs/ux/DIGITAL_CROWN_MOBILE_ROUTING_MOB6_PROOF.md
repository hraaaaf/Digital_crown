# DIGITAL CROWN — MOB-6 Canonisation du routage mobile — Proof

## Goal
Supprimer l’ambiguïté entre la PWA mobile dédiée et le shell desktop responsive sans casser desktop, onboarding, offline/cache, biométrie, context bridges ni routes publiques.

## Baseline
- master : `301454a367b8b7952d0fef94e86c40e8e4a248e2` ;
- branche : `ux/mobile-routing-mob6` ;
- commit pré-implémentation figé pour BEFORE : `d5bf9439e8eae60c1d0c8616a92353041fb5ac9a`.

## BEFORE
Premier run `34210241473` : artifact produit mais run FAILURE à cause d’une assertion de harness trop stricte qui attendait `/login`.

Le report brut a néanmoins établi sur 9/9 probes (3 routes × 3 viewports) :
- routes : `/patients`, `/agenda`, `/stock` ;
- viewports : 390×844 / 430×932 / 768×1024 ;
- HTTP 200 ;
- le pathname reste exactement la route desktop d’entrée ;
- onboarding mobile absent ;
- horizontal overflow absent ;
- page errors = 0.

Artifact initial : `10049516548` ; digest `sha256:8dd859d17c19c8ca42d2b67645e5f816d7731a749dbff950cba650e03f6ab85c`.

Le harness a été corrigé et le workflow recertifie explicitement le commit pré-implémentation exact après checkout detached.

Recertification finale BEFORE : run `34211312980` — **IN PROGRESS au dernier contrôle**.

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

Après refactor vers la source unique `MOBILE_BRIDGE_ROUTES`, une certification finale a été relancée : run `34211284167` sur HEAD `0214dfe89a7198d54e1f5e7f040b29350a31fc4b` — **IN PROGRESS au dernier contrôle**.

## Comparaison visuelle
BEFORE : entrée mobile directe sur une route desktop → surface/loader desktop, sans bascule vers le parcours mobile.

AFTER : même entrée → onboarding mobile canonique en état non appairé, sans chevauchement aux trois viewports.

Score visuel/comportemental provisoire : **9.4/10**, à confirmer sur la certification finale.

## Déploiement
Aucun déploiement Vercel.

## Gate de fermeture
MOB-6 ne peut pas être déclaré pré-merge certifié avant :
1. SUCCESS de la recertification BEFORE exacte `34211312980` ;
2. SUCCESS de la certification AFTER finale `34211284167` ;
3. artifact/digest final AFTER relevés.

Statut : `IMPLEMENTED — FINAL CERTIFICATION IN PROGRESS — NOT YET PRE-MERGE CERTIFIED`.
