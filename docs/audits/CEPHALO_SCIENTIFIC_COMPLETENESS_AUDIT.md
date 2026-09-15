# CEPHALO SCIENTIFIC COMPLETENESS AUDIT — Céphalo-N

**Statut :** AUDIT SOURCE-LOCKED — HUMAN GATE REQUIS AVANT MODIFICATION SCIENTIFIQUE  
**Baseline auditée :** `master@0097e3a08340f753803a86d2a1134880ad9ce902`  
**Périmètre :** Steiner, Tweed, McNamara, Ricketts, COM, Toutes analyses ; backend géométrique, evidence graph, read-path, tracing et Workbench R19.  
**Nature de ce lot :** documentation/audit uniquement. Aucune formule, norme, interprétation clinique, DB, patient, document ou UI n'est modifié par ce commit.

---

## 0. Goal / Success / Proof

### Goal

Établir avant toute implémentation une spécification de complétude céphalométrique source-lockée, distinguant sans ambiguïté :

1. ce qui est déjà calculé correctement ;
2. ce qui existe dans une couche backend mais n'atteint pas le runtime/UI ;
3. ce qui est tracé sans être mesuré ;
4. ce qui est affiché sans être calculé ;
5. ce qui manque réellement au backend ;
6. ce qui est impossible sans landmarks/conventions supplémentaires ;
7. ce qui ne peut recevoir aucune norme/interprétation tant que source, version et population ne sont pas verrouillées.

### Success observable

- une matrice `MEASURE → SOURCE → LANDMARKS → FORMULE → BACKEND → TRACING → UI → STATUS` est présente ;
- chaque analyse nommée a une source primaire identifiée et au moins une corroboration scientifique indépendante lorsque disponible ;
- les variantes historiques et Digital Crown ne sont jamais fusionnées silencieusement ;
- les normes non validées restent non autoritatives ;
- les P0/P1 et lots d'implémentation sont explicités ;
- aucune modification clinique n'est autorisée avant le HUMAN GATE final.

### Proof

Preuves repo lues sur la baseline :

- `docs/audits/CEPHALO_R19_ANALYSIS_REFERENCE_LAYOUT.md`
- `docs/CEPHALO_DIAGNOSTIC_SPEC.md`
- `docs/SRPOSE38_LANDMARK_CONTRACT.md`
- `backend/services/cephalo_engine.py`
- `backend/services/cephalo_safe_engine.py`
- `backend/services/cephalo_service.py`
- `backend/services/cephalo_constructions.py`
- `backend/services/cephalo_runtime_evidence.py`
- `backend/services/cephalo_runtime_chain.py`
- `backend/services/cephalo_typed_read.py`
- `backend/services/cephalo_landmark_correction_evidence.py`
- `backend/services/cephalo_steiner_geometry.py`
- `backend/services/cephalo_steiner_evidence_adapter.py`
- `backend/services/cephalo_steiner_dental_evidence.py`
- `backend/services/cephalo_tweed_merrifield_geometry.py`
- `backend/services/cephalo_tweed_merrifield_evidence.py`
- `backend/services/cephalo_mcnamara_geometry.py`
- `backend/services/cephalo_mcnamara_evidence.py`
- `backend/services/cephalo_ricketts_geometry.py`
- `backend/services/cephalo_ricketts_evidence.py`
- `backend/services/cephalo_com_evidence_ledger.py`
- `backend/services/cephalo_normative_registry.py`
- `backend/services/cephalo_normative_service.py`
- `frontend/src/features/ortho/CephaloTracingLayer.tsx`
- `frontend/src/features/ortho/CephaloTracingLayerBase.tsx`
- `frontend/src/features/ortho/components/CephaloAnalysisWorkbenchPanel.tsx`
- `backend/tests/test_cephalo_runtime_evidence.py`
- `backend/tests/test_cephalo_normative_service.py`

---

## 1. Conclusion exécutive : le problème principal n'est pas un backend géométrique vide

### Conclusion vérifiée

L'hypothèse « les analyses sont incomplètes parce que le backend ne sait presque rien calculer » est **fausse dans sa forme générale**.

Digital Crown possède déjà :

- un moteur géométrique brut fail-closed ;
- des constructions versionnées ;
- un graphe d'evidence typé ;
- des adapters source-spécifiques Steiner, Tweed/Merrifield, McNamara et Ricketts ;
- un registre normatif séparé et fail-closed ;
- un contrat SRPose38 explicite ;
- des tests de persistance/parité pour une partie du pipeline.

Le défaut dominant est une **rupture de continuité scientifique entre les couches** :

`landmarks → geometry/evidence source-spécifique → evidence graph → read-path autoritatif → rows UI/tracing`.

Actuellement :

