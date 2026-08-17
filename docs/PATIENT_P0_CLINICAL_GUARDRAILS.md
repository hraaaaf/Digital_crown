# Patient P0-D — Garde-fous cliniques canoniques

Statut : garde-fous de sécurité avant recertification assistant par assistant.

## Goal

Empêcher qu'un assistant déterministe transforme quelques réponses de questionnaire en diagnostic, prescription, sédation, imagerie ou acte thérapeutique présenté comme acquis sans validation explicite du praticien.

## Règle générale

Tout résultat automatisé doit rester l'un des états suivants jusqu'à validation praticien :

- observation structurée ;
- hypothèse diagnostique ;
- proposition d'examen complémentaire ;
- proposition thérapeutique ;
- alerte / red flag.

Aucun de ces états ne devient automatiquement diagnostic retenu, ordonnance, acte réalisé ou plan validé.

## G1 — Antibiothérapie endodontique / douleur pulpaire

**Source primaire :** American Dental Association, Evidence-Based Clinical Practice Guideline on Antibiotic Use for Urgent Management of Pulpal- and Periapical-Related Dental Pain and Intraoral Swelling, 2019.

Contrat Digital Crown :

- pas d'antibiotique automatique pour une douleur pulpaire/péri-apicale localisée ;
- priorité au traitement dentaire définitif lorsque indiqué ;
- toute proposition antibiotique doit exposer l'indication observée et rester soumise à validation praticien ;
- l'implication systémique, le terrain immunitaire et les autres facteurs pertinents doivent être évalués avant toute proposition.

## G2 — Antibiothérapie pédiatrique

**Source primaire :** American Academy of Pediatric Dentistry, Use of Antibiotic Therapy for Pediatric Dental Patients, dernière révision 2026.

Contrat Digital Crown :

- antibiothérapie uniquement selon indication clinique compatible ;
- aucune prescription calculée à partir d'un QCM réduit sans poids, âge, terrain, allergie, diagnostic et indication vérifiés ;
- les situations virales ne doivent pas générer d'antibiotique ;
- toute proposition reste à valider par le praticien.

## G3 — Antibioprophylaxie

**Source primaire :** American Academy of Pediatric Dentistry, Antibiotic Prophylaxis for Dental Patients at Risk for Infection, dernière révision 2026.

Contrat Digital Crown :

- aucune antibioprophylaxie automatique sur un simple drapeau générique de risque ;
- indication conditionnée au terrain à risque et au caractère invasif de l'acte ;
- cas complexes ou non couverts : signaler le besoin de décision/avis médical plutôt qu'inventer une conduite.

## G4 — Sédation pédiatrique / MEOPA / anesthésie générale

**Source primaire :** American Academy of Pediatrics + American Academy of Pediatric Dentistry, Guidelines for Monitoring and Management of Pediatric Patients Before, During, and After Sedation for Diagnostic and Therapeutic Procedures, réaffirmées 2025.

Contrat Digital Crown :

- aucune sédation ne peut être recommandée comme décision automatique à partir du comportement seul ;
- évaluation pré-sédation, terrain, voies aériennes, médicaments/interactions, jeûne selon contexte, compétences de sauvetage, monitoring et récupération sont des prérequis de sécurité ;
- Digital Crown peut signaler qu'une évaluation de sédation est à considérer, jamais déclarer seul MEOPA/AG comme conduite acquise.

## G5 — Parodontologie

**Source primaire :** European Federation of Periodontology, S3 Clinical Practice Guideline for treatment of stage I–III periodontitis, 2020, et ressources cliniques EFP associées.

Contrat Digital Crown :

- diagnostic et planification fondés sur l'évaluation parodontale et la classification appropriée ;
- stratégie thérapeutique séquentielle/stepwise selon le diagnostic et les objectifs cliniques ;
- aucun ordre universel inter-spécialités ne doit être présenté comme règle scientifique ;
- toute proposition de traitement reste dépendante des données patient effectivement présentes.

## G6 — Ordre des spécialités

Le tableau `scientificOrder` actuel de ClinicalHub n'est pas une règle scientifique générale certifiée.

Contrat Digital Crown :

- supprimer tout ordre universel codé en dur présenté comme scientifique ;
- l'ordre du plan doit découler des urgences, risques, dépendances thérapeutiques, diagnostic retenu et décisions du praticien ;
- en l'absence de preuve patient suffisante, conserver l'ordre saisi/validé par le praticien.

## Preuve requise avant fermeture P0-D

Pour chacun des assistants Général, Examen complet, Paro, Endo, Chirurgie, Prothèse, Pédodontie, Ortho, ATM et Pathologie :

1. inventaire des règles déclenchantes ;
2. classification observation / hypothèse / proposition / red flag ;
3. source primaire et version pour chaque règle thérapeutique ;
4. suppression ou fail-closed de toute règle non suffisamment justifiée ;
5. validation praticien explicite avant écriture dans le dossier/plan/ordonnance ;
6. tests déterministes couvrant cas positif, négatif et données manquantes.

P0-D reste OPEN tant que cette matrice n'est pas complétée assistant par assistant.
