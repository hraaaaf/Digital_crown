# LOT05 / J10K — GitHub Actions, vérification ONNX ↔ PyTorch D-FINE Nano COCO

**2026-10-22 · Recherche technique uniquement · Aucune radiographie ni donnée patient sur GitHub.**

## Pourquoi J10K

Le propriétaire a demandé de mener la suite des travaux de panoramique **entièrement sur GitHub Actions**. J10J PR #1021 a déjà prouvé **3/3 jobs SUCCESS** ([run #39825954519](https://github.com/hraaaaf/Digital_crown/actions/runs/39825954519)) : gate de licences, chargement du **D-FINE Nano COCO Apache 2.0** sur runner Ubuntu 24.04 et Windows Server 2025. SHA256 exact `19e06bdc873da819920a8d373b879721a5b9759d822f8213220bb09abbdab58b`, 80 classes COCO, 300 requêtes, 640², FPS non extrapolés. Durée CPU image artificielle : Ubuntu 0,124 s, Windows 0,178 s ; pas un benchmark clinique.

J10K doit vérifier la **représentation ONNX** du même checkpoint *corrigé*, et non convertir le vieux modèle en prétendant qu'il est identique. La version ONNX publique est [AnnotateIt/dfine-nano-coco-onnx](https://huggingface.co/AnnotateIt/dfine-nano-coco-onnx), annoncée Apache 2.0, dérivée du modèle officiel `ustc-community/dfine-nano-coco` à la révision fixée `066438d3d8f0da137a37b38fdf3368fd4afceced`, **modèle corrigé le 20 août 2025**. Attention : une ancienne conversion de ONNX Community était dérivée de poids plus vieux et ne pouvait pas prouver la parité sur la version courante.

## Chaîne de vérification CI autonome

`.github/workflows/lot05-j10k-dfine-onnx-parity.yml` — jobs déclenchés sur Draft PR :
1. `licensing-parity-preflight`, Linux : garde commerciale J10I toujours BLOQUÉ + tests négatifs sur SHA, mauvaise architecture, valeurs non finies, classes et dérives ONNX.
2. `cpu-onnx-parity` sur **ubuntu-24.04** et **windows-2025** : Torch 2.7.1 CPU, Transformers 4.57.3, ONNX Runtime 1.22.1, ONNX 1.18, provenance PyTorch modèle sous SHA ci-dessus. Source ONNX tierce vérifiée sur **fichier entier** :
   - `AnnotateIt/dfine-nano-coco-onnx/model.onnx` (origine indépendante, non modèle officiel), SHA256 **`b0ec2e5793f3a3cbd07440d098645a0e102cd450fb92f4f35e713f36e35d152e`**, taille 15 434 935 octets, FP32 opset 18, modèle 80 classes COCO. Le SHA du commit HuggingFace est résolu et consigné. Aucun poids chargé si digest incohérent.
   - Reconstruit le même dessin fictif J10J en RAM, en produit l'entrée 640×640 NCHW et calcule PyTorch et ONNX Runtime CPU. Vérifie les formes exactes `logits[1,300,80]` et `pred_boxes[1,300,4]`, l'absence NaN/Inf, les différences numériques maximales (limite logits 0,08, boîtes 0,02 coordonnées normalisées), et accord de classes argmax dans au moins 285/300 requêtes (95 %). Toute dérive = échec.
   - Artifacts GitHub Actions = **rapports JSON sans poids, sans images ni logits complets**. Aucune valeur médicale, aucune donnée patient. Ne pas conserver les modèles téléchargés entre runs, éviter les artefacts publics de checkpoint.

## Portée du PASS

Un succès signifie **parité numérique technique du backbone public COCO sur une illustration synthétique**, par machine native CPU. Il ne prouve ni entraînement de numérotation FDI, ni qualité sur vraie radiographie, ni licence du dataset d'entraînement FDI, ni validation ou usage clinique et ne livre aucun modèle en production. Un ONNX COCO ne devient jamais FDI 32 classes par simple conversion.

Le J10J approuvé par la CI, les recherches modèles/licences J10I, et le PDF panoramique textuel J10G/J10H restent inchangés. Dossiers patient non touchés, aucune image de radio dans le PDF, PR Draft/unmerged, V1.5 NO-GO.

Sources : [conversion indépendante ONNX et validation annoncée](https://huggingface.co/AnnotateIt/dfine-nano-coco-onnx) ; [poids corrigés source](https://huggingface.co/ustc-community/dfine-nano-coco/blob/main/model.safetensors). L'étude technique doit reproduire la comparaison elle-même et ne pas se fier aux résultats déclarés par l'auteur de la conversion.
