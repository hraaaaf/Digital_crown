# DIGITAL CROWN — SCIENTIFIC CORE REBUILD — CANONICAL HANDOVER

**Rôle :** source canonique de reprise du chantier Scientific Core.  
**Reprise :** lire ce fichier en premier, puis vérifier `repo / branche / PR / HEAD / CI` avant toute modification. Ne jamais supposer que les SHA/runs ci-dessous sont encore courants.

---

## 1. GOAL FINAL

Reconstruire le noyau scientifique de Digital Crown pour qu'il soit :

- minimal et maintenable ;
- explicable ;
- déterministe quand possible ;
- versionné et sourcé ;
- patient-specific lorsque le contexte clinique le permet ;
- **fail-closed** quand une donnée clinique indispensable manque ;
- sans moteur mort, doublon inutile ou règle clinique inventée ;
- sans donnée patient synthétique ;
- sans diagnostic ou recommandation automatique présentés comme vérité ;
- avec praticien toujours décisionnaire ;
- couvert par tests, golden cases, négatifs, non-régression et CI avant merge.

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

- code consolidé ;
- tests unitaires + golden cases + cas négatifs/fail-closed ;
- tests runtime/non-régression ;
- docs canoniques cohérentes ;
- PR certifiée ;
- merge `master` ;
- CI post-merge verte.

**Aucun déploiement Vercel sans autorisation explicite du user.**

---

## 2. PRINCIPES DE CLASSIFICATION

- `KEEP` : actif, utile, responsabilité claire, comportement acceptable.
- `CONSOLIDATE` : actif/utile mais redondant avec un autre moteur.
- `REPLACE` : actif mais scientifiquement insuffisant, trop absolu, non sourcé ou dangereux.
- `DELETE` : mort, obsolète, sans consommateur réel ou responsabilité abandonnée.

Règle dure : **une couche clinique active classée `REPLACE` n'est jamais supprimée sans couverture/remplacement prouvé.**

---

## 3. REPO / BRANCHE / PR — ÉTAT VÉRIFIÉ AVANT CE COMMIT DOCUMENTAIRE

Repo : `hraaaaf/Digital_crown`  
Branche : `refactor/scientific-core-purge`  
PR : `#371` — draft, ouverte  
Base : `master`  
HEAD code vérifié : `b559a3dd681aa35de6bc773288409d087f615fe8`  
Commit : `refactor: remove dormant panoramic wrappers`

### CI vérifiée sur ce HEAD

- Digital Crown CI : run `34232806194` — **SUCCESS**.
- Patient Indicators Truth Certification : échec secondaire connu sur le viewport `768`, timeout Playwright en attente du heading `Dossiers Patients`; l'artifact `1440` du même run avait réussi. Défaut classé responsive/race indépendant du changement panorama. **Ne pas présenter le HEAD comme globalement all-green.**

Ce commit documentaire crée un nouveau HEAD. En reprise, vérifier le SHA/runs courants.

---

## 4. ÉTAT GLOBAL

### Phase 1 — Nettoyage scientifique

**EN COURS.**

### Phase 2 — Consolidation

**PAS ENCORE COMMENCÉE FORMELLEMENT.**

### Phase 3 — Rebuild

**PAS ENCORE COMMENCÉE FORMELLEMENT.**

### Phase 4 — Certification scientifique

**PAS ENCORE COMMENCÉE FORMELLEMENT.**

---

# PHASE 1 — NETTOYAGE

## LOT 1 — `TreatmentPlanEngine`

**État : SUPPRIMÉ ET CERTIFIÉ SUR PR.**

Preuves : moteur dormant supprimé, imports/tests dédiés retirés, contrat anti-régression ajouté, runners temporaires retirés, CI antérieure `34222898913` SUCCESS.  
Décision : `DELETE` confirmé.

---

## LOT 2 — Prescription / Medication Safety Legacy

### État

**NETTOYAGE PARTIEL CERTIFIÉ. REBUILD RESTANT.**

Déjà corrigé :

- allergie générique ≠ alerte pénicilline automatique ;
- rappel `pas de détartrage depuis 12 mois` retiré du medication-safety ;
- alertes spécifiques pénicilline et DDI conservées ;
- heuristique `antibiotique sans acte invasif => incohérent` retirée/neutralisée ;
- tests anti-régression associés.

### Gap safety UX prouvé

`PrescriptionAgenticStudio.tsx` maintient `safetyStatus`, mais `useDocumentGenerator.ts` ne reçoit pas directement ce statut comme gate final save/print. Un safety-check pending/error/unverified n'est donc pas, à lui seul, un gate final.

