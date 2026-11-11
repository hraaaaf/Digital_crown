# DIGITAL CROWN — LOT08.2-B / B-7d — Conflit GitHub `master` / DRAFT, isolation et preuve (2026-11-09)

**Décision RED :** corriger les 5 conflits réels de la PR [#1239](https://github.com/hraaaaf/Digital_crown/pull/1239) **sans fusionner la PR vers master**, activer la clinique, installer une release ou utiliser des patients réels. La PR était OPEN/DRAFT, HEAD `c6954e6ec0c775c245754840ad532e6ed147640e`, base historique `324afd13487acf7ff29223f077451927b54b8178`. Master lu et actualisé en **lecture seule** à `edbc24edac8d3f02c2c3146a501f021c3766190a`. Un checkout git shallow avait masqué la merge-base; `git fetch --deepen=100` a retrouvé la base exacte sans modification du code.

## BEFORE / cause constatée, non supposée

`git merge-tree --write-tree origin/master HEAD` est **RED**, avec 5 chemins / 6 blocs de conflit :
- `backend/tests/test_cephalo_v1_l3_a4_document.py` : fixture positive UTC + schema version côté PR, fixture médicale et refus cross-patient complémentaire déjà corrigés indépendamment sur master
- `frontend/src/ClientFacingCopyCandidateAudit.test.ts` : audit JSX/AST segmenté 48 fichiers côté PR et timeout de 30 secondes côté master
- `frontend/src/test/mobileM4CDocumentContext.test.ts` : assertions patient actif/blob de la PR et assertions preview/route de master
- `frontend/src/test/v15HubRoutingContract.test.ts` : équivalence Windows CRLF testée strictement côté PR, assertion regex de master
- `techdoubt.md` : limites de LAB Queue Core sur PR, décision de gouvernance « FUE remplace revue indépendante obligatoire » sur master

## ACTION, worktree temporaire uniquement

Un **worktree Git détaché** `DigitalCrown-B7D-ConflictProof` simule `git merge --no-commit --no-ff origin/master` sans modifier master ni la branche PR. Les 6 blocs ont été résolus avec sélection explicite des invariants **des deux branches** :

- Céphalo : garder la fixture T0/UPLOAD/`media.ORTHO_MEDIA_SCHEMA_VERSION`/UTC, le test de refus du mauvais patient déjà en master **et** les tests supplémentaires refusant patient/T1/provenance DERIVED de la PR
- Client-facing copy : analyse AST exhaustive par tranches de 48 sources et vérification de couverture exacte, tout en conservant une tolérance 30 secondes par tranche issue de master ; aucune règle de copy médicale retirée
- Documents M4-C : conserver patient actif, vérification de preview avec nom/blob/patient et **toutes** les assertions de master sur `responseType:'blob'`, composant PDF et ID patient
- Hub : garder l'assertion stricte sur CRLF normalisés **et** la regex de classification fail-closed master
- `techdoubt.md` : conserver les avertissements LAB et la politique de vérification FUE ; aucune autorisation clinique inventée

**Proof statique vérifiée sur le worktree fusionné :** 0 conflit non résolu, `git diff --cached --check` PASS, `compileall` du test Céphalo PASS ; présence vérifiée des refus mauvais patient et provenance ainsi que des assertions Documents côté master + PR. **Tests ciblés Céphalo + Ortho : 15/15 PASS / exit 0** (88,35 s sur Python 3.12 avec SQLite `sqlite:///:memory:` et ENVIRONMENT=test, strictement données fictives). Les tests frontend ciblés sont à vérifier indépendamment, sans tourner simultanément avec les tests Python sur le PC 8 Go.

## GATES conservés

- **PR DRAFT / NO MERGE TO MASTER** : aucune migration SQL/données clinique, activation, release ou déploiement. Une mise à jour future de la branche DRAFT doit rester distincte du merge final master soumis à GO explicite.
- **Human visual approval :** après tout changement SHA, le gate [UI Human Visual Approval #42697010891](https://github.com/hraaaaf/Digital_crown/actions/runs/42697010891) révoque légitimement l'ancienne approbation : nouvelles captures et évènement label `visual-approved-by-achraf` par le propriétaire GitHub `hraaaaf`. Aucun bypass / auto-approbation n'est admis.
- **CODE_CERTIFIED/INSTALLABLE_CERTIFIED** : aucun workflow exact SHA confirmé pour ce projet, donc aucune validation officielle, Windows installé ni LOT10 physique.

## Next exact

Terminer les tests frontend M4-C/Hub/Audit/Prescription/Garde-brouillon sur worktree isolé, puis Queue Core/compilation proportionnelle. Ne promouvoir la résolution vers la **seule branche PR DRAFT** que si les preuves sont positives ; ensuite vérifier le nouveau HEAD, CI GitHub et Notion. Si le PC ne permet pas les tests, conserver le **STOP sans pousser de merge non testé**.

## B-7d CLOSEOUT — evidence on simulated master integration

**Précision sur master :** la résolution a d'abord été testée contre `edbc24ed...` puis `master` a avancé à `d4d2d144393fc884e01ca8734c1efa9fb0e0f2e3`. Ces six nouveaux commits ne changent **aucun des cinq fichiers conflictuels** ; ils ajoutent trois fichiers LOT05 (workflow GitHub, document qualité, script Windows). La merge simulation a été refaite **sans commit**, avec comparaison SHA-256 des cinq résolutions d'origine : **identiques octet pour octet**. `git diff --cached --check` PASS et zéro fichier non mergé. `MERGE_HEAD=d4d2d144...`.

**Preuve frontend sur les cinq fichiers conflictuels** : après l'échec initial du runner Vitest combiné (`onTaskUpdate`), chaque suite a été exécutée dans son propre processus `vitest run <fichier> --maxWorkers=1 --minWorkers=1 --reporter=dot` ; chaque process **exit 0**, sans erreur worker et avec comptage attendu : audit AST **13/13**, Documents M4-C **6/6**, Hub **8/8**, PrescriptionForm **7/7**, PatientDraftGuard **8/8**. **TOTAL 42/42 PASS, 5/5 processus exit 0**. Durées observées : 58,9s, 25,7s, 24,5s, 45,2s, 33,1s. La version des cinq fichiers testés est identique après mise à jour du merge vers `d4d2`. Les logs bruts restent dans le dossier LAB externe `DigitalCrown-B7D-Sequential-Evidence`. Le manifeste `docs/v1.5/evidence/lot08_2_b7d_master_conflict_sequential_20261109.json` contient les 5 SHA-256 vérifiés, fichiers et codes de sortie. **Ces tests restent un LAB, pas une certification médicale des protocoles ni une revue GUI native.**

**Backend Céphalo/Ortho :** `15/15 PASS / exit 0` sur la résolution précédente `edbc` ; les résolutions conflictuelles en cause sont strictement identiques après merge courant `d4d2`. Ni patient réel ni base clinique. Test anti-tenant, mauvais patient, T0/T1 et provenance maintenus.

**Queue Core sur le merge courant d4d2 :** premier `pytest -q queue_core/tests` : **124 PASS / 3 FAIL / exit 1**, les **trois** uniquement dans `test_installable_source_preflight_08_2_b.py`, car le checkout **sparse** du worktree isolé ne contenait pas le fichier tracked `installer/DigitalCrown.iss` ; ce n'était **pas** une absence de garde dans Git. Après `git sparse-checkout add installer` (aucune modification de code), `pytest -q queue_core/tests/test_installable_source_preflight_08_2_b.py` **5/5 PASS / exit 0 / 6,13s**. **Ne pas appeler le premier run complet PASS** ; couverture vérifiée en deux étapes, sans relâcher les exigences source. `SOURCE_GATE_PRESENT_NO_INSTALLABLE_GO` reste l'unique état autorisé.

**TypeScript final :** `frontend/node_modules/.bin/tsc.cmd --noEmit -p tsconfig.app.json` sur le worktree fusionné courant d4d2 **PASS / exit 0** (457,77s sur machine Windows 8Go, ~270–500Mo libres). Aucun artefact de production ni installateur produit.

**PROMOTION** : le worktree local est prêt pour une réconciliation contrôlée de la **seule branche PR DRAFT** si les SHAs distants demeurent `master=d4d2d144...` et `PR=c6954e6e...`. Aucune autorisation de merge de PR vers `master`, packaging, déploiement ou relabel visuel n'est implicite. Après promotion, actualiser la CI exact SHA et Notion. Les workflows Queue/Scope/CODE_CERTIFIED candidate **ne sont pas acceptés sans runs et logs authentiques** ; human visual approval révoquée sur changement de HEAD, requiert nouvelles captures et validation explicite.

### Preuve complète additionnelle — 10/11/2026

Après restauration **locale et sans changement du code Git** du fichier `installer/DigitalCrown.iss` suivi par Git dans le worktree sparse, le passage **intégral** `py -3.12 -m pytest -q queue_core/tests --tb=short` sur la résolution intégrant `master=d4d2d144393fc884e01ca8734c1efa9fb0e0f2e3` a produit **127 passed in 158.86s, `QUEUE_CORE_FULL_EXIT=0`**, processus entier **exit 0**. Ce résultat remplace le blocage de validation, tout en conservant le premier résultat historique 124 PASS / 3 FAIL dû uniquement au checkout incomplet.

Il est interdit d'extrapoler les 127 tests Queue Core, les 42 tests frontend séquentiels, les 15 tests Céphalo/Ortho ou la compilation TypeScript à une certification master, installation Windows native ou approbation clinique/visuelle. La PR reste DRAFT, et la gate humaine attend toujours des captures fraîches et une validation explicite après nouveau SHA.
