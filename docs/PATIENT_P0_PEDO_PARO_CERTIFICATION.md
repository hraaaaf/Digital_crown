# Page Patient P0-D — Certification Pédodontie & Parodontologie

Statut : **OPEN — garde-fous scientifiques verrouillés, implémentation non réalisée**.

## Goal

Empêcher les assistants Pédodontie et Parodontologie de convertir un QCM court en décision thérapeutique autoritative.

## Succès

- aucun score comportemental seul ne déclenche sédation ou anesthésie générale ;
- aucune antibiothérapie systémique par règle générique de stade/risque parodontal ;
- les observations restent distinctes d'une décision validée par le praticien ;
- toute décision de sédation ou d'antibiothérapie exige les préconditions cliniques nécessaires et une validation explicite.

## Pédodontie — décision verrouillée

### Comportement actuel à supprimer

`Frankl 1/2 -> MEOPA ou AG` ne peut pas être une décision automatique.

### Contrat cible

Un score/comportement peut seulement déclencher une **évaluation de prise en charge comportementale**. Toute sédation nécessite notamment une évaluation pré-sédation médicale, un examen ciblé des voies aériennes, l'analyse des risques/interactions, du personnel formé au rescue, le monitoring et l'équipement adaptés, ainsi qu'une récupération documentée avant sortie.

L'anesthésie générale ou la sédation profonde nécessite en plus une indication documentée, un consentement, une évaluation préopératoire et des professionnels/facilités répondant aux exigences applicables.

Sources primaires :
- AAPD/AAP, *Guidelines for Monitoring and Management of Pediatric Patients Before, During, and After Sedation for Diagnostic and Therapeutic Procedures*, reaffirmed 2025.
- AAPD, *Use of Anesthesia Providers in the Administration of Office-Based Deep Sedation/General Anesthesia to the Pediatric Dental Patient*, latest revision 2023, Reference Manual 2026-2027.

## Parodontologie — décision verrouillée

### Comportement actuel à supprimer

Une règle de type `Stage III + risque -> Amoxicilline + Métronidazole` ne peut pas être universelle ni automatique.

### Contrat cible

La thérapeutique parodontale suit une approche progressive et individualisée. L'instrumentation sous-gingivale est le socle de la deuxième étape. L'EFP indique que l'utilisation routinière d'antibiotiques systémiques en adjuvant **n'est pas recommandée**, en raison du rapport bénéfice/risque, des effets indésirables et de l'antibiorésistance. Leur usage peut seulement être envisagé dans certaines catégories particulières après évaluation clinique, jamais sur un simple couple stade/score de risque.

Source primaire :
- EFP S3 Level Clinical Practice Guideline, *Treatment of stage I-III periodontitis*, Journal of Clinical Periodontology 2020, guideline EFP toujours publiée comme référence clinique Stage I-III.

## Règle commune P0-D

```text
observations structurées
-> données manquantes / red flags
-> options ou besoin d'évaluation
-> validation explicite du praticien
-> seulement ensuite décision dossier / traitement
```

Aucune sortie de ces assistants ne devient automatiquement diagnostic, prescription, acte, imagerie ou plan de traitement canonique.
