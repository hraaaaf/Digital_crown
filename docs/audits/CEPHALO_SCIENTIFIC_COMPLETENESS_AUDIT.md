# CEPHALO SCIENTIFIC COMPLETENESS AUDIT — Céphalo-N

**Statut :** AUDIT SOURCE-LOCKED — HUMAN GATE REQUIS AVANT MODIFICATION SCIENTIFIQUE  
**Baseline auditée :** `master@0097e3a08340f753803a86d2a1134880ad9ce902`  
**Périmètre :** Steiner, Tweed, McNamara, Ricketts, COM, Toutes analyses ; backend géométrique, evidence graph, read-path, tracing et Workbench R19.  
**Nature de ce lot :** documentation/audit uniquement. Aucune formule, norme, interprétation clinique, DB, patient, document ou UI n'est modifié par ce commit.

---

## 0. Goal / Success / Proof

### Goal

Établir avant toute implémentation une spécification de complétude céphalométrique source-lockée distinguant : calcul correct, backend non exposé, trace sans mesure, UI sans calcul, vrai manque backend, impossibilité liée aux landmarks, et norme/interprétation non validée.

### Success observable

- matrice `MEASURE → SOURCE → LANDMARKS → FORMULE → BACKEND → TRACING → UI → STATUS` ;
- source primaire + ≥1 source scientifique indépendante sérieuse par analyse canonique lorsque disponible ;
- variantes historiques/Digital Crown non fusionnées ;
- normes non validées non autoritatives ;
- P0/P1 + lots post-gate ;
- aucun changement clinique avant HUMAN GATE.

### Proof repo

Baseline lue : `CEPHALO_R19_ANALYSIS_REFERENCE_LAYOUT.md`, `CEPHALO_DIAGNOSTIC_SPEC.md`, `SRPOSE38_LANDMARK_CONTRACT.md`, moteur/safe-engine/service, constructions, runtime evidence/chain/read-path, correction landmarks, adapters Steiner/Tweed/McNamara/Ricketts/COM/normatifs, tracing R19 + base, Workbench, tests runtime evidence et normative service.

---

## 1. Conclusion exécutive

### Diagnostic vérifié

Le problème principal **n'est pas un backend géométrique vide ou globalement défaillant**.

Digital Crown possède déjà : moteur brut fail-closed, constructions versionnées, evidence graph typé, adapters source-spécifiques, registre normatif séparé, contrat SRPose38 et tests de parité/persistance.

La perte dominante se situe dans la continuité :

`landmarks → geometry/evidence source-spécifique → evidence graph → read-path autoritatif → UI/tracing`.

Constats :

- plusieurs mesures existent dans des modules backend mais ne sont pas composées dans l'evidence graph actif ;
- le typed read-path ne projette autoritativement que quatre mesures linéaires CRANIOM ;
- le Workbench R19 utilise des listes statiques réduites ;
- `Toutes analyses` n'est pas une union réelle ;
- le tracing contient encore des normes frontend codées en dur malgré la neutralisation normative backend.

**Priorité :** ne pas réécrire `cephalo_engine.py`. Raccorder typed evidence → read-path → UI, puis compléter seulement les vrais gaps géométriques.

---

## 2. Source lock et variantes

### Steiner

**Primaire**
- Steiner CC. *Cephalometrics for you and me*. Am J Orthod. 1953;39(10):729-755. DOI `10.1016/0002-9416(53)90082-7`.
- Steiner CC. *Cephalometrics in Clinical Practice*. Angle Orthod. 1959;29:8-29.

**Indépendantes**
- Siangloy T, Charoemratrote C. *Incisor and Soft Tissue Characteristics of Adult Bimaxillary Protrusion Patients among Different Skeletal Anteroposterior Classifications*. Diagnostics. 2024;14(10):1031. DOI `10.3390/diagnostics14101031`, PMCID `PMC11119585` : définitions U1-NA/L1-NB angle et distance.
- Uysal T et al. *Ethnic differences in dentofacial relationships of Turkish and Saudi young adults with normal occlusions and well-balanced faces*. Saudi Dent J. 2011;23(4):183-190. DOI `10.1016/j.sdentj.2011.08.002`, PMCID `PMC3723299` : confirme la dépendance populationnelle des références céphalométriques.

