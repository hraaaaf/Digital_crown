# Portability & Launcher — roadmap canonique

Dernière mise à jour vérifiée : 2026-08-28.

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
| P10 — Cross-platform Update Engine | 13 EP | ACTIVE — 0 EP |
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
- `docs/portability/PORTABILITY_P0_BASELINE.md`.

---

## P1 — OS abstraction layer — CLOSED ✅ — 13 EP

### Goal
Retirer du cœur partagé les primitives Windows/macOS directes nécessaires au runtime.

### Preuve
- PR `#219` — MERGED ; merge master `2907b3d1ea529dde27468f27ce5835d2655275e9`.

---

## P2 — Runtime Supervisor / Launcher V2 — CLOSED ✅ — 13 EP

### Goal
Créer une autorité unique et cross-platform du lifecycle local.

### Preuve
- PR `#220` — MERGED ; merge master `19bf42b61001c77c219fc2b957d6dadc84f79480`.

---

## P3 — Cabinet data portability — CLOSED ✅ — 13 EP

### Goal
Rendre le cabinet portable entre machines/OS sans transporter les secrets liés à la machine source.

### Preuve
- PR `#222` — MERGED ; merge `98fe4440806b38d33cbdfb32eab6e7bc85e9b573` ;
- closeout : `docs/portability/PORTABILITY_P3_CLOSEOUT.md`.

---

## P4 — Licence & local secrets cross-platform — CLOSED ✅ — 8 EP

### Goal
Conserver identité et données cabinet lors d’une migration sans faire confiance aux secrets/sessions/coffre de la machine source.

### Preuve
- PR `#224` — MERGED ; merge `40cb22d6dddcbae6dee7340dc23956decaf701d8` ;
- closeout : `docs/portability/PORTABILITY_P4_CLOSEOUT.md`.

---

## P5 — Scientific/native runtime portability — CLOSED ✅ — 13 EP

### Goal
Prouver la portabilité du runtime natif/scientifique requis sur Windows x64 et macOS Apple Silicon, avec comportement fail-closed lorsque les assets scientifiques externes ne sont pas provisionnés.

### Preuve
- candidat `3ee3447e1cd3d92575e3b930abeef8e31061bfb8` ;
- Portability P5 `32750343308` — SUCCESS Windows + macOS Apple Silicon ;
- aucune équivalence clinique non démontrée n’est revendiquée.

---

## P6 — Industrialized Windows packaging — CLOSED ✅ — 8 EP

### Goal
Rendre la distribution Windows déterministe, reproductible et installable en préservant explicitement les données cabinet.

### Preuve
- PR `#259` ; candidat certifié `6eea148ceede740ea4646023e5f3aa58ea1ee8d1` ;
- P6 `32999393374` — SUCCESS ;
- closeout : `docs/portability/PORTABILITY_P6_CLOSEOUT.md`.

### Limite distribution production
Le packaging P6 est fermé, mais le certificat Authenticode production n’est pas provisionné. La distribution signée exige `WINDOWS_CODESIGN_PFX_B64` + `WINDOWS_CODESIGN_PASSWORD`; l’évidence existante reste `P6_AUTHENTICODE=NOT_CONFIGURED`.

---

## P7 — Native macOS packaging — NEXT — 13 EP

### Goal
Livrer une application macOS normale, signée/notarisée, sans Terminal ni contournement Gatekeeper.

### Candidat préparé
- PR `#274` ; HEAD `53563b1b22ddb6905a54c16ca8486412130c3921` ;
- workflow de distribution `workflow_dispatch` exige Developer ID, notarisation, stapling, Gatekeeper et lifecycle réel.

### Gate restant
Secrets Apple requis : `MACOS_DEVELOPER_ID_P12_B64`, `MACOS_DEVELOPER_ID_P12_PASSWORD`, `MACOS_CODESIGN_IDENTITY`, `APPLE_NOTARY_KEY_P8_B64`, `APPLE_NOTARY_KEY_ID`, `APPLE_NOTARY_ISSUER_ID`, `P6_SCIENTIFIC_BUNDLE_SHA256`.

---

## P8 — Hardware & peripheral compatibility — CLOSED ✅ — 21 EP

