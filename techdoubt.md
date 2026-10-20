# TECHDOUBT — Digital Crown

## PROCESS-AUTOPILOT / 2026-10-20 — Réserve de gouvernance OPEN

Le protocole prospectif réduit les micro-accords et micro-scores, sans toucher aux workflows CI/Human Visual Approval, règles de sécurité, labels ou release cabinet. Les branches historiques et workflows peuvent exiger encore des artefacts propriétaires; un docs-only GREEN n'est pas un produit FUE. **Risque non résolu :** la baisse effective d'interruptions et l'absence de régression ne sont pas encore mesurées. **Next :** examiner le diff sur HEAD, tests documentaires et gates réels ; GO propriétaire distinct avant merge ; pilote sur trois lots autorisés avec suivi des interruptions, réexécutions et incidents. Aucun contournement de gate.



## GLOBAL-G10-S / LOT10 — 2026-10-18 — Two-agent isolation requirement withdrawn

**Status: RESOLVED AS A FALSE DEPENDENCY (doctrine correction, not proof of a completed FUE).**

**Previous concern:** The merged PR #960 required two AI BLIND USER agents running in independent contexts, with separate browsers and withheld reports. That had been documented as a blocking precondition even for ordinary internal adversarial review. The product owner clarified that the **same ChatGPT conversation should perform both specialized perspectives A/B itself** rather than waiting for humans or two separate AI agents.

**Resolution rule:** `AGENTS.md`, `.claude/rules/execution-scoring-verification.md` and `docs/quality/REALITY_PROOF_GATE.md` now instruct the assistant to write two distinct, task-specific *internal adversarial* reviews, correct/test, rerun on new HEAD and confirm. This is not evidence of two genuinely independent reviewers; it is sufficient for the **internal A/B double-review procedure**. Self-review is capped at 9.4/10 and normal VERIFIED starts at 9.0/10 when required proofs/gates pass. No external reviewer or two-agent orchestration is a prerequisite.

**Distinct unclosed verification work — GLOBAL-G10-S:** Inventory V1+V1.5 routes/features, execute actual frontend/backend FUE journeys on fictitious tenants starting at login (or a public entry where applicable), preserve BEFORE/ACTION/AFTER, negative RBAC/tenant checks, exact-HEAD evidence and CI statuses. **These tests have NOT been executed by this documentation correction.** An imagined browser session or two written perspectives are not executable test proof.

**Unchanged gates:** Specifically required human clinical/regulatory/visual approvals and LOT10 hardware/person-on-device observations remain separate from conversation-based A/B review. No deployment, merge or clinical activation is authorized by this documentation.

**Historical origin:** PR #960, master merge `3cbd1d83cdbcbf97e71019a3182f4699d9645421`. This file supersedes the inaccurate "two-agent independence not yet demonstrated" as an *internal review blocker*.


## 2026-10-19 — FUE-first governance migration (#988)
- ACTIVE doctrine migrated in AGENTS.md, CLAUDE.md, scoring, RPG, visual closeout, PR template, policy contract test and G10-S documentary checker.
- RESERVE: historical audit/handover files and specialist skills may still describe mandatory A/B reviews. They are historical or domain-specific evidence, not an override of active FUE-first policy; assess applicability before changing them, do not rewrite old evidence.
- RESERVE: repository-wide policy contract tests and G10-S have not been executed locally in this connector session; CI on final HEAD and applicable gate must be checked before merge. FUE-0 documentary only, no UI journey or clinical/physical certification claimed.

- CLOSEOUT RESERVE (2026-10-19): active `skills/reality-proof-gate/SKILL.md` still imposed mandatory two A/B reviews; corrected in PR #988. Final HEAD after this consistency correction requires fresh exact-HEAD CI results. Previous GREEN on `c91776c` does not certify later commits. PR remains DRAFT/OPEN; no merge or deployment authorized. Historical files remain out of scope.


## LOT07 / 07-C — 2026-10-20 — PR #989 trusted visual approval, FUE-0

