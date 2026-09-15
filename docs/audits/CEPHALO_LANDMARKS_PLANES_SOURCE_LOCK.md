# Céphalo-N — Source-lock des landmarks, plans et lignes

Statut : **AUDIT SOURCE-LOCK V4 — DÉCISION TWEED FERMÉE — ZÉRO NOUVELLE FORMULE CLINIQUE**

Date : 2026-09-15

Dépend de : `docs/audits/CEPHALO_GLOBAL_ANALYSIS_VALIDATION.md`

Compléments :

- `docs/audits/CEPHALO_SRPOSE38_PROVENANCE.md`
- `docs/audits/CEPHALO_PRIMARY_LANDMARK_CONSTRUCTIONS.md`

## Goal / Succès / Preuve

**Goal** — figer le vocabulaire anatomique et les référentiels nécessaires à Steiner, Tweed, McNamara, Ricketts et `COM_DC_LEGACY_V1` avant toute nouvelle mesure.

**Succès** — ne jamais confondre : primitive géométrique, ID logiciel, liaison SRPose, identité anatomique, point construit, variante d’analyse, absence et blocage de modalité.

**Preuve** — moteurs Digital Crown + provenance exacte SRPose38 + sources primaires Steiner 1953, Tweed 1954, Ricketts 1972/1981 et McNamara 1984 + décision clinique du 2026-09-15 de conserver le Frankfort Digital Crown `Po-Or` pour Tweed.

## États

- `MATCH_GEOMETRY` : géométrie conforme à la construction source.
- `LEGACY_AUTO_UNVERIFIED` : canal/ID automatique local présent, sémantique anatomique amont non démontrée.
- `CONSTRUCTED` : point construit par une convention explicite.
- `MISSING` : point/contrat absent.
- `SOURCE_LOCK_REQUIRED` : définition ou liaison détecteur insuffisamment prouvée.
- `BLOCKED_MODALITY` : modalité actuelle incapable de fournir l’information.
- `WRONG_VARIANT` : construction voisine non interchangeable avec la version historique stricte.
- `SELECTED_DC_CONTRACT` : convention explicitement retenue pour Digital Crown, sans prétendre être la reproduction historique stricte lorsqu’elle diffère.

---

# 1. Règles verrouillées

1. Aucun nouveau calcul clinique dans ce lot.
2. Un alias logiciel n’est pas une preuve anatomique.
3. `Pog` dur ≠ `Pog'` mou.
4. `Gn_anatomic` ≠ `Gn_constructed`.
5. `Pt_Ricketts` ≠ `PTM_McNamara`.
6. `Po_anatomic-Or` est la référence explicite de McNamara 1984 et Ricketts 1981. Pour Tweed dans Digital Crown, **la décision clinique est de conserver `Po-Or` comme contrat actif `DC_TWEED_ANATOMICAL_FH_VARIANT`**. La construction ear-rod de Tweed 1954 reste documentée comme version historique distincte et non active.
7. Bord incisif, apex et surface faciale/coronaire sont distincts.
8. `Go-Me`, `Go-Gn` et `Sub.Go.-M.` ne sont pas fusionnés par commodité.
9. Ricketts frontal/PA reste `BLOCKED_MODALITY` sans pipeline frontal validé.
10. La position d’un canal neuronal ne permet jamais de déduire son anatomie.
11. Le mapping SRPose legacy est préservé pour non-régression, sans devenir une autorité scientifique.
12. Les normes historiques Tweed 1954 ne doivent pas être présentées comme strictement source-concordantes avec `DC_TWEED_ANATOMICAL_FH_VARIANT` sans validation normative spécifique ; l’existant est préservé, mais toute nouvelle couche scientifique doit versionner explicitement ce point.

---

# 2. SRPose38 : contrat logiciel observé

Runtime certifié :

- modèle : `srpose38-tta-1024.onnx` ;
- SHA256 : `a5ecd466d6d2c4ef02e145a143076a05720c0be56a260224812c23e2ecf42ddb` ;
- sortie : 38 heatmaps ;
- checkpoint source : `5k5000/CLdetection2023` commit `18d17d1934970016e7610c4849311900b8d1f191`.

Le dépôt source exact du checkpoint nomme ses keypoints uniquement `0..37`. Il ne fournit aucun dictionnaire anatomique public.

Digital Crown possède néanmoins ce mapping local :

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

Classification :

