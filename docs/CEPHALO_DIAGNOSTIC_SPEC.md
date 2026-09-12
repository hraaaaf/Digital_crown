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
**R12 problem list + objectifs :** HEAD certifié `dc04d759191828afe85c643719165e7d4fcc916e` — CI #3500 SUCCESS — T2 #2465 SUCCESS — PR #441 — merge `02d4be759e4ddbc24293340c6c10848174ace07a`  
**R13 options thérapeutiques :** HEAD certifié `7fd6fdae604010510b74e5fe908dc76a425a71cf` — CI #3526 SUCCESS — T2 #2489 SUCCESS — PR #444 — merge `4740b463e49f8ddee9dbb704faaecd086c389beb`  
**R14 validation clinique finale :** HEAD certifié `017a7eaf7d293c5a7af19fb44987a2d5ff3f675c` — CI #3581 SUCCESS — T2 #2536 SUCCESS — PR #447 — merge `2f1f1d88bf6027988a398967bed5e65883b729aa`  
**Statut courant :** R14 implémentation certifiée et mergée ; closeout documentaire en cours ; aucun déploiement ; NEXT = fermer R14 puis reprendre R15 depuis master final vérifié.

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

Cette section conserve le contrat scientifique/HFE R1. Elle n'est pas le pointeur de reprise courant ; le pointeur courant est R15 après fermeture documentaire de R14.

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

## R12 — PROBLEM LIST + OBJECTIFS — CONTRAT FERMÉ

### Goal

`diagnostics validés → problem list traçable → objectifs traçables`, avec contradictions et données manquantes propagées sans transformation thérapeutique.

### Contrat certifié

- contrats dédiés et versionnés : `R12_PROBLEM_LIST_V1` et `R12_OBJECTIVE_V1` ;
- un problème R12 ne peut référencer que des diagnostics R11 existants en état `ACCEPTED` ou `EDITED` ;
- les findings dérivés doivent correspondre exactement aux findings supporting/opposing des diagnostics sélectionnés ;
- chaque finding utilisé doit être `AVAILABLE` et posséder une validation praticien explicite dont la dernière action est `ACCEPT` ou `EDIT` ;
- `finding_refs`, `missing_data_refs`, `contradictions` et `evidence_refs` doivent correspondre exactement à la provenance amont attendue ; aucune omission silencieuse n'est acceptée ;
- un objectif R12 ne peut dériver que de problèmes R12 validés (`ACCEPTED` ou `EDITED`) ;
- un objectif recopie exactement sa provenance vers problèmes, diagnostics, findings, missing data et contradictions ;
- les identifiants problem/objective doivent rester uniques par rapport au graphe amont ;
- le validateur R12 réexécute d'abord le contrat R11 : aucun contournement de la sécurité diagnostique ;
- le snapshot R12 refuse toute fuite de `treatment_options` ou `final_plans` ;
- aucune indication, contre-indication, option thérapeutique, mécanique, appareil ou prescription n'est introduite en R12 ;
- aucune règle clinique, norme, seuil ou valeur médicale nouvelle n'est activée par R12 ;
- aucune mesure n'est supprimée : `BLOCKED != DROPPED` reste obligatoire.

### Goldens / refus certifiés

- positif : lineage validée complète ;
- négatif : diagnostic non validé → problème refusé ;
- négatif : finding sans validation praticien → problème refusé ;
- missing data : propagation exacte obligatoire jusqu'au problème puis à l'objectif ;
- contradiction : propagation exacte obligatoire ;
- problème non validé → objectif refusé ;
- fuite de couche thérapeutique → refus ;
- champ thérapeutique additionnel sur contrat R12 → refus.

### Preuve R12

- branche implémentation : `feat/cephalo-r12-problem-list-objectives` ;
- candidate HEAD : `dc04d759191828afe85c643719165e7d4fcc916e` ;
- CI #3500 : SUCCESS ;
- T2 Runtime Browser Certification #2465 : SUCCESS ;
- PR #441 : 1 commit, 3 fichiers ajoutés, scope backend R12 uniquement ;
- reviews : 0 ; threads : 0 ; commentaires PR : 0 ;
- merge implementation : `02d4be759e4ddbc24293340c6c10848174ace07a` ;
- master post-merge implementation vérifié : `02d4be759e4ddbc24293340c6c10848174ace07a` ;
- UI : aucune modification ;
- déploiement : aucun.

