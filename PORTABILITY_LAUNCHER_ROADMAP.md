# Portability & Launcher — roadmap canonique

Dernière mise à jour vérifiée : 2026-08-26.

> **Source de vérité unique du chantier.** `docs/PORTABILITY_LAUNCHER_ROADMAP.md` est déprécié et renvoie ici.

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
- Le comportement OS-spécifique passe par des adapters/frontières dédiés.
- Données cabinet et identité/secrets machine sont des contrats distincts.
- Une dépendance native importable n’est pas, à elle seule, une preuve scientifique.
- Les poids scientifiques non redistribuables ne vont ni dans le repo produit public ni dans une Release publique.
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

Effort Points = complexité relative, pas durée. Aucun EP partiel n’est crédité pour un lot ouvert.

---

## P0 — Baseline & portability contract — CLOSED ✅ — 5 EP

### Goal
Rendre explicite la frontière de portabilité avant modification d’architecture.

### Preuve
- `docs/portability/PORTABILITY_P0_BASELINE.md` ;
- dépendances OS, chemins, runtime, secrets, natifs/scientifiques et surfaces hardware classés.

---

## P1 — OS abstraction layer — CLOSED ✅ — 13 EP

### Goal
Retirer du cœur partagé les primitives Windows/macOS directes nécessaires au runtime.

### Preuve
- PR `#219` — MERGED ;
- candidat `31f7c612327c48ead478b18f224875dba6313c61` ; merge `2907b3d1ea529dde27468f27ce5835d2655275e9` ;
- Portability P1 `32599659706` — SUCCESS Windows/macOS/Ubuntu ;
- CI `32599659683`, Guided Restore `32599659687`, T2 `32599659693` — SUCCESS.

---

## P2 — Runtime Supervisor / Launcher V2 — CLOSED ✅ — 13 EP

### Goal
Créer une autorité unique et cross-platform du lifecycle local.

### Preuve
- PR `#220` — MERGED ;
- candidat `0b6071b663162575efe0de40c411a8ff29763d7a` ; merge `19bf42b61001c77c219fc2b957d6dadc84f79480` ;
- Portability Runtime `32601811079` — SUCCESS Windows/macOS/Ubuntu ;
- CI `32601811065`, Guided Restore `32601811069`, T2 `32601811078`, Catalog `32601811060`, Patient P7 `32601811091` — SUCCESS.

---

## P3 — Cabinet data portability — CLOSED ✅ — 13 EP

### Goal
Rendre le cabinet portable entre machines/OS sans transporter les secrets liés à la machine source.

### Preuve
- `.dcbundle` chiffré, intégrité, export SQLCipher, médias, exclusion des secrets, rollback Guided Restore ;
- PR `#222` — MERGED ; candidat `89708100838b85f3574674de21882684c98be9f6` ; merge `98fe4440806b38d33cbdfb32eab6e7bc85e9b573` ;
- Runtime `32605929004`, Guided Restore `32605928982`, T2 `32605928994`, Catalog `32605928980`, Patient P7 `32605928983`, CI `32605929015` — SUCCESS.

---

## P4 — Licence & local secrets cross-platform — CLOSED ✅ — 8 EP

### Goal
Conserver identité et données cabinet lors d’une migration sans faire confiance aux secrets/sessions/coffre de la machine source.

### Preuve
- PR `#224` — MERGED ; candidat `3bc7426848d544183f235244ae8eab7b255d1341` ; merge `40cb22d6dddcbae6dee7340dc23956decaf701d8` ;
- Runtime `32610745183`, Guided Restore `32610745196`, Settings P2 `32610745220`, T2 `32610745188`, Catalog `32610745249`, Patient P7 `32610745225`, CI `32610745134` — SUCCESS.

---

## P5 — Scientific/native runtime portability — CLOSED ✅ — 13 EP

### Goal verrouillé le 24 août 2026
Prouver la **portabilité du runtime natif/scientifique réellement requis** sur Windows x64 et macOS Apple Silicon et son comportement fail-closed en absence d’assets scientifiques.

### Boundary
P5 ne revendique aucune précision clinique de modèle. La sélection/remplacement scientifique est traitée séparément ; les assets externes sont provisionnés dans P6/P7 puis certifiés P12/P13.

