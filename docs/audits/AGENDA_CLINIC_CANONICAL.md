# Digital Crown — Agenda clinique multi-praticiens

Statut: chantier actif — A1/A2 clôturés; A3 produit mergé et post-merge certifié, closeout documentaire final en cours
Date d'ouverture: 2026-09-16
Dernière mise à jour: 2026-09-17
Repo: `hraaaaf/Digital_crown`
Fichier canonique: `docs/audits/AGENDA_CLINIC_CANONICAL.md`

## Goal global

Faire évoluer l'agenda existant vers un agenda réellement exploitable en clinique multi-dentistes sans réécrire le moteur actuel et sans casser les données, rendez-vous, documents ou comportements déjà validés.

Architecture à préserver:

`Appointment + employer_id + praticien_id + logique de conflits existante`

## Baseline métier vérifiée

- Les rendez-vous sont isolés par `employer_id`.
- `praticien_id` est nullable pour compatibilité historique.
- Un praticien assignable doit appartenir au cabinet et respecter les règles d'activité/approbation existantes.
- Deux praticiens différents peuvent occuper le même horaire.
- Un même praticien ne peut pas avoir deux rendez-vous exact-time qui se chevauchent.
- Les rendez-vous historiques `praticien_id = NULL` restent des bloqueurs globaux.
- Les fermetures cabinet restent absolues.

## Règles de sécurité

1. Préserver DB, patients, documents, rendez-vous et fonctionnalités validées.
2. Aucune migration destructive.
3. Aucune réaffectation silencieuse d'un rendez-vous existant.
4. Les rendez-vous non assignés restent visibles tant qu'ils peuvent bloquer un créneau.
5. Toute modification significative inclut des tests de non-régression adaptés.
6. Aucun merge sans accord explicite utilisateur sur le HEAD exact.
7. Aucun déploiement Vercel sans autorisation explicite.
8. Un lot à la fois.
9. Toute évolution UI/UX suit BEFORE → Goal → référence/mockup → implémentation → AFTER mêmes viewports → comparaison/tests → score visuel → validation humaine.

## LOT A1 — Filtrage praticien réel

Goal: quand un praticien est sélectionné dans le contexte clinique, les vues Jour/Semaine/Mois affichent réellement son agenda.

Résultat:
- filtre praticien tenant-scoped;
- lecture filtrée = praticien sélectionné + rendez-vous `praticien_id = NULL`;
- sans filtre, comportement cabinet-wide conservé;
- édition sans réaffectation silencieuse;
- aucune migration DB; moteur de conflits inchangé.

Preuve:
- PR #528 mergée;
- HEAD pré-merge `9e3d9e8de8362b8bb4d69e908e1c68b971d43f51`;
- merge `86958c913e5c2872504505eb3af0485b22e66c05`;
- CI post-merge #4528 / `35081648852` SUCCESS;
- Cabinet Upgrade PostgreSQL #912 / `35081649142` SUCCESS.

État A1: **CLÔTURÉ**.

## LOT A2 — Vue clinique multi-praticiens

Goal: grille horaire journalière synchronisée `Heure | Dr A | Dr B | Dr C ...`, sans disponibilités individuelles A3.

Résultat:
- axe horaire commun et slots 15 min;
- lanes praticiens actifs/assignables;
- rendez-vous exact-time positionnés selon heure/durée réelles;
- rendez-vous flexibles visibles sans heure inventée;
- `praticien_id = NULL` conservé comme bloqueur transversal;
- création depuis lane avec praticien injecté au conflit + POST;
- aucun praticien injecté sur PUT d'édition;
- responsive avec scroll horizontal interne mobile, sans overflow page;
- aucun backend/migration A2.

Preuve produit:
- PR #533 mergée;
- merge commit `1e9fd49af91ffafad89ad9936c6f2e372e883354`;
- post-merge CI #4578 / `35102444953` SUCCESS;
- Cabinet Upgrade PostgreSQL #918 / `35102444861` SUCCESS;
- AFTER V2: mêmes viewports 390×844, 768×1024, 1280×900; `syncDelta = 0 px`; aucune erreur navigateur; aucun overflow page.

État A2: **CLÔTURÉ**.

## LOT A3 — Disponibilités individuelles

Goal: horaires, jours travaillés, pauses, congés et absences propres à chaque praticien, superposés aux fermetures globales du cabinet.

Principe contractuel:

`disponibilité effective = disponibilité cabinet ∩ disponibilité praticien`

Le praticien peut réduire sa disponibilité mais jamais élargir celle du cabinet. Sans override individuel, il hérite exactement du cabinet. Les fermetures globales cabinet restent absolues. Les rendez-vous historiques `praticien_id = NULL` restent des bloqueurs globaux multi-praticien.

### Résultat A3

