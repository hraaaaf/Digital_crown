# CPV2-02C — Integrated-master DRAFT rehearsal (NEVER MERGE)

This branch copies the exact changed Pocket product + test-only safety files from `3490c6a3c0d817e925762e0e1a8831e3c4a77072` onto `master@7e821dff1112249d0bda25c5708f9b37cca7082b` and resolves the single same-path conflict `backend/main.py` by preserving both branches' CORS headers. It is **NOT an authorized merge into master**. Source branches remain untouched.

## Sources / scope

- Product PR #1201 HEAD: `d7852f25c3f4b69f8f8ad4b4e2d58ffbae5cefb1`
- Pocket safety PR #1224 HEAD: `3490c6a3c0d817e925762e0e1a8831e3c4a77072`
- Master snapshot: `7e821dff1112249d0bda25c5708f9b37cca7082b`
- Merge-base before integration: `3a4a8941d287ad9726f56f58e5a12bd9e253b30d`
- Total changed candidate paths: 46; concurrent master changes: 70 paths; same-path collision: only `backend/main.py`.
- The integrated CORS authorization list includes `Idempotency-Key`; its exposed headers preserve master `Content-Disposition` and Pocket `X-Document-Id`, `X-Idempotent-Replay`.

## Evidence and gates

The dedicated `tests/test_cpv2_02c_integration_cors_lab.py` checks the actual parsed CORSMiddleware configuration, and the G04 matrix runs this check on Windows and Ubuntu. The new DRAFT PR against master must pass independent CI/FUE on its **own exact SHA**. Existing standalone success on #1224 does **not** transfer automatically.

Synthetic-only tests. No clinic database or media, no real patient data, no restoration or auto-reassociation. No migration, clinical deployment, PR merge, or production activation. Final clinical NO-GO until separately approved operational restore, security/integrity review or documented risk acceptance, and human authorizations.

## RESTORE-03 cross-workflow compatibility investigation (8 November 2026)

On the first integrated tree `78ed8dd54fd8f7431eeaf6e1c8318df8a98bf80c`, two Windows B restore checks failed with `AssertionError` (RESTORE-03 P4 #42429036826 and Remote Windows #42429036874). Their fixture generated `documents/SYNTHETIC.txt` with **no** `DocumentArchive` row, whereas the Pocket integrity preflight deliberately rejects every unlinked `documents/` member. The worker suppresses the exact assertion location in the public CI logs; this explanation is a code-traced **hypothesis pending new CI verification**.

The isolated rehearsal now relocates only this **generic, fictitious, nonclinical file** from `documents/SYNTHETIC.txt` to `misc/SYNTHETIC.txt` in the three existing RESTORE-03 synthetic test scripts. The file's content and cross-host hash checks remain unchanged; no real medical document or linked archive is reclassified. The Pocket preflight, orphan protections, production scripts, UI and database schema are **not weakened or modified**. Pocket G04 must still prove that true `documents/` orphans are blocked. Treat the follow-up exact-SHA CI as mandatory, with the original failures preserved in GitHub history.

This remains an **integration-only dry-run branch**. Do not cherry-pick these test fixture changes into production without a separate review; DO NOT MERGE the DRAFT PR, deploy, migrate or use real patient data.

## J7 — Cohérence DB + médias lors de captures non atomiques (test fictif du 08/11/2026)

Le bundle de `CabinetBundleService.create_bundle` capture la base puis les
médias **successivement** : la présence d'un manifeste chiffré n'établit
**pas** une transaction commune DB+médias. Cette limite est maintenue.

Scénario ajouté au test G04 réel `tests/test_pocket_restore_real_schema_lab.py` :
prendre un snapshot SQLCipher lié à un `DocumentArchive`/reçu COMPLETED,
modifier **à longueur égale** le PDF canonique après snapshot DB mais avant
capture médias, créer un bundle portable cryptographiquement valide et
convertir en archive GuidedRestore. Son préflight DOIT retourner `blocked`
malgré le chiffrement correct ; `prepare` DOIT refuser et les originaux
fictifs doivent rester identiques. Le bundle cohérent original doit
continuer à être restauré et annulé par les primitives de rollback.

**Preuve attendue :** G04 Windows + Ubuntu sur le SHA intégrant ce cas,
plus FUE/API globale. Cette preuve vérifie un refus fail-closed d'un
exemple de capture incohérente ; **elle ne prouve pas** la quiescence
du cabinet, ni la détection de toutes les courses/concurrences entre
captures. L'activation clinique exige une procédure opérateur de gel
d'écriture/backup cohérent, un inventaire DB+médias complet et une
restauration/rollback vérifiables dans son périmètre autorisé.

Aucune base clinique, patient réel, réparation automatique, migration,
merge ou déploiement. La revue indépendante demeure facultative et sautée
pour CPV2-02C selon le canonique.
