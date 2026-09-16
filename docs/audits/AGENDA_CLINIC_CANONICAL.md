# Digital Crown — Agenda clinique multi-praticiens

Statut: chantier actif — A1 mergé, certification post-merge du master courant en cours
Date d'ouverture: 2026-09-16
Repo: `hraaaaf/Digital_crown`
Branche d'ouverture: `feat/agenda-clinic-a1-practitioner-filter-20260916`
Base vérifiée à l'ouverture: `master@a396acfd6570ff24ca683009e1f31bdb3f2c0d92`
CI master de référence à l'ouverture: `CI #4494` — SUCCESS

## Goal global

Faire évoluer l'agenda existant vers un agenda réellement exploitable en clinique multi-dentistes sans réécrire le moteur actuel et sans casser les données, rendez-vous, documents ou comportements déjà validés.

Architecture à préserver:

`Appointment + employer_id + praticien_id + logique de conflits existante`

Le chantier ajoute une couche clinique au-dessus de ce socle.

## Baseline vérifiée avant chantier

- Les rendez-vous sont isolés par `employer_id`.
- `praticien_id` est un FK nullable vers `users.id`.
- Un praticien assignable doit être actif, approuvé et appartenir au cabinet.
- Deux praticiens différents peuvent avoir un rendez-vous au même horaire.
- Un même praticien ne peut pas avoir deux rendez-vous exact-time qui se chevauchent.
- Les rendez-vous legacy avec `praticien_id = NULL` sont des bloqueurs globaux.
- La création, la réaffectation et le bulk revalident les conflits.
- Les horaires et exceptions actuels sont au niveau cabinet, pas au niveau praticien.
- Avant A1, les vues Jour/Semaine/Mois lisaient l'ensemble des rendez-vous du cabinet.
- Avant A1, le sélecteur praticien influençait l'attribution des nouveaux rendez-vous, pas la lecture de l'agenda standard.
- Une vue multi-praticiens PREMIUM+ existe mais n'est pas encore une grille horaire synchronisée.
- Aucun fauteuil/salle/ressource n'est actuellement modélisé dans `Appointment`.

## Règles de sécurité du chantier

1. Préserver la compatibilité des données existantes.
2. Aucune migration destructive.
3. Aucun changement silencieux d'affectation d'un rendez-vous existant.
4. Les rendez-vous legacy non assignés restent visibles tant qu'ils peuvent bloquer un créneau.
5. Toute modification significative doit inclure des tests de non-régression adaptés.
6. Aucun merge sans accord explicite utilisateur sur le HEAD exact.
7. Aucun déploiement Vercel sans autorisation explicite.
8. Un lot à la fois; pas de mélange de responsabilités entre lots.
9. Toute modification UI/UX visuelle doit suivre BEFORE → Goal → référence/mockup → implémentation → AFTER mêmes viewports → comparaison/tests → score visuel.

## Découpage canonique

### LOT A1 — Filtrage praticien réel

Goal: quand un praticien est sélectionné dans le contexte clinique, les vues Jour/Semaine/Mois affichent réellement son agenda.

Succès observable:
- `GET /appointments/` accepte un filtre praticien sécurisé et tenant-scoped;
- la vue d'un praticien inclut ses rendez-vous et les rendez-vous legacy non assignés qui restent des bloqueurs globaux;
- elle n'affiche pas les rendez-vous attribués à un autre praticien;
- sans filtre, le comportement historique cabinet-wide est inchangé;
- le changement de praticien rafraîchit Jour/Semaine/Mois;
- création et édition conservent les règles actuelles d'attribution/non-réaffectation;
- tests backend + frontend/non-régression verts sur le HEAD pré-merge exact.

État vérifié A1:
- PR `#528` — `feat(agenda): A1 real practitioner filtering`;
- HEAD pré-merge exact: `9e3d9e8de8362b8bb4d69e908e1c68b971d43f51`;
- CI pré-merge `#4520` — SUCCESS;
- T2 Runtime Browser Certification `#3392` — SUCCESS;
- Cabinet Upgrade PostgreSQL Certification `#907` — SUCCESS;
- Clinic P1 Multi-Practitioner Visual Certification `#109` — SUCCESS;
- M6-I Biometric Passkey Certification `#2192` — SKIPPED attendu;
- aucun commentaire, aucune review et aucun review thread au dernier contrôle avant merge;
- PR #528 mergée avec accord utilisateur explicite;
- merge commit A1: `86958c913e5c2872504505eb3af0485b22e66c05`.

