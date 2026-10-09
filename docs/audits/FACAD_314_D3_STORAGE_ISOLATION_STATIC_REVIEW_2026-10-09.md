# Facad 3.14 — D3 isolation des stockages : audit statique parallèle et gate non-clinique

**Date :** 2026-10-09. **Statut : OPEN / BLOCKER, aucune isolation certifiée.**
**Branche :** `feat/cephalo-facad-direct-parity-runtime-probe`. **Périmètre :** instrumentation/audit uniquement ; aucun acte sur dossier clinique, aucun Save/Load patient, aucun merge ou Vercel.
**Contexte :** travail indépendant du run [Ricketts #37865416188](https://github.com/hraaaaf/Digital_crown/actions/runs/37865416188), dont le SHA testé `8eadb304aa7a147d0a889426658e0e272902756a` précède ces travaux. **Ne pas attribuer cet audit au run.**

## 1. Observations provenant du code — et non de la machine Windows

1. Le workflow `.github/workflows/facad-314-quick-demo-bootstrap.yml` copie le dossier `release/Examples` au complet dans `d3-app-copy` et lance Facad sur `d3-app-copy/Robert-2.0.fcd`, puis compare **uniquement les empreintes du fichier `Robert-2.0.fcd`** source et copie. La copie initiale de tous les siblings n'est pas suivie d'un contrôle exhaustif de leur intégrité. **Faille de couverture**, pas preuve de modification.
2. `scripts/facad_314_d3_sandbox_preflight.ps1` crée une autre copie jetable du seul fichier `.fcd`, vérifie ses empreintes, puis émet explicitement `D3_TEST_EXECUTION=BLOCKED_PENDING_APPLICATION_LEVEL_ISOLATION`. Ce script **ne collecte ni modifications des ressources auxiliaires ni écritures sur les stockages communs**.
3. Le workflow journalise `SHARED_APP_STORAGE_ISOLATION=UNVERIFIED` et `CLINICAL_EDIT_ALLOWED=false` ; c'est conforme à son niveau de preuve, mais pas une certification D3. L'absence de dérive du `.fcd` n'exclut pas des écritures dans les dossiers partagés, réglages, registres, caches, index et bases locales.
4. Aucun dossier patient réel n'est nécessaire. Seul l'exemple officiel Robert est admissible pour ce benchmark ; aucune exploration de licence ou de secret ne fait partie de ce travail.

## 2. Livrable autonome vérifié — validateur de manifests hors ligne

- `scripts/facad_314_d3_snapshot_diff_gate.py` : compare des instantanés JSON BEFORE/AFTER **fournis**, ne capture **pas** le système, ne lance pas Facad et **n'autorise jamais l'édition clinique**.
- `scripts/test_facad_314_d3_snapshot_diff_gate.py` : **13 tests unitaires synthétiques passés localement**, y compris création/modification/suppression, sibling officiel, dérive de registre, périmètres absents, capture incomplète, root/session non identiques, faux hash, champs additionnels et codes CLI. **Non exécutés sur un runner Windows**, et ne prouvent aucune isolation réelle.
- Schema `facad314_d3_snapshot_v1` ; neuf scopes obligatoires : `official_examples_tree`, `disposable_examples_tree`, `facad_install_tree`, `facad_appdata_roaming`, `facad_appdata_local`, `facad_programdata`, `facad_documents`, `facad_registry_hkcu`, `facad_registry_hklm`.
- Chaque scope doit inclure : `kind` (filetree ou registry), `root_fingerprint` (SHA256 de l'identité normalisée du même chemin/racine BEFORE et AFTER), `capture_ok=true`, `present` (booléen) et `entries` (mapping clé relative => `sha256` et `size`). Les snapshots ont un `session_id` commun et le champ `phase` distinct.
- Aucun nom de fichier ni valeur de registre brute dans les rapports : seulement le scope et le SHA256 de la clé relative modifiée. **Attention : les snapshots d'entrée peuvent contenir des noms ; ne publier aucune entrée qui ne concerne pas le démonstrateur autorisé.** Les exports de registre contenant clés de licence ou données de santé sont interdits.

```bash
python scripts/facad_314_d3_snapshot_diff_gate.py --before before.json --after after.json --output verdict.json
python -m unittest scripts/test_facad_314_d3_snapshot_diff_gate.py -v
```

**Codes de sortie intentionnellement non verts :**
- `1` = `BLOCKED_OBSERVED_STORAGE_DRIFT` ; au moins un fichier/registre surveillé a changé ;
- `2` = `BLOCKED_INVALID_OR_INCOMPLETE_EVIDENCE` ; données invalides, périmètre manquant, mauvaise identité ou capture incomplète ;
- `3` = `INCONCLUSIVE_NO_OBSERVED_STORAGE_DRIFT` ; aucune dérive observée dans les champs fournis, **mais couverture causale non démontrée**.

**Il n'existe volontairement aucun code 0 de validation D3.** Le JSON produit comporte toujours `d3_isolation_verified=false` et `clinical_edit_allowed=false`. Une CI ne doit jamais transformer un résultat `3` en succès d'isolation.

## 3. P0 — Ce qu'il manque pour ouvrir le vrai gate D3

**REQUIRED, non réalisé :** sur un runner officiel neuf et sur le seul exemple Robert, capturer les périmètres réels BEFORE et AFTER, leur identité canonique et les erreurs d'accès de façon lisible, avec preuve temporelle et état de la session Facad. Traiter séparément une première initialisation de Facad (écritures de configuration possibles) et une session d'observation. Recenser les chemins effectivement ouverts/écrits par **le processus Facad et ses enfants** — sans supposer qu'une liste de neuf répertoires couvre tout le système. Examiner aussi les fichiers siblings de `Examples` et toute sauvegarde automatique, bases ou chemins documentaires. Comparer les manifests et vérifier manuellement l'attribution des éventuelles écritures.

**REQUIRED, non réalisé :** démontrer explicitement quelle racine serait confinée à la copie jetable, que l'original et ses dépendances demeurent intacts, que les écritures communes sont absentes ou isolées, que toute interaction peut être restaurée sans effet de bord et qu'une revue clinique humaine approuve la première future mutation. Aucun test d'édition ne doit être lancé avant ces conditions.

**EXPERIMENTAL, sans gate produit :** script futur Windows **lecture seule** pour générer les manifests et les captures redigées. L'absence d'une nouvelle détection n'est pas la preuve de l'absence de stockage caché ; ce validateur n'attribue pas les écritures à un processus et n'atteste pas la fidélité du collecteur. Pas de capture brute de registres ou données patient ; ne pas étendre à d'autres profils.

**HORS SCOPE :** Vercel, merge, import patient réel, licence, sauvegarde clinique, export, interprétation des normes, parité D5.

## 4. Double revue adversariale INTERNE (pas deux reviewers indépendants)

**Perspective A — preuves / fail-open :** risque BLOCKER si un snapshot incomplet avec `capture_ok=true` est pris comme preuve totale, si le collecteur n'a pas de provenance instrumentée, si le code 3 devient vert dans CI ou si la racine change entre les phases. Mitigation intégrée : ensembles de scopes exacts, hashes/root/session obligatoires, code 3 non vert, flags cliniques constants à `false`. Reste OUVERT : provenance et complétude du collecteur non démontrées.

**Perspective B — sécurité clinique / effets latéraux :** risque BLOCKER si une vue `read-only` modifie des préférences, MRU, index, fichiers image liés, base locale ou dossiers partagés ; l'empreinte du seul `.fcd` ne couvre rien de cela. Mitigation : aucune mutation clinique, monitoring projeté des siblings + registres + données communes, runner neuf. Reste OUVERT : chemins réellement touchés/isolement applicatif non prouvés.

**Verdict : OUVERT, non convergé.** Il s'agit d'un contrat de détectabilité **et non** d'une certification d'isolation. Le run D1C parallèle demeure indépendant de ces commits.

**Next :** collecteur Windows read-only avec provenance et redaction éprouvées, CI expérimentale distincte du run d'inventaire, review des artefacts, puis décision sur D3 sans jamais substituer un vert de test unitaire à un gate de sécurité.


## 5. Lot Windows lecture seule indépendant, démarré (2026-10-09)

**Source contrôlée** : nouveau collecteur `scripts/facad_314_d3_windows_snapshot.ps1`, commit [1e924f94](https://github.com/hraaaaf/Digital_crown/commit/1e924f9401587f9ec893eeaf24e3266e1c7bc7d5). Workflow autonome `.github/workflows/facad-314-d3-windows-storage-observation.yml`, commit [74124ed4](https://github.com/hraaaaf/Digital_crown/commit/74124ed421647aeb03f480b9fe37362b2ab3b770). **GitHub Actions Windows EXPERIMENTAL** : [run #37866961333](https://github.com/hraaaaf/Digital_crown/actions/runs/37866961333), sur SHA `74124ed421647aeb03f480b9fe37362b2ab3b770`, **in_progress au premier contrôle ; aucune preuve exécutée de snapshot ni artefact encore validée**. Le workflow a été dérivé des deux étapes strictes de téléchargement de l'installateur officiel et d'installation Quick Demo précédemment testées, sans le pilote D1C ni ses interactions patient. Il lance **uniquement** `Facad.exe` sur une copie fraîche de `Examples/Robert-2.0.fcd`, observe le démarrage puis termine le processus sans clic UI/Save/Load/planification.

**Avant/après comparés** : neuf scopes explicites du contrat `facad314_d3_snapshot_v1`, mêmes racines et `session_id`. Deux arbres `Examples` hashés en SHA256 de contenu ; autres périmètres Facad d'installation, AppData roaming/local, ProgramData et Documents **métadonnées seulement** (taille/date modification), pour éviter de lire secrets/licences/configurations ou données médicales potentielles. Registre HKCU/HKLM : **structure des clés seulement**, jamais `Get-ItemProperty`, jamais lecture ni émission de valeurs. Dans les manifests, **aucun chemin brut** : noms relatifs hachés. Tout refus d'accès, plafond d'énumération ou fichier potentiellement sensible sous les racines surveillées marque `capture_ok=false` (fail-closed). Artefact conservé 14 jours.

**Limites P0 qui subsistent même si run vert** : couverture limitée aux chemins Facad prédéfinis et clés Facad/Citodent ; aucune découverte réelle des chemins écrits par le processus ou ses descendants ; aucune garantie concernant dossiers vendor alternatifs, clés registre atypiques, bases externes ou stockage invisible ; les valeurs de registre ne sont pas observées ; les changements sur fichiers hors exemple, à taille et date identiques, peuvent échapper au contrôle ; écrire sur cache mémoire ou système, désinstaller/fermer et gérer les processus enfants n'est pas démontré. Même un `INCONCLUSIVE_NO_OBSERVED_STORAGE_DRIFT` n'établit pas l'isolation. **`SHARED_APP_STORAGE_ISOLATION=UNVERIFIED`, `CLINICAL_EDIT_ALLOWED=false`, aucun D3 patient mutation.**

**Interprétation du job** : uniquement **préflight expérimental lecture seule**. Le comparateur a les sorties 1=drift (job rouge), 2=invalide (rouge), 3=inconclusif (le workflow peut être vert si capture correcte, mais *pas* D3 validé). Le statut du run doit être revérifié et le ZIP consulté pour rendre le verdict avant toute suite. **Next** : collecter preuve Windows réelle, rapprocher avec les deux traces de sessions D1C, dresser les écritures possibles restant hors scopes et concevoir une observation process-aware sans secrets.

## 6. Phase D3B — Manufacturer-specific patient store topology counter-audit (2026-10-09)

**Result: MAJOR coverage defect confirmed from official vendor sources; D3 remains BLOCKED.** GitHub version of this section updates an existing research report only; **no real Facad application run** and **no patient/access/license reading** occurred.

### Original Facad 3.14 authority, not an assumption about generic databases

- [Manufacturer **Facad 3.14 Reference Manual**, chapter 2, `Facad Data and Images`](https://www.facad.com/dox/dox314/FacadRefMan.pdf): patient/tracing data are **file/folder based, NOT a relational database**. `Patient Data Root` can be on local PC **or file server**, and the configured `Patient Data Node` holds patient folders and their `.fcd` tracings. The product's `Work List` receives imported images and data via plugin. `C:\Facad\FacadData` / `...\Patients` are **typical example paths, not a verified runner configuration**.
- [Official Facad 3.14 release notes (installation information)](https://www.facad.com/wp/wp-content/uploads/2024/01/FacadReleaseNotes_3.14.pdf): user preferences are in **`%APPDATA%\Ilexis\Facad.settings`**. `Facad.Administrator.settings` sits alongside the actual `Facad.exe`. `license.fcl` (confidential: **NEVER READ OR COPY**) sits in `License` under **Patient Data Root**, not necessarily in the installation folder. The Windows registry is **no longer the application's settings store**, even if observing registry key existence can still be a cautious secondary guard.
- [Vendor technical specifications](https://www.facad.com/wp/technical-specifications/): both standalone and server-shared installations are supported, and the vendor explicitly states **no databases**. [Vendor FAQ](https://www.facad.com/wp/support-faq/) accepts UNC-style server paths and describes configurable access logging; do not capture patient audit logs or actual clinical root names in public artifacts.
- **Acquisition limitation**: manufacturer PDF texts were indexed by public search, but direct web PDF open/screenshot cache missed. These precise claims are based on official vendor-hosted indexed PDF text and independently confirmable vendor HTML, **not a locally inspected original PDF rendering**. No inventing configuration actually in effect on a specific machine.

### Adversarial reconciliation with the *existing*, already-run D3 observer

The existing `scripts/facad_314_d3_windows_snapshot.ps1` enumerates 9 scopes such as `$env:APPDATA\Facad`, `$env:LOCALAPPDATA\Facad`, `$env:ProgramData\Facad`, Windows registry keys and two bundled-example directories. It does **not** identify the actual configured **Patient Data Root**, **Patient Data Node**, **Work List**, **Ilexis\Facad.settings**, administrative settings beside the executable, `License` under the patient root, or any remote UNC root. Consequently, `capture_ok=true` for nine nominated directories — even if no change is reported — is **NOT a complete observation of real Facad data persistence**. It is a genuine missing-source-coverage blocker, **not proof of observed unauthorized writes**.

`scripts/facad_314_d3_process_io_observer.ps1` uses Windows process I/O counters and explicitly outputs `path_attribution_available=false`, `complete_child_process_coverage=false`. Counters do **not locate the files written**; they cannot rule out changes to a configured patient store. No bootstrap demonstration makes this gate green.

The original [GitHub D3 Windows observation run #37866961333](https://github.com/hraaaaf/Digital_crown/actions/runs/37866961333) **FAILED** at **Observe nonclinical startup ...** before collecting a successful completed BEFORE/AFTER verdict: its job log shows `D3_SCOPE_CAPTURE_FAILURE_COUNT=1` at pre-start snapshot, then PowerShell threw **one or more monitoring scopes incomplete**. This is a **capture failure**, not an observed patient write, nor isolation evidence. No retry of that Facad-launching workflow is authorized by this Phase.

**Operational access**: Remote Desktop Commander [device DESKTOP-3MAJEEH] was found **OFFLINE** on Oct 9; no live target-machine path identity, administrator configuration, redirected clinic share or patient-root existence was accessed or verified. A GitHub-hosted ephemeral demo runner does not imply isolation on that machine.

### Research-only fail-closed additions

- `scripts/facad_314_d3_storage_authority_gap_gate.py`: analyzes only **checked-in source text** of collector, process observer and comparator. It compares nine vendor-relevant storage categories with **source-visible coverage**, never reads actual settings, license, registry values, medical files or real paths. Prints category identifiers only (no full patient paths), always reports `d3_isolation_verified=false` / `clinical_edit_allowed=false`.
- `scripts/test_facad_314_d3_storage_authority_gap_gate.py`: 12 synthetic/adversarial tests, including registry not being a substitute for settings, bogus claim of coverage, missing configured roots, Ilexis folder omitted, process counters ≠ path attribution, and **even fabricated complete static coverage must be INCONCLUSIVE**, never `D3=VERIFIED`.
- Existing `.github/workflows/facad-314-d3-snapshot-validator.yml` now runs this source-only guard on **ubuntu-latest** (alongside earlier 13 offline comparator tests), with `FACAD_APPLICATION_LAUNCHED=false` and `SHARED_APP_STORAGE_ISOLATION=UNVERIFIED`. No Windows Facad installer or app process is launched; no patient or protected path accessed. **A green workflow validates only the detector and its negative tests**, not actual D3.

**Adversarial precision:** a registry *write-event monitor* must record only event timing, process association and privacy-safe scope categories; **no registry value reads** or collection of license/patient strings. For Facad 3.14 the registry is not the default preferences store; this extra event channel is precautionary, not a claim that registry content must be inspected. The category label is `REGISTRY_WRITE_EVENT_ATTRIBUTION`, replacing an imprecise value-change wording.

**REQUIRED next before any Facad same-tracing numeric comparison:** evidence from an isolated, authorized environment of *configured* Patient Data Root/Node/Work List location identity (only non-sensitive hashes/categories may enter public reports); the actual user and admin settings locations; local versus UNC targeting and access controls; process-and-descendant **write-path attribution** and full pre/post structural/content-safe snapshots; clear first-run bootstrap effects; rollback and independent clinical approval. Any inaccessible, ambiguous, redacted-but-unverifiable or shared target must produce **BLOCKED**, not a false-green verdict. Do not read `license.fcl`, publish path components or perform test clinical writes.

**GATES unchanged:** `SHARED_APP_STORAGE_ISOLATION=UNVERIFIED`, `FACAD_NUMERICAL_PARITY_CERTIFIED=false`, `CLINICAL_EDIT_ALLOWED=false`, `F01_13_GLOBAL_CLOSED=false`, `SAME_LANDMARK_PARITY_PROTOCOL_EXECUTED=false`. **No merge, deployment, proprietary runtime, patient records, or purchase.**