- plusieurs mesures existent dans des modules source-spécifiques mais ne sont pas composées dans l'evidence graph actif ;
- le read-path typé ne projette autoritativement que quatre mesures linéaires CRANIOM ;
- le Workbench R19 expose des listes statiques très réduites ;
- « Toutes analyses » n'est pas l'union des analyses ;
- le tracing contient encore une fuite normative frontend indépendante du backend sécurisé.

**Donc :** la priorité n'est pas de réécrire `cephalo_engine.py`. La priorité est de rendre la chaîne typed-evidence/read-path/UI cohérente, puis de compléter seulement les mesures réellement absentes.

---

## 2. Source lock et variantes

### 2.1 Steiner

**Primaire canonique :**

- Steiner CC. *Cephalometrics for you and me*. Am J Orthod. 1953;39(10):729-755. DOI `10.1016/0002-9416(53)90082-7`.
- Extension clinique : Steiner CC. *Cephalometrics in Clinical Practice*. Angle Orthod. 1959;29:8-29.

**Corroborations indépendantes :** littérature peer-reviewed contemporaine définissant SNA/SNB/ANB, U1-NA angle/distance, L1-NB angle/distance et interincisal ; les études populationnelles montrent que les références numériques ne doivent pas être universalisées.

**Variante à verrouiller :** le plan mandibulaire Steiner retenu par la couche typed actuelle est `Go-Gn`, pas `Go-Me`. Toute autre convention doit avoir un autre `method_id`.

### 2.2 Tweed pur vs Merrifield

**Primaires Tweed :**

- Tweed CH. *The Frankfort-mandibular incisor angle (FMIA) in orthodontic diagnosis, treatment planning and prognosis*. Angle Orthod. 1954;24:121-169.
- Tweed CH. *The diagnostic facial triangle in the control of treatment objectives*. Am J Orthod. 1969;55(6):651-667. DOI `10.1016/0002-9416(69)90041-4`.

**Corroboration indépendante :** Iwasawa T, Moro T, Nakamura K. *Tweed triangle and soft-tissue consideration of Japanese with normal occlusion and good facial profile*. Am J Orthod. 1977;72(2):119-127. DOI `10.1016/0002-9416(77)90054-9`.

**Séparation obligatoire :** FMA/IMPA/FMIA = Tweed ; Z-angle = Merrifield, avec `analysis_id=MERRIFIELD` séparé dans le repo.

**Avertissement source exact :** le tracing historique de Tweed utilise une construction historique de Frankfort et du bord inférieur mandibulaire. Le couple Digital Crown actuel `Po-Or` + `Go-Me` est une géométrie versionnée utile, mais ne doit pas recevoir silencieusement les normes historiques de Tweed 1954 comme si les constructions étaient identiques.

### 2.3 McNamara

**Primaire :** McNamara JA Jr. *A method of cephalometric evaluation*. Am J Orthod. 1984;86(6):449-469. DOI `10.1016/S0002-9416(84)90352-X`.

**Corroboration indépendante :** Storniolo-Souza JM et al. *McNamara analysis cephalometric parameters in White-Brazilians, Japanese and Japanese-Brazilians with normal occlusion*. Dental Press J Orthod. 2021;26(1):e2119133. DOI `10.1590/2177-6709.26.1.e2119133.oar`, PMCID `PMC8018756`.

Cette source indépendante confirme notamment A-Nperp, Co-Gn, Co-A, différence maxillo-mandibulaire, ANS-Me, angle plan mandibulaire, axe facial Ba-N/Pt-Gn, Pog-Nperp, incisives et angle nasolabial, et montre des dépendances sexe/population.

### 2.4 Ricketts

**Primaires :**

- Ricketts RM. *A foundation for cephalometric communication*. Am J Orthod. 1960;46(5):330-357. DOI `10.1016/0002-9416(60)90047-6`.
- Ricketts RM. *Perspectives in the clinical application of cephalometrics. The first fifty years*. Angle Orthod. 1981;51(2):115-150. DOI `10.1043/0003-3219(1981)051<0115:PITCAO>2.0.CO;2`.

**Corroboration indépendante :** Bae EJ, Kwon HJ, Kwon OW. *Changes in longitudinal craniofacial growth in subjects with normal occlusions using the Ricketts analysis*. Korean J Orthod. 2014;44(2):77-87. DOI `10.4041/kjod.2014.44.2.77`, PMCID `PMC3971129`.

Cette étude confirme que Ricketts ne se réduit pas à l'E-line : familles dentaire, dentosquelettique, squelettique, mâchoires/crâne et structures internes ; plusieurs mesures varient avec âge et sexe.

### 2.5 COM

Aucune source primaire unique ne définit dans le repo ou la littérature auditée un « COM » universel correspondant exactement au paquet R19.

