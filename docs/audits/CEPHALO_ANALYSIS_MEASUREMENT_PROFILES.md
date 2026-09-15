# Céphalo-N — Profils d'analyse basés sur le registre canonique

Statut : **WORKING V1 — PROFILS DE SÉLECTION, ZÉRO DUPLICATION DE FORMULE**

Date : 2026-09-15

## Principe

Chaque analyse référence des `measurement_id` du registre `CEPHALO_CANONICAL_MEASUREMENT_REGISTRY.md`.

Aucune formule, aucun landmark et aucune norme n'est recopié dans ce fichier.

Colonnes :

`ANALYSE_VERSION | MEASUREMENT_ID | RÔLE | ÉTAT DANS LE PROFIL`

- `CORE` : mesure constitutive du profil/version.
- `SUPPL` : mesure supplémentaire/sérielle de la version.
- `OPTIONNEL` : mesure contextuelle utile mais hors noyau quantitatif.
- `LOCKED` : identité avec le registre canonique verrouillée.
- `PENDING_EQUIVALENCE` : profil candidat, équivalence exacte encore à fermer avant activation.
- `BLOCKED_*` : membre scientifique valide mais non calculable actuellement.

---

# Steiner

## `STEINER_1953_CORE_V1`

| Measurement ID | Rôle | État |
|---|---|---|
| `M_SNA_DEG_V1` | CORE | LOCKED |
| `M_SNB_DEG_V1` | CORE | LOCKED |
| `M_ANB_DEG_V1` | CORE | LOCKED |
| `M_U1_NA_DEG_V1` | CORE | LOCKED |
| `M_U1_NA_MM_V1` | CORE | BLOCKED_LANDMARK |
| `M_L1_NB_DEG_V1` | CORE | LOCKED |
| `M_L1_NB_MM_V1` | CORE | BLOCKED_LANDMARK |
| `M_INTERINCISAL_DEG_V1` | CORE/SUPPL | LOCKED |
| `M_OCCLUSAL_PLANE_SN_DEG_V1` | CORE | SOURCE_LOCK_REQUIRED |
| `M_SN_GOGN_DEG_V1` | CORE | LOCKED_GEOMETRY |
| `M_L1_GOGN_DEG_V1` | SUPPL | IMPLEMENTATION_MISSING |
| `M_U6_NA_MM_V1` | SUPPL/SERIAL | BLOCKED_LANDMARK |
| `M_L6_NB_MM_V1` | SUPPL/SERIAL | BLOCKED_LANDMARK |

**Cardinalité 1953 : 13 références canoniques.**

## `STEINER_1959_CLINICAL_EXTENSION_V1`

Cette version **étend** le profil 1953 et ajoute :

| Measurement ID | Rôle | État |
|---|---|---|
| `M_SND_DEG_V1` | CORE extension | BLOCKED_LANDMARK |
| `M_POG_NB_MM_V1` | CORE extension | IMPLEMENTATION_MISSING |
| `M_L1_DLINE_MM_V1` | EXTENSION | BLOCKED_LANDMARK |
| `M_L1_DLINE_DEG_V1` | EXTENSION | BLOCKED_LANDMARK |
| `M_SERIAL_INCISOR_DISPLACEMENT_V1` | SERIAL | IMPLEMENTATION_MISSING |
| `M_SERIAL_MOLAR_DISPLACEMENT_V1` | SERIAL | IMPLEMENTATION_MISSING |

**Ajouts 1959 : 6. Profil complet 1959 = 13 + 6 = 19 références.**

---

# Tweed

## `TWEED_1954_TRIANGLE_DC_PO_OR_V1`

| Measurement ID | Rôle | État |
|---|---|---|
| `M_FH_GOME_DEG_V1` | CORE — FMA | LOCKED pour variante DC Po-Or/Go-Me |
| `M_IMPA_GOME_DEG_V1` | CORE — IMPA | LOCKED |
| `M_FMIA_L1_FH_DEG_V1` | CORE — FMIA | LOCKED |

**Cardinalité : 3.**

Important : ce profil est la **variante Digital Crown Po-Or sélectionnée**, pas une revendication de reproduction géométrique stricte de l'ear-rod Frankfort de Tweed 1954. Les normes historiques restent séparées.

---

# McNamara

## `MCNAMARA_1984_SINGLE_FILM_V1`

