# DIGITAL CROWN — SCIENTIFIC CORE REBUILD — CANONICAL HANDOVER

**Rôle :** source canonique de reprise du chantier Scientific Core.  
**Reprise :** lire ce fichier en premier, puis vérifier `repo / branche / PR / HEAD / CI` avant toute modification. Les SHA/runs ci-dessous sont des preuves historiques, jamais une excuse pour ne pas revérifier l'état courant.

---

## 1. GOAL FINAL

Reconstruire le noyau scientifique de Digital Crown pour qu'il soit minimal, explicable, déterministe quand possible, versionné/sourcé, patient-specific, **fail-closed** quand une donnée clinique indispensable manque, sans moteur mort ni donnée patient synthétique, sans diagnostic/recommandation automatique présenté comme vérité, avec praticien décisionnaire et certification complète avant merge.

### Succès observable

1. un moteur canonique par responsabilité scientifique ;
2. aucun wrapper/service scientifique dormant ou redondant non justifié ;
3. aucune règle clinique active non sourcée/versionnée dans le futur moteur ;
4. aucune valeur patient par défaut susceptible de modifier une décision clinique ;
5. séparation nette : contexte patient / observation / diagnostic / safety / recommandation ;
6. provenance et niveau de confiance disponibles lorsque pertinents ;
7. CI + tests scientifiques verts avant merge ;
8. revue humaine obligatoire pour les règles médicales sensibles.

### Preuve finale attendue

Code consolidé + tests unitaires/golden/négatifs/non-régression + docs canoniques cohérentes + PR certifiée + merge `master` + CI post-merge verte.

**Aucun déploiement Vercel sans autorisation explicite du user.**

---

## 2. CLASSIFICATION

- `KEEP` : actif, utile, responsabilité claire, comportement acceptable.
- `CONSOLIDATE` : actif/utile mais redondant avec un autre moteur.
- `REPLACE` : actif mais scientifiquement insuffisant, trop absolu, non sourcé ou dangereux.
- `DELETE` : mort, obsolète, sans consommateur réel ou responsabilité abandonnée.

Règle dure : **une couche clinique active classée `REPLACE` n'est jamais supprimée sans couverture/remplacement prouvé.**

---

## 3. REPO / BRANCHE / PR — DERNIER ÉTAT CODE CERTIFIÉ

Repo : `hraaaaf/Digital_crown`  
Branche : `refactor/scientific-core-purge`  
PR : `#371` — draft, ouverte  
Base : `master`  
HEAD code certifié avant ce commit documentaire : `7ace175d2cce54b420effe71011ae941bb61db24`  
Commit : `test: lock clinical coherence runtime consumers`

### CI vérifiée sur ce HEAD

- Digital Crown CI : run `34257536407` — **SUCCESS**.
- T2 Runtime Browser Certification : run `34257536283` — **SUCCESS**.
- Catalog Connected Truth Certification : run `34257536425` — **SUCCESS**.
- Patient P7 Final Certification : run `34257536424` — **SUCCESS**.
- Settings TemplateEngine Reachability Certification : run `34257536303` — **SUCCESS**.
- Patient Indicators Truth Certification : run `34257536281` — **FAILURE** ; défaut transverse responsive/race déjà observé, à traiter avant certification globale.
- M6-I Biometric Passkey Certification : `SKIPPED`.

**Ne pas qualifier la PR de globalement all-green** tant que la certification Patient Indicators reste rouge. Ce commit documentaire crée un nouveau HEAD : ses workflows doivent être vérifiés séparément.

---

## 4. ÉTAT GLOBAL

- **Phase 1 — Nettoyage scientifique : EN COURS, lots panorama/report fermés ; prescription démographie certifiée ; céphalo au gate médical.**
- **Phase 2 — Consolidation : PAS ENCORE COMMENCÉE FORMELLEMENT.**
- **Phase 3 — Rebuild : PAS ENCORE COMMENCÉE FORMELLEMENT.**
- **Phase 4 — Certification scientifique globale : PAS ENCORE COMMENCÉE FORMELLEMENT.**

---

# PHASE 1 — NETTOYAGE

## LOT 1 — `TreatmentPlanEngine`

**État : SUPPRIMÉ ET CERTIFIÉ SUR PR.**

