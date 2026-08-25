# Digital Crown — Mobile Full Experience — M4-C Document contextuel — Closeout

Date : 2026-08-25
Status : CLOSED

## Goal

Depuis un `DocumentArchive` canonique précis dans la bibliothèque desktop, ouvrir exactement ce document sur le mobile appairé via un QR opaque, sans exposer patient ID, document ID ni chemin média dans le QR ou l’URL mobile.

## Produit exact

- base : `cb66d2f379803220d1a81f307db803737a167c94`
- HEAD produit : `684c526a92b63da3cd8ec37510a1ab4de8975384`
- PR : #244
- merge : `8a11a452cc7a3b14964a1908a32589700a4cb6f7`
- structure PR : 1 commit / 10 fichiers / 0 behind
- CI : #1834 / run `32835212709`
- Vercel : aucun

## Résultat

- bridge ressource généralisé à `document` en réutilisant le noyau Patient/Panoramique ;
- permission dérivée du `document_type` réel et revalidée pour l’émetteur, la cible mobile et chaque ouverture ;
- document ACTIF, tenant/cabinet, patient, appareil et existence de la ressource revalidés serveur ;
- QR opaque : aucun patient ID, document ID ou chemin média transporté dans le QR/URL mobile ;
- média servi par POST authentifié `context_key`, puis Blob URL côté client ;
- route finale mobile `/mobile/context` sans identifiant ni query ;
- action `Ouvrir sur mobile` ajoutée au document canonique exact ;
- documents legacy explicitement marqués `desktop uniquement`, sans Edit/Corbeille/Mobile fictifs ;
- Voir/Télécharger desktop passent par `/api/documents/{id}/download` et la permission documentaire canonique ;
- Corbeille/Restaurer/Suppression canonique alignées sur la permission typée du document ;
- contrôles M4-C tactiles portés à au moins 44 px ;
- MobileContext Document affiche patient, type/date, aperçu si applicable et actions Ouvrir/Télécharger ;
- garde M4-B `image/*` conservée après généralisation du média.

## BEFORE

Run evidence-first `32829274229` : SUCCESS.

Artifact :
- id `9556142341`

Constats verrouillés :
- 7/7 captures inspectées ;
- bridge Document absent ;
- contexte mobile Document non supporté ;
- actions documentaires critiques à 28×28 px ;
- legacy proposant des actions incompatibles avec le backend réel ;
- Goal + mockup versionnés avant implémentation ;
- aucun défaut d’overflow signalé dans le harness.

## Goal visuel / cible

Cible figée avant implémentation :
- CTA explicite sur le document exact ;
- modal QR contextualisé et tactile ;
- contexte mobile `Document` avec patient, type/date, nom du fichier, aperçu si applicable et actions utiles ;
- legacy clairement limité au desktop ;
- aucun contrôle M4-C <44 px ;
- identité visuelle Digital Crown conservée.

## AFTER visuel

Inspection visuelle déjà réalisée sur le produit byte-identique avant l’ultime correction de test filesystem :
- 8/8 captures ;
- 3/3 contextes Document exacts ;
- 0 erreur runtime ;
- 0 overflow horizontal ;
- aucun contrôle M4-C <44 px ;
- score visuel : **9,6/10**.

Artifact inspecté :
- id `9557959164`
- digest `sha256:c90a9868958caa44fa1408e1c85593105a18d6bbb78f7e3b0d59f4aa21d33559`

Entre ce produit inspecté et le HEAD final `684c526a...`, aucune ligne produit n’a changé : seule l’isolation filesystem du test backend a été corrigée.

## AFTER exact-head final

Job `M4-C Document contextual bridge AFTER` de CI #1834 : SUCCESS sur `684c526a92b63da3cd8ec37510a1ab4de8975384`.

Artifact exact-head :
- id `9558362281`
- nom `mobile-m4c-document-after`
- digest `sha256:5b2770f9affe4c4c22c667ff19d94eb1edbc991ed55b27e4c315f0fbd79d7226`

Gates automatisés exact-head :
- 8 captures ;
- 3 contextes mobile Document ;
- pairing body sûr ;
- document exact visible ;
- route mobile `/mobile/context` sans ID/query ;
- média contextuel observé ;
- aucune requête legacy trash ;
- 0 erreur runtime ;
- 0 overflow horizontal ;
- aucun contrôle M4-C <44 px.

## Preuve CI et régression

Tous les workflows PR associés au HEAD final sont SUCCESS :
- CI #1834 / `32835212709` : SUCCESS ;
- T2 Runtime Browser Certification #996 / `32835212714` : SUCCESS ;
- Catalog Connected Truth Certification #269 / `32835212732` : SUCCESS ;
- Patient P7 Final Certification #295 / `32835212741` : SUCCESS ;
- Settings TemplateEngine Reachability #43 / `32835212727` : SUCCESS.

Dans CI #1834 :
- Tests & durcissement : SUCCESS ;
- Frontend tests & build : SUCCESS ;
- garde production négative : SUCCESS ;
- M4-A Patient contextual bridge AFTER : SUCCESS ;
- M4-B Panoramic contextual bridge AFTER : SUCCESS ;
- M4-C Document contextual bridge AFTER : SUCCESS.

Le dernier échec avant ce run provenait de l’isolation filesystem du test. Le test final utilise un `tmp_path` média privé partagé par les composants de test, sans modifier le stockage runtime produit.

## Post-merge

PR #244 passée ready puis mergée sans divergence de base. Merge produit : `8a11a452cc7a3b14964a1908a32589700a4cb6f7`.

## Conclusion

M4-C Document contextuel est CLOSED.

M4 reste IN PROGRESS. Restant canonique : RDV contextuel exact → matrice finale erreurs / retour / expiration au niveau ressource.
