# Tamis applicatif — état canonique

Dernière mise à jour : 2026-08-21

## Goal
Réduire le dépôt aux sources, outils et preuves encore utiles, sans supprimer de runtime actif ni toucher aux données patient.

## Doctrine de décision
- Suppression uniquement avec preuve de caractère généré, machine-local, one-shot, non monté ou remplacé.
- Les suffixes `legacy`, `core` ou `deprecated` ne constituent jamais seuls une preuve.
- Toute suppression de code potentiellement importé est certifiée par les gates courants avant merge.
- Aucun déploiement Vercel dans ce chantier.

## Lots validés

### P2 — backend racine — MERGED ✅
- Merge : `508cd7856dd3b49c03c08e76beaac00d167ce4f0`
- 12 fichiers historiques/machine-local retirés.
- Certification : CI + T2 + Catalogue + Patient P7 vertes.

### P3 — frontend local artifacts — MERGED ✅
- PR : #203
- Head certifié : `81cbf748ec63440915e43ea864ec2b66cd6df284`
- Merge : `27c8821fd8e7cb99ff9c5aad9b9a5a97529fb63b`
- Suppressions : `frontend/fix_lint.py`, `frontend/lint-targets.txt`, raccourci Windows racine frontend.
- `.gitignore` protège désormais `*.lnk` et `frontend/lint-targets.txt`.
- 4/4 certifications vertes.

### P4-A — generated/local tracked artifacts — MERGED ✅
- PR : #204
- Head certifié : `71338dcbb2b814bbf82f43cb37428a05150a00e5`
- Merge : `17e31ed7cd84fe955b125800f5a8f2cbbde75c14`
- Diff : 5 285 fichiers, +5 / -1 160 831.
- Retirés : `node_modules/`, `brain/`, `scratch/`, `test-results/`, logs, sorties coverage et previews temporaires suivis par erreur.
- Garde-fous `.gitignore` ajoutés pour ces artefacts.
- 4/4 certifications vertes.

### P4-B — obsolete one-shot patches — MERGED ✅
- PR : #205
- Head certifié : `36017d092927cf1dbce5bbc12874752a5049a9ee`
- Merge : `9454c15788c501f19b0a607bba1fd7e6ac563076`
- Diff : 16 fichiers, +0 / -1 333.
- Retirés : patchs source ponctuels, scripts de maintenance risqués/hardcodés, anciens snapshots/tests, capture P0-H historique et deux raccourcis Windows résiduels.
- Conservés volontairement : backup/bootstrap/release/recovery, migration QR, exports ONNX, `backend/seed_demo.py`, launchers actuels.
- 4/4 certifications vertes.

### P4-C — dormant clinical routers — MERGED ✅
- PR : #206
- Head certifié : `5cb01ca0e54005f5fbdf5786e5682b62465b6ff9`
- Merge : `e1df2bececfe4afa57848394bfe04bc619d56084`
- Diff : 2 fichiers, +0 / -329.
- Retirés : `backend/routers/clinical.py` et `backend/routers/medical_library.py`.
- Preuve structurelle : aucun des deux routers n'était monté ; `clinical.py` appelait une méthode disparue ; `medical_library.py` dupliquait d'anciennes surfaces cliniques, contenait des calculs pédiatriques hardcodés et référençait des modèles désormais absents de `models.py`.
- Preuve de non-régression : CI `32505278694`, T2 `32505278677`, Catalogue `32505278710`, Patient P7 `32505278733` — SUCCESS.
- Cartographie `backend/routers` après audit : aucun autre router orphelin évident ; les modules `patient_*`/`imaging_lifecycle_p4` sont injectés par `routers/__init__.py`, et les façades `*_legacy`/`*_core` restantes sont utilisées.

### P4-D — dead Patient phase workflows — MERGED ✅
- PR : #208
- Head certifié : `77470f493edb28c0f70ba95fc6b81b28e248871a`
- Merge : `38460500e04f2fa714a3268324a4ae5ea665543e`
- Diff : 14 workflows, +0 / -1 561.
- Retirés : anciens workflows Patient P3→P6 BEFORE/AFTER/backend/UI/stack-sync ciblant exclusivement des branches empilées désormais supprimées.
- Branches historiques vérifiées absentes : `agent/patient-page-p2-journey`, `agent/patient-page-p3-clinique`, `agent/patient-page-p4-imagerie`, `agent/patient-page-p5-documents`.
- Deux stack-sync retirés détenaient encore inutilement `contents: write`.
- Remplacement prouvé : `patient-p7-final-certification.yml` reste actif sur chaque PR et recouvre explicitement les contrats/tests P0→P6 backend, frontend et navigateur.
- Préservés : `patient-p1-architecture-after.yml`, `patient-p2-journey-after.yml`, workflows Settings actifs, `patient-p0e-payment-after.yml` (manuel encore utilisable), `patient-indicators-before.yml` (baseline encore déclenchable).
- Preuve de non-régression : CI `32506537354`, T2 `32506537235`, Catalogue `32506537212`, Patient P7 `32506537310` — SUCCESS.

### P4-E — one-shot media count utility — MERGED ✅
- PR : #209
- Head certifié : `24ed414b94c035e170ba524e4c33f891d3f96ee2`
- Merge : `6e191fa779ef0b23b4028697df07598c45301655`
- Diff : 1 fichier, +0 / -35.
- Retiré : `backend/scripts/count_records.py`.
- Preuve d'obsolescence : créé avec le hardening médias du 2026-07-06 comme utilitaire explicite de comptage avant/après ; aucune référence actuelle ; aucun rôle runtime, migration, backup/recovery ou launcher.
- Preuve de non-régression : CI `32508317596`, T2 `32508317598`, Catalogue `32508317593`, Patient P7 `32508317587` — SUCCESS.

