# HANDOVER — Digital Crown / Cephalo 2.0 — Past / Now / Future

Date: 2026-10-02
Repository: `hraaaaf/Digital_crown`

This handover is the canonical restart point for a new conversation. Do not reconstruct state from chat memory when this file and live GitHub evidence are available.

## PAST — What is already proven

### LOT00 — Baseline freeze
- Frozen baseline inspected on master SHA `71efbb62db60fbb2152c7f70e263b500a44f2c80`.
- SRPose38 runtime mapping documented.
- Important semantic non-equivalences recorded: D_point vs D_Steiner, PT_point vs Pt_Ricketts, Ptm vs PTM_McNamara, generic Gn/U6/L6 vs source-specific definitions, hard vs soft Pog.
- Runtime landmark names are not automatically authorized anatomical identities.

### LOT01 — Scientific contract
- Scientific contract and source locks established.
- Downs 1948 and Jacobson/Wits 1975 primary-source locks resolved.
- Wits remains dependent on an explicit occlusal-plane construction and must fail closed when unavailable.
- Historical names/norms are not promoted by similarity.

### LOT02 — Gold-set materialization
Official Aariz source:
- DOI: `10.6084/m9.figshare.27986417.v1`
- archive file ID: `51041642`
- expected size: `2,098,209,792` bytes
- MD5: `e0bd645bca6759abdae4f199d841bda6`
- license: CC BY 4.0

Local materialization was executed on authorized PC `DESKTOP-3MAJEEH`:
- archive size exact: PASS
- MD5 exact: PASS
- extraction complete: PASS
- split counts: 700 train / 150 valid / 150 test
- paired Junior + Senior annotations: 1000/1000 cases

Final reproducible evidence:
- cross-platform manifest SHA-256:
  `73c742db47686b0cf8b75b599b6373d3fc707d9b25a440c8d81d3d99ced241df`
- QC artifact SHA-256:
  `f5dc5552c3484dce8cbc16e25f2c2207be1cf48c1f2407fb584c85efc3e26be0`
- sentinel-measurement artifact SHA-256:
  `868de930eba33bf2b6d6b175b386f1c42e7fdb3205566ddbe331141fa5f1804d`
- per-landmark/device agreement file SHA-256:
  `e99fa49373ed20902c7266cbe805fcc2eee2d5bc70f747f64f424cfa45d35ff0`

QC across 29,000 Junior/Senior landmark pairs:
- `CONSENSUS_CANDIDATE`: 27,248
- `REVIEW_REQUIRED`: 1,309
- `ADJUDICATION_REQUIRED`: 441
- `STRUCTURAL_INVALID`: 2

Policy:
- <=2 mm is a QC consensus band only, not a clinical acceptance threshold.
- >2 to <=4 mm = review.
- >4 mm = adjudication.
- invalid coordinates = structural invalid.
- only consensus candidates may receive an automatic midpoint.
- ambiguous pairs are retained as G1-B stress evidence and are never silently averaged into exact ground truth.

G1 is therefore split:
- G1-A = consensus exact-reference subset.
- G1-B = ambiguity/stress set retained in coverage reporting.

G2:
- seven acquisition devices are frozen and tested.
- every device has 29-landmark human-agreement statistics.

G0:
- executable synthetic geometry oracle exists.
- exact geometry + degenerate fail-closed cases are tested.

G3:
- executable legacy compatibility fixture exists.
- migration/round-trip preservation is tested.

Human-reference evidence:
- per-landmark mean/median/SD/p90/p95/max in px and mm.
- directional X/Y bias and dispersion.
- device-stratified agreement.
- nine sentinel measurements across all 1000 cases and G1-A consensus-only subset.
- Aariz publication intra-observer repeatability source locked.

### SRPose38 provenance
Published source:
- repo: `5k5000/CLdetection2023`
- source commit: `18d17d1934970016e7610c4849311900b8d1f191`
- source pretrained weight SHA-256:
  `fb1a781ac1c83149b379cb15724e3b0fae06ba2d567978f35c61e9d06b46fdcc`

Digital Crown frozen checkpoint has the same SHA-256 byte-for-byte.

Published source training procedure consumes CL-Detection2023 data; no Aariz reference was found in the published repository/configuration. This is provenance evidence only, not clinical detector validation.

### LOT04 — Detector contract
- Protocol sub-gate `CEPH_DETECTOR_CONTRACT_APPROVED` is approved.
- SRPose38 is an engineering baseline candidate.
- Canonical `CEPH_DETECTOR_SELECTED` is NOT yet granted.
- No clinical detector-selection claim is authorized from parity/provenance alone.

### LOT05 — Canonical schema
Technical evidence already exists for the canonical extended schema:
- evidence HEAD: `9a53b755b692c530de6b27cb27aaff7b6647f1de`
- CI #7276: SUCCESS
- targeted backend tests: 51/51 PASS
- Agenda #2095: SUCCESS
- T2 #6093: SUCCESS

LOT05 has not activated V2 product runtime, changed cabinet data, replaced the detector, or merged to master.

## NOW — Exact current state

Cephalo working PR:
- PR: #746
- branch: `docs/cephalo-vnext-lot05-canonical-schema`
- base: `docs/cephalo-vnext-lot04-detector-contract`
- base SHA: `ddb6178babebf31510bf815f0c4a692faeb1bd3a`
- current HEAD:
  `319c1274928c01c029de64d04b4c6c3cd57e7e43`
- PR state: draft, not merged, mergeable.

