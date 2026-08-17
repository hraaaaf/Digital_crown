# Page Patient — P0-D Endodontie / Urgence — matrice de sécurité

Statut : IN_PROGRESS

Cette matrice transforme l'audit scientifique en règles d'implémentation testables. Elle ne constitue pas une prescription clinique et ne remplace pas le jugement du praticien.

| Situation actuellement codée | Risque P0 | Comportement autorisé après P0 |
|---|---|---|
| 3 réponses Endo → « Pulpite irréversible », « Nécrose pulpaire », etc. | diagnostic affirmatif à partir d'un jeu de données insuffisant | « Hypothèse endodontique à confirmer » + observations utilisées + examens manquants |
| Pulpite présumée → extirpation / traitement canalaire automatique | traitement autonome | options à apprécier selon examen clinique, diagnostic praticien et restaurabilité |
| Lésion radioclaire → suivi à 6 mois automatique | calendrier thérapeutique universel | besoin de suivi à déterminer par le praticien selon diagnostic, traitement et évolution |
| Tuméfaction pulpaire → Amoxicilline 2 g/j × 5 j | antibiotique automatique malgré possibilité d'infection localisée | aucune proposition antibiotique automatique ; signaler signes systémiques / diffusion et nécessité d'évaluation clinique |
| Fièvre → antibiotique systématique avec molécule/dose/durée | prescription sans terrain, allergies, poids, interactions ni diagnostic complet | alerte « atteinte systémique possible — évaluation urgente et décision thérapeutique du praticien » |
| Cellulite/trismus → diagnostic « Cellulite cervico-faciale » + IV amox/métronidazole | diagnostic et protocole hospitalier automatisés | red flag majeur : évaluation urgente, voies aériennes/extension/état général à apprécier, orientation urgente selon examen ; aucune ordonnance automatique |
| « Cardiopathie / prothèse valvulaire » → Amox 2 g 1 h avant | indication de prophylaxie beaucoup trop large | demander le type exact de cardiopathie et le geste prévu ; indiquer seulement que l'éligibilité doit être vérifiée selon critères AHA/ADA actuels |
| Bruxisme → gouttière + IRM éventuelle | traitement/examen généré sans diagnostic différentiel | observations + hypothèses + examens/options à apprécier |
| Lésion muqueuse suspecte → biopsie automatique | acte invasif présenté comme conséquence déterministe | red flag + évaluation prioritaire / orientation à apprécier par le praticien |

## Règles d'affichage

- Interdit : `Diagnostic`, `Génération du diagnostic`, `Urgence absolue` comme conclusion automatisée, ou tout libellé laissant croire que l'application a validé le diagnostic.
- Interdit dans la sortie automatique P0 : nom d'antibiotique, dose, durée, prophylaxie médicamenteuse.
- Autorisé : observations factuelles saisies, hypothèses explicitement qualifiées, red flags, données manquantes, options/examens à apprécier.
- Toute sortie est étiquetée `Proposition clinique à valider` / `Validation praticien requise`.
- Aucun changement du Master Plan par un assistant.

## Sources primaires de cadrage

- American Dental Association — Evidence-Based Clinical Practice Guideline on Antibiotic Use for Urgent Management of Pulpal/Periapical Dental Pain and Intraoral Swelling.
- American Dental Association / American Heart Association — Antibiotic Prophylaxis Prior to Dental Procedures / prevention of infective endocarditis.
- American Association of Endodontists — Guidelines & Position Statements : systemic antibiotic guidance actuellement marquée `Under Review`.
- AAE / European Society of Endodontology — initiative actuelle d'actualisation de la terminologie diagnostique endodontique.

## Critère de fermeture de ce sous-lot

La matrice n'est CLOSED que lorsque les assistants Endo + Examen complet/urgence :
1. respectent ces règles dans le code ;
2. ont des tests ciblés ;
3. passent la CI ;
4. ont une preuve visuelle avant/après sur les quatre viewports du Goal ;
5. n'introduisent aucune régression runtime.
