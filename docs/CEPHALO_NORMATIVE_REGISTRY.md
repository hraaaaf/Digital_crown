# CÉPHALO — REGISTRE NORMATIF VERSIONNÉ

**Statut : R10 / références inertes**  
**Parent :** `docs/CEPHALO_DIAGNOSTIC_SPEC.md`  
**Lot :** 11 — registre normatif

## GOAL

Conserver les références céphalométriques avec leur méthode, construction, population, source et version **sans transformer une publication en règle diagnostique automatique**.

La mesure patient reste séparée de la référence :

`MeasurementEvidence → NormReference → NormativeEvaluation → Finding`

Une `NormReference` n'a aucun droit de produire un diagnostic ou un traitement.

## RÈGLE D'ACTIVATION

Toutes les références sont **inertes par défaut** : `active_for_patient_classification = false`.

Le registre accepte désormais deux formes numériques strictes :

- `EXTREME_RANGE` : `lower` et `upper` obligatoires, finis, `lower <= upper`, sans `mean`/`sd` ;
- `MEAN_SD` : `mean` et `sd` obligatoires et finis, `sd > 0`, sans `lower`/`upper`.

`PERCENTILE` reste fail-closed tant qu'un contrat exact n'est pas défini. Une référence numérique exige toujours au moins une source de recherche primaire admissible et un `population_context` explicite.

Le registre interdit l'enregistrement direct d'une référence active. L'activation future exigera un gate séparé :

- construction géométrique certifiée ;
- source primaire et contexte applicables ;
- population/âge/sexe/développement explicités quand pertinents ;
- compatibilité d'échelle/radiographie pour les mesures linéaires ;
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
| `MOROCCO_STEINER_OUSEHAL_2012` | étude populationnelle peer-reviewed | 71 jeunes adultes 19–27 ans, CCTD Casablanca | contexte marocain ; valeurs numériques bloquées faute de table primaire accessible |
| `MCNAMARA_1984` | article primaire | 111 adultes Ann Arbor, 73 femmes / 38 hommes, Classe I, bon équilibre squelettique | références `MEAN_SD` Table I, descriptives et inertes |
| `PEDIATRIC_NORMS_REVIEW_NGUYEN_2024` | scoping review peer-reviewed | données normatives pédiatriques multi-études | garde âge/développement |

### Références bibliographiques

- Bonnefont R, Casteigt J, Ernoult J-F, Sorel O. J Dentofacial Anom Orthod. 2010;13(4):385-400. DOI `10.1051/odfen/2010406`.
- Bonnefont R, Ernoult J-F, Sorel O. J Dentofacial Anom Orthod. 2011;14:105. DOI `10.1051/odfen/2011104`.
- Ousehal L, Lazrak L, Chafii A. Int Orthod. 2012;10(1):122-134. DOI `10.1016/j.ortho.2011.12.001`, PMID `22236522`.
- Govinakovi PS, Al-Busaidi I, Senguttuvan V. Sultan Qaboos Univ Med J. 2018;18(2):e182-e189. DOI `10.18295/squmj.2018.18.02.010`, PMID `30210848`.
- McNamara JA Jr. Am J Orthod. 1984;86(6):449-469. DOI `10.1016/S0002-9416(84)90352-X`, PMID `6594933`.
- Nguyen TK, Cambala A, Hrit M, Zimmermann EA. Korean J Orthod. 2024;54(4):210-228. PMID `38898629`.

## RÉFÉRENCES NUMÉRIQUES ENREGISTRÉES

### CRANIOM — `EXTREME_RANGE`

| ID | Mesure | Référence | Construction requise | Activation |
|---|---|---:|---|---|
| `CRANIOM_L1_DOWNS_MP_EXTREMES_YOUNG_ADULT_V1` | incisive mandibulaire / plan mandibulaire de Downs | 78°–114° | `DOWNS_MP_TANGENT` | NON |
| `CRANIOM_U1_FH_EXTREMES_YOUNG_ADULT_V1` | incisive maxillaire / Francfort | 97,5°–130,1° | `FH_PO_OR_V1` | NON |

