# DIGITAL CROWN — SCIENTIFIC CORE REBUILD

Status: PHASE 1 — NETTOYAGE EN COURS

Fichier canonique du chantier de nettoyage, consolidation et reconstruction du noyau scientifique.

## GOAL FINAL

Obtenir un noyau scientifique Digital Crown :

- minimal : aucun moteur mort, doublon ou wrapper sans utilité ;
- explicite : une seule responsabilité claire par moteur ;
- sûr : aucune décision clinique automatique non validée par le praticien ;
- déterministe et testable quand cela est possible ;
- traçable : chaque sortie clinique importante doit avoir une source, une règle et un niveau de confiance compréhensibles ;
- maintenable : les couches transitoires sont retirées après remplacement prouvé ;
- certifié par tests avant intégration dans `master`.

Le but n'est pas de conserver le plus de moteurs possible. Le but est de conserver le moins de moteurs nécessaires, mais de très bonne qualité.

## RÈGLE DE SUPPRESSION

Aucun fichier scientifique n'est supprimé sur intuition seule.

Chaque candidat est classé :

1. `KEEP` — responsabilité utile, active et correcte ;
2. `CONSOLIDATE` — utile mais redondant avec une meilleure couche ;
3. `REPLACE` — actif mais scientifiquement insuffisant ou dangereux ;
4. `DELETE` — mort, non consommé, doublon intégral ou obsolète sans responsabilité nécessaire.

Pour `DELETE`, la preuve minimale est :

- références runtime vérifiées ;
- routes/services/scripts/tests vérifiés ;
- comportement équivalent ou responsabilité explicitement abandonnée ;
- tests/CI après suppression.

Une couche `REPLACE` n'est supprimée qu'après remplacement et validation du comportement requis.

## PHASE 1 — NETTOYAGE SCIENTIFIQUE

### 1.1 Inventaire de dépendances

Goal: établir la carte réelle des moteurs scientifiques actifs.

Succès:
- chaque moteur scientifique a ses consommateurs runtime connus ;
- les tests seuls sont distingués des appels produit ;
- les wrappers/imports inutilisés sont identifiés.

Preuve:
- code search + inspection runtime + CI/checks repo.

État: EN COURS.

### 1.2 Lot 1 — supprimer le vieux TreatmentPlanEngine

Cible : `backend/services/treatment_plan_engine.py`.

Constat vérifié :
- imports présents dans `backend/routers/ia.py` et `backend/services/elite_manager.py`, sans appel runtime du moteur ;
- `EliteManager.get_treatment_plan()` est déjà fail-closed et refuse la génération automatique d'un plan clinique ;
- les usages effectifs restants du vieux moteur étaient ses propres tests ;
- le moteur proposait des actes et coûts à partir de labels automatiques, responsabilité qui ne doit plus exister sous cette forme.

Application :
- moteur supprimé ;
- imports morts supprimés ;
- tests dédiés supprimés sans retirer les tests des autres moteurs partageant les mêmes fichiers ;
- contrat anti-régression ajouté dans `backend/tests/test_scientific_core_purge_contract.py` ;
- workflows temporaires `.github/workflows/scientific-core-purge-apply.yml` et `.github/workflows/scientific-core-purge-audit.yml` supprimés.

État: CERTIFIÉ SUR PR.

Preuve:
- CI run `34222898913` : SUCCESS ;
- Patient Indicators Truth Certification : SUCCESS ;
- T2 Runtime Browser Certification : SUCCESS ;
- Catalog Connected Truth Certification : SUCCESS ;
- Patient P7 Final Certification : SUCCESS ;
- Settings TemplateEngine Reachability Certification : SUCCESS.

### 1.3 Couche clinical coherence

Cible: `backend/services/clinical_coherence.py`.

Constat vérifié :
- couche réellement consommée par le runtime ;
- elle ne peut donc pas être supprimée comme code mort ;
- certaines heuristiques doivent être auditées scientifiquement avant conservation.

Classement actuel: `REPLACE / CONSOLIDATE`, PAS `DELETE` immédiat.

Next:
- inventorier chaque règle ;
- identifier celles déjà couvertes par prescription/safety ;
- retirer les règles faibles seulement après remplacement prouvé.

### 1.4 Prescription / safety legacy

Constat vérifié : certaines règles legacy étaient trop larges ou hors responsabilité du medication-safety.

