# REPO_MAP — Digital Crown, modules scientifiques (audit du dépôt réel)

Date d'audit : 2026-07-18. Méthode : lecture directe du dépôt (grep/glob),
aucune supposition non vérifiée. Toute absence de résultat est notée
explicitement "non trouvé" plutôt que déduite.

Repo racine : `C:\Users\lenovo\Documents\Cabinet\DigitalCrown`.

---

## 1. Modèles SQLAlchemy (`backend/models.py`, 1440 lignes, fichier unique — pas de package `models/`)

| Classe | Ligne | Notes |
|---|---|---|
| `DossierClinique` | `backend/models.py:294` | `__tablename__="dossiers_cliniques"`, 1:1 avec `Patient` |
| `CephaloAnalysis` | `backend/models.py:365` | `__tablename__="cephalo_analyses"` |
| `PanoramicAnalysis` | `backend/models.py:383` | `__tablename__="panoramic_analyses"`, docstring "Stockage des analyses radiographiques panoramiques (DENTEX IA)", champ `report_narrative` (`:392`) |
| `Medication` | `backend/models.py:402` | `__tablename__="medications"`, "Base de connaissance des médicaments avec score de fréquence" |
| `ClinicalCategory` | `backend/models.py:412` | catégorie de protocole de prescription |
| `ClinicalProtocol` | `backend/models.py:421` | "Protocoles de prescription par défaut par catégorie" |
| `ClinicalActCatalog` | `backend/models.py:438` | |
| `Acte` | `backend/models.py:329` | "Actes rattachés aux spécialités pour agenda, devis et **odontogramme**" — **pas de modèle `Odontogram` dédié**, l'odontogramme est dérivé côté UI (`Acte`/`ToothData`) |
| `DoctorPrescriptionPreference` | `backend/models.py:730` | `__tablename__="doctor_prescription_preferences"` |
| `DoctorMedicationHabit` | `backend/models.py:749` | |
| `ClinicalContraindication` | `backend/models.py:976` | "Antécédent → liste de molécules contre-indiquées" |
| `ClinicalDrug` | `backend/models.py:988` | "Molécule → noms commerciaux marocains, dosages, forme galénique" |
| `ClinicalProtocolDB` | `backend/models.py:1002` | "Procédure → molécules recommandées + conseil post-opératoire (versionnées en DB)" |
| `LabJob` | `backend/models.py:1119` | champ `tooth_number` (`:1131`), `status` enum incluant `PRESCRIPTION` (`:1135`) |
| `CatalogAct.RADIOGRAPHIE`, `.BILAN` | `backend/models.py:501`, `:503` | membres d'enum, pas des classes |
| `TreatmentMasterPlan` / `TreatmentPlanStep` | `backend/models.py:305`, `:316` | proche diagnostic/plan de traitement |

**Non trouvé** : aucune classe `Prescription`, `Allergy`, `Interaction`,
`Diagnosis`, `Odontogram`, `Tooth`, `Xray`, `Dicom`, `Report` par ce nom
exact — ces concepts sont modélisés comme champs/enums sur les classes
ci-dessus (une ordonnance est un document PDF généré via
`DocumentArchive`, pas une ligne DB dédiée).

## 2. Migrations Alembic (`alembic/versions/`, 7 fichiers)

| Fichier | Pertinent ? | Résumé |
|---|---|---|
| `74e675197637_add_medical_library_models.py` | Oui | "Add medical library models" ; crée `clinical_rules`, `diagnostic_templates`, `medicaments` (lignes 23, 35, 55) |
| `0ac66fa0bdb8_remove_color_ref_and_init_lab_jobs.py` | Oui | crée `clinical_drugs` (l.50), `medications` (l.75), `doctor_medication_habits` (l.244) |
| `8f6465e49d90_sync_db_and_models_after_god_file_split_.py` | Oui | altère `cephalo_analyses.is_calibrated`/`calibration_data`, drop/re-add `image_tracings_path` (l.176-184, 274-279) |
| `2872d2ae6349_add_superadmin_features.py` | Non | hors périmètre |
| `a1b2c3d4e5f6_add_user_id_to_bot_sessions.py` | Non | hors périmètre |
| `b2c3d4e5f6a7_add_patient_id_to_bot_sessions.py` | Non | hors périmètre |

