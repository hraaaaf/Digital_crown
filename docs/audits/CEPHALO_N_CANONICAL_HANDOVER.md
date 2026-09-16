# Digital Crown — Céphalo-N — Canonique de reprise

Statut : **CHANTIER ACTIF — NON TERMINÉ — ORTHO V2 PARKED**

Date d’état : 2026-09-16

Ce fichier est le **fichier canonique de reprise du chantier Céphalo-N**. Toujours le lire en premier, puis revérifier GitHub avant toute mutation : les SHA et CI ci-dessous sont des preuves historiques vérifiées, jamais une autorité temps réel.

---

## 1. Goal / Succès / Preuve

### Goal

Livrer un module Céphalo-N scientifiquement source-locké permettant, à partir d’une téléradiographie et des landmarks réellement disponibles :

1. un graphe patient unique de landmarks, corrigible/validable par le praticien ;
2. des mesures canoniques calculées une seule fois ;
3. des profils Steiner / Tweed / McNamara / Ricketts / COM qui référencent ces mesures ;
4. des normes/interprétations versionnées séparées de la géométrie ;
5. un tracé SVG synchronisé avec les mêmes primitives que les valeurs numériques ;
6. un fail-closed explicite si landmark, modalité, calibration ou source manque ;
7. une synthèse inter-analyses sans moyenne naïve ni diagnostic automatique ;
8. validation/correction praticien ;
9. un PDF cohérent avec l’état validé.

### Succès observable

Céphalo-N n’est clos que si :

- analyses/version/source explicites ;
- landmarks, plans, constructions et mesures source-lockés ou explicitement bloqués ;
- faux équivalents séparés ;
- profils d’analyse basés sur les `measurement_id` canoniques ;
- normes séparées/versionnées ;
- SVG et tables synchronisés ;
- absence de substitution silencieuse ;
- tests ciblés + non-régression DB/patients/documents/fonctions validées ;
- BEFORE/AFTER + validation visuelle si UI/PDF visuel modifié ;
- CI HEAD final verte ;
- merge + post-merge verts ;
- ce fichier à jour ;
- gate `CEPHALO_N_CLOSEOUT_VERIFIED` posé uniquement après ces preuves.

### Preuve attendue par lot

```text
code/contrat exact
→ tests ciblés
→ non-régression proportionnelle
→ compare avec master
→ CI exacte du HEAD
→ canonique à jour
→ merge avec accord utilisateur
→ post-merge
```

---

## 2. Priorité verrouillée

Le chantier actif est **Céphalo-N**.

`ORTHO_MODULE_V2.md` reste une roadmap future derrière :

```text
CEPHALO_N_CLOSEOUT_VERIFIED
        ↓
ORTHO_V2_D0
```

Il est interdit de commencer Ortho V2 avant closeout Céphalo-N réellement prouvé.

---

## 3. Architecture verrouillée

```text
LANDMARK GRAPH PATIENT UNIQUE
          ↓
LANDMARKS / CONSTRUCTIONS
          ↓
CANONICAL MEASUREMENT REGISTRY
          ↓
ANALYSIS PROFILES
          ↓
NORMS / INTERPRETATION
          ↓
SVG / TABLES / SYNTHESIS / PDF
```

Règles :

1. Une mesure mathématique n’appartient pas à une analyse.
2. Même géométrie + landmarks + modalité + signe + convention = une seule mesure canonique.
3. Une analyse référence des `measurement_id`; elle ne recopie pas la formule.
4. Géométrie, normes et interprétation restent séparées.
5. Fail-closed : aucune approximation silencieuse.
6. Un seul graphe patient par image.
7. Le SVG utilise exactement les mêmes primitives géométriques que les calculs.
8. La synthèse n’émet pas de diagnostic final automatique.

Registre runtime unique :

- `backend/services/cephalo_measure_registry.py`
- ne jamais créer un second registre canonique parallèle ;
- conserver `cephalo_unit()`, `is_mm_metric()` et les comportements legacy validés ;
- unité canonique inconnue = `None` / fail-closed ;
- `M_OVERBITE_V1` reste sans unité canonique verrouillée tant qu’une source exacte ne la verrouille pas ;
- registre normatif séparé du registre géométrique.

États canoniques utilisés :

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

