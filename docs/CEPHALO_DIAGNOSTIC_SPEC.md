# DIGITAL CROWN — CÉPHALOMÉTRIE DIAGNOSTIQUE

**FICHIER CANONIQUE DE REPRISE**

**Runtime SRPose38 :** PR #388 — `4e3ec0c84b58893d19214268075333042c4021a4`  
**Fondation diagnostique :** PR #390 — `ce7cc5a17d0571290c0b762a553b4feaa534e026`  
**Registre normatif :** PR #391 — `1c055f817e38a694de1d47f8144fcb1d9eaa2e9d`  
**Intégrité inter-objets :** PR #392 — `1566f77ff5ee9d848f8e31787f92e542f16a38b7`  
**Adaptateur MeasurementEvidence :** PR #393 — `65349a62d4b132f6bd6c2cb15f3e52b38e5d38ab`  
**Matérialisation ConstructionEvidence :** PR #394 — `c647c0843b265eadf4a70652ae4608708f48d2be`  
**Frontière patient/cas :** PR #395 — `3e8e39eb88581bd461a8104b9fad96b82d65292a`  
**Persistence runtime evidence :** PR #397 — `7aa83d566c87db6796cddea5a1facd891f8b5896`  
**Calibration manuelle auditée :** PR #398 — `35f5eca034ab780e92aa877b1120fd4e6c3b3dce`  
**Corrections landmarks auditées :** PR #399 — merge `6dcdb18d364545a151f1e2a3fa01b1ce37a9494f`  
**Typed read-path :** PR #400 — HEAD certifié `b5f1d991ec1c954840c609dfcd5dcee8063ad9c1` — merge master `5f453d906c0562e53c921c683bb16c1a6deb3536`  
**PR active :** #406 — `feat/cephalo-auto-fiducial-calibration`  
**Statut :** R1 actif ; certification exact-head finale non acquise ; aucun diagnostic ni plan thérapeutique déclaré certifié.

## GOAL GLOBAL

`cas patient → image → 38 landmarks → constructions → mesures → analyses → findings → synthèse diagnostique → problem list → objectifs → options thérapeutiques → validation praticien → plan final`

## INVARIANT

`landmark != construction != measurement != interpretation != diagnosis != indication != treatment plan`

Une donnée manquante reste `UNKNOWN` / `NOT_COMPUTABLE`. Aucune norme, classe, croissance, indication ou traitement n'est deviné.

## GATE EXPERTS AVANT ENREGISTREMENT CANONIQUE

Toute décision significative qui modifie le contrat scientifique, clinique ou UX est revue avant d'être enregistrée comme règle canonique selon trois angles :
- **clinique / sécurité :** preuve suffisante, limites explicites, fail-closed ;
- **architecture / traçabilité :** source, version, auteur/acteur, révision et dépendances auditables ;
- **UX/HFE :** état, incertitude et action attendue immédiatement compréhensibles.

Une revue interne spécialisée n'est jamais présentée comme l'avis d'un expert humain externe. Une validation externe réelle reste un human gate explicite lorsqu'elle est nécessaire.

## DISCIPLINE UX/UI DIGITAL CROWN

Tout changement visuel du studio suit obligatoirement :

`BEFORE réel → Goal visuel → référence/mockup → vérification tokens → implémentation → AFTER mêmes viewports → comparaison → tests → score visuel/revue experte`

Règles :
- tokens existants de `frontend/src/features/ortho/cephaloTheme.ts` ;
- identité Digital Crown et glassmorphisme existant ;
- aucun mockup générique comme cible finale sans remappage exact aux tokens ;
- viewports **390 / 768 / 1280+** ;
- clavier/touch/lisibilité testés proportionnellement au risque ;
- couleurs réservées aux états système/scientifiques, jamais à un diagnostic non validé.

## ACQUIS VÉRIFIÉS

### SRPose38
- runtime CPU certifié ;
- ordre CL-Detection 38/38 documenté ;
- hash modèle et pipeline déterministes ;
- aucun fallback automatique n'est qualifié de preuve SRPose38.

### CRANIOM
Sources publiées enregistrées : DOI `10.1051/odfen/2010406` et `10.1051/odfen/2011104`.

Constructions versionnées :
- `CRANIOM_A_TO_N_VERTICAL_V1` ;
- `CRANIOM_B_TO_N_VERTICAL_V1` ;
- `CRANIOM_AB_PRIME_V1` ;
- `CRANIOM_S_TO_N_VERTICAL_DEPTH_V1`.

