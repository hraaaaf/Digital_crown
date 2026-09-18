# CÉPHALO-N — Inventaire des mesures runtime

Date d'audit : 2026-09-16
Base auditée initiale : master `e83b9713e80c94c42a16014d802be850c246adde`
Base réalignée avant PR : master `a396acfd6570ff24ca683009e1f31bdb3f2c0d92`
Lot : MESURES MANQUANTES RÉELLEMENT CALCULABLES

## Goal / succès / preuve

Goal : activer uniquement les mesures canoniques dont la définition, les landmarks, la géométrie, l'unité et la calibration éventuelle sont verrouillés.

Succès : aucune activation par ressemblance de nom ; chaque mesure est classée A ou B ; les nouvelles mesures A ont un calcul centralisé, un ID canonique, une provenance et des tests déterministes.

Preuve attendue : code + tests ciblés + CI exacte du HEAD + revue du diff + non-régression.

## Sources de vérité croisées

- `backend/services/cephalo_measure_registry.py`
- `docs/audits/CEPHALO_ANALYSIS_MEASUREMENT_PROFILES.md`
- `docs/audits/CEPHALO_CANONICAL_MEASUREMENT_REGISTRY.md`
- `docs/audits/CEPHALO_GEOMETRIC_MEASUREMENT_CONTRACTS.md`
- `docs/SRPOSE38_LANDMARK_CONTRACT.md`
- services Steiner / Tweed-Merrifield / McNamara / Ricketts / COM existants
- McNamara JA Jr. *A method of cephalometric evaluation*. Am J Orthod. 1984;86(6):449-469. DOI 10.1016/S0002-9416(84)90352-X, PMID 6594933.
- validation secondaire de la définition McNamara N-perpendicular : PMC4436328.

## Règles d'identité appliquées

Aucun des faux équivalents interdits par le handover n'est fusionné. En particulier : `M_B_NPERP_MM_V1` n'est pas `M_POG_NPERP_MM_V1`, les axes faciaux Ricketts/McNamara restent distincts, `Gn_anatomic` n'est pas `Gn_constructed`, `Pt_Ricketts` n'est pas `PTM_McNamara`, et `Pog_hard` n'est pas `Pog_soft`.

Le contrat SRPose38 autorise `Pog` comme Pogonion osseux et sépare `Pog_soft`. Il ne certifie pas silencieusement les variantes spécialisées de `Go`, `Gn`, `Co`, `Ptm/PTM` ou les landmarks PA.

## Matrice exhaustive

Légende :
- **A** = calculable avec preuve complète. Cela inclut les mesures déjà couvertes et les deux activations de ce lot.
- **B** = bloquée explicitement. Aucun calcul n'est activé.

