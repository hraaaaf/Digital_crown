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
**PR active :** #400 — typed read-path  
**HEAD #400 avant cette mise à jour doc :** `203f7ba1893383bdfa5c9283c98cfeba4cbc9e1e`  
**CI #400 vérifiée sur ce HEAD :** CI #3153 success ; T2 #2164 success ; Portability #490 success ; Onboarding Visual #299 success ; M6-I #964 skipped.  
**Statut :** chantier actif ; aucun diagnostic ni plan thérapeutique déclaré certifié.

## GOAL GLOBAL

`cas patient → image → 38 landmarks → constructions → mesures → analyses → findings → synthèse diagnostique → problem list → objectifs → options thérapeutiques → validation praticien → plan final`

## INVARIANT

`landmark != construction != measurement != interpretation != diagnosis != indication != treatment plan`

Une donnée manquante reste `UNKNOWN` / `NOT_COMPUTABLE`. Aucune norme, classe, croissance, indication ou traitement n'est deviné.

## GATE EXPERTS AVANT ENREGISTREMENT CANONIQUE

Toute décision significative qui modifie le contrat scientifique, clinique ou UX doit être revue avant d'être enregistrée comme règle canonique.

La revue minimale comporte trois angles :
- **clinique / sécurité :** la donnée affichée ou utilisée est-elle réellement prouvée et correctement limitée ?
- **architecture / traçabilité :** source, version, auteur, révision et dépendances sont-ils auditables ?
- **UX/HFE :** l'état, le risque d'erreur et l'action attendue sont-ils immédiatement compréhensibles par le praticien ?

Une revue interne spécialisée ne doit jamais être présentée comme l'avis d'un expert humain externe. Si une validation externe réelle est requise, elle reste un human gate explicite.

## DISCIPLINE UX/UI DIGITAL CROWN

Tout changement visuel du studio suit obligatoirement :

`BEFORE réel → Goal visuel → référence/mockup → vérification tokens → implémentation → AFTER mêmes viewports → comparaison → tests → score visuel/revue experte`

Règles :
- utiliser les tokens existants de `frontend/src/features/ortho/cephaloTheme.ts` ;
- conserver l'identité Digital Crown et le glassmorphisme existant (`backdrop-blur`, surfaces translucides, bordures et ombres cohérentes) ;
- ne jamais adopter un mockup générique ou extérieur comme référence finale s'il ne respecte pas ces tokens ;
- viewports de certification : **390 / 768 / 1280+** ;
- clavier/touch et lisibilité doivent être testés proportionnellement au risque ;
- les couleurs décrivent des **états système/scientifiques**, pas des diagnostics non validés.

## LOTS

| Lot | Goal | État vérifié |
|---|---|---|
| 0 | Modèle de preuve clinique typé | EN COURS — contrats, resolver, patient/cas, constructions, mesures, persistence, calibration manuelle auditée et corrections landmarks auditées mergés ; read-path #400 en cours |
| 1 | Purger logique clinique non sourcée | FAIT — PR #371 |
| 2 | Runtime SRPose38 exact | FAIT — PR #388 |
| 3 | Contrat des 38 landmarks | EN COURS — ordre/identité 38/38 certifiés ; définitions opérationnelles partielles |
| 4 | Constructions géométriques | EN COURS — CRANIOM linéaire matérialisé ; conventions mandibulaires restantes |
| 5 | COM / CRANIOM | EN COURS — géométrie + références spécifiques inertes disponibles |
| 6 | Steiner | À FAIRE |
| 7 | Tweed/Merrifield | À FAIRE |
| 8 | Wits/Jacobson + Downs | À FAIRE |
| 9 | McNamara | À FAIRE |
| 10 | Ricketts + tissus mous | À FAIRE |
| 11 | Registre normatif | EN COURS — fondation inerte mergée ; aucune activation patient |
| 12 | Synthèse diagnostique | À FAIRE |
| 13 | Indications / options thérapeutiques | À FAIRE |
| 14 | Validation clinique + UX/PDF | À FAIRE |

## ACQUIS VÉRIFIÉS

### SRPose38
- runtime CPU certifié ;
- ordre CL-Detection 38/38 documenté ;
- hash modèle et pipeline déterministes ;
- le bridge persistence refuse qu'un fallback automatique soit qualifié de preuve SRPose38.

### CRANIOM
Sources publiées enregistrées :
- Part 1 DOI `10.1051/odfen/2010406` ;
- Part 2 DOI `10.1051/odfen/2011104`.