### Preuve
- P5A PR `#228` — MERGED ; run natif `32723535974` — SUCCESS Windows x64 + macOS ARM64 ;
- P5 final PR `#233`, candidat `3ee3447e1cd3d92575e3b930abeef8e31061bfb8` ;
- run `32750343308` — SUCCESS ; Windows `NATIVE_RUNTIME_GATE=OK`, macOS `NATIVE_RUNTIME_GATE=OK` + `APPLE_SILICON_GATE=OK` ;
- CI `32750343210`, T2 `32750343211`, Patient P7 `32750343288`, Catalog `32750343395` — SUCCESS.

---

## P6 — Industrialized Windows packaging — ACTIVE — 8 EP

### Goal
Rendre la distribution Windows déterministe, reproductible et installable en préservant explicitement les données cabinet.

### EP
**0/8 EP crédité.** P6 n’est pas fermé tant que le build/install/upgrade/uninstall et les assets requis ne sont pas certifiés.

### Sous-lot scientifique actif
`P6 Scientific Assets Refresh` est un prérequis de recherche de P6. Il **ne remplace pas P6** et ne gagne aucun EP Portability à lui seul.

#### Céphalométrie — technique verrouillée
- candidat : `DC-Ceph-UNet29Q4 / Aariz v1` ;
- training scellé `32876308676` — SUCCESS ;
- direct-20 test : MRE `1.232893 mm`, SDR2 `83.1333%`, SDR4 `97.2667%` ;
- ONNX : SHA256 `809f1d3d2347d2a34f57d4a3415bb319c29f8a25c325d41160e5f28d4e5dadad`, `7,624,307 bytes` ;
- bridge de récupération exacte `32911022192` — SUCCESS et SHA/size vérifiés ;
- protocole clinique préparé : `docs/P6_CEPHALOMETRY_CLINICAL_VALIDATION_PROTOCOL.md` ;
- **aucune revendication clinique** ; `Occ_Ant`/`Occ_Post` restent absents, Wits fail-closed.

#### Rétention privée céphalo — BLOQUÉE HUMAIN
- repo cible : `hraaaaf/DigitalCrown-assets` — PRIVATE ;
- branche : `training/p6-ceph-unet29` ;
- le binaire exact est récupérable et vérifié ;
- run de transfert privé `32911260037` : échec explicite au premier gate ;
- preuve log : `P6_ASSET_TOKEN secret missing` ;
- aucune étape de clone/transfert privé n’a été exécutée ;
- la rétention privée n’est donc **pas** encore créditée.

Le blocage n’est plus infrastructurel ni scientifique : il manque le secret GitHub Actions `P6_ASSET_TOKEN` sur le repo produit, avec accès au repo privé `hraaaaf/DigitalCrown-assets`. Le workflow prêt à reprendre est `.github/workflows/p6-ceph-winner-private-retention.yml`.

#### Panoramique — Mendeley V3 first-party fermé
Cible Phase A : **localisation dentaire + numérotation FDI**, sans diagnostic automatique de pathologies.

Probe first-party `10.17632/73n3kz2k4k.3` :
- run inventaire `32910249394` — SUCCESS ;
- run sémantique `32910743873` — SUCCESS ;
- 111 fichiers / `84,254,649` octets ;
- 107 images metadata ; 25 images avec régions ; 772 régions ;
- `annotations.json` SHA256 `b6de2c396cb76758227562798141a00fb5d769f9d8f9eb3919470f4ff23578bd` ;
- 540 régions exposent l’attribut `Teeth`, mais les **540 valeurs sont `""`** ;
- `0` token dentaire, `0` code FDI, `0` région FDI ;
- `direct_fdi_ground_truth_ready=false`.

Le vieux miroir « 3 images » était incomplet. La conclusion FDI reste néanmoins confirmée par la source first-party : **aucune vérité FDI source**. Preuve canonique : `docs/P6_MENDELEY_V3_PROVENANCE_RESULT.md`.

#### Déduplication pano
Sur les 107 images Mendeley V3 : **96 SHA256 uniques / 11 doublons exacts**. Toute future séparation train/validation/test doit être groupée par SHA/source avant split.

### Scope packaging canonique
- un seul builder autoritaire (`DigitalCrown.spec`/PyInstaller ou successeur validé) ;
- toolchain pinée ; frontend via `npm ci` ;
- assets contrôlés et fail-closed ;
- version unique ;
- Inno Setup install/upgrade/uninstall + conservation données ;
- signature Authenticode/timestamp lorsque certificat disponible ;
- smoke frozen + installateur sur Windows propre.

