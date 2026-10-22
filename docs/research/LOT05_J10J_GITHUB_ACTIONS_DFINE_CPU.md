# LOT05 / J10J — Tout exécuter dans GitHub Actions : modèle de base D-FINE Nano COCO et verrou FDI

**Date 2026-10-22 — Research-only Draft PR empilée sur J10I.**
Objectif utilisateur : « Go tout sur github actions ?! ». Réponse opérationnelle : oui pour toutes les étapes de **vérification technique réalisables sans données médicales**. **Non** pour un entraînement FDI commercial tant qu'aucun corpus 32 classes n'a une provenance/réutilisation commerciale démontrée. Ce blocage n'est pas à contourner via GitHub Actions. Aucune utilisation de la machine du cabinet, aucun serveur connecté au patient, aucun merge/déploiement.

## Workflow concret

`.github/workflows/lot05-j10j-dfine-cpu-smoke.yml` exécute uniquement sur la PR J10J (et, plus tard, en `workflow_dispatch` si la workflow est introduite sur la branche par défaut) :

1. **`rights-before-model`** — exécute le catalogue FDI J10I et ses **10 tests négatifs** : les droits/qualité insuffisants maintiennent `COMMERCIAL_AND_CLINICAL_RELEASE_BLOCKED`, empêchent les poids d'être injectés dans l'application et n'autorisent jamais la distribution sur simple déclaration MIT/Apache.
2. **`pinned-public-coco-cpu`**, matrice **`ubuntu-24.04` + `windows-2025`**, dépend du point 1. Télécharge **uniquement trois fichiers publics** d'un modèle de détection d'objets COCO — pas d'image radiographique et aucun corpus FDI :
   - [`ustc-community/dfine-nano-coco`](https://huggingface.co/ustc-community/dfine-nano-coco) sous **Apache 2.0** ;
   - révision immuable `066438d3d8f0da137a37b38fdf3368fd4afceced`, [détails du SHA](https://huggingface.co/ustc-community/dfine-nano-coco/blob/main/model.safetensors) ;
   - poids `model.safetensors` **SHA-256 `19e06bdc873da819920a8d373b879721a5b9759d822f8213220bb09abbdab58b`**, `config.json`, `preprocessor_config.json`, aucun autre fichier ;
   - PyTorch/torchvision et Transformers épinglés, CPU seulement, exécution avec `trust_remote_code=False` et `local_files_only=True` après SHA. Image de test **entièrement générée en mémoire par Pillow**, avec rectangle et ellipse sur fond neutre, **pas une radio**.
3. Vérifie le traitement et la géométrie tensorielle : sorties finies, nombre de classes du backbone COCO supérieur à 32, nombre de propositions cohérent et post-traitement disponible. Produit un **petit rapport JSON** : SHA, taille du checkpoint, environnement Windows/Linux, versions, temps CPU, noms de schémas et statut `PUBLIC_COCO_FOUNDATION_SYNTHETIC_CPU_PASS`. **Pas de précision FDI, pas de diagnostic, pas de patients.**
4. Artifact `research-coco-metadata-ubuntu-24.04` ou `research-coco-metadata-windows-2025` : **seul JSON, sans poids ni images**. Pas de secret, cloud clinique, artefact modèle publié, ni dépôt GitHub Release, ni copie dans le bundle Digital Crown.

`experiments/test_lot05_j10j_dfine_actions_smoke.py` utilise uniquement des fixtures fictives pour vérifier la révision et le SHA attendus, l'interdiction d'un faux modèle FDI, les rejets SHA incohérents et le maintien du refus des licences cliniques/commerciales.

## Ce que GitHub Actions n'autorise pas encore

- **Entraînement de numérotation des 32 dents FDI sur de vraies panoramiques** : **bloqué par la provenance insuffisante du dataset Roboflow 1 577 images / CC BY 4.0 affichée**, et par les ambiguïtés DENTEX ; il ne suffit pas de cocher une case de consentement. Préparer un dossier de droits montrant auteur, titulaire, chaîne de redistribution, confidentialité, base légale et exclusions, puis faire une revue indépendante.
- **Benchmarks cliniques / validation sur imagerie patient**, ou toute transmission d'images vers GitHub : aucun. GitHub Actions public n'est pas une place autorisée pour héberger des données médicales sensibles. Un éventuel entraînement devra utiliser un corpus explicitement autorisé à être traité sur des runners cloud et public/privé selon l'accord.
- **Export ONNX puis validation de parité D-FINE spécifique** : phase suivante, à traiter seulement après succès prouvé du chargement du modèle D-FINE Nano COCO et des tests CPU sur Ubuntu+Windows. Un ONNX COCO ne devient jamais numérotation FDI par conversion.
- **Déploiement, fusion ou migration clinique** : aucun ; PR Draft uniquement.

## Définition de PASS

Un PASS signifie : « GitHub Actions peut récupérer le backbone D-FINE Nano COCO déclaré Apache 2.0, vérifier son SHA exact, l'exécuter sur un dessin non médical, restituer les métriques techniques et verrouiller l'usage commercial FDI. » Il **ne signifie jamais** : « les numéros dentaires FDI fonctionnent » ou « Digital Crown peut vendre ce checkpoint entraîné ». La radiographie reste séparée du PDF panoramique approuvé, dont le texte uniquement est préservé depuis J10G/J10H.

Références :
- [D-FINE Nano source](https://huggingface.co/ustc-community/dfine-nano-coco), [SHA des poids](https://huggingface.co/ustc-community/dfine-nano-coco/blob/main/model.safetensors), [D-FINE dans Transformers](https://huggingface.co/docs/transformers/main/en/model_doc/d_fine) ;
- [D-FINE source GitHub Apache](https://github.com/Peterande/D-FINE) ;
- [Guide Github Actions Artifact](https://docs.github.com/en/actions/concepts/workflows-and-actions/workflow-artifacts).
