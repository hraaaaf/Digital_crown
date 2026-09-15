# Prescription Pharmacology Morocco RCP M1

Status: ACTIVE — M1-B1 WAVE 1 RCP ACQUISITION

## Goal

Construire un snapshot local, versionné et vérifiable des preuves réglementaires/RCP AMMPS utiles à la pharmacologie dentaire, sans second moteur de prescription, sans dépendance réseau au runtime cabinet et sans promouvoir une donnée clinique non prouvée.

## Success

M1 est clos uniquement lorsque chaque présentation prioritaire possède une identité réglementaire unique, un statut AMM/commercialisation sourcé, un état RCP explicite (`PENDING_DOWNLOAD`, `SNAPSHOT_VERIFIED` ou `UNAVAILABLE_VERIFIED`) et, pour tout RCP capturé, une URL officielle exacte, une date et une empreinte SHA-256.

Aucune ligne M1 n'autorise à elle seule une posologie ou un passage vers `AUTO_OK_MAROC`.

## M1-A — clos et mergé

PR #517 mergée en squash : `d474ad18ba47d55a0d53f1f90e47a451f4dbac5e`.

Preuves exact-head avant merge sur `6ef95315d8d08e870cedddbfe1a3abbc329d8268` : CI #4391, PostgreSQL #790, Catalog Connected Truth #1285 et T2 Runtime #3275 success ; M6-I skipped attendu.

Post-merge master CI #4392 : frontend/build success, backend complet DB/patients/documents success, garde production success.

M1-A a livré le snapshot AMMPS courant package-level, `regulatory_presentation_id`, isolation des APIs historiques et APIs réglementaires fail-closed, sans activation clinique.

## M1-B0 — fondation RCP close et mergée

PR #518 mergée en squash : `81bf142021cdf4770e9c6ca92078306ac4898783`.

Preuves exact-head avant merge sur `4c01107c50a18a4055b818c564b63408679ac034` : CI #4399 success, PostgreSQL #797 success, T2 Runtime #3282 success, M6-I skipped attendu.

M1-B0 a livré :

- `backend/data/medications_ma_ammps_rcp_manifest_2026.json` ;
- schéma `m1b-rcp.1` ;
- 8/8 présentations d'amoxicilline liées à leur `regulatory_presentation_id` ;
- toutes restent `PENDING_DOWNLOAD` ;
- lecteur documentaire fail-closed ;
- `SNAPSHOT_VERIFIED` exige URL AMMPS, date, SHA-256 et artefact sous `backend/data/rcp/...` ;
- `UNAVAILABLE_VERIFIED` exige une preuve officielle explicite d'absence ;
- aucun fallback CNOPS/RMMG ;
- aucune extraction clinique.

Post-merge CI #4409 a été annulée/supplantée avant la régression complète ; elle n'est pas retenue comme preuve post-merge. Les preuves pre-merge exact-head restent vertes.

## M1-B1 — Wave 1 acquisition

Branche : `feat/prescription-pharmacology-morocco-rcp-m1b-wave1`, créée depuis le merge exact M1-B0 `81bf142021cdf4770e9c6ca92078306ac4898783`.

Queue machine : `docs/audits/PRESCRIPTION_PHARMACOLOGY_MOROCCO_RCP_WAVE1_QUEUE.json`.

Univers exact Wave 1 :

1. paracétamol ;
2. ibuprofène ;
3. amoxicilline ;
4. phénoxyméthylpénicilline ;
5. métronidazole ;
6. clarithromycine ;
7. clindamycine.

État vérifié au 2026-09-15 :

- 4 molécules `READY_FOR_CAPTURE_TRANSPORT` ;
- 1 `PENDING_RCP_LINK_CONFIRMATION` ;
- 1 `PENDING_CURRENT_PAGE_CONFIRMATION` ;
- 1 `PENDING_CURRENT_PRESENTATION_DISCOVERY` ;
- aucune molécule omise silencieusement ;
- aucune donnée clinique extraite.

Les pages AMMPS officielles exposent le bouton « Télécharger RCP » pour plusieurs présentations Wave 1. Le href/fichier cible n'est pas exposé de façon fiable par les moyens de fetch actuellement disponibles. Aucun `rcp_url`, hash ou `SNAPSHOT_VERIFIED` n'est donc fabriqué.

## Règles de capture

1. identifier la présentation réglementaire exacte ;
2. récupérer le document depuis l'AMMPS officielle ;
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