Classement : `REPLACE / CONSOLIDATE`.

---

## LOT 3 — `clinical_rules_engine.py`

### État

**ACTIF RUNTIME. AUDIT PARTIEL. `REPLACE / CONSOLIDATE`.**

Consommateurs vérifiés :

- `prescription_service_legacy.py` appelle `clinical_rules.analyze_case()` ;
- `prescription_service.py` utilise `clinical_rules` pour le contexte d'acte ;
- `prescription_agentic_service.py` passe par `prescription_service`.

### Défaut patient synthétique critique

`clinical_rules_engine.py` utilise encore des valeurs synthétiques `age=30` et `poids=70`. Elles influencent `is_child`, la forme et `_calculate_pediatric_dosage()`.  
`prescription_service_legacy.py` injecte également historiquement `poids=70`.

Le wrapper moderne protège une partie du chemin pédiatrique, mais le moteur reste dangereux s'il est appelé directement/autrement. **Cible proposée : aucune valeur clinique synthétique ; décision dépendante d'une donnée absente => non évaluable/fail-closed.** Modification médicale, donc gate humain requis avant implémentation.

### Règles déjà classées

- clindamycine 600 mg comme alternative automatique de prophylaxie d'endocardite : `REPLACE` ;
- grossesse + shielding déclaré obligatoire : `REPLACE / CONFLIT DE SOURCES` ;
- Saccharomyces boulardii auto après amoxicilline/Augmentin : `REPLACE / DELETE AUTO-RECOMMENDATION` ;
- implant => prophylaxie antibiotique universelle : `REPLACE / NON SOURCÉ` ;
- grossesse => AINS interdits uniformément : `REPLACE` ;
- mapping mot-clé acte/diagnostic => médicament : `REPLACE / REASONING REQUIRED`.

Toute implémentation finale devra revalider source primaire/version/applicabilité Maroc.

---

## LOT 4 — `clinical_coherence.py`

### État

**ACTIF RUNTIME. `REPLACE / CONSOLIDATE`.**

Déjà retiré : `antibiotique + absence d'acte invasif => incohérence`.

Audit technique restant : le module mélange validation documentaire, règle clinique NSAID/GI basée sur mots-clés et contrôle comptable. Cible de consolidation : validation documentaire hors moteur clinique, comptabilité hors moteur clinique, medication safety dans le futur moteur pharmacologique structuré.

---

## LOT 5 — Imagerie panoramique

### Goal

Identifier le pipeline produit réel, supprimer les wrappers morts et préserver le chemin actif sans perte fonctionnelle.

### État

**SUPPRESSION DES WRAPPERS MORTS CERTIFIÉE. LOT DE PURGE FERMÉ.**

### Pipeline produit actif préservé

`backend/routers/ia.py` → `panoramic_service.detect_teeth_only()` → `sota_panoramic_service.py` → `panoramic_report_engine.py` → `PanoramicAnalysis`

### Classification finale

| Composant | Décision |
|---|---|
| `panoramic_service.py` | `KEEP / CONSOLIDATE` |
| `sota_panoramic_service.py` | `KEEP` |
| `panoramic_ai_advisor.py` | `DELETE` confirmé |
| `panoramic_expert_engine.py` | `DELETE` confirmé |
| `panoramic_vision_service.py` | `DELETE` confirmé |
| `panoramic_report_engine.py` | actif, transféré LOT 6, `REPLACE / CONSOLIDATE` |

### Preuves

- commit `b559a3dd681aa35de6bc773288409d087f615fe8` supprime réellement les trois wrappers ;
- `backend/tests/test_scientific_core_purge_contract.py` vérifie leur absence et scanne les références runtime interdites ;
- le seul consommateur révélé par le premier contrat était le test legacy de `PanoramicExpertEngine` dans `backend/tests/test_services_unit8.py` ; cette section auto-testant le moteur mort a été retirée, les tests céphalo du fichier ont été conservés ;
- pipeline produit actif conservé ;
- Digital Crown CI `34232806194` : **SUCCESS**.

**Conclusion prouvée :** les trois wrappers sont du code mort supprimé sans casser la CI principale ni le pipeline panoramique réellement servi.

---

## LOT 6 — Vision / Report

### Goal

Séparer observation/détection, interprétation clinique et recommandation, avec provenance explicite et absence de faux négatif implicite.

### État

**AUDIT TECHNIQUE TERMINÉ. `panoramic_report_engine.py` = `REPLACE / CONSOLIDATE`. BLOQUÉ SUR GATE MÉDICAL POUR CHANGEMENT SÉMANTIQUE.**