## R13 — OPTIONS THÉRAPEUTIQUES — CONTRAT FERMÉ

### Goal

`objectifs R12 validés → indications/contre-indications sourcées → options thérapeutiques évaluables → sélection/rejet praticien audité`, sans prescription autonome ni plan final.

### Contrat certifié

- contrats versionnés : `R13_INDICATION_V1`, `R13_CONTRAINDICATION_V1`, `R13_TREATMENT_OPTION_V1` ;
- chaque critère thérapeutique lie explicitement `rule_id`, `rule_version`, `source_id`, `source_version`, contexte d'applicabilité et evidence requise ;
- le registre thérapeutique production est **vide par défaut** : aucune règle ou option clinique réelle n'est active sans source-lock et revue explicites ;
- une source thérapeutique enregistrée conserve un contexte immuable, une citation, un type, une revue traçable et un timestamp timezone-aware ;
- le contexte utilisé par un critère/une option doit respecter les valeurs d'applicabilité de toutes ses sources ; aucun simple match de clés ne suffit ;
- le validateur R13 réexécute d'abord R12 : aucun contournement de la chaîne diagnostique/problem-list/objectifs ;
- une option ne peut référencer que des objectifs R12 existants et validés (`ACCEPTED`/`EDITED`) ;
- provenance exacte obligatoire : `option → objectifs → problèmes → diagnostics/findings`, avec `evidence_refs`, `missing_data_refs` et `contradictions` sans omission ni ajout silencieux ;
- indication et contre-indication doivent correspondre exactement aux bindings du rule registry ;
- toute donnée manquante, contradiction, indication non satisfaite ou contre-indication non levée crée un `blocking_gate` explicite et maintient l'option `BLOCKED` ;
- une contre-indication n'est jamais supprimée, neutralisée ou ignorée silencieusement ;
- `EVALUABLE` signifie uniquement que les gates R13 sont satisfaits, jamais que l'option est prescrite ou choisie ;
- `CLINICIAN_SELECTED` / `CLINICIAN_REJECTED` exigent une décision praticien complète et une `ClinicianValidationEvidence` cohérente cible/action/clinicien/timestamp ;
- aucune sélection automatique, aucun plan final, aucun séquençage, aucune mécanique ou appareil imposé n'est introduit en R13 ;
- aucune mesure n'est supprimée : `BLOCKED != DROPPED` et la dette scientifique reste active.

### Goldens / refus certifiés

- positif : option synthétique entièrement sourcée et évaluée sur lineage R12 validée ;
- négatif : règle/source non enregistrée ou mauvais binding/version → refus ;
- contexte source incompatible → refus ;
- upstream objectif/finding non validé → refus via R12/R13 ;
- missing data → blocage explicite ;
- contradiction → blocage explicite ;
- indication non satisfaite → blocage ;
- contre-indication active/non levée → blocage ;
- provenance option inexacte → refus ;
- décision praticien incomplète/incohérente → refus ;
- validation de décision orpheline → refus ;
- source-lock : contexte immuable après enregistrement et revue timezone-aware obligatoire.

### Preuve R13

- branche implémentation : `feat/cephalo-r13-therapeutic-options` ;
- candidate HEAD : `7fd6fdae604010510b74e5fe908dc76a425a71cf` ;
- CI #3526 : SUCCESS ;
- T2 Runtime Browser Certification #2489 : SUCCESS ;
- PR #444 : 5 fichiers R13 backend/tests ; reviews 0 ; threads 0 ; commentaires PR 0 ;
- branche candidate avant merge : 9 commits ahead / 0 behind `master` ;
- merge implementation : `4740b463e49f8ddee9dbb704faaecd086c389beb` ;
- master post-merge implementation vérifié : `4740b463e49f8ddee9dbb704faaecd086c389beb` ;
- UI : aucune modification ;
- déploiement : aucun.

## R14 — VALIDATION CLINIQUE FINALE — CONTRAT FERMÉ

### Goal

`objets R13 valides → stratégie clinique finale structurée → validation/rejet praticien final audité`, sans choix thérapeutique autonome ni contenu clinique fabriqué.

### Contrat certifié

