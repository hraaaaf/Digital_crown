# CÉPHALOMÉTRIE — REGISTRE DES CONSTRUCTIONS

**Statut : Lot 4 actif**  
**Parent canonique :** `docs/CEPHALO_DIAGNOSTIC_SPEC.md`  
**Contrat landmarks :** `docs/SRPOSE38_LANDMARK_CONTRACT.md`

## GOAL

Versionner séparément chaque construction géométrique utilisée par une analyse clinique afin qu'aucune formule ne dépende d'une convention implicite.

## SOURCE HISTORIQUE CRANIOM

La méthode historiquement appelée « COM » dans Digital Crown correspond au périmètre de la méthode **C.R.A.N.I.O.M.** décrite par René Bonnefont, Jean Casteigt, Jean‑François Ernoult et Olivier Sorel.

Source publiée :
- *A new method for the utilization of cephalometric measurements in orthodontics or how standard deviations can sometimes be the practitioner's false friends (Part 1)*, Journal of Dentofacial Anomalies and Orthodontics, 2010, 13(4):385‑400, DOI `10.1051/odfen/2010406`.

Important : cette référence décrit une **méthode spécifique** et son échantillon de référence. Elle ne transforme pas ses valeurs en normes universelles.

## REGISTRE CERTIFIABLE AVEC SRPOSE38

### `FH_PO_OR_V1`

**Nom :** plan de Francfort anatomique.  
**Dépendances :** `Po`, `Or`.  
**Définition :** droite passant par Porion et Orbitale.  
**Orientation numérique :** vecteur unitaire `Po → Or`, utilisé comme direction antérieure positive.  
**Échec :** `NOT_COMPUTABLE` si Po/Or absents ou confondus.  
**État :** `VERIFIED_GEOMETRY`.

### `CRANIOM_A_PRIME_V1`

**Nom :** A'.  
**Dépendances :** `A` + `FH_PO_OR_V1`.  
**Définition :** projection orthogonale du point A sur le plan de Francfort.  
**État :** `SOURCE_VERIFIED`.

### `CRANIOM_B_PRIME_V1`

**Nom :** B'.  
**Dépendances :** `B` + `FH_PO_OR_V1`.  
**Définition :** projection orthogonale du point B sur le plan de Francfort.  
**État :** `SOURCE_VERIFIED`.

### `CRANIOM_AB_PRIME_V1`

**Nom :** segment algébrique A'B'.  
**Dépendances :** `A`, `B`, `Po`, `Or`, calibration mm/px.  
**Définition :** distance signée entre les projections orthogonales de A et B sur Francfort.  
**Convention :** positive lorsque A est antérieur à B selon `Po → Or`, négative lorsque A est postérieur à B.  
**Formule équivalente :** `dot(A - B, unit(Po→Or)) × mm_per_pixel`.  
**État :** `SOURCE_VERIFIED`.

La publication CRANIOM décrit explicitement A' et B' comme projections orthogonales de A et B sur Francfort et utilise le signe positif quand A est en avant de B.

### `NASION_VERTICAL_FH_V1`

**Nom :** verticale par Nasion dans le repère Francfort horizontalisé.  
**Dépendances :** `N` + `FH_PO_OR_V1`.  
**Définition numérique :** droite passant par N et perpendiculaire à Francfort.  
**État :** `SOURCE_COMPATIBLE_GEOMETRY`.

### `CRANIOM_A_TO_N_VERTICAL_V1`

**Dépendances :** `A`, `N`, `Po`, `Or`, calibration.  
**Définition :** distance AP signée du point A à `NASION_VERTICAL_FH_V1`.  
**Formule :** `dot(A - N, unit(Po→Or)) × mm_per_pixel`.  
**Convention :** positif en avant de Nasion, négatif en arrière.  
**État :** `SOURCE_COMPATIBLE_GEOMETRY`.

### `CRANIOM_B_TO_N_VERTICAL_V1`

