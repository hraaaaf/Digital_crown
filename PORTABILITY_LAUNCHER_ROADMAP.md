# Portability & Launcher — roadmap canonique

Dernière mise à jour vérifiée : 2026-08-26.

> **Source de vérité unique du chantier.** L’ancienne roadmap `docs/PORTABILITY_LAUNCHER_ROADMAP.md` est dépréciée et renvoie vers ce fichier.

## Goal global

Digital Crown doit offrir **un seul produit local-first**, issu d’un cœur partagé, installable et exploitable sur Windows et macOS avec démarrage, données cabinet, restauration, licence/secrets, packaging, mises à jour, récupération et certification maîtrisés.

## Succès global

- cœur applicatif commun Windows/macOS, sans fork fonctionnel ;
- intégrations OS derrière des frontières explicites ;
- runtime unique et readiness réelle avant ouverture UI ;
- chemins data/config/log/runtime natifs ;
- cabinet portable indépendamment des secrets machine ;
- builds Windows/macOS installables et signés selon leur plateforme ;
- backup, update et rollback vérifiés ;
- matériel explicitement classé par OS ;
- certification E2E sur machines propres avant toute revendication de support complet.

## Doctrine d’architecture

- **Un cœur commun**, pas deux applications Windows/macOS.
- Frontend React et backend FastAPI restent partagés.
- Le comportement OS-spécifique passe par les adapters/frontières dédiés.
- Données cabinet et identité/secrets machine sont des contrats distincts.
- Une dépendance native importable n’est pas, à elle seule, une preuve scientifique.
- Aucun déploiement Vercel n’appartient à ce chantier sans autorisation explicite.

## Effort canonique

| Lot | Effort | État |
|---|---:|---|
| P0 — Baseline & portability contract | 5 EP | CLOSED ✅ |
| P1 — OS abstraction layer | 13 EP | CLOSED ✅ |
| P2 — Runtime Supervisor / Launcher V2 | 13 EP | CLOSED ✅ |
| P3 — Cabinet data portability | 13 EP | CLOSED ✅ |
| P4 — Licence, secrets & machine identity | 8 EP | CLOSED ✅ |
| P5 — Scientific/native runtime portability | 13 EP | CLOSED ✅ |
| P6 — Industrialized Windows packaging | 8 EP | ACTIVE — 0/8 EP |
| P7 — Native macOS packaging | 13 EP | PLANNED |
| P8 — Hardware & peripherals | 21 EP | PLANNED |
| P9 — Backup / Recovery / DR | 8 EP | PLANNED |
| P10 — Cross-platform Update Engine | 13 EP | PLANNED |
| P11 — Launcher & Recovery UX | 8 EP | PLANNED |
| P12 — CI & certification matrix | 13 EP | PLANNED |
| P13 — Real cabinet certification | 13 EP | PLANNED |
| P14 — Closeout | 5 EP | PLANNED |
| **TOTAL** | **162 EP** | |

Effort Points = complexité relative, pas durée.

---

## P0 — Baseline & portability contract — CLOSED ✅ — 5 EP

### Goal
Rendre explicite la frontière de portabilité avant modification d’architecture.

### Preuve
- baseline/audit canonique : `docs/portability/PORTABILITY_P0_BASELINE.md` ;
- dépendances OS, chemins, runtime, secrets, natifs/scientifiques et surfaces hardware classés pour les lots ultérieurs.

---

## P1 — OS abstraction layer — CLOSED ✅ — 13 EP

### Goal
Retirer du cœur partagé les primitives Windows/macOS directes nécessaires au runtime.

### Implémentation vérifiée
- `backend/core/platform.py` = frontière plateforme ;
- chemins data/config/log/runtime centralisés ;
- macOS : `~/Library/Application Support/DigitalCrown` et `~/Library/Logs/DigitalCrown` ;
- `AppPaths` délègue à la frontière plateforme ;
- bootstrap env, permissions atomiques, ouverture URI, liveness PID et Guided Restore centralisés ;
- garde statique contre les dépendances OS non gérées.