Le ledger interne montre au contraire un assemblage de lignées Tweed, Downs, Steiner, Ricketts, CRANIOM et Ballard/Eastman, avec plusieurs dettes de source explicites.

**Statut du paquet : `PROTOCOLE INTERNE NON SOURCE-LOCKED`.**

Les mesures individuelles peuvent être source-lockées séparément. Le paquet COM ne reçoit aucune norme universelle par héritage.

---

## 3. Landmarks : disponibilité réelle

### 3.1 Contrat 19 points

Set documenté : `S,N,Po,Or,Ar,Co,Ba,ANS,PNS,A,B,Pog,Gn,Me,Go,U1i,U1R,L1i,L1R`.

Il permet géométriquement une part importante de Steiner/Tweed/McNamara et certains éléments Ricketts, mais ne contient pas les landmarks tissus mous nécessaires à E-line/nasolabial ni `Pt`, `Xi`, `Pm`, `CF/DC`.

### 3.2 Contrat SRPose38

Ordre/noms certifiés par `docs/SRPOSE38_LANDMARK_CONTRACT.md` :

`S,N,Or,Po,A,B,Pog,Me,Gn,Go,L1_incisal,U1_incisal,Ls_soft,Li_soft,Sn_soft,Pog_soft,PNS,ANS,Ar,D_point,U1_apex,L1_apex,Cm,Ptm,Co,Prn,Ba,PT_point,Bo,Ls2,Li2,Gn_soft,Me_soft,G_soft,N_soft,C_point,U6,L6`.

**Nuances qui restent bloquantes :**

- `Go` : convention anatomique vs Gonion construit à verrouiller analyse par analyse ;
- `Po` : anatomical Porion vs machine/ear-rod ;
- `PT_point` : son nom CL-Detection ne suffit pas à certifier l'identité avec le `Pt` exact de Ricketts/McNamara ;
- `Xi`, `Pm`, `CF/DC` : absents du contrat SRPose38.

Présence d'un nom ≠ autorisation de substitution dans une analyse historique.

---

## 4. Cartographie de l'architecture actuelle

### Ce qui est sain

- `cephalo_engine.py` : géométrie brute uniquement ; pas de norme/diagnostic/traitement.
- `cephalo_safe_engine.py` : retire toute autorité normative du payload legacy.
- `cephalo_normative_service.py` : couche normative séparée, versionnée, age/sex/population aware, fail-closed, non branchée aux consommateurs cliniques.
- evidence adapters : `analysis_id`, `method_id`, version et constructions explicites.

### Ruptures actuelles

1. `build_cephalo_runtime_evidence_payload()` compose CRANIOM + Steiner ; Tweed/Merrifield/Downs arrivent indirectement via l'adapter Steiner, mais McNamara et Ricketts ne sont pas composés.
2. La reconstruction après édition landmark reproduit la même limitation.
3. `cephalo_typed_read.py` rend autoritatives uniquement quatre mesures linéaires CRANIOM.
4. McNamara et Ricketts ont des modules source-spécifiques partiellement prêts mais orphelins du read-path actif.
5. R19 utilise une liste UI statique par analyse au lieu d'un registre de mesures source-versionné.

---

## 5. Matrice scientifique de complétude

Convention : `—` = aucune norme autoritative activée par cet audit. Les normes historiques restent des métadonnées de source tant que construction + population + version ne sont pas validées.

### 5.1 Steiner

