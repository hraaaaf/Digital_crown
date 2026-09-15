# Digital Crown — Céphalo-N — Canonique de reprise

Statut : **CHANTIER ACTIF — NON TERMINÉ — ORTHO V2 PARKED**

Date d’état : 2026-09-15

Ce fichier est le **fichier canonique de reprise du chantier Céphalo-N**. Il doit être lu en premier dans toute nouvelle conversation consacrée à la céphalométrie, puis l’état GitHub réel doit être revérifié avant toute modification.

---

## 1. Goal / Succès / Preuve

### Goal

Livrer dans Digital Crown un module Céphalo-N scientifiquement source-locké permettant, à partir d’une téléradiographie et des landmarks réellement disponibles :

1. de construire un graphe de landmarks patient cohérent et corrigible par le praticien ;
2. de calculer une seule fois les mesures canoniques ;
3. de faire référencer ces mesures par plusieurs profils d’analyses ;
4. d’appliquer des normes/interprétations versionnées sans mélanger géométrie et population normative ;
5. d’afficher un tracé SVG synchronisé avec les valeurs numériques ;
6. d’exposer les mesures non calculables en fail-closed ;
7. de synthétiser les convergences/divergences entre Steiner, Tweed, McNamara, Ricketts et COM sans moyenne naïve ;
8. de permettre validation/correction praticien ;
9. de générer un bilan/PDF céphalométrique cohérent avec l’état validé.

### Succès observable

Le chantier Céphalo-N ne sera considéré clos que si :

- les analyses retenues ont une composition/version/source explicite ;
- les landmarks, plans, lignes et constructions utilisés sont source-lockés ;
- les mesures canoniques nécessaires sont implémentées ou explicitement bloquées ;
- aucune mesure n’est dupliquée lorsque la géométrie est réellement identique ;
- les faux équivalents restent séparés ;
- les analyses référencent les `measurement_id` canoniques ;
- les normes sont versionnées et séparées de la géométrie ;
- le tracé SVG est synchronisé avec les mesures ;
- les données manquantes produisent un statut explicite et non une approximation silencieuse ;
- les tests de non-régression DB/patients/documents/fonctions validées passent ;
- les écrans/PDF concernés ont un BEFORE/AFTER et une validation visuelle lorsque l’UI est modifiée ;
- CI du HEAD final, merge et post-merge sont réellement verts.

### Preuve

Chaque lot significatif doit fournir :

- code ou contrat source exact ;
- tests ciblés ;
- non-régression proportionnelle au risque ;
- CI exacte du HEAD ;
- comparaison avec `master` ;
- mise à jour de ce fichier canonique ;
- merge + post-merge si le lot est terminé.

---

## 2. PRIORITÉ VERROUILLÉE

**Le chantier actif est Céphalo-N.**

`ORTHO_MODULE_V2.md` est une roadmap future seulement.

Gate obligatoire :

```text
CEPHALO_N_CLOSEOUT_VERIFIED
        ↓
ORTHO_V2_D0
```

Il est interdit de commencer l’implémentation Ortho V2 tant que Céphalo-N n’a pas été fermé avec :

```text
mesures
→ profils d’analyses
→ tracé SVG
→ normes / interprétation
→ synthèse
→ validation praticien
→ PDF / UI concernée
→ tests
→ CI
→ merge
→ post-merge
→ closeout canonique
```

---

## 3. Architecture Céphalo-N verrouillée

### 3.1 Mesures d’abord, analyses ensuite

```text
LANDMARKS / CONSTRUCTIONS
          ↓
CANONICAL MEASUREMENT REGISTRY
          ↓
ANALYSIS PROFILES
          ↓
NORMS / INTERPRETATION
          ↓
TRACING / TABLES / SYNTHESIS / PDF
```

Une mesure mathématique n’appartient pas à une analyse.

Si géométrie + landmarks + modalité + sens du signe + convention sont identiques, une seule mesure canonique est calculée puis référencée par plusieurs analyses.

