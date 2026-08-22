# Portability & Launcher — roadmap canonique

Dernière mise à jour vérifiée : 2026-08-22.

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
- double autorité d'ouverture navigateur encore présente ;
- readiness basée sur délai fixe dans `run.py` ;
- absence de single-instance/supervisor complet ;
- packaging macOS non construit ;
- licence/secrets inter-machine non traités ;
- bundle cabinet de migration non défini.

---

## P2 — Runtime Supervisor — ACTIVE 🟡

### Goal
Créer une autorité unique de lifecycle du runtime local.

### Succès
- une seule instance par poste ;
- une seule autorité d'ouverture UI ;
- port canonique unique ;
- readiness `/health` avant ouverture ;
- démarrage, arrêt, crash et restart déterministes ;
- Guided Restore reste compatible avec le restart hors-processus.

### Défauts déjà vérifiés
- `run.py` ouvre `127.0.0.1:8005` après un délai fixe de 2 s ;
- `backend/main.py` ouvre encore `127.0.0.1:8000` en build mode ;
- la duplication peut produire deux onglets et un port erroné.

### Preuve requise
- tests unitaires supervisor ;
- test concurrent-launch / single-instance ;
- readiness réelle, aucun `sleep` comme critère de santé ;
- CI exacte HEAD ;
- non-régression Guided Restore.

---

## P3 — Cabinet Bundle portability — PLANNED

Définir un contrat de migration explicite regroupant au minimum DB, médias et configuration exportable, avec manifeste/version/checksums et restauration vérifiée. Les secrets ou identifiants machine-bound ne doivent pas être copiés aveuglément.

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
- P2 : ACTIVE 🟡
- P3→P7 : PLANNED
- progression chiffrée : **non définie** tant qu'une pondération canonique des lots n'est pas fixée ; ne pas inventer de pourcentage.
- Next exact : P2 Runtime Supervisor — supprimer la double autorité, introduire readiness et single-instance, puis certifier exact-head.
