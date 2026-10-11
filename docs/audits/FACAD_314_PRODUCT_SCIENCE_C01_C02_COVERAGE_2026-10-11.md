# FACAD 3.14 — Consolidation scientifique 65 analyses / C01-C02 / exploration produit

Date : 2026-10-11. **RESEARCH-ONLY — OPEN.** Branch source : `feat/cephalo-facad-direct-parity-runtime-probe` at `bb19a48e1c5cc002d406a3e8c5feeac478dab1b3`. Aucune certification clinique, équivalence de formules, mesure patient, merge ou déploiement.

## Sources et join vérifiable

- `docs/audits/data/FACAD_314_D1_LATERAL_STANDARD_65.csv` blob `63ad09d0f5aba5f66359c983948e44f86cbc574c` : **65** entrées Standard latérales.
- `docs/audits/data/FACAD_314_D1C_EDITOR_DEFINITIONS_LEDGER_2026-10-09.csv` blob `fa5f22937a6cbc47c3de62f76c780e5cc0a382fb` : **65** observations D1C ; **64** `EDITOR_DEFINITION_LOADED_NOT_SAVED` et **1** `EDITOR_OBSERVED_UNSAVED_IN_PARTIAL_FAILURE` (Steiner).
- `docs/audits/data/FACAD_314_F01_13_SOURCE_CROSSWALK_2026-10-09.csv` blob `61ac5bf24b2c180c5702ff66ba1d2ee3dbdd097d` : **65** rapprochements nominaux, **56** `NO_REPO_MAPPING`, **4** `EXACT_NAMED_MAPPING_UNVERIFIED`, **4** `RICKETTS_VENDOR_VARIANT_UNRESOLVED`, **1** `NAME_ONLY_PROVISIONAL_PACK`.
- Répertoire `docs/audits/data` : **141 fichiers**, dont **126 CSV d'interface UIA**, représentant **42 analyses × 3 onglets** (`MEASUREMENTS`, `LINES`, `MARKERS`), triplets complets au sens **présence de fichiers**, pas complétude scientifique. **23 analyses** n'ont pas les trois CSV *dans Git à ce ref* ; les preuves peuvent exister en Library ou dans les artefacts de runs.
- Source ledger : **65/65 `patient_calculation=NOT_TESTED`**, crosswalk : **65/65 `facad_exact_composition=UNVERIFIED`**, **65/65 `geometry_equivalence=UNVERIFIED`**, **65/65 `normative_equivalence=NOT_ACTIVATED`**. Aucun transfert automatique au runtime Digital Crown.
- Le vieux catalogue D1 dit `loaded_on_robert=NO` pour 65 entrées, tandis que le registre D1C ultérieur témoigne du **chargement dans l'éditeur**, non du chargement clinique chez Robert. Ces deux champs concernent des opérations différentes.
- Jointure effectuée sur les noms d'analyses exacts pour catalogue/ledger/crosswalk ; correspondance des *noms de fichier* par suppression de ponctuation/espaces et alias de slug `RICKETTS_G_SAMSON` ↔ `Ricketts acc G. Samson`. Cette normalisation sert seulement à l'inventaire de fichiers, jamais aux repères anatomiques ou à la science.

**Règle :** observation de grille ≠ définition scientifique vérifiée ; étiquette identique ≠ géométrie équivalente ; capture d'éditeur ≠ calcul de patient ; PDF découvert ≠ norme applicable.

## C01 et C02 : statut des sources

Manifest officiel de l'installation, `FACAD_314_INSTALLED_SCIENCE_PDF_PROVENANCE_2026-10-09.json` blob `5b4f43df296d9f7583275fe85c95d2ecd5bf91c1`, [GitHub run #37981554220](https://github.com/hraaaaf/Digital_crown/actions/runs/37981554220) : **145 PDF installés**, 75 filtrés par nom, 12 prioritaires. Les filtres n'établissent aucune validation de formule.

| Bibliothèque installée | Pages | SHA-256 du PDF | Manque décisif |
|---|---:|---|---|
| `C01_Lateral Cephalometry Library - Lines and Contructed markers.pdf` | 12 | `a977f219b6c9b95543551fe7a6e48587ac597b065e0200ab844e20ed322ba119` | Identité des points, lignes, constructions, orientation, conditions de dégénérescence et provenance page/édition |
| `C02_Lateral Cephalometry Library - Measurements.pdf` | 34 | `4dbd3fa8419b684529fcbc17f615f49f7486cdf037fcfff025b1b307c0c0a548` | Type, arguments, formule, unité, signe, normes et population source par mesure |

Déjà acquis : `CEPHALO_FACAD_F01_13_INSTALLED_MANUALS_SOURCE_ACQUISITION_2026-10-09.md` ; `CEPHALO_FACAD_F01_13_RICKETTS_GEOMETRY_DISCREPANCY_TRIAGE_2026-10-09.md` ; `CEPHALO_FACAD_F01_13_RICKETTS_PRIMARY_SOURCE_RECONCILIATION_2026-10-09.md`. Ces dossiers contiennent des preuves partielles, qu'il faut utiliser sans les présenter comme validation universelle.

**Points rouges de science :** Facad 13F `PFH=Dist2p(CF,Go)` représente une **longueur**, face à une entrée angulaire ambiguë de l'Atlas 2009 indexé ; `PM'` dans la définition Ricketts vendor est un **point construit par intersection**, pas l'alias de `Pm_Ricketts`. Les éditions Ricketts 1960, 1981, Atlas 2009 et la version FACAD ne doivent pas être fusionnées par nom. Exiger l'Atlas authentifié avant de régler les ambiguïtés éditoriales.

**Fiche scientifique demandée pour chaque entrée de C01/C02 :** `source_sha256 | pdf_page | edition | object_id | vendor_label | type | arguments | dependencies | formula | unit | sign | norm_raw | norm_population | landmark_provenance | canonical_dc_id | geometry_state | independent_oracle | test_case | reviewer | status`. Remplir `UNKNOWN` au lieu d'inférer.

## 23 analyses sans triplet CSV versionné dans la branche source

1. Ancell
2. Bern University
3. Bjork-Tiops
4. Bjork-Tiops (female-11)
5. Bjork-Tiops (male-12)
6. EAIO
7. Facad Mini
8. Geneve
9. HarmonyBox
10. Harvold
11. Jefferson-Sassouni
12. Mahony FFG
13. McGann
14. McLaughlin
15. Oslo
16. Photo AM Schwarz
17. Quadrilateral DiPaolo
18. Rakosi
19. Steiner
20. Tubingen
21. Tweed
22. Wylie
23. Zurich

**Action vérifiable :** suivre le `github_run_id` du ledger, récupérer la capture et son ZIP/empreinte (GitHub artifacts ou Library), revoir captures et lignes hors écran, puis ajouter les données uniquement avec provenance. **Steiner et Tweed** sont prioritaires : l'ouverture de l'éditeur a été observée, les trois CSV manquent dans cette copie Git. Aucune reconstitution imaginaire.

## Matrice 65/65 — niveau d'observation, pas de validation

| # | Analyse | Éditeur D1C | CSV UIA sur ce ref | Crosswalk FACAD→DC |
|---:|---|---|---:|---|
| 1 | ABO | Chargé sans Save | 3/3 | `NO_REPO_MAPPING` |
| 2 | Airway (FH) | Chargé sans Save | 3/3 | `NO_REPO_MAPPING` |
| 3 | Airway (McNamara) | Chargé sans Save | 3/3 | `NO_REPO_MAPPING` |
| 4 | Airway (Mochida) | Chargé sans Save | 3/3 | `NO_REPO_MAPPING` |
| 5 | Airway (NL) | Chargé sans Save | 3/3 | `NO_REPO_MAPPING` |
| 6 | Alexander | Chargé sans Save | 3/3 | `NO_REPO_MAPPING` |
| 7 | AM Schwarz | Chargé sans Save | 3/3 | `NO_REPO_MAPPING` |
| 8 | Ancell | Chargé sans Save | 0/3 | `NO_REPO_MAPPING` |
| 9 | Arnett STCA (female) | Chargé sans Save | 3/3 | `NO_REPO_MAPPING` |
| 10 | Arnett STCA (male) | Chargé sans Save | 3/3 | `NO_REPO_MAPPING` |
| 11 | Arnett STCA Midface (female) | Chargé sans Save | 3/3 | `NO_REPO_MAPPING` |
| 12 | Arnett STCA Midface (male) | Chargé sans Save | 3/3 | `NO_REPO_MAPPING` |
| 13 | Basel 2013 | Chargé sans Save | 3/3 | `NO_REPO_MAPPING` |
| 14 | Bergen | Chargé sans Save | 3/3 | `NO_REPO_MAPPING` |
| 15 | Bergen short | Chargé sans Save | 3/3 | `NO_REPO_MAPPING` |
| 16 | Bern analysis | Chargé sans Save | 3/3 | `NO_REPO_MAPPING` |
| 17 | Bern University | Chargé sans Save | 0/3 | `NO_REPO_MAPPING` |
| 18 | Bimler | Chargé sans Save | 3/3 | `NO_REPO_MAPPING` |
| 19 | Bjork | Chargé sans Save | 3/3 | `NO_REPO_MAPPING` |
| 20 | Bjork-DK | Chargé sans Save | 3/3 | `NO_REPO_MAPPING` |
| 21 | Bjork-DK-extended | Chargé sans Save | 3/3 | `NO_REPO_MAPPING` |
| 22 | Bjork-Tiops | Chargé sans Save | 0/3 | `NO_REPO_MAPPING` |
| 23 | Bjork-Tiops (female-11) | Chargé sans Save | 0/3 | `NO_REPO_MAPPING` |
| 24 | Bjork-Tiops (male-12) | Chargé sans Save | 0/3 | `NO_REPO_MAPPING` |
| 25 | Burstone (female) | Chargé sans Save | 3/3 | `NO_REPO_MAPPING` |
| 26 | Burstone (male) | Chargé sans Save | 3/3 | `NO_REPO_MAPPING` |
| 27 | Downs | Chargé sans Save | 3/3 | `EXACT_NAMED_MAPPING_UNVERIFIED` |
| 28 | EAIO | Chargé sans Save | 0/3 | `NO_REPO_MAPPING` |
| 29 | Facad Mini | Chargé sans Save | 0/3 | `NO_REPO_MAPPING` |
| 30 | Geneve | Chargé sans Save | 0/3 | `NO_REPO_MAPPING` |
| 31 | HarmonyBox | Chargé sans Save | 0/3 | `NO_REPO_MAPPING` |
| 32 | Harvold | Chargé sans Save | 0/3 | `NO_REPO_MAPPING` |
| 33 | Hasund | Chargé sans Save | 3/3 | `NO_REPO_MAPPING` |
| 34 | Hasund regression | Chargé sans Save | 3/3 | `NO_REPO_MAPPING` |
| 35 | Holdaway Soft | Chargé sans Save | 3/3 | `NO_REPO_MAPPING` |
| 36 | Jarabak | Chargé sans Save | 3/3 | `NO_REPO_MAPPING` |
| 37 | Jefferson-Sassouni | Chargé sans Save | 0/3 | `NO_REPO_MAPPING` |
| 38 | Legan-Burstone Surgical | Chargé sans Save | 3/3 | `NO_REPO_MAPPING` |
| 39 | Mahony FFG | Chargé sans Save | 0/3 | `NO_REPO_MAPPING` |
| 40 | Mahony FFG + soft | Chargé sans Save | 3/3 | `NO_REPO_MAPPING` |
| 41 | McGann | Chargé sans Save | 0/3 | `NO_REPO_MAPPING` |
| 42 | McLaughlin | Chargé sans Save | 0/3 | `NO_REPO_MAPPING` |
| 43 | McNamara | Chargé sans Save | 3/3 | `EXACT_NAMED_MAPPING_UNVERIFIED` |
| 44 | Oslo | Chargé sans Save | 0/3 | `NO_REPO_MAPPING` |
| 45 | Oslo Surgical | Chargé sans Save | 3/3 | `NO_REPO_MAPPING` |
| 46 | Pancherz-post | Chargé sans Save | 3/3 | `NO_REPO_MAPPING` |
| 47 | Pancherz-pre | Chargé sans Save | 3/3 | `NO_REPO_MAPPING` |
| 48 | Photo AM Schwarz | Chargé sans Save | 0/3 | `NO_REPO_MAPPING` |
| 49 | Quadrilateral DiPaolo | Chargé sans Save | 0/3 | `NO_REPO_MAPPING` |
| 50 | Rakosi | Chargé sans Save | 0/3 | `NO_REPO_MAPPING` |
| 51 | Ricketts | Chargé sans Save | 3/3 | `NAME_ONLY_PROVISIONAL_PACK` |
| 52 | Ricketts (13 F) | Chargé sans Save | 3/3 | `RICKETTS_VENDOR_VARIANT_UNRESOLVED` |
| 53 | Ricketts (32 F) | Chargé sans Save | 3/3 | `RICKETTS_VENDOR_VARIANT_UNRESOLVED` |
| 54 | Ricketts acc G. Samson | Chargé sans Save | 3/3 | `RICKETTS_VENDOR_VARIANT_UNRESOLVED` |
| 55 | Ricketts Summary | Chargé sans Save | 3/3 | `RICKETTS_VENDOR_VARIANT_UNRESOLVED` |
| 56 | Roth-Jarabak | Chargé sans Save | 3/3 | `NO_REPO_MAPPING` |
| 57 | Sato Denture Frame | Chargé sans Save | 3/3 | `NO_REPO_MAPPING` |
| 58 | Sato Denture Frame mod Kim | Chargé sans Save | 3/3 | `NO_REPO_MAPPING` |
| 59 | Steiner | Observation partielle | 0/3 | `EXACT_NAMED_MAPPING_UNVERIFIED` |
| 60 | Trygde-analysen | Chargé sans Save | 3/3 | `NO_REPO_MAPPING` |
| 61 | Tubingen | Chargé sans Save | 0/3 | `NO_REPO_MAPPING` |
| 62 | Tweed | Chargé sans Save | 0/3 | `EXACT_NAMED_MAPPING_UNVERIFIED` |
| 63 | Wits appraisal | Chargé sans Save | 3/3 | `NO_REPO_MAPPING` |
| 64 | Wylie | Chargé sans Save | 0/3 | `NO_REPO_MAPPING` |
| 65 | Zurich | Chargé sans Save | 0/3 | `NO_REPO_MAPPING` |

## Exploration Robert, écran par écran : cible

Suivre le contrat préexistant `docs/audits/FACAD_314_FULL_APPLICATION_COVERAGE_CONTRACT.md` (**9 menus ; 30 commandes de barre d'outils observées**). Les tutoriels officiels [FACAD How-to](https://www.facad.com/wp/how-to-movies/) couvrent import DICOM, nouveau tracé, calibration, landmarks, simulations et superpositions ; leur présence n'est pas un résultat de notre essai.

Parcours avec `BEFORE → commande → AFTER → reset`, captures et état explicitement conservés :
1. Ouvrir l'exemple officiel Robert, vérifier la version, visualiser la liste patient/examens sans édition.
2. Entrer dans l'import DICOM, **inspecter puis annuler** sans envoyer/écrire de données réelles.
3. Observer les options de calibration (règle, mm/pixel, DPI, agrandissement) et leurs exigences.
4. Tracé : placement/correction de points, constructions, commandes de dessin, correction / undo **en mode lecture sans création persistante**.
5. Sélecteur d'analyse, mesures et normes : noms/version, colonne, scroll, offscreen ; ne sélectionner que dans des conditions sans écriture non contrôlée.
6. VTO et mouvements dento-osseux / tissus mous : inspecter modes et prévisualisation, **ne pas engager d'édition persistante** tant que D3 est ouvert.
7. Superposition et comparaison : identifier calage, transparence, couches et différences sans revendiquer de précision.
8. Rapports, sorties et exports : inventorier fenêtres, types et aperçu ; aucune impression réelle ni export de données cliniques.

**Journal obligatoire :** `feature_id | build | fixture | menu/control | enabled | risk | screenshot_before | action | screenshot_after | restore_proof | run_sha | result | uncertainty`. Une commande visible n'est pas `TESTED` ; seul un comportement AFTER et une restauration effectivement observés le sont.

## Gates et revues adversariales internes

- **Données A :** une lecture incorrecte « 65 validations / 65 CSV complets » est un BLOCKER de preuve. Corrigé dans cet inventaire : 65 états d'éditeur, seulement 42 triplets Git, aucune parité patient.
- **Clinique/sécurité B :** un alias `PFH` angulaire/linéaire, `PM'`/Pm ou l'activation de normes sans population, ainsi qu'une modification de l'exemple avec isolation non prouvée, seraient des BLOCKER. Aucun changement runtime ici.
- **Gates ouverts :** `ORTHO_ANALYSIS_PROTOCOLS_VERIFIED=OPEN` ; `FAC03_D3=OPEN_RED`, `SHARED_APP_STORAGE_ISOLATION=UNVERIFIED`, `CLINICAL_EDIT_ALLOWED=false`, `CONVERGED=false`. Pas de revue humaine indépendante ici.
- **Next :** récupérer 23 triplets avec preuves, construire des fiches page-citées C01/C02 sur Ricketts/Steiner/Tweed/McNamara puis exécuter des oracles synthétiques de géométrie et une exploration Robert réellement observée, chacun selon son gate.

**Ce document n'autorise ni merge, ni déploiement Vercel, ni validation scientifique/clinique.**
