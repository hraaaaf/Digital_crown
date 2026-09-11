# Digital Crown — Clinique multi-praticiens

## Statut

Chantier actif. P0 en cours sur `feat/clinic-multipractitioner-p0`.

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

## P0 — Agenda multi-praticiens réel

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

### Preuve attendue

Migration Alembic + tests automatisés create/update/conflicts/bulk/tenant/legacy + CI GitHub sur le HEAD exact.

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
- Le modèle agenda actuel utilise `Appointment.employer_id`, `datetime_start` et `duration_minutes`.
- Chaîne Alembic vérifiée au démarrage P0 : `f7a8b9c0d1e2 → c1a55e700001 → c2a55e700002`.

## Next exact

Implémenter P0 sur le modèle réel : `praticien_id` nullable → validation tenant/praticien → conflits par praticien + legacy global → bulk atomique → vue multi-praticien réelle → migration → tests → CI.
