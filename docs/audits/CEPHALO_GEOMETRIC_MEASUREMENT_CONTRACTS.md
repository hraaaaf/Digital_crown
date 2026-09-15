# Céphalo-N — Contrats géométriques exhaustifs des mesures

Statut : **WORKING V1 — SOURCE-LOCKED CARTOGRAPHY — ZÉRO NOUVELLE NORME / ZÉRO INTERPRÉTATION**

Date : 2026-09-15

## Goal / Succès / Preuve

**Goal** — transformer la cartographie clinique validée Steiner / Tweed / McNamara / Ricketts / COM en contrats géométriques non ambigus avant toute nouvelle mesure runtime.

**Succès** — chaque mesure possède : version, incidence, landmarks, construction(s), opération, unité/signe, état Digital Crown et gate explicite. Aucun alias anatomique ou plan voisin n'est substitué silencieusement.

**Preuve** — `CEPHALO_GLOBAL_ANALYSIS_VALIDATION.md`, `CEPHALO_GLOBAL_ANALYSIS_CARTOGRAPHY.md`, `CEPHALO_LANDMARKS_PLANES_SOURCE_LOCK.md`, `CEPHALO_PRIMARY_LANDMARK_CONSTRUCTIONS.md`, `CEPHALO_SRPOSE38_PROVENANCE.md`, puis tests géométriques manuels source-lockés à ajouter dans ce lot.

## Règles fermes

- Landmark ≠ ligne/plan ≠ construction ≠ mesure ≠ norme ≠ interprétation.
- `Gn_anatomic` ≠ `Gn_constructed`.
- `Pt_Ricketts` ≠ `PTM_McNamara`.
- `Pog_hard` ≠ `Pog_soft`.
- `Go-Me`, `Go-Gn` et `Sub.Go.-M` ne sont pas interchangeables.
- `DC_TWEED_ANATOMICAL_FH_VARIANT = Po-Or` est le contrat actif Digital Crown ; le Frankfort ear-rod 1954 reste historique non actif.
- Toute surface coronaire, airway landmark, Xi/Pm ou landmark PA non disponible reste fail-closed.
- SRPose38 fournit un ordre de canaux local legacy, pas une preuve anatomique amont.
- Aucune mesure PA/frontale ne doit être calculée depuis une téléradiographie de profil.

## Matrice de contrats — Steiner

| Mesure | Construction géométrique | Opération | Unité | Gate DC |
|---|---|---|---|---|
| SNA | SN + NA | angle(SN, NA) | ° | disponible |
| SNB | SN + NB | angle(SN, NB) | ° | disponible |
| ANB | NA + NB / SNA-SNB | angle intermaxillaire | ° | disponible |
| U1-NA angle | axe U1 apex→incisal + NA | angle | ° | géométrie disponible; mapping auto à qualifier |
| U1-NA linéaire | surface faciale U1 + NA | distance perpendiculaire signée | mm | `MISSING_CORONAL_SURFACE` |
| L1-NB angle | axe L1 apex→incisal + NB | angle | ° | géométrie disponible; mapping auto à qualifier |
| L1-NB linéaire | surface faciale L1 + NB | distance perpendiculaire signée | mm | `MISSING_CORONAL_SURFACE` |
| Interincisif | axes U1 + L1 | angle supplémentaire clinique | ° | disponible |
| Plan occlusal-SN | plan occlusal source-locké + SN | angle | ° | définition/landmarks occlusaux à verrouiller |
| GoGn-SN | Go-Gn + SN | angle | ° | Gn anatomique requis |
| L1-GoGn | axe L1 + Go-Gn | angle | ° | Gn anatomique requis |
| U6-NA | point molaire U6 source-locké + NA | distance/projection selon source | mm | point molaire à verrouiller |
| L6-NB | point molaire L6 source-locké + NB | distance/projection selon source | mm | point molaire à verrouiller |
| SND (1959) | SN + ND | angle | ° | D source-lock requis |
| Pog-NB (1959) | Pog hard + NB | distance perpendiculaire | mm | hard Pog explicite |
| L1-D line lin. | surface L1 + D-line ⟂ GoGn par D | distance | mm | D + surface coronaire |
| L1-D line ang. | axe L1 + D-line | angle | ° | D + Gn anatomique |

