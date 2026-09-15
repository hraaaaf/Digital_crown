# Céphalo-N — Registre canonique des mesures

Statut : **WORKING V2 — MESURES D'ABORD, ANALYSES ENSUITE — CHANTIER CÉPHALO-N ACTIF**

Date : 2026-09-15

> **Priorité de continuité : le chantier Céphalo-N / tracé céphalométrique est toujours actif et non clos.** Ce registre fait partie de ce chantier. `ORTHO_MODULE_V2.md` est une roadmap future et ne doit pas interrompre le closeout Céphalo-N.

## Goal / Succès / Preuve

**Goal** — construire un catalogue unique de mesures céphalométriques, indépendant des analyses, afin que Steiner / Tweed / McNamara / Ricketts / COM ne fassent ensuite que référencer les mesures qu'elles utilisent.

**Succès** — une géométrie donnée n'existe qu'une seule fois dans le registre. Deux lignes ne restent distinctes que si au moins un élément scientifique change : landmark, plan/ligne, point dentaire exact, modalité, opération, signe ou convention géométrique.

**Preuve** — périmètre dérivé de la cartographie A–E validée et des source-locks déjà mergés : `CEPHALO_GLOBAL_ANALYSIS_VALIDATION.md`, `CEPHALO_GLOBAL_ANALYSIS_CARTOGRAPHY.md`, `CEPHALO_LANDMARKS_PLANES_SOURCE_LOCK.md`, `CEPHALO_PRIMARY_LANDMARK_CONSTRUCTIONS.md`.

> Ce V2 couvre **toutes les mesures du périmètre scientifique A–E validé**. Il ne prétend pas couvrir toute mesure publiée dans toute l'histoire de la céphalométrie.

## Architecture retenue

```text
LANDMARKS / CONSTRUCTIONS
          ↓
CANONICAL MEASUREMENT REGISTRY
          ↓
ANALYSIS PROFILE
  Steiner / Tweed / McNamara / Ricketts / COM
          ↓
NORMS / INTERPRETATION propres à la version de l'analyse
```

Une analyse **ne possède pas** une formule. Elle référence un `measurement_id` canonique et lui associe ensuite sa version, son statut core/optionnel et sa norme éventuelle.

## Règles de dédoublonnage

1. Même géométrie + mêmes landmarks + même convention de signe + même modalité = **une mesure canonique**, même si plusieurs auteurs l'utilisent.
2. Même nom mais landmarks différents = **deux mesures**.
3. Même plan général mais point dentaire différent (`edge` vs `facial surface`) = **deux mesures**.
4. `Gn_anatomic` ≠ `Gn_constructed`.
5. `Pt_Ricketts` ≠ `PTM_McNamara`.
6. `Pog_hard` ≠ `Pog_soft`.
7. `Go-Me` ≠ `Go-Gn` ≠ `Sub.Go.-M`.
8. Profil ≠ PA/frontale.
9. Une mesure bloquée reste dans le registre avec son gate ; elle n'est jamais remplacée par une approximation voisine.
10. Les normes ne font pas partie de l'identité mathématique de la mesure ; elles seront rattachées dans les profils d'analyse.

## Légende des états

- `GEOMETRY_COVERED` : géométrie implémentée/testée.
- `PRIMITIVE_AVAILABLE` : primitive mathématique présente mais contrat canonique dédié à matérialiser.
- `IMPLEMENTATION_MISSING` : définition verrouillée, fonction dédiée absente.
- `BLOCKED_LANDMARK` : landmark exact absent/non certifié.
- `BLOCKED_MODALITY_PA` : nécessite une vraie incidence PA/frontale.
- `SOURCE_LOCK_REQUIRED` : sémantique exacte encore insuffisante.
- `LEGACY_TO_AUDIT` : comportement DC existe mais provenance/convention à verrouiller avant promotion canonique.

---

# 1. Squelettique sagittal / AP