Rappel `CLAUDE.md` : Alembic n'est **jamais auto-appliqué** ; le schéma
réel est géré par `create_all()` + `migrate_appointment_columns()`
(additif uniquement) dans le lifespan de `main.py`.

## 3. Routes FastAPI pertinentes

**`prescriptions.py`** (510 lignes, `prescription_router` + `actes_router`) :
`/search`, `/search/web`, `/suggest`, `/habits/suggest`, `/habits/details`,
`/habits/presets`, `/habits/record` (POST), `/habits/record-batch` (POST),
`/safety/check` (POST), `/smart-suggest/{patient_id}`,
`/agentic/assessment/{patient_id}`, `/agentic/design` (POST),
`/preferences` (POST/DELETE), `/certif-suggest/{patient_id}`, +
`actes_router` : `/catalog/search`, `/catalog/quick-add` (POST),
`/duration`, `/catalog/bundles` (POST), `/brain/summary`, `/` (POST),
`/{acte_id}` (PUT), `/{acte_id}/upload` (POST), `/patient/{patient_id}`
(`backend/routers/prescriptions.py:17-457`).

**`medications.py`** : `/search` (`:25`), `/validate` (`:34`).

**`clinical.py`** : `/pubmed-extract` (POST, `:12`).

**`clinical_data.py`** : `/contraindications` GET/POST (`:62,70`), DELETE
`/contraindications/{ci_id}` (`:78`) ; `/drugs` GET/POST/PUT/DELETE
(`:90,98,110,123`) ; `/protocols` GET/POST/PUT/DELETE
(`:135,143,154,166`).

**`medical_library.py`** : `/medicaments` GET/POST/DELETE (`:14,41,65`),
`/diagnostics` GET/POST/DELETE (`:86,114,143`), `/rules` GET/POST
(`:163,183`), `/rules/pediatric-guide` (`:203`), `/rules/pediatric-all`
(`:250`).

**`ia.py`** (céphalo + panoramique) : `/upload-radio` (`:53`),
`/analyses/{analysis_id}` GET/PUT (`:94,112`), `/upload-panoramic`
(`:126`), `/patients/{patient_id}/panoramic-analyses` (`:200`),
`/patients/{patient_id}/panoramic-comparison` (`:210`),
`/analyses/{analysis_id}/calibrate` (POST, `:231`),
`/generate-panoramic-report` (POST, `:268`),
`/panoramic/{analysis_id}/report` (PUT, `:322`),
`/patients/{patient_id}/cephalo-analyses` (`:343`),
`/cephalo/{analysis_id}` (DELETE, `:350`), `/panoramic/{analysis_id}/pdf`
(`:384`), `/panoramic/{analysis_id}` (DELETE, `:399`).

**`intelligence.py`** : `/patient/{patient_id}/upcoming-prescription`
(`:525`) — reste du fichier hors périmètre (analytics).

**Non trouvé** : `patients.py` n'a pas de route nommée
prescription/odontogramme/allergie.

## 4. Schémas Pydantic pertinents

`backend/schemas/clinical.py` : `DiagnosticSLM` (`:8`), `MeasureData`,
`DentalAnalysis`, `SkeletalAnalysis`, `EstheticAnalysis`,
`AnalysisMetrics`, `CephaloAnalysisOut` (`:62`), `LandmarkItem`,
`DDMComponent`, `ClinicalData`, `McNamaraProjections`,
`AnalysisMetadata`, `CephaloAnalysisResult` (`:129`), `AnalysisUpdate`,
`CephaloViewModel` (`:149`), `CephaloPDFRequest` (`:163`),
`CalibrationPoint/Request/Response`, `VisionResult`.