## Matrice de contrats — Tweed Digital Crown

| Mesure | Construction géométrique | Opération | Unité | Gate DC |
|---|---|---|---|---|
| FMA | FH DC Po-Or + plan mandibulaire Tweed/DC | angle | ° | contrat Po-Or sélectionné ; plan mandibulaire doit rester versionné |
| IMPA | axe L1 apex→incisal + plan mandibulaire Tweed/DC | angle | ° | disponible |
| FMIA | axe L1 apex→incisal + FH DC Po-Or | angle | ° | backend existe ; UI Tweed incomplète |

Note : ces mesures sont `DC_TWEED_ANATOMICAL_FH_VARIANT`; ne pas les présenter comme reproduction géométrique stricte de l'ear-rod Frankfort 1954. Les normes historiques Tweed nécessitent un source-lock normatif séparé avant activation.

## Matrice de contrats — McNamara 1984

| Mesure | Construction géométrique | Opération | Unité | Gate DC |
|---|---|---|---|---|
| A→Nperp | FH anatomic Po-Or ; Nperp ⟂ FH par N | distance AP signée A→Nperp | mm | géométrie disponible ; identité auto Po/Or à qualifier |
| SNA | SN + NA | angle | ° | disponible |
| Co-A | Co anatomic + A | longueur segment | mm | Co auto non autoritaire |
| Co-Gn | Co anatomic + Gn anatomic | longueur segment | mm | distinguer Gn anatomic |
| Différentiel maxillo-mandibulaire | Co-Gn − Co-A | différence | mm | dépend des deux longueurs valides |
| ANS-Me | ANS + Me | longueur segment | mm | géométrie disponible |
| Mandibular plane angle | FH Po-Or + Go-Me | angle | ° | géométrie source-lockée |
| Facial axis | Ba-N + PTM→Gn_constructed | angle | ° | PTM et Gn_constructed explicites |
| Pog→Nperp | Pog hard + Nperp | distance AP signée | mm | ne jamais substituer B (`Situation_B`) |
| U1→A vertical | surface faciale U1 + verticale par A // Nperp | distance | mm | `MISSING_CORONAL_SURFACE` |
| L1→A-Pog | surface faciale L1 + A-Pog | distance | mm | `MISSING_CORONAL_SURFACE` |
| Upper pharynx | palais mou postérieur → point le plus proche paroi pharyngée postérieure | distance minimale selon définition 1984 | mm | airway landmarks absents |
| Lower pharynx | jonction langue postérieure/bord mandibulaire inférieur → point le plus proche paroi pharyngée postérieure | distance minimale selon définition 1984 | mm | airway landmarks absents |

## Matrice de contrats — Ricketts 1981 Summary Descriptive

### Profil — 11 facteurs

| Mesure | Construction géométrique | Opération | Unité | Gate DC |
|---|---|---|---|---|
| Facial Axis | Pt_Ricketts-Gn_constructed + Ba-N | angle | ° | Pt_Ricketts auto non prouvé |
| Facial Angle | N-Pog hard + true FH Po-Or | angle | ° | géométrie disponible |
| Mandibular Plane | Sub.Go.-M + true FH | angle | ° | `Sub.Go.-M` absent ; ne pas substituer Go-Me |
| Oral Gnomon | ANS-Xi-Pm | angle | ° | Xi/Pm absents runtime |
| Palatal Plane | ANS-PNS + FH | angle | ° | PNS auto non autoritaire |
| Maxillary Convexity | A → facial plane N-Pog | distance perpendiculaire signée | mm | géométrie disponible |
| Lower incisor→APo | surface/edge L1 selon source + A-Pog | distance | mm | landmark dentaire exact à verrouiller |
| Upper first molar→PTV | distal crown U6 → PTV | distance | mm | PR/PTV + distal crown absents |
| Interincisal angle | axes U1/L1 | angle | ° | disponible |
| Lower lip→E-plane | Li soft → Prn-Pog_soft | distance perpendiculaire signée | mm | soft/hard separation obligatoire |
| Bend of mandible | corpus/condyle reflex construction Ricketts | angle | ° | construction exacte à fixture/source-locker |