### 3.2 Une téléradiographie / un graphe de landmarks patient

```text
Téléradiographie
→ détection landmarks disponibles
→ correction / validation praticien
→ LANDMARK GRAPH PATIENT UNIQUE
→ constructions
→ mesures canoniques
→ profils d’analyses sélectionnés
```

Changer d’analyse ne doit pas recréer un second SNA, ANB, FMA, etc.

### 3.3 Fail-closed

Aucune approximation silencieuse.

États attendus selon cas :

- `GEOMETRY_COVERED`
- `PRIMITIVE_AVAILABLE`
- `IMPLEMENTATION_MISSING`
- `BLOCKED_LANDMARK`
- `BLOCKED_MODALITY_PA`
- `SOURCE_LOCK_REQUIRED`
- `LEGACY_TO_AUDIT`
- `NOT_COMPUTABLE`

---

## 4. Analyses scientifiques retenues

### Steiner

Sources primaires :

- Steiner CC, *Cephalometrics for you and me*, Am J Orthod 1953;39(10):729-755, DOI `10.1016/0002-9416(53)90082-7` ;
- Steiner CC, *Cephalometrics in clinical practice*, Angle Orthod 1959;29:8-29, DOI `10.1043/0003-3219(1959)029<0008:CICP>2.0.CO;2`.

Versions :

- `STEINER_1953_CORE_V1`
- `STEINER_1959_CLINICAL_EXTENSION_V1`

Core 1953 validé : SNA, SNB, ANB, U1-NA°, U1-NA mm, L1-NB°, L1-NB mm, interincisif, SN-plan occlusal, SN-GoGn, L1-GoGn, U6-NA, L6-NB.

Extension 1959 : SND, Pog-NB, L1-D line linéaire/angulaire, séries incisives/molaires/superpositions.

Les mesures linéaires U1-NA/L1-NB nécessitent la surface coronaire/faciale exacte, pas seulement le bord incisif.

### Tweed

Sources primaires : Tweed 1946 / Tweed 1954.

Triangle : FMA + IMPA + FMIA.

Décision utilisateur verrouillée :

```text
DC_TWEED_ANATOMICAL_FH_VARIANT = Porion anatomique → Orbitale
```

Ne jamais présenter cette convention comme reproduction stricte du Frankfort historique 1954 au repère d’ear rod.

### McNamara

Source primaire : McNamara JA Jr, *A method of cephalometric evaluation*, Am J Orthod 1984;86(6):449-469, DOI `10.1016/S0002-9416(84)90352-X`.

Profil : `MCNAMARA_1984_SINGLE_FILM_V1`.

13 variables retenues :

1. A→Nperp ;
2. SNA ;
3. Co-Gn ;
4. Co-A ;
5. différentiel maxillo-mandibulaire ;
6. ANS-Me ;
7. angle mandibulaire ;
8. facial axis ;
9. Pog→Nperp ;
10. incisive supérieure→verticale de A ;
11. incisive inférieure→A-Pog ;
12. upper pharynx ;
13. lower pharynx.

Séparer `Gn_anatomic` et `Gn_constructed`.

Airway = indicateur céphalométrique, jamais diagnostic ORL.

### Ricketts

Source principale : Ricketts RM 1981, Angle Orthod 51(2):115-150, DOI `10.1043/0003-3219(1981)051<0115:PITCAO>2.0.CO;2`.

Profil : `RICKETTS_1981_SUMMARY_DESCRIPTIVE_V1`.

11 facteurs latéraux + 12 facteurs frontaux/PA.

Le PA/front reste `BLOCKED_MODALITY_PA` tant qu’une incidence frontale réelle n’existe pas.

Points/constructions à ne pas confondre : Pt Ricketts, Xi, Pm, Sub.Go.-M, PTV, true Frankfort.

Dette de nomenclature connue : le runtime `RICKETTS_FACIAL_DEPTH_DEG_V1` calcule la géométrie `FH ↔ N-Pog`, correspondant au **Facial Angle** validé. Ne pas migrer/renommer à la légère sans lot de compatibilité.