Même définition avec B.  
**État :** `SOURCE_COMPATIBLE_GEOMETRY`.

### `CRANIOM_S_TO_N_VERTICAL_DEPTH_V1`

**Dépendances :** `S`, `N`, `Po`, `Or`, calibration.  
**Définition :** distance géométrique de S à la verticale par Nasion, mesurée parallèlement à Francfort.  
**Formule :** `abs(dot(S - N, unit(Po→Or))) × mm_per_pixel`.  
**État :** `GEOMETRY_VERIFIED_SOURCE_SEMANTICS_TO_CONFIRM`.

## IMPLÉMENTATION

Les constructions ci-dessus sont matérialisées dans `backend/services/cephalo_constructions.py`. `backend/services/cephalo_engine.py` est branché sur ces fonctions pour `Situation_A`, `Situation_B`, `Decalage_A_B`, `Profondeur_Faciale` et les projections visuelles A'/B'/N'.

Les anciennes `mcnmara_projections` calculées côté client restent acceptées dans l'API pour compatibilité mais **ne peuvent plus modifier une mesure backend**. Les coordonnées sources des landmarks sont la seule source de vérité géométrique.

## CONVENTIONS MANDIBULAIRES — GATE EXPLICITE

Le terme « plan mandibulaire » n'est pas une construction universelle. Les sources sérieuses décrivent plusieurs variantes :

- un plan `Go-Me` est couramment utilisé dans certains schémas/logiciels ;
- Downs est classiquement décrit par une **tangente au bord inférieur mandibulaire** ;
- Tweed est également décrit dans la littérature par une tangente au bord inférieur, avec Menton antérieurement et la région goniale postérieurement ;
- d'autres analyses utilisent `Go-Gn`.

Sources de contrôle :
- Downs WB. *Variations in facial relationships: Their significance in treatment and prognosis.* Am J Orthod. 1948;34(10):812‑840. DOI `10.1016/0002-9416(48)90015-3`.
- Tweed CH. *The Frankfort-mandibular plane angle in orthodontic diagnosis, classification, treatment planning, and prognosis.* Am J Orthod Oral Surg. 1946;32:175‑230. DOI `10.1016/0096-6347(46)90001-4`.
- Shindoi et al./comparative literature summarized in *Assessing lower incisor inclination change: a comparison of four cephalometric methods* (peer-reviewed): Downs/Tweed use a tangent to the lower mandibular border, whereas other analyses use Go-Me or Go-Gn constructions.

### Conséquence Digital Crown

Le champ historique `Angle_de_Tweed` est actuellement calculé avec `Go-Me`. **Il reste une mesure géométrique legacy, pas une mesure Tweed certifiée**, tant que la convention exacte de la fiche historique `26° ± 4°` n'est pas reliée à une source autoritative.

Même règle pour `IMPA` : l'axe incisif est disponible, mais la construction du plan mandibulaire doit être rattachée explicitement à l'analyse choisie avant toute norme/interprétation.

## CONSTRUCTIONS MANDIBULAIRES VERSIONNÉES — DÉCISION SCIENTIFIQUE ACTIVE

Les source-locks plus récents de Céphalo-N ont fermé la géométrie Steiner et la variante Tweed Digital Crown sans réinterpréter les normes historiques.

### `STEINER_MP_GO_GN_V1`

**Nom :** plan mandibulaire Steiner Go-Gn.  
**Dépendances :** `Go`, `Gn_anatomic`.  
**Définition :** droite passant par Gonion et le Gnathion anatomique utilisé par le contrat Steiner 1953.  
**Usages autorisés :** SN-GoGn et mesures explicitement rattachées à la version Steiner correspondante.  
**Échec :** `NOT_COMPUTABLE` si Go manque, si Gn n'est pas explicitement anatomique, ou si les deux points sont confondus.  
**État :** `SOURCE_LOCKED_GEOMETRY`.  
**Source contractuelle :** `docs/audits/CEPHALO_PRIMARY_LANDMARK_CONSTRUCTIONS.md` + `docs/audits/CEPHALO_LANDMARKS_PLANES_SOURCE_LOCK.md`.

