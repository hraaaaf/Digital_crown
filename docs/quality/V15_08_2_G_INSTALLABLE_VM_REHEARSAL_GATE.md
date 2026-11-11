# Digital Crown — LOT08.2-G — Gate d'éligibilité pour une recette Windows INSTALLABLE_CERTIFIED

## Décision, périmètre et vérité du 10/11/2026

**Goal** : préparer une recette Windows isolée sur un véritable `INSTALLABLE_CERTIFIED`, avec SQLCipher et restauration contrôlée, sans confondre une CI verte et l'autorisation d'installation. Le GO donné concerne la préparation et les FUE synthétiques ; il ne permet ni merge implicite, ni activation d'un cabinet, ni accès aux patients.

**État inventorié** : `master = bb3c92b9b8c7a56ecd5f60bf9c1d52c578f2f3a4`. La liste GitHub Releases était vide lors du contrôle, et la liste des exécutions `workflow_dispatch` ne contenait pas de `Cabinet Certified Release` émis pour ce master. Le dernier `CODE_CERTIFIED` réussi retrouvé est [run #40598411922](https://github.com/hraaaaf/Digital_crown/actions/runs/40598411922), source **historique** `98f0199dde54123d1caf3b41443c47a000c3b39f`, artefact `code-certified-dc-cabinet-98f0199dde54-run40598411922` (ID 12778323883, ZIP SHA256 `72bfc5fd9aa4505ceb5d02d8e31058784723481ec487e6c4b00bd1b2298706f1`). **Il ne correspond pas au master courant et n'est PAS installable.** Le succès du `Cabinet Upgrade PostgreSQL Certification` [#42851885842](https://github.com/hraaaaf/Digital_crown/actions/runs/42851885842) sur le master actuel ne fabrique ni `CODE_CERTIFIED`, ni `INSTALLABLE_CERTIFIED`.

## GATE 0 — Fail-closed avant toute VM

1. Obtenir de **`.github/workflows/cabinet-release-certification.yml`** lancé sur **`master`** un `CODE_CERTIFIED` dont le contenu, l'attestation GitHub/Sigstore et le SHA sont exactement ceux du master courant. Le connecteur disponible permet de contrôler GitHub en lecture, mais ne permet pas de déclencher ce workflow. Ne pas simuler une certification.
2. Sur le poste qui détient les modèles/assets autorisés, émettre le bundle runtime en vérifiant hashes, taille, registre scientifique et SHA identique au CODE. Aucun téléchargement non approuvé, aucune copie de médias patients.
3. Composer par `backend/scripts/create_release.ps1` uniquement après vérification de la provenance cryptographique code et des assets. La composition est distincte d'un lancement. Ne jamais utiliser d'artefact CODE seul, d'un HEAD PR ou d'un EXE ad hoc comme installable.
4. **Lire** la release candidate via `python -m scripts.quality.lot08_2_g_installable_gate --expected-master-sha <SHA40> --candidate-dir <DOSSIER_RELEASE>`. Le gate utilise le vérificateur canonique `verify_installable_release_directory` et exige exact SHA master. Sortie `ELIGIBLE_FOR_ISOLATED_REHEARSAL_ONLY` signifie **pré-éligible à une recette** et ne vaut pas GO d'installation, de clinique ni de production. Aucune release disponible = `BLOCKED_NO_INSTALLABLE_GO`, code de sortie 3, aucune activation.
5. Après une **nouvelle gate humaine** autorisant spécifiquement l'installation en VM jetable, créer un profil isolé et faux sans cabinet réel, vérifier l'exécutable installé, la chaîne de certificats/manifestes embarqués, la sélection de profil, les permissions NTFS, SQLCipher vrai (PRAGMA cipher_version, mauvaise clé refusée) et le restart/rollback sur copie privée. En l'absence de toute preuve obligatoire : STOP.

## Preuve SQLCipher LAB distincte (ne débloque jamais GATE 0)

Le workflow `v15-08-2-g-installable-vm-readiness-fue.yml` teste un vrai driver `sqlcipher3` Linux sur des bases **créées de zéro**, sans Patient ni cabinets, avec trois DB chiffrées, mauvaise clé et lecture SQLite standard refusées, copie à froid vers répertoire neuf, divergence d'epochs, fichier altéré et overwrite refusés. Il réutilise en plus l'oracle existant `scripts/ci/cb03_g7_real_sqlcipher_sigkill.py` pour **SIGKILL avant et après COMMIT** d'une transaction SQLCipher synthétique. Ces preuves portent sur les **primitives SQLCipher/processus**, pas sur le logiciel réellement installé, ni sur une transaction atomique des trois DB en cas de panne.

Le workflow Linux/Windows vérifie également qu'un faux manifest `INSTALLABLE_CERTIFIED`, un `CODE_CERTIFIED` ancien ou une absence de répertoire n'autorise rien. Il n'y a volontairement **pas de téléchargement, build, exécution d'installateur, migration, service, accès réseau cabinet, lecture de données cliniques ou déploiement**.

## Critères de sortie et risques non levés

- **Succès borné** : run exact HEAD, diff strict des cinq fichiers, tests négatifs et SQLCipher authentique passés, artefacts JUnit/JSON sans DB, clés, médias, noms de comptes ou données patient.
- **Bloqué aujourd'hui** : `CODE_CERTIFIED` de ce master absent des exécutions observées, assets certifiés synchronisés non démontrés, aucune release `INSTALLABLE_CERTIFIED` présentée. Donc **aucune VM d'installation réelle lancée**.
- **Inconnu/non autorisé** : schéma clinique SQLCipher réel, restauration DB+WAL+médias, snapshots multi-store atomiques après crash, politique d'activation réelle, reboot, profil Windows installé, RPO/RTO mesurés, QR clinique et LOT09/10. Aucun `CODE_CERTIFIED`, `INSTALLABLE_GO` ni `INSTALLABLE_CERTIFIED` ne sera attribué par ce lot.

**Next exact** : produire et authentifier les deux artefacts exact SHA (`CODE_CERTIFIED` de master + assets runtime), préparer le binaire certifié, obtenir GO spécifique pour exécuter sa recette **en VM entièrement isolée**, puis seulement tester l'installation/rétablissement des vraies contraintes de l'application. Maintenir le projet local-first et **NO_INSTALLABLE_GO** jusqu'aux preuves complètes.
