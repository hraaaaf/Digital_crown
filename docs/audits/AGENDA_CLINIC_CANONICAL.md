# Digital Crown — Agenda clinique multi-praticiens

Statut: chantier actif — A1 clôturé; A2 produit certifié pré-merge; closeout documentaire en cours
Date d'ouverture: 2026-09-16
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
- Les horaires et exceptions existants sont au niveau cabinet, pas au niveau praticien.
- Aucun fauteuil/salle/ressource n'est actuellement modélisé dans `Appointment`.

## Règles de sécurité

1. Préserver DB, patients, documents, rendez-vous et fonctionnalités validées.
2. Aucune migration destructive.
3. Aucune réaffectation silencieuse d'un rendez-vous existant.
4. Les rendez-vous non assignés restent visibles tant qu'ils peuvent bloquer un créneau.
5. Toute modification significative inclut des tests de non-régression adaptés.
6. Aucun merge sans accord explicite utilisateur sur le HEAD exact.
7. Aucun déploiement Vercel sans autorisation explicite.
8. Un lot à la fois.
9. Toute évolution UI/UX suit BEFORE → Goal → référence/mockup → implémentation → AFTER mêmes viewports → comparaison/tests → score visuel.

## LOT A1 — Filtrage praticien réel

Goal: quand un praticien est sélectionné dans le contexte clinique, les vues Jour/Semaine/Mois affichent réellement son agenda.

Résultat livré:
- `GET /appointments/` accepte un filtre praticien sécurisé et tenant-scoped;
- la lecture filtrée contient le praticien sélectionné + les rendez-vous `praticien_id = NULL`;
- les rendez-vous d'un autre praticien sont exclus;
- sans filtre, le comportement cabinet-wide historique est conservé;
- changement de praticien → refetch Jour/Semaine/Mois;
- édition sans réaffectation silencieuse;
- aucune migration DB;
- moteur de conflits inchangé.

Preuve A1:
- PR `#528` mergée;
- HEAD pré-merge: `9e3d9e8de8362b8bb4d69e908e1c68b971d43f51`;
- merge commit: `86958c913e5c2872504505eb3af0485b22e66c05`;
- CI pré-merge `#4520` — SUCCESS;
- T2 `#3392` — SUCCESS;
- PostgreSQL `#907` — SUCCESS;
- Clinic P1 `#109` — SUCCESS;
- master contenant A1 vérifié: `8a37913c23f182a8de4e0f1dd0e2049e48b7267f`;
- CI post-merge `#4528` / run `35081648852` — SUCCESS;
- Cabinet Upgrade PostgreSQL `#912` / run `35081649142` — SUCCESS.

État A1: **CLÔTURÉ**.

## LOT A2 — Vue clinique multi-praticiens

Goal: remplacer la lecture Multi en listes verticales par une grille horaire journalière synchronisée, sans introduire les disponibilités individuelles A3.

Cible UX: `Heure | Dr A | Dr B | Dr C ...`

### Résultat produit certifié

- Multi devient une vue quotidienne J-1/J+1.
- Axe horaire commun, slots de 15 minutes, même repère temporel pour toutes les lanes.
- Une lane par praticien actif/assignable renvoyé par l'API existante.
- Les rendez-vous exact-time sont positionnés à leur vraie heure et selon leur vraie durée.
- Les rendez-vous flexibles restent visibles sans heure inventée.
- Les rendez-vous `praticien_id = NULL` sont affichés comme bloqueurs transversaux explicites.
- Création depuis une lane: praticien de lane injecté au GET de conflit et au POST de création.
- L'intercepteur de création est installé avant l'ouverture du modal et supprimé à la fermeture/édition/unmount.
- Aucun praticien n'est injecté sur un PUT d'édition: pas de réaffectation silencieuse.
- Les horaires globaux cabinet existants sont réutilisés; aucune disponibilité individuelle n'est introduite.
- Jour/Semaine/Mois A1 restent préservés.
- Responsive: matrice conservée, scroll horizontal interne sur petit écran, pas d'overflow horizontal de page.
- Aucun backend A2, aucune migration DB.

### BEFORE A2

- base produit: `bc3d8d145670dc70dc6c6842e772e56d1d89aa99`;
- capture HEAD: `2911da0f4e8bd4766b725089924e5ba5a616eaff`;
- run `35084989399` — SUCCESS;
- viewports: `390×844`, `768×1024`, `1280×900`;
- artifact digest: `sha256:c4fc22b6a489170e06b5a7f6ff09f76cdaa2e68ac40cec82c5bdd55abc7a3755`;
- référence UX: `docs/audits/AGENDA_CLINIC_A2_UX_REFERENCE.md`.

### AFTER / preuve produit A2

PR: `#533` — `feat(agenda): A2 synchronized multi-practitioner grid`
Branche: `feat/agenda-clinic-a2-multi-grid-20260916`
HEAD produit certifié: `677414578010a7b9983e19e035a2ee5a0001603c`

