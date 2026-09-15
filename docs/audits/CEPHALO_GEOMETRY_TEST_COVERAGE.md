# Céphalo-N — Couverture géométrique et fixtures

Statut : **WORKING V1 — INVENTAIRE VÉRIFIÉ DU RUNTIME ACTUEL**

Date : 2026-09-15

## Goal / Succès / Preuve

**Goal** — relier chaque mesure validée à une preuve géométrique concrète : fonction runtime, fixture manuelle, test existant, ou gate fail-closed.

**Succès** — aucune mesure ne peut être dite « couverte » sans fonction + convention + test/fixture ; aucune mesure bloquée n'est approximée avec une autre géométrie.

**Preuve** — inspection des modules `cephalo_steiner_geometry.py`, `cephalo_tweed_merrifield_geometry.py`, `cephalo_mcnamara_geometry.py`, `cephalo_ricketts_geometry.py`, `cephalo_constructions.py`, tests R6/R8/R9/CRANIOM existants, plus la fixture synthétique `backend/tests/fixtures/cephalo/source_locked_geometry_v1.json` et son test transversal.

## Légende

- `COVERED` : géométrie implémentée + preuve de test/fixture.
- `PRIMITIVE_ONLY` : primitive géométrique existe ailleurs mais pas encore de contrat source-spécifique pour cette analyse.
- `IMPLEMENTATION_MISSING` : définition source-lockée mais fonction dédiée absente.
- `BLOCKED_LANDMARK` : landmark exact absent/non validé ; substitution interdite.
- `BLOCKED_MODALITY_PA` : nécessite une vraie incidence PA/frontale.
- `SOURCE_LOCK_REQUIRED` : définition exacte encore insuffisamment verrouillée.
- `NOMENCLATURE_MISMATCH` : calcul géométrique présent mais identifiant/label runtime non aligné avec la cartographie validée.

---

## Steiner

| Mesure | État géométrique | Preuve / gate |
|---|---|---|
| SNA | `COVERED` | `steiner_sna_deg_v1` + fixture V1 |
| SNB | `COVERED` | `steiner_snb_deg_v1` + fixture V1 |
| ANB | `COVERED` | `steiner_anb_deg_v1` + fixture V1 ; conserve la parité runtime par arrondi SNA/SNB |
| U1-NA angle | `COVERED` | `steiner_u1_na_deg_v1` + fixture V1 |
| U1-NA linéaire | `BLOCKED_LANDMARK` | surface coronaire/faciale U1 explicite absente |
| L1-NB angle | `COVERED` | `steiner_l1_nb_deg_v1` + fixture V1 |
| L1-NB linéaire | `BLOCKED_LANDMARK` | surface coronaire/faciale L1 explicite absente |
| Angle interincisif | `COVERED` géométrie partagée | CRANIOM interincisal déjà typé/testé ; source-spécificité Steiner à conserver dans futur contrat |
| Plan occlusal-SN | `SOURCE_LOCK_REQUIRED` | définition exacte du plan occlusal non matérialisée |
| GoGn-SN | `COVERED` | `steiner_sn_mp_deg_v1` + fixture avec `Gn_anatomic` explicite |
| L1-GoGn | `IMPLEMENTATION_MISSING` | axe L1 + Go-Gn définis ; fonction Steiner dédiée absente |
| U6-NA | `BLOCKED_LANDMARK` | point molaire exact/couronne à source-locker |
| L6-NB | `BLOCKED_LANDMARK` | point molaire exact/couronne à source-locker |
| SND 1959 | `BLOCKED_LANDMARK` | D non matérialisé comme contrat source-locké runtime |
| Pog-NB 1959 | `IMPLEMENTATION_MISSING` | Pog hard / NB définissables ; fonction dédiée absente |
| L1-D line linéaire | `BLOCKED_LANDMARK` | D + surface coronaire L1 |
| L1-D line angulaire | `BLOCKED_LANDMARK` | D + contrat GoGn/Gn anatomique à matérialiser |

## Tweed — variante Digital Crown Po-Or sélectionnée