Les quatre mesures passent par `MeasurementEvidence`. Sans construction disponible et calibration vérifiée, elles restent `NOT_COMPUTABLE`.

### Graphe de preuve et persistence
- #395 impose même patient/cas et cohérence d'audit ;
- #397 persiste `_evidence_graph_v1` avec révision/historique ;
- #398 fournit la transition `MANUAL_TWO_POINT` auditée ;
- #399 conserve la provenance des corrections landmarks et `current_landmark_refs` ;
- #400 rend le graphe typé autoritaire à la lecture pour les quatre linéaires CRANIOM.

### R0 — typed read-path #400 — FERMÉ

Contrat vérifié :
- GET canonique unique ;
- typed `AVAILABLE` écrase une valeur legacy stale ;
- typed `NOT_COMPUTABLE` projette `None`, sans fallback legacy ;
- graphe malformed/incomplet → fail closed HTTP 409 ;
- comportement legacy uniquement lorsqu'aucun graphe typé n'existe ;
- l'ancien marqueur persistant `authority_status=PERSISTED_NOT_YET_READ_PATH` est retiré du chemin d'autorité ;
- calibration revision comprise dans la suppression de ce marqueur.

Preuve finale : HEAD `b5f1d991ec1c954840c609dfcd5dcee8063ad9c1` ; CI #3182 success ; T2 #2190 success ; Portability #500 success ; Onboarding Visual #309 success ; reviews 0 ; threads 0 ; merge master `5f453d906c0562e53c921c683bb16c1a6deb3536` vérifié.

## R1 — CALIBRATION FIDUCIALE ASSISTÉE

### Goal

Exploiter une réglette/fiducial visible avec automatisation maximale sans confondre détection géométrique et preuve d'échelle physique.

### Règle canonique

La confirmation praticien est **recommandée mais non obligatoire** lorsqu'une calibration automatique possède une preuve physique déterministe et franchit des gates objectifs versionnés.

Deux chemins vérifiés sont autorisés :

`détection → candidat → profil physique validé + gates objectifs → AUTO_VERIFIED → mm calculables → confirmation/modification praticien facultative`

ou

`détection/candidat insuffisant → CANDIDATE_UNVERIFIED → modification/calibration manuelle praticien → calibration vérifiée → mm calculables`

Une future confirmation explicite d'une calibration automatique doit rester distinguable de l'auto-vérification, par exemple `CLINICIAN_CONFIRMED`, sans effacer la provenance automatique initiale.

### Interdits

- une simple forme de réglette ne suffit jamais à `AUTO_VERIFIED` ;
- aucune distance physique n'est supposée silencieusement ;
- aucun seuil clinique global « magique » n'est codé dans le détecteur ;
- aucune mesure mm n'utilise `CANDIDATE_UNVERIFIED` ;
- aucune provenance automatique ne prétend `clinician_confirmed=true` ;
- aucune auto-calibration ne réétiquette ou reconstruit silencieusement les landmarks existants ;
- aucune révision calibration ne traverse silencieusement des findings/diagnostics/objets cliniques aval déjà présents.

### Fondement scientifique/HFE retenu

- DICOM PS3.3 §10.7 distingue l'espacement détecteur de l'espacement calibré et décrit `FIDUCIAL` comme une calibration reposant sur un objet visible de taille connue ;
- la validité d'une calibration fiduciale dépend de la géométrie du dispositif et du plan/profondeur pertinents ;
- les principes FDA Human Factors imposent un état de calibration et un feedback utilisateur explicites lorsque cette étape influence l'usage.

Conclusion canonique : la régularité des graduations est un signal géométrique ; l'échelle physique provient d'un **profil validé, versionné et traçable**, ou d'une calibration praticien.

### Contrat `AUTO_VERIFIED`

`ValidatedFiducialProfile` porte au minimum :
- `profile_id` ;
- `version` ;
- `known_tick_spacing_mm` ;
- `min_ticks` ;
- `max_spacing_deviation_ratio` ;
- `validation_reference`.

