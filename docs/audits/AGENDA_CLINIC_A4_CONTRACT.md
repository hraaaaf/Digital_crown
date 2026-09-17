# Agenda Clinique — A4 Resource Contract

Date: 2026-09-17
Baseline: `master@b91924d67aa0f0d8d79af32c9c028ccb874e7af4`
Lot: **A4 — Fauteuils / salles / ressources**
État: **CONTRAT VERROUILLÉ — IMPLÉMENTATION EN COURS**

## Goal

Modéliser la capacité physique du cabinet avec une ressource clinique facultative et empêcher qu'une même ressource de capacité 1 soit occupée par deux rendez-vous exact-time qui se chevauchent, sans modifier les contrats A1-A3.

## Succès observable

- le cabinet peut définir des ressources `CHAIR`, `ROOM` ou `OTHER`;
- chaque ressource appartient strictement à un `employer_id`;
- `Appointment.resource_id` reste nullable: aucun backfill ni affectation silencieuse;
- une ressource active du même cabinet peut être affectée à un nouveau rendez-vous;
- une ressource inactive reste lisible dans l'historique mais ne peut plus être nouvellement affectée;
- deux rendez-vous exact-time non annulés ne peuvent pas se chevaucher sur la même ressource;
- le conflit ressource est indépendant du conflit praticien A1-A3;
- une ressource référencée historiquement n'est pas hard-delete: désactivation uniquement;
- les rendez-vous sans ressource conservent le comportement A1-A3.

## Décisions minimales

1. **Une table générique `agenda_resources`**, pas deux modèles salle/fauteuil.
2. **Typage explicite** `CHAIR | ROOM | OTHER` pour éviter une migration ultérieure juste pour distinguer l'usage.
3. **Capacité fixe = 1 en A4**. Pas de capacité configurable: hors scope et inutile pour le Goal.
4. **Affectation facultative**. `resource_id = NULL` est valide et n'est jamais interprété comme bloqueur global.
5. **Inactive = interdite pour nouvelle affectation**, historique conservé.
6. **Pas de hard-delete métier** en A4; l'action de retrait est une désactivation.
7. **Pas d'affectation par défaut depuis le praticien**: cela créerait une réaffectation implicite non prouvée.
8. **Conflit ressource séparé du conflit praticien**: même règle d'overlap temporel, mais aucun couplage de portée.

## Invariants

- tenant: une ressource d'un autre cabinet retourne un refus et n'est jamais exposée comme assignable;
- exact-time: conflit si `existing.start < candidate.end` ET `candidate.start < existing.end`;
- rendez-vous annulés exclus des collisions;
- update exclut le rendez-vous courant;
- changer uniquement `resource_id` déclenche la validation ressource et collision;
- create/update/bulk/check-conflicts doivent appliquer la même sémantique avant closeout;
- A1-A3 restent régressés: praticien scoped, legacy `praticien_id=NULL` global, disponibilité cabinet ∩ praticien.

## Preuve requise avant fermeture A4

- migration Alembic non destructive et upgrade PostgreSQL vert;
- tests unitaires/intégration tenant + active/inactive + collisions create/update/bulk/check-conflicts;
- régression A1-A3 verte;
- CI exact HEAD verte;
- si UI modifiée: BEFORE → Goal → référence/mockup → AFTER mêmes viewports → comparaison/tests → validation humaine;
- revue adversariale + Perfection Pass;
- aucun merge sans accord explicite utilisateur sur le HEAD exact.
