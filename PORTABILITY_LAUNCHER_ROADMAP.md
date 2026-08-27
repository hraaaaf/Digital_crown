# Portability & Launcher — roadmap canonique

Dernière mise à jour vérifiée : 2026-08-27.

> **Source de vérité unique du chantier.** L’ancienne roadmap `docs/PORTABILITY_LAUNCHER_ROADMAP.md` est dépréciée et renvoie vers ce fichier.

## Goal global

Digital Crown doit offrir **un seul produit local-first**, issu d’un cœur partagé, installable et exploitable sur Windows et macOS avec démarrage, données cabinet, restauration, licence/secrets, packaging, mises à jour, récupération et certification maîtrisés.

## Succès global

- cœur applicatif commun Windows/macOS, sans fork fonctionnel ;
- intégrations OS derrière des frontières explicites ;
- runtime unique et readiness réelle avant ouverture UI ;
- chemins data/config/log/runtime natifs ;
- cabinet portable indépendamment des secrets machine ;
- builds Windows/macOS installables et signés selon leur plateforme lorsque les certificats de distribution requis sont disponibles ;
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
| P6 — Industrialized Windows packaging | 8 EP | CLOSED ✅ |
| P7 — Native macOS packaging | 13 EP | NEXT |
| P8 — Hardware & peripherals | 21 EP | CLOSED ✅ |
| P9 — Backup / Recovery / DR | 8 EP | PLANNED |
| P10 — Cross-platform Update Engine | 13 EP | PLANNED |
| P11 — Launcher & Recovery UX | 8 EP | CLOSED ✅ |
| P12 — CI & certification matrix | 13 EP | PREPARED — 0 EP |
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

### Preuve
- PR `#219` — MERGED ; candidat `31f7c612327c48ead478b18f224875dba6313c61` ; merge master `2907b3d1ea529dde27468f27ce5835d2655275e9` ;
- Portability P1 `32599659706` — SUCCESS Windows/macOS/Ubuntu ;
- CI `32599659683`, Guided Restore `32599659687`, T2 `32599659693` — SUCCESS.

---

## P2 — Runtime Supervisor / Launcher V2 — CLOSED ✅ — 13 EP

### Goal
Créer une autorité unique et cross-platform du lifecycle local.

### Preuve
- PR `#220` — MERGED ; candidat `0b6071b663162575efe0de40c411a8ff29763d7a` ; merge master `19bf42b61001c77c219fc2b957d6dadc84f79480` ;
- Portability Runtime `32601811079`, CI `32601811065`, Guided Restore `32601811069`, T2 `32601811078`, Catalog `32601811060`, Patient P7 `32601811091` — SUCCESS.

---

## P3 — Cabinet data portability — CLOSED ✅ — 13 EP

### Goal
Rendre le cabinet portable entre machines/OS sans transporter les secrets liés à la machine source.

### Preuve
- `.dcbundle` chiffré, manifeste/version/intégrité, médias inclus et rechiffrés destination ;
- secrets machine exclus ; prepare/apply/smoke/rollback via Guided Restore ;
- PR `#222` — MERGED ; candidat `89708100838b85f3574674de21882684c98be9f6` ; merge `98fe4440806b38d33cbdfb32eab6e7bc85e9b573` ;
- Runtime `32605929004`, Guided Restore `32605928982`, T2 `32605928994`, Catalog `32605928980`, Patient P7 `32605928983`, CI `32605929015` — SUCCESS.

---

## P4 — Licence & local secrets cross-platform — CLOSED ✅ — 8 EP

### Goal
Conserver identité et données cabinet lors d’une migration sans faire confiance aux secrets/sessions/coffre de la machine source.

### Preuve
- PR `#224` — MERGED ; candidat `3bc7426848d544183f235244ae8eab7b255d1341` ; merge `40cb22d6dddcbae6dee7340dc23956decaf701d8` ;
- Runtime `32610745183`, Guided Restore `32610745196`, Settings P2 `32610745220`, T2 `32610745188`, Catalog `32610745249`, Patient P7 `32610745225`, CI `32610745134` — SUCCESS ;
- closeout : `docs/portability/PORTABILITY_P4_CLOSEOUT.md`.

---

## P5 — Scientific/native runtime portability — CLOSED ✅ — 13 EP