### COM

Pas de méthode historique homogène démontrée.

Profil : `COM_DC_LEGACY_V1`.

Traiter COM comme composite interne Digital Crown avec provenance par mesure, jamais comme analyse d’un auteur unique.

---

## 5. Faux équivalents interdits

Ne jamais dédupliquer :

- `B→Nperp != Pog→Nperp`
- `U1/FH != FMIA`
- `Ricketts Facial Angle != COM legacy facial depth`
- `Pt_Ricketts != PTM_McNamara`
- `Gn_anatomic != Gn_constructed`
- `Pog_hard != Pog_soft`
- `Go-Me != Go-Gn != Sub.Go.-M`
- `L1 edge→A-Pog != L1 facial-surface→A-Pog`
- `FH/Go-Me != FH/Sub.Go.-M`
- profil latéral `!=` incidence PA/frontale

---

## 6. État scientifique déjà acquis

Lots déjà réalisés/validés historiquement dans le chantier :

1. cartographie scientifique globale Steiner/Tweed/McNamara/Ricketts/COM ;
2. source-lock landmarks/plans ;
3. provenance SRPose38 ;
4. contrats géométriques ;
5. fixtures géométriques manuelles indépendantes du mapping SRPose ;
6. registre canonique de mesures ;
7. profils d’analyses documentaires.

Le modèle SRPose38 existant reste `LEGACY_LOCAL_MAPPING / SOURCE_LOCK_REQUIRED` : son repo source nomme ses 38 canaux `0..37` sans sémantique anatomique publique suffisante. Les nouvelles extensions cliniques ne doivent pas promouvoir arbitrairement ce mapping en vérité anatomique.

---

## 7. Mesures canoniques importantes déjà cartographiées

Exemples non exhaustifs :

### Sagittal

- `M_SNA_DEG_V1`
- `M_SNB_DEG_V1`
- `M_ANB_DEG_V1`
- `M_SND_DEG_V1`
- `M_A_NPERP_MM_V1`
- `M_B_NPERP_MM_V1`
- `M_POG_NPERP_MM_V1`
- `M_POG_NB_MM_V1`
- `M_MAXILLARY_CONVEXITY_A_NPOG_MM_V1`
- `M_FACIAL_ANGLE_NPOG_FH_DEG_V1`

### Vertical

- `M_SN_GOGN_DEG_V1`
- `M_FH_GOME_DEG_V1`
- `M_FH_SUBGO_M_DEG_V1`
- `M_ANS_ME_MM_V1`
- `M_PALATAL_PLANE_FH_DEG_V1`
- `M_OCCLUSAL_PLANE_SN_DEG_V1`

### Axes faciaux / longueurs

- `M_FACIAL_AXIS_RICKETTS_DEG_V1`
- `M_FACIAL_AXIS_MCNAMARA_DEG_V1`
- `M_CO_A_MM_V1`
- `M_CO_GN_ANATOMIC_MM_V1`
- `M_CO_GN_MINUS_CO_A_MM_V1`

### Dentaire / dento-alvéolaire

- `M_U1_NA_DEG_V1`
- `M_U1_NA_MM_V1`
- `M_U1_FH_DEG_V1`
- `M_U1_A_VERTICAL_MM_V1`
- `M_L1_NB_DEG_V1`
- `M_L1_NB_MM_V1`
- `M_L1_GOGN_DEG_V1`
- `M_IMPA_GOME_DEG_V1`
- `M_FMIA_L1_FH_DEG_V1`
- `M_L1_FACIAL_SURFACE_APOG_MM_V1`
- `M_L1_EDGE_APOG_MM_V1`
- `M_INTERINCISAL_DEG_V1`
- `M_OVERJET_MM_V1`
- `M_OVERBITE_V1`

### Tissus mous / airway