### `TWEED_DC_MP_GO_ME_V1`

**Nom :** plan mandibulaire Tweed — variante Digital Crown active.  
**Dépendances :** `Go`, `Me`.  
**Définition :** droite Go-Me utilisée par le contrat Digital Crown actif.  
**Usages autorisés :** `M_FH_GOME_DEG_V1` et `M_IMPA_GOME_DEG_V1` lorsque la variante est explicitement identifiée comme `DC_TWEED_ANATOMICAL_FH_VARIANT`.  
**Frankfort associé :** `FH_PO_OR_V1`.  
**Échec :** `NOT_COMPUTABLE` si Go/Me absents ou confondus.  
**État :** `SELECTED_DC_GEOMETRY`.  
**Limite :** cette construction ne doit pas être présentée comme reproduction stricte du Frankfort ear-rod de Tweed 1954 et n'active aucune norme historique Tweed par héritage de nom.  
**Source contractuelle :** `docs/audits/CEPHALO_PRIMARY_LANDMARK_CONSTRUCTIONS.md` + `docs/audits/CEPHALO_LANDMARKS_PLANES_SOURCE_LOCK.md`.

### Harmonisation de l'ancien avertissement

L'avertissement historique ci-dessus reste utile pour interdire les substitutions entre plans mandibulaires. En revanche, pour la **géométrie Digital Crown active**, la décision clinique/source-lock du 2026-09-15 ferme désormais explicitement le couple `Po-Or + Go-Me` sous le nom versionné `DC_TWEED_ANATOMICAL_FH_VARIANT`. Les normes/interprétations Tweed historiques restent un chantier distinct.

## CONSTRUCTIONS NON COMPUTABLES OU NON CERTIFIÉES

### CRANIOM `Gi/Gs`

La méthode CRANIOM publiée décrit pour certaines mesures verticales des points goniaques inférieur/supérieur `Gi/Gs`. SRPose38 fournit un unique `Go`.

**Décision :** aucune substitution `Go ↔ Gi/Gs` silencieuse. Ces mesures restent `NOT_COMPUTABLE` tant qu'une construction compatible n'est pas prouvée ou qu'une saisie manuelle explicite n'est pas ajoutée.

### A''B'' / regard horizontal

CRANIOM distingue `A'B'` projeté sur Francfort et `A''B''` projeté sur le plan du regard horizontal. Digital Crown n'a pas actuellement de capture standardisée du regard horizontal liée à la photographie de profil.

**Décision :** `A''B'' = NOT_COMPUTABLE` jusqu'à implémentation/validation du protocole photo + orientation naturelle de tête.

## TESTS GOLDEN DU LOT 4

1. Francfort horizontal : A=+5 mm devant B → A'B' = +5 mm.
2. Francfort incliné : rotation rigide de tous les points ne change pas A'B'.
3. A derrière B → signe négatif.
4. translation globale → valeurs invariantes.
5. changement d'échelle pixel + calibration compensatrice → même valeur mm.
6. Po=Or → `NOT_COMPUTABLE`.
7. calibration absente, non finie ou ≤0 → `NOT_COMPUTABLE`.
8. A/B/N/S manquant → seulement les mesures dépendantes deviennent `NOT_COMPUTABLE`.
9. projection fournie par le client → aucun effet sur la mesure backend.

Tests :
- `backend/tests/test_cephalo_craniom_constructions.py`
- `backend/tests/test_cephalo_craniom_runtime_parity.py`

## NEXT EXACT