### Correction de périmètre

`backend/services/vision_service.py` et `backend/services/sota_vision_service.py` ne sont pas des moteurs panorama/report dormants. Ils participent au pipeline **céphalométrique actif** et sont transférés au LOT 7.

### Impact produit vérifié

- le backend génère/persiste le rapport panoramique ;
- après saisie des observations praticien, la route de régénération reconstruit `report_narrative` ;
- `frontend/src/features/panoramic/PanoramicStudio.tsx` charge les analyses persistées, envoie les findings praticien, régénère le rapport puis remplace l'analyse affichée ;
- `frontend/src/features/panoramic/ReportViewer.tsx` affiche `analysis.report_narrative` dans le produit ;
- le footer UI rappelle que le rapport assiste le diagnostic et que la décision finale appartient au praticien, mais ce disclaimer ne corrige pas une inférence clinique erronée en amont.

### Risques scientifiques prouvés dans le code

1. **Absence d'observation peut devenir langage de normalité/absence d'anomalie.**
   - sinus sans finding : `Aspect aéré sans anomalie majeure signalée...` ;
   - ATM sans finding : `Morphologie condylienne homogène sans anomalie majeure signalée.` ;
   - osseux sans finding : `Trame osseuse homogène sans lésion focale majeure signalée.`
   - donc donnée absente/non saisie ≠ explicitement distinguée d'un négatif confirmé.

2. **Une anomalie peut produire automatiquement conduite thérapeutique + CCAM.**
   - carie : évaluation/restauration + traitement restaurateur + code CCAM ;
   - lésion périapicale : vitalité/endo-retraitement ± chirurgie + code CCAM ;
   - autres mappings similaires présents.

### Couverture actuelle vérifiée

- `backend/tests/test_ia_router.py` couvre liste/suppression/persistance panorama et édition de report ;
- `backend/tests/test_ia_extended.py` couvre génération basique, anomalies manuelles, annotations visuelles et PDF ;
- `frontend/src/test/mobileM4BPanoramicContext.test.ts` couvre le bridge mobile et l'usage des analyses persistées ;
- **aucun de ces tests ne constitue un contrat de sécurité sémantique** contre `absence => normalité` ou `anomalie => traitement/CCAM automatique`.

### Gate médical requis

Aucune modification de ces règles n'a encore été appliquée. La politique clinique cible doit être approuvée explicitement avant changement du comportement médical.

**Option A — recommandée : fail-closed sémantique.**

- absence/non-saisie => `non documenté / non évalué`, jamais normalité implicite ;
- observation/anomalie => constat descriptif ;
- aucune conduite thérapeutique ni CCAM déduite automatiquement du seul label d'imagerie ;
- conduite clinique laissée au praticien, avec contexte/examen complémentaire lorsque nécessaire ;
- provenance et limitations conservées.

**Option B : conserver le comportement actuel** de normalité implicite et suggestions traitement/CCAM automatiques. Non recommandé car incompatible avec le Goal scientifique déjà verrouillé (`détection ≠ diagnostic`, `diagnostic ≠ traitement automatique`).

---

## LOT 7 — Céphalométrie

### Pipeline à auditer/revalider

`upload → ia.py → CephaloService → calibration → VisionEngine PyTorch 19 ou ONNX 38 → CephaloEngine → repository → édition frontend → refine → validator → PDF`

### Services actifs déjà reclassés

- `backend/services/vision_service.py` : multiplexer landmarks céphalo, chemin ONNX 38 avec fallback PyTorch 19 ; `KEEP / CONSOLIDATE` à auditer ;
- `backend/services/sota_vision_service.py` : dépendance active du pipeline céphalo ; `KEEP / CONSOLIDATE` à auditer ;
- `backend/services/cephalo_service.py` consomme `vision_engine` ;
- `backend/tests/test_vision_apex_provenance.py` protège la provenance du fallback et interdit la fabrication silencieuse des apex.

### Goal

- un seul pipeline landmarks réellement supporté ;
- calibration explicite ;
- prediction vs correction manuelle distinguées ;
- mesures déterministes à partir de landmarks validés ;
- pas de conclusion clinique automatique non sourcée ;
- validator avant export ;
- golden cases géométriques et cas limites.

### État

**PRÉ-AUDIT EFFECTUÉ, AUDIT COMPLET RESTANT.**

---

# PHASE 2 — CONSOLIDATION CIBLE

1. `PatientClinicalContext` : âge, poids/BSA lorsque pertinent, allergies, diagnostics/conditions, médicaments actifs, grossesse/âge gestationnel si pertinent, fonction rénale/hépatique, données biologiques utiles, indication actuelle.
2. `MedicationKnowledge` : DCI/ingrédients, classe/ATC, marques, dosage, forme, voie, présentation, disponibilité marché/pays, source/version/date d'effet.
3. `MedicationSafetyEngine` : allergie/cross-réactivité, interactions, duplications, contre-indications, limites de dose, rénal/hépatique, grossesse/allaitement, données manquantes, sévérité/management.
4. `DentalClinicalReasoningEngine` : diagnostic, symptômes, signes systémiques, indication, traitement étiologique, proposition explicable non autoritaire.
5. `ImagingPipeline` : acquisition, détection/landmarks, mesures, validation, interprétation séparée, rapport.
6. `CephaloEngine` : landmarks validés, calibration, mesures déterministes, provenance/version modèle, correction humaine traçable.

---

# PHASE 3 — MEDICATION INTELLIGENCE TARGET

Flow cible :

`médicament sélectionné` → résolution marque/DCI/ingrédients → contexte patient → formes/forces disponibles → données indispensables manquantes → checks allergy/DDI/rénal/hépatique/grossesse/duplication/dose → options pertinentes avec raison/source → validation praticien → override explicite/traçable lorsqu'autorisé.

Approche recommandée : hybride, avec terminologie/normalisation, labels structurés, catalogue officiel Maroc/AMM, base de connaissance clinique professionnelle à évaluer, orchestration/contextualisation Digital Crown.

Toute règle clinique implémentée doit revalider source primaire, version et applicabilité Maroc avant activation.

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
7. Chaque règle clinique sensible doit avoir source/version/provenance.
8. Conflit de sources : exposer l'incertitude.
9. Aucune suppression active sans preuve d'usage/remplacement.
10. Aucun déploiement Vercel sans autorisation explicite.
11. Ne pas mélanger ce chantier avec d'autres produits/projets.

**Proposition non encore approuvée, donc pas encore décision durable :** absence d'annotation imagerie => `non documenté/non évalué`, et label d'imagerie seul => aucune prescription de traitement/CCAM.

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

## Human gate actif — Vision / Report

Choix requis avant modification médicale de `panoramic_report_engine.py` :

- **A — recommandé :** fail-closed sémantique, absence = non documenté/non évalué, constat descriptif séparé, aucune conduite thérapeutique/CCAM automatique issue du seul label d'imagerie.
- **B :** conserver le comportement actuel.

Après décision :

1. écrire les tests négatifs/fail-closed avant code ;
2. modifier minimalement le report engine ;
3. tester endpoints + persistance + UI/report ;
4. CI ;
5. closeout LOT 6 ;
6. reprendre `Prescription / cohérence` avec un second gate clinique dédié aux valeurs synthétiques âge/poids ;
7. auditer céphalo ;
8. consolidation ;
9. rebuild ;
10. certification globale ;
11. closeout PR ;
12. merge ;
13. CI post-merge.

---

# CLOSEOUT ATTENDU

`validation → tests/golden cases → docs canoniques → cohérence roadmap → PR → CI → merge → post-merge CI`

Si CI en cours : ne pas attendre passivement. Faire tout travail indépendant, puis revérifier seulement quand nécessaire.

---

## REPÈRES DE REPRISE

- chantier : Digital Crown — Scientific Core Rebuild
- phase : Phase 1 nettoyage
- lot actif : Vision / Report
- Goal actif : séparer observation, interprétation clinique et recommandation sans casser le pipeline panorama actif
- repo : `hraaaaf/Digital_crown`
- branche : `refactor/scientific-core-purge`
- PR : `#371` draft
- HEAD code vérifié avant ce commit documentaire : `b559a3dd681aa35de6bc773288409d087f615fe8`
- CI principale de ce HEAD : `34232806194` — SUCCESS
- certification secondaire Patient Indicators : rouge sur timeout responsive/race 768, indépendant du panorama au diagnostic disponible
- dernière preuve : wrappers pano supprimés/certifiés ; `report_narrative` actif, persisté et affiché ; trou sémantique identifié et non couvert par tests
- blocage réel : human gate médical LOT 6
- Next exact : choix A/B du comportement du rapport puis tests fail-closed avant code
- Séquence restante : vision/report → prescription/cohérence → céphalo → consolidation → rebuild → certification → closeout → merge → post-merge
- déploiement : aucun déploiement Vercel autorisé dans ce chantier

**FICHIER CANONIQUE : `docs/SCIENTIFIC_CORE_REBUILD_ROADMAP.md`**
