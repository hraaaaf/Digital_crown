# Patient P0-H — Goal visuel neutralité clinique

## Baseline

Référence obligatoire : le header réel de la fiche Patient sur la branche `agent/patient-page-p0-rescue`, capturé avant toute modification sur 390×844, 430×932, 768×1024 et 1280×900.

Le header actuel peut afficher, lorsque le réglage existant `show_patient_badges` est activé :

`Nom patient | PatientScoreBadge | Assurance | Dossier actif | Modifier dossier`

Le `PatientScoreBadge` classe le patient en Platinum / Gold / Silver / Bronze avec des notions de VIP, fiabilité ou vigilance. Ce signal commercial/comportemental ne doit pas orienter la lecture clinique du dossier.

## Goal

Retirer uniquement le score/grade commercial du header clinique de la fiche Patient, sans redesign du header et sans déplacer volontairement les autres informations.

## Succès observable

Cible :

`Nom patient | Assurance | Dossier actif | Modifier dossier`

Critères :

1. aucune mention ou icône de grade Platinum/Gold/Silver/Bronze dans le header clinique ;
2. nom, assurance, statut dossier et bouton Modifier conservent leur hiérarchie et leur positionnement relatif ;
3. aucun nouveau badge, KPI ou indicateur ne remplace le score ;
4. aucun changement backend du moteur de scoring dans ce lot ;
5. aucune régression d'overflow horizontal sur 390/430/768/1280 ;
6. comparaison avant / référence / après obligatoire avant certification.

## Référence visuelle

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

Aucune invention visuelle : la cible est l'application actuelle avec le seul signal non clinique retiré.
