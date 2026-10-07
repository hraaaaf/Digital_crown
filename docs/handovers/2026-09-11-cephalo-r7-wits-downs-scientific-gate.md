# Céphalométrie R7 — Wits / Downs scientific gate

Date: 2026-09-11

## Sources vérifiées
1. Jacobson A. The "Wits" appraisal of jaw disharmony. Am J Orthod. 1975;67(2):125-138. DOI: `10.1016/0002-9416(75)90065-2`.
2. Downs WB. Variations in facial relationships; their significance in treatment and prognosis. Am J Orthod. 1948;34(10):812-840. DOI: `10.1016/0002-9416(48)90015-3`.
3. Corroboration moderne peer-reviewed de l'inventaire Downs: facial angle, angle of convexity, A-B plane angle, mandibular plane angle, Y-axis, occlusal-plane cant, interincisal angle, lower-incisor/occlusal-plane, lower-incisor/mandibular-plane, U1-A-Pog.

## Wits / Jacobson
### WITS_AO_BO_MM_V1 — BLOCKED_LANDMARK_CONVENTION
Définition primaire: projections perpendiculaires de A et B sur le plan occlusal, puis distance AO-BO mesurée le long de ce plan.

Le plan occlusal fonctionnel n'est pas encore défini par une paire de landmarks SRPose38 scientifiquement certifiée/versionnée. Les alias runtime `Occ_Ant` / `Occ_Post` ne suffisent pas comme evidence source-bound.

Aucune implémentation Wits n'est autorisée tant que ce gate n'est pas levé.

## Downs — sous-ensemble implémentable
### DOWNS_FACIAL_ANGLE_V1 — IMPLEMENTABLE
- géométrie: angle entre N-Pog et Frankfort Po-Or;
- landmarks: N, Pog, Po, Or;
- calibration: non requise;
- orientation/signature à verrouiller par source + runtime éventuel.

### DOWNS_CONVEXITY_ANGLE_V1 — IMPLEMENTABLE
- géométrie: angle N-A-Pog / angle entre N-A et A-Pog;
- landmarks: N, A, Pog;
- calibration: non requise;
- signature clinique à versionner explicitement; ne pas réduire silencieusement à un angle absolu si la source exige un signe.

### DOWNS_AB_PLANE_ANGLE_V1 — IMPLEMENTABLE
- géométrie: angle entre la ligne A-B et N-Pog;
- landmarks: A, B, N, Pog;
- calibration: non requise;
- convention signée à vérifier avant activation.

### DOWNS_Y_AXIS_V1 — IMPLEMENTABLE
- géométrie: S-Gn vs Frankfort Po-Or;
- landmarks: S, Gn, Po, Or;
- calibration: non requise.

## Downs — géométries déjà couvertes par contrats existants
### Mandibular plane angle / MP-FH
Même géométrie de base que FMA: Go-Me vs Po-Or. R6 expose déjà `TWEED_FMA_DEG_V1` avec parité runtime `Angle_de_Tweed`.

R7 ne doit pas créer une seconde source de vérité numérique sans justification. Le besoin éventuel d'un alias/profil Downs doit rester un mapping sémantique, pas un calcul divergent.

### Interincisal angle
Déjà versionné en R4 via `CRANIOM_INTERINCISAL_DEG_V1` et parité runtime `Inter_Incisif`.

### Lower incisor / mandibular plane angle
La géométrie L1 vs Go-Me est déjà couverte en R6 par `TWEED_IMPA_DEG_V1`. Toute représentation Downs doit réutiliser ce contrat ou prouver une convention distincte.

## Downs — bloqué par le plan occlusal
### DOWNS_OCCLUSAL_PLANE_FH_V1 — BLOCKED_LANDMARK_CONVENTION
Plan occlusal vs Frankfort.

### DOWNS_L1_OCCLUSAL_PLANE_V1 — BLOCKED_LANDMARK_CONVENTION
Axe L1 vs plan occlusal.

