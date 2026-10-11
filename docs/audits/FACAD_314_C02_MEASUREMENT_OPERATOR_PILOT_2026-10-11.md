# FACAD 3.14 — C02 measurement operator pilot, scientific evidence v0.1

**2026-10-11 — ONLY SOURCE-OBSERVED UIA; NOT FORMULA-CERTIFIED, NOT CLINICALLY VALIDATED.** Source branche FACAD `feat/cephalo-facad-direct-parity-runtime-probe`, PR documentaire #829. Les cinq profils examinés sont **Steiner, Tweed, Ricketts (13 F), Ricketts (32 F), McNamara**.

## Premier résultat testable — composition des grilles Measurements

Total **93 lignes UIA**, dont **13 titres `Heading`** non calculés et **80 entrées de mesure** (y compris deux soustractions, sans calcul réel). Tous ces types et colonnes sont transcrits de l'éditeur **non enregistré**, et non observés dans le moteur runtime.

| Opérateur littéral | Occurrences sur 5 profils | Classification documentaire provisoire |
|---|---:|---|
| `Angle2ln` | 12 | Angle candidat (unité ° ; convention à tester) |
| `Angle3p` | 11 | Angle candidat (unité ° ; convention à tester) |
| `Angle4p` | 20 | Angle candidat (unité ° ; convention à tester) |
| `Dist2p` | 8 | Distance/projection candidate (calibration, orientation à prouver) |
| `Dist3p` | 4 | Distance/projection candidate (calibration, orientation à prouver) |
| `DistLine` | 13 | Distance/projection candidate (calibration, orientation à prouver) |
| `Heading` | 13 | Titre non calculé |
| `Proj90Line` | 1 | Distance/projection candidate (calibration, orientation à prouver) |
| `ProjLine` | 9 | Distance/projection candidate (calibration, orientation à prouver) |
| `Sub` | 2 | Opération arithmétique, dimension dépend des opérandes |

Ventilation par profil :
- Steiner : **17 lignes (3 titres, 14 mesures)**, extraites de [run #37857655276](https://github.com/hraaaaf/Digital_crown/actions/runs/37857655276), artefact #11585052434. **Run global FAILED** ; l'éditeur a été observé, pas validé dans son ensemble.
- Tweed : **9 mesures**, [run #37861203066](https://github.com/hraaaaf/Digital_crown/actions/runs/37861203066), artefact #11585454878, extraction `FACAD_D1C_RECOVERED_23_UIA_2026-10-11.json` disponible en artefact de travail de la conversation, pas encore intégré à Git.
- Ricketts (13 F) : **17 lignes (4 titres, 13 mesures)** ; fichier UIA `docs/audits/data/FACAD_314_D1C_RICKETTS13F_EDITOR_MEASUREMENTS_UIA_2026-10-09.csv`, Git blob `802df33d3c15cbaba095123f4b2b700689edae44`.
- Ricketts (32 F) : **38 lignes (6 titres, 32 mesures)** ; fichier UIA `docs/audits/data/FACAD_314_D1C_RICKETTS32F_EDITOR_MEASUREMENTS_UIA_2026-10-09.csv`, blob `220b4a23d469e1c634ff9d8df7ad22706ae7cc7a`.
- McNamara : **12 mesures**, fichier UIA `docs/audits/data/FACAD_314_D1C_MCNAMARA_EDITOR_MEASUREMENTS_UIA_2026-10-09.csv`, blob `e355591a8055ef383aeb9ebee955734250ac9976`.

**Totalisation :** les comptes source sont vérifiés dans les CSV disponibles et les grilles reconstruites (Steiner/Tweed). Un inventaire de types n'est ni preuve de formule ni preuve de parité clinique.

## Exceptions structurelles découvertes — garder fail closed

1. **Même nom de plan, construction différente selon profil.** L'éditeur Steiner définit `ML = Line(Go,Gn)` tandis que Tweed définit `ML = Line(Go,Me)`. Les calculs `ML/NSL` (Steiner) et `FMA (ML/FH)` (Tweed) ne doivent jamais être construits à partir d'un alias global `ML` qui ignorerait la définition par analyse. Source : grilles Lines récupérées de l'éditeur Steiner/Tweed, runs précités. Règle : `(profile_id, line_id, definition_version)` plutôt qu'un identifiant de plan non contextualisé.
2. **Steiner `SL = Line(PGs,MS)`**, avec `Ls-SL` et `Li-SL` comme distances à cette ligne. Le point `MS` et sa provenance doivent être explicités avant de déclarer équivalence à un autre plan esthétique. `MS` ne peut être automatiquement remplacé par un point issu d'une autre publication.
3. **Ricketts 13F `PFH = Dist2p(CF,Go)`, norme UIA littérale `63±3.5`.** Il s'agit d'une distance vendue comme telle par le fabricant ; interdit d'aligner avec une **mesure angulaire** du résumé Atlas 2009 indexé. Ricketts 32F utilise aussi `Dist2p(CF,Go)`. Référence existante `CEPHALO_FACAD_F01_13_RICKETTS_GEOMETRY_DISCREPANCY_TRIAGE_2026-10-09.md`. La norme ne doit pas être activée sans population/unité et référence.
4. **Ricketts 32F `Mand len=Dist2p(Xi,PM')`.** Le vendor CPH étudié définit `PM' = Intersect(Xi,PM,A,Pog)`. Il est interdit de faire un alias silencieux `PM'=Pm_Ricketts` ou de prétendre une parité même-sujet. Une différence mathématique sur configuration synthétique est déjà documentée dans l'audit F01.13.
5. **McNamara `Max-Mand diff=Sub(Co-Gn,Co-A)`.** Cette ligne utilise deux **mesures dérivées**, elles-mêmes observées comme `Dist2p`. Vérifier dans le moteur que les dépendances sont présentes, mesurées dans la même unité et étalonnées avec la même calibration ; aucun fallback à zéro si Co/Gn/A absent.
6. **Type d'angle et orientation à examiner** : Steiner `ANB=Angle3p(N,A,B)`, Tweed `IMPA=Angle4p(Go,Me,Ii,Iia)`, Ricketts `Facial axis=Angle4p(Pt,Gn,N,Ba)`. Ces signatures UIA ne déterminent PAS automatiquement l'angle réfléchi, son orientation, l'ordre géométrique interne, le signe, ni une convention universelle.
7. **Projections ne sont pas toutes équivalentes.** Ricketts 32F distingue `Overjet=ProjLine(OL,Ii,Is)` de `Overbite=Proj90Line(OL,Is,Ii)`. Ne pas échanger ces opérateurs ou inverser les arguments sans un oracle de référence.
8. **Contraste de normes entre analyses :** des colonnes `Norm` même nom (p. ex. `Facial axis` Ricketts 13F 90±3.5 contre 32F 90±3) diffèrent déjà, même avant population/âge/version. Le schéma de Digital Crown doit porter la source normative **par profil et édition**, jamais par simple label.

## Bibliothèques PDF : source, contenu réellement examiné, preuves requises

- **C01 original** (12 pages), SHA256 `a977f219b6c9b95543551fe7a6e48587ac597b065e0200ab844e20ed322ba119` : court contexte officiellement vérifié pour `PtV` en p.1 et `Xi`/`CF` en p.2 par whole-token source-run [#37990457485](https://github.com/hraaaaf/Digital_crown/actions/runs/37990457485). **Piège déjà identifié** : l'ancienne occurrence de `Xi` p.1 correspondait à une sous-chaîne de `Maxillary`, invalidée. Le texte complet de définition n'est pas reconstitué.
- **C02 original** (34 pages), SHA256 `4dbd3fa8419b684529fcbc17f615f49f7486cdf037fcfff025b1b307c0c0a548` : fichier officiel inventorié dans [run #37981554220](https://github.com/hraaaaf/Digital_crown/actions/runs/37981554220). **Aucune page de définition d'opérateur ou de norme ne peut encore être citée comme inspectée dans cette étape.** L'ancien dictionnaire `hits={}` était limité aux termes recherchés, pas à la totalité de C02.
- Le [manuel de référence officiel 3.14](https://www.facad.com/dox/dox314/FacadRefMan.pdf) décrit l'éditeur, les 8 colonnes `Ceph Name / Type / Arg1-4 / Norm / Draw`, et l'utilisation de lignes/points construits dans les mesures. C'est une preuve **de structure produit**, pas une convention mathématique indépendante ni une preuve des 80 valeurs.
- Règle licence : ne pas republier les PDF propriétaires complets ni prétendre les avoir lus lorsque seuls noms/hashes/courts extraits sont accessibles.

## C02 : contrat scientifique à remplir avant toute implémentation

Une **ligne** de contrat par opérateur, puis une ligne **par instanciation profile + arguments** :

`vendor_build | profile_name | item_name | operator | arg_order | dependency_types | anatomical_landmark_ids | constructed_object_ids | mathematical_definition | angle_convention | signed_projection_direction | calibration_required | canonical_unit | norm_source_edition | norm_population_age_sex | official_pdf_page | independent_primary_source | reference_output | synthetic_oracle | dc_contract_id | source_state | clinical_gate`.

Priorité :
1. **Dimensions :** Dist/Proj → longueur ou valeur de projection qui requiert une calibration ; Angle → angle ; Sub/Div → dimension dérivée, dimensions des entrées requises et compatibles.
2. **Dépendances :** interdiction de alias pour `ML`, `SL`, `MS`, `PM'` ; `Co-Gn` et `Co-A` non résolus => `NOT_COMPUTABLE`, sans valeur inventée.
3. **Orientation et dégénérescences :** angles 2 lignes et 3/4 points sur quadrants distincts ; ligne de longueur zéro ; division par zéro ; projections inversées ; échelle pixels↔mm.
4. **Normes :** par version, population, sexe/âge applicables ; sans preuve `NOT_ACTIVATED` même si un intervalle est affiché dans Facad.
5. **Parité numérique :** uniquement sur mêmes landmarks et calibration, avec oracle indépendant, tolérance prédéfinie et avis clinique ; jamais depuis seul tableau UIA.

## Revue adversariale interne — non humaine

**Perspective A science (BLOCKER si fausse identité) :** le plan `ML` n'est pas universel (Go-Gn vs Go-Me), `SL` dépend de `MS`, `PFH` longueur ne devient pas angle, `PM'` n'est pas `Pm`. Aucune promotion clinique de ces constructions. **Statut OPEN :** 34 pages C02 restent à examiner effectivement.

**Perspective B QA/provenance (BLOCKER si faux green) :** exactement **80** entrées de mesure dans **93** lignes UIA, titres exclus, run Steiner FAILED conservé ; document n'affirme pas avoir lu C02 page-par-page ni exécuté une seule valeur patient. Aucun moteur runtime touché. Le chemin d'extraction JSON des 23 doit être versionné/testé avant intégration au référentiel.

**Gates :** `ORTHO_ANALYSIS_PROTOCOLS_VERIFIED=OPEN` ; `FAC03_D3=OPEN_RED` ; `CLINICAL_EDIT_ALLOWED=false` ; `CONVERGED=false`. Même si la CI documentaire est verte, aucune validation indépendante réelle ni test de formules sur application.

**Next précis :** lire la source C02 complète en essai autorisé, isoler les pages des opérateurs `Angle2ln/Angle3p/Angle4p/Dist2p/DistLine/ProjLine/Proj90Line/Dist3p/Sub`, annoter page+définition+dimension+convention ; ensuite jeux de vecteurs synthétiques, comparaisons du moteur LOT06, puis vrais écrans Robert lorsque l'agent Windows est accessible et les gates d'isolation satisfaites.