# CÉPHALO — R10 REGISTRE NORMATIF ACTIVABLE

**Statut : R10 en cours — références inertes, aucune classification patient active**  
**Parent :** `docs/CEPHALO_DIAGNOSTIC_SPEC.md`  
**Branche :** `feat/cephalo-r10-normative-registry`

## GOAL

Conserver puis matérialiser des références céphalométriques avec leur analyse, mesure versionnée, construction, population, source et contexte **sans transformer une publication en diagnostic automatique**.

Chaîne R10 :

`MeasurementEvidence → NormReference → NormativeEvaluationEvidence`

R11 seulement pourra utiliser une évaluation normative pour produire un `Finding` explicable.

## SUCCÈS R10

1. références numériques strictement sourcées et versionnées ;
2. contexte population/âge/sexe/site explicite quand pertinent ;
3. `EXTREME_RANGE` et `MEAN_SD` validés fail-closed ;
4. aucune référence secondaire seule ne peut créer une référence numérique ;
5. aucune référence ne peut être enregistrée directement avec `active_for_patient_classification=true` ;
6. un adaptateur descriptif peut produire `NormativeEvaluationEvidence` sans `classification` ni `classification_rule_id` ;
7. création, édition landmark, calibration manuelle et AUTO_VERIFIED rematérialisent ces évaluations descriptives à partir des mesures courantes ;
8. findings/diagnostics/objets cliniques aval restent bloquants lors d'une transition qui invaliderait leur preuve ;
9. intégrité inter-objets vérifie aussi `mean/sd`, pas seulement les bornes d'intervalle ;
10. exact-head CI/T2 verts avant merge.

## RÈGLE D'ACTIVATION

Toutes les références restent **inertes par défaut** :

`active_for_patient_classification = false`

R10 prépare un registre **activable**, pas une classification implicite. Une activation future exigera une règle de classification versionnée, un contexte d'applicabilité explicite, des cas goldens et une validation clinique dédiée.

Interdit dans R10 :

- `hors plage → diagnostic` ;
- `z-score → normal/anormal` sans règle clinique versionnée ;
- norme de manuel non traçable ;
- valeur legacy promue sans source ;
- généralisation d'une cohorte locale à une population nationale ;
- traitement ou recommandation thérapeutique.

## CONTRAT DU REGISTRE

### Sources

`NormSource` conserve au minimum : source ID, niveau de preuve, citation, DOI/PMID/URL si disponibles, description de l'échantillon et limites d'applicabilité.

Une référence numérique exige au moins une source de recherche primaire parmi :

- `PRIMARY_ARTICLE` ;
- `PEER_REVIEWED_POPULATION_STUDY`.

Une reproduction technique ou une revue peut recouper une valeur mais ne suffit pas seule.

### Références

Le contrat historique du graphe est conservé pour éviter une migration transverse pendant R10 :

- `NormReference.method_id` correspond à `MeasurementEvidence.analysis_id` ;
- `NormReference.measurement_id` correspond à `MeasurementEvidence.method_id` ;
- `method_version` versionne la référence/méthode et doit être explicitement vérifié par l'adaptateur ;
- `unit` doit correspondre exactement à la mesure.

Le nom `method_id` est historiquement imparfait mais sa sémantique ne sera pas changée silencieusement dans R10.

### Types numériques

`EXTREME_RANGE` :

- `lower` et `upper` obligatoires, finis, `lower <= upper` ;
- `mean/sd` interdits.

`MEAN_SD` :

- `mean` et `sd` obligatoires et finis ;
- `sd > 0` ;
- `lower/upper` interdits.

`PERCENTILE` reste fail-closed tant qu'un contrat dédié n'est pas conçu et testé.

## SOURCES ENREGISTRÉES