Nettoyage appliqué :
- faux signal `allergie` générique ne doit plus devenir automatiquement une alerte pénicilline ;
- rappel `pas de détartrage depuis 12 mois` retiré du contrat medication-safety ;
- alertes spécifiques pénicilline et DDI conservées ;
- tests adaptés au nouveau contrat.

Preuve :
- CI run `34222898913` : SUCCESS.

Classement actuel: `REPLACE / CONSOLIDATE` pour le legacy restant.

### 1.5 ClinicalRulesEngine

Cible : `backend/services/clinical_rules_engine.py`.

Constat vérifié :
- le moteur contient `age = patient_data.get("age", 30)` et `poids = patient_data.get("poids", 70)` ;
- recherche exhaustive dans le fichier : ces deux variables ne sont jamais relues après leur affectation ;
- elles ne modifient donc actuellement aucune recommandation ;
- elles sont néanmoins trompeuses et doivent être supprimées comme code mort.

Classement : `DELETE` pour ces deux fallback locaux uniquement ; audit scientifique du moteur complet toujours requis.

#### Audit scientifique actif — premiers résultats vérifiés

1. **Prophylaxie endocardite avec clindamycine**
   - code actuel : alternative automatique `Clindamycine 600 mg` en cas d'allergie pénicilline ;
   - état : `REPLACE` ;
   - preuve externe : les recommandations AAPD 2026 basées sur les recommandations AHA indiquent explicitement que la clindamycine n'est plus recommandée pour la prophylaxie d'une procédure dentaire ;
   - conséquence : ne pas conserver cette alternative automatique dans le futur moteur canonique.

2. **Radiographie pendant la grossesse — tablier plombé obligatoire**
   - code actuel : message `CRITICAL` affirmant que tablier plombé + collerette sont obligatoires ;
   - état : `REPLACE / CONFLIT DE SOURCES` ;
   - preuve externe : ADA 2024 recommande de ne plus utiliser systématiquement tablier abdominal/collerette, y compris chez la patiente enceinte ; une publication ACOG plus ancienne mentionne encore le shielding ;
   - conséquence : retirer toute formulation absolue et reconstruire cette règle sur une source/version clairement choisie, avec réglementation locale si nécessaire.

3. **Probiotique automatique après amoxicilline/Augmentin**
   - code actuel : ajoute automatiquement `Saccharomyces boulardii` et le présente comme prévention de colite/diarrhée ;
   - état : `REPLACE / DELETE AUTO-RECOMMENDATION` ;
   - preuve externe : la page ADA Antibiotic Stewardship rapporte que les données sont insuffisantes pour recommander les probiotiques pour prévenir l'infection à C. difficile ;
   - conséquence : ne pas faire d'une co-prescription automatique un comportement canonique.

4. **Antibioprophylaxie automatique des implants**
   - code actuel : protocole implant => Augmentin + message de prophylaxie systématique ;
   - état : `REPLACE / NON SOURCÉ` ;
   - preuve externe : l'ADA indique qu'une recommandation dédiée aux patients sains subissant une pose d'implant est encore dans son programme de guideline vivante et attendue pour l'hiver 2026 ;
   - conséquence : Digital Crown ne doit pas présenter une prophylaxie implant universelle comme vérité établie sans référentiel validé.

5. **Grossesse et AINS**
   - code actuel : classe tous les AINS/ibuprofène comme contre-indication absolue pour toute grossesse ;
   - état : `REPLACE` ;
   - preuve externe : FDA recommande d'éviter les AINS à partir de 20 semaines, de les éviter après 30 semaines, et prévoit des nuances/exceptions ;
   - conséquence : une règle grossesse doit utiliser l'âge gestationnel et ne pas transformer une règle temporelle en interdiction uniforme.

6. **Antibiotiques pour pathologies pulpaires/périapicales**
   - code actuel : plusieurs protocoles associent directement diagnostic/acte à molécules ;
   - état : `REPLACE / REASONING REQUIRED` ;
   - preuve externe : guideline ADA douleur/infection 2019 recommande le traitement dentaire définitif plutôt que l'antibiothérapie pour la majorité des pathologies pulpaires/périapicales, avec antibiotiques notamment en cas d'atteinte systémique ;
   - conséquence : le futur moteur doit raisonner sur diagnostic + signes systémiques + traitement étiologique, pas sur un simple mapping mot-clé → médicament.

#### Conclusion du lot ClinicalRulesEngine