**Version** : la couche typed Digital Crown retient `SN` vs `Go-Gn` pour `STEINER_SN_MP_DEG_V1`. `Go-Me` est une autre convention et exige un autre `method_id`.

### Tweed pur vs Merrifield

**Primaires**
- Tweed CH. *The Frankfort-mandibular incisor angle (FMIA) in orthodontic diagnosis, treatment planning and prognosis*. Angle Orthod. 1954;24:121-169.
- Tweed CH. *The diagnostic facial triangle in the control of treatment objectives*. Am J Orthod. 1969;55(6):651-667. DOI `10.1016/0002-9416(69)90041-4`.

**Indépendante**
- Iwasawa T, Moro T, Nakamura K. *Tweed triangle and soft-tissue consideration of Japanese with normal occlusion and good facial profile*. Am J Orthod. 1977;72(2):119-127. DOI `10.1016/0002-9416(77)90054-9`.

**Variante** : FMA/IMPA/FMIA = Tweed. Z-angle = Merrifield, déjà séparé par `analysis_id=MERRIFIELD`.

**Gate historique** : le Frankfort et le plan mandibulaire du tracing historique Tweed ne peuvent pas être assimilés silencieusement au couple automatique `Po-Or`/`Go-Me`. Les mesures DC actuelles sont une géométrie versionnée utile ; les normes historiques ne sont pas transférables sans contrat exact de construction.

### McNamara

**Primaire**
- McNamara JA Jr. *A method of cephalometric evaluation*. Am J Orthod. 1984;86(6):449-469. DOI `10.1016/S0002-9416(84)90352-X`.

**Indépendante**
- Storniolo-Souza JM et al. *McNamara analysis cephalometric parameters in White-Brazilians, Japanese and Japanese-Brazilians with normal occlusion*. Dental Press J Orthod. 2021;26(1):e2119133. DOI `10.1590/2177-6709.26.1.e2119133.oar`, PMCID `PMC8018756`.

Cette étude confirme A-Nperp, Co-A, Co-Gn, différence maxillo-mandibulaire, ANS-Me, plan mandibulaire, axe facial Ba-N/Pt-Gn, Pog-Nperp, incisives et nasolabial, et démontre des effets sexe/population sur plusieurs références.

### Ricketts

**Primaires**
- Ricketts RM. *A foundation for cephalometric communication*. Am J Orthod. 1960;46(5):330-357. DOI `10.1016/0002-9416(60)90047-6`.
- Ricketts RM. *Perspectives in the clinical application of cephalometrics. The first fifty years*. Angle Orthod. 1981;51(2):115-150. DOI `10.1043/0003-3219(1981)051<0115:PITCAO>2.0.CO;2`.

**Indépendante**
- Bae EJ, Kwon HJ, Kwon OW. *Changes in longitudinal craniofacial growth in subjects with normal occlusions using the Ricketts analysis*. Korean J Orthod. 2014;44(2):77-87. DOI `10.4041/kjod.2014.44.2.77`, PMCID `PMC3971129`.

Cette étude confirme les familles dentaire, dentosquelettique, squelettique, mâchoires/crâne et structures internes, et démontre une dépendance âge/sexe pour plusieurs mesures. Ricketts ne peut donc pas être réduit à l'E-line.

### COM

Aucune source primaire unique ne définit le paquet `COM` R19 comme analyse universelle. `cephalo_com_evidence_ledger.py` documente un assemblage Tweed, Downs, Steiner, Ricketts, CRANIOM et Ballard/Eastman, avec plusieurs dettes de source.

**Package status : `PROTOCOLE INTERNE NON SOURCE-LOCKED`.** Les mesures individuelles peuvent être source-lockées séparément ; aucune norme universelle ne s'hérite du nom COM.

---

## 3. Landmarks réellement exploitables

### Contrat 19 points

`S,N,Po,Or,Ar,Co,Ba,ANS,PNS,A,B,Pog,Gn,Me,Go,U1i,U1R,L1i,L1R`.