| Mesure | État géométrique | Preuve / gate |
|---|---|---|
| FMA | `COVERED` | `tweed_fma_deg_v1` + `test_cephalo_r6_tweed_merrifield.py` + fixture V1 |
| IMPA | `COVERED` | `tweed_impa_deg_v1` + R6 + fixture V1 |
| FMIA | `COVERED` | `tweed_fmia_deg_v1` + R6 + fixture V1 |

**Contrat actif** : `DC_TWEED_ANATOMICAL_FH_VARIANT = Po_anatomic-Or`. Cela ne transforme pas cette géométrie en reproduction stricte du Frankfort ear-rod 1954. Les normes historiques Tweed restent un lot normatif séparé.

## McNamara 1984

| Mesure | État géométrique | Preuve / gate |
|---|---|---|
| A→Nperp | `PRIMITIVE_ONLY` | `nasion_vertical_offset_mm_v1` existe côté CRANIOM ; contrat McNamara dédié absent |
| SNA | `PRIMITIVE_ONLY` | calcul Steiner disponible ; pas de contrat McNamara dédié |
| Co-A | `COVERED` | `mcnamara_co_a_mm_v1` + R8 + fixture V1 |
| Co-Gn anatomique | `COVERED` | `mcnamara_co_gn_mm_v1` + R8 + fixture V1 ; futur ID doit dire explicitement `Gn_anatomic` |
| Différentiel CoGn-CoA | `PRIMITIVE_ONLY` | dérivation exacte testée dans fixture V1 ; mesure dédiée non matérialisée |
| ANS-Me | `COVERED` | `mcnamara_ans_me_mm_v1` + R8 + fixture V1 |
| Mandibular plane angle | `PRIMITIVE_ONLY` | angle FH/Go-Me calculable via primitives Tweed ; contrat McNamara dédié absent |
| Facial axis | `IMPLEMENTATION_MISSING` | contrat McNamara doit utiliser PTM→Gn_constructed vs Ba-N ; ne pas reprendre `Pt_Ricketts` |
| Pog→Nperp | `PRIMITIVE_ONLY` | primitive Nperp disponible ; ne jamais substituer `Situation_B` (B→Nperp) |
| U1→A vertical | `BLOCKED_LANDMARK` | surface faciale U1 absente |
| L1→A-Pog | `BLOCKED_LANDMARK` | surface faciale L1 absente |
| Upper pharynx | `BLOCKED_LANDMARK` | landmarks airway dédiés absents |
| Lower pharynx | `BLOCKED_LANDMARK` | landmarks airway dédiés absents |

## Ricketts 1981 — profil

| Mesure | État géométrique | Preuve / gate |
|---|---|---|
| Facial Angle (N-Pog / FH) | `COVERED` + `NOMENCLATURE_MISMATCH` | `ricketts_facial_depth_deg_v1` calcule le bon angle et est testé R9 + fixture V1, mais runtime l'identifie `FACIAL_DEPTH` |
| Facial Axis (Pt-Gn / Ba-N) | géométrie `COVERED`, runtime `BLOCKED_LANDMARK` | `ricketts_constructed_gn_v1` + `ricketts_facial_axis_deg_v1` testés ; `Pt_Ricketts` auto non prouvé |
| Mandibular Plane FH/Sub.Go.-M | `IMPLEMENTATION_MISSING` | `Sub.Go.-M` absent ; **Go-Me interdit comme substitution** |
| Oral Gnomon ANS-Xi-Pm | `BLOCKED_LANDMARK` | Xi/Pm absents runtime |
| Palatal Plane ANS-PNS/FH | `PRIMITIVE_ONLY` | points potentiels présents mais mapping PNS auto non autoritaire et contrat dédié absent |
| Maxillary Convexity A→N-Pog | `COVERED` | `ricketts_convexity_signed_distance_px_v1` + R9 + fixture V1 |
| L1→A-Pog | `BLOCKED_LANDMARK` | point/surface dentaire exact à source-locker |
| U6→PTV | `BLOCKED_LANDMARK` | PR/PTV + distal crown U6 absents |
| Interincisal angle | `COVERED` géométrie partagée | CRANIOM interincisal déjà testé ; contrat Ricketts dédié futur |
| Lower lip→E-plane | `COVERED` | E-line V2 perpendiculaire R18/R9, hard/soft séparés |
| Bend of Mandible | `IMPLEMENTATION_MISSING` | construction corpus/condyle exacte à matérialiser |