Même blocker que Wits: absence d'une convention occlusale SRPose38 certifiée/versionnée.

## Downs — linéaire à ne pas activer encore
### DOWNS_U1_APOG_MM_V1 — BLOCKED_SOURCE_LANDMARK_CONVENTION
La mesure linéaire U1 vers A-Pog nécessite de verrouiller le point dentaire exact utilisé par la source et la convention de distance signée. Ne pas substituer automatiquement `U1_incisal` sans source/versioning dédiés.

## Next exact R7
1. vérifier signe/orientation primaire de Facial Angle, Convexity, AB Plane et Y-axis avec une seconde source fiable;
2. auditer les champs runtime existants correspondant à ces quatre mesures;
3. implémenter uniquement ce sous-ensemble non ambigu;
4. réutiliser FMA/interincisal/IMPA au lieu de dupliquer les calculs;
5. garder Wits + mesures occlusales bloqués;
6. tests fail-closed + transitions + CI/T2 exact-head.

## Safety
ZERO LLM. Aucun Vercel. Aucune norme, classification, diagnostic ou traitement activé.


---

## Addendum — Facad 3.14 compatibility resolution — 2026-10-07

### Evidence base

The exhaustive official-installer inventory from run `37596906703` parsed all 73 shipped `.cph` profiles with zero parse failures. Artifact `11470928482`, digest `sha256:e520adef6c6c1a3faf0fbf5c2bda5c4bc9c6419d676ca43a352e388fb65f86e1`.

For `Downs.cph`:
- file SHA-256: `3415d02e655c5f4cb6b1e0ef466a0f75fa1947f971b3b200568f8f00925625de`;
- Facad file version: `3,9,0`;
- 10 measurements total.

Five rows previously left `UNMAPPED` by the conservative Facad -> DC mapper are dispositioned here. This addendum does **not** change clinical runtime and does **not** grant Facad norms diagnostic authority.

### 1. Convexity

Direct Facad definition:

`Angle4p(N, A, A, Pog)`, vendor norm `0±5.1`.

This is the Downs angle-of-convexity geometry family: line `N-A` versus line `A-Pog`. The existing R7 scientific gate already source-locked this geometry from Downs 1948, but Digital Crown has no dedicated canonical runtime measurement ID for the angular Downs value.

Disposition:

`DOWNS_HISTORICAL_GEOMETRY_SOURCE_LOCKED__CANONICAL_ID_MISSING__SIGNED_PARITY_GATED`

Proposed compatibility/canonical identity:

`M_DOWNS_CONVEXITY_NA_APOG_DEG_V1`

Runtime remains OFF. The Facad `Angle4p` argument order is evidence and must be preserved. The Reference Manual defines the four-point angle but does not, by itself, establish the exact clinical positive/negative convention required for Downs interpretation. Same-trace parity is required before a signed runtime claim.

### 2. A-B plane

Direct Facad definition:

`Angle4p(A, B, N, Pog)`, vendor norm `-4.6±3.7`.

This matches the source-locked Downs geometry family: line `A-B` versus facial plane `N-Pog`.

Disposition:

`DOWNS_HISTORICAL_GEOMETRY_SOURCE_LOCKED__CANONICAL_ID_MISSING__SIGNED_PARITY_GATED`

Proposed compatibility/canonical identity:

`M_DOWNS_AB_PLANE_AB_NPOG_DEG_V1`

Runtime remains OFF until the Facad/Downs sign convention is demonstrated on same-trace evidence. No absolute-angle substitution is allowed.

### 3. OL/FH

Direct Facad definition:

`Angle2ln(FH, OL)`, vendor norm `9.3±3.8`.

The Facad landmark guide defines `OLp` as “Occlusal Line, posterior point”. Independent peer-reviewed use of Facad documents `OLa` as an automatically constructed midpoint of `Is` and `Ii`, while `OLp` is manually plotted.

