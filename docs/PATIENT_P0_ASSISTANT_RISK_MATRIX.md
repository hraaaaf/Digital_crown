# Patient P0-D — Matrice de risque des assistants cliniques

Statut : audit en cours. Seuls les assistants effectivement relus sur la branche P0 sont classés ci-dessous.

| Assistant | Entrées actuelles | Sorties automatiques constatées | Risque P0 | Décision |
|---|---|---|---|---|
| Général | motif, hygiène, drapeau médical | diagnostic affirmatif, RVG, détartrage/assainissement, routage spécialité, **antibioprophylaxie Amox 2 g** | Critique | Fail-closed : collecte/propositions uniquement ; supprimer dose/prophylaxie automatique |
| Endodontie | douleur, sensibilité pulpaire, radio | diagnostics pulpaires/péri-apicaux affirmatifs, extirpation, traitement canalaire, coiffage, suivi radio | Élevé | Transformer en hypothèses structurées + examens/traitements à valider praticien |
| Chirurgie | motif, proximité anatomique, terrain | avulsion simple/complexe, CBCT, bilan hémostase, protocole bisphosphonates + antibioprophylaxie | Critique | Aucun acte/imagerie/prophylaxie automatique ; proposition conditionnelle et validation praticien |
| Pédodontie | denture, motif, Frankl | diagnostic, **MEOPA/AG**, fluor, sealants, pulpotomie/CPP, restauration, imagerie, contention/coiffage/avulsion | Critique | Frankl ne suffit jamais à décider sédation ; toutes conduites deviennent propositions contextualisées |
| Parodontologie | à relire | à relire | À qualifier | OPEN |
| Prothèse | à relire | à relire | À qualifier | OPEN |
| Orthodontie | à relire | à relire | À qualifier | OPEN |
| ATM | à relire | à relire | À qualifier | OPEN |
| Pathologie | à relire | à relire | À qualifier | OPEN |
| Examen complet | à relire en profondeur | orchestration multi-domaines | Critique présumé | OPEN |

## Garde-fous applicables immédiatement

1. Le callback `onComplete` ne doit pas transformer directement une sortie assistant en diagnostic retenu ou étape validée.
2. Les libellés thérapeutiques générés deviennent des **propositions à examiner** jusqu'à validation praticien.
3. Toute règle de prescription, antibioprophylaxie, sédation, imagerie ou chirurgie exige une source primaire et des préconditions explicites.
4. Les données manquantes doivent produire `insufficient_data` / proposition d'examen complémentaire, jamais une conduite par défaut.
5. Les assistants ne définissent pas un ordre scientifique global entre spécialités.

## Sources de garde-fou déjà verrouillées

- ADA — guideline 2019 antibiotiques pour douleur/infection pulpaire et péri-apicale.
- AAPD — Use of Antibiotic Therapy for Pediatric Dental Patients, révision 2026.
- AAPD — Antibiotic Prophylaxis for Dental Patients at Risk for Infection, révision 2026.
- AAP/AAPD — Guidelines for Monitoring and Management of Pediatric Patients Before, During, and After Sedation, réaffirmées 2025.
- EFP — S3 Clinical Practice Guideline, traitement des parodontites stades I–III.

P0-D reste OPEN jusqu'à relecture des 10 assistants et tests fail-closed.
