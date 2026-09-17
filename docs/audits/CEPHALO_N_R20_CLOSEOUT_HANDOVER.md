# CÉPHALO-N R20 — CLOSEOUT HANDOVER — CANONICAL RESUME FILE

Status: IN PROGRESS — product/UI merged and visually validated; repository-wide post-merge backend certification is not yet green because successive stale regression tests were exposed by the full backend suite.

Last verified: 2026-09-17.

## 0. RESUME RULE — READ THIS FIRST

In a new conversation/window:
1. Read this file completely.
2. Verify GitHub live state before any write: `master` HEAD, PR #566 state/head/base/mergeability, exact-head CI/T2, and any newer commits on master.
3. Do not infer current state from this handover when GitHub can verify it.
4. Continue the `Next exact` and `Remaining sequence` at the end of this file without asking for routine authorization.
5. Do not declare R20 VERIFIED until the final post-merge full backend regression is green on the final merge SHA and the canonical R20 document has been updated consistently.
6. No Vercel deployment is authorized by this handover.

Repository: `hraaaaf/Digital_crown`
Default branch: `master`

Master HEAD at handover creation: `6075ae5f052b290258c4b66df97a05b0e61a3610`.
Master is highly active and may advance at any time; recheck before writes/merges.

## 1. GLOBAL GOAL

Close R20 — Céphalo-N Workbench UX Redesign with a fully evidenced state:
- product/UI implementation merged;
- scientific/calculation architecture preserved;
- deterministic visual evidence and human validation preserved;
- CI orchestration able to finish post-merge regression on active master;
- stale tests revealed by that regression corrected without resurrecting deprecated runtime behavior;
- final full backend regression + PostgreSQL certification green on the final merge SHA;
- canonical R20 markdown updated with the real chronology and final proof;
- no unresolved accidental-deletion risk from corrective PRs.

Success = final post-merge default-branch backend suite and required DB/CI gates are green on an exact final merge SHA, followed by coherent canonical documentation.

Proof = exact SHA + exact workflow/run/job results + reviewed diffs + R19 visual artifact + human visual validation.

## 2. PRODUCT / UI R20 — LOCKED AND ALREADY VALIDATED

Certified product code candidate HEAD:
`2cfc3ba66b8c0dc9a99e89a8da51ed53247a12e3`

Original R20 PR: #540.
Original R20 merge SHA:
`7821819b237aebdc7e3de1d2646510434251d2eb`

Product implementation commits:
1. `4b7b22bfbe8b97a5e7a4843882e940c315aabb1d` — `feat(cephalo): reshape workbench around radiograph`
   - left real controls / center dominant radiograph / right compact measures;
   - real controls only: Loupe, Tissus mous, Face 3D, Projection T1, Projection T2;
   - no invented scientific control/measure/geometry;
   - radiographic stage anchor `#f8fafc`.
2. `0500af094e580577accce93ffd1a6f62786ff68a` — `fix(cephalo): guarantee scientific contrast across themes`
   - skeletal `#38A8FF`;
   - dental `#FF7A45`;
   - soft tissue `#2EC68C`;
   - reference `#E85AAD`;
   - auxiliary `#64748B`;
   - adaptive mix: `color-mix(in srgb, <baseHue> 42%, var(--cephalo-scientific-anchor, var(--text-main)) 58%)`;
   - semantic tests: 5 distinct families, exact 42/58, each >=4.5:1 on card/input across 8 themes, viewer >=7:1 on `#020617`.
3. `8dc7173...` — compact responsive controls.
4. `2cfc3ba...` — mobile 390 px keeps all five controls visible with T1/T2 compact labels.

Locked visual reference:
- Google Drive file: `CEPHALO_N_WORKBENCH_UX_REFERENCE_V2.png`
- Drive ID: `1XBZC4BM_H0xuvJl1v3i6T-pvVj0thOSH`
- visual direction only, never a scientific specification.

Final intended rendering:
- desktop: utility rail / dominant radiograph / compact measures;
- tablet: controls reflow above radiograph;
- mobile 390: all five controls visible;
- COM synchronization preserved;
- no fictitious controls/measures/geometry.

Human product-owner visual validation: PASS on 2026-09-16.

