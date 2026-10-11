# FACAD 3.14 C02 — primary-source micro-excerpts, ANB geometry and PFH profile collision

**Date 2026-10-11 · SOURCE MICRO-EXCERPTS VERIFIED · NUMERIC PARITY NOT TESTED · RESEARCH ONLY.** No patient data; no clinical runtime edit, vendor binary transfer, merge, deployment or clinical-gate change.

## 1. Reproducible provenance and evidence integrity

Successful source-only [Windows run #38103228900](https://github.com/hraaaaf/Digital_crown/actions/runs/38103228900), **COMPLETED/SUCCESS** on SHA **`b01c5a46170c94100202f44bec6b9e5c4732f393`** (parent of this PR's later documentation-only commits). The exact step **“C02 original short-page quotations (strict 160-word total bound)”** is SUCCESS. Artifact **#11689141187**, ZIP SHA256 **`3075cbd9426b9c0bb50618ec51e967612633533475ce8f37d651c8c6d33ead16`**, was downloaded and inspected. Its **four** members only:

| Artifact member | SHA256 |
|---|---|
| `c02-pdf-minimal-index.json` | `011f9330320c46ce2b776506710080bc42826c4155e54ea9e9600ee5ed5158a4` |
| `c02-landmark-cooccurrence.json` | `a6903d480aa21c97b8bce40d5f13b1a3666e9b102fa4432cb4d8127fb84edf28` |
| `c02-bounded-page-contexts.json` | `b1c93a58a23fe66e5e35180d4b722c1a3be9b6b7bb136b63cb76777e5ae29406` |
| `installed-manual-status.txt` | `75bb64848268a22739bc825acd189c6d3a00f6af4c1a3a620e2e190b59f08980` |

Original FACAD-installed PDF `C02_Lateral Cephalometry Library - Measurements.pdf`, pinned SHA256 **`4dbd3fa8419b684529fcbc17f615f49f7486cdf037fcfff025b1b307c0c0a548`**, 34/34 pages, **5,718,901 bytes**. Page text SHAs were compared to original [source-index run #38101420112](https://github.com/hraaaaf/Digital_crown/actions/runs/38101420112); embedded index hash cross-check succeeded. **Ten tiny contexts, 147 total words**, all ≤16 words, seven distinct pages PDF 1-based `5,10,19,20,22,24,30`. Local independent ZIP/JSON verification in same session checked exactly four file names, 34 indexed pages, expected source SHA and source-index hash, all context word budgets, required source safety flags, and no claimed formulas in metadata. **No original PDF, whole PDF page, proprietary diagrams or patient data was exported.**

The runner status explicitly records `CLINICAL_APP_AUTO_STARTED_BY_INSTALLER=true` and `FACAD_PROCESS_ABSENT_BEFORE_DOCUMENT_INVENTORY=true` as well as `SHARED_APP_STORAGE_ISOLATION=UNVERIFIED`: we cannot infer that the temporary process caused no shared write. Clinical D3 stays red.

## 2. Source-derived meaning versus observations and inference

Everything below is a **paraphrase of a short, SHA/page-pinned manufacturer C02 snippet**, not an invented operator definition. Exact proprietary paragraphs/figures are deliberately not redistributed.

| PDF page / anchor | Observed manufacturer statement, paraphrased | Adjudication |
|---|---|---|
| **5 / SNA** | Angle at the N center using A and S | `VERTEX_N_CONFIRMED`; direction/sign unresolved |
| **5 / SNB** | Angle at N using B and S | `VERTEX_N_CONFIRMED`; direction/sign unresolved |
| **5 / ANB** | Angle at N using A and B | `VERTEX_N_AND_RAY_ENDPOINTS_CONFIRMED`; direction/sign unresolved |
| **10 / InterIncisal** | Between incisor axes `Iia–Ii` and `Isa–Is` | `TWO_LINES_CONFIRMED`; alias mapping DC, direction/sign unresolved |
| **19 / PFH** | In a ratio fragment involving `PFH` and `AFH` (both numerator orders present in context), not a stand-alone PFH length | `RATIO_CONTEXT_ONLY`; cannot assign geometry |
| **20 / PFH** | Named distance from `S` to `Go` | `S_GO_DISTANCE_CONTEXT_CONFIRMED`, **not** global PFH definition |
| **22 / Max-Mand diff** | Describes a subtraction between named `Mand ln` and `Max ln` derived measures | `DEPENDENT_LENGTHS_CONFIRMED`; exact operand sign, profile/version must be tied to UIA |
| **24 / Xi** | Excerpt concerns an *angle centered on Xi* with `ANS` and `PM`, not how Xi is constructed | `XI_AS_ANGLE_VERTEX_ONLY`, no Xi construction proven |
| **24 / CF** | Excerpt concerns an *angle centered on CF* with `Xi` and `P`, not how CF is constructed | `CF_AS_ANGLE_VERTEX_ONLY`, no CF construction proven |
| **30 / Max-Mand base** | Excerpt starts a projection description involving `TVL`, but is truncated before full endpoints | `PARTIAL_PROJECTION`; no formula certified |

**Important normative caveat**: the angle presentation Auto rule from FACAD reference manual is a **range-selection/UI format rule**, not the sign/ordering definition of these angles. C02 short text alone does not validate the vendor program's 0–360°/±180° endpoint convention or measurement outputs.

### FACAD 13F and the collision named PFH

The actual FACAD Ricketts (13 F) editor grid (UIA metadata), as source-recorded in [operator pilot](FACAD_314_C02_MEASUREMENT_OPERATOR_PILOT_2026-10-11.md), reports **`PFH=Dist2p(CF,Go)`**; Ricketts (32 F) has the same observed two-point distance. **C02 page 20** separately contains a `PFH` distance using **`S,Go`**. We do **NOT** know from this tiny snippet whether that entry is within a Ricketts analysis, another section/profile, an example or an alternate measure. These are *distinct geometric pairs*; do not globally collapse them to a single `PFH` in Digital Crown by label. Require `(vendor_build, profile_id, item_id, source_edition, landmark_dependencies)` before source-lock.

### Facad Steiner and ANB

Steiner UIA (historical overall-run FAILED, partial editor evidence) records **`ANB=Angle3p(N,A,B)`**; C02 p.5 now explicitly confirms the manufacturer describes **vertex N, rays toward A/B**. This strengthens geometric source attribution but still does not prove `Angle3p` direction, signed vs unsigned, quadrant selection, boundary or raw numeric output. No automatic equivalence to `SNA−SNB`.

## 3. Real Digital Crown source routing and independent synthetic contrast

Live `master` source snapshots observed through GitHub, not inferred from historical documentation:

- `backend/services/cephalo_engine.py` blob **`240e938a6618557c9630fee8b5e9b49e18b6403c`**. The `_get_clinical_angle` function returns a rounded **non-oriented** `acos(dot)` value 0–180°. In `calculate_metrics`, SNA and SNB are two `_get_clinical_angle` calls from N→S toward N→A and N→B; ANB is calculated as `sna - snb` when available.
- `backend/services/cephalo_service.py` blob **`2e3c05d38d380d3f486d742281374272346b9a5b`**, imports `cephalo_safe_engine` under alias `cephalo_engine` and calls its `calculate_metrics` in 2 places. `backend/services/cephalo_safe_engine.py` blob **`9b0957f298d1cb3b98e38889bac813c34db4ee04`** delegates to the legacy `CephaloEngine`; this **shows an existing call chain**, but is not proof what all consumer views use.
- `backend/services/cephalo_runtime_evidence.py` blob **`ee82322369291d85b0f93338292196cb61f4b6e5`** separately invokes `materialize_canonical_analysis_v2_measurements`. The workbench export contracts also state LOT06 canonical authority; the authoritative value for each **screen/report** remains to be resolved, and duplication/priority could matter.

Standalone independent `math.acos` replay on **no-patient points** produced:

| Fixture | S | N | A | B | Legacy code math SNA | SNB | Legacy ANB=SNA−SNB | Hypothetical unoriented angle A–N–B |
|---|---|---|---|---|---:|---:|---:|---:|
| F1 | (−1,0) | (0,0) | (1,1) | (1,−1) | 135.0° | 135.0° | **0.0°** | **90.0°** |
| F1-mirror | (−1,0) | (0,0) | (1,1) | (1,1) | 135.0° | 135.0° | **0.0°** | **0.0°** |
| F2 | (0,1) | (0,0) | (1,1) | (1,−1) | 45.0° | 135.0° | **−90.0°** | **90.0°** |
| F3 | (0,−1) | (0,0) | (1,1) | (1,2) | 135.0° | 153.4° | **−18.4°** | **18.4°** |

**Proved conditional mathematical insufficiency:** F1 and F1-mirror have exactly the same *unsigned* SNA, SNB and DC `ANB=0`, while their **unsigned vertex ANB angles** differ 90° vs 0°. Consequently a difference of two unoriented reference angles **cannot represent the unoriented A–N–B angle for all synthetic configurations**. This says **nothing about exact FACAD numeric convention without running the manufacturer math oracle**, and does not assert that both cases are anatomically plausible patient configurations or that any production diagnosis is wrong. It is a **MAJOR risk hypothesis**, not yet a confirmed clinical defect.

## 4. Adversarial internal review / gates / Next

**Review A (science/source) — 8/10 for page-locked source attribution, 0/10 for vendor numeric parity; MAJOR remains.** p.5 provides a vertex and rays but not `Angle3p` operational signed convention; p.20 PFH differs from profile-specific Ricketts observed data; p.19 ratio is not the p.20 standalone distance; p.24 Xi/CF excerpts address angle examples, **not** construction of the points. Do not convert any of these into scientific formula certification automatically.

**Review B (release/privacy/implementation) — 7/10 for bounded metadata provenance, 0/10 for clinical equivalence; BLOCKER remains.** Zip four members and source hash verified, no patient export, vendor binary undistributed. Runner FACAD auto-start before kill is explicit, D3 isolation not demonstrated, no patient-safe same-case measurement, no independent clinical professional review, no authoritative screen-route proof. All affected **product runtime code unchanged**.

| Gate | Decision |
|---|---|
| C02 SHA/Page/limited **textual** source evidence | **VERIFIED** (10 anchors, not diagrams) |
| F01.13 science crosswalk 65 profiles / all operators | **OPEN** |
| FAC03 D3 safe write isolation | **OPEN_RED** |
| FAC05 FACAD↔DC same-case numeric parity | **NOT_TESTED** |
| CEPH08 whole-protocol source-lock | **OPEN** |
| CLINICAL_EDIT_ALLOWED / CONVERGED | **false / false** |
| Canonical milestone count | **39/99 = 39.4%** |

**Next falsifiable step:** isolate actual FACAD `Angle3p` math/presentation and inspect the **full relevant diagrams**, using allowed limited evidence without exporting the proprietary entire PDF; on a truly **non-patient** same-case setup and only after the appropriate D3/safety gate, compare actual output to routed DC measurements (legacy **and** LOT06 canonical) with declared sign, units, version and pre-fixed tolerance. Independently source-lock `PFH` per analysis; never merge distinct `S-Go` and `CF-Go` by label. Two actual independent expert reviews are required for scientific/clinical closure, not two perspectives by the same assistant.

**No merge, no deploy, no clinical approval, no case patient.** Experimental source CI was green on the parent SHA only; newly amended report HEAD must be checked separately.
