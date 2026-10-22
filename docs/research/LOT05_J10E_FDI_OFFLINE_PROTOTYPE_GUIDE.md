# Digital Crown — LOT05 / 05.7-J10E : prototype FDI local (2026-10-22)

**Modèle retenu par le propriétaire** : miquic/app-odonto-fdi-yolov8s (32 dents permanentes) · HF SHA `82b4d9a02f9e6f32a746dc17afe681e20e8b99e2` · poids `best.pt` SHA256 `533833a4244f092f82bc94a6c2d6fac7e1656c9437994e98d09843c54aafd3f6`. **Prototype de recherche uniquement. Ni clinique ni redistribution commerciale autorisées.**

## Éditeur de numérotation opérationnel sans backend patient

Le démonstrateur autonome `experiments/lot05_j10e_fdi_review_demo.html` charge une radiographie depuis le disque local et un JSON de propositions FDI. Les boîtes et numéros sont modifiables : glisser, redimensionner par coordonnées, réassigner FDI, ajouter une dent manquée, supprimer un faux positif, confirmer le numéro. Les propositions du modèle sont toutes **non confirmées**. Si le dentiste modifie une dent, sa confirmation précédente ainsi que les éventuels actes associés sont annulés. Deux dents ne peuvent pas être simultanément confirmées sous le même FDI. Numéros temporaires et mixtes : hors classe modèle adulte. Aucun diagnostic/acte inféré.

Les actes sont ajoutés **manuellement** par spécialité au dictionnaire de démonstration, enregistré en localStorage du navigateur (actes seulement, AUCUN patient). Le clinicien ne peut attribuer un acte qu'à une dent confirmée. L'export JSON local `digital-crown-fdi-clinician-review-v1` ne sauvegarde ni dans le dossier patient ni sur serveur. Une image chargée en mémoire n'est pas persistée.

### Démarrer sur le poste de recherche

Dans la racine du dépôt sur la branche expérimentale, lancer le serveur sur loopback uniquement :

~~~powershell
python -m http.server 8765 --bind 127.0.0.1 --directory experiments
~~~

Ouvrir `http://127.0.0.1:8765/lot05_j10e_fdi_review_demo.html`. Aucune ressource distante n'est référencée par cette page. Ce n'est **pas** un écran activé dans l'application Digital Crown de production.

## Produire un vrai JSON du modèle via ONNX local

Pont `experiments/lot05_j10e_fdi_onnx_bridge.py`. Il exige les fichiers locaux déjà acquis légalement, SHA256 exact pour le poids PyTorch (pickle non fiable si non vérifié) et pour l'ONNX exporté. Aucun modèle n'est téléchargé automatiquement. Un exécutable de cabinet ne doit pas encore incorporer les poids CC BY-NC-SA.

Sur une machine de **recherche autorisée**, Python 3.11 + ultralytics, torch CPU, onnx, onnxruntime et OpenCV :

~~~powershell
$env:PYTHONPATH="experiments"
$env:ULTRALYTICS_AUTOINSTALL="False"
python experiments/lot05_j10e_fdi_onnx_bridge.py export --checkpoint C:\research\best.pt --onnx C:\research\fdi-selected.onnx --authorized-research-local
~~~

L'export émet le vrai SHA256 de l'ONNX local. Pour une radiographie **publique autorisée** de recherche, et non une donnée patient du cabinet :

~~~powershell
python experiments/lot05_j10e_fdi_onnx_bridge.py infer --onnx C:\research\fdi-selected.onnx --onnx-sha256 VRAI_SHA256_64_HEX --image C:\research\pano_publique.jpg --json-out C:\research-private\propositions-fdi.json --authorized-research-local
~~~

Importer d'abord l'image correspondante puis `propositions-fdi.json`. Les propositions suivent `digital-crown-fdi-review-v1` : dimensions pixels image_width/image_height, liste de boîtes normalisées `[x1,y1,x2,y2]` sur [0,1], FDI texte 11–48, confiance. Le prototype refuse dimensions différentes, nombres FDI non permanents, boîtes invalides et doublons de FDI confirmés.

## GitHub Actions

`.github/workflows/lot05-j10e-fdi-prototype.yml` sur **PR expérimentale DRAFT empilée** :
- Job Node.js et Python pur : tests de correction/confirmation/actes/geometry, rejets et hash modèle. Aucun film.
- Job CPU éphémère : export du poids HF épinglé en ONNX, comparaison des régions/classes des résultats `.pt` vs `.onnx` sur **2 panoramiques de recherche AKUDENTAL publiques**, avec IoU 0.90 et écart max confiance 0.08. Ne conserve que des agrégats techniques JSON et le SHA export, **pas de binaire de modèle, image, annotation individuelle ou données patient**.

Les codes verts CI ne garantissent pas la parité Windows, l'adéquation clinique ou la sûreté de l'interface.

## Réglementation, dette et prochaine étape

La validation du modèle par le propriétaire **clôt sa sélection**, elle ne donne pas un droit commercial sur les poids/données (CC BY-NC-SA 4.0) ni une homologation clinique. Le vrai benchmark (40 panoramiques) n'a que 81,08 % de rappel exact FDI + localisation, 139 dents oubliées et 3/40 films totalement corrects : confirmer manuellement chaque dent. Pas de reconnaissance de pathologie, pas de choix automatique d'acte. Ne pas envoyer d'images du cabinet vers GitHub Actions ou HF.

Après la preuve ONNX CPU et l'éditeur de recherche : (1) obtenir droits commerciaux ; (2) architecturer intégration locale Windows sûre, sauvegarde/traçabilité RBAC et tests sur Windows réel ; (3) faire valider l'UX clinicien, numérotation et cas particuliers ; (4) seulement alors envisager branchement au dossier patient et au catalogue d'actes de Digital Crown, sous nouveau lot et revue. **Ne rien fusionner/déployer/installer pour l'instant. V1.5 NO-GO.**

**Roadmap** : J10D choix modèle VALIDÉ → J10E parité ONNX et éditeur FDI expérimental → droits commerciaux + sûreté Windows → UI dossier patient et dictionnaire certifiables → GO clinique ultérieur.