| ID canonique | Mesure | Géométrie canonique | Landmarks | Type/unité | État |
|---|---|---|---|---|---|
| `M_SNA_DEG_V1` | SNA | angle SN / NA | S,N,A | angle ° | `GEOMETRY_COVERED` |
| `M_SNB_DEG_V1` | SNB | angle SN / NB | S,N,B | angle ° | `GEOMETRY_COVERED` |
| `M_ANB_DEG_V1` | ANB | angle NA / NB, compatible avec SNA−SNB selon convention verrouillée | S,N,A,B | angle ° | `GEOMETRY_COVERED` |
| `M_SND_DEG_V1` | SND | angle SN / ND | S,N,D | angle ° | `BLOCKED_LANDMARK` |
| `M_A_NPERP_MM_V1` | A → N-perp | distance AP signée de A à la perpendiculaire à FH passant par N | A,N,Po_anatomic,Or | mm signé | `PRIMITIVE_AVAILABLE` |
| `M_B_NPERP_MM_V1` | B → N-perp | même construction avec B | B,N,Po_anatomic,Or | mm signé | `GEOMETRY_COVERED` côté DC legacy |
| `M_POG_NPERP_MM_V1` | Pog → N-perp | même construction avec Pog hard | Pog_hard,N,Po_anatomic,Or | mm signé | `PRIMITIVE_AVAILABLE` |
| `M_POG_NB_MM_V1` | Pog → NB | distance perpendiculaire Pog hard → NB | Pog_hard,N,B | mm | `IMPLEMENTATION_MISSING` |
| `M_AB_PRIME_FH_MM_V1` | A′B′ | différence signée des projections de A et B sur FH | A,B,Po_anatomic,Or | mm signé | `GEOMETRY_COVERED` |
| `M_MAXILLARY_CONVEXITY_A_NPOG_MM_V1` | Convexité maxillaire | distance perpendiculaire signée A → N-Pog | A,N,Pog_hard | mm signé | `GEOMETRY_COVERED` |
| `M_FACIAL_ANGLE_NPOG_FH_DEG_V1` | Facial Angle | angle N-Pog / FH | N,Pog_hard,Po_anatomic,Or | angle ° | `GEOMETRY_COVERED`; runtime nommé actuellement `FACIAL_DEPTH` |
| `M_COM_S_NPERP_DEPTH_MM_V1` | Profondeur faciale legacy COM | magnitude S → N-perp | S,N,Po_anatomic,Or | mm absolu | `GEOMETRY_COVERED` |

# 2. Squelettique vertical / pattern facial

| ID canonique | Mesure | Géométrie canonique | Landmarks | Type/unité | État |
|---|---|---|---|---|---|
| `M_SN_GOGN_DEG_V1` | SN–GoGn | angle SN / Go-Gn | S,N,Go,Gn_anatomic | angle ° | `GEOMETRY_COVERED`; auto-mapping Gn non autoritaire |
| `M_FH_GOME_DEG_V1` | FH–GoMe | angle FH Po-Or / Go-Me | Po_anatomic,Or,Go,Me | angle ° | `GEOMETRY_COVERED` |
| `M_FH_SUBGO_M_DEG_V1` | FH–Sub.Go.-M | angle FH / plan mandibulaire Ricketts strict | Po_anatomic,Or,SubGo,M | angle ° | `IMPLEMENTATION_MISSING` |
| `M_ANS_ME_MM_V1` | ANS–Me | longueur segment ANS-Me | ANS,Me | mm | `GEOMETRY_COVERED` |
| `M_PALATAL_PLANE_FH_DEG_V1` | Plan palatin / FH | angle ANS-PNS / FH | ANS,PNS,Po_anatomic,Or | angle ° | `PRIMITIVE_AVAILABLE`; PNS auto non autoritaire |
| `M_OCCLUSAL_PLANE_SN_DEG_V1` | Plan occlusal / SN | angle plan occlusal / SN | S,N + points occlusaux exacts | angle ° | `SOURCE_LOCK_REQUIRED` |
| `M_ORAL_GNOMON_ANS_XI_PM_DEG_V1` | Oral gnomon | angle ANS-Xi-Pm | ANS,Xi,Pm | angle ° | `BLOCKED_LANDMARK` |
| `M_BEND_OF_MANDIBLE_DEG_V1` | Bend of mandible | construction corpus/condyle Ricketts | Xi/Pm + condylar construction source-lockée | angle ° | `IMPLEMENTATION_MISSING` |