## 3. PRODUCT EXACT-HEAD CERTIFICATION — GREEN

On product HEAD `2cfc3ba66b8c0dc9a99e89a8da51ed53247a12e3`:
- CI #4686 / run `35138070995`: SUCCESS.
- R19 Analysis Reference AFTER #31 / run `35138071116`: SUCCESS.
- R1 AFTER #140 / run `35138071150`: SUCCESS.
- R15 AFTER #188 / run `35138071099`: SUCCESS.
- R15bis AFTER #149 / run `35138071127`: SUCCESS.
- T2 Runtime Browser Certification #3543 / run `35138071079`: SUCCESS.
- PR Merge Summary #146 / run `35138071199`: SUCCESS.
- M6-I: SKIPPED as expected for scope.

R19 artifact:
- artifact ID `10463673566`;
- digest `sha256:0e06ae30366f195686070ce2731029d10979035654298a93c5f1ffe1472f7acf`;
- product HEAD `2cfc3ba66b8c0dc9a99e89a8da51ed53247a12e3`;
- default theme;
- viewports `390x844`, `768x1024`, `1280x900`;
- modes all / Steiner / Tweed / McNamara / COM / Ricketts;
- no page/console errors, no horizontal overflow, invalidCount 0, blockedExternalRequests empty;
- 21 PNGs in evidence artifact.

Docs-only certified HEAD before original merge:
`2e6fbefab105766ff75b0b641766f93480174970`

On that docs HEAD:
- CI #4692 / `35142008877`: SUCCESS.
- R19 #32 / `35142008909`: SUCCESS.
- R1 #141 / `35142008821`: SUCCESS.
- R15 #189 / `35142008861`: SUCCESS.
- R15bis #150 / `35142008818`: SUCCESS.
- T2 #3548 / `35142008829`: SUCCESS.
- PR Merge Summary #152 / `35142008870`: SUCCESS.
- M6-I skipped expected.

## 4. SCIENCE / NON-REGRESSION LOCKS

Céphalo-N global scientific goal:
image/landmarks → unique correctable patient evidence graph → canonical measures calculated once → analysis profiles → separate/versioned normative data → synchronized SVG → clinical synthesis → practitioner validation/correction → coherent PDF.

Locked rules:
- single canonical measure registry: `backend/services/cephalo_measure_registry.py`;
- normative registry separate;
- unknown canonical unit fails closed;
- `M_OVERBITE_V1` has no locked unit -> `None`;
- preserve legacy functions/evidence/PDF/patient/DB/certified measures;
- lateral != PA/frontal.

False equivalents forbidden:
- `M_B_NPERP_MM_V1 != M_POG_NPERP_MM_V1`
- `M_U1_FH_DEG_V1 != M_FMIA_L1_FH_DEG_V1`
- `M_FACIAL_ANGLE_NPOG_FH_DEG_V1 != M_COM_S_NPERP_DEPTH_MM_V1`
- `M_FACIAL_AXIS_RICKETTS_DEG_V1 != M_FACIAL_AXIS_MCNAMARA_DEG_V1`
- `M_L1_EDGE_APOG_MM_V1 != M_L1_FACIAL_SURFACE_APOG_MM_V1`
- `M_FH_GOME_DEG_V1 != M_FH_SUBGO_M_DEG_V1`
- `Gn_anatomic != Gn_constructed`
- `Pt_Ricketts != PTM_McNamara`
- `Pog_hard != Pog_soft`.

New-measure gate requires exact source / landmarks / construction / unit / calibration / canonical ID / centralized calculation / deterministic numeric tests / negative tests / no duplication. Missing item => BLOCKED.

Latest activated measures: `M_A_NPERP_MM_V1`, `M_POG_NPERP_MM_V1`.
McNamara primary DOI `10.1016/S0002-9416(84)90352-X`, PMID `6594933`; secondary PMC `4436328`.
Profiles: Steiner, Tweed DC variant, McNamara, Ricketts, COM.
Ortho V2 remains parked until `CEPHALO_N_CLOSEOUT_VERIFIED`.

## 5. WHY POST-MERGE CERTIFICATION BECAME A SEPARATE CHAIN