`backend/schemas/panoramic.py` : `BoundingBox`, `Finding`, `ToothObject`
(`:23`, redéfini `:63` avec `noqa: F811`), `FullAnalysis`,
`PanoramicAnalysisBase/Create/Out` (`:34,40,44`), `PanoramicAnalysis`
(`:88`), `PanoramicVisualAnnotation`, `PanoramicReportRequest/Edit`
(`:106,115`).

`backend/schemas/documents.py` : `MedicationItem` (`:10`),
`ToothTreatmentInfo` (`:35`), `ToothData` (`:41`), `MedicationOut`
(`:150`), `ClinicalProtocolOut` (`:165`), `PrescriptionLearnRequest`
(`:173`), `AIPrescriptionRequest` (`:201`).

**Point d'attention** : `ContraindicationOut`, `DrugOut`, `ProtocolOut`
(utilisés par les routes `clinical_data.py`) sont définis **en dur dans le
fichier de la route**, pas dans `backend/schemas/`
(`backend/routers/clinical_data.py:31,43,54`) — logique dupliquée /
mal placée à corriger lors d'une future tâche (hors périmètre de cette
mission).

## 5. Inventaire des services

| Fichier | Lignes | Classes/fonctions | Constantes numériques codées en dur (file:line) |
|---|---|---|---|
| `medication_dict.py` | 126 | `_load`, `_to_mg`, `_strengths_mg`, `_brand_root`, `search`, `_matching_records`, `validate_dosage` | aucune hors logique de parsing d'unité mg |
| `prescription_service.py` | 609 | `PrescriptionService` (`resolve_smart_prescription`, `learn_habit`, `record_medication_usage`, `get_personalized_suggestions`, `get_medication_details`, `_normalize_to_molecule`, `check_drug_interactions`, `check_safety`, `get_doctor_presets`, `delete_doctor_preset`, `get_doctor_habits_summary`, `_calculate_age`) | aucune signalée (délègue à `clinical_rules_engine`) |
| `prescription_agentic_service.py` | 82 | `PrescriptionAgenticService` (`generate_clinical_assessment`, `design_treatment_plan`, `_calculate_age`) | aucune |
| `clinical_coherence.py` | 160 | `ClinicalCoherenceService` (`_calculate_age`, `_check_ordonnance_coherence`, `_check_accounting_coherence`, `_is_antibiotic`, `_is_nsaid`, `_is_stomach_risk`, `_is_invasive_act`) | aucune signalée |
| `clinical_intelligence.py` | 321 | `_resolve_motifs`, `ClinicalIntelligenceService` (`get_patient_summary`, `get_full_diagnostic`, `_calculate_age`) | aucune signalée |
| `clinical_rules_engine.py` | 503 | `RuleWarning`, `ClinicalRulesEngine` (`analyze_case`, `_calculate_pediatric_dosage`, `_normalize_act_name`, `_get_alternative`) | `:191` `if val > 8.0:` ; `:277` "Amoxicilline 2g ou Clindamycine 600mg" (prophylaxie endocardite) ; `:365` "Clindamycine 600mg" (allergie pénicilline) ; `:390` "Saccharomyces boulardii 250mg" ; `:427,451,459` seuil pédiatrique `age < 15` ; `:466` `poids*50/2` "50mg/kg/j" ; `:468` `poids*15` "60mg/kg/j" ; `:470` `poids*10` "30mg/kg/j" ; `:29` liste de molécules interdites si allergie pénicilline |
| `cephalo_engine.py` | 706 | `CephaloEngine` (`_get_point`, `_get_clinical_angle`, `_get_orthogonal_projection`, `_evaluate_metric`, `calculate_ddm_reelle`, `_project_t1_growth`, `_project_t2_growth`, `calculate_metrics`) | `:14` `mm_per_pixel=0.1` par défaut ; `:132-140` règle DDM "2.5° = 1mm" ; `:300` norme Surplomb `2.25±0.75` ; `:303` norme Recouvrement `2.25±0.75` ; `:310` IMPA `90.0±5.0` plage `(80,100)` ; `:316` I/Francfort `107.0±5.0` plage `(97,120)` ; `:322` inter-incisif `131.0±10.0` plage `(120,142)` ; `:330` SNA `82.0±2.0` ; `:335` SNB `80.0±2.0` ; `:340` ANB `2.0±2.0` ; `:352` NLA `102.0±10.0` ; `:360` FMA `26.0±4.0` ; `:370-373` tuples de normes enfant/adulte (DecAB, SitA, SitB, ProfFac) |
| `cephalo_service.py` | 178 | `CephaloService` (`process_new_radio`, `refine_analysis`, `_calculate_complex_ddm`) | aucune signalée directement (délègue au moteur) |
| `cephalo_measure_registry.py` | 28 | `is_mm_metric`, `cephalo_unit` | classification d'unité uniquement |
| `cephalo_consistency_validator.py` | 272 | `_val`, `ValidationResult`, `CephaloConsistencyValidator` (`_iter_metrics`, `_check_unit_contradictions`, `_check_mm_bounds`, `validate`) | bornes de contrôle mm `:136-165` |
| `calibration_service.py` | 100 | `CalibrationService` (`detect_mm_per_pixel`) | aucune signalée dans cette passe |
| `bilan_ortho_engine.py` | 182 | `BilanOrthoEngine` (`generate_bilan`, `_generate_resume_cephalo`, `_generate_resume_moulages`, `_generate_synthese_diagnostique`, `_generate_plan_traitement`) | aucune (générateur de texte narratif) |
| `panoramic_service.py` | 338 | `_is_production`, `PanoramicEngine` (`_letterbox`, `_apply_clahe`, `detect_teeth_only`, `predict`, `_map_fdi_elite`, `_apply_nms`, `_run_simulation`) | taille image `1280x1280` (`:62`), seuils NMS/détection présents dans `predict`/`_apply_nms` (non individuellement cités, relecture dédiée nécessaire) |
| `panoramic_report_engine.py` | 297 | `PanoramicReportEngine` (`generate_markdown`, `_fmt_teeth_phrase`, `_teeth_list`, `_phrase_for`, `_append_normality`, `_build_synthesis`, `_build_recommendations`) | aucune (templating texte) |
| `panoramic_expert_engine.py` | 152 | `PanoramicExpertEngine` (`_build_clinical_phrase`, `generate_report`) | aucune |
| `panoramic_ai_advisor.py` | 49 | `PanoramicAIAdvisor` | aucune (fichier court) |
| `panoramic_vision_service.py` | 55 | `PanoramicVisionEngine` (`_apply_clahe`, `predict_abnormalities`) | aucune |
| `sota_panoramic_service.py` | 276 | `_is_production`, `SOTAPanoramicEngine` (`_load_model`, `_letterbox`, `_apply_clahe`, `analyze`, `_map_fdi_refined`, `_apply_smart_nms`, `_run_simulation`) | `1280x1280` letterbox |
| `sota_vision_service.py` | 159 | `SOTAVisionEngine` (`_initialize_engine`, `predict_landmarks`) | chemin modèle de repli vers dossier externe inexistant `DigitalCrown_SOTA` (`:51`) — mode SOTA désactivé si absent (`:68`) |
| `vision_service.py` | 258 | `VisionEngine` (`_initialize_engine`, `predict_landmarks`) | charge `ceph_weights.pth` depuis le dépôt vendored `cephld_cca` (`:63`) |
| `ai_advisor.py` | 208 | `ClinicalNorms` (`get`), `AIAdvisor` (`generate_diagnostic`, `_generate_nlg_report`) | table de normes via `ClinicalNorms.get(is_child)` — lecture dédiée nécessaire pour les valeurs exactes |
| `ai_coherence.py` | 135 | `AICoherenceService` | piloté par prompt LLM, pas de seuil clinique codé en dur |
| `treatment_plan_engine.py` | 139 | `TreatmentPlanEngine` (`generate_plan`, `_map_to_phase`, `_suggest_act`, `_generate_summary`) | aucune |
| `acte_classification.py` | 30 | `classify_acte_type` | aucune (helper court) |