# 3. Axes faciaux / croissance

Ces deux mesures portent un nom proche mais **ne sont pas fusionnées** car leur landmark postérieur n'est pas le même.

| ID canonique | Mesure | Géométrie canonique | Landmarks | Type/unité | État |
|---|---|---|---|---|---|
| `M_FACIAL_AXIS_RICKETTS_DEG_V1` | Facial Axis — variante Pt | angle Pt_Ricketts→Gn_constructed / Ba-N | Pt_Ricketts,Gn_constructed,Ba,N | angle ° | géométrie `GEOMETRY_COVERED`, auto `BLOCKED_LANDMARK` |
| `M_FACIAL_AXIS_MCNAMARA_DEG_V1` | Facial Axis — variante PTM | angle PTM_McNamara→Gn_constructed / Ba-N | PTM_McNamara,Gn_constructed,Ba,N | angle ° | `IMPLEMENTATION_MISSING` |

# 4. Longueurs maxillo-mandibulaires

| ID canonique | Mesure | Géométrie canonique | Landmarks | Type/unité | État |
|---|---|---|---|---|---|
| `M_CO_A_MM_V1` | Co–A | longueur Co_anatomic → A | Co_anatomic,A | mm | `GEOMETRY_COVERED` |
| `M_CO_GN_ANATOMIC_MM_V1` | Co–Gn | longueur Co_anatomic → Gn_anatomic | Co_anatomic,Gn_anatomic | mm | `GEOMETRY_COVERED`; alias runtime legacy `Gn` à ne pas prendre comme preuve anatomique |
| `M_CO_GN_MINUS_CO_A_MM_V1` | Différentiel maxillo-mandibulaire | Co-Gn − Co-A | dérivé des deux mesures ci-dessus | mm | `PRIMITIVE_AVAILABLE` |

# 5. Dento-alvéolaire maxillaire

| ID canonique | Mesure | Géométrie canonique | Landmarks | Type/unité | État |
|---|---|---|---|---|---|
| `M_U1_NA_DEG_V1` | U1–NA angulaire | axe U1 / NA | U1_apex,U1_incisal,N,A | angle ° | `GEOMETRY_COVERED` |
| `M_U1_NA_MM_V1` | U1–NA linéaire | surface faciale U1 → NA | U1_facial_surface,N,A | mm | `BLOCKED_LANDMARK` |
| `M_U1_FH_DEG_V1` | U1–Frankfort | axe U1 / FH | U1_apex,U1_incisal,Po_anatomic,Or | angle ° | `GEOMETRY_COVERED` côté DC/COM |
| `M_U1_A_VERTICAL_MM_V1` | U1 → A vertical | surface faciale U1 → verticale par A parallèle à N-perp | U1_facial_surface,A,Po_anatomic,Or | mm | `BLOCKED_LANDMARK` |
| `M_U6_NA_MM_V1` | U6–NA | position molaire U6 par rapport à NA selon point molaire source-locké | U6_exact,N,A | mm | `BLOCKED_LANDMARK` |
| `M_U6_PTV_MM_V1` | U6→PTV | distal crown U6 → PTV | U6_distal_crown,PR/PTV construction | mm | `BLOCKED_LANDMARK` |

# 6. Dento-alvéolaire mandibulaire