### Preuve
- PR `#219` — MERGED ;
- candidat `31f7c612327c48ead478b18f224875dba6313c61` ;
- merge master `2907b3d1ea529dde27468f27ce5835d2655275e9` ;
- Portability P1 `32599659706` — SUCCESS Windows/macOS/Ubuntu ;
- CI `32599659683` — SUCCESS ; Guided Restore `32599659687` — SUCCESS ; T2 `32599659693` — SUCCESS.

---

## P2 — Runtime Supervisor / Launcher V2 — CLOSED ✅ — 13 EP

### Goal
Créer une autorité unique et cross-platform du lifecycle local.

### Implémentation vérifiée
- verrou inter-processus derrière `PlatformAdapter` ;
- `RuntimeSupervisor` stdlib pur, single-instance + readiness ;
- second lancement : réutilise l’instance existante ;
- premier lancement : UI seulement après health réel ;
- `.env` canonique chargé avant résolution host/port ;
- backend lourd importé après arbitrage single-instance ;
- `run.py` reste autorité du port/lifecycle ;
- Guided Restore reste compatible.

### Preuve
- PR `#220` — MERGED ;
- candidat `0b6071b663162575efe0de40c411a8ff29763d7a` ;
- merge master `19bf42b61001c77c219fc2b957d6dadc84f79480` ;
- Portability Runtime `32601811079` — SUCCESS Windows/macOS/Ubuntu ;
- CI `32601811065`, Guided Restore `32601811069`, T2 `32601811078`, Catalog `32601811060`, Patient P7 `32601811091` — SUCCESS.

---

## P3 — Cabinet data portability — CLOSED ✅ — 13 EP

### Goal
Rendre le cabinet portable entre machines/OS sans transporter les secrets liés à la machine source.

### Implémentation vérifiée
- `.dcbundle` chiffré, manifeste/version/intégrité ;
- export SQLCipher indépendant de la clé machine source ;
- médias inclus puis rechiffrés destination ;
- `.env`, `backup.key`, `license_vault.bin`, locks/logs/caches exclus ;
- prepare/apply/smoke/rollback via Guided Restore ;
- certification Windows/macOS/Ubuntu.

### Preuve
- candidat `89708100838b85f3574674de21882684c98be9f6` ; PR `#222` — MERGED ;
- merge master `98fe4440806b38d33cbdfb32eab6e7bc85e9b573` ;
- Runtime `32605929004`, Guided Restore `32605928982`, T2 `32605928994`, Catalog `32605928980`, Patient P7 `32605928983`, CI `32605929015` — SUCCESS.

---

## P4 — Licence & local secrets cross-platform — CLOSED ✅ — 8 EP

### Goal
Conserver identité et données cabinet lors d’une migration sans faire confiance aux secrets/sessions/coffre de la machine source.

### Implémentation vérifiée
- secrets destination conservés/régénérés localement ;
- `license_vault.bin` non portable + revalidation locale ;
- grâce offline stricte 72 h + anti-clock rollback ;
- Firebase indisponible non destructif (`active=None`) ;
- recheck licence lié à l’identité cabinet authentifiée ;
- restore portable invalide licence locale + pairings/tokens mobiles ;
- pools SQLAlchemy disposés avant restore ;
- coffre local fail-closed sur clé faible/prévisible ;
- Guided Restore rollback-safe.

### Preuve
- candidat `3bc7426848d544183f235244ae8eab7b255d1341` ; PR `#224` — MERGED ;
- merge master `40cb22d6dddcbae6dee7340dc23956decaf701d8` ;
- Runtime `32610745183`, Guided Restore `32610745196`, Settings P2 `32610745220`, T2 `32610745188`, Catalog `32610745249`, Patient P7 `32610745225`, CI `32610745134` — SUCCESS.