Il couvre une grande partie de Steiner/Tweed/McNamara et certains éléments Ricketts, mais pas les tissus mous E-line/nasolabial ni `Pt`, `Xi`, `Pm`, `CF/DC`.

### SRPose38

Ordre/noms certifiés :

`S,N,Or,Po,A,B,Pog,Me,Gn,Go,L1_incisal,U1_incisal,Ls_soft,Li_soft,Sn_soft,Pog_soft,PNS,ANS,Ar,D_point,U1_apex,L1_apex,Cm,Ptm,Co,Prn,Ba,PT_point,Bo,Ls2,Li2,Gn_soft,Me_soft,G_soft,N_soft,C_point,U6,L6`.

**Gates restants** :
- `Go` : anatomique vs construit ;
- `Po` : anatomique vs machine/ear-rod ;
- `PT_point` : le nom dataset ne certifie pas le `Pt` exact Ricketts/McNamara ;
- `Xi`, `Pm`, `CF/DC` : absents.

Présence d'un landmark homonyme ≠ autorisation de substitution historique.

---

## 4. Architecture actuelle : ce qui fonctionne et où elle casse

### Sain

- `cephalo_engine.py` : géométrie brute seulement.
- `cephalo_safe_engine.py` : neutralise normes/status/interprétations legacy.
- `cephalo_normative_service.py` : couche séparée, versionnée, age/sex/population aware, fail-closed.
- evidence adapters : `analysis_id`, `method_id`, version et constructions explicites.

### Ruptures

1. `build_cephalo_runtime_evidence_payload()` compose CRANIOM + Steiner ; Tweed/Merrifield/Downs arrivent indirectement via Steiner, mais McNamara/Ricketts ne sont pas composés.
2. Le rebuild après correction landmark reproduit cette limitation.
3. `cephalo_typed_read.py` rend autoritatives uniquement quatre mesures CRANIOM linéaires.
4. McNamara/Ricketts ont des modules source-spécifiques partiellement prêts mais restent orphelins du read-path actif.
5. R19 utilise une liste UI statique, pas un registre scientifique générateur.

---

## 5. Matrice de complétude

`—` = aucune norme autoritative activée par cet audit.

### Steiner

| MEASURE | SOURCE | LANDMARKS | PLAN/LINE | FORMULA | UNIT | NORM | DEPENDENCE | BACKEND | TRACING | UI | STATUS |
|---|---|---|---|---|---|---|---|---|---|---|---|
| SNA | Steiner 1953 | S,N,A | SN/NA | angle(SN,NA) | ° | — | pop | engine+typed | SN+NA | row | COMPLETE |
| SNB | Steiner 1953 | S,N,B | SN/NB | angle(SN,NB) | ° | — | pop | engine+typed | SN+NB | row | COMPLETE |
| ANB | Steiner 1953 | S,N,A,B | NA/NB | SNA−SNB, parity checked | ° | — | geometry/age/pop | engine+typed | NA+NB | row | COMPLETE |
| SN-GoGn | Steiner 1953/1959, DC V1 | S,N,Go,Gn | SN/GoGn | angle axes | ° | — | age/pop | `STEINER_SN_MP_DEG_V1` | not in Steiner focus | absent | CALCULATED BUT NOT DISPLAYED |
| U1-NA angle | Steiner | U1 apex/tip,N,A | U1/NA | angle axes | ° | — | pop | typed | omitted in Steiner focus | absent | CALCULATED BUT NOT DISPLAYED |
| U1-NA distance | Steiner | U1 tip,N,A | point→NA | perpendicular distance; sign versioned | mm | — | pop | absent | absent | absent | MISSING |
| L1-NB angle | Steiner | L1 apex/tip,N,B | L1/NB | angle axes | ° | — | pop | typed | omitted in Steiner focus | absent | CALCULATED BUT NOT DISPLAYED |
| L1-NB distance | Steiner | L1 tip,N,B | point→NB | perpendicular distance; sign versioned | mm | — | pop | absent | absent | absent | MISSING |
| Interincisal | Steiner extended | U1,L1 axes | U1/L1 | angle axes | ° | — | pop | engine/CRANIOM | visible globally | absent Steiner | CALCULATED BUT NOT DISPLAYED |
| Occlusal/SN | Steiner | SN + exact occlusal points | SN/OP | exact OP source required | ° | — | age/dentition | absent | orphan Occ logic | absent | IMPOSSIBLE WITH CURRENT LANDMARKS |
| SND | Steiner extended | S,N,D | SN/ND | exact source angle | ° | — | source | D exists in 38; method absent | absent | absent | MISSING |
| Pog/NB | Steiner extended | Pog,N,B | Pog→NB | perpendicular distance | mm | — | pop | absent | absent | absent | MISSING |