| measurement_id | analyse(s) | source / géométrie | landmarks requis | calibration | runtime avant lot | groupe | blocage / action |
|---|---|---|---|---|---|---|---|
| M_SNA_DEG_V1 | Steiner | Steiner angle S-N-A | S,N,A | non | GEOMETRY_COVERED | A | conserver |
| M_SNB_DEG_V1 | Steiner | Steiner angle S-N-B | S,N,B | non | GEOMETRY_COVERED | A | conserver |
| M_ANB_DEG_V1 | Steiner | SNA-SNB | S,N,A,B | non | GEOMETRY_COVERED | A | conserver |
| M_SND_DEG_V1 | Steiner 1959 | source-lock Steiner | S,N,D | non | BLOCKED_LANDMARK | B | D indisponible |
| M_A_NPERP_MM_V1 | McNamara | A vers N-perp, FH Po-Or, signé | A,N,Po_anatomic,Or | oui | PRIMITIVE_AVAILABLE | A | **implémenté dans ce lot** |
| M_B_NPERP_MM_V1 | COM/legacy DC | N-perp legacy vers B | B,N,Po,Or | oui | GEOMETRY_COVERED | A | conserver ; ne jamais aliaser Pog |
| M_POG_NPERP_MM_V1 | McNamara | Pog vers N-perp, FH Po-Or, signé | Pog_hard,N,Po_anatomic,Or | oui | PRIMITIVE_AVAILABLE | A | **implémenté dans ce lot** |
| M_POG_NB_MM_V1 | Steiner 1959 | distance Pog-NB | Pog_hard,N,B | oui | IMPLEMENTATION_MISSING | B | définition/signage runtime non source-lockés |
| M_AB_PRIME_FH_MM_V1 | COM | projection A/B sur FH | A,B,Po,Or | oui | GEOMETRY_COVERED | A | conserver |
| M_MAXILLARY_CONVEXITY_A_NPOG_MM_V1 | Ricketts | distance A au plan N-Pog | A,N,Pog_hard | oui | GEOMETRY_COVERED | A | conserver |
| M_FACIAL_ANGLE_NPOG_FH_DEG_V1 | Ricketts | N-Pog vs FH | N,Pog_hard,Po,Or | non | GEOMETRY_COVERED | A | conserver |
| M_COM_S_NPERP_DEPTH_MM_V1 | COM | S vers N-perp, magnitude legacy | S,N,Po,Or | oui | GEOMETRY_COVERED | A | conserver ; distinct facial angle |
| M_SN_GOGN_DEG_V1 | Steiner | SN vs GoGn | S,N,Go,Gn | non | GEOMETRY_COVERED | A | conserver géométrie certifiée ; pas d'extension d'identité |
| M_FH_GOME_DEG_V1 | Tweed/McNamara/COM | FH vs Go-Me | Po,Or,Go,Me | non | GEOMETRY_COVERED | A | conserver uniquement contrat existant |
| M_FH_SUBGO_M_DEG_V1 | Ricketts | FH vs SubGo-M | Po,Or,SubGo,M | non | IMPLEMENTATION_MISSING | B | SubGo/M non disponibles |
| M_ANS_ME_MM_V1 | McNamara | distance ANS-Me | ANS,Me | oui | GEOMETRY_COVERED | A | conserver |
| M_PALATAL_PLANE_FH_DEG_V1 | McNamara/Ricketts | ANS-PNS vs FH | ANS,PNS,Po,Or | non | PRIMITIVE_AVAILABLE | B | PNS auto non autoritatif |
| M_OCCLUSAL_PLANE_SN_DEG_V1 | profil source-lock | plan occlusal vs SN | points occlusaux,S,N | non | SOURCE_LOCK_REQUIRED | B | définition/points non verrouillés |
| M_ORAL_GNOMON_ANS_XI_PM_DEG_V1 | Ricketts | oral gnomon | ANS,Xi,Pm | non | BLOCKED_LANDMARK | B | Xi/Pm indisponibles |
| M_BEND_OF_MANDIBLE_DEG_V1 | Ricketts | bend mandibulaire | source-specific | non | IMPLEMENTATION_MISSING | B | construction/landmarks non verrouillés |
| M_FACIAL_AXIS_RICKETTS_DEG_V1 | Ricketts | Pt-Ricketts / Gn construit | Pt_Ricketts,Gn_constructed,Ba,N | non | GEOMETRY_COVERED+BLOCKED_LANDMARK | B | exact Pt_Ricketts automatique absent |
| M_FACIAL_AXIS_MCNAMARA_DEG_V1 | McNamara | PTM-Gn vs N-perp | PTM_McNamara,Gn_constructed,Ba,N | non | IMPLEMENTATION_MISSING | B | PTM exact / construction spécialisée non prouvés |
| M_CO_A_MM_V1 | McNamara | Co-A | Co,A | oui | GEOMETRY_COVERED | A | conserver contrat existant |
| M_CO_GN_ANATOMIC_MM_V1 | McNamara | Co-Gn anatomique | Co,Gn_anatomic | oui | GEOMETRY_COVERED | A | conserver contrat certifié ; pas d'alias supplémentaire |
| M_CO_GN_MINUS_CO_A_MM_V1 | McNamara | (Co-Gn)-(Co-A) | Co,Gn_anatomic,A | oui | PRIMITIVE_AVAILABLE | B | identité anatomique automatique insuffisante pour nouvelle activation |
| M_U1_NA_DEG_V1 | Steiner | axe U1 vs NA | U1 apex/edge,N,A | non | GEOMETRY_COVERED | A | conserver |
| M_U1_NA_MM_V1 | Steiner | surface U1 vers NA | U1 facial surface,N,A | oui | BLOCKED_LANDMARK | B | surface faciale absente |
| M_U1_FH_DEG_V1 | COM | axe U1 vs FH | U1 apex/edge,Po,Or | non | GEOMETRY_COVERED | A | conserver ; distinct FMIA |
| M_U1_A_VERTICAL_MM_V1 | McNamara | U1 facial surface vers A-vertical | U1 facial surface,A,Po,Or | oui | BLOCKED_LANDMARK | B | surface faciale absente |
| M_U6_NA_MM_V1 | source-lock | U6 vers NA | U6,N,A | oui | BLOCKED_LANDMARK | B | landmark molaire exact absent |
| M_U6_PTV_MM_V1 | Ricketts | U6 vers PTV | U6,Pt_Ricketts/verticale dédiée | oui | BLOCKED_LANDMARK | B | landmarks exacts absents |
| M_L1_NB_DEG_V1 | Steiner | axe L1 vs NB | L1 apex/edge,N,B | non | GEOMETRY_COVERED | A | conserver |
| M_L1_NB_MM_V1 | Steiner | surface L1 vers NB | L1 facial surface,N,B | oui | BLOCKED_LANDMARK | B | surface faciale absente |
| M_L1_GOGN_DEG_V1 | Steiner | axe L1 vs GoGn | L1 apex/edge,Go,Gn_anatomic | non | IMPLEMENTATION_MISSING | B | Go/Gn spécialisés non certifiés pour nouvelle activation |
| M_IMPA_GOME_DEG_V1 | Tweed/COM | L1 vs Go-Me | L1 apex/edge,Go,Me | non | GEOMETRY_COVERED | A | conserver |
| M_FMIA_L1_FH_DEG_V1 | Tweed | L1 vs FH | L1 apex/edge,Po,Or | non | GEOMETRY_COVERED | A | conserver ; distinct U1-FH |
| M_L1_FACIAL_SURFACE_APOG_MM_V1 | source-lock | surface L1 vers A-Pog | L1 facial surface,A,Pog_hard | oui | BLOCKED_LANDMARK | B | surface faciale absente |
| M_L1_EDGE_APOG_MM_V1 | Ricketts | edge L1 vers A-Pog | L1 edge,A,Pog_hard | oui | PRIMITIVE_AVAILABLE | B | définition/source exacte et signe pas assez verrouillés pour activation |
| M_L1_DLINE_MM_V1 | Steiner 1959 | L1 vers D-line | L1,D-line landmarks | oui | BLOCKED_LANDMARK | B | D-line non disponible |
| M_L1_DLINE_DEG_V1 | Steiner 1959 | L1 vs D-line | L1,D-line landmarks | non | BLOCKED_LANDMARK | B | D-line non disponible |
| M_L6_NB_MM_V1 | source-lock | L6 vers NB | L6,N,B | oui | BLOCKED_LANDMARK | B | L6 exact absent |
| M_INTERINCISAL_DEG_V1 | Steiner/Ricketts/COM | axes U1/L1 | U1 apex/edge,L1 apex/edge | non | GEOMETRY_COVERED | A | conserver |
| M_OVERJET_MM_V1 | COM legacy | relation incisive | incisive landmarks | oui | LEGACY_TO_AUDIT | B | sémantique legacy à auditer |
| M_OVERBITE_V1 | COM legacy | relation incisive | incisive landmarks | oui (mm) | LEGACY_TO_AUDIT | B | unité verrouillée; géométrie/sémantique legacy encore à auditer |
| M_LI_EPLANE_MM_V1 | Ricketts | Li vers E-plane | Li,Prn,Pog_soft | oui | GEOMETRY_COVERED | A | conserver |
| M_LS_EPLANE_MM_V1 | Ricketts | Ls vers E-plane | Ls,Prn,Pog_soft | oui | GEOMETRY_COVERED | A | conserver |
| M_NASOLABIAL_ANGLE_DEG_V1 | soft tissue | angle nasolabial | landmarks soft exacts | non | SOURCE_LOCK_REQUIRED | B | définition/landmarks source-lock requis |
| M_UPPER_PHARYNX_MM_V1 | McNamara | espace pharyngé supérieur | points airway exacts | oui | BLOCKED_LANDMARK | B | landmarks absents |
| M_LOWER_PHARYNX_MM_V1 | McNamara | espace pharyngé inférieur | points airway exacts | oui | BLOCKED_LANDMARK | B | landmarks absents |
| M_PA_NASAL_CAVITY_WIDTH_MM_V1 | Ricketts PA | PA | landmarks PA | oui | BLOCKED_MODALITY_PA | B | modalité PA absente |
| M_PA_MAXILLARY_RELATION_R_MM_V1 | Ricketts PA | PA | landmarks PA | oui | BLOCKED_MODALITY_PA | B | modalité PA absente |
| M_PA_MAXILLARY_RELATION_L_MM_V1 | Ricketts PA | PA | landmarks PA | oui | BLOCKED_MODALITY_PA | B | modalité PA absente |
| M_PA_MANDIBULAR_WIDTH_MM_V1 | Ricketts PA | PA | landmarks PA | oui | BLOCKED_MODALITY_PA+NORM_HOLD | B | PA absente + hold normatif |
| M_PA_SKELETAL_SYMMETRY_V1 | Ricketts PA | PA | landmarks PA | unité non verrouillée | BLOCKED_MODALITY_PA+SOURCE_LOCK_REQUIRED | B | PA + source-lock |
| M_PA_INTERMOLAR_WIDTH_MM_V1 | Ricketts PA | PA | landmarks PA | oui | BLOCKED_MODALITY_PA | B | modalité PA absente |
| M_PA_INTERCANINE_WIDTH_MM_V1 | Ricketts PA | PA | landmarks PA | oui | BLOCKED_MODALITY_PA | B | modalité PA absente |
| M_PA_LOWER_MOLAR_FDP_R_MM_V1 | Ricketts PA | PA | landmarks PA | oui | BLOCKED_MODALITY_PA | B | modalité PA absente |
| M_PA_LOWER_MOLAR_FDP_L_MM_V1 | Ricketts PA | PA | landmarks PA | oui | BLOCKED_MODALITY_PA | B | modalité PA absente |
| M_PA_LOWER_INCISOR_FRONTAL_APO_MM_V1 | Ricketts PA | PA | landmarks PA | oui | BLOCKED_MODALITY_PA | B | modalité PA absente |
| M_PA_MOLAR_CROSSBITE_R_MM_V1 | Ricketts PA | PA | landmarks PA | oui | BLOCKED_MODALITY_PA | B | modalité PA absente |
| M_PA_MOLAR_CROSSBITE_L_MM_V1 | Ricketts PA | PA | landmarks PA | oui | BLOCKED_MODALITY_PA | B | modalité PA absente |
| M_SERIAL_INCISOR_DISPLACEMENT_V1 | serial | superposition | paired studies | non verrouillée | IMPLEMENTATION_MISSING | B | architecture paired/superposition absente |
| M_SERIAL_MOLAR_DISPLACEMENT_V1 | serial | superposition | paired studies | non verrouillée | IMPLEMENTATION_MISSING | B | architecture paired/superposition absente |
| M_SERIAL_CO_A_CHANGE_MM_V1 | serial McNamara | delta Co-A | paired Co,A | oui | IMPLEMENTATION_MISSING | B | paired-study authority absente |
| M_SERIAL_CO_GN_CHANGE_MM_V1 | serial McNamara | delta Co-Gn | paired Co,Gn | oui | IMPLEMENTATION_MISSING | B | paired-study authority absente |
| M_SERIAL_MAXMAND_DIFF_CHANGE_MM_V1 | serial McNamara | delta différentiel | paired lengths | oui | IMPLEMENTATION_MISSING | B | paired-study authority absente |
| M_SERIAL_ANS_ME_CHANGE_MM_V1 | serial McNamara | delta ANS-Me | paired ANS,Me | oui | IMPLEMENTATION_MISSING | B | paired-study authority absente |

