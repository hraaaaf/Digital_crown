# CEPH J1.B1-S3 — Les 38 repères et équivalents FR/EN, sans fausse certification clinique

## Décision unique — avancer sur le lexique exhaustif

**GOAL :** rendre les 38 identifiants des sorties SRPose38 lisibles en céphalométrie française et internationale, confronter les synonymes aux sources peer-reviewed, figer les indices 0–37 / challenge 1–38 et le SHA, puis permettre les développements **hors diagnostic** (UI de revue manuelle, catalogue d'étiquettes, documentation, tests). Il ne s'agit PAS de certifier la précision de chaque canal ONNX sur un cliché ni d'activer l'inférence automatique. La science médicale ne découle pas d'une table de synonymes.

**SUCCESS** observable : `38/38` enregistrements sans doublon ni champ de nom vide, compatibilité complète avec `SOTA_LANDMARKS_MAPPING`, 7 associations directement numérotées par les organisateurs et conservées, 1 cas `Pos` de terminologie externe explicité, 30 autres indices sans lien numéroté vérifié dans la publication primaire consultée. Aucune mutation de modèle, interprétation diagnostique, dossier patient, stockage, pipeline ou moteur céphalo. Les tests rejettent un changement d'indice, une fausse preuve d'auteur, un alias `Pos` déclaré cliniquement certifié, une activation même sur un seul canal et une liste incomplète.

## Matrice exhaustive des équivalents

| Index ONNX 0–37 | N° challenge 1–38 | ID historique | Nom français | Nom anglais / terme de référence | Type de preuve du N° |
|---:|---:|---|---|---|---|
| 00 | 1 | `S` | Selle turcique | Sella | Lexique externe |
| 01 | 2 | `N` | Nasion | Nasion | Lexique externe |
| 02 | 3 | `Or` | Orbitale | Orbitale | Lexique externe |
| 03 | 4 | `Po` | Porion anatomique | Anatomical porion | Lexique externe · **convention nécessaire** |
| 04 | 5 | `A` | Point A (subspinale) | Subspinale / A-point | Auteur #5 |
| 05 | 6 | `B` | Point B (supramentale) | Supramentale / B-point | Lexique externe |
| 06 | 7 | `Pog` | Pogonion osseux | Bony pogonion | Lexique externe |
| 07 | 8 | `Me` | Menton osseux | Bony menton | Lexique externe |
| 08 | 9 | `Gn` | Gnathion osseux | Bony gnathion | Lexique externe |
| 09 | 10 | `Go` | Gonion / angle mandibulaire | Gonion | Auteur #10 · **convention nécessaire** |
| 10 | 11 | `L1_incisal` | Bord incisif de l’incisive mandibulaire | Lower central incisor incisal edge | Lexique externe |
| 11 | 12 | `U1_incisal` | Bord incisif de l’incisive maxillaire | Upper central incisor incisal edge | Lexique externe |
| 12 | 13 | `Ls_soft` | Labrale supérieur (lèvre supérieure) | Labrale superius / upper lip | Lexique externe |
| 13 | 14 | `Li_soft` | Labrale inférieur (lèvre inférieure) | Labrale inferius / lower lip | Lexique externe |
| 14 | 15 | `Sn_soft` | Subnasale | Subnasale | Lexique externe |
| 15 | 16 | `Pog_soft` | Pogonion cutané | Soft-tissue pogonion | « Pos » #16, équiv. lexicale |
| 16 | 17 | `PNS` | Épine nasale postérieure | Posterior nasal spine | Auteur #17 |
| 17 | 18 | `ANS` | Épine nasale antérieure | Anterior nasal spine | Lexique externe |
| 18 | 19 | `Ar` | Articulare | Articulare | Lexique externe |
| 19 | 20 | `D_point` | Point D (centre de la symphyse) | Point D (center of mandibular symphysis) | Lexique externe · **convention nécessaire** |
| 20 | 21 | `U1_apex` | Apex de l’incisive maxillaire | Upper central incisor root apex | Lexique externe |
| 21 | 22 | `L1_apex` | Apex de l’incisive mandibulaire | Lower central incisor root apex | Lexique externe |
| 22 | 23 | `Cm` | Columelle nasale | Columella | Lexique externe |
| 23 | 24 | `Ptm` | Fente ptérygomaxillaire | Pterygomaxillary fissure | Lexique externe · **convention nécessaire** |
| 24 | 25 | `Co` | Condylion | Condylion | Auteur #25 |
| 25 | 26 | `Prn` | Pronasale / pointe du nez | Pronasale | Auteur #26 |
| 26 | 27 | `Ba` | Basion | Basion | Auteur #27 |
| 27 | 28 | `PT_point` | Point ptérygoïdien (Pt de Ricketts) | Ricketts pterygoid point (Pt) | Lexique externe · **convention nécessaire** |
| 28 | 29 | `Bo` | Point de Bolton | Bolton point | Auteur #29 |
| 29 | 30 | `Ls2` | Point additionnel lèvre supérieure (UL′) | Additional upper lip point UL-prime | Lexique externe · **convention nécessaire** |
| 30 | 31 | `Li2` | Point additionnel lèvre inférieure (LL′) | Additional lower lip point LL-prime | Lexique externe · **convention nécessaire** |
| 31 | 32 | `Gn_soft` | Gnathion cutané | Soft-tissue gnathion | Lexique externe |
| 32 | 33 | `Me_soft` | Menton cutané | Soft-tissue menton | Lexique externe |
| 33 | 34 | `G_soft` | Glabelle cutanée | Soft-tissue glabella | Lexique externe |
| 34 | 35 | `N_soft` | Nasion cutané | Soft-tissue nasion | Lexique externe |
| 35 | 36 | `C_point` | Point cervical | Cervical point | Lexique externe |
| 36 | 37 | `U6` | Repère de la première molaire maxillaire | Upper first molar landmark | Lexique externe · **convention nécessaire** |
| 37 | 38 | `L6` | Repère de la première molaire mandibulaire | Lower first molar landmark | Lexique externe · **convention nécessaire** |

**Attention :** une « concordance auteur » prouve uniquement qu'une abréviation a été associée explicitement à un numéro dans le texte des organisateurs. Ce n'est **pas** une validation métrique, une preuve d'identité anatomique du checkpoint, ni une autorisation de diagnostics. Pour les 30 autres, nous avons seulement des équivalents lexicaux de la céphalométrie et la table historique Digital Crown, pas une table officielle confirmée 1..38.

## Arbitrage des alias délicats — aucune substitution silencieuse

- **#16 « Pos » / `Pog_soft`** : les auteurs du challenge écrivent « Pos (No. 16) » ; la publication indépendante de 2018 définit explicitement `Pos = soft tissue pogonion`. L'équivalence lexicale est documentée ; l'identité exacte du canal SRPose38 avec cet objet clinique n'est **pas** certifiée sans preuve appariée. Pas de `Pos → Pog_hard` (pogonion osseux).
- **#30 `Ls2` / « UL′ » et #31 `Li2` / « LL′ » :** variantes historiques de deuxième repère labial. **Ne pas les fusionner** avec les repères `Ls_soft` / `Li_soft` des indices 12 et 13 ; placement exact non explicitement défini par l'annotation source. Les libellés FR/EN ci-dessus restent volontairement *additionnels*, pas synonymes interchangeables.
- **#24 `Ptm` vs #28 `PT_point` :** la fente ptérygomaxillaire et le point ptérygoïdien de Ricketts ne sont pas dédupliqués ; convention géométrique du point exact exigée.
- **#4 `Po` :** porion **anatomique** et repère des ear rods non interchangeables. **#10 `Go`** : angle anatomique et gonion construit ne sont pas supposés interchangeables.
- **#37 `U6` / #38 `L6` :** usage clinique fréquent de la cuspide mésio-vestibulaire de première molaire, mais **la surface précise annotée par le challenge** n'est pas fixée par les seuls libellés `Upper Molar` / `Lower Molar` du contrat local. Le lexique n'ajoute donc pas de précision fictive.
- **#20 `D_point` :** centre de symphyse de Steiner ; le protocole précis de placement reste à documenter avant une norme d'analyse. **#32–35** repères cutanés distincts des osseux correspondants.

## Sources traçables, sans transfert abusif de numéro

- [Publication CL-Detection 2023 des organisateurs, arXiv v1](https://arxiv.org/html/2409.15834v1) — seuls sept couples `No. → abréviation` non équivoques sont retenus comme directement attestés : 5 A, 10 Go, 17 PNS, 25 Co, 26 Prn, 27 Ba et 29 Bo. Le n°16 apparaît comme `Pos`, avec interprétation lexicale ci-dessous.
- [Automatic Analysis of Lateral Cephalograms… (2018), Table 1](https://onlinelibrary.wiley.com/doi/10.1155/2018/1797502) — nomenclature indépendante, dont `Pos = Soft tissue pogonion`, `Ptm`, `Cm`, `Gn` cutané et autres.
- [StatPearls, Cephalometric Points, Table 1](https://www.ncbi.nlm.nih.gov/books/NBK594272/table/article-131913.table1/) et [dataset clinique Aariz, Table 4](https://www.nature.com/articles/s41597-025-05542-3) — définitions S, N, Po, Or, A, B, Gn, Co, bord incisif et apex. **Les numéros propres au dataset Aariz sont différents de ceux de CL-Detection2023 et ne sont jamais importés comme numéros du challenge.**
- [J Clin Med 2019 : points dentaires et tissus mous](https://www.mdpi.com/2077-0383/8/12/2106) et [Oxford, table de référence des points](https://academic.oup.com/view-large/426793504) — points cutanés, cervical, repères U6/L6, Pt distinct de Ptm.
- Source d'identité **logicielle** : `backend/services/srpose38_contract.py`, source checkpoint `5k5000/CLdetection2023@18d17d1934970016e7610c4849311900b8d1f191`, ONNX SHA-256 `a5ecd466d6d2c4ef02e145a143076a05720c0be56a260224812c23e2ecf42ddb`; [source-lock S1](CEPHALO_J1B1_S1_NUMERIC_SOURCE_LOCK_GATE.md) et [7 preuves auteur S2](CEPHALO_J1B1_S2_AUTHOR_PAPER_NUMBERED_EVIDENCE.md).

## Prochaine phase autorisée et phase encore bloquée

**Autorisée** : développer, à partir de cette table, un catalogue d'affichage/français, UI de revue et de correction **manuelles**, export de la nomenclature, validations de collisions et tests synthétiques hors clinique. Les alias automatiques unverified ne sont jamais promus pour les calculs canoniques.

**Bloquée** : qualification des 38 canaux automatiques comme vérités anatomiques, normes SNA/SNB/ANB et rapports de diagnostic basés sur SRPose, usage sur dossiers patients, installation, déploiement et merge sans preuves scientifiques / autorisations distinctes.

**Evidence gate pour décision ultérieure :** table officielle organisateurs liant les 38 catégories au même `train-gt.json`, puis étude sur radiographies légalement autorisées et annotations indépendantes (par repère MRE en mm, SDR@2 mm, calibrations, cas difficiles, cohérence inter-examinateurs). Aucune métrique d'autres modèles ne valide automatiquement `srpose38-tta-1024.onnx`.

**Statut : nomenclature 38/38 documentée ; validation clinique du checkpoint 0/38. NO_INSTALLABLE_GO / DRAFT / NO DEPLOY.** Fichier machine canonique : `docs/audits/CEPHALO_J1B1_S3_38_LANDMARK_TERMINOLOGY.json`.


## S3-CI post-fusion S4 — 2026-11-11 · correction du contrôle de périmètre (PR DRAFT)

La fusion déjà autorisée de [S4 #1286](https://github.com/hraaaaf/Digital_crown/pull/1286) dans la branche S3 a produit le commit `3f7941d72cd3080f7c7f986954748b3b433daec8`, **sans fusion dans master ni autorisation clinique**. Le [workflow S3 post-fusion #43002472070](https://github.com/hraaaaf/Digital_crown/actions/runs/43002472070) a alors refusé le diff S3+S4, car son contrat S3 initial demandait **exactement quatre chemins**, tandis que la branche en possède désormais **treize** : quatre fichiers S3 et neuf fichiers S4. Il s'agit d'un refus de contrat de périmètre devenu obsolète, **pas** d'une erreur scientifique du lexique démontrée.

**Goal et périmètre du correctif :** le workflow `.github/workflows/ceph-j1b1-s3-38-lexicon.yml` conserve l'ancrage immuable sur `f6985fa65cbcfa4f3c5dd7712864ca3ac1fade06` et le HEAD exact, puis exige l'égalité stricte des chemins avec les **4 S3 + 9 S4** attendus. Le test refuse une suppression, une injection backend, une substitution backend ou un doublon : **quatre scénarios négatifs obligatoires**. Sur les mêmes runners Linux/Windows, il exécute **les deux** garde-fous de provenance S3 et de lecture seule S4, avec les cinq et sept contrôles adversariaux déjà présents. Le changement est limité au contrat CI S3 et à ce document S3 existant ; ni code clinique, ni UI, ni poids modèle, ni base patients ne changent. L'échec post-fusion historique doit rester visible.

**Limites de preuve :** une CI verte sur une PR DRAFT de correction ne prouve pas la CI du HEAD futur de la branche parente S3 ; sa fusion nécessitera une autorisation séparée et un nouveau contrôle de tous les workflows après fusion. Le `Human Visual Approval` du HEAD fusionné S3 reste un gate distinct : la validation authentifiée de S4 `0a51d288...` n'est pas automatiquement transférable. Le workflow S4, lui aussi ancré sur son diff initial exact de neuf fichiers, devra être contrôlé sur tout nouveau HEAD S3 ; ne jamais contourner les vérifications. Toute certification de source anatomique SRPose38 et l'activation clinique demeurent `SOURCE_LOCK_REQUIRED` et `clinical_activation_authorized=false`.

**Success / Proof :** vérifier GitHub Actions Linux et Windows **sur le HEAD exact du correctif**, avec marqueurs `J1B1_S3_S4_FOUR_ADVERSARIAL_PATH_SCOPE_CASES_DENIED` et `J1B1_S3_S4_EXACT_HEAD_THIRTEEN_APPROVED_FILES_PASS`, puis provenance S3 et sécurité S4. Les numéros de runs et le verdict seront enregistrés une fois réellement disponibles ; aucun SUCCESS anticipé. **Pas de merge, déploiement, installateur ni patients réels.**
