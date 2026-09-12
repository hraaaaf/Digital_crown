# Digital Crown — Clinique multi-praticiens

## Statut

P0 backend certifié puis mergé dans `master` via PR #429, merge commit `f265ebcd9f0654f346a969def5d93f66451af67d`. P1 UX clinique est certifié sur le code HEAD `3c29f2e29b730d447aff72f81416249bdf5073f5`; closeout documentaire final sur `feat/clinic-multipractitioner-p1-ui` / PR #430 avant merge.

## Goal global

Faire évoluer Digital Crown d'un agenda de cabinet partagé vers un fonctionnement clinique réellement multi-praticiens, sans casser les données historiques ni mélanger les axes licence, abonnement et type de cabinet.

## Principes invariants

- Le tenant canonique reste le cabinet propriétaire : `User.get_employer_id()` / `Appointment.employer_id`.
- Le praticien canonique est un `User.id` existant, pas une table parallèle.
- Un praticien assignable appartient au même cabinet, est actif, approuvé et a le rôle `DENTISTE`; le propriétaire du cabinet est également assignable lorsqu'il est dentiste/admin actif.
- Les rendez-vous historiques restent valides sans backfill forcé.
- `praticien_id = NULL` signifie rendez-vous legacy/non assigné et conserve un comportement de blocage global pour prévenir les doubles réservations historiques.
- Un rendez-vous assigné ne conflit qu'avec le même praticien ou avec un rendez-vous legacy/non assigné qui chevauche le créneau.
- Deux praticiens différents peuvent travailler simultanément.
- Les imports bulk obéissent aux mêmes règles d'accès, de disponibilité et de conflit que la création unitaire.
- Aucun changement de déploiement Vercel dans ce chantier sans autorisation explicite.

## P0 — Agenda multi-praticiens réel — CERTIFIÉ / MERGÉ

### Goal

Attribuer chaque nouveau rendez-vous à un praticien réel et isoler les conflits par praticien, tout en conservant les rendez-vous historiques `NULL` et l'isolation tenant.

### Succès observable

1. `appointments.praticien_id` existe, nullable, FK vers `users.id`, indexé.
2. Create/update/check-conflicts/bulk valident le praticien dans le cabinet courant.
3. Même praticien + chevauchement exact => HTTP 409.
4. Deux praticiens différents + même créneau => autorisé.
5. Rendez-vous legacy `praticien_id=NULL` + chevauchement => bloque toute nouvelle réservation du créneau.
6. Secrétaire, dentiste pending/inactif ou utilisateur d'un autre cabinet => refus.
7. `/multi-practitioner` groupe les rendez-vous par `praticien_id` réel et expose séparément le legacy non assigné.
8. Les rendez-vous historiques restent lisibles et aucune migration destructive/backfill n'est effectuée.
9. Tests backend et CI verts sur le HEAD exact.

### Preuve vérifiée

- Code HEAD certifié : `f2e96286409ac22783afb3eff6b9651dce9d7ebc`.
- CI GitHub run `34660038023` : `completed / success`.
- Job backend `Tests & durcissement` `103460450879` : `completed / success`, incluant `Test suite` et `Prod safety check`.
- Frontend tests + build : success.
- M4-A, M4-B, M4-C et garde production : success.
- Certifications exact-head : Patient P7 `34660038043` success; T2 Runtime Browser `34660038036` success; Marketplace `34660038059` success; Catalog Connected Truth `34660038075` success. M6-I `34660037963` skipped.
- Migration Alembic et tests automatisés create/update/conflicts/bulk/tenant/legacy font partie du code certifié.
- PR #429 mergée ; `master` vérifié sur `f265ebcd9f0654f346a969def5d93f66451af67d`.

## P1 — UX clinique ciblée — CERTIFIÉ

### Goal

Rendre le praticien actif explicite sur Dashboard, Agenda et Team Manager, puis l'utiliser comme contexte réel des nouvelles écritures Agenda sans réaffectation silencieuse d'un rendez-vous existant.

### BEFORE vérifié

- Baseline HEAD : `eedb1e6a57f57c016f6837f45dd06e6a671866b9`.
- Run visuel : `34681249518` — success.
- 9 captures : Dashboard / Agenda / Team × 390x844 / 768x1024 / 1280x900.
- Dashboard 390 : `scrollWidth=402` pour `clientWidth=390`, soit 12 px de débordement dans le harnais direct.
- Agenda / Team : 0 overflow, mais aucun contexte praticien global explicite.

### Implémentation certifiée

Référence détaillée : `docs/clinic/P1_MULTI_PRACTITIONER_UI.md`.

- rail glass « Contexte clinique » avec chips praticiens ;
- état de sélection session partagé ;
- affichage sur Dashboard / Agenda / Settings ;
- Agenda create / bulk / conflict-check utilisent le praticien actif sans écraser un `praticien_id` explicite ;
- update conserve le praticien existant si le payload ne demande pas explicitement une réaffectation ;
- mapping rendez-vous → praticien utilisé pour le conflict-check d'une édition ;
- tests de contrat frontend ajoutés.

### AFTER vérifié

- Code HEAD certifié : `3c29f2e29b730d447aff72f81416249bdf5073f5`.
- Visual P1 `34681876692` : completed / success.
- T2 Runtime Browser `34681876693` : completed / success.
- CI principale `34681876685` : completed / success.
- Voluntary Tutorial Visual `34681876771` : completed / success.
- 9 captures AFTER : Dashboard / Agenda / Team × 390x844 / 768x1024 / 1280x900.
- 0 overflow horizontal sur les 9 captures.
- 0 pageerror / console error selon le gate exact-head.
- Dashboard 390 : 12 px overflow BEFORE → 0 AFTER.
- Score visuel documenté : **9,2 / 10**.
- Aucun déploiement Vercel.

### Verdict

P1 est certifié côté code et UX. La PR #430 doit encore être mergée puis `master` vérifié avant ouverture du P2.

## P2 — Patient, actes et facturation

Ajouter le praticien référent du patient, l'auteur/praticien des actes quand pertinent, puis les agrégations de production/CA par praticien avec règles d'accès cabinet cohérentes.

## P3 — Documents, signatures et ressources

Étendre les signatures/auteurs de documents, permissions avancées et, si justifié par le workflow clinique, ressources physiques (salles/fauteuils).

## Différé

Multi-site : hors périmètre tant qu'un besoin produit réel et prioritaire n'est pas démontré.

## Références

- `docs/PATIENT_P3_CLINIQUE_GOAL.md` reste une référence complémentaire; ce chantier ne le remplace pas.
- `docs/clinic/P1_MULTI_PRACTITIONER_UI.md` est la spécification visuelle et fonctionnelle P1.
- Le modèle agenda utilise `Appointment.employer_id`, `datetime_start`, `duration_minutes` et désormais `praticien_id`.
- Chaîne Alembic au démarrage P0 : `f7a8b9c0d1e2 → c1a55e700001 → c2a55e700002`; P0 ajoute `d3a55e700003`.

## Next exact

Vérifier les checks du HEAD documentaire final de la PR #430. S'ils sont verts : merger #430, vérifier `master` post-merge, puis ouvrir P2. En cas d'échec d'un check : diagnostiquer et corriger avant merge.
