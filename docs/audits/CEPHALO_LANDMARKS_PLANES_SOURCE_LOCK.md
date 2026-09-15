# Céphalo-N — Source-lock des landmarks, plans et lignes

Statut : **AUDIT SOURCE-LOCK V2 — ZÉRO NOUVELLE FORMULE CLINIQUE**

Date : 2026-09-15

Dépend de : `docs/audits/CEPHALO_GLOBAL_ANALYSIS_VALIDATION.md`

Complément provenance : `docs/audits/CEPHALO_SRPOSE38_PROVENANCE.md`

## Goal / Succès / Preuve

**Goal** — figer le vocabulaire anatomique et les référentiels géométriques nécessaires aux analyses validées Steiner, Tweed, McNamara, Ricketts et `COM_DC_LEGACY_V1`, avant toute nouvelle implémentation de mesure.

**Succès** — chaque landmark et chaque plan/ligne est classé sans confondre : existence géométrique, existence d’un ID logiciel, liaison automatique SRPose, identité anatomique démontrée, construction, absence et blocage de modalité.

**Preuve** — comparaison entre la cartographie clinique validée, les moteurs géométriques Digital Crown, `sota_vision_service.py`, `srpose38_pipeline.py`, `cephalo_runtime_evidence.py`, l’historique Git du mapping 38 points et le dépôt source exact du checkpoint SRPose certifié.

## États utilisés

- `EXISTS_GEOMETRY` : primitive géométrique déjà présente.
- `LEGACY_AUTO_UNVERIFIED` : ID produit par le mapping SRPose local, sans preuve anatomique amont suffisante.
- `CONSTRUCTED` : point/axe construit par une convention explicite.
- `MISSING` : point ou contrat absent.
- `AMBIGUOUS` : symbole présent mais plusieurs définitions possibles.
- `SOURCE_LOCK_REQUIRED` : définition/convention ou liaison détecteur non suffisamment prouvée.
- `BLOCKED_MODALITY` : impossible dans la modalité actuelle.
- `WRONG_VARIANT` : variante voisine existante mais non interchangeable.

## Règles verrouillées

1. Aucun nouveau calcul clinique dans ce lot.
2. Un alias logiciel n’est jamais une preuve d’équivalence anatomique.
3. `Pog` dur ≠ `Pog'` mou.
4. `Gn` anatomique ≠ `Gn` construit d’une analyse.
5. `Pt` ≠ `PTM/Ptm` tant que la convention source ne l’établit pas explicitement.
6. `Po` signifie Porion anatomique lorsqu’un plan de Frankfort clinique est requis ; aucun point machine n’est substitué silencieusement.
7. Bord incisif / apex / surface labiale coronaire sont trois concepts différents.
8. `Go-Me`, `Go-Gn` et `sub-Go-M` sont des plans mandibulaires différents et versionnés par analyse.
9. Le frontal/PA Ricketts reste `BLOCKED_MODALITY` tant qu’un pipeline frontal validé n’existe pas.
10. L’existence d’un mapping logiciel `index → nom` ne prouve pas sa sémantique anatomique.
11. La non-régression impose de préserver le mapping SRPose historique tant qu’aucune migration clinique contrôlée n’est décidée ; cette préservation ne le transforme pas en preuve scientifique.

---

# 1. Réalité moteur actuelle

## 1.1 Contrat générique

`cephalo_engine.py` accepte actuellement des clés canoniques et plusieurs alias, notamment :

- `S`: `S`, `Sella`
- `N`: `N`, `Nasion`
- `Po`: `Po`, `Porion`
- `Or`: `Or`, `Orbitale`
- `A`: `A`, `Point_A`
- `B`: `B`, `Point_B`
- `Go`: `Go`, `Gonion`
- `Me`: `Me`, `Menton`
- `U1i`: `U1i`, `U1_incisal`, `11_incisal`, `UIe`
- `U1a`: `U1a`, `U1_apex`, `11_apex`, `UIa`
- `L1i`: `L1i`, `L1_incisal`, `41_incisal`, `LIe`
- `L1a`: `L1a`, `L1_apex`, `41_apex`, `LIa`
- `Prn`, `Pog_soft`, `Sn`, `Ls`, `Li`
- `Co`: `Co`, `Condylion`, `Condyle`
- `Gn`: `Gn`, `Gnathion`
- `ANS`: `ANS`, `ENA`, `Anterior_Nasal_Spine`
- `Occ_Ant`, `Occ_Post`