Sources primaires : Steiner 1953 + Steiner 1959.

Profils :

- `STEINER_1953_CORE_V1`
- `STEINER_1959_CLINICAL_EXTENSION_V1`

Les mesures linéaires U1-NA / L1-NB nécessitent la surface faciale/coronaire exacte, pas seulement le bord incisif.

### Tweed

Sources primaires : Tweed 1946 / 1954.

Triangle : FMA + IMPA + FMIA.

Convention Digital Crown verrouillée :

```text
DC_TWEED_ANATOMICAL_FH_VARIANT = Porion anatomique → Orbitale
```

Ne jamais présenter cette convention comme reproduction stricte du Frankfort ear-rod historique de Tweed.

### McNamara

Source primaire du profil : McNamara JA Jr, 1984.

Profil : `MCNAMARA_1984_SINGLE_FILM_V1`.

Source verrouillée pour le lot N-perp :

- DOI `10.1016/S0002-9416(84)90352-X`
- PMID `6594933`
- cross-check secondaire : `PMC4436328`

Séparer strictement `Gn_anatomic` et `Gn_constructed`.

Airway = indicateur céphalométrique, jamais diagnostic ORL.

### Ricketts

Source principale : Ricketts 1981.

Profil : `RICKETTS_1981_SUMMARY_DESCRIPTIVE_V1`.

- facteurs latéraux séparés des facteurs PA/frontaux ;
- PA reste `BLOCKED_MODALITY_PA` sans vraie incidence frontale ;
- ne pas confondre Pt Ricketts, Xi, Pm, Sub.Go.-M, PTV, true Frankfort.

Dette de nomenclature conservée : `RICKETTS_FACIAL_DEPTH_DEG_V1` calcule `FH ↔ N-Pog`, géométrie correspondant au Facial Angle validé. Aucun renommage sans lot de compatibilité dédié.

### COM

Profil : `COM_DC_LEGACY_V1`.

COM est un composite interne Digital Crown, pas une méthode historique homogène d’un auteur unique.

---

## 5. Faux équivalents interdits

Ne jamais fusionner ni aliaser :

- `M_B_NPERP_MM_V1` ≠ `M_POG_NPERP_MM_V1`
- `M_U1_FH_DEG_V1` ≠ `M_FMIA_L1_FH_DEG_V1`
- `M_FACIAL_ANGLE_NPOG_FH_DEG_V1` ≠ `M_COM_S_NPERP_DEPTH_MM_V1`
- `M_FACIAL_AXIS_RICKETTS_DEG_V1` ≠ `M_FACIAL_AXIS_MCNAMARA_DEG_V1`
- `M_L1_EDGE_APOG_MM_V1` ≠ `M_L1_FACIAL_SURFACE_APOG_MM_V1`
- `M_FH_GOME_DEG_V1` ≠ `M_FH_SUBGO_M_DEG_V1`
- `Gn_anatomic` ≠ `Gn_constructed`
- `Pt_Ricketts` ≠ `PTM_McNamara`
- `Pog_hard` ≠ `Pog_soft`
- profil latéral ≠ incidence PA/frontale.

Aucun alias `PENDING_EQUIVALENCE` / `SOURCE_LOCK_REQUIRED` ne peut être promu par simple ressemblance de nom.

---

## 6. État GitHub vérifié au 2026-09-16

Repo : `hraaaaf/Digital_crown`

### PR #513 — MERGED

- merge SHA : `d762dec2487b42b6775990fdaa0b2f67b7a1a6f8`
- post-merge CI #4407 : **SUCCESS**
- scope : contrats/fixtures géométriques Céphalo.

### PR #515 — MERGED

- merge SHA : `8f74464998a721414e67957e0c9346f6a67efdb2`
- post-merge CI #4442 : **SUCCESS**
- scope : registre documentaire canonique + profils + Ortho V2 parked.

### PR #524 — MERGED — runtime registry

- titre : `feat(cephalo): add canonical runtime measurement registry`
- merge SHA : `e83b9713e80c94c42a16014d802be850c246adde`
- post-merge CI #4488 : **SUCCESS**
- registre canonique runtime matérialisé dans le registre existant ;
- helpers legacy conservés ;
- unité canonique inconnue fail-closed ;
- aucun faux alias introduit ;
- pas de DB, persistance, UI ou norme fusionnée dans ce lot.

