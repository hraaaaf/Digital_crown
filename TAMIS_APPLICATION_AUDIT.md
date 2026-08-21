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

## Éléments explicitement conservés
- `backend/routers/admin_legacy.py` : utilisé par `admin.py`.
- `backend/routers/mobile_legacy.py` : utilisé par `mobile.py`.
- `backend/routers/prescriptions_core.py` : utilisé par la façade `prescriptions.py`.
- `backend/services/base_template_core.py` : utilisé par la façade `base_template.py`.
- `backend/services/prescription_service_legacy.py` : classe parente active de `PrescriptionService`.
- `backend/deprecated/convert_to_onnx.py` : convertisseur générique, consolidation éventuelle mais suppression non prouvée.
- `backend/scripts/migrate_qr_style.py` : compatibilité anciennes bases non encore remplacée de façon certaine.
- `Start_DigitalCrown.bat`, `Start_PROD.bat`, `run_real_backend.ps1` : relèvent du chantier Portability/launcher.

## P4-C — dormant clinical routers — PRÉPARÉ, NON VALIDÉ
Candidats :
- `backend/routers/clinical.py`
- `backend/routers/medical_library.py`

Preuves disponibles :
- ni l'un ni l'autre n'est monté dans `backend/main.py` ou `backend/routers/__init__.py` ;
- `clinical.py` appelle `ClinicalIntelligenceService.extract_pubmed_pearls()`, méthode absente du service actuel ;
- `medical_library.py` contient d'anciennes surfaces médicaments/diagnostics/règles et des calculs pédiatriques hardcodés ;
- les surfaces canoniques actuelles incluent `clinical_data.py` (RBAC, données cliniques versionnées) et `medications.py` (référentiel national).

La suppression P4-C ne doit être créditée qu'après certification exacte du HEAD puis merge.

## Audit workflows — en cours
- Les anciens workflows ne sont pas supprimés sur leur nom seul.
- `patient-p0e-payment-after.yml` : ancienne branche dédiée + manuel, ne surcharge pas les PR actuelles.
- `patient-p1-architecture-after.yml` et `patient-p2-journey-after.yml` : régressions PR encore path-scoped, conservées.
- `patient-indicators-before.yml` : snapshot BEFORE figé sur ancien commit, candidat futur de retrait mais non responsable de la file courante.

## Next exact
1. Rebaser/reconstruire P4-C sur le master courant après ce closeout.
2. Publier un seul commit P4-C.
3. Certifier CI + T2 + Catalogue + Patient P7.
4. Si vert : merge exact-head, puis poursuivre l'audit lifecycle des workflows et autres orphelins runtime.