**Décision V2** : ces alias sont des chemins logiciels observés. La future couche scientifique ne doit accepter une équivalence que si la définition anatomique et la provenance sont explicites.

## 1.2 SRPose38 : résultat de l’audit de provenance

Le runtime certifié impose :

- modèle `srpose38-tta-1024.onnx` ;
- SHA256 `a5ecd466d6d2c4ef02e145a143076a05720c0be56a260224812c23e2ecf42ddb` ;
- `SRPOSE38_NUM_LANDMARKS = 38` ;
- sortie exacte de 38 heatmaps ;
- checkpoint source `5k5000/CLdetection2023`, commit `18d17d1934970016e7610c4849311900b8d1f191`.

Digital Crown possède un mapping local dans `sota_vision_service.py` :

| Index | ID local | Index | ID local |
|---:|---|---:|---|
| 0 | S | 19 | D_point |
| 1 | N | 20 | U1_apex |
| 2 | Or | 21 | L1_apex |
| 3 | Po | 22 | Cm |
| 4 | A | 23 | Ptm |
| 5 | B | 24 | Co |
| 6 | Pog | 25 | Prn |
| 7 | Me | 26 | Ba |
| 8 | Gn | 27 | PT_point |
| 9 | Go | 28 | Bo |
| 10 | L1_incisal | 29 | Ls2 |
| 11 | U1_incisal | 30 | Li2 |
| 12 | Ls_soft | 31 | Gn_soft |
| 13 | Li_soft | 32 | Me_soft |
| 14 | Sn_soft | 33 | G_soft |
| 15 | Pog_soft | 34 | N_soft |
| 16 | PNS | 35 | C_point |
| 17 | ANS | 36 | U6 |
| 18 | Ar | 37 | L6 |

**Point crucial** : le dépôt source exact du checkpoint définit ses `keypoint_info` uniquement comme catégories numériques `0..37`. Il ne donne pas de noms anatomiques. Le code Digital Crown actuel indique lui-même que la parité d’inférence est distincte de la validation clinique de la nomenclature.

Donc :

`SOTA_LANDMARKS_MAPPING = LEGACY_AUTO_UNVERIFIED`

et non `SOURCE_PROVEN_ANATOMY`.

Cette distinction corrige l’ancien constat trop grossier « mapping absent ». Le mapping existe, mais sa sémantique anatomique n’est pas source-lockée.

## 1.3 Chaîne d’autorité runtime

`cephalo_runtime_evidence.py` importe le mapping local, exige exactement ses 38 IDs en mode `SOTA_ONNX_38`, puis persiste modèle, SHA256 et version de pipeline dans la preuve de landmark.

Cela prouve correctement **quel modèle et quelle sortie logicielle** ont produit un point. Cela ne prouve pas **que le nom anatomique attaché au canal est celui du contrat d’annotation historique**.

## 1.4 Géométries déjà versionnées à conserver

- Steiner : SNA, SNB, ANB, U1-NA angulaire, L1-NB angulaire, SN/Go-Gn.
- Tweed : FMA `Go-Me / Po-Or`, IMPA `L1 / Go-Me`, FMIA `L1 / Po-Or`.
- McNamara : segments Co-A, Co-Gn, ANS-Me avec calibration fail-closed.
- Ricketts : facial depth, Gn construit V1, facial axis, convexité maxillaire, E-line V1 legacy + V2 perpendiculaire.
- CRANIOM/COM : Situation A, Situation B, A'B', profondeur faciale legacy, U1/FH, L1/Downs, interincisif, avec conventions versionnées ou contrats bloqués.

---

# 2. Matrice latérale : science, moteur et disponibilité automatique