`SOTA_LANDMARKS_MAPPING = LEGACY_AUTO_UNVERIFIED`

La chaîne d’évidence prouve modèle/hash/pipeline et ID logiciel produit. Elle ne prouve pas que `index 3 = Porion anatomique`, etc.

---

# 3. Matrice landmarks / constructions latérales

| ID scientifique cible | Analyse(s) | DC géométrie | SRPose local | Verdict |
|---|---|---|---|---|
| `S` | Steiner, COM | présent | `0:S` | `LEGACY_AUTO_UNVERIFIED` |
| `N` | Steiner, McNamara, Ricketts, COM | présent | `1:N` | idem |
| `A` | Steiner, McNamara, Ricketts, COM | présent | `4:A` | idem |
| `B` | Steiner, COM | présent | `5:B` | idem ; jamais Pog |
| `Po_anatomic` | McNamara, Ricketts, COM, Tweed/DC | Po-Or disponible | `3:Po` | géométrie oui ; auto non validé |
| `Or` | McNamara, Ricketts, COM, Tweed/DC | présent | `2:Or` | auto non validé |
| `Tweed_FH_earrod_point` | Tweed 1954 strict historique | absent | aucun | `HISTORICAL_NOT_SELECTED` |
| `Go` | Steiner, Tweed/DC, McNamara | présent | `9:Go` | auto non validé |
| `Me` | Tweed/DC, McNamara | présent | `7:Me` | auto non validé |
| `Gn_anatomic` | Steiner, McNamara Co-Gn | ID générique ambigu | `8:Gn` | séparer du construit |
| `Gn_cephalometric_constructed` | Ricketts axis; McNamara facial axis | construction possible | n/a | source-locké comme construction ; ID distinct requis |
| `Pog_hard` | McNamara, Ricketts | primitives présentes | `6:Pog` | auto non validé |
| `Pog_soft/Pog'` | Ricketts E-line | présent | `15:Pog_soft` | auto non validé |
| `Prn` | Ricketts E-line | présent | `25:Prn` | auto non validé |
| `Co/Condylion` | McNamara | segments présents | `24:Co` | définition primaire source-lockée ; canal non validé |
| `Ba` | McNamara/Ricketts | utilisable si fourni | `26:Ba` | auto non validé |
| `Pt_Ricketts` | Ricketts | facial axis présent | `27:PT_point` | définition source-lockée ; liaison canal non validée |
| `PTM_McNamara` | McNamara | contrat incomplet | `23:Ptm` | définition source-lockée ; liaison canal non validée |
| `ANS` | McNamara/Ricketts | présent | `17:ANS` | auto non validé |
| `PNS` | Ricketts palatal | point nécessaire | `16:PNS` | auto non validé |
| `D_Steiner_1959` | Steiner 1959 | absent | `19:D_point` | équivalence non démontrée |
| `Xi_Ricketts` | Ricketts | absent | aucun | définition/construction source-lockée, runtime manquant |
| `Pm_Ricketts` | Ricketts | absent | aucun | définition source-lockée, runtime manquant |
| `U1_apex` | Steiner/COM | présent | `20:U1_apex` | auto non validé |
| `U1_incisal` | Steiner/COM | présent | `11:U1_incisal` | auto non validé |
| `U1_facial_crown` | Steiner linéaire/McNamara | absent | aucun explicite | `MISSING` |
| `L1_apex` | Steiner/Tweed/COM | présent | `21:L1_apex` | auto non validé |
| `L1_incisal` | Steiner/Tweed/Ricketts/COM | présent | `10:L1_incisal` | auto non validé |
| `L1_facial_crown` | Steiner linéaire/McNamara | absent | aucun explicite | `MISSING` |
| `U6_Ricketts_distal_crown` | Ricketts U6-PTV | contrat absent | `36:U6` générique | ne pas assimiler |
| `U6_Steiner` | Steiner suivi | contrat absent | `36:U6` | ne pas assimiler |
| `L6_Steiner` | Steiner suivi | contrat absent | `37:L6` | ne pas assimiler |
| `upper_pharynx_soft_palate` | McNamara | absent | aucun | définition source-lockée ; runtime manquant |
| `upper_pharynx_wall` | McNamara | absent | aucun | idem |
| `lower_pharynx_tongue-mandible` | McNamara | absent | aucun | définition source-lockée ; runtime manquant |
| `lower_pharynx_wall` | McNamara | absent | aucun | idem |

