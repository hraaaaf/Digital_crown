# DIGITAL CROWN — SCIENTIFIC CORE REBUILD — CANONICAL HANDOVER

**Rôle :** source canonique de reprise du chantier Scientific Core.  
**Reprise :** lire ce fichier en premier, puis vérifier `repo / branche / PR / HEAD / CI` avant toute modification. Ne jamais supposer que les SHA/runs ci-dessous sont encore courants.

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

## 3. REPO / BRANCHE / PR — ÉTAT VÉRIFIÉ AVANT CE COMMIT DOCUMENTAIRE

Repo : `hraaaaf/Digital_crown`  
Branche : `refactor/scientific-core-purge`  
PR : `#371` — draft, ouverte, mergeable  
Base : `master`  
HEAD code vérifié : `8a11ae6ec4c51751854586849cbdf4e3ce330c8f`  
Commit : `test: lock panoramic PDF fail-closed semantics`

### CI vérifiée sur ce HEAD

- Digital Crown CI : run `34250350231` — **SUCCESS**.
- T2 Runtime Browser Certification : run `34250350115` — **SUCCESS**.
- Catalog Connected Truth Certification : run `34250350215` — **SUCCESS**.
- Patient P7 Final Certification : run `34250350246` — **SUCCESS**.
- Settings TemplateEngine Reachability Certification : run `34250350196` — **SUCCESS**.
- Patient Indicators Truth Certification : run `34250350109` — **FAILURE**, même timeout responsive/race déjà observé sur le viewport `768`, indépendant du lot panorama/report au diagnostic disponible.

**Ne pas présenter le HEAD comme globalement all-green** tant que cette certification secondaire reste rouge. Ce commit documentaire crée un nouveau HEAD ; revérifier les runs après commit.

---

## 4. ÉTAT GLOBAL

- **Phase 1 — Nettoyage scientifique : EN COURS.**
- **Phase 2 — Consolidation : PAS ENCORE COMMENCÉE FORMELLEMENT.**
- **Phase 3 — Rebuild : PAS ENCORE COMMENCÉE FORMELLEMENT.**
- **Phase 4 — Certification scientifique : PAS ENCORE COMMENCÉE FORMELLEMENT.**

---

# PHASE 1 — NETTOYAGE

## LOT 1 — `TreatmentPlanEngine`

**État : SUPPRIMÉ ET CERTIFIÉ SUR PR.**

Preuves : moteur dormant supprimé, imports/tests dédiés retirés, contrat anti-régression ajouté, runners temporaires retirés, CI antérieure `34222898913` SUCCESS.  
Décision : `DELETE` confirmé.

---

## LOT 2 — Prescription / Medication Safety Legacy

**État : NETTOYAGE PARTIEL CERTIFIÉ. REBUILD RESTANT.**

Déjà corrigé : allergie générique ≠ pénicilline automatique ; rappel détartrage retiré du medication-safety ; alertes spécifiques pénicilline/DDI conservées ; heuristique `antibiotique sans acte invasif => incohérent` retirée/neutralisée.

### Gap safety UX prouvé

`PrescriptionAgenticStudio.tsx` maintient `safetyStatus`, mais `useDocumentGenerator.ts` ne reçoit pas directement ce statut comme gate final save/print. Un safety-check pending/error/unverified n'est donc pas, à lui seul, un gate final.

Classement : `REPLACE / CONSOLIDATE`.

---

## LOT 3 — `clinical_rules_engine.py`

**État : ACTIF RUNTIME. AUDIT PARTIEL. `REPLACE / CONSOLIDATE`.**

Consommateurs vérifiés :
- `prescription_service_legacy.py` appelle `clinical_rules.analyze_case()` ;
- `prescription_service.py` utilise `clinical_rules` pour le contexte d'acte ;
- `prescription_agentic_service.py` passe par `prescription_service`.

### Défaut patient synthétique critique

`clinical_rules_engine.py` utilise encore `age=30` et `poids=70`. Ces valeurs influencent `is_child`, la forme et `_calculate_pediatric_dosage()`. `prescription_service_legacy.py` injecte également historiquement `poids=70`.

Le wrapper moderne protège une partie du chemin pédiatrique, mais le moteur reste dangereux s'il est appelé directement/autrement. **Cible : aucune valeur clinique synthétique ; décision dépendante d'une donnée absente => non évaluable/fail-closed.** Modification médicale, donc gate humain requis avant implémentation.

Règles déjà classées `REPLACE` : clindamycine 600 mg alternative automatique de prophylaxie d'endocardite ; grossesse + shielding obligatoire ; Saccharomyces boulardii auto après amoxicilline/Augmentin ; implant => prophylaxie antibiotique universelle ; grossesse => AINS interdits uniformément ; mapping mot-clé acte/diagnostic => médicament.

Toute implémentation finale devra revalider source primaire/version/applicabilité Maroc.

---

## LOT 4 — `clinical_coherence.py`

**État : ACTIF RUNTIME. `REPLACE / CONSOLIDATE`.**