| ID scientifique cible | Classe | Usages | Géométrie/contrat DC | Liaison SRPose locale | Décision V2 |
|---|---|---|---|---|---|
| `S` | anatomique | Steiner; COM | EXISTS_GEOMETRY | index 0 `S` | auto `LEGACY_UNVERIFIED`; définition scientifique à figer |
| `N` | anatomique | Steiner; McNamara; Ricketts; COM | EXISTS_GEOMETRY | 1 `N` | idem |
| `A` | anatomique | Steiner; McNamara; Ricketts; COM | EXISTS_GEOMETRY | 4 `A` | idem |
| `B` | anatomique | Steiner; COM | EXISTS_GEOMETRY | 5 `B` | ne jamais substituer à Pog |
| `Po_anat` | anatomique | Tweed; McNamara; Ricketts; COM | EXISTS_GEOMETRY | 3 `Po` | `SOURCE_LOCK_REQUIRED` pour identité Porion anatomique |
| `Or` | anatomique | Tweed; McNamara; Ricketts; COM | EXISTS_GEOMETRY | 2 `Or` | auto non validé sémantiquement |
| `Go` | anatomique | Steiner; Tweed; COM | EXISTS_GEOMETRY | 9 `Go` | plan dépend de l’analyse |
| `Me` | anatomique | Tweed; McNamara; COM | EXISTS_GEOMETRY | 7 `Me` | auto non validé sémantiquement |
| `Gn_anat` | anatomique | Steiner; McNamara | symbole présent / ambigu | 8 `Gn` | séparer du Gn construit Ricketts |
| `Gn_Ricketts_constructed` | construit | Ricketts Facial Axis | CONSTRUCTED | aucune liaison directe nécessaire | garder ID distinct |
| `Pog_hard` | anatomique | McNamara; Ricketts | primitives possibles si point fourni | 6 `Pog` | `LEGACY_AUTO_UNVERIFIED`; ne jamais confondre avec Pog' |
| `Pog_soft` / `Pog'` | tissu mou | Ricketts E-line | EXISTS_GEOMETRY | 15 `Pog_soft` | liaison locale non prouvée anatomiquement |
| `Prn` | tissu mou | Ricketts E-plane | EXISTS_GEOMETRY | 25 `Prn` | idem |
| `Li` | tissu mou | Ricketts E-plane | EXISTS_GEOMETRY | 13 `Li_soft`; 30 `Li2` | deux IDs locaux : définition exacte requise |
| `Ls` | tissu mou | Ricketts extension; profil | EXISTS_GEOMETRY | 12 `Ls_soft`; 29 `Ls2` | deux IDs locaux : définition exacte requise |
| `Sn` | tissu mou | contexte McNamara | EXISTS_SYMBOL | 14 `Sn_soft` | auto non validé sémantiquement |
| `Co` / Condylion | anatomique | McNamara Co-A/Co-Gn | EXISTS_GEOMETRY | 24 `Co` | retirer l’équivalence future avec générique `Condyle`; source-lock Condylion |
| `Ba` | anatomique | McNamara/Ricketts | absent du contrat générique principal | 26 `Ba` | **pas réellement absent du mapping local** ; auto `LEGACY_UNVERIFIED` |
| `Pt_Ricketts` | source-spécifique | Ricketts Facial Axis | contrat cible manquant | 27 `PT_point` | ne pas déclarer `PT_point = Pt_Ricketts` sans source |
| `PTM_McNamara` | source-spécifique | McNamara | contrat cible manquant | 23 `Ptm` | ne pas déclarer équivalence avant source-lock |
| `ANS` | anatomique | McNamara; Ricketts | EXISTS_GEOMETRY | 17 `ANS` | auto non validé sémantiquement |
| `PNS` | anatomique | Ricketts palatal plane | absent du contrat générique principal | 16 `PNS` | **ID auto local existe**, sémantique à valider |
| `D_Steiner` | source-spécifique | Steiner 1959 | MISSING_CONTRACT | 19 `D_point` | `D_point = D_Steiner` non démontré |
| `Xi_Ricketts` | construit | Ricketts | MISSING | aucun | construction source-spécifique requise |
| `Pm_Ricketts` | source-spécifique | Ricketts | MISSING | aucun ID explicite | ne pas réutiliser Me/Pog |
| `subGo_M_Ricketts` | construit | Ricketts MP | MISSING_CONTRACT | n/a | ne pas substituer Go-Me |
| `U1_apex` | dentaire | Steiner; COM | EXISTS_GEOMETRY | 20 `U1_apex` | axe possible, auto non validé sémantiquement |
| `U1_incisal` | dentaire | Steiner; COM | EXISTS_GEOMETRY | 11 `U1_incisal` | bord incisif, pas surface labiale |
| `U1_labial_crown` | surface dentaire | Steiner linéaire; McNamara | MISSING | aucun ID explicite | bloquant |
| `L1_apex` | dentaire | Steiner; Tweed; COM | EXISTS_GEOMETRY | 21 `L1_apex` | auto non validé sémantiquement |
| `L1_incisal` | dentaire | Steiner; Tweed; Ricketts; COM | EXISTS_GEOMETRY | 10 `L1_incisal` | bord incisif |
| `L1_labial_crown` | surface dentaire | Steiner/McNamara selon protocole | MISSING | aucun ID explicite | bloquant |
| `U6_Steiner` | dentaire | Steiner suivi | contrat exact manquant | 36 `U6` | `U6` générique ≠ point Steiner prouvé |
| `L6_Steiner` | dentaire | Steiner suivi | contrat exact manquant | 37 `L6` | idem |
| `U6_Ricketts` | dentaire | Ricketts U6-PTV | contrat exact manquant | 36 `U6` | exact point molaire/repère non source-locké |
| `Occ_Ant` | construit/dentaire | plan occlusal | EXISTS_SYMBOL | aucun ID direct | définition Steiner à figer |
| `Occ_Post` | construit/dentaire | plan occlusal | EXISTS_SYMBOL | aucun ID direct | idem |
| `pharynx_upper_soft_palate` | airway | McNamara | MISSING | aucun | protocole 1984 exact requis |
| `pharynx_upper_wall` | airway | McNamara | MISSING | aucun | idem |
| `pharynx_lower_tongue` | airway | McNamara | MISSING | aucun | idem |
| `pharynx_lower_wall` | airway | McNamara | MISSING | aucun | idem |