- **Scope / evidence:** PR #989 corrects only the trusted `pull_request_target` label revocation script and its tests. Canonical FUE level: **FUE-0**, not FUE-I/G; no first-user Cabinet journey or screenshots are claimed. CI on `c54b118e60516ef86b38eddf172d0b30e8980d40`: 22/22 mocked GitHub API contract tests pass in both Visual Gate Security Regression and UI Visual Approval Contract; CI Scope Gate GREEN. Human Visual Approval GREEN is **`skipped-non-ui`**, not proof of an actual UI owner `labeled` approval event.
- **RESERVE (expected gate restriction):** Until this PR is reviewed and merged with explicit authorization to trusted `master`, the `pull_request_target` workflow still runs the older script; PR #971 still needs fresh exact-HEAD visual evidence plus a genuine owner-applied approval label event. Its `synchronize` failing closed is expected, not a defect to bypass.
- **RESERVE (proof boundary):** GitHub API failure, absent label, SHA race, label-removal no-op, and owner identity paths are exercised via mocked Node tests, **not** a real GitHub owner-label workflow on a UI PR. This is sufficient FUE-0 code/contract evidence, not a verified FUE-I/G user journey or live end-to-end approval certification.
- **Next:** confirm final HEAD targeted CI after this documentary reservation; keep PR #989 DRAFT/no merge/deploy without approval; after trusted patch lands, acquire fresh screenshots and exact-head human visual approval for #971.

## LOT07 / 07-C — 2026-10-20 — Integration reconciliation after research PR #961

**Active reservation:** The isolated Command React target has no Cabinet backend, real login, RBAC, patient records, production UI integration or clinical certification. Shared CSS still requests Google Fonts, so fully offline/private egress is NOT certified. Keep 07-D/E frozen.

**Merge conflict and safety decision:** PR #971 diverged from #989's trusted visual approval gate. Resolve by preserving the **unchanged master script** from merged #989 (owner-only labeled event, SHA match and fail-closed synchronize); additionally retain two targeted sanitized 403/500 regression tests from the research branch. Preserve visual UI blobs exactly, do not merge deprecated trusted script from #971. The merge reconciliation creates a new source HEAD, invalidating the previous SHA-bound owner approval until fresh exact-HEAD screenshots and a genuine authorized owner `labeled` event succeed. DO NOT describe the old GREEN as approval of the new SHA. Do not merge #971 until the trusted gate is GREEN again.

**Historical context, not active release gates:** The following #971 branch notes are preserved as an audit trail of earlier experiments. Any historical claim that two independent blind-user agents are mandatory, or that the visual-gate fix/approval remains OPEN on the old SHA, is superseded by the canonical FUE-first policy and later GitHub evidence.

## LOT07 / 07-C — 2026-10-19 — visual approval revocation error cause unknown

**Status: OPEN / MAJOR gate availability; fail-closed retained.**

**Evidence:** Human Visual Gate run https://github.com/hraaaaf/Digital_crown/actions/runs/39313124584 failed with `Failed to revoke stale visual approval`. The `synchronize` handler attempts DELETE of `visual-approved-by-achraf`, tolerates 404, verifies label disappearance and refuses stale approval. Original HTTP status was not visible in CI log. Commit `b499e9604e6336bc7a4e509e184148841c74f91f` adds only sanitized HTTP status reporting; it does not change approval or revocation semantics.

**Unresolved:** Actual HTTP status and cause (workflow token permission `issues:write`, API behavior or other), whether label existed, trusted workflow configuration, rerun outcome, and human approval remain unverified. No Cabinet integration or production proof. React synthetic screenshot disables sticky only during full-page snapshot; actual sticky scrolling requires separate verification. Whole-app TypeScript and full accessibility audit remain unproven.

**Resolution gate:** Inspect exact trusted workflow permissions and event payload; run tests for 403, 404, 500 and label absence; rerun gate against new exact HEAD, diagnose sanitized status, preserve fail-closed and require fresh owner-labeled approval. Repeat independent A/B review on same final HEAD. Keep PR #971 DRAFT and CONVERGED=NO until verified.


## LOT07 / 07-C — 2026-10-19 — FUE evidence gate on exact HEAD

**Status: OPEN / REQUIRED evidence, no product defect asserted.** FUE replaces additional independent reviewer opinions for this sublot, but passing unit tests and older Chromium artifacts are not two blind-user FUE traces.

**Evidence:** HEAD c7d57d31db8d02daf13d8917c383b0f164dab5bf: Visual Gate Security Regression, UI Visual Approval Contract and CI Scope Gate SUCCESS. React target is standalone synthetic-only; patient switch uses confirmation and an inert dialog; session reducer rejects unauthorized mock transitions. The last cited screenshot artifact belongs to older HEAD e3ff472485731961238ea2fac1a1fb72ae55ab59, so it cannot certify current HEAD. Trusted pull_request_target workflow checks out default branch, so PR-only gate diagnostic changes do not run in that privileged workflow until separately promoted through an authorized safe process.

**FUE-A / REQUIRED — clinical workflow:** From fresh isolated browser profile at exact HEAD, execute TEST-001 consultation pause/resume/finish, same-practitioner next patient, A→B→A and Dossier→Imagerie→Dossier; capture before/action/after, patient IDs, keyboard focus, 390/430/768/1280, 200% zoom. Confirm no patient A content under B and all nonfunctional actions explicitly synthetic.