Conclusion : **registre runtime canonique intégré et post-merge vérifié**.

### PR #527 — MERGED — mesures McNamara N-perp runtime

- titre : `feat(cephalo): add canonical McNamara N-perp runtime measures`
- branche historique : `feat/cephalo-n-missing-runtime-measurements`
- HEAD pré-merge certifié : `800729c55c4c256239a910c6aa48aade05c92526`
- merge commit réel : `2c36a04d90933d70fe8d501f44b9f8e04f7acca0`
- master vérifié sur ce merge commit après merge ;
- diff pré-merge final : 9 fichiers Céphalo attendus, +567/-36 ;
- 0 behind au gate final ;
- reviews : 0 ; threads de review : 0 au dernier audit pré-merge ;
- CI pré-merge #4552 : **SUCCESS** ;
- T2 Runtime Browser Certification #3419 : **SUCCESS** ;
- PR Merge Summary #20 : **SUCCESS** ;
- M6-I #2219 : **SKIPPED attendu** ;
- post-merge CI #4565 : **SUCCESS** ;
- post-merge Cabinet Upgrade PostgreSQL Certification #916 : **SUCCESS**.

Conclusion : **lot mesures manquantes N-perp intégré et post-merge vérifié**.

Master vérifié lors du closeout de ce lot :

```text
2c36a04d90933d70fe8d501f44b9f8e04f7acca0
```

Toujours revérifier le master réel avant toute nouvelle mutation.

---

## 7. Mesures activées par le lot #527

Seulement :

- `M_A_NPERP_MM_V1`
- `M_POG_NPERP_MM_V1`

Contrat scientifique verrouillé :

- Frankfort anatomique `Po → Or` ;
- N-perpendicular passant par `N` ;
- `Pog` = Pogonion osseux / hard tissue ;
- distance antéro-postérieure signée ;
- positif = antérieur ;
- négatif = postérieur ;
- calibration obligatoire pour une sortie en mm ;
- calibration absente/incohérente = fail-closed ;
- aucune équivalence avec `M_B_NPERP_MM_V1`.

Cycle runtime désormais préservé :

```text
création
→ édition landmarks
→ reconstruction evidence
→ calibration/recalibration
→ lecture du graphe actif
```

Le rebuild après édition des landmarks et la recalibration rematérialisent les constructions/mesures McNamara N-perp sans dupliquer les formules ni créer un registre parallèle.

---

## 8. Mesures encore bloquées / non autorisées

Restent explicitement bloquées tant que leurs prérequis scientifiques ne sont pas tous prouvés :

- L1-GoGn ;
- McNamara differential ;
- McNamara facial axis ;
- Sub.Go.-M ;
- toute mesure dépendant d’un `Go`, `Gn`, `Co`, `Pt`, `PTM` ambigu/non source-locké ;
- toute mesure PA/frontale sans vraie modalité PA ;
- tout alias fondé uniquement sur ressemblance de nom.

Gate obligatoire pour une nouvelle mesure :

1. source exacte ;
2. landmarks exacts disponibles ;
3. construction non ambiguë ;
4. unité verrouillée ;
5. calibration si distance réelle ;
6. ID canonique ;
7. calcul centralisé ;
8. tests numériques déterministes ;
9. tests négatifs/fail-closed ;
10. absence de duplication sémantique.

Un seul élément manquant → **BLOCKED**.

---

## 9. Roadmap restante Céphalo-N

### Prochain lot — SVG synchronisé

Goal : faire représenter visuellement exactement les primitives réellement calculées, sans ligne décorative ni géométrie parallèle.

Règles UI/UX obligatoires :

```text
BEFORE mêmes viewports
→ Goal écrit
→ mockup/référence
→ implémentation
→ AFTER mêmes viewports
→ comparaison visuelle
→ tests fonctionnels/non-régression
→ score visuel argumenté
```

Le lot n’est pas validable sans preuves visuelles BEFORE/AFTER si le rendu Céphalo est modifié.

### Puis — normes/interprétation

```text
geometry_result
!=
normative_context
!=
interpretation
```

Normes versionnées avec population/âge/sexe/source lorsque pertinent.

### Puis — synthèse inter-analyses