| MEASURE | SOURCE | LANDMARKS | PLAN / LINE | GEOMETRIC FORMULA | UNIT | NORM | AGE/SEX/POP | CURRENT BACKEND | CURRENT TRACING | CURRENT UI | STATUS |
|---|---|---|---|---|---|---|---|---|---|---|---|
| SNA | Steiner 1953 | S,N,A | SN / NA | angle(SN,NA) | ° | — | population-dependent refs | engine + typed | SN+NA | Steiner row | COMPLETE |
| SNB | Steiner 1953 | S,N,B | SN / NB | angle(SN,NB) | ° | — | population-dependent refs | engine + typed | SN+NB | Steiner row | COMPLETE |
| ANB | Steiner 1953 | S,N,A,B | NA / NB | SNA−SNB, parity checked | ° | — | geometry/age/pop influence | engine + typed | NA+NB | Steiner row | COMPLETE |
| SN-GoGn | Steiner 1953/1959, current V1 | S,N,Go,Gn | SN / GoGn | angle between source axes | ° | — | population/age | typed `STEINER_SN_MP_DEG_V1` | GoGn not exposed in Steiner mode | absent | CALCULATED BUT NOT DISPLAYED |
| U1-NA angle | Steiner 1953/1959 | U1 apex/tip,N,A | U1 axis / NA | non-reflex source angle | ° | — | population | typed `STEINER_U1_NA_DEG_V1` | Steiner mode omits U1 | absent | CALCULATED BUT NOT DISPLAYED |
| U1-NA distance | Steiner | U1 tip,N,A | point→NA | perpendicular distance to NA; sign convention must be versioned | mm | — | population | absent | absent | absent | MISSING |
| L1-NB angle | Steiner | L1 apex/tip,N,B | L1 axis / NB | non-reflex source angle | ° | — | population | typed `STEINER_L1_NB_DEG_V1` | Steiner mode omits L1 | absent | CALCULATED BUT NOT DISPLAYED |
| L1-NB distance | Steiner | L1 tip,N,B | point→NB | perpendicular distance to NB; sign convention must be versioned | mm | — | population | absent | absent | absent | MISSING |
| Interincisal | Steiner extended | U1 axis,L1 axis | U1/L1 | angle axes | ° | — | population | engine/CRANIOM | visible outside Steiner | absent from Steiner | CALCULATED BUT NOT DISPLAYED |
| Occlusal/SN | Steiner | SN + source occlusal points | SN / occlusal | exact occlusal-plane definition required | ° | — | age/dentition | absent | orphan `Occ_Ant/Occ_Post` logic | absent | IMPOSSIBLE WITH CURRENT LANDMARKS |
| SND | Steiner extended | S,N,D | SN / ND | exact source angle | ° | — | source-specific | 38 has `D_point`, method absent | absent | absent | MISSING |
| Pog/NB | Steiner extended | Pog,N,B | Pog→NB | perpendicular distance; exact sign/source | mm | — | population | absent | absent | absent | MISSING |

### 5.2 Tweed pur

| MEASURE | SOURCE | LANDMARKS | PLAN / LINE | GEOMETRIC FORMULA | UNIT | NORM | AGE/SEX/POP | CURRENT BACKEND | CURRENT TRACING | CURRENT UI | STATUS |
|---|---|---|---|---|---|---|---|---|---|---|---|
| FMA | Tweed 1954/1969 | historical FH + mandibular border | FH / MP | angle(FH,MP) | ° | historical only | population | engine + typed DC `Po-Or/Go-Me` | FH+MP | Tweed row | NON SOURCE-LOCKED |
| IMPA | Tweed 1954 | L1 axis + MP | L1 / MP | angle(L1,MP) | ° | historical only | population | engine + typed DC `Go-Me` | L1+MP | Tweed row | NON SOURCE-LOCKED |
| FMIA | Tweed 1954 | L1 axis + FH | L1 / FH | angle(L1,FH) | ° | historical only | population | typed `TWEED_FMIA_DEG_V1` | FH/L1 available | absent | CALCULATED BUT NOT DISPLAYED |
| Triangle consistency | Tweed | same 3 axes | FH/MP/L1 | `FMA+IMPA+FMIA=180°` only under one coherent internal-angle convention | ° | n/a | n/a | no dedicated invariant certified in this audit | n/a | n/a | MISSING |
| Z-angle | Merrifield 1966 | soft Pog + most protrusive lip + FH | profile/FH | source-specific Merrifield | ° | — | population | typed `MERRIFIELD`, separate | absent | absent | COMPLETE as separate variant, not Tweed |

**Décision scientifique :** les géométries DC FMA/IMPA sont utiles mais ne doivent pas être appelées « exact Tweed 1954 » tant que le plan mandibulaire/Frankfort historique n'est pas source-locké landmark par landmark.

### 5.3 McNamara