Downs' historical occlusal plane is source-described through the midpoint of incisal overbite and posterior first-molar occlusion. Therefore the anterior construction is compatible, but a generic manually placed `OLp` is not enough proof that the exact Downs posterior molar-contact convention was used.

Disposition:

`FACAD_VENDOR_OCCLUSAL_CANT__DOWNS_STRICT_OLP_SEMANTICS_UNPROVEN`

Proposed compatibility identity:

`M_FACAD_DOWNS_OL_FH_DEG_V1`

No alias to a generic/legacy occlusal plane and no strict Downs claim until `OLp` placement is source-bound.

### 4. ILi/OL

Direct Facad definition:

`Angle4p(Iia, Ii, OLp, OLa)`, vendor norm `75.5±3.5`.

This is the raw acute angle between the lower-incisor long axis and the Facad occlusal line. Downs literature conventionally reports the **deviation from a right angle**, approximately `14.5°`, rather than the raw `75.5°` axis-plane angle.

Therefore the Facad row must not be displayed or stored as if it were already the conventional reported Downs incisor/occlusal-plane value.

Disposition:

`FACAD_RAW_L1_OL_ANGLE__DOWNS_REPORTED_DEVIATION_IS_COMPLEMENT__RUNTIME_GATED`

Compatibility identities:
- raw vendor angle: `M_FACAD_DOWNS_L1_OL_RAW_DEG_V1`;
- candidate Downs-reported relation: `90° - raw_angle`, only after exact plane/sign/orientation parity is proven.

The same unresolved `OLp` placement gate applies.

### 5. Is to A-Pog

Direct Facad definition:

`Dist3p(Pog, A, Is)`, vendor norm `2.7±1.8`.

Facad `Is` is the upper-incisor tip. This is the same landmark family described for the Downs upper-incisor-to-A-Pog linear measure. Digital Crown already has a Ricketts-specific upper-incisal-edge A-Pog geometry, but an analysis-specific alias is not authorized because sign/orientation conventions and provenance are not automatically interchangeable.

Disposition:

`DOWNS_U1_EDGE_APOG_GEOMETRY_SOURCE_LOCKED__SIGNED_PARITY_GATED`

Proposed Downs identity:

`M_DOWNS_U1_EDGE_APOG_MM_V1`

Existing geometry-family reference only:

`M_RICKETTS_U1_APOG_PROTRUSION_MM_V1`

Direct aliasing is forbidden until sign parity is demonstrated.

### Scientific references / corroboration

- Primary Downs authority: Downs WB. *Variations in facial relationships; their significance in treatment and prognosis.* Am J Orthod. 1948;34(10):812-840. DOI `10.1016/0002-9416(48)90015-3`.
- Facad Reference Manual 3.13: `https://www.facad.com/dox/dox313/FacadTracingRefMan.pdf`.
- Facad landmark guide: `https://www.facad.com/dox/dox38/FacadTracingUsersGuide_ENG.pdf`.
- Peer-reviewed occlusal-plane review describing the original Downs construction: `https://pmc.ncbi.nlm.nih.gov/articles/PMC10318316/`.
- Peer-reviewed Downs measurement reconstruction: `https://pmc.ncbi.nlm.nih.gov/articles/PMC12949154/`.
- Facad landmark/construction use documenting manual `OLp` and midpoint `OLa`: `https://eos.journals.ekb.eg/article_78871_5aa73ba8051db89a8c446945ea15e7ae.pdf`.

### Runtime safety boundary

1. no new Downs clinical runtime in this addendum;
2. no Facad norm becomes a diagnostic/classification threshold;
3. preserve serialized Facad argument order;
4. no signed angular parity claim without same-trace evidence;
5. no generic `OLp` -> strict Downs posterior molar-contact substitution;
6. no direct `ILi/OL = Downs 14.5°` alias; complement semantics must remain explicit;
7. no cross-analysis Ricketts U1-A-Pog alias without sign/provenance proof.