| ID | Type | Population/contexte | Usage R10 |
|---|---|---|---|
| `CRANIOM_PART1_2010` | article primaire | 83 jeunes adultes, Classe I, non traités | provenance méthode |
| `CRANIOM_PART2_2011` | article primaire | même cohorte | intervalles extrêmes publiés |
| `CRANIOM_TECHNICAL_REPRODUCTION` | secondaire technique | reproduction CRANIOM | recoupement uniquement |
| `MOROCCO_STEINER_OUSEHAL_2012` | étude populationnelle peer-reviewed | 71 jeunes adultes 19–27 ans, CCTD Casablanca | cohorte marocaine locale |
| `OUSEHAL_NUMERIC_CROSSCHECK_GOVINAKOVI_2018` | étude peer-reviewed | tableau comparatif reproduisant les valeurs Ousehal | recoupement numérique SNA/SNB/ANB |
| `PEDIATRIC_NORMS_REVIEW_NGUYEN_2024` | scoping review | multi-études pédiatriques | garde âge/développement uniquement |

### Références bibliographiques principales

- Bonnefont R et al. J Dentofacial Anom Orthod. 2010;13(4):385-400. DOI `10.1051/odfen/2010406`.
- Bonnefont R, Ernoult J-F, Sorel O. J Dentofacial Anom Orthod. 2011;14:105. DOI `10.1051/odfen/2011104`.
- Ousehal L, Lazrak L, Chafii A. Int Orthod. 2012;10(1):122-134. DOI `10.1016/j.ortho.2011.12.001`, PMID `22236522`.
- Govinakovi PS, Al-Busaidi I, Senguttuvan V. Sultan Qaboos Univ Med J. 2018;18(2):e182-e189. DOI `10.18295/squmj.2018.18.02.010`, PMID `30210848`.
- Nguyen TK et al. Korean J Orthod. 2024;54(4):210-228. PMID `38898629`.

## RÉFÉRENCES NUMÉRIQUES

### CRANIOM

| ID | Mesure | Référence | Construction | Activation |
|---|---|---:|---|---|
| `CRANIOM_L1_DOWNS_MP_EXTREMES_YOUNG_ADULT_V1` | L1 / plan mandibulaire Downs | 78°–114° | `DOWNS_MP_TANGENT` | NON |
| `CRANIOM_U1_FH_EXTREMES_YOUNG_ADULT_V1` | U1 / Francfort | 97,5°–130,1° | `FH_PO_OR_V1` | NON |

Ces valeurs sont des **extrêmes observés** dans la cohorte CRANIOM et restent `EXTREME_RANGE`, jamais déguisées en moyenne ± SD.

### Steiner — cohorte CCTD Casablanca 19–27 ans

Valeurs Ousehal 2012, recoupées dans une publication peer-reviewed indépendante :

| Référence R10 | Mesure runtime | Moyenne ± SD | Activation |
|---|---|---:|---|
| `STEINER_SNA_CCTD_CASABLANCA_19_27_MEAN_SD_V1` | `STEINER_SNA_DEG_V1` | 80,59 ± 3,80° | NON |
| `STEINER_SNB_CCTD_CASABLANCA_19_27_MEAN_SD_V1` | `STEINER_SNB_DEG_V1` | 77,68 ± 3,55° | NON |
| `STEINER_ANB_CCTD_CASABLANCA_19_27_MEAN_SD_V1` | `STEINER_ANB_DEG_V1` | 3,11 ± 1,68° | NON |

Contexte obligatoire : 71 sujets, 47 femmes / 24 hommes, 19–27 ans, moyenne 22,73 ± 1,69 ans, CCTD Casablanca, harmonie faciale/profil acceptable, Classe I, non traités.

**Limite canonique :** la cohorte est enregistrée comme `CCTD Casablanca`, jamais comme « norme marocaine universelle ». Les auteurs demandent des études plus exhaustives avant généralisation.

## INCOHÉRENCES DÉCOUVERTES À CORRIGER DANS R10

### 1. Liaison registre ↔ MeasurementEvidence