Constructions versionnées :
- `CRANIOM_A_TO_N_VERTICAL_V1` ;
- `CRANIOM_B_TO_N_VERTICAL_V1` ;
- `CRANIOM_AB_PRIME_V1` ;
- `CRANIOM_S_TO_N_VERTICAL_DEPTH_V1`.

Les quatre mesures correspondantes passent par `MeasurementEvidence`. Sans construction disponible et calibration prouvée, elles restent `NOT_COMPUTABLE`.

### Graphe de preuve et persistence
Le resolver impose l'existence/type des références. #395 impose même patient, même cas et audit praticien cohérent. #397 persiste `_evidence_graph_v1` dans `CephaloAnalysis.angles_data` avec révisions/historique.

### Calibration manuelle auditée #398
PR #398 est mergée au commit `35f5eca034ab780e92aa877b1120fd4e6c3b3dce`. Son HEAD final `e06af52d611ece465e5087b2c485784b6cf74d49` a passé CI `34498056894` et T2 `34498056887` avant merge.

Le POST canonique `/analyses/{analysis_id}/calibrate` persiste p1/p2, distance réelle, ratio, méthode/version, opérateur authentifié, timestamp UTC, géométrie et révision `MANUAL_CALIBRATION`. Une analyse legacy reste calibrable sans fabrication rétroactive de graphe.

### Audit corrections landmarks #399
PR #399 est mergée. HEAD final `e2c82aa8155a308b67d776388b6909b611a8c106`, merge master `6dcdb18d364545a151f1e2a3fa01b1ce37a9494f`.

Contrat acquis pour un graphe typé :
- landmarks inchangés → aucune fausse révision `LANDMARK_EDIT` ;
- correction d'un point SRPose → `MANUAL_CORRECTED`, coordonnées automatiques originales conservées, praticien + timestamp UTC ;
- correction répétée → même ancre automatique originale ;
- point omis → dépendances concernées `NOT_COMPUTABLE` ;
- `current_landmark_refs` empêche la résurrection silencieuse d'un point historique ;
- réintroduction d'un point précédemment omis reste auditée ;
- modification mm/pixel via le PUT générique interdite pour un cas typé ;
- couche clinique aval non vide bloque une vraie correction tant que l'invalidation explicite n'existe pas.

### Typed read-path #400 — en cours
Goal : lorsqu'un graphe typé existe, les quatre mesures CRANIOM versionnées sont lues depuis `MeasurementEvidence`, pas depuis une valeur legacy concurrente.

Contrat déjà implémenté sur le HEAD `203f7ba1893383bdfa5c9283c98cfeba4cbc9e1e` :
- typed AVAILABLE écrase une valeur legacy stale ;
- typed `NOT_COMPUTABLE` projette `None`, sans fallback legacy ;
- graphe incomplet/malformed → fail closed ;
- absence de graphe → comportement legacy inchangé ;
- façade GET canonique dédiée montée par remplacement ciblé.

La CI/T2 de ce HEAD est verte. Le lot n'est pas déclaré fermé tant que la sémantique `authority_status`, la preuve API/route unique, la doc finale et le merge ne sont pas clos.

## CALIBRATION FIDUCIALE / RÉGLETTE — RÈGLE CANONIQUE

Le service historique `calibration_service.detect_mm_per_pixel()` sait déjà rechercher une structure de réglette, mais son hypothèse actuelle de **10 mm entre graduations** ne constitue pas une preuve suffisante pour valider automatiquement une calibration clinique.

La nouvelle règle est :

`détection automatique → candidat de calibration → notification praticien → possibilité de modifier repères/distance → validation explicite praticien → calibration vérifiée → mesures mm calculables`

### Interdits
- une réglette détectée ne met jamais seule `is_calibrated=true` dans le chemin scientifique typé ;
- aucune distance réelle n'est supposée silencieusement ;
- aucune mesure linéaire typée n'utilise un ratio candidat non validé ;
- aucun faux niveau de confiance n'est affiché si le détecteur ne le produit pas réellement.

### Succès du lot calibration fiduciale
- le backend retourne un **candidat** avec repères détectés et distance image ;
- l'UI affiche clairement **Réglette détectée — non validée** ;
- le praticien peut **Valider** ou **Modifier le calibrage** ;
- la validation explicite crée une provenance auditée (méthode, géométrie, distance réelle, ratio, praticien, timestamp) ;
- un rejet ou une absence de réglette retombe sur la calibration manuelle à deux points ;
- sans calibration vérifiée : angles autorisés, mesures millimétriques `NOT_COMPUTABLE`.

Référence conceptuelle : DICOM `FIDUCIAL` décrit une calibration par mesure d'un objet visible de taille connue ; la validité géométrique dépend notamment du plan/profondeur du fiducial. La détection automatique n'abolit donc pas la nécessité d'un état explicite et traçable.

