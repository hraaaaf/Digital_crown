# M6-C — Validation / signature au fauteuil — Closeout

Date : 2026-08-25
État : CLOSED

## Goal

Durcir la signature mobile au fauteuil sans changer le flow métier : ergonomie tactile correcte, canvas net et responsive, signature vide impossible, payload serveur réellement validé, re-signature interdite et devis déjà signés exclus.

## Succès observables

- contrôles critiques ≥ 48 px ;
- canvas responsive avec backing store aligné sur `devicePixelRatio` ;
- signature vide bloquée côté UI et côté serveur ;
- signature acceptée uniquement comme PNG valide, décodable et bornée ;
- re-signature refusée ;
- devis déjà signés non reproposés ;
- permissions et ownership tenant conservés ;
- 390 / 430 / 768 sans overflow ni erreur runtime ;
- régressions backend/frontend et CI exact-head vertes.

## Base / produit

- Base exacte : `5f7325b58abd9c81e437d3c4e776e61f3a0bd0b0`
- Branche produit : `mobile/m6-c-signature-hardening`
- HEAD certifié : `a07ed396dae3af26b5a57170b8e0e42a67ccff41`
- PR : #254
- Merge produit : `7c8983d6da48c95de3798c72f7bce130ab3afb51`
- Scope produit : 1 commit / 5 fichiers / 0 behind avant merge

## BEFORE

Run `32879729585` — SUCCESS.

Constats :
- action Signature : 37 px ;
- Effacer / Enregistrer : 42 px ;
- Fermer : 38 px ;
- select : 35 px ;
- cible icône fermeture : 18 px ;
- signature vide acceptée ;
- canvas backing fixe 300×180 ;
- 0 overflow ;
- 0 erreur runtime.

## Goal + référence visuelle

Verrouillés avant code dans le commit audit `383668bcaff8169f303994710f93b6275aacf1a3`.

## Préparation

Prep final canonique Python 3.12 : run `32885405326` — SUCCESS.

Avant le commit produit :
- scope exact validé ;
- tests M6-C + régressions M6-A/M6-B passés ;
- build frontend passé ;
- un seul commit produit créé.

Les essais de prep précédents n'ont produit aucun commit produit ; ils ont seulement révélé des défauts du harness, dont un faux signal lié à Python 3.11 alors que la CI canonique utilise Python 3.12.

## Produit certifié

Backend :
- validation stricte du préfixe `data:image/png;base64,` ;
- décodage base64 strict ;
- limite 2 MiB ;
- limite 8 MP ;
- décodage Pillow + normalisation PNG ;
- rejet d'une image sans quantité minimale d'encre ;
- document limité au type DEVIS ;
- verrou `with_for_update()` ;
- `409` si déjà signé ;
- devis signés exclus de la liste ;
- permission `patients` et ownership tenant conservés.

Frontend :
- canvas `ResizeObserver` ;
- backing store CSS × DPR ;
- Pointer Events ;
- tracé préservé lors d'un resize ;
- Enregistrer désactivé tant qu'aucun trait n'est présent ;
- contrôles critiques à 48 px minimum ;
- états vide / prêt explicités.

## AFTER exact-head

Run `32886124856` — SUCCESS sur `a07ed396dae3af26b5a57170b8e0e42a67ccff41`.

Artifact : `9577691774`
Digest : `sha256:02547626869d9a5e0265a0d1492bfd83b6ff94239ca5873ab78348a1e0b70264`

9/9 captures : 390 / 430 / 768 × entrée / vide / tracée.

Gates :
- min tactile : 48 px ;
- signature vide bloquée partout ;
- trait réel active Enregistrer ;
- payload PNG confirmé ;
- canvas DPR exact 2× dans le harness ;
- 0 overflow horizontal ;
- 0 erreur runtime.

Inspection humaine : 9,7/10.

Point perfectible non bloquant : le bouton texte `Fermer` et le bouton `×` restent redondants dans le modal.

## CI exact-head

- T2 #1008 — run `32885809298` — SUCCESS
- Patient P7 #307 — run `32885809263` — SUCCESS
- Catalog #281 — run `32885809274` — SUCCESS
- CI #1862 — run `32885809299` — SUCCESS

## Conclusion

M6-C satisfait son Goal avec preuves produit, runtime, visuelles et CI. Le lot est CLOSED.

Aucun déploiement Vercel effectué.