# M6-F — Partage mobile contextuel sûr — Closeout

Date : 2026-08-26
État : **CLOSED**

## Goal

Permettre depuis le contexte Document mobile exact de remettre volontairement le fichier déjà autorisé au partage natif de l’OS, sans exposer URL, token de bridge, `context_key`, nom patient, nom de fichier original potentiellement sensible ou texte prérempli.

## Succès observé

- Le partage est limité au contexte `document` déjà résolu et au Blob déjà chargé par M4-C.
- `navigator.share()` est déclenché depuis le geste utilisateur, sans requête réseau préalable.
- `navigator.canShare({ files })` est obligatoire ; sinon le produit reste fail-closed et conserve `Télécharger` comme fallback explicite.
- `ShareData` contient uniquement `files` : aucune clé `url`, `text` ou `title`.
- Le fichier remis au share sheet est renommé génériquement `document-digital-crown.<ext>`.
- L’annulation native `AbortError` reste silencieuse ; une autre erreur affiche un message générique sans détail sensible.
- `Ouvrir`, `Télécharger`, retour mobile et protocole M4-C sont préservés.
- UI certifiée sur 390 / 430 / 768 px avec cibles M6-F >=48 px, zéro overflow et zéro erreur runtime.

## Preuves

- PR produit : #263.
- HEAD produit certifié : `b5b349606fecb805fd5902189298bf30c238a2a0`.
- Squash merge `master` : `731e1efc1b22c823cb6763d28dc551c974b1301d`.
- CI exact-head : run `32949490898` — **SUCCESS**.
  - `Tests & durcissement` backend : SUCCESS.
  - Frontend tests + build : SUCCESS.
  - Garde production : SUCCESS.
  - M4-A / M4-B / M4-C AFTER : SUCCESS.
- T2 Runtime Browser Matrix : run `32949491080` — **SUCCESS**.
- P7 Final Patient Matrix : run `32949490982` — **SUCCESS**.
- BEFORE exact produit : run `32916285437`, artifact M4-C `9588310220`.
- Goal : `.audit/mobile-m6-f-goal.md`.
- Mockup : `.audit/mobile-m6-f-mockup.svg`.
- AFTER exact-head : run `32949490898`, artifact `9599594152`.
- Digest AFTER : `sha256:92c46a564bff5ce5f5b37946a67d220e6808dc55e26750d3473f550b79338dcf`.
- Viewports AFTER : 390×844, 430×932, 768×1024.

## Validation comportementale

Le harness M4-C étendu a exercé le partage sur les trois viewports :

- 3/3 appels au share sheet avec une seule clé `files` ;
- fichier `document-digital-crown.pdf` ;
- type `application/pdf` ;
- aucun nom `BENNANI` ou `Ordonnance` ajouté au fichier partagé ;
- fallback unsupported observé avec absence du CTA Partager et maintien de `Télécharger`.

## Validation visuelle

Comparaison BEFORE → mockup → AFTER inspectée sur 390 / 430 / 768.

- Hiérarchie clarifiée : `Ouvrir` / `Télécharger` secondaires, partage natif en action principale lorsque supporté.
- Microcopy sécurité visible.
- Aucun overflow.
- Aucune erreur runtime.
- Cibles tactiles M6-F >=48 px.

**Score visuel verrouillé : 9,8/10.**

## Limite sécurité explicitement non sur-vendue

Le document partagé peut lui-même contenir des données patient ou cliniques. M6-F ne prétend pas rendre le contenu du document anonyme. La garantie certifiée est plus précise : **Digital Crown n’ajoute au partage ni URL, ni token, ni `context_key`, ni texte/titre, ni nom de fichier patient/original potentiellement sensible**. La destination finale est choisie explicitement par l’utilisateur dans le share sheet natif de l’OS.

## Anomalie indépendante

`Catalog Connected Truth #298` a échoué avant son AFTER sur le step `Targeted backend truth tests`. Le même step avait déjà échoué sur `Catalog #297`, exécuté sur le commit précédent docs-only. Le workflow lance exclusivement `test_catalog_connected_truth.py`, `test_patient_p3_master_plan_revisions.py` et `TestCatalogQuickAdd` à cette étape. M6-F ne modifie aucun backend : ce rouge est hors scope M6-F.

## Déploiement

Aucun déploiement Vercel.