| Measurement ID | Rôle | État |
|---|---|---|
| `M_A_NPERP_MM_V1` | CORE | LOCKED construction ; contrat dédié à matérialiser |
| `M_SNA_DEG_V1` | CORE contextuel | LOCKED |
| `M_CO_GN_ANATOMIC_MM_V1` | CORE | LOCKED geometry / auto anatomy non autoritaire |
| `M_CO_A_MM_V1` | CORE | LOCKED geometry / auto anatomy non autoritaire |
| `M_CO_GN_MINUS_CO_A_MM_V1` | CORE | PRIMITIVE_AVAILABLE |
| `M_ANS_ME_MM_V1` | CORE | LOCKED |
| `M_FH_GOME_DEG_V1` | CORE — mandibular plane angle | LOCKED geometry |
| `M_FACIAL_AXIS_MCNAMARA_DEG_V1` | CORE | IMPLEMENTATION_MISSING |
| `M_POG_NPERP_MM_V1` | CORE | PRIMITIVE_AVAILABLE |
| `M_U1_A_VERTICAL_MM_V1` | CORE | BLOCKED_LANDMARK |
| `M_L1_FACIAL_SURFACE_APOG_MM_V1` | CORE | BLOCKED_LANDMARK |
| `M_UPPER_PHARYNX_MM_V1` | CORE | BLOCKED_LANDMARK |
| `M_LOWER_PHARYNX_MM_V1` | CORE | BLOCKED_LANDMARK |

**Cardinalité quantitative principale : 13.**

### Contexte optionnel

| Measurement ID | Rôle | État |
|---|---|---|
| `M_NASOLABIAL_ANGLE_DEG_V1` | OPTIONNEL / soft tissue context | SOURCE_LOCK_REQUIRED |

### Couche sérielle séparée

| Measurement ID | Rôle | État |
|---|---|---|
| `M_SERIAL_CO_A_CHANGE_MM_V1` | SERIAL | IMPLEMENTATION_MISSING |
| `M_SERIAL_CO_GN_CHANGE_MM_V1` | SERIAL | IMPLEMENTATION_MISSING |
| `M_SERIAL_MAXMAND_DIFF_CHANGE_MM_V1` | SERIAL | IMPLEMENTATION_MISSING |
| `M_SERIAL_ANS_ME_CHANGE_MM_V1` | SERIAL | IMPLEMENTATION_MISSING |

---

# Ricketts

## `RICKETTS_1981_SUMMARY_DESCRIPTIVE_V1` — Profil : 11 facteurs

| # | Measurement ID | Rôle | État |
|---:|---|---|---|
| 1 | `M_FACIAL_AXIS_RICKETTS_DEG_V1` | CORE | geometry LOCKED / auto Pt BLOCKED_LANDMARK |
| 2 | `M_FACIAL_ANGLE_NPOG_FH_DEG_V1` | CORE | LOCKED geometry ; nomenclature runtime à corriger séparément |
| 3 | `M_FH_SUBGO_M_DEG_V1` | CORE | IMPLEMENTATION_MISSING |
| 4 | `M_ORAL_GNOMON_ANS_XI_PM_DEG_V1` | CORE | BLOCKED_LANDMARK |
| 5 | `M_PALATAL_PLANE_FH_DEG_V1` | CORE | PRIMITIVE_AVAILABLE / PNS auto non autoritaire |
| 6 | `M_MAXILLARY_CONVEXITY_A_NPOG_MM_V1` | CORE | LOCKED |
| 7 | `M_L1_EDGE_APOG_MM_V1` | CORE | PRIMITIVE_AVAILABLE |
| 8 | `M_U6_PTV_MM_V1` | CORE | BLOCKED_LANDMARK |
| 9 | `M_INTERINCISAL_DEG_V1` | CORE | LOCKED |
| 10 | `M_LI_EPLANE_MM_V1` | CORE | LOCKED |
| 11 | `M_BEND_OF_MANDIBLE_DEG_V1` | CORE | IMPLEMENTATION_MISSING |

**Cardinalité profil : 11.**

### Extension tissus mous déjà disponible dans DC

| Measurement ID | Rôle | État |
|---|---|---|
| `M_LS_EPLANE_MM_V1` | OPTIONNEL | LOCKED geometry ; hors noyau 11 facteurs 1981 |

## `RICKETTS_1981_SUMMARY_DESCRIPTIVE_V1` — PA/frontale : 12 facteurs

