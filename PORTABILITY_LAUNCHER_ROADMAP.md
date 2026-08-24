# Portability & Launcher — roadmap canonique

Dernière mise à jour vérifiée : 2026-08-25.

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
| P6 — Industrialized Windows packaging | 8 EP | NEXT |
| P7 — Native macOS packaging | 13 EP | PLANNED |
| P8 — Hardware & peripherals | 21 EP | PLANNED |
| P9 — Backup / Recovery / DR | 8 EP | PLANNED |
| P10 — Cross-platform Update Engine | 13 EP | PLANNED |
| P11 — Launcher & Recovery UX | 8 EP | CLOSED ✅ |
| P12 — CI & certification matrix | 13 EP | PLANNED |
| P13 — Real cabinet certification | 13 EP | PLANNED |
| P14 — Closeout | 5 EP | PLANNED |
| **TOTAL** | **162 EP** | |

Effort Points = complexité relative, pas durée. Aucun EP partiel n’est crédité pour un lot ouvert.

---

## P0 — Baseline & portability contract — CLOSED ✅ — 5 EP

### Goal
Rendre explicite la frontière de portabilité avant modification d’architecture.

### Preuve
- `docs/portability/PORTABILITY_P0_BASELINE.md` ;
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
- PR `#219` — MERGED ; candidat `31f7c612327c48ead478b18f224875dba6313c61` ; merge master `2907b3d1ea529dde27468f27ce5835d2655275e9` ;
- Portability P1 `32599659706` — SUCCESS Windows/macOS/Ubuntu ;
- CI `32599659683`, Guided Restore `32599659687`, T2 `32599659693` — SUCCESS.

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
- PR `#220` — MERGED ; candidat `0b6071b663162575efe0de40c411a8ff29763d7a` ; merge master `19bf42b61001c77c219fc2b957d6dadc84f79480` ;
- Portability Runtime `32601811079`, CI `32601811065`, Guided Restore `32601811069`, T2 `32601811078`, Catalog `32601811060`, Patient P7 `32601811091` — SUCCESS.

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
- PR `#222` — MERGED ; candidat `89708100838b85f3574674de21882684c98be9f6` ; merge master `98fe4440806b38d33cbdfb32eab6e7bc85e9b573` ;
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
- PR `#224` — MERGED ; candidat `3bc7426848d544183f235244ae8eab7b255d1341` ; merge master `40cb22d6dddcbae6dee7340dc23956decaf701d8` ;
- Runtime `32610745183`, Guided Restore `32610745196`, Settings P2 `32610745220`, T2 `32610745188`, Catalog `32610745249`, Patient P7 `32610745225`, CI `32610745134` — SUCCESS.

---

## P5 — Scientific/native runtime portability — CLOSED ✅ — 13 EP

### Goal amendé et verrouillé le 24 août 2026
Prouver la **portabilité du runtime natif/scientifique réellement requis** sur Windows x64 et macOS Apple Silicon, ainsi que le comportement fail-closed lorsque les assets scientifiques externes ne sont pas provisionnés.

### Décision de périmètre
Le modèle céphalométrique historique SOTA 38 points n’a pas pu être retrouvé comme artefact canonique avec poids + provenance + SHA256. Le produit a explicitement décidé de **ne pas reconstruire arbitrairement cet ancien poids pour P5**.

- sélection/qualité/précision clinique du futur moteur céphalo transférées à **Cephalometry NextGen** (`cephalo/nextgen-research`) ;
- aucune équivalence clinique ou numérique des modèles revendiquée par P5 ;
- poids céphalo legacy et panoramique restent externes/non versionnés ;
- leur provisioning installable appartient à P6/P7 puis P12/P13.

### Preuve
- P5A PR `#228` — MERGED ; run natif `32723535974` — SUCCESS Windows x64 + macOS Apple Silicon ;
- P5 final PR `#233`, candidat `3ee3447e1cd3d92575e3b930abeef8e31061bfb8` ;
- Portability P5 `32750343308` — SUCCESS ; Windows `NATIVE_RUNTIME_GATE=OK` + `SCIENTIFIC_FAIL_CLOSED_GATE=OK` ; macOS `NATIVE_RUNTIME_GATE=OK (Darwin arm64)` + `SCIENTIFIC_FAIL_CLOSED_GATE=OK` + `APPLE_SILICON_GATE=OK` ;
- CI `32750343210`, T2 `32750343211`, Patient P7 `32750343288`, Catalog `32750343395` — SUCCESS.

### Gate A — CORE/NATIVE PORTABLE ✅
Le cœur partagé et les dépendances natives certifiées s’exécutent sur Windows x64 et macOS Apple Silicon selon le contrat P5 amendé. **Cette gate n’est pas une certification de précision clinique des modèles.**

---

## P6 — Industrialized Windows packaging — NEXT — 8 EP

### Goal
Rendre la distribution Windows déterministe, reproductible et installable en préservant explicitement les données cabinet.

### Scope canonique
- un seul builder autoritaire basé sur `DigitalCrown.spec`/PyInstaller ou successeur explicitement validé ;
- toolchain de build piné/reproductible ;
- frontend via `npm ci` + build ;
- ressources/assets contrôlés et build fail-closed si un asset requis manque ;
- source de version unique ;
- Inno Setup, install/upgrade/uninstall et conservation des données ;
- signature Authenticode + timestamp lorsque le certificat de distribution est disponible ;
- smoke du build frozen puis test installateur sur Windows propre.