Déjà retiré : `antibiotique + absence d'acte invasif => incohérence`.

Audit technique restant : le module mélange validation documentaire, règle clinique NSAID/GI basée sur mots-clés et contrôle comptable. Cible : validation documentaire hors moteur clinique, comptabilité hors moteur clinique, medication safety dans le futur moteur pharmacologique structuré.

---

## LOT 5 — Imagerie panoramique

### Goal

Identifier le pipeline produit réel, supprimer les wrappers morts et préserver le chemin actif sans perte fonctionnelle.

### État

**SUPPRESSION DES WRAPPERS MORTS CERTIFIÉE. LOT DE PURGE FERMÉ.**

Pipeline actif : `backend/routers/ia.py` → `panoramic_service.detect_teeth_only()` → `sota_panoramic_service.py` → `panoramic_report_engine.py` → `PanoramicAnalysis`.

### Classification finale

| Composant | Décision |
|---|---|
| `panoramic_service.py` | `KEEP / CONSOLIDATE` |
| `sota_panoramic_service.py` | `KEEP` |
| `panoramic_ai_advisor.py` | `DELETE` confirmé |
| `panoramic_expert_engine.py` | `DELETE` confirmé |
| `panoramic_vision_service.py` | `DELETE` confirmé |
| `panoramic_report_engine.py` | actif, transféré LOT 6 |

### Preuves

- commit `b559a3dd681aa35de6bc773288409d087f615fe8` : suppression réelle des trois wrappers ;
- `test_scientific_core_purge_contract.py` : absence fichiers + scan références runtime ;
- seul consommateur détecté initialement : test legacy auto-testant `PanoramicExpertEngine`, retiré sans toucher aux tests céphalo ;
- pipeline actif conservé ;
- CI `34232806194` : **SUCCESS**.

---

## LOT 6 — Vision / Report panoramique

### Goal

Séparer observation/détection, interprétation clinique et recommandation, avec provenance explicite et **aucun faux négatif/diagnostic/traitement implicite** issu d'une donnée absente ou d'un simple label d'imagerie.

### État

**POLITIQUE FAIL-CLOSED IMPLÉMENTÉE ET CERTIFIÉE SUR CI PRINCIPALE. LOT 6 FERMÉ CÔTÉ PANORAMA/REPORT.**

### Décision clinique appliquée

Politique A :
- absence/non-saisie => `non documenté / non évalué`, jamais normalité implicite ;
- observation/anomalie => constat descriptif ;
- aucune conduite thérapeutique ni CCAM déduite automatiquement du seul label d'imagerie ;
- conduite clinique laissée au praticien ;
- provenance/limitations conservées.

Cette politique est désormais alignée avec les décisions durables : `détection ≠ diagnostic` et `diagnostic ≠ traitement automatique`.

### Changements prouvés depuis le closeout LOT 5

Comparaison `b559a3d… → 8a11ae6…` :
- `backend/services/panoramic_report_engine.py` modifié pour retirer normalité implicite et traitement/CCAM automatiques ;
- `backend/services/generators/panoramic_elite_gen.py` durci pour que l'export PDF n'invente pas denture, statut céphalo, diagnostic ou spécialité professionnelle ;
- `backend/tests/test_panoramic_report_fail_closed.py` ajouté ;
- `backend/tests/test_panoramic_pdf_fail_closed.py` ajouté ;
- `backend/tests/test_services_unit10.py` migré du contrat privé legacy vers le nouveau contrat observable ;
- total compare : 6 commits, 6 fichiers concernés sur ce sous-lot/documentation.

### Contrats de sécurité couverts

- absence de finding ≠ normalité implicite ;
- label d'anomalie ≠ plan thérapeutique automatique ;
- label d'anomalie ≠ CCAM automatique ;
- PDF : denture non documentée reste non documentée ;
- PDF : métrique céphalo incomplète/absente ne devient pas `Normal/Harmonieux` ;
- PDF : libellé `Diagnostics` trompeur neutralisé ;
- PDF : spécialité praticien non fournie non inventée.

### Preuve

HEAD `8a11ae6ec4c51751854586849cbdf4e3ce330c8f` + CI principale run `34250350231` : **SUCCESS**.

La certification secondaire `Patient Indicators Truth Certification` reste rouge sur un timeout responsive/race connu, sans signal de régression panorama/report dans les preuves disponibles. Elle reste un défaut transverse à traiter séparément avant certification globale.

### Périmètre reclassé

`backend/services/vision_service.py` et `backend/services/sota_vision_service.py` appartiennent au pipeline **céphalométrique actif** et sont maintenus pour le LOT 7.

---

## LOT 7 — Céphalométrie

Pipeline à auditer/revalider : `upload → ia.py → CephaloService → calibration → VisionEngine PyTorch 19 ou ONNX 38 → CephaloEngine → repository → édition frontend → refine → validator → PDF`.

