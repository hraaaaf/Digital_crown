# M6-H — Imagerie mobile plein écran — Closeout

Date : 2026-08-26  
État : **CLOSED**

## Goal

Transformer la consultation Panoramique mobile exacte en viewer mobile-first plein écran dans l’app, sans modifier l’analyse clinique, le contexte M4-B ni la sécurité d’accès au média.

## Succès observé

- même contexte `panoramic` exact et même média protégé M4-B ;
- aucun endpoint, modèle backend, permission ou dépendance ajouté ;
- CTA `Agrandir` ≥52 px uniquement lorsque le média est disponible ;
- viewer in-app `100dvh`, fond noir et safe areas ;
- zoom borné 1×–4× ;
- commandes − / + / reset disponibles comme alternative mono-pointeur ;
- pinch deux doigts et pan un doigt lorsque zoomé ;
- arrière-plan rendu `inert` pendant le dialog et scroll body verrouillé ;
- Escape ferme le viewer et le focus revient au bouton `Agrandir` ;
- fermeture réinitialise la transformation à 1× ;
- aucune requête réseau supplémentaire pendant l’ouverture/zoom/pan ;
- M4-B historique préservé ;
- UI certifiée sur 390 / 430 / 768 avec zéro overflow et zéro erreur runtime.

## Preuves

- PR produit : #265.
- HEAD produit certifié : `da5c30c34f263e97cf65f6d741eb5869d8d6a717`.
- Squash merge `master` : `9ed2694a327e65ca823f63e4a161a98168d27856`.
- CI exact-head : run `32953694807` — **SUCCESS**.
  - `Tests & durcissement` backend : SUCCESS.
  - Frontend tests + build : SUCCESS.
  - Garde production : SUCCESS.
  - M4-A / M4-B / M4-C AFTER : SUCCESS.
- T2 Runtime Browser Matrix : run `32953694847` — **SUCCESS**.
- P7 Final Patient Matrix : run `32953694747` — **SUCCESS**.
- BEFORE exact produit : run `32949490898`, artifact M4-B `9599589719`.
- Goal : `.audit/mobile-m6-h-goal.md`.
- Mockup : `.audit/mobile-m6-h-mockup.svg`.
- AFTER exact-head : run `32953694807`, artifact M4-B `9601180254`.
- Digest AFTER : `sha256:4e333d85020315a8c3a5eb9b19568969a47fb19d936d7a7ca93b966481dc224e`.
- AFTER report : `m6hPass=true`, 3/3 viewports.

## Validation comportementale

Le harness M4-B étendu a exercé le viewer sur 390×844, 430×932 et 768×1024 :

- ouverture depuis le CTA exact ;
- viewer visible et racine applicative `inert` ;
- body scroll lock actif ;
- état initial 1× ;
- zoom via boutons ;
- pan de l’image zoomée ;
- pinch simulé via Pointer Events ;
- contrôles du viewer ≥48 px, réellement 52 px dans le produit ;
- aucune requête réseau supplémentaire pendant le viewer ;
- Escape ferme le dialog ;
- `inert` et scroll lock sont retirés ;
- focus restauré sur `Agrandir`.

## Validation visuelle

Comparaison BEFORE → mockup → AFTER inspectée sur 390 / 430 / 768.

- Écran normal : hiérarchie M4-B préservée ; CTA d’agrandissement lisible sans dominer la radio.
- Viewer : surface noire dédiée, image centrée et contrôles stables.
- Zoom 3× : cadrage de détail utile, sans débordement.
- Aucun overflow.
- Aucune erreur runtime.
- Cibles tactiles M6-H ≥52 px.

**Score visuel verrouillé : 9,7/10.**

La réserve de 0,3 concerne uniquement la densité de microcopy d’aide, volontairement discrète. Aucun correctif produit supplémentaire n’est justifié par cette réserve.

## Accessibilité / interaction

- Le pinch n’est pas obligatoire : les boutons − / + offrent une alternative mono-pointeur.
- La surface gérée par l’application utilise `touch-action: none` afin que les Pointer Events puissent piloter pan/zoom.
- Le fond est rendu `inert` tant que le dialog est ouvert.
- Le viewer supporte Escape et restaure le focus à la fermeture.

## Anomalie indépendante

`Catalog Connected Truth #300` échoue encore au step backend-only `Targeted backend truth tests`, avant tout AFTER. Le même défaut était déjà observé sur les runs Catalog précédents, dont un commit docs-only. M6-H ne modifie aucun backend : cette anomalie reste hors scope M6-H.

## Déploiement

Aucun déploiement Vercel.