### Goal amendé et verrouillé le 24 août 2026
Prouver la **portabilité du runtime natif/scientifique réellement requis** sur Windows x64 et macOS Apple Silicon, ainsi que le comportement fail-closed lorsque les assets scientifiques externes ne sont pas provisionnés.

### Décision de périmètre
Le modèle céphalométrique historique SOTA 38 points n’a pas été retrouvé comme artefact canonique avec poids + provenance + SHA256. Il n’a pas été reconstruit arbitrairement.

- sélection/qualité/précision clinique du futur moteur céphalo transférées à **Cephalometry NextGen** (`cephalo/nextgen-research`) ;
- aucune équivalence clinique ou numérique des modèles revendiquée par P5 ;
- poids céphalo legacy et panoramique restent externes/non versionnés.

### Preuve
- P5A PR `#228` — MERGED ; run natif `32723535974` — SUCCESS Windows x64 + macOS Apple Silicon ;
- P5 final PR `#233`, candidat `3ee3447e1cd3d92575e3b930abeef8e31061bfb8` ;
- Portability P5 `32750343308` — SUCCESS ; Windows `NATIVE_RUNTIME_GATE=OK` + `SCIENTIFIC_FAIL_CLOSED_GATE=OK` ; macOS `NATIVE_RUNTIME_GATE=OK (Darwin arm64)` + `SCIENTIFIC_FAIL_CLOSED_GATE=OK` + `APPLE_SILICON_GATE=OK` ;
- CI `32750343210`, T2 `32750343211`, Patient P7 `32750343288`, Catalog `32750343395` — SUCCESS.

### Gate A — CORE/NATIVE PORTABLE ✅
Le cœur partagé et les dépendances natives certifiées s’exécutent sur Windows x64 et macOS Apple Silicon selon le contrat P5 amendé. **Cette gate n’est pas une certification de précision clinique des modèles.**

---

## P6 — Industrialized Windows packaging — CLOSED ✅ — 8 EP

### Goal
Rendre la distribution Windows déterministe, reproductible et installable en préservant explicitement les données cabinet.

### Implémentation vérifiée
- `DigitalCrown.spec` est le builder frozen autoritaire utilisé par la certification ; `scripts/build_exe.py` est explicitement quarantainé par le static contract via `LEGACY_BUILDER_DISABLED` ;
- PyInstaller `6.16.0` est piné dans `backend/requirements-p6-windows.txt` ;
- frontend construit via `npm ci` puis build ;
- ressources requises contrôlées fail-closed ; `.env`, `firebase_creds.json` et poids scientifiques non qualifiés sont interdits dans le bundle ;
- source de version unique `VERSION`, métadonnées Windows générées et version Inno paramétrée ;
- dépendances runtime packagées cohérentes (`pip check`) et imports critiques restaurés ;
- Inno Setup `6.7.3` téléchargé depuis la release officielle, SHA256 vérifié et signature éditeur Inno validée avant compilation ;
- frozen self-test et installed self-test : `status=ok`, `scientific_capabilities=FAIL_CLOSED_NO_WEIGHTS`, aucun poids scientifique non qualifié ;
- install propre, runtime `/health`, reinstall/upgrade et uninstall réussissent sur `windows-2025` ;
- sentinel de données cabinet préservé après uninstall ;
- runtime `console=False` journalise sur fichier et Uvicorn n’installe pas de handlers console dans le binaire frozen.

### Authenticode produit
Le chemin de signature produit est intégré et vérifie signature + timestamp lorsqu’un certificat `WINDOWS_CODESIGN_PFX_B64` est disponible. Sur le candidat P6 certifié, aucun certificat de distribution n’était provisionné : **`P6_AUTHENTICODE=NOT_CONFIGURED`**. L’installateur exact uploadé est non signé ; aucune signature produit n’est revendiquée.