Obtenir la preuve CI des golden tests puis séparer explicitement les constructions `TWEED_MP`, `DOWNS_MP` et les besoins `CRANIOM_Gi/Gs` avant d'activer IMPA/FMA comme mesures attribuées à une école.
### RICKETTS_GN_CONSTRUCTED_NPOG_GOME_V1
- ID: `RICKETTS_GN_CONSTRUCTED_NPOG_GOME_V1`
- Output: `Gn_constructed_Ricketts`
- Inputs: N, Pog_hard, Go, Me.
- Rule: intersection of the infinite N-Pog_hard facial line and Go-Me mandibular line.
- Purpose: explicit dependency for Ricketts facial axis; never interchangeable with `Gn_anatomic`.

## Steiner LOT08 source-locked explicit constructions ? 2026-10-03

These constructions extend the LOT06 deterministic authority without activating norms, diagnosis, or treatment. Explicit/manual identities fail closed when absent.

- `STEINER_SND_1959_V1` ? SN/ND using explicit `D_Steiner_1959`; detector `D_point` is not an authorized alias.
- `STEINER_U1_NA_LINEAR_V1` ? perpendicular U1 facial-crown surface to NA; requires `U1_facial_surface` and verified calibration.
- `STEINER_L1_NB_LINEAR_V1` ? perpendicular L1 facial-crown surface to NB; requires `L1_facial_surface` and verified calibration.
- `STEINER_POG_NB_1959_V1` ? perpendicular `Pog_hard` to NB with verified calibration.
- `STEINER_L1_GOGN_V1` ? lower-incisor long axis vs Steiner Go-Gn using explicit `Gn_anatomic`.
- `STEINER_OCCLUSAL_SN_1953_V1` ? SN vs version-scoped Steiner 1953 occlusal plane using explicit/constructed `Occ_Steiner_Ant` and `Occ_Steiner_Post`; Wits/Ricketts occlusal planes are not aliases.
- `STEINER_L1_DLINE_LINEAR_1959_V1` ? L1 facial-crown surface to D-line; D-line passes through explicit `D_Steiner_1959` perpendicular to Go-Gn; verified calibration required.
- `STEINER_L1_DLINE_ANGULAR_1959_V1` ? lower-incisor long axis vs D-line orientation; explicit Steiner D remains an evidence dependency even though line orientation is determined by Go-Gn.


## RICKETTS_PTV_PR_POSTERIOR_PPF_PERP_FH_V1

- Purpose: Ricketts pterygoid vertical construction for upper-molar position.
- Required landmarks: `PR_Ricketts_PTV`, `Po_anatomic`, `Or`.
- Rule: infinite line through `PR_Ricketts_PTV`, perpendicular to anatomical Frankfort `Po_anatomic-Or`.
- Coordinate space: source-image pixels.
- Evidence gate: all identities available from one source image; degenerate Frankfort => INVALID.
- Forbidden alias: generic `PT_point`, `Ptm`, and facial-axis `Pt_Ricketts` must not be promoted by name.
- Authority gate: `PR_Ricketts_PTV` must be `MANUAL` or `MANUAL_CORRECTED`.
- Downstream measurement `M_U6_PTV_MM_V1` is `CONDITIONAL_EXECUTABLE` only with manual/manual-corrected `U6_DISTAL_Ricketts` and verified calibration.
- Forbidden substitutions: generic `PTV`, `Pt`, `PT_point`, `Ptm`, generic/cusp/centroid/mesial `U6`.
- Source contract: `docs/audits/CEPHALO_LOT08_RICKETTS_U6_PTV_SOURCE_LOCK.md`.


## RICKETTS_FUNCTIONAL_OCCLUSAL_PLANE_BICUSPID_MOLAR_V1

