# M6-E — Communication patient mobile — Closeout

Date : 2026-08-26
État : **CLOSED**

## Goal

Permettre depuis le contexte Patient mobile de contacter le patient en un geste par appel ou WhatsApp, sans inventer d'indicatif pour un numéro ambigu, sans préremplir de donnée patient/clinique et sans dégrader les actions Agenda / Photo / Scan.

## Succès observé

- `Appeler` conserve un lien `tel:` sûr ; un numéro local reste appelable sans être transformé artificiellement en numéro international.
- WhatsApp est activé uniquement lorsqu'un numéro international explicite est disponible (`+...` ou notation internationale `00...` valide).
- Numéro local/ambigu, absent ou invalide : WhatsApp reste fail-closed avec microcopy explicative.
- URL WhatsApp composée uniquement du numéro international normalisé ; aucun `?text=`, nom patient, motif, note, montant ni contenu clinique.
- Lien externe WhatsApp ouvert avec `noopener noreferrer`.
- Grille mobile Appeler / WhatsApp / Agenda certifiée avec cibles 64 px.
- Agenda, Photo et Scan restent fonctionnellement et visuellement préservés.
- Aucun changement backend, permission, modèle ou migration.

## Preuves

- PR produit : #261.
- HEAD produit certifié : `3c1ae523c7ced679f3b14a614d6b1ab1cfd58819`.
- Squash merge `master` : `3dc875f1816244fc567b58197f9cee23afc2199b`.
- CI exact-head : run `32916285437` — **SUCCESS**.
  - Frontend tests + build : SUCCESS.
  - Backend `Tests & durcissement` : SUCCESS.
  - Garde production : SUCCESS.
  - M4-A / M4-B / M4-C AFTER : SUCCESS.
- Patient P7 #322 : run `32916285977` — **SUCCESS**.
- P2 Onboarding #247 : run `32916285768` — **SUCCESS**.
- T2 Browser Matrix #1023 : run `32916285641` — **SUCCESS**.
- Runtime Contracts #1034 : run `32916285798` — **SUCCESS**.
- BEFORE : artifact `9587628216`, viewports 390 / 430 / 768 inspectés.
- Goal : `.audit/mobile-m6-e-goal.md`.
- Mockup : `.audit/mobile-m6-e-mockup.svg`.
- AFTER exact-head : artifact `9588307185`.
- Digest AFTER : `sha256:a280e7a5ed9121b2498df03dfa25d755fac632765ae84c90001e12759d66ef48`.
- Viewports AFTER : 390×844, 430×932, 768×1024.
- E2E Patient : 3/3 contextes conformes.
- Liens observés dans le harness : `tel:+212612345678` et `https://wa.me/212612345678` sans query/prefill.

## Validation visuelle

Comparaison BEFORE → mockup → AFTER inspectée sur les trois viewports.

- Trois actions compactes et lisibles sans écraser le contexte Patient.
- Cibles tactiles 64 px ; aucune cible M6-E sous 48 px.
- Agenda conserve sa priorité et Photo / Scan ne régressent pas.
- Zéro overflow horizontal.
- Zéro erreur runtime dans le harness.

**Score visuel verrouillé : 9,8/10.**

## Sécurité / confidentialité

- Aucun indicatif pays n'est deviné à partir d'un numéro local.
- Aucun texte ou contexte Patient n'est prérempli dans WhatsApp.
- Aucun nouvel endpoint ni stockage n'est introduit.
- Le numéro utilisé provient du contexte Patient déjà autorisé ; M6-E n'élargit pas les droits d'accès.

## Anomalie indépendante

`Catalog Connected Truth #296` (`32916285374`) est rouge sur le step `Targeted backend truth tests`, avant les étapes frontend/AFTER. Le diff M6-E est strictement 1 commit / 6 fichiers frontend + audit, sans fichier backend, dépendance ni workflow ; CI principale, backend, T2, Runtime Contracts et Patient P7 sont verts sur le même HEAD. Cette anomalie est donc classée hors scope M6-E et ne constitue pas une preuve de régression du lot.

## Déploiement

Aucun déploiement Vercel.
