# Patient P0-H — Goal visuel neutralité clinique

## Baseline

Référence visuelle existante : matrice Patient baseline 24/24 capturée avant les changements P0 sur la branche `agent/patient-page-p0-truth-safety` au SHA `5da55b1cbd1c7bc35e4221cc21c5ad7a2c819988`.

Dans `PatientDetailsInner`, le header clinique actuel affiche, sur la même ligne que le nom du patient :

`Nom patient | PatientScoreBadge | Assurance | Dossier actif | Modifier dossier`

Le `PatientScoreBadge` représente une classification commerciale/comportementale (Platinum/Gold/Silver/Bronze) calculée notamment à partir de rendez-vous et paiements. Cette information ne doit pas orienter la lecture clinique du dossier.

## Goal

Retirer uniquement le score/grade commercial du header de la fiche Patient, sans redesign du header et sans déplacer d'autres informations.

## Succès observable

Le header devient :

`Nom patient | Assurance | Dossier actif | Modifier dossier`

Critères :

1. aucune mention Platinum/Gold/Silver/Bronze n'apparaît dans le header clinique ;
2. le nom, l'assurance, le statut dossier et le bouton Modifier conservent leur positionnement relatif ;
3. aucun nouveau badge, KPI ou indicateur n'est ajouté pour remplacer le score ;
4. le composant `PatientScoreBadge` peut rester disponible hors surface clinique tant qu'un usage administratif futur est explicitement décidé ;
5. aucun changement backend du moteur de scoring dans ce lot ; P0-H porte sur la neutralité de la lecture clinique.

## Wireframe de référence

Avant :

```text
┌──────────────────────────────────────────────────────────────────────┐
│ ←  NOM PATIENT  [Score patient] [Assurance] [Dossier actif] [Modifier]
│    N° dossier · naissance · téléphone · email · adresse              │
└──────────────────────────────────────────────────────────────────────┘
```

Cible :

```text
┌──────────────────────────────────────────────────────────────────────┐
│ ←  NOM PATIENT  [Assurance] [Dossier actif] [Modifier]               │
│    N° dossier · naissance · téléphone · email · adresse              │
└──────────────────────────────────────────────────────────────────────┘
```

Le changement est volontairement minimal : suppression d'un signal non clinique, aucune invention visuelle.

## Implémentation

- Correctif minimal appliqué au commit `5db676f1255a307fd582b39a521f9294f2621a2a`.
- `PatientScoreBadge` n'est plus importé ni rendu dans `PatientDetailsInner`.
- `show_patient_badges` n'est plus lu par la fiche Patient.
- Aucun autre élément du header n'a été déplacé volontairement par ce correctif.

Statut : **implémenté, non certifié visuellement** tant que la CI et les captures après sur HEAD exact ne sont pas acquises.

## Preuve après implémentation requise

- build/typecheck ou CI frontend sur HEAD exact ;
- capture après sur les mêmes viewports de la baseline Patient ;
- comparaison baseline / cible / après ;
- score visuel argumenté seulement après inspection des captures.
