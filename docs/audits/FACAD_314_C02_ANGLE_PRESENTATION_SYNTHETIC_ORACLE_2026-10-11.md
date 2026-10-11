# FACAD 3.14 — C02 : règle de présentation angulaire et contrat d'oracles synthétiques

**2026-10-11. STATUT : RESEARCH-ONLY · NOT CLINICALLY VERIFIED · C02 PDF CONTENT NOT ACQUIRED.** Branche documentaire de PR #829. Aucune action sur l'application Facad de Robert, aucune interaction patient, aucune modification de code produit, aucune livraison clinique.

## Résultat nouveau — règle contrôlable depuis les sources éditeur

**Source primaire officielle accessible (pas le PDF C02) :** `Facad 3.14 Reference Manual`, chapitre 12 « The Analysis Editor », **page imprimée 85**, rubrique « Cephalometric properties », entrée « Angle Presentation ». Référence fabricante : https://www.facad.com/dox/dox314/FacadRefMan.pdf . Le texte de la page est accessible par extrait indexé ; le PDF complet n'a pas été relu visuellement dans cette étape.

**Contre-source primaire officielle, datée et récupérable :** Ilexis, `Facad Tracing Release Notes 3.12.1`, édition du **2020-10-05**, **page imprimée 1 sur 6**, paragraphe 2.2 (source https://www.facad.com/dox/dox312/FacadTracingReleaseNotes_3.12.pdf). Cet exemplaire **confirme indépendamment dans une édition antérieure du fabricant** la règle de sélection automatique. Pas une seconde étude indépendante.

**Sélecteur documenté, distinct de la fonction mathématique qui calcule l'angle :**

| Configuration | Rendu de l'angle |
|---|---|
| « Angle Presentation » = `Auto`, pas de `Norm` | `0–360°` |
| `Auto`, **borne supérieure** de l'intervalle `Norm` strictement **<135°** | `±180°` |
| `Auto`, borne supérieure **≥135°** | `0–360°` |
| Sélection manuelle `±180°` ou `0–360°` | La plage choisie manuellement |

La propriété « Change sign » du même formulaire renvoie à la documentation d'opérateurs de **distance à la ligne** ; son fonctionnement concret n'est pas établi par ce seul renvoi. En conséquence il faut également auditer les distances signées, et ne pas extrapoler le signe de tous les opérateurs.

**Attention clinique et science :** la norme littérale dans l'éditeur, même si elle influence le **format d'affichage**, ne devient pas une norme de référence validée pour Digital Crown. La documentation fabricant n'établit pas ici l'ordre des vecteurs, la convention signée aux bornes `±180°`, ni les valeurs du moteur calculateur.

## Accès réel à C02 — succès inventaire, blocage sur pages sources

Le [run d'inventaire d'installation #37981554220](https://github.com/hraaaaf/Digital_crown/actions/runs/37981554220) a été **retéléchargé** via l'artefact GitHub **#11642105521**, non expiré. Son ZIP contient uniquement les quatre pièces `installed-manuals-index.json`, `quick-demo-process.txt`, `installed-manual-status.txt`, `consent-gate.txt`. **Aucun PDF C01/C02 n'est contenu dans cet artefact.**

La ligne JSON C02 décrit :
- chemin relatif fabricant `Program/Doc/Cephalometry/C_Cephalometry Library/C02_Lateral Cephalometry Library - Measurements.pdf` ;
- **5 718 901 octets**, **34 pages**, SHA256 **`4dbd3fa8419b684529fcbc17f615f49f7486cdf037fcfff025b1b307c0c0a548`** ;
- `VENDOR_ARCHIVE_PDF_METADATA_ONLY` et `clinical_equivalence_certified=false` ;
- `keyword_page_locations_1based={}` (aucune localisation d'opérateur dans cet index, pas démonstration de leur absence).

Le poste Windows autorisé `DESKTOP-3MAJEEH` est **OFFLINE** à la vérification de cette étape. Les pages C02 restent **NOT_ACQUIRED** et leurs définitions précises **NOT_VERIFIED** ; ne pas générer de citations p.X imaginaires. Le manuel de référence 3.14 est une preuve **de comportement UI/conventions de rendu**, pas un remplacement du PDF C02.

## Banc de géométrie synthétique local : 30/30 tests passés, frontière de preuve stricte

Banc standard Python `facad_c02_synthetic_geometry_contract.py` **exécuté localement dans cette conversation** : `python /mnt/data/facad_c02_synthetic_geometry_contract.py -v`. Résultat observé : **`Ran 30 tests ... OK`**, exit code **0**, SHA256 script **`fd8b3aee737614f9a8b67cccf71aced182ea7a356365eb1d3dcb5cca57e3320f`**, SHA256 journal **`4d8b2fc303b9d98ab5fde06e50b9296ea2b8bbcdf8d0149d6886a46bce44077b`**. **Attention** : le script et son journal existent seulement comme artefacts de conversation locaux et **ne sont pas encore versionnés dans Git**, donc le rapport documente un résultat exécuté mais ne fournit pas encore le test source Git clonable. Ne pas inférer « 30/30 tests FACAD ». Le banc n'importe pas le code Digital Crown ni les bibliothèques patient.

Vérifications réalisées dans le script :
- Sélecteur **source-documenté** Auto : bornes 134,99 et 135, absence de norme, override manuel, entrées NaN/options inconnues refusées ;
- Oracles **mathématiques candidats indépendants** et explicitement *non équivalents FACAD jusqu'à preuve* : normalisation en plages, inversion d'ordre des vecteurs, angles directs obtus, distance euclidienne avec calibration mm/pixel, translation/rotation invariantes, projection signée et direction inversée, géométries dégénérées, intersection de lignes ;
- Contre-exemples **fail-closed** : `PM'=Intersect(Xi,PM,A,Pog)` synthétique différent de `PM` ; plans `ML` contextuels Steiner `Go–Gn` vs Tweed `Go–Me` ; `Max-Mand diff=Sub(Co-Gn,Co-A)` exige des valeurs résolues en unités compatibles ; aucune valeur par défaut si dépendance absente.

### Vecteurs synthétiques vérifiés (AUCUN PATIENT)

| Test candidat / illustration | Entrée synthétique | Sortie banc | Statut FACAD propriétaire |
|---|---|---|---|
| Règle Auto | borne Norm `134.99°` | `±180°` | **Documenté fabricant** |
| Règle Auto au seuil | borne Norm `135°` | `0–360°` | **Documenté fabricant** |
| Distance calibrée | A `(0,0)`, B `(3,4)`, 0.5 mm/pixel | `2.5 mm` | **Non testé contre Facad** |
| Ordre des vecteurs | u `(1,0)`, v `(0,1)` | angle candidat `+90°` puis `-90°` si inversé | **Orientation Facad non certifiée** |
| PM' construit | Xi `(0,0)`, PM `(10,0)`, A `(5,-5)`, Pog `(5,5)` | `Xi–PM'=5`, `Xi–PM=10` | **Identité interdite** |
| Plan mandibulaire | Go `(0,0)`, Gn `(4,0)`, Me `(4,3)` | `ML` Steiner ≠ `ML` Tweed | **Différence de lignes source UIA** |
| Longueurs McNamara | Co–Gn `112 mm`, Co–A `84 mm` | différence candidate `28 mm` | **Source dépendances, exécution Facad non testée** |
| Input absent | Co–Gn absent | `NOT_COMPUTABLE` | **Proposition fail-closed Digital Crown** |

**Important :** le résultat `+180°→−180°` du normaliseur candidat `[-180°,180°)` n'est pas démontré conforme à la règle du fabricant ; le choix de borne exacte doit être traité séparément dans une campagne de parité numérique.

## Revue adversariale interne (deux perspectives ; pas revue humaine)

**A — Science :** l'alternative de plage documentaire est une preuve du **rendu**, non de la valeur brute ni de la géométrie. 30 tests du banc ne prouvent aucune exécution de Facad ni Digital Crown. C02 34 pages reste non acquis, donc les familles `Angle2ln`, `Angle3p`, `Angle4p`, `DistLine`, `ProjLine`, `Proj90Line`, `Dist3p` demeurent `DEFINITION_NOT_VERIFIED`. **BLOCKER scientifique non résolu.**

**B — Assurance qualité/sécurité :** aucun nouveau workflow Windows/donnée patient, aucune modification moteur, aucune activation de normes. Les assertions impossibles à prouver ont des libellés distincts ; l'ancien run d'inventaire n'est pas présenté comme contenant le PDF. **BLOCKER de reproductibilité :** copier le code et journal du banc dans un emplacement pérenne (après revue de licence et de source) ; ajouter des assertions LOT06 seulement quand l'interface runtime est identifiée et testée, sans spéculer.

## GO/NO-GO

- `DOCUMENTED_ANGLE_AUTO_PRESENTATION=SUPPORTED_BY_VENDOR_MANUAL_AND_RELEASE_NOTES`.
- `SYNTHETIC_ORACLE_SELF_TEST=30_OF_30_OK_LOCAL_ONLY`.
- `C02_OFFICIAL_OPERATOR_PAGE_PROVENANCE=NOT_ACQUIRED`.
- `FACAD_VS_DIGITAL_CROWN_NUMERIC_PARITY=NOT_TESTED`.
- `FAC03_D3=OPEN_RED`, `SHARED_APP_STORAGE_ISOLATION=UNVERIFIED`, `CLINICAL_EDIT_ALLOWED=false`, `CONVERGED=false`.

**Next action réelle :** récupérer, dans un cadre autorisé et hors données patient, le document C02 original ou de courts extraits sourcés par page depuis l'installation sur poste isolé ; versionner le banc source indépendant ; tester d'abord le rendu Auto aux bornes 134,99°/135° puis signer les projections et comparer les valeurs du runtime LOT06 avec des oracles non cliniques avant toute revendication de parité. Ne pas fusionner ni déployer sur la base de cette étape.