## ROADMAP CANONIQUE

### R0 — Fermer #400 typed read-path
**Goal :** une seule source scientifique de lecture pour les quatre mesures CRANIOM lorsqu'un graphe typé existe.  
**Succès :** GET canonique unique ; typed AVAILABLE/NOT_COMPUTABLE autoritaires ; malformed fail-closed ; legacy seulement sans graphe.  
**Preuve :** tests service + API + unicité route + CI/T2 exact-head + merge vérifié.

Actions restantes :
1. résoudre la sémantique `authority_status` sans inventer un statut contradictoire ;
2. ajouter la preuve API et l'unicité du GET canonique ;
3. relancer les tests ciblés et la certification exact-head ;
4. vérifier reviews/threads/mergeability ;
5. merge si vert ;
6. vérifier le HEAD master post-merge.

### R1 — Calibration fiduciale assistée + provenance complète
**Goal :** exploiter une réglette visible sans jamais transformer une détection automatique en validation clinique silencieuse.  
**Succès :** candidat détecté, notification, modification possible, validation praticien explicite, provenance persistée et liaison à `MeasurementEvidence`.  
**Preuve :** tests sur vraie/synthétique réglette contrôlée, faux positifs, absence de réglette, modification, validation, divergence et relecture persistée.

Séquence :
1. refactorer le détecteur pour retourner un candidat structuré au lieu d'un ratio implicitement validé ;
2. supprimer la promotion automatique de ce candidat en calibration vérifiée ;
3. exposer le candidat dans le contrat API ;
4. UI Digital Crown : notification glassmorphique non bloquante mais visible, boutons **Valider la calibration** / **Modifier le calibrage** ;
5. validation serveur auditée par le praticien ;
6. recalcul des mesures linéaires après validation ;
7. fallback manuel à deux points ;
8. tests + BEFORE/AFTER 390/768/1280+ + revue experte.

### R2 — Chaîne runtime scientifique traversante
**Goal :** une chaîne unique `SourceEvidence → LandmarkEvidence → ConstructionEvidence → MeasurementEvidence`.  
**Succès :** création, correction, calibration, recalcul et GET réutilisent la même preuve.  
**Preuve :** tests traversants DB/service/API + validation du graphe + fail-closed sur références incohérentes.

### R3 — Conventions géométriques / CRANIOM
**Goal :** supprimer toute ambiguïté avant extension des analyses.  
**Succès :** chaque mesure dispose de landmarks, construction, convention, formule et source versionnés.  
**Preuve :** références + tests géométriques + cas goldens.

Points ouverts connus : plan mandibulaire propre à chaque analyse ; ambiguïté `Go` ; `Gi/Gs` CRANIOM ; `A''B''` sans protocole NHP/regard horizontal.

### R4 — COM / CRANIOM complet
**Goal :** compléter l'analyse COM/CRANIOM sur des constructions et sources prouvées.  
**Succès :** aucune mesure patient ne dépend d'une convention implicite.  
**Preuve :** méthodes versionnées + cas de référence + calibration requise pour les linéaires.

### R5 — Steiner
Même gate : définition → construction → formule → source → tests → aucune norme patient avant validation normative séparée.

### R6 — Tweed / Merrifield
Même gate scientifique et traçabilité.

### R7 — Wits / Jacobson + Downs
Même gate scientifique ; aucune mesure si les constructions nécessaires restent ambiguës.

### R8 — McNamara
Même gate scientifique ; distinguer strictement mesure, norme et interprétation.

### R9 — Ricketts + tissus mous
Même gate scientifique ; provenance explicite des landmarks tissus mous.

### R10 — Registre normatif activable
**Goal :** séparer les valeurs patient des références normatives.  
**Succès :** source, population, âge/sexe si applicable, domaine d'usage, version et règle de classification sont explicites.  
**Preuve :** tests de contexte + cas limites + aucune norme implicite.

### R11 — Diagnostic multiaxial
**Goal :** transformer des mesures validées en findings puis hypothèses explicables.  
**Succès :** contradictions et données manquantes visibles ; aucune conclusion sans règle sourcée/versionnée.  
**Preuve :** cas goldens + tests de contradiction + validation clinique.

### R12 — Problem list + objectifs
**Goal :** structurer les problèmes et objectifs sans saut thérapeutique.  
**Succès :** chaque item référence explicitement les diagnostics/findings validés.  
**Preuve :** graphe de dépendance + validation praticien.

### R13 — Options thérapeutiques
**Goal :** produire des options évaluables, jamais une prescription autonome.  
**Succès :** indications, contre-indications, données manquantes, bénéfices/limites/risques et sélection praticien explicites.  
**Preuve :** règles sourcées + gates cliniques + cas goldens.