- `M_LI_EPLANE_MM_V1`
- `M_LS_EPLANE_MM_V1`
- `M_NASOLABIAL_ANGLE_DEG_V1`
- `M_UPPER_PHARYNX_MM_V1`
- `M_LOWER_PHARYNX_MM_V1`

---

## 8. État GitHub vérifié au moment de ce handover

**Toujours revérifier. Ne jamais supposer cet état encore actuel.**

Repo : `hraaaaf/Digital_crown`

### master

- HEAD vérifié : `d474ad18ba47d55a0d53f1f90e47a451f4dbac5e`

### PR #513 — fixtures géométriques

- branche : `feat/cephalo-source-locked-geometry-fixtures`
- HEAD : `0ba23f30f5b66df65654b5d48b6b9aa15f04f252`
- état : ouverte, non draft
- diff : 4 fichiers Céphalo uniquement
- dernière CI de ce HEAD :
  - CI #4360 SUCCESS
  - Cabinet PostgreSQL #760 SUCCESS
  - T2 #3245 SUCCESS
  - M6-I #2045 skipped attendu
- backend complet observé dans CI : **3528 passed / 10 skipped / 4 warnings**
- divergence actuelle vérifiée : **7 commits ahead / 2 commits behind master**

Conclusion : la PR est scientifiquement/testée sur son HEAD, mais doit être resynchronisée avec le `master` courant puis recertifiée avant merge.

### PR #515 — registre canonique + profils d’analyses

- branche : `audit/cephalo-canonical-measurement-registry`
- HEAD avant ajout de ce fichier : `7d1555b40c643517568d1c53b09abe7ad7af9548`
- état : draft ouverte
- dernière CI de ce HEAD :
  - CI #4358 SUCCESS
  - Cabinet PostgreSQL #758 SUCCESS
  - T2 #3243 SUCCESS
  - M6-I #2043 skipped attendu
- divergence actuelle vérifiée : **7 commits ahead / 2 commits behind master**

Cette PR contient :

- `CEPHALO_CANONICAL_MEASUREMENT_REGISTRY.md`
- `CEPHALO_ANALYSIS_MEASUREMENT_PROFILES.md`
- `ORTHO_MODULE_V2.md` en roadmap future uniquement
- ce fichier canonique après son ajout

---

## 9. Roadmap restante Céphalo-N

Ordre obligatoire :

### Étape 1 — Fermer PR #513

Goal : intégrer les contrats/fixtures géométriques source-lockés sur le `master` actuel.

Succès :

- resynchronisée avec master ;
- diff inchangé fonctionnellement ;
- CI exacte nouveau HEAD verte ;
- merge ;
- post-merge vert.

### Étape 2 — Fermer PR #515

Goal : intégrer le registre canonique + profils d’analyses après #513.

Succès :

- resynchronisée avec master incluant #513 ;
- aucune duplication de formule ;
- faux équivalents préservés ;
- CI exacte verte ;
- merge ;
- post-merge vert.

### Étape 3 — Matérialiser le registre machine-readable

Goal : faire du registre canonique la source runtime des `measurement_id` sans changer les valeurs existantes validées.

Inclure :

- définitions versionnées ;
- dépendances landmarks/constructions ;
- disponibilité ;
- statut fail-closed ;
- provenance ;
- pas encore de normes nouvelles non validées.

### Étape 4 — Implémenter les mesures manquantes réellement calculables

Prioriser seulement les mesures dont :

- source exacte verrouillée ;
- landmarks exacts disponibles/certifiés ;
- convention géométrique verrouillée ;
- calibration disponible pour les distances.

Toute mesure sans ces prérequis reste bloquée explicitement.

### Étape 5 — Tracé SVG complet et synchronisé

Goal : chaque mesure/plan/construction affichée doit provenir du même graphe géométrique que la valeur numérique.

Règles :

- familles de plans avec conventions visuelles stables ;
- aucune ligne décorative qui ne correspond pas au calcul ;
- tables + tracé synchronisés ;
- mesures non calculables non dessinées comme si elles existaient.

