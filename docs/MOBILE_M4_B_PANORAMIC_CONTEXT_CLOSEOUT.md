# Digital Crown — Mobile Full Experience — M4-B Radio contextuelle — Closeout

Date : 2026-08-25
Status : CLOSED

## Goal

Depuis une radio panoramique précise dans l’historique desktop, générer un pont QR opaque qui ouvre exactement cette radio sur le mobile appairé, sans exposer de patient ID, d’analysis ID ni de chemin média dans le QR ou l’URL mobile.

## Produit exact

- base : `c6de4b7a86acc33ecfc2ae09e2b10da452281590`
- HEAD produit : `d4ae66e7e66a4955efed32083a39e6a7d6f1fae1`
- PR : #243
- merge : `f0c120868c71948bf835758f472c741179e7b128`
- structure PR : 1 commit / 10 fichiers / 0 behind
- CI : #1826 / run `32803721352`
- Vercel : aucun

## Résultat

- bridge ressource M4-A généralisé de `patient` vers `patient + panoramic` sans dupliquer le protocole ;
- permission `panoramic`, cabinet/tenant, patient, appareil et existence de l’analyse revalidés côté serveur ;
- QR opaque : seul `token=<pairing token>` est transporté vers `/mobile/onboarding` ;
- aucun `analysis_id`, `resource_id`, `patient_id`, `image_path` ou nom média dans le QR/URL ;
- média panoramique servi par POST authentifié `context_key` + bearer mobile, puis Blob URL côté client ;
- route finale mobile `/mobile/context` sans ID ni query ;
- action `Ouvrir sur mobile` ajoutée sur l’examen panoramique exact ;
- modal QR rendu via portal `document.body`, hors stacking context de l’historique ;
- fausse Corbeille/Restaurer retirée : l’UI reflète désormais le hard-delete réel et audité du backend ;
- suppression et contrôles touchés mis à au moins 44 px ;
- M4-A Patient recertifié sans régression.

## BEFORE

Run evidence-first `32788361811` : SUCCESS.

Artifact :
- id `9542280515`
- nom `mobile-m4b-panoramic-before-diagnostic`
- digest `sha256:fa3460120e1c68018bf0bc21799d75273ac4d97ccf484b92a594ad3988e7eaf8`

Constats :
- 7/7 captures ;
- historique réel cassé par `panoramic-trash` 404 ;
- 12 erreurs runtime liées à cet endpoint absent ;
- cible suppression : 40 px ;
- boutons de modalité : 40 px ;
- contexte mobile `panoramic` non supporté ;
- 0 overflow horizontal.

## Goal visuel / cible

Cible figée après BEFORE et avant implémentation :
- CTA explicite sur l’examen exact ;
- modal QR contextualisé et tactile ;
- mobile `Radio panoramique` avec patient, date, image, statut du rapport et retour ;
- identité visuelle Digital Crown conservée ;
- aucun contrôle M4-B <44 px.

Le mockup avait été créé comme objet Git de préparation hors tree final de la branche audit ; son contrat visuel a été conservé dans la PR et vérifié contre l’AFTER, mais l’objet dangling n’est pas référencé comme fichier canonique.

## AFTER exact-head

Job `M4-B Panoramic contextual bridge AFTER` de CI #1826 : SUCCESS.

Artifact :
- id `9547429867`
- nom `mobile-m4b-panoramic-after`
- head SHA `d4ae66e7e66a4955efed32083a39e6a7d6f1fae1`
- digest `sha256:b82c9d010c2b0db8f5d09f90216c3a36b34ea5508ead44bd2e73f41f476f11d5`

Gates :
- 7/7 captures ;
- desktop : 768×1024 et 1280×900 ;
- mobile : 390×844, 430×932, 768×1024 ;
- `safePairingBodies = true` ;
- fausse route `panoramic-trash` absente ;
- route mobile finale `/mobile/context` sans ID/query ;
- 0 erreur runtime ;
- 0 overflow horizontal ;
- aucun contrôle M4-B <44 px.

Score visuel final : **9,5/10**.

## Preuve backend et régression

CI #1826 : SUCCESS.

- backend : **2800 passed / 8 skipped / 0 failed** ;
- 4 warnings SQLAlchemy existants dans `superadmin.py`, non liés à M4-B ;
- frontend tests : SUCCESS ;
- frontend build : SUCCESS ;
- garde production négative : SUCCESS ;
- M4-A Patient contextual bridge AFTER : SUCCESS ;
- T2 #990 : SUCCESS ;
- Catalog #263 : SUCCESS ;
- Patient P7 #289 : SUCCESS.

## Post-merge

`master` vérifié sur `f0c120868c71948bf835758f472c741179e7b128`, avec `d4ae66e7e66a4955efed32083a39e6a7d6f1fae1` comme parent produit.

## Conclusion

M4-B Radio contextuelle est CLOSED.

M4 reste IN PROGRESS. Restant canonique : Document contextuel → RDV contextuel → matrice erreurs/retour/expiration au niveau ressource.