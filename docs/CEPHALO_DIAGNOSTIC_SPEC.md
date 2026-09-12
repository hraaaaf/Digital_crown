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
**R10 registre normatif :** HEAD certifié `9ffd36306ec6fa09b71d590e078af01db67e6888` — CI #3431 SUCCESS — T2 #2411 SUCCESS — PR #431 — merge `d0bdfc4fa47346f27e432139e6785177da4deef3` — closeout R10 master `2ac6ac538c79eb95a3988f2e6da9854b76dbd422`  
**R11 diagnostic multiaxial :** HEAD certifié `6916dee975acb83d13acd540d5d2e4a8f839a478` — CI #3477 SUCCESS — T2 #2452 SUCCESS — PR #437 — merge `bc66b58b6ee4459362d3bd52150877908bdc996c`  
**Statut courant :** R11 implémentation FERMÉE ; closeout documentaire R11 en cours ; aucun déploiement ; R12 ne doit être ouvert que dans une nouvelle fenêtre après closeout final.

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

## R1 — CALIBRATION FIDUCIALE ASSISTÉE — CONTRAT HISTORIQUE

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

### État production contractuel

Le registre `validated_fiducial_profiles` est **vide par défaut**. Donc aucun profil de test ou hypothèse implicite ne peut activer `AUTO_VERIFIED` en production. L'architecture permet l'auto-vérification, mais son activation réelle exige l'introduction explicite d'un profil physique validé.

Cette section conserve le contrat scientifique/HFE R1. Elle n'est pas le pointeur de reprise courant ; le pointeur courant est R12 après fermeture documentaire de R11.

## R11 — DIAGNOSTIC MULTIAXIAL — CONTRAT FERMÉ

### Goal

`findings → hypothèses explicables`, avec contradictions et données manquantes visibles, sans conclusion patient non sourcée.

### Contrat certifié

- chaîne : `measurement evidence → contexte normatif optionnel → finding → diagnostic hypothesis → contradictions/missing data → validation praticien ultérieure` ;
- chaque finding R11 lie un `rule_id`, une `rule_version` et un `domain` exacts ;
- chaque hypothèse diagnostique R11 lie un `rule_id`, une `rule_version` et un `domain` exacts ;
- le registre production de règles diagnostiques reste **vide** tant qu'une règle clinique n'est pas source-lockée et revue ;
- une mesure indisponible ne peut pas devenir une évaluation normative `AVAILABLE` ;
- une évaluation normative indisponible ou inactive ne peut pas porter une classification patient ;
- un support/opposition doit être `AVAILABLE` ;
- un finding indisponible ne peut pas supporter ou opposer une hypothèse ;
- une référence déclarée manquante doit réellement être indisponible, sauf contexte normatif inactif explicitement bloqué ;
- supporting/opposing overlap est rejeté pour findings et hypothèses ;
- aucune option thérapeutique, indication ou prescription n'est introduite en R11.

### Source-lock / valeurs délibérément bloquées

`docs/CEPHALO_COM_VALUE_AUDIT.md` demeure l'autorité d'audit des valeurs COM/CRANIOM historiques. Les statuts `CONVENTIONAL_REFERENCE_ONLY`, `HISTORICAL_ONLY_BLOCKED`, `DIVERGENT_BLOCKED` et `CONSTRUCTION_BLOCKED` ne sont jamais promus en norme active. McNamara reste inert/scale-blocked ; les références actuelles ne sont pas activées pour classification patient.

### Preuve R11

- candidate HEAD : `6916dee975acb83d13acd540d5d2e4a8f839a478` ;
- CI #3477 : SUCCESS ;
- T2 Runtime Browser Certification #2452 : SUCCESS ;
- PR #437 : mergeable avant merge, 7 fichiers de scope, reviews 0, comments 0 ;
- merge implementation : `bc66b58b6ee4459362d3bd52150877908bdc996c` ;
- master post-merge implementation vérifié : `bc66b58b6ee4459362d3bd52150877908bdc996c` ;
- aucun déploiement.

## ROADMAP CANONIQUE

### R0 — Typed read-path
**État : FERMÉ.**  
**Preuve :** #400 certifiée et mergée sur master `5f453d906c0562e53c921c683bb16c1a6deb3536`.

### R1 — Calibration fiduciale assistée + provenance
**Goal :** automatiser la calibration lorsque la preuve physique est suffisante, avec confirmation praticien facultative et toujours disponible.

### R2 — Chaîne runtime scientifique traversante
**Goal :** chaîne unique `SourceEvidence → LandmarkEvidence → ConstructionEvidence → MeasurementEvidence`.

### R3 — Conventions géométriques / CRANIOM
**Goal :** supprimer toute ambiguïté avant extension des analyses.

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
**État : FERMÉ.**  
Source, population, contexte, version et règles de classification explicites ; aucune norme implicite.  
**Preuve :** candidate `9ffd36306ec6fa09b71d590e078af01db67e6888` ; CI #3431 SUCCESS ; T2 #2411 SUCCESS ; PR #431 ; merge `d0bdfc4fa47346f27e432139e6785177da4deef3` ; closeout master `2ac6ac538c79eb95a3988f2e6da9854b76dbd422`.

### R11 — Diagnostic multiaxial
**État : FERMÉ côté implémentation ; closeout documentaire en cours.**  
Findings puis hypothèses explicables ; contradictions et données manquantes visibles ; aucune conclusion non sourcée.  
**Preuve :** candidate `6916dee975acb83d13acd540d5d2e4a8f839a478` ; CI #3477 SUCCESS ; T2 #2452 SUCCESS ; PR #437 ; merge `bc66b58b6ee4459362d3bd52150877908bdc996c` ; master post-merge implementation identique.

### R12 — Problem list + objectifs
**NEXT.**  
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
- R10 HEAD `9ffd36306ec6fa09b71d590e078af01db67e6888` : CI #3431 SUCCESS ; T2 #2411 SUCCESS ; merge PR #431 `d0bdfc4fa47346f27e432139e6785177da4deef3` ; closeout master `2ac6ac538c79eb95a3988f2e6da9854b76dbd422`.
- R11 HEAD `6916dee975acb83d13acd540d5d2e4a8f839a478` : CI #3477 SUCCESS ; T2 #2452 SUCCESS ; merge PR #437 `bc66b58b6ee4459362d3bd52150877908bdc996c`.

## NEXT EXACT

Après merge du closeout R11 et vérification de master final :
1. ouvrir **une nouvelle fenêtre exclusivement R12** ;
2. lire `AGENTS.md` puis `STATE.md` puis ce fichier canonique ;
3. vérifier repo/master/HEAD/PR/CI avant toute modification ;
4. exécuter R12 seulement : `Problem list + objectifs` ;
5. chaque item doit référencer explicitement findings/diagnostics validés ; aucune indication ou option thérapeutique ne doit être introduite avant R13.

## SÉQUENCE RESTANTE

`R12 problem list/objectifs → R13 options thérapeutiques → R14 validation clinique → R15 studio UX/UI → R16 PDF → R17 certification/closeout`

## DÉPLOIEMENT

Aucun déploiement Vercel sans autorisation explicite.