## 2.1 Points SRPose locaux sans équivalence clinique validée pour les cinq analyses

Les IDs suivants existent dans le mapping local mais ne doivent pas être recyclés par ressemblance de nom :

- `Cm`
- `Ar`
- `Bo`
- `C_point`
- `G_soft`
- `N_soft`
- `Gn_soft`
- `Me_soft`
- `Ls2`
- `Li2`

Ils restent disponibles comme **observations logicielles legacy**, sans autorité nouvelle pour Steiner/Tweed/McNamara/Ricketts/COM tant que leur définition n’est pas source-lockée.

---

# 3. Landmarks PA/frontaux Ricketts 1981

Tous les éléments suivants sont `BLOCKED_MODALITY` dans le pipeline latéral actuel :

| Landmark / famille | Usage |
|---|---|
| `NC_R`, `NC_L` | largeur cavité nasale NC-NC |
| `Z_R`, `Z_L` | frontal facial reference |
| `J_R`, `J_L` | relation maxillaire / fronto-denture |
| `Ag_R`, `Ag_L` | largeur mandibulaire Ag-Ag / plans frontaux |
| `Cg` + repères de plan sagittal médian | asymétrie |
| `ANS_PA`, `Pog_PA` | asymétrie squelettique |
| `B6_R`, `B6_L` | largeur intermolaire / relation au fronto-denture |
| `B3_R`, `B3_L` | largeur intercanine |
| `U6_R`, `U6_L` | crossbite transverse |
| `iif` | midpoint incisives inférieures |

**Règle** : aucun de ces points ne doit être dérivé d’une téléradiographie de profil par projection, symétrisation ou heuristique.

---

# 4. Plans, lignes et axes source-lockés

| ID cible | Définition / landmarks | Analyse/version | État actuel |
|---|---|---|---|
| `SN_STEINER` | S-N | Steiner | EXISTS_GEOMETRY |
| `NA_STEINER` | N-A | Steiner | EXISTS_GEOMETRY |
| `NB_STEINER` | N-B | Steiner | EXISTS_GEOMETRY |
| `ND_STEINER_1959` | N-D | Steiner 1959 | MISSING_CONTRACT |
| `GOGN_STEINER` | Go-Gn anatomique | Steiner | PARTIAL ; distinguer Gn anatomique |
| `OCCLUSAL_STEINER` | définition primaire Steiner à partir des repères occlusaux validés | Steiner | SOURCE_LOCK_REQUIRED |
| `D_LINE_STEINER_1959` | ligne D selon protocole 1959 | Steiner 1959 | MISSING / SOURCE_LOCK_REQUIRED |
| `FH_TWEED_PO_OR` | Porion anatomique-Orbitale | Tweed | EXISTS_GEOMETRY ; identité des points auto à confirmer |
| `MP_TWEED_GO_ME` | Go-Me dans moteur actuel | Tweed | EXISTS_GEOMETRY ; garder version Tweed |
| `L1_AXIS` | L1 apex-incisal | Tweed/Steiner/COM | EXISTS_GEOMETRY |
| `U1_AXIS` | U1 apex-incisal | Steiner/COM | EXISTS_GEOMETRY |
| `FH_MCNAMARA_PO_OR` | Po-Or | McNamara | géométrie réutilisable, ID sémantique séparé |
| `N_PERP_MCNAMARA` | perpendiculaire à FH passant par N | McNamara | primitive EXISTS_GEOMETRY |
| `A_VERTICAL_MCNAMARA` | parallèle à N-perp passant par A | McNamara | NOT_EXPOSED_AS_VERSIONED_CONTRACT |
| `A_POG_MCNAMARA` | A-Pog dur | McNamara | dépend de Pog hard source-locké |
| `BA_N` | Ba-N | McNamara/Ricketts | géométrie possible ; Ba auto legacy non validé |
| `PTM_GN_MCNAMARA` | PTM-Gn selon convention 1984 | McNamara | SOURCE_LOCK_REQUIRED |
| `NPog_RICKETTS` | N-Pog dur facial plane | Ricketts | EXISTS_GEOMETRY si Pog fourni |
| `FH_RICKETTS` | Po-Or | Ricketts | EXISTS_GEOMETRY |
| `PT_GN_RICKETTS` | Pt-Gn construit | Ricketts | EXISTS_GEOMETRY ; identité `PT_point` non démontrée |
| `MP_RICKETTS` | plan mandibulaire source 1981 `sub-Go-M` | Ricketts | MISSING_CONTRACT ; ne pas substituer Tweed Go-Me |
| `PALATAL_RICKETTS` | ANS-PNS | Ricketts | géométriquement simple ; PNS auto legacy non validé |
| `APOG_RICKETTS` | A-Pog dur | Ricketts | dépend de Pog hard contractuel |
| `PTV_RICKETTS` | Pterygoid Vertical source 1981 | Ricketts | SOURCE_LOCK_REQUIRED |
| `E_LINE_RICKETTS` | Prn-Pog' | Ricketts | EXISTS_GEOMETRY V2 perpendiculaire |
| `CORPUS_AXIS_RICKETTS` | source-specific | Ricketts bend | MISSING / SOURCE_LOCK_REQUIRED |
| `CONDYLE_AXIS_RICKETTS` | source-specific | Ricketts bend | MISSING / SOURCE_LOCK_REQUIRED |
| `FH_CRANIOM` | Po-Or | COM | EXISTS_GEOMETRY as `FH_PO_OR_V1` |
| `N_VERTICAL_CRANIOM` | N-perp to FH | COM Situation A/B/depth | EXISTS_GEOMETRY |
| `DOWNS_MP_GO_ME` | Go-Me | COM L1/Downs | EXISTS source-referenced ; ne pas renommer Tweed/Ricketts |
| `FRONTAL_FACIAL_PLANE_R/L` | Z-Ag | Ricketts PA | BLOCKED_MODALITY |
| `FRONTO_DENTURE_R/L` | J-Ag | Ricketts PA | BLOCKED_MODALITY |
| `CENTRAL_SAGITTAL_PA` | convention 1981 source-lockée | Ricketts PA | BLOCKED_MODALITY / SOURCE_LOCK_REQUIRED |
| `FRONTAL_APO` | frontal A-Po | Ricketts PA | BLOCKED_MODALITY |

---

# 5. Réutilisable vs à corriger

## Réutilisable sans réécrire la géométrie

1. Primitives fail-closed de projection/distance et calibration.
2. Steiner angulaire déjà séparé dans son module.
3. Tweed FMA/IMPA/FMIA déjà séparé ; **FMIA existe déjà dans le backend**.
4. McNamara Co-A/Co-Gn/ANS-Me linéaires.
5. Ricketts facial depth, facial axis, convexité et E-line V2.
6. CRANIOM conventions explicitement versionnées.
7. Provenance modèle/hash/pipeline SRPose38 déjà persistable dans la chaîne d’évidence.

## À corriger avant toute extension clinique

