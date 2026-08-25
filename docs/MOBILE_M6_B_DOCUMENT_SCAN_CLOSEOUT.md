# M6-B — Scan de documents contextuel — Closeout canonique

Date : 2026-08-25
État : CLOSED

## Goal

Depuis le contexte Patient exact sur mobile, permettre de photographier 1 à 8 pages, les prévisualiser, ajouter/supprimer des pages puis enregistrer explicitement un PDF canonique dans `DocumentArchive` avec type `AUTRE`, sans `patient_id` fourni par le téléphone.

## Résultat certifié

- PR : #253
- base produit : `0a577f05f55a772a1b3f6d2980b18ef4e1a643fb`
- HEAD produit final certifié : `2eccb8710ae511f53282825f631d11ccddfbeb45`
- merge : `72d96ab2f796748fa5d1c7b4da008047ae7a6b17`
- scope final : 1 commit / 3 fichiers / 0 behind
- aucun Vercel

## BEFORE / Goal visuel / mockup

BEFORE réutilisé du M6-A exact-head car, entre le HEAD capturé et le baseline M6-B, seuls les documents de closeout/roadmap M6-A avaient changé.

- run BEFORE : `32864337475`
- artifact : `9569518739`
- digest : `sha256:69dd249809ba98246b84c298cd5cdffdc387d104ba1dee2e3fa81fde1b76fd1e`
- viewports : 390 / 430 / 768
- constat BEFORE : aucune action « Scanner un document », aucun endpoint de scan documentaire contextuel

Goal + mockup figés avant implémentation : commit audit `b8108d487a06538d03ea941052338d387ccc2bc4`.

## Architecture métier certifiée

- contexte Patient résolu et revalidé côté serveur ;
- upload lié au `context_key`, sans `patient_id` fourni par le mobile ;
- 1 à 8 pages ;
- JPEG / PNG / WebP ;
- `capture="environment"` côté mobile ;
- limite 12 MiB par page ;
- limite 48 MiB cumulée ;
- limite 50 MP par page ;
- décodage réel avec Pillow ;
- normalisation EXIF ;
- PDF généré côté serveur ;
- archivage canonique `DocumentArchive` / `AUTRE` ;
- aucun OCR, cloud ou auto-crop introduit par ce lot.

## Correction mémoire avant merge

Le premier candidat `fd45d97004774ff3261aede51ae6c5c726c2d2c4` a été supersédé avant merge après revue interne : l'assembleur conservait potentiellement toutes les pages simultanément comme bitmaps RGB. Au plafond théorique 8 × 50 MP, le pic mémoire pouvait dépasser 1 GiB.

Correction appliquée avant certification finale :

- JPEG normalisés conservés compressés ;
- PDF assemblé page par page avec PyMuPDF / `insert_image` ;
- ancienne liste globale de bitmaps RGB supprimée ;
- branche produit réécrite par `force-with-lease` en exactement un commit depuis le même baseline.

Finalizer : run `32876398093` — SUCCESS.

Preuves finalizer :

- architecture memory-safe vérifiée ;
- `py_compile` vert ;
- M6-B + régression M6-A : 8 tests passés ;
- HEAD final : `2eccb8710ae511f53282825f631d11ccddfbeb45`.

## AFTER final exact-head

Run : `32876699557` — SUCCESS.

Artifact :

- id : `9574230973`
- digest : `sha256:53c698d468653e7c10a8a6cf434c2ef2ed76d0674adb74ae6d464193f286d08e`

Captures : 9/9, soit trois états sur chaque viewport 390 / 430 / 768 :

1. action « Scanner un document » ;
2. aperçu 2 pages ;
3. confirmation « Document enregistré ».

Gates du report :

- `productHead` exact = `2eccb8710ae511f53282825f631d11ccddfbeb45` ;
- action scan présente ;
- entrée caméra correcte ;
- 3 uploads simulés ;
- upload contextuel ;
- multi-page ;
- `patient_id` absent ;
- hauteur tactile minimale M6-B : 52 px ;
- aucun overflow horizontal ;
- aucune erreur runtime inattendue.

Inspection visuelle finale : conforme au Goal et au mockup, hiérarchie nette, scan distinct de la photo clinique, aperçu multipage lisible et succès explicite.

Score visuel final : **9,7/10**.

## CI exact-head finale

Après le rewrite du HEAD par GitHub Actions, une première série de checks a été classée `action_required` avant tout job car l'événement venait de `github-actions[bot]`. Aucun test produit n'avait échoué. La PR a été fermée/réouverte sans changement de code afin de réémettre l'événement avec l'acteur utilisateur.

Série finale sur `2eccb8710ae511f53282825f631d11ccddfbeb45` :

- CI #1859 — run `32876806240` — SUCCESS ;
- T2 Runtime Browser Certification #1007 — run `32876806337` — SUCCESS ;
- Catalog Connected Truth Certification #280 — run `32876806248` — SUCCESS ;
- Patient P7 Final Certification #306 — run `32876806274` — SUCCESS.

## Dette hors scope observée

`npm ci` continue de signaler des vulnérabilités de dépendances héritées du repo. M6-B ne les introduit pas et aucune correction opportuniste n'a été mélangée au lot.

## Conclusion

M6-B est CLOSED : le mobile peut scanner plusieurs pages depuis le Patient exact, les prévisualiser puis produire un PDF canonique archivé côté serveur, avec contexte revalidé, limites média, absence de `patient_id` mobile, assemblage mémoire-safe et preuves visuelles/exact-head complètes.

Prochain lot canonique : **M6-C — Validation / signature au fauteuil**, audit d'abord de la fonctionnalité existante puis correction ciblée des défauts réellement prouvés.
