# Digital Crown — MOB-5B Frontdesk Mobile — Goal UI

Status: GOAL LOCKED / BEFORE IMPLEMENTATION
Date: 2026-09-05
Repo: `hraaaaf/Digital_crown`
Branch: `ux/mobile-frontdesk-mob5b`
Baseline: `89098066ef0c943c0e084af4b9cd388d3ab0aa5b`

## Goal
Permettre à un utilisateur autorisé de traiter une demande de rendez-vous depuis le cockpit mobile en quelques gestes, sans dupliquer la logique métier desktop.

## Success observable
- entrée `Plus → Frontdesk` sans modifier les 5 entrées permanentes ;
- liste des demandes `EN_ATTENTE_DEMANDE` / `EN_ATTENTE_CONFIRM` issue des mêmes endpoints serveur ;
- confirmer / refuser / demander confirmation sur la même donnée métier que desktop ;
- appel direct si téléphone disponible ;
- WhatsApp ouvre un message prérempli mais ne prétend jamais qu’un message serveur a été envoyé ;
- permission agenda respectée ;
- zéro overflow horizontal aux viewports 390×844, 430×932, 768×1024 ;
- thème et typographie pilotés par les settings runtime ;
- zéro erreur console/page dans la preuve AFTER.

## Référence actuelle
Audit : `docs/ux/DIGITAL_CROWN_MOBILE_FRONTDESK_MOB5B_AUDIT.md`.
Backend réutilisé : `backend/routers/frontdesk.py`.
Desktop source métier : `frontend/src/features/agenda/PendingRequestCard.tsx` et `FrontdeskModal.tsx`.

## Cible UX mobile
### Entrée
`Plus → Frontdesk`

### Écran
- header compact `Frontdesk` ;
- compteur demandes en attente ;
- cartes empilées adaptées au pouce ;
- patient + téléphone ;
- créneau + durée ;
- motif ;
- statut / expiration ;
- actions primaires : `Confirmer`, `Refuser` ;
- action conditionnelle : `Demander confirmation` ;
- actions secondaires : `Appeler`, `WhatsApp`.

### Priorités visuelles
1. identité patient ;
2. date/heure ;
3. statut ;
4. actions métier ;
5. contact rapide.

### Interactions
- tap cible ≥44 px ;
- confirmation de refus dans une sheet/dialog mobile, pas `window.confirm` ;
- erreurs inline, pas `alert()` ;
- retour de mutation explicite puis refresh de la liste ;
- état vide utile : `Aucune demande en attente`.

## Hors scope
- refonte des règles de planning ;
- automatisation WhatsApp serveur ;
- création manuelle complète des demandes depuis mobile ;
- paramétrage Frontdesk ;
- administration lourde.

## Preuve requise
BEFORE → Goal UI → implémentation → AFTER mêmes viewports 390/430/768 → tests frontend/backend ciblés → build → runtime → comparaison → score visuel.

Deployment: none. No Vercel deployment authorized.