Original R20 merge SHA `7821819b237aebdc7e3de1d2646510434251d2eb` triggered CI #4696 / run `35143127506`.
The backend job `104952565254` was CANCELLED, not failed. A targeted backend rerun `104960302644` was also CANCELLED. Logs reached ~32% pytest with no test failure before cancellation.

Root cause: `.github/workflows/ci.yml` used:

```yaml
concurrency:
  group: ci-${{ github.ref }}
  cancel-in-progress: true
```

On highly active `master`, newer pushes cancelled in-progress post-merge backend regressions.

After two same failures/cancellations, strategy changed as required: fix CI orchestration instead of rerunning blindly.

## 6. CI ORCHESTRATION FIX — PR #554

Minimal fix:

```yaml
concurrency:
  group: ci-${{ github.ref }}
  # Keep every post-merge default-branch regression alive. Superseded PR/feature
  # runs may still be cancelled to avoid wasting CI capacity.
  cancel-in-progress: ${{ !(github.event_name == 'push' && (github.ref == 'refs/heads/master' || github.ref == 'refs/heads/main')) }}
```

PR #554 exact head:
`881f2359351e12f7b02c918b72500a4a99d41fcc`

Pre-merge:
- CI #4715 / `35151571222`: SUCCESS.
- PR Merge Summary #167: SUCCESS.
- T2 #3563: SUCCESS.
- M6-I skipped expected.

Merge SHA:
`96a5d1a68ac027f112e0ca349ed6f2f0abbe3243`

Post-merge CI #4716 on that SHA:
- production guard: SUCCESS;
- frontend: SUCCESS;
- PostgreSQL #935: SUCCESS;
- backend full regression: FAILURE, now allowed to finish;
- result: `1 failed, 2028 passed, 6 skipped in 364.36s`.

This proved the orchestration fix worked and exposed a genuine stale test instead of cancellation.

## 7. FIRST STALE MOBILE/FCM REGRESSION — PR #558

Root cause: old test still called `POST /api/mobile/register-device` expecting success. Runtime intentionally removed/deprecated FCM registration; Web Push is canonical. `backend/routers/mobile_legacy.py` may still contain the legacy definition, but `backend/routers/mobile_push.py` removes it before mount. 404 is deliberate. DO NOT restore `/register-device`.

PR #558 title: `test(mobile): align license subject regression with supported mutation`.
Branch: `fix/mobile-identity-license-test`.
Final reconciled PR HEAD:
`df1f7239c6fd9aeff157ca411c9288ee0b914191`

Pre-merge:
- CI #4734 / `35158747614`: SUCCESS.
- T2 #3579 / `35158747593`: SUCCESS.
- PR Merge Summary #184 / `35158747600`: SUCCESS.
- M6-I #2379 skipped expected.

Merge result:
`eb2353b68d880b89dfadd13819fb43d1c71e2f1d`

Actual merge parents:
- `c547e30d4bab4928ff64de3757bff98a83a60a53`
- `df1f7239c6fd9aeff157ca411c9288ee0b914191`.

Post-merge CI #4737 / run `35160284375`:
- production guard SUCCESS;
- frontend SUCCESS;
- PostgreSQL #938 SUCCESS;
- backend FAILURE because the replacement test used `/api/mobile/appointments`, which Agenda A3 had meanwhile intentionally converted to `410 Gone` in favor of `/api/appointments/`.

## 8. CANONICAL MOBILE LICENSE MUTATION FIX — PR #562

PR #562 title: `test(mobile): target canonical mutation for license subject regression`.
Branch: `fix/mobile-license-supported-mutation`.
Base at creation:
`eb2353b68d880b89dfadd13819fb43d1c71e2f1d`
Pre-merge HEAD:
`87c95687ee1b58f04d0d3b80ffe7ad550b8b845f`
Merge SHA:
`d237648c958e8567ea68beaa8b084d33a160c775`

Test strategy:
- preserve numeric mobile JWT subject/license middleware regression;
- use canonical supported `POST /api/appointments/`;
- intentionally incomplete payload;
- licensed cabinet passes license middleware and reaches FastAPI validation => 422;
- then set owner `dentiste.is_licensed = False`, commit, clear `backend_main._license_cache`;
- same mutation with same mobile token => middleware intercepts first => 403 `NOT_LICENSED`.