Le fichier ne doit pas devenir le noyau scientifique canonique en l'état.

Responsabilités à conserver :
- moteur déterministe ;
- détection structurée de contexte ;
- capacité à produire des alertes explicables.

Responsabilités à reconstruire :
- règles pharmacologiques ;
- prophylaxies ;
- diagnostics ;
- recommandations thérapeutiques ;
- sources/versioning ;
- niveau de certitude ;
- gestion des données manquantes.

Classement global actuel : `REPLACE / CONSOLIDATE`, pas `DELETE` brutal tant que ses garde-fous utiles ne sont pas couverts ailleurs.

Next :
- retirer le code mort local ;
- inventorier ses consommateurs runtime ;
- identifier les garde-fous uniques à préserver ;
- isoler les règles obsolètes/trop absolues derrière un futur moteur scientifique versionné.

### 1.6 Imagerie panoramique

Goal: éliminer la multiplication historique des moteurs/wrappers panoramiques et vision.

À auditer :
- `panoramic_*` ;
- `vision_*` ;
- `sota_*` ;
- generators/report engines associés.

Succès:
- un pipeline produit clairement identifié ;
- aucun wrapper dormant ;
- aucune détection automatique transformée en diagnostic ou traitement ;
- tests du pipeline restant.

État: À AUDITER.

### 1.7 Céphalométrie

Goal: conserver un seul pipeline canonique et retirer les générations obsolètes sans réduire les mesures utiles.

À vérifier :
- service d'upload/process ;
- moteur landmarks ;
- calibration ;
- calculs de mesures ;
- refine manuel ;
- validator ;
- export/PDF.

État: À AUDITER après panoramique/safety.

## PHASE 2 — CONSOLIDATION

Après le nettoyage :

- définir les moteurs canoniques par domaine ;
- fusionner les responsabilités dupliquées ;
- normaliser les contrats d'entrée/sortie ;
- isoler règles cliniques, documentaires et financières ;
- supprimer les scores globaux mélangeant des dimensions incompatibles ;
- documenter dépendances et limites.

État: NON COMMENCÉ.

## PHASE 3 — REBUILD SCIENTIFIQUE

Construire ou réécrire uniquement ce qui manque après consolidation :

- safety clinique déterministe ;
- prescription avec garde-fous explicites ;
- cohérence dossier/document ;
- céphalométrie ;
- panoramique limitée aux responsabilités réellement validées ;
- synthèse clinique sans plan de traitement automatique ;
- provenance et niveau de confiance des sorties.

État: NON COMMENCÉ.

## PHASE 4 — CERTIFICATION

Pour chaque moteur canonique :

- tests unitaires des règles ;
- golden cases ;
- tests négatifs/fail-closed ;
- tests de non-régression ;
- tests runtime sur les routes réellement exposées ;
- revue scientifique humaine des résultats cliniquement sensibles.

Aucune sortie n'est déclarée certifiée sans preuve.

État: NON COMMENCÉ.

## PHASE 5 — INTÉGRATION / CLOSEOUT

- cohérence du canonique ;
- PR vers `master` ;
- CI verte ;
- merge ;
- post-merge ;
- suppression des branches/workflows temporaires restants ;
- statut final documenté.

Aucun déploiement Vercel dans ce chantier sans autorisation explicite.

## REPÈRES VÉRIFIÉS

Repo: `hraaaaf/Digital_crown`

Branche: `refactor/scientific-core-purge`

PR: `#371` draft

HEAD certifié safety/nettoyage: `f4a455292d85eae142c9d023c20555929ab123d1`

CI certifiée: run `34222898913` — SUCCESS.

Premières conclusions :
- `TreatmentPlanEngine` : supprimé et certifié sur PR ;
- `clinical_coherence.py` : actif, audit/remplacement requis ;
- prescription/safety legacy : faux signaux déjà réduits, consolidation restante ;
- `clinical_rules_engine.py` : classé globalement `REPLACE / CONSOLIDATE`; plusieurs règles actives obsolètes, trop absolues ou non sourcées identifiées ;
- panoramique/vision : consolidation à auditer ;
- céphalométrie : audit après nettoyage prioritaire.

## NEXT EXACT

Inventorier les consommateurs runtime de `clinical_rules_engine.py`, identifier les garde-fous uniques à préserver, puis isoler/supprimer les règles scientifiquement faibles uniquement après couverture ou remplacement prouvé.