### Tweed pur

| MEASURE | SOURCE | LANDMARKS | PLAN/LINE | FORMULA | UNIT | NORM | DEPENDENCE | BACKEND | TRACING | UI | STATUS |
|---|---|---|---|---|---|---|---|---|---|---|---|
| FMA | Tweed 1954/1969 | historical FH+MP | FH/MP | angle | ° | historical only | pop | DC Po-Or/Go-Me engine+typed | yes | row | NON SOURCE-LOCKED for exact historical Tweed |
| IMPA | Tweed 1954 | L1+historical MP | L1/MP | angle | ° | historical only | pop | DC Go-Me engine+typed | yes | row | NON SOURCE-LOCKED for exact historical Tweed |
| FMIA | Tweed 1954 | L1+FH | L1/FH | angle | ° | historical only | pop | typed `TWEED_FMIA_DEG_V1` | geometry visible | absent | CALCULATED BUT NOT DISPLAYED |
| Triangle invariant | Tweed | same 3 axes | FH/MP/L1 | FMA+IMPA+FMIA=180 only under one coherent internal-angle convention | ° | n/a | n/a | invariant test not certified here | n/a | n/a | MISSING |
| Z-angle | Merrifield 1966 | soft Pog/lip/FH | profile/FH | separate method | ° | — | pop | `analysis_id=MERRIFIELD` | absent | absent | COMPLETE AS SEPARATE VARIANT |

### McNamara

| MEASURE | SOURCE | LANDMARKS | PLAN/LINE | FORMULA | UNIT | NORM | DEPENDENCE | BACKEND | TRACING | UI | STATUS |
|---|---|---|---|---|---|---|---|---|---|---|---|
| A→N-perp | McNamara 1984 | A,N,Po,Or | N-perp ⟂ FH | signed AP distance | mm | — | age/sex/pop | CRANIOM analogue only, no McNamara ID | drawn | absent McN | NON SOURCE-LOCKED |
| Pog→N-perp | McNamara 1984 | Pog,N,Po,Or | N-perp | signed AP distance | mm | — | age/sex/pop | absent | N-perp available | absent | MISSING |
| Co-A | McNamara 1984 | Co,A | segment | Euclidean × verified mm/px | mm | — | age/sex/pop | R8 source module exists, not active graph/read | line | row NC | DISPLAYED BUT NOT CALCULATED |
| Co-Gn | McNamara 1984 | Co,Gn | segment | Euclidean × verified mm/px | mm | — | age/sex/pop | R8 source module exists, not active graph/read | line | row NC | DISPLAYED BUT NOT CALCULATED |
| Difference | McNamara 1984 | Co,A,Gn | lengths | Co-Gn−Co-A | mm | — | age/sex/pop | absent | absent | absent | MISSING |
| ANS-Me | McNamara 1984 | ANS,Me | segment | Euclidean × verified mm/px | mm | — | age/sex/pop | R8 source module exists, not active graph/read | line | row NC | DISPLAYED BUT NOT CALCULATED |
| Mandibular plane angle | McNamara | Po,Or,Go,Me | FH/Go-Me | angle | ° | — | pop | generic FMA only; no McN ID | planes | absent | MISSING |
| Facial axis | McNamara | Ba,N,Pt,Gn | Ba-N/Pt-Gn | exact source angle | ° | — | age/sex/pop | absent | absent | absent | IMPOSSIBLE WITH CURRENT LANDMARKS |
| U1→A vertical | McNamara | U1,A,FH | A-vertical | signed linear | mm | — | pop | absent | absent | absent | MISSING |
| L1→A-Pog | McNamara | L1,A,Pog | A-Pog | perpendicular distance | mm | — | pop | absent | absent | absent | MISSING |
| Nasolabial | McNamara | Prn,Sn,Ls | Prn-Sn/Sn-Ls | angle at Sn | ° | — | age/sex/pop | 38 landmarks present; method absent | profile only | absent | MISSING |

