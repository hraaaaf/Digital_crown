# Portability & Launcher — roadmap canonique

Dernière mise à jour vérifiée : 2026-08-23.

## Goal global

Digital Crown doit offrir le même produit local-first sur **Windows et macOS**, avec installation, démarrage, données, restauration, licence, mises à jour et migration de poste maîtrisés, sans créer deux applications divergentes.

## Succès global

- un cœur applicatif commun Windows/macOS ;
- aucune connaissance OS dispersée hors frontière plateforme autorisée ;
- un seul runtime Digital Crown par poste ;
- ouverture de l'UI uniquement après readiness réelle ;
- chemins de données/config/logs natifs à chaque OS ;
- migration cabinet vérifiée DB + médias + config + licence/secrets selon leur contrat ;
- packaging installable et signé sur Windows et macOS ;
- mise à jour avec sauvegarde, validation et rollback ;
- certification E2E sur machines propres et architectures supportées.

## Doctrine d'architecture

- **Un cœur commun**, pas deux forks Windows/macOS.
- Les intégrations spécifiques OS passent par un adapter explicite.
- Le frontend React et le backend FastAPI restent communs.
- La décision de packaging final reste réversible jusqu'au lot P6 ; ne pas maintenir PyInstaller et Tauri comme deux architectures produit concurrentes.
- Aucun déploiement Vercel n'appartient à ce chantier.

---

## P1 — OS abstraction layer — CLOSED ✅

### Goal
Retirer du cœur partagé les branches et primitives Windows/macOS directes nécessaires au runtime actuel.

### Implémentation vérifiée
- `backend/core/platform.py` devient la frontière plateforme ;
- chemins data/config/log/runtime centralisés ;
- macOS utilise `~/Library/Application Support/DigitalCrown` et `~/Library/Logs/DigitalCrown` ;
- `AppPaths` délègue à la frontière plateforme ;
- bootstrap env packagé, écriture atomique privée et ouverture URI centralisés ;
- liveness PID et lancement détaché Guided Restore centralisés ;
- garde AST contre les dépendances OS non gérées ;
- certification dédiée sur Windows, macOS et Ubuntu.

### Preuve
- PR `#219` — MERGED ;
- head candidat : `31f7c612327c48ead478b18f224875dba6313c61` ;
- merge master : `2907b3d1ea529dde27468f27ce5835d2655275e9` ;
- Portability P1 run `32599659706` — SUCCESS ;
- Windows — SUCCESS ;
- macOS — SUCCESS ;
- Ubuntu — SUCCESS ;
- CI générale run `32599659683` — SUCCESS ;
- Guided Restore AFTER run `32599659687` — SUCCESS ;
- T2 Runtime Browser run `32599659693` — SUCCESS.

### Limites laissées volontairement à P2+
- packaging macOS non construit ;
- licence/secrets inter-machine non traités ;
- bundle cabinet de migration non défini.

---

## P2 — Runtime Supervisor — CLOSED ✅

### Goal
Créer une autorité unique de lifecycle du runtime local.

### Implémentation vérifiée
- verrou inter-processus non bloquant derrière `PlatformAdapter` sur Windows et POSIX ;
- `RuntimeSupervisor` stdlib pur pour single-instance et readiness ;
- second lancement : attend l'instance existante, ouvre son UI puis sort ;
- premier lancement : ouvre l'UI uniquement après health réel ;
- `backend.main` ne possède plus d'autorité d'ouverture navigateur ;
- `.env` canonique chargé avant résolution `CABINET_HOST` / `CABINET_PORT` ;
- import du backend lourd après arbitrage single-instance ;
- `run.py` reste la source canonique du port et du lifecycle ;
- restart Guided Restore conserve `DIGITALCROWN_RESTORE_RESTART` et reste compatible avec le supervisor.

### Preuve
- PR `#220` — MERGED ;
- head candidat : `0b6071b663162575efe0de40c411a8ff29763d7a` ;
- merge master : `19bf42b61001c77c219fc2b957d6dadc84f79480` ;
- Portability Runtime run `32601811079` — SUCCESS ;
- Windows — SUCCESS ;
- macOS — SUCCESS ;
- Ubuntu — SUCCESS ;
- CI générale run `32601811065` — SUCCESS ;
- Guided Restore AFTER run `32601811069` — SUCCESS ;
- T2 Runtime Browser run `32601811078` — SUCCESS ;
- Catalog Connected Truth run `32601811060` — SUCCESS ;
- Patient P7 Final Certification run `32601811091` — SUCCESS.

### Défaut intermédiaire non crédité
Le candidat précédent `a61f54d7…` déplaçait le chargement `.env` après `_resolve_host_port()`. Il aurait pu ignorer `CABINET_HOST` / `CABINET_PORT` du fichier cabinet. Il a été corrigé avant certification finale et n'est pas crédité.

---

## P3 — Cabinet Bundle portability — NEXT

Définir un contrat de migration explicite regroupant au minimum DB, médias et configuration exportable, avec manifeste/version/checksums et restauration vérifiée. Les secrets ou identifiants machine-bound ne doivent pas être copiés aveuglément.

### Direction technique déjà auditée
- ne pas transporter `backup.key`, `.env`, locks, logs, caches ou secrets machine-bound ;
- produire un snapshot DB portable indépendant de la clé SQLCipher source ;
- chiffrer le bundle avec une clé de migration indépendante du poste ;
- à destination : vérifier le bundle, reconstruire les artefacts locaux avec les clés destination, puis réutiliser le moteur Guided Restore existant ;
- conserver rescue DB/WAL, bascule média atomique, smoke-check et rollback existants.

## P4 — License & secrets rebinding — PLANNED

Définir ce qui est portable, régénéré ou réautorisé lors d'un changement de poste/OS. Vérifier le comportement Windows DPAPI et le stockage sécurisé macOS, ainsi que le contrat de machine binding de la licence.

## P5 — Native/scientific dependency parity — PLANNED

Prouver que SQLCipher, moteurs locaux, ONNX/PyTorch et autres dépendances natives nécessaires au produit fonctionnent sur les plateformes/architectures réellement supportées. Aucune équivalence scientifique n'est supposée sur la seule base d'un import réussi.

## P6 — Cross-platform packaging & signing — PLANNED

Choisir et verrouiller **une** architecture de distribution : build Windows + build macOS issus du même cœur, avec métadonnées/version communes. Windows : packaging/signature installable. macOS : `.app` puis DMG/PKG selon besoin, code signing et notarization, avec prise en compte Apple Silicon et Intel selon la matrice supportée.

## P7 — Install / update / migration certification — PLANNED

Certification finale sur environnements propres : installation, premier boot, restart, autostart si retenu, update, rollback, désinstallation sans perte de données, import d'un cabinet, migration Windows↔macOS et reprise après erreur. Aucun statut production-ready sans ces preuves.

---

## État courant

- P1 : CLOSED ✅
- P2 : CLOSED ✅
- P3 : NEXT
- P4→P7 : PLANNED
- progression chiffrée : **non définie** tant qu'une pondération canonique des lots n'est pas fixée ; ne pas inventer de pourcentage.
- Next exact : P3 Cabinet Bundle portability — implémenter le format portable, la validation destination et les tests de migration inter-machine sans transporter les secrets machine-bound.