| ID canonique | Mesure | Géométrie canonique | Landmarks | Type/unité | État |
|---|---|---|---|---|---|
| `M_L1_NB_DEG_V1` | L1–NB angulaire | axe L1 / NB | L1_apex,L1_incisal,N,B | angle ° | `GEOMETRY_COVERED` |
| `M_L1_NB_MM_V1` | L1–NB linéaire | surface faciale L1 → NB | L1_facial_surface,N,B | mm | `BLOCKED_LANDMARK` |
| `M_L1_GOGN_DEG_V1` | L1–GoGn | axe L1 / Go-Gn | L1_apex,L1_incisal,Go,Gn_anatomic | angle ° | `IMPLEMENTATION_MISSING` |
| `M_IMPA_GOME_DEG_V1` | IMPA | axe L1 / Go-Me | L1_apex,L1_incisal,Go,Me | angle ° | `GEOMETRY_COVERED` |
| `M_FMIA_L1_FH_DEG_V1` | FMIA | axe L1 / FH Po-Or | L1_apex,L1_incisal,Po_anatomic,Or | angle ° | `GEOMETRY_COVERED` |
| `M_L1_FACIAL_SURFACE_APOG_MM_V1` | L1 surface → A-Pog | surface faciale L1 → A-Pog | L1_facial_surface,A,Pog_hard | mm | `BLOCKED_LANDMARK` |
| `M_L1_EDGE_APOG_MM_V1` | L1 edge → A-Pog | bord incisif L1 → A-Pog | L1_incisal,A,Pog_hard | mm | `PRIMITIVE_AVAILABLE` |
| `M_L1_DLINE_MM_V1` | L1–D line linéaire | surface L1 → D-line | L1_facial_surface,D,Go,Gn_anatomic | mm | `BLOCKED_LANDMARK` |
| `M_L1_DLINE_DEG_V1` | L1–D line angulaire | axe L1 / D-line | L1_apex,L1_incisal,D,Go,Gn_anatomic | angle ° | `BLOCKED_LANDMARK` |
| `M_L6_NB_MM_V1` | L6–NB | position molaire L6 par rapport à NB selon point molaire source-locké | L6_exact,N,B | mm | `BLOCKED_LANDMARK` |

# 7. Relations dentaires / occlusales

| ID canonique | Mesure | Géométrie canonique | Landmarks | Type/unité | État |
|---|---|---|---|---|---|
| `M_INTERINCISAL_DEG_V1` | Angle interincisif | axe U1 / axe L1 | U1_apex,U1_incisal,L1_apex,L1_incisal | angle ° | `GEOMETRY_COVERED` |
| `M_OVERJET_MM_V1` | Surplomb | relation sagittale U1/L1 selon convention DC à verrouiller | incisives exactes | mm | `LEGACY_TO_AUDIT` |
| `M_OVERBITE_V1` | Recouvrement | relation verticale U1/L1 selon convention DC à verrouiller | incisives exactes | unité à verrouiller | `LEGACY_TO_AUDIT` |

# 8. Tissus mous

| ID canonique | Mesure | Géométrie canonique | Landmarks | Type/unité | État |
|---|---|---|---|---|---|
| `M_LI_EPLANE_MM_V1` | Lèvre inférieure → E-plane | distance perpendiculaire signée Li_soft → Prn-Pog_soft | Li_soft,Prn,Pog_soft | mm signé | `GEOMETRY_COVERED` |
| `M_LS_EPLANE_MM_V1` | Lèvre supérieure → E-plane | distance perpendiculaire signée Ls_soft → Prn-Pog_soft | Ls_soft,Prn,Pog_soft | mm signé | `GEOMETRY_COVERED` comme extension DC ; non core Ricketts 1981 11 facteurs |
| `M_NASOLABIAL_ANGLE_DEG_V1` | Angle nasolabial | convention columelle/Prn'-Sn-Ls à verrouiller exactement | soft-tissue dédiés | angle ° | `SOURCE_LOCK_REQUIRED` ; contextuel McNamara, hors 13 variables quantitatives principales |

# 9. Voies aériennes

| ID canonique | Mesure | Géométrie canonique | Landmarks | Type/unité | État |
|---|---|---|---|---|---|
| `M_UPPER_PHARYNX_MM_V1` | Upper pharynx | palais mou postérieur → point le plus proche de la paroi pharyngée postérieure sur la moitié antérieure du palais mou | airway dédiés | mm | `BLOCKED_LANDMARK` |
| `M_LOWER_PHARYNX_MM_V1` | Lower pharynx | jonction langue postérieure / bord mandibulaire inférieur → point le plus proche de la paroi pharyngée postérieure | airway dédiés | mm | `BLOCKED_LANDMARK` |