| # | Measurement ID | Rôle | État |
|---:|---|---|---|
| 1 | `M_PA_NASAL_CAVITY_WIDTH_MM_V1` | CORE | BLOCKED_MODALITY_PA |
| 2 | `M_PA_MAXILLARY_RELATION_R_MM_V1` | CORE | BLOCKED_MODALITY_PA |
| 3 | `M_PA_MAXILLARY_RELATION_L_MM_V1` | CORE | BLOCKED_MODALITY_PA |
| 4 | `M_PA_MANDIBULAR_WIDTH_MM_V1` | CORE | BLOCKED_MODALITY_PA / NORM_HOLD |
| 5 | `M_PA_SKELETAL_SYMMETRY_V1` | CORE | BLOCKED_MODALITY_PA + SOURCE_LOCK_REQUIRED |
| 6 | `M_PA_INTERMOLAR_WIDTH_MM_V1` | CORE | BLOCKED_MODALITY_PA |
| 7 | `M_PA_INTERCANINE_WIDTH_MM_V1` | CORE | BLOCKED_MODALITY_PA |
| 8 | `M_PA_LOWER_MOLAR_FDP_R_MM_V1` | CORE | BLOCKED_MODALITY_PA |
| 9 | `M_PA_LOWER_MOLAR_FDP_L_MM_V1` | CORE | BLOCKED_MODALITY_PA |
| 10 | `M_PA_LOWER_INCISOR_FRONTAL_APO_MM_V1` | CORE | BLOCKED_MODALITY_PA |
| 11 | `M_PA_MOLAR_CROSSBITE_R_MM_V1` | CORE | BLOCKED_MODALITY_PA |
| 12 | `M_PA_MOLAR_CROSSBITE_L_MM_V1` | CORE | BLOCKED_MODALITY_PA |

**Cardinalité Ricketts 1981 : 11 profil + 12 frontal = 23 core, + 1 extension optionnelle DC.**

---

# COM

## `COM_DC_LEGACY_V1`

| # | Measurement ID | Libellé COM actuel | État |
|---:|---|---|---|
| 1 | `M_OVERJET_MM_V1` | Surplomb | LEGACY_TO_AUDIT |
| 2 | `M_OVERBITE_V1` | Recouvrement | LEGACY_TO_AUDIT |
| 3 | `M_IMPA_GOME_DEG_V1` | IMPA | LOCKED shared geometry |
| 4 | `M_U1_FH_DEG_V1` | I / Frankfort | LOCKED geometry |
| 5 | `M_INTERINCISAL_DEG_V1` | Angle interincisif | LOCKED shared geometry |
| 6 | `M_FH_GOME_DEG_V1` | Angle de Tweed / FMA | LOCKED shared geometry |
| 7 | `M_AB_PRIME_FH_MM_V1` | Décalage osseux A′B′ | LOCKED internal DC geometry |
| 8 | `M_A_NPERP_MM_V1` | Situation A | **PENDING_EQUIVALENCE** : même géométrie candidate, signer/convention à fermer |
| 9 | `M_B_NPERP_MM_V1` | Situation B | LOCKED internal DC geometry |
| 10 | `M_COM_S_NPERP_DEPTH_MM_V1` | Profondeur faciale DC | LOCKED internal DC geometry |

**Cardinalité : 10.**

---

# Mesures partagées visibles immédiatement

| Measurement ID | Profils qui le référencent |
|---|---|
| `M_SNA_DEG_V1` | Steiner 1953 + McNamara 1984 |
| `M_INTERINCISAL_DEG_V1` | Steiner 1953 + Ricketts 1981 + COM DC |
| `M_FH_GOME_DEG_V1` | Tweed DC + McNamara 1984 + COM DC |
| `M_IMPA_GOME_DEG_V1` | Tweed DC + COM DC |
| `M_A_NPERP_MM_V1` | McNamara 1984 + COM DC candidate alias |

Ces lignes sont calculées **une seule fois** dans le futur moteur canonique. Les profils appliquent ensuite leur propre statut, ordre UI, norme et interprétation.

# Faux doublons explicitement interdits

| Mesure A | Mesure B | Pourquoi distinctes |
|---|---|---|
| `M_B_NPERP_MM_V1` | `M_POG_NPERP_MM_V1` | B ≠ Pog |
| `M_U1_FH_DEG_V1` | `M_FMIA_L1_FH_DEG_V1` | incisive supérieure ≠ incisive inférieure |
| `M_FACIAL_ANGLE_NPOG_FH_DEG_V1` | `M_COM_S_NPERP_DEPTH_MM_V1` | angle N-Pog/FH ≠ distance S→Nperp |
| `M_FACIAL_AXIS_RICKETTS_DEG_V1` | `M_FACIAL_AXIS_MCNAMARA_DEG_V1` | Pt_Ricketts ≠ PTM_McNamara |
| `M_L1_EDGE_APOG_MM_V1` | `M_L1_FACIAL_SURFACE_APOG_MM_V1` | bord incisif ≠ surface faciale coronaire |
| `M_FH_GOME_DEG_V1` | `M_FH_SUBGO_M_DEG_V1` | Go-Me ≠ Sub.Go.-M |

## Next exact

1. Fermer les quelques `PENDING_EQUIVALENCE` / `SOURCE_LOCK_REQUIRED` qui empêchent une identité canonique définitive.
2. Vérifier automatiquement les cardinalités 13 / 3 / 13 / 23 / 10 contre la cartographie source.
3. Après verrouillage, matérialiser ces profils en structures de données versionnées sans dupliquer les fonctions de géométrie.
4. Implémenter les mesures manquantes au niveau du registre, jamais directement dans un profil d'analyse.