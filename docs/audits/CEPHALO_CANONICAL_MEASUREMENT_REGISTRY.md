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
| `M_SND_DEG_V1` | SND | angle SN / ND | S,N,D_Steiner_1959 | angle ° | `GEOMETRY_COVERED_EXPLICIT_STEINER_D_REQUIRED` |
| `M_A_NPERP_MM_V1` | A → N-perp | distance AP signée de A à la perpendiculaire à FH passant par N | A,N,Po_anatomic,Or | mm signé | `GEOMETRY_COVERED` |
| `M_B_NPERP_MM_V1` | B → N-perp | même construction avec B | B,N,Po_anatomic,Or | mm signé | `GEOMETRY_COVERED` côté DC legacy |
| `M_POG_NPERP_MM_V1` | Pog → N-perp | même construction avec Pog hard | Pog_hard,N,Po_anatomic,Or | mm signé | `GEOMETRY_COVERED` |
| `M_POG_NB_MM_V1` | Pog → NB | distance perpendiculaire Pog hard → NB | Pog_hard,N,B | mm | `GEOMETRY_COVERED_EXPLICIT_IDENTITY_REQUIRED` |
| `M_AB_PRIME_FH_MM_V1` | A′B′ | différence signée des projections de A et B sur FH | A,B,Po_anatomic,Or | mm signé | `GEOMETRY_COVERED` |
| `M_MAXILLARY_CONVEXITY_A_NPOG_MM_V1` | Convexité maxillaire | distance perpendiculaire signée A → N-Pog | A,N,Pog_hard | mm signé | `GEOMETRY_COVERED` |
| `M_FACIAL_ANGLE_NPOG_FH_DEG_V1` | Facial Angle | angle N-Pog / FH | N,Pog_hard,Po_anatomic,Or | angle ° | `GEOMETRY_COVERED + CONVENTION_COLLISION` — Downs = angle aigu d’axes; Ricketts `FACIAL_DEPTH` = angle postérieur dirigé; split/version requis avant promotion canonique |
| `M_COM_S_NPERP_DEPTH_MM_V1` | Profondeur faciale legacy COM | magnitude S → N-perp | S,N,Po_anatomic,Or | mm absolu | `GEOMETRY_COVERED` |

# 2. Squelettique vertical / pattern facial

| ID canonique | Mesure | Géométrie canonique | Landmarks | Type/unité | État |
|---|---|---|---|---|---|
| `M_SN_GOGN_DEG_V1` | SN–GoGn | angle SN / Go-Gn | S,N,Go,Gn_anatomic | angle ° | `GEOMETRY_COVERED`; auto-mapping Gn non autoritaire |
| `M_FH_GOME_DEG_V1` | FH–GoMe | angle FH Po-Or / Go-Me | Po_anatomic,Or,Go,Me | angle ° | `GEOMETRY_COVERED` |
| `M_FH_SUBGO_M_DEG_V1` | FH–Sub.Go.-M | angle FH / plan mandibulaire Ricketts strict | Po_anatomic,Or,SubGo,M | angle ° | `IMPLEMENTATION_MISSING` |
| `M_ANS_ME_MM_V1` | ANS–Me | longueur segment ANS-Me | ANS,Me | mm | `GEOMETRY_COVERED` |
| `M_PALATAL_PLANE_FH_DEG_V1` | Plan palatin / FH | angle ANS-PNS / FH | ANS,PNS,Po_anatomic,Or | angle ° | `PRIMITIVE_AVAILABLE`; PNS auto non autoritaire |
| `M_OCCLUSAL_PLANE_SN_DEG_V1` | Plan occlusal / SN | angle plan occlusal Steiner 1953 / SN | S,N,Occ_Steiner_Ant,Occ_Steiner_Post | angle ° | `GEOMETRY_COVERED_EXPLICIT_STEINER_ANCHORS_REQUIRED` |
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
| `M_U1_NA_MM_V1` | U1–NA linéaire | surface faciale U1 → NA | U1_facial_surface,N,A | mm | `GEOMETRY_COVERED_EXPLICIT_CROWN_SURFACE_REQUIRED` |
| `M_U1_FH_DEG_V1` | U1–Frankfort | axe U1 / FH | U1_apex,U1_incisal,Po_anatomic,Or | angle ° | `GEOMETRY_COVERED` côté DC/COM |
| `M_U1_A_VERTICAL_MM_V1` | U1 → A vertical | surface faciale U1 → verticale par A parallèle à N-perp | U1_facial_surface,A,Po_anatomic,Or | mm | `BLOCKED_LANDMARK` |
| `M_U6_NA_MM_V1` | U6–NA | position molaire U6 par rapport à NA selon point molaire source-locké | U6_exact,N,A | mm | `BLOCKED_LANDMARK` |
| `M_U6_PTV_MM_V1` | U6→PTV | Ricketts A6 distal reference → source-locked PTV | `U6_DISTAL_Ricketts`,`RICKETTS_PTV_PR_POSTERIOR_PPF_PERP_FH_V1` | mm | `CONDITIONAL_EXECUTABLE`; manual U6/PR + verified calibration |
| `M_RICKETTS_MOLAR_RELATION_FOP_MM_V1` | Ricketts molar relation | lower minus upper first-molar distal references projected on posterior-positive Ricketts FOP | `L6_DISTAL_Ricketts,U6_DISTAL_Ricketts` + FOP | mm signed | `GEOMETRY_COVERED`; manual molar distals + calibration |
| `M_RICKETTS_CANINE_RELATION_FOP_MM_V1` | Ricketts canine relation | lower minus upper canine cusp references projected on posterior-positive Ricketts FOP | `L3_CUSP_Ricketts,U3_CUSP_Ricketts` + FOP | mm signed | `GEOMETRY_COVERED`; manual canine cusps + calibration |
| `M_RICKETTS_OVERJET_FOP_MM_V1` | Ricketts overjet | lower minus upper incisal edges projected on posterior-positive Ricketts FOP | `L1_incisal,U1_incisal` + FOP | mm signed | `GEOMETRY_COVERED`; calibration |
| `M_RICKETTS_OVERBITE_FOP_MM_V1` | Ricketts overbite | incisal-edge separation perpendicular to Ricketts FOP; open bite negative in source convention | `L1_incisal,U1_incisal` + FOP | mm signed | `SOURCE_SIGN_KNOWN__SUPERIOR_INFERIOR_IMAGE_AXIS_UNAVAILABLE` |
| `M_RICKETTS_U1_APOG_PROTRUSION_MM_V1` | Ricketts upper-incisor protrusion | perpendicular signed U1 incisal-edge distance to A-Pog; anterior positive | `U1_incisal,A,Pog_hard,Po_anatomic,Or` | mm signed | `GEOMETRY_COVERED_EXPLICIT_U1_EDGE_PERPENDICULAR_APOG_ANTERIOR_POSITIVE`; calibration |
| `M_RICKETTS_U1_APOG_INCLINATION_DEG_V1` | Ricketts upper-incisor inclination | acute line angle U1 long axis / A-Pog | `U1_incisal,U1_apex,A,Pog_hard` | angle ° | `GEOMETRY_COVERED` |

