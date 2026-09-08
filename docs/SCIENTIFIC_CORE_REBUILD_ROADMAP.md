# DIGITAL CROWN — SCIENTIFIC CORE REBUILD

Status: PHASE 1 — NETTOYAGE EN COURS

## GOAL FINAL

Construire un noyau scientifique Digital Crown minimal, explicable, déterministe quand possible, versionné, sourcé et fail-closed quand le contexte clinique manque.

Principes :
- aucun moteur mort ou doublon inutile ;
- aucune donnée patient inventée ;
- aucune décision clinique automatique présentée comme vérité sans source/version ;
- le praticien reste décisionnaire ;
- une couche `REPLACE` n'est supprimée qu'après couverture/remplacement prouvé ;
- tests + CI avant intégration dans `master`.

## CLASSIFICATION

- `KEEP` : utile, actif, correct.
- `CONSOLIDATE` : utile mais redondant.
- `REPLACE` : actif mais scientifiquement insuffisant/dangereux.
- `DELETE` : mort, obsolète ou responsabilité abandonnée.

## PHASE 1 — NETTOYAGE

### LOT 1 — TreatmentPlanEngine

État : **CERTIFIÉ SUR PR**.

Preuves :
- moteur dormant supprimé ;
- imports/tests dédiés retirés ;
- contrat anti-régression ajouté ;
- CI `34222898913` : SUCCESS ;
- certifications Patient Indicators, T2 Runtime, Catalog Connected Truth, Patient P7 et Settings TemplateEngine : SUCCESS.

### LOT 2 — Prescription / safety legacy

État : **NETTOYAGE PARTIEL CERTIFIÉ**.

Appliqué :
- `allergie` générique ne devient plus automatiquement une alerte pénicilline ;
- rappel `pas de détartrage depuis 12 mois` retiré du medication-safety ;
- alertes spécifiques pénicilline et DDI conservées ;
- tests adaptés ;
- CI `34222898913` : SUCCESS.

Classement restant : `REPLACE / CONSOLIDATE`.

### LOT 3 — ClinicalRulesEngine

Cible : `backend/services/clinical_rules_engine.py`.

Classement global actuel : **REPLACE / CONSOLIDATE**.

#### Contexte pédiatrique — correction vérifiée

Constat initial corrigé après lecture complète :
- `age` et `poids` sont bien consommés par le moteur ;
- ils déterminent `is_child`, la forme pharmaceutique et `_calculate_pediatric_dosage()` ;
- `prescription_service_legacy.py` injecte encore `poids = 70` en dur ;
- le wrapper moderne `prescription_service.py` bloque actuellement le chemin legacy pour les patients `<15 ans`, mais le moteur lui-même reste dangereux s'il est appelé directement ou depuis un autre consommateur.

Conclusion :
- **ne pas supprimer `age` / `poids` comme code mort** ;
- **supprimer toute valeur synthétique** et rendre la voie pédiatrique non évaluable si le poids réel manque ;
- tracer tous les consommateurs runtime avant modification.

#### Règles actives déjà classées

1. **Clindamycine 600 mg comme alternative automatique de prophylaxie d'endocardite**
   - état : `REPLACE` ;
   - AAPD 2026 / recommandations dérivées AHA : clindamycine non recommandée pour prophylaxie d'une procédure dentaire.

2. **Grossesse : tablier plombé + collerette déclarés OBLIGATOIRES**
   - état : `REPLACE / CONFLIT DE SOURCES` ;
   - ADA 2024 : shielding systématique non recommandé, y compris grossesse ;
   - une page ACOG plus ancienne mentionne encore le shielding ;
   - futur moteur : source/version explicites + réglementation locale.

3. **Saccharomyces boulardii automatiquement ajouté après amoxicilline/Augmentin**
   - état : `REPLACE / DELETE AUTO-RECOMMENDATION` ;
   - ADA Antibiotic Stewardship rapporte des données insuffisantes pour recommander les probiotiques en prévention de C. difficile.