Pre-merge exact-head workflows on `87c95687...`:
- T2 #3582 / run `35161921395`: SUCCESS.
- CI #4738 / run `35161921369`: SUCCESS.
- PR Merge Summary #187 / run `35161921616`: SUCCESS.
- M6-I #2382 skipped expected.

Post-merge on `d237648c...`:
- Cabinet Upgrade PostgreSQL Certification #939 / run `35192566873`: SUCCESS.
- CI #4744 / run `35192566909`:
  - frontend SUCCESS;
  - production guard SUCCESS;
  - backend FAILURE;
  - exact result: `1 failed, 2129 passed, 6 skipped in 412.37s`;
  - failure: `backend/tests/test_mobile_router.py::TestMobileAuthGuard::test_register_device_requires_mobile_auth`;
  - test expected 422 for `/api/mobile/register-device`, actual 404.

This was a second independent stale FCM expectation. Runtime remained correct and must not be restored.

### PR #562 diff-risk review
A prior concern existed because PR #562 reported one file, +25/-86, raising the possibility that an update had truncated unrelated tests.
The PR #562 diff was inspected during this closeout. It shows the apparent large deletion count is predominantly formatting compaction plus the intended mutation-test replacement. No wholesale unrelated test block deletion was observed in the reviewed diff. This reduces the truncation concern, but the final closeout should still avoid claiming more than the reviewed diff proves.

## 9. SECOND FCM TEST CLEANUP — PR #564

PR #564 title: `test(mobile): align removed FCM route expectation`.
Branch: `fix/mobile-register-device-legacy-test`.
Pre-merge HEAD:
`98e6b722c8f179d655de9229d703a4f22e14efd7`

Change was strict/minimal: one test file, +2/-2; rename stale auth-guard test and assert deliberate 404 for removed FCM route. Runtime unchanged.

Pre-merge exact HEAD:
- CI #4751: SUCCESS.
- T2 #3592: SUCCESS.
- PR Merge Summary #197: SUCCESS.
- M6-I skipped expected.

Merge SHA:
`6075ae5f052b290258c4b66df97a05b0e61a3610`

Post-merge on `6075ae5f...`:
- PostgreSQL #942: SUCCESS.
- frontend/build: SUCCESS.
- production guard: SUCCESS.
- backend: FAILURE;
- exact result: `1 failed, 2165 passed, 6 skipped`;
- failure: `backend/tests/test_ngap_insurance_schema_migration.py` expected Alembic head `d0b000000003`, while current head is Agenda A3 revision `a3pa0000003`.

This is not an R20 runtime failure. It is a stale migration-test assumption exposed by the now-completing repository-wide backend regression.

## 10. CURRENT ACTIVE FIX — PR #566 — DO NOT LOSE THIS

PR #566 title: `test(ngap): follow current Alembic head contract`.
Branch: `fix/ngap-alembic-head-contract`.
Base SHA at creation:
`6075ae5f052b290258c4b66df97a05b0e61a3610`
Exact PR HEAD:
`7f79c16b0c8e8066ea55c0ede178b1b0a83d5dbd`

Current live state at handover creation:
- PR OPEN, not merged.
- master still `6075ae5f052b290258c4b66df97a05b0e61a3610` when last checked.
- PR diff: exactly one file, `backend/tests/test_ngap_insurance_schema_migration.py`, +19/-5.
- runtime files unchanged;
- migration files unchanged.

The fix deliberately avoids hardcoding the transient current head:
- adds `_alembic_script()` helper;
- keeps NGAP migration identity locked: `migration.revision == "d0b000000003"`;
- keeps `migration.down_revision == "d0b000000002"`;
- asserts exactly one current Alembic head;
- verifies NGAP revision is on the active revision chain from current head to base;
- empty-SQLite baseline compares `alembic_version.version_num` with the actual unique `heads[0]`, not old `d0b000000003`.

Exact diff intent:
```python
def _alembic_script() -> ScriptDirectory:
    config = Config(str(ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(ROOT / "alembic"))
    return ScriptDirectory.from_config(config)


def _alembic_heads() -> list[str]:
    return list(_alembic_script().get_heads())


def test_ngap_insurance_migration_is_on_current_unique_revision_chain():
    migration = _load_migration()
    script = _alembic_script()
    heads = list(script.get_heads())

    assert migration.revision == "d0b000000003"
    assert migration.down_revision == "d0b000000002"
    assert len(heads) == 1

    revisions_to_head = {
        revision.revision
        for revision in script.iterate_revisions(heads[0], "base")
    }
    assert migration.revision in revisions_to_head
```