**FUE-B / REQUIRED — safety and accessibility:** Separate fresh profile and independent trace; attempt stale pending switch, Escape/cancel/focus restoration, keyboard-only tabs, rapid patient switching, no backend requests, no cross-patient leakage, mobile sticky context, all eight themes and no horizontal overflow. Score each check severely /10; any BLOCKER/MAJOR must be fixed and rerun on same final HEAD. The two agents' provenance/isolation must be demonstrated, not claimed.

**FUE-C / REQUIRED — visual approval security:** Verify trusted default-branch workflow behavior, exact-HEAD human visual label event by authorized owner and successful attestation; test 403/404/500 and HEAD race with no fail-open. Existing contract tests do not prove actual GitHub DELETE status of earlier failed run 39313124584.

**Gates:** REQUIRED = FUE-A/B/C and owner human visual approval; EXPERIMENTAL = exploratory UX scores or prototype-only extra interactions (nonblocking unless real security/production risk); HORS SCOPE = Cabinet production, real patients, RBAC certification, 07-D/E. Until fresh evidence: FUE=OPEN, HUMAN_GATE=OPEN, CONVERGED=NO, PR #971 DRAFT, no merge.


## LOT07 / 07-C — 2026-10-19 — CI FUE browser adaptation evidence limit

**Status: OPEN / REQUIRED.** Added `scripts/research/lot07_07c_command_react_fue.cjs` and wired the existing `v15-07-c-command-react-target.yml` on the PR #971 branch to run two fresh, separate Chromium browser contexts (A synthetic workflow, B keyboard/cancel/isolation), capture screenshots and JSON with exact SOURCE_HEAD, and fail on negative assertions. This is a *single scripted CI job*, NOT two independent blind-user AI agents and NOT real Cabinet authentication. Its score 10/0 per scripted assertion is a technical pass/fail score, not an independent UX or clinical rating.

**Required before closure:** Inspect the actual GitHub Actions run and artifact on the final HEAD; investigate any failures and repair; execute two genuinely independent blind-user FUE agents if required by global doctrine; obtain separate owner Human Visual Gate approval; no merge/deploy. Workflow push path filters mean only the workflow/script changes trigger browser execution. FUE-C real approval remains OPEN.


## LOT07 / 07-C — 2026-10-19 — FUE network egress RED diagnosis

Run https://github.com/hraaaaf/Digital_crown/actions/runs/39322829080: 13/15, both failures were third-party Google Fonts requests (fonts.googleapis.com and fonts.gstatic.com) inherited from shared `frontend/src/index.css`. No unexpected clinical/backend requests were reported. **Reservation OPEN:** the isolated Command visual target is not fully offline, and font fetch may disclose visitor IP to Google. The scoped FUE laboratory now explicitly allows only these two font asset hosts, documents them in JSON and still rejects any other external host. This changes the test claim from 'zero external requests' to 'zero unexpected external requests'; it does NOT certify offline or privacy compliance. Do not change shared Cabinet CSS in LOT07/07-C without separate approval. Human visual approval remains blocked independently.


## LOT07 / 07-C — 2026-10-19 — Human Visual Gate trusted-branch remediation blocked

Live PR #971 labels API returns an empty list, while trusted `master` `scripts/ci/visual-approval-gate.mjs` unconditionally issues a DELETE on every UI `synchronize` event, then rejects the changed HEAD. Run https://github.com/hraaaaf/Digital_crown/actions/runs/39323262173 fails `Failed to revoke stale visual approval`. The actual DELETE HTTP status is not available from this trusted log; root-cause hypothesis (unnecessary DELETE of absent label) is not yet proven. A minimal branch edit to conditionally DELETE only if a label was present was **blocked by execution security controls**, so no trusted gate change was made. Do not infer that CI GREEN fixes Human Gate; no label was added, no privileged workflow bypass or default-branch change is authorized. Required: authorized owner reviews trusted-branch fix and its adversarial tests, validates actual DELETE status and confirms new exact-HEAD visual evidence and explicit human approval. PR remains DRAFT/NO-GO.


## LOT07 / 07-C — 2026-10-20 — Exact-HEAD synthetic Command evidence renewal