- contrat versionné : `R14_FINAL_CLINICAL_VALIDATION_V1` ;
- le validateur R14 réexécute d'abord R13, donc toute la chaîne R13 → R12 → R11 reste autoritaire ;
- provenance exacte obligatoire : stratégie R14 → options R13 → validations de décision d'option → critères indication/contre-indication + sources → objectifs R12 → problèmes → diagnostics/findings R11 → evidence/missing/contradictions ;
- toute provenance manquante, ajoutée ou altérée est refusée ;
- une option R13 `EVALUABLE` ne devient jamais automatiquement un plan : elle ajoute `clinician_selection_required` et maintient la stratégie R14 `BLOCKED` ;
- une option R13 `BLOCKED` propage exactement ses gates ; une option `CLINICIAN_REJECTED` reste bloquante ;
- `missing_data_refs` et contradictions sont recopiés exactement et deviennent des blockers explicites ;
- seule une option R13 `CLINICIAN_SELECTED` peut participer à une stratégie R14 non bloquée ;
- `AWAITING_CLINICIAN_VALIDATION` est explicitement non final ;
- `CLINICIAN_VALIDATED` / `CLINICIAN_REJECTED` exigent une `ClinicianValidationEvidence` résolue vers la stratégie exacte, avec cible/action/clinicien/timestamp cohérents et timezone-aware ;
- une validation finale orpheline, mal ciblée ou incohérente est refusée ;
- les états non finaux ne peuvent pas porter de faux champs d'audit final ;
- les champs de stratégie thérapeutique libre, séquençage ou détails de plan sont interdits à cette couche ;
- aucun registre thérapeutique réel, norme, seuil, indication ou source clinique nouvelle n'a été activé ;
- aucune mesure n'est supprimée : `BLOCKED != DROPPED` reste obligatoire ;
- aucune UI n'a été modifiée ; aucun déploiement n'a été effectué.

### Goldens / refus certifiés

- positif : stratégie finale synthétique issue d'une option R13 `CLINICIAN_SELECTED` + validation finale praticien exacte ;
- `EVALUABLE` → jamais de promotion automatique ;
- `EVALUABLE` ne peut être représenté qu'avec blocker explicite `clinician_selection_required` ;
- missing data et gates R13 doivent être préservés exactement ;
- contradiction explicite → propagation + blocage ;
- suppression silencieuse d'un missing ref → refus ;
- falsification de provenance finding → refus ;
- suppression de provenance validation de décision R13 → refus ;
- validation finale non résolue / mauvaise cible / orpheline → refus ;
- snapshot R13 invalide → refus car R13 est réexécuté ;
- champs free-text/sequencing → refus ;
- timestamp final sans timezone → refus.

### Preuve R14

- branche implémentation : `feat/cephalo-r14-final-clinical-validation` ;
- candidate HEAD certifié : `017a7eaf7d293c5a7af19fb44987a2d5ff3f675c` ;
- CI #3581 : SUCCESS ;
- T2 Runtime Browser Certification #2536 : SUCCESS ;
- Cabinet Upgrade PostgreSQL Certification #51 : SUCCESS ;
- PR #447 : 3 fichiers ajoutés, 827 additions, 0 suppression ; reviews 0 ; threads 0 ; commentaires PR 0 ;
- diff exact avant merge : 3 fichiers R14 uniquement ;
- merge implementation : `2f1f1d88bf6027988a398967bed5e65883b729aa` ;
- master post-merge implementation vérifié : `2f1f1d88bf6027988a398967bed5e65883b729aa` ;
- UI : aucune modification ;
- déploiement : aucun.

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
**État : FERMÉ.**  
Findings puis hypothèses explicables ; contradictions et données manquantes visibles ; aucune conclusion non sourcée.  
**Preuve :** candidate `6916dee975acb83d13acd540d5d2e4a8f839a478` ; CI #3477 SUCCESS ; T2 #2452 SUCCESS ; PR #437 ; merge `bc66b58b6ee4459362d3bd52150877908bdc996c` ; master post-merge implementation identique.

### R12 — Problem list + objectifs
**État : FERMÉ.**  
Chaque item référence explicitement les findings/diagnostics validés dont il dérive ; missing data et contradictions sont propagées fail-closed.  
**Preuve :** candidate `dc04d759191828afe85c643719165e7d4fcc916e` ; CI #3500 SUCCESS ; T2 #2465 SUCCESS ; PR #441 ; merge `02d4be759e4ddbc24293340c6c10848174ace07a` ; master post-merge implementation identique.