### Findings déjà vérifiés
- `DigitalCrown.spec` est le chemin documenté et utilise `run.py` ;
- `scripts/build_exe.py` est un builder legacy divergent ;
- PyInstaller n’est pas piné dans les requirements ;
- le spec peut collecter zéro modèle silencieusement si `backend/ai_models` est absent ;
- `AppVersion=1.0.0` reste hardcodé dans Inno Setup ;
- aucun signing Windows n’est encore intégré ;
- `docs/CABINET_ONPREM_GUIDE.md` contient une contradiction PostgreSQL vs SQLite/SQLCipher ;
- run P6 `32783305531` échoue actuellement au static gate : `forbidden spec content: .env` dans `DigitalCrown.spec`.

### Succès
Un artefact Windows exact peut être reconstruit, installé, mis à niveau et désinstallé sur une machine propre sans fuite de secrets ni perte de données cabinet.

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

---

## P9 — Backup, Recovery & Disaster Recovery — PLANNED — 8 EP

### Goal
Faire en sorte que la perte d’un ordinateur n’implique jamais la perte du cabinet : backup, intégrité, chiffrement, restore, interruptions, disque insuffisant, corruption et récupération inter-OS.

---

## P10 — Cross-platform Update Engine — PLANNED — 13 EP

### Goal
Updates authentifiées avec checksum/signature, rescue point, migration, health post-update et rollback automatique sur Windows/macOS.

> La branche `portability/p10-update-engine` sert actuellement aussi de base d’intégration à P11. Cela ne crédite ni ne ferme P10.

---

## P11 — Launcher & Recovery UX — CLOSED ✅ — 8 EP

### Goal
Exposer des états de lifecycle/récupération vrais et actionnables sans console. Tout changement visuel suit BEFORE → Goal → mockup → implémentation → AFTER → score.

### Implémentation vérifiée
- recovery HTML local autonome, disponible même si FastAPI ne devient jamais healthy ;
- codes `RUNTIME_NOT_READY`, `RUNTIME_START_FAILED`, `INSTANCE_NOT_READY` ;
- formulation truth-safe : l’écran de récupération lui-même ne lance aucune restauration, suppression ni réinitialisation ;
- retry/open + copie du chemin du journal ;
- Guided Restore rendu scannable : `Analyse -> Secours -> Restauration -> Vérification` ;
- contrôles critiques mobiles >= 44 px ;
- `.dcbundle` exclu du picker standard, car le flow portable dédié exige `migration_secret`.

### Preuve
- BEFORE run `32780649466` — SUCCESS ; artifact `9539649740` ; 10 captures matching ;
- mockup/référence visuelle verrouillé avant implémentation ;
- candidat final `cbaf21a066fb6b8b70f4c9d6b3ec1a950cda890b` ; PR `#241` ;
- P11 final `32783305559` — SUCCESS ; contrat P11 + 8 tests + frontend build ;
- AFTER artifact `9540590729`, digest `sha256:47ffdcee25d9237ac89f9665c2a0d34603005b8b2786412b63eb30f2a0457cf1` ;
- 15/15 AFTER captures sur 1440 / 1024 / 768 / 430 / 390 ; zéro overflow ; zéro erreur runtime/page ;
- régressions : Runtime `32783305528`, T2 `32783305594`, Catalog `32783305574`, Patient `32783305575`, RBAC `32783305530`, Security `32783305489`, CI `32783305627` — SUCCESS ;
- score Startup : **9,3/10** (BEFORE 5,6) ; Guided Restore : **9,1/10** (BEFORE 7,7) ;
- PR `#241` merged into `portability/p10-update-engine` ; merge `455e7603c78b0139c0b39e217bed768bfe1186e7` ;
- closeout canonique : `docs/portability/P11_LAUNCHER_RECOVERY_UX.md` ;
- aucun Vercel.

### Limite observée
L’état `prepared` reste volontairement dense à 390 px, mais la hiérarchie décisionnelle reste lisible et aucun overflow horizontal n’est observé.

---

## P12 — CI & certification matrix — PLANNED — 13 EP

### Goal
Certifier les artefacts Windows/macOS et empêcher les régressions plateforme : runtime, frozen build, models/assets, backup/restore, packaging, update et tests raisonnables.

---

## P13 — Real cabinet certification — PLANNED — 13 EP

### Goal
Prouver le flow cabinet critique sur machines propres Windows/macOS et la migration croisée, avec scénarios d’échec contrôlés.

---

## P14 — Closeout & permanent compass — PLANNED — 5 EP

### Goal
Fermer le chantier avec docs, matrices OS/hardware, guides d’installation, recovery/update, troubleshooting, gouvernance et preuve finale cohérents avec le HEAD certifié.

---

## Ordre canonique

Ordre produit cible : P0 → P1 → P2 → P3 → P4 → P5 → P6 → P7 → P8 → P9 → P10 → P11 → P12 → P13 → P14.

P11 a été fermé hors ordre pendant que P6 reste ouvert/non crédité. Cela ne change pas les dépendances restantes ni le Next canonique : **P6**.

## État courant

- P0–P5 : **CLOSED ✅** ;
- P6 : **NEXT / blocker connu `DigitalCrown.spec` + `.env`** ;
- P7–P10 : **PLANNED** ;
- P11 : **CLOSED ✅** ;
- P12–P14 : **PLANNED** ;
- validé : **73 / 162 EP = 45,1 %** ;
- aucun EP partiel n’est crédité pour un lot ouvert ;
- Cephalometry NextGen est un chantier scientifique séparé et n’est pas compté dans les 162 EP ;
- aucun Vercel ;
- Next exact : **P6 Industrialized Windows packaging** — corriger le static packaging gate (`DigitalCrown.spec` ne doit pas embarquer `.env`), figer le builder canonique, supprimer/neutraliser les chemins legacy dangereux, pinner toolchain/version/assets, puis construire et certifier un installateur Windows exact sur environnement propre.
