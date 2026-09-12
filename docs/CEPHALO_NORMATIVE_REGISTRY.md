# CÉPHALO — REGISTRE NORMATIF VERSIONNÉ

**Statut : R10 FERMÉ / références inertes**  
**Parent :** `docs/CEPHALO_DIAGNOSTIC_SPEC.md`  
**Lot :** 11 — registre normatif

## GOAL

Conserver des références céphalométriques versionnées avec source, méthode, construction et population, sans les convertir automatiquement en classification patient.

## CONTRAT NUMÉRIQUE

Le registre accepte uniquement :

- `EXTREME_RANGE` : `lower` + `upper`, finis, `lower <= upper`, sans `mean`/`sd` ;
- `MEAN_SD` : `mean` + `sd`, finis, `sd > 0`, sans `lower`/`upper`.

`PERCENTILE` reste fail-closed. Toute référence exige une source de recherche admissible et un `population_context`. `active_for_patient_classification=True` est refusé.

## BINDING AU GRAPHE

Le contrat existant de `cephalo_evidence_graph.py` est la source de vérité :

- `NormReference.method_id` ↔ `MeasurementEvidence.analysis_id` ;
- `NormReference.measurement_id` ↔ `MeasurementEvidence.method_id` ;
- `NormReference.method_version` ↔ `MeasurementEvidence.method_version` ;
- unité identique.

`MeasurementEvidence.measurement_id` est namespacé par cas et n'est pas une clé normative stable.

## SOURCES ET RÉFÉRENCES ACTIVES DANS LE REGISTRE

### CRANIOM

Deux `EXTREME_RANGE`, toujours inertes :

- `CRANIOM_L1_DOWNS_MP_EXTREMES_YOUNG_ADULT_V1` : 78°–114°, gate `DOWNS_MP_TANGENT` ;
- `CRANIOM_U1_FH_EXTREMES_YOUNG_ADULT_V1` : 97,5°–130,1°, gate `FH_PO_OR_V1`.

Sources primaires : Bonnefont et al. 2010, DOI `10.1051/odfen/2010406`, et Bonnefont et al. 2011, DOI `10.1051/odfen/2011104`. Les intervalles sont conservés comme extrêmes observés, pas comme seuils universels.

### McNamara 1984

Source primaire : McNamara JA Jr., *A method of cephalometric evaluation*, Am J Orthod. 1984;86(6):449-469. DOI `10.1016/S0002-9416(84)90352-X`, PMID `6594933`.

Table I, échantillon Ann Arbor : 111 adultes non traités, 73 femmes et 38 hommes. Six `MEAN_SD` sont enregistrés :

| Mesure / `MeasurementEvidence.method_id` | Femmes | Hommes | Construction |
|---|---:|---:|---|
| Co–Gn / `MCNAMARA_CO_GN_MM_V1` | 120,2 ± 5,3 mm | 134,3 ± 6,8 mm | `MCNAMARA_CO_GN_V1` |
| Co–A / `MCNAMARA_CO_A_MM_V1` | 91,0 ± 4,3 mm | 99,8 ± 6,0 mm | `MCNAMARA_CO_A_V1` |
| ANS–Me / `MCNAMARA_ANS_ME_MM_V1` | 66,7 ± 4,1 mm | 74,6 ± 5,0 mm | `MCNAMARA_ANS_ME_V1` |

Pour les six références : `method_id="MCNAMARA"`, `method_version="1"`, `unit="mm"`, `active_for_patient_classification=False`.

Le papier primaire précise que, lorsque possible, les mesures de ses échantillons intègrent un facteur d'agrandissement de 8 %. Digital Crown produit des millimètres physiques après calibration. Le contexte porte donc `scale_compatibility="BLOCKED_UNTIL_8_PERCENT_ENLARGEMENT_MATCHED"`. Aucune comparaison patient directe n'est autorisée tant que cette compatibilité n'est pas établie.

## OUSEHAL 2012 — BLOQUÉ

La source `MOROCCO_STEINER_OUSEHAL_2012` conserve le contexte : 71 jeunes adultes du CCTD Casablanca, 47 femmes / 24 hommes, 19–27 ans, Classe I, profil acceptable, non traités. DOI `10.1016/j.ortho.2011.12.001`, PMID `22236522`.

Une publication peer-reviewed secondaire reproduit SNA `80,59 ± 3,80°`, SNB `77,68 ± 3,55°`, ANB `3,11 ± 1,68°`, mais le tableau numérique primaire Ousehal n'a pas été directement vérifié. Ces trois nombres restent donc hors `NormReference`.

Si ces références deviennent admissibles, le binding devra être :

- `method_id="STEINER"` ;
- `measurement_id="STEINER_SNA_DEG_V1"`, `STEINER_SNB_DEG_V1` ou `STEINER_ANB_DEG_V1` ;
- version `1`, unité `deg`, construction exacte correspondante.

## TRIAGE SCIENTIFIQUE R10

| Famille | Décision |
|---|---|
| Steiner historique 82/80/2 | pas de `MEAN_SD` démontré |
| Tweed 25/90/65 | valeurs conventionnelles/plages, pas `MEAN_SD` |
| Downs | chiffres non enregistrés sans table primaire certifiée |
| McNamara | 6 `MEAN_SD` primaires enregistrés, inertes, gate 8 % |
| Ricketts | chiffres non enregistrés sans table primaire + stratification d'âge exacte |
| Ousehal/Maroc | candidats documentés, hors registre numérique jusqu'au tableau primaire |

## PREUVE CODE

- Registre : `backend/services/cephalo_norm_registry.py`
- Tests : `backend/tests/test_cephalo_norm_registry.py`
- Contrat McNamara : `backend/services/cephalo_mcnamara_evidence.py`
- Validation du binding : `backend/services/cephalo_evidence_graph.py`

Les tests couvrent les formes `EXTREME_RANGE`/`MEAN_SD`, valeurs non finies ou SD non positive, contexte obligatoire, immutabilité, provenance, absence de chiffres Ousehal non vérifiés, six références McNamara exactes, binding au graphe et blocage d'échelle.

## PREUVE DE CLÔTURE R10

- Candidate HEAD certifié : `9ffd36306ec6fa09b71d590e078af01db67e6888` ;
- CI #3431 : `success` ;
- T2 Runtime Browser Certification #2411 : `success` ;
- PR #431 : mergée ;
- merge commit R10 : `d0bdfc4fa47346f27e432139e6785177da4deef3` ;
- le merge R10 est ancêtre du `master` vérifié après intégration d'autres chantiers ;
- aucun déploiement requis ni déclenché par R10.

## NEXT EXACT

R11 — diagnostic multiaxial : cadrer les findings et hypothèses explicables, rendre contradictions et données manquantes visibles, et conserver une frontière stricte entre preuve, interprétation et conclusion clinique.
