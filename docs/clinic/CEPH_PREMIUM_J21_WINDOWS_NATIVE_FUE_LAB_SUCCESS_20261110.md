# DIGITAL CROWN — J2.1 — 10 novembre 2026
## STATUT CANONIQUE ACTUEL : 3 FUE Windows LAB 🟢 · application clinique officielle 🔴 HOLD

**GOAL / Décision :** remplacer la revue indépendante de clôture demandée par l'utilisateur par **trois FUE automatisés sur véritable runner Windows et navigateur Chromium**, sans jamais présenter les FUE comme une certification anatomique ni autoriser l'usage patient. Pas de merge, mise en production ni migration critique.

**SOURCE TESTÉE EXACTE :** `23d3d97f21c6b227c7df319278f4e96490041885` dans [PR #1253](https://github.com/hraaaaf/Digital_crown/pull/1253) OPEN/DRAFT/UNMERGED. [CI J2.1 #42874664949](https://github.com/hraaaaf/Digital_crown/actions/runs/42874664949) **COMPLETED SUCCESS 10/10 jobs**, dont vraie compilation PyInstaller Windows du LAB, prébuild Linux de MainLayout, tests JWT/SQLCipher/AES-GCM/React. Autres contrôles de ce commit : Scope Gate, Alembic/schema et Theme Wave09/10/11 SUCCESS ; biométrie SKIPPED hors périmètre. Aucune route clinique activée.

### FUE 1 — Shell Desktop réel en sandbox 🟢
- Entrypoint FUE distinct qui **importe le véritable `MainLayout` de Digital Crown** et appelle `/api/auth/me` avec JWT d'un dentiste fictif `example.com`.
- Chromium vérifie DOM de shell, sidebar, `nav`, menu, workspace, vrai appel média, scène source et EDIT en viewBox 800×600 ; captures 390, 430, 768, 1280 en BEFORE/AFTER et REOPENED 1280.
- **Limite :** ce shell est importé dans un EXE de test distinct, pas dans l'installateur certifié `DigitalCrown.exe`. Sur l'image synthétique, certaines étiquettes de points se chevauchent : pas de validation de lisibilité clinique, mm ni anatomie.

### FUE 2 — Provenance du binaire exact et sécurité patient 🟢
- Binaire `DigitalCrown-J21-FUE-LAB.exe` identifié par SHA256 **`b129e0ae9cfe4ab9f1d2ab64a10c049b57577b7842012d6c0f4563ab08e1659d`**, manifeste exact-HEAD `head=23d3d97f...`, `is_installable_certified=false`, `signed=false`, `clinical_release=false`, `production_route_mounted=false`.
- Refus d'exécution hors garde GitHub/sandbox PASS ; neuf profils céphalométriques JSON/YAML source→package SHA identiques ; SQLCipher sur disque, pas de fichier SQLite plaintext ; image PNG synthétique AES-GCM DC-DOS-05 avec SHA256 source `d18e1f863c91a2876cbb2c979951ec0117ddcd039bc6f3d91011213292429787`.
- FUE A/B/X : anonyme **401** ; patient B du même cabinet avec étude A **404** ; dentiste X d'un autre cabinet **403** ; autre étude X **404** ; rejeu d'un CAS ancien **409**. Aucune élévation de licence/permissivité, aucune donnée réelle.

### FUE 3 — CAS, arrêt/reprise et restauration chiffrée DB + médias 🟢
- Dans Chromium sur `127.0.0.1:8879`, landmark A `x=45→46`, `PRACTITIONER_EDIT`, mesures SNA `UNAVAILABLE/null`, sauvegarde CAS **revision 2**.
- EXE intégralement arrêté, SQLCipher checkpoint alors que le serveur est fermé ; **copie de DB et de deux blobs AES-GCM `.dcm` avec préfixe DCM1**, suppression des originaux, restauration de tous les fichiers, vérification des empreintes triées de chaque blob et de la DB. La base chiffrée restaurée SHA256 `d57a3e243807c86c319c6f9dd2e7a62d250caa6b9b5e7d25c3f84770534782f7`; manifeste média SHA256 `f81a52cc0f100a84676310baa43b53c9a316daad75ef986d0a00f3c1782a6acb` avant→backup→restauration.
- EXE relancé sur le même profil fictif. Révision 2, image source et SHA de scène **`90ab75fcf639d18dfd01b423500c975adc3d01e14b21fa19e73cf92af8d68f85`** strictement identiques. Neuf PNG SHA256 vérifiés indépendamment sur le ZIP. Nettoyage du profil, des blobs, des clés et de la copie temporaire backup dans `if: always()` PASS ; port 8879/processus arrêtés.
- **Limite :** test de restauration de fichiers fictifs hors ligne ; **ne certifie pas** le module de sauvegarde/restauration du cabinet clinique et ne constitue pas un exercice de reprise sur patient réel.

### Preuves vérifiées indépendamment
- [ZIP 9 captures + manifestes JSON #13792111361](https://github.com/hraaaaf/Digital_crown/actions/runs/42874664949/artifacts/13792111361) — ZIP SHA256 **`d83c43edfd68a913e469fea39c41a38c2fbb5311138b1409e34f81e771c018cb`** ; les 9 SHA PNG, les deux FUE navigateur et le manifeste `synthetic-backup-roundtrip.json` ont été relus/recalculés hors CI.
- [ZIP EXE Windows LAB NON INSTALLABLE #13792740759](https://github.com/hraaaaf/Digital_crown/actions/runs/42874664949/artifacts/13792740759) — archive SHA256 GitHub **`f6d31b356c9a9645be096dccdda2939b97b918103e126ce9d5143f6d6470a1b9`**. Rétention CI limitée, pas une release, aucune signature.
- GitHub CI seule : **10/10 J2.1 SUCCESS**. Le workflow séparé `UI Human Visual Approval` a refusé faute d'étiquette d'approbation visuelle explicite : **ne pas le contourner ou le déclarer PASS** ; aucune fusion n'est envisagée.

### Jalons du chantier
- **M1 🟢** ; **M2–M5 🟡** (contrats/API/LAB prouvés, produit clinique non intégré) ; **trois FUE Windows LAB 🟢 TERMINÉS** ; **M6 véritable Desktop clinique certifié 🔴 HOLD**.
- L'utilisateur a choisi les FUE à la place d'une revue indépendante de clôture ; aucun second reviewer n'est revendiqué. Les FUE ne peuvent certifier la correspondance anatomique réelle des 38 canaux SRPose38, la calibration mm, des résultats diagnostiques ou un traitement : les statuts restent NON VALIDÉS / UNAVAILABLE.
- Le build officiel `DigitalCrown.spec` impose `INSTALLABLE_CERTIFIED` et **n'a pas été modifié** ; les FUE n'insèrent aucune route/UX dans l'installateur destiné aux patients. Pas de merge master/main, activation médicale, migration ni déploiement.

**NEXT EXACT / human gate :** si l'objectif suivant est l'intégration clinique officielle, préparer la provenance `INSTALLABLE_CERTIFIED` de l'exécutable réel, les FUE sur l'installateur officiel et l'autorisation explicite de mise en production. Ne pas cocher M6 produit tant qu'une preuve de ce niveau n'existe pas. Le fichier présent est canonique pour les **trois FUE LAB terminés**, pas pour une sortie clinique.

---

### Historique antérieur (ancien FUE LAB autonome)

## Verified SUCCESS on exact source, clinical Desktop product HOLD

**Decision / Goal:** Build a GitHub Actions Windows-only, nonclinical standalone FUE executable and prove a real Chromium workflow: JWT login, verified source image, SVG practitioner landmark correction, CAS persistence, full executable shutdown/relaunch, identical verified image/scene digests, and SHA-checked screenshots. Do not register the scene UI/API in the production clinical application.

### Source identity and CI evidence
- Repository: `hraaaaf/Digital_crown`, PR [#1253](https://github.com/hraaaaf/Digital_crown/pull/1253), OPEN / DRAFT / UNMERGED when verified.
- **Exact tested source SHA:** `36a454cfb499fa2c3d15aeafc272c6ec69ad4916`. Later documentation commits **are not** silently represented as tested by that run.
- [GitHub Actions #42836380198](https://github.com/hraaaaf/Digital_crown/actions/runs/42836380198): **COMPLETED SUCCESS 9/9 jobs** (8 contract/API/React/LAB + 1 real Windows native test-only EXE + Chromium).
- Other same-SHA checks: CI Scope Gate, PostgreSQL Alembic Schema Certification, Theme Wave09/10/11 **SUCCESS**, no clinical migration or deploy; Biometric **SKIPPED**, out of scope.
- Windows job evidence markers: `CEPH_NATIVE_FUE_EDIT_PASS`, `CEPH_NATIVE_FUE_REOPEN_PASS`, `WINDOWS_NONCLINICAL_NATIVE_EXE_REAL_BROWSER_CAS_RESTART_SHA_PASS`, `SYNTHETIC_TEST_DB_MEDIA_KEYS_CLEANED_AND_NATIVE_EXE_STOPPED`.

### Native proof, verified from CI logs **and** archived JSON/PNG
- Native PyInstaller binary `DigitalCrown-J21-FUE-LAB.exe`, SHA256 `13e1f9615969c193576071b6d2c5a0d3521c3040ec8fbc15bd86364c536b2faa`; 9/9 bundled static cephalometry resource filenames and SHA256 values matched version-controlled originals.
- Fail-closed launch outside explicit GitHub Windows synthetic flags: PASS. Only loopback `http://127.0.0.1:8879`; outbound browser requests outside this origin blocked. Existing clinic port `8005` unaffected.
- Fresh disposable synthetic **SQLCipher** app DB; no plaintext SQLite header; same actual native backend DB engine on both processes. Synthetic licensed dentist JWT; synthetic AES-GCM PNG source and real study media binding.
- Image SHA256 before/after process restart: `d18e1f863c91a2876cbb2c979951ec0117ddcd039bc6f3d91011213292429787`. SVG viewBox `0 0 800 600`; 38 synthetic landmarks. Landmark `A` x=45 → x=46, new origin `PRACTITIONER_EDIT`, measurements invalidated.
- CAS revision 2 read-back SHA256: `90ab75fcf639d18dfd01b423500c975adc3d01e14b21fa19e73cf92af8d68f85`. Full shutdown of first EXE and reopening same SQLCipher DB from second EXE produced **the same revision, point and scene SHA**.
- Anonymous API: HTTP 401. Wrong patient: HTTP 404. A/B/X full native clinical access-control test still pending; no claim of clinic certification.
- Chromium captures: **BEFORE / AFTER** at 390, 430, 768, 1280 px (8 images) plus **REOPENED-1280** (1 image). Independently rehashed **all 9 PNG** against archival JSON metadata; all matched. The film is a plain synthetic 800×600 color image with artificial diagonal points, **not** a plausible patient radiograph or anatomy certification.
- Cleanup PASS: native process and port stopped; disposable DB, sample media, config/keys and temporary scripts deleted. No real patient data, production registration, clinical release, migration, merge, deploy or forged certification.

### Artifacts and expiry
- [Synthetic FUE screenshots + JSON ZIP (7-day retention)](https://github.com/hraaaaf/Digital_crown/actions/runs/42836380198/artifacts/13773568367); verified ZIP SHA256 `e76dfa900d6851d6f70dba87eae977e54f1321cdf11a56d1b742bc8eac509353`.
- [Windows LAB-only, NOT installable/certified executable archive (1-day retention)](https://github.com/hraaaaf/Digital_crown/actions/runs/42836380198/artifacts/13774852067); archive SHA256 `b158e81b42cd033f14beca42f3a1240c5fd591e950e3c10d5e45117f97ab9a2a`. Not signed, not released, not for clinical deployment.

### Milestone gates and next exact decision
- **M1 🟢** contract closed. **M2–M5 🟡** isolated laboratory/API evidence complete within tested scope; application/native clinical integration remains unproven.
- **Windows FUE LAB 🟢 SUCCESS**. **M6 product/native clinical Desktop 🔴 HOLD**: scene remains outside Digital Crown official installed UI/API, no certified release; scientific SRPose38 channel-to-anatomy mapping and mm calibration still not independently validated.
- **Next:** design an explicitly isolated nonclinical integration into the real Desktop packaging and get a provenance-certified exact-source candidate. Then prove native clinical shell login, film editing/CAS/close/reopen, local DB/backup and A/B/X access denial, screenshots at the same viewports. Independent anatomy/medical review is a separate human gate.
- **Human gate:** no merge to master, production routing, migration of clinical patient data or deployment without explicit user approval. Keep M2–M6 checklist unchecked until the product-level gates are evidenced.

**Handover:** this document + [PR Draft #1253](https://github.com/hraaaaf/Digital_crown/pull/1253) + Notion checklist/roadmap. The tested commit above, not any later documentation-only commit, is the immutable successful CI source.