### R14 — Validation clinique finale
**Goal :** aucune synthèse ou stratégie finale sans validation praticien traçable.  
**Succès :** `ClinicianValidationEvidence` cohérent avec les objets validés.  
**Preuve :** tests de transitions, rejet, édition, validation et historique.

### R15 — Studio clinique UX/UI Digital Crown
**Goal :** rendre la preuve scientifique immédiatement lisible sans masquer la radiographie.  
**Succès :** radio dominante + barre d'état compacte + panneau contextuel ; calibration, provenance, correction et calculabilité visibles ; aucune couleur diagnostique trompeuse.  
**Preuve :** cycle UX obligatoire complet + captures 390/768/1280+ + clavier/touch + revue experte avant adoption.

Le studio doit rester strictement aligné sur les tokens `cephaloTheme.ts` et le glassmorphisme existant. Un mockup externe/générique ne peut pas être utilisé comme cible finale sans remappage complet sur ces tokens.

### R16 — PDF / restitution
**Goal :** le document restitue exactement l'état validé du graphe et du praticien.  
**Succès :** aucune divergence UI/API/PDF.  
**Preuve :** tests de génération, valeurs, provenance, `NOT_COMPUTABLE`, validations et snapshots visuels.

### R17 — Certification / closeout
**Goal :** fermer sur une preuve reproductible.  
**Succès :** code, tests, runtime observé, UX et docs canoniques concordent sur master.  
**Preuve :** CI/T2 verts, revues closes, merge, vérification post-merge, documentation cohérente.

## GATES SCIENTIFIQUES

Mesure : `landmarks définis → construction versionnée → formule testée → unité/calibration → source enregistrée → norme séparée → contexte explicite → absence = NOT_COMPUTABLE`.

Diagnostic : `règle versionnée/sourcée → supporting/opposing evidence → contradictions → cas goldens → validation praticien`.

Traitement : `diagnostic validé → données cliniques requises → indication/contre-indications sourcées → options → sélection praticien`. Jamais de prescription autonome.

## PREUVES CI

- #391 : CI `34471586594` success ; T2 `34471586570` success.
- #392 : CI `34472921729` success ; T2 `34472921733` success.
- #393 : CI `34474219020` success ; T2 `34474219021` success.
- #394 : CI `34474296352` success ; T2 `34474296300` success.
- #395 : CI `34476589446` success ; T2 `34476589386` success ; merge `3e8e39eb88581bd461a8104b9fad96b82d65292a`.
- #397 HEAD `a52fc93ec8cc37b72b8e9b66e48f5a26d38f91b0` : CI `34490188077` success ; T2 `34490188120` success ; merge `7aa83d566c87db6796cddea5a1facd891f8b5896`.
- #398 HEAD `e06af52d611ece465e5087b2c485784b6cf74d49` : CI `34498056894` success ; T2 `34498056887` success ; merge `35f5eca034ab780e92aa877b1120fd4e6c3b3dce`.
- #399 HEAD `e2c82aa8155a308b67d776388b6909b611a8c106` : merged via `6dcdb18d364545a151f1e2a3fa01b1ce37a9494f`.
- #400 HEAD avant mise à jour documentaire `203f7ba1893383bdfa5c9283c98cfeba4cbc9e1e` : CI #3153 success ; T2 #2164 success ; Portability #490 success ; Onboarding Visual #299 success ; M6-I #964 skipped.

## NEXT EXACT

1. fermer `authority_status` dans #400 ;
2. ajouter preuve API + unicité du GET canonique ;
3. tests ciblés puis exact-head CI/T2 ;
4. reviews/threads/mergeability ;
5. merge #400 si vert et vérifier master ;
6. ouvrir R1 calibration fiduciale assistée ;
7. revue experts avant contrat final ;
8. implémenter candidat → notification → modification → validation praticien → provenance ;
9. BEFORE/AFTER UX Digital Crown ;
10. poursuivre R2 puis R3 sans sauter les gates.

## SÉQUENCE RESTANTE

`#400 typed read-path → calibration fiduciale/provenance → chaîne runtime traversante → conventions mandibulaires/CRANIOM → COM/CRANIOM complet → Steiner → Tweed/Merrifield → Wits/Downs → McNamara → Ricketts/soft tissue → registre normatif → diagnostic multiaxial → problem list/objectifs → options thérapeutiques → validation clinique → studio UX/UI → PDF → certification/closeout`

## DÉPLOIEMENT

Aucun déploiement Vercel sans autorisation explicite.