Les IDs locaux `Cm`, `Ar`, `Bo`, `C_point`, `G_soft`, `N_soft`, `Gn_soft`, `Me_soft`, `Ls2`, `Li2` ne reçoivent aucune nouvelle autorité clinique par ressemblance de nom.

---

# 4. Plans / lignes / axes versionnés

| Contrat cible | Définition source | Version | État DC |
|---|---|---|---|
| `SN_STEINER` | S-N | Steiner 1953 | `MATCH_GEOMETRY` |
| `NA_STEINER` | N-A | Steiner 1953 | `MATCH_GEOMETRY` |
| `NB_STEINER` | N-B | Steiner 1953 | `MATCH_GEOMETRY` |
| `GOGN_STEINER` | Go-Gn | Steiner 1953 | géométrie présente ; Gn anatomique à distinguer |
| `OCCLUSAL_STEINER` | plan occlusal vs SN | Steiner 1953 | `SOURCE_LOCK_REQUIRED` pour repères exacts |
| `ND_STEINER_1959` | N-D | Steiner 1959 | `MISSING` |
| `D_LINE_STEINER_1959` | convention 1959 | Steiner 1959 | `SOURCE_LOCK_REQUIRED` |
| `FH_TWEED_1954_STRICT` | point 4,5 mm au-dessus centre ear-rod → bord inférieur orbite | Tweed 1954 historique | `HISTORICAL_NOT_SELECTED` |
| `FH_DC_TWEED_PO_OR_V1` | Porion anatomique-Orbitale | variante DC retenue | **`SELECTED_DC_CONTRACT`** |
| `MP_TWEED_DC_GO_ME` | Go-Me | variante DC actuelle | présent |
| `L1_AXIS` | apex→bord incisif | Tweed | `MATCH_GEOMETRY` |
| `FH_MCNAMARA` | Porion anatomique-Orbitale | McNamara 1984 | `MATCH_GEOMETRY`; inputs auto non validés |
| `N_PERP_MCNAMARA` | ⟂ FH par N | McNamara 1984 | primitive présente |
| `A_VERTICAL_MCNAMARA` | parallèle N-perp par A | McNamara 1984 | non exposé comme contrat complet |
| `A_POG_MCNAMARA` | A-Pog dur | McNamara 1984 | possible ; surfaces incisives manquantes |
| `MP_MCNAMARA` | Go-Me | McNamara 1984 | primitive possible |
| `FACIAL_PLANE_MCNAMARA` | N-Pog | McNamara 1984 | primitive possible |
| `FACIAL_AXIS_MCNAMARA` | PTM→Gn construit vs Ba-N | McNamara 1984 | `PARTIAL` |
| `FH_RICKETTS` | true Porion-Orbitale, pas ear-rod | Ricketts 1981 | `MATCH_GEOMETRY`; auto IDs non validés |
| `NPog_RICKETTS` | N-Pog | Ricketts 1981 | présent |
| `PT_GN_RICKETTS` | Pt-Gn céphalométrique | Ricketts 1972/1981 | `MATCH_GEOMETRY`; Pt input auto non validé |
| `GN_RICKETTS_CONSTRUCTED` | intersection facial plane + mandibular plane | Ricketts 1972 | construction DC correspondante |
| `MP_RICKETTS_1981` | FH vs `Sub.Go.-M.` | Ricketts 1981 | `MISSING / SOURCE_LOCK_REQUIRED` |
| `PALATAL_RICKETTS` | ANS-PNS | Ricketts 1981 | géométrie simple ; PNS auto non validé |
| `ORAL_GNOMON_RICKETTS` | ANS-Xi-Pm | Ricketts 1981 | `MISSING` |
| `PTV_RICKETTS` | verticale à true FH depuis le repère pterygoïdien source | Ricketts 1981 | `MISSING_STRICT_CONTRACT` |
| `E_LINE_RICKETTS` | Prn-Pog' | Ricketts | V2 perpendiculaire présent |
| `CORPUS_AXIS_RICKETTS` | Xi-Pm | Ricketts 1981 | `MISSING` |
| `CONDYLE_AXIS_RICKETTS` | axe condylien source-spécifique | Ricketts 1981 | `MISSING` |
| `FH_CRANIOM` | Po-Or | COM legacy | présent et versionné |
| `N_VERTICAL_CRANIOM` | N-perp à FH | COM legacy | présent |
| `DOWNS_MP_GO_ME` | Go-Me | COM/Downs | présent ; garder distinct des contrats Tweed/Ricketts |

