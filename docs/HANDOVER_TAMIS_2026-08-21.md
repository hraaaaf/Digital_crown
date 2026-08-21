# HANDOVER — Digital Crown / Tamis applicatif

Date: 2026-08-21
Repo: `hraaaaf/Digital_crown`

## Goal
Passer l'application et le dépôt au tamis pour supprimer uniquement ce qui est prouvé obsolète, mort, local-machine, dupliqué ou hors runtime, sans casser les fonctions actives ni toucher aux données patients.

## Règles d'exécution
- preuve avant suppression ; aucun fichier ambigu supprimé au seul motif de son nom ;
- 1 préparation complète → 1 commit final → 1 cycle CI pour chaque lot lourd ;
- une CI en cours n'arrête pas le chantier : avancer sur du travail indépendant, sans polling/sleep ;
- aucun déploiement Vercel sans autorisation explicite ;
- UI/UX non touchée sur les lots ci-dessous, donc pas de captures requises ;
- ne jamais supprimer/réinitialiser/reseeder les données patients.

## État vérifié sur master
Master au moment de ce handover: `7e71cf1b7323455565827eb3d305fed38bf8100e`.

### Terminé
1. R11 Settings legacy
   - `TemplateBuilder` orphelin supprimé ; 608 lignes mortes retirées.
   - PR #190 fusionnée ; doublon #189 fermé.

2. P0 artefacts dépôt
   - `.coverage` supprimé.
   - `.vibecode-backup/` supprimé.
   - garde-fous ajoutés à `.gitignore`.
   - PR #196 fusionnée.

3. P0 tooling local
   - `.beads/` supprimé sur décision utilisateur après audit.
   - `.antigravitycli/` supprimé, symlink machine-local vers `C:/Users/lenovo/.gemini/...`.
   - garde-fous `.gitignore` ajoutés.
   - PR #197 fusionnée.

4. P1-A `backend/deprecated/` debug/check/fix ponctuels
   - 23 fichiers supprimés.
   - 1 008 lignes retirées.
   - PR #198 fusionnée.
   - CI `32475301227` success.
   - T2 `32475301155` success.
   - Patient P7 `32475301154` success.
   - Catalogue connecté `32475301296` success.

5. P1-B `backend/deprecated/` migrations/réparations/seeds historiques
   - 17 fichiers supprimés.
   - 1 427 lignes retirées.
   - commit de lot `93345f0c7158ea403a8fadff331d4f710fe14e3f`.
   - PR #200 fusionnée.
   - merge master `7e71cf1b7323455565827eb3d305fed38bf8100e`.
   - CI `32485423509` success.
   - Catalogue `32485423710` success.
   - T2 `32485423497` success.
   - Patient P7 `32485423481` success.

## Conservé volontairement
- `DigitalCrown.spec` : packaging PyInstaller réel, pas prouvé obsolète.
- `backend/deprecated/convert_to_onnx.py` : utilitaire techniquement cohérent ; `ultralytics`, `onnx`, `onnxruntime`, `onnxslim` sont encore dans `backend/requirements.txt`. À relocaliser ultérieurement vers `tools/` plutôt qu'à supprimer.
- `backend/seed_user.py` racine : version actuelle sécurisée, mot de passe généré/env ; ne pas confondre avec l'ancien `backend/deprecated/seed_user.py` supprimé.

## Lot en cours — P2 backend racine
Un commit préparatoire historique existe: `57ed82499972a437038ca74f4eac732eb2d0dad7`, mais il a été préparé avant le merge P1-B. **Ne pas le pousser tel quel.** Recréer exactement le même diff sur le master courant avant branche/PR.

Candidats P2 déjà audités à forte confiance :
- `backend/alter_db.py`
- `backend/download_fonts.py`
- `backend/download_fonts_from_css.py`
- `backend/header_bg.jpg`
- `backend/migrate_patients.py`
- `backend/migrate_scheduling.py`
- `backend/scratch/check_users.py`
- `backend/scratch/cleanup_legacy.py`
- `backend/scratch/migrate_archives.py`
- `backend/scratch/update_patients_silver.py`
- `backend/services - Raccourci.lnk`
- `backend/test_sanitizer.py`

Justification P2 : migrations manuelles anciennes, scripts `scratch/`, chemins Windows locaux, raccourci `.lnk`, utilitaires setup sans référence, test manuel hors `backend/tests/`, image racine sans référence retrouvée. `backend/scratch/` est déjà ignoré par `.gitignore` mais ses fichiers sont suivis historiquement.

### Next exact P2
1. repartir de `master` courant ;
2. reconstruire le diff P2 ci-dessus dans un seul tree/commit ;
3. comparer `master...HEAD` et prouver : 12 suppressions, 0 ajout/modification produit ;
4. créer branche/PR P2 ;
5. lancer un seul cycle CI ;
6. si vert, merger puis vérifier `master` ;
7. enchaîner P3 sans demander validation.

## P3 frontend préparé mais non publié
Préparation antérieure hors branche autour de `033b4da4…`, à reconstruire après P2 sur le master courant. Candidats déjà prouvés :
- `frontend/fix_lint.py`
- `frontend/lint-targets.txt` contenant des chemins absolus `C:\Users\lenovo\Documents\...`
- raccourci Windows `.lnk` frontend identifié pendant l'audit
- garde-fous prévus dans `.gitignore` pour `*.lnk` et `frontend/lint-targets.txt`

Ne pas publier l'ancien commit préparatoire directement : resync/reconstruction sur le master post-P2 obligatoire.

## P4 / suite du tamis
- poursuivre scan racine/reliquats : backups, temporaires, copies, chemins machine-local, artefacts générés ;
- ensuite passer aux vrais orphelins runtime : composants/routes frontend, endpoints/services backend, dépendances inutilisées, docs/tests/scripts obsolètes ;
- toute surface UI réellement touchée déclenche le protocole visuel complet BEFORE → Goal/mockup → implémentation → AFTER → score.

## GitHub / concurrence
Au moment du closeout P1-B, ses quatre runs étaient verts et la PR #200 a été fusionnée. Avant de publier P2, vérifier une seule fois qui occupe GitHub ; ne pas poller.

## Progression
Aucun pourcentage global fiable n'est déclaré tant que l'inventaire total n'est pas borné et pondéré. Ne pas inventer de %.

## Reprise recommandée
Commencer par vérifier `master`, relire ce fichier, puis exécuter immédiatement P2 selon le Next exact ci-dessus. Aucun human gate n'est requis pour ces suppressions déjà auditées, sauf apparition d'un conflit ou d'une nouvelle preuve d'utilisation.