### R13 — Options thérapeutiques
**État : FERMÉ.**  
Options évaluables, jamais prescription autonome ; indications/contre-indications sourcées, gates explicites et décision praticien auditée.  
**Preuve :** candidate `7fd6fdae604010510b74e5fe908dc76a425a71cf` ; CI #3526 SUCCESS ; T2 #2489 SUCCESS ; PR #444 ; merge `4740b463e49f8ddee9dbb704faaecd086c389beb` ; master post-merge implementation identique.

### R14 — Validation clinique finale
**État : FERMÉ côté implémentation ; closeout documentaire en certification.**  
Stratégie finale impossible sans sélection R13 praticien préalable et validation/rejet final R14 traçable ; aucune prescription autonome.  
**Preuve :** candidate `017a7eaf7d293c5a7af19fb44987a2d5ff3f675c` ; CI #3581 SUCCESS ; T2 #2536 SUCCESS ; PR #447 ; merge `2f1f1d88bf6027988a398967bed5e65883b729aa` ; master post-merge implementation identique.

### R15 — Studio clinique UX/UI Digital Crown
Radio dominante, état scientifique compact, provenance/correction/calculabilité visibles ; cycle UX obligatoire complet.

### R16 — PDF / restitution
UI/API/PDF doivent restituer le même graphe et le même état validé.

### R17 — Certification / closeout
Code, tests, runtime, UX et docs canoniques concordants sur master.

## GATES SCIENTIFIQUES

Mesure : `landmarks définis → construction versionnée → formule testée → unité/calibration → source enregistrée → norme séparée → contexte explicite → absence = NOT_COMPUTABLE`.

Diagnostic : `règle versionnée/sourcée → supporting/opposing evidence → contradictions → cas goldens → validation praticien`.

Traitement : `diagnostic validé → données cliniques requises → indication/contre-indications sourcées → options → sélection praticien → validation clinique finale`. Jamais de prescription autonome.

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
- R12 HEAD `dc04d759191828afe85c643719165e7d4fcc916e` : CI #3500 SUCCESS ; T2 #2465 SUCCESS ; merge PR #441 `02d4be759e4ddbc24293340c6c10848174ace07a`.
- R13 HEAD `7fd6fdae604010510b74e5fe908dc76a425a71cf` : CI #3526 SUCCESS ; T2 #2489 SUCCESS ; merge PR #444 `4740b463e49f8ddee9dbb704faaecd086c389beb`.
- R14 HEAD `017a7eaf7d293c5a7af19fb44987a2d5ff3f675c` : CI #3581 SUCCESS ; T2 #2536 SUCCESS ; PostgreSQL #51 SUCCESS ; merge PR #447 `2f1f1d88bf6027988a398967bed5e65883b729aa`.

## NEXT EXACT

Après merge du closeout R14 et vérification de master final :
1. ouvrir **une nouvelle fenêtre exclusivement R15** ;
2. lire `AGENTS.md` puis `STATE.md` puis ce fichier canonique puis `docs/CEPHALO_MEASUREMENT_EVIDENCE_RECOVERY.md` puis `docs/handovers/2026-09-12-cephalo-r14-to-r15-handover.md` ;
3. vérifier repo/master/HEAD/PR/CI avant toute modification ;
4. exécuter R15 seulement : `Studio clinique UX/UI Digital Crown` ;
5. appliquer obligatoirement `BEFORE réel → Goal visuel → référence/mockup → implémentation → AFTER mêmes viewports 390/768/1280+ → comparaison → tests → score visuel` ;
6. exposer fidèlement les états R11/R12/R13/R14 sans inventer de contenu clinique ni simuler une validation praticien ;
7. ne pas démarrer R16 dans R15.

Dette séparée à vérifier au démarrage R15 : `.github/workflows/document-history-actions-visual-cert.yml` était déjà corrompu avant R14 et peut produire un workflow visuel sans jobs ; R14 ne l'a pas modifié.

## SÉQUENCE RESTANTE

`R15 studio UX/UI → R16 PDF → R17 certification/closeout`

## DÉPLOIEMENT

Aucun déploiement Vercel sans autorisation explicite.