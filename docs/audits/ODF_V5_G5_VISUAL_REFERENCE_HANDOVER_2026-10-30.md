# Digital Crown · G5 — Référence visuelle validée, reproduction LAB (2026-10-30)

**Décision praticien** : « Là c'est parfait » = GO sur **la planche de revue en tant que cible visuelle**, NON validation anatomique des 6 contours, non signature R14. Le fichier source de la planche s'appelait `G5_planche_revue_praticien.png`. Les 4 couches en pointillés restent incertaines et non cliniques.

## Contrat canonique, une source seulement

- `docs/audits/fixtures/g5/g5_visual_reference.json` : six jeux exacts de points-guides de la planche acceptée (44/25/13/21/12/10), couleurs, ordre, styles, avertissements et provenance; aucune génération de courbes à partir de landmarks.
- Source : jeu Aariz, film `cks2ip8fp29yl0yuf6ry9266i.png`, article Figshare 27986417, fichier 51041642, CC BY 4.0, DOI 10.1038/s41597-025-05542-3.
- Image affichée : **1935×2400**, SHA-256 `7f0746c91faeebbd5a80180b13e0dfa5baa0fe1e0d9403f59f85cf1c03f7eb50`. Film original 1972×2225, SHA-256 `c2c391d7637206123b81c4e43b98d2e21f14ce9b5723698d768d68d3292e88c7`. La transformation affine est consignée dans le JSON.
- Un image test ANUG, ou toute autre étude dont le SHA-256 est différent, doit **échouer**, non tenter un réalignement approximatif.
- Seuls **soft_tissue_profile** et **mandible** sont affichés en continu; **maxilla**, **cranial_base**, **upper_incisor**, **lower_incisor** en **pointillés**, comme sur la planche.
- **Correctif visuel obligatoire** : l'ancien manifeste comportait 19 points pour `cranial_base`, avec une diagonale jusqu'à x=1251, qui ne correspondait **pas** à la planche validée. Le manifeste canonique utilise désormais 21 points, secteur court sinueux x=585–856, y=899–979, et reste en pointillés. Vérifier la comparaison visuelle, pas seulement le respect du schéma.

## Commande de reproduction visuelle (preuve de QA, pas PDF clinique)

Dans le run LAB après `python -m scripts.odf_v5_g3_aariz_matched_pair` :

```bash
python -m scripts.g5_visual_reference_preview \
  --manifest docs/audits/fixtures/g5/g5_visual_reference.json \
  --source artifacts/ortho-v5-g3-expert-lateral/expert-matched-cephalogram.png \
  --out artifacts/ortho-v5-g5-visual-reference
```

Sorties : `G5_reference_overlay_UNAPPROVED.png` (vraie radio + six courbes), `G5_reference_clean_UNAPPROVED.png` (tracés seuls, sans film), `G5_reference_two_views_REVIEW_ONLY.pdf` (2 pages A4 avec **NON CLINIQUE**), `G5_reference_evidence.json` (preuve coordonnées/état/6 couches). Le lissage pour l'affichage utilise PCHIP, en conservant les points-guides comme source d'autorité.

**Barrière absolue** : ne jamais appeler les endpoints `saveAnatomicalTraceDraft` ou `approveAnatomicalTrace` avec ce manifeste, et ne jamais insérer ces points dans le système de production. `clinical_approval=false` est contrôlé indépendamment. Le PDF ci-dessus n'est **pas** le bilan clinique Digital Crown signé ; les deux rendus finaux du vrai système nécessitent une saisie/approbation manuelle séparée.

## Sous-lot suivant : reproduction dans l'éditeur et le PDF officiels

FUE obligatoires avant toute demande de GO clinique :

1. **Image appariée** : ouvrir la même étude Aariz dans le Cabinet LAB et prouver le SHA256 réel du fichier servi; bloquer si différent, même si patient/étude ou dimensions semblent correspondre. Le script G3 remplace le fichier de seed par l'Aariz appariée dans le run dédié, mais ce n'est **pas vrai de tout environnement LAB**.
2. **Mode référence QA lecture seule** : afficher les deux traits continus et quatre pointillés comme cible inspectable, avec badge non clinique, mais jamais en tant que contours enregistrés/validés par défaut.
3. **Saisie praticien des 6 contours** : correction manuelle des zones ambiguës sur la source, distinction explicite entre points / tangentes, état modifié non approuvé, contrôle des coordonnées pixel source malgré zoom et scroll.
4. **Signatures et PDF** : après une approbation réellement effectuée par le praticien et non issue de la fixture, comparer les 6 points/courbes persistés et les 2 vues document factory sur la *même* source et révision. Refuser tout contour absent ou désapparié, le bypass de l'état approbation, ou un PDF inchangé après edit.
5. **Batterie FUE-G5 / R14** : captures 390/430/768/1280, zoom ×1/×2/×4/×8, drag clavier/tactile ou pointer selon support, négatifs secrétaire/étude différente/révision périmée/image remplacée ; double revue technique + anatomie praticien. Ne pas promouvoir une fixture de points visuellement approuvée en diagnostic certifié.

## Situation à la clôture du lot fixture

PR [#1048](https://github.com/hraaaaf/Digital_crown/pull/1048) **Draft, conflits avec master**. Aucun merge, aucune migration ni déploiement Vercel. R14 **NO-GO**. La qualité visuelle de la planche est acceptée ; validité clinique, quatre régions incertaines et flux patient authentifié restent à résoudre.
