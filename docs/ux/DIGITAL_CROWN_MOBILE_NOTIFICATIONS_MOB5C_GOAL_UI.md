# Digital Crown — MOB-5C Notifications Mobile — Goal UI

Status: GOAL LOCKED / BEFORE IMPLEMENTATION
Date: 2026-09-05
Repo: `hraaaaf/Digital_crown`
Branch: `ux/mobile-notifications-mob5c`
Baseline métier: `8891c771f1d77f0ab9347682609b0460881ae2a8`
Audit: `docs/ux/DIGITAL_CROWN_MOBILE_NOTIFICATIONS_MOB5C_AUDIT.md`

## Goal
Permettre à un utilisateur mobile de voir immédiatement les alertes qu’il est autorisé à traiter, comprendre leur priorité et ouvrir le bon contexte en moins de 30 secondes.

## Success observable
- entrée `Plus → Notifications`, sans modifier les 5 boutons permanents ;
- données issues de `/api/mobile/notifications`, aucune seconde source de vérité ;
- alertes financières invisibles sans permission `accounting`/`payments` ;
- aucune alerte Labo tant que son isolation tenant n’est pas certifiée ;
- priorité et récence lisibles sans code couleur seul ;
- action contextuelle uniquement via allowlist ;
- état vide et erreur inline ;
- zéro overflow aux viewports 390×844, 430×932, 768×1024 ;
- thème/typographie issus des settings runtime ;
- zéro erreur console/page dans AFTER.

## Mockup textuel de référence

Header compact :
`Notifications` + compteur non-lu + bouton actualiser.

Sous-header :
`Toutes` | `Prioritaires`

Carte :
1. badge priorité explicite (`Urgent`, `Important`, `Info`)
2. titre
3. patient/contexte si autorisé
4. message, deux ou trois lignes maximum
5. âge de l’alerte
6. CTA unique contextuel (`Voir patient`, `Voir finance`, etc.) si résolvable

État vide :
`Aucune alerte à traiter` + texte court.

## Hiérarchie
1. Urgence/priorité
2. Action attendue
3. Contexte patient/métier
4. Récence

## Interaction
- cibles tactiles ≥44 px ;
- pas de swipe destructeur pour V1 ;
- pas de “tout marquer comme lu” avant audit du endpoint de mutation ;
- aucune navigation vers une route non autorisée ;
- refresh à l’ouverture + bouton manuel ;
- push OS = signal de réveil, jamais source de contenu sensible.

## Hors scope V1
- préférences fines de notification ;
- centre d’administration desktop ;
- alertes Labo ;
- création d’un nouveau moteur de persistance ;
- réglages push complexes ;
- actions destructrices directement depuis une notification.

## AFTER requis
Même scénario déterministe en 390×844, 430×932 et 768×1024, puis comparaison avec le BEFORE, tests ciblés, build, runtime et score visuel.

Deployment: none. No Vercel deployment authorized.
