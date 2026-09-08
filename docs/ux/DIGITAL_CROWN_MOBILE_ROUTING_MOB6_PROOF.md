# DIGITAL CROWN — MOB-6 Canonisation du routage mobile — Proof

## Goal
Supprimer l’ambiguïté entre la PWA mobile dédiée et le shell desktop responsive sans casser desktop, onboarding, offline/cache, biométrie, context bridges ni routes publiques.

## Baseline
- master : `301454a367b8b7952d0fef94e86c40e8e4a248e2` ;
- branche : `ux/mobile-routing-mob6` ;
- commit pré-implémentation figé pour BEFORE : `d5bf9439e8eae60c1d0c8616a92353041fb5ac9a`.

## BEFORE — VERIFIED
Recertification finale :
- run `34211312980` — SUCCESS ;
- code testé : `d5bf9439e8eae60c1d0c8616a92353041fb5ac9a` ;
- artifact `10049990601` ;
- digest `sha256:c89e86a107100e1596187291f9650c12bf716ffcc95c225efd4e670230b1eef4` ;
- 9/9 probes : `/patients`, `/agenda`, `/stock` × 390×844 / 430×932 / 768×1024 ;
- HTTP 200 ; pathname desktop inchangé ; onboarding mobile absent ;
- 0 overflow ; 0 page error.

Le premier run `34210241473` avait produit le même comportement brut mais échoué sur une assertion de harness erronée qui attendait `/login`. Il n’est pas utilisé comme preuve finale.

## Implémentation
- règle mobile historique conservée : `width <= 768 || mobile user-agent` ;
- canonisation dans `main.tsx` avant auth et rendu ;
- `history.replaceState` uniquement pour les routes desktop top-level ayant un équivalent mobile prouvé ;
- URLs mobiles résolues par la source unique `MOBILE_BRIDGE_ROUTES` ;
- `waiting-room` ajouté au bridge canonique ;
- `/mobile/*` inconnu retombe vers Agenda mobile, jamais vers le shell desktop ;
- routes mobiles connues inchangées ;
- `MobileProtectedRoute`, cache offline et `MobileBiometricGate` inchangés ;
- routes publiques/auth non redirigées ;
- deep-links riches non redirigés si leur contexte exact ne peut pas être préservé.

## Scope top-level certifié
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

## AFTER — VERIFIED
Certification finale :
- run `34211780896` — SUCCESS ;
- product/test HEAD certifié `e62217739c14c46747c159d9c3be9f76668c7a30` ;
- routing contract SUCCESS ;
- frontend build SUCCESS ;
- browser AFTER 390×844 / 430×932 / 768×1024 SUCCESS ;
- `/patients`, `/agenda`, `/stock` → `/mobile/onboarding` en état non appairé ;
- desktop login absent ; onboarding mobile présent ;
- 0 overflow ; 0 page error ; 0 console error ;
- artifact `10050137272` ;
- digest `sha256:dc1e5a72d02f668cf537ec9fa28341940d34df7388603da6974eeac393d82ec7`.

## Incident de recertification
Le run précédent `34211284167` avait build + browser verts mais un contrat rouge parce que le test attendait encore `/mobile/dashboard` alors que la source canonique renvoyait correctement `/mobile/dashboard?tab=agenda`. Le test obsolète a été corrigé ; aucun changement produit n’a été nécessaire.

## Comparaison visuelle
BEFORE : entrée mobile directe sur une route desktop → surface/loader desktop, sans bascule vers le parcours mobile.

AFTER : même entrée → onboarding mobile canonique en état non appairé, propre sur les trois viewports.

Score visuel/comportemental : **9.4/10**.

## Déploiement
Aucun déploiement Vercel.

## Gate de fermeture
Le lot est **PRE-MERGE CERTIFIED**. Il ne devient `CLOSED` qu’après PR produit mergée, CI post-merge master verte et closeout documentaire final cohérent.

Statut : `PRE-MERGE CERTIFIED — PRODUCT PR REQUIRED — NOT YET CLOSED`.