**Status: OPEN — independent UI-human gate distinct; synthetic First User Experience only.** Current PR #971 HEAD before evidence renewal: `d1aeedb342197cdd7326460c546676e0ca37275e`. Earlier React browser run `39323225019` (`bbbd503d...`) and its screenshots are from an older HEAD and must **not** attest this HEAD. The latest PR-only tests (Security Regression, UI Visual Contract, Scope Gate) pass; the old Human Visual `synchronize` run fails closed, as intended for unapproved new UI HEAD. The visual approval communicated in ChatGPT only covers the earlier screenshot design direction, not a valid GitHub owner `labeled` event on this HEAD.

**Trusted gate update:** Separate PR #989 merged to `master` as `67ed5a851dd8b369d27c9f87cbe10b9cace0284c`. Trusted label handler now skips DELETE when label is absent and keeps SHA binding, owner-only genuine `labeled` event, and fail-closed `synchronize` refusal. Post-merge PostgreSQL certification run https://github.com/hraaaaf/Digital_crown/actions/runs/39346178348 succeeded on attempt 2 after ECR Public image-rate-limit infrastructure failure.

**FUE classification:** Standalone React/Vite Command target has a usable synthetic browser UI, so execute **prototype-scoped FUE-I lab** (two fresh browser profiles on synthetic TEST-IDs), not real Cabinet FUE-G, no real login/backend/RBAC or independent human/AI agents. Browser screenshots 390/430/768/1280/1440, eight theme tokens, real native X11 200% zoom, keyboard/confirmation/cancel/identity guard must be evidenced on source exact SHA. Passing scripted assertions is not clinical validation or user-owner visual approval. Google Fonts external requests inherited from shared CSS remain disclosed privacy/offline reserve; do not silently equate them with zero external network egress.

**Next / no-go:** Trigger existing isolated visual/FUE workflow for final PR #971 HEAD via a scoped workflow-evidence integrity change, verify checks, inspect exact-SHA downloadable screenshots, submit images for owner visual review, then require genuine owner-labeled attestation under trusted `master`. Do not auto-add owner label, bypass required gate, integrate into Cabinet, merge, deploy, or open 07-D/E.


### CEPH-FAC-PARITY / P2ter++ — extraction chirurgicale vers master : contrat PDF manquant (2026-10-20)

**Statut : BLOCKER d'intégration vers master ; PAS un défaut démontré de la PR #957 sur sa base #953.** Cette note est conservée sur la branche **d'audit documentaire isolée** `audit/ceph-p2ter-master-extraction-20261020` partant de master `a2ad3002414a8a046221bb9993f71d0bfa8471a0`. Elle ne touche ni master, ni #957, ni leurs validations. Autorisation utilisateur : réconciliation technique **sans fusion ni déploiement**. Périmètre inchangé CEPH-FAC-PARITY / P2ter++, roadmap 41/99.

**Sources immuables lues** : #957 HEAD `52c3631f8cfae79a9c5c3b7a145a4d2fab6bbe82`, parent #953 HEAD `945fcd45d34d0cbb550e72d24bf509fb3d72c0b5`, #951 `02d3218b136533eabd8604baf32282052604b68d`, master `a2ad3002414a8a046221bb9993f71d0bfa8471a0`. GitHub compare master→#957 = diverged **572 commits ahead / 723 behind, 167 fichiers**. #878→#911→#938→#941→#944→#951→#953→#957 encore tous DRAFT/non mergées ; #911/#941/#944 affichent explicitement **clinical NO-GO**. La fusion GitHub `mergeable=true` de #957 ne vaut que contre #953.