La source CRANIOM décrit ces intervalles comme des **extrêmes observés**, pas comme des seuils universels de pathologie.

### McNamara 1984 — `MEAN_SD` primaire

La Table I primaire du PDF de l'Université du Michigan donne les valeurs suivantes pour 111 adultes non traités d'Ann Arbor avec visages équilibrés et bonnes occlusions : 73 femmes et 38 hommes. L'âge moyen indiqué est de 26 ans 8 mois chez les femmes et 30 ans 9 mois chez les hommes.

| Mesure / contrat Digital Crown | Femmes, moyenne ± SD | Hommes, moyenne ± SD | Construction | Activation |
|---|---:|---:|---|---|
| Co–Gn / `MCNAMARA_CO_GN_MM_V1` | 120,2 ± 5,3 mm | 134,3 ± 6,8 mm | `MCNAMARA_CO_GN_V1` | NON |
| Co–A / `MCNAMARA_CO_A_MM_V1` | 91,0 ± 4,3 mm | 99,8 ± 6,0 mm | `MCNAMARA_CO_A_V1` | NON |
| ANS–Me / `MCNAMARA_ANS_ME_MM_V1` | 66,7 ± 4,1 mm | 74,6 ± 5,0 mm | `MCNAMARA_ANS_ME_V1` | NON |

Le même texte primaire précise que, lorsque possible, les mesures de ses échantillons intègrent un **facteur d'agrandissement de 8 %**. Digital Crown produit au contraire des millimètres physiques à partir d'une calibration vérifiée. Ces six références sont donc stockées pour provenance et traçabilité, mais portent le gate :

`BLOCKED_UNTIL_8_PERCENT_ENLARGEMENT_MATCHED`

Elles ne doivent pas être comparées directement aux mesures patient Digital Crown tant que cette compatibilité d'échelle n'est pas explicitement résolue.

## OUSEHAL 2012 — CANDIDATS BLOQUÉS

L'abstract primaire Ousehal 2012 confirme une analyse de Steiner sur 71 jeunes adultes du CCTD Casablanca, 47 femmes et 24 hommes, âge moyen 22,73 ± 1,69 ans, Classe I, profil acceptable et sans traitement orthodontique antérieur.

Une table comparative peer-reviewed de Govinakovi et al. 2018 reproduit pour Ousehal 2012 :

| Mesure | Moyenne ± SD reproduite | Statut R10 |
|---|---:|---|
| SNA | 80,59° ± 3,80° | BLOQUÉ — tableau numérique primaire Ousehal non directement vérifié |
| SNB | 77,68° ± 3,55° | BLOQUÉ — tableau numérique primaire Ousehal non directement vérifié |
| ANB | 3,11° ± 1,68° | BLOQUÉ — tableau numérique primaire Ousehal non directement vérifié |

Le PDF et les tableaux de l'éditeur restent derrière l'accès éditeur. Ces trois valeurs demeurent donc des **candidats documentés**, pas des `NormReference` runtime. La publication secondaire sert de recoupement, pas de substitut silencieux à la table primaire.

Les contrats runtime correspondants existent et ont été vérifiés dans `cephalo_steiner_evidence_adapter.py` :

- SNA → `STEINER_SNA_DEG_V1`, construction `STEINER_SNA_V1`, version `1`, `deg` ;
- SNB → `STEINER_SNB_DEG_V1`, construction `STEINER_SNB_V1`, version `1`, `deg` ;
- ANB → `STEINER_ANB_DEG_V1`, construction `STEINER_ANB_V1`, version `1`, `deg`.

Le `MeasurementEvidence.measurement_id` runtime reste namespacé par cas ; le registre conserve donc `SNA`/`SNB`/`ANB` comme clés sémantiques, tandis que le binding technique fiable repose sur méthode + version + unité + construction.