Services actifs déjà reclassés :
- `vision_service.py` : multiplexer landmarks céphalo, ONNX 38 avec fallback PyTorch 19 ; `KEEP / CONSOLIDATE` à auditer ;
- `sota_vision_service.py` : dépendance active ; `KEEP / CONSOLIDATE` à auditer ;
- `cephalo_service.py` consomme `vision_engine` ;
- `test_vision_apex_provenance.py` interdit la fabrication silencieuse des apex.

### Goal

Un seul pipeline landmarks supporté ; calibration explicite ; prediction vs correction manuelle distinguées ; mesures déterministes depuis landmarks validés ; aucune conclusion clinique automatique non sourcée ; validator avant export ; golden cases géométriques/cas limites.

**État : PRÉ-AUDIT EFFECTUÉ, AUDIT COMPLET RESTANT.**

---

# PHASE 2 — CONSOLIDATION CIBLE

1. `PatientClinicalContext` : âge, poids/BSA lorsque pertinent, allergies, conditions, médicaments actifs, grossesse/âge gestationnel si pertinent, fonction rénale/hépatique, données biologiques utiles, indication.
2. `MedicationKnowledge` : DCI/ingrédients, classe/ATC, marques, dosage, forme, voie, présentation, disponibilité marché/pays, source/version/date d'effet.
3. `MedicationSafetyEngine` : allergie/cross-réactivité, interactions, duplications, contre-indications, limites de dose, rénal/hépatique, grossesse/allaitement, données manquantes, sévérité/management.
4. `DentalClinicalReasoningEngine` : diagnostic, symptômes, signes systémiques, indication, traitement étiologique, proposition explicable non autoritaire.
5. `ImagingPipeline` : acquisition, détection/landmarks, mesures, validation, interprétation séparée, rapport.
6. `CephaloEngine` : landmarks validés, calibration, mesures déterministes, provenance/version modèle, correction humaine traçable.

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

---

# PROCÉDURE DE REPRISE

1. lire ce fichier entier ;
2. vérifier branche `refactor/scientific-core-purge` ;
3. vérifier PR `#371` ;
4. vérifier HEAD courant ;
5. vérifier CI/runs du HEAD ;
6. inspecter les changements depuis le dernier HEAD consigné ;
7. reprendre au `NEXT EXACT` ;
8. après chaque gros lot, mettre à jour ce fichier avec état réellement vérifié ;
9. ne jamais modifier états/% sur intuition ;
10. closeout complet avant merge.

---

# NEXT EXACT

## Human gate suivant — Prescription / cohérence

Problème prouvé : `clinical_rules_engine.py` possède encore des valeurs patient synthétiques `age=30` et `poids=70`, et `prescription_service_legacy.py` injecte aussi `poids=70`. Elles peuvent influencer branche pédiatrique, forme et dosage.

### Option A — recommandée

- supprimer toutes les valeurs patient synthétiques ;
- une règle nécessitant âge/poids absent devient `non évaluable / fail-closed` ;
- conserver les contrôles indépendants de l'âge/poids lorsqu'ils restent valides ;
- ne pas fabriquer de dose pédiatrique ;
- couvrir appels directs legacy + wrapper moderne + cas adulte/pédiatrique/donnée manquante.

### Option B

Conserver les valeurs par défaut historiques. Non recommandé et incompatible avec le Goal final `aucune donnée patient synthétique`.

Après décision : tests négatifs avant code → patch minimal → tests prescription/cohérence → CI → closeout lots 2/3/4 → audit céphalo → consolidation → rebuild → certification globale → closeout PR → merge → CI post-merge.

---

# CLOSEOUT ATTENDU

`validation → tests/golden cases → docs canoniques → cohérence roadmap → PR → CI → merge → post-merge CI`

Si CI en cours : aucun polling/attente passive. Faire le travail indépendant puis revérifier seulement quand nécessaire.

---

## REPÈRES DE REPRISE

- chantier : Digital Crown — Scientific Core Rebuild
- phase : Phase 1 nettoyage
- dernier lot fermé : LOT 6 Vision / Report panoramique
- lot actif suivant : Prescription / cohérence
- Goal actif : éliminer les valeurs patient synthétiques sans perdre les contrôles réellement évaluables
- repo : `hraaaaf/Digital_crown`
- branche : `refactor/scientific-core-purge`
- PR : `#371` draft, ouverte, mergeable
- HEAD code vérifié avant ce commit documentaire : `8a11ae6ec4c51751854586849cbdf4e3ce330c8f`
- CI principale de ce HEAD : `34250350231` — SUCCESS
- certification secondaire Patient Indicators : `34250350109` — FAILURE sur timeout responsive/race connu 768
- dernière preuve : fail-closed panorama/report + PDF verrouillé par tests dédiés et CI principale verte
- blocage réel suivant : human gate médical prescription sur suppression des valeurs synthétiques âge/poids
- Next exact : appliquer A si confirmé, tests négatifs avant code
- Séquence restante : prescription/cohérence → céphalo → consolidation → rebuild → certification → closeout → merge → post-merge
- déploiement : aucun déploiement Vercel autorisé

**FICHIER CANONIQUE : `docs/SCIENTIFIC_CORE_REBUILD_ROADMAP.md`**
