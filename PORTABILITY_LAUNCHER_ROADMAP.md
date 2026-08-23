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

## P3 — Cabinet Bundle portability — CLOSED ✅

### Goal
Rendre les données cabinet portables entre machines/OS supportés sans transporter les secrets liés à la machine source.

### Implémentation vérifiée
- bundle canonique chiffré `.dcbundle` avec manifeste/version/intégrité ;
- export SQLCipher indépendant de la clé machine source ;
- médias inclus puis rechiffrés pour la restauration destination ;
- `.env`, `backup.key`, `license_vault.bin`, locks/logs/caches exclus ;
- Guided Restore réutilisé pour prepare/apply/smoke/rollback ;
- frontière `PlatformAdapter` respectée ;
- certification Windows/macOS/Ubuntu.

### Preuve
- head candidat : `89708100838b85f3574674de21882684c98be9f6` ;
- PR `#222` — MERGED ;
- merge master : `98fe4440806b38d33cbdfb32eab6e7bc85e9b573` ;
- Portability Runtime Certification `32605929004` — SUCCESS ;
- Settings Guided Restore AFTER `32605928982` — SUCCESS ;
- T2 Runtime Browser Certification `32605928994` — SUCCESS ;
- Catalog Connected Truth Certification `32605928980` — SUCCESS ;
- Patient P7 Final Certification `32605928983` — SUCCESS ;
- CI `32605929015` — SUCCESS.

---

## P4 — License & secrets rebinding — CLOSED ✅

### Goal
Lors d'une migration inter-machine, conserver l'identité et les données du cabinet sans transporter ni faire confiance aux secrets, sessions ou coffre licence de la machine source.

### Implémentation vérifiée
- secrets machine destination conservés/régénérés localement ;
- `license_vault.bin` non portable et revalidation locale obligatoire ;
- grâce offline stricte 72 h + anti-clock rollback ;
- indisponibilité Firebase non destructive (`active=None`) ;
- `/recheck-license` lié à l'identité `CabinetConfig` authentifiée ;
- détection d'un restore portable par manifeste validé, indépendamment de l'extension du fichier ;
- rebind portable invalide licence locale + pairings/tokens mobiles ;
- pools SQLAlchemy disposés avant restore et dans les chemins d'échec/finally ;
- coffre local : clé faible/prévisible refusée, écriture atomique et permissions privées via abstraction plateforme ;
- Guided Restore rollback-safe ;
- garde P1 respectée sur Windows/macOS/Ubuntu.

### Preuve
- head candidat : `3bc7426848d544183f235244ae8eab7b255d1341` ;
- PR `#224` — MERGED ;
- merge produit master : `40cb22d6dddcbae6dee7340dc23956decaf701d8` ;
- Portability Runtime Certification `32610745183` — SUCCESS ;
- Settings Guided Restore AFTER `32610745196` — SUCCESS ;
- Onboarding Settings P2 Visual Certification `32610745220` — SUCCESS ;
- T2 Runtime Browser Certification `32610745188` — SUCCESS ;
- Catalog Connected Truth Certification `32610745249` — SUCCESS ;
- Patient P7 Final Certification `32610745225` — SUCCESS ;
- CI `32610745134` — SUCCESS.

---

## P5 — Native/scientific dependency parity — NEXT

Prouver que SQLCipher, moteurs locaux, ONNX/PyTorch et autres dépendances natives nécessaires au produit fonctionnent sur les plateformes/architectures réellement supportées. Aucune équivalence scientifique n'est supposée sur la seule base d'un import réussi.

## P6 — Cross-platform packaging & signing — PLANNED

Choisir et verrouiller **une** architecture de distribution : build Windows + build macOS issus du même cœur, avec métadonnées/version communes. Windows : packaging/signature installable. macOS : `.app` puis DMG/PKG selon besoin, code signing et notarization, avec prise en compte Apple Silicon et Intel selon la matrice supportée.

## P7 — Install / update / migration certification — PLANNED

Certification finale sur environnements propres : installation, premier boot, restart, autostart si retenu, update, rollback, désinstallation sans perte de données, import d'un cabinet, migration Windows↔macOS et reprise après erreur. Aucun statut production-ready sans ces preuves.

---

## État courant

- P0 : CLOSED ✅ — 5 EP ;
- P1 : CLOSED ✅ — 13 EP ;
- P2 : CLOSED ✅ — 13 EP ;
- P3 : CLOSED ✅ — 13 EP ;
- P4 : CLOSED ✅ — 8 EP ;
- P5 : NEXT ;
- P6→P7 : PLANNED ;
- progression vérifiée : `52 / 162 EP` = **32.1%** ;
- aucun EP partiel n'est crédité pour un lot ouvert ;
- Next exact : P5 Native/scientific dependency parity — verrouiller provenance des modèles/fixtures, dépendances natives et exécution réelle Windows/macOS Apple Silicon avant tout benchmark de parité scientifique.
