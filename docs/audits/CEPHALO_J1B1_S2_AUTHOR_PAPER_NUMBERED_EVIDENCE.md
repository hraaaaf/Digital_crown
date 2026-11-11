# CEPH J1.B1-S2 — 7 associations numérotées d'auteurs, PAS une validation des 38 sorties

## Décision / GOAL / SUCCESS / PROOF

**Décision unique :** ne plus considérer que la seule configuration MMPose « `name=0..37` » décrit toute la preuve publique disponible. Lire la **publication des auteurs et organisateurs de CL-Detection2023**, classer les associations numéro/nom explicitement mentionnées, sans promettre qu'un canal de notre export ONNX possède une vérité anatomique validée.

**GOAL :** produire une table auditée, reproductible et limitée aux affirmations textuelles de cette publication, avec un verrou permanent `SOURCE_LOCK_REQUIRED`, sans calcul clinique ni donnée patient.

**Source primaire vérifiée par lecture :** Hongyuan Zhang et coll., *Deep Learning Techniques for Automatic Lateral X-ray Cephalometric Landmark Detection: Is the Problem Solved?*, [arXiv 2409.15834 version 1](https://arxiv.org/html/2409.15834v1), §5.3 et §6.1. Auteurs, dont Ching-Wei Wang et Bingsheng Huang, également organisateurs du challenge. Le §5.3 nomme « Prn » au numéro 26 et « Basion » au numéro 27 ; le §6.1 nomme « A » au 5, « Go » au 10, « Pos » au 16, « PNS » au 17, « Co » au 25, « Ba » au 27 et « Bo » au 29.

**Concordance limitée et explicite, 7 numéros :**

| Catégorie challenge (1-based) | Canal modèle attendu (0-based) | Abréviation textuelle de la publication | Alias historique Digital Crown | État |
|---:|---:|---|---|---|
| 5 | 4 | A | A | Accord des abréviations numérotées, **non clinique** |
| 10 | 9 | Go | Go | Accord, **non clinique** |
| 17 | 16 | PNS | PNS | Accord, **non clinique** |
| 25 | 24 | Co | Co | Accord, **non clinique** |
| 26 | 25 | Prn | Prn | Accord, **non clinique** |
| 27 | 26 | Ba / Basion | Ba | Accord, **non clinique** |
| 29 | 28 | Bo | Bo | Accord, **non clinique** |

**Ambiguïté explicitement réservée :** catégorie 16 = **« Pos »** dans l'article ; le canal historique 15 = `Pog_soft`. Sans glossaire autoritatif confirmant `Pos ⇔ Pog_soft` pour **le même jeu et le même checkpoint**, pas d'équivalence adoptée. **Les 30 autres catégories** n'ont pas de nom explicitement associé à leur numéro dans les passages textuels audités ici. Cela ne prouve pas qu'une table complète n'existe nulle part dans les matériels des organisateurs.

**Bilan d'évidence :** 7 concordances textuelles, 1 abréviation ambiguë, 30 autres associations non établies dans les passages inspectés ; **0/38 canaux anatomiquement/clinquement validés pour déploiement**. Le `SOURCE_LOCK_REQUIRED` du registre reste en vigueur pour les **38**.

## Preuve technique proposée

Le script standard-library `scripts/ci/ceph_j1b1_s2_author_paper_crosswalk.py` télécharge **la seule version v1** du texte HTML des auteurs, vérifie le titre, les signatures d'auteurs dans le document et les sept paires `label (No. N)` ; enregistre le SHA-256 du HTML consulté. Refuse les catégories dont le numéro dérive, refuse d'assimiler « Pos » à `Pog_soft`, confronte la table historique de `backend/services/srpose38_contract.py` à la provenance/pins de `backend/scientific_assets.json` déjà explicitement `SOURCE_LOCK_REQUIRED`. Rapporte **métadonnées uniquement** : catégories, noms locaux historiques, noms cités, état `NO_CLINICAL_GO`. Ne télécharge **aucun modèle, aucune image, aucun dossier patient, aucun jeu d'annotations**, n'importe pas le backend, ne produit aucune inférence. Tests négatifs intégrés.

**Aucune affirmation de réussite CI avant lecture des jobs au HEAD exact.** La vérification dépend de la disponibilité de l'HTML auteur v1 ; indisponible = **fail closed**, ne pas remplacer silencieusement par un autre document ni supposer succès.

## Source décisive encore manquante

Le [challenge officiel](https://cl-detection2023.grand-challenge.org/) et le [repo de référence des organisateurs](https://github.com/cwwang1979/CL_detection2023_reference_docker) documentent 38 catégories numériques sans publier, dans les fichiers consultés, les 38 définitions anatomiques associées à ces catégories. Le document officiel de conception [BIAS/Zenodo](https://zenodo.org/records/7835592/files/CephalometricLandmarkDetectioninLateralX-rayImages_04-17-2023_11-16-01_withSupplement.pdf) décrit une annotation réalisée par deux médecins et un CSV à champs `PID, X, Y`, **sans fournir la table nominative 1..38 exploitable dans le texte vérifié**.

**Contacts vérifiés :** [page challenge](https://cl-detection2023.grand-challenge.org/) : Ching-Wei Wang `cweiwang@mail.ntust.edu.tw` et Hikam Muzakky `m11123801@mail.ntust.edu.tw`. L'[article des organisateurs](https://arxiv.org/html/2409.15834v1) identifie aussi Bingsheng Huang `huangb@szu.edu.cn`. Aucun courriel n'est envoyé dans ce lot sans validation.

### Demande technique aux organisateurs — prête à envoyer (EN, non envoyée)

**Subject:** CL-Detection2023 — authoritative 1–38 landmark nomenclature for exact SRPose checkpoint

Dear Prof. Wang and Prof. Huang,

I am auditing the anatomical nomenclature of the 38 landmark channels in the CL-Detection2023 benchmark for a local, clinician-controlled cephalometric application. The model under review traces to `5k5000/CLdetection2023@18d17d1934970016e7610c4849311900b8d1f191`, with checkpoint SHA-256 `fb1a781ac1c83149b379cb15724e3b0fae06ba2d567978f35c61e9d06b46fdcc`. Its MMPose dataset configuration lists channels 0–37 numerically.

Your 2024 paper explicitly identifies A (No. 5), Go (No. 10), PNS (No. 17), Co (No. 25), Prn (No. 26), Ba (No. 27) and Bo (No. 29). Could you please share or point us to the **authoritative category numbers 1–38 mapped to each anatomical name and operational definition**, including whether No. 16 "Pos" denotes soft-tissue pogonion? If available, a dated challenge annotation guide or schema/version identifier linking this numbering to the official `train-gt.json` and the referenced training setup would make the correspondence reproducible.

We will keep automatic clinical interpretation disabled until the nomenclature and independent paired-image landmark accuracy are validated. We are **not requesting patient images or private data by email**.

Thank you for your help.

Best regards,

## Next gate (distinct)

Une réponse d'auteur avec guide/version et liste des 38 définitions doit être recoupée avec le checkpoint et les annotations **sur clichés autorisés**, suivie d'une **revue clinique indépendante** (MRE par repère, SDR@2 mm, cas difficiles, reproductibilité inter-opérateurs, traçabilité modèle→dataset). Aucune valeur globale de leaderboard ou concordance de 7 noms ne remplace cette preuve. Pas de merge, déploiement, installation ou activation céphalométrique automatique dans ce lot.

**État : DRAFT / NONCLINICAL / SOURCE_LOCK_REQUIRED / NO_INSTALLABLE_GO.**