Tout changement UI/UX : BEFORE → Goal → mockup/référence → implémentation → AFTER mêmes viewports → comparaison/tests → score visuel.

### Étape 6 — Normes et interprétation versionnées

Séparer strictement :

```text
geometry_result
!=
normative_context
!=
interpretation
```

Normes doivent préciser si utile : âge, sexe, population, source/version, historique/contemporain, agrandissement éventuel.

Ne jamais appliquer une norme historique universellement sans contexte.

### Étape 7 — Synthèse inter-analyses

Goal : organiser les résultats en domaines :

- sagittal/AP ;
- vertical ;
- transverse si vraie modalité PA ;
- dentaire/dento-alvéolaire ;
- tissus mous ;
- croissance/airway si réellement évalués.

Moteur :

- convergence ;
- divergence ;
- compensation ;
- insuffisance de preuve ;
- provenance par finding.

Interdit : moyenne naïve ou diagnostic final automatique.

### Étape 8 — Validation praticien + PDF céphalo

Le praticien doit pouvoir :

- corriger landmarks ;
- revoir mesures ;
- accepter/modifier la synthèse ;
- produire un PDF reflétant exactement l’état validé.

Le PDF doit inclure seulement ce qui est réellement évalué, avec provenance/version lorsque pertinent.

### Étape 9 — Closeout Céphalo-N

Preuves :

- tests ciblés ;
- backend complet ;
- frontend/build ;
- tests runtime/browser pertinents ;
- non-régression DB/patients/documents ;
- validation visuelle si UI ;
- canonical à jour ;
- merge ;
- post-merge ;
- gate `CEPHALO_N_CLOSEOUT_VERIFIED` posé uniquement après preuve.

Ensuite seulement : `ORTHO_MODULE_V2.md` / ORTHO-V2-D0.

---

# 10. Handover compact

```text
HANDOVER — Digital Crown / Céphalo-N

REPO
hraaaaf/Digital_crown

FICHIER CANONIQUE
`docs/audits/CEPHALO_N_CANONICAL_HANDOVER.md`

PRIORITÉ
Céphalo-N est le chantier actif et NON TERMINÉ.
Ortho V2 est PARKED derrière `CEPHALO_N_CLOSEOUT_VERIFIED`.

GOAL
Finaliser le tracé céphalométrique Digital Crown : landmarks/constructions source-lockés → mesures canoniques → profils Steiner/Tweed/McNamara/Ricketts/COM → normes/interprétation versionnées → SVG synchronisé → synthèse → validation praticien → PDF → closeout.

ÉTAT SCIENTIFIQUE ACQUIS
- cartographie scientifique globale validée ;
- source-lock landmarks/plans ;
- provenance SRPose documentée ;
- contrats géométriques + fixtures ;
- registre canonique et profils d’analyses documentés ;
- Tweed DC conserve Po-Or anatomique ;
- McNamara/Ricketts/COM ont leurs distinctions verrouillées ;
- PA Ricketts bloqué sans vraie incidence PA.

ÉTAT GITHUB À REVÉRIFIER
Dernier master vérifié : d474ad18ba47d55a0d53f1f90e47a451f4dbac5e
PR #513 : head 0ba23f30f5b66df65654b5d48b6b9aa15f04f252, dernière CI verte, mais 2 commits derrière master.
PR #515 : head 7d1555b40c643517568d1c53b09abe7ad7af9548 avant mise à jour du canonique, dernière CI verte, mais 2 commits derrière master.

DERNIÈRE PREUVE #513
CI #4360 SUCCESS
PostgreSQL #760 SUCCESS
T2 #3245 SUCCESS
backend 3528 passed / 10 skipped

NEXT EXACT
1. Lire ce fichier canonique.
2. Vérifier master/HEAD/PR #513/#515/divergence/CI.
3. Resynchroniser #513 sur master sans modifier son scope.
4. Recertifier #513.
5. Si vert : merge #513 + post-merge.
6. Resynchroniser #515 sur nouveau master.
7. Recertifier/fermer #515.
8. Poursuivre mesures manquantes → registre runtime → SVG → normes → synthèse → PDF → closeout.

INTERDICTIONS
- ne pas commencer Ortho V2 ;
- ne pas inventer landmark/norme/mesure ;
- ne pas déduire PA depuis latéral ;
- ne pas casser DB/patients/documents ;
- ne pas renommer une dette runtime sans stratégie de compatibilité ;
- ne pas déclarer Céphalo-N terminé avant preuve post-merge.
```