- Purpose: functional occlusal plane for the Ricketts/Gregoret source-locked profile.
- Required landmarks: `FOP_PREMOLAR_Ricketts`, `FOP_MOLAR_Ricketts`.
- Rule: line through the explicit premolar- and molar-occlusion identities; incisors are not anchors.
- Evidence gate: both identities available from one source image; coincident anchors => `INVALID`.
- Forbidden substitutions: generic occlusal anchors, incisor-defined planes, Steiner/Downs occlusal planes.
- State: `SOURCE_LOCKED_GEOMETRY`.
- Downstream: `M_RICKETTS_L1_OCCLUSAL_EXTRUSION_MM_V1` is `CONDITIONAL_EXECUTABLE` with explicit FOP anchors, `L1_incisal`, `L1_apex`, and verified calibration. Sign is positive on the crownward/incisal side of the FOP and negative on the apical side; the L1 long axis orients the plane normal.
- Source contract: `docs/audits/CEPHALO_LOT08_RICKETTS_FOP_MANDIBULAR_PLANE_SOURCE_LOCK.md`.

## RICKETTS_MANDIBULAR_PLANE_ANGLE_MENTON_V1

- Purpose: Ricketts mandibular plane for MP–FH.
- Required landmarks: `MP_ANGLE_INFERIOR_Ricketts`, `Me`.
- Rule: line through the source-specific inferior mandibular-angle point and Menton.
- Evidence gate: both identities available from one source image; coincident anchors => `INVALID`.
- Forbidden substitutions: generic `Go`, `Go-Me`, `Go-Gn`, Tweed FMA geometry.
- State: `SOURCE_LOCKED_GEOMETRY`.
- Downstream: `M_RICKETTS_MANDIBULAR_PLANE_FH_DEG_V1` is `CONDITIONAL_EXECUTABLE` and consumes this canonical `ConstructionEvidence` plus anatomical Frankfort `Po_anatomic-Or`.
- Source contract: `docs/audits/CEPHALO_LOT08_RICKETTS_FOP_MANDIBULAR_PLANE_SOURCE_LOCK.md`.


## RICKETTS_XI_RAMAL_RECTANGLE_R1_R4_FH_V1

- Purpose: source-locked construction of `Xi_Ricketts`, the geometric center of the mandibular ramus.
- Required landmarks: `R1_Ricketts`, `R2_Ricketts`, `R3_Ricketts`, `R4_Ricketts`, `Po_anatomic`, `Or`.
- Source geometry: R1/R2 define opposed ramal limits along Frankfort; R3/R4 define superior/inferior limits along the perpendicular axis; Xi is the center of the resulting rectangle.
- Numerical rule: compute the midpoint of the R1/R2 limits on the anatomical Frankfort axis and the midpoint of the R3/R4 limits on its perpendicular, then reconstruct the point in source-image coordinates.
- Evidence gate: `R1_Ricketts`..`R4_Ricketts` must be `MANUAL` or `MANUAL_CORRECTED`; Po/Or may use their established canonical authority; all six identities must come from one source image; degenerate Frankfort or collapsed rectangle => `INVALID`.
- Forbidden substitutions: generic `Xi`, `Go`, `Ar`, `PT_point`; no detector alias is promoted by name.
- State: `SOURCE_LOCKED_GEOMETRY`.
- Downstream: `M_ORAL_GNOMON_ANS_XI_PM_DEG_V1` is `CONDITIONAL_EXECUTABLE` with constructed Xi + explicit `ANS` + explicit `Pm_Ricketts`.
- `M_RICKETTS_MANDIBULAR_ARC_DCXI_XIPM_DEG_V1` is `CONDITIONAL_EXECUTABLE` with manual/manual-corrected `DC_Ricketts`, this canonical Xi construction, and manual/manual-corrected `Pm_Ricketts`; generic condylar/chin aliases remain forbidden.
- Source authority: Ricketts RM 1972 source-locks the R1-R4 ramal rectangle/centroid; Ricketts RM 1981 confirms Xi-Pm/oral-gnomon use. FH/PtV axis orientation is corroborated by peer-reviewed Ricketts implementations (e.g. Mangla et al., 2011, DOI `10.4103/0976-237X.86458`).

- Mandibular-arc DC authority source contract: `docs/audits/CEPHALO_LOT08_RICKETTS_DC_MANDIBULAR_ARC_SOURCE_LOCK.md`.
