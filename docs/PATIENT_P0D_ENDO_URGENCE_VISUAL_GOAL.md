# Page Patient — P0-D Endodontie / Urgence — Goal visuel et clinique

Statut : IN_PROGRESS

## Goal

Conserver l'architecture visuelle actuelle de `ClinicalHub`, `AssistantEndo` et `AssistantExamenComplet` tout en supprimant toute apparence de diagnostic ou prescription autonome.

## Succès observable

1. Même shell, mêmes cartes, mêmes couleurs, même hiérarchie et même navigation que la baseline réelle.
2. Les questions restent des observations cliniques structurées.
3. La sortie n'est jamais intitulée « diagnostic » ni présentée comme une conclusion acquise.
4. La sortie est structurée en :
   - Observations recueillies ;
   - Hypothèses à confirmer ;
   - Points de vigilance ;
   - Options / examens à apprécier par le praticien.
5. Aucun antibiotique, prophylaxie, dose, durée ou traitement médicamenteux n'est proposé automatiquement depuis ces assistants.
6. Les red flags peuvent imposer une alerte d'évaluation urgente / orientation selon l'examen, sans diagnostiquer automatiquement une cellulite ni choisir un protocole thérapeutique.
7. La persistance du plan de traitement reste impossible sans action explicite du praticien ; l'assistant ne modifie jamais le Master Plan.
8. Responsive sans overflow aux viewports 390×844, 430×932, 768×1024 et 1280×900.

## Preuve attendue

- baseline avant : 8 captures, 4 Endodontie + 4 Examen Clinique Complet ;
- tests de contrat interdisant les libellés/régimes prescriptifs P0 ;
- captures après sur les 8 mêmes combinaisons ;
- zéro erreur runtime ;
- comparaison avant / Goal / après.

## Référence visuelle / wireframe

Le visuel de référence reste l'application actuelle. Aucun nouveau langage graphique n'est introduit.

```text
[Protocole Endodontie / Examen Clinique Complet]
[Aide structurée — validation praticien requise]

Progression existante
Question clinique existante
[option]
[option]
[option]

Après la collecte :
┌──────────────────────────────────────────┐
│ Proposition clinique à valider           │
│ Observations recueillies                 │
│ Hypothèses à confirmer                   │
│ Points de vigilance                      │
│ Options / examens à apprécier            │
│ Validation du praticien requise          │
└──────────────────────────────────────────┘
```

## Garde-fous scientifiques P0

- ADA, Antibiotics for Dental Pain and Swelling: traitement dentaire local prioritaire pour la majorité des atteintes pulpaires/péri-apicales ; antibiotiques lorsque l'état progresse vers une atteinte systémique.
- ADA/AHA, prophylaxie de l'endocardite : uniquement sous-groupe cardiovasculaire à plus haut risque et procédures dentaires concernées ; jamais « cardiopathie = prophylaxie ».
- AAE : `Guidance on the Use of Systemic Antibiotics in Endodontics` actuellement indiquée `Under Review`.
- AAE/ESE : terminologie diagnostique endodontique en cours d'actualisation ; l'assistant P0 ne doit donc pas prétendre transformer trois réponses en diagnostic définitif.

## Hors scope de ce sous-lot

- prescription médicamenteuse ;
- validation scientifique complète des autres assistants ;
- refonte graphique de ClinicalHub ;
- nouveau modèle de données clinique ;
- déploiement.