### Preuve exacte
- PR `#259` ; candidat produit certifié `6eea148ceede740ea4646023e5f3aa58ea1ee8d1` ;
- P6 Windows Packaging `32999393374`, job `98276906459` — SUCCESS ;
- toutes les étapes produit critiques 5–17 — SUCCESS, y compris static contract, frozen build/self-test, Inno exact, installer, lifecycle, Authenticode status et artifacts ;
- exact-head regressions : Runtime `32999393381`, T2 `32999393529`, P5 Native `32999393360`, Catalog `32999393394`, P11 `32999393369`, Patient P7 `32999393410`, CI `32999393419`, P8 Hardware `32999393352` — SUCCESS ;
- lifecycle artifact `9618198566`, digest `sha256:a68fbcdc17953a5995c50c1ea6271d710c997aa2a7b6aadcbe286656bde4fb7a` ;
- installer artifact `9618206397`, digest archive `sha256:de9b4a82ef39e51c755be578d04fd65334ad00cfe7c4255cb30104a3697e1398` ;
- `DigitalCrownSetup-1.0.0.exe` SHA256 `24e662dd88a941b7c10017e0c34470a1b4206185852102e79bd624f372163edd` ; PE Certificate Table exacte `offset=0`, `size=0`, cohérente avec `NOT_CONFIGURED` ;
- closeout : `docs/portability/PORTABILITY_P6_CLOSEOUT.md`.

### Limites explicites
- P6 ne certifie pas la précision clinique des moteurs scientifiques ; les poids non qualifiés restent volontairement absents/fail-closed ;
- la distribution Windows signée nécessitera le provisionnement réel du certificat de distribution ;
- P6 ne remplace pas P12/P13 pour la matrice finale ni la certification cabinet réel.

---

## P7 — Native macOS packaging — NEXT — 13 EP

### Goal
Livrer une application macOS normale, signée/notarisée, sans Terminal ni contournement Gatekeeper.

### Scope
`.app` Apple Silicon arm64, ressources/assets, bundle metadata/icône, chemins natifs, permissions, DMG/PKG selon besoin, Developer ID, Hardened Runtime/entitlements, notarisation, stapling, Gatekeeper, clean install/upgrade/uninstall.

### Candidat préparé
- PR `#274` ; HEAD `53563b1b22ddb6905a54c16ca8486412130c3921` ; 1 commit / 3 fichiers ;
- politique scientifique `FAIL_CLOSED_NO_WEIGHTS` ; ancien provisioning de poids supprimé ;
- requirements macOS corrigé vers `-r requirements.txt` ;
- checker Developer ID + Hardened Runtime + secure timestamp ;
- workflow de distribution exige Developer ID, notarisation, stapling et Gatekeeper.

### Gate restant
Le workflow `Portability P7 macOS Distribution Certification` reste `workflow_dispatch` et requiert les credentials Apple. Les checks PR automatiques ne remplacent pas ce run de distribution signé/notarisé.

---

## P8 — Hardware & peripheral compatibility — CLOSED ✅ — 21 EP

### Goal
Classer explicitement chaque périphérique clinique par OS : `SUPPORTED`, `LIMITED`, `FILE-IMPORT` ou `UNSUPPORTED`, sur test réel ou preuve fabricant clairement distinguée.

### Résultat certifié
P8 ferme la **frontière de compatibilité actuelle**, sans inventer de support natif. Aucun périphérique dentaire direct n’est déclaré `SUPPORTED` sans intégration Digital Crown et test device réel.

- 10 surfaces obligatoires classées Windows/macOS ;
- RVG, panoramique, céphalo et caméra intra-orale clinique : `FILE-IMPORT` ;
- QR pairing et imprimante standard : `LIMITED` avec limites explicites ;
- DICOM/PACS, TWAIN/WIA/Image Capture, USB/serial/vendor SDK et scanner STL/PLY : `UNSUPPORTED` en acquisition/intégration directe ;
- tout futur passage à `SUPPORTED` exige modèle/firmware/driver, preuve fabricant, adapter Digital Crown, tests acquisition/reconnexion/erreurs et preuve device réelle sur chaque OS revendiqué.

### Preuve exacte
- candidat `5c583761f204c6c0de7cd9c2c60976c7dcf7e23b` ; 1 commit / 5 fichiers ;
- PR `#275` — MERGED ; merge `b5e1ea41fa039cc174da5d1690f6d9bd3332728b` ;
- Portability P8 Hardware Compatibility Contract `33057900937`, job `98469174459` — SUCCESS exact-head ;
- P12 Certification Matrix Prep `33057900997` — SUCCESS exact-head ;
- closeout : `docs/portability/P8_HARDWARE_COMPATIBILITY_MATRIX.md` ;
- aucun Vercel.

---

## P9 — Backup, Recovery & Disaster Recovery — PLANNED — 8 EP

### Goal
Faire en sorte que la perte d’un ordinateur n’implique jamais la perte du cabinet : backup, intégrité, chiffrement, restore, interruptions, disque insuffisant, corruption et récupération inter-OS.

