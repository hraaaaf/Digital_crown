# Digital Crown — LOT05.7-F : laboratoire fail-closed tenant et publication sans écrasement

**Mission immuable 05.7-F, test-only.** Suite stricte à 05.7-E (#967) et aux PR Draft #963→#966. La PR 05.7-F ne doit modifier **aucune** API, service, Alembic, modèle, base Cabinet, écran, appareil mobile ni procédure de déploiement. Aucun import ou restauration sur une installation réelle n'est autorisé.

## Différence avec 05.7-E

05.7-E prouve une vraie migration-opérateur `alembic upgrade head` sur une DB **SQLCipher temporaire réellement chiffrée**, ses vrais modèles ORM, le chemin `BackupService.backup_active_database()` et `BackupService.restore_backup(...verify_sqlcipher=True)`, mais les gardes précédents étaient test-only. 05.7-F ajoute un **contrat négatif indépendant** sur les chemins d'exécution possibles, sans le brancher au runtime.

Le test `backend/tests/test_legacy_sql_057f_failclosed_tenant_publish_lab.py` réutilise **le fixture réel** du 05.7-E avec des données **inventées seulement** : deux propriétaires fictifs, six patients, douze rendez-vous, quatre actes, quatre paiements, deux métadonnées de documents, aucun octet médical réel. Il exécute des requêtes statiques `SELECT` sur les **véritables colonnes Alembic head `neo000000031`** et exige deux identités de propriétaires fictives explicites. Toute prétention à une authentification réelle est interdite ; les ID de propriétaires sont uniquement la fixture et ne proviennent pas d'un système d'identité approuvé.

## Sécurité tenant vérifiée, mais non branchée à la production

Les anomalies testées incluent :
- patient rattaché à un utilisateur qui n'est pas le propriétaire racine ;
- rendez-vous attaché à un patient d'un autre cabinet, ou à une ressource d'agenda d'un autre cabinet ;
- acte signé par un praticien d'un autre cabinet (y compris praticien subordonné via `COALESCE(users.employer_id,users.id)`) ;
- paiement lié à un acte d'un autre patient ;
- document uploadé par un utilisateur d'un autre cabinet ;
- revendication propriétaire absente, erronée ou hors périmètre.

Le rendez-vous rapide dont `patient_id IS NULL` reste explicitement autorisé dans le laboratoire lorsqu'il correspond à son propriétaire de cabinet. Les tests d'injection s'effectuent soit dans une transaction de fixture annulée, soit dans une **sauvegarde chiffrée fictive** dont la source est remise à son état original. Le rapport d'erreur ne contient jamais nom ou ligne patient. Ce contrôle reste une **fonction dans backend/tests**, nullement un veto réellement intégré au pipeline, au service Windows ou au module d'import.

Le test de **parité de six familles** (`users`, `patients`, `appointments`, `actes`, `payments`, `document_archives`) exige en outre le même SHA logique que le fixture approuvé. Ce hash est une preuve locale rédigée par la même partie, pas une preuve indépendante de provenance clinique. Les liens non couverts (échéances, autres collections médicales, praticiens multi-organisations, médias physiques) restent explicitement hors certification.

## Publication atomique exclusivement fictive

La nouvelle fonction de test restaure d'abord en **fichier de staging unique dans le même répertoire privé jetable** via la **vraie méthode `BackupService.restore_backup(...verify_sqlcipher=True)`**. Elle vérifie le head Alembic, l'intégrité SQLCipher, `PRAGMA foreign_key_check`, l'empreinte des six familles et les anomalies tenant. **Seulement ensuite** elle publie le fichier fictif par `os.link(staged, target, follow_symlinks=False)`. La création de lien dur vers un nom de destination déjà occupé est atomiquement refusée (`EEXIST`) : aucun appel à `os.replace(target)`, ni `shutil.copy` de repli. Si les liens durs ne sont pas supportés par le filesystem du laboratoire, l'opération refuse de publier (fail-closed). Le fichier de staging est supprimé, la destination autorisée étant un second lien physique sur le même système de fichiers.

Tests négatifs : destination déjà présente, **collision créée entre vérification et création du lien**, indisponibilité volontaire de `os.link`, backup Fernet altéré, source ou cible hors du dossier fictif, et rejeu sans écrasement ; tests positifs : schéma réel, sauvegarde restaurée authentique, rendez-vous autonome et refus d'incohérences patient/cabinet/praticien/paiement/document.

**LIMITATION CRITIQUE** : la publication exclusive est un **prototype de laboratoire**, pas une restauration de production éprouvée sur NTFS DACL/reparse, système de fichiers partagé, concurrents malveillants, liens durs déjà existants, journaux WAL/SHM, durabilité `fsync`, sauvegarde cohérente de tous les médias ou plan de rescue/rollback. Le `BackupService.restore_backup` réel **peut toujours écraser un fichier cible** lorsqu'il est invoqué sans ce prototype ; aucun blocage n'a été installé dans le service de production. Il faut explicitement un vrai contrat d'autorisation humaine et de propriétaire, un environnement de restauration fermé, des preuves Windows/SQLCipher de panne et un mécanisme de rollback validé **avant toute activation clinique**.

## Gates et état

Le workflow `.github/workflows/v15-05-7-f-tenant-noreplace-lab.yml` exige Linux + Windows, Python 3.12, SQLCipher natif, `alembic upgrade head` authentique depuis le fixture E, **14 tests sans skip au même HEAD**, plus `CI Scope Gate`. Le trigger expérimental M6-I et le gate UI Human automatique restent hors périmètre car aucun écran (desktop ou mobile) n'est modifié. Deux perspectives adversariales internes indépendantes dans leur axe, mais **pas externes**, sont exigées après tests, puis confirmation du SHA exact.

**Décision tant que la CI n'est pas démontrée : OPEN / NON CONVERGED.** Même si elle devient verte : convergence **LAB FAKE ONLY**, **GO clinique réel toujours NO-GO**. Aucune fusion ni déploiement. Réserves dans `techdoubt.md`.
