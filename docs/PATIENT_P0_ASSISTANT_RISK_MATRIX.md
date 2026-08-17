# Patient P0-D — Matrice de risque des assistants cliniques

Statut : **10/10 assistants relus au niveau moteur de règles**. La certification scientifique détaillée règle par règle reste ouverte.

| Assistant | Entrées actuelles | Sorties automatiques constatées | Risque P0 | Décision |
|---|---|---|---|---|
| Général | motif, hygiène, drapeau médical | diagnostic affirmatif, RVG, détartrage/assainissement, routage spécialité, **antibioprophylaxie Amox 2 g** | Critique | Collecte/propositions uniquement ; supprimer dose/prophylaxie automatique |
| Examen complet | urgence/routine ; douleur, signes généraux ou antécédents, hygiène, paro, dentaire, occlusion, tissus mous | diagnostics affirmatifs, hospitalisation, antibiothérapie orale/IV dosée, pulpectomie, drainage, AINS/myorelaxants, imagerie, biopsie, traitements multiples | Critique | Triage/red flags possibles ; aucune prescription, diagnostic retenu ou traitement automatique |
| Endodontie | douleur, sensibilité pulpaire, radio | diagnostics pulpaires/péri-apicaux affirmatifs, extirpation, traitement canalaire, coiffage, suivi radio | Élevé | Hypothèses structurées + propositions à valider praticien |
| Chirurgie | motif, proximité anatomique, terrain | avulsion simple/complexe, CBCT, bilan hémostase, protocole bisphosphonates + antibioprophylaxie | Critique | Aucun acte/imagerie/prophylaxie automatique |
| Pédodontie | denture, motif, Frankl | diagnostic, **MEOPA/AG**, fluor, sealants, pulpotomie/CPP, restauration, imagerie, contention/coiffage/avulsion | Critique | Frankl ne décide jamais la sédation ; toutes conduites restent propositions contextualisées |
| Parodontologie | CAL, complexité, BOP, tabac/diabète | staging/grading affirmatif, surfaçage, **amoxicilline + métronidazole**, chirurgie | Critique | Conserver collecte structurée ; recertifier staging/grading ; supprimer antibiothérapie automatique |
| Prothèse | perte tissulaire, esthétique, occlusion | diagnostic, implant/CBCT, couronnes/inlay-core, gouttière, facette/onlay | Élevé | Options thérapeutiques conditionnelles, pas plan acquis |
| Orthodontie | motif, croissance, préférence patient | diagnostic dysmorphose/malocclusion, bilan ODF, appareillage, orthognathie, contention | Élevé | Collecte + options ; diagnostic et indication ODF validés par praticien |
| ATM | symptôme, parafonction, facteur déclenchant | diagnostic DAM/disc displacement, gouttière, myorelaxants, CBCT/IRM, kiné, avis chirurgical | Critique | Red flags/orientation possibles ; diagnostic, médicament et imagerie non automatiques |
| Pathologie | aspect, durée, symptômes | diagnostic de lésion, antifongique/antiviral, exérèse/biopsie, adressage | Critique | **Préserver le red-flag persistant/induration/adénopathie**, mais traitement et diagnostic restent propositions |

## Garde-fous applicables immédiatement

1. Le callback `onComplete` ne doit pas transformer directement une sortie assistant en diagnostic retenu ou étape validée.
2. Les libellés thérapeutiques générés deviennent des **propositions à examiner** jusqu'à validation praticien.
3. Toute règle de prescription, antibioprophylaxie, sédation, imagerie ou chirurgie exige une source primaire et des préconditions explicites.
4. Les données manquantes doivent produire `insufficient_data` / proposition d'examen complémentaire, jamais une conduite par défaut.
5. Les assistants ne définissent pas un ordre scientifique global entre spécialités.
6. Les red flags utiles restent visibles, mais ne doivent pas masquer l'incertitude diagnostique.

## Sources de garde-fou déjà verrouillées

- ADA — guideline 2019 antibiotiques pour douleur/infection pulpaire et péri-apicale.
- AAPD — Use of Antibiotic Therapy for Pediatric Dental Patients, révision 2026.
- AAPD — Antibiotic Prophylaxis for Dental Patients at Risk for Infection, révision 2026.
- AAP/AAPD — Guidelines for Monitoring and Management of Pediatric Patients Before, During, and After Sedation, réaffirmées 2025.
- EFP — S3 Clinical Practice Guideline, traitement des parodontites stades I–III.

## Preuve restante pour fermer P0-D

- mapper chaque branche thérapeutique à une source primaire/version ;
- supprimer ou neutraliser toute règle non suffisamment justifiée ;
- imposer validation praticien explicite avant écriture dossier/plan/ordonnance ;
- tests positifs, négatifs et données manquantes assistant par assistant.

P0-D reste **OPEN**.
