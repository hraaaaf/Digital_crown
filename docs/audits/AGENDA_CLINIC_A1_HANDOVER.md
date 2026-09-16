# HANDOVER — Digital Crown / Agenda clinique — A1 → A2

Date: 2026-09-16
Repo: `hraaaaf/Digital_crown`
Fichier canonique: `docs/audits/AGENDA_CLINIC_CANONICAL.md`

## Première action obligatoire dans la nouvelle conversation

1. Lire intégralement `docs/audits/AGENDA_CLINIC_CANONICAL.md`.
2. Lire intégralement le présent fichier.
3. Vérifier sur GitHub le master ACTUEL, sans supposer qu'un SHA ci-dessous est encore actuel.
4. Vérifier que le merge A1 `86958c913e5c2872504505eb3af0485b22e66c05` est bien ancêtre du master ACTUEL.
5. Vérifier les CI/certifications post-merge réellement associées au master contenant A1.
6. Si un gate pertinent est rouge, diagnostiquer et corriger avant tout travail A2.
7. Si les gates sont verts, commencer A2 par le protocole UI/UX obligatoire BEFORE → Goal → mockup/référence → implémentation → AFTER mêmes viewports → comparaison/tests → score visuel.

## Goal global du chantier

Faire évoluer l'agenda existant vers un agenda réellement exploitable en clinique multi-dentistes sans réécrire le moteur existant et sans casser les données, rendez-vous, documents ou fonctionnalités validées.

Architecture à préserver:

`Appointment + employer_id + praticien_id + logique de conflits existante`

## A1 — Résultat implémenté et mergé

Goal A1: rendre le sélecteur praticien réellement opérant sur les vues Jour/Semaine/Mois.

Implémentation:
- `GET /appointments/` accepte désormais `praticien_id`;
- validation du praticien via la logique tenant-scoped existante;
- une lecture filtrée contient les rendez-vous du praticien sélectionné + les rendez-vous legacy `praticien_id = NULL`;
- les rendez-vous d'un autre praticien sont exclus;
- sans filtre, la lecture historique cabinet-wide reste inchangée;
- `AgendaPage.tsx` injecte le praticien actif uniquement dans les GET standard;
- les PUT d'édition ne réaffectent pas silencieusement le rendez-vous;
- `AgendaStudio.tsx` remonte/refetch Jour/Semaine/Mois lors du changement de praticien;
- tests backend A1 et contrat frontend A1 ajoutés;
- aucune migration DB;
- aucune modification fauteuil/salle/ressource;
- aucune disponibilité individuelle A3;
- aucune modification de la logique de collision existante.

Fichiers A1:
- `backend/routers/appointments.py`
- `backend/tests/test_agenda_practitioner_filter_a1.py`
- `frontend/src/AgendaClinicA1.test.ts`
- `frontend/src/features/agenda/AgendaStudio.tsx`
- `frontend/src/pages/AgendaPage.tsx`
- `docs/audits/AGENDA_CLINIC_CANONICAL.md`

## Preuve pré-merge A1

PR: `#528` — `feat(agenda): A1 real practitioner filtering`
Branche: `feat/agenda-clinic-a1-practitioner-filter-20260916`
HEAD exact pré-merge: `9e3d9e8de8362b8bb4d69e908e1c68b971d43f51`

Certifications exact-HEAD vérifiées avant merge:
- CI `#4520` — SUCCESS;
- T2 Runtime Browser Certification `#3392` — SUCCESS;
- Cabinet Upgrade PostgreSQL Certification `#907` — SUCCESS;
- Clinic P1 Multi-Practitioner Visual Certification `#109` — SUCCESS;
- M6-I Biometric Passkey Certification `#2192` — SKIPPED attendu.

Revue au dernier contrôle avant merge:
- aucun commentaire PR;
- aucune review;
- aucun review thread;
- PR devenue `mergeable: true`;
- passage draft → ready effectué;
- accord utilisateur explicite reçu pour le merge du HEAD exact.

Merge A1:
- PR #528 mergée;
- merge commit: `86958c913e5c2872504505eb3af0485b22e66c05`.

## Post-merge observé

Le push CI `#4527` sur le merge commit A1 a été `CANCELLED` parce que master a avancé immédiatement après.

Master vérifié ensuite:
`8a37913c23f182a8de4e0f1dd0e2049e48b7267f`

Ce commit avait comme parent le merge A1 `86958c913e5c2872504505eb3af0485b22e66c05`, donc A1 était bien contenu dans le master observé.

Sur ce master observé au moment du handover:
- CI `#4528` — QUEUED;
- Cabinet Upgrade PostgreSQL Certification `#912` — QUEUED.

Ne pas transformer cet état en SUCCESS sans relecture GitHub.

## A2 — Lot suivant

Nom: Vue clinique multi-praticiens.

Goal:
remplacer la lecture multi-praticiens en listes verticales par une vraie matrice horaire synchronisée, sans introduire encore les disponibilités individuelles A3.

Cible UX:
`Heure | Dr A | Dr B | Dr C ...`

Chaque colonne praticien doit permettre:
- lecture immédiate des créneaux occupés/libres selon les données existantes;
- création dans la colonne du praticien;
- édition sans réaffectation silencieuse;
- comportement responsive cohérent;
- maintien des rendez-vous legacy de manière explicite et non trompeuse.

Hors scope A2:
- horaires individuels, pauses, congés et absences — A3;
- fauteuils/salles/ressources — A4;
- timezone explicite, soft-delete/historique, migration legacy — A5;
- réécriture du moteur de conflits existant.

## Process UI/UX A2 obligatoire

Avant toute implémentation visuelle:
1. capturer le BEFORE aux mêmes viewports utiles;
2. écrire le Goal observable;
3. produire/figer une référence ou mockup de la matrice;
4. implémenter;
5. capturer l'AFTER aux mêmes viewports;
6. comparer BEFORE/AFTER;
7. exécuter tests fonctionnels + non-régression;
8. attribuer un score visuel uniquement sur preuve observable.

## Sécurité / non-régression

- préserver DB, patients, documents et rendez-vous existants;
- aucune migration destructive;
- aucune réaffectation silencieuse;
- conserver tenant isolation `employer_id`;
- conserver les collisions par praticien déjà validées;
- les rendez-vous legacy non assignés restent des bloqueurs globaux tant qu'A5 n'a pas défini leur stratégie de migration;
- aucun merge A2 sans accord utilisateur explicite sur le HEAD exact;
- aucun déploiement Vercel sans autorisation explicite.

## Next exact

Vérifier le master ACTUEL et les gates post-merge du master contenant A1. Si verts, ouvrir le lot A2 dans une nouvelle conversation et commencer uniquement par le BEFORE UI/UX et la référence de grille synchronisée.