Post-merge:
- le CI push `#4527` sur `86958c913e5c2872504505eb3af0485b22e66c05` a été CANCELLED car master a avancé immédiatement après;
- master vérifié ensuite: `8a37913c23f182a8de4e0f1dd0e2049e48b7267f`, qui contient `86958c913e5c2872504505eb3af0485b22e66c05` comme parent;
- sur ce master courant, `CI #4528` et `Cabinet Upgrade PostgreSQL Certification #912` étaient QUEUED au dernier contrôle;
- ne pas déclarer la certification post-merge A1 terminée tant que ces gates du master contenant A1 ne sont pas vérifiés verts.

Hors scope A1:
- grille multi-lanes;
- horaires individuels;
- fauteuils/salles/ressources;
- timezone explicite;
- soft-delete;
- migration des rendez-vous legacy.

### LOT A2 — Vue clinique multi-praticiens

Goal: remplacer la lecture multi-praticiens en listes verticales par une vraie matrice horaire synchronisée, sans modifier la logique métier des disponibilités individuelles.

Cible UX: `Heure | Dr A | Dr B | Dr C ...`, avec création/édition dans la colonne du praticien et lecture immédiate des créneaux occupés/libres.

Gate d'entrée A2:
1. lire le présent fichier et `docs/audits/AGENDA_CLINIC_A1_HANDOVER.md`;
2. vérifier le master ACTUEL, sans réutiliser un SHA ancien;
3. confirmer que le merge A1 est bien ancêtre du master;
4. vérifier les certifications post-merge pertinentes du master contenant A1;
5. si un gate est rouge, diagnostiquer/corriger avant A2;
6. si les gates sont verts, exécuter obligatoirement le protocole UI/UX A2: BEFORE → Goal écrit → mockup/référence → implémentation → AFTER mêmes viewports → comparaison/tests → score visuel.

### LOT A3 — Disponibilités individuelles

Goal: horaires, jours travaillés, pauses, congés et absences propres à chaque praticien, superposés aux fermetures globales du cabinet.

### LOT A4 — Fauteuils / salles / ressources

Goal: capacité physique réelle du cabinet avec allocation facultative de ressource et contrôle des collisions praticien + ressource.

### LOT A5 — Robustesse clinique + closeout

Goal: timezone cabinet explicite, stratégie soft-delete/historique, traitement/migration legacy, non-régression globale, documentation et certification finale du chantier.

## Règle d'or de continuité

A1 se traite dans la conversation d'ouverture du chantier.

Dès que A1 est mergé et que A2 devient le prochain lot, produire obligatoirement:
1. un handover compact et vérifié d'A1;
2. un prompt prêt à copier pour une NOUVELLE conversation dédiée à A2;
3. le chemin exact du présent fichier canonique à lire en premier;
4. l'état repo/branche/PR/HEAD/CI exact au moment du handover.

Même règle ensuite pour chaque changement de lot.

## Procédure de reprise

Dans toute nouvelle conversation:
1. lire intégralement `docs/audits/AGENDA_CLINIC_CANONICAL.md` et le dernier handover du chantier;
2. vérifier `master`, branche du lot, PR, HEAD, CI et divergence réelle;
3. ne jamais supposer qu'un SHA ou une CI ancien est encore actuel;
4. reprendre uniquement le lot actif et ses gates.

## État courant

A1: MERGÉ — post-merge du master contenant A1 à confirmer.
Prochain lot: A2 — Vue clinique multi-praticiens.

Next exact: vérifier une fois `CI #4528` et `Cabinet Upgrade PostgreSQL Certification #912` sur le master contenant A1; si verts, A1 est clôturable et la nouvelle conversation A2 peut démarrer par le BEFORE UI/UX.
