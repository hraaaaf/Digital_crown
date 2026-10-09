# Facad 3.14 — D3 isolation des stockages : audit statique parallèle et gate non-clinique

**Date :** 2026-10-09. **Statut : OPEN / BLOCKER, aucune isolation certifiée.**
**Branche :** \`feat/cephalo-facad-direct-parity-runtime-probe\`. **Périmètre :** instrumentation/audit uniquement ; aucun acte sur dossier clinique, aucun Save/Load patient, aucun merge ou Vercel.
**Contexte :** travail indépendant du run [Ricketts #37865416188](https://github.com/hraaaaf/Digital_crown/actions/runs/37865416188), dont le SHA testé \`8eadb304aa7a147d0a889426658e0e272902756a\` précède ces travaux. **Ne pas attribuer cet audit au run.**

## 1. Observations provenant du code — et non de la machine Windows

1. Le workflow \`.github/workflows/facad-314-quick-demo-bootstrap.yml\` copie le dossier \`release/Examples\` au complet dans \`d3-app-copy\` et lance Facad sur \`d3-app-copy/Robert-2.0.fcd\`, puis compare **uniquement les empreintes du fichier \`Robert-2.0.fcd\`** source et copie. La copie initiale de tous les siblings n'est pas suivie d'un contrôle exhaustif de leur intégrité. **Faille de couverture**, pas preuve de modification.
2. \`scripts/facad_314_d3_sandbox_preflight.ps1\` crée une autre copie jetable du seul fichier \`.fcd\`, vérifie ses empreintes, puis émet explicitement \`D3_TEST_EXECUTION=BLOCKED_PENDING_APPLICATION_LEVEL_ISOLATION\`. Ce script **ne collecte ni modifications des ressources auxiliaires ni écritures sur les stockages communs**.
3. Le workflow journalise \`SHARED_APP_STORAGE_ISOLATION=UNVERIFIED\` et \`CLINICAL_EDIT_ALLOWED=false\` ; c'est conforme à son niveau de preuve, mais pas une certification D3. L'absence de dérive du \`.fcd\` n'exclut pas des écritures dans les dossiers partagés, réglages, registres, caches, index et bases locales.
4. Aucun dossier patient réel n'est nécessaire. Seul l'exemple officiel Robert est admissible pour ce benchmark ; aucune exploration de licence ou de secret ne fait partie de ce travail.

## 2. Livrable autonome vérifié — validateur de manifests hors ligne

- \`scripts/facad_314_d3_snapshot_diff_gate.py\` : compare des instantanés JSON BEFORE/AFTER **fournis**, ne capture **pas** le système, ne lance pas Facad et **n'autorise jamais l'édition clinique**.
- \`scripts/test_facad_314_d3_snapshot_diff_gate.py\` : **13 tests unitaires synthétiques passés localement**, y compris création/modification/suppression, sibling officiel, dérive de registre, périmètres absents, capture incomplète, root/session non identiques, faux hash, champs additionnels et codes CLI. **Non exécutés sur un runner Windows**, et ne prouvent aucune isolation réelle.
- Schema \`facad314_d3_snapshot_v1\` ; neuf scopes obligatoires : \`official_examples_tree\`, \`disposable_examples_tree\`, \`facad_install_tree\`, \`facad_appdata_roaming\`, \`facad_appdata_local\`, \`facad_programdata\`, \`facad_documents\`, \`facad_registry_hkcu\`, \`facad_registry_hklm\`.
- Chaque scope doit inclure : \`kind\` (filetree ou registry), \`root_fingerprint\` (SHA256 de l'identité normalisée du même chemin/racine BEFORE et AFTER), \`capture_ok=true\`, \`present\` (booléen) et \`entries\` (mapping clé relative => \`sha256\` et \`size\`). Les snapshots ont un \`session_id\` commun et le champ \`phase\` distinct.
- Aucun nom de fichier ni valeur de registre brute dans les rapports : seulement le scope et le SHA256 de la clé relative modifiée. **Attention : les snapshots d'entrée peuvent contenir des noms ; ne publier aucune entrée qui ne concerne pas le démonstrateur autorisé.** Les exports de registre contenant clés de licence ou données de santé sont interdits.

\`\`\`bash
python scripts/facad_314_d3_snapshot_diff_gate.py --before before.json --after after.json --output verdict.json
python -m unittest scripts/test_facad_314_d3_snapshot_diff_gate.py -v
\`\`\`

**Codes de sortie intentionnellement non verts :**
- \`1\` = \`BLOCKED_OBSERVED_STORAGE_DRIFT\` ; au moins un fichier/registre surveillé a changé ;
- \`2\` = \`BLOCKED_INVALID_OR_INCOMPLETE_EVIDENCE\` ; données invalides, périmètre manquant, mauvaise identité ou capture incomplète ;
- \`3\` = \`INCONCLUSIVE_NO_OBSERVED_STORAGE_DRIFT\` ; aucune dérive observée dans les champs fournis, **mais couverture causale non démontrée**.

**Il n'existe volontairement aucun code 0 de validation D3.** Le JSON produit comporte toujours \`d3_isolation_verified=false\` et \`clinical_edit_allowed=false\`. Une CI ne doit jamais transformer un résultat \`3\` en succès d'isolation.

## 3. P0 — Ce qu'il manque pour ouvrir le vrai gate D3

**REQUIRED, non réalisé :** sur un runner officiel neuf et sur le seul exemple Robert, capturer les périmètres réels BEFORE et AFTER, leur identité canonique et les erreurs d'accès de façon lisible, avec preuve temporelle et état de la session Facad. Traiter séparément une première initialisation de Facad (écritures de configuration possibles) et une session d'observation. Recenser les chemins effectivement ouverts/écrits par **le processus Facad et ses enfants** — sans supposer qu'une liste de neuf répertoires couvre tout le système. Examiner aussi les fichiers siblings de \`Examples\` et toute sauvegarde automatique, bases ou chemins documentaires. Comparer les manifests et vérifier manuellement l'attribution des éventuelles écritures.

**REQUIRED, non réalisé :** démontrer explicitement quelle racine serait confinée à la copie jetable, que l'original et ses dépendances demeurent intacts, que les écritures communes sont absentes ou isolées, que toute interaction peut être restaurée sans effet de bord et qu'une revue clinique humaine approuve la première future mutation. Aucun test d'édition ne doit être lancé avant ces conditions.

**EXPERIMENTAL, sans gate produit :** script futur Windows **lecture seule** pour générer les manifests et les captures redigées. L'absence d'une nouvelle détection n'est pas la preuve de l'absence de stockage caché ; ce validateur n'attribue pas les écritures à un processus et n'atteste pas la fidélité du collecteur. Pas de capture brute de registres ou données patient ; ne pas étendre à d'autres profils.

**HORS SCOPE :** Vercel, merge, import patient réel, licence, sauvegarde clinique, export, interprétation des normes, parité D5.

## 4. Double revue adversariale INTERNE (pas deux reviewers indépendants)

**Perspective A — preuves / fail-open :** risque BLOCKER si un snapshot incomplet avec \`capture_ok=true\` est pris comme preuve totale, si le collecteur n'a pas de provenance instrumentée, si le code 3 devient vert dans CI ou si la racine change entre les phases. Mitigation intégrée : ensembles de scopes exacts, hashes/root/session obligatoires, code 3 non vert, flags cliniques constants à \`false\`. Reste OUVERT : provenance et complétude du collecteur non démontrées.

**Perspective B — sécurité clinique / effets latéraux :** risque BLOCKER si une vue \`read-only\` modifie des préférences, MRU, index, fichiers image liés, base locale ou dossiers partagés ; l'empreinte du seul \`.fcd\` ne couvre rien de cela. Mitigation : aucune mutation clinique, monitoring projeté des siblings + registres + données communes, runner neuf. Reste OUVERT : chemins réellement touchés/isolement applicatif non prouvés.

**Verdict : OUVERT, non convergé.** Il s'agit d'un contrat de détectabilité **et non** d'une certification d'isolation. Le run D1C parallèle demeure indépendant de ces commits.

**Next :** collecteur Windows read-only avec provenance et redaction éprouvées, CI expérimentale distincte du run d'inventaire, review des artefacts, puis décision sur D3 sans jamais substituer un vert de test unitaire à un gate de sécurité.