and the SQLite baseline changed from:
```python
.scalar_one() == "d0b000000003"
```
to:
```python
.scalar_one() == heads[0]
```

Why both changes matter: the first failing assertion was stale, and the same file contained a second hardcoded `d0b000000003` that would likely become the next failure after fixing only the first one. Both are addressed in the same semantic contract without modifying migration history.

### PR #566 exact-head gates — VERIFIED GREEN
On HEAD `7f79c16b0c8e8066ea55c0ede178b1b0a83d5dbd`:
- CI #4755 / run `35200350697`: SUCCESS.
- T2 Runtime Browser Certification #3595 / run `35200350712`: SUCCESS.
- PR Merge Summary #200 / run `35200350653`: SUCCESS.
- M6-I #2395 / run `35200350719`: SKIPPED as expected.

Important CI nuance: on pull_request CI, `Full backend regression (post-merge)` is SKIPPED by design. Therefore the final proof still requires merge + push/default-branch full backend regression.

PR #566 has not been merged as of this handover. The GitHub `merge_commit_sha` field shown on an open PR is a prospective/test merge SHA and is NOT evidence of merge. A `/pulls/566/merge` GET returned 404, confirming not merged at that check.

## 11. INTERVENING AGENDA A3 / ACTIVE MASTER CONTEXT

Master is fast-moving. Agenda A3 introduced a meaningful intervening set of changes. A prior comparison around `96a5d1...` → `ef23b714...` showed 37 commits / 24 files including:
- Agenda A3 workflows;
- Alembic availability migration;
- backend agenda models/router/services/tests;
- agenda closeout/canonical/reference docs;
- frontend agenda settings/availability/timeline/theme tests;
- backend `appointments.py` changes.

This is why `/api/mobile/appointments` became a deliberate 410 legacy route and why Alembic head advanced beyond NGAP.

Rule: exact-head certification and live master recheck are mandatory before every merge/write.

## 12. CURRENT CANONICAL R20 DOCUMENT IS STALE

Existing canonical file:
`docs/audits/CEPHALO_N_WORKBENCH_UX_REDESIGN.md`

At master `6075ae5f...`, blob SHA was:
`063b7171d151b2383a1451315d49b68420e923b9`

Its status still says:
`READY FOR MERGE — R20 UI/UX implementation certified and human-validated`

It still contains obsolete language:
- `Only explicit merge authorization remains.`
- `Do not merge PR #540 unless...`

That is now false because PR #540 was already merged and the closeout entered post-merge repository certification.

Do NOT update this file prematurely before final post-merge proof. After final green, update it to record the true chronology and final verified SHA/runs.

Required chronology to include in final canonical update:
1. certified product head `2cfc3ba...`;
2. original R20 merge `7821819b...`;
3. original backend cancellations caused by CI concurrency;
4. CI orchestration fix PR #554 / merge `96a5d1...`;
5. full backend exposed stale FCM test;
6. PR #558 / merge `eb2353b...` moved test away from removed FCM route but hit Agenda A3 410 mobile appointments;
7. PR #562 / merge `d237648c...` moved license test to canonical shared appointment mutation;
8. post-merge #562 exposed separate stale FCM auth-guard test;
9. PR #564 / merge `6075ae5f...` aligned removed FCM route expectation;
10. post-merge #564 exposed stale NGAP Alembic-head assumption;
11. PR #566 exact-head fix and its final merge SHA;
12. final successful post-merge full backend regression and PostgreSQL certification — ONLY if actually proven;
13. distinguish product candidate SHA, original R20 merge SHA, infrastructure/test corrective SHAs, and final proof SHA.

Remove stale merge-authorization language.

## 13. SCORING / CLAIM DISCIPLINE

Final pre-merge R20 visual/product scoring:
- EXECUTION_SCORE: 9.3/10.
- ADVERSARIAL_SCORE: 9.2/10.
- retained: 9.2/10.
- no independent third-party reviewer; no claim >9.4.

