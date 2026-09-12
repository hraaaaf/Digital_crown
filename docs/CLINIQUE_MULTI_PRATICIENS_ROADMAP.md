# Digital Crown — Clinique multi-praticiens

## Statut

P0 backend et P1 UX sont certifiés/mergés. P2 Patient, actes et facturation est certifié sur le code HEAD `33f5e6cc4de8d8345c699088832994e7cdd886a6`; closeout documentaire en cours avant merge PR #433. P3 Documents, signatures et ressources est le lot suivant.

## Goal global

Faire évoluer Digital Crown d'un agenda de cabinet partagé vers un fonctionnement clinique réellement multi-praticiens, sans casser les données historiques ni mélanger les axes licence, abonnement et type de cabinet.

## Principes invariants

- Le tenant canonique reste le cabinet propriétaire : `User.get_employer_id()` / `Appointment.employer_id`.
- Le praticien canonique est un `User.id` existant, pas une table parallèle.
- Un praticien assignable appartient au même cabinet, est actif, approuvé et a le rôle `DENTISTE`; le propriétaire du cabinet est également assignable lorsqu'il est dentiste/admin actif.
- Les données Patients et Documents locales restent la source de vérité et ne sont pas remplacées par une couche cloud.
- Les rendez-vous historiques restent valides sans backfill forcé.
- `praticien_id = NULL` signifie rendez-vous legacy/non assigné et conserve un comportement de blocage global.
- Deux praticiens différents peuvent travailler simultanément.
- Aucun changement de déploiement Vercel dans ce chantier sans autorisation explicite.

## P0 — Agenda multi-praticiens réel — CERTIFIÉ / MERGÉ

- Code HEAD certifié : `f2e96286409ac22783afb3eff6b9651dce9d7ebc`.
- CI `34660038023` : success.
- PR #429 mergée ; merge `f265ebcd9f0654f346a969def5d93f66451af67d`.
- `appointments.praticien_id` nullable, tenant-safe, conflits par praticien et legacy NULL conservés.

## P1 — UX clinique ciblée — CERTIFIÉ / MERGÉ

- Code HEAD certifié : `3c29f2e29b730d447aff72f81416249bdf5073f5`.
- Visual `34681876692`, T2 `34681876693`, CI `34681876685` : success.
- 9 captures Dashboard / Agenda / Team × 390 / 768 / 1280 : 0 overflow, 0 runtime error.
- Score visuel : **9,2 / 10**.
- PR #430 mergée ; merge `1a115752e133e583e523fea7c4180d97db956f75`.

## P2 — Patient, actes et facturation — CERTIFIÉ / CLOSEOUT

### Goal

Ajouter un référent clinique et une lecture financière multi-praticiens sans modifier la liste Patients locale ni déplacer/réécrire les documents locaux existants.

### Architecture certifiée

- `patients` reste la table canonique locale, sans nouvelle colonne P2.
- `DocumentArchive` et les fichiers/documents locaux restent inchangés.
- table additive `patient_practitioner_assignments` : 0/1 attribution par patient ; aucun backfill forcé.
- praticien référent limité au même cabinet, actif, approuvé et assignable ; secrétaire exclue comme référent.
- `Acte.praticien_id` existant reste la source d'attribution de la production.
- encaissements attribués à un praticien uniquement lorsqu'un lien vers un acte est prouvable, directement ou via un échéancier lié à l'acte.
- paiements sans preuve de rattachement restent explicitement `unattributed_collected` ; aucune ventilation artificielle.
- formulaires Nouveau / Modifier patient restent indépendants du référent afin de ne pas alourdir les données locales historiques.

### BEFORE / AFTER

- BEFORE baseline : `85cc4ca39df3d1064e1d82bb3a6a7048dc3e6d80`.
- BEFORE visual `34685062932` : success.
- 12 captures Dossier / Finances / Modifier / Nouveau × 390x844 / 768x1024 / 1280x900.
- AFTER code HEAD certifié : `33f5e6cc4de8d8345c699088832994e7cdd886a6`.
- AFTER Visual P2 `34685916843` : success.
- T2 Runtime Browser `34685916888` : success.
- Patient P7 `34685916847` : success.
- CI principale `34685916864` : success, incluant backend Tests & durcissement et frontend tests/build.
- AFTER : 12/12 captures, 0 overflow horizontal, 0 runtime/page error selon le gate exact-head.
- défaut intermédiaire de placement/capture Finances 390 détecté visuellement puis corrigé avant certification finale.
- score visuel final : **9,2 / 10**.
- référence détaillée : `docs/clinic/P2_PATIENT_PRACTITIONER_BILLING.md`.
- aucun déploiement Vercel.

## P3 — Documents, signatures et ressources

Étendre les signatures/auteurs de documents, permissions avancées et, si justifié par le workflow clinique, ressources physiques (salles/fauteuils), tout en conservant le stockage documentaire local comme source de vérité.

## Différé

Multi-site : hors périmètre tant qu'un besoin produit réel et prioritaire n'est pas démontré.

## Références

- `docs/PATIENT_P3_CLINIQUE_GOAL.md` reste une référence complémentaire.
- `docs/clinic/P1_MULTI_PRACTITIONER_UI.md` — spécification P1.
- `docs/clinic/P2_PATIENT_PRACTITIONER_BILLING.md` — spécification et preuves P2.
- Chaîne Alembic : P0 `d3a55e700003`; P2 ajoute `e4a55e700004` de façon additive.

## Next exact

Merger PR #433 avec garde SHA documentaire, vérifier `master`, puis ouvrir P3 par l'audit Documents / signatures / auteurs / permissions en préservant strictement les documents locaux existants.
