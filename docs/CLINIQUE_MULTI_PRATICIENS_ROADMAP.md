# Digital Crown — Clinique multi-praticiens

## Statut

P0 backend certifié sur le code HEAD `f2e96286409ac22783afb3eff6b9651dce9d7ebc`. Closeout documentaire en cours sur `feat/clinic-multipractitioner-p0`; P1 UX clinique ciblée est le prochain lot.

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

## P0 — Agenda multi-praticiens réel — CERTIFIÉ

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

## P1 — UX clinique ciblée

Dashboard, Agenda, contexte praticien global et Team Manager. Toute modification visuelle suit obligatoirement : BEFORE → Goal → mockup/référence → implémentation → AFTER aux mêmes viewports 390/768/1280 → comparaison + tests → score visuel.

## P2 — Patient, actes et facturation

Ajouter le praticien référent du patient, l'auteur/praticien des actes quand pertinent, puis les agrégations de production/CA par praticien avec règles d'accès cabinet cohérentes.

## P3 — Documents, signatures et ressources

Étendre les signatures/auteurs de documents, permissions avancées et, si justifié par le workflow clinique, ressources physiques (salles/fauteuils).

## Différé

Multi-site : hors périmètre tant qu'un besoin produit réel et prioritaire n'est pas démontré.

## Références

- `docs/PATIENT_P3_CLINIQUE_GOAL.md` reste une référence complémentaire; ce chantier ne le remplace pas.
- Le modèle agenda utilise `Appointment.employer_id`, `datetime_start`, `duration_minutes` et désormais `praticien_id`.
- Chaîne Alembic au démarrage P0 : `f7a8b9c0d1e2 → c1a55e700001 → c2a55e700002`; P0 ajoute `d3a55e700003`.

## Next exact

Merger le closeout P0 après vérification de la PR, vérifier `master` post-merge, puis ouvrir P1 par la capture BEFORE des écrans Dashboard/Agenda/Team Manager aux viewports 390/768/1280 avant toute modification UI.
