# M6-D1 — Centre de notifications mobile — Closeout

Date : 2026-08-25
Statut : CLOSED

## Goal

Brancher la vérité `ProactiveAlert` existante sur l’expérience mobile appairée sans créer de seconde source de vérité, avec une UX tactile fiable et un cloisonnement RBAC des domaines sensibles.

## Succès certifié

- notifications non lues tenant-scopées via JWT mobile et appareil appairé ;
- badge et bottom sheet mobile ;
- actions `Lu` et snooze `+24 h` persistées sur `ProactiveAlert` ;
- stale GET race fail-safe ;
- contrôles critiques >= 48 px ;
- alertes financières filtrées pour les utilisateurs sans `accounting`/`payments` ;
- mutations non autorisées fail-closed en 404 ;
- aucun second moteur d’alertes ;
- AFTER 390 / 430 / 768 sans overlap, overflow horizontal ni erreur runtime.

## Base / BEFORE

- baseline master : `4d58c080569d0177e887deda6948d65026fe3887` ;
- BEFORE run : `32893435768` — SUCCESS ;
- prep initial : `32894190631` — SUCCESS ;
- diagnostic composant : `32896742941` — SUCCESS, 2/2 tests.

## Produit

- branche : `mobile/m6-d1-notification-center` ;
- PR : #256 ;
- portal + test permanent : `e0b684e5b8962b4914fb8aedcb9f7fe47dcc8ab5` ;
- HEAD produit final certifié : `cdac655b20b54e3a3cb7262fd1b5a634c9a30ede` ;
- merge réel : `101a6059919739bd508cd5e9fd26b5e33c9ca529`.

## Hardening confidentialité / RBAC

L’audit a identifié un défaut réel : certaines alertes financières générées par le scheduler pouvaient être lisibles par un utilisateur disposant seulement de `patients`.

Correction finale :

- `OVERDUE_PAYMENT*` ;
- `HIGH_VALUE_RISK*` ;
- `ORTHO_SEMESTER_*` ;

exigent désormais `accounting` ou `payments` pour le mobile. Le filtrage GET intervient avant `limit(20)`. Les mutations `Lu` / snooze non autorisées répondent 404 afin de ne pas révéler l’existence de l’alerte.

Preuve : privacy prep `32899871156` — SUCCESS (tests backend ciblés, test frontend, build, scope exact).

## AFTER exact-head

- run : `32901108250` — SUCCESS ;
- artifact : `9583139456` ;
- digest : `sha256:e3b30c86210e99c7f9adc49a8ff23be1efeb80924b4af7a56a9561ccc7d689a9` ;
- `productHead` : `cdac655b20b54e3a3cb7262fd1b5a634c9a30ede` ;
- 3/3 captures : 390 / 430 / 768 ;
- targets >= 48 px ;
- `Lu` et `+24 h` observés ;
- stale race exercée ;
- vérité serveur finale vide après actions ;
- zéro overlap ;
- zéro overflow horizontal ;
- zéro erreur runtime inattendue.

## CI exact-head finale

- CI `32901666809` — SUCCESS ;
- T2 Runtime Browser Certification `32901666811` — SUCCESS ;
- Catalog Connected Truth Certification `32901666807` — SUCCESS ;
- Patient P7 Final Certification `32901666803` — SUCCESS.

## Validation visuelle

AFTER 390 / 430 / 768 inspectés : bottom sheet propre, aucune collision avec la navigation basse, hiérarchie et lisibilité conservées.

Score visuel final : **9,6/10**.

## Non-objectifs / suite

M6-D1 ne certifie pas encore la chaîne push OS/PWA. L’audit D2 a confirmé que le runtime FCM historique est cabinet-wide : `DeviceToken` ne conserve que `employer_id`, alors que l’auth mobile dispose déjà d’un `MobilePairedDevice` lié à `user_id`, `employer_id` et révocation.

**Next : M6-D2 — push PWA/OS device-bound et permission-aware.**

## Déploiement

Aucun déploiement Vercel.