| MEASURE | SOURCE | LANDMARKS | PLAN / LINE | GEOMETRIC FORMULA | UNIT | NORM | AGE/SEX/POP | CURRENT BACKEND | CURRENT TRACING | CURRENT UI | STATUS |
|---|---|---|---|---|---|---|---|---|---|---|---|
| A→N-perp | McNamara 1984 | A,N,Po,Or | N-perp to FH | signed AP distance to N-perp | mm | — | age/pop/sex | generic CRANIOM analogue only; no McNamara method ID | line drawn | absent in McNamara tab | NON SOURCE-LOCKED |
| Pog→N-perp | McNamara 1984 | Pog,N,Po,Or | N-perp | signed AP distance | mm | — | age/pop/sex | absent | N-perp exists | absent | MISSING |
| Co-A | McNamara 1984 | Co,A | segment | Euclidean length × verified mm/px | mm | — | age/sex/pop | source module R8 exists, not active graph/read-path | line | row NC | DISPLAYED BUT NOT CALCULATED |
| Co-Gn | McNamara 1984 | Co,Gn | segment | Euclidean length × verified mm/px | mm | — | age/sex/pop | source module R8 exists, not active graph/read-path | line | row NC | DISPLAYED BUT NOT CALCULATED |
| Maxillo-mandibular difference | McNamara 1984 | Co,A,Gn | lengths | Co-Gn − Co-A | mm | — | age/sex/pop | absent | absent | absent | MISSING |
| ANS-Me | McNamara 1984 | ANS,Me | segment | Euclidean length × verified mm/px | mm | — | age/sex/pop | source module R8 exists, not active graph/read-path | line | row NC | DISPLAYED BUT NOT CALCULATED |
| Mandibular plane angle | McNamara 1984 | Po,Or,Go,Me | FH/Go-Me | angle planes | ° | — | population | generic FMA exists; no McNamara method ID | planes available | absent | MISSING |
| Facial axis | McNamara corroborated | Ba,N,Pt,Gn | Ba-N / Pt-Gn | exact source angle | ° | — | age/sex/pop | absent | absent | absent | IMPOSSIBLE WITH CURRENT LANDMARKS |
| Upper incisor→A vertical | McNamara | U1,A,FH | vertical through A ⟂ FH | signed linear distance | mm | — | population | absent | absent | absent | MISSING |
| Lower incisor→A-Pog | McNamara | L1,A,Pog | A-Pog | perpendicular signed distance | mm | — | population | absent | absent | absent | MISSING |
| Nasolabial | McNamara | Prn,Sn,Ls | Prn-Sn / Sn-Ls | angle at Sn | ° | — | age/sex/pop | 38 landmarks available; method absent | soft profile only | absent | MISSING |

`Pt` remains a hard gate: `PT_point` from CL-Detection cannot be silently declared equivalent to the source-specific Pt required by McNamara/Ricketts.

### 5.4 Ricketts

| MEASURE | SOURCE | LANDMARKS | PLAN / LINE | GEOMETRIC FORMULA | UNIT | NORM | AGE/SEX/POP | CURRENT BACKEND | CURRENT TRACING | CURRENT UI | STATUS |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Facial depth | Ricketts 1960/1981 | Po,Or,N,Pog | FH / N-Pog | source-directed angle | ° | — | age/sex/pop | typed source module exists, not active read-path | FH+N-Pog drawn | absent | CALCULATED BUT NOT DISPLAYED |
| Convexity A | Ricketts 1981 | A,N,Pog + FH sign | A→N-Pog | signed perpendicular distance × calibration | mm | — | age/pop | typed source module exists, not active read-path | perpendicular drawn | absent | CALCULATED BUT NOT DISPLAYED |
| E-line Ls | Ricketts E-plane lineage | Prn,Pog′,Ls | Prn-Pog′ | V2 signed shortest perpendicular distance | mm | — | population | engine + typed R18 V2, typed not active read-path | soft profile/E-line base | row | NON SOURCE-LOCKED at active UI read authority |
| E-line Li | idem | Prn,Pog′,Li | Prn-Pog′ | V2 signed shortest perpendicular distance | mm | — | population | engine + typed R18 V2, typed not active read-path | soft profile/E-line base | row | NON SOURCE-LOCKED at active UI read authority |
| Facial axis | Ricketts | Ba,N,Pt,constructed Gn | Ba-N / Pt-Gn | source angle; helper exists | ° | — | age/sex | helper exists but evidence contract BLOCKED | absent | absent | IMPOSSIBLE WITH CURRENT LANDMARKS |
| Mandibular plane/FH | Ricketts variant-specific | source FH + source mandibular plane | FH/MP | exact variant required | ° | — | age/sex | generic FMA cannot be silently reused | generic planes | absent | NON SOURCE-LOCKED |
| Lower facial height | Ricketts | ANS,Xi,Pm | ANS-Xi-Pm | source angle | ° | — | age/sex/pop | absent | absent | absent | IMPOSSIBLE WITH CURRENT LANDMARKS |
| Maxillary depth | Ricketts | Po,Or,N,A | FH / N-A | source-directed angle | ° | — | age/pop | absent | geometry possible | absent | MISSING |
| Mandibular arc | Ricketts | variant-specific incl. Xi/Pm/DC | source-specific | exact primary definition required | ° | — | age/sex | absent | absent | absent | IMPOSSIBLE WITH CURRENT LANDMARKS |
| Corpus length | Ricketts | variant-specific | source-specific | exact primary definition must be locked; no Xi/Pm↔Go/Gn substitution | mm | — | age/sex | absent | absent | absent | NON SOURCE-LOCKED |
| L1→A-Pog distance | Ricketts | L1,A,Pog | A-Pog | perpendicular distance | mm | — | population | absent | geometry possible | absent | MISSING |
| L1/A-Pog inclination | Ricketts | L1 axis,A,Pog | L1 / A-Pog | angle | ° | — | population | absent | geometry possible | absent | MISSING |
| Overjet | Ricketts family | U1,L1 + source convention | source-specific | exact Ricketts definition required | mm | — | age/pop | generic FH-projected `Surplomb` exists | generic | absent Ricketts | NON SOURCE-LOCKED |
| Overbite | Ricketts family | U1,L1 + source convention | source-specific | exact Ricketts definition required | mm | — | age/pop | generic FH-projected `Recouvrement` exists | generic | absent Ricketts | NON SOURCE-LOCKED |
| U6→PTV | Ricketts | U6 + PTV construction | PTV | source linear definition | mm | — | age/sex | U6/Ptm exist in 38; PTV method absent | absent | absent | MISSING |
| Internal structures | Ricketts comprehensive | Xi/Pm/CF/DC/etc. | source-specific | multiple | °/mm | — | age/sex/pop | absent | absent | absent | IMPOSSIBLE WITH CURRENT LANDMARKS |

