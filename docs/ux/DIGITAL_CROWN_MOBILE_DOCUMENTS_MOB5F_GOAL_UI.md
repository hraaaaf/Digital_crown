# DIGITAL CROWN — MOB-5F — QUICK DOCUMENT STUDIO — GOAL UI

Status: GOAL UI LOCKED — BEFORE PENDING — IMPLEMENTATION NOT STARTED

## Goal UI

Depuis le patient déjà sélectionné, lancer un document courant sans quitter le cockpit, avec une interaction mobile courte, sûre et cohérente avec le reste de Digital Crown.

Cible produit: document courant en idéalement <30 s lorsque les données nécessaires sont déjà connues.

## Références retenues

### Référence interne

- `MobilePatientsView`: cartes compactes, actions cliniques rapides, patient déjà contextualisé.
- pattern MOB-5H: détail / action complexe dans une sheet plein écran plutôt qu'une forêt de boutons inline.
- moteur desktop Document Studio: source de vérité fonctionnelle, pas référence de layout mobile.

### Référence externe

- CareStack: actions documentaires en quick links depuis le contexte patient.
- Open Dental / ODTouch: création clinique/prescription directement depuis le patient sélectionné.

## Structure cible

### État 1 — Cockpit patient

Dans `Actions cliniques rapides`, ajouter une action principale:

`Créer un document`

Elle ne remplace aucune action existante.

### État 2 — Choix du type

Sheet mobile avec cartes courtes, filtrées par permissions:
- Ordonnance;
- Certificat;
- Document libre;
- Devis.

Chaque type affiche une phrase d'usage, pas une documentation administrative.

### État 3 — Éditeur rapide

Principes:
- patient verrouillé et toujours visible;
- alerte médicale immédiatement visible pour Ordonnance;
- champs strictement nécessaires;
- presets/templates quand ils existent déjà;
- CTA primaire unique;
- aucune donnée financière ou clinique inutile au type choisi.

### État 4 — Preview / confirmation

Avant archivage:
- résumé du type;
- patient;
- date;
- contenu essentiel;
- warnings déterministes éventuels;
- action `Archiver le document` explicite.

Le PDF canonique est produit par le moteur existant. Le mobile ne fabrique pas son propre format documentaire.

### État 5 — Succès

Retour compact:
- document archivé;
- accès au document créé;
- retour patient.

Pas de navigation perdue ni de brouillon fantôme.

## Comportement responsive

Viewports de certification:
- 390x844;
- 430x932;
- 768x1024.

Règles:
- aucun overflow horizontal;
- zones tactiles >= 44 px lorsque possible;
- CTA final visible sans ambiguïté;
- sheet scrollable, header patient stable;
- pas de tableau desktop compressé sur mobile.

## Sécurité / vérité UI

L'UI ne présente jamais une capacité que le backend refuse réellement.

Permissions attendues par type:
- Ordonnance → `prescriptions`;
- Certificat → `patients`;
- Devis → `accounting`;
- Document libre → `clinical`.

Le backend demeure autoritaire et revérifie patient + permission lors de la génération.

## BEFORE attendu

Baseline produit exacte: `e30b858f58686f5f7bef19ca93f1c5dae42929c9`.

Constat à prouver visuellement et par report:
- patient cockpit fonctionnel;
- quatre actions cliniques existantes;
- aucune entrée `Créer un document`;
- 0 overflow / runtime error sur 390/430/768.

## AFTER attendu

Même patient, mêmes viewports:
- `Créer un document` visible et priorisé;
- choix des types lisible;
- au moins un flow complet représentatif jusqu'à preview/confirmation dans la capture/certification;
- aucune régression des actions existantes;
- 0 overflow / runtime error;
- score visuel >= 9/10 visé, sans le déclarer atteint avant inspection.
