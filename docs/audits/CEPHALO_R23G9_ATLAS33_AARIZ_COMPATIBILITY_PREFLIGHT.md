# CEPH-UXCLIN-01 — R23-G9 — Atlas33 / Aariz : inventaire de compatibilité source

**2026-10-17 · Audit documentaire READ-ONLY · Clinique NO-GO · Desktop uniquement**

## Découverte et méthode

Le corpus public Aariz, déjà qualifié par Digital Crown LOT02, **existe** : 1 000 céphalogrammes, 29 repères annotés, sept appareils, splits gelés 700/150/150 et qualification QC traçable par SHA. C'est une référence valable **dans son périmètre LOT02**, pas une validation automatique des 33 facteurs Atlas 2009. Source originale : [Aariz Scientific Data 2025](https://doi.org/10.1038/s41597-025-05542-3) ; [Figshare CC BY 4.0](https://doi.org/10.6084/m9.figshare.27986417.v1). Junior et senior sont des agrégats de groupes, et non deux fichiers d'annotation individuelle indépendante.

Le rapprochement ci-dessous est **littéral seulement**, construit à partir de la liste de 24 identités candidates dans `docs/audits/CEPHALO_VNEXT_LOT02_PUBLIC_GOLDSET_AUDIT.md` et des contrats exacts LOT06/G7/W1/W2/W3 au HEAD parent `d86d2963e3b31e6cacc2b77838f93d509460dfd1`. Il inclut les repères indirects disponibles dans les contrats de construction. Une présence littérale n'est **jamais une équivalence anatomique, un calcul valide ni une autorisation de Focus**.

