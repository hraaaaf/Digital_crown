# DIGITAL CROWN — MOB-6 Canonisation du routage mobile — Proof

## Goal
Supprimer l’ambiguïté entre la PWA mobile dédiée et le shell desktop responsive sans casser desktop, onboarding, offline/cache, biométrie, context bridges ni routes publiques.

## Baseline
- master initial : `301454a367b8b7952d0fef94e86c40e8e4a248e2` ;
- branche produit : `ux/mobile-routing-mob6` ;
- commit pré-implémentation BEFORE : `d5bf9439e8eae60c1d0c8616a92353041fb5ac9a`.

## BEFORE — VERIFIED
- run `34211312980` — SUCCESS ;
- artifact `10049990601` ;
- digest `sha256:c89e86a107100e1596187291f9650c12bf716ffcc95c225efd4e670230b1eef4` ;
- 9/9 probes : `/patients`, `/agenda`, `/stock` × 390×844 / 430×932 / 768×1024 ;
- HTTP 200 ; pathname desktop inchangé ; onboarding mobile absent ;
- 0 overflow ; 0 page error.

## Implémentation certifiée
- règle mobile historique conservée ;
- canonisation dans `main.tsx` avant auth/rendu ;
- `history.replaceState` uniquement pour les routes desktop top-level ayant un équivalent mobile prouvé ;
- source unique `MOBILE_BRIDGE_ROUTES` ;
- `waiting-room` ajouté au bridge ;
- `/mobile/*` inconnu retombe vers Agenda mobile ;
- routes publiques/auth non redirigées ;
- deep-links riches non redirigés sans conservation exacte du contexte.

## AFTER — VERIFIED
- run `34211780896` — SUCCESS ;
- HEAD certifié `e62217739c14c46747c159d9c3be9f76668c7a30` ;
- routing contract SUCCESS ;
- frontend build SUCCESS ;
- browser 390×844 / 430×932 / 768×1024 SUCCESS ;
- `/patients`, `/agenda`, `/stock` → onboarding mobile en état non appairé ;
- 0 overflow ; 0 page error ; 0 console error ;
- artifact `10050137272` ;
- digest `sha256:dc1e5a72d02f668cf537ec9fa28341940d34df7388603da6974eeac393d82ec7` ;
- score visuel/comportemental **9.4/10**.

## PR / CI / merge
- PR produit `#372` ;
- HEAD final PR `8904dae5d82e218d5c73273042d85b966d929f11` ;
- CI PR `34212226491` — SUCCESS ;
- T2 `34212226402` — SUCCESS ;
- merge exact `97546777e3b4adbb8a670559553c1079aad4c2e2` ;
- post-merge master `34226941958` — **IN PROGRESS au dernier contrôle**.

## Déploiement
Aucun déploiement Vercel.

## Gate de fermeture
MOB-6 ne devient `CLOSED` qu’après SUCCESS du post-merge master `34226941958`, mise à jour documentaire finale cohérente, merge du closeout et vérification du master final.

Statut : `MERGED — POST-MERGE MASTER PENDING — NOT YET CLOSED`.