| `M_RICKETTS_OCCLUSAL_PLANE_XI_MM_V1` | Ricketts FOP→Xi | signed perpendicular Xi/FOP relation; + FOP above Xi / − below | canonical Xi + source-locked FOP | mm | `SOURCE_SIGN_KNOWN__SUPERIOR_INFERIOR_IMAGE_AXIS_UNAVAILABLE` |
| `M_RICKETTS_OCCLUSAL_PLANE_XIPM_DEG_V1` | Ricketts occlusal-plane inclination | acute angle FOP / Xi-Pm | canonical FOP, canonical Xi, manual Pm | angle ° | `GEOMETRY_COVERED` |
| `M_RICKETTS_UPPER_LIP_LENGTH_ANS_COMMISSURE_MM_V1` | Ricketts upper-lip length | straight-line ANS to labial commissure | ANS, `LABIAL_COMMISSURE_Ricketts` | mm | `GEOMETRY_COVERED`; manual commissure + calibration |
| `M_RICKETTS_COMMISSURE_FOP_MM_V1` | Ricketts commissure to FOP | signed relation; negative when FOP passes below commissure | `LABIAL_COMMISSURE_Ricketts` + source-locked FOP | mm | `SOURCE_SIGN_KNOWN__SUPERIOR_INFERIOR_IMAGE_AXIS_UNAVAILABLE` |
| `M_RICKETTS_FACIAL_TAPER_NPOG_MP_DEG_V1` | Ricketts facial taper | acute angle N-Pog / source-locked Ricketts MP | N,Pog + Ricketts MP construction | angle ° | `GEOMETRY_COVERED` |
| `M_RICKETTS_MAXILLARY_HEIGHT_NCFA_DEG_V1` | Ricketts maxillary height | angle N-CF-A | N,A + `RICKETTS_CF_FH_PTV_INTERSECTION_V1` | angle ° | `GEOMETRY_COVERED` |
| `M_RICKETTS_PALATAL_PLANE_FH_DEG_V1` | Ricketts palatal plane | directional ANS-PNS / anatomical FH angle; source direction known | ANS,`PNS_Ricketts`,Po_anatomic,Or | angle ° | `SOURCE_SIGN_KNOWN__SUPERIOR_INFERIOR_IMAGE_AXIS_UNAVAILABLE` |

# 6. Dento-alvéolaire mandibulaire

