# DIGITAL CROWN — MOB-5F QUICK DOCUMENT STUDIO — PROOF

Status: PRE-MERGE — FINAL PRODUCT CERTIFICATION PENDING

## Goal

Créer rapidement un document depuis le cockpit patient mobile en réutilisant le moteur canonique, avec RBAC serveur, preview avant archivage et aucune donnée/DB documentaire parallèle.

## BEFORE certifié

- product baseline: `e30b858f58686f5f7bef19ca93f1c5dae42929c9`
- run: `34143420251` — SUCCESS
- artifact: `10026785108`
- digest: `sha256:b827b8b31f7bb604667d1a8df624eda98b1aa794ac25145f8c7acec72af5bdff`
- viewports: 390x844 / 430x932 / 768x1024
- HTTP 200, 0 page error, 0 console error, 0 overflow horizontal
- CTA `Créer un document`: absent

## Produit implémenté

- CTA unique `Créer un document` depuis le patient sélectionné;
- familles: Ordonnance / Certificat / Devis / Honoraires / Document libre;
- familles filtrées par capacités serveur chiffrées;
- Honoraires et Devis alignés sur le guard canonique `accounting`;
- formulaire compact par type;
- preview serveur `preview=true&archive=false`;
- payload verrouillé après preview;
- confirmation `Archiver le document`;
- archivage avec le même payload via `/api/documents/generate`;
- rappel de l'alerte médicale dans le flow Ordonnance;
- preview démo sans appel réseau;
- aucun nouveau modèle DB, générateur PDF ou moteur documentaire;
- aucun Vercel.

## Corrections issues de la validation croisée

Avant la certification finale, trois écarts ont été détectés et corrigés:
1. `teeth_data={}` corrigé en liste conforme à `DevisData`;
2. Honoraires à 0 refusé côté UI comme le validator backend;
3. capacité Honoraires corrigée de `payments` vers le guard réel `accounting`.

## Gate final attendu

La preuve AFTER finale doit être issue du HEAD produit `91688ffc2d5bf97e584844f972a12df717fc74da` ou d'un HEAD produit ultérieur explicitement vérifié, et démontrer aux 3 viewports:
- CTA présent;
- cinq familles présentes dans la preview SuperUser;
- flow Certificat jusqu'à `Aperçu prêt` + `Archiver le document`;
- 0 API request en preview;
- 0 page error;
- 0 console error;
- 0 overflow horizontal;
- tests ciblés et build verts.

MOB-5F n'est pas CLOSED avant PR verte, merge exact, post-merge CI et closeout canonique.