`PT_point` reste un hard gate pour l'axe facial : aucune aliasation automatique vers `Pt` source-specific.

### Ricketts

| MEASURE | SOURCE | LANDMARKS | PLAN/LINE | FORMULA | UNIT | NORM | DEPENDENCE | BACKEND | TRACING | UI | STATUS |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Facial depth | Ricketts 1960/1981 | Po,Or,N,Pog | FH/N-Pog | source-directed angle | ° | — | age/sex/pop | typed module, not active read | FH+N-Pog drawn | absent | CALCULATED BUT NOT DISPLAYED |
| Convexity A | Ricketts 1981 | A,N,Pog+FH sign | A→N-Pog | signed perpendicular × calibration | mm | — | age/pop | typed module, not active read | perpendicular drawn | absent | CALCULATED BUT NOT DISPLAYED |
| E-line Ls | Ricketts E-plane lineage | Prn,Pog′,Ls | Prn-Pog′ | V2 shortest perpendicular signed | mm | — | pop | engine + typed R18 V2; typed not active read | soft/E-line | row | NON SOURCE-LOCKED at active UI authority |
| E-line Li | idem | Prn,Pog′,Li | Prn-Pog′ | V2 shortest perpendicular signed | mm | — | pop | engine + typed R18 V2; typed not active read | soft/E-line | row | NON SOURCE-LOCKED at active UI authority |
| Facial axis | Ricketts | Ba,N,Pt,constructed Gn | Ba-N/Pt-Gn | helper source angle | ° | — | age/sex | helper exists, evidence explicitly BLOCKED | absent | absent | IMPOSSIBLE WITH CURRENT LANDMARKS |
| Mandibular plane/FH | Ricketts variant-specific | source FH+MP | FH/MP | exact variant required | ° | — | age/sex | generic FMA cannot be relabeled | generic | absent | NON SOURCE-LOCKED |
| Lower facial height | Ricketts | ANS,Xi,Pm | ANS-Xi-Pm | source angle | ° | — | age/sex/pop | absent | absent | absent | IMPOSSIBLE WITH CURRENT LANDMARKS |
| Maxillary depth | Ricketts | Po,Or,N,A | FH/N-A | source-directed angle | ° | — | age/pop | absent | possible | absent | MISSING |
| Mandibular arc | Ricketts | Xi/Pm/DC variant-specific | source-specific | primary exact required | ° | — | age/sex | absent | absent | absent | IMPOSSIBLE WITH CURRENT LANDMARKS |
| Corpus length | Ricketts | variant-specific | source-specific | exact primary definition required; no Xi/Pm↔Go/Gn substitution | mm | — | age/sex | absent | absent | absent | NON SOURCE-LOCKED |
| L1→A-Pog distance | Ricketts | L1,A,Pog | A-Pog | perpendicular | mm | — | pop | absent | possible | absent | MISSING |
| L1/A-Pog inclination | Ricketts | L1 axis,A,Pog | L1/A-Pog | angle | ° | — | pop | absent | possible | absent | MISSING |
| Overjet | Ricketts family | U1,L1+source convention | source-specific | exact definition required | mm | — | age/pop | generic FH `Surplomb` only | generic | absent Rick. | NON SOURCE-LOCKED |
| Overbite | Ricketts family | U1,L1+source convention | source-specific | exact definition required | mm | — | age/pop | generic FH `Recouvrement` only | generic | absent Rick. | NON SOURCE-LOCKED |
| U6→PTV | Ricketts | U6+PTV | PTV | source linear definition | mm | — | age/sex | U6/Ptm exist; PTV method absent | absent | absent | MISSING |
| Internal structures | Ricketts comprehensive | Xi/Pm/CF/DC/etc. | source-specific | multiple | °/mm | — | age/sex/pop | absent | absent | absent | IMPOSSIBLE WITH CURRENT LANDMARKS |

### COM

