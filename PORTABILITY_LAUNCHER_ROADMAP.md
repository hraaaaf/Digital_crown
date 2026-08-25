# Portability & Launcher — roadmap canonique

Dernière mise à jour vérifiée : 2026-08-26.

> **Source de vérité unique du chantier.** `docs/PORTABILITY_LAUNCHER_ROADMAP.md` est déprécié et renvoie ici.

## Goal global

Un seul Digital Crown local-first, cœur partagé Windows/macOS, installable, restaurable, updatable et certifiable avec données cabinet, licence/secrets, assets scientifiques et hardware maîtrisés.

## Doctrine

- un cœur React/FastAPI commun ;
- frontières OS explicites ;
- données cabinet distinctes des secrets machine ;
- aucun asset scientifique non autorisé dans le repo produit public ;
- une dépendance importable ou un benchmark technique n’est pas une preuve clinique ;
- capacité scientifique non qualifiée = indisponible/fail-closed, jamais simulée ;
- aucun Vercel sans autorisation explicite.

## Effort canonique

| Lot | EP | État |
|---|---:|---|
| P0 — Baseline & portability contract | 5 | CLOSED ✅ |
| P1 — OS abstraction layer | 13 | CLOSED ✅ |
| P2 — Runtime Supervisor / Launcher V2 | 13 | CLOSED ✅ |
| P3 — Cabinet data portability | 13 | CLOSED ✅ |
| P4 — Licence, secrets & machine identity | 8 | CLOSED ✅ |
| P5 — Scientific/native runtime portability | 13 | CLOSED ✅ |
| P6 — Industrialized Windows packaging | 8 | ACTIVE — 0/8 EP |
| P7 — Native macOS packaging | 13 | PLANNED |
| P8 — Hardware & peripherals | 21 | PLANNED |
| P9 — Backup / Recovery / DR | 8 | PLANNED |
| P10 — Cross-platform Update Engine | 13 | PLANNED |
| P11 — Launcher & Recovery UX | 8 | PLANNED |
| P12 — CI & certification matrix | 13 | PLANNED |
| P13 — Real cabinet certification | 13 | PLANNED |
| P14 — Closeout | 5 | PLANNED |
| **TOTAL** | **162** | |

Aucun EP partiel n’est crédité pour un lot ouvert.

## P0–P5 — état fermé

- P0 : baseline de portabilité fermée.
- P1 : PR `#219`, Portability `32599659706` SUCCESS Windows/macOS/Ubuntu.
- P2 : PR `#220`, Runtime `32601811079` SUCCESS Windows/macOS/Ubuntu.
- P3 : PR `#222`, bundle cabinet/restore inter-OS ; CI `32605929015` SUCCESS.
- P4 : PR `#224`, secrets/licence/restore cross-platform ; CI `32610745134` SUCCESS.
- P5 : PR `#233`, candidat `3ee3447e1cd3d92575e3b930abeef8e31061bfb8`, natif `32750343308` SUCCESS Windows x64 + macOS ARM64, CI `32750343210` SUCCESS.

Validé avant P6 : **65 EP**.

---

# P6 — Industrialized Windows packaging — ACTIVE — 0/8 EP

## Goal

Produire un artefact Windows déterministe, installable/upgradeable/uninstallable sur machine propre, sans fuite de secrets ni perte de données, tout en laissant les capacités scientifiques non qualifiées explicitement fail-closed.

## Décision scientifique de packaging

P6 **n’embarque aucun poids scientifique non qualifié**.

Raison vérifiée :
- le poids panoramique historique n’a pas de provenance/licence de redistribution fermée ;
- le gagnant céphalo `DC-Ceph-UNet29Q4 / Aariz v1` est un candidat technique 29 points / 512 grayscale, tandis que le runtime SOTA produit actuel attend 38 points / 1024 couleur ;
- le substituer silencieusement sous `model.onnx` serait scientifiquement et techniquement faux.

Le package doit donc rester exploitable avec ces capacités indisponibles, et le self-test frozen doit prouver cette vérité.

## Candidat Windows final

