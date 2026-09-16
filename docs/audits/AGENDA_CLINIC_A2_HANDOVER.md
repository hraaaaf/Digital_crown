# HANDOVER — Digital Crown / Agenda clinique — A2 → A3

Date: 2026-09-16
Repo: `hraaaaf/Digital_crown`
Fichier canonique: `docs/audits/AGENDA_CLINIC_CANONICAL.md`
Référence UX A2: `docs/audits/AGENDA_CLINIC_A2_UX_REFERENCE.md`

## Première action obligatoire dans la nouvelle conversation

1. Lire intégralement `docs/audits/AGENDA_CLINIC_CANONICAL.md`.
2. Lire intégralement le présent handover.
3. Vérifier GitHub live: master ACTUEL, PR #533 si elle existe encore, merge A2, HEAD, CI/certifications, reviews/threads et divergence.
4. Ne jamais supposer qu'un SHA ou un statut ci-dessous est encore actuel.
5. Si A2 n'est pas mergé, terminer A2 avant de démarrer A3.
6. Si A2 est mergé, vérifier son post-merge avant toute modification A3.

## Goal global du chantier

Faire évoluer l'agenda existant vers un agenda réellement exploitable en clinique multi-dentistes en préservant:

`Appointment + employer_id + praticien_id + logique de conflits existante`.

## A2 — résultat produit certifié pré-merge

Goal A2:
remplacer la vue Multi en listes verticales par une grille horaire journalière synchronisée par praticien, sans introduire les disponibilités individuelles A3.

Résultat livré:
- vue Multi quotidienne avec navigation J-1/J+1;
- axe horaire commun;
- slots 15 min, 80 px/h;
- une lane par praticien actif/assignable;
- rendez-vous exact-time positionnés à leur heure réelle et selon leur durée;
- rendez-vous flexibles conservés sans heure inventée;
- rendez-vous historiques `praticien_id = NULL` affichés comme bloqueurs transversaux explicites;
- création depuis une lane avec praticien injecté au contrôle de conflit ET au POST;
- intercepteur création installé avant ouverture modal et retiré à la fermeture/édition/unmount;
- aucun `praticien_id` injecté dans un PUT d'édition;
- horaires globaux cabinet réutilisés;
- Jour/Semaine/Mois A1 préservés;
- responsive avec scroll horizontal interne sur petit écran;
- aucun backend A2;
- aucune migration DB.

## Preuve produit A2

PR: `#533` — `feat(agenda): A2 synchronized multi-practitioner grid`
Branche: `feat/agenda-clinic-a2-multi-grid-20260916`
HEAD produit certifié: `677414578010a7b9983e19e035a2ee5a0001603c`

BEFORE:
- run `35084989399` — SUCCESS;
- HEAD capture `2911da0f4e8bd4766b725089924e5ba5a616eaff`;
- viewports `390×844`, `768×1024`, `1280×900`;
- digest `sha256:c4fc22b6a489170e06b5a7f6ff09f76cdaa2e68ac40cec82c5bdd55abc7a3755`.

AFTER canonique:
- Agenda A2 AFTER Visual Certification V2 `#11` / run `35093443999` — SUCCESS;
- artifact id `10445091768`;
- digest `sha256:51eab42cf5522cc199b7f3cfd561518406a658427916a74e8155cc922b3739d4`;
- mêmes trois viewports;
- `syncDelta = 0 px` aux trois viewports;
- aucune erreur navigateur;
- aucun overflow horizontal de page;
- création lane Dr Youssef: `praticien_id = 2` au GET conflit et au POST;
- modal seedé `2026-09-16 15:00`, durée 30 min;
- score visuel observé: `9.1/10`.

Gates exacts sur le HEAD produit certifié:
- CI `#4558` / run `35093443889` — SUCCESS;
- T2 Runtime Browser `#3425` / run `35093443907` — SUCCESS;
- Clinic P1 Multi-Practitioner Visual `#125` / run `35093444003` — SUCCESS;
- A2 AFTER V2 `#11` / run `35093443999` — SUCCESS;
- M6-I `#2225` — SKIPPED attendu;
- A2 focused contract: 4/4 PASS.

