# Digital Crown — Agenda clinique multi-praticiens

Statut: chantier actif — A1/A2 clôturés; A3 validé humainement et techniquement, closeout pré-merge
Date d'ouverture: 2026-09-16
Dernière mise à jour: 2026-09-16
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
- `CURRENT_ALEMBIC_HEAD = a3pa0000003`;
- aucune migration destructive.

### UX / validation humaine

Référence: `docs/audits/AGENDA_CLINIC_A3_UX_REFERENCE.md`.

BEFORE et AFTER ont été produits aux viewports 390×844, 768×1024 et 1280×900. Les AFTER exact-head ont été inspectés et validés explicitement par le product owner le 2026-09-16.

Le terme `legacy_unassigned` est interne. L'UI produit présente un rendez-vous historique sans praticien comme `Non assigné (historique)`; le mot `Legacy` visible dans le jeu de données de certification n'est pas un libellé produit.

Résiduel accepté: Settings à 390 px est verticalement dense mais lisible et sans overflow horizontal.

### Preuves exact-head avant closeout documentaire

HEAD produit validé humainement: `c286bcf9713bc9fcc5a9701a7fa75b35d94d843c`.

- CI #4703 / run `35147129150`: SUCCESS;
- Agenda A3 Certification #22 / `35147129229`: SUCCESS;
- Agenda A3 Theme Certification #16 / `35147129160`: SUCCESS;
- PostgreSQL Alembic Schema Certification #34 / `35147129187`: SUCCESS;
- Settings Read Truth Visual Certification #66 / `35147129136`: SUCCESS;
- Settings Agenda R7 Visual Certification #87 / `35147129129`: SUCCESS;
- Settings RBAC Visual Certification #389 / `35147129167`: SUCCESS;
- Clinic P1 Multi-Practitioner Visual Certification #151 / `35147129212`: SUCCESS;
- Agenda A2 AFTER Visual Certification V2 #37 / `35147129149`: SUCCESS;
- T2 Runtime Browser Certification #3556 / `35147129145`: SUCCESS;
- Mobile SuperAdmin MOB-5H Cert #120 / `35147129292`: SUCCESS.

AFTER artifact exact-head:
- `agenda-a3-after-visual-evidence`;
- artifact `10467149884`;
- digest `sha256:9410e5791cc6e288924942a7209438a8db21ff29be97379e03b54bf5cbb8ef56`.

Settings Read Truth artifact:
- artifact `10467870005`;
- digest `sha256:419d0a6c9a7d1e4a7b9e80068f3fe4a8d93d5881118846816701cf2a5a59a5c1`.

### Perfection Pass

Après validation humaine:
- aucune review thread ouverte sur PR #542;
- aucune CI requise rouge sur le HEAD produit validé;
- thème default/emerald/dark certifié;
- pas d'overflow page;
- lanes synchronisées;
- migration/runtime schema head cohérents;
- le correctif Settings Read Truth stabilise le harness Vite/workbox sans affaiblir l'oracle métier.

Scoring final produit:
- EXECUTION_SCORE 9.3/10;
- ADVERSARIAL_SCORE 9.2/10;
- retenu 9.2/10.

La revue adversariale étant réalisée par le même agent que l'exécution, aucun score >=9.5 n'est revendiqué.

Closeout détaillé: `docs/audits/AGENDA_CLINIC_A3_CLOSEOUT.md`.

Important: les commits documentaires descendants du HEAD produit validé doivent être re-vérifiés avant merge. La validation humaine porte sur les captures du produit; aucun changement visuel ne doit intervenir après cette validation sans nouvelle capture/validation.

État A3: **VALIDÉ HUMAINEMENT + PRODUIT CERTIFIÉ — CLOSEOUT DOCS PRÉ-MERGE**.

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
A3: **VALIDÉ HUMAINEMENT — CLOSEOUT PRÉ-MERGE**.
A4: **NON DÉMARRÉ**.
A5: **NON DÉMARRÉ**.

Next exact: vérifier le HEAD documentaire final de PR #542 et ses gates. Si aucune régression n'est introduite, passer la PR ready. Le merge exige ensuite l'accord explicite utilisateur sur le HEAD exact. Après merge et post-merge verts, préparer le handover/start prompt A4 avant tout code A4.
