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
**PR active :** #399 — audit authentifié des corrections de landmarks  
**Statut :** chantier actif ; aucun diagnostic ni plan thérapeutique déclaré certifié

## GOAL GLOBAL

`cas patient → image → 38 landmarks → constructions → mesures → analyses → findings → synthèse diagnostique → problem list → objectifs → options thérapeutiques → validation praticien → plan final`

## INVARIANT

`landmark != construction != measurement != interpretation != diagnosis != indication != treatment plan`

Une donnée manquante reste `UNKNOWN` / `NOT_COMPUTABLE`. Aucune norme, classe, croissance ou indication n'est devinée.

## LOTS

| Lot | Goal | État vérifié |
|---|---|---|
| 0 | Modèle de preuve clinique typé | EN COURS — contrats, resolver, patient/cas, constructions, mesures, persistence et calibration auditée mergés ; correction-landmark audit en #399 ; read-path source de vérité restant |
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
Le resolver impose l'existence/type des références. #395 impose même patient, même cas et audit praticien cohérent. #397 persiste `_evidence_graph_v1` dans `CephaloAnalysis.angles_data` avec révisions/historique sans modifier le payload API public.

### Calibration auditée #398
PR #398 est mergée au commit `35f5eca034ab780e92aa877b1120fd4e6c3b3dce`. Son HEAD final `e06af52d611ece465e5087b2c485784b6cf74d49` a passé CI `34498056894` et T2 `34498056887` avant merge.

Le POST canonique `/analyses/{analysis_id}/calibrate` conserve le contrat public et persiste atomiquement : p1/p2, distance réelle, ratio, méthode/version, opérateur authentifié, timestamp UTC, géométrie et révision `MANUAL_CALIBRATION`. Une analyse legacy reste calibrable sans fabrication rétroactive de graphe.

### Audit corrections landmarks #399
Le lot en cours remplace le PUT canonique `/analyses/{analysis_id}` par une façade qui tire `clinician_id` du contexte authentifié. Pour un graphe typé :
- landmarks inchangés → aucune fausse révision `LANDMARK_EDIT` ;
- correction d'un point SRPose → `MANUAL_CORRECTED`, coordonnées automatiques originales conservées, praticien + timestamp UTC ;
- correction répétée → même ancre automatique originale ;
- point omis → dépendances concernées `NOT_COMPUTABLE` ;
- `current_landmark_refs` rend le jeu courant explicite pour empêcher la résurrection silencieuse d'un point historique ;
- calibration ultérieure conserve ce jeu courant explicite ;
- réintroduction d'un point SRPose précédemment omis est auditée comme correction, même si ses coordonnées redeviennent identiques à l'auto original ;
- modification mm/pixel via le PUT générique interdite pour un cas typé : passage obligatoire par la calibration auditée ;
- toute couche clinique aval non vide bloque une vraie correction plutôt que de devenir silencieusement périmée.

Cette section #399 reste **en certification CI**, pas déclarée mergée.

## GATES OUVERTS

- CI/T2 exact-head + reviews/threads de #399 puis merge ;
- faire du graphe persistant la source read-path des quatre mesures CRANIOM ;
- convention du plan mandibulaire propre à chaque analyse ;
- `Gi/Gs` CRANIOM absents comme landmarks SRPose38 distincts ;
- `A''B''` non calculable sans protocole NHP/regard horizontal ;
- aucune référence normative active pour classifier un patient.

## GATES SCIENTIFIQUES

Mesure : landmarks définis → construction versionnée → formule testée → unité/calibration → source enregistrée → norme séparée → contexte explicite → absence = `NOT_COMPUTABLE`.

Diagnostic : règle versionnée/sourcée + contradictions visibles + cas goldens + validation praticien.

Traitement : diagnostic validé + données cliniques requises + indication/contre-indications sourcées + sélection praticien. Jamais de prescription autonome.

## PREUVES CI

- #391 : CI `34471586594` success ; T2 `34471586570` success.
- #392 : CI `34472921729` success ; T2 `34472921733` success.
- #393 : CI `34474219020` success ; T2 `34474219021` success.
- #394 : CI `34474296352` success ; T2 `34474296300` success.
- #395 : CI `34476589446` success ; T2 `34476589386` success ; merge `3e8e39eb88581bd461a8104b9fad96b82d65292a`.
- #397 HEAD `a52fc93ec8cc37b72b8e9b66e48f5a26d38f91b0` : CI `34490188077` success ; T2 `34490188120` success ; merge `7aa83d566c87db6796cddea5a1facd891f8b5896`.
- #398 HEAD `e06af52d611ece465e5087b2c485784b6cf74d49` : CI `34498056894` success ; T2 `34498056887` success ; merge `35f5eca034ab780e92aa877b1120fd4e6c3b3dce`.
- #399 : exact-head final à certifier après consolidation du lot ; aucune preuve verte finale déclarée ici avant exécution.

## PLAN DE FERMETURE RESTANT

### 1. Fermer #399 — audit des corrections landmarks
**Goal :** chaque correction manuelle doit être authentifiée, traçable et non ambiguë.  
**Succès :** tous les appels `refine_analysis` et leurs tests utilisent le nouveau contrat ; aucune régression ; CI/T2 exact-head verts.  
**Preuve :** suite backend complète + CI/T2 + absence de review/thread bloquant + merge vérifié.