---

## P5 — Scientific/native runtime portability — CLOSED ✅ — 13 EP

### Goal amendé et verrouillé le 24 août 2026
Prouver la **portabilité du runtime natif/scientifique réellement requis** sur Windows x64 et macOS Apple Silicon, ainsi que le comportement fail-closed lorsque les assets scientifiques externes ne sont pas provisionnés.

### Décision de périmètre
Le modèle céphalométrique historique SOTA 38 points n’a pas pu être retrouvé comme artefact canonique avec poids + provenance + SHA256. Le produit a explicitement décidé de **ne pas reconstruire arbitrairement cet ancien poids pour P5**.

En conséquence :
- la sélection, qualité, précision numérique/clinique et éventuel remplacement du moteur céphalo sont transférés au chantier séparé **Cephalometry NextGen** (`cephalo/nextgen-research`) ;
- P5 **ne revendique aucune équivalence clinique ou numérique des modèles** ;
- les poids céphalo legacy et panoramique restent des assets externes, non versionnés dans le dépôt public ;
- leur packaging/provisionnement sur installation propre appartient à P6/P7 puis à la certification P12/P13.

### Implémentation vérifiée
- OpenCV unique : `opencv-python-headless==4.13.0.92` ;
- ONNX Runtime, PyTorch CPU, SQLCipher, ReportLab, WeasyPrint, Pillow/QR exécutés réellement ;
- Pango/GObject provisionnés pour WeasyPrint sur Windows/macOS ;
- Apple Silicon explicitement exigé `arm64` ;
- `backend/scientific_assets.json` schema v2 : scope `native-runtime-and-fail-closed`, assets `external-not-versioned` ;
- SOTA absent → moteur désactivé ;
- céphalo sans SOTA/legacy → `FAILED`, zéro landmark fabriqué, placement manuel requis ;
- panoramique sans modèle en environnement clinique → `RuntimeError`, aucune simulation acceptée comme preuve ;
- harness charge les vrais services scientifiques sans exécuter l’initialiseur global `backend/__init__.py`, afin de ne pas transformer un test natif ciblé en bootstrap SQLAlchemy complet.

### Preuve
P5A :
- PR `#228` — MERGED ; candidat `375aae5432da8531882d791574dd251cf09d32d5` ; merge produit `ae9efc5055e8b1105e058788e0de3386e8880335` ;
- Portability P5 Native Dependency Certification `32723535974` — SUCCESS Windows x64 + macOS Apple Silicon ;
- CI `32723535895`, T2 `32723535977`, Catalog `32723535901`, Patient P7 `32723535937` — SUCCESS.

P5 final :
- PR `#233` ; candidat final `3ee3447e1cd3d92575e3b930abeef8e31061bfb8` ;
- Portability P5 Native Dependency Certification `32750343308` — SUCCESS ;
- Windows : `NATIVE_RUNTIME_GATE=OK (Windows AMD64)` + `SCIENTIFIC_FAIL_CLOSED_GATE=OK` ;
- macOS : `NATIVE_RUNTIME_GATE=OK (Darwin arm64)` + `SCIENTIFIC_FAIL_CLOSED_GATE=OK` + `APPLE_SILICON_GATE=OK (arm64)` ;
- CI `32750343210` — SUCCESS ;
- T2 `32750343211` — SUCCESS ;
- Patient P7 `32750343288` — SUCCESS ;
- Catalog `32750343395` — SUCCESS.

### Échecs intermédiaires non crédités
- `32743721990` : harness lancé par chemin, `backend` absent de `sys.path` ;
- `32749972672` : mode module corrigé mais `backend/__init__.py` entraînait SQLAlchemy hors scope ;
- après deux échecs similaires, stratégie changée vers namespace ciblé ; run final vert ci-dessus.

