# Patient P0-C — ClinicalHub Truth Wireframe

## Référence visuelle

Baseline authentifiée issue de `T2 Runtime Browser Certification` run #73, HEAD `5da55b1cbd1c7bc35e4221cc21c5ad7a2c819988`.

- 24 captures : 6 onglets × 390 / 430 / 768 / 1280.
- 24 routes Patient rendues, 0 redirection, 0 erreur runtime.
- Artifact : `t2-browser-evidence/patient-baseline/`.
- Score baseline Clinique : **4/10 mobile**, **7/10 desktop**.
- Anomalie visible principale : à 390 px, le header, la barre d'onglets et ClinicalHub sont coupés horizontalement malgré l'absence d'overflow document global.

## Goal P0-C

Corriger uniquement la vérité clinique sans refaire le design : un dossier vide doit rester vide, une sauvegarde échouée doit rester une erreur, et aucune donnée clinique locale ne doit être présentée comme persistée.

## Succès

1. Aucun Master Plan fictif quand le backend renvoie zéro étape.
2. `localStorage` n'est jamais la source autoritative du Master Plan, du diagnostic ou de l'odontogramme.
3. Une mutation du plan n'est affichée comme sauvegardée qu'après succès backend.
4. En cas d'échec, le dernier état backend connu reste affiché et un message d'erreur est visible.
5. Structure visuelle actuelle conservée pendant P0 ; le redesign responsive appartient à P1/P3.

## Wireframe cible, basé sur l'écran existant

```text
┌──────────────────────────────────────────────────────────────┐
│ [icône actuelle] Cerveau Clinique Central                  │
│                  libellés actuels conservés pendant P0      │
├──────────────────────────────────────────────────────────────┤
│ Radar de vigilance actuel                                   │
│                                                              │
│ Dossier clinique                     [Assistants][Dentaire] │
│                                                              │
│  Si backend vide :                                            │
│  ┌────────────────────────────────────────────────────────┐  │
│  │ Aucun plan de traitement enregistré                   │  │
│  │ Le dossier restera vide jusqu'à validation praticien. │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                              │
│  Assistants/protocoles actuels                               │
│                                                              │
├──────────────────────────────────────────────────────────────┤
│ MASTER PLAN DE TRAITEMENT                                    │
│                                                              │
│  0 étape backend → 0 %                                       │
│  Étapes backend → affichage inchangé                         │
│                                                              │
│  Mutation :                                                   │
│  clic → requête backend → succès → état affiché + toast      │
│                        ↘ échec → état précédent + erreur     │
└──────────────────────────────────────────────────────────────┘
```

## Hors scope P0-C visuel

- renommage `Cerveau Clinique Central` / `Ghost Orchestrator` ;
- refonte des assistants ;
- changement des 6 onglets vers l'architecture 5 espaces ;
- correction responsive globale ;
- suppression du PatientScoreBadge.

Ces sujets restent dans P0-D/P0-H/P1/P3 et devront utiliser cette baseline comme capture avant.
