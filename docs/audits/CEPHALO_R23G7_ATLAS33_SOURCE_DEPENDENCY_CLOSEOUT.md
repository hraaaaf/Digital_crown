# Digital Crown — R23-G7 / Atlas2009 33 — Focus dependency source-lock ledger

Status: **PARTIAL SOURCE COVERAGE ONLY — NEVER CLINICAL APPROVAL** (2026-10-17). Product surface: **desktop**, not smartphone.

## Proven scientific scope

Source identity: `RICKETTS_ATLAS_2009_COMPLETE_33_PROTOCOL_V1` (Fernández Sánchez / Da Silva Filho, 2009), exactly **33** versioned factors, not an unqualified vendor “Ricketts 32/13”. Source: `backend/data/cephalometry/ricketts_atlas2009_complete33_protocol_profile_v1.json`; canonical method implementations: `backend/services/cephalo_canonical_analysis_v2.py`; previous source-lock: `docs/audits/CEPHALO_LOT08_RICKETTS_32_13_SOURCE_LOCK_MATRIX.md`.

**Critically: clinical executability is NOT equivalent to published Focus dependencies.** The Atlas source already gives executable/conditional method contracts for all 33, but LOT06 Focus published explicit dependencies for only 8. A clinical value is allowed only through the verified, source-image/versioned typed runtime chain with all required geometric/evidence gates. This work adds **three display-only source obligation previews**, not clinical measurements or permission for drawing anatomical geometry.

Ledger generator: `python scripts/cephalo_r23g7_source_coverage.py --output atlas33-dependency-ledger.json`. In CI it checks canonical backend literal landmark signature, Atlas gate, references, non-overlap with LOT06, exact identity and ordering. Test: `audit/cephalo_r23g7_contract_tests/test_atlas33_source_coverage.py`.

| Source dependency state | Factor count | Clinical value/active Focus by THIS contract |
|---|---:|---|
| Published LOT06 geometry/source dependency register | 8 | **No** — needs verified runtime evidence |
| Published R23-G7 Atlas-only source **preview** | 3 | **No** — preview of required points only |
| No published frontend Focus-dependency source contract | 22 | **No** — requirements not inferred |

## R23-G7: exact scientific obligations published as non-executable UI preview

All three are source-profile-scoped; they do not add aliases or overwrite the generated LOT06 registry.

| Atlas factor | Canonical measurement ID | Exact source landmarks | External contract |
|---|---|---|---|
| #11, upper incisor protrusion to A-Pog | `M_RICKETTS_U1_APOG_PROTRUSION_MM_V1` | `U1_incisal`, `A`, `Pog_hard`, `Po_anatomic`, `Or` | Upper incisal tip perpendicular to A-Pog with **anatomic FH** as orientation and **verified calibration** for millimeters |
| #13, upper incisor inclination to A-Pog | `M_RICKETTS_U1_APOG_INCLINATION_DEG_V1` | `U1_incisal`, `U1_apex`, `A`, `Pog_hard` | Anatomically explicit upper incisor long axis versus A-Pog; angle only, no clinical norm |
| #26, cranial deflection | `M_RICKETTS_CRANIAL_DEFLECTION_FH_BAN_DEG_V1` | `Po_anatomic`, `Or`, `Ba`, `N` | Anatomical FH versus Ba–N; never substitute generic `Po` |

Contract: `docs/audits/schemas/cephalo_r23g7_atlas33_source_dependencies_v1.json`. It is consumed by `frontend/src/features/ortho/cephaloR23G7AtlasSourceRequirements.ts` **only when source profile is the full Atlas 33** and only when the operator selects the row. UI labels it as a requirement preview and visibly refuses to claim calculation/Focus. `resolveR23G3RuntimeFocus` remains unchanged and strictly requires real, verified row-level `focus_evidence`.

Scientific corroboration of measurement family (NOT universal norms): Bae, Kwon & Kwon (2014), *Korean Journal of Orthodontics* 44(2):77–87, DOI 10.4041/kjod.2014.44.2.77, PMID 24696824, https://pubmed.ncbi.nlm.nih.gov/24696824/. That publication is a Korean longitudinal cohort and **cannot license norms for all patient populations**. Specific landmark-method guards come from the source-locked Atlas contracts and checked-in backend implementation, not from assumed synonym equivalence.

## Remaining 22 nonpublished Focus obligations: grouped by blocking evidence

**W1 — image orientation evidence, 4/22:** Atlas factors **#4, #14, #18, #24**. Signed relationships require exact, versioned **same-image** anatomical superior/inferior orientation; raw display axes or mirroring must not substitute. Preserve `VERSIONED_IMAGE_ORIENTATION_EVIDENCE_REQUIRED` until the canonical orientation evidence and calibration gate are proven through active runtime and an independently verified sample.

**W2 — dentition/occlusal and explicit manual sources, 7/22:** factors **#1, #2, #3, #5, #9, #15, #17**. Source-locked Ricketts FOP (not generic occlusal line), molar distal, canine cusp, upper molar PTV or labial commissure manual records, relevant incisor axis and verified calibration where needed. For each factor, source the individual identity, coordinate system and exact method before publishing any Focus requirement. No inferential “U6”, “L6” or generic PTV proxies.

**W3 — cranial and mandibular constructions, 11/22:** factors **#8, #21, #23, #25, #27, #28, #29, #30, #31, #32, #33**. Dependent on exact Ricketts Xi/Pm, anatomical FH and/or source-locked PTV, CC, CF, GO_PFH, mandibular inferior angle or DC as specified by each source gate. **No aliases** among `Po` / `Po_anatomic`, `Pog` / `Pog_hard`, `PTM_McNamara` / `Pt_Ricketts`, or `Co` / `Co_anatomic`.

**Acceptance gate for each future publication:** (1) exact canonical measurement and source edition; (2) per-factor source definition and expected sign/unit; (3) explicit landmark and construction identities from the executable backend contract; (4) type/version/same-image provenance of manual/anatomical points; (5) verified calibration and orientation when needed; (6) geometry goldset and fail-closed negative tests; (7) actual source measurement evidence / no numeric fallback; (8) qualified clinical and independent adversarial review. A mere frontend list of required points does not satisfy these steps.

## Current decision

**33/33 Atlas profile maintained. 8 LOT06 + 3 G7 preview = 11 rows with published dependency description; 22 remain unpublished in frontend. ZERO new numeric values, norm sets, diagnoses or SVG Focus were authorized by R23-G7.**

R23-G4 visual evidence on desktop and R23-G5 authenticated API are distinct technical gates; neither certifies anatomy. Clinical release **NO-GO**. PR #911 remains draft/unmerged, no Vercel deployment, no hardware activation or real patient data.
