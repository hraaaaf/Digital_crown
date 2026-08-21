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
- Preuve structurelle : aucun des deux routers n'était monté ; `clinical.py` appelait une méthode disparue ; `medical_library.py` dupliquait d'anciennes surfaces cliniques et contenait des calculs pédiatriques hardcodés.
- Preuve de non-régression : CI `32505278694`, T2 `32505278677`, Catalogue `32505278710`, Patient P7 `32505278733` — SUCCESS.
- Cartographie `backend/routers` après audit : aucun autre router orphelin évident ; les modules `patient_*`/`imaging_lifecycle_p4` sont injectés par `routers/__init__.py`, et les façades `*_legacy`/`*_core` restantes sont utilisées.

## Éléments explicitement conservés
- `backend/routers/admin_legacy.py` : utilisé par `admin.py`.
- `backend/routers/mobile_legacy.py` : utilisé par `mobile.py`.
- `backend/routers/prescriptions_core.py` : utilisé par la façade `prescriptions.py`.
- `backend/services/base_template_core.py` : utilisé par la façade `base_template.py`.
- `backend/services/prescription_service_legacy.py` : classe parente active de `PrescriptionService`.
- `backend/deprecated/convert_to_onnx.py` : convertisseur générique, consolidation éventuelle mais suppression non prouvée.
- `backend/scripts/migrate_qr_style.py` : compatibilité anciennes bases non encore remplacée de façon certaine.
- `Start_DigitalCrown.bat`, `Start_PROD.bat`, `run_real_backend.ps1` : relèvent du chantier Portability/launcher.

## P4-D — dead Patient phase workflows — PRÉPARÉ, NON VALIDÉ
Scope audité : 14 workflows historiques P3→P6 qui ciblent exclusivement des branches de stack supprimées (`agent/patient-page-p2-journey`, `agent/patient-page-p3-clinique`, `agent/patient-page-p4-imagerie`, `agent/patient-page-p5-documents`).

Preuves disponibles :
- les quatre branches historiques ont été vérifiées absentes ;
- les workflows P3/P4/P5/P6 BEFORE/AFTER/backend/UI et stack-sync concernés ne peuvent donc plus se déclencher normalement ;
- deux stack-sync conservent inutilement `contents: write` ;
- la certification consolidée `patient-p7-final-certification.yml` tourne sur chaque PR et recouvre explicitement les contrats/tests P0→P6 backend, frontend et navigateur ;
- les régressions `patient-p1-architecture-after.yml` et `patient-p2-journey-after.yml` restent actives sur `master` et doivent être conservées ;
- les workflows Settings R5 BEFORE/AFTER restent eux aussi actifs sur `master` et sont conservés.

Préparation hors branche uniquement : ancien candidat `7ddd398fca1c0a943b79da6fa120177388a999f0`, 14 suppressions, +0 / -1 561. Il doit être reconstruit sur le master courant avant publication.

## Audit workflows — reste à trancher séparément
- `patient-p0e-payment-after.yml` : ancienne branche dédiée + manuel, ne surcharge pas les PR actuelles.
- `patient-indicators-before.yml` : snapshot BEFORE figé sur ancien commit, candidat futur de retrait mais non responsable de la file courante.
- Ne supprimer aucun autre workflow sans vérifier trigger, branche cible et couverture de remplacement.

## Next exact
1. Reconstruire P4-D sur le master courant après ce closeout.
2. Vérifier diff exact : 14 suppressions, aucune autre modification.
3. Publier un seul commit P4-D et une seule PR.
4. Certifier CI + T2 + Catalogue + Patient P7.
5. Si vert : merge exact-head, closeout canonique, puis poursuivre les autres orphelins prouvables.
