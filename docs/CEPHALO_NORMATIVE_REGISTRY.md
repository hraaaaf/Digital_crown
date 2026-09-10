# CÉPHALO — REGISTRE NORMATIF VERSIONNÉ

**Statut : fondation / références inertes**  
**Parent :** `docs/CEPHALO_DIAGNOSTIC_SPEC.md`  
**Lot :** 11 — registre normatif

## GOAL

Conserver les références céphalométriques avec leur méthode, construction, population, source et version **sans transformer une publication en règle diagnostique automatique**.

La mesure patient reste séparée de la référence :

`MeasurementEvidence → NormReference → NormativeEvaluation → Finding`

Une `NormReference` n'a aucun droit de produire un diagnostic ou un traitement.

## RÈGLE D'ACTIVATION

Toutes les références sont **inertes par défaut** : `active_for_patient_classification = false`.

Le registre actuel interdit même l'enregistrement direct d'une référence active. L'activation future exigera un gate séparé :

- construction géométrique certifiée ;
- source primaire et contexte applicables ;
- population/âge/sexe/développement explicités quand pertinents ;
- règle de classification versionnée ;
- golden cases ;
- validation praticien ;
- aucune translation directe `hors plage → diagnostic → traitement`.

## SOURCES ENREGISTRÉES

| ID | Type | Population/contexte | Usage actuel |
|---|---|---|---|
| `CRANIOM_PART1_2010` | article primaire | 83 jeunes adultes, Classe I, non traités | provenance méthode |
| `CRANIOM_PART2_2011` | article primaire | même cohorte décrite | deux intervalles extrêmes explicitement publiés |
| `CRANIOM_TECHNICAL_REPRODUCTION` | document technique secondaire | reproduction détaillée CRANIOM | contrôle uniquement |
| `MOROCCO_STEINER_OUSEHAL_2012` | étude populationnelle peer-reviewed | 71 jeunes adultes 19–27 ans, CCTD Casablanca | contexte marocain ; aucune valeur copiée sans table primaire vérifiée |
| `PEDIATRIC_NORMS_REVIEW_NGUYEN_2024` | scoping review peer-reviewed | données normatives pédiatriques multi-études | garde âge/développement |

### Références bibliographiques

- Bonnefont R, Casteigt J, Ernoult J-F, Sorel O. J Dentofacial Anom Orthod. 2010;13(4):385-400. DOI `10.1051/odfen/2010406`.
- Bonnefont R, Ernoult J-F, Sorel O. J Dentofacial Anom Orthod. 2011;14:105. DOI `10.1051/odfen/2011104`.
- Ousehal L, Lazrak L, Chafii A. Int Orthod. 2012;10(1):122-134. DOI `10.1016/j.ortho.2011.12.001`, PMID `22236522`.
- Nguyen TK, Cambala A, Hrit M, Zimmermann EA. Korean J Orthod. 2024;54(4):210-228. PMID `38898629`.

## RÉFÉRENCES NUMÉRIQUES ACTUELLEMENT ENREGISTRÉES

Deux seules valeurs CRANIOM sont intégrées à ce stade parce qu'elles figurent explicitement dans la source primaire accessible et sont recoupées par le document technique :

| ID | Mesure | Référence | Construction requise | Activation |
|---|---|---:|---|---|
| `CRANIOM_L1_DOWNS_MP_EXTREMES_YOUNG_ADULT_V1` | incisive mandibulaire / plan mandibulaire de Downs | 78°–114° | `DOWNS_MP_TANGENT` | NON |
| `CRANIOM_U1_FH_EXTREMES_YOUNG_ADULT_V1` | incisive maxillaire / Francfort | 97,5°–130,1° | `FH_PO_OR_V1` | NON |

La source CRANIOM décrit ces intervalles comme des **extrêmes observés dans sa cohorte**, pas comme des seuils universels de pathologie. Le logiciel conserve donc `ReferenceKind.EXTREME_RANGE` au lieu de les déguiser en moyenne ± écart-type.

## POURQUOI LE CONTEXTE EST OBLIGATOIRE

La littérature récente et populationnelle confirme qu'un même nombre céphalométrique ne doit pas être traité comme universel :

- l'étude marocaine Ousehal et al. porte sur un échantillon spécifique du CCTD Casablanca et ses auteurs préviennent que les résultats ne peuvent pas être généralisés sans études plus larges ;
- une revue 2024 des données pédiatriques montre des changements liés à la croissance et au développement ;
- des travaux longitudinaux plus récents construisent des références dépendant notamment de l'âge et du sexe.

Conséquence architecture : `population_context` est obligatoire dans toute référence numérique.

## VALEURS EXPLICITEMENT NON ACTIVÉES

Les valeurs 9 ans/adulte présentes sur la fiche historique COM et le document technique CRANIOM pour A'B', Situation A/B et profondeur faciale restent **hors registre numérique actif** tant que leur provenance primaire exacte n'est pas vérifiée dans un texte/tableau exploitable.

Même traitement pour les anciennes constantes Digital Crown de PR #371 : elles sont historiques, jamais autoritatives.

## GATES CONSTRUCTION

Une référence peut exister alors que la mesure correspondante reste non calculable :

- `CRANIOM_L1_DOWNS_MP...` exige `DOWNS_MP_TANGENT`. Le `Go-Me` legacy ne lui est pas substitué ;
- `CRANIOM_U1_FH...` exige le Francfort anatomique `Po-Or` ;
- Gi/Gs CRANIOM restent absents de SRPose38 ;
- le regard horizontal/NHP reste requis pour A''B''.

## PREUVE CODE

Implémentation : `backend/services/cephalo_norm_registry.py`  
Tests : `backend/tests/test_cephalo_norm_registry.py`

Les tests vérifient provenance, intervalles exacts, contexte populationnel obligatoire, rejet des doublons/sources inconnues/plages invalides, et interdiction d'activer directement une référence pour classifier un patient.

## NEXT EXACT

Après merge du socle PR #390 : rebaseliner cette branche sur `master`, exécuter CI, puis créer l'adaptateur `MeasurementEvidence → NormativeEvaluationEvidence` en mode **descriptif/inert** uniquement. La première classification active attendra une règle scientifique explicitement validée.