## TRIAGE SCIENTIFIQUE R10

| Famille | Preuve primaire examinée | Décision R10 |
|---|---|---|
| Steiner | articles historiques identifiés ; standards 82/80/2 non prouvés comme moyenne ± SD d'une cohorte compatible | pas de `MEAN_SD` |
| Tweed | PDF primaire 1954, Tweed Foundation | pas de `MEAN_SD` : 25° est explicitement appelé norme choisie arbitrairement ; IMPA 90° est désigné dans une plage 85–95° ; FMIA 65° en découle |
| Downs | source primaire 1948 identifiée ; contrats runtime `DOWNS_FACIAL_ANGLE_DEG_V1` et `DOWNS_Y_AXIS_DEG_V1` vérifiés | valeurs 1956 non enregistrées tant que la table primaire n'est pas visuellement certifiée |
| McNamara | PDF primaire 1984, Table I, Université du Michigan | six `MEAN_SD` enregistrés, inertes, avec gate d'agrandissement 8 % |
| Ricketts | article primaire 1960 : 1000 cas, cinq mesures, changements liés à l'âge | pas de norme numérique activée : tables exactes/stratification d'âge non certifiées ici et Facial Axis reste fail-closed en R9 |
| Ousehal/Maroc | abstract primaire + table secondaire peer-reviewed concordante | SNA/SNB/ANB documentés mais non enregistrés tant que la table primaire n'est pas lisible |

Ce triage évite un piège classique : transformer des objectifs historiques, des plages de travail ou des moyennes secondaires en « normes statistiques » simplement parce qu'elles sont faciles à trouver.

## POURQUOI LE CONTEXTE EST OBLIGATOIRE

Une valeur céphalométrique n'est pas universelle : population, âge, sexe, sélection de l'échantillon, méthode de construction et échelle radiographique peuvent changer son sens. Les références sont donc conservées avec leur contexte explicite plutôt qu'aplaties en une table de « normales » sans provenance.

## VALEURS EXPLICITEMENT NON ACTIVÉES

- Ousehal SNA/SNB/ANB : table primaire non directement vérifiée ;
- standards historiques Steiner 82/80/2 : cibles historiques, pas `MEAN_SD` populationnels prouvés ;
- Tweed 25/90/65 : valeurs conventionnelles/ranges, pas `MEAN_SD` ;
- Downs : valeurs numériques secondaires non promues sans contrôle primaire ;
- Ricketts : normes numériques non promues sans table primaire et contexte d'âge exacts ;
- anciennes constantes Digital Crown de PR #371 : historiques, jamais autoritatives ;
- valeurs secondaires CRANIOM non retrouvées dans une source primaire exploitable ;
- McNamara Table I : enregistrées mais non comparables au runtime tant que le facteur 8 % n'est pas harmonisé.

## PREUVE CODE

Implémentation : `backend/services/cephalo_norm_registry.py`  
Tests : `backend/tests/test_cephalo_norm_registry.py`  
Contrats McNamara : `backend/services/cephalo_mcnamara_evidence.py`  
Contrats Steiner : `backend/services/cephalo_steiner_evidence_adapter.py`  
Contrats Downs : `backend/services/cephalo_downs_evidence.py`

Les tests couvrent les invariants `EXTREME_RANGE` et `MEAN_SD`, le contexte populationnel obligatoire, l'immutabilité, les sources, les formes numériques invalides, `PERCENTILE` fail-closed, l'interdiction de classification patient, l'absence de référence numérique Ousehal non vérifiée et les six bindings McNamara exacts avec blocage d'échelle.

## NEXT EXACT

Faire certifier le nouveau HEAD R10 par CI/T2. Si vert, conserver les références McNamara comme données descriptives inertes, puis merger R10. Ousehal, Downs et Ricketts restent des gates scientifiques séparés tant que leurs tables primaires exactes ne sont pas vérifiées ; aucune valeur secondaire ou conventionnelle ne doit être promue pour « remplir » le registre.