### État préparé
Le moteur déterministe est déjà présent : `.dcbundle.partial` → vérification → promotion atomique, SHA-256 sidecar, rétention des générations vérifiées, Guided Restore, comportements disque plein/interruption/destination indisponible et fail-closed PostgreSQL portable non supporté.

### Gate restant
P9 ne ferme qu’après destination externe réelle + restauration sur cible packagée propre + preuve inter-OS applicable. Cette dernière preuve dépend du package macOS P7.

---

## P10 — Cross-platform Update Engine — PLANNED — 13 EP

### Goal
Updates authentifiées avec checksum/signature, rescue point, migration, health post-update et rollback automatique sur Windows/macOS.

> La branche `portability/p10-update-engine` sert actuellement aussi de base d’intégration. Cela ne crédite ni ne ferme P10.

### État préparé
Le secure-core vérifie manifestes Ed25519, séquence anti-rollback/replay, expiration/temps de confiance, cible OS/architecture, HTTPS, taille + SHA-256 et rescue point immuable. L’apply reste volontairement `apply_certified=false` jusqu’aux installateurs certifiés P6/P7.

---

## P11 — Launcher & Recovery UX — CLOSED ✅ — 8 EP

### Goal
Exposer des états de lifecycle/récupération vrais et actionnables sans console.

### Preuve
- BEFORE run `32780649466` — SUCCESS ; artifact `9539649740` ; mockup verrouillé avant implémentation ;
- candidat final `cbaf21a066fb6b8b70f4c9d6b3ec1a950cda890b` ; PR `#241` ;
- P11 final `32783305559` — SUCCESS ; AFTER artifact `9540590729`, digest `sha256:47ffdcee25d9237ac89f9665c2a0d34603005b8b2786412b63eb30f2a0457cf1` ;
- 15/15 AFTER captures sur 1440 / 1024 / 768 / 430 / 390 ; zéro overflow ; zéro erreur runtime/page ;
- score Startup **9,3/10**, Guided Restore **9,1/10** ;
- merge `455e7603c78b0139c0b39e217bed768bfe1186e7` ; closeout `docs/portability/P11_LAUNCHER_RECOVERY_UX.md` ; aucun Vercel.

---

## P12 — CI & certification matrix — PREPARED — 13 EP — 0 EP crédité

### Goal
Certifier les artefacts Windows/macOS et empêcher les régressions plateforme : runtime, frozen build, models/assets, backup/restore, packaging, update et tests raisonnables.

### Préparation vérifiée
- candidat `00b837c52be3a7fc332661c05d2689fd05b0b199` ; PR `#270` ; merge `8e1d0d6d9c676b39d40f75a18fc0db168dcc5257` ;
- P12 Certification Matrix Prep `33020917211`, job `98350792934` — SUCCESS ;
- exact-head T2 `33020917126`, Patient P7 `33020917151`, Catalog `33020917139`, CI `33020917134` — SUCCESS ;
- matrice préparatoire : `docs/portability/P12_CERTIFICATION_MATRIX.md` ;
- P12 reste ouvert et 0 EP sont crédités tant que P7/P9/P10 et la matrice finale cross-platform ne sont pas certifiés.

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

P11 et P8 ont été fermés hors ordre sans contourner leurs critères. Le Next canonique reste **P7**, qui débloque les preuves finales P9/P10/P12/P13.

## État courant

- P0–P6 : **CLOSED ✅** ;
- P7 : **NEXT / candidat préparé** ;
- P8 : **CLOSED ✅** ;
- P9–P10 : **PLANNED / moteurs préparés, gates finales dépendantes de P7** ;
- P11 : **CLOSED ✅** ;
- P12 : **PREPARED — 0 EP crédité** ;
- P13–P14 : **PLANNED** ;
- validé : **102 / 162 EP = 63,0 %** ;
- aucun EP partiel n’est crédité pour un lot ouvert ;
- Cephalometry NextGen est un chantier scientifique séparé et n’est pas compté dans les 162 EP ;
- aucun Vercel ;
- Next exact : **P7 Native macOS packaging** — obtenir le run de distribution macOS signé/notarisé sur `53563b1b22ddb6905a54c16ca8486412130c3921`, inspecter artifacts/signing/notarisation/lifecycle, puis enchaîner P9 → P10 → P12 → P13.
