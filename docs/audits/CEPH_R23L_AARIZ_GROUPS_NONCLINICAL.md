# R23-L — diagnostic des points SRPose38 par tissu, sans modification des indices

**Goal demandé** : distinguer les erreurs de placement de repères vs éventuelles erreurs de correspondance d'indices, après clarification que le modèle détecte les points et **ne calcule pas les angles**. Conserver SRPose38 et ses 38 sorties inchangés, ne pas toucher à la Production et ne pas réétiqueter les repères sans démonstration externe.

## Sources de preuve actuelles (déjà exécutées)

1. `docs/audits/evidence/lot04/cephalo_vnext_lot04_benchmark_manifest.json` : **150 cas acceptance Aariz**, protocole `REFERENCE_EQUIVALENCE_V1`, modèle `srpose38-tta-1024.onnx` SHA `a5ecd466d6d2c4ef02e145a143076a05720c0be56a260224812c23e2ecf42ddb`.
2. `cephalo_vnext_lot04_results.json` : 150 jeux de **38 coordonnées prédites par le poids**, statistiques d'écarts par repère et par appareil, avec checksum de provenance. Pas de nouvelles inférences ici.
3. `cephalo_vnext_lot04_acceptance_record.json` : **23/24 FAIL**, **9/9 FAIL sur les mesures aval**. Restent inchangés et ne doivent pas être requalifiés en succès.
4. `cephalo_vnext_lot04_acceptance_record_detail.json` : SHA256 de l'archive des prédictions liée au record.
5. `scripts/run_cephalo_vnext_lot04_benchmark.py::AARIZ_TO_DC` : **24 noms appariés** par la convention logicielle locale. Ceci **n'atteste pas les noms anatomiques originels** des canaux du poids `SRPose38` (`LEGACY_LOCAL_MAPPING`, source-lock scientifique encore ouvert).

## Répartition descriptive des 24 points Aariz en classes locales

| Famille (classification locale de travail) | Nombre compatible Aariz | PASS | FAIL |
|---|---:|---:|---:|
| Osseux : A, ANS, Ar, B, Co, Gn, Go, Me, N, Or, PNS, Po, Pog, S | 14 | 1 (Me) | 13 |
| Dentaire : L1_apex, L1_incisal, U1_apex, U1_incisal | 4 | 0 | 4 |
| Cutané / tissus mous : Li_soft, Ls_soft, N_soft, Pog_soft, Prn, Sn_soft | 6 | 0 | 6 |
| **Total** | **24** | **1** | **23** |

Les 14 canaux restants parmi les 38 sorties ne sont PAS couverts par un appariement Aariz de ce benchmark. Ils ne sont pas tous cutanés : plusieurs autres labels locaux sont dentaires, osseux ou de construction. Les groupes ci-dessus sont **un diagnostic interne**, pas une table officielle du challenge CL-Detection2023.

## Cibles prioritaires constatées

La p95 est la **distance point-prédit ↔ point-référence** en mm mesurée dans le benchmark existant, pas une erreur de calcul d'angle ni un seuil de sécurité clinique universel.

| Famille | Repère (nom local) | p95 modèle | p95 référence humaine | Excès |
|---|---|---:|---:|---:|
| Osseux | PNS | 5,221 mm | 0,985 mm | 5,30× |
| Osseux | Ar | 8,902 mm | 2,220 mm | 4,01× |
| Osseux | N | 7,490 mm | 1,891 mm | 3,96× |
| Osseux | S | 1,698 mm | 0,457 mm | 3,72× |
| Dentaire | L1_apex | 5,371 mm | 2,985 mm | 1,80× |
| Dentaire | U1_incisal | 2,433 mm | 1,391 mm | 1,75× |
| Cutané | Pog_soft | 8,135 mm | 1,334 mm | 6,10× |
| Cutané | Ls_soft | 2,423 mm | 0,709 mm | 3,42× |

**Signal d'imagerie non causal** : Pour `N`, p95 par appareil de `Rotograph EVO` ≈9,08 mm (n=11), `ART Plus` ≈8,51 mm (n=55), contre d'autres sous-groupes plus bas. Les tailles d'échantillon, modalités et distributions patients diffèrent ; **on ne peut pas attribuer cette variance au seul détecteur ni à l'appareil sans protocole de comparaison contrôlé**. Les strates n<20 sont marquées explicitement dans le rapport reproductible.

## Test « confusion d'indices » : ce qui est prouvé et ce qui ne l'est pas

Le code `scripts/audit_ceph_r23l_aariz_point_families.py` vérifie sans exécuter ONNX l'identité cryptographique des résultats originaux, les 150 cas, les 38 canaux numériques par cas, les 24 comparables et la cohérence du statut scientifique. Il **ne possède pas les positions x/y des points annotés par les humains pour chaque cas** ; seules les prédictions individuelles et erreurs déjà agrégées se trouvent dans ce dépôt.

**Conséquence fondamentale :** une prédiction proche d'un autre *point prédit* ne démontre pas qu'elle correspond au *point expert* d'un autre indice. Un échange de canaux ne peut pas être sélectionné par minimisation post hoc sur les 150 cas d'acceptance gelés. Une correction d'indice à partir de ces seules statistiques serait scientifiquement invérifiable et exposerait à une fuite du test.

Le chemin recevable pour trancher est :
1. Obtenir légalement les annotations **cas-par-cas** Aariz qualifiées du même cliché (hors export non autorisé), de préférence sur la machine de recherche autorisée ; ou un exemple CL2023 avec une paire officielle `même image + index 1..38`.
2. Étudier en **développement** une matrice candidate `canal i ↔ référence j`, avec preuves anatomiques indépendantes et mapping figé *avant* test d'acceptation. Ne jamais remapper automatiquement les dossiers historiques.
3. Confirmer sur un **nouveau jeu d'acceptance indépendant non utilisé pour proposer la permutation** et conserver les résultats défavorables. Si aucun nouvel ensemble légitime n'est disponible, la confirmation reste OPEN.
4. Contrôler séparément les effets de cadrage, modalité / appareil, points cutanés et dentaires, calibration mm/px puis les erreurs des angles **aval**. Aucun seuil ni poids retouché dans ce lot.

## Bilan attendu

**R23-L = diagnostic agrégé outillé uniquement, HYPOTHÈSE MAPPING NON RÉSOLUE.** Un CI vert ne qualifie pas les 38 points ni ne sélectionne un détecteur. `CEPH_DETECTOR_SELECTED` non satisfait ; **CLINICAL NO-GO**, 6 HOLD Ricketts maintenus, roadmap 41/99. Aucune modification du modèle, de la nomenclature runtime, du backend métier, du cabinet, de Production ni de la base patient. PR DRAFT, no merge/deploy.