## Sous-ensemble activé par ce lot

### M_A_NPERP_MM_V1

- Source primaire : McNamara 1984, DOI 10.1016/S0002-9416(84)90352-X.
- Construction : Frankfort anatomique `Po -> Or`; droite passant par N et perpendiculaire à FH.
- Mesure : projection signée `(A - N)` sur l'axe unitaire `Po -> Or`.
- Convention : antérieur positif, postérieur négatif.
- Unité : `mm`, verrouillée par le registre canonique.
- Calibration : obligatoire ; sans paire `mm_per_pixel + calibration_ref`, patient value indisponible.

### M_POG_NPERP_MM_V1

- Même construction N-perp.
- Cible : `Pog` osseux/hard, explicitement distinct de `Pog_soft`.
- Mesure : projection signée `(Pog - N)` sur `Po -> Or`.
- Convention : antérieur positif, postérieur négatif.
- Unité/calibration : identiques à A-Nperp.
- Aucun alias vers `M_B_NPERP_MM_V1`.

## Groupe B — règle de maintien

Toute mesure B reste non activée tant qu'au moins un verrou manque : source exacte, landmark spécialisé, construction non ambiguë, unité, calibration, modalité ou architecture longitudinale. Aucun statut B ne doit être promu par proximité lexicale avec une mesure existante.