Le gate automatique exige :
1. profil exact ID/version disponible ;
2. source de validation physique non vide ;
3. nombre de graduations ≥ minimum du profil ;
4. dispersion géométrique ≤ tolérance versionnée du profil ;
5. ratio dérivé fini, positif et mathématiquement cohérent ;
6. provenance complète conservant profil, méthode détecteur, géométrie, tolérance et ratio.

Sans profil validé : `CANDIDATE_UNVERIFIED`.

### État production actuel

Le registre `validated_fiducial_profiles` est **vide par défaut**. Donc aucun profil de test ou hypothèse implicite ne peut activer `AUTO_VERIFIED` en production. L'architecture permet l'auto-vérification, mais son activation réelle exige l'introduction explicite d'un profil physique validé.

### Implémenté dans PR #406, en attente de certification finale

- `CalibrationCandidate` image-space uniquement ;
- retrait du `10 mm` hardcodé du détecteur ;
- `detect_mm_per_pixel()` historique ne produit plus de ratio automatique ;
- `process_new_radio()` persiste le candidat avec `mm_per_pixel=None` et `is_calibrated=False` ;
- gate `ValidatedFiducialProfile → AutoCalibrationDecision` ;
- états distincts `CANDIDATE_UNVERIFIED`, `AUTO_VERIFIED`, `CLINICIAN_CONFIRMED` ;
- provenance `AUTO_VERIFIED_FIDUCIAL_PROFILE` fail-closed ;
- registre de profils vide par défaut ;
- transition calibration-only préservant landmarks, constructions et `current_landmark_refs` ;
- blocage si objets cliniques aval existent ;
- recalcul des quatre linéaires uniquement après état vérifié ;
- endpoint explicite `POST /analyses/{analysis_id}/auto-calibrate` ;
- réponse API : confirmation praticien `required=false`, `recommended=true` ;
- tests candidat, détecteur, gate, registre, source typée, runtime, transition et frontière API ajoutés.

**Non déclaré acquis tant que la CI/T2 exact-head de #406 n'est pas verte.**

## ROADMAP CANONIQUE

### R0 — Typed read-path
**État : FERMÉ.**  
**Preuve :** #400 certifiée et mergée sur master `5f453d906c0562e53c921c683bb16c1a6deb3536`.

### R1 — Calibration fiduciale assistée + provenance
**Goal :** automatiser la calibration lorsque la preuve physique est suffisante, avec confirmation praticien facultative et toujours disponible.  
**Succès :** candidat détecté ; fail-closed sans profil ; `AUTO_VERIFIED` seulement sur profil/gates validés ; provenance persistée ; landmarks préservés ; quatre linéaires recalculés ; API claire ; fallback manuel intact ; UX certifiée.  
**Preuve requise :** tests synthétiques/absence/faux positifs/divergence/profile version ; tests de transition et relecture ; exact-head CI/T2 ; BEFORE/AFTER 390/768/1280+ ; revue experte.

Séquence restante R1 :
1. obtenir CI/T2 verts sur contrat backend/API ;
2. corriger toute régression observée ;
3. figer contrat frontend ;
4. capture BEFORE réelle ;
5. Goal visuel + référence alignée tokens ;
6. implémenter états `NON CALIBRÉ`, `CANDIDAT`, `AUTO_VÉRIFIÉ`, `CONFIRMÉ/MODIFIÉ` ;
7. conserver action de modification/calibration manuelle ;
8. AFTER 390/768/1280+ + comparaison + tests + score/revue ;
9. closeout #406, merge, vérification master.

### R2 — Chaîne runtime scientifique traversante
**Goal :** chaîne unique `SourceEvidence → LandmarkEvidence → ConstructionEvidence → MeasurementEvidence`.  
**Succès :** création, correction, calibration, recalcul et GET réutilisent la même preuve.  
**Preuve :** tests traversants DB/service/API + fail-closed sur références incohérentes.

### R3 — Conventions géométriques / CRANIOM
**Goal :** supprimer toute ambiguïté avant extension des analyses.  
**Succès :** landmarks, construction, convention, formule et source versionnés pour chaque mesure.  
**Points ouverts :** plan mandibulaire propre à chaque analyse ; ambiguïté `Go` ; `Gi/Gs` CRANIOM ; `A''B''` sans protocole NHP/regard horizontal.

### R4 — COM / CRANIOM complet
Compléter l'analyse sans convention implicite ; calibration vérifiée requise pour les linéaires.

### R5 — Steiner
Définition → construction → formule → source → tests ; norme patient séparée.