Domaines : sagittal/AP, vertical, transverse si PA réelle, dentaire, tissus mous, croissance/airway si réellement évalués.

Sorties : convergence, divergence, compensation, insuffisance de preuve, provenance.

Interdit : moyenne naïve / diagnostic final automatique.

### Puis — validation praticien + PDF

Le praticien doit pouvoir corriger landmarks, revoir mesures, valider/modifier la synthèse et produire un PDF reflétant exactement l’état validé.

### Enfin — closeout global

```text
tests ciblés
→ backend complet
→ frontend/build/runtime pertinent
→ non-régression DB/patients/documents
→ validation visuelle si UI
→ canonique final
→ merge
→ post-merge
→ CEPHALO_N_CLOSEOUT_VERIFIED
```

Ensuite seulement : Ortho V2.

---

## 10. Next exact

1. Fermer documentalement le lot #527 avec ce canonique actualisé.
2. Vérifier que le diff documentaire ne modifie que ce canonique.
3. Ouvrir une PR documentaire dédiée ; **ne pas la merger sans accord utilisateur explicite**.
4. En parallèle, auditer le rendu Céphalo actuel pour le prochain lot SVG.
5. Capturer/identifier le BEFORE aux mêmes viewports avant toute mutation visuelle.
6. Écrire le Goal SVG et la référence/mockup.
7. Seulement ensuite implémenter le SVG synchronisé.

---

## 11. Règles globales de non-régression

Toute modification doit préserver :

- base de données ;
- données patients ;
- documents ;
- comportements déjà validés ;
- compatibilité runtime existante sauf migration explicitement conçue et prouvée.

Aucune migration DB n’est autorisée par défaut : elle doit être démontrée nécessaire.

Aucun déploiement Vercel n’est pertinent pour Digital Crown local/on-premise.

Ne jamais déclarer « terminé », « validé », « production-ready » ni poser `CEPHALO_N_CLOSEOUT_VERIFIED` sans preuve exacte.

---

## 12. Sources canoniques du chantier

Documents à conserver cohérents :

- `docs/audits/CEPHALO_N_CANONICAL_HANDOVER.md` — reprise/état global ;
- `docs/audits/CEPHALO_CANONICAL_MEASUREMENT_REGISTRY.md` — identités de mesures ;
- `docs/audits/CEPHALO_ANALYSIS_MEASUREMENT_PROFILES.md` — composition des analyses ;
- `docs/audits/CEPHALO_N_MISSING_MEASUREMENTS_INVENTORY.md` — inventaire des mesures manquantes/blocked ;
- `docs/audits/ORTHO_MODULE_V2.md` — futur uniquement.

Le mapping local SRPose38 reste `LEGACY_LOCAL_MAPPING / SOURCE_LOCK_REQUIRED`. L’existence d’un canal ONNX ne suffit jamais à promouvoir un landmark clinique en vérité anatomique.

---

## 13. Handover compact

```text
CHANTIER
Digital Crown / Céphalo-N

CANONIQUE
docs/audits/CEPHALO_N_CANONICAL_HANDOVER.md

PRIORITÉ
Céphalo-N actif. Ortho V2 parked derrière CEPHALO_N_CLOSEOUT_VERIFIED.

ACQUIS
#513 merged d762dec2 + post-merge CI #4407 SUCCESS.
#515 merged 8f744649 + post-merge CI #4442 SUCCESS.
#524 merged e83b9713 + post-merge CI #4488 SUCCESS.
#527 merged 2c36a04d + post-merge CI #4565 SUCCESS + PostgreSQL #916 SUCCESS.
Registre runtime canonique unique conservé.
M_A_NPERP_MM_V1 et M_POG_NPERP_MM_V1 activées avec calibration fail-closed et lifecycle édition/recalibration préservé.

BLOQUÉ
L1-GoGn, McNamara differential, facial axis McNamara, Sub.Go.-M et toute géométrie dépendant de landmarks ambigus ou non source-lockés.

LOT SUIVANT
SVG synchronisé.

NEXT
Closeout documentaire #527 → audit/capture BEFORE SVG → Goal + référence → implémentation → AFTER mêmes viewports → comparaison/tests/score → normes → synthèse → validation praticien → PDF → closeout global.
```
