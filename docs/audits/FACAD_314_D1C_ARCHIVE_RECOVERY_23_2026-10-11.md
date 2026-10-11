# FACAD 3.14 — Recovery réelle des 23 archives D1C manquantes dans Git

**2026-10-11 · Scope : retranscription UIA de l'éditeur, à partir des artefacts officiels Robert (non clinique).** Recherche à partir de `feat/cephalo-facad-direct-parity-runtime-probe@bb19a48e1c5cc002d406a3e8c5feeac478dab1b3`. Documentation seule, aucune exécution de FACAD ni édition patient dans cette étape.

## Verdict précis et reproductible

- **23/23 archives ZIP récupérées et inspectées**, y compris le run partiellement échoué **Steiner**, distinct du run **Tweed** exécuté séparément. Chaque archive présente les trois dumps de la grille UIA active (Measurements, Lines and calc. points, Markers), y compris lorsque le tableau comporte réellement zéro ligne.
- **69/69 onglets sources** parcourus à partir de la *première* grille `AUTOID=1317` (mesures/lignes) ou `1316` (repères) ; en-têtes testés exactement, chaque ligne validée pour l'identité du premier champ et le nombre exact de colonnes. Autres grilles (Analysis Values/Properties) délibérément exclues.
- **1 436 lignes de premier tableau récupérées** : **527** lignes Measurements (dont headings), **220** Lines/constructions, **689** Markers. Parmi elles, **335 UIA_OFFSCREEN=True** (133 mesures ; 202 repères), signalant un défilement/une visibilité à vérifier si l'on veut une preuve visuelle complète.
- **69/69 noms d'éditeur identifiés** dans les dumps ; **66** correspondent littéralement au catalogue, tandis que **3/3 grilles de Tubingen** affichent la variante orthographique réelle **`Tübingen`**. Alias de titre observé et accepté explicitement pour l'inventaire, **pas un alias de repère/formule**.
- **21/21 empreintes SHA-256 ZIP** concordent *exactement* avec les valeurs des 21 archives précédemment épinglées dans le registre D1C. Pour **Steiner/Tweed**, SHA-256 calculés sur les ZIP réellement téléchargés mais **non assimilés à une empreinte préalablement certifiée dans le registre**.
- Toutes les archives portent les statuts `D1C_EDITOR_SAVE_BUTTON_NOT_INVOKED=true` et `D1C_PATIENT_ANALYSIS_LOAD_NOT_INVOKED=true`. Ce sont des déclarations d'instrumentation, non une preuve universelle qu'aucun stockage partagé n'a été écrit.
- Le fichier de sortie dérivé de cette session, `FACAD_D1C_RECOVERED_23_UIA_2026-10-11.json`, contient les cellules, colonnes, étiquettes, état/offscreen, origine run/artefact/SHA pour chaque ligne ; **SHA-256 9b2e5fe5990658689cc03258e53ddb5a3b8cf5912ae4140eecfda59dc11711ba**. Le fichier JSON est un **artefact de conversation / travail, pas encore ajouté au dépôt**. Les archives GitHub liées ici restent les sources primaires contrôlables.
- La donnée récupérée **n'est pas une formule cliniquement validée, ni une mesure patient**, et les analyses dotées de 42 triplets Git ne changent pas : **42 triplets versionnés dans la branche**, 23 ensembles de **preuves UIA récupérées hors de Git**.

## Matrice de provenance 23/23

