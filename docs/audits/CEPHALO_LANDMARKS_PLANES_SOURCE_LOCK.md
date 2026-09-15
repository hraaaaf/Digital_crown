# Céphalo-N — Source-lock des landmarks, plans et lignes

Statut : **AUDIT SOURCE-LOCK V1 — ZÉRO NOUVELLE FORMULE CLINIQUE**

Date : 2026-09-15

Dépend de : `docs/audits/CEPHALO_GLOBAL_ANALYSIS_VALIDATION.md`

## Goal / Succès / Preuve

**Goal** — figer le vocabulaire anatomique et les référentiels géométriques nécessaires aux analyses validées Steiner, Tweed, McNamara, Ricketts et `COM_DC_LEGACY_V1`, avant toute nouvelle implémentation de mesure.

**Succès** — chaque landmark et chaque plan/ligne est classé `EXISTS`, `CONSTRUCTED`, `MISSING`, `AMBIGUOUS`, `SOURCE_LOCK_REQUIRED`, `BLOCKED_MODALITY` ou `WRONG_VARIANT`; aucune équivalence anatomique n’est déduite d’un alias de code.

**Preuve** — comparaison entre la cartographie clinique validée et les contrats géométriques présents dans `cephalo_engine.py`, `cephalo_steiner_geometry.py`, `cephalo_tweed_merrifield_geometry.py`, `cephalo_mcnamara_geometry.py`, `cephalo_ricketts_geometry.py`, `cephalo_constructions.py`, `cephalo_geometric_conventions.py` et `srpose38_pipeline.py`.

## Règles verrouillées

1. Aucun nouveau calcul clinique dans ce lot.
2. Un alias logiciel n’est jamais une preuve d’équivalence anatomique.
3. `Pog` dur ≠ `Pog'` mou.
4. `Gn` anatomique ≠ `Gn construit` d’une analyse.
5. `Pt` ≠ `PTM/Ptm` tant que la convention source ne l’établit pas explicitement.
6. `Po` signifie ici Porion anatomique lorsque Frankfort est construit; aucun Porion machine n’est substitué silencieusement.
7. Bord incisif / apex / surface labiale coronaire sont trois concepts différents.
8. Un plan mandibulaire est versionné par analyse; `Go-Me`, `Go-Gn`, `sub-Go-M` ne sont pas interchangeables.
9. Le frontal/PA Ricketts reste `BLOCKED_MODALITY` tant qu’un pipeline frontal validé n’existe pas.
10. L’ordre anatomique des 38 sorties SRPose38 doit être démontré par contrat/modèle/source; l’existence de 38 heatmaps ne suffit pas à nommer leurs indices.

---

# 1. Réalité moteur actuelle

## 1.1 Contrat générique

`cephalo_engine.py` accepte actuellement des clés canoniques et plusieurs alias :

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

**Décision V1** : ces alias restent un état logiciel observé. Ils ne deviennent pas un contrat scientifique sans définition source et mapping détecteur explicites.

## 1.2 SRPose38

Le runtime vérifié impose `SRPOSE38_NUM_LANDMARKS = 38` et attend une sortie de 38 heatmaps.

**État** : `SOURCE_LOCK_REQUIRED` pour le mapping **index 0..37 → nom anatomique → définition**. Aucun mapping n’a été identifié dans les fichiers inspectés pendant ce lot. Il est interdit de reconstruire cet ordre par intuition ou par proximité avec un autre modèle.

## 1.3 Géométries déjà versionnées à conserver

- Steiner : SNA, SNB, ANB, U1-NA angulaire, L1-NB angulaire, SN/Go-Gn.
- Tweed : FMA `Go-Me / Po-Or`, IMPA `L1 / Go-Me`, FMIA `L1 / Po-Or`.
- McNamara : segments Co-A, Co-Gn, ANS-Me avec calibration fail-closed.
- Ricketts : facial depth, Gn construit V1, facial axis, convexité maxillaire, E-line V1 legacy + V2 perpendiculaire.
- CRANIOM/COM : Situation A, Situation B, A'B', profondeur faciale legacy, U1/FH, L1/Downs, interincisif, tous avec conventions versionnées ou contrats bloqués.

---

# 2. Matrice des landmarks latéraux cibles