1. Remplacer la confiance implicite dans les alias par un contrat anatomique explicite au point d’entrée scientifique.
2. Traiter `SOTA_LANDMARKS_MAPPING` comme `LEGACY_AUTO_UNVERIFIED`, pas comme dictionnaire anatomique officiel.
3. Séparer `Gn_anat` et `Gn_Ricketts_constructed` dans les contrats et preuves.
4. Introduire un `Pog_hard` explicite ; ne jamais réutiliser `Pog_soft` ni B.
5. Exiger `Co = Condylion` source-locké ; retirer toute équivalence silencieuse avec un générique `Condyle` dans la future couche scientifique.
6. Ajouter les surfaces coronaires U1/L1 avant les distances linéaires qui les exigent.
7. Source-locker Ba, Pt/PTM, PNS, D, U6/L6 avant d’utiliser les IDs SRPose locaux homonymes comme autorité clinique.
8. Ajouter Xi, Pm et les repères airway qui n’ont pas d’équivalent auto explicite.
9. Laisser tout Ricketts PA en fail-closed jusqu’à une modalité frontale validée.

---

# 6. Gaps par analyse après source-lock V2

## Steiner

- Angles principaux : géométrie largement présente.
- Le mapping local fournit S/N/A/B/Go/Gn/U1/L1 et un `D_point`, mais ces liaisons auto restent `LEGACY_UNVERIFIED`.
- Bloquants réels : surfaces coronaires U1/L1, définition D 1959, plan occlusal source-locké, définitions U6/L6 source-spécifiques, extension 1959.

## Tweed

- FMA, IMPA, FMIA : géométrie présente.
- Le trio Po/Or/Go-Me/L1 a des IDs locaux, mais l’identité anatomique automatique reste non validée.
- Pas de nouvelle formule nécessaire pour le triangle.

## McNamara

- Co-A, Co-Gn, ANS-Me présents géométriquement.
- Le mapping local contient Co, Pog, Ba et Ptm, mais aucun ne doit être promu automatiquement au contrat McNamara sans source-lock.
- Restent à définir : A-vertical exact, surfaces incisives si requises par la mesure, airway landmarks et conventions PTM/Gn.

## Ricketts

- Plusieurs primitives latérales sont présentes.
- Le mapping local contient Pog, Ba, PNS et `PT_point`, mais leur équivalence aux conventions Ricketts 1981 n’est pas démontrée.
- Xi, Pm, MP `sub-Go-M`, PTV/U6 exact et axes du mandibular bend restent à construire/source-locker.
- Les 12 facteurs frontaux restent `BLOCKED_MODALITY`.
- `Ag-Ag` reste `NORM HOLD`; ce lot ne lève pas le conflit normatif.

## COM_DC_LEGACY_V1

- Les constructions actuelles sont documentées et versionnées.
- Elles restent un composite interne ; aucune réattribution historique n’est autorisée.
- Les points auto utilisés par le flux legacy conservent leur comportement pour non-régression, sans extension de leur autorité scientifique.

---

# 7. Gate avant angles/distances supplémentaires

Une mesure supplémentaire n’est autorisée que si :

1. tous les landmarks requis ont un ID scientifique non ambigu ;
2. leur définition anatomique/construite et leur incidence sont source-lockées ;
3. le plan/axe exact est versionné par analyse ;
4. le point est fourni/corrigé manuellement avec provenance **ou** la liaison automatique détecteur→landmark a été validée ;
5. aucune variante voisine n’est substituée ;
6. la calibration mm est valide pour les distances ;
7. le transversal reste impossible sans PA/frontale validée.

## Gate SRPose borné

Le runtime et la provenance du modèle sont maintenant prouvés, mais la **sémantique anatomique du mapping local** reste `SOURCE_LOCK_REQUIRED`.

Conséquence :

- la géométrie et les contrats scientifiques peuvent avancer ;
- des fixtures manuelles explicites peuvent servir aux tests ;
- aucune nouvelle mesure ne peut obtenir son autorité clinique automatique du seul mapping local SRPose38.

---

# 8. Prochaine séquence

`définitions anatomiques primaires → contrats landmark IDs → plans/lignes versionnés → fixtures manuelles de référence → tests géométriques isolés → angles/distances → SVG synchronisé → logique par analyse → synthèse inter-analyses → onboarding ODF`

Aucune norme clinique nouvelle et aucune interprétation diagnostique n’est activée dans ce lot.

## Next exact

Source-locker maintenant les **définitions anatomiques et constructions** nécessaires aux mesures déjà validées, analyse par analyse, en commençant par le noyau réutilisable Steiner/Tweed/McNamara/Ricketts, sans utiliser la table SRPose locale comme source anatomique.