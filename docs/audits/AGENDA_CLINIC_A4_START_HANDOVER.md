# Agenda Clinique — A4 Start Handover

Date: 2026-09-17
Repo: `hraaaaf/Digital_crown`
Canonique: `docs/audits/AGENDA_CLINIC_CANONICAL.md`
Lot cible: **A4 — Fauteuils / salles / ressources**
État: **NON DÉMARRÉ**

## Goal A4

Modéliser la capacité physique du cabinet avec allocation facultative d'une ressource clinique (fauteuil, salle ou ressource équivalente) et empêcher les collisions incompatibles, sans casser les règles A1-A3.

Succès observable:
- une ressource peut être définie au niveau du cabinet;
- un rendez-vous peut rester sans ressource pour préserver la compatibilité historique;
- lorsqu'une ressource est affectée, deux rendez-vous incompatibles ne peuvent pas occuper simultanément cette même ressource;
- les collisions praticien existantes restent appliquées indépendamment;
- les rendez-vous `praticien_id = NULL` conservent leur comportement de bloqueur global tel que certifié A1-A3;
- aucune migration destructive ni réaffectation silencieuse;
- UI/UX validée selon BEFORE → Goal → référence/mockup → implémentation → AFTER mêmes viewports → comparaison/tests → validation humaine.

## Baseline à préserver

A1, A2 et A3 sont CLOSED.

Contrats déjà certifiés:
- isolation cabinet par `employer_id`;
- `praticien_id` nullable pour compatibilité historique;
- conflit praticien-scoped avec legacy NULL global;
- disponibilité effective = cabinet ∩ praticien;
- fermetures cabinet absolues;
- création / mise à jour / bulk / check-conflicts practitioner-aware;
- vue multi-praticiens synchronisée;
- aucune modification visuelle A3 après le HEAD humainement validé `c286bcf9713bc9fcc5a9701a7fa75b35d94d843c`.

Preuve finale A3:
- PR #568 mergée sur `ec6bf4f40137f6e7d395effd97e0be3b0f6a2362`;
- Cabinet Upgrade PostgreSQL #944 / `35204790254`: SUCCESS;
- CI #4761 / `35204790247`: SUCCESS, Frontend + garde production + Full backend regression;
- master a ensuite avancé vers `7d936cc76257911d03e98f7788f25056399783d3` uniquement par 4 fichiers de documentation Céphalo.

## Contraintes de conception A4

Ne pas supposer avant audit:
- qu'une nouvelle table est forcément nécessaire;
- qu'un rendez-vous doit obligatoirement avoir une ressource;
- qu'une salle et un fauteuil doivent être deux modèles séparés;
- qu'un conflit ressource doit réutiliser exactement la logique de conflit praticien;
- qu'un changement UI est nécessaire avant d'avoir inspecté le flux existant.

Préférer le modèle minimal compatible avec l'existant.

## Ordre de reprise obligatoire

1. Lire intégralement `docs/audits/AGENDA_CLINIC_CANONICAL.md`.
2. Lire `docs/audits/AGENDA_CLINIC_A3_CLOSEOUT.md`.
3. Vérifier live master, HEAD, PR ouvertes, CI et divergence.
4. Vérifier la roadmap V1 consolidée: A4 ne doit pas être lancé simplement parce qu'A3 est fermé si un autre chantier est prioritaire pour le freeze V1.
5. Si A4 est effectivement le prochain lot global, auditer:
   - modèle `Appointment` et migrations;
   - endpoints create/update/bulk/check-conflicts;
   - logique actuelle de collisions;
   - Settings cabinet et écrans Agenda concernés;
   - tests Agenda A1-A3 pertinents.
6. Écrire le contrat de données minimal A4 et les invariants avant toute migration.
7. Pour toute UI/UX: produire le BEFORE aux mêmes viewports utilisés ensuite pour AFTER.
8. Implémenter backend/data/tests avant de complexifier l'UI.
9. Faire les preuves exact-head, revue adversariale, Perfection Pass, puis closeout.
10. Aucun merge sans accord explicite utilisateur sur le HEAD exact; aucun déploiement Vercel sans autorisation explicite.

## Questions que l'audit doit trancher, pas le handover

- Ressource générique unique (`resource`) ou typage fauteuil/salle?
- Capacité = 1 uniquement pour MVP A4 ou capacité configurable?
- Ressource inactive: blocage des nouveaux rendez-vous uniquement ou traitement particulier des historiques?
- Suppression: interdite si historique référencé, soft-delete ou autre stratégie?
- Affectation par défaut à partir du praticien: utile ou source de réaffectation silencieuse?

Ces points sont des décisions d'implémentation à résoudre par preuve du repo et simplicité, pas des hypothèses déjà validées.

## Non-goals A4

- ne pas traiter la timezone globale A5;
- ne pas lancer une migration legacy générale A5;
- ne pas refondre l'Agenda;
- ne pas modifier les contrats A1-A3 sans nécessité démontrée;
- ne pas geler V1 à ce stade.

## Next exact

Vérifier la roadmap V1 consolidée. Si A4 est le prochain chantier retenu, démarrer par l'audit du modèle de données et de la logique de collision, puis produire un plan A4 exact avec Goal / Succès / Preuve avant le premier changement produit.