### Gate A — CORE/NATIVE PORTABLE ✅
Le cœur partagé et les dépendances natives certifiées s’exécutent sur Windows x64 et macOS Apple Silicon selon le contrat P5 amendé. **Cette gate n’est pas une certification de précision clinique des modèles.**

---

## P6 — Industrialized Windows packaging — ACTIVE — 8 EP

### Goal
Rendre la distribution Windows déterministe, reproductible et installable en préservant explicitement les données cabinet.

### État d’exécution au 26 août 2026
P6 est **ouvert mais 0/8 EP sont crédités**. Le packaging est temporairement en pause sur un prérequis scientifique explicite, sans fermer ni renuméroter P6.

Sous-lot actif : **P6 Scientific Assets Refresh** (`portability/p6-scientific-assets-refresh`).

- ce sous-lot de recherche ne remplace pas P6 et ne gagne aucun EP Portability à lui seul ;
- céphalométrie : `DC-Ceph-UNet29Q4 / Aariz v1` est le gagnant technique du benchmark scellé, run `32876308676` — SUCCESS ; aucune revendication d’équivalence clinique ;
- ONNX gagnant attendu : SHA256 `809f1d3d2347d2a34f57d4a3415bb319c29f8a25c325d41160e5f28d4e5dadad`, `7,624,307 bytes` ;
- rétention privée exacte du binaire gagnant : **OPEN**, aucune rétention privée n’est créditée tant qu’elle n’est pas prouvée ;
- panoramique : cible Phase A = localisation dentaire + numérotation FDI ; aucune pathologie automatique n’est requise pour restaurer le contrat produit actif ;
- aucun corpus direct-FDI inspecté ne ferme encore simultanément provenance, droits commerciaux, labels FDI traçables et reproductibilité ;
- protocole clinique d’annotation FDI : `docs/P6_PANORAMIC_FDI_ANNOTATION_PROTOCOL.md` ;
- matrice scientifique canonique : `docs/P6_SCIENTIFIC_ASSETS_REFRESH.md` ;
- handover packaging : `docs/PORTABILITY_P6_PAUSE_HANDOVER.md`.

### Scope canonique
- un seul builder autoritaire, basé sur `DigitalCrown.spec`/PyInstaller ou successeur explicitement validé ;
- toolchain de build piné/reproductible ;
- frontend via `npm ci` + build ;
- ressources/assets contrôlés et build fail-closed si un asset requis manque ;
- source de version unique ;
- Inno Setup, install/upgrade/uninstall et conservation des données ;
- signature Authenticode + timestamp lorsque le certificat de distribution est disponible ;
- smoke du build frozen puis test installateur sur Windows propre.

### Findings déjà vérifiés avant démarrage
- `DigitalCrown.spec` est le chemin documenté et utilise `run.py` ;
- `scripts/build_exe.py` est un builder legacy divergent : `npm install`, `backend/main.py`, collecte complète `ai_models` et possibilité d’embarquer `firebase_creds.json` ; il doit être supprimé du chemin de production ou aligné ;
- PyInstaller n’est pas piné dans les requirements ;
- le spec peut collecter zéro modèle silencieusement si `backend/ai_models` est absent d’un checkout propre ;
- `AppVersion=1.0.0` reste hardcodé dans Inno Setup ;
- aucun signing Windows n’est encore intégré ;
- `docs/CABINET_ONPREM_GUIDE.md` contient une contradiction entre « PostgreSQL seul supporté » et le mode cabinet SQLite/SQLCipher confirmé par README/tests.

### Succès
Un artefact Windows exact peut être reconstruit, installé, mis à niveau et désinstallé sur une machine propre sans fuite de secrets ni perte de données cabinet.

### Preuve requise
Build reproducible + smoke frozen + install/upgrade/uninstall propre + signature vérifiée selon le gate de certificat retenu.