## Ricketts 1981 — PA/frontale

Les **12 facteurs** restent tous `BLOCKED_MODALITY_PA` : aucune valeur ne doit être dérivée d'une téléradiographie latérale.

1. Nasal cavity width NC-NC
2. Maxillary relation droite J→Z-Ag
3. Maxillary relation gauche J→Z-Ag
4. Mandibular width Ag-Ag
5. Skeletal symmetry
6. Intermolar width B6-B6
7. Intercuspid width B3-B3
8. Lower molar→Fronto-Denture Plane droite
9. Lower molar→Fronto-Denture Plane gauche
10. Lower incisor midpoint→Frontal A-Po
11. Molar crossbite droite
12. Molar crossbite gauche

## COM_DC_LEGACY_V1

| Mesure | État géométrique | Preuve / gate |
|---|---|---|
| Situation A | `COVERED` | `nasion_vertical_offset_mm_v1` + fixture V1 |
| Situation B | `COVERED` | même primitive avec B + fixture V1 ; **≠ McNamara Pog→Nperp** |
| A'B' | `COVERED` | `craniom_ab_prime_mm_v1` + conventions CRANIOM + fixture V1 |
| Profondeur faciale legacy | `COVERED` | `craniom_facial_depth_mm_v1` + fixture V1 ; **≠ Ricketts Facial Angle** |
| I/Frankfort | `COVERED` | CRANIOM U1/FH convention testée ; **≠ Tweed FMIA** |
| IMPA / FMA / Interincisif | `COVERED` géométrie existante | conventions CRANIOM/Tweed testées |
| Surplomb / Recouvrement | `RUNTIME_LEGACY_TO_AUDIT` | présents dans moteur/UI COM ; provenance et convention exacte doivent être verrouillées séparément avant promotion scientifique |

## Couverture apportée par ce lot

Fixture manuelle commune : `backend/tests/fixtures/cephalo/source_locked_geometry_v1.json`.

Test transversal : `backend/tests/test_cephalo_source_locked_geometry_fixture_v1.py`.

Il certifie sans dépendance au détecteur :

- Steiner : SNA, SNB, ANB, U1-NA°, L1-NB°, SN-GoGn ;
- Tweed DC Po-Or : FMA, IMPA, FMIA + fermeture du triangle sur le cas synthétique ;
- McNamara : Co-A, Co-Gn anatomique, ANS-Me + différentiel dérivé ;
- Ricketts : Facial Angle géométrique, Gn construit, Facial Axis géométrique, convexité ;
- COM : signe AP de Situation A/B, A'B', magnitude de profondeur faciale legacy ;
- cas dégénérés : références nulles/parallèles/calibration absente → fail-closed.

## Divergence identifiée

`RICKETTS_FACIAL_DEPTH_DEG_V1` / `FACIAL_DEPTH` dans le runtime calcule l'angle `FH ↔ N-Pog`, qui correspond au **Facial Angle** de la cartographie Ricketts 1981 validée. La formule n'est pas corrigée dans ce lot ; l'identifiant/label doit être traité comme dette de nomenclature avec migration de compatibilité avant tout changement runtime.

## Next exact

1. Faire exécuter le nouveau test transversal par CI.
2. Si vert, matérialiser les prochains contrats **non bloqués** seulement : McNamara A→Nperp/différentiel/Pog→Nperp et Steiner L1-GoGn/Pog-NB selon source-lock exact.
3. Garder toutes les mesures nécessitant surface coronaire, Xi/Pm, airway, PTV, Sub.Go.-M ou PA en fail-closed.
4. Traiter le mismatch `Ricketts Facial Angle` vs `FACIAL_DEPTH` dans un lot de compatibilité séparé, sans casser les snapshots historiques.