4. **Implant => prophylaxie antibiotique automatique**
   - état : `REPLACE / NON SOURCÉ` ;
   - guideline ADA dédiée aux implants sains encore en programme de guideline vivante, publication annoncée pour hiver 2026 ;
   - ne pas présenter une prophylaxie universelle comme vérité établie.

5. **Grossesse => AINS interdits uniformément**
   - état : `REPLACE` ;
   - FDA : recommandation dépend notamment de l'âge gestationnel, avec seuils 20/30 semaines et exceptions ;
   - futur moteur : âge gestationnel requis.

6. **Mapping acte/diagnostic => médicaments**
   - état : `REPLACE / REASONING REQUIRED` ;
   - ADA douleur/infection : traitement dentaire définitif prioritaire pour la majorité des pathologies pulpaires/périapicales, antibiotiques selon contexte notamment systémique ;
   - futur moteur : diagnostic + symptômes + signes systémiques + traitement étiologique, pas mot-clé => molécule.

#### Consommateurs déjà vérifiés

- `prescription_service_legacy.py` appelle directement `clinical_rules.analyze_case()` ;
- `prescription_service.py` utilise aussi `clinical_rules` pour normaliser le contexte d'acte ;
- `prescription_agentic_service.py` passe par `prescription_service` et bénéficie du garde-fou moderne de contexte.

Next :
1. tracer les autres consommateurs éventuels ;
2. identifier les garde-fous uniques du moteur ;
3. neutraliser le poids synthétique pédiatrique avec fail-closed ;
4. sortir les règles obsolètes/trop absolues du runtime uniquement avec tests et remplacement prouvé.

### LOT 4 — Clinical coherence

Cible : `backend/services/clinical_coherence.py`.

État : `REPLACE / CONSOLIDATE`, actif runtime.

Next : inventorier chaque règle et ses recouvrements avec prescription/safety.

### LOT 5 — Imagerie panoramique

À auditer : `panoramic_*`, `vision_*`, `sota_*`, report/generators associés.

Succès : un seul pipeline produit identifié, aucun wrapper dormant, aucune détection transformée automatiquement en diagnostic/traitement.

### LOT 6 — Céphalométrie

À auditer après safety/panoramique : upload/process, landmarks, calibration, mesures, refine manuel, validator, export/PDF.

## PHASE 2 — CONSOLIDATION

Après purge :
- un moteur canonique par responsabilité ;
- contrats d'entrée/sortie normalisés ;
- séparation patient / observation / diagnostic / safety / recommandation ;
- provenance, version et niveau de confiance obligatoires.

## PHASE 3 — REBUILD

Construire uniquement ce qui manque après consolidation :
- Patient Clinical Context ;
- Pharmacology Engine ;
- Dental Clinical Reasoning Engine ;
- prescription intelligente ;
- cohérence diagnostic ↔ actes ↔ ordonnance ;
- imagerie et céphalo sur contrats scientifiques propres.

## PHASE 4 — CERTIFICATION

Pour chaque moteur : unit tests, golden cases, tests négatifs/fail-closed, runtime, non-régression et revue humaine des règles cliniquement sensibles.

## CLOSEOUT

Canonique cohérent → PR → CI → merge → post-merge. Aucun déploiement Vercel sans autorisation explicite.

## REPÈRES VÉRIFIÉS

Repo : `hraaaaf/Digital_crown`

Branche : `refactor/scientific-core-purge`

PR : `#371` draft

Dernier HEAD produit certifié : `f4a455292d85eae142c9d023c20555929ab123d1`

CI certifiée : `34222898913` — SUCCESS.

## NEXT EXACT

Auditer les consommateurs et garde-fous uniques de `clinical_rules_engine.py`, puis neutraliser la voie pédiatrique à poids synthétique avant toute autre reconstruction scientifique.