### 5.5 COM

| MEASURE/PACKAGE | SOURCE | CURRENT BACKEND | TRACING/UI | STATUS |
|---|---|---|---|---|
| COM package | mixed internal ledger | mixed CRANIOM/Tweed/other geometry | 10 rows R19 | PROTOCOLE INTERNE NON SOURCE-LOCKED |
| Surplomb / Recouvrement | internal FH-projected convention | raw engine | rows + tracing | NON SOURCE-LOCKED as universal COM norms |
| IMPA | DC geometry + Tweed lineage | raw/typed | row + normative wedge | geometry exists; norm binding NON SOURCE-LOCKED |
| U1/FH | DC geometry + Eastman/Ballard lineage debt | raw CRANIOM | row + normative wedge | NON SOURCE-LOCKED |
| Interincisal | multiple historical lineages | raw CRANIOM | row | NON SOURCE-LOCKED for universal norm |
| FMA | DC Po-Or/Go-Me | engine | row | NON SOURCE-LOCKED for historical Ricketts/Tweed norms |
| A'B', A/Nvert, B/Nvert | CRANIOM lineage | versioned constructions | rows | geometry COMPLETE; norms remain gated |
| `Profondeur_Faciale` COM | CRANIOM S→N-vertical magnitude | versioned construction | row | COMPLETE for its CRANIOM method; **not** Ricketts facial-depth angle |

### 5.6 Toutes analyses

R19 `all` contient seulement 15 clés statiques. Il n'inclut notamment pas `SN_MP`, `U1_NA`, `L1_NB`, `FMIA`, ni les familles McNamara/Ricketts source-spécifiques avancées.

**Statut : `MISSING` comme véritable union scientifique.**

La cible est une union générée depuis un registre de mesures source-versionné, avec lignes `NC` explicites quand un metric est non calculable.

---

## 6. Audit frontend / tracing

### P0 confirmé — fuite normative frontend

`CephaloTracingLayerBase.tsx` contient encore des constantes cliniques codées en dur :

- `IMPA_MEAN = 90`
- `IMPA_NORM_HALF = 5`
- `IMPA_COMP_HALF = 10`
- `IF_MEAN = 107`
- `IF_NORM_HALF = 5`
- `IF_COMP_LOW = 97`
- `IF_COMP_HIGH = 120`

Elles alimentent directement des `WedgeZone` pendant l'édition des incisives.

Ceci contredit l'architecture backend actuelle qui neutralise toute autorité normative, et le ledger COM qui indique que plusieurs de ces références ne sont pas universellement source-lockées pour la géométrie effectivement utilisée.

**Statut : P0 — autorité clinique frontend non autorisée.**

Correction future après HUMAN GATE : le tracing peut visualiser une construction, mais une zone normative ne doit exister que si le backend fournit un profil normatif versionné, applicable et explicitement validé. Sinon : aucune zone clinique.

### Ricketts R19

Le wrapper R19 mappe `ricketts → esthetique` pour la base et ajoute des constructions dures `FH`, `N-Pog` et `A→N-Pog`. Le tracing connaît donc déjà plus de Ricketts que le tableau, lequel n'affiche que les deux distances E-line.

=> `TRACED BUT NOT MEASURED/DISPLAYED` existe réellement au niveau produit pour facial depth/convexity.

### McNamara R19

Le tracing montre Co-A, Co-Gn, ANS-Me et N-perp ; le tableau affiche les trois longueurs mais le payload runtime actif ne les fournit pas.

=> preuve directe d'un problème de composition/read-path plus que de géométrie.

---

## 7. Architecture normative cible : déjà largement présente

Ne pas reconstruire un deuxième système.

La couche existante `cephalo_normative_registry.py` + `cephalo_normative_service.py` possède déjà les propriétés recherchées :

