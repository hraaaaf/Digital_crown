# Digital Crown — Référentiel dentaire Maroc — Clinical Pass 1 CORE

Date: 2026-09-16
Status: VERIFIED PARTIAL CLINICAL PASS — NO CLINICAL ACTIVATION

## Goal
Valider un premier noyau de traitements dentaires courants avec séparation stricte entre :
1. présence/disponibilité Maroc ;
2. indication dentaire ;
3. dose adulte ;
4. dose pédiatrique/pondérale ;
5. contre-indications/interactions ;
6. niveau de validation.

## Sources croisées
- SDCEP Dental Prescribing, contenu actuel aligné BNF 91 / BNFC 2025-2026, avec mise à jour de la section infections bactériennes en mai-juin 2026.
- American Dental Association, Acute Dental Pain living guideline / oral analgesics, adultes-adolescents 2024 et suivi d'évidence jusqu'en février 2026.
- American Academy of Pediatric Dentistry, Useful Medications for Oral Conditions, Reference Manual 2025-2026, révision 2025.
- Présence Maroc : fichiers AMMPS déjà audités dans `PRESCRIPTION_PHARMACOLOGY_MOROCCO_AVAILABILITY_PASS1_2026-09-16.md`.

## Résultats validés dans le CSV compagnon
Le fichier `PRESCRIPTION_PHARMACOLOGY_MOROCCO_CLINICAL_PASS1_CORE_2026-09-16.csv` contient les premières fiches structurées :
- paracetamol ;
- ibuprofen ;
- phenoxymethylpenicillin / penicillin V ;
- amoxicillin ;
- metronidazole ;
- clarithromycin ;
- clindamycin ;
- amoxicillin + clavulanic acid.

## Règles cliniques importantes confirmées
### Douleur dentaire
- Les antalgiques non opioïdes sont la première intention pour la douleur dentaire aiguë.
- L'ibuprofène seul ou associé au paracétamol est soutenu par la guideline ADA pour la douleur aiguë chez l'adulte/adolescent ; le choix dépend des contre-indications et de l'histoire médicale.
- Les opioïdes ne doivent pas devenir un chemin par défaut du référentiel.

### Infections odontogènes
- Le traitement local/drainage et le traitement de la cause restent prioritaires.
- Un antibiotique n'est pas indiqué pour une douleur inflammatoire seule, une infection localisée sans signes de diffusion/systémiques, ou un dry socket simple.
- Pour abcès dentaire lorsqu'un antibiotique est réellement indiqué : SDCEP 2026 place la phenoxymethylpenicillin comme premier choix étroit ; amoxicillin est une alternative de première ligne notamment lorsque l'adhésion au schéma est problématique ; metronidazole est une alternative en cas d'allergie à la pénicilline.
- Revue idéalement à 3 jours ; la durée habituelle est 3-5 jours et ne doit pas être prolongée inutilement si les signes systémiques ont disparu.
- Clindamycin et clarithromycin sont restreints à la deuxième ligne dans les infections sévères/non répondantes après réévaluation ; leur usage empirique routinier n'est pas justifié.
- Co-amoxiclav a été retiré en mai 2026 des recommandations SDCEP de deuxième ligne pour l'abcès dentaire ; sa disponibilité ou son dosage général ne doit donc pas être transformé en recommandation dentaire empirique.

## Conflits / divergences gérés explicitement
- Les schémas pédiatriques AAPD et SDCEP ne sont pas toujours exprimés de la même manière (mg/kg vs bandes d'âge/poids). Le dataset conserve le schéma dentaire SDCEP quand il existe et garde l'AAPD comme contrôle secondaire/pondéral.
- Le metronidazole a des doses différentes selon indication (abcès, conditions parodontales, association). Aucune dose unique globale n'est autorisée.
- Les doses générales AAPD d'amoxicilline-acide clavulanique ou de clindamycine ne valent pas automatiquement indication dentaire de première intention.

## Guardrails
- Aucun automatisme de prescription.
- Toute fiche avec interactions incomplètes garde un statut `PENDING_INTERACTION_FULL_PASS` implicite et ne peut pas être promue comme fiche finale.
- La présence AMMPS ne vaut pas recommandation clinique.
- Une guideline étrangère ne vaut pas preuve de commercialisation Maroc.
- Aucune information enfant ne doit dépasser le plafond adulte correspondant.
- Toute insuffisance rénale/hépatique, grossesse/allaitement, anticoagulant, allergie, comorbidité majeure ou polymédication doit déclencher une vérification dédiée avant proposition clinique.

## Sources principales
- https://www.sdcep.org.uk/published-guidance/drug-prescribing/
- https://www.sdcepdentalprescribing.nhs.scot/guidance/odontogenic-pain/
- https://www.sdcepdentalprescribing.nhs.scot/guidance/bacterial-infections/
- https://www.ada.org/resources/research/science/evidence-based-dental-research/pain-management-guideline
- https://www.ada.org/resources/ada-library/oral-health-topics/oral-analgesics-for-acute-dental-pain
- https://www.aapd.org/research/oral-health-policies--recommendations/useful-medications-for-oral-conditions/

## Next exact
Clinical Pass 2 : antifongiques + antiviraux + lésions/muqueuses buccales, avec double-source pour indication/dose/âge/contre-indications, puis disponibilité Maroc séparée.