| ID canonique | Mesure | Géométrie canonique | Landmarks | Type/unité | État |
|---|---|---|---|---|---|
| `M_L1_NB_DEG_V1` | L1–NB angulaire | axe L1 / NB | L1_apex,L1_incisal,N,B | angle ° | `GEOMETRY_COVERED` |
| `M_L1_NB_MM_V1` | L1–NB linéaire | surface faciale L1 → NB | L1_facial_surface,N,B | mm | `GEOMETRY_COVERED_EXPLICIT_CROWN_SURFACE_REQUIRED` |
| `M_L1_GOGN_DEG_V1` | L1–GoGn | axe L1 / Go-Gn | L1_apex,L1_incisal,Go,Gn_anatomic | angle ° | `GEOMETRY_COVERED` |
| `M_IMPA_GOME_DEG_V1` | IMPA | axe L1 / Go-Me | L1_apex,L1_incisal,Go,Me | angle ° | `GEOMETRY_COVERED` |
| `M_FMIA_L1_FH_DEG_V1` | FMIA | axe L1 / FH Po-Or | L1_apex,L1_incisal,Po_anatomic,Or | angle ° | `GEOMETRY_COVERED` |
| `M_L1_FACIAL_SURFACE_APOG_MM_V1` | L1 surface → A-Pog | surface faciale L1 → A-Pog | L1_facial_surface,A,Pog_hard | mm | `BLOCKED_LANDMARK` |
| `M_L1_EDGE_APOG_MM_V1` | L1 edge → A-Pog | bord incisif L1 → A-Pog | L1_incisal,A,Pog_hard | mm | `PRIMITIVE_AVAILABLE` |
| `M_L1_DLINE_MM_V1` | L1–D line linéaire | surface L1 → D-line | L1_facial_surface,D_Steiner_1959,Go,Gn_anatomic | mm | `GEOMETRY_COVERED_EXPLICIT_STEINER_D_AND_CROWN_REQUIRED` |
| `M_L1_DLINE_DEG_V1` | L1–D line angulaire | axe L1 / D-line | L1_apex,L1_incisal,D_Steiner_1959,Go,Gn_anatomic | angle ° | `GEOMETRY_COVERED_EXPLICIT_STEINER_D_REQUIRED` |
| `M_L6_NB_MM_V1` | L6–NB | position molaire L6 par rapport à NB selon point molaire source-locké | L6_exact,N,B | mm | `BLOCKED_LANDMARK` |

# 7. Relations dentaires / occlusales

| ID canonique | Mesure | Géométrie canonique | Landmarks | Type/unité | État |
|---|---|---|---|---|---|
| `M_INTERINCISAL_DEG_V1` | Angle interincisif | axe U1 / axe L1 | U1_apex,U1_incisal,L1_apex,L1_incisal | angle ° | `GEOMETRY_COVERED` |
| `M_OVERJET_MM_V1` | Surplomb | relation sagittale U1/L1 selon convention DC à verrouiller | incisives exactes | mm | `LEGACY_TO_AUDIT` |
| `M_OVERBITE_V1` | Recouvrement | relation verticale U1/L1 selon convention DC à verrouiller | incisives exactes | mm | `LEGACY_TO_AUDIT` |

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

| `M_RICKETTS_CRANIAL_DEFLECTION_FH_BAN_DEG_V1` | Ricketts cranial deflection | acute angle anatomical FH / Ba-N | Po_anatomic,Or,Ba,N | angle ° | `GEOMETRY_COVERED` |
| `M_RICKETTS_ANTERIOR_CRANIAL_LENGTH_CC_N_MM_V1` | Ricketts anterior cranial length | CC→N | Atlas CC construction + N | mm | `GEOMETRY_COVERED`; calibration |
| `M_RICKETTS_POSTERIOR_FACIAL_HEIGHT_GO_CF_MM_V1` | Ricketts posterior facial height | Go→CF | manual `GO_Ricketts_PFH` + source-locked CF | mm | `GEOMETRY_COVERED`; calibration |
| `M_RICKETTS_TOTAL_FACIAL_HEIGHT_BAN_XIPM_DEG_V1` | Ricketts total facial height | acute angle Ba-N / Pm-Xi | Ba,N + canonical Xi + manual Pm | angle ° | `GEOMETRY_COVERED`; Atlas row-29 transcription conflict resolved |
| `M_RICKETTS_RAMUS_POSITION_FH_CFXI_DEG_V1` | Ricketts ramus position | acute angle FH / CF-Xi | anatomical FH + canonical CF + canonical Xi | angle ° | `GEOMETRY_COVERED` |
| `M_RICKETTS_PORION_LOCATION_PTV_MM_V1` | Ricketts Porion location | signed PTV→Po distance along FH; posterior negative | Po_anatomic + source-locked PTV | mm signed | `GEOMETRY_COVERED`; calibration |
| `M_RICKETTS_CORPUS_LENGTH_XI_PM_MM_V1` | Ricketts mandibular corpus length | Xi→Pm | canonical Xi + manual Pm | mm | `GEOMETRY_COVERED`; calibration |