- `measurement_id`
- `definition_version`
- profils versionnés
- population explicite
- âge min/max et dépendance d'âge
- sexe explicite/pooled
- mean / SD / range / value selon type
- validation/quarantine
- aucune sélection silencieuse en cas d'ambiguïté
- aucune classification sans `ClassificationRule` validée.

**Architecture recommandée :**

`source landmarks → source-specific geometry → MeasurementEvidence(analysis_id, method_id, version) → optional NormativeEvaluation(versioned context) → active typed read-path → UI/tracing`.

Aucune formule clinique dans le frontend. Aucune norme dans `cephalo_engine.py`.

---

## 8. P0 / P1

### P0

1. **Neutraliser la fuite normative frontend** IMPA/U1-FH tant qu'aucun profil backend validé/applicable n'est fourni.
2. **Rendre les noms d'analyses honnêtes** : soit listes complètes source-lockées, soit libellé explicite « subset » temporaire. Un onglet `Ricketts` avec seulement E-line ne peut être présenté comme analyse complète.
3. **Transformer `Toutes analyses` en vraie union** issue d'un registre, pas une liste statique de 15 clés.
4. **Étendre le typed read-path** avant que l'UI revendique une mesure source-spécifique.
5. **Interdire la réutilisation silencieuse d'une géométrie sous une autre analyse** : un FMA générique n'est ni Tweed 1954 ni Ricketts 1981 sans construction/version correspondante.

### P1

1. Composer McNamara R8 Co-A/Co-Gn/ANS-Me dans evidence graph + rebuild + read-path + UI.
2. Exposer Steiner typed `SN_MP`, `U1_NA angle`, `L1_NB angle` dans Workbench/tracing.
3. Exposer Tweed `FMIA` et ajouter invariant géométrique du triangle sous convention versionnée.
4. Composer Ricketts source-aware facial depth, convexity et E-line V2 dans evidence graph/read-path ; rendre l'UI provenance-bound.
5. Implémenter ensuite seulement les mesures réellement absentes, en petits lots source-lockés.
6. Ouvrir un chantier landmarks source-exacts `Pt`, `Xi`, `Pm`, `CF/DC` si l'objectif est un Ricketts complet.

---

## 9. Inventaire de clôture audit

### Mesures déjà correctes / exploitables sans réécriture du moteur

- SNA, SNB, ANB ;
- Steiner SN-GoGn typed ;
- Steiner U1-NA angle typed ;
- Steiner L1-NB angle typed ;
- IMPA/FMA géométriques Digital Crown ;
- FMIA typed ;
- interincisal ;
- CRANIOM A'B', A/Nvert, B/Nvert, profondeur faciale interne ;
- Ricketts facial depth/convexity/E-line dans modules source-aware, sous réserve de les brancher au runtime autoritatif ;
- McNamara Co-A/Co-Gn/ANS-Me dans module source-aware, sous réserve de les brancher.

### Mesures immédiatement calculables avec landmarks existants après source-lock exact

- Steiner U1-NA mm, L1-NB mm, Pog/NB, SND sur SRPose38 ;
- McNamara Pog-Nperp, différence Co-Gn−Co-A, mandibular plane angle, U1→A vertical, L1→A-Pog, nasolabial sur SRPose38 ;
- Ricketts maxillary depth, L1/APog angle+distance, plusieurs mesures dentaires simples ;
- U6/PTV uniquement après verrouillage exact de la construction PTV.

### Nouveaux landmarks/conventions requis

- `Pt` exact source-specific : le `PT_point` actuel reste insuffisant pour certification automatique ;
- `Xi` ;
- `Pm` ;
- `CF/DC` et autres points internes selon la variante Ricketts choisie ;
- convention Gonion/plan mandibulaire par analyse ;
- convention Porion/Frankfort par analyse ;
- définition source-lockée du plan occlusal pour Steiner/Wits.

---

## 10. Lots d'implémentation recommandés APRÈS HUMAN GATE

### Lot A — Safety frontend

Retirer/quarantiner les wedges normatifs codés en dur. Aucun changement de géométrie patient.

### Lot B — Registry/UI truth

Créer le registre source-versionné des mesures exposables et générer `Steiner/Tweed/McNamara/Ricketts/Toutes` depuis ce registre. Valeur absente = `NC` + raison structurée.

### Lot C — Typed read authority

Étendre evidence graph/rebuild/read-path aux mesures typed déjà existantes : Steiner avancé, Tweed FMIA, McNamara R8, Ricketts R18.

### Lot D — Gaps géométriques simples

Ajouter les métriques calculables avec les landmarks déjà validés, une analyse/méthode à la fois, avec golden geometry tests.

### Lot E — Landmark expansion