### État packaging vérifié
- PR `#242` — OPEN/DRAFT, mergeable ; branche `portability/p6-windows-packaging-resume` ; HEAD publié `90b1262cb13b22172d6d0d2f36aa6eb96d360cdf` ;
- dernier run lourd `32803814701` — FAILURE après static gate + frontend build verts ;
- candidat préparé `4501ad8d167c65a64e174d923e6f1d3a36b14399` existe et est exactement `1` commit devant le HEAD PR ;
- il corrige `protobuf==5.29.6`, ajoute `pip check` et un gate de repo scientifique privé ;
- **ne pas pousser/lancer ce candidat lourd maintenant** : son provisioner attend encore les assets legacy `panoramic_model.onnx` + `cephld_cca/ceph_weights.pth`, alors que le remplacement scientifique n’est pas encore fermé. Le provisioner doit être réconcilié avec le set final, pas alimenté avec des poids hérités non prouvés.

### Succès P6
Un artefact Windows exact est reconstruit, installé, mis à niveau et désinstallé sur machine propre sans fuite de secrets ni perte de données cabinet, avec les assets scientifiques réellement autorisés et leur comportement fail-closed vérifié.

### Next exact
1. **Human gate : créer `P6_ASSET_TOKEN`** dans les Actions secrets de `hraaaaf/Digital_crown`, avec accès lecture/écriture minimal à `hraaaaf/DigitalCrown-assets`.
2. Rejouer `P6 Ceph Winner Private Retention` et exiger `P6_PRIVATE_RETENTION=OK` + SHA exact privé.
3. Figer le pool pano rights-cleared/dédupliqué puis appliquer `docs/P6_PANORAMIC_FDI_ANNOTATION_PROTOCOL.md` ; aucune géométrie automatique n’est vérité terrain.
4. Après FDI humain fermé, qualifier/train le moteur Phase A puis Windows x64 + macOS ARM64.
5. Réconcilier le provisioner P6 avec le **set scientifique final** ; ne pas réintroduire CephLD/panoramic legacy par commodité.
6. Seulement alors avancer PR `#242` vers un candidat final et lancer **1 run Windows lourd**.

---

## P7 — Native macOS packaging — PLANNED — 13 EP

### Goal
Livrer une application macOS Apple Silicon normale, signée/notarisée, sans Terminal ni contournement Gatekeeper.

---

## P8 — Hardware & peripheral compatibility — PLANNED — 21 EP

### Goal
Classer chaque périphérique clinique par OS : `SUPPORTED`, `LIMITED`, `FILE-IMPORT` ou `UNSUPPORTED`, sur test réel ou preuve fabricant explicitement distinguée.

---

## P9 — Backup, Recovery & Disaster Recovery — PLANNED — 8 EP

### Goal
Faire en sorte que la perte d’un ordinateur n’implique jamais la perte du cabinet : backup, intégrité, chiffrement, restore, interruptions, disque insuffisant, corruption et récupération inter-OS.

---

## P10 — Cross-platform Update Engine — PLANNED — 13 EP

### Goal
Updates authentifiées avec checksum/signature, rescue point, migration, health post-update et rollback automatique sur Windows/macOS.

---

## P11 — Launcher & Recovery UX — PLANNED — 8 EP

### Goal
Exposer des états lifecycle/récupération vrais et actionnables sans console. Tout changement visuel suit BEFORE → Goal → mockup → implémentation → AFTER → score.

---

## P12 — CI & certification matrix — PLANNED — 13 EP

### Goal
Certifier les artefacts Windows/macOS et empêcher les régressions : runtime, frozen build, models/assets, backup/restore, packaging, update et tests raisonnables.

---

## P13 — Real cabinet certification — PLANNED — 13 EP

### Goal
Prouver le flow cabinet critique sur machines propres Windows/macOS et la migration croisée, avec scénarios d’échec contrôlés.

---

## P14 — Closeout & permanent compass — PLANNED — 5 EP

### Goal
Fermer le chantier avec docs, matrices OS/hardware, guides installation/recovery/update/troubleshooting, gouvernance et preuve finale cohérents avec le HEAD certifié.

---

## État courant

- P0–P5 : **CLOSED ✅** ;
- P6 : **ACTIVE — 0/8 EP** ;
- P7–P14 : **PLANNED** ;
- validé : **65 / 162 EP = 40,1 %** ;
- aucun EP partiel crédité ;
- aucun Vercel ;
- blocage réel actuel : **secret GitHub Actions `P6_ASSET_TOKEN` absent** pour la rétention privée céphalo ;
- après ce human gate : rétention privée → FDI clinique pano → set scientifique final → packaging Windows.
