# Prescription Pharmacology Morocco RCP M1

Status: ACTIVE — M1-B0 RCP EVIDENCE FOUNDATION

## Goal

Construire un snapshot local, versionné et vérifiable des preuves réglementaires/RCP AMMPS utiles à la pharmacologie dentaire, sans second moteur de prescription, sans dépendance réseau au runtime cabinet et sans promouvoir une donnée clinique non prouvée.

## Success

M1 est clos uniquement lorsque chaque présentation prioritaire possède une identité réglementaire unique, un statut AMM/commercialisation sourcé, un état RCP explicite (`PENDING_DOWNLOAD`, `SNAPSHOT_VERIFIED` ou `UNAVAILABLE_VERIFIED`) et, pour tout RCP capturé, une URL officielle exacte, une date et une empreinte SHA-256.

Aucune ligne M1 n'autorise à elle seule une posologie ou un passage vers `AUTO_OK_MAROC`.

## M1-A — clos et mergé

PR #517 mergée en squash sur master : `d474ad18ba47d55a0d53f1f90e47a451f4dbac5e`.

Preuves exact-head avant merge sur `6ef95315d8d08e870cedddbfe1a3abbc329d8268` :

- CI #4391 : success ;
- PostgreSQL #790 : success ;
- Catalog Connected Truth #1285 : success ;
- T2 Runtime #3275 : success ;
- M6-I : skipped attendu.

Post-merge CI master #4392 : démarrée ; conclusion finale encore requise pour closeout post-merge.

M1-A a livré :

- snapshot AMMPS courant package-level ;
- `regulatory_presentation_id` distinct par conditionnement ;
- APIs historiques CNOPS/RMMG inchangées ;
- APIs réglementaires fail-closed sur le snapshot AMMPS courant uniquement ;
- aucune posologie, durée, décision clinique, DB, patient, document ou UI modifiés.

## M1-B0 — fondation de preuve RCP

Branche active : `feat/prescription-pharmacology-morocco-rcp-m1b-foundation`, créée depuis le merge M1-A exact `d474ad18ba47d55a0d53f1f90e47a451f4dbac5e`.

Fondation actuellement implémentée :

- `backend/data/medications_ma_ammps_rcp_manifest_2026.json` ;
- schéma `m1b-rcp.1` ;
- 8/8 présentations AMMPS d'amoxicilline liées à leur `regulatory_presentation_id` exact ;
- toutes les entrées restent `PENDING_DOWNLOAD` ;
- aucune extraction clinique ;
- `SNAPSHOT_VERIFIED` exige URL officielle, date, artefact local et SHA-256 valide ;
- absence de lien observé n'est jamais convertie automatiquement en `UNAVAILABLE_VERIFIED` ;
- source secondaire autorisée uniquement comme recoupement, jamais comme preuve primaire d'activation ;
- lecteur documentaire isolé `backend/services/medication_rcp_manifest.py` ;
- manifest inclus dans le packaging desktop ;
- tests fail-closed dédiés ajoutés.

## Wave 1 M1-B

Ordre prioritaire :

1. paracétamol ;
2. ibuprofène ;
3. amoxicilline ;
4. phénoxyméthylpénicilline ;
5. métronidazole ;
6. clarithromycine ;
7. clindamycine.

AMMPS expose actuellement des liens « Télécharger RCP » pour plusieurs présentations exactes Wave 1. Le href du document n'étant pas encore capturé de façon fiable dans notre flux, aucune URL RCP ni aucun hash n'est inventé : l'état reste `PENDING_DOWNLOAD`.

## Règles de capture

1. identifier la présentation réglementaire exacte ;
2. récupérer le RCP depuis l'AMMPS officielle ;
3. conserver URL officielle exacte + date ;
4. calculer SHA-256 ;
5. seulement alors passer à `SNAPSHOT_VERIFIED` ;
6. extraire ensuite uniquement les champs explicitement présents ;
7. toute donnée absente/ambiguë reste `PENDING_*` ou review ;
8. une recherche web négative ne prouve jamais l'absence d'un RCP.

## Non-régression obligatoire

- aucun changement DB ;
- aucun changement patient/document ;
- aucun changement UI ;
- aucun fallback réglementaire vers CNOPS/RMMG ;
- aucun nouveau `AUTO_OK_MAROC` ;
- aucun schéma thérapeutique nouveau activé ;
- aucune disponibilité pharmacie temps réel fabriquée.

## Human gate

Toute donnée RCP extraite susceptible de modifier une décision clinique reste soumise à validation médicale avant M2.

Aucun Vercel.
