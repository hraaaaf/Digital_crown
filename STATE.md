## DECISION CANONIQUE DE GOUVERNANCE — 2026-11-09 — FUE À LA PLACE DE REVUE INDEPENDANTE DE CODE

**Décision propriétaire 2026-11-09 — FUE remplace la revue indépendante de code comme gate standard.** La preuve requise est une FUE-0/I/G réellement exécutée, proportionnée au risque, avec scénarios négatifs/sécurité et oracles explicites, résultats inspectables, artefacts et SHA/HEAD exacts. Aucun reviewer indépendant, double review A/B, agent externe ou validation fictive n'est requis **en plus** de cette FUE pour un merge logiciel. Une FUE verte ne vaut pas automatiquement autorisation de merge, acte médical, restauration réelle, installation, validation humaine clinique/réglementaire/physique ou déploiement ; ces gates explicites restent inchangés. Les sections historiques qui imposent une revue indépendante de code sont supersédées prospectivement ; leurs constats et preuves restent archivés.

**Effet immédiat pour LOT05 / J7 et les lots V1.5 à venir :** un reviewer indépendant absent ne bloque plus une PR lorsque la FUE et les contrôles spécialisés applicables sont exécutés avec preuves exact-HEAD ; un backend CI encore en cours/rouge, une faille prouvée, ou une autorisation humaine requise continue à bloquer. Les anciennes mentions « fresh independent review », « separate reviewer », « two reviewers » ci-dessous conservent leur valeur d'historique et **ne sont plus un gate prospectif**. La roadmap/Notion et `AGENTS.md` sont autorités.

# STATE — DigitalCrown

## LOT08 — OS KILL & DEVICE REVOKE GUARD — 2026-11-10

- **Décision propriétaire** : « Next » après la clôture des premiers FUE-I ; poursuite en DRAFT sans merge, migration, installation ou déploiement. Base master recontrôlée `027a82aca4cc37308f6323e759283c4ca0e45fad`.
- **08.3 PR #1265** : branche `feat/v15-08-3-atomic-commit-guard-fue0-20261110`, dernier HEAD source `f6e4df6553826aca06d2f01fc83674baf5018634`. FUE nouvelle : un **vrai processus enfant Python distinct**, utilisant `AuthorizedLocalQueue.perform` sur SQLite isolé, réalise `db.flush()` pour la visite et les 2 événements avant commit ; le parent le tue réellement (`process.kill()`, SIGKILL Linux), rouvre ensuite le fichier et prouve PLANNED version 0 / zéro événement, puis check-in de reprise valide version 2 / 2 événements. [Run exact SHA #42818314843](https://github.com/hraaaaf/Digital_crown/actions/runs/42818314843) **SUCCESS : 145 PASS, 3 SKIPPED**, artifact JUnit #13764853528. Ne prouve NI coupure d'alimentation, NI RPO/RTO de backups.
- **08.2-C PR #1264** : branche `feat/v15-08-2-c-device-pairing-fue0-20261110`, dernier HEAD `88ebec4244519182ee6445056ba47702f305bd14`. Nouveau garde INTERNE `_guarded_device_session` dans `DurableDeviceStoreLab` prend les verrous **auth BEGIN IMMEDIATE puis devices BEGIN IMMEDIATE**, contrôle la session vivante et garde les locks tant que l'appelant est dedans. Trois tests : la révocation admin attend la sortie du garde, mauvais tenant/révocation préalable refusés, exception libère les verrous. [Run exact SHA #42819299776](https://github.com/hraaaaf/Digital_crown/actions/runs/42819299776) **SUCCESS : 147 PASS, 3 SKIPPED, 4 subtests**, JUnit #13765538815. `require()` demeure un simple contrôle ponctuel, **interdit pour une mutation QR**.
- **Contrat 08.2-D/08.4 PR #1266** : même branche documentaire `docs/v15-08-2d-08-4-qr-api-contract-20261110`, section dédiée à la prévention TOCTOU et aux verrous **auth → devices → queue**. La future arrivée Kiosk doit garder ces locks jusqu'au commit Queue, sans rappeler `AuthorizedLocalQueue.perform` qui reprendrait le verrou auth ; toutes les écritures (QR consommé + version visite + ARRIVED + WAITING_ENTERED + idempotence) doivent se situer dans **un seul fichier SQLite Queue / une transaction**. Le fichier devices n'est que lu sous verrou. Pas de garantie mensongère de commit atomique distribué entre trois fichiers SQLite.
- **PROOF CI au dernier relevé** : PR #1265 SHA exact 7 SUCCESS / 1 SKIPPED / 0 ACTIVE ; PR #1264 SHA exact 5 SUCCESS / 1 SKIPPED et 2 runs LOT07 transverses encore actifs, aucun FAIL constaté. Les deux FUE ciblées sont SUCCESS. Tous trois PR restent DRAFT, non fusionnés. `master` inchangé.
- **NEXT exact / HUMAN GATE** : exécuter le FUE de jonction auth + devices + queue avec **acquisition unique des verrous**, check-in Kiosk et révocation concurrente, test anti-rejeu/idempotence QR sur une base Queue isolée, puis FUE de restauration sauvegarde/coupure sur LAB. Ne pas composer de transaction QR à partir du garde et de la méthode publique `perform` actuels (risque de deadlock), ni utiliser patient réel. Certification officielle CODE_CERTIFIED seulement après clôture du LOT08, NO_INSTALLABLE_GO. Notion consigne les dernières preuves. 

## LOT08 — 08.2-C / 08.3 / 08.2-D 08.4 PARALLEL DRAFT — 2026-11-10

- **Décision / contexte** : propriétaire « Go then » autorise développement parallèle isolé après la fusion validée de 08.2-B. MASTER prouvé à l'ouverture : `027a82aca4cc37308f6323e759283c4ca0e45fad`. PR #1239 CLOSED/MERGED sur ce SHA ; 08.1, 08.2-A, 08.2-B fusionnés. Anciennes sections plus bas disant « #1239 DRAFT / NO MERGE » : historique, non état actuel.
- **08.2-C, PR #1264 DRAFT** : branche `feat/v15-08-2-c-device-pairing-fue0-20261110`, HEAD `3189bc446990ea19e8301098d3bc5420b82596da`. Après FUE-0 in-memory, SQLite **isolé et explicitement initialisé pour LAB**, contrôle Admin `device.manage` vérifié sur la session locale vivante, tickets/bearers empreintes seulement, re-pair et révocation durables, tests restart, expiration, concurrence. [Run #42814174960](https://github.com/hraaaaf/Digital_crown/actions/runs/42814174960) **SUCCESS exact HEAD : 144 PASS / 3 SKIPPED + 4 subtests**, JUnit #13762474172. RED historique #42813994051 : assertion de test incorrecte pour bearer Admin malformé, corrigée sans assouplissement RBAC. **NON clos** : ACL Windows réelles, vrais appareils, usage du verrou de révocation pendant chaque mutation QR/Queue, reprise physique/cryptographie production.
- **08.3, PR #1265 DRAFT** : `feat/v15-08-3-atomic-commit-guard-fue0-20261110`, HEAD `b067bc8f7b657b798fe338c82d245c479e28af65`. Garde d'atomicité avant SQL dans moteur SQLite existant, sans duplication ; corruption événement => zéro écriture, panne simulée APRÈS `db.flush` AVANT commit => rollback intégral et reprise depuis nouvelle connexion, concurrence 2 check-ins => 1 seul gagnant. [Run #42814094809](https://github.com/hraaaaf/Digital_crown/actions/runs/42814094809) **SUCCESS exact HEAD : 17 ciblés PASS, full 144 PASS / 3 SKIPPED**, JUnit #13763407858. **NON clos** : crash du processus OS/killed, coupure électrique, restauration sauvegardes/RPO/RTO et concurrence inter-processus à certifier séparément.
- **08.2-D / 08.4, PR #1266 DRAFT** : branche `docs/v15-08-2d-08-4-qr-api-contract-20261110`, contrat uniquement `docs/v1.5/V15_08_2D_08_4_QR_API_PARALLEL_CONTRACT_20261110.md` ; QR Queue APPOINTMENT opaque, une seule consommation, 15 min par défaut 5–30, transition ARRIVED + WAITING transactionnelle, séparé de Station 03.2, Patient QR 03.3 et Station arrivée 03.4. REST/SSE/webhooks, 7 jours d'idempotence, aucune API ni QR runtime livrée.
- **Dépendances** : implémentation 08.2-D attend 08.2-C durable + 08.3 transactionnel. 08.2-E/08.5/08.6 attendent intégration et FUE. LOT09 raccord clinique des interfaces existantes ; LOT10 preuves appareils physiques. CODE_CERTIFIED officiel reporté jusqu'à clôture complète LOT08. Aucun merge de PR 1264–1266 ni activation, migration, déploiement, patient réel ou installateur. NO_INSTALLABLE_GO.
- **NEXT** : inspecter les deux derniers workflows transverses LOT07 encore actifs par PR (même si les FUE Queue exact-HEAD sont GREEN) ; compléter la frontière de transaction **device revocation + Queue commit** sans TOCTOU, la récupération après OS kill et les ACL Windows sur LAB séparé. 08.2-D QR runtime seulement après contrats stables. Aucun merge implicite ; NOTION est la source de preuve la plus fraîche.

## LOT08.2-B / B-7d — RED CONFLICTS RECONCILED / LAB FUE-I PASS — 2026-11-09