Au dernier contrôle du HEAD produit:
- master `bc3d8d145670dc70dc6c6842e772e56d1d89aa99`;
- branche A2 ahead 18 / behind 0;
- PR #533 mergeable et draft;
- aucune review, aucun commentaire, aucun review thread.

Important: le closeout documentaire est ajouté sur un descendant docs-only du HEAD produit certifié. Vérifier son SHA/gates live avant merge. Aucun merge A2 ne doit être supposé à partir du présent handover.

## Invariants backend revalidés

`GET /appointments/check-conflicts`:
- accepte `praticien_id`;
- valide le praticien dans le tenant;
- limite les collisions au praticien ciblé;
- inclut les rendez-vous `praticien_id = NULL` comme bloqueurs globaux.

`GET /appointments/multi-practitioner`:
- expose les rendez-vous par praticien;
- expose les historiques non assignés via `legacy_unassigned`.

A2 n'a pas modifié ce moteur.

## A1 — statut à conserver

A1 est clôturé:
- PR #528 mergée;
- merge commit `86958c913e5c2872504505eb3af0485b22e66c05`;
- master contenant A1 `8a37913c23f182a8de4e0f1dd0e2049e48b7267f`;
- CI post-merge #4528 — SUCCESS;
- PostgreSQL #912 — SUCCESS.

## A3 — baseline vérifiée

Aujourd'hui, les disponibilités sont globales cabinet:
- `cabinet_settings.weekly_schedule_json` est tenant-scoped par `employer_id`;
- `agenda_exceptions` est tenant-scoped par `employer_id`;
- `validate_appointment_availability(...)` applique ces horaires/fermetures à tout le cabinet;
- aucune structure individuelle praticien n'a été introduite par A2.

## A3 — Goal exact

Ajouter horaires, jours travaillés, pauses, congés et absences propres à chaque praticien, superposés aux fermetures globales du cabinet.

Principe fonctionnel:

`disponibilité effective = disponibilité cabinet ∩ disponibilité praticien`.

Succès attendu A3:
- planning hebdomadaire individuel par praticien;
- pauses individuelles;
- congés/absences/exceptions individuelles;
- fermeture cabinet = blocage pour tous;
- indisponibilité individuelle = blocage du seul praticien concerné;
- un autre praticien peut rester disponible au même horaire;
- grille A2 distingue visuellement les indisponibilités individuelles;
- création, édition/réaffectation et contrôle de conflit refusent côté serveur un praticien indisponible;
- Jour/Semaine/Mois filtrés A1 restent cohérents;
- rendez-vous `praticien_id = NULL` restent des bloqueurs globaux;
- compatibilité des cabinets existants préservée;
- migration uniquement additive si nécessaire;
- tests backend/frontend/browser proportionnels au risque;
- protocole UI BEFORE → Goal → référence → implémentation → AFTER identiques viewports.

## Hors scope A3

- A4: fauteuils, salles, ressources physiques;
- A5: timezone cabinet explicite, soft-delete/historique, migration legacy;
- aucune réécriture du moteur de collisions au-delà de l'extension nécessaire à la disponibilité individuelle.

## Sécurité A3

- auditer modèles/migrations et chemin d'upgrade avant de choisir un schéma;
- aucune migration destructive;
- global cabinet reste autoritaire;
- tenant isolation `employer_id` obligatoire;
- aucun changement silencieux d'affectation;
- aucun déploiement Vercel sans autorisation explicite;
- aucun merge sans accord explicite utilisateur sur le HEAD exact.

## Next exact

Si A2 n'est pas encore mergé:
1. vérifier le HEAD final docs-only de PR #533;
2. certifier/revoir la divergence et les gates;
3. obtenir l'accord utilisateur explicite;
4. merger;
5. vérifier le post-merge.

Si A2 est déjà mergé et post-merge propre:
1. ouvrir A3 dans une nouvelle conversation avec `docs/audits/AGENDA_CLINIC_A3_START_PROMPT.md`;
2. capturer le BEFORE A3 avant toute modification visuelle;
3. auditer la persistance/migrations existantes avant toute évolution de schéma;
4. figer la référence UX A3 avant l'implémentation.