---

# 11. Prompt prêt à coller dans une nouvelle conversation

```text
Tu es désormais l’agent responsable du chantier Digital Crown « Céphalo-N — Tracé céphalométrique complet ».

REPO
hraaaaf/Digital_crown

FICHIER CANONIQUE À LIRE EN PREMIER
docs/audits/CEPHALO_N_CANONICAL_HANDOVER.md

IMPORTANT
Céphalo-N est le chantier ACTIF et NON TERMINÉ.
Le chantier `ORTHO_MODULE_V2.md` existe mais il est PARKED. Il est interdit de commencer Ortho V2 avant un closeout Céphalo-N réellement vérifié avec le gate `CEPHALO_N_CLOSEOUT_VERIFIED`.

OBJECTIF
Finaliser le moteur et le tracé Céphalo-N de bout en bout :
LANDMARKS / CONSTRUCTIONS
→ CANONICAL MEASUREMENT REGISTRY
→ ANALYSIS PROFILES
→ NORMS / INTERPRETATION
→ SVG / TABLES
→ SYNTHÈSE INTER-ANALYSES
→ VALIDATION PRATICIEN
→ PDF
→ TESTS / CI / MERGE / POST-MERGE / CLOSEOUT.

ANALYSES RETENUES
- Steiner 1953 + extension clinique 1959
- Tweed DC avec Frankfort anatomique Po-Or décidé par le praticien
- McNamara 1984
- Ricketts 1981 latéral + frontal/PA seulement si modalité réelle disponible
- COM_DC_LEGACY_V1 comme composite interne, pas comme analyse historique homogène

ARCHITECTURE VERROUILLÉE
1. Une mesure canonique n’appartient pas à une analyse.
2. Si géométrie/landmarks/modalité/signe/convention sont identiques, elle est calculée une seule fois puis référencée par les analyses.
3. Les analyses possèdent leur profil de measurement_id et leurs normes/interprétations, pas des copies de formules.
4. Un seul graphe de landmarks patient par image, corrigible/validable par le praticien.
5. Fail-closed si landmark/modalité/calibration/source manque.
6. Géométrie, normes et interprétation restent séparées.
7. Le tracé SVG doit utiliser exactement les mêmes primitives que les calculs.
8. Le diagnostic final n’est jamais automatique ; la synthèse doit être validée/modifiée par le praticien.

FAUX ÉQUIVALENTS À NE JAMAIS FUSIONNER
- B→Nperp != Pog→Nperp
- U1/FH != FMIA
- Ricketts Facial Angle != COM legacy facial depth
- Pt_Ricketts != PTM_McNamara
- Gn_anatomic != Gn_constructed
- Pog_hard != Pog_soft
- Go-Me != Go-Gn != Sub.Go.-M
- FH/Go-Me != FH/Sub.Go.-M
- L1 edge→A-Pog != L1 facial-surface→A-Pog
- profil latéral != PA/frontale

TWEED
Conserver `DC_TWEED_ANATOMICAL_FH_VARIANT = Porion anatomique → Orbitale`.
Ne pas appeler cela une reproduction stricte du Tweed 1954 ear-rod Frankfort.

RICKETTS
Le runtime `RICKETTS_FACIAL_DEPTH_DEG_V1` calcule `FH ↔ N-Pog`, géométrie correspondant au Facial Angle validé. Ne pas renommer/migrer sans lot compatibilité séparé.
PA Ricketts reste `BLOCKED_MODALITY_PA` sans vraie incidence frontale.

SRPOSE38
Le mapping local 38 points est `LEGACY_LOCAL_MAPPING / SOURCE_LOCK_REQUIRED`.
Ne jamais promouvoir un nouveau landmark clinique uniquement parce qu’un canal ONNX existe.

AVANT TOUTE MODIFICATION
1. Lis entièrement `CEPHALO_N_CANONICAL_HANDOVER.md`.
2. Vérifie `master` exact.
3. Vérifie PR #513 et #515, leurs HEAD, divergence et CI exacte.
4. Ne suppose jamais que les SHA du fichier sont encore actuels.
5. Audite le repo avant d’ajouter un nouveau moteur ou une formule déjà existante.

DERNIER ÉTAT CONNU À VÉRIFIER
- master : d474ad18ba47d55a0d53f1f90e47a451f4dbac5e
- PR #513 : feat/cephalo-source-locked-geometry-fixtures, HEAD 0ba23f30f5b66df65654b5d48b6b9aa15f04f252, dernière CI verte, backend 3528 passed / 10 skipped, mais 2 commits derrière master lors du dernier compare
- PR #515 : audit/cephalo-canonical-measurement-registry, HEAD 7d1555b40c643517568d1c53b09abe7ad7af9548 avant mise à jour du canonique, dernière CI verte, mais 2 commits derrière master lors du dernier compare

NEXT EXACT
1. Resynchroniser proprement #513 sur le master courant sans changer son scope.
2. Recertifier le nouveau HEAD.
3. Si vert : merge #513 et vérifier post-merge.
4. Puis resynchroniser #515 sur le nouveau master.
5. Recertifier #515.
6. Si vert et cohérent : fermer #515.
7. Ensuite matérialiser le registre canonique machine-readable.
8. Implémenter seulement les mesures manquantes dont source + landmarks + convention + calibration sont verrouillés.
9. Construire le tracé SVG synchronisé.
10. Ajouter normes/interprétations versionnées.
11. Construire la synthèse inter-analyses.
12. Validation praticien + PDF.
13. Non-régression complète + closeout.
14. Seulement après preuve post-merge : poser `CEPHALO_N_CLOSEOUT_VERIFIED`, puis Ortho V2 peut commencer.

RÈGLE DE NON-RÉGRESSION
Toute modification doit préserver l’existant. Aucun changement ne doit casser, altérer ou rendre incompatibles la DB, les données patients, les documents, ni les fonctionnalités déjà validées. Toute modification significative inclut des vérifications adaptées avant validation/merge.

UI/UX
Pour tout changement visuel :
BEFORE → Goal écrit → mockup/référence → implémentation → AFTER mêmes viewports → comparaison + tests → score visuel.

EXÉCUTION
- avance sans demander validation quand le chemin est clair ;
- après 2 échecs similaires, change de stratégie ;
- CI pending n’arrête pas le travail indépendant ;
- pas de sleep/polling ;
- pas de Vercel sans autorisation explicite ;
- ne jamais déclarer terminé/validé sans preuve exacte.

COMMUNICATION
Résultat → preuve → prochaine action.
Fin de chaque message avec :
📍 REPÈRES
- chantier/lot
- Goal
- repo/branche/PR/HEAD
- CI/run + état
- dernière preuve
- blocage réel
- Next exact
- Séquence restante
- avancement global seulement si réellement mesurable
- effort suivant

Commence immédiatement par vérifier master, PR #513, PR #515, divergence et CI. Puis poursuis le chemin critique sans redemander ce qui est déjà décidé dans ce canonique.
```

---

## 12. Closeout de reprise

À chaque gros lot :

```text
validation
→ tests
→ mise à jour CEPHALO_N_CANONICAL_HANDOVER.md
→ cohérence docs scientifiques
→ Git / PR / merge
→ post-merge
→ lot suivant
```

Ne jamais poser `CEPHALO_N_CLOSEOUT_VERIFIED` sans preuve complète.