| PACKAGE/MEASURE | SOURCE | BACKEND | UI/TRACING | STATUS |
|---|---|---|---|---|
| COM package | mixed internal ledger | mixed | 10 rows | PROTOCOLE INTERNE NON SOURCE-LOCKED |
| Surplomb/Recouvrement | internal FH-projected | raw engine | rows+trace | NON SOURCE-LOCKED as universal COM norms |
| IMPA | DC geometry + Tweed lineage | raw/typed | row + hardcoded norm wedge | geometry exists; norm binding NON SOURCE-LOCKED |
| U1/FH | DC geometry + Eastman/Ballard debt | raw CRANIOM | row + hardcoded norm wedge | NON SOURCE-LOCKED |
| Interincisal | multiple lineages | raw CRANIOM | row | NON SOURCE-LOCKED for universal norm |
| FMA | DC Po-Or/Go-Me | engine | row | NON SOURCE-LOCKED for historical Tweed/Ricketts norms |
| A'B', A/Nvert, B/Nvert | CRANIOM | versioned | rows | geometry COMPLETE; norms gated |
| `Profondeur_Faciale` COM | CRANIOM S→N-vertical magnitude | versioned | row | COMPLETE pour CRANIOM ; **pas** le facial-depth angle Ricketts |

### Toutes analyses

R19 `all` est une liste statique de 15 clés et exclut notamment `SN_MP`, `U1_NA`, `L1_NB`, `FMIA` et les familles avancées McNamara/Ricketts.

**STATUS : MISSING comme union scientifique réelle.**

---

## 6. Frontend/tracing : P0 confirmé

### Fuite normative frontend

`CephaloTracingLayerBase.tsx` contient encore :

- `IMPA_MEAN = 90`
- `IMPA_NORM_HALF = 5`
- `IMPA_COMP_HALF = 10`
- `IF_MEAN = 107`
- `IF_NORM_HALF = 5`
- `IF_COMP_LOW = 97`
- `IF_COMP_HIGH = 120`

Ces valeurs alimentent directement des `WedgeZone` pendant l'édition. Le backend, lui, neutralise les normes ; le ledger COM refuse précisément plusieurs de ces références comme normes universelles pour les constructions actuelles.

**P0 : autorité clinique frontend non autorisée.**

Cible post-gate : construction SVG autorisée ; zone normative seulement si un profil backend versionné, applicable et validé est fourni. Sinon aucune zone clinique.

### Ricketts R19

Le wrapper mappe `ricketts → esthetique` pour la base et ajoute `FH`, `N-Pog`, `A→N-Pog`. Le tracing connaît donc facial depth/convexity alors que le tableau `Ricketts` ne montre que E-line Ls/Li.

=> gap prouvé tracing/backend-module → UI.

### McNamara R19

Le tracing montre Co-A, Co-Gn, ANS-Me et N-perp ; le tableau montre les trois longueurs en `NC`; les modules R8 existent mais ne sont pas composés dans le graph/read-path actif.

=> gap prouvé **composition/read-path**, pas absence de géométrie.

---

## 7. Normative architecture

Ne pas créer un second système.

`cephalo_normative_registry.py` + `cephalo_normative_service.py` gèrent déjà : measurement/version, population, âge, sexe, mean/SD/range/value, validation/quarantine, ambiguïté fail-closed et règle de classification explicite.

Architecture cible :

`source landmarks → source-specific geometry → MeasurementEvidence(analysis_id, method_id, version) → optional NormativeEvaluation(context/version) → active typed read-path → UI/tracing`.

Aucune formule clinique dans le frontend ; aucune norme dans `cephalo_engine.py`.

---

## 8. Priorités

### P0

1. Neutraliser/quarantiner les wedges normatifs frontend IMPA/U1-FH.
2. Rendre les noms d'analyses honnêtes : analyse complète source-lockée ou `subset` explicite temporaire.
3. Transformer `Toutes analyses` en vraie union générée par registre.
4. Étendre le typed read-path avant toute revendication UI source-spécifique.
5. Interdire le relabeling silencieux d'une même géométrie sous Tweed/McNamara/Ricketts.

### P1