Seulement si Ricketts complet est retenu : Pt/Xi/Pm/CF/DC avec contrat anatomique, provenance, correction manuelle et fail-closed.

### Lot F — Norms

Brancher `cephalo_normative_service` uniquement sur des profils source-lockés et applicables. Jamais de fallback silencieux.

Pour chaque lot UI : BEFORE mêmes viewports → Goal → référence/mockup → implémentation → AFTER mêmes viewports → comparaison → tests → score visuel.

---

## 11. HUMAN GATE — obligatoire

Aucune modification de formule, norme ou interprétation clinique ne doit être introduite avant validation humaine des décisions suivantes :

1. **Architecture** : typed evidence/read-path comme autorité, UI générée depuis registre source-versionné.
2. **Tweed** : décider si l'onglet doit reproduire le Tweed historique exact ou exposer une variante Digital Crown anatomique explicitement nommée/versionnée.
3. **Ricketts** : décider cible exhaustive historique vs subset clinique source-locké ; ces objectifs n'ont pas le même coût en landmarks.
4. **COM** : accepter son statut de protocole interne composite non source-locké au niveau du paquet, avec source-lock individuel par métrique.

Avant ce gate, seule documentation/audit est autorisée.

---

## 12. Références scientifiques verrouillées

### Steiner

- Steiner CC. *Cephalometrics for you and me*. Am J Orthod. 1953;39(10):729-755. DOI `10.1016/0002-9416(53)90082-7`.
- Steiner CC. *Cephalometrics in Clinical Practice*. Angle Orthod. 1959;29:8-29.
- Corroboration contemporaine : études peer-reviewed utilisant les définitions U1-NA/L1-NB et montrant des différences populationnelles ; aucune norme universelle n'est activée par cet audit.

### Tweed / Merrifield

- Tweed CH. *The Frankfort-mandibular incisor angle (FMIA) in orthodontic diagnosis, treatment planning and prognosis*. Angle Orthod. 1954;24:121-169.
- Tweed CH. *The diagnostic facial triangle in the control of treatment objectives*. Am J Orthod. 1969;55(6):651-667. DOI `10.1016/0002-9416(69)90041-4`.
- Iwasawa T, Moro T, Nakamura K. *Tweed triangle and soft-tissue consideration of Japanese with normal occlusion and good facial profile*. Am J Orthod. 1977;72(2):119-127. DOI `10.1016/0002-9416(77)90054-9`.
- Merrifield LL. *The profile line as an aid in critically evaluating facial esthetics*. Am J Orthod. 1966;52(11):804-822. DOI `10.1016/0002-9416(66)90250-8`.

### McNamara

- McNamara JA Jr. *A method of cephalometric evaluation*. Am J Orthod. 1984;86(6):449-469. DOI `10.1016/S0002-9416(84)90352-X`.
- Storniolo-Souza JM et al. *McNamara analysis cephalometric parameters in White-Brazilians, Japanese and Japanese-Brazilians with normal occlusion*. Dental Press J Orthod. 2021;26(1):e2119133. DOI `10.1590/2177-6709.26.1.e2119133.oar`, PMCID `PMC8018756`.

### Ricketts

- Ricketts RM. *A foundation for cephalometric communication*. Am J Orthod. 1960;46(5):330-357. DOI `10.1016/0002-9416(60)90047-6`.
- Ricketts RM. *Perspectives in the clinical application of cephalometrics. The first fifty years*. Angle Orthod. 1981;51(2):115-150. DOI `10.1043/0003-3219(1981)051<0115:PITCAO>2.0.CO;2`.
- Bae EJ, Kwon HJ, Kwon OW. *Changes in longitudinal craniofacial growth in subjects with normal occlusions using the Ricketts analysis*. Korean J Orthod. 2014;44(2):77-87. DOI `10.4041/kjod.2014.44.2.77`, PMCID `PMC3971129`.

### Wits, utilisé uniquement comme contrôle de convention

- Jacobson A. *The Wits appraisal of jaw disharmony*. Am J Orthod. 1975;67(2):125-138. DOI `10.1016/0002-9416(75)90065-2`. La méthode projette A et B sur le plan occlusal ; aucune substitution par le plan mandibulaire n'est autorisée.

---

## 13. Décision finale de l'audit

**Diagnostic d'architecture :** le défaut principal de complétude R19 est **exposition/composition/read-path/UI**, pas une absence générale du backend.

**Mais** plusieurs métriques restent réellement absentes et plusieurs conventions historiques restent bloquées scientifiquement. Les traiter comme de simples problèmes d'affichage serait aussi faux que d'accuser tout le backend.

**État : AUDIT DOCUMENTAIRE SOURCE-LOCKED. IMPLÉMENTATION SCIENTIFIQUE BLOQUÉE PAR HUMAN GATE.**