- **Décision autorisée** : utilisateur « Go then », tests frontend B-7d sur le merge simulé et, après preuves de sécurité, réconciliation contrôlée de la **branche PR DRAFT #1239 uniquement**. Ne jamais merger la PR vers master, installer, créer une release, utiliser de vrais dossiers patient ou approuver automatiquement le visuel.
- **SOURCE** : branche `feat/v15-08-2-b-rbac-isolation-20261109` HEAD avant lot `c6954e6ec0c775c245754840ad532e6ed147640e`, master actuel confirmé `d4d2d144393fc884e01ca8734c1efa9fb0e0f2e3` (master antérieur `edbc24ed...` avait avancé de six commits LOT05 sans chevauchement des cinq conflits). Exact **5 fichiers / 6 blocs** résolus dans worktree Git détaché sans modification de master, conservant tests de provenance/identité patient, tests blob/PDF authentifié, audit AST et garde Hub Windows, gouvernance FUE. Hash SHA256 des cinq résolutions identique entre simulations master anciennes et actuelles, 0 unmerged, git diff --cached --check PASS.
- **FUE frontend** : 5 suites chacune dans un processus indépendant avec **1 worker**, toutes **exit 0** : audit ClientFacingCopy 13/13, Documents M4-C 6/6, Hub 8/8, PrescriptionForm 7/7, PatientDraft 8/8 ; total **42/42 PASS**, zéro erreur worker. L'ancienne exécution combinée 42 assertions mais erreur onTaskUpdate/exit1 reste RED dans l'historique.
- **FUE backend** : Céphalo/Ortho **15/15 PASS / exit0** sur le merge précédent, contenus des cinq fichiers conflictuels inchangés après intégration master d4d2 ; aucune donnée patient réelle. Premier essai Queue Core sur l'arbre actuel **124 PASS / 3 FAIL / exit1** dû exclusivement au checkout sparse omettant le fichier Git suivi `installer/DigitalCrown.iss`. Après `git sparse-checkout add installer`, préflight **5/5 PASS / exit0** ; puis **régression complète Queue Core 127/127 PASS / exit0 / 158,86 s**, sur le même arbre fusionné. Les trois échecs initiaux restent conservés dans l'historique, mais le run complet final est maintenant réellement vert.
- **TypeScript final** : `tsc --noEmit -p tsconfig.app.json` **PASS / exit0** sur le master d4d2 fusionné, machine Windows 8 Go. Dossier de preuve [B-7d](docs/v1.5/V15_08_2_B_B7D_CONFLICT_RECONCILIATION_20261109.md) et manifeste 5 logs SHA-256 `docs/v1.5/evidence/lot08_2_b7d_master_conflict_sequential_20261109.json`, logs bruts hors dépôt.
- **GATES** : certification `CODE_CERTIFIED` master et `INSTALLABLE_CERTIFIED`, migration `/appointments`, tests Windows natifs installés/LOT10 physique **NOT_RUN / NOT_AUTHORIZED** ; B-6 `NO_INSTALLABLE_GO` demeure. [UI Human Visual Approval](https://github.com/hraaaaf/Digital_crown/actions/runs/42697010891) rouge attendu après changement HEAD et requiert de nouvelles preuves/screenshots et approbation **explicite** par propriétaire GitHub.
- **NEXT exact** : commit de réconciliation dans worktree isolé en respectant parent SHA exact, push uniquement vers branche DRAFT après vérification des références distantes, puis recontrôler PR/CI et documenter Notion. Aucune fusion vers master autorisée.



## LOT08.2-B / B-7c — 2026-11-09 — 388/388 FRONTEND FILES / 2035 TESTS WINDOWS SHARDED PASS · CI NOT VERIFIED

- **Décision GO utilisateur :** finir les lots 7–9 de Vitest Windows sous contrainte de 8 Go RAM, revalider les preuves machine et vérifier la CI GitHub du HEAD exact `66c2f3d4fb0efc6fa5d99a2d15211a5b02c4203f`. PR #1239 OPEN/DRAFT/NON MERGÉE, branch `feat/v15-08-2-b-rbac-isolation-20261109`, base master `324afd13487acf7ff29223f077451927b54b8178`.
- **RÉSULTAT OBSERVÉ (exhaustif sous plan de tests sharded)** : `frontend/src` contient **388 fichiers de tests**, répartis en **9 exécutions Vitest** de 48/48/48/48/48/48/48/48/4 fichiers, avec au maximum **2 workers**. **9/9 shards EXIT 0**, **388/388 fichiers PASS**, **2 035/2 035 tests PASS**, aucun FAIL dans les neuf groupes. Détail par shard : `271 + 264 + 215 + 263 + 274 + 237 + 268 + 224 + 19 = 2035`. Contrôle indépendant des neuf logs `ALL_VERIFIED=True FILES=388 TESTS=2035` / exit 0 ; par shard test/file count exact et SHA-256 des journaux enregistrés.
- **PREUVE CANONIQUE** : `docs/v1.5/evidence/lot08_2_b7c_windows_vitest_shards_20261109.json`, 9 empreintes SHA-256 de logs bruts non commités restant sur le PC de test `DigitalCrown-B7C-Shard-Evidence` ; rapport `docs/v1.5/V15_08_2_B_B7C_PRESCRIPTION_TIMEOUT_STABILITY_20261109.md`. Le code testé est le SHA `66c2f3d` avant commit documentaire. **Les exécutions Vitest globales non plafonnées antérieures restent RED**, ce PASS est une **validation exhaustive découpée**, pas un PASS d'un `npm test` monolithique.
- **Frontières** : tests ciblés B-7c plus anciens 34/34 PASS ; prescription plus forte (quatre presets, label, payload et ordre) et audit des libellés exhaustif par 48 sources, garde-brouillon patient intact. Aucune mutation de code clinique, patients, documents réels, installateur ou migration.
- **CI/GITHUB** : connecteur GitHub `fetch_commit_workflow_runs` limité à la première page des runs `pull_request` a retourné **0** ; un GET **public en lecture seule avec filtre exact `head_sha=66c2f3d`** a vérifié **1 run réel** : [UI Human Visual Approval #42686757746](https://github.com/hraaaaf/Digital_crown/actions/runs/42686757746), évènement `pull_request_target`, **FAILURE attendu** car `PR HEAD changed: approval revoked; new screenshots and explicit approval required`. Ce run ne prouve **aucune** CI Queue Core / Scope / CODE_CERT candidate au SHA testé ; elles restent **NON VÉRIFIÉES**. La PR est **mergeable_state=dirty** (conflits contre master) au contrôle public. Le CLI `gh` local est non authentifié, sans accès de dispatch CI. **Ne jamais contourner la gate visuelle humaine**. Politique `SOURCE_GATE_PRESENT_NO_INSTALLABLE_GO` : tests natifs installés, `CODE_CERTIFIED` exact master, assets certifiés, LOT10 physique, vrai `/appointments` et humains **NOT_RUN/NOT_AUTHORIZED**.
- **BUILD + MÉNAGE** : `tsc --noEmit -p tsconfig.app.json` **PASS**, `npm run build:test` **PASS**, Vite PWA créé sous `dist-test`, manifeste `environment=test`, `commit=66c2f3d`, `mode=test`, **exit 0** ; jamais de build cabinet. La sortie de test `audit/out/frontend.json` et `frontend/dist-test` ont été vérifiées synthétiques puis supprimées ; seuls les logs de preuve externes au dépôt sont conservés.
- **NEXT EXACT** : committer rapport + manifeste dans PR DRAFT, vérifier nouveau HEAD et GitHub CI avec accès paginé, puis traiter les conflits `mergeable_state=dirty` et renouveler la preuve/approbation visuelle via décision séparée. Aucune fusion ou installation pour forcer un workflow.



## LOT08.2-B / B-7c — REAL PRESCRIPTION TEST TIMEOUT & EXHAUSTIVE AUDIT BATCHING — 2026-11-09

- **User GO:** continue the exact last RED: full frontend Vitest 2022 PASS / 1 FAIL (test-only PrescriptionForm quick-preset **5000ms timeout**), not a proven clinical prescription bug. PR #1239 DRAFT, starting SHA `82248e25c9eecc12c4b63052d40a9aee1c22a6f1`, no merge/install/deploy/clinical migration.
- **Oracle repair, NO clinical production code changes:** `frontend/src/features/admin/DocumentStudio/PrescriptionForm.g4Interactive.test.tsx` checks all four quick-preset names, order, payload drug name and exact 4 calls to `onApplyPreset`, with explicit 20s load budget. BEFORE the same isolated unchanged PrescriptionForm file passed **7/7**, actual test time **2.77s**; the RED was runner timeout only, not a callback assertion.
- **Second load failure discovered:** monolithic AST `ClientFacingCopyCandidateAudit.test.ts` timed out even at 20s during a four-suite focused run. Converted to exhaustive **48-file** source batches using identical source discovery filter, same per-file AST/technical-copy rules; new positive source count/unique/flatten coverage assertion, no exclusions and no weaker language scanning.
- **FUE-I Windows focused actual:** the four sensitive suites (copy audit, PrescriptionForm, patient draft-guard, M4-C documents) **34/34 PASS** across **4/4 files**, process exit 0; previous patient draft active-identity+empty editor test retained. Further TypeScript and full default frontend Vitest run currently in progress. `frontend/src/ClientFacingCopyCandidateAudit.test.ts`, `frontend/src/features/patients/PatientDraftRouteGuard.test.tsx` were previously local-uncommitted at `82248e2`.
- **Clinical safety boundaries:** no actual medication instructions altered, no prescribing algorithm clinically certified, no real patient data. `CODE_CERTIFIED`, `INSTALLABLE_CERTIFIED`, physical LOT10 and real `/appointments` migration **NOT_RUN/NOT_AUTHORIZED**; LOT08.2-B OPEN. Repro/report `docs/v1.5/V15_08_2_B_B7C_PRESCRIPTION_TIMEOUT_STABILITY_20261109.md`.
- **NEXT EXACT:** read full Vitest/TypeScript verdict; fix proven residual failures without dropping tests, compile/build if relevant, push safe verified changes only to DRAFT PR #1239, verify GitHub exact HEAD workflows and Notion. GitHub CLI local PC is not authenticated, so do not invent run IDs or CI state.



## LOT08.2-B / B-7 — RED / 3 FAILED CODE_CERT CANDIDATE ASSERTIONS — 2026-11-09

- **Décision :** GO « Red » : traiter les **trois échecs** du workflow GitHub candidat `Cabinet CODE_CERTIFIED candidate regression (no package)` [#42644548911](https://github.com/hraaaaf/Digital_crown/actions/runs/42644548911) au HEAD `c64d9e94077fb63bb6c37e3b80cf24d477dab3dc`. PR #1239 `feat/v15-08-2-b-rbac-isolation-20261109` OPEN/DRAFT/non mergée. Ne pas fusionner, déployer, créer d'installable ni migrer des patients.
- **CAUSE PROUVÉE logs :** frontend Vitest **2022 PASSED/1 FAILED** sur signature `handleView(doc.id)` qui ne correspond plus à l'appel réel sécurisé `handleView(doc.id, doc.name)`. Backend **5918 PASSED/2 FAILED/30 SKIPPED** : `test_cephalo_v1_l3_a4_document` simule un média sans `patient_id`, T0, provenance/date conformes et se heurte au **refus sécuritaire légitime** du lecteur ; `test_ortho_frontend_fail_closed_contract` exige un avertissement clinique littéral manquant dans le composant PDF Step4. Contrôle PostgreSQL/JWT candidat indépendant SUCCESS.
- **CHANGEMENTS MINIMAUX :** mise à jour de l'assertion frontend vers la vraie signature à deux arguments, renforcée par assertions du rattachement patient du blob ; correction de la fixture positive Céphalo avec T0 / patient 42 / upload / slot / version / date réels, **trois nouveaux cas négatifs** patient étranger, mauvais timepoint et image sans provenance pour vérifier l'absence de lecture des bytes ; ajout de l'avertissement clinique visible près des actions PDF dans Step4. Aucun garde de sécurité de production retiré ; le lecteur Céphalo et le module patient Documents restent inchangés.
- **Preuves locales initiales :** process isolé `ENVIRONMENT=test`, `sqlite:///:memory:` avec données fictives ; tests backend Céphalo+Ortho **14/14 PASS**, Vitest M4-C **6/6 PASS**. Premier **Vitest complet Windows 2019 PASS / 3 FAIL + 1 suite en erreur**, isolés en 2 fixtures Git absentes du sparse-checkout local, 1 assertion LF-only sous Windows CRLF et 1 test avec timeout 5 s. Après ajout des fixtures suivies Git **sans changement de code** et correction d'un seul test de portabilité CRLF en conservant l'assertion de garde exacte, les 4 suites ciblées **16/16 PASS**, y compris le timeout en isolation. Il ne s'agit pas d'un nouveau run complet vert. **TypeScript tsc PASS**, **build gardé npm run build:test PASS** vers `frontend/dist-test` avec manifest `mode=test`, sans installation. Nouveau Vitest Windows complet en cours dans checkout élargi ; CI Github sur SHA final à vérifier ; ne pas déclarer le candidat CODE_CERTIFIED tant que la CI complète n'est pas verte.
- **Dossier :** `docs/v1.5/V15_08_2_B_B7_CANDIDATE_RED_REPAIR_20261109.md`. Dernier **B-6** source-only maintient `SOURCE_GATE_PRESENT_NO_INSTALLABLE_GO`, LOT08.2-B OPEN, tests natifs/physiques LOT10 NOT_RUN, aucune donnée patient réelle.
- **Next exact :** finir les régressions, pousser uniquement sur la même PR DRAFT, contrôler les runs de certification candidate au SHA exact, documenter Notion. CEPH experimental et Mobile Pocket restent des workflows séparés non clos sans preuve.



## LOT08.2-B / B-6 — DESKTOP INSTALLABLE ACCEPTANCE CONTRACT — 2026-11-09 — SOURCE PREFLIGHT PASS / NO GO

- **GO utilisateur :** « Go » pour définir et tester les conditions d'acceptation du véritable Desktop installable ; aucune autorisation de merge, de certification master, de build EXE, d'installation ni de migration clinique. PR #1239 DRAFT/OPEN, HEAD source avant ce sous-lot `b003528a744f78ad4a9375e7de0eb70762f38b34`.
- **Décision unique :** le LAB Queue Core et sa CI ne constituent pas `CODE_CERTIFIED` ni `INSTALLABLE_CERTIFIED`. Le vrai binaire installable exige les gates de `docs/CABINET_CERTIFIED_RELEASE_POLICY.md` : SHA exact master → CODE_CERTIFIED+Sigstore → assets scientifiques certifiés au même SHA → INSTALLABLE_CERTIFIED+7 manifestes → packaging natif fail-closed → FUE installable sur PC fictif → GO distinct de migration patients et LOT10 physique.
- **Livré :** matrice de décision exhaustive `docs/v1.5/V15_08_2_B_B6_DESKTOP_INSTALLABLE_ACCEPTANCE_20261109.md` avec Success/Proof/STOP et états PRESENT/NOT_RUN/NOT_AUTHORIZED. Nouveau préflight source **READ-ONLY** `scripts/v15_08_2_b_desktop_installable_preflight.py` : SHA 40 hex exact, dix garde-fous source inspectés, détection de couplage entre `WaitingRoomPage` et Queue Core LAB, rapport permanent `installable_ready=false` / `clinical_go=false`; aucun accès cabinet, installation ou package. `queue_core/tests/test_installable_source_preflight_08_2_b.py` injecte source altérée, mauvais SHA, refus de sortie dans repo, état NO GO.
- **Preuves source Windows Python 3.12 :** `SOURCE_GATE_PRESENT_NO_INSTALLABLE_GO`, **10/10 contrôles statiques PRESENT** ; **5/5 tests ciblés de préflight PASS** ; suite globale Queue Core finale **127/127 PASS / 95,37 s**, compilation et diff-check PASS. Préflight désormais **strictement lecture seule** (stdout simple ou `--json`, aucune option de fichier de sortie). Les protections doivent encore être exercées sur un vrai artefact certifié avant acceptation native ; CI au nouveau SHA à relever après push.
- **Source canonique existante :** `docs/CABINET_CERTIFIED_RELEASE_POLICY.md`, `docs/quality/REALITY_PROOF_GATE.md`, `installer/DigitalCrown.iss`, `DigitalCrown.spec`, `run.py`, `docs/handovers/2026-11-07-restore03-installable-candidate-preflight.md`. La preuve B-5b sur le SHA `b003528` est Queue Core Linux **119 PASSED / 3 SKIPPED** et Scope Gate SUCCESS ; `Cabinet CODE_CERTIFIED candidate regression (no package)` était QUEUED au contrôle et **n'est pas une certification master**.
- **STOP / NEXT EXACT :** LOT08.2-B reste OPEN. Finaliser régression, exact-head PR/CI, mettre Notion à jour ; toute promotion vers master/installable et tout test sur clinique nécessitent un GO humain séparé. Ne pas créer de pourcentage non prouvé.



## LOT08.2-B / B-5b — RED CI DEPENDENCY ISOLATION — 2026-11-09 — WINDOWS PASS / LINUX CI PENDING

- **GO utilisateur :** « Red », traiter le blocage critique suivant de la PR #1239, sans fusion, installation, déploiement ou migration patient. HEAD avant fix `10ff5f55b4ec43709ad23e7f1b7a4e90f31283b9`. BRANCHE `feat/v15-08-2-b-rbac-isolation-20261109`, PR OPEN/DRAFT.
- **Cause constatée dans les logs GitHub :** [Queue Core #42634986803](https://github.com/hraaaaf/Digital_crown/actions/runs/42634986803) FAIL au SHA 10ff5f5 pendant **pytest collection, 0 tests exécutés**, `ModuleNotFoundError: email_validator`. La suite isolée Queue Core importait `backend.queue_core_desktop_lab`, ce qui importait d'abord `backend/__init__` et des schémas médicaux nécessitant `pydantic.EmailStr`. [Scope #42634986969](https://github.com/hraaaaf/Digital_crown/actions/runs/42634986969) SUCCESS. Ce n'était PAS un échec d'autorisation Queue Core.
- **Correction sécurité/architecture :** le module LAB existant, inchangé, est maintenant `queue_core/service/desktop_lab_bridge.py` ; `backend/queue_core_desktop_lab.py` est un shim de compatibilité vers cette implémentation, afin que l'authentique `backend.main` conserve sa composition. Tests Queue Core importent directement le module isolé ; nouveau test sur interpréteur vierge interdit l'import implicite de `backend`. Aucune dépendance clinique ajoutée, aucun skip de test ni affaiblissement de la CI ; aucun changement aux données, aux rendez-vous ni à la sécurité de production.
- **Proof Windows locale vérifiée :** `BACKEND_LOADED=False` import du module LAB depuis processus Python vierge ; suite ciblée Desktop 8/8 PASS ; suite globale `py -3.12 -m pytest -q queue_core/tests` **122/122 PASS / 82,28 s**, `compileall` et `git diff --check` exit 0. **Véritable `backend.main` ASGI synthetic** après shim : autorisation 403/401/200/CHECK_IN/logout/401, **exit 0**, sans démarrer `lifespan` clinique, et SQLite temporaire supprimée.
- **Document :** `docs/v1.5/V15_08_2_B_B5B_CI_ISOLATION_FIX_20261109.md`. CI au prochain SHA final à attester et Notion à synchroniser. **LOT08.2-B OPEN**, logiciel cabinet certifié/installer, essais physiques LOT10, données patients et migration `/appointments` NOT_RUN.
- **NEXT EXACT :** push contrôlé du correctif sur PR #1239 DRAFT, lire jobs/logs Linux et Scope Gate du nouveau SHA ; si échec changer de stratégie sans prétendre PASS, sinon actualiser Notion/PR. Aucune fusion ou déploiement non autorisé.



## LOT08.2-B / B-5a — REAL BACKEND.MAIN ASGI LAB FUE-I — 2026-11-09 — PASS / NO DEPLOY

- **Décision & périmètre :** GO « Green next » après B-5 Chromium LAB ; vérifier le véritable point d'entrée `backend.main:app` et ses middlewares via ASGI local synthétique. Aucun runtime clinique/lifespan, aucun installable ni migration patient ou de cabinet. Base git `3203eff850b081261ec7959cb81cc8f4a2bda782` PR #1239 DRAFT et non fusionnée.
- **Test autonome :** `queue_core/tests/desktop_main_lab_probe.py` : flag explicite `DIGITALCROWN_QUEUE_MAIN_FUE_RUN=1`, `ENVIRONMENT=test`, clinique `sqlite:///:memory:` et attestation runtime isolé, deux vraies SQLite temporaires B-2 + Queue Core avec comptes/visites fictifs, import réel `backend.main` **sans lancer clinical lifespan**, réseau absent ; test HTTP ASGI loopback réel sur la composition globale et les middlewares (synthetic `testclient` 403, 127.0.0.1 → 401 sans auth, 200 login/snapshot/check-in, 200 logout, 401 session révoquée). `backend.main` garde `WaitingRoomPage` clinique historique intacte. Commande : `$env:DIGITALCROWN_QUEUE_MAIN_FUE_RUN='1'; py -3.12 -m queue_core.tests.desktop_main_lab_probe` → **exit 0 / ACTUAL_BACKEND_MAIN_ROUTING_AND_RBAC_PASS_NO_CLINICAL_LIFESPAN**. Fermeture explicite moteurs SQLAlchemy pour suppression des fichiers Windows.
- **Écarts rencontrés et résolus :** `relay` absent seulement du sparse-checkout local, ajouté sans changement source ; testclient ASGI synthétique 403 attendu car seul loopback réel est autorisé ; SQLite test verrouillée pendant nettoyage initial, puis `engine.dispose` et rerun code 0. Warnings imports modèle Pydantic / ONNX absent dans sparse checkout non bloquants pour ce test.
- **Preuve :** `docs/v1.5/V15_08_2_B_MAIN_ENTRYPOINT_FUE_I_20261109.md`. B-5 précédent : FUE-G navigateur Chromium 19/19 PASS + captures 7, suite locale Windows 121/121 PASS, build:test isolé PASS. Le présent FUE-I **n'est pas** un test du cycle de vie de l'application clinique, du paquet installable, du contenu patient ou des machines cabinet. LOT08.2-B OPEN / LOT10 PHYSICAL NOT_RUN.
- **CI :** Scope Gate sur HEAD B-5 3203eff SUCCESS ; Queue Core #42632131539 encore QUEUED au relevé ; le prochain commit B-5a nécessite une vérification CI sur son SHA propre avant tout jugement. Aucun merge / déploiement / Vercel.
- **Next exact :** attester CI exact-SHA, documenter Notion + PR, puis isoler les critères d'acceptation d'un candidat Desktop installable avant tout test patient réel.



## LOT08.2-B / B-5 — DESKTOP LOCAL LAB FUE-G — 2026-11-09 — PREUVE BROWSER PASS / B OPEN

- **GO utilisateur :** raccorder B-4 HTTP/SSE au runtime Desktop local en laboratoire, FUE-G navigateur, sans fusion/déploiement/installation ni patient réel. PR #1239 DRAFT, HEAD avant B-5 `16bf642d2558380326e89fea3ac049308048de0f`, base master `324afd13487acf7ff29223f077451927b54b8178`.
- **Reality check :** Desktop réel `run.py → backend.main:app` + React ; `WaitingRoomPage.tsx` existante utilise les vrais `/appointments`. Aucune mutation de ce workflow ni de données cliniques. Montage `backend.queue_core_desktop_lab.attach_queue_core_lab` derrière flag + environnement `test` uniquement, deux fichiers SQLite synthétiques préexistants, marqueur explicite ; le montage dans `backend/main.py` est opt-in et exclut cabinet/production. Login opérateur B-2 tenant résolu serveur, rôles/grants seulement comme indices UI, RBAC toujours côté serveur.
- **Client LAB :** `frontend/src/features/queue-core/QueueCoreLabPane.tsx`, route React dév protégée `/queue-core-lab` plus entrée Vite de test isolée `/queue-core-fue.html`. Un navigateur réel utilise token Bearer volatile (pas URL/cookie/storage), fait check-in→call→chair→done, affiche les événements SSE, cache les actions non autorisées, et efface les visites immédiatement si le flux est clos/révoqué.
- **FUE-I :** montage Desktop 8/8 PASS, tests ciblés montage+HTTP/SSE 21/21 PASS, Python 3.12 Windows. **FUE-G navigateur :** Chromium + Python FastAPI et Vite sur processus loopback distincts, deux SQLite temporaires, 19/19 checks PASS, 7 captures 390/768/1280 et JSON hashes SHA256 ; aucune erreur navigateur inattendue ; vérification du 401 après révocation externe. Preuve : `docs/v1.5/V15_08_2_B_DESKTOP_LAB_FUE_G_20261109.md` et `docs/v1.5/evidence/lot08_2_b5_fue_g_20261109/`.
- **CI et gates :** re-tests complets Windows Python 3.12 **121/121 PASS (89,32 s)**, compilation Python PASS, TypeScript `tsc --noEmit -p tsconfig.app.json` PASS, build gardé `npm run build:test` PASS dans `frontend/dist-test` sans toucher au dist cabinet ; GitHub CI au SHA final à vérifier après push. FUE-G est **LAB navigateur synthétique**, PAS une session clinique native installée ; aucune preuve USB/Windows installer/TLS LAN, ni intégration aux rendez-vous cliniques ; LOT10 physique NOT_RUN. **LOT08.2-B OPEN, PR DRAFT, aucun merge/déploiement.**
- **Next exact :** relever résultats locaux et Actions exact SHA, POST Notion, puis définir gate distinct pour intégration dans candidat Desktop certifiable, sans exposer de vrais patients.



## LOT08.2-B / B-4 — HTTP/SSE LOCAL ASGI — 2026-11-09 — FUE-I PASS LAB, B OPEN / NO MERGE

- **GO user :** développer la vraie interface HTTP/SSE du Queue Core depuis le B-3 in-process, sans fusion, installation, déploiement ni patient réel. PR #1239 DRAFT, base master 324afd13487acf7ff29223f077451927b54b8178 ; HEAD avant B-4 a94343a12f6045db5595e108763fe6cfd7d3068d.
- **Implémenté :** queue_core/service/http_transport.py, factory FastAPI ASGI locale (aucun socket démarré), POST commandes, GET snapshot, GET replay paginé, GET SSE streaming (text/event-stream). B-2 session Bearer obligatoire depuis Authorization header, local loopback peer+Host, pas de credentials URL/cookie, Docs/OpenAPI/CORS fermés, refus 401/403, schéma HTTP fermé à l'injection de tenant/actor, SSE recontrôle droit B-2 avant ouverture et avant chaque frame / heartbeat, reprise Last-Event-ID tenant/queue, évents minimisés sans secret et IDs validés. Ajout queue_core/service/authorized_queue.py require_queue_read() à validation fraîche.
- **FUE-I transport local réel (sans réseau) :** queue_core/tests/test_http_sse_08_2_b.py, FastAPI TestClient + httpx.ASGITransport, 13 scénarios HTTP/SSE réels / négatifs avec deux vraies SQLite isolées et données synthétiques : commandes 0→2→3→5→7, IDOR, token, non-loopback, host, corps malformé, paginated replay, cursor, SSE révocation au milieu d'un lot d'événements et anti-injection de champs SSE. Suite Windows Python 3.12 après modifications : **113/113 PASS / 46,20 s** ; compileall et git diff --check exit 0.
- **CI GitHub vérifiée sur commit transport f75bc8dc6acab24720c89fadfafceb72741b6e76 :** workflow .github/workflows/v15-08-1-queue-domain-fue0.yml avec dépendances isolées FastAPI/httpx/anyio/pydantic/starlette ; run #42620845974 COMPLETED/SUCCESS, job #129172271703, logs Linux Python 3.11 : **110 PASSED / 3 SKIPPED / 31,19s** ; Scope Gate run #42620845954 SUCCESS. Les skips ne sont pas des passes. Le commit final de documentation/STATE appelle sa propre CI, dont le verdict doit être consigné dans Notion. Preuve : docs/v1.5/V15_08_2_B_HTTP_SSE_FUEI_20261109.md.
- **LIMITES :** aucun serveur écoutant, TLS, Windows packaging, client navigateur/UI ni expérience opérateur physique ; FUE-G non exécuté, LOT10 PHYSICAL NOT_RUN. Un octet déjà envoyé ne peut pas être retiré après révocation. Architecture non déployée/non activée en cabinet. LOT08.2-B OPEN, pas de merge ni production.
- **Next exact :** vérifier la CI Linux et Scope Gate au SHA poussé, enregistrer Notion, puis réconcilier l'interface vers le périmètre 08.3 et effectuer FUE-G/browser quand un vrai client est disponible. Pas de pourcentage inventé.



## LOT08.2-B — LOCAL COMMAND/REPLAY ADAPTER FUE-I — 2026-11-09 — CANDIDATE / NO MERGE

- **GO utilisateur :** après B-2 FUE-0, intégrer le contrôle humain aux vraies commandes/lectures événementielles du Queue Core, FUE proportionné ; aucune revue indépendante obligatoire par défaut, mais contrôles SEC/IDOR/intégrité systématiquement négatifs. Pas de GO fusion ou mise en production.
- **Source réelle vérifiée :** PR #1239 DRAFT sur base master 324afd13487acf7ff29223f077451927b54b8178 ; HEAD avant travaux a642bb38d26c5b6420456fc02867e2da8ea5d6b7. Domaine et tables Queue Core existants ; aucun HTTP/SSE runtime existant.
- **Implémentation :** queue_core/service/authorized_queue.py : adaptateur local in-process sur le vrai domaine Queue Core et la base SQLAlchemy séparée de la SQLite auth B-2 ; RECEPTION check-in, STAFF call/recall, CHAIR/DONE grants séparés, NO_SHOW/override explicites, verrou de transaction auth→queue, scope tenant/visite/ressource résolu depuis le serveur, événements minimisés, pagination/replay et queue snapshot réautorisés à chaque appel. Aucun listener, create_all, migration, données patient ni identité Device.
- **FUE-I local :** 11 tests sur 2 SQLite temporaires avec commandes/vrais événements, IDOR, annulation/révocation, cursor cross-tenant, concurrence command→revoke et pagination. FUE-I ciblé 11/11 PASS ; suite globale Windows Python 3.12 finale 100/100 PASS (33,65s), compileall et git diff --check PASS ; CI GitHub au SHA final à relever après push. Preuve : docs/v1.5/V15_08_2_B_LOCAL_SERVICE_FUEI_20261109.md.
- **Limite critique :** ce FUE-I concerne l'adaptateur local **sans transport HTTP/SSE**. Aucune preuve FUE-G/browser/SSE live ni physique (LOT10 NOT_RUN). Le prochain vrai endpoint/service devra revalider les autorisations par requête, souscription, replay et événement émis. B RESTE OPEN ; ne pas fusionner, déployer ou créer de comptes cabinet.
- **NEXT EXACT :** terminer re-test Windows + CI GitHub exact-SHA, consigner Notion, puis poursuivre l'intégration transport uniquement sur périmètre autorisé quand 08.3 expose un vrai service. Ne pas revendiquer de service HTTP déjà livré.



## LOT08.2-B — FUE-FIRST remplacement gate reviewer — 2026-11-09 — B-2 FUE-0 PASS / B OPEN

- **Décision utilisateur :** la revue indépendante systématique est substituée par le FUE approprié, conformément à SKILLS.md FUE-first ; les contrôles SEC/data/révocation restent obligatoires selon les risques. Pas de revue artificielle ni de sign-off humain inventé.
- **Base vérifiée :** PR #1239 DRAFT au SHA de départ `43581796b4c57223ddd734f8b2d35bc68ab2be72`; base master `324afd13487acf7ff29223f077451927b54b8178`.
- **FUE-0 exécuté sur Windows Python 3.12 :** nouveau `queue_core/tests/test_fue_08_2_b.py` : 3/3 PASS (SQLite réel isolé : reprise, revoke/A recovery, concurrence sérialisée, fail-closed rôle corrompu). Suite complète `py -3.12 -m pytest -q queue_core/tests` : **89 PASSED**, compileall et diff-check PASS.
- **Protocole et limites :** `docs/v1.5/V15_08_2_B_FUE0_20261109.md` ; données fictives, pas de clinique, FUE-I/G indisponible (routes/API/SSE pas encore implémentés). Tests physiques exclusif LOT10. Aucune fusion/déploiement accordé.
- **Next exact :** confirmer la CI au HEAD final de ce checkpoint FUE puis traiter l'intégration des contrôles d'autorisation aux vraies commandes/flux dans un sous-lot distinct ; le lot B reste OPEN. Aucune validation FUE-G ou produit affirmée.



## LOT08.2-B — B-2 persistance opérateurs candidate — 2026-11-09 — OPEN / NO MERGE

- **GO owner 2026-11-09 :** poursuivre B-2 exclusivement après B-1 au HEAD `e0363e055fd4b31b3903b105229445e7252e1078` de PR #1239 DRAFT. Aucun GO de merge, déploiement, installation ou activation clinique.
- **B-2 implémenté en LAB isolé :** `queue_core/security/operator_store.py`, extension additive au fichier SQLite local de 08.2-A (distinct de toute DB clinique), premier Admin bind tenant contrôlé par garde local, opérateurs nominatifs, scrypt, sessions opaques, rôle unique, attributions file/ressource, grants explicites, audit append-only, last-admin et bootstrap immuable par API + trigger SQL. `local_auth.recover_admin` invalide désormais les sessions A et B atomiquement.
- **Preuve directe Windows Python 3.12 :** `py -3.12 -m pytest -q queue_core/tests` → **86 PASSED / 0 FAILED** (fixtures synthétiques SQLite temporaires uniquement) ; `compileall` et `git diff --check` exit 0. Ne pas assimiler cette preuve à une validation physique ou sécurité complète ; le SHA final et CI GitHub sont à consigner après commit.
- **Contrat :** `docs/v1.5/V15_08_2_B_RBAC_ISOLATION_CONTRACT.md`, nouvelle section B-2 avec limites. `test_operator_store_08_2_b.py` fournit tests persistés, tenant/IDOR, droits, expiration, lockout, transactions, audit refus, rollback et récupération.
- **OPEN :** revue SEC ciblée sur SHA final et CI Linux/Windows applicable ; résolution serveur fiable des tenants/visites/ressources et couplage auth→commande/flux futurs non implémentés ; aucune route/API, service SSE ou installation. Scope mono-tenant local de B-2. Essais physiques exclusivement LOT10 NOT_RUN.
- **Next exact :** commit/push candidat sur PR #1239 DRAFT, inspecter CI exacte et revue SEC indépendante, corriger tout défaut critique et demander décision de fusion distincte une fois tous les gates logiciels requis satisfaits. Aucun merge automatique.



## LOT08.2-B — RBAC tenant-scopé / isolation — 2026-11-09 — B-1 EN COURS

- **08.2-A** : [PR #1238](https://github.com/hraaaaf/Digital_crown/pull/1238) MERGED sur master commit `324afd13487acf7ff29223f077451927b54b8178`; Windows CI 53/53 PASS au SHA source `1b4380735932896b8b7a38485b2af709182c796c`, physique `NOT_RUN / LOT10`. Un workflow transversal postmerge #42599749810 était IN_PROGRESS au premier relevé.
- **Décision propriétaire** : séquence 08.2-A → **08.2-B**, pas 08.3. G2 validé : Admin configuration/audit sans droits opérationnels ; accueil check-in/QR ; staff call/recall ; CHAIR/DONE distincts, NO_SHOW et queue.override OFF par défaut, permissions par tenant/file/visite/ressource.
- **B-1 candidat (PR DRAFT, non fusionné)** : policy pure `queue_core/security/rbac.py`, oracles synthétiques d'isolation/refus/révocation via resolver de session live, contrat `docs/v1.5/V15_08_2_B_RBAC_ISOLATION_CONTRACT.md`. La présence de code + tests ne constitue PAS une preuve d'auth multi-opérateurs persistante ni une certification des flux.
- **B reste OPEN** : persistance isolée des opérateurs nominaux, rattachements/permissions et authentification par compte, révocation immédiate de sessions, preuve last-admin et contrôle réellement appliqué sur chaque future commande/flux, revue SEC indépendante et CI au SHA avant GO de merge. C/D/E, 08.3, déploiement, cabinet et données patients hors périmètre.
- **Next exact** : CI Python/tests existants + nouveaux tests RBAC, examiner SEC et compléter durable store/transactions ; aucune validation physique avant LOT10.

## DÉCISION PROPRIÉTAIRE — 2026-11-09 — LOT08 logiciel/LAB ≠ LOT10 physique

**Cette décision prime sur les anciens checkpoints « NO-GO merge car tests physiques non exécutés » contenus plus bas.** La roadmap officielle [V1.5-10 — Tests physiques exclusivement](https://app.notion.com/p/3e677c66336281fcbe65f8889baf8c6a) réserve la validation matérielle/terrain au **LOT10** : 10.1 (installation postes), 10.2 (Queue Core réel), 10.7 (incidents/sécurité terrain), 10.8 (réception humaine). Le premier enrôlement physique Admin `issue→enroll→recover`, les ACL sur installation réelle, la récupération offline et le refus d'autres profils sont **PHYSICAL NOT_RUN / LOT10**. Ils ne sont **pas un préalable de clôture logicielle/merge du LOT08.2-A** ; l'utilisation clinique reste interdite jusqu'aux gates terrain applicables.

**Preuves 08.2-A :** [Windows Actions #42596486051](https://github.com/hraaaaf/Digital_crown/actions/runs/42596486051) SUCCESS sur SHA exécutable `1b4380735932896b8b7a38485b2af709182c796c`, **53/53 tests PASS**, création Win32 et vérification ACL réelles uniquement sous RUNNER_TEMP, refus CLI non interactive sans modification ProgramData, refus ACL non conforme ; [Ubuntu FUE-0 #42596493320](https://github.com/hraaaaf/Digital_crown/actions/runs/42596493320) SUCCESS. Une **décision de clôture du logiciel** doit considérer revue SEC, CI, risques et périmètre, sans exiger le terrain physique.

**PR #1238 :** reste DRAFT/non fusionnée **en attente d'une décision d'intégration distincte du propriétaire et des contrôles logiciels applicables, pas d'une preuve physique LOT10**. Pas de déploiement, d'installation cabinet ou de passage automatique à 08.2-B–E. **Next exact :** revoir les preuves et le diff logiciel A, proposer décision de merge ; si approuvée, merge + contrôles post-merge, puis poursuivre roadmap logicielle. Les précédentes mentions contradictoires documentent le gate erroné désormais supersédé.

## LOT08.2-A — Windows GitHub Actions ACL complémentaire — 2026-11-09 — CI PROUVÉ / PHYSIQUE OPEN

- **PR #1238 : OPEN/DRAFT/NOT MERGED**, [preuve Windows Actions #42596486051](https://github.com/hraaaaf/Digital_crown/actions/runs/42596486051) **SUCCESS** sur SHA exact testé `1b4380735932896b8b7a38485b2af709182c796c`, Windows hosted runner et Python 3.12. La suite `queue_core/tests` **53/53 PASS** ; non-interactive `status` refusé `INTERACTIVE_CONSOLE_REQUIRED` sans effet sur ProgramData ; **vraie création Win32 d'un dossier et fichier temporaires** sous RUNNER_TEMP avec validation owner/ACE réelle Get-Acl + refus ACL non conforme. Artifact JUnit non médical. Aucun accès cabinet ni donnée patient.
- **Linux FUE-0 existant** [#42596493320](https://github.com/hraaaaf/Digital_crown/actions/runs/42596493320) **SUCCESS** sur ce SHA ; correctif de l'oracle du test de refus sous non-Windows (attendre LOCAL_WINDOWS_CONSOLE_REQUIRED) inclus. Le code sécurité runtime est resté inchangé depuis le SHA source sécurité revu `44bc6fc639332796f064dbf18a59a4f8b5c3333f`.
- **Diagnostic des premiers FAIL :** Powershell 7 runner -> sous-processus Windows PowerShell 5.1 incapable d'auto-charger `Microsoft.PowerShell.Security` pour `Get-Acl`. La même vérification exécutée directement sous Windows PowerShell 5.1 (shell natif dans Actions) est PASS. Ce n'était pas une preuve de permissions correctes tant que la vraie vérification n'était pas PASS.
- **STOP MAINTENU :** runner hébergé ≠ console physique locale élevée. Aucun `issue→enroll→recover` réel à la console LAB, aucune vérification d'identité utilisateur non privilégié par second profil humain, aucune restauration hors ligne réelle sur poste LAB : **NOT_RUN**. Aucun merge, déploiement, installation cabinet, 08.2-B/C/D/E ni certification clinique autorisés. **Next exact :** Windows LAB physiquement isolé, Admin élevé local, recette première inscription + ACL + récupération offline, preuves expurgées, puis gate humain GO/NO-GO.
- **Fichier canonique :** ce checkpoint documentaire est ajouté après la CI ; le SHA testé `1b438073...` reste la preuve exécutable. Toute différence de SHA ultérieure doit être réconciliée par comparaison du delta, sans déclarer une nouvelle CI PASS si elle n'a pas tourné.

## LOT08.2-A — Local Windows identity/bootstrap — IN PROGRESS / DRAFT (2026-11-09)

- **2026-11-09 SEC review current source `44bc6fc639332796f064dbf18a59a4f8b5c3333f`**: independent read-only Codex delta review from `09f3d40e` reports **no actionable defect**. Prior full review found P2 stale expired session rows; corrected within serialized login transactions, including denied logins, with negative retention test. **53/53 direct Windows Python 3.12 PASS postcommit**, compileall exit 0, git clean. Directory/file SDDL accepted by Windows API without writes, remote CLI rejected with `INTERACTIVE_CONSOLE_REQUIRED` exit 2 and no real auth-store file created. [SEC review report](docs/v1.5/V15_08_2_A_SECURITY_REVIEW_20261109.md). **Physical elevated Windows console positive bootstrap/ACL NOT RUN; PR #1238 remains DRAFT / NO-GO merge or clinic install pending physical LAB proof**. No 08.2-B GO.

- **2026-11-09 independent Codex review on SHA 09f3d40e:** found P2 unbounded expired sessions retained in SQLite. Fixed under the login transaction by pruning `expires_epoch <= now` even on denied logins; added negative synthetic retention test. **53/53 direct Windows Python 3.12 PASS**, compileall and diff check PASS. New exact SHA and separate final review still required. Physical Windows local elevated console enrollment/ACL positive **NOT_RUN**; no clinical use, merge, 08.2-B or deploy.

- **2026-11-09 separate Codex review on e3513ac9:** no P1/P2 findings; one P3: read-only `status` unexpectedly created an auth directory before first enrollment. Fixed `windows_cli._database_path(initialize=False)` to inspect without creating, with a regression test. **52/52 direct Windows Python 3.12 PASS**, compileall and diff-check PASS. Fresh reviewer required on the *new* commit; physical elevated Windows-console positive enrollment/ACL still NOT_RUN, no real auth store created and no merge under this checkpoint.

- **SEC critical review #1, initial SHA 58e3b5e7:** independent targeted Codex SEC/OPS review identified P1 directory-owner ACL spoof and P2 dangling reparse bypass. Corrected with atomic Windows SDDL protected CreateDirectoryW/CreateFileW, trusted SID owner and both distinct required ACEs, non-following `lstat()` and `FILE_FLAG_OPEN_REPARSE_POINT`, with synthetic negative/static Win32/PowerShell tests. **51/51 direct Windows Python 3.12 PASS on preceding e3513ac9.** Subsequent 2026-11-09 review P3 correction now **52/52 PASS**. Real elevated physical console creation/ACL remains NOT_RUN. New SHA needs another independent security review before merge.

- **GOAL:** standalone Queue Core first Admin enrollment on a physically local elevated Windows console, no Internet, Firebase, patient records or clinical database access.
- **Owner GO:** « Play 8-2 A go ». This authorizes implementation of A only, not merge/release or 08.2-B–E.
- **BASE:** `edf26bb7ff70904b802069891f31ef3b4dc7691d` master (LOT08.1 CLOSED 29/29). Worktree `feat/v15-08-2-a-local-admin-bootstrap-20261108`, isolated branch.
- **DELIVERABLE CANDIDATE:** `queue_core/security/local_auth.py` (SQLite local auth + bootstrapping), `windows_console.py` OS privilege/console gate, `windows_cli.py` ProgramData ACL-controlled offline CLI, synthetic negative unit tests and `docs/v1.5/V15_08_2_A_LOCAL_ADMIN_BOOTSTRAP_CONTRACT.md`.
- **PRELIMINARY DIRECT WINDOWS EVIDENCE:** Python 3.12 `pytest -q queue_core/tests` **52/52 passed** (29 08.1 + 23 08.2-A incl. Windows ACL/symlink hardening and read-only status); compileall PASS. Real Remote Desktop Commander shell `python -m queue_core.security.windows_cli status` denied with `INTERACTIVE_CONSOLE_REQUIRED` exit 2; `ProgramData\DigitalCrownQueueCore\local_auth.sqlite` absent before/after. NO real admin account or recovery secret generated; tests use temp SQLite synthetic fixtures and injected guard.
- **SECURITY CONTRACT:** 256-bit random bootstrap (10min), single use/5-attempt cap; scrypt salted passwords, opaque SHA-256 session verifier and lockout, 8h sessions; separate 256-bit offline recovery secret, one-time rotation and all-session revocation. Restricted Windows physical console and ACL verification; no public route. No default admin.
- **UNVERIFIED / BLOCKED FOR REAL USE:** actual elevated physical Windows-console onboarding, DirectorySecurity Set-Acl success on target PC, backup/restore/installed service, session-cookie/network auth, multi-tenant RBAC, kiosk/QR, standalone runtime and legal G3. Risk-critical source needs independent SEC/OPS review on exact SHA before any merge, with negative tests and correction loops. No automation GitHub Actions requested.
- **NEXT:** commit & push DRAFT PR, direct Windows proof exact SHA, separate reviewer, POST Notion. Do NOT merge, install or begin 08.2-B without distinct GO.

## LOT08.1 — Queue Core domain contracts — CLOSED / POST-MERGE VERIFIED (2026-11-08)

- **GOAL:** isolated standalone Queue Core domain state machine, dynamic ranking, auditable event plans, dedicated SQLAlchemy schema and synthetic FUE-0. **Delivered:** G1 transitions/rank oracles, manual NO_SHOW and queue.override, tenant/resource constraints, active chair occupancy, provenance and SQL integrity checks. No clinical DB coupling, migration, patient data or runtime deployment.
- **RESULT:** [PR #1234](https://github.com/hraaaaf/Digital_crown/pull/1234) **MERGED**; final contributor SHA `1df36d79a694f713cb19b112ae26831501cf1678`; squash master SHA `a5c47f5efcc7b9843a9fea13799bae073ca541e7` (based on parent master `16f531f04eb7daff3bf5d75017717e12927f47ab`). Owner GO "Green" captured.
- **PROOF POST-MERGE Windows:** authorized device DESKTOP-3MAJEEH, isolated worktree checked out on the exact master merge SHA; Python 3.12 `pytest -q queue_core/tests` **29/29 PASS**, `compileall -q queue_core` **PASS**, clean git tree. No GitHub Actions tests deliberately launched; older green runs belong to earlier contributor SHAs and are not evidence for this one.
- **INDEPENDENT CODE REVIEW:** fresh Codex CLI read-only agent on final contributor SHA against updated `origin/master`: no definite actionable defects reported. Its default Python 3.14 lacked pytest; only separate Windows 3.12 tests substantiate FUE. Earlier distinct reviews identified P1/P2 defects corrected and re-tested. This is **AI code review, not medical or human signoff**.
- **CLOSEOUT SCORES (08.1 scope ONLY):** EXECUTION 9.0/10, FUE_EVIDENCE 9.0/10, RETAINED 9.0/10 (minimum). FUE-0 applicable and demonstrated, no UI exists in 08.1; FUE-I/G and installed runtime remain later sublots. Final independent review + postmerge tests serve as scoped Perfection Pass.
- **LIMITS:** `call_visit` cannot prove candidate completeness; future 08.3 MUST load authoritative candidates under DB transaction lock and atomically commit resource state, audit and versions. No durable append-only, encryption, RBAC, kiosk/QR, API/SSE, webhooks, UI, backups/restore or real patient enablement is claimed.
- **HANDOVER:** `docs/v1.5/V15_08_1_QUEUE_CORE_CLOSEOUT_20261108.md`; contract `docs/v1.5/V15_08_1_QUEUE_CORE_DOMAIN_CONTRACT.md`; historical detailed review trail in `techdoubt.md` and [canonical Notion LOT08](https://app.notion.com/p/3ec77c66336281d59cdcffe610561f86).
- **NEXT EXACT:** 08.2 local identity/RBAC/device/QR requires separate GO and fresh preflight; no 08.2 start, merge beyond closeout documentation, clinic release or Vercel deployment under this approval.

# LOT07 V1.5 Desktop Experience & MultiView — 2026-11-08 — INTEGRATED DELIVERY CLOSED (LIMITED SCOPE)

- **Scope closed:** R8.3 + POLISH-01 + POLISH-02 (historical merge and postmerge CI success 2026-10-31), plus Windows B10 true NVDA certification workflow fix PR #1228, source head `68279047d9d73a501f18a1e5c7fb235f241deae7` merged at `1131f117254894d208490b2b6916fd2a4799d18b`.
- **Proof B10 source:** Windows actual NVDA, native zoom and synthetic authenticated FastAPI/React [run #42481818872](https://github.com/hraaaaf/Digital_crown/actions/runs/42481818872) SUCCESS (18 screenshots, 104 checks), owner Human Visual Approval [#42504061075](https://github.com/hraaaaf/Digital_crown/actions/runs/42504061075) SUCCESS.
- **Proof postmerge:** [Cabinet Upgrade PostgreSQL Certification #42504229531](https://github.com/hraaaaf/Digital_crown/actions/runs/42504229531), **2/2 SUCCESS** on the B10 merge commit. Merge diff is exactly one CI workflow and one synthetic browser test script, no patient/clinical runtime changes.
- **Historical DRAFT disposition:** #1131 (R5) CLOSED/NOT MERGED, core R5 API/preferences modules present on master; #1109 (R3) CLOSED/NOT MERGED, historical 3-pane DEV pilot NOT SHIPPED. The nine declared layout starting points on master are **not nine independently certified clinical UIs**. Numerous historical DRAFTs remain outside this verified closure and are not silently certified. No clinical or patient data imported.
- **Future scope:** R3 prototype and missing 3-pane specialist views are **unshipped/deferred**, preserved in [Notion backlog](https://app.notion.com/p/41277c66336281cc9654e5e69fe4e2d4), with branch/PR history intact; if deemed REQUIRED by owner, reopen LOT07 scope before treating it as completed. No blanket clearance for unimplemented clinical interfaces.
- **Roadmap:** [LOT07 canonical closeout](https://app.notion.com/p/40277c66336281b6b7ffeeecae6baff9) and [V1.5 roadmap](https://app.notion.com/p/3e677c66336281d88c82d2fbe43835fb). LOT08 G6 is cleared only for this delivered, bounded LOT07 scope. Resume LOT08 preflight against current master, and still lock G1-G5 before 08.1. 35 SP LOT08 re-estimate remains tentative, not approved baseline.
- **No release:** no Vercel, no cabinet PROD deployment, no physical multi-monitor / OS DPI200 field certification; physical tests at LOT10.

**NEXT EXACT:** Re-check current master SHA/CI, confirm relevant LOT07 closure and any REQUIRED scope exception; re-run LOT08 PRE / domain/tenant/visits before any LOT08 implementation. No implicit permission for real patient data, migration, merge of future features or production.

---


> Fichier de reprise canonique. Historique pré-audit : `docs/archive/STATE_2026-07-21.md`.

# Etat canonique scientifique — 2026-10-07

## LOT08 — Facad Ricketts 32F compatibility disposition — MERGED / POST-MERGE CLOSEOUT PENDING

- Repository: `hraaaaf/Digital_crown`
- PR: `#775` — MERGED / CLOSED
- Branch: `feat/ortho-studio-lot08-ricketts-protocol-v2`
- exact evidence HEAD before docs closeout: `575fc9e2ad21133763bdacbe512e7591a39b9f59`
- Facad source: official 3.14.1.1111 `Ricketts (32 F).cph`
- pinned profile SHA-256: `d0b442b39ac7db3dc9c46d807cb3c20bd937c69783b096b484872017f9376518`
- originally unmapped compatibility rows: **26**
- explicitly dispositioned compatibility rows: **26/26**
- remaining `unmapped`: **0**
- important boundary: **26/26 dispositioned does not mean 26 runtime aliases**. Vendor variants, landmark-authority differences, signed/presentation parity gates and non-authoritative Facad norms remain fail-closed.
- final targeted workflow: `Facad Ricketts 32F final seven contract #2` — **SUCCESS** on `575fc9e...`
- explicit adversarial review A (science/provenance): **15/15 PASS**, 0 BLOCKER / 0 MAJOR
- explicit adversarial review B (CI/reproducibility): **14/14 PASS**, 0 BLOCKER / 0 MAJOR
- additional confirmation pass: **10/10 PASS**
- final Perfection Pass: **16/16 PASS**
- final scores on evidence HEAD: EXECUTION **9.4/10**, ADVERSARIAL **9.4/10**, RETAINED **9.4/10**
- no frontend product delta; no clinical runtime activation in the final compatibility-disposition clusters
- Vercel: **NOT AUTHORIZED / NOT USED**
- merge commit: `c7209e9d35f0a85a12ee1725589bca2863aa6607` — **MERGED**

Canonical closeout source:
- `docs/handovers/2026-10-07-ricketts32-compatibility-closeout.md`

**Next exact:** merge the docs-only post-merge reconciliation PR after its exact-head documentary checks are green; then perform a read-only master coherence check and mark the LOT08 Ricketts 32F compatibility closeout fully closed.

# Etat canonique manuel - 2026-10-01

## V1.5-01 — Cabinet topology & workstation roles — CLOSED

- PR topology/workstation harness: #734 — MERGED
- merge commit #734: `a37367dcc3283ef2cb89fd79f736b387171ed89d`
- follow-up deterministic Honoraires harness: PR #738 — MERGED
- exact candidate head #738: `5de868634a2335bce13a306b70124a58d33f99d9`
- final merge commit: `b7c6d25b99e1de2b5a8e937f0909ba02b040f99e`
- T2 PR certification #5948 / run `36894203496`: **SUCCESS** end-to-end
- PR CI #7129 / run `36894203439`: **SUCCESS**
- post-merge master CI #7132 / run `36912825476`: **SUCCESS**
- post-merge Cabinet Upgrade PostgreSQL #1091 / run `36912825240`: **SUCCESS**
- deterministic Honoraires period: fixed September 2026 fixture + explicit Accounting UI period selection; no UTC/local month rollover dependency
- WorkstationModeGate/auth: unchanged by the hardening follow-up
- production runtime: unchanged by PR #738
- double-check internal review: **9.7/10**
- triple-check adversarial internal review: **9.6/10**
- Vercel: **NOT AUTHORIZED / NOT REQUIRED**

**Next exact:** open **V1.5-02 — Patient Identity & Photo**.

# Etat canonique manuel - 2026-09-30

## V1.5-00 — Hub & Dispatcher — CLOSED

- PR closeout: #724 — MERGED
- merge commit: `2f0fdeb4583e633e479627a275d7da2d6bc1375e`
- exact candidate head: `f406ae767f2585e468a15cbc65ce5d106573e9f1`
- targeted Hub/Gate/Station/Admin tests: **17/17 PASS**
- Hub Visual Proof run `36788607154`: **SUCCESS**
- Human Visual Approval run `36790450196`: **SUCCESS**
- double-check exact-head: **9.3/10**
- triple-check adversarial exact-head: **9.0/10**
- post-merge code identity: the four touched Hub/Gate runtime+test blobs are byte-identical between candidate HEAD and merge commit
- V1.5-00 residual gap closed: Control Center remains fail-soft as a local recovery surface while clinical routes remain fail-closed; Station remains restrictive
- CI doctrine: only directly impacted tests/builds/workflows are proof-relevant; broad unrelated frontend/browser matrices are not rerun or treated as blockers unless a transverse dependency or invariant requires it
- Vercel: **NOT AUTHORIZED / NOT REQUIRED**

**Next exact after closeout docs merge:** open **V1.5-01 — Cabinet topology & workstation roles**.

# Etat canonique manuel - 2026-09-29

## V1 — CLOSED / V1_OPERATIONAL

- Repository: `hraaaaf/Digital_crown`
- V1-08 initial freeze: **CLOSED** - `3c86e72bf0e132e6f79bc336d4ff9eb121d08fab`
- V1-09 installability: **CLOSED / INSTALLABLE_CERTIFIED**
- V1-10 real cabinet activation: **CLOSED / VERIFIED**
- Final certified/installed V1 SHA: `bce60b26059054ba43cf8ec13cd210098e648ea4`
- Installed release: `dc-cabinet-bce60b260590-run36628947897`
- `INSTALLABLE_CERTIFIED`: **OUI**
- `V1_OPERATIONAL`: **OUI**
- Evidence-carrying master before docs closeout: `6966ebf2656f78dd6674d435bc806bd659248d0f`
- Master CI `36638379136`: **SUCCESS**
- PostgreSQL certification `36638379156`: **SUCCESS**
- Live cabinet: health/db/storage HTTP 200; normal launcher restart OK
- Preservation: 434/434 document archives and 2915 media files; integrity PASS
- Rollback: fresh encrypted DB/media backup retained; isolated historical rollback rehearsal documented
- Limitation: V1-10 does not claim comparative visual UX certification
- Vercel: **NOT AUTHORIZED / NOT REQUIRED**

## Continuite

V1 is **CLOSED** and operational on the real cabinet. No V1 execution lot remains. After this final canonical documentation closeout is merged and re-read on `master`, execution authority transfers to the canonical POST-V1 / V1.5 roadmap. Next exact: **V1.5-00 — Hub & Dispatcher**.

# Historique canonique — 2026-08-14

## Baseline vérifiée

- Repository : `hraaaaf/Digital_crown`
- `master` après merge P0-6 : `412ab81cc5c47b7220865881f83836b539458a69`
- PR P0-6 : `#12` — MERGED
- Head candidat P0-6 certifié : `8dfe6bcfd866f62a1b41aca08554246411ad67e4`
- CI P0-6 : run `31810762297` — SUCCESS
- Backend tests/durcissement : **SUCCESS**
- Frontend tests/build : **SUCCESS**
- Garde production négative : **SUCCESS**

## Doctrine produit confirmée

- Application **on-premise / local-first**.
- Firebase : identité/licence, jamais source de vérité des dossiers patients.
- Architecture courante : modèles locaux + moteurs déterministes ; aucun LLM requis.
- Donnée patient requise mais absente = inconnue/non-évaluable ; jamais inventée.
- `tests green != validation scientifique`.
- Dans ce projet, `review` signifie par défaut **double-check complet par l’agent**, sauf demande explicite d’un reviewer externe.

## P0 — Safety & Integrity — CLOSED ✅

### P0-1 — PRESCRIPTION-MISSING-DATA-FAIL-CLOSED — CLOSED ✅

Objectif : empêcher toute valeur patient synthétique/estimée de déclencher un calcul patient-spécifique lorsqu’une donnée requise manque.

Implémentation intégrée :
- garde backend explicite `evaluable/non_evaluable` ;
- âge absent reste `None` ;
- poids absent n’est jamais synthétisé ;
- antécédents absents restent explicitement incomplets ;
- enfant sans contexte sûr ne passe pas dans le chemin pédiatrique legacy ;
- plan non évaluable = zéro ligne automatique ;
- `PrescriptionGuideModal` exige un poids explicite pour l’automatisme pédiatrique ;
- `estimateWeightFromAge()` est neutralisé ;
- top-level `assessment.age` est masqué lorsque le contexte n’est pas évaluable ;
- tests backend/frontend missing-data ajoutés.

Double-check final avant merge :
- restauration de tests `clinical_rules_engine` + `habits_engine` supprimés accidentellement ;
- test honoraires rendu déterministe, sans assertion permissive `409 ou 422` ;
- diff final : 16 fichiers, aucun fichier parasite ;
- couverture backend finale : **2459 passed, 7 skipped, 0 failed**.

Limite explicite :
- ce lot **ne valide pas scientifiquement** les constantes thérapeutiques/doses historiques du moteur legacy ;
- ces constantes restent une dette scientifique distincte.

Dette CI non bloquante :
- la CI force `httpx==0.27.2` pour compatibilité Starlette/TestClient ;
- cela entre en conflit déclaré avec `firebase-admin 7.5.0` et `ultralytics-platform 0.1.4`, qui demandent `httpx>=0.28` ;
- correction durable à traiter séparément : upgrade FastAPI/Starlette ou isolation des dépendances de test.

### P0-2 — CMO-NON-PRESCRIPTIVE-BOUNDARY — CLOSED ✅

Objectif : empêcher la synthèse CMO de transformer des mentions textuelles documentaires en diagnostic, pronostic ou décision thérapeutique autonome.

Implémentation intégrée :
- synthèse CMO convertie en signaux documentaires uniquement ;
- conservation des clés de réponse historiques nécessaires à la compatibilité ;
- ajout explicite de `evidence`, `uncertainty`, `practitioner_validation_required=True` et `automation_scope="signal_only"` ;
- pronostic autonome neutralisé en `Non déterminé automatiquement` ;
- aucune décision automatique d'initier, reporter ou modifier un traitement orthodontique ;
- mémoire Ghost CMO reclassée en `SIGNAL_CLINIQUE` ;
- tests ciblés couvrant les signaux textuels et le cas de texte négatif traité comme mention à valider, jamais comme diagnostic.

Certification :
- PR `#6` — MERGED ;
- head candidat certifié : `84c14bb54068d21a9d7c668b5d041fdac7d93e01` ;
- CI : run `31758201657` — SUCCESS ;
- backend : **2462 passed, 7 skipped, 4 warnings, 0 failed** ;
- frontend tests/build et garde production négative : **SUCCESS** ;
- merge commit : `6def2a2501cd687f5fa9be03741206b77b02643f`.

Limite explicite :
- la détection reste lexicale et peut relever une mention négative ou hors contexte ; elle est exposée comme **signal incertain à valider**, jamais comme conclusion clinique.

### P0-3 — SQLCIPHER-FAIL-CLOSED — CLOSED ✅

Objectif : empêcher un cabinet on-premise configuré sur SQLite disque de démarrer en clair si SQLCipher est indisponible ou si la migration de chiffrement échoue.

Implémentation intégrée :
- `ENVIRONMENT=cabinet` + SQLite disque impose désormais SQLCipher ;
- driver `sqlcipher3` absent = `RuntimeError` bloquant avant ouverture d'une SQLite non chiffrée ;
- migration plaintext → SQLCipher échouée = restauration du fichier d'origine puis démarrage refusé ;
- `development` et SQLite `:memory:` restent compatibles avec la CI/tests ;
- tests subprocess forcent l'absence de `sqlcipher3`, couvrent le refus de démarrage, la restauration du fichier plaintext et la non-régression development.

Certification :
- PR `#8` — MERGED ;
- head candidat certifié : `bf01fc9b66848c64ba159924ceb900da90d886fe` ;
- CI : run `31785414095` — SUCCESS ;
- backend : **2465 passed, 7 skipped, 4 warnings, 0 failed** ;
- frontend tests/build et garde production négative : **SUCCESS** ;
- merge commit : `c4adedb6528d586e3a8ec8fa5c52e33069cfb9f3`.

### P0-4 — PARTIAL-PAYMENT-NO-INFERENCE — CLOSED ✅

Objectif : empêcher `documents/generate` de créer un véritable `Payment` partiel à partir d'un montant inventé lorsque le contrat ne transporte aucun montant encaissé explicite.

Implémentation intégrée :
- `DocumentRequest` refuse `payment_status=PARTIEL` sans montant encaissé explicite ;
- le flux dédié `/accounting/payments` reste le chemin autorisé pour un paiement partiel car `PaymentCreate.amount` y est obligatoire ;
- `EN_ATTENTE` et `PAYE` restent valides ;
- tests dédiés couvrent le refus fail-closed et l'absence d'écriture partielle inférée ;
- le test financier legacy a été réaligné sur `PAYE` afin de ne plus codifier l'ancien comportement dangereux.

Certification :
- PR `#9` — MERGED ;
- head candidat certifié : `7e5066d1dd53abfde33ad5e8043cd1c5d14c4d37` ;
- CI : run `31805059079` — SUCCESS ;
- frontend tests/build et garde production négative : **SUCCESS** ;
- merge commit : `a99025d67a5470219369c633570a617e19f6f557`.

Limite UX connue :
- le bouton `PARTIEL` du Document Studio reste fail-closed jusqu'à ajout d'un vrai champ montant encaissé ; aucune valeur financière ne doit être devinée entre-temps.

### P0-5 — PRESCRIPTION-SAFETY-TENANT-GUARD — CLOSED ✅

Objectif : empêcher `POST /api/prescriptions/safety/check` de lire ou évaluer un patient hors tenant avant l'appel au service clinique.

Implémentation intégrée :
- `assert_patient_access(patient_id, current_user, db)` s'exécute avant `prescription_service.check_safety(...)` ;
- un patient d'un autre tenant produit `403 Accès refusé` ;
- le service de sécurité n'est jamais appelé pour ce patient ;
- test cross-tenant dédié ajouté.

Certification :
- PR `#11` — MERGED ;
- head candidat certifié : `d579750ce5897f86e902cf70b4e5003d188f1762` ;
- CI : run `31807332356` — SUCCESS ;
- frontend tests/build et garde production négative : **SUCCESS** ;
- merge commit : `67dc6620f5667ad4060592ef5662379fc720b6f9`.

### P0-6 — PREVIEW-MUST-BE-READ-ONLY — CLOSED ✅

Objectif : garantir qu'une preview documentaire ne persiste aucun état comptable ou archive en base.

Implémentation intégrée :
- les previews d'échéancier à données directes utilisent `flush()` puis `rollback()` au lieu de commits durables ;
- `DocumentFactory.create_installment_plan(..., archive=False)` désactive la création de `DocumentArchive` en preview ;
- le chemin preview avec `plan_id` existant désactive lui aussi l'archivage ;
- le log d'audit `GENERATE` n'est pas persisté en preview ;
- `DocumentRequest` accepte explicitement `echeancier`, alignant le contrat avec le routeur ;
- test dédié vérifie que `InstallmentPlan`, `Installment` et `AuditLog` restent inchangés et que la factory reçoit `archive=False`.

Certification :
- PR `#12` — MERGED ;
- head candidat certifié : `8dfe6bcfd866f62a1b41aca08554246411ad67e4` ;
- CI : run `31810762297` — SUCCESS ;
- backend tests/durcissement, frontend tests/build et garde production négative : **SUCCESS** ;
- merge commit : `412ab81cc5c47b7220865881f83836b539458a69`.

## P1 — Hardening — ACTIVE

### P1-1 — NATIVE-SECURE-STORAGE — CLOSED ✅ (N/A runtime courant)

Constat vérifié : le client actuel est une PWA React/Vite et le dépôt ne contient aucun runtime natif Capacitor/Tauri/Electron ni dépendance Keychain/Keystore/SecureStore à câbler.

Décision :
- ne pas introduire un wrapper natif artificiel uniquement pour satisfaire la roadmap ;
- le runtime web courant ne doit pas persister de bearer secret longue durée dans `localStorage`, `sessionStorage` ou IndexedDB ;
- tout futur client natif devra stocker les credentials longue durée exclusivement dans le Keychain/Keystore du système.

### P1-2 — MOBILE-CREDENTIAL-LIFETIME-REVOCATION — ACTIVE

Objectif : réduire l'exposition des credentials mobiles longue durée et vérifier une révocation réellement fail-closed.

Constats initiaux :
- le flux mobile/ZKA émet actuellement un bearer JWT avec une durée de vie de 365 jours ;
- une infrastructure `jti`/blacklist existe déjà et doit être conservée puis testée, pas réinventée ;
- le flux de claim one-shot doit être vérifié pour ne pas consommer définitivement le token avant validation complète du handshake.

### P1-3 — CABINET-SETTINGS-STRICT-WHITELIST

Whitelist Pydantic stricte pour les paramètres cabinet ; pas de mass assignment générique.

### P1-4 — PATIENT-SCOPED-TENANT-AUDIT

Audit tenant exhaustif des routes patient-scopées.

### P1-5 — UPLOAD-MIME-MAGIC-BYTES

MIME + magic bytes systématiques sur uploads sensibles.

### P1-6 — FRONTEND-HASACCESS-CENTRALIZATION

Centraliser `hasAccess()` frontend.

### P1-7 — LEGACY-ENGINE-QUARANTINE

Quarantainer/supprimer les anciens moteurs non utilisés.

## P2 — Certification

- CI sur le head réellement candidat.
- Backend + frontend + build.
- Smoke live/rehearsal ciblé selon le risque.
- Audit visuel 390 / 768 / 1280 pour les lots UI concernés.
- Accessibilité clavier/ARIA sur contrôles custom.
- Validation scientifique céphalométrique source par source avant toute revendication autoritative.

## Skills scientifiques applicables

- `.claude/skills/audit-prescription-flow/SKILL.md`
- `.claude/skills/audit-clinical-diagnosis-flow/SKILL.md`
- `.claude/skills/audit-panoramic-report-pipeline/SKILL.md`
- `.claude/skills/validate-cephalo-pipeline/SKILL.md`
- `.claude/rules/scientific-engineering.md`

## Lot actif

### LOT P1-2 — MOBILE CREDENTIAL LIFETIME + REVOCATION — ACTIVE

---

## Document Studio — chantier actif — 2026-08-15

Roadmap canonique : `DOCUMENT_STUDIO_ROADMAP.md`.

### R1 — P0 Cohérence médicament / Maroc-first — CLOSED ✅
- PR `#17` — MERGED.
- Head certifié : `8063b11b061ea6d1912e1b4e1a0ab8ef1fcb649a`.
- CI : run `31852032393` — SUCCESS.
- Merge : `e32ab311f72980e0797b93a306c3616a4ff66042`.

### R2 — P0 Persistance protocoles/habitudes — CLOSED ✅
- PR `#19` — MERGED.
- Head certifié : `ba66457e5f65917f71670e151826062442525200`.
- CI : run `31852827218` — SUCCESS.
- Merge : `432a95eca05d1d7b9781d2d8e81077f0dcb589f2`.

### R3 — P0 Safety orchestration — CLOSED ✅
- PR `#20` — MERGED.
- Head certifié : `becadcafb4ba0e6a5f4fda10a0053bb92c96fe1e`.
- CI : run `31853962025` — SUCCESS.
- Frontend tests/build : SUCCESS.
- Backend tests/durcissement : SUCCESS.
- Garde production négative : SUCCESS.
- Merge squash : `75e4693dc983ba1708914d16432504bea8f0cd8c`.
- Le Studio n'affiche plus d'état safety vérifié avant succès réel du backend ; états explicites `unchecked/checking/verified/error`.
- Dette R3 non bloquante : appel safety read-only parallèle encore présent dans `DocumentHub`, à dédupliquer lors du prochain lot pertinent.
- Aucune certification clinique/scientifique humaine revendiquée.

### R4 — P0 Dirty-state & actions — CLOSED ✅
- PR `#21` — MERGED.
- Head certifié : `cdaf28874bc9155d115108bba7548470300c5ca1`.
- CI : run `31855874418` — SUCCESS.
- Frontend tests/build : SUCCESS.
- Backend tests/durcissement : SUCCESS.
- Garde production négative : SUCCESS.
- Merge : `6a4debe01cf0e0ea78e49ed787cae5e26c4976b8`.
- Dirty-state dérivé du fingerprint ordonnance complet ; garde onglet/navigateur ; reset après archivage ; actualisation contexte explicite.
- Le fallback source `forme: d.forme || 'Sachets'` existe encore dans le legacy, mais son effet caché est neutralisé à la frontière transport et la forme manquante est explicitée dans l’UI.
- Aucune certification UX runtime ni clinique/scientifique humaine revendiquée.

### R5 — P1 Fast Prescription UX — CLOSED ✅
- PR `#22` — MERGED.
- Head certifié : `6de453962668e66be9e26978ec07fc9082afacb7`.
- CI : run `31878337816` — SUCCESS.
- Frontend tests/build : SUCCESS.
- Backend tests/durcissement : SUCCESS.
- Garde production négative : SUCCESS.
- Merge : `8957635e1bd50d8f44fbcef38c529b3c27f8fb32`.
- Quick-picks praticien issus des habitudes réelles : récents + fréquents. Aucun favori étoilé explicite inventé.
- Aucune certification UX runtime ni clinique/scientifique humaine revendiquée.

### R6 — P1 Protocoles + Référentiel — CLOSED ✅
- PR `#23` — MERGED.
- Head certifié : `10751078601c3aa5be728bc263e25a58e856c676`.
- CI : run `31879112143` — SUCCESS.
- Frontend tests/build : SUCCESS.
- Backend tests/durcissement : SUCCESS.
- Garde production négative : SUCCESS.
- Merge : `6f2b8a22f9cdca25cafe228f266ed46deee8281b`.
- Référentiel search-first, ajout manuel replié, contexte âge/poids visible, `Mes protocoles` réversible après masquage.
- Aucune certification UX runtime ni clinique/scientifique humaine revendiquée.

### R7 — P1 Contexte + Preview premium — CLOSED ✅
- PR finale `#26` — MERGED.
- Head certifié : `9a39ecc4d415e59c5457a58638a48ba0c22f81fd`.
- CI : run `31879649826` — SUCCESS.
- Frontend tests/build : SUCCESS.
- Backend tests/durcissement : SUCCESS.
- Garde production négative : SUCCESS.
- Merge squash : `2596da527fdd1bee5c6746f645e995f682ca3189`.
- PR intermédiaires `#24` et `#25` fermées sans merge car remplacées par le candidat consolidé sur baseline post-R6.
- Contexte patient et preview utilisent une terminologie déterministe ; preview responsive ; test backend prouve qu’une ordonnance `preview=true&archive=true` ne crée ni archive, ni audit, ni paiement, ni acte.
- Aucune certification UX runtime ni clinique/scientifique humaine revendiquée.

### P1 Ordonnance — ENGINEERING CLOSED ✅
- R1→R7 fermés et fusionnés.
- Roadmap canonique synchronisée.
- Interaction runtime et recertification UX/clinique restent des gates séparés et ne sont pas revendiqués.

### P2 Devis + Honoraires — ACTIVE 🟡
- Audit canonique : `docs/audits/DOCUMENT_STUDIO_P2_DEVIS_HONORAIRES_AUDIT.md`.

#### P2-A — Prix catalogue local conservé — CLOSED ✅
- PR `#27` — MERGED.
- Head certifié : `7289d0bf64c8139838470923622f8c0b588206e1`.
- CI : run `31882328096` — SUCCESS.
- Frontend tests/build : SUCCESS.
- Backend tests/durcissement : SUCCESS.
- Garde production négative : SUCCESS.
- Merge squash : `a8ce1f8143fd58f20aee5cb4ebb9b8827128c4cc`.
- Le wrapper répare uniquement les suggestions locales dont le prix catalogue existe ; aucun prix absent n’est inventé.

#### P2-B — PARTIEL fail-closed cohérent UI/backend — CLOSED ✅
- PR `#29` — MERGED.
- Head certifié : `d60a99c290e0e27c84d73fb95d947fa111461f7a`.
- CI finale : run `31884437013` — SUCCESS.
- Frontend tests/build : SUCCESS.
- Backend tests/durcissement : SUCCESS.
- Garde production négative : SUCCESS.
- Merge squash : `6543c3dad146bdbe055117fe0302b3fbe9cbda07`.
- Premier head `1005f2281868f435b8fb2f56066bc920b3151df5` : frontend/build + garde production verts, backend rouge uniquement parce qu’un `ValueError` Pydantic restait non sérialisable dans le contexte du handler JSON ; corrigé avec `PydanticCustomError`.
- `PARTIEL` ne peut plus devenir l’état du document dans ce flux ; aucun montant partiel n’est inféré.
- `PaymentCreate.amount` est strictement positif et les méthodes connues sont normalisées explicitement.

#### P2-E — Échéances/réconciliation financière exacte — ACTIVE 🟡
- Défaut confirmé : Honoraires global peut créer un plan dont la somme des échéances diffère du total facturé.
- Préparation P2-E : réconciliation exacte au centime frontend/backend + tests ; PR draft `#30` 3/3 verte sur ancienne baseline.
- #30 ne doit pas être mergée : reconstruction obligatoire sur baseline post-P2-B.

#### P2-F — Allocation PAYE exacte par Acte — PREPARED
- Défaut confirmé : Honoraires PAYE crée des Acte marqués PAYE mais un Payment global sans `acte_id`, ce qui peut diverger de la vue `actes-billing`.
- Helper/test d’allocation exacte préparés sur PR draft `#31`; intégration route à faire après P2-E.

#### Préparation UX suivante
- P2-C : quick actions tactiles + phases déterministes sans durée clinique estimée, PR draft `#32`.
- P2-D : handler legacy de déduplication odontogramme confirmé orphelin ; policy `dent::traitement`, PR draft `#33`.

#### Pré-audits isolés pendant les CI
- P3 : `work-20260815-p3-static-audit` — non fusionné.
- P4 : `work-20260815-p4-static-audit` — non fusionné.
- P5 : `work-20260815-p5-static-audit` — non fusionné.
- P6 : `work-20260815-p6-static-audit` — non fusionné.

#### P5-P0 clinique découvert — NON CORRIGÉ 🔴
- `HouseWizard` est atteignable via `Mode Expert`.
- `DiagnosticEngine` produit diagnostic/protocole/plan de traitement et substitue actuellement automatiquement des classes thérapeutiques à partir d’une détection textuelle d’allergie.
- Exemple source vérifié : pénicilline → remplacement `AMOXICILLINE` par `CLINDAMYCINE/MACROLIDE`; AINS → remplacement par `CORTICOSTÉROÏDES`.
- `Appliquer` transforme le résultat en insight `DETERMINISTIC` et positionne le score d’intelligence à 100 ; il ne persiste pas directement le treatment plan dans la DB au point inspecté.
- Branche de sécurité `work-20260815-p5p0-no-auto-substitution` : test de frontière ajouté, correctif applicatif non encore fusionné.
- Priorité : aucune substitution thérapeutique automatique ; exposer une alerte à validation praticien.

Aucune certification financière production, UX runtime ou clinique/scientifique humaine n’est revendiquée pour les lots actifs/pré-audits.