### R6 — Tweed / Merrifield
Même gate scientifique et traçabilité.

### R7 — Wits / Jacobson + Downs
Même gate scientifique ; aucune mesure si constructions ambiguës.

### R8 — McNamara
Séparer strictement mesure, norme et interprétation.

### R9 — Ricketts + tissus mous
Même gate ; provenance explicite des landmarks tissus mous.

### R10 — Registre normatif activable
Source, population, contexte, version et règles de classification explicites ; aucune norme implicite.

### R11 — Diagnostic multiaxial
Findings puis hypothèses explicables ; contradictions et données manquantes visibles ; aucune conclusion non sourcée.

### R12 — Problem list + objectifs
Chaque item référence explicitement findings/diagnostics validés.

### R13 — Options thérapeutiques
Options évaluables, jamais prescription autonome ; indications/contre-indications sourcées et sélection praticien.

### R14 — Validation clinique finale
Aucune synthèse/stratégie finale sans validation praticien traçable.

### R15 — Studio clinique UX/UI Digital Crown
Radio dominante, état scientifique compact, provenance/correction/calculabilité visibles ; cycle UX obligatoire complet.

### R16 — PDF / restitution
UI/API/PDF doivent restituer le même graphe et le même état validé.

### R17 — Certification / closeout
Code, tests, runtime, UX et docs canoniques concordants sur master.

## GATES SCIENTIFIQUES

Mesure : `landmarks définis → construction versionnée → formule testée → unité/calibration → source enregistrée → norme séparée → contexte explicite → absence = NOT_COMPUTABLE`.

Diagnostic : `règle versionnée/sourcée → supporting/opposing evidence → contradictions → cas goldens → validation praticien`.

Traitement : `diagnostic validé → données cliniques requises → indication/contre-indications sourcées → options → sélection praticien`. Jamais de prescription autonome.

## PREUVES CI HISTORIQUES

- #391 : CI `34471586594` success ; T2 `34471586570` success.
- #392 : CI `34472921729` success ; T2 `34472921733` success.
- #393 : CI `34474219020` success ; T2 `34474219021` success.
- #394 : CI `34474296352` success ; T2 `34474296300` success.
- #395 : CI `34476589446` success ; T2 `34476589386` success ; merge `3e8e39eb88581bd461a8104b9fad96b82d65292a`.
- #397 HEAD `a52fc93ec8cc37b72b8e9b66e48f5a26d38f91b0` : CI `34490188077` success ; T2 `34490188120` success ; merge `7aa83d566c87db6796cddea5a1facd891f8b5896`.
- #398 HEAD `e06af52d611ece465e5087b2c485784b6cf74d49` : CI `34498056894` success ; T2 `34498056887` success ; merge `35f5eca034ab780e92aa877b1120fd4e6c3b3dce`.
- #399 HEAD `e2c82aa8155a308b67d776388b6909b611a8c106` : merge `6dcdb18d364545a151f1e2a3fa01b1ce37a9494f`.
- #400 HEAD `b5f1d991ec1c954840c609dfcd5dcee8063ad9c1` : CI #3182 success ; T2 #2190 success ; Portability #500 success ; Onboarding Visual #309 success ; merge `5f453d906c0562e53c921c683bb16c1a6deb3536`.

## NEXT EXACT

1. certifier le HEAD backend/API de #406 ;
2. corriger si rouge puis recertifier ;
3. figer le contrat frontend sans inventer de profil physique ;
4. exécuter le cycle BEFORE → Goal visuel → référence/tokens → implémentation → AFTER 390/768/1280+ → comparaison/tests → score/revue ;
5. closeout #406 puis merge et vérification master ;
6. ouvrir R2 depuis master vérifié.

## SÉQUENCE RESTANTE

`R1 calibration fiduciale/provenance → R2 chaîne runtime traversante → R3 conventions géométriques/CRANIOM → R4 COM/CRANIOM → R5 Steiner → R6 Tweed/Merrifield → R7 Wits/Downs → R8 McNamara → R9 Ricketts/soft tissue → R10 registre normatif → R11 diagnostic multiaxial → R12 problem list/objectifs → R13 options thérapeutiques → R14 validation clinique → R15 studio UX/UI → R16 PDF → R17 certification/closeout`

## DÉPLOIEMENT

Aucun déploiement Vercel sans autorisation explicite.