Preuves : moteur dormant supprimé, imports/tests dédiés retirés, contrat anti-régression ajouté, runners temporaires retirés, CI antérieure `34222898913` SUCCESS.  
Décision : `DELETE` confirmé.

---

## LOT 2 — Prescription / Medication Safety Legacy

**État : NETTOYAGE PARTIEL CERTIFIÉ. REBUILD RESTANT.**

Déjà corrigé :
- allergie générique ≠ pénicilline automatique ;
- rappel détartrage retiré du medication-safety ;
- heuristique `antibiotique sans acte invasif => incohérent` neutralisée sur le chemin moderne ;
- alertes spécifiques pénicilline/DDI conservées ;
- valeurs patient synthétiques retirées du chemin de calcul démographique, voir LOT 3.

### Gap safety UX prouvé

`PrescriptionAgenticStudio.tsx` maintient `safetyStatus`, mais `useDocumentGenerator.ts` ne reçoit pas directement ce statut comme gate final save/print. Un safety-check pending/error/unverified n'est donc pas, à lui seul, un gate final.

Classement : `REPLACE / CONSOLIDATE`.

---

## LOT 3 — `clinical_rules_engine.py`

**État : ACTIF RUNTIME. SOUS-LOT DÉMOGRAPHIE FAIL-CLOSED IMPLÉMENTÉ ET CERTIFIÉ. MOTEUR GLOBAL `REPLACE / CONSOLIDATE`.**

### Consommateurs vérifiés

- `prescription_service_legacy.py` appelle `clinical_rules.analyze_case()` ;
- `prescription_service.py` constitue le wrapper public moderne et applique le guard de contexte ;
- `prescription_agentic_service.py` passe par le wrapper moderne.

### Politique A validée par le user et implémentée

- `age=30` supprimé ;
- `poids=70` supprimé du moteur ;
- injection legacy `poids=70` supprimée ;
- âge absent => aucune posologie dépendante de l'âge calculée ;
- enfant sans poids => aucune dose pédiatrique calculée ;
- enfant avec poids explicite => calcul utilise ce poids ;
- adulte connu sans poids => chemin de posologie adulte standard conservé lorsque le poids n'est pas requis ;
- contrôles indépendants des données démographiques conservés.

### Limite de modèle patient vérifiée

Le modèle `Patient` actuel ne possède pas de champ poids. Le legacy tente uniquement des attributs réels s'ils existent (`weight_kg` / `poids`) et obtient sinon `None`. Aucun poids de substitution n'est inventé.

### Preuves

- `backend/tests/test_prescription_demographics_fail_closed.py` couvre âge absent, enfant sans poids, enfant avec poids explicite, adulte sans poids, absence de literals synthétiques et reachability du legacy ;
- `backend/services/clinical_rules_engine.py`, `prescription_service.py`, `prescription_service_legacy.py` modifiés ;
- contrat de reachability : seul `prescription_service.py` est autorisé à consommer directement le service legacy ;
- HEAD code certifié `7ace175d2cce54b420effe71011ae941bb61db24` ;
- CI `34257536407` : **SUCCESS**.

### Règles médicales restant `REPLACE`

Exemples déjà audités : clindamycine 600 mg comme alternative automatique de prophylaxie d'endocardite ; grossesse + shielding obligatoire ; Saccharomyces boulardii automatique après amoxicilline/Augmentin ; implant => prophylaxie antibiotique universelle ; grossesse => AINS interdits uniformément ; mapping mot-clé acte/diagnostic => médicament.

Toute règle finale devra être reliée à une source primaire/professionnelle, version, date d'effet et applicabilité au contexte Maroc.

---

## LOT 4 — `clinical_coherence.py`

**État : ACTIF RUNTIME PROUVÉ. `REPLACE / CONSOLIDATE`. PAS CANDIDAT DELETE.**

### Reachability exacte certifiée

Imports runtime autorisés et observés :
- `backend/routers/documents.py` ;
- `backend/services/elite_manager.py`.

`backend/tests/test_clinical_coherence_reachability.py` utilise l'AST pour verrouiller exactement ces consommateurs et ignorer commentaires/tests comme faux positifs.

### Architecture à corriger ultérieurement

Le module mélange actuellement :
- validation/documentation clinique ;
- règle NSAID/GI basée sur mots-clés ;
- contrôle comptable ;
- scoring/fixes.

