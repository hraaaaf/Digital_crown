# R5 — QR documentaire — CLOSEOUT

Date : 2026-08-20

## Goal
Rendre les QR documentaires factuels et explicites sans inventer de signature électronique ni de paiement en ligne, tout en préservant les comportements historiques hors correction ciblée.

## Résultat vérifié
- 7 types QR conservés : Contact, Site Web, Instagram, WhatsApp, Maps, Vérification du document, Suivi du paiement.
- `Signature` remplacé par `Vérification du document`.
- `Paiement` remplacé par `Suivi du paiement` avec avertissement explicite : aucun paiement n'est encaissé ici.
- VALIDATION encode `/api/documents/verify/<document>`.
- PAYMENT encode `/api/documents/track/<document>`.
- Website / Instagram / WhatsApp affichent une aide adaptée ; Maps utilise l'adresse du cabinet.
- Aucun changement DB ni déploiement Vercel.

## Preuves UI/UX
- BEFORE canonique : run `32370918895` — SUCCESS — artifact `9407139877`.
- AFTER final au HEAD produit corrigé : run `32374163733` — SUCCESS.
- Artifact AFTER : `9408382545`.
- Digest : `sha256:7272aa7d2f74c74516f6daf5b8a3f5f9b8d2b9232ee95781e9a101651700607c`.
- Viewports certifiés : 390 / 430 / 768 / 1024 / 1440 px.
- Aucun overflow horizontal et aucune erreur runtime sur les 5 viewports.
- Score visuel : **9,4/10**.

Le run BEFORE lancé sur le HEAD final échoue volontairement : ce workflow vérifie la présence de l'ancien état `Signature` / `Paiement` et n'est pas un gate AFTER.

## Preuves code et régression
- Commit produit : `3304b6f9dfd9331d764f52758672b255649d6a0c`.
- Correction harness AFTER : `eed6631ba418e6a09fdb7e7b09f519df6dd4d29f`.
- Correctif compatibilité façade `ImageReader` : `a40722fc3db8f1c89d25ee66e37143034029654c`.
- CI : run `32374163732` — SUCCESS.
- T2 Runtime Browser Certification : run `32374163943` — SUCCESS.
- Settings RBAC Visual Certification : run `32374163649` — SUCCESS.
- Patient P7 Final Certification : run `32374163768` — SUCCESS.
- `base_template_core.py` préservé : `ef695ba7abc0c8b6c98b3be255352996f806a1e9`.
- `StudioControlsCore.tsx` préservé : `38f08ee3b80b03ea4083c830749177c557012905`.

## Dette non bloquante
Le texte Maps peut produire la formulation redondante `Destination : Source : adresse du cabinet`. Le comportement est correct ; seule la microcopie reste perfectible.

## Verdict
R5 est fonctionnellement et visuellement certifié sur le HEAD produit `a40722fc3db8f1c89d25ee66e37143034029654c`. Le présent commit ne contient que ce closeout documentaire.
