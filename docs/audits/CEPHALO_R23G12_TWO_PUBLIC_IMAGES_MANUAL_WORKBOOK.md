# CEPH-UXCLIN-01 · R23-G12 — Atelier manuel sur deux vraies téléradios publiques

**Statut : recherche / annotation provisoire en pixels uniquement. AUCUN GO clinique.**

## Ce qui existe déjà dans Digital Crown

`frontend/src/features/ortho/CephaloTracingLayerBase.tsx` contient déjà un mécanisme de clic, de tracé et d'édition des repères ; `frontend/src/features/ortho/components/Step1CephaloBase.tsx` prévoit la calibration manuelle. **G12 ne remplace ni ne modifie ces composants**, car les images publiques n'ont pas de vraie vérité clinique pour les 21 identités spécifiques Ricketts et les constructions Atlas2009.

G12 est un **atelier de collecte isolé**, hors runtime, permettant de matérialiser des clics réellement faits sur des JPEG publics, sans appeler des clics de test « annotations expertes ».

## Sources et identité des images

La procédure reprend exactement les deux JPEG originaux G11, leurs empreintes SHA-1 et leurs dimensions, avec la licence CC BY-SA 4.0 et attribution :

- [ANUG 2014 — Cephalometric radiograph](https://commons.wikimedia.org/wiki/File:Cephalometric_radiograph.JPG), 2272×1818, SHA1 `2a284993c666790a72d0c004044b35a92534ce9d`.
- [Challiyan 2023 — A lateral cephalogram without true vertical](https://commons.wikimedia.org/wiki/File:A_lateral_cephalogram_without_true_vertical.jpg), 1000×1255, SHA1 `66c74c588af3c54dfc581f8a870c5276c3427498`.

Le constructeur `scripts/cephalo_r23g12_public_manual_workbook.py` appelle le véritable vérificateur G11 : 2 JPEG originaux, SHA1, SOF JPEG et dimensions, puis **2 tentatives d'admission refusées par G10**. Il dérive les SHA-256 des bytes réels et les **21 identités Ricketts exactes** de G9. Aucune position de repère n'est induite par le script.

## Utilisation sur un poste autorisé

Avec les deux fichiers publics téléchargés (nommés `anug.jpg` et `challiyan.jpg`), exécuter :

```bash
python -m scripts.cephalo_r23g12_public_manual_workbook \
  --input-dir /tmp/mes_deux_jpeg_publics \
  --output-dir /tmp/atelier_atlas33_public
```

Ouvrir `index.html` localement dans un navigateur moderne ou via un serveur local strictement lié à `127.0.0.1`. Choisir le cliché, saisir un jeton pseudonyme, sélectionner un des **21 points** et cliquer sur la véritable radiographie. Le SVG transporte le clic écran vers les coordonnées **originales de l'image** grâce à la matrice de transformation ; zoom 100/150/200 %, suppression et changement de cliché fonctionnent sans calcul d'angle ou distance physique. Un jeton est bloqué après le premier clic ; une session distincte est obligatoire par opérateur.

Le bouton **Exporter** produit localement un fichier JSON de brouillon, contenant exclusivement les coordonnées pixels de ces deux images publiques et les 21 identités autorisées. Aucune requête réseau, aucun `localStorage`, aucune valeur en mm, aucune identification patient ou approbation de source, calibration, orientation ou expertise. Ne pas utiliser ce prototype pour des images patient confidentielles ; pour une vraie étude experte il faut un environnement sécurisé, la traçabilité/supervision des praticiens et une validation clinique indépendante.

**Très important :** rien n'est placé automatiquement ; les coordonnées produites par le scénario Playwright ne sont que des **clics synthétiques d'interaction**. Elles ne représentent pas une annotation anatomique, même si leur forme JSON est conforme.

## Validation et non-substitution

- `audit/cephalo_r23g12_contract_tests/test_pixel_draft.py` — tests négatifs refusant les coordonnées hors image, valeurs non finies, alias génériques, champs supplémentaires, identité/dimensions erronées, conversion mm ou promotion du brouillon en vérité clinique.
- `audit/cephalo_r23g12_contract_tests/g12_public_browser_e2e.cjs` — Chromium réel, sur **les deux JPEG originaux**, affichage, choix du point, clic, zoom, suppression, changement de cliché, export et contrat JSON. Viewports desktop `1280×900` et `1600×1000` ; capture visuelle de clic **SYNTHÉTIQUE NON CLINIQUE**. Deux statuts `clinical_release=false` et `atlas33_measurements_validated=0` obligatoires.
- `.github/workflows/cephalo-r23g12-public-workbook.yml` — CI **EXPÉRIMENTALE** avec checkout exact SHA, fichiers sources éphémères, source manifests publics, e2e et contrôles des brouillons. L'artefact ne comprend que preuve **synthétique** et attribution CC BY-SA 4.0 ; aucun jeu privé Aariz, fichier patient ni repère réel.
- `verify_draft()` est un **contrôle structurel**, pas un oracle clinique : un JSON peut être cohérent tout en contenant des points placés au mauvais endroit anatomiquement.

## Ce qu'il faut encore pour Atlas33

Ce prototype ne certifie **aucun** des 21 repères, ne vérifie ni sens anatomique ni calibrage mm/pixel, n'obtient pas les 2 experts qualifiés, ne démontre ni répétabilité inter/intra ni les **33 facteurs** calculés. Il démontre uniquement que l'on peut annoter manuellement des coordonnées sur de vrais clichés publics et récupérer un brouillon **non clinique** et source-verrouillé.

Pour un **goldset clinique**, l'étude doit utiliser des images autorisées et calibrées, un protocole spécialisé versionné et **deux vrais experts indépendants**, avec confrontation anatomique et mesure d'incertitude; la PR G12 seule n'autorise ni merge, ni déploiement, ni `Focus` clinique.

**Roadmap :** W1–W3 registres → G9 gap IDs → G10 sécurité d'admission → G11 2 JPEG réels → **G12 opérabilité annotation sur JPEG** → experts/références calées → validation des mesures Atlas33 → décision clinique/closeout.