## 6. Prompts LLM dans les fichiers à thématique clinique

- `backend/services/ai_coherence.py:40` — `prompt = f"""Tu es un assistant de vigilance clinique expert en odontologie (IAmina)."""` 
- `backend/services/prescription_agentic_service.py` — aucun prompt direct trouvé (délègue ailleurs).
- `backend/services/card_extractor.py:32` — prompt OCR carte de visite (hors périmètre clinique strict, signalé par le grep initial).
- `backend/services/bot/llm_parser.py:24` — `self.system_prompt = """Tu es l'assistant IA déterministe 'Crown Bot' d'un logiciel dentaire."""` (NLU du bot, limite du périmètre clinique car le bot manipule du contexte patient).
- `backend/deprecated/test_slm.py:52` — `SYSTEM_PROMPT = """Tu es un Expert Orthodontiste Senior au sein du Centre d'Orthodontie Moderne (COM)."""` — **dans `backend/deprecated/`, code mort**.
- **Non trouvé** : aucun prompt `Tu es`/`You are` dans `backend/routers/*.py`.

## 7. Générateurs PDF (`backend/services/generators/`, 14 fichiers `.py`)

`accounting_gen.py`, `bilan_gen.py`, `bilan_ortho_gen.py`, `cephalo_gen.py`,
`certificat_gen.py`, `document_layout_safety.py`,
`document_typography.py`, `installment_gen.py`,
`installment_receipt_gen.py`, `libre_gen.py`, `ordonnance_gen.py`,
`panoramic_elite_gen.py`, `panoramic_gen.py`, `report_gen.py`.

