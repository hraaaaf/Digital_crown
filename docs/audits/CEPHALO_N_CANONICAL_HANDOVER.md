# Digital Crown — Céphalo-N — Canonique de reprise

Statut : **CHANTIER ACTIF — NON TERMINÉ — ORTHO V2 PARKED**

Date d’état : 2026-09-15

Ce fichier est le **fichier canonique de reprise du chantier Céphalo-N**. Toujours le lire en premier, puis revérifier GitHub avant toute mutation : les SHA et CI ci-dessous sont des preuves historiques/snapshots, jamais une autorité temps réel.

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
- ce fichier mis à jour ;
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

Core documenté : 13 mesures. Extension 1959 : 6 références supplémentaires.

Les mesures linéaires U1-NA / L1-NB nécessitent la surface faciale/coronaire exacte, pas seulement le bord incisif.

### Tweed

Sources primaires : Tweed 1946 / 1954.

Triangle : FMA + IMPA + FMIA.

Décision Digital Crown verrouillée :

```text
DC_TWEED_ANATOMICAL_FH_VARIANT = Porion anatomique → Orbitale
```

Ne jamais présenter cette convention comme reproduction stricte du Frankfort ear-rod historique de Tweed.

### McNamara

Source primaire : McNamara 1984.

Profil : `MCNAMARA_1984_SINGLE_FILM_V1`.

13 variables quantitatives principales documentées. Séparer strictement `Gn_anatomic` et `Gn_constructed`.

Airway = indicateur céphalométrique, jamais diagnostic ORL.

### Ricketts

Source principale : Ricketts 1981.

Profil : `RICKETTS_1981_SUMMARY_DESCRIPTIVE_V1`.

- 11 facteurs latéraux ;
- 12 facteurs PA/frontaux ;
- PA reste `BLOCKED_MODALITY_PA` sans vraie incidence frontale.

Ne pas confondre : Pt Ricketts, Xi, Pm, Sub.Go.-M, PTV, true Frankfort.

Dette de nomenclature connue : `RICKETTS_FACIAL_DEPTH_DEG_V1` calcule `FH ↔ N-Pog`, géométrie correspondant au **Facial Angle** validé. Aucun renommage sans lot de compatibilité dédié.

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
- profil latéral ≠ incidence PA/frontale

---

## 6. Sources canoniques du chantier

Documents à conserver cohérents :

- `docs/audits/CEPHALO_N_CANONICAL_HANDOVER.md` — reprise/état global ;
- `docs/audits/CEPHALO_CANONICAL_MEASUREMENT_REGISTRY.md` — identités de mesures ;
- `docs/audits/CEPHALO_ANALYSIS_MEASUREMENT_PROFILES.md` — composition des analyses ;
- `docs/audits/ORTHO_MODULE_V2.md` — futur uniquement.

Le mapping local SRPose38 reste `LEGACY_LOCAL_MAPPING / SOURCE_LOCK_REQUIRED`. L’existence d’un canal ONNX ne suffit jamais à promouvoir un landmark clinique en vérité anatomique.

---

## 7. État GitHub vérifié

Repo : `hraaaaf/Digital_crown`

### PR #513 — CLOSED

- titre : `test(cephalo): lock source-specific geometry fixtures`
- merge SHA : `d762dec2487b42b6775990fdaa0b2f67b7a1a6f8`
- post-merge CI : **#4407 SUCCESS**
- scope : contrats/fixtures géométriques Céphalo, sans modification runtime production.

Conclusion : **lot géométrie source-lockée intégré et post-merge vérifié**.

### PR #515 — CLOSED

- titre : `docs(cephalo): canonicalize measurements before analysis profiles`
- merge SHA / master de départ du lot runtime : `8f74464998a721414e67957e0c9346f6a67efdb2`
- post-merge CI : **#4442 SUCCESS**
- scope : registre documentaire canonique + profils + handover + Ortho V2 parked.

Conclusion : **registre/profils documentaires intégrés et post-merge vérifiés**.

### PR #524 — ACTIVE — runtime registry

Branche : `feat/cephalo-canonical-runtime-registry`

Goal : matérialiser le registre canonique dans le runtime existant, sans second registre et sans casser le legacy.

Décisions verrouillées du lot :

- enrichir `backend/services/cephalo_measure_registry.py` existant ;
- conserver `cephalo_unit()` et `is_mm_metric()` pour les noms legacy ;
- exposer les IDs `M_*` canoniques explicitement ;
- unité canonique non source-lockée = **pas d’invention** (`None` / fail-closed) ;
- `M_OVERBITE_V1` reste sans unité canonique verrouillée ;
- aucun alias automatique ;
- conserver `method_id` de `cephalo_measurement_adapter.py` ;
- conserver le registre normatif séparé ;
- Ricketts facial axis : géométrie couverte mais usage auto encore `BLOCKED_LANDMARK`.

