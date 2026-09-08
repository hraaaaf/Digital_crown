# DIGITAL CROWN — MOB-5I Salle d’attente — Audit

## État final vérifié

Baseline auditée : `fd19dab006d46f274946fd932927b9ac4821d3ec`.

Faits métier confirmés :
- `AppointmentStatus.EN_SALLE_ATTENTE` existait déjà ;
- `Appointment.ticket_number` existait déjà ;
- le bridge mobile BEFORE aplatissait la salle d’attente en `PLANIFIE` et n’exposait pas `ticket_number` ;
- aucune nouvelle table n’était nécessaire.

Implémentation livrée :
- `EN_ATTENTE` ↔ `AppointmentStatus.EN_SALLE_ATTENTE` ;
- `ticket_number` enrichi sous tenant scope ;
- Agenda : `PLANIFIE → EN_ATTENTE` ;
- `WaitingRoomView` dérivée de `Snapshot.appointments` ;
- `Au fauteuil` → `EN_COURS` / backend `EN_FAUTEUIL` ;
- accès secondaire dans `Plus` ; bottom-nav principale inchangée ;
- aucune durée d’attente inventée.

## Preuves
- BEFORE run `34168710412` — SUCCESS ; artifact `10035019049` ;
- AFTER/cert run `34169388445` — SUCCESS ; artifact `10035225974` ;
- score visuel **9.3/10** ;
- CI PR `34169598948` — SUCCESS ;
- PR produit `#367` ;
- merge exact `e2522a6d8b4794e64253eb4af36500e18cd87b40` ;
- post-merge master `34170398551` — SUCCESS ;
- PR closeout `#369` : CI `34170522549` SUCCESS et T2 `34170522692` SUCCESS avant merge docs.

Aucun déploiement Vercel.

Statut : `DONE / MERGED / CLOSED`.