### Next exact scientifique avant reprise packaging
1. exécuter **un seul probe reproductible Mendeley V3** sur `10.17632/73n3kz2k4k.3` ;
2. figer hashes + inventaire + contenu réel de `annotations.json`, sans synthèse FDI ;
3. mettre à jour la matrice scientifique selon la preuve obtenue ;
4. fermer la rétention privée exacte du gagnant céphalo et son protocole clinique ;
5. reprendre le candidat packaging P6 préparé puis lancer **un seul run Windows lourd** lorsque les assets requis sont réellement fermés.

---

## P7 — Native macOS packaging — PLANNED — 13 EP

### Goal
Livrer une application macOS normale, signée/notarisée, sans Terminal ni contournement Gatekeeper.

### Scope
`.app` Apple Silicon arm64, ressources/assets, bundle metadata/icône, chemins natifs, permissions, DMG/PKG selon besoin, Developer ID, Hardened Runtime/entitlements, notarisation, stapling, Gatekeeper, clean install/upgrade/uninstall.

### Contrainte vérifiée
PyInstaller n’est pas cross-compiler : le build macOS devra être produit sur macOS. Le spec actuel n’a ni `BUNDLE`, ni `codesign_identity`, ni entitlements configurés.

---

## P8 — Hardware & peripheral compatibility — PLANNED — 21 EP

### Goal
Classer explicitement chaque périphérique clinique par OS : `SUPPORTED`, `LIMITED`, `FILE-IMPORT` ou `UNSUPPORTED`, sur test réel ou preuve fabricant clairement distinguée.

## P9 — Backup, Recovery & Disaster Recovery — PLANNED — 8 EP

### Goal
Faire en sorte que la perte d’un ordinateur n’implique jamais la perte du cabinet : backup, intégrité, chiffrement, restore, interruptions, disque insuffisant, corruption et récupération inter-OS.

## P10 — Cross-platform Update Engine — PLANNED — 13 EP

### Goal
Updates authentifiées avec checksum/signature, rescue point, migration, health post-update et rollback automatique sur Windows/macOS.

## P11 — Launcher & Recovery UX — PLANNED — 8 EP

### Goal
Exposer des états de lifecycle/récupération vrais et actionnables sans console. Tout changement visuel suit BEFORE → Goal → mockup → implémentation → AFTER → score.

## P12 — CI & certification matrix — PLANNED — 13 EP

### Goal
Certifier les artefacts Windows/macOS et empêcher les régressions plateforme : runtime, frozen build, models/assets, backup/restore, packaging, update et tests raisonnables.

## P13 — Real cabinet certification — PLANNED — 13 EP

### Goal
Prouver le flow cabinet critique sur machines propres Windows/macOS et la migration croisée, avec scénarios d’échec contrôlés.

## P14 — Closeout & permanent compass — PLANNED — 5 EP

### Goal
Fermer le chantier avec docs, matrices OS/hardware, guides d’installation, recovery/update, troubleshooting, gouvernance et preuve finale cohérents avec le HEAD certifié.

---

## Ordre canonique

P0 → P1 → P2 → P3 → P4 → P5 → **P6**.

P7 et P8 peuvent ensuite avancer lorsque leurs dépendances/hardware le permettent.

Puis : P9 → P10 → P11 → P12 → P13 → P14.

## État courant

- P0–P5 : **CLOSED ✅** ;
- P6 : **ACTIVE — 0/8 EP crédité** ;
- sous-lot actif : **P6 Scientific Assets Refresh** ;
- P7–P14 : **PLANNED** ;
- validé : **65 / 162 EP = 40,1 %** ;
- aucun EP partiel n’est crédité pour un lot ouvert ;
- Cephalometry NextGen / Scientific Assets Refresh reste non crédité séparément dans les 162 EP ;
- aucun Vercel ;
- Next exact : **probe Mendeley V3 → hashes/annotations → mise à jour scientifique → rétention privée céphalo → reprise P6 Industrialized Windows packaging**.