GitHub Actions for current HEAD:
- CI #7334: SUCCESS
- targeted backend tests: 73/73 PASS
- no skip reported in the targeted pytest result
- Agenda A5 #2151: SUCCESS
- T2 Runtime Browser #6149: SUCCESS

Important nuance:
- PR CI checks out GitHub's PR merge ref `dedc7c61d4e00e52c8d9d493e2ec46cd316e3315`, whose head commit is `319c1274...`. This is strong integration evidence against the current base, but the log is not a direct checkout of the isolated head SHA.

Two internal adversarial perspectives were performed on the current evidence:
1. science / biometrics;
2. architecture / reproducibility.

Latest material findings were fixed:
- cross-platform manifest paths;
- reproducible measurement script;
- G0 oracle error;
- complete per-landmark SD/X/Y evidence;
- seven-device stratification;
- hash binding to committed aggregate evidence.

At the latest content review, no new BLOCKER or MAJOR was demonstrated in those two perspectives.

### Current closeout blocker

LOT02 must NOT yet be called fully closed/certified on the current HEAD because the canonical contract still contains stale exact-head closeout text referring to:

- old evidence HEAD: `db9642e1695cd3f04a53f4fc606de178cbdfc151`
- CI #7324 / 70 tests / T2 #6139 / Agenda #2141

while the real current evidence is:
- HEAD `319c1274...`
- CI #7334 / 73 tests / T2 #6149 / Agenda #2151

This is a documentation/evidence-coherence defect. It is not a data or algorithm failure, but under the project doctrine it prevents clean closeout.

Current severe scores:
- science/biometrics evidence: 9.4/10 maximum (internal review, no independent external reviewer)
- architecture/reproducibility: 9.4/10 maximum
- closeout/document coherence: 8.5/10 because stale exact-head evidence remains
- retained status: OPEN, not final VERIFIED closeout

### Governance decision made today

GitHub Actions is now the intended default execution surface for Digital Crown:
- tests;
- certifications;
- reproducible audits;
- SHA-bound evidence.

Remote/local execution is reserved for real dependencies such as:
- large public datasets kept outside repo;
- machine/hardware inspection;
- non-exportable secrets;
- authorized cabinet runtime.

Governance branch:
- `docs/github-actions-default-governance`
- HEAD `8c5054dcff5af25204580c189da309b59bfe7fe7`
- draft PR #748
- not merged because the current V1 execution lock forbids an out-of-sequence governance merge.

## FUTURE — Exact continuation sequence

### Step 1 — Finish LOT02 closeout
On the Cephalo branch:
1. read this handover and verify live PR #746 / HEAD / runs;
2. update `docs/audits/CEPHALO_VNEXT_LOT02_ANALYSIS_GOLDSET_CONTRACT.md` so exact-head evidence references the new final HEAD and current runs;
3. include the final per-landmark/device agreement evidence and current hashes;
4. create a NEW HEAD;
5. run/verify the directly impacted GitHub Actions tests on that new HEAD;
6. verify actual test collection/execution, not only green status;
7. rerun the two adversarial perspectives from zero on the new HEAD;
8. perform a separate confirmation pass from zero;
9. only if clean: mark LOT02 `CEPH_GOLDSET_READY` cleanly closed in repo + Notion.

Any new HEAD invalidates prior final confidence.

### Step 2 — Reconcile downstream handover
The existing `docs/cephalo/handovers/LOT_06_START_PROMPT.md` is stale because it still says LOT02 `CEPH_GOLDSET_READY` is NOT SATISFIED.

After LOT02 exact-head closeout:
- update LOT06 start prompt with the final LOT02 evidence;
- preserve that LOT04 canonical `CEPH_DETECTOR_SELECTED` is still NOT SATISFIED unless separately proven.

### Step 3 — Resolve LOT04 canonical detector selection
Use the now-qualified G1/G2 evidence to evaluate detector candidates.

Required:
- untouched acceptance subset discipline;
- contamination review;
- per-landmark/device performance;
- downstream sentinel-measurement error;
- predeclared tolerance policy;
- fail-closed behavior;
- no threshold retuning to make a model pass;
- two adversarial reviews + confirmation.

Do not select SRPose38 merely because:
- runtime parity is excellent;
- checkpoint provenance is known;
- CI is green.

### Step 4 — LOT06
Target:
`CEPH_ENGINE_CONCORDANT`

First action:
- inspect the actual CephaloEngine measurement registry/formulas;
- map every implemented measurement to exact landmarks/constructions, formula, unit, source contract and fail-closed behavior;
- produce an executable baseline before runtime changes.

Do not activate detector-dependent semantics until the applicable upstream detector gate is genuinely green.

### Later sequence
Continue canonical roadmap only after each gate closes:
- LOT06 engine concordance
- LOT07 tracing verification
- LOT08 human review
- LOT09 validation evidence
- LOT10 report traceability
- LOT11 Cephalo 2.0 candidate verification
- LOT12 integrated verification

No master mutation, cabinet mutation, production activation or Vercel deployment is authorized by this handover.

## Restart prompt for a new conversation

Continue Digital Crown Cephalo 2.0 from:

`docs/cephalo/handovers/CEPHALO_2_0_HANDOVER_2026-10-02.md`

Repository: `hraaaaf/Digital_crown`

First:
1. read the handover fully;
2. verify live PR #746, branch and exact HEAD;
3. verify current GitHub Actions state;
4. do not trust stale chat memory over repo/tool evidence.

Immediate goal:
finish the LOT02 exact-head closeout by correcting the stale certification SHA/run references, then rerun the required evidence/reviews on the resulting new HEAD.

Do not merge or deploy.