Cible : validation documentaire hors moteur clinique, comptabilité hors moteur clinique, medication safety consolidée dans le moteur pharmacologique structuré. Les règles médicales ne changent pas sans gate humain.

Preuve CI : `34257536407` — **SUCCESS**.

---

## LOT 5 — Imagerie panoramique

**État : SUPPRESSION DES WRAPPERS MORTS CERTIFIÉE. LOT DE PURGE FERMÉ.**

Pipeline actif : `backend/routers/ia.py` → `panoramic_service.detect_teeth_only()` → `sota_panoramic_service.py` → `panoramic_report_engine.py` → `PanoramicAnalysis`.

Classification :
- `panoramic_service.py` : `KEEP / CONSOLIDATE` ;
- `sota_panoramic_service.py` : `KEEP` ;
- `panoramic_ai_advisor.py` : `DELETE` confirmé ;
- `panoramic_expert_engine.py` : `DELETE` confirmé ;
- `panoramic_vision_service.py` : `DELETE` confirmé ;
- `panoramic_report_engine.py` : actif, traité LOT 6.

Preuves : commit `b559a3dd681aa35de6bc773288409d087f615fe8`, contrat purge, pipeline actif conservé, CI `34232806194` SUCCESS.

---

## LOT 6 — Vision / Report panoramique

**État : POLITIQUE FAIL-CLOSED IMPLÉMENTÉE ET CERTIFIÉE. LOT PANORAMA/REPORT FERMÉ.**

Politique appliquée :
- absence/non-saisie => `non documenté / non évalué`, jamais normalité implicite ;
- observation/anomalie => constat descriptif ;
- aucune conduite thérapeutique ni CCAM déduite automatiquement du seul label d'imagerie ;
- décision clinique laissée au praticien ;
- provenance/limitations conservées.

Preuves : `panoramic_report_engine.py` et générateur PDF durcis, tests fail-closed rapport/PDF, HEAD `8a11ae6ec4c51751854586849cbdf4e3ce330c8f`, CI `34250350231` SUCCESS.

`vision_service.py` et `sota_vision_service.py` sont **céphalo actifs**, pas panorama legacy.

---

## LOT 7 — Céphalométrie

### Pipeline actif vérifié

`upload → ia.py → CephaloService → calibration → VisionEngine ONNX 38 ou fallback PyTorch 19 → CephaloEngine → repository → édition frontend → refine → validator → PDF`.

Composants :
- `vision_service.py` : multiplexer landmarks céphalo, actif, `KEEP / CONSOLIDATE` à certifier ;
- `sota_vision_service.py` : dépendance active, `KEEP / CONSOLIDATE` à certifier ;
- `cephalo_service.py` : récupère âge/sexe réels du patient, sans invention ;
- `test_vision_apex_provenance.py` interdit la fabrication silencieuse des apex ;
- absence de calibration => mesures linéaires mm non évaluables dans le chemin principal ;
- `Patient` ne possède pas de `population_id`, donc aucun profil populationnel spécifique ne peut être sélectionné aujourd'hui.

### Registre normatif

`cephalo_normative_service.py` est fail-closed :
- pas de fallback silencieux ;
- profils `LEGACY_UNVALIDATED` non autoritatifs ;
- quarantine/ambiguïté bloquent la classification ;
- classification uniquement via règle explicitement validée pour le profil.

Les fichiers `normative_profiles.yaml` et `classification_rules.yaml` conservent explicitement les conflits legacy et les marquent non validés/quarantined. Plusieurs docstrings indiquant encore que le registre n'est « pas wired » sont obsolètes et devront être corrigées.

### Risque scientifique principal prouvé : double vérité normative

`CephaloEngine` continue parallèlement à appeler `_evaluate_metric()` avec de nombreuses normes hardcodées legacy et génère `Normal/High/Low/Compensated`, interprétations et z-scores. Exemples : SNA 82±2, SNB 80±2, ANB 2±2, Tweed 26±4, IMPA 90±5, I/Francfort 107±5, Wits 0±1.5.

Donc le registre externe est fail-closed mais l'ancien moteur continue à produire une seconde sémantique normative. Cible : **une seule autorité normative**.

### Risque médical principal prouvé : stratégie thérapeutique automatique active

