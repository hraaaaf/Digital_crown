# REPO-LARGE-FILES-SAFE-AUDIT-1 — Audit read-only des fichiers volumineux

**Date** : 2026-07-11
**Périmètre** : `C:\Users\lenovo\Documents\Cabinet\DigitalCrown` uniquement (dépôt de travail).
**Aucun fichier supprimé, déplacé, compressé ou modifié.** `DigitalCrown-Runtime\`, les
médias réels, `digitalcrown_db`, `clinical_vault.db` et les backups réels n'ont pas été
touchés — vérifié explicitement en fin d'audit (PID réel 14516 inchangé, port 8005
toujours actif).

---

## ⚠️ Constat prioritaire — à traiter avant tout nettoyage de disque

**`backend/static/{documents,reports,uploads,archives,patients}` (439 Mo) est un dossier
actif dans le code, pas un dossier orphelin.** `document_factory.py` et tous les
générateurs PDF (`ordonnance_gen.py`, `certificat_gen.py`, `bilan_gen.py`,
`panoramic_gen.py`, etc.) utilisent `output_dir="static/documents"` /
`"static/reports"` comme chemin **relatif par défaut**, et `main.py` sert ces fichiers
via des routes authentifiées (`/api/static/uploads/...`, `/api/static/archives/...`,
`/api/static/documents/...`), testées par `test_media_security.py`. Ce n'est donc pas
un dossier "dev inutile" au sens strict.

Ce qui a été vérifié (métadonnées uniquement, aucun contenu ni nom de fichier
patient consulté) :
- 1419 fichiers, du **13/02/2026** au **02/07/2026** — plus aucune écriture depuis 9 jours
- Le vrai média cabinet (`%APPDATA%\DigitalCrown\media\`) est toujours actif jusqu'au
  **10/07/2026** — donc `backend/static/` a cessé d'être alimenté nettement avant que
  la vraie activité cabinet ne s'arrête
- Le process réel actuel (PID 14516) tourne depuis la release immuable
  `20260711-012549-738eb5234efc`, qui **ne contient aucun dossier `static/`** — le
  process réel actuel n'y a jamais écrit
- La plage de dates (13/02–02/07) couvre exactement la période où le backend réel
  tournait via `uvicorn --reload` directement depuis le dépôt (avant
  RRIG-1, 2026-07-10) — cohérent avec un `cwd` = dépôt à cette époque, ce qui explique
  que le chemin relatif `static/documents` ait atterri ici plutôt que dans
  `%APPDATA%`

**Hypothèse la plus probable, non confirmée : ce sont des documents générés réellement
par le cabinet avant le passage au runtime immuable — jamais couverts par aucun
mécanisme de backup construit dans cette session** (RRIG-1, AUTO-BACKUP-*,
SCHEDULED-TASK-BACKUP-* n'ont sauvegardé que `digitalcrown_db` et
`%APPDATA%\DigitalCrown\media\`, jamais `backend/static/`). Alternative possible : il
s'agit de données de test/rehearsal antérieures. **Impossible de trancher sans lecture
de contenu, ce qui sort du périmètre read-only de cette mission.**

**Recommandation : mission dédiée `BACKEND-STATIC-COVERAGE-AUDIT-1` avant toute
décision de suppression ou d'archivage sur ce dossier.** Ne pas le classer "sûr à
supprimer" tant que son statut (données réelles historiques vs données de test) n'est
pas confirmé par le CTO.

---

## 1. Espace libre initial

4,41 Go au lancement de l'audit (2026-07-11). **3,24 Go en fin d'audit** — baisse
supplémentaire pendant l'audit due au scheduler de backup planifié
(`DigitalCrown_DailyBackup_v2`) tournant en tâche de fond, pas à cet audit (100 %
read-only). Confirme l'urgence du sujet disque, indépendamment de cette mission.

## 2. Taille totale du dépôt

**10,02 Go**

## 3. Taille par dossier (racine du dépôt)

| Dossier | Taille |
|---|---|
| `backend/` | 3,111 Go |
| `venv/` | 3,045 Go |
| `.venv312/` | 2,740 Go |
| `frontend/` | 0,435 Go |
| `build/` | 0,253 Go |
| `artifacts/` | 0,162 Go |
| `.git/` | 0,115 Go |
| `node_modules/` (racine) | 0,082 Go |
| `scratch/` | 0,031 Go |
| `e2e/` | 0,030 Go |
| `.vibecode-backup/` | 0,017 Go |
| `.beads/`, `install_rehearsal_media/`, autres | < 0,002 Go chacun |
| Fichiers directs à la racine | 1,3 Mo |

**Sous-détail `backend/`** :

| Sous-dossier | Taille |
|---|---|
| `ai_models/` | 2,144 Go |
| `backups/` | 0,525 Go |
| `static/` | 0,426 Go |
| `tests/` | 10 Mo |
| reste (`services/`, `routers/`, etc.) | < 5 Mo au total |

**Sous-détail `ai_models/`** :

| Sous-dossier | Taille |
|---|---|
| `cephld_cca/` | 1068,5 Mo |
| `dentex_repo/` | 98 Mo (dont ~65 Mo de `.git/` imbriqué) |
| `CL-Detection2023/` | 75,2 Mo |
| `CLdetection2023-master/` | 20,1 Mo |
| `cephmark/` | 5,4 Mo |
| `cephalometric-master/` | 2 Mo |
| + fichiers `.pt`/`.onnx` à la racine (`best.pt` 350 Mo, `best.onnx` 249 Mo, `panoramic_model.onnx` 217,6 Mo, `panoramic_model.pt` 109 Mo) | ~925 Mo |

**Sous-détail `backend/static/`** :

| Sous-dossier | Taille |
|---|---|
| `models/` | 250 Mo (1 fichier : `panoramic_model.onnx`, différent du modèle actif) |
| `documents/` | 112 Mo |
| `uploads/` | 33 Mo |
| `archives/` | 28 Mo |
| `reports/` | 12 Mo |
| `patients/` | 3,8 Mo |
| `archive/`, `backups/` | 0 |

## 4. Top 100 fichiers (extrait — les 20 plus gros)

| Taille | Fichier | Dernière modif |
|---|---|---|
| 944,6 Mo | `.venv312\...\tensorflow\...\_pywrap_tensorflow_common.dll` | 08/07/2026 |
| 944,6 Mo | `venv\...\tensorflow\...\_pywrap_tensorflow_common.dll` | 19/02/2026 |
| 350,7 Mo | `backend\ai_models\best.pt` | 04/05/2026 |
| 293,5 Mo | `.venv312\...\torch\lib\torch_cpu.dll` | 08/07/2026 |
| 266,0 Mo | `backend\backups\media_backup_20260710_200559.zip.enc` | 10/07/2026 |
| 266,0 Mo | `backend\backups\media_backup_20260711_004950.zip.enc` | 11/07/2026 |
| 252,7 Mo | `venv\...\torch\lib\torch_cpu.dll` | 19/02/2026 |
| 249,1 Mo | `backend\static\models\panoramic_model.onnx` | 11/05/2026 |
| 249,1 Mo | `backend\ai_models\best.onnx` | 11/05/2026 |
| 217,6 Mo | `backend\ai_models\panoramic_model.onnx` (modèle **actif**) | 29/04/2026 |
| 176,2 Mo | `.venv312\...\_polars_runtime.pyd` | 08/07/2026 |
| 173,9 Mo | `venv\...\_polars_runtime.pyd` | 29/04/2026 |
| 109,2 Mo | `backend\ai_models\panoramic_model.pt` | 29/04/2026 |
| 101,7 Mo | `venv\...\llvmlite.dll` | 30/05/2026 |
| 80,1 Mo | `venv\...\libclang.dll` | 19/02/2026 |
| 80,1 Mo | `.venv312\...\libclang.dll` | 08/07/2026 |
| 75,4 Mo | `build\DigitalCrown\DigitalCrown.exe` | 07/07/2026 |
| 75,0 Mo | `build\DigitalCrown\DigitalCrown.pkg` | 07/07/2026 |
| 75,0 Mo | `build\DigitalCrown\PYZ-00.pyz` | 07/07/2026 |
| 73,4 Mo | `.git\objects\pack\pack-....pack` | 29/05/2026 |

Puis ~15 fichiers `.pth` de 33,65 Mo chacun sous
`backend\ai_models\cephld_cca\model\...` (checkpoints d'entraînement, ~500 Mo au
total), et `backend\ai_models\dentex_repo\.git\objects\pack\...` (65,0 Mo, dépôt Git
imbriqué).

**Nombre de fichiers > 20 Mo : 44** (comptage sur l'extrait top-100 filtré à ce seuil ;
liste complète disponible sur demande — non dupliquée ici pour rester lisible).

## 5. Top 50 dossiers

Voir section 3 (tableaux par niveau) — la profondeur demandée est couverte par
`ai_models/*` et `backend/static/*`, qui concentrent l'essentiel de la variance.

## 6. Doublons détectés

| Élément | Constat |
|---|---|
| **`venv/` vs `.venv312/`** | Environnements Python quasi-identiques : mêmes paquets lourds présents en double (`tensorflow` 944,6 Mo ×2, `torch_cpu.dll` ~250-293 Mo ×2, `_polars_runtime.pyd` ~175 Mo ×2, `libclang.dll` 80,1 Mo ×2, `cv2.pyd` ~71 Mo ×2, `numpy.libs` 36,4 Mo ×2). **Espace dupliqué estimé : ~2,7 Go.** |
| `CL-Detection2023/` (75,2 Mo) vs `CLdetection2023-master/` (20,1 Mo) | Noms quasi-identiques, tailles différentes — probable double import du même dépôt externe (zip + clone), à vérifier fichier par fichier avant toute action |
| `backend/ai_models/best.onnx` (249,1 Mo) vs `backend/static/models/panoramic_model.onnx` (249,1 Mo) | **Taille identique**, hash **non comparé** (`best.onnx` n'a pas été hashé dans cet audit) — à vérifier avant toute décision |
| `backend/ai_models/panoramic_model.onnx` (217,6 Mo, hash `1AE20CE5...`) vs `backend/static/models/panoramic_model.onnx` (249,1 Mo, hash `02D344FC...`) | **Hash différent confirmé** — ce n'est **pas** un doublon malgré le nom identique ; probablement une version antérieure ou un export différent du modèle |

Aucun `Get-FileHash` en masse (>10 Mo) n'a été exécuté sur l'ensemble du dépôt — seuls
les cas ci-dessus, identifiés comme suspects par nom/taille, ont été vérifiés
individuellement. Une passe de hashing complète (section 4 de l'ODM) reste à faire si
une mission de nettoyage est lancée.

## 7. Caches et artefacts générés

| Élément | Taille | Suivi Git | Ignoré | Risque suppression |
|---|---|---|---|---|
| `__pycache__/` (189 dossiers sous `backend/`) | négligeable (dossiers parents `services/`, `routers/`, `tests/` déjà < 10 Mo au total) | Non | Oui | Aucun |
| `.pytest_cache/` | 299 Ko | Non | Oui | Aucun |
| `scratch/__pycache__` | 4 Ko | Non | Oui | Aucun |
| `frontend/dist-rehearsal/` | 4,36 Mo | Non | Oui | Aucun — recréable via `npm run build:rehearsal` |
| `frontend/dist-test/` | absent | — | — | — |
| `build/DigitalCrown/` | 253 Mo | Non | **Non couvert par `.gitignore`** (seul `build/` générique à la racine, `dist_cabinet/` ajouté récemment) | Faible — artefact intermédiaire PyInstaller du même build stale (07/07/2026) que `dist_cabinet/` déjà supprimé avec accord CTO |

**Ne pas confondre avec `frontend/dist/` (4,36 Mo)** : c'est le build actuellement
servi par le backend réel (`index-BO2OChwV.js`, confirmé tout au long de cette
session) — **protégé, catégorie "ne jamais toucher"**, pas un cache.

## 8. Environnements Python

| Environnement | Taille | Utilisé par | Dernière modif |
|---|---|---|---|
| `venv/` | 3,045 Go | `run_real_backend.ps1`, `run_scheduled_backup.ps1`, `DigitalCrown_DailyBackup_v2` (tâche Windows active) | continue |
| `.venv312/` | 2,740 Go | **Référencé par `backend/scripts/run_rehearsal_backend.ps1`** et documenté dans `docs/NEW_CABINET_INSTALL_PATH.md` | 08/07/2026 (récent — pendant cette session) |

`.venv312` n'est **pas** un résidu abandonné au sens strict : il est toujours cité par
un script actif (`run_rehearsal_backend.ps1`) et a été modifié il y a 3 jours. Sa
nécessité réelle (le venv rehearsal a-t-il vraiment besoin d'être séparé du venv
principal ?) n'a pas pu être tranchée dans le périmètre read-only de cet audit —
**catégorie I, ne pas supprimer sans vérification explicite que
`run_rehearsal_backend.ps1` n'en a plus besoin.**

## 9. Node modules et builds

| Élément | Taille | Suivi Git actuel | Risque |
|---|---|---|---|
| `frontend/node_modules/` | 431,8 Mo | Non (`.gitignore` : `frontend/node_modules/`) | Aucun — recréable via `npm install` |
| `node_modules/` (racine) | 82 Mo | **OUI — 5215 fichiers suivis, aucune règle `.gitignore` ne couvre ce chemin** | Bloat Git permanent, voir section 12 |
| `e2e/node_modules/` | 18 Mo | **OUI — 186 fichiers suivis** | Bloat Git permanent |
| `e2e/test-results/` | inclus dans les 186 fichiers ci-dessus | **OUI — inclut des `trace.zip` de runs Playwright réels (jusqu'à 2,9 Mo chacun)** | Artefacts de test, jamais censés être versionnés |
| `frontend/dist/` | 4,36 Mo | Non (`.gitignore`) | **Protégé — servi par le backend réel** |

## 10. Modèles IA

| Modèle | Taille | Référencé par le code actif | Statut |
|---|---|---|---|
| `backend/ai_models/panoramic_model.onnx` | 217,6 Mo | `panoramic_service.py`, `sota_panoramic_service.py` | **Actif, confirmé par les logs de boot réels (RRIG-1)** |
| `backend/ai_models/cephld_cca/` (dossier entier) | 1068,5 Mo | `vision_service.py` (référence le dossier comme `repo_path`) | Le dossier est référencé, mais contient ~15+ checkpoints `.pth` de 33,65 Mo chacun (epochs successifs d'entraînement) — un seul est probablement effectivement chargé par le code interne à ce repo vendored ; **lequel n'a pas été déterminé dans cet audit** |
| `backend/ai_models/best.pt` | 350,7 Mo | `deprecated/convert_to_onnx.py` uniquement (script déprécié) | Probable résidu de pipeline de conversion, non chargé par l'app en production |
| `backend/ai_models/best.onnx` | 249,1 Mo | Aucune référence trouvée dans le code non-déprécié | Usage inconnu — possible doublon de `panoramic_model.onnx` (à vérifier par hash) |
| `backend/ai_models/panoramic_model.pt` | 109,2 Mo | Aucune référence directe trouvée | Probable poids source pré-export ONNX |
| `backend/static/models/panoramic_model.onnx` | 249,1 Mo | Aucune route ni service ne pointe vers `static/models` | Orphelin probable (voir section 6) |
| `backend/ai_models/dentex_repo/` | 98 Mo (dont 65 Mo de `.git/` imbriqué) | Non vérifié dans le code (nom suggère un dépôt externe cloné tel quel) | `.git/` imbriqué = dette sans ambiguïté ; le reste du dossier à vérifier |
| `backend/ai_models/CL-Detection2023/` + `CLdetection2023-master/` | 95,3 Mo cumulés | Non vérifié | Doublon probable du même dépôt externe (compétition CL-Detection), noms quasi-identiques |

**Aucun modèle n'a été classé "sûr à supprimer" sur la seule base de sa taille**,
conformément à la consigne — chaque candidat listé ci-dessus nécessite une vérification
de code supplémentaire (quel fichier exact `cephld_cca`'s code charge-t-il ?) avant
toute décision.

## 11. Backups et archives

| Emplacement | Contenu | Statut |
|---|---|---|
| `backend/backups/` | 525 Mo — 3 paires DB+médias (07-09, 07-10, 07-11), retenues manuellement lors d'un nettoyage précédent (accord CTO) | **Backups manuels réels, protégés** |
| `artifacts/safety-backups/` | 168 Mo | Nom suggère des sauvegardes de sécurité liées aux missions "SAFETY" antérieures (ex. `CABINET-PATIENT-DATA-SAFETY-1`, visible dans l'historique Git) — **contenu non inspecté, à vérifier avant toute action** |
| `artifacts/preflight/` | 156 Ko | Petit, probablement des logs de préflight de missions passées |
| `artifacts/test_docs/` | 0 | Vide |
| `install_rehearsal_media/`, `treatment_journey_rehearsal_media/` | < 1 Mo chacun | Médias de rehearsal, déjà `.gitignore`d (ajouté lors d'une mission précédente) |

Aucun de ces éléments n'a été proposé à suppression — tous nécessitent soit une
confirmation de contenu (artifacts/safety-backups) soit sont déjà correctement
protégés (backend/backups).

## 12. Taille de `.git`

```
count: 130 objets non empaquetés (572,28 Kio)
in-pack: 11748 objets empaquetés
size-pack: 115,69 Mio
garbage: 1 objet, 1,81 Kio (résidu d'opération incomplète, négligeable)
```

**Total ≈ 116 Mo.** Pas de `git gc`/`prune`/réécriture effectué (interdit par la
mission).

**Constat significatif** : les 30 plus gros blobs de l'historique Git incluent des
fichiers de `node_modules/` (racine) **et** `e2e/node_modules/` **et**
`e2e/test-results/*.zip` — confirmant que ces trois arborescences sont **actuellement
suivies par Git** (`git ls-files` : 5215 + 186 + 186 fichiers respectivement), sans
aucune règle `.gitignore` les couvrant. C'est une dette de dépôt réelle et permanente
(chaque `git clone` futur embarque ces ~530 Mo de dépendances/artefacts de test), même
si son impact sur l'espace disque *local actuel* est marginal par rapport aux venv/
ai_models (le contenu est déjà présent sur disque de toute façon, tracké ou non).

## 13. Suppression probablement sûre

*(Proposition uniquement — rien supprimé. Nécessite une mission
`REPO-LARGE-FILES-SAFE-CLEANUP-1` distincte avec validation explicite.)*

| Élément | Taille | Justification |
|---|---|---|
| `.vibecode-backup/` | 17 Mo | Outillage d'un agent IA tiers ("VibeCode"), sans rapport avec Digital Crown, aucune référence dans le code ou les scripts |
| `build/DigitalCrown/` | 253 Mo | Artefact intermédiaire PyInstaller du même build stale (07/07/2026) que `dist_cabinet/` déjà supprimé avec l'accord du CTO — même nature, même date |
| `.pytest_cache/`, `__pycache__/` (tous) | < 1 Mo cumulé | Caches Python standards, régénérés automatiquement |
| `frontend/dist-rehearsal/` | 4,36 Mo | Recréable via `npm run build:rehearsal`, ne sert rien en continu |
| `scratch/` | 31 Mo | Scripts de debug ponctuels non référencés (`fix_paths.py`, `check_db_schema.py`, etc.), déjà `.gitignore`d — à confirmer qu'aucun n'est encore utilisé avant suppression |

**Sous-total : ~305 Mo** — modeste par rapport au besoin (10 Go visé), mais sans risque
réel.

## 14. Suppression conditionnelle

| Élément | Taille | Condition requise avant suppression |
|---|---|---|
| `.venv312/` | 2,74 Go | Confirmer que `run_rehearsal_backend.ps1` peut utiliser `venv/` à la place, ou que le rehearsal n'est plus nécessaire sous cette forme |
| `node_modules/` + `e2e/node_modules/` + `e2e/test-results/` (untrack Git) | 100 Mo sur disque, ~530 Mo dans l'historique Git | Ajouter les règles `.gitignore` manquantes, `git rm -r --cached` (ne réécrit pas l'historique, arrête juste le suivi futur) — **n'allège pas l'historique existant**, seulement la croissance future |
| `backend/ai_models/cephld_cca/model/*.pth` (checkpoints redondants) | ~500 Mo | Identifier précisément quel(s) fichier(s) le code charge réellement avant de supprimer les autres epochs |
| `backend/ai_models/best.pt` + `best.onnx` + `panoramic_model.pt` | ~709 Mo | Confirmer qu'aucun ne sert de source de re-génération future du modèle actif avant suppression |
| `backend/ai_models/CLdetection2023-master/` | 20,1 Mo | Confirmer doublon exact de `CL-Detection2023/` par hash avant de choisir lequel garder |
| `backend/ai_models/dentex_repo/.git/` (uniquement le `.git` imbriqué, pas le reste du dossier) | 65 Mo | Confirmer que le reste de `dentex_repo/` est toujours nécessaire ; si oui, seul le `.git/` imbriqué peut être retiré sans perte fonctionnelle |
| `backend/static/` (tout ou partie) | 439 Mo | **Voir le constat prioritaire en tête de document — nécessite sa propre mission d'audit avant toute décision** |

**Sous-total espace récupérable conditionnel : ~2,0-4,0 Go** selon les décisions.

## 15. Éléments protégés (ne jamais toucher)

- `C:\Users\lenovo\DigitalCrown-Runtime\` (releases actives, backup-releases, backups
  planifiés) — hors périmètre du dépôt, non touché
- `%APPDATA%\DigitalCrown\media\` — médias patients réels
- `digitalcrown_db`, `clinical_vault.db`
- `venv/` — utilisé activement par `DigitalCrown_DailyBackup_v2` et le backend réel
- `frontend/dist/` — servi actuellement par le backend réel
- `backend/backups/` (3 paires DB+médias retenues) — backups manuels réels validés
- `backend/ai_models/panoramic_model.onnx` — modèle actif confirmé par les logs de boot
- Toute donnée dans `backend/static/patients/` tant que son statut n'est pas confirmé

## 16. Espace récupérable estimé

| Catégorie | Estimation |
|---|---|
| Suppression sûre (section 13) | ~305 Mo |
| Suppression conditionnelle, hors `.venv312` (section 14) | ~1,3 Go |
| `.venv312` seul, si confirmé obsolète | 2,74 Go |
| **Total si tout est approuvé** | **~4,3 Go** |
| `backend/static/` si confirmé non nécessaire (constat prioritaire) | +439 Mo supplémentaires |

**Un nettoyage complet et approuvé rapprocherait le disque de l'objectif de 10 Go
libres, mais ne l'atteindrait probablement pas seul** — à combiner avec la politique
de rétention déjà en place sur les backups planifiés (déjà limitée par
`SCHEDULED_MIN_BACKUPS_TO_KEEP`) et une vigilance continue sur `backend/backups/`
(toujours sans rétention automatique).

## 17. Plan de nettoyage par étapes (proposition, non exécutée)

1. **Trancher le sort de `backend/static/`** (mission dédiée, priorité absolue — voir
   constat en tête de document)
2. Confirmer par hash le statut de `best.onnx` vs `panoramic_model.onnx` vs
   `static/models/panoramic_model.onnx`, et de `CL-Detection2023` vs
   `CLdetection2023-master`
3. Identifier précisément le(s) checkpoint(s) `.pth` réellement chargé(s) par
   `vision_service.py`/`cephld_cca`
4. Confirmer avec le CTO si `.venv312` peut être supprimé (dépend de
   `run_rehearsal_backend.ps1`)
5. Une fois ces vérifications faites : mission `REPO-LARGE-FILES-SAFE-CLEANUP-1`,
   strictement scopée aux éléments explicitement approuvés, avec sauvegarde préalable
   de tout élément ambigu avant suppression définitive
6. Séparément : ajouter les règles `.gitignore` manquantes (`node_modules/` racine,
   `e2e/node_modules/`, `e2e/test-results/`) et `git rm -r --cached` pour arrêter la
   croissance future du dépôt — n'allège pas l'historique déjà existant (nécessiterait
   une réécriture d'historique, explicitement hors périmètre de toute mission jusqu'à
   nouvel ordre)