### PA/frontale — 12 facteurs

| Mesure | Construction géométrique | Opération | Unité | Gate DC |
|---|---|---|---|---|
| Nasal cavity width | NC-NC | largeur | mm | `BLOCKED_MODALITY_PA` |
| Maxillary relation droite | J droit → frontal facial plane Z-Ag | distance | mm | `BLOCKED_MODALITY_PA` |
| Maxillary relation gauche | J gauche → frontal facial plane Z-Ag | distance | mm | `BLOCKED_MODALITY_PA` |
| Mandibular width | Ag-Ag | largeur | mm | `BLOCKED_MODALITY_PA`; norme en hold |
| Skeletal symmetry | ANS et Po selon source → central sagittal plane | asymétrie | mm/position | `BLOCKED_MODALITY_PA`; sémantique Po à ne pas réinterpréter |
| Intermolar width | B6-B6 | largeur | mm | `BLOCKED_MODALITY_PA` |
| Intercuspid width | B3-B3 | largeur | mm | `BLOCKED_MODALITY_PA` |
| Lower molar→Fronto-Denture Plane D | B6→J-Ag droit | distance | mm | `BLOCKED_MODALITY_PA` |
| Lower molar→Fronto-Denture Plane G | B6→J-Ag gauche | distance | mm | `BLOCKED_MODALITY_PA` |
| Lower incisor midpoint→Frontal A-Po | midpoint incisif → plan frontal A-Po | distance | mm | `BLOCKED_MODALITY_PA` |
| Molar crossbite droit | relation molaire transversale droite | distance/relation | mm | `BLOCKED_MODALITY_PA` |
| Molar crossbite gauche | relation molaire transversale gauche | distance/relation | mm | `BLOCKED_MODALITY_PA` |

## Matrice de contrats — COM_DC_LEGACY_V1

| Mesure | Construction géométrique | Opération | Unité | Gate DC |
|---|---|---|---|---|
| Surplomb | incisives U1/L1 selon convention DC | distance horizontale | mm | provenance exacte à conserver comme DC legacy |
| Recouvrement | incisives U1/L1 selon convention DC | distance verticale | mm/% selon contrat existant | provenance exacte à conserver comme DC legacy |
| IMPA | axe L1 + plan mandibulaire DC | angle | ° | import Tweed/DC |
| I/Frankfort | axe U1 + FH Po-Or | angle | ° | **pas FMIA Tweed** |
| Interincisif | axes U1/L1 | angle | ° | disponible |
| Angle de Tweed / FMA | FH Po-Or + plan mandibulaire DC | angle | ° | import Tweed/DC |
| Décalage A'B' | projections A/B sur FH via parallèles aux Nperp | distance signée | mm | contrat CRANIOM/DC existant |
| Situation A | A→Nperp sur FH Po-Or | distance AP signée | mm | géométrie McNamara-like ; provenance COM/DC |
| Situation B | B→Nperp sur FH Po-Or | distance AP signée | mm | interne DC ; **≠ Pog→Nperp McNamara** |
| Profondeur faciale | S→Nperp sur FH Po-Or | distance absolue | mm | legacy COM/DC ; **≠ Facial Angle Ricketts** |

## Gates avant implémentation de nouvelles mesures

1. Construire des fixtures manuelles indépendantes du détecteur pour chaque primitive déjà source-lockée.
2. Tester orientation, angle supplémentaire, signe AP et calibration mm.
3. Formaliser les IDs distincts `Gn_anatomic`, `Gn_constructed`, `Pt_Ricketts`, `PTM_McNamara`, surfaces coronaires, Xi/Pm et airway.
4. Maintenir toutes les mesures PA en `BLOCKED_MODALITY_PA` tant qu'une vraie modalité frontale n'existe pas.
5. Ne pas activer de norme historique dans ce lot.
6. Une mesure ne devient implémentable que si landmark + construction + opération + modalité sont tous source-lockés.

## Next exact

Créer les fixtures géométriques manuelles et les tests unitaires correspondants pour les primitives déjà calculables, puis confronter les résultats aux modules Steiner/Tweed/McNamara/Ricketts/COM existants sans modifier leurs valeurs runtime tant qu'une divergence n'est pas expliquée.