Current closeout certification is NOT VERIFIED while final post-merge backend proof is missing/red.
User scoring rule: required proof red/missing => max 7.9 for the closeout certification, regardless of product visual score.

VERIFIED requires >=9.0 and all binary gates green. Even >=9.2 requires final Perfection Pass.

## 14. PRIOR IMPORTANT MERGES / DO-NOT-RESTORE

Historical references if needed:
- #527 measures merged: premerge `800729c...`, merge `2c36a04...`, postmerge CI #4565 SUCCESS, PostgreSQL #916 SUCCESS.
- #513 merged `d762dec...`, postmerge #4407 success.
- #515 `8f744649...`, #4442 success.
- #524 `e83b971...`, #4488 success.
- bad dangling commit `2b8008f...`: NEVER restore/merge.
- older canonical closeout PR #535 branch `docs/cephalo-n-closeout-527`, docs HEAD `2daad5e...`, historically open/not merged; do not assume it should be merged. R20 canonical closeout supersedes old assumptions; verify if ever relevant.

## 15. OPERATING RULES FOR NEXT WINDOW

- Verify facts, calculations, hypotheses, conclusions; never invent proof/status.
- For significant work: Goal / Success / Proof.
- Continue autonomously while safe and authorized.
- Do not ask merely because one step finished.
- CI: check once; if pending, do independent work; no polling/sleep/passive waiting.
- After two similar failures, change strategy.
- Do not claim done/validated/production-ready without proof.
- No Vercel deployment without explicit authorization.
- UI changes require BEFORE → Goal → reference/mockup → implementation → AFTER same viewports → comparison/tests → visual score. R20 UI gate already has this evidence; do not unnecessarily redo unless product code changes materially.
- For command/work updates, include an internal expert opinion, explicitly non-independent; there is no real subagent tool, so never fabricate an independent subagent.

## 16. NEXT EXACT — START HERE

1. Recheck live `master` HEAD and PR #566 state/head/base.
2. If PR #566 remains open at exact head `7f79c16b0c8e8066ea55c0ede178b1b0a83d5dbd`, master has not diverged incompatibly, and the exact-head gates remain green, merge #566 using expected head SHA.
3. Capture the real merge SHA.
4. Check the post-merge push workflows on that exact merge SHA:
   - full backend regression must COMPLETE SUCCESS;
   - PostgreSQL certification must COMPLETE SUCCESS;
   - frontend/production guard should remain green if triggered.
5. If backend exposes another stale unrelated test, diagnose and correct the test/runtime contract according to actual architecture; do not weaken genuine regression coverage or restore deprecated runtime just to get green.
6. Once final post-merge backend + PostgreSQL are green, update `docs/audits/CEPHALO_N_WORKBENCH_UX_REDESIGN.md` with the chronology above and final proof.
7. Review the docs diff for factual consistency, commit/PR/merge it safely against then-current master, and verify any required post-merge docs CI.
8. Only then declare `CEPHALO_N_CLOSEOUT_VERIFIED` and unpark the next authorized lot (Ortho V2 only if that remains the roadmap decision).

## 17. REMAINING SEQUENCE

PR #566 live recheck → merge if exact-head proof still valid → final post-merge backend + PostgreSQL → if red, diagnose/fix/retest/merge/postmerge → if green, canonical R20 markdown update → coherence/diff review → docs PR/merge → final post-merge docs checks as required → final Perfection Pass → `CEPHALO_N_CLOSEOUT_VERIFIED` → next lot.

## 18. CURRENT BLOCKER

At handover creation there is no technical red gate on PR #566 itself: exact-head CI/T2/summary are green. The immediate action is merge + post-merge certification. Because this handover is being created on a separate docs branch, do not confuse its commit with the product/test PR #566.

## 19. CANONICAL POINTERS

Primary R20 design/certification document to update after final green:
`docs/audits/CEPHALO_N_WORKBENCH_UX_REDESIGN.md`

This resume/handover file:
`docs/audits/CEPHALO_N_R20_CLOSEOUT_HANDOVER.md`

For resumption, this handover is the first file to read until the closeout is finished. After final closeout, the redesigned canonical document becomes authoritative again and this file remains historical traceability.