- helpers backend d'intersection cabinet/praticien;
- compatibilité absence de configuration individuelle = héritage cabinet;
- correction wall-clock: une heure locale aware reste la même heure métier après normalisation;
- endpoints settings/exceptions praticien tenant-scoped et contrôlés par rôle;
- création, mise à jour, bulk et check-conflicts rendus practitioner-aware;
- conflits praticien-scoped avec legacy NULL global;
- `/appointments/multi-practitioner` expose la disponibilité et conserve `legacy_unassigned` comme contrat technique;
- UI Multi distingue Libre / Cabinet fermé / Hors horaires praticien / Pause / Absence;
- panneau Settings praticien: héritage, plages personnalisées multiples, reset cabinet, absences;
- thème A3 branché sur les tokens Digital Crown; états sémantiques conservés;
- migration additive `a3pa0000003` chaînée après `d0b000000003`;
- aucune migration destructive.

### UX / validation humaine

Référence: `docs/audits/AGENDA_CLINIC_A3_UX_REFERENCE.md`.

BEFORE et AFTER ont été produits aux viewports 390×844, 768×1024 et 1280×900. Les AFTER exact-head ont été inspectés et validés explicitement par le product owner le 2026-09-16.

Le terme `legacy_unassigned` est interne. L'UI produit présente un rendez-vous historique sans praticien comme `Non assigné (historique)`; le mot `Legacy` visible dans le jeu de données de certification n'est pas un libellé produit.

Résiduel accepté: Settings à 390 px est verticalement dense mais lisible et sans overflow horizontal.

### Preuves et merge

HEAD produit validé humainement: `c286bcf9713bc9fcc5a9701a7fa75b35d94d843c`.

- preuves produit détaillées dans `docs/audits/AGENDA_CLINIC_A3_CLOSEOUT.md`;
- PR #542 mergée; merge réel `ef23b7147c5ed3dfa7c06267eec797a520cb7366`;
- correctif wiring A3 PR #560 mergé `c547e30d4bab4928ff64de3757bff98a83a60a53`;
- les régressions postérieures mobile puis NGAP/Alembic ont été diagnostiquées comme indépendantes du comportement A3;
- PR #566 a corrigé le gate NGAP/Alembic sans réécrire l'historique de migration;
- master certifié `24844a5d19a6bd575d175b331a1bba68bc3c0b0f`;
- Cabinet Upgrade PostgreSQL #943 / run `35203491675`: SUCCESS;
- CI globale #4757 / run `35203491846`: SUCCESS, incluant Frontend, garde production et Full backend regression post-merge.

### Perfection Pass

- validation humaine conservée car aucun changement visuel A3 après le HEAD validé;
- thème default/emerald/dark certifié;
- pas d'overflow page sur les captures certifiées;
- lanes synchronisées;
- migration additive et chaîne Alembic contrôlées;
- master final observé possède une régression backend globale verte.

Scoring produit:
- EXECUTION_SCORE 9.3/10;
- ADVERSARIAL_SCORE 9.2/10;
- retenu 9.2/10.

La revue adversariale étant réalisée par le même agent que l'exécution, aucun score >=9.5 n'est revendiqué.

Closeout détaillé: `docs/audits/AGENDA_CLINIC_A3_CLOSEOUT.md`.

État A3: **PRODUIT MERGÉ + POST-MERGE CERTIFIÉ — CLOSEOUT DOCS FINAL EN COURS**.

## LOT A4 — Fauteuils / salles / ressources

Goal: modéliser la capacité physique du cabinet avec allocation facultative de ressource et contrôle des collisions praticien + ressource.

État A4: **NON DÉMARRÉ**.

## LOT A5 — Robustesse clinique + closeout

Goal: timezone cabinet explicite, stratégie soft-delete/historique, traitement/migration legacy, non-régression globale, documentation et certification finale du chantier.

État A5: **NON DÉMARRÉ**.

## Procédure de reprise

Dans toute nouvelle conversation:
1. lire intégralement ce fichier;
2. lire le dernier handover du chantier;
3. vérifier live master, branche, PR, HEAD, CI, reviews/threads et divergence;
4. ne jamais supposer qu'un SHA ou une CI ancien est encore actuel;
5. reprendre uniquement le lot actif et ses gates.

## État courant

A1: **CLOSED**.
A2: **CLOSED**.
A3: **PRODUIT MERGÉ + POST-MERGE CERTIFIÉ — CLOSEOUT DOCS FINAL EN COURS**.
A4: **NON DÉMARRÉ**.
A5: **NON DÉMARRÉ**.

Next exact: vérifier les gates du HEAD documentaire final, puis obtenir l'accord explicite utilisateur sur ce HEAD avant merge. Après merge documentaire et vérification master, déclarer A3 CLOSED et préparer le handover/start prompt A4 avant tout code A4.