Gates exacts sur ce HEAD:
- CI `#4558` / run `35093443889` — SUCCESS;
- T2 Runtime Browser `#3425` / run `35093443907` — SUCCESS;
- Clinic P1 Multi-Practitioner Visual `#125` / run `35093444003` — SUCCESS;
- Agenda A2 AFTER Visual Certification V2 `#11` / run `35093443999` — SUCCESS;
- M6-I `#2225` — SKIPPED attendu;
- test contractuel A2: 4/4 PASS.

Artifact AFTER V2:
- id `10445091768`;
- digest `sha256:51eab42cf5522cc199b7f3cfd561518406a658427916a74e8155cc922b3739d4`;
- mêmes viewports que le BEFORE;
- `syncDelta = 0 px` aux trois viewports;
- aucune erreur navigateur;
- aucun overflow horizontal de page;
- mobile 390 px: scroll interne `364 → 728` px;
- création lane Dr Youssef: `praticien_id = 2` sur le contrôle de conflit ET le POST;
- modal seedé `2026-09-16 15:00`, durée `30 min`;
- `datetime_start = 2026-09-16T14:00:00.000Z`, cohérent avec 15:00 à Casablanca UTC+1.

Comparaison visuelle:
- BEFORE: cartes empilées, dates mélangées, pas d'axe temporel commun, legacy non assigné absent de la lecture Multi;
- AFTER: axe commun, durées proportionnelles, simultanéité lisible, fermeture cabinet visible, legacy transversal explicite, matrice responsive.

Score visuel observé: **9.1/10**.
Compromis connu: à 390 px, trois praticiens nécessitent un scroll horizontal interne; c'est intentionnel et la page elle-même ne déborde pas.

Contrat backend revalidé sans modification A2:
- `/appointments/check-conflicts` accepte `praticien_id` et conserve `praticien_id = NULL` comme bloqueur global;
- `/appointments/multi-practitioner` renvoie `legacy_unassigned` séparément;
- aucun changement du moteur de collision n'était nécessaire.

Au dernier contrôle du HEAD produit certifié:
- master: `bc3d8d145670dc70dc6c6842e772e56d1d89aa99`;
- branche A2: ahead 18 / behind 0;
- PR #533 mergeable et encore draft;
- aucun commentaire, aucune review, aucun review thread.

Important: le commit documentaire qui contient le présent closeout est un descendant docs-only du HEAD produit certifié ci-dessus. Son SHA et ses gates doivent être vérifiés live avant merge; ne pas extrapoler les certifications du parent à un HEAD différent sans cette vérification.

État A2: **PRODUIT CERTIFIÉ PRÉ-MERGE — CLOSEOUT DOCS À RECERTIFIER SUR LE HEAD FINAL**.

## LOT A3 — Disponibilités individuelles

Goal: horaires, jours travaillés, pauses, congés et absences propres à chaque praticien, superposés aux fermetures globales du cabinet.

Baseline vérifiée avant A3:
- `cabinet_settings.weekly_schedule_json` est tenant-scoped par `employer_id` et décrit les horaires globaux du cabinet;
- `agenda_exceptions` est tenant-scoped par `employer_id` et décrit les fermetures globales;
- `validate_appointment_availability(...)` applique aujourd'hui ces règles globales;
- A2 n'a ajouté aucune disponibilité individuelle.

Principe A3 à préserver:
`disponibilité effective = disponibilité cabinet ∩ disponibilité praticien`.

## LOT A4 — Fauteuils / salles / ressources

Goal: modéliser la capacité physique du cabinet avec allocation facultative de ressource et contrôle des collisions praticien + ressource.

## LOT A5 — Robustesse clinique + closeout

Goal: timezone cabinet explicite, stratégie soft-delete/historique, traitement/migration legacy, non-régression globale, documentation et certification finale du chantier.

## Procédure de reprise

Dans toute nouvelle conversation:
1. lire intégralement ce fichier;
2. lire le dernier handover du chantier;
3. vérifier live `master`, branche, PR, HEAD, CI, reviews/threads et divergence;
4. ne jamais supposer qu'un SHA ou une CI ancien est encore actuel;
5. reprendre uniquement le lot actif et ses gates.

## État courant

A1: **CLOSED**.
A2: produit certifié sur `677414578010a7b9983e19e035a2ee5a0001603c`; closeout documentaire descendant en cours de recertification.
A3: **NON DÉMARRÉ**.

Next exact: vérifier le HEAD documentaire final de PR #533, ses gates et sa divergence; si propre, passer la PR ready et obtenir l'accord utilisateur explicite pour merger ce HEAD exact. Après merge/post-merge vérifié, démarrer A3 dans une nouvelle conversation via `docs/audits/AGENDA_CLINIC_A3_START_PROMPT.md`.