### Goal
Classer explicitement chaque périphérique clinique par OS sans inventer de support natif.

### Preuve
- candidat `5c583761f204c6c0de7cd9c2c60976c7dcf7e23b` ;
- PR `#275` — MERGED ; merge `b5e1ea41fa039cc174da5d1690f6d9bd3332728b` ;
- matrix : `docs/portability/P8_HARDWARE_COMPATIBILITY_MATRIX.md`.

---

## P9 — Backup, Recovery & Disaster Recovery — PLANNED — 8 EP

### Goal
Faire en sorte que la perte d’un ordinateur n’implique jamais la perte du cabinet.

### Gate restant
Destination externe réelle + restauration sur cible packagée propre + preuve inter-OS applicable. Cette dernière preuve dépend du package macOS P7.

---

## P10 — Cross-platform Update Engine — ACTIVE — 13 EP — 0 EP crédité

### Goal
Updates authentifiées avec signature, rescue point, health post-update et rollback automatique sur Windows/macOS.

### Preuve actuelle
- branche `portability/p10-update-engine`, PR `#239` ;
- production trust root : deux clés publiques Ed25519 réelles `primary` + `recovery`, privées conservées hors ligne ;
- HEAD produit certifié `e4d16ffdbf4bf91cf9315c00ab1ba611dbf654ed` ;
- P10 #49 `33195861612` — **SUCCESS** : secure-core + windows-worker + lifecycle packagé ;
- artifact `9696388069`, digest `sha256:5af1d77b184f0a744bf51dd57f1171c2ddb6b29b26b44c26a4280b6312cfb1d5` ;
- merge proof `05d4ec176e39768521bbfba45746d5c7e38ca67d`, exact merge du candidat dans la base P9 ;
- Windows réel : `1.0.0 → 1.0.1`, self-test, health, finalization, package rollback, SQLCipher DB rescue, interruption recovery et target-start/runtime-bind failure rollback verts ;
- contrat/évidence : `docs/portability/P10_UPDATE_ENGINE.md` ;
- cérémonie/rotation : `docs/portability/P10_UPDATE_SIGNING_KEY_CEREMONY.md`.

### Gates restants
1. P6 Windows production signé + timestampé et apply réel certifié ;
2. P7 macOS signé/notarisé/staplé/Gatekeeper + lifecycle/update réel ;
3. Windows + macOS clean-machine ;
4. closeout cohérence/evidence.

P10 reste 0/13 EP tant que ces gates ne sont pas tous satisfaits.

---

## P11 — Launcher & Recovery UX — CLOSED ✅ — 8 EP

### Preuve
- PR `#241` ; merge `455e7603c78b0139c0b39e217bed768bfe1186e7` ;
- closeout : `docs/portability/P11_LAUNCHER_RECOVERY_UX.md`.

---

## P12 — CI & certification matrix — PREPARED — 13 EP — 0 EP crédité

### Preuve
- PR `#270` ; merge `8e1d0d6d9c676b39d40f75a18fc0db168dcc5257` ;
- matrix : `docs/portability/P12_CERTIFICATION_MATRIX.md`.

### Gate restant
P12 reste 0 EP tant que P7/P9/P10 et la matrice finale cross-platform ne sont pas certifiés.

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

P11, P8 et le travail parallèle P10 ont avancé hors ordre sans contourner leurs critères. Le Next canonique reste **P7**, qui débloque les preuves finales P9/P10/P12/P13.

## État courant

- P0–P6 : **CLOSED ✅** ;
- P7 : **NEXT / candidat préparé / credentials Apple requis** ;
- P8 : **CLOSED ✅** ;
- P9 : **PLANNED / moteur préparé** ;
- P10 : **ACTIVE / trust + lifecycle Windows certifiés / 0 EP** ;
- P11 : **CLOSED ✅** ;
- P12 : **PREPARED — 0 EP** ;
- P13–P14 : **PLANNED** ;
- validé : **102 / 162 EP = 63,0 %** ;
- aucun EP partiel n’est crédité pour un lot ouvert ;
- aucun Vercel ;
- Next canonique : **P7 Native macOS packaging** ;
- Next P10 : provisionner Authenticode Windows, certifier artifact signé/apply, puis P7 macOS et clean-machine.
