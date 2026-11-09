# STATE — DigitalCrown

## DÉCISION PROPRIÉTAIRE — 2026-11-09 — LOT08 logiciel/LAB ≠ LOT10 physique

**Cette décision prime sur les anciens checkpoints « NO-GO merge car tests physiques non exécutés » contenus plus bas.** La roadmap officielle [V1.5-10 — Tests physiques exclusivement](https://app.notion.com/p/3e677c66336281fcbe65f8889baf8c6a) réserve la validation matérielle/terrain au **LOT10** : 10.1 (installation postes), 10.2 (Queue Core réel), 10.7 (incidents/sécurité terrain), 10.8 (réception humaine). Le premier enrôlement physique Admin `issue→enroll→recover`, les ACL sur installation réelle, la récupération offline et le refus d'autres profils sont **PHYSICAL NOT_RUN / LOT10**. Ils ne sont **pas un préalable de clôture logicielle/merge du LOT08.2-A** ; l'utilisation clinique reste interdite jusqu'aux gates terrain applicables.

**Preuves 08.2-A :** [Windows Actions #42596486051](https://github.com/hraaaaf/Digital_crown/actions/runs/42596486051) SUCCESS sur SHA exécutable `1b4380735932896b8b7a38485b2af709182c796c`, **53/53 tests PASS**, création Win32 et vérification ACL réelles uniquement sous RUNNER_TEMP, refus CLI non interactive sans modification ProgramData, refus ACL non conforme ; [Ubuntu FUE-0 #42596493320](https://github.com/hraaaaf/Digital_crown/actions/runs/42596493320) SUCCESS. Une **décision de clôture du logiciel** doit considérer revue SEC, CI, risques et périmètre, sans exiger le terrain physique.

**PR #1238 :** reste DRAFT/non fusionnée **en attente d'une décision d'intégration distincte du propriétaire et des contrôles logiciels applicables, pas d'une preuve physique LOT10**. Pas de déploiement, d'installation cabinet ou de passage automatique à 08.2-B–E. **Next exact :** revoir les preuves et le diff logiciel A, proposer décision de merge ; si approuvée, merge + contrôles post-merge, puis poursuivre roadmap logicielle. Les précédentes mentions contradictoires documentent le gate erroné désormais supersédé.

## LOT08.2-A — Windows GitHub Actions ACL complémentaire — 2026-11-09 — CI PROUVÉ / PHYSIQUE OPEN

- **PR #1238 : OPEN/DRAFT/NOT MERGED**, [preuve Windows Actions #42596486051](https://github.com/hraaaaf/Digital_crown/actions/runs/42596486051) **SUCCESS** sur SHA exact testé `1b4380735932896b8b7a38485b2af709182c796c`, Windows hosted runner et Python 3.12. La suite `queue_core/tests` **53/53 PASS** ; non-interactive `status` refusé `INTERACTIVE_CONSOLE_REQUIRED` sans effet sur ProgramData ; **vraie création Win32 d'un dossier et fichier temporaires** sous RUNNER_TEMP avec validation owner/ACE réelle Get-Acl + refus ACL non conforme. Artifact JUnit non médical. Aucun accès cabinet ni donnée patient.
- **Linux FUE-0 existant** [#42596493320](https://github.com/hraaaaf/Digital_crown/actions/runs/42596493320) **SUCCESS** sur ce SHA ; correctif de l'oracle du test de refus sous non-Windows (attendre LOCAL_WINDOWS_CONSOLE_REQUIRED) inclus. Le code sécurité runtime est resté inchangé depuis le SHA source sécurité revu `44bc6fc639332796f064dbf18a59a4f8b5c3333f`.
- **Diagnostic des premiers FAIL :** Powershell 7 runner -> sous-processus Windows PowerShell 5.1 incapable d'auto-charger `Microsoft.PowerShell.Security` pour `Get-Acl`. La même vérification exécutée directement sous Windows PowerShell 5.1 (shell natif dans Actions) est PASS. Ce n'était pas une preuve de permissions correctes tant que la vraie vérification n'était pas PASS.
- **STOP MAINTENU :** runner hébergé ≠ console physique locale élevée. Aucun `issue→enroll→recover` réel à la console LAB, aucune vérification d'identité utilisateur non privilégié par second profil humain, aucune restauration hors ligne réelle sur poste LAB : **NOT_RUN**. Aucun merge, déploiement, installation cabinet, 08.2-B/C/D/E ni certification clinique autorisés. **Next exact :** Windows LAB physiquement isolé, Admin élevé local, recette première inscription + ACL + récupération offline, preuves expurgées, puis gate humain GO/NO-GO.
- **Fichier canonique :** ce checkpoint documentaire est ajouté après la CI ; le SHA testé `1b438073...` reste la preuve exécutable. Toute différence de SHA ultérieure doit être réconciliée par comparaison du delta, sans déclarer une nouvelle CI PASS si elle n'a pas tourné.

## LOT08.2-A — Local Windows identity/bootstrap — IN PROGRESS / DRAFT (2026-11-09)

- **2026-11-09 SEC review current source `44bc6fc639332796f064dbf18a59a4f8b5c3333f`**: independent read-only Codex delta review from `09f3d40e` reports **no actionable defect**. Prior full review found P2 stale expired session rows; corrected within serialized login transactions, including denied logins, with negative retention test. **53/53 direct Windows Python 3.12 PASS postcommit**, compileall exit 0, git clean. Directory/file SDDL accepted by Windows API without writes, remote CLI rejected with `INTERACTIVE_CONSOLE_REQUIRED` exit 2 and no real auth-store file created. [SEC review report](docs/v1.5/V15_08_2_A_SECURITY_REVIEW_20261109.md). **Physical elevated Windows console positive bootstrap/ACL NOT RUN; PR #1238 remains DRAFT / NO-GO merge or clinic install pending physical LAB proof**. No 08.2-B GO.

- **2026-11-09 independent Codex review on SHA 09f3d40e:** found P2 unbounded expired sessions retained in SQLite. Fixed under the login transaction by pruning `expires_epoch <= now` even on denied logins; added negative synthetic retention test. **53/53 direct Windows Python 3.12 PASS**, compileall and diff check PASS. New exact SHA and separate final review still required. Physical Windows local elevated console enrollment/ACL positive **NOT_RUN**; no clinical use, merge, 08.2-B or deploy.

- **2026-11-09 separate Codex review on e3513ac9:** no P1/P2 findings; one P3: read-only `status` unexpectedly created an auth directory before first enrollment. Fixed `windows_cli._database_path(initialize=False)` to inspect without creating, with a regression test. **52/52 direct Windows Python 3.12 PASS**, compileall and diff-check PASS. Fresh reviewer required on the *new* commit; physical elevated Windows-console positive enrollment/ACL still NOT_RUN, no real auth store created and no merge under this checkpoint.

- **SEC critical review #1, initial SHA 58e3b5e7:** independent targeted Codex SEC/OPS review identified P1 directory-owner ACL spoof and P2 dangling reparse bypass. Corrected with atomic Windows SDDL protected CreateDirectoryW/CreateFileW, trusted SID owner and both distinct required ACEs, non-following `lstat()` and `FILE_FLAG_OPEN_REPARSE_POINT`, with synthetic negative/static Win32/PowerShell tests. **51/51 direct Windows Python 3.12 PASS on preceding e3513ac9.** Subsequent 2026-11-09 review P3 correction now **52/52 PASS**. Real elevated physical console creation/ACL remains NOT_RUN. New SHA needs another independent security review before merge.

- **GOAL:** standalone Queue Core first Admin enrollment on a physically local elevated Windows console, no Internet, Firebase, patient records or clinical database access.
- **Owner GO:** « Play 8-2 A go ». This authorizes implementation of A only, not merge/release or 08.2-B–E.
- **BASE:** `edf26bb7ff70904b802069891f31ef3b4dc7691d` master (LOT08.1 CLOSED 29/29). Worktree `feat/v15-08-2-a-local-admin-bootstrap-20261108`, isolated branch.
- **DELIVERABLE CANDIDATE:** `queue_core/security/local_auth.py` (SQLite local auth + bootstrapping), `windows_console.py` OS privilege/console gate, `windows_cli.py` ProgramData ACL-controlled offline CLI, synthetic negative unit tests and `docs/v1.5/V15_08_2_A_LOCAL_ADMIN_BOOTSTRAP_CONTRACT.md`.
- **PRELIMINARY DIRECT WINDOWS EVIDENCE:** Python 3.12 `pytest -q queue_core/tests` **52/52 passed** (29 08.1 + 23 08.2-A incl. Windows ACL/symlink hardening and read-only status); compileall PASS. Real Remote Desktop Commander shell `python -m queue_core.security.windows_cli status` denied with `INTERACTIVE_CONSOLE_REQUIRED` exit 2; `ProgramData\DigitalCrownQueueCore\local_auth.sqlite` absent before/after. NO real admin account or recovery secret generated; tests use temp SQLite synthetic fixtures and injected guard.
- **SECURITY CONTRACT:** 256-bit random bootstrap (10min), single use/5-attempt cap; scrypt salted passwords, opaque SHA-256 session verifier and lockout, 8h sessions; separate 256-bit offline recovery secret, one-time rotation and all-session revocation. Restricted Windows physical console and ACL verification; no public route. No default admin.
- **UNVERIFIED / BLOCKED FOR REAL USE:** actual elevated physical Windows-console onboarding, DirectorySecurity Set-Acl success on target PC, backup/restore/installed service, session-cookie/network auth, multi-tenant RBAC, kiosk/QR, standalone runtime and legal G3. Risk-critical source needs independent SEC/OPS review on exact SHA before any merge, with negative tests and correction loops. No automation GitHub Actions requested.
- **NEXT:** commit & push DRAFT PR, direct Windows proof exact SHA, separate reviewer, POST Notion. Do NOT merge, install or begin 08.2-B without distinct GO.

## LOT08.1 — Queue Core domain contracts — CLOSED / POST-MERGE VERIFIED (2026-11-08)

- **GOAL:** isolated standalone Queue Core domain state machine, dynamic ranking, auditable event plans, dedicated SQLAlchemy schema and synthetic FUE-0. **Delivered:** G1 transitions/rank oracles, manual NO_SHOW and queue.override, tenant/resource constraints, active chair occupancy, provenance and SQL integrity checks. No clinical DB coupling, migration, patient data or runtime deployment.
- **RESULT:** [PR #1234](https://github.com/hraaaaf/Digital_crown/pull/1234) **MERGED**; final contributor SHA `1df36d79a694f713cb19b112ae26831501cf1678`; squash master SHA `a5c47f5efcc7b9843a9fea13799bae073ca541e7` (based on parent master `16f531f04eb7daff3bf5d75017717e12927f47ab`). Owner GO "Green" captured.
- **PROOF POST-MERGE Windows:** authorized device DESKTOP-3MAJEEH, isolated worktree checked out on the exact master merge SHA; Python 3.12 `pytest -q queue_core/tests` **29/29 PASS**, `compileall -q queue_core` **PASS**, clean git tree. No GitHub Actions tests deliberately launched; older green runs belong to earlier contributor SHAs and are not evidence for this one.
- **INDEPENDENT CODE REVIEW:** fresh Codex CLI read-only agent on final contributor SHA against updated `origin/master`: no definite actionable defects reported. Its default Python 3.14 lacked pytest; only separate Windows 3.12 tests substantiate FUE. Earlier distinct reviews identified P1/P2 defects corrected and re-tested. This is **AI code review, not medical or human signoff**.
- **CLOSEOUT SCORES (08.1 scope ONLY):** EXECUTION 9.0/10, FUE_EVIDENCE 9.0/10, RETAINED 9.0/10 (minimum). FUE-0 applicable and demonstrated, no UI exists in 08.1; FUE-I/G and installed runtime remain later sublots. Final independent review + postmerge tests serve as scoped Perfection Pass.
- **LIMITS:** `call_visit` cannot prove candidate completeness; future 08.3 MUST load authoritative candidates under DB transaction lock and atomically commit resource state, audit and versions. No durable append-only, encryption, RBAC, kiosk/QR, API/SSE, webhooks, UI, backups/restore or real patient enablement is claimed.
- **HANDOVER:** `docs/v1.5/V15_08_1_QUEUE_CORE_CLOSEOUT_20261108.md`; contract `docs/v1.5/V15_08_1_QUEUE_CORE_DOMAIN_CONTRACT.md`; historical detailed review trail in `techdoubt.md` and [canonical Notion LOT08](https://app.notion.com/p/3ec77c66336281d59cdcffe610561f86).
- **NEXT EXACT:** 08.2 local identity/RBAC/device/QR requires separate GO and fresh preflight; no 08.2 start, merge beyond closeout documentation, clinic release or Vercel deployment under this approval.

# LOT07 V1.5 Desktop Experience & MultiView — 2026-11-08 — INTEGRATED DELIVERY CLOSED (LIMITED SCOPE)

- **Scope closed:** R8.3 + POLISH-01 + POLISH-02 (historical merge and postmerge CI success 2026-10-31), plus Windows B10 true NVDA certification workflow fix PR #1228, source head `68279047d9d73a501f18a1e5c7fb235f241deae7` merged at `1131f117254894d208490b2b6916fd2a4799d18b`.
- **Proof B10 source:** Windows actual NVDA, native zoom and synthetic authenticated FastAPI/React [run #42481818872](https://github.com/hraaaaf/Digital_crown/actions/runs/42481818872) SUCCESS (18 screenshots, 104 checks), owner Human Visual Approval [#42504061075](https://github.com/hraaaaf/Digital_crown/actions/runs/42504061075) SUCCESS.
- **Proof postmerge:** [Cabinet Upgrade PostgreSQL Certification #42504229531](https://github.com/hraaaaf/Digital_crown/actions/runs/42504229531), **2/2 SUCCESS** on the B10 merge commit. Merge diff is exactly one CI workflow and one synthetic browser test script, no patient/clinical runtime changes.
- **Historical DRAFT disposition:** #1131 (R5) CLOSED/NOT MERGED, core R5 API/preferences modules present on master; #1109 (R3) CLOSED/NOT MERGED, historical 3-pane DEV pilot NOT SHIPPED. The nine declared layout starting points on master are **not nine independently certified clinical UIs**. Numerous historical DRAFTs remain outside this verified closure and are not silently certified. No clinical or patient data imported.
- **Future scope:** R3 prototype and missing 3-pane specialist views are **unshipped/deferred**, preserved in [Notion backlog](https://app.notion.com/p/41277c66336281cc9654e5e69fe4e2d4), with branch/PR history intact; if deemed REQUIRED by owner, reopen LOT07 scope before treating it as completed. No blanket clearance for unimplemented clinical interfaces.
- **Roadmap:** [LOT07 canonical closeout](https://app.notion.com/p/40277c66336281b6b7ffeeecae6baff9) and [V1.5 roadmap](https://app.notion.com/p/3e677c66336281d88c82d2fbe43835fb). LOT08 G6 is cleared only for this delivered, bounded LOT07 scope. Resume LOT08 preflight against current master, and still lock G1-G5 before 08.1. 35 SP LOT08 re-estimate remains tentative, not approved baseline.
- **No release:** no Vercel, no cabinet PROD deployment, no physical multi-monitor / OS DPI200 field certification; physical tests at LOT10.

**NEXT EXACT:** Re-check current master SHA/CI, confirm relevant LOT07 closure and any REQUIRED scope exception; re-run LOT08 PRE / domain/tenant/visits before any LOT08 implementation. No implicit permission for real patient data, migration, merge of future features or production.

---


> Fichier de reprise canonique. Historique pré-audit : `docs/archive/STATE_2026-07-21.md`.

# Etat canonique scientifique — 2026-10-07

## LOT08 — Facad Ricketts 32F compatibility disposition — MERGED / POST-MERGE CLOSEOUT PENDING

- Repository: `hraaaaf/Digital_crown`
- PR: `#775` — MERGED / CLOSED
- Branch: `feat/ortho-studio-lot08-ricketts-protocol-v2`
- exact evidence HEAD before docs closeout: `575fc9e2ad21133763bdacbe512e7591a39b9f59`
- Facad source: official 3.14.1.1111 `Ricketts (32 F).cph`
- pinned profile SHA-256: `d0b442b39ac7db3dc9c46d807cb3c20bd937c69783b096b484872017f9376518`
- originally unmapped compatibility rows: **26**
- explicitly dispositioned compatibility rows: **26/26**
- remaining `unmapped`: **0**
- important boundary: **26/26 dispositioned does not mean 26 runtime aliases**. Vendor variants, landmark-authority differences, signed/presentation parity gates and non-authoritative Facad norms remain fail-closed.
- final targeted workflow: `Facad Ricketts 32F final seven contract #2` — **SUCCESS** on `575fc9e...`
- explicit adversarial review A (science/provenance): **15/15 PASS**, 0 BLOCKER / 0 MAJOR
- explicit adversarial review B (CI/reproducibility): **14/14 PASS**, 0 BLOCKER / 0 MAJOR
- additional confirmation pass: **10/10 PASS**
- final Perfection Pass: **16/16 PASS**
- final scores on evidence HEAD: EXECUTION **9.4/10**, ADVERSARIAL **9.4/10**, RETAINED **9.4/10**
- no frontend product delta; no clinical runtime activation in the final compatibility-disposition clusters
- Vercel: **NOT AUTHORIZED / NOT USED**
- merge commit: `c7209e9d35f0a85a12ee1725589bca2863aa6607` — **MERGED**

Canonical closeout source:
- `docs/handovers/2026-10-07-ricketts32-compatibility-closeout.md`

**Next exact:** merge the docs-only post-merge reconciliation PR after its exact-head documentary checks are green; then perform a read-only master coherence check and mark the LOT08 Ricketts 32F compatibility closeout fully closed.

# Etat canonique manuel - 2026-10-01

## V1.5-01 — Cabinet topology & workstation roles — CLOSED

- PR topology/workstation harness: #734 — MERGED
- merge commit #734: `a37367dcc3283ef2cb89fd79f736b387171ed89d`
- follow-up deterministic Honoraires harness: PR #738 — MERGED
- exact candidate head #738: `5de868634a2335bce13a306b70124a58d33f99d9`
- final merge commit: `b7c6d25b99e1de2b5a8e937f0909ba02b040f99e`
- T2 PR certification #5948 / run `36894203496`: **SUCCESS** end-to-end
- PR CI #7129 / run `36894203439`: **SUCCESS**
- post-merge master CI #7132 / run `36912825476`: **SUCCESS**
- post-merge Cabinet Upgrade PostgreSQL #1091 / run `36912825240`: **SUCCESS**
- deterministic Honoraires period: fixed September 2026 fixture + explicit Accounting UI period selection; no UTC/local month rollover dependency
- WorkstationModeGate/auth: unchanged by the hardening follow-up
- production runtime: unchanged by PR #738
- double-check internal review: **9.7/10**
- triple-check adversarial internal review: **9.6/10**
- Vercel: **NOT AUTHORIZED / NOT REQUIRED**

**Next exact:** open **V1.5-02 — Patient Identity & Photo**.

# Etat canonique manuel - 2026-09-30

## V1.5-00 — Hub & Dispatcher — CLOSED

- PR closeout: #724 — MERGED
- merge commit: `2f0fdeb4583e633e479627a275d7da2d6bc1375e`
- exact candidate head: `f406ae767f2585e468a15cbc65ce5d106573e9f1`
- targeted Hub/Gate/Station/Admin tests: **17/17 PASS**
- Hub Visual Proof run `36788607154`: **SUCCESS**
- Human Visual Approval run `36790450196`: **SUCCESS**
- double-check exact-head: **9.3/10**
- triple-check adversarial exact-head: **9.0/10**
- post-merge code identity: the four touched Hub/Gate runtime+test blobs are byte-identical between candidate HEAD and merge commit
- V1.5-00 residual gap closed: Control Center remains fail-soft as a local recovery surface while clinical routes remain fail-closed; Station remains restrictive
- CI doctrine: only directly impacted tests/builds/workflows are proof-relevant; broad unrelated frontend/browser matrices are not rerun or treated as blockers unless a transverse dependency or invariant requires it
- Vercel: **NOT AUTHORIZED / NOT REQUIRED**

**Next exact after closeout docs merge:** open **V1.5-01 — Cabinet topology & workstation roles**.

# Etat canonique manuel - 2026-09-29

## V1 — CLOSED / V1_OPERATIONAL

- Repository: `hraaaaf/Digital_crown`
- V1-08 initial freeze: **CLOSED** - `3c86e72bf0e132e6f79bc336d4ff9eb121d08fab`
- V1-09 installability: **CLOSED / INSTALLABLE_CERTIFIED**
- V1-10 real cabinet activation: **CLOSED / VERIFIED**
- Final certified/installed V1 SHA: `bce60b26059054ba43cf8ec13cd210098e648ea4`
- Installed release: `dc-cabinet-bce60b260590-run36628947897`
- `INSTALLABLE_CERTIFIED`: **OUI**
- `V1_OPERATIONAL`: **OUI**
- Evidence-carrying master before docs closeout: `6966ebf2656f78dd6674d435bc806bd659248d0f`
- Master CI `36638379136`: **SUCCESS**
- PostgreSQL certification `36638379156`: **SUCCESS**
- Live cabinet: health/db/storage HTTP 200; normal launcher restart OK
- Preservation: 434/434 document archives and 2915 media files; integrity PASS
- Rollback: fresh encrypted DB/media backup retained; isolated historical rollback rehearsal documented
- Limitation: V1-10 does not claim comparative visual UX certification
- Vercel: **NOT AUTHORIZED / NOT REQUIRED**

## Continuite

V1 is **CLOSED** and operational on the real cabinet. No V1 execution lot remains. After this final canonical documentation closeout is merged and re-read on `master`, execution authority transfers to the canonical POST-V1 / V1.5 roadmap. Next exact: **V1.5-00 — Hub & Dispatcher**.

# Historique canonique — 2026-08-14

## Baseline vérifiée

- Repository : `hraaaaf/Digital_crown`
- `master` après merge P0-6 : `412ab81cc5c47b7220865881f83836b539458a69`
- PR P0-6 : `#12` — MERGED
- Head candidat P0-6 certifié : `8dfe6bcfd866f62a1b41aca08554246411ad67e4`
- CI P0-6 : run `31810762297` — SUCCESS
- Backend tests/durcissement : **SUCCESS**
- Frontend tests/build : **SUCCESS**
- Garde production négative : **SUCCESS**

## Doctrine produit confirmée

- Application **on-premise / local-first**.
- Firebase : identité/licence, jamais source de vérité des dossiers patients.
- Architecture courante : modèles locaux + moteurs déterministes ; aucun LLM requis.
- Donnée patient requise mais absente = inconnue/non-évaluable ; jamais inventée.
- `tests green != validation scientifique`.
- Dans ce projet, `review` signifie par défaut **double-check complet par l’agent**, sauf demande explicite d’un reviewer externe.

## P0 — Safety & Integrity — CLOSED ✅

### P0-1 — PRESCRIPTION-MISSING-DATA-FAIL-CLOSED — CLOSED ✅

Objectif : empêcher toute valeur patient synthétique/estimée de déclencher un calcul patient-spécifique lorsqu’une donnée requise manque.

Implémentation intégrée :
- garde backend explicite `evaluable/non_evaluable` ;
- âge absent reste `None` ;
- poids absent n’est jamais synthétisé ;
- antécédents absents restent explicitement incomplets ;
- enfant sans contexte sûr ne passe pas dans le chemin pédiatrique legacy ;
- plan non évaluable = zéro ligne automatique ;
- `PrescriptionGuideModal` exige un poids explicite pour l’automatisme pédiatrique ;
- `estimateWeightFromAge()` est neutralisé ;
- top-level `assessment.age` est masqué lorsque le contexte n’est pas évaluable ;
- tests backend/frontend missing-data ajoutés.

Double-check final avant merge :
- restauration de tests `clinical_rules_engine` + `habits_engine` supprimés accidentellement ;
- test honoraires rendu déterministe, sans assertion permissive `409 ou 422` ;
- diff final : 16 fichiers, aucun fichier parasite ;
- couverture backend finale : **2459 passed, 7 skipped, 0 failed**.

Limite explicite :
- ce lot **ne valide pas scientifiquement** les constantes thérapeutiques/doses historiques du moteur legacy ;
- ces constantes restent une dette scientifique distincte.

Dette CI non bloquante :
- la CI force `httpx==0.27.2` pour compatibilité Starlette/TestClient ;
- cela entre en conflit déclaré avec `firebase-admin 7.5.0` et `ultralytics-platform 0.1.4`, qui demandent `httpx>=0.28` ;
- correction durable à traiter séparément : upgrade FastAPI/Starlette ou isolation des dépendances de test.

### P0-2 — CMO-NON-PRESCRIPTIVE-BOUNDARY — CLOSED ✅

Objectif : empêcher la synthèse CMO de transformer des mentions textuelles documentaires en diagnostic, pronostic ou décision thérapeutique autonome.

Implémentation intégrée :
- synthèse CMO convertie en signaux documentaires uniquement ;
- conservation des clés de réponse historiques nécessaires à la compatibilité ;
- ajout explicite de `evidence`, `uncertainty`, `practitioner_validation_required=True` et `automation_scope="signal_only"` ;
- pronostic autonome neutralisé en `Non déterminé automatiquement` ;
- aucune décision automatique d'initier, reporter ou modifier un traitement orthodontique ;
- mémoire Ghost CMO reclassée en `SIGNAL_CLINIQUE` ;
- tests ciblés couvrant les signaux textuels et le cas de texte négatif traité comme mention à valider, jamais comme diagnostic.

Certification :
- PR `#6` — MERGED ;
- head candidat certifié : `84c14bb54068d21a9d7c668b5d041fdac7d93e01` ;
- CI : run `31758201657` — SUCCESS ;
- backend : **2462 passed, 7 skipped, 4 warnings, 0 failed** ;
- frontend tests/build et garde production négative : **SUCCESS** ;
- merge commit : `6def2a2501cd687f5fa9be03741206b77b02643f`.

Limite explicite :
- la détection reste lexicale et peut relever une mention négative ou hors contexte ; elle est exposée comme **signal incertain à valider**, jamais comme conclusion clinique.

### P0-3 — SQLCIPHER-FAIL-CLOSED — CLOSED ✅

Objectif : empêcher un cabinet on-premise configuré sur SQLite disque de démarrer en clair si SQLCipher est indisponible ou si la migration de chiffrement échoue.

Implémentation intégrée :
- `ENVIRONMENT=cabinet` + SQLite disque impose désormais SQLCipher ;
- driver `sqlcipher3` absent = `RuntimeError` bloquant avant ouverture d'une SQLite non chiffrée ;
- migration plaintext → SQLCipher échouée = restauration du fichier d'origine puis démarrage refusé ;
- `development` et SQLite `:memory:` restent compatibles avec la CI/tests ;
- tests subprocess forcent l'absence de `sqlcipher3`, couvrent le refus de démarrage, la restauration du fichier plaintext et la non-régression development.

Certification :
- PR `#8` — MERGED ;
- head candidat certifié : `bf01fc9b66848c64ba159924ceb900da90d886fe` ;
- CI : run `31785414095` — SUCCESS ;
- backend : **2465 passed, 7 skipped, 4 warnings, 0 failed** ;
- frontend tests/build et garde production négative : **SUCCESS** ;
- merge commit : `c4adedb6528d586e3a8ec8fa5c52e33069cfb9f3`.

### P0-4 — PARTIAL-PAYMENT-NO-INFERENCE — CLOSED ✅

Objectif : empêcher `documents/generate` de créer un véritable `Payment` partiel à partir d'un montant inventé lorsque le contrat ne transporte aucun montant encaissé explicite.

Implémentation intégrée :
- `DocumentRequest` refuse `payment_status=PARTIEL` sans montant encaissé explicite ;
- le flux dédié `/accounting/payments` reste le chemin autorisé pour un paiement partiel car `PaymentCreate.amount` y est obligatoire ;
- `EN_ATTENTE` et `PAYE` restent valides ;
- tests dédiés couvrent le refus fail-closed et l'absence d'écriture partielle inférée ;
- le test financier legacy a été réaligné sur `PAYE` afin de ne plus codifier l'ancien comportement dangereux.

Certification :
- PR `#9` — MERGED ;
- head candidat certifié : `7e5066d1dd53abfde33ad5e8043cd1c5d14c4d37` ;
- CI : run `31805059079` — SUCCESS ;
- frontend tests/build et garde production négative : **SUCCESS** ;
- merge commit : `a99025d67a5470219369c633570a617e19f6f557`.

Limite UX connue :
- le bouton `PARTIEL` du Document Studio reste fail-closed jusqu'à ajout d'un vrai champ montant encaissé ; aucune valeur financière ne doit être devinée entre-temps.

### P0-5 — PRESCRIPTION-SAFETY-TENANT-GUARD — CLOSED ✅

Objectif : empêcher `POST /api/prescriptions/safety/check` de lire ou évaluer un patient hors tenant avant l'appel au service clinique.

Implémentation intégrée :
- `assert_patient_access(patient_id, current_user, db)` s'exécute avant `prescription_service.check_safety(...)` ;
- un patient d'un autre tenant produit `403 Accès refusé` ;
- le service de sécurité n'est jamais appelé pour ce patient ;
- test cross-tenant dédié ajouté.

Certification :
- PR `#11` — MERGED ;
- head candidat certifié : `d579750ce5897f86e902cf70b4e5003d188f1762` ;
- CI : run `31807332356` — SUCCESS ;
- frontend tests/build et garde production négative : **SUCCESS** ;
- merge commit : `67dc6620f5667ad4060592ef5662379fc720b6f9`.

### P0-6 — PREVIEW-MUST-BE-READ-ONLY — CLOSED ✅

Objectif : garantir qu'une preview documentaire ne persiste aucun état comptable ou archive en base.

Implémentation intégrée :
- les previews d'échéancier à données directes utilisent `flush()` puis `rollback()` au lieu de commits durables ;
- `DocumentFactory.create_installment_plan(..., archive=False)` désactive la création de `DocumentArchive` en preview ;
- le chemin preview avec `plan_id` existant désactive lui aussi l'archivage ;
- le log d'audit `GENERATE` n'est pas persisté en preview ;
- `DocumentRequest` accepte explicitement `echeancier`, alignant le contrat avec le routeur ;
- test dédié vérifie que `InstallmentPlan`, `Installment` et `AuditLog` restent inchangés et que la factory reçoit `archive=False`.

Certification :
- PR `#12` — MERGED ;
- head candidat certifié : `8dfe6bcfd866f62a1b41aca08554246411ad67e4` ;
- CI : run `31810762297` — SUCCESS ;
- backend tests/durcissement, frontend tests/build et garde production négative : **SUCCESS** ;
- merge commit : `412ab81cc5c47b7220865881f83836b539458a69`.

## P1 — Hardening — ACTIVE

### P1-1 — NATIVE-SECURE-STORAGE — CLOSED ✅ (N/A runtime courant)

Constat vérifié : le client actuel est une PWA React/Vite et le dépôt ne contient aucun runtime natif Capacitor/Tauri/Electron ni dépendance Keychain/Keystore/SecureStore à câbler.

Décision :
- ne pas introduire un wrapper natif artificiel uniquement pour satisfaire la roadmap ;
- le runtime web courant ne doit pas persister de bearer secret longue durée dans `localStorage`, `sessionStorage` ou IndexedDB ;
- tout futur client natif devra stocker les credentials longue durée exclusivement dans le Keychain/Keystore du système.

### P1-2 — MOBILE-CREDENTIAL-LIFETIME-REVOCATION — ACTIVE

Objectif : réduire l'exposition des credentials mobiles longue durée et vérifier une révocation réellement fail-closed.

Constats initiaux :
- le flux mobile/ZKA émet actuellement un bearer JWT avec une durée de vie de 365 jours ;
- une infrastructure `jti`/blacklist existe déjà et doit être conservée puis testée, pas réinventée ;
- le flux de claim one-shot doit être vérifié pour ne pas consommer définitivement le token avant validation complète du handshake.

### P1-3 — CABINET-SETTINGS-STRICT-WHITELIST

Whitelist Pydantic stricte pour les paramètres cabinet ; pas de mass assignment générique.

### P1-4 — PATIENT-SCOPED-TENANT-AUDIT

Audit tenant exhaustif des routes patient-scopées.

### P1-5 — UPLOAD-MIME-MAGIC-BYTES

MIME + magic bytes systématiques sur uploads sensibles.

### P1-6 — FRONTEND-HASACCESS-CENTRALIZATION

Centraliser `hasAccess()` frontend.

### P1-7 — LEGACY-ENGINE-QUARANTINE

Quarantainer/supprimer les anciens moteurs non utilisés.

## P2 — Certification

- CI sur le head réellement candidat.
- Backend + frontend + build.
- Smoke live/rehearsal ciblé selon le risque.
- Audit visuel 390 / 768 / 1280 pour les lots UI concernés.
- Accessibilité clavier/ARIA sur contrôles custom.
- Validation scientifique céphalométrique source par source avant toute revendication autoritative.

## Skills scientifiques applicables

- `.claude/skills/audit-prescription-flow/SKILL.md`
- `.claude/skills/audit-clinical-diagnosis-flow/SKILL.md`
- `.claude/skills/audit-panoramic-report-pipeline/SKILL.md`
- `.claude/skills/validate-cephalo-pipeline/SKILL.md`
- `.claude/rules/scientific-engineering.md`

## Lot actif

### LOT P1-2 — MOBILE CREDENTIAL LIFETIME + REVOCATION — ACTIVE

---

## Document Studio — chantier actif — 2026-08-15

Roadmap canonique : `DOCUMENT_STUDIO_ROADMAP.md`.

### R1 — P0 Cohérence médicament / Maroc-first — CLOSED ✅
- PR `#17` — MERGED.
- Head certifié : `8063b11b061ea6d1912e1b4e1a0ab8ef1fcb649a`.
- CI : run `31852032393` — SUCCESS.
- Merge : `e32ab311f72980e0797b93a306c3616a4ff66042`.

### R2 — P0 Persistance protocoles/habitudes — CLOSED ✅
- PR `#19` — MERGED.
- Head certifié : `ba66457e5f65917f71670e151826062442525200`.
- CI : run `31852827218` — SUCCESS.
- Merge : `432a95eca05d1d7b9781d2d8e81077f0dcb589f2`.

### R3 — P0 Safety orchestration — CLOSED ✅
- PR `#20` — MERGED.
- Head certifié : `becadcafb4ba0e6a5f4fda10a0053bb92c96fe1e`.
- CI : run `31853962025` — SUCCESS.
- Frontend tests/build : SUCCESS.
- Backend tests/durcissement : SUCCESS.
- Garde production négative : SUCCESS.
- Merge squash : `75e4693dc983ba1708914d16432504bea8f0cd8c`.
- Le Studio n'affiche plus d'état safety vérifié avant succès réel du backend ; états explicites `unchecked/checking/verified/error`.
- Dette R3 non bloquante : appel safety read-only parallèle encore présent dans `DocumentHub`, à dédupliquer lors du prochain lot pertinent.
- Aucune certification clinique/scientifique humaine revendiquée.

### R4 — P0 Dirty-state & actions — CLOSED ✅
- PR `#21` — MERGED.
- Head certifié : `cdaf28874bc9155d115108bba7548470300c5ca1`.
- CI : run `31855874418` — SUCCESS.
- Frontend tests/build : SUCCESS.
- Backend tests/durcissement : SUCCESS.
- Garde production négative : SUCCESS.
- Merge : `6a4debe01cf0e0ea78e49ed787cae5e26c4976b8`.
- Dirty-state dérivé du fingerprint ordonnance complet ; garde onglet/navigateur ; reset après archivage ; actualisation contexte explicite.
- Le fallback source `forme: d.forme || 'Sachets'` existe encore dans le legacy, mais son effet caché est neutralisé à la frontière transport et la forme manquante est explicitée dans l’UI.
- Aucune certification UX runtime ni clinique/scientifique humaine revendiquée.

### R5 — P1 Fast Prescription UX — CLOSED ✅
- PR `#22` — MERGED.
- Head certifié : `6de453962668e66be9e26978ec07fc9082afacb7`.
- CI : run `31878337816` — SUCCESS.
- Frontend tests/build : SUCCESS.
- Backend tests/durcissement : SUCCESS.
- Garde production négative : SUCCESS.
- Merge : `8957635e1bd50d8f44fbcef38c529b3c27f8fb32`.
- Quick-picks praticien issus des habitudes réelles : récents + fréquents. Aucun favori étoilé explicite inventé.
- Aucune certification UX runtime ni clinique/scientifique humaine revendiquée.

### R6 — P1 Protocoles + Référentiel — CLOSED ✅
- PR `#23` — MERGED.
- Head certifié : `10751078601c3aa5be728bc263e25a58e856c676`.
- CI : run `31879112143` — SUCCESS.
- Frontend tests/build : SUCCESS.
- Backend tests/durcissement : SUCCESS.
- Garde production négative : SUCCESS.
- Merge : `6f2b8a22f9cdca25cafe228f266ed46deee8281b`.
- Référentiel search-first, ajout manuel replié, contexte âge/poids visible, `Mes protocoles` réversible après masquage.
- Aucune certification UX runtime ni clinique/scientifique humaine revendiquée.

### R7 — P1 Contexte + Preview premium — CLOSED ✅
- PR finale `#26` — MERGED.
- Head certifié : `9a39ecc4d415e59c5457a58638a48ba0c22f81fd`.
- CI : run `31879649826` — SUCCESS.
- Frontend tests/build : SUCCESS.
- Backend tests/durcissement : SUCCESS.
- Garde production négative : SUCCESS.
- Merge squash : `2596da527fdd1bee5c6746f645e995f682ca3189`.
- PR intermédiaires `#24` et `#25` fermées sans merge car remplacées par le candidat consolidé sur baseline post-R6.
- Contexte patient et preview utilisent une terminologie déterministe ; preview responsive ; test backend prouve qu’une ordonnance `preview=true&archive=true` ne crée ni archive, ni audit, ni paiement, ni acte.
- Aucune certification UX runtime ni clinique/scientifique humaine revendiquée.

### P1 Ordonnance — ENGINEERING CLOSED ✅
- R1→R7 fermés et fusionnés.
- Roadmap canonique synchronisée.
- Interaction runtime et recertification UX/clinique restent des gates séparés et ne sont pas revendiqués.

### P2 Devis + Honoraires — ACTIVE 🟡
- Audit canonique : `docs/audits/DOCUMENT_STUDIO_P2_DEVIS_HONORAIRES_AUDIT.md`.

#### P2-A — Prix catalogue local conservé — CLOSED ✅
- PR `#27` — MERGED.
- Head certifié : `7289d0bf64c8139838470923622f8c0b588206e1`.
- CI : run `31882328096` — SUCCESS.
- Frontend tests/build : SUCCESS.
- Backend tests/durcissement : SUCCESS.
- Garde production négative : SUCCESS.
- Merge squash : `a8ce1f8143fd58f20aee5cb4ebb9b8827128c4cc`.
- Le wrapper répare uniquement les suggestions locales dont le prix catalogue existe ; aucun prix absent n’est inventé.

#### P2-B — PARTIEL fail-closed cohérent UI/backend — CLOSED ✅
- PR `#29` — MERGED.
- Head certifié : `d60a99c290e0e27c84d73fb95d947fa111461f7a`.
- CI finale : run `31884437013` — SUCCESS.
- Frontend tests/build : SUCCESS.
- Backend tests/durcissement : SUCCESS.
- Garde production négative : SUCCESS.
- Merge squash : `6543c3dad146bdbe055117fe0302b3fbe9cbda07`.
- Premier head `1005f2281868f435b8fb2f56066bc920b3151df5` : frontend/build + garde production verts, backend rouge uniquement parce qu’un `ValueError` Pydantic restait non sérialisable dans le contexte du handler JSON ; corrigé avec `PydanticCustomError`.
- `PARTIEL` ne peut plus devenir l’état du document dans ce flux ; aucun montant partiel n’est inféré.
- `PaymentCreate.amount` est strictement positif et les méthodes connues sont normalisées explicitement.

#### P2-E — Échéances/réconciliation financière exacte — ACTIVE 🟡
- Défaut confirmé : Honoraires global peut créer un plan dont la somme des échéances diffère du total facturé.
- Préparation P2-E : réconciliation exacte au centime frontend/backend + tests ; PR draft `#30` 3/3 verte sur ancienne baseline.
- #30 ne doit pas être mergée : reconstruction obligatoire sur baseline post-P2-B.

#### P2-F — Allocation PAYE exacte par Acte — PREPARED
- Défaut confirmé : Honoraires PAYE crée des Acte marqués PAYE mais un Payment global sans `acte_id`, ce qui peut diverger de la vue `actes-billing`.
- Helper/test d’allocation exacte préparés sur PR draft `#31`; intégration route à faire après P2-E.

#### Préparation UX suivante
- P2-C : quick actions tactiles + phases déterministes sans durée clinique estimée, PR draft `#32`.
- P2-D : handler legacy de déduplication odontogramme confirmé orphelin ; policy `dent::traitement`, PR draft `#33`.

#### Pré-audits isolés pendant les CI
- P3 : `work-20260815-p3-static-audit` — non fusionné.
- P4 : `work-20260815-p4-static-audit` — non fusionné.
- P5 : `work-20260815-p5-static-audit` — non fusionné.
- P6 : `work-20260815-p6-static-audit` — non fusionné.

#### P5-P0 clinique découvert — NON CORRIGÉ 🔴
- `HouseWizard` est atteignable via `Mode Expert`.
- `DiagnosticEngine` produit diagnostic/protocole/plan de traitement et substitue actuellement automatiquement des classes thérapeutiques à partir d’une détection textuelle d’allergie.
- Exemple source vérifié : pénicilline → remplacement `AMOXICILLINE` par `CLINDAMYCINE/MACROLIDE`; AINS → remplacement par `CORTICOSTÉROÏDES`.
- `Appliquer` transforme le résultat en insight `DETERMINISTIC` et positionne le score d’intelligence à 100 ; il ne persiste pas directement le treatment plan dans la DB au point inspecté.
- Branche de sécurité `work-20260815-p5p0-no-auto-substitution` : test de frontière ajouté, correctif applicatif non encore fusionné.
- Priorité : aucune substitution thérapeutique automatique ; exposer une alerte à validation praticien.

Aucune certification financière production, UX runtime ou clinique/scientifique humaine n’est revendiquée pour les lots actifs/pré-audits.