Ancienne PR `#242` : **CLOSED — SUPERSEDED**, non mergée.

Certification active :
- PR `#259` — OPEN/DRAFT ;
- branche `portability/p6-windows-packaging-final-20260826` ;
- HEAD final `e8aaa2cfd2b68bc84a777c2e07fa4e8ee7dee5fd` ;
- run exact-head `32912896028` ;
- état au dernier contrôle : **QUEUED**.

Contrat du candidat :
- `DigitalCrown.spec` ne collecte plus `panoramic_model.onnx`, `ceph_weights.pth` ni poids SOTA ;
- `backend/scientific_assets.json` reste la vérité de lifecycle : `cephalo_sota=deferred`, `cephalo_legacy=external`, `panoramic=external` ;
- le self-test rejette la présence de poids scientifiques connus non qualifiés ;
- marqueurs attendus : `P6_SCIENTIFIC_PACKAGE_POLICY=FAIL_CLOSED_NO_WEIGHTS` et `P6_SCIENTIFIC_CAPABILITIES=FAIL_CLOSED` ;
- `protobuf==5.29.6` ;
- `python -m pip check` obligatoire ;
- aucun token inter-repo ni Release scientifique requis pour le build P6 ;
- aucun Vercel.

### Preuves requises pour fermer P6

1. static packaging contract PASS ;
2. frontend production build PASS ;
3. installation Python + `pip check` PASS ;
4. PyInstaller frozen build + package self-test PASS ;
5. install propre + runtime health + reinstall/upgrade + uninstall PASS ;
6. sentinel données cabinet préservé ;
7. statut Authenticode enregistré honnêtement (`SUCCESS` ou `NOT_CONFIGURED`) ;
8. installer artifact retenu ;
9. closeout canonique cohérent avec le HEAD certifié ;
10. opérations Git prévues terminées avant crédit des 8 EP.

---

## Sous-lot P6 Scientific Assets Refresh

Ce sous-lot est un prérequis/research track de P6, pas un lot EP autonome. Il ne bloque plus le packaging Windows fail-closed.

### Céphalométrie — technique verrouillée

`DC-Ceph-UNet29Q4 / Aariz v1`

- training `32876308676` — SUCCESS ;
- evidence commit `1da113b8776aa2b57e42ac194f12b7a48b01558c` ;
- dataset Aariz v1, DOI `10.6084/m9.figshare.27986417.v1`, CC BY 4.0 ;
- dataset SHA256 `d9fa872b36065dac9615cfcad0c7512c450fe2d86a1839cdec4cbe001def33ea` ;
- ONNX SHA256 `809f1d3d2347d2a34f57d4a3415bb319c29f8a25c325d41160e5f28d4e5dadad` ;
- taille `7,624,307 bytes` ;
- contrat `[1,1,512,512] -> [1,29,128,128]`, opset 17 ;
- direct-20 held-out : MRE `1.232893 mm`, SDR2 `83.1333%`, SDR4 `97.2667%` ;
- `clinical_claim=false` ;
- `Occ_Ant` / `Occ_Post` absents ; Wits fail-closed ;
- protocole clinique : `docs/P6_CEPHALOMETRY_CLINICAL_VALIDATION_PROTOCOL.md`.

### Récupération binaire exacte

- bridge `32911633368` — SUCCESS ;
- artifact `9586717545` ;
- digest artifact `sha256:3ed73e3d39325d5b880e72264ac2a8a25996aa5eaef7bedd1a14b76d9b03ec55` ;
- SHA et taille du modèle revalidés avant artifact.

La récupération exacte est fermée. La **rétention privée** reste un archivage scientifique séparé et non prouvé.

### Rétention privée — OPEN / external GitHub gate

Repo cible : `hraaaaf/DigitalCrown-assets`, branche `training/p6-ceph-unet29`.

- ancien transfert public `32911260037` : échec avant copie, `P6_ASSET_TOKEN secret missing` ;
- smoke privé minimal : commit `7022d34608be268c3b364963bd2de833b53ecbad` ;
- run privé `32911736812` : FAILURE avant toute step, `steps=null`.

