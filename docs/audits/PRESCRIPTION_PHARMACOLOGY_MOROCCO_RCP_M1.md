# Prescription Pharmacology Morocco RCP M1

Status: ACTIVE — M1-B2 FIRST VERIFIED RCP CAPTURE TRANSPORT

## Goal

Construire un snapshot local, versionné et vérifiable des preuves réglementaires/RCP AMMPS utiles à la pharmacologie dentaire, sans second moteur de prescription, sans dépendance réseau au runtime cabinet et sans promouvoir une donnée clinique non prouvée.

## Success

M1 est clos uniquement lorsque chaque présentation prioritaire possède une identité réglementaire unique, un statut AMM/commercialisation sourcé, un état RCP explicite (`PENDING_DOWNLOAD`, `SNAPSHOT_VERIFIED` ou `UNAVAILABLE_VERIFIED`) et, pour tout RCP capturé, une URL officielle exacte, une date et une empreinte SHA-256 concordant avec l'artefact local réellement présent.

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

## M1-B1 — Wave 1 acquisition close et mergée

PR #519 mergée en squash : `21651f22df9ba5210078969aa46abc527ba9e2bd`.

Preuves exact-head avant merge sur `65a24f69366865811e2f22e432e2af69e4650a90` :

- CI #4411 : success ;
- PostgreSQL #806 : success ;
- Catalog Connected Truth #1288 : success ;
- T2 Runtime #3291 : success ;
- M6-I : skipped attendu.

Le post-merge CI #4418 a été annulé immédiatement parce que `master` a avancé sur un commit documentaire Patient Companion D1. Il n'est pas retenu comme preuve post-merge.

Queue machine : `docs/audits/PRESCRIPTION_PHARMACOLOGY_MOROCCO_RCP_WAVE1_QUEUE.json`.

Univers exact Wave 1 :

1. paracétamol ;
2. ibuprofène ;
3. amoxicilline ;
4. phénoxyméthylpénicilline ;
5. métronidazole ;
6. clarithromycine ;
7. clindamycine.

## M1-B1 evidence refresh — PR #522 mergée

PR #522 `docs(pharmacology): refresh Wave 1 RCP evidence` mergée en squash : `12f2550aaa38f3045095152ab862b587db109238`.

HEAD exact pré-merge : `0f9af14763bc6d85bc3a028d12f186c55e7ff746`.

Certifications exact-head : CI #4447 success, PostgreSQL #838 success, Catalog Connected Truth #1301 success, T2 Runtime #3323 success, M6-I skipped attendu.

État Wave 1 vérifié après #522 :

- 5 molécules `READY_FOR_CAPTURE_TRANSPORT` : paracétamol, ibuprofène, amoxicilline, phénoxyméthylpénicilline, clarithromycine ;
- 1 molécule `PENDING_RCP_LINK_CONFIRMATION` : métronidazole ;
- 0 molécule `PENDING_CURRENT_PAGE_CONFIRMATION` ;
- 1 molécule `PENDING_CURRENT_PRESENTATION_DISCOVERY` : clindamycine ;
- aucune donnée clinique extraite ;
- une recherche négative ne vaut jamais preuve d'absence réglementaire.

Pour l'ibuprofène, le bouton RCP oral est confirmé sur la recherche médicaments AMMPS courante. Pour le métronidazole, les présentations orales génériques package-level et EAN sont confirmées dans le RMMG AMMPS janvier 2026, mais le lien RCP exact reste à confirmer.

Post-merge master CI #4460 a été lancé sur `12f2550aaa38f3045095152ab862b587db109238` ; son état final doit être revérifié avant closeout.

## M1-B2 — first verified capture transport

Branche active resynchronisée : `feat/prescription-pharmacology-morocco-rcp-first-capture-sync`.

Base réelle : `12f2550aaa38f3045095152ab862b587db109238`.

Cette branche succède techniquement à la PR #520 sans force-push : les deux commits master arrivés depuis la base initiale de #520 ne touchaient aucun des trois fichiers M1-B2. Les fichiers exécutables `backend/services/medication_rcp_manifest.py` et `backend/tests/test_medication_rcp_manifest_m1b.py` ont été réappliqués byte-identiques depuis le HEAD #520 `15430e879f8e763e55f117842ad27364df8257d5`, puis le présent document a été réaligné sur l'état Wave 1 après #522.

Infrastructure actuellement implémentée :

- helper documentaire `prepare_verified_snapshot_entry(...)` dans `backend/services/medication_rcp_manifest.py` ;
- aucun téléchargement réseau ;
- aucune persistance automatique ;
- aucune extraction clinique ;
- source obligatoire = entrée `PENDING_DOWNLOAD` déjà fail-closed ;
- artefact capturé doit commencer par la signature PDF ;
- URL RCP obligatoire en HTTPS sur domaine AMMPS officiel ;
- date de contrôle strictement `YYYY-MM-DD` ;
- artefact local limité à `backend/data/rcp/*.pdf` ;
- l'artefact déclaré doit exister réellement ;
- les octets de l'artefact local doivent correspondre exactement aux octets capturés ;
- SHA-256 calculé sur l'artefact local réel, pas sur une valeur déclarative ;
- `snapshot_is_verified(...)` relit l'artefact local et refuse un hash discordant ou un fichier absent ;
- résultat construit par copie, sans mutation silencieuse de l'entrée source ;
- tests négatifs couvrent faux PDF, domaine non officiel, date invalide, chemin non sûr, fichier absent, hash faux, mismatch d'octets et entrée source polluée.

État de preuve : aucun PDF RCP AMMPS n'a encore été physiquement capturé dans ce lot. Donc aucune entrée n'est encore promue en `SNAPSHOT_VERIFIED`.

Le premier objectif de capture reste AMOXICILLINE SP 1 G comprimé dispersible boîte de 12, `regulatory_presentation_id = ammps-reg:6fd268f476e7efe0c11f0c4b`, page AMMPS 42. Le bouton RCP est observé mais le document cible exact n'est toujours pas exposé par les fetchs disponibles. Aucun `rcp_url` n'est inventé.

Une revue scientifique indépendante distincte de l'agent auteur reste obligatoire avant merge de M1-B2. Une auto-revue ne vaut pas cette gate.

## Règles de capture

1. identifier la présentation réglementaire exacte ;
2. récupérer le document depuis l'AMMPS officielle ;
3. conserver URL officielle exacte + date ;
4. conserver l'artefact réel sous `backend/data/rcp/...` ;
5. vérifier que les octets locaux correspondent aux octets capturés puis calculer SHA-256 ;
6. seulement alors passer à `SNAPSHOT_VERIFIED` ;
7. extraire ensuite uniquement les champs explicitement présents ;
8. toute donnée absente/ambiguë reste `PENDING_*` ou review ;
9. une recherche web négative ne prouve jamais l'absence d'un RCP.

## Non-régression obligatoire

- aucun changement DB ;
- aucun changement patient/document ;
- aucun changement UI ;
- aucun fallback réglementaire vers CNOPS/RMMG ;
- aucun nouveau `AUTO_OK_MAROC` ;
- aucun schéma thérapeutique nouveau activé ;
- aucune disponibilité pharmacie temps réel fabriquée ;
- aucun accès réseau AMMPS requis au runtime cabinet.

## Human gate

Toute donnée RCP extraite susceptible de modifier une décision clinique reste soumise à validation médicale avant M2.

Aucun merge M1-B2 sans revue scientifique indépendante et sans accord explicite utilisateur.

Aucun Vercel.