# 10. PA / frontal Ricketts

Les mesures suivantes sont canoniques mais **toutes bloquées par modalité** tant qu'aucun vrai pipeline PA/frontale n'existe :

| ID canonique | Mesure | État |
|---|---|---|
| `M_PA_NASAL_CAVITY_WIDTH_MM_V1` | NC-NC | `BLOCKED_MODALITY_PA` |
| `M_PA_MAXILLARY_RELATION_R_MM_V1` | J droit → Z-Ag | `BLOCKED_MODALITY_PA` |
| `M_PA_MAXILLARY_RELATION_L_MM_V1` | J gauche → Z-Ag | `BLOCKED_MODALITY_PA` |
| `M_PA_MANDIBULAR_WIDTH_MM_V1` | Ag-Ag | `BLOCKED_MODALITY_PA` + `NORM_HOLD` |
| `M_PA_SKELETAL_SYMMETRY_V1` | ANS/Po vers plan sagittal central, libellé exact à source-locker | `BLOCKED_MODALITY_PA` + `SOURCE_LOCK_REQUIRED` |
| `M_PA_INTERMOLAR_WIDTH_MM_V1` | B6-B6 | `BLOCKED_MODALITY_PA` |
| `M_PA_INTERCANINE_WIDTH_MM_V1` | B3-B3 | `BLOCKED_MODALITY_PA` |
| `M_PA_LOWER_MOLAR_FDP_R_MM_V1` | B6 droit → J-Ag | `BLOCKED_MODALITY_PA` |
| `M_PA_LOWER_MOLAR_FDP_L_MM_V1` | B6 gauche → J-Ag | `BLOCKED_MODALITY_PA` |
| `M_PA_LOWER_INCISOR_FRONTAL_APO_MM_V1` | midpoint L1 → frontal A-Po | `BLOCKED_MODALITY_PA` |
| `M_PA_MOLAR_CROSSBITE_R_MM_V1` | crossbite molaire droit | `BLOCKED_MODALITY_PA` |
| `M_PA_MOLAR_CROSSBITE_L_MM_V1` | crossbite molaire gauche | `BLOCKED_MODALITY_PA` |

# 11. Séries / croissance

Ces entrées décrivent des **mesures de changement**, distinctes de la mesure statique source :

| ID canonique | Mesure | État |
|---|---|---|
| `M_SERIAL_INCISOR_DISPLACEMENT_V1` | déplacement incisif Steiner selon superposition verrouillée | `IMPLEMENTATION_MISSING` |
| `M_SERIAL_MOLAR_DISPLACEMENT_V1` | déplacement molaire Steiner selon superposition verrouillée | `IMPLEMENTATION_MISSING` |
| `M_SERIAL_CO_A_CHANGE_MM_V1` | Δ Co-A | `IMPLEMENTATION_MISSING` |
| `M_SERIAL_CO_GN_CHANGE_MM_V1` | Δ Co-Gn | `IMPLEMENTATION_MISSING` |
| `M_SERIAL_MAXMAND_DIFF_CHANGE_MM_V1` | Δ différentiel maxillo-mandibulaire | `IMPLEMENTATION_MISSING` |
| `M_SERIAL_ANS_ME_CHANGE_MM_V1` | Δ ANS-Me | `IMPLEMENTATION_MISSING` |

# 12. Conclusion d'architecture

Ce registre est la **source de vérité des identités de mesure** du chantier Céphalo-N.

Le profil d'analyse répond ensuite seulement à la question :

> « Quelle sélection de ces mesures appartient à cette analyse/version ? »

Le moteur d'analyse ne doit jamais devenir une seconde implémentation de géométrie.

## Next exact Céphalo-N

1. fermer les équivalences/source-locks encore ouverts ;
2. matérialiser le registre/profils en structures machine-readable versionnées ;
3. implémenter au niveau du registre les mesures non bloquées réellement manquantes ;
4. poursuivre le tracé SVG synchronisé, normes/interprétation et sorties Céphalo-N ;
5. **terminer le closeout Céphalo-N avant tout démarrage de `ORTHO_MODULE_V2`**.
