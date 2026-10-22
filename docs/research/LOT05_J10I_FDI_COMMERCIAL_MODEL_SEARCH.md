# LOT05/J10I — Recherche de modèles FDI à droits commerciaux vérifiables (22 octobre 2026)

**Décision propriétaire** : Digital Crown est un logiciel Windows propriétaire et commercial. Une solution qui demande une licence commerciale négociée individuellement, ou une ouverture du code entier, ne remplit pas l'objectif demandé. Ne jamais commercialiser ou entraîner sur un matériau dont les droits sont douteux. La validation fonctionnelle du **bilan PDF écrit sans image** J10H est indépendante et acquise.

**Verdict au 22/10/2026 : aucun checkpoint FDI préentraîné découvert n'est simultanément (a) autorisé commercialement avec toute sa chaîne de droits, (b) de provenance vérifiable, (c) fonctionnellement robuste pour 32 classes FDI et (d) validé pour Digital Crown sous Windows. COMMERCIAL HOLD et CLINICAL NO-GO.**

## Sources premières et audit des candidats

### Préentraînés FDI : pas encore admissibles à une distribution commerciale propriétaire

| Checkpoint | Licence affichée | Observation d'audit | Décision |
|---|---|---|---|
| [miquic/app-odonto-fdi-yolov8s](https://huggingface.co/miquic/app-odonto-fdi-yolov8s) | CC BY-NC-SA 4.0 | Licence « NC » incompatible avec la vente ; résultats indépendants Digital Crown 840/1036 dents correctes et 3/40 panoramiques intégralement correctes | BLOQUÉ |
| [Kölüş & Güleç — poids YOLO FDI sur Mendeley, DOI 10.17632/83k2rtz4bc.1](https://data.mendeley.com/datasets/83k2rtz4bc/1) | CC BY 4.0 indiqué sur le dépôt de poids | Licence favorable en elle-même, mais YOLOv5/8/11 produits avec Ultralytics ; [l'éditeur Ultralytics](https://www.ultralytics.com/license) déclare que les modèles entraînés avec sa stack sont AGPL-3.0 par défaut et exigent une Enterprise Licence si l'application reste propriétaire ; provenance des images/poids non auditée indépendamment. Une licence du déposant ne remplace pas automatiquement les droits des composants tiers. | BLOQUÉ dans Digital Crown propriétaire |
| [Mobe1 — argos-dentsight-stage1-fdi-v1](https://huggingface.co/Mobe1/argos-dentsight-stage1-fdi-v1) | Apache 2.0 en métadonnées, mais licence finale de projet « open » dans sa carte | D-FINE entraîné sur corpus Roboflow privé ; échec déclaré du classifieur FDI : au seuil 0,30, mAP50=0,000 ; mAP50=0,744 est calculée au seuil 0,000 (classement seulement). Reconnaissance des quadrants : 16/32 seulement. | BLOQUÉ techniquement et droits |
| [Garry2k2 Tooth Detection](https://github.com/Garry2k2/Tooth-Detection) | README affiche un badge MIT, mais LICENSE racine inaccessible | Dépendance Ultralytics AGPL, données OralVis propriétaires, poids et droits non prouvés ; performances 99 % auto-déclarées sans validation indépendante | BLOQUÉ |
| [abychkov/dental-fdi-detection](https://huggingface.co/abychkov/dental-fdi-detection) | Licence « other », NOTICE propriétaire | Mention expresse « non-commercial only » et interdiction de redistribution. | BLOQUÉ (non inclus dans la matrice de tests) |

### Architectures de départ pertinentes : poids permissifs, mais PAS de capacité FDI avant entraînement

1. **Premier choix d'investigation : [ustc-community/dfine-nano-coco](https://huggingface.co/ustc-community/dfine-nano-coco)** : poids COCO sous **Apache 2.0**, 3,8 millions de paramètres, **15,3 Mo** (révision publique [`066438d3d8f0da137a37b38fdf3368fd4afceced`](https://huggingface.co/ustc-community/dfine-nano-coco/tree/066438d3d8f0da137a37b38fdf3368fd4afceced) ; SHA-256 annoncé [sur la page poids](https://huggingface.co/ustc-community/dfine-nano-coco/blob/main/model.safetensors) : `19e06bdc873da819920a8d373b879721a5b9759d822f8213220bb09abbdab58b`). Potentiellement convenable pour un client Windows CPU : **pas encore testé localement ni entraîné pour les dents**.
2. **Comparateur : [PekingU/rtdetr_v2_r18vd](https://huggingface.co/PekingU/rtdetr_v2_r18vd)** : base COCO **Apache 2.0**, **80,9 Mo**. Plus lourde, architecture RT-DETRv2 sur Hugging Face Transformers. Aucune prédiction FDI attendue sans fine-tuning.
3. **Autre comparateur : [ustc-community/dfine-small-coco](https://huggingface.co/ustc-community/dfine-small-coco)** : base COCO Apache 2.0, **41,5 Mo**. Option si Nano échoue à la détection des dents après entraînement.
4. Ancien [PekingU/rtdetr_v2_r101vd](https://huggingface.co/PekingU/rtdetr_v2_r101vd) : COCO Apache 2.0, **307 Mo**, moins prioritaire pour Windows CPU.

Les licences de ces poids de départ et l'utilisation via Transformers ne valent pas autorisation d'utiliser **n'importe quelle nouvelle donnée clinique**. Les futurs poids FDI auront une provenance (dataset + architecture + données + droits) propre à documenter.

### Jeux de données / droit sur les radiographies

- **Piste FDI 32 classes : [Roboflow dentalxray — Panoramic-Dental-Xray-FDI](https://universe.roboflow.com/dentalxray-yjztn/panoramic-dental-xray-fdi)** : **1 577 images**, **32 numéros FDI** listés 11–48, **CC BY 4.0 indiquée**. Cependant le propriétaire de ce corpus ne décrit PAS la provenance clinique, ni la chaîne des droits de diffusion des radios, les consentements ou les conditions des contributeurs. **Seul le catalogue public est vérifié**. Avant toute formation de modèle *destiné à la vente*, preuve de provenance et de permission de réutilisation requises.
- Une [copie Roboflow « s Workspace »](https://universe.roboflow.com/s-workspace-pw73p/panoramic-dental-xray-fdi-8vaz4) affiche exactement **1 577 images** et 32 classes. Risque de duplication/dérivation de corpus à examiner pour éviter de compter deux fois les mêmes données.
- **[DENTEX Zenodo](https://zenodo.org/records/7812323)** : benchmark scientifique important mais licences rapportées divergentes : [inventaire scientifique indépendant Uribe et al.](https://journals.sagepub.com/doi/full/10.1177/00220345241272052) indique « no license specified » tandis qu'un [fork GitHub](https://github.com/DShomin/DENTEX-1) annonce CC BY-SA 4.0. Résoudre directement auprès de la source juridique de la release avant commercial. Aucune fusion automatique de variantes de licence.
- **[InReDD PAN924/PhysioNet](https://physionet.org/content/inredd-dataset-pan924/1.0.0/)** : **924 OPG et 32 classes FDI**, mais l'accès est conditionné à utilisateur accrédité, DUA et approbation de l'étude par les auteurs. **Ne respecte pas la demande « sans demander les droits »**.
- **[Orthopantomogram teeth segmentation and numbering / Zenodo](https://zenodo.org/records/10538750)** : 250 OPG, papier en CC BY-NC, licence précise des données non établie sur Zenodo ; HOLD.

## Implémentation durable du sous-lot

- `docs/research/LOT05_J10I_FDI_COMMERCIAL_CANDIDATES.json` : inventaire structuré des statuts commerciaux/techniques, sources et limites, *zéro checkpoint autorisé en production*.
- `experiments/lot05_j10i_fdi_commercial_rights_gate.py` : vérification indépendante de **licence du modèle, runtime, provenance, existence des preuves et autorisation**, et des chemins du produit qui pourraient contenir des poids FDI non autorisés. Le programme refuse par construction d'approuver une distribution sur la simple base d'un catalogue éditable. Même une licence « MIT » dans un README ne suffit pas.
- `experiments/test_lot05_j10i_fdi_commercial_rights_gate.py` : tests négatifs : faux GO, faux droits, un modèle COCO présenté comme FDI 32 classes, source `file://`, artefact ONNX ajouté au répertoire client, catalogue incomplet.
- CI Linux/Windows **sans images patients, sans téléchargement de poids, sans modèle en production**. Les tests marqués PASS signifient uniquement : **garde-fous de sélection et journal de preuve valides ; PAS licence commerciale homologuée**.

## Étape technique J10J envisagée (nouvelle autorisation séparée)

1. **Établir la provenance du dataset CC BY 4.0 réellement utilisable**, ses droits de création/redistribution, hachages, versions, exclusions. Si impossible, acquérir ou créer un autre jeu d'entraînement dont les autorisations sont explicitement documentées.
2. Isoler et vérifier un checkpoint de base Apache 2.0 `D-FINE Nano COCO` dans un environnement de **recherche**, sans radios de patients. Benchmarker son runtime Windows CPU/ONNX, uniquement technique.
3. Entraîner les **32 classes FDI**, sans diagnostic ni traitements, avec splits par patient/source, jeu externe jamais vu à l'entraînement, contrôle des erreurs sur dents absentes, inversions gauche/droite, implants, formes anatomiques, distances entre dents et rapports entre quadrants. N'utiliser la numérotation que comme **proposition à corriger et confirmer** par le praticien.
4. Redémontrer toutes les limites qualitatives, droits des poids et des dépendances de livraison. Ne produire aucun « GO clinique » sur la seule base de mAP ou de parité ONNX ; revue réglementaire et validation radiologique indépendante demeurent indispensables.

**Décision du sous-lot J10I : recherche de chaîne permissive structurée ; modèle commercial READY = **aucun**. PDF panoramique textuel J10H inchangé et validé par le propriétaire. Toutes PR expérimentales toujours Draft. Aucun merge/déploiement/données patient.**