**BLOCKER 1 — schéma PDF identité/révision, contre-exemple de parsing :**
- master `backend/schemas/clinical.py::CephaloPDFRequest` a seulement `ai_diagnostic`, `clinical_data`, `archive`. Il n'exige ni `analysis_id` ni `expected_revision`, et ne contient pas `extra="forbid"`.
- #953 (hérité de #951) impose `model_config=ConfigDict(extra="forbid")`, `analysis_id: int=Field(strict=True,gt=0)` et `expected_revision: int=Field(strict=True,gt=0)`.
- Démonstration isolée Pydantic dans environnement analytique (PAS un run de l'application) : avec l'ancienne classe, la requête `{"analysis_id":22,"expected_revision":7,"archive":true}` s'instancie mais ces deux clés sont **ignorées**; avec la nouvelle classe, elles sont préservées et l'absence de chacune provoque ValidationError. Une transplantation seulement #957 dans master ne garantit pas la sélection d'étude correcte, et l'accès à `req.analysis_id` risquerait un échec serveur.

**BLOCKER 2 — route PDF pas fail-closed sur master :**
- master `backend/routers/patients.py::generate_cephalo_pdf` choisit le `last_analysis` du patient par `id.desc()` au lieu de valider le couple (analyse explicitement sélectionnée, révision scientifique) ; en cas d'échec d'archive, son `except Exception` journalise « Archivage ... ignoré » puis renvoie le fichier PDF. Une archive manquante peut ainsi être présentée comme un PDF généré.
- #953 fournit `_bound_cephalo_study`, validation de `req.analysis_id`/`expected_revision`, en-têtes `X-Cephalo-Analysis-Id`/`X-Cephalo-Revision` et échec explicite en cas de preuve périmée. #957 ajoute le verrou étude/révision, transaction et recovery ; ceux-ci supposent le contrat #951 déjà présent.
- **Interdit** : copier `archive_service` ou les deux modules natifs seuls et déclarer la parité/atomicité verte.

**BLOCKER 3 — dépendance de l'interface :**
- master n'a pas `frontend/src/features/ortho/cephaloDocumentSource.ts`. #951 l'a ajouté : `prepareBoundCephaloDocumentSource` sauvegarde l'étude choisie, relit `angles_data.scientific_read_path.revision`, vérifie la sélection pendant les opérations et fournit `analysis_id/expected_revision`.
- Le `useOrthoStore` de #953 importe ce module, et `cephaloRepository.generatePDF` valide les en-têtes PDF. Un cherry-pick indépendant de `Step4Documents`, `useOrthoStore` ou `cephaloRepository` depuis #957 sans ce contrat serait non fonctionnel/incomplet.

**Éléments isolables sous réserve, pas intégrés :**
- `backend/services/cephalo_document_lock.py` et `backend/services/cephalo_archive_recovery.py` sont créés par #957 et absents de master/#953, mais ils nécessitent l'API identity-bound de #951, le writer-lock des `CephaloAnalysis` et les appels transactionnels dans `ArchiveService`, route patient et documents.
- `backend/models.py` est byte-for-byte identique entre master et #953 (blob SHA `6f5a4d4641e02690594d2adbd3dc383e329d8c70`), ce qui est encourageant pour les colonnes communes mais **ne prouve pas** la compatibilité transactionnelle ou runtime.
- `backend/services/archive_service.py` est identique entre master et #953 avant #957 (blob `14b599914c0db5eef695721aedf7954ebce53024`). Il reste à extraire **les hunks P2ter++ seulement** en conservant les autres logiques financières/documents et les routes protégées.
- `backend/services/cephalo_pdf_projection.py` diffère entre master et #953 ; toute récupération d'un contrat scientifique de #951 doit être évaluée séparément. Ne jamais recopier l'ensemble #911/#941/#944 ni activer les six HOLD cliniques pour obtenir un test vert.

**Plan d'intégration minimal NON EXÉCUTÉ (fail-closed) :**
1. Baseline **master immuable** et test négatif réellement exécuté sur un futur candidat isolé : PDF sans IDs refusé ; étude A sélectionnée mais B plus récente ne génère jamais B ; révision absente/périmée refuse 409 ; patient/cabinet/role non autorisé 403/404, pas d'archive créée ; une erreur SQL/FS ne doit jamais retourner faussement succès.
2. Transplanter le **contrat minimal #951** (schema strict `CephaloPDFRequest`, sélecteur d'étude/révision et headers, `cephaloDocumentSource` et frontend bounded PDF) via diff chirurgical/revue d'impacts, pas les modules cliniques NO-GO ; exécuter tests ciblés et compiler.
3. **Ensuite seulement** les nouvelles sections P2ter++ dans `ArchiveService`/routes/Step4/store ainsi que lock+journal, avec vrais tests crash/retry, SQLCipher Windows, RBAC, tamper, idempotence, FUE-I desktop (1280×900 /1600×1000) et approval humaine du **nouveau HEAD**.
4. Au moindre besoin d'activer des projections scientifiquement non validées ou d'importer #911/#941 cliniques, **STOP, NO-GO, scinder ou requalifier le scope**, aucune simplification des guards. Éviter toute mutation production/installation cabinet, merge ou déploiement.
5. Les statuts verts et l'approbation de #957 `52c3631...` ne sont **pas** transférables à une nouvelle branche/HEAD sans vérification pertinente.

**Preuve actuelle : audit statique de fichiers/blob GitHub + démonstration Pydantic isolée. Aucun candidat fonctionnel n'a été assemblé ni testé contre master ; ne pas déclarer extraction PASS.** La branche actuelle est documentaire, destinée à conserver explicitement ce risque dans `techdoubt.md`, sans toucher le sous-lot certifié. Prochaine étape : mise en place contrôlée d'un candidat réellement testable après arbitrage du contrat #951 sans dépendances cliniques ; toute modification serait un nouveau HEAD et une nouvelle campagne de preuves ciblées.