### P4-F — superseded Devis certification harness — MERGED ✅
- PR : #211
- Head certifié : `b3e8c54c0f10fc77982e7f3a567571ad6d9c8577`
- Merge : `b3aa7711e6ac0256e1a9b718ce4f55068e39b6c3`
- Diff : 1 fichier, +0 / -91.
- Retiré : `scripts/certify_p3_devis.sh`.
- Preuve de remplacement : `scripts/certify_document_studio_p3_p6.sh` recouvre les mêmes tests Devis ciblés et une régression P3→P6 plus large ; `certify_document_studio_t2.sh` exige les harness P3→P6, P7 et T1, mais pas ce harness P3 Devis.
- Preuve de non-régression : CI `32509375426`, T2 `32509375450`, Catalogue `32509375382`, Patient P7 `32509375455` — SUCCESS.

### P4-G — shared VS Code workspace sanitization — MERGED ✅
- PR : #212
- Head certifié : `abe2e4ca8b32ab3ade4c4b6218240d8faa0ac53a`
- Merge : `28c2aeb084c19cd77332db14af62a88cb843033a`
- Diff : `.vscode/settings.json` uniquement, +2 / -6.
- Retirés : préférence personnelle `editor.fontSize`, préférence locale `task.quickOpen.showAll`, interpréteur Windows `python.defaultInterpreterPath`, tableau vide `css.customData`.
- Conservés : `css.lint.unknownAtRules` et `python.analysis.extraPaths`, normalisé en `${workspaceFolder}/backend`.
- Preuve de non-régression : CI `32513372590`, T2 `32513372730`, Catalogue `32513372685`, Patient P7 `32513372642` — SUCCESS.
- Vérification post-merge : le fichier sur `master` contient uniquement les deux réglages portables attendus.

## Éléments explicitement conservés
- `backend/routers/admin_legacy.py` : utilisé par `admin.py`.
- `backend/routers/mobile_legacy.py` : utilisé par `mobile.py`.
- `backend/routers/prescriptions_core.py` : utilisé par la façade `prescriptions.py`.
- `backend/services/base_template_core.py` : utilisé par la façade `base_template.py`.
- `backend/services/prescription_service_legacy.py` : classe parente active de `PrescriptionService`.
- `backend/deprecated/convert_to_onnx.py` : convertisseur générique paramétrable ; `backend/scripts/panoramic_export.py` est spécialisé et ne le remplace pas exactement.
- `backend/scripts/migrate_qr_style.py` : compatibilité anciennes bases non encore remplacée de façon certaine.
- `scripts/certify_document_studio_p3_p6.sh`, `scripts/certify_document_studio_p7.sh`, `scripts/certify_document_studio_t1.sh` : harness actifs de régression ; `certify_document_studio_t2.sh` exige explicitement leur présence.
- `scripts/migrate_bot_pending_actions.py` et `scripts/migrate_m1_subscription_plans.py` : migrations idempotentes/rejouables sans remplacement canonique suffisamment prouvé.
- backup/bootstrap/release/recovery, setup HTTPS/backup, probes T2, prod safety, preflight data audit et validation scientifique : rôles opératoires actuels ou de reprise, conservés.
- `Start_DigitalCrown.bat`, `Start_PROD.bat`, `run_real_backend.ps1` : relèvent du chantier Portability/launcher.
- `.claude/` et `.codex/` : configurations partagées de développement ; non classées machine-local.

## Audit workflows — état après P4-D
- Le cimetière Patient P3→P6 mort est retiré.
- `patient-p0e-payment-after.yml` : branche automatique historique supprimée, mais `workflow_dispatch` reste utilisable ; conservé.
- `patient-indicators-before.yml` : baseline figée mais toujours déclenchable sur PR `master` quand son goal/mockup/workflow change ; conservé.
- `agenda-r7-downstream-baseline.yml` : déclenché uniquement si son workflow change ; conservé.
- `dashboard-visual-cert.yml` : path-scoped Dashboard + manuel ; conservé.
- Les workflows Settings inspectés restent actifs sur `master` ; conservés.

## Closeout borné — 2026-08-21

### Résultat
Le Goal du tamis raisonnablement borné est atteint sur les classes auditées : artefacts générés suivis, fichiers machine-local, scripts one-shot, anciens patchs/snapshots, routers dormants, workflows de branches disparues, harness de certification remplacés et préférences workspace locales.

### Preuve
- Tous les lots P2→P4-G crédités ci-dessus ont été fusionnés après leurs preuves respectives.
- Les suppressions potentiellement sensibles ont été validées par CI + T2 + Catalogue + Patient P7 sur leur HEAD exact avant merge.
- Le balayage terminal borné n'a produit aucune suppression supplémentaire suffisamment prouvée pour justifier un nouveau lot.
- Les éléments ambigus ou encore opératoires sont explicitement conservés au lieu d'être supprimés sur leur nom.
- Aucun changement n'a touché les données patient.
- Aucun déploiement Vercel n'a été effectué.

### Limite
Ce closeout ne prétend pas démontrer l'absence mathématique de tout code mort futur ou de toute dette d'architecture. Les futurs changements peuvent créer de nouveaux reliquats ; un nouveau tamis devra alors repartir de preuves fraîches.

## Next exact
Aucune suppression supplémentaire n'est autorisée sans nouvelle preuve positive. Le prochain chantier distinct pour les fichiers volontairement conservés est `Portability / launcher`, notamment les launchers Windows et chemins locaux encore nécessaires au runtime actuel.
