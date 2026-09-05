# Digital Crown — MOB-5B Frontdesk Mobile — Audit initial

Status: AUDIT COMPLETE / IMPLEMENTATION NOT STARTED
Date: 2026-09-05
Repo: `hraaaaf/Digital_crown`
Branch: `audit/mobile-secondary-value-mob5`

## Goal produit

Permettre de traiter une demande de rendez-vous depuis mobile en quelques gestes, avec la même donnée métier que le desktop et sans dupliquer la logique Frontdesk.

Cible mobile verrouillée : voir → accepter/refuser → appeler/WhatsApp → suivi rapide. L'administration lourde reste desktop.

## État vérifié du repo

### Backend déjà exploitable

`backend/routers/frontdesk.py` fournit déjà :
- `POST /frontdesk/appointment-request`
- `GET /appointments/pending`
- `POST /appointments/{id}/request-confirmation`
- `POST /appointments/{id}/confirm`
- `POST /appointments/{id}/reject`
- `POST /appointments/{id}/expire`

Toutes ces routes passent par la permission `agenda`, sont tenant-scoped via `employer_id`, et journalisent les transitions métier importantes.

### Desktop existant

`frontend/src/features/agenda/PendingRequestCard.tsx` possède déjà les actions :
- demander confirmation ;
- confirmer ;
- refuser.

`frontend/src/features/agenda/FrontdeskModal.tsx` permet la création manuelle d'une demande.

### Dette UX actuelle

Les composants desktop utilisent des couleurs locales (`blue`, `orange`, `yellow`, `red`, `gray`) et des patterns desktop (`alert`, `window.confirm`). Ils ne doivent pas être portés tels quels sur mobile.

Le backend retourne déjà le téléphone et le motif, donc appel/WhatsApp peuvent être exposés côté mobile sans nouvelle source de données.

Le endpoint `request-confirmation` retourne encore un template de message avec une note explicite indiquant que l'intégration WhatsApp n'est pas native. Le mobile devra refléter cette vérité et ne pas prétendre qu'un message a été envoyé.

## Recommandation d'architecture

Créer une vue mobile dédiée dans le shell canonique, consommatrice des mêmes endpoints et mêmes statuts. Ne pas réutiliser le composant desktop compressé.

Entrée recommandée : `Plus → Frontdesk` pour les rôles possédant la permission agenda.

Carte mobile recommandée :
- patient + téléphone ;
- date/heure + motif ;
- statut/expiration ;
- actions primaires : confirmer / refuser ;
- actions secondaires : appeler / WhatsApp ;
- demande de confirmation si statut compatible.

## Gates avant implémentation

1. BEFORE visuel sur shell mobile canonique 390/430/768.
2. Goal UI écrit sur la base du BEFORE réel.
3. Mockup/référence.
4. Implémentation.
5. AFTER mêmes viewports.
6. Tests frontend + backend ciblés + build + runtime.
7. Vérification RBAC/tenant + absence d'état positif mensonger pour WhatsApp.
8. Score visuel et preuve canonique.

## Success observable

- Frontdesk accessible depuis mobile sans modifier les 5 entrées permanentes.
- Liste pending partagée avec desktop.
- confirmer/refuser met à jour la même donnée serveur.
- appel/WhatsApp utilisent uniquement le téléphone fourni par la donnée métier.
- aucun faux statut « envoyé » pour le template de confirmation.
- zéro overflow 390/430/768.
- zéro erreur runtime.
- thème/typographie settings-driven.

## Hors scope MOB-5B

- création/refonte complète des règles de planning ;
- paramétrage Frontdesk ;
- automatisation WhatsApp côté serveur ;
- workflows administratifs lourds.

Deployment: none. No Vercel deployment authorized.