---

# 5. Findings par analyse

## Steiner

`MATCH_GEOMETRY` pour SNA, SNB, ANB, U1/NA angulaire, L1/NB angulaire et SN/Go-Gn. Les distances coronaires restent correctement fail-closed faute de surfaces coronaires dédiées. Steiner 1959 reste une couche séparée.

## Tweed

**Décision clinique fermée le 2026-09-15 : conserver le Frankfort Digital Crown `Po-Or`.** Le contrat actif devient `DC_TWEED_ANATOMICAL_FH_VARIANT`. Aucune migration ni modification de FMA/FMIA n’est requise : les valeurs runtime actuelles restent inchangées.

La construction `TWEED_1954_STRICT_EAR_ROD_FH` reste documentée comme historique, mais n’est pas le contrat choisi pour Digital Crown. En conséquence, toute nouvelle couche de normes/interprétation doit distinguer explicitement la variante DC `Po-Or` des normes historiquement dérivées d’un autre Frankfort ; aucun collage silencieux de norme « strict 1954 » n’est autorisé.

## McNamara

Les segments Co-A, Co-Gn et ANS-Me sont géométriquement cohérents si les landmarks sont valides. Le papier 1984 source-locke Porion anatomique, N-perp, Condylion, Gn anatomique, Gn construit, PTM, facial plane et airway. Les surfaces faciales des incisives restent manquantes.

## Ricketts

Facial depth et facial axis ont une base géométrique cohérente. Le Gn construit DC est compatible avec la définition du cephalometric Gn de Ricketts 1972. Xi, Pm, PTV/U6 strict, mandibular plane `Sub.Go.-M.` et mandibular bend restent incomplets. Les 12 facteurs frontaux restent bloqués par modalité.

## COM_DC_LEGACY_V1

Conserver ses conventions versionnées telles quelles pour non-régression. Ne pas les réattribuer à une analyse historique voisine.

---

# 6. Ricketts frontal/PA 1981

Tous les contrats suivants restent `BLOCKED_MODALITY` en latéral :

- NC-NC ;
- J droite/gauche vers frontal facial plane ;
- Ag-Ag ;
- symétrie médiane ;
- B6-B6 ;
- B3-B3 ;
- B6 droite/gauche vers J-Ag ;
- midpoint incisives inférieures vers frontal A-Po ;
- relations molaires transverses droite/gauche.

Le conflit normatif Ag-Ag reste `NORM_HOLD` : cue sheet +1,25 mm/an, tableau 9 +1,35 mm/an, et les valeurs âge 3→18 correspondent mathématiquement à +1,35 mm/an.

---

# 7. Gates avant nouvelle mesure

Une nouvelle mesure n’est autorisée que si :

1. landmarks non ambigus ;
2. définition anatomique/construite source-lockée ;
3. plan/axe versionné par analyse ;
4. provenance manuelle validée **ou** liaison automatique détecteur→landmark validée ;
5. aucune variante voisine substituée ;
6. calibration mm valide si nécessaire ;
7. modalité adaptée.

### État des gates

- **Tweed geometry** : `CLOSED` — contrat retenu `DC_TWEED_ANATOMICAL_FH_VARIANT = Po-Or`; runtime inchangé.
- **Tweed historical norms** : `SOURCE_LOCK_REQUIRED` pour toute future prétention de stricte concordance normative 1954 avec la variante DC.
- **SRPose semantics** : `SOURCE_LOCK_REQUIRED` pour toute extension automatique.
- **Ricketts PA** : `BLOCKED_MODALITY`.

---

# 8. Next exact

1. formaliser les contrats scientifiques séparés `Pt_Ricketts`, `PTM_McNamara`, `Gn_anatomic`, `Gn_constructed`, surfaces incisives, Xi/Pm et airway ;
2. préparer des fixtures manuelles source-lockées pour tests géométriques ;
3. conserver `Po-Or` pour Tweed sans migration runtime ;
4. ne promouvoir aucun canal SRPose legacy en vérité anatomique ;
5. valider séparément toute future couche normative Tweed appliquée à la variante DC.

Aucune norme, interprétation, UI ou valeur clinique runtime n’est modifiée par ce document.