| ID scientifique | Classe | Analyses / usages validés | État DC V1 | Risque / action |
|---|---|---|---|---|
| `S` | anatomique | Steiner; COM | EXISTS | conserver définition Sella source-lockée |
| `N` | anatomique | Steiner; McNamara; Ricketts; COM | EXISTS | référence commune possible seulement si même définition anatomique |
| `A` | anatomique | Steiner; McNamara; Ricketts; COM | EXISTS | pas de problème identifié |
| `B` | anatomique | Steiner; COM | EXISTS | ne jamais substituer à Pog pour McNamara |
| `Po_anat` | anatomique | Tweed; McNamara; Ricketts; COM | EXISTS_SYMBOL / SOURCE_LOCK_REQUIRED | confirmer que le point fourni par le pipeline est bien Porion anatomique |
| `Or` | anatomique | Tweed; McNamara; Ricketts; COM | EXISTS | utilisé avec Po pour FH |
| `Go` | anatomique | Steiner/Tweed/COM; constructions Ricketts | EXISTS | convention du plan mandibulaire dépend de l’analyse |
| `Me` | anatomique | Tweed; McNamara; COM; construction Gn Ricketts | EXISTS | ne pas substituer à Gn |
| `Gn_anat` | anatomique | Steiner; McNamara | EXISTS_SYMBOL / AMBIGUOUS | séparer explicitement de Gn construit Ricketts |
| `Gn_Ricketts_constructed` | construit | Ricketts Facial Axis | CONSTRUCTED | moteur V1 existe; garder ID distinct |
| `Pog_hard` | anatomique | McNamara Pog-Nperp; Ricketts facial plane/convexity | SOURCE_LOCK_REQUIRED | moteur générique n’expose pas `Pog` dur dans son mapping principal |
| `Pog_soft` | tissu mou | Ricketts E-line; Merrifield séparé | EXISTS | jamais alias de Pog dur |
| `Prn` | tissu mou | Ricketts E-plane | EXISTS | conserver distinct de Sn |
| `Li` | tissu mou | Ricketts E-plane core | EXISTS | E-line lower lip core 1981 |
| `Ls` | tissu mou | Ricketts E-line extension; contexte tissus mous | EXISTS | optionnel pour Ricketts 1981 Summary |
| `Sn` | tissu mou | McNamara contexte nasolabial | EXISTS | contexte, pas mesure core 13 |
| `Co` | anatomique | McNamara Co-A / Co-Gn | EXISTS_SYMBOL / SOURCE_LOCK_REQUIRED | alias `Condyle` trop permissif; exiger Condylion défini |
| `Ba` | anatomique | McNamara/Ricketts Facial Axis | MISSING_FROM_GENERIC_CONTRACT | nécessaire |
| `Pt_Ricketts` | anatomique/construction source | Ricketts Facial Axis | MISSING / SOURCE_LOCK_REQUIRED | ne pas confondre avec PTM |
| `PTM_McNamara` | anatomique/construction source | McNamara facial-axis convention | MISSING / SOURCE_LOCK_REQUIRED | versionner séparément de Pt si définitions diffèrent |
| `ANS` | anatomique | McNamara; Ricketts; Steiner plan palatal si utilisé | EXISTS | alias ENA acceptable seulement comme traduction contrôlée |
| `PNS` | anatomique | Ricketts palatal plane | MISSING | nécessaire |
| `D_Steiner` | construit/anatomique selon protocole Steiner | Steiner 1959 SND/D-line | MISSING | définition primaire obligatoire avant implémentation |
| `Xi_Ricketts` | construit | Ricketts Oral Gnomon / axes mandibulaires | MISSING | construction source-spécifique requise |
| `Pm_Ricketts` | anatomique/construit selon convention | Ricketts Oral Gnomon | MISSING | source-lock requis |
| `subGo_M_Ricketts` | construit | Ricketts mandibular plane | MISSING / SOURCE_LOCK_REQUIRED | ne pas substituer Go-Me |
| `U1_apex` | dentaire | Steiner; COM; axes | EXISTS | axe dentaire seulement |
| `U1_incisal` | dentaire | Steiner; COM; axes | EXISTS | bord incisif, pas surface labiale |
| `U1_labial_crown` | dentaire surface | Steiner U1-NA linéaire; McNamara U1-A vertical | MISSING | bloque les distances linéaires correspondantes |
| `L1_apex` | dentaire | Steiner; Tweed; COM | EXISTS | axe dentaire seulement |
| `L1_incisal` | dentaire | Steiner; Tweed; Ricketts interincisal; COM | EXISTS | bord incisif |
| `L1_labial_crown` | dentaire surface | Steiner L1-NB linéaire; McNamara/Ricketts L1-A-Pog si source exige surface | MISSING | ne pas remplacer par bord incisif sans source |
| `U6_Steiner` | dentaire | Steiner suivi U6-NA | MISSING / SOURCE_LOCK_REQUIRED | point molaire exact à définir |
| `L6_Steiner` | dentaire | Steiner suivi L6-NB | MISSING / SOURCE_LOCK_REQUIRED | point molaire exact à définir |
| `U6_Ricketts` | dentaire | Ricketts U6-PTV | MISSING / SOURCE_LOCK_REQUIRED | peut différer du point molaire Steiner |
| `Occ_Ant` | dentaire construit | plan occlusal | EXISTS_SYMBOL / SOURCE_LOCK_REQUIRED | définition du plan occlusal Steiner à figer |
| `Occ_Post` | dentaire construit | plan occlusal | EXISTS_SYMBOL / SOURCE_LOCK_REQUIRED | idem |
| `pharynx_upper_soft_palate` | tissu mou/airway | McNamara upper pharynx | MISSING | protocole 1984 exact requis |
| `pharynx_upper_wall` | tissu mou/airway | McNamara upper pharynx | MISSING | protocole 1984 exact requis |
| `pharynx_lower_tongue` | tissu mou/airway | McNamara lower pharynx | MISSING | protocole 1984 exact requis |
| `pharynx_lower_wall` | tissu mou/airway | McNamara lower pharynx | MISSING | protocole 1984 exact requis |

---

# 3. Landmarks PA/frontaux Ricketts 1981

Tous les éléments suivants sont **`BLOCKED_MODALITY`** dans le pipeline latéral actuel :

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
| `SN_STEINER` | S-N | Steiner | EXISTS |
| `NA_STEINER` | N-A | Steiner | EXISTS |
| `NB_STEINER` | N-B | Steiner | EXISTS |
| `ND_STEINER_1959` | N-D | Steiner 1959 | MISSING |
| `GOGN_STEINER` | Go-Gn anatomique | Steiner | PARTIAL; distinguer Gn anatomique |
| `OCCLUSAL_STEINER` | définition primaire Steiner à partir des repères occlusaux validés | Steiner | SOURCE_LOCK_REQUIRED |
| `D_LINE_STEINER_1959` | ligne D selon protocole 1959 | Steiner 1959 | MISSING / SOURCE_LOCK_REQUIRED |
| `FH_TWEED_PO_OR` | Porion anatomique-Orbitale | Tweed | EXISTS; source identity of Po to confirm |
| `MP_TWEED_GO_ME` | Go-Me dans moteur actuel | Tweed | EXISTS; garder version Tweed |
| `L1_AXIS` | L1 apex-incisal | Tweed/Steiner/COM | EXISTS |
| `U1_AXIS` | U1 apex-incisal | Steiner/COM | EXISTS |
| `FH_MCNAMARA_PO_OR` | Po-Or | McNamara | REUSABLE geometry, separate semantic ID |
| `N_PERP_MCNAMARA` | perpendiculaire à FH passant par N | McNamara | geometry primitive EXISTS |
| `A_VERTICAL_MCNAMARA` | parallèle à N-perp passant par A | McNamara | NOT EXPOSED AS VERSIONED CONTRACT |
| `A_POG_MCNAMARA` | A-Pog dur | McNamara | MISSING until Pog hard source-lock |
| `BA_N` | Ba-N | McNamara/Ricketts | MISSING landmarks |
| `PTM_GN_MCNAMARA` | PTM-Gn selon convention 1984 | McNamara | SOURCE_LOCK_REQUIRED |
| `NPog_RICKETTS` | N-Pog dur facial plane | Ricketts | geometry EXISTS if Pog supplied |
| `FH_RICKETTS` | Po-Or | Ricketts | geometry EXISTS |
| `PT_GN_RICKETTS` | Pt-Gn construit | Ricketts | geometry EXISTS, missing landmark supply/source map |
| `MP_RICKETTS` | plan mandibulaire source 1981 `sub-Go-M` | Ricketts | MISSING; ne pas substituer Tweed Go-Me |
| `PALATAL_RICKETTS` | ANS-PNS | Ricketts | MISSING PNS |
| `APOG_RICKETTS` | A-Pog dur | Ricketts | MISSING Pog hard contract |
| `PTV_RICKETTS` | Pterygoid Vertical source 1981 | Ricketts | SOURCE_LOCK_REQUIRED |
| `E_LINE_RICKETTS` | Prn-Pog' | Ricketts | EXISTS V2 perpendicular distance |
| `CORPUS_AXIS_RICKETTS` | source-specific | Ricketts bend | MISSING / SOURCE_LOCK_REQUIRED |
| `CONDYLE_AXIS_RICKETTS` | source-specific | Ricketts bend | MISSING / SOURCE_LOCK_REQUIRED |
| `FH_CRANIOM` | Po-Or | COM | EXISTS as `FH_PO_OR_V1` |
| `N_VERTICAL_CRANIOM` | N-perp to FH | COM Situation A/B/depth | EXISTS |
| `DOWNS_MP_GO_ME` | Go-Me | COM L1/Downs | EXISTS source-referenced; ne pas renommer Tweed/Ricketts |
| `FRONTAL_FACIAL_PLANE_R/L` | Z-Ag | Ricketts PA | BLOCKED_MODALITY |
| `FRONTO_DENTURE_R/L` | J-Ag | Ricketts PA | BLOCKED_MODALITY |
| `CENTRAL_SAGITTAL_PA` | convention 1981 source-lockée | Ricketts PA | BLOCKED_MODALITY / SOURCE_LOCK_REQUIRED |
| `FRONTAL_APO` | frontal A-Po | Ricketts PA | BLOCKED_MODALITY |