- **33/33** lignes source inventoriées : LOT06 8 + G7 3 + W1 4 + W2 7 + W3 11.
- **21** identités distinctes de repères nécessaires sont absentes du mapping littéral Aariz (surtout `Po_anatomic`, `Pog_hard`, `Pt_Ricketts`, `PR_Ricketts_PTV`, `Pm_Ricketts`, R1–R4, FOP, dents distales et canines source-spécifiques).
- **1/33** facteur (#6, `M_INTERINCISAL_DEG_V1`) dispose de tous les libellés candidats dans cet inventaire. Ce n'est **pas une validation clinique**.
- Les déclarations de construction des groupes réunis ne donnent pas encore tous les `upstream` des constructions citées par les facteurs #20 (`RICKETTS_GN_CONSTRUCTED_NPOG_GOME_V1`) et #22 (`FH_PO_OR_V1`). Les repères directs existent dans les contrats; cette limite concerne l'agrégation documentaire, et ne prétend pas que le constructeur backend manque.
- **0/33** mesures sont validées cliniquement par G9 ; aucune valeur, norme, prédiction, diagnostic ou repère sur patient n'a été généré.

Les deux images publiques de la capture G4 (ANUG et Challiyan) ont des points synthétiques non enregistrés sur l'anatomie, et n'établissent pas une calibration ou un goldset de 33 facteurs. Le statut LOT02 `CEPH_GOLDSET_READY` ne devient pas `ATLAS33_CLINICAL_READY`.

## Matrice brute de compatibilité par facteur

| Atlas # | Origine des dépendances | N identités sans correspondance littérale | Exemples / liste des identités manquantes |
|---:|---|---:|---|
| 1 | W2 | 4 | `FOP_MOLAR_Ricketts`, `FOP_PREMOLAR_Ricketts`, `L6_DISTAL_Ricketts`, `U6_DISTAL_Ricketts` |
| 2 | W2 | 4 | `FOP_MOLAR_Ricketts`, `FOP_PREMOLAR_Ricketts`, `L3_CUSP_Ricketts`, `U3_CUSP_Ricketts` |
| 3 | W2 | 2 | `FOP_MOLAR_Ricketts`, `FOP_PREMOLAR_Ricketts` |
| 4 | W1 | 2 | `FOP_MOLAR_Ricketts`, `FOP_PREMOLAR_Ricketts` |
| 5 | W2 | 2 | `FOP_MOLAR_Ricketts`, `FOP_PREMOLAR_Ricketts` |
| 6 | LOT06 | 0 | Aucun manque littéral ≠ GO clinique |
| 7 | LOT06 | 2 | `Po_anatomic`, `Pog_hard` |
| 8 | W3 | 6 | `Pm_Ricketts`, `Po_anatomic`, `R1_Ricketts`, `R2_Ricketts`, `R3_Ricketts`, `R4_Ricketts` |
| 9 | W2 | 3 | `PR_Ricketts_PTV`, `Po_anatomic`, `U6_DISTAL_Ricketts` |
| 10 | LOT06 | 2 | `Po_anatomic`, `Pog_hard` |
| 11 | G7 | 2 | `Po_anatomic`, `Pog_hard` |
| 12 | LOT06 | 1 | `Pog_hard` |
| 13 | G7 | 1 | `Pog_hard` |
| 14 | W1 | 7 | `FOP_MOLAR_Ricketts`, `FOP_PREMOLAR_Ricketts`, `Po_anatomic`, `R1_Ricketts`, `R2_Ricketts`, `R3_Ricketts`, `R4_Ricketts` |
| 15 | W2 | 8 | `FOP_MOLAR_Ricketts`, `FOP_PREMOLAR_Ricketts`, `Pm_Ricketts`, `Po_anatomic`, `R1_Ricketts`, `R2_Ricketts`, `R3_Ricketts`, `R4_Ricketts` |
| 16 | LOT06 | 1 | `Po_anatomic` |
| 17 | W2 | 1 | `LABIAL_COMMISSURE_Ricketts` |
| 18 | W1 | 3 | `FOP_MOLAR_Ricketts`, `FOP_PREMOLAR_Ricketts`, `LABIAL_COMMISSURE_Ricketts` |
| 19 | LOT06 | 2 | `Po_anatomic`, `Pog_hard` |
| 20 | LOT06 | 3 | `Ba`, `Pog_hard`, `Pt_Ricketts` |
| 21 | W3 | 2 | `MP_ANGLE_INFERIOR_Ricketts`, `Pog_hard` |
| 22 | LOT06 | 1 | `Po_anatomic` |
| 23 | W3 | 2 | `PR_Ricketts_PTV`, `Po_anatomic` |
| 24 | W1 | 2 | `PNS_Ricketts`, `Po_anatomic` |
| 25 | W3 | 2 | `MP_ANGLE_INFERIOR_Ricketts`, `Po_anatomic` |
| 26 | G7 | 2 | `Ba`, `Po_anatomic` |
| 27 | W3 | 3 | `Ba`, `Pog_hard`, `Pt_Ricketts` |
| 28 | W3 | 3 | `GO_Ricketts_PFH`, `PR_Ricketts_PTV`, `Po_anatomic` |
| 29 | W3 | 7 | `Ba`, `Pm_Ricketts`, `Po_anatomic`, `R1_Ricketts`, `R2_Ricketts`, `R3_Ricketts`, `R4_Ricketts` |
| 30 | W3 | 6 | `PR_Ricketts_PTV`, `Po_anatomic`, `R1_Ricketts`, `R2_Ricketts`, `R3_Ricketts`, `R4_Ricketts` |
| 31 | W3 | 2 | `PR_Ricketts_PTV`, `Po_anatomic` |
| 32 | W3 | 7 | `DC_Ricketts`, `Pm_Ricketts`, `Po_anatomic`, `R1_Ricketts`, `R2_Ricketts`, `R3_Ricketts`, `R4_Ricketts` |
| 33 | W3 | 6 | `Pm_Ricketts`, `Po_anatomic`, `R1_Ricketts`, `R2_Ricketts`, `R3_Ricketts`, `R4_Ricketts` |

La trace machine est le fichier versionné [JSON G9](../schemas/cephalo_r23g9_atlas33_aariz_compatibility_preflight_v1.json). Aucune image ou donnée patient n'entre dans ce document ou ce JSON.

## Gates réels restant ouverts

1. Matérialiser dans un environnement protégé le corpus/hashes LOT02 existants et définir les cas d'acceptation indépendants de l'entraînement et du réglage des modèles ; ne pas copier de données de patient dans GitHub, CI, Notion ou artefacts publics.
2. Faire annoter sur **les mêmes images** les identités Ricketts manquantes par des orthodontistes qualifiés indépendants, avec protocole de repérage et de désaccord/adjudication préenregistré. Les noms voisins ne sont pas des alias.
3. Recueillir orientation anatomique, miroir, origine, provenance de calibration mm/pixel et validations manuelles exactes (date/réviseur/source). Définir des critères **par repère/par facteur** avant examen des résultats, sans transposer automatiquement les seuils de sélection de détecteur LOT04.
4. Exécuter ensuite une comparaison de valeurs et signes sur images réelles via le **backend versionné** et un oracle indépendant, y compris cas négatifs, taux `NOT_COMPUTABLE`, biais, limites d'accord, erreurs angulaires/linéaires et répétabilité intra/inter-observateur.
5. Deux perspectives de revue réellement indépendantes + confirmation au même HEAD, gate humain clinique explicite et décision de release **distincte**. Pas de merge ni Vercel sans permission expresse.

**Important :** cet audit a recalculé une matrice à partir des schémas source et effectué des assertions de cardinalité/exclusivité/cohérence. Il ne constitue ni des tests Python/React nouveaux, ni une revue externe, ni une exécution sur radiographie. Les actions CI de W3 restent attachées au HEAD parent, non au nouveau commit G9. **Clinical NO-GO**.

**Roadmap :** G2/G7/W1/W2/W3 descriptions ✓ → G9 cartographie documentaire ✓ → collecte/annotation indépendantes BLOCKED → validation même-image → revue externe → gate clinique / closeout.