Snapshot avant mise à jour du présent canonique :

- HEAD : `9bc2f69752810ce4db2a4792b9358d99177d8c11`
- compare : 3 ahead / 0 behind master
- fichiers alors modifiés : runtime registry + test dédié
- PR `mergeable=true`
- review threads : 0
- exact-head workflows alors lancés : CI #4451, PostgreSQL #842, T2 #3327 ; M6-I #2127 skipped attendu.

**Important : cette mise à jour du canonique crée un nouveau HEAD. Les états CI ci-dessus sont donc un snapshot pré-canonique et ne valent pas certification finale. Revérifier le nouveau HEAD exact avant merge.**

---

## 8. Runtime registry — contrat attendu

Le registre runtime canonique doit :

1. rester dans `backend/services/cephalo_measure_registry.py` ;
2. fournir identité canonique + unité source-lockée si connue + statut scientifique ;
3. ne résoudre aucun faux alias ;
4. conserver le fallback legacy existant ;
5. ne pas remplacer les `method_id` d’evidence ;
6. ne pas fusionner le registre normatif ;
7. ne pas activer une mesure `SOURCE_LOCK_REQUIRED`, `BLOCKED_*` ou unité inconnue par simple convention de nom ;
8. ne modifier ni DB, ni données patients, ni documents persistés, ni UI dans ce lot.

Tests minimum :

- IDs canoniques résolus exactement ;
- unités mm/° correctes ;
- unité non verrouillée fail-closed ;
- helpers legacy inchangés ;
- faux équivalents distincts ;
- non-régression générale via CI.

---

## 9. Roadmap restante Céphalo-N

Ordre obligatoire :

### Lot actuel — fermer #524

Succès :

- diff limité au registre runtime + tests + présent canonique ;
- exact HEAD CI/T2/PostgreSQL verts, M6-I skipped attendu ;
- master toujours compatible ;
- 0 thread bloquant ;
- PR ready ;
- **accord utilisateur explicite avant merge** ;
- squash merge ;
- post-merge CI verte.

### Lot suivant — mesures manquantes réellement calculables

Implémenter seulement si :

- source exacte verrouillée ;
- landmarks exacts disponibles/certifiés ;
- convention géométrique verrouillée ;
- calibration disponible pour les distances.

Sinon : rester explicitement bloqué.

### Puis — SVG synchronisé

Règles UI/UX obligatoires :

```text
BEFORE mêmes viewports
→ Goal écrit
→ mockup/référence
→ implémentation
→ AFTER mêmes viewports
→ comparaison/tests
→ score visuel
```

Aucune ligne décorative sans correspondance calculée.

### Puis — normes/interprétation

```text
geometry_result
!=
normative_context
!=
interpretation
```

Normes versionnées avec population/âge/sexe/source quand pertinent.

### Puis — synthèse inter-analyses

Domaines : sagittal/AP, vertical, transverse si PA réelle, dentaire, tissus mous, croissance/airway si réellement évalués.

Sorties : convergence, divergence, compensation, insuffisance de preuve, provenance.

Interdit : moyenne naïve / diagnostic final automatique.

### Puis — validation praticien + PDF

Le praticien doit pouvoir corriger landmarks, revoir mesures, valider/modifier la synthèse et produire un PDF reflétant exactement l’état validé.

### Enfin — closeout

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

1. Relever le nouveau HEAD de #524 après cette mise à jour canonique.
2. Vérifier compare vs `master` et scope exact.
3. Certifier les workflows du **nouveau HEAD**.
4. Recontrôler review threads + mergeability + master.
5. Si tout est vert : marquer #524 ready.
6. Stop au **HUMAN GATE — ACCORD MERGE #524 REQUIS**.
7. Après accord : squash merge avec `expected_head_sha`.
8. Vérifier master réel + post-merge CI.
9. Enchaîner automatiquement sur le lot « mesures manquantes réellement calculables ».

---

## 11. Règles globales de non-régression

Toute modification doit préserver :

- base de données ;
- données patients ;
- documents ;
- comportements déjà validés ;
- compatibilité runtime existante sauf migration explicitement conçue et prouvée.

Aucun déploiement Vercel n’est pertinent pour Digital Crown local/on-premise.

Ne jamais déclarer « terminé », « validé », « production-ready » ou poser `CEPHALO_N_CLOSEOUT_VERIFIED` sans preuve exacte.

---

## 12. Handover compact

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
Registre/profils scientifiques documentés.

LOT ACTIF
PR #524 — feat/cephalo-canonical-runtime-registry.
Étendre le registre existant, préserver legacy, aucun faux alias, normes séparées, unités inconnues fail-closed.

NEXT
Certifier le HEAD final de #524 → master/reviews/mergeability → ready → accord utilisateur merge → squash merge → post-merge → mesures manquantes → SVG → normes → synthèse → validation praticien → PDF → closeout.
```