---

# 5. Réutilisable vs à corriger

## Réutilisable sans réécrire la géométrie

1. Primitives fail-closed de projection/distance et calibration.
2. Steiner angulaire déjà séparé dans son module.
3. Tweed FMA/IMPA/FMIA déjà séparé; **FMIA existe déjà dans le backend**.
4. McNamara Co-A/Co-Gn/ANS-Me linéaires.
5. Ricketts facial depth, facial axis, convexité et E-line V2.
6. CRANIOM conventions explicitement versionnées.

## À corriger avant toute extension clinique

1. Remplacer la confiance implicite dans les alias par un contrat anatomique explicite au point d’entrée.
2. Source-locker le mapping des 38 sorties SRPose38 avant de prétendre qu’un index représente un landmark donné.
3. Séparer `Gn_anat` et `Gn_Ricketts_constructed` dans les contrats et preuves.
4. Introduire un `Pog_hard` explicite; ne jamais réutiliser `Pog_soft` ni B.
5. Exiger `Co` = Condylion source-locké; retirer toute équivalence silencieuse avec un générique `Condyle` dans la future couche scientifique.
6. Ajouter les surfaces coronaires U1/L1 avant les distances linéaires Steiner/McNamara qui les exigent.
7. Ajouter Ba, Pt/PTM versionnés, PNS, Xi, Pm et les repères molaires source-spécifiques seulement lorsque leur définition et leur provenance sont figées.
8. Laisser tout Ricketts PA en fail-closed jusqu’à une modalité frontale validée.

---

# 6. Gaps par analyse après source-lock

## Steiner

- Angles principaux : géométrie largement présente.
- Bloquants : surfaces coronaires U1/L1, D 1959, plan occlusal source-lock, U6/L6 source-spécifiques, extension 1959.

## Tweed

- FMA, IMPA, FMIA : géométrie présente.
- Bloquant principal : exposition/chaînage et confirmation contractuelle de Po anatomique; pas de nouvelle formule nécessaire pour le triangle.

## McNamara

- Co-A, Co-Gn, ANS-Me présents.
- Manquent/à verrouiller : Pog dur, Ba, PTM/Gn convention, A-Nperp contractuel McNamara, A-vertical, surfaces incisives, airway landmarks.

## Ricketts

- Plusieurs primitives latérales présentes mais la couverture 11/23 reste incomplète.
- Manquent/à verrouiller : Pt supply, Ba, PNS, Xi, Pm, MP Ricketts, PTV/U6, bend axes, Pog dur contractuel.
- Les 12 facteurs frontaux restent `BLOCKED_MODALITY`.
- `Ag-Ag` reste `NORM HOLD`; ce lot ne lève pas le conflit normatif.

## COM_DC_LEGACY_V1

- Les constructions actuelles sont documentées et versionnées.
- Elles restent un composite interne; aucune réattribution historique n’est autorisée.

---

# 7. Gate avant angles/distances supplémentaires

Le lot géométrique suivant n’est autorisé que si, pour chaque mesure à implémenter :

1. tous les landmarks requis ont un ID scientifique non ambigu;
2. leur définition anatomique/construite et leur incidence sont source-lockées;
3. le plan/axe exact est versionné par analyse;
4. le mapping détecteur → landmark est prouvé ou le point est fourni/corrigé manuellement avec provenance;
5. aucune variante voisine n’est substituée;
6. la calibration mm est valide pour les distances;
7. le transversal reste impossible sans PA/frontale validée.

## Gate encore ouvert

**Le mapping anatomique complet SRPose38 38-index est actuellement `SOURCE_LOCK_REQUIRED`.** Tant qu’il n’est pas démontré, ce document autorise la classification et la préparation des contrats, mais pas l’activation automatique de nouveaux landmarks détectés.

---

# 8. Prochaine séquence

`source-lock mapping détecteur → contrats landmark IDs → plans/lignes versionnés → tests géométriques isolés → angles/distances → SVG synchronisé → logique par analyse → synthèse inter-analyses → onboarding ODF`

Aucune norme clinique nouvelle et aucune interprétation diagnostique n’est activée dans ce lot.