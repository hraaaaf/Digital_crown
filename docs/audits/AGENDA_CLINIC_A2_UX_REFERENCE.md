# Agenda clinique — A2 UX reference

Date: 2026-09-16
Lot: A2 — Vue clinique multi-praticiens
PR: #533
Base produit BEFORE: `bc3d8d145670dc70dc6c6842e772e56d1d89aa99`

## BEFORE — preuve figée avant implémentation

Workflow: `Agenda A2 BEFORE Visual Certification`
Run: `35084989399` — SUCCESS
HEAD de capture: `2911da0f4e8bd4766b725089924e5ba5a616eaff`
Artifact: `agenda-a2-before-visual-evidence`
Digest: `sha256:c4fc22b6a489170e06b5a7f6ff09f76cdaa2e68ac40cec82c5bdd55abc7a3755`

Viewports immuables:
- 390 × 844
- 768 × 1024
- 1280 × 900

Constats BEFORE:
1. rendez-vous empilés verticalement par praticien, sans axe horaire partagé;
2. plusieurs jours mélangés alors que l'en-tête porte une date unique;
3. `legacy_unassigned` présent côté API mais absent de la vue Multi;
4. lecture mobile peu exploitable pour plusieurs praticiens;
5. navigation précédent/suivant non journalière en mode Multi.

Aucun fichier produit n'a été modifié pour capturer le BEFORE.

## GOAL A2

Remplacer la lecture Multi par une grille journalière synchronisée:

`Heure | Dr A | Dr B | Dr C | ...`

Le même axe temporel doit permettre de lire immédiatement les créneaux libres/occupés de tous les praticiens actifs/assignables sans modifier les règles existantes d'attribution, de collision ni d'isolation cabinet.

## Succès observable

- axe horaire commun;
- une lane par praticien actif/assignable;
- rendez-vous exact dans la bonne lane, à sa vraie heure et durée;
- création depuis une lane attribue explicitement ce praticien;
- contrôle de conflit de la création utilise le même praticien;
- édition sans réaffectation silencieuse;
- rendez-vous `praticien_id = NULL` visibles comme bloqueurs transversaux;
- rendez-vous flexibles conservés sans heure inventée;
- horaires globaux cabinet réutilisés, sans disponibilité individuelle A3;
- Jour/Semaine/Mois A1 préservés;
- aucune migration DB;
- responsive utilisable et aucun overflow horizontal de page.

## Référence UX figée avant implémentation

```text
┌────────┬──────────────────────┬──────────────────────┬──────────────────────┐
│ HEURE  │ Dr Lina Alaoui       │ Dr Youssef Benali    │ Dr Salma Idrissi     │
│        │ 2 RDV aujourd'hui    │ 2 RDV aujourd'hui    │ 1 RDV aujourd'hui    │
├────────┼──────────────────────┼──────────────────────┼──────────────────────┤
│ 09:00  │ Sara · Consultation  │ Yasmine · Prothèse   │                      │
│        │ 30 min               │ 60 min               │                      │
├────────┼──────────────────────┼──────────────────────┼──────────────────────┤
│ 10:00  │                      │                      │ Aya · 10:30 · 30 min │
├────────┼──────────────────────┼──────────────────────┼──────────────────────┤
│ 11:00  │ Adam · Endodontie    │                      │                      │
├────────┴──────────────────────┴──────────────────────┴──────────────────────┤
│ 12:00  NON ASSIGNÉ — bloque tous les praticiens — 30 min                   │
├────────┬──────────────────────┬──────────────────────┬──────────────────────┤
│ 13:00  │      HORS HORAIRES CABINET / pause globale existante              │
├────────┼──────────────────────┼──────────────────────┼──────────────────────┤
│ 14:00  │                      │ Omar · 14:30 · 30 min│                      │
├────────┼──────────────────────┼──────────────────────┼──────────────────────┤
│ 15:00+ │        zones blanches = créneaux libres cliquables                 │
└────────┴──────────────────────┴──────────────────────┴──────────────────────┘
```

Décisions figées:
- Multi = vue journalière J-1/J+1;
- slots de 15 min, 80 px par heure;
- axe horaire fixe à gauche;
- lane praticien min-width 220 px;
- desktop: lanes utilisent la largeur disponible;
- tablette/mobile: même matrice avec scroll horizontal interne, jamais conversion en listes;
- horaires fermés globaux grisés et non créables;
- rendez-vous hors horaires existants restent visibles;
- legacy exact-time = bande transversale à son heure réelle;
- flexibles = zone dédiée sans placement horaire inventé;
- modal de création indique visuellement le praticien choisi.

## Contrat de sécurité réellement implémenté

Création depuis une lane:
- `MultiPractitionerTimelineView` conserve le praticien sélectionné;
- un intercepteur Axios strictement limité à la création est installé **synchroniquement avant l'ouverture du modal**;
- le GET `/appointments/check-conflicts` reçoit `praticien_id` si absent;
- le POST `/appointments/` reçoit le même `praticien_id` si absent;
- l'intercepteur est supprimé à la fermeture, avant toute édition et au démontage.

Édition:
- aucun `praticien_id` n'est ajouté à un PUT;
- le praticien historique reste autoritaire;
- un rendez-vous non assigné reste non assigné tant qu'une action explicite de migration/réaffectation n'existe pas.

Backend revalidé sans modification A2:
- `/appointments/check-conflicts` limite les collisions au praticien ciblé tout en incluant `praticien_id = NULL` comme bloqueur global;
- `/appointments/multi-practitioner` expose `legacy_unassigned` séparément.

## AFTER — preuve finale

Workflow canonique: `Agenda A2 AFTER Visual Certification V2`
Run: `#11` / `35093443999` — SUCCESS
HEAD produit certifié: `677414578010a7b9983e19e035a2ee5a0001603c`
Artifact id: `10445091768`
Artifact digest: `sha256:51eab42cf5522cc199b7f3cfd561518406a658427916a74e8155cc922b3739d4`

Même matrice de viewports que le BEFORE:
- 390 × 844
- 768 × 1024
- 1280 × 900

Mesures observées:
- `syncDelta = 0 px` à 390, 768 et 1280;
- document 390/390, 768/768 et 1280/1280: aucun overflow horizontal de page;
- mobile 390: conteneur interne 364 px, contenu 728 px — scroll interne présent;
- `errors = []` aux trois viewports.

Contrat navigateur création lane Dr Youssef:
- modal seedé: `2026-09-16`, `15:00`;
- durée: 30 min;
- GET conflit: `praticien_id = 2`;
- POST création: `praticien_id = 2`;
- `datetime_start = 2026-09-16T14:00:00.000Z`, soit 15:00 à Casablanca UTC+1.

## BEFORE → AFTER

BEFORE:
- cartes empilées sans repère horaire commun;
- dates mélangées;
- disponibilité relative impossible à lire;
- legacy non assigné invisible dans Multi;
- mobile non exploitable pour comparaison multi-praticiens.

AFTER:
- axe horaire partagé;
- rendez-vous alignés et dimensionnés selon leur durée;
- simultanéité immédiatement visible;
- plages cabinet fermées visibles;
- non assigné affiché comme bloqueur transversal;
- mobile conserve la matrice via scroll interne sans faire déborder la page.

Score visuel observé: **9.1/10**.

Compromis assumé: à 390 px, comparer trois praticiens nécessite un scroll horizontal interne. Ce comportement est intentionnel et préférable à une conversion en listes qui détruirait la synchronisation temporelle.

## Incidents de certification intermédiaires

Les premiers essais du gate AFTER ont échoué pour des raisons de harness, pas sur une preuve de régression produit. Le diagnostic final a identifié notamment un mock `/api/catalog/specialties` incorrectement renvoyé comme objet `{}` alors que le modal attend une liste. Le mock canonique a été corrigé en `[]` et le run final #11 est vert de bout en bout.

Seul le run #11 est la preuve AFTER canonique A2.

## Hors scope maintenu

A3: horaires individuels, jours travaillés, pauses, congés, absences.
A4: fauteuils, salles, ressources physiques.
A5: timezone cabinet explicite, soft-delete/historique, migration legacy.