| Profil | Mesures : lignes UIA | Lignes : lignes UIA | Repères : lignes UIA | Lignes UIA offscreen | Run / archive | SHA-256 ZIP téléchargé | État |
|---|---:|---:|---:|---:|---|---|---|
| Ancell | 10 | 16 | 34 | 11 | [#37957532550](https://github.com/hraaaaf/Digital_crown/actions/runs/37957532550/artifacts/11630165932) | `eb7288543be48187a4f9b659afbf5e92705bab84eeb01e6cf70ac4a0408c8253` | Editor unsaved |
| Bern University | 37 | 8 | 37 | 28 | [#37957532753](https://github.com/hraaaaf/Digital_crown/actions/runs/37957532753/artifacts/11630855135) | `a22fa9e4b64aa05867d49a7e29d9eb5df28367da1d2bbd7b290894b1ca8d2e14` | Editor unsaved |
| Bjork-Tiops | 38 | 19 | 42 | 34 | [#37957532699](https://github.com/hraaaaf/Digital_crown/actions/runs/37957532699/artifacts/11631055793) | `965278f37a77ce8b833ea7aefa744ef45f7cb86801b5a965126c2841196f6ac4` | Editor unsaved |
| Bjork-Tiops (female-11) | 38 | 19 | 42 | 34 | [#37957532439](https://github.com/hraaaaf/Digital_crown/actions/runs/37957532439/artifacts/11630096541) | `5b0aae5448b5a60bc7d968eb0584775e521edb30c3048b3478e3914a9b642f09` | Editor unsaved |
| Bjork-Tiops (male-12) | 38 | 19 | 42 | 34 | [#37957532922](https://github.com/hraaaaf/Digital_crown/actions/runs/37957532922/artifacts/11630851742) | `418256ab1aee03ef35014418e0c5b5046714e3363b92456e141763211c83e77e` | Editor unsaved |
| EAIO | 32 | 10 | 33 | 19 | [#37957532651](https://github.com/hraaaaf/Digital_crown/actions/runs/37957532651/artifacts/11630525128) | `2fb56a970249caecbee91eb82b2fba899bb9d99935b312cfb6c5966d0adc447d` | Editor unsaved |
| Facad Mini | 7 | 2 | 26 | 3 | [#37957532539](https://github.com/hraaaaf/Digital_crown/actions/runs/37957532539/artifacts/11630065264) | `3d3a1deec1df7e436150ba0f02e08bdc2b17bd302efcd91ae801e24edf742604` | Editor unsaved |
| Geneve | 19 | 7 | 29 | 6 | [#37957532517](https://github.com/hraaaaf/Digital_crown/actions/runs/37957532517/artifacts/11631265723) | `19bfd96c8cf23865ffeaabb8a52e6569029243e64a5848c42805c3d3b3da4180` | Editor unsaved |
| HarmonyBox | 8 | 3 | 26 | 3 | [#37957532281](https://github.com/hraaaaf/Digital_crown/actions/runs/37957532281/artifacts/11631090683) | `e5833293fdb5b234236cacc4ad896d6ca272a38389d4f7a539f21daf7c320f15` | Editor unsaved |
| Harvold | 4 | 0 | 5 | 0 | [#37957533614](https://github.com/hraaaaf/Digital_crown/actions/runs/37957533614/artifacts/11630781507) | `5a8567f2c7f5d341a5e0ffd286855aa81b56d19b4d6a7b417043e08db0ec3440` | Editor unsaved |
| Jefferson-Sassouni | 11 | 11 | 30 | 7 | [#37957532509](https://github.com/hraaaaf/Digital_crown/actions/runs/37957532509/artifacts/11630495314) | `c88a43079b00e562b43945080077afae8d99ede28a2d49ac1f3012d61ef4b12c` | Editor unsaved |
| Mahony FFG | 46 | 17 | 38 | 38 | [#37957532369](https://github.com/hraaaaf/Digital_crown/actions/runs/37957532369/artifacts/11629055989) | `bcfae7b9d6202c64e59a4470c3dd971a23adf554808f2c169c85a466d1a4fc28` | Editor unsaved |
| McGann | 19 | 8 | 31 | 8 | [#37957532521](https://github.com/hraaaaf/Digital_crown/actions/runs/37957532521/artifacts/11630550826) | `767754620fe6bc013405e07944d21971d778bdd857d8b7fe2e02cbcc837cf939` | Editor unsaved |
| McLaughlin | 17 | 7 | 30 | 7 | [#37957532438](https://github.com/hraaaaf/Digital_crown/actions/runs/37957532438/artifacts/11630586035) | `2e1fc744eb7587e57e7cd292e180c86b85a7fe4d78f2645c43ed5124ed25faa7` | Editor unsaved |
| Oslo | 27 | 6 | 32 | 13 | [#37957532620](https://github.com/hraaaaf/Digital_crown/actions/runs/37957532620/artifacts/11630705537) | `c076023d4bad23864c020d02eb89bb0b8240ada8e2a61633e40acd015d381432` | Editor unsaved |
| Photo AM Schwarz | 18 | 4 | 10 | 0 | [#37957532617](https://github.com/hraaaaf/Digital_crown/actions/runs/37957532617/artifacts/11630460309) | `7a261117a1c75cfe28a91cae7b224464958cfd09585219baf36f16e786357513` | Editor unsaved |
| Quadrilateral DiPaolo | 22 | 13 | 12 | 0 | [#37957532660](https://github.com/hraaaaf/Digital_crown/actions/runs/37957532660/artifacts/11630875772) | `21df37f52d6acde52f9021e68a2b5817f62b6a457e0ef9e96d8e77bce79ea27a` | Editor unsaved |
| Rakosi | 31 | 14 | 32 | 18 | [#37957532320](https://github.com/hraaaaf/Digital_crown/actions/runs/37957532320/artifacts/11629785970) | `94b1bcaeb17cd8f5814d892905ec32c9f6b6a186022e0b0cfd06bb456e4ebc8c` | Editor unsaved |
| Steiner | 17 | 6 | 31 | 8 | [#37857655276](https://github.com/hraaaaf/Digital_crown/actions/runs/37857655276/artifacts/11585052434) | `c9d52eb3012a426dd67bdec994a6f0ad3d7bc68b78e2bf514dd300bfc93d62f7` | Éditeur observé ; run global FAILED |
| Tubingen | 44 | 9 | 32 | 31 | [#37958732410](https://github.com/hraaaaf/Digital_crown/actions/runs/37958732410/artifacts/11631277115) | `5818ca03021e4e5420d8506e7fb2d4cab7bf5f3614d81c9127352ba1e4013673` | Editor unsaved |
| Tweed | 9 | 5 | 28 | 5 | [#37861203066](https://github.com/hraaaaf/Digital_crown/actions/runs/37861203066/artifacts/11585454878) | `60e5ff7797cb5107d32c012ab0a8f40e5f0eaab33c152495c435f70d13ae2409` | Editor unsaved |
| Wylie | 5 | 2 | 28 | 5 | [#37957532916](https://github.com/hraaaaf/Digital_crown/actions/runs/37957532916/artifacts/11631356112) | `78e154649298e37fab5f535cf9bf398c3702c06b459965eb5ead24cb24413c6a` | Editor unsaved |
| Zurich | 30 | 15 | 39 | 23 | [#37957532681](https://github.com/hraaaaf/Digital_crown/actions/runs/37957532681/artifacts/11631150646) | `dec5cdbeffdd676d87ce20941341d496ea9c7f00e79da244e831827d0c74e745` | Editor unsaved |

*Le zéro dans « lignes » pour Harvold est un tableau réellement vide observé dans les traces de l'éditeur ; il ne faut pas créer des entrées de lignes imaginaires.*

## Exemples nouvellement rétablis (ne pas activer les normes)

- **Steiner (échec global)** : 17 lignes de mesures dont headings, 6 objets de l'onglet Lines, 31 repères ; l'UIA expose `SNA Angle3p`, `SNB Angle3p`, `ANB Angle3p`, `Is-NA DistLine`, `OL/NSL Angle2ln` et `SL Line`. Les nombres de la colonne `Norm` sont **des littéraux FACAD sans population validée**, pas les normes activables Digital Crown. Le run d'origine a échoué : preuve partielle seulement.
- **Tweed** : 9 lignes de mesures, 5 lignes/constructions, 28 repères. `FMA (ML/FH)` est présenté `Angle2ln`, `IMPA (ILi/ML)` `Angle4p`, `FMIA (ILi/FH)` `Angle2ln`. Cette variété de types et d'arguments doit être explicitement reconnue avant toute correspondance LOT06.
- **Ancell** : 10 lignes de mesures, 16 lignes/constructions, 34 repères ; exemples : `Xi` de type `Intersect`, `R23`/`R13` de type `Inter2ln`. Les opérateurs et points doivent être vérifiés par définition et cas synthétique, jamais par un libellé commun.
- **Harvold** : 4 mesures et zéro ligne dans la grille source ; la présence de 5 repères n'autorise pas à inventer de lignes sous-jacentes.

## C01/C02 : assertions littérales et trou scientifique restant

**C01 — 12 pages, SHA-256 `a977f219b6c9b95543551fe7a6e48587ac597b065e0200ab844e20ed322ba119` :**
- `PtV` : extrait court **page PDF 1** décrit une verticale ptérygoïdienne/perpendiculaire ; sa ligne de référence exacte **n'est pas prouvée par ce court extrait**.
- `CF` et `Xi` : les entrées construites sont signalées **page PDF 2** par le contrôle *whole-token* [run #37990457485](https://github.com/hraaaaf/Digital_crown/actions/runs/37990457485), associé au fichier `data/FACAD_F01_13_V314_WHOLE_TOKEN_SOURCE_SNIPPETS_2026-10-09.json`. **ATTENTION** : le premier scan `Xi` p.1 avait été un faux positif sur le mot anglais *Maxillary*. Les définitions complètes de leurs intersections restent à corroborer avec CPH et texte intégral.
- Les opérations `Line`, `Normal`, `Intersect`, `Inter2ln`, `Parallel`, `Arc` observées ne suffisent pas à reconstituer les conventions d'orientation et cas dégénérés.

**C02 — 34 pages, SHA-256 `4dbd3fa8419b684529fcbc17f615f49f7486cdf037fcfff025b1b307c0c0a548` :**
- Document officiel **localisé + SHA verrouillé**, mais **aucune définition de mesure page/règle n'est encore démontrée** par `FACAD_F01_13_V314_FIVE_PDF_TERM_PAGE_MATRIX_2026-10-09.json` ; son dictionnaire de hits C02 est vide uniquement pour les termes sélectionnés par l'ancien contrôle, **pas preuve d'une bibliothèque vide**.
- Priorité aux opérateurs observés `Angle2ln`, `Angle3p`, `Angle4p`, `Dist2p`, `DistLine`, `ProjLine`, `Proj90Line`, `Dist3p`, `Sub`, `Div` pour construire des références page-citées. Exiger versions, unité, convention de signe, inversion de direction et comportement sur géométrie dégénérée.
- Les rapprochements doivent vérifier **une définition indépendamment de FACAD**, puis comparer les résultats calculés dans Digital Crown **sur même géométrie et calibration**, avant toute affirmation de parité.
- **Contre-exemples déjà verrouillés** : Ricketts FACAD `PFH=Dist2p(CF,Go)` longueur ≠ entrée angulaire de l'Atlas indexé ; `PM'` est un point construit et non un alias direct du `Pm` anatomique. Références `CEPHALO_FACAD_F01_13_RICKETTS_GEOMETRY_DISCREPANCY_TRIAGE_2026-10-09.md` et `CEPHALO_FACAD_F01_13_RICKETTS_PRIMARY_SOURCE_RECONCILIATION_2026-10-09.md`.

**Documentation officielle de l'éditeur :** [Facad — analyses et éditeur](https://www.facad.com/wp/analyses/) ; [Manuel de référence 3.14](https://www.facad.com/dox/dox314/FacadRefMan.pdf). La bibliothèque est accessible depuis les onglets Measurement library / Line library ; ce constat produit ne remplace pas l'examen des pages d'origine.

## Contrôles indépendants internes : mêmes données, deux perspectives

**A — audit de provenance/données :** 23 correspondances nom→run→artefact, contrôle ZIP SHA pour les 21 archives précédemment épinglées, assertions de structure de 69 grilles, somme des lignes et offscreen. Résultat de recherche **SUPPORTED/VERIFIED pour les archives effectivement examinées**, pas pour les algorithmes vendor. Risque résiduel : les lignes UIA hors écran ne constituent pas une validation visuelle individuelle, et un résultat de run échoué n'est pas réécrit en SUCCESS.

**B — audit clinique/sécurité :** aucune formule, norme patient, mesure calculée ou recommandation thérapeutique n'est promue ; les erreurs d'identité, dimensions et versions sont signalées ; aucune activité Windows nouvelle ni changement runtime de Digital Crown. La source humaine indépendante et les oracles scientifiques manquent toujours.

**STATUT OPEN :** `ORTHO_ANALYSIS_PROTOCOLS_VERIFIED=OPEN`, `FAC03_D3=OPEN_RED`, `SHARED_APP_STORAGE_ISOLATION=UNVERIFIED`, `CLINICAL_EDIT_ALLOWED=false`, `CONVERGED=false`.

**Next précis :** ajouter le JSON dérivé contrôlé au dépôt avec vérificateur de structure adapté, puis étude C01/C02 page-par-page sur quatre familles prioritaires (Ricketts / Steiner / Tweed / McNamara) ; ensuite explorer réellement le menu d'éditeur sur Robert avec BEFORE/AFTER non destructifs. Le poste distant est actuellement OFFLINE, ce qui ne permet pas de certifier un nouvel essai visuel natif ici.