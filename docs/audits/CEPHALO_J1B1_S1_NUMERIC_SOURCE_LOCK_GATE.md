# J1.B1-S1 — Source-lock scientifique des 38 sorties SRPose38 (non clinique)

## Décision, risque, périmètre

L'export SRPose38 267 484 931 octets est déjà prouvé cryptographiquement sur Windows. **Cela ne valide ni les 38 noms anatomiques, ni le diagnostic.** Le challenge CL-Detection2023 représente les 38 cibles comme des catégories numériques et l'exacte configuration du checkpoint SRPose `5k5000/CLdetection2023@18d17d1934970016e7610c4849311900b8d1f191` utilise des `name: "0".."37"`. Les correspondances `0→S, 1→N, ...` du logiciel doivent être décrites comme hypothèses de compatibilité, jamais comme une table source officiellement prouvée.

**OBJECTIF / SUCCESS** : prouver automatiquement, sans patient ni modèle téléchargé, que le code, le registre scientifique et la table documentaire des 38 canaux correspondent exactement au format numérique attesté, tout en mettant les **38 correspondances anatomiques** en `SOURCE_LOCK_REQUIRED`. Invalider une source modifiée, un index manquant, une paire locale incohérente, ou une tentative de promouvoir le registre en validation/activation clinique.

## Sources et références exactes

- Source *amont directement utilisée pour l'entraînement* : [configuration MMPose du commit figé](https://github.com/5k5000/CLdetection2023/blob/18d17d1934970016e7610c4849311900b8d1f191/mmpose_package/mmpose/configs/_base_/datasets/cephalometric.py). Git blob SHA-1 exact **`82d4fffcc0c74736edc43a12110bed322b67e839`**, relu depuis GitHub pour cette investigation. Cette configuration possède 38 clés et libellés **NUMÉRIQUES** ; aucun champ `S`, `N`, `Po` ou définition anatomique.
- Source organisateur du benchmark : [CL-Detection2023, Grand Challenge](https://cl-detection2023.grand-challenge.org/) et [dataset Zenodo](https://zenodo.org/records/7787671) : 600 céphalogrammes, 38 landmarks ; l'accès au dataset est contractuel/avec inscription. **Aucune image de ce jeu n'est utilisée ici**.
- [Utilitaire source](https://github.com/5k5000/CLdetection2023/blob/18d17d1934970016e7610c4849311900b8d1f191/cldetection_utils.py) : les noms de catégorie du JSON d'annotations sont numérotés 1..38. Le lien arithmétique entre les indices de fichiers est vérifié, mais **le lien exact avec l'anatomie n'est pas démontré**.
- Contrat local : `backend/services/srpose38_contract.py`, 38 alias historiques; registre `backend/scientific_assets.json`; note corrective de base `docs/SRPOSE38_LANDMARK_CONTRACT.md` dans [PR #1276 DRAFT](https://github.com/hraaaaf/Digital_crown/pull/1276).

## Contrat machine-checkable

`scripts/ci/ceph_j1b1_srpose_source_lock.py` :

1. Télécharge uniquement **3,7 Ko de code source public** d'un commit Git exact ; vérifie l'identité du **blob Git SHA-1** avant de parser AST, puis confirme 38 identifiants `0..37` aux noms numériques égaux à leurs indices. Refuse la source inaccessible (fail-closed).
2. Relit par AST sans importer l'application `SOTA_LANDMARKS_MAPPING` et les constantes PIN (modèle/nom/taille), et confronte les 38 index aux 38 lignes du tableau de compatibilité documentaire, avec numéros de challenge 1..38.
3. Rejette un registre sans `anatomical_mapping_validation=SOURCE_LOCK_REQUIRED` ou avec `clinical_activation_authorized != false`. Reformule la `note` du registre initialement trompeuse « validated 38-point » en **intégrité numérique vérifiée / anatomie NON vérifiée**.
4. Tests négatifs : source falsifiée identifiée par SHA incorrect ; source à un seul point rejetée même quand on lui donne volontairement un hash cohérent.
5. Produit **uniquement** un JSON de métadonnées contenant les 38 indices, leurs libellés numériques upstream et les anciens alias logiciels **explicitement non attestés**. `number_of_anatomical_mappings_source_verified=0` indique le nombre de correspondances établies dans **les sources vérifiées ici**, et non une démonstration que les alias historiques sont tous erronés. Aucun contenu patient, aucune matrice de pixels, aucune ONNX, aucune inférence ni clé clinique.

## Effets et limites

- Le changement de `backend/scientific_assets.json` modifie le digest du registre pour cette branche. **Il ne re-certifie pas une release existante** ; une future certification du commit exact exige toutes les signatures/manifestes et gates ordinaires.
- Il ne renomme aucun point ni migration et ne modifie aucun calcul. L'autorisation clinique existante demeure **NON**. La PR J1.B1 applicative [#1277](https://github.com/hraaaaf/Digital_crown/pull/1277) sur les alias canoniques est distincte et encore DRAFT ; ne pas fusionner ce lot documentaire seul en prétendant avoir sécurisé tous les consommateurs.
- Aucune conclusion clinique sur une image du patient, aucun seuil d'exactitude par landmark, aucune concordance avec annotations expert, aucune source officielle table `index→structure` du checkpoint exact prouvée par cette CI.
- **HUMAN GATE** : obtenir la définition officielle numérotée rattachée au même jeu d'annotations et une étude sur clichés appariés autorisés avec lecture indépendante et évaluation en millimètres et par landmark, puis revue médicale ; seulement alors envisager la sortie du HOLD.

Statut initial : protocole défini, la CI exacte-HEAD doit encore exécuter et prouver les assertions. **NO MERGE, NO DEPLOY, NO PATIENT, NO INSTALLER**.
