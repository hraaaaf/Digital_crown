# Page Patient — P1 Architecture générale

## Chantier
P1 — Architecture générale Page Patient

## Goal
Réduire la densité perçue de la fiche Patient et faire apparaître immédiatement l'identité, les alertes utiles et les actions fréquentes, sans redesign gratuit ni perte fonctionnelle.

## Baseline validée
Source visuelle : artefact P0-I AFTER, run `32186499282`, artifact `9342853792`.
Viewports :
- `nba-after-390x844.png`
- `nba-after-430x932.png`
- `nba-after-768x1024.png`
- `nba-after-1280x900.png`

Constats vérifiés dans `PatientDetailsInner.tsx` :
- header large avec identité, coordonnées, badges et actions dispersées ;
- 6 onglets principaux : `Séances & Suivi`, `Examen Clinique`, `Radiologie (IA)`, `Documents A5`, `Archives & Historique`, `Finances` ;
- labels techniques exposés à l'utilisateur ;
- Archives et Documents sont deux surfaces séparées alors qu'elles appartiennent au même domaine documentaire ;
- la navigation principale dépasse la largeur utile sur petits viewports.

## Cible fonctionnelle
Navigation principale en 5 espaces :
1. Vue d’ensemble
2. Clinique
3. Imagerie
4. Documents
5. Finances

Mapping :
- `tracking` → Vue d’ensemble
- `clinical` → Clinique
- `radiology` → Imagerie
- `admin` + `archives` → Documents
- `finances` → Finances

## Wireframe cible

```text
┌──────────────────────────────────────────────────────────────────────┐
│ ←  NOM Prénom   Dossier · âge/date naissance · assurance · alertes │
│                  [RDV] [Séance/Examen] [Document] [Encaisser]       │
├──────────────────────────────────────────────────────────────────────┤
│ Vue d’ensemble | Clinique | Imagerie | Documents | Finances        │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│                    CONTENU DE L’ESPACE ACTIF                        │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘

Documents :
┌──────────────────────────────────────────────────────────────────────┐
│ [Créer] [Historique]                                                 │
├──────────────────────────────────────────────────────────────────────┤
│ Document Studio OU bibliothèque des documents existants             │
└──────────────────────────────────────────────────────────────────────┘
```

## Règles UI
- conserver couleurs, tokens, typographie et composants existants ;
- compacter le header sans supprimer l'identité essentielle ;
- les coordonnées secondaires ne doivent plus dicter la hauteur du header ;
- actions rapides explicites : RDV, Séance/Examen, Document, Encaisser ;
- `Radiologie (IA)` devient `Imagerie` ;
- `Documents A5` devient `Documents` ;
- `Archives & Historique` disparaît de la navigation principale et devient `Historique` dans Documents ;
- aucune logique clinique ou financière n'est modifiée par P1.

## Succès observable
- 5 onglets principaux maximum ;
- aucune perte d'accès à PatientJourney, ClinicalHub, Cephalo/Panoramic, DocumentHub, PatientDocuments ou PatientFinances ;
- création et historique des documents accessibles depuis le même espace ;
- header plus compact sur desktop et mobile ;
- aucune régression permission `clinical` ;
- aucun overflow horizontal aux viewports baseline ;
- captures AFTER sur 390 / 430 / 768 / 1280 comparées à la baseline.

## Preuve requise
- tests frontend ciblés ;
- build frontend ;
- capture AFTER mêmes viewports ;
- inspection visuelle avant / wireframe / après ;
- score visuel argumenté ;
- CI exacte sur HEAD final du lot.
