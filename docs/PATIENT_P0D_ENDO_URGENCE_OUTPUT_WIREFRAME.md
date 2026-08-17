# Patient P0-D — Endodontie / Urgence fail-closed — Goal visuel

## Chantier

Page Patient → P0-D Assistants cliniques fail-closed → sous-lot Endodontie + Examen clinique complet / Urgence.

## Référence avant

La référence visuelle est le runtime Patient existant, sans redesign :

- wizards Endodontie et Examen Clinique Complet déjà présents dans `ClinicalHub` ;
- même carte protocole, mêmes questions et mêmes boutons ;
- même carte indigo `Proposition clinique à valider` dans `ClinicalHub` après completion ;
- matrice 390 / 430 / 768 / 1280 ;
- baseline des questions P0-D déjà certifiée ;
- baseline dédiée des sorties générées doit être GREEN avant implémentation.

## Goal

Conserver exactement la logique visuelle actuelle tout en retirant l'autorité clinique implicite : les réponses servent à structurer des observations, jamais à établir automatiquement un diagnostic, prescrire un médicament, imposer une imagerie, une chirurgie ou un traitement.

## Succès observable

1. Les questions et le flow visuel restent reconnaissables et dans le même ordre.
2. L'état de calcul Endodontie ne dit plus `Génération du Diagnostic Endodontique` mais une formulation de synthèse non diagnostique.
3. L'état de calcul Urgence ne dit plus `Génération du diagnostic + plan de traitement`.
4. La carte finale reste la carte existante `Proposition clinique à valider`.
5. La carte finale contient uniquement des observations issues des réponses, les limites/données à compléter, les éventuels signaux de vigilance, et un rappel de validation praticien.
6. Aucun texte généré ne contient automatiquement molécule, dose, durée, chirurgie, hospitalisation, imagerie ou traitement prescrit.
7. Aucun step généré par ces deux protocoles n'est ajouté au Master Plan.
8. 16 captures après sur les mêmes 4 viewports et les mêmes états `calculating` / `result`.

## Mockup cible basé sur l'application existante

```text
┌──────────────────────────────────────────────────────────┐
│ Protocole Endodontie / Examen Clinique Complet          │
│                                                          │
│ [questions existantes, ordre et composants conservés]   │
│                                                          │
│              Synthèse des observations...               │
└──────────────────────────────────────────────────────────┘

Puis, dans ClinicalHub :

┌──────────────────────────────────────────────────────────┐
│ ✦ Proposition clinique à valider — Endodontie           │
│                                                          │
│ Observations recueillies : …                             │
│ Données à confirmer / compléter : …                      │
│ Vigilance : … (uniquement si réponses red-flag)          │
│                                                          │
│ Diagnostic et conduite thérapeutique : décision du       │
│ praticien après examen clinique et examens nécessaires.  │
│                                           [supprimer]     │
└──────────────────────────────────────────────────────────┘
```

## Hors scope de ce sous-lot

- redesign du ClinicalHub ;
- correction responsive globale P1/P3 ;
- modification des autres assistants ;
- génération d'un plan thérapeutique automatique ;
- ajout de nouvelles recommandations médicales non présentes dans les données collectées.

## Preuve attendue

- baseline sorties `avant` : 16 PNG + `summary.json` + `evidence.json`, fail-closed ;
- tests source/contrat interdisant les anciennes sorties autoritatives ciblées ;
- build frontend ;
- captures `après` : 16 PNG mêmes viewports/états ;
- inspection visuelle avant / mockup / après ;
- CI et T2 exact-head avant fermeture.