1. Composer McNamara R8 Co-A/Co-Gn/ANS-Me dans graph + rebuild + read-path + UI.
2. Exposer Steiner `SN_MP`, `U1_NA angle`, `L1_NB angle`.
3. Exposer Tweed `FMIA` + invariant du triangle sous convention versionnée.
4. Composer Ricketts facial depth/convexity/E-line V2 dans graph/read-path et lier l'UI à cette provenance.
5. Ajouter ensuite les vrais gaps géométriques par petits lots source-lockés.
6. Pt/Xi/Pm/CF/DC seulement si une cible Ricketts complète est retenue.

---

## 9. Clôture scientifique de l'audit

### Correct / déjà exploitable sans réécriture globale

- SNA/SNB/ANB ;
- Steiner SN-GoGn, U1-NA angle, L1-NB angle typed ;
- IMPA/FMA géométriques DC et FMIA typed ;
- interincisal ;
- CRANIOM A'B', A/Nvert, B/Nvert et profondeur interne ;
- modules source-aware McNamara Co-A/Co-Gn/ANS-Me ;
- modules source-aware Ricketts facial depth/convexity/E-line V2.

### Immédiatement calculable avec landmarks actuels après source-lock exact

- Steiner U1-NA mm, L1-NB mm, Pog/NB, SND sur 38 ;
- McNamara Pog-Nperp, différence Co-Gn−Co-A, mandibular plane angle, U1→A vertical, L1→A-Pog, nasolabial sur 38 ;
- Ricketts maxillary depth, L1/APog angle+distance ;
- U6/PTV après verrouillage PTV.

### Nouveaux landmarks/conventions nécessaires

- `Pt` source-specific ;
- `Xi`, `Pm`, `CF/DC` ;
- Gonion/plan mandibulaire par analyse ;
- Porion/Frankfort par analyse ;
- plan occlusal source-locké pour Steiner/Wits.

---

## 10. Lots post-HUMAN-GATE

**A — Frontend safety :** retirer/quarantiner les normes hardcodées, sans toucher à la géométrie patient.  
**B — Registry/UI truth :** générer Steiner/Tweed/McNamara/Ricketts/Toutes depuis un registre source-versionné ; indisponible = `NC` + raison.  
**C — Typed read authority :** brancher les typed measurements déjà existants.  
**D — Geometry gaps :** une métrique source-lockée à la fois + golden tests.  
**E — Landmark expansion :** Pt/Xi/Pm/CF/DC seulement si nécessaire.  
**F — Norms :** activer `cephalo_normative_service` uniquement pour profils validés/applicables.

Tout impact UI : BEFORE mêmes viewports → Goal → référence → implémentation → AFTER mêmes viewports → comparaison/tests → score visuel.

---

## 11. HUMAN GATE — obligatoire

Avant toute modification de formule, norme ou interprétation clinique, validation humaine requise sur :

1. architecture `typed evidence/read-path → UI` comme autorité ;
2. Tweed : reproduction historique exacte vs variante Digital Crown anatomique explicitement nommée/versionnée ;
3. Ricketts : analyse exhaustive historique vs subset clinique source-locké ;
4. COM : protocole interne composite non source-locké au niveau package, source-lock par métrique.

Avant ce gate : documentation/audit seulement.

---

## 12. Références de contrôle additionnelles

- Jacobson A. *The Wits appraisal of jaw disharmony*. Am J Orthod. 1975;67(2):125-138. DOI `10.1016/0002-9416(75)90065-2` : A et B sont projetés sur le plan occlusal ; aucune substitution par le plan mandibulaire.
- Merrifield LL. *The profile line as an aid in critically evaluating facial esthetics*. Am J Orthod. 1966;52(11):804-822. DOI `10.1016/0002-9416(66)90250-8`.

---

## 13. Décision finale audit

**Le défaut dominant R19 est exposition/composition/read-path/UI, pas une absence générale du backend.**

Il existe néanmoins de vrais gaps métriques et des conventions historiques scientifiquement bloquées. Les traiter comme de simples omissions UI serait aussi incorrect que de réécrire tout le moteur.

**État : AUDIT SOURCE-LOCKED. IMPLÉMENTATION SCIENTIFIQUE BLOQUÉE PAR HUMAN GATE.**
