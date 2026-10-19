# Digital Crown — LOT05.7-J — Fail-closed restauration et génération FAKE

**Périmètre** : PR Draft empilée sur LOT05.7-I [#975](https://github.com/hraaaaf/Digital_crown/pull/975), HEAD de départ `fbde55eda867be64a502889a3836465f50596735`. Ce lot modifie la politique effective de refus de `GuidedRestoreService` et `GuidedRestoreWorker` mais **ne fournit PAS un moteur de restauration clinique certifié**. Les opérations de migration/import et le LOT10 terrain restent distincts.

## Mesures actives (fail closed)

1. `GuidedRestoreService._assert_owner` refuse `None`, les propriétaires absents, booléens, chaînes, nombres non positifs et propriétaires différents. Un `owner_id` numérique identique reste une vérification de cohérence et non une preuve JWT→worker.
2. `GuidedRestoreService.request_apply` utilise le veto inconditionnel `require_clinical_apply` **avant** l'écriture d'un état `scheduled`, tout lancement de processus ou toute terminaison du serveur. Même `sys.frozen=True`, `ENVIRONMENT=cabinet` et confirmation `RESTAURER` ne déverrouillent rien.
3. `GuidedRestoreWorker.run` oppose le même veto à l'entrée, **avant** consultation du job, secours DB, remplacement, média, coffre, kill/restart. Un exécutable lancé directement avec `--guided-restore-worker` n'obtient aucun droit supplémentaire.
4. L'API renvoie un conflit explicite (HTTP 409 via `RuntimeError`) lors de la tentative d'activation ; la restauration guidée réelle est délibérément suspendue en attendant une véritable autorité SCM/Service SID/ACL et un protocole crash-safe validé. Préflight, lecture et préparation conservent leurs contrats existants, sous réserve du contrôle strict de propriétaire pour la préparation.

## Prototype vérifiable FAKE uniquement

`legacy_migration_safe_restore_lab_v15.py` accepte exclusivement un dossier temporaire dont le nom commence par `lot05j_fake_`, un principal et propriétaire attendus strictement entiers concordants (simulations, PAS identité Windows), une connexion `sqlite3` existante liée à `inputs/clinical.db`, un coffre `license_fake.bin` et deux médias `.fake`. L'API native SQLite `Connection.backup` réalise un snapshot logique incluant le dernier COMMIT WAL pendant qu'une connexion source reste ouverte ; les fichiers du snapshot sont copiés, synchronisés, mesurés SHA-256/longueur et vérifiés en intégrité SQLite. Des générations immuables sont créées sous un nom unique. Un `CURRENT.json` est publié **après** vérification complète, par remplacement d'un pointeur de test seulement. L'ancienne génération persiste. Un clone distinct est autorisé seulement vers une destination neuve `isolated-recovery`.

Les interruptions de test `after_db`, `after_media`, `before_publish`, `after_generation` laissent l'ancien pointeur intact ; aucune API du prototype ne supprime ou ne remplace `clinical_vault.db`, un fichier actif réel ou les médias du cabinet. Ces garanties ne s'appliquent qu'à la structure FAKE contrôlée par le test. `Path.resolve` et les contrôles de symlinks ne prouvent PAS les reparse points NTFS et leur TOCTOU. Les hashes issus des mêmes acteurs de test ne prouvent PAS une provenance de sauvegarde. Le pointeur n'est pas signé par une autorité indépendante. Un `os.replace` sans flush parent portable Windows ne garantit PAS la résistance à une perte d'alimentation. SQLite standard n'est PAS SQLCipher et des générations de copies ne constituent PAS une transaction réelle DB/WAL/médias/coffre.

## Gates et preuves exigées

- Nouveau workflow J obligatoire : Linux + Windows, Python 3.12, **15 tests J** sans skip, et **21 tests hérités I** avec véritable SQLCipher et JWT sans skip ; exécuter aussi les tests historiques `test_guided_restore.py` qui doivent confirmer le refus avant exécution. Contrôler CI Scope et diff exact depuis le HEAD I.
- A : revue adversariale intégrité/crash et faux atomicité. B : autorité Windows, JWT/SCM, ACL, chemins hostiles et fail-open ; distinctes perspectives internes. Revue de confirmation sur **même SHA**, pas d'affirmation d'indépendance externe.
- Les défauts actifs antérieurs `_rescue_database` copie DB/WAL séparément, `_restore_database_from_rescue` supprime la cible avant copie et `_apply_database` remplace toujours dangereusement : ils restent **inaccessibles via run/request_apply certifiés de ce lot**, MAIS les helpers restent présents et ne doivent jamais être appelés par un autre chemin avant un audit d'inventaire complet.
- Aucun service SCM/Session 0/Service SID dédié n'est installé ou testé ; pas de vrai SQLCipher dans le prototype J (les tests hérités I vérifient seulement les anciens helpers), pas de backup/restore clinique, RPO/RTO, intégrité multi-composants effective, preuve USB/terrain, ni approbation humaine d'activation.

**Statut** : 05.7-J implémentation à qualifier seulement par preuves CI exact HEAD ; ne jamais appeler CONVERGED avant les gates, toujours clinique **NO-GO**. Aucun merge, Vercel, ni donnée patient réelle.

**Roadmap** : LOT05 / SQL Migration Wizard → A-I convergés labo → J fail-closed actif + génération fictive, convergence à vérifier → J suite autorité réelle SCM et récupération multicomposants → certification clinique reste NO-GO → LOT10 terrain séparé.