- Générateur d'ordonnance réel confirmé : **`ordonnance_gen.py`**
  (ReportLab, importé par `prescription_service`/routers).
- Code mort confirmé : `backend/templates/ordonnance_elite.html` existe
  sur disque mais **zéro référence** à la chaîne `ordonnance_elite` dans
  un `.py` sous `backend/` (déjà noté dans `CLAUDE.md`).

## 8. `backend/ai_models/` — tailles et usage runtime réel

| Sous-dossier/fichier | Taille | Référencé dans `backend/services`/`backend/routers` ? |
|---|---|---|
| `cephld_cca/` | 1.1G | **Oui** — `backend/services/vision_service.py:13` (`repo_path = ... "cephld_cca"`), charge `ceph_weights.pth` (`:63`). Modèle de landmarks céphalo réellement chargé. |
| `best.onnx` | 250M | Non trouvé — probablement artefact mort/obsolète |
| `best.pt` | 351M | Non trouvé — probablement artefact mort/obsolète |
| `panoramic_model.onnx` | 218M | **Oui** — `panoramic_service.py`, `sota_panoramic_service.py` |
| `panoramic_model.pt` | 110M | Non trouvé par nom exact (checkpoint d'entraînement co-localisé, probablement pas chargé directement) |
| `panoramic_model.pth` | 4.0K (fichier pointeur/stub) | Non trouvé par nom exact |
| `CL-Detection2023/` | 76M | Non trouvé — dépôt de recherche vendored, mort |
| `CLdetection2023-master/` | 28M | Non trouvé — dépôt vendored mort (confirmé aussi par `CLAUDE.md`, casse la limite de chemin Inno Setup) |
| `cephalometric-master/` | 2.1M | Non trouvé — dépôt vendored mort |
| `cephmark/` | 5.7M | Non trouvé — dépôt vendored mort |
| `dentex/` | 0 (dossier vide) | Non trouvé |
| `dentex_repo/` | 99M | Non trouvé — dépôt vendored mort |
| `model_audit.txt` | 4.0K | Doc de métadonnées : décrit `panoramic_model.onnx` comme un YOLO11x Ultralytics entraîné sur "dentex-dataset-1" (4 classes : Caries, Deep Caries, Impacted, Periapical Lesion) |

Corrobore exactement l'incident déjà documenté dans `CLAUDE.md`
(INSTALL-AUTOMATION-1) : ~1.7 Go de dépôts de recherche vendored jamais
chargés au runtime, exclus du packaging PyInstaller via
`DigitalCrown.spec::_collect_ai_models_datas()`.

## 9. `backend/tests/` — fichiers de test pertinents

`test_cephalo_engine_soft_tissue.py`, `test_cephalo_service_calibration.py`,
`test_cephalo_validator.py`, `test_clinical_data_router.py`,
`test_clinical_intelligence_service.py`, `test_clinical_v4.py`,
`test_prescription_safety_crosscheck.py`, `test_prescriptions_router.py`.

**Non trouvé** : aucun fichier de test nommé explicitement `medication`,
`panoramic`, `diagnosis` ou `odontogram` (couverture probablement
indirecte dans les fichiers `clinical_*`/`prescriptions_*` ci-dessus, non
vérifié plus avant).

## 10. Arborescence frontend

**`frontend/src/features/ortho/`** : `CephaloHistory.tsx`,
`cephaloMath.ts`, `cephaloRepository.ts`, `cephaloShared.ts`,
`CephaloStatsTable.tsx`, `cephaloTheme.ts`, `CephaloTracingLayer.tsx`,
`cephaloTypes.ts`, `cephaloUtils.ts`, `CephaloWorkspace.tsx`,
`DocumentArchiveManager.tsx`, `orthoExpertSystem.ts`, `components/`
(`AnatomicalTooth.tsx`, `Step1Cephalo.tsx`, `Step2BlockerModal.tsx`,
`Step2Occlusal.tsx`, `Step3Clinical.tsx`, `Step4Documents.tsx`,
`StepTab.tsx`, `SyncBadge.tsx`, `WedgeZone.tsx`),
`hooks/useCephaloPersistence.ts`, `stores/useOrthoStore.ts`, `tests/`.

**`frontend/src/features/panoramic/`** : `PanoramicHistory.tsx`,
`PanoramicStudio.tsx`, `ReportViewer.tsx`, `XRayCanvas.tsx`,
`stores/usePanoramicStore.ts`.

**`frontend/src/features/clinical-ref/`** : `ClinicalRefContent.tsx`,
`ClinicalRefSidebar.tsx`, `ClinicalRefTabs.tsx`, `ClinicalSoinMode.tsx`,
`EliteLibrary.tsx`, `EliteScienceHub.tsx`, `types.ts`, `useClinicalRef.ts`.

**`frontend/src/features/patients/`** : `AddPatientForm.tsx`,
`CsvImportModal.tsx`, `EditPatientForm.tsx`, `PatientDetails.tsx`,
`PatientDocuments.tsx`, `PatientList.tsx`, `components/`
(`ClinicalHub.tsx`, `InstallmentPlanModal.tsx`, `LegacyActeNotes.tsx`,
`MotifSelector.tsx`, `PatientFinances.tsx`, `PatientJourney.tsx`(+test),
`PatientScoreBadge.tsx`, `PatientSummaryHoverCard.tsx`,
`PayActeModal.tsx`, `QuickPayModal.tsx`, `RvgCard.tsx`,
`RvgUploadModal.tsx`, `wizards/` — `AssistantATM.tsx`,
`AssistantChirurgie.tsx`, `AssistantEndo.tsx`,
`AssistantExamenComplet.tsx`, `AssistantGeneral.tsx`,
`AssistantOrtho.tsx`, `AssistantParo.tsx`, `AssistantPatho.tsx`,
`AssistantPedo.tsx`, `AssistantProthese.tsx`).

**Grep en dehors de ces dossiers** :
- `"odontogram"` (insensible à la casse) trouvé uniquement dans
  `frontend/src/components/odontogram/` (`types.ts`,
  `OdontogramSVG.tsx`, `Odontogram.tsx`, `DocumentWithOdontogram.tsx`,
  `index.ts`), référencé depuis
  `frontend/src/features/patients/components/ClinicalHub.tsx`,
  `frontend/src/features/admin/DocumentHub.tsx`,
  `frontend/src/features/admin/AccountingStudio.tsx`,
  `frontend/src/features/admin/DocumentStudio/*`,
  `frontend/src/components/GuidedTour/tourConfig.ts`.
- `"prescription"` (insensible à la casse) : l'UI principale vit sous
  `frontend/src/features/admin/DocumentStudio/` (`Forms/PrescriptionForm.tsx`,
  `Forms/PrescriptionGuideModal.tsx`, `Forms/PrescriptionAgenticStudio.tsx`,
  `Forms/DrugRow.tsx`(+test), `Forms/QuickEntryBar.tsx`(+test),
  `DiagnosticEngine.ts`, `TreatmentPlanStudio.tsx`, `EliteAssistant.tsx`,
  `clinical_rules.ts`, `useDocumentGenerator.ts`) — **l'UI de
  prescription n'est ni dans `features/patients/` ni dans
  `features/ortho/`, mais dans `features/admin/DocumentStudio/`**, une
  feature distincte (cohérent avec le dossier additionnel donné en
  environnement de travail :
  `frontend/src/features/admin/SetupWizard/steps`).

## 11. `backend/data/` — données de référence

- `backend/data/medications_ma.json` — fichier JSON unique (0 saut de
  ligne, minifié, chargé via `json.load`), liste de dicts, **4234
  entrées** (base de médicaments marocains).
- **Non trouvé** : aucune table de normes céphalométriques ni de
  constantes de numérotation dentaire externalisées dans `backend/data/`
  — les normes céphalo sont codées en dur dans `cephalo_engine.py`
  (section 5 ci-dessus), la numérotation FDI est codée en dur dans
  `panoramic_service.py::_map_fdi_elite` / `sota_panoramic_service.py::_map_fdi_refined`.

---

## Zones d'incertitude

- Les seuils NMS/détection exacts de `panoramic_service.py::predict` /
  `_apply_nms` et `sota_panoramic_service.py::_apply_smart_nms` n'ont pas
  été extraits ligne par ligne (nécessite une lecture dédiée par
  `radiology-engineer` avant toute modification).
- La table `ClinicalNorms` de `ai_advisor.py` n'a pas été lue en détail
  (valeurs exactes par tranche enfant/adulte non extraites).
- La couverture de test réelle de `medications_ma.json`, du panoramique et
  du diagnostic (hors fichiers `clinical_*`/`prescriptions_*`) n'a pas été
  vérifiée assertion par assertion — seule l'existence des fichiers de
  test a été confirmée.
- `ContraindicationOut`/`DrugOut`/`ProtocolOut` définis en dur dans
  `backend/routers/clinical_data.py` plutôt que dans `backend/schemas/`
  constituent une dette d'architecture à signaler à
  `scientific-architect`, pas une action à corriger dans cette mission.
- `panoramic_model.pt` / `.pth` co-localisés avec le `.onnx` réellement
  chargé n'ont pas été confirmés comme totalement inertes (probable
  checkpoint d'entraînement, à vérifier avant suppression éventuelle).
