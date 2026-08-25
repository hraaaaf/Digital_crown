# M6-A — Photo clinique contextuelle — Closeout canonique

Date : 2026-08-25
État : CLOSED

## Goal

Depuis un contexte mobile Patient exact, permettre au praticien de prendre une photo clinique au fauteuil, de la prévisualiser avant confirmation puis de l'archiver dans le dossier patient canonique, sans faire transiter de `patient_id` depuis le téléphone.

## Succès vérifié

- Patient exact résolu côté serveur depuis le `context_key` appairé.
- Action `Photo clinique` disponible sur 390 / 430 / 768 px.
- Sélection caméra/picker → preview → confirmation explicite → succès.
- Aucun archivage avant confirmation.
- Upload multipart lié au contexte ; aucun `patient_id` émis par le client.
- Source de vérité : `DocumentArchive` / `DocumentType.PHOTO_CLINIQUE`.
- Permission `patients`, tenant, utilisateur, appareil et ressource revalidés au moment de l'upload.
- Fichiers JPEG / PNG / WebP décodés réellement par Pillow, limite brute 12 MiB, limite 50 MP, orientation EXIF normalisée, réécriture JPEG sans métadonnées, nom de fichier généré côté serveur.
- 0 overflow horizontal et 0 erreur runtime dans l'AFTER.
- Nouveaux contrôles tactiles : minimum 52 px ; action principale : 66 px.

## Preuves UI/UX

### BEFORE

- Run : `32859436355` — SUCCESS.
- Artifact : `9567596003`.
- Digest : `sha256:3c536022957b961b6612f05820799b5c6c4f8542971ed18b7be3f657615cfd97`.
- Viewports : 390×844, 430×932, 768×1024.
- Constat : contexte BENNANI Sara exact et propre, mais aucune action `Photo clinique` et aucun input caméra ; 0 overflow / erreur runtime.

### Goal + référence visuelle

- Commit audit : `43d81ff50f37a8399c8b77db271a1ce036e1f75f`.
- Goal et mockup figés avant code produit.
- Cible : CTA Photo clinique → bottom sheet d'aperçu avec patient exact → Reprendre / Enregistrer → succès explicite.

### AFTER

- HEAD produit exact : `24dcdc5543f68fd31b65a4facfa824f4a51cfbd8`.
- Run : `32864337475` — SUCCESS.
- Artifact : `9569518739`.
- Digest : `sha256:69dd249809ba98246b84c298cd5cdffdc387d104ba1dee2e3fa81fde1b76fd1e`.
- 9/9 captures : action / preview / saved × 390 / 430 / 768.
- `capture=environment` avec fallback picker via input fichier.
- 3 uploads observés : `context_key` présent ; `patient_id` absent.
- 0 overflow ; 0 erreur runtime.
- Comparaison BEFORE → mockup → AFTER conforme.

## Score visuel

**9,7/10.**

Forces : hiérarchie nette, CTA clinique évident sans surcharger le dossier, preview explicite avant persistance, état succès lisible, excellente tenue 390/430 et composition centrée propre à 768.

Limite de preuve : le média utilisé par le harness AFTER est une image synthétique neutre ; la qualité colorimétrique d'une vraie photographie clinique sera à recroiser sur appareils physiques lors de la certification finale.

## Preuves produit / CI

- Base : `432955745da8a39fcf63277859ff4ec973722c9c`.
- Prepare canonique : run `32863757202` — SUCCESS.
- Produit : 1 commit, 3 fichiers, 0 behind.
- PR : #252.
- CI #1854 : run `32864234840` — SUCCESS.
  - backend : **2812 passed, 8 skipped**, 4 warnings non bloquants préexistants ;
  - frontend tests + build : SUCCESS ;
  - garde production : SUCCESS ;
  - régressions M4-A / M4-B / M4-C : SUCCESS.
- T2 #1004 : run `32864234205` — SUCCESS.
- Catalog #277 : run `32864234328` — SUCCESS.
- Patient P7 #303 : run `32864234154` — SUCCESS.
- Merge PR #252 : `5657ce7dfa529b39aaae2e562399938524bc43bd`.

## Run de préparation dupliqué

Le run `32863836802` a été déclenché par une course de déclenchement du workflow d'audit. Son build et ses gates statiques étaient verts ; il a échoué uniquement à l'étape de création/push parce que la branche produit avait déjà été créée par le run canonique #1. Il n'a créé aucune modification produit supplémentaire et n'est pas un échec M6-A.

## Dette non bloquante

Un retry manuel après perte de la réponse HTTP d'un upload pourtant archivé peut créer une nouvelle version. Il n'existe pas de fail-open, mélange de patient ou perte de permission ; l'idempotence du retry doit être traitée avec la future logique offline/queue plutôt que d'élargir ce lot.

## Déploiement

Aucun Vercel. Aucun déploiement demandé ni effectué.

## Next

M6-B — Scan de documents contextuel : audit / BEFORE avant tout changement produit.