`CephaloEngine.calculate_metrics()` construit encore automatiquement une `strategie_therapeutique` à partir des mesures/classements et peut proposer notamment :
- Twin Block / activateur / Herbst ;
- disjonction + masque de Delaire ;
- TADs / contrôle vertical ;
- Damon / Invisalign / Forsus ;
- compensation de Classe III ou chirurgie orthognathique.

Cette stratégie est exposée dans `ai_narrative`. Elle est incompatible avec la décision durable `diagnostic ≠ traitement automatique` et nécessite un gate médical explicite avant modification.

`bilan_ortho_engine.generate_bilan()` est déjà plus sûr : il utilise le plan praticien s'il existe, sinon indique qu'aucune stratégie thérapeutique n'est générée automatiquement. Sa méthode legacy `_generate_plan_traitement()` reste à prouver dormante avant suppression.

`ai_advisor.py` contient également des stratégies thérapeutiques automatiques ; ses imports observés dans `cephalo_service.py` et `elite_manager.py` paraissent inutilisés, mais **DELETE non encore certifié** : reachability de branche à prouver avant suppression.

### Hypothèses quantitatives à revalider

- `calculate_ddm_reelle()` applique `(IMPA - 90) / 2.5` comme conversion globale d'espace ; la relation 2,5°/mm existe dans la littérature orthodontique mais sa traduction en espace dépend notamment de géométrie d'arcade et du mouvement. Ce n'est pas une constante patient-specific universelle prouvée dans l'état actuel.
- `_project_t1_growth()` applique des vecteurs annuels fixes de croissance ; des méthodes de prévision peuvent reproduire des tendances moyennes mais l'erreur individuelle est suffisamment importante pour interdire de présenter cette projection comme vérité patient-specific sans validation.
- `_project_t2_strategy()` projette des landmarks depuis une stratégie inférée : comportement clinique à retirer/quarantiner si la politique A ci-dessous est validée.
- `cephalo_consistency_validator.py` possède aussi des bornes hard/soft/mm legacy. Elles doivent devenir plausibility guards sourcés, pas une seconde source de « norme clinique » implicite.

### Goal LOT 7

Un seul pipeline landmarks supporté ; calibration explicite ; prédiction vs correction manuelle distinguées ; mesures géométriques déterministes depuis landmarks validés ; une seule autorité normative ; aucune conclusion/stratégie thérapeutique automatique non sourcée ; validator avant export ; golden cases géométriques et cas limites.

**État : AUDIT TECHNIQUE AVANCÉ. BLOQUÉ AU GATE MÉDICAL POUR LES CHANGEMENTS DE SÉMANTIQUE CLINIQUE.**

---

# PHASE 2 — CONSOLIDATION CIBLE

1. `PatientClinicalContext` : âge, poids/BSA lorsque pertinent, allergies, conditions, médicaments actifs, grossesse/âge gestationnel si pertinent, fonction rénale/hépatique, données biologiques utiles, indication.
2. `MedicationKnowledge` : DCI/ingrédients, classe/ATC, marques, dosage, forme, voie, présentation, disponibilité marché/pays, source/version/date d'effet.
3. `MedicationSafetyEngine` : allergie/cross-réactivité, interactions, duplications, contre-indications, limites de dose, rénal/hépatique, grossesse/allaitement, données manquantes, sévérité/management.
4. `DentalClinicalReasoningEngine` : diagnostic, symptômes, signes systémiques, indication, proposition explicable non autoritaire.
5. `ImagingPipeline` : acquisition, détection/landmarks, mesures, validation, interprétation séparée, rapport.
6. `CephaloEngine` : landmarks validés, calibration, mesures déterministes, provenance/version modèle, correction humaine traçable, normes séparées de la géométrie.

---

# PHASE 3 — MEDICATION INTELLIGENCE TARGET

Flow cible : `médicament sélectionné` → résolution marque/DCI/ingrédients → contexte patient → formes/forces disponibles → données indispensables manquantes → checks allergy/DDI/rénal/hépatique/grossesse/duplication/dose → options pertinentes avec raison/source → validation praticien → override explicite/traçable lorsqu'autorisé.

Approche : terminologie/normalisation + labels structurés + catalogue officiel Maroc/AMM + base clinique professionnelle à évaluer + orchestration Digital Crown. Toute règle clinique finale doit revalider source primaire, version et applicabilité Maroc.

---

# FRONTEND ORDONNANCE — ÉTAT CONNU

Forces : quick entry, DrugRow riche, safety status accessible, validation payload, draft protection, preview/save/print/archive, préservation des formes explicites.

Risques : safety status non relié directement au gate final, surcharge cognitive, couches legacy/R3 superposées, modals/dropdowns locaux fragiles, densité élevée.

**Visual certification ordonnance complète : NON FAITE.** Toute modification UI suit obligatoirement : `BEFORE → Goal visuel → mockup/référence → implémentation → AFTER mêmes viewports → comparaison + tests → score visuel`.

---

# DÉCISIONS DURABLES

1. Pas de LLM comme autorité scientifique/pharmacologique.
2. NLP/LLM éventuel uniquement parsing/explication/résumé, jamais source primaire de dose/interaction/contre-indication.
3. Aucun patient fictif : pas d'âge, poids, grossesse, fonction rénale, etc. inventés.
4. Donnée indispensable absente : fail-closed pour la décision concernée.
5. Détection image ≠ diagnostic.
6. Diagnostic ≠ traitement automatique.
7. Absence d'annotation imagerie => `non documenté / non évalué`, jamais normalité implicite.
8. Label d'imagerie seul => aucune conduite thérapeutique ni CCAM automatique.
9. Chaque règle clinique sensible doit avoir source/version/provenance.
10. Conflit de sources : exposer l'incertitude.
11. Aucune suppression active sans preuve d'usage/remplacement.
12. Aucun déploiement Vercel sans autorisation explicite.
13. Ne pas mélanger ce chantier avec d'autres produits/projets.
14. Une mesure géométrique peut être calculée sans norme ; une classification normative ne peut être produite que par une source/profil explicitement validé.
15. Une projection de croissance ou de traitement ne doit jamais être présentée comme prédiction patient-specific sans validation adaptée.

---

# PROCÉDURE DE REPRISE

1. lire ce fichier ;
2. vérifier PR `#371`, branche, HEAD et mergeability ;
3. vérifier les workflows du HEAD courant une fois ;
4. si CI en cours, avancer sur le travail indépendant ;
5. comparer tout DELETE candidat aux consommateurs runtime réels de la branche ;
6. tests négatifs avant changement clinique risqué ;
7. appliquer le patch minimal ;
8. CI + comportement observable ;
9. mettre ce canonique à jour uniquement avec état prouvé ;
10. closeout complet avant merge.

---

# NEXT EXACT

## Human gate suivant — Céphalométrie

### Option A — RECOMMANDÉE

- conserver la géométrie/mesures déterministes ;
- seule la couche normative explicitement validée peut produire une classification clinique ;
- neutraliser/quarantiner les `Normal/High/Low/Compensated` legacy lorsqu'aucun profil validé ne les autorise ;
- supprimer toute stratégie thérapeutique automatique de `CephaloEngine.ai_narrative` ;
- ne conserver un plan thérapeutique que s'il vient explicitement du praticien ;
- neutraliser/quarantiner les projections T1/T2 patient-specific non validées ;
- conserver les valeurs brutes et la provenance pour permettre la validation clinique humaine ;
- transformer le validator en garde de plausibilité/cohérence, sans norme clinique implicite non sourcée.

### Option B

Conserver les stratégies thérapeutiques et projections automatiques en les étiquetant « expérimental / non validé ». **Non recommandé** : cela maintient une seconde vérité clinique et reste contraire au Goal `diagnostic ≠ traitement automatique`.

Après validation A/B : tests négatifs → patch minimal céphalo → tests géométriques/normatifs/PDF → CI → closeout LOT 7 → consolidation → rebuild → certification scientifique globale → correction du défaut transverse Patient Indicators → closeout PR → merge → CI post-merge.

---

## REPÈRES DE REPRISE

- chantier : Scientific Core Rebuild
- lot courant : LOT 7 Céphalométrie
- dernier HEAD code certifié avant ce commit documentaire : `7ace175d2cce54b420effe71011ae941bb61db24`
- CI principale code : `34257536407` SUCCESS
- PR : `#371`
- blocage réel : gate médical céphalo A/B
- déploiement : aucun déploiement Vercel autorisé

**FICHIER CANONIQUE : `docs/SCIENTIFIC_CORE_REBUILD_ROADMAP.md`**
