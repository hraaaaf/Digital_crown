# DIGITAL CROWN — MOB-5I Salle d’attente — Goal UI

## Goal
Rendre la salle d’attente réellement exploitable sur mobile à partir du modèle Appointment canonique existant, sans dupliquer le métier ni inventer de données.

## Succès observable
- le mobile distingue `EN_SALLE_ATTENTE` de `PLANIFIE` ;
- un rendez-vous peut passer de `PLANIFIE` à `EN_SALLE_ATTENTE`, puis `EN_FAUTEUIL`, puis `TERMINE` depuis le flux mobile autorisé ;
- la vue mobile affiche les patients actuellement en salle d’attente avec leur heure de RDV et `ticket_number` quand présent ;
- aucune métrique de temps d’attente n’est affichée tant qu’aucun timestamp d’arrivée canonique n’est prouvé ;
- tenant scope et permission `agenda` restent imposés côté serveur ;
- aucun nouveau modèle/table n’est créé sans nécessité démontrée ;
- aucun débordement horizontal aux viewports 390×844, 430×932 et 768×1024 ;
- score visuel cible >= 9/10 après certification AFTER.

## Référence UX
Surface mobile clinique compacte, centrée sur l’état opérationnel du patient :
1. compteur Salle d’attente ;
2. liste ordonnée des patients présents ;
3. actions explicites et réversibles selon le contrat métier ;
4. accès depuis la navigation mobile sans masquer l’Agenda.

La Salle d’attente ne remplace pas l’Agenda. Elle est une vue opérationnelle dérivée des mêmes rendez-vous.

## BEFORE obligatoire
Capturer la baseline exacte avant changement produit sur :
- 390×844 ;
- 430×932 ;
- 768×1024.

Le BEFORE doit prouver au minimum :
- absence de vue mobile Salle d’attente dédiée ;
- `EN_SALLE_ATTENTE` aplati en `PLANIFIE` par le bridge mobile ;
- absence de `ticket_number` dans le snapshot mobile ;
- absence d’overflow horizontal / erreurs page-console sur le harness.

Harness versionné :
- `.github/workflows/mobile-waiting-room-mob5i-before.yml` ;
- `frontend/scripts/capture-mobile-waiting-room-mob5i-before.mjs`.

## Périmètre technique minimal
Backend :
- étendre le vocabulaire mobile avec `EN_ATTENTE` mappé exactement sur `AppointmentStatus.EN_SALLE_ATTENTE` ;
- exposer `ticket_number` dans les rendez-vous du snapshot / liste mobile ;
- autoriser le PATCH de statut vers `EN_ATTENTE` sous permission `agenda` et tenant scope existants.

Frontend :
- étendre `ApptStatus` et `STATUS_META` ;
- ajouter une vue Salle d’attente dérivée du snapshot ;
- ajouter une entrée de navigation adaptée sans retirer de prérogative existante ;
- préserver Agenda, Patients, quick actions et autres surfaces.

## Hors périmètre tant que non prouvé
- nouvelle table de file d’attente ;
- estimation du temps d’attente ;
- timestamp d’arrivée reconstruit à partir de l’heure du RDV ;
- notifications patient ;
- déploiement Vercel.

## Preuve finale attendue
AFTER aux mêmes viewports + tests backend/frontend + CI générale + preuve de mapping exact statut/ticket + comparaison BEFORE/AFTER + score visuel.

Statut : `GOAL UI LOCKED — BEFORE HARNESS ARMED`.