Les trois premières références Steiner R10 ont été initialement écrites avec une sémantique naturelle `method_id = method versionné` / `measurement_id = nom clinique`. Le validateur historique attend l'inverse contractuel décrit plus haut.

**Correction obligatoire avant adaptation runtime :**

- `method_id = STEINER` ;
- `measurement_id = STEINER_SNA_DEG_V1 | STEINER_SNB_DEG_V1 | STEINER_ANB_DEG_V1` ;
- version/unité contrôlées explicitement.

Aucune évaluation normative Steiner ne doit être matérialisée avant cette correction.

### 2. Intégrité `MEAN_SD`

Le validateur inter-objets historique compare `kind/lower/upper`, mais pas encore `mean/sd`.

**Correction obligatoire :** comparer le payload normatif exact selon `ReferenceKind` :

- `EXTREME_RANGE` → `kind/lower/upper` ;
- `MEAN_SD` → `kind/mean/sd` ;
- toute clé numérique incohérente → fail closed.

### 3. Transitions runtime

Création, édition landmark et calibrations produisent actuellement `normative_evaluations: []`.

Les transitions landmark/manual/AUTO bloquent aussi toute `normative_evaluations` existante comme si elle était déjà une preuve diagnostique aval.

R10 doit distinguer :

- **évaluation normative descriptive/inert** : recalculable/rematérialisable avec la mesure courante ;
- **finding/diagnostic/problem/objective/treatment/validation/final plan** : toujours bloquant si une transition rend leur preuve obsolète.

La rematérialisation doit être centralisée dans un seul adaptateur R10, pas dupliquée dans trois transitions.

## ADAPTATEUR R10 CIBLE

Entrée : `MeasurementEvidence[]` + `NormRegistry`.

Pour chaque mesure :

1. chercher les références dont `method_id == measurement.analysis_id` ;
2. exiger `measurement_id == measurement.method_id` ;
3. exiger unité et version compatibles ;
4. créer une `NormativeEvaluationEvidence` descriptive avec référence numérique exacte et `population_context` ;
5. `classification_rule_id = None` ;
6. `classification = None` ;
7. `source_refs = NormReference.source_ids` ;
8. `evidence_refs = [measurement.measurement_id]` ;
9. aucune interprétation clinique implicite.

Pour une mesure indisponible, l'adaptateur doit rester fail-closed et ne jamais produire de classification. Le choix exact `NOT_COMPUTABLE` versus absence d'évaluation sera figé par tests avant branchement runtime.

## PREUVE CODE ACTUELLE

- registre : `backend/services/cephalo_norm_registry.py` ;
- intégrité graphe : `backend/services/cephalo_evidence_graph.py` ;
- schéma : `backend/schemas/cephalo_evidence.py` ;
- création runtime : `backend/services/cephalo_runtime_evidence.py` ;
- édition : `backend/services/cephalo_landmark_correction_evidence.py` ;
- calibration manuelle : `backend/services/cephalo_calibration_evidence.py` ;
- auto-calibration : `backend/services/cephalo_auto_calibration_transition.py` ;
- tests registre : `backend/tests/test_cephalo_norm_registry.py` ;
- tests graphe : `backend/tests/test_cephalo_evidence_graph.py`.

## NEXT EXACT

1. fermer/merger R9 sur exact-head vert ;
2. reconstruire R10 proprement depuis le master post-R9 sans force-push ;
3. porter uniquement les changements R10 déjà prouvés ;
4. corriger la liaison des trois références Steiner au contrat historique ;
5. étendre l'intégrité `MEAN_SD` ;
6. implémenter l'adaptateur descriptif unique ;
7. brancher création + édition + calibration manuelle + AUTO_VERIFIED ;
8. tests fail-closed + transitions + read/rematerialisation ;
9. draft PR R10 ;
10. CI/T2 exact-head ;
11. anti-stale → merge → closeout.