Conclusion : ne pas relancer aveuglément le workflow privé. Cette rétention peut être faite manuellement puis SHA-vérifiée lorsque le canal privé est utilisable. **Elle ne bloque plus P6 Windows**, qui ne distribue aucun poids non qualifié.

---

## Panoramique Phase A

Cible : **localisation dentaire + FDI**, pas diagnostic automatique de pathologies.

### Mendeley V3 first-party

Dataset `73n3kz2k4k.3`, DOI `10.17632/73n3kz2k4k.3`, record CC BY 4.0.

- inventaire `32910249394` — SUCCESS ;
- audit sémantique `32910743873` — SUCCESS ;
- 111 fichiers / `84,254,649` octets ;
- 107 images metadata ;
- 25 images avec géométrie source ;
- 772 régions ;
- 540 attributs `Teeth`, **540 valeurs `""`** ;
- 0 code FDI / 0 région FDI ;
- `direct_fdi_ground_truth_ready=false`.

Décision : source image/géométrie commercialement exploitable selon le record first-party, mais **jamais vérité FDI directe**.

### Pack FDI clinicien — READY

- builder `scripts/p6_mendeley_fdi_annotation_pack.py` ;
- workflow `.github/workflows/p6-mendeley-fdi-annotation-pack.yml` ;
- HEAD `6f7614f23b793dd6804d6c7d770f62928a3a09f0` ;
- run `32912109975` — SUCCESS ;
- artifact `9586914372` ;
- digest `sha256:a72599acf4b96b3d8519f174614feca3cec011dddce0dcc594f01ac4c656ea09` ;
- 107 images ; 25 avec propositions géométriques ; 772 propositions ;
- FDI clinicien attribué `0` ; orientation confirmée `0` ; split attribué `0` ;
- ledger SHA256 `42950b89eb2856b8b4c9302837ea95a170aec5b11257d15a06ed3ae619122cad` ;
- source manifest SHA256 `f59fb925d9e33123300fcd984edb6091e6353205e6b9ef5b0a549a4b5ce8cebd`.

Protocole : `docs/P6_PANORAMIC_FDI_ANNOTATION_PROTOCOL.md`.

**Human clinical gate réel** : orientation → validation/édition géométrie → FDI → déduplication/splits → double review test → adjudication. Aucun entraînement pano lourd avant ces gates.

---

## Next exact P6

1. Ne faire **aucun micro-push** sur `portability/p6-windows-packaging-final-20260826` pendant le run `32912896028`.
2. Quand son résultat devient nécessaire : inspecter une fois le run exact-head.
3. Si FAILURE : diagnostic précis → correction ciblée → test → un nouveau run seulement si nécessaire.
4. Si SUCCESS : vérifier logs/steps + artifact installateur + fail-closed markers + data sentinel + signing status.
5. Puis closeout P6 : docs canoniques → cohérence → PR #259 → merge selon preuves → post-merge → créditer **8 EP** seulement après fermeture réelle.
6. En parallèle séparé : annotation clinique du pack pano ; archivage privé céphalo quand le canal privé est utilisable.

---

## P7–P14

- P7 : packaging macOS natif signé/notarisé.
- P8 : matrice hardware/peripherals par OS.
- P9 : backup/recovery/DR.
- P10 : update engine cross-platform avec rollback.
- P11 : launcher/recovery UX avec BEFORE → mockup → AFTER.
- P12 : matrice CI/certification Windows/macOS.
- P13 : certification cabinet réel sur machines propres.
- P14 : closeout permanent docs/gouvernance/preuves.

## État courant

- P0–P5 CLOSED ✅ ;
- P6 ACTIVE — 0/8 EP ;
- P7–P14 PLANNED ;
- validé : **65/162 EP = 40,1 %** ;
- PR active P6 : `#259` ;
- HEAD : `e8aaa2cfd2b68bc84a777c2e07fa4e8ee7dee5fd` ;
- CI : `32912896028` — QUEUED au dernier contrôle ;
- aucun Vercel.
