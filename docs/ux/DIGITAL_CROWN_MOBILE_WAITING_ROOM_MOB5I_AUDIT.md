# DIGITAL CROWN — MOB-5I Salle d’attente — Audit

## Baseline auditée
Master de départ : `fd19dab006d46f274946fd932927b9ac4821d3ec`.

## Faits vérifiés

### Modèle métier existant
`AppointmentStatus` contient déjà :
- `PREVU` ;
- `EN_SALLE_ATTENTE` ;
- `EN_FAUTEUIL` ;
- `TERMINE` ;
- `ANNULE`.

`Appointment.ticket_number` existe déjà. Aucune nouvelle table n’est nécessaire pour matérialiser l’état Salle d’attente.

### Contrat mobile actuel
Dans `backend/routers/mobile_legacy.py` :
- `_MOBILE_TO_BACKEND_STATUS` ne connaît que `PLANIFIE`, `EN_COURS`, `TERMINE`, `ANNULE` ;
- `_BACKEND_TO_MOBILE_STATUS` transforme `EN_SALLE_ATTENTE` en `PLANIFIE` ;
- `/snapshot` expose les rendez-vous sans `ticket_number` ;
- le PATCH `/appointments/{appointment_id}/status` refuse tout statut hors vocabulaire mobile actuel.

Conséquence : un patient déjà en salle d’attente côté métier devient indistinguable d’un patient seulement planifié dans l’expérience mobile.

### Frontend mobile actuel
`frontend/src/features/mobile/Dashboard/types.tsx` :
- `ApptStatus = 'PLANIFIE' | 'EN_COURS' | 'TERMINE' | 'ANNULE'` ;
- aucun meta-status Salle d’attente.

`MobileDashboard.tsx` :
- aucune tab/vue `waiting-room` ;
- Agenda reste la seule surface opérationnelle des rendez-vous.

`AgendaView.tsx` :
- consomme le snapshot et `DraggableApptCard` ;
- aucune séparation des patients présents en salle d’attente.

## Risques
1. Modifier seulement le frontend serait faux : le backend aplatit actuellement l’état.
2. Créer une nouvelle table file d’attente dupliquerait `Appointment.status` et introduirait du drift.
3. Calculer un temps d’attente avec `datetime_start` serait trompeur : heure de rendez-vous != heure d’arrivée.
4. Toute mutation doit rester sous permission `agenda` et tenant scope existants.

## Solution minimale recommandée
1. Ajouter `EN_ATTENTE` au vocabulaire mobile et mapper exactement vers `EN_SALLE_ATTENTE`.
2. Exposer `ticket_number` dans les DTO mobile existants.
3. Ajouter une vue mobile Salle d’attente dérivée du snapshot.
4. Préserver l’Agenda et toutes les prérogatives existantes.
5. Certifier BEFORE puis AFTER aux mêmes viewports.

Statut : `AUDIT COMPLETE — IMPLEMENTATION NOT STARTED — BEFORE PENDING`.