Actions :
- scanner tous les appels `refine_analysis` ;
- corriger en lot les tests historiques encore basés sur l'ancien contrat ;
- relancer une seule certification finale ;
- corriger toute défaillance réelle ;
- vérifier reviews/threads ;
- merger #399 si vert ;
- vérifier le HEAD master post-merge.

### 2. Basculer le read-path vers le graphe typé
**Goal :** supprimer la double vérité scientifique entre `angles_data` / `landmarks_data` legacy et le graphe d'évidence.  
**Succès :** lorsqu'un graphe typé existe, les quatre mesures CRANIOM sont lues exclusivement depuis `MeasurementEvidence`.  
**Preuve :** tests création → persistence → GET → valeurs typées ; `NOT_COMPUTABLE` reste `None` et ne retombe jamais sur une valeur legacy.

Règle de transition : le legacy peut rester une vue de compatibilité, mais ne doit plus être la source scientifique canonique d'un cas typé.

### 3. Fermer totalement la provenance des corrections manuelles
**Goal :** prouver qui a modifié quoi, quand, depuis quelle donnée originale.  
**Succès :** chaque correction conserve coordonnées avant/après, origine, `clinician_id`, timestamp, révision et historique ; aucune coordonnée corrigée n'est acceptée sans trace.  
**Preuve :** tests multi-révisions, suppression/réintroduction, correction répétée et relecture persistée.

### 4. Verrouiller la provenance de calibration
**Goal :** toute mesure millimétrique doit dépendre d'une calibration prouvée et reproductible.  
**Succès :** calibration manuelle persistée avec points, distance réelle, ratio, méthode/version, praticien et timestamp ; liaison explicite calibration → `MeasurementEvidence`.  
**Preuve :** reconstruction du ratio depuis les données persistées + tests de divergence + comportement fail-closed.

### 5. Certifier la chaîne runtime complète
**Goal :** obtenir une chaîne scientifique unique et traversante.  
**Succès :** `SourceEvidence → LandmarkEvidence → ConstructionEvidence → MeasurementEvidence` fonctionne sur création, modification, recalibration et relecture patient/cas.  
**Preuve :** tests traversants DB/service/API + validation `validate_case_evidence_graph` + comportement fail-closed en cas de référence incohérente.

### 6. Fermer les conventions céphalométriques restantes
**Goal :** supprimer toute ambiguïté de construction avant d'étendre les analyses.  
**Succès :** chaque mesure dispose d'une définition anatomique, construction géométrique, convention et source versionnées.  
**Preuve :** documentation + tests géométriques + références scientifiques.

Points ouverts connus :
- convention du plan mandibulaire propre à chaque analyse ;
- ambiguïté opérationnelle de `Go` ;
- `Gi/Gs` CRANIOM absents comme landmarks SRPose38 distincts ;
- `A''B''` non calculable sans protocole NHP/regard horizontal.

### 7. Construire le diagnostic clinique seulement après fermeture du socle
**Goal :** passer de mesures prouvées à une synthèse clinique explicable sans raccourci thérapeutique.  
**Succès :** analyses → findings → hypothèses → problem list → objectifs → options, avec provenance et validation praticien.  
**Preuve :** règles versionnées/sourcées, cas goldens, contradictions visibles, validation praticien obligatoire.

Contraintes :
- aucune norme patient activée avant validation scientifique de sa source, population et domaine d'usage ;
- aucun seuil céphalométrique isolé ne déclenche automatiquement un traitement ;
- aucun plan final sans `ClinicianValidationEvidence` cohérent.

### 8. Certification et closeout final
**Goal :** fermer le chantier sur une preuve reproductible, pas sur une impression de solidité.  
**Succès :** code, tests, runtime observé et docs canoniques concordent sur master.  
**Preuve :** tests backend complets + CI/T2 verts + documentation cohérente + merge + vérification post-merge.

Ordre de closeout :
`validation → docs canoniques → cohérence → roadmap/statut réellement vérifié → Git/merge → post-merge → lot suivant`.

## NEXT EXACT

1. terminer le scan global des appels `refine_analysis` sur #399 ;
2. corriger en lot tous les tests historiques incompatibles avec le contrat d'audit ;
3. produire un HEAD final unique ;
4. certifier CI/T2 exact-head ;
5. si échec : diagnostiquer → corriger → tester → relancer ;
6. si vert : vérifier reviews/threads → merge #399 → vérifier master ;
7. rebaseliner le lot `read-path typé` sur master ;
8. certifier création → persistence → GET sans fallback legacy ;
9. poursuivre la chaîne runtime complète puis les conventions mandibulaires.

## SÉQUENCE RESTANTE

`#399 audit landmarks → read-path source-of-truth → provenance manuelle/calibration complète → chaîne runtime traversante → conventions mandibulaires/CRANIOM → COM/CRANIOM complet → Steiner → Tweed/Merrifield → Wits/Downs → McNamara → Ricketts/soft tissue → diagnostic multiaxial → problem list/objectifs → options → validation clinique → UX/PDF → certification/closeout`

## DÉPLOIEMENT

Aucun déploiement Vercel sans autorisation explicite.
