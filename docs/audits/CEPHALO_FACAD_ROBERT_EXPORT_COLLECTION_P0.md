# CÉPHALO 2.0 × FACAD — official Robert same-trace export collection (P0 preparation)

**Scope:** [PR #974](https://github.com/hraaaaf/Digital_crown/pull/974) / FACAD-REA-P0 / P0-META-EXPORT. **Status: PREPARED; RUNTIME AND NUMERIC PARITY NOT VERIFIED.** This is a collection protocol, not permission to operate the trial, bypass licensing, decode proprietary CIL, import real patients, or change Digital Crown clinical runtime.

## Source-locked references (existing, not superseded)

- [FACAD version-sensitive public manual research](CEPHALO_LOT08_FACAD_PUBLIC_ARTIFACT_SEARCH.md): version 3.14 Cephalometry > Export documents **Analysis Values**, **Analysis Properties**, **Object Values** (the last is the 3.14 export surface covering marker positions; historical 3.8/3.13 manuals say **Marker Positions**).
- Canonical existing [LOT08 evidence manifest](schemas/ortho_lot08_facad_ricketts_direct_parity_evidence_v1.json) and [validator](../../audit/cephalo_lot08_facad_parity_validate.py): do **not** invent a second evidence schema or silently set `OBSERVED`. Its required *logical* kinds stay `ANALYSIS_VALUES`, `ANALYSIS_PROPERTIES`, `MARKER_POSITIONS` for both profile targets.
- Official pinned FACAD 3.14.1.1111 installer `A60D13EA2C32D49C192BCF07F40BA07D8C0410E6577FE28CE4B0181BB4018B86` (SHA-256), internal `FacadRelease-3.14.1.1111.zip` `48A5844B4EFF8EFC06F559C962A3AD88FD9B6983C37FDDBA5C28B19C0CE4ABC4`.
- The `Robert-2.0.fcd` file is expected within `release/Examples/`. GitHub's **headless P0 proof** may attest to its presence and SHA-256, but **never** that its clinical tracing was opened or exported.

## Permission gate before any GUI session

An authorized operator must verify applicable FACAD license, EULA and permissions and must have access to a licensed FACAD 3.14.1.1111 installation. If not established, **STOP — NO GUI / NO EXPORT**. The expired/trial or disposable Windows runner used in older PRs is not a transferable license. Use only the manufacturer's included **Robert example**, not real patient data. Work on a disposable copy of the demo; hash the official original before/after and prove it unchanged. Do not distribute the original `.fcd`, proprietary binaries or protected exports publicly without permission.

## Reproducible same-trace operator procedure (only after permission gate)

1. Record FACAD application version, the **SHA-256** of the original official `Robert-2.0.fcd`, workstation/environment description (no license secrets), local date/time **including timezone**, the specific lateral tracing selected, and an opaque `same_trace_case_id` that identifies that **one tracing**. A patient/sample name alone is **not** a tracing identifier. If the sample lacks a suitable tracing, **STOP**, do not synthesize geometry.
2. In the authorized FACAD user interface, open the disposable **Robert example** and explicitly select **the same lateral tracing** for both analyses. Preserve unedited landmarks, calibration and tracing state. Record the exact profile shown in the UI.
3. Select standard `Ricketts (32 F)`. Under **Cephalometry > Export**, produce *three raw vendor artifacts*: `Analysis Values`, `Analysis Properties`, `Object Values`. Retain their original filenames and bytes; annotate the latter as candidate evidence for the logical `MARKER_POSITIONS` family **only after verifying its actual contents include marker positions and construction references required by the validator**. An empty/missing/irrelevant Object Values export does **not** meet that requirement.
4. Without changing the tracing, calibration or source case, switch to standard `Ricketts (13 F)`, then repeat the **same three raw exports**. Preserve the original vendor output; do not normalize, rewrite, extrapolate or manually fill missing rows.
5. For **each of six distinct export files**, record the exact vendor menu label, original filename, SHA-256 of the original bytes, file size, source FACAD version, timezone-aware export timestamp, opaque same-trace ID, profile target ID, and operator evidence that the chosen tracing stayed identical. Keep export files private until permitted disclosure is established.
6. Map the six artifacts (two profiles × three logical kinds) into the existing LOT08 evidence manifest. The 3.14 `Object Values` export can back `MARKER_POSITIONS` **only after it is inspected and qualified as actually containing the relevant marker positions**, with its 3.14 vendor provenance retained in the source filename and acquisition notes. Use the existing validator; ensure the paths and exact SHA-256 are correct and no source path escapes the designated evidence root. Prefer a controlled private evidence checkout, not unrestricted public artifacts.

| Actual FACAD 3.14 menu | Existing LOT08 logical evidence kind | Required profiles |
| --- | --- | --- |
| `Analysis Values` | `ANALYSIS_VALUES` | `FACAD_RICKETTS_32F_COMPATIBILITY_TARGET`, `FACAD_RICKETTS_13F_COMPATIBILITY_TARGET` |
| `Analysis Properties` | `ANALYSIS_PROPERTIES` | Both, on the identical tracing |
| `Object Values` **only if positions are actually present** | `MARKER_POSITIONS` | Both, with original 3.14 menu provenance documented |

### What is NOT proven by a complete file set

A collection may reach `PARTIAL` or pass basic evidence validation without proving signs, construction identity, norms, rounding or numeric parity. The manifest can only become `DIRECT_PARITY_OBSERVED` after both profiles have the required ordered rows and comparison dimensions resolved using actual Digital Crown calculations for the **same calibrated tracing**; no inferred matches, invented measurements, copied norms or implicit 32F↔13F equivalence. The static `.cph` profiles prove definitions, not patient/sample numerical measurements.

## Evidence validation (authorized, private evidence location)

Run the pre-existing repo validator against its canonical manifest after source files are staged and their evidence records intentionally reviewed:

```bash
python audit/cephalo_lot08_facad_parity_validate.py
python -m pytest backend/tests/test_cephalo_lot08_facad_direct_parity_validator.py backend/tests/test_cephalo_lot08_facad_direct_parity_contract.py -q
```

**Fail-closed collection stop:** if rights, same-trace identity, source hashes, 3.14 Object Values marker coverage, profile identity, export timestamps, row counts, or version matching cannot be proved, retain `UNOBSERVED` / `PARTIAL` as appropriate. Never promote those gaps to clinical parity. No merge, deployment or activation through this protocol.

**Next required human/technical evidence:** confirmation of lawful use of FACAD 3.14 GUI; one trace in the official Robert demo; real, hashed 6-file export set; then source-locked Ricketts 32F/13F comparison using the existing validator.


## Private offline intake (after authorized GUI exports exist; no cloud upload)

The source-locked staging utility lives at `audit/cephalo_facad_robert_evidence_stage.py`. It reads **six actual vendor-generated files** in one private intake folder and writes a new, independent private evidence tree and a **copy** of the existing canonical LOT08 parity manifest (never edits the repository manifest). It does **not** operate FACAD, inspect the tracing's geometry, prove the operator's attestation, calculate numerical parity, or automatically upgrade the evidence beyond `DIRECT_EVIDENCE_PARTIAL`. It must run only on a controlled computer with authorized use and export content verified.

Create a PRIVATE JSON intake file beside the six vendor exports, specifying the exact observed timestamp with timezone and the same opaque tracing ID for each. Do not paste license credentials or real patient names:

```json
{
  "official_robert_sha256": "67a81ad8d2c2489ffe84a1dfbbb897761ae855ece4ebf948c12af232562ec089",
  "facad_version": "3.14.1.1111",
  "same_trace_case_id": "ROBERT_LATERAL_TRACE_A",
  "authorized_facad_use_confirmed": true,
  "same_lateral_tracing_confirmed": true,
  "exports": [
    {"profile_target_id":"FACAD_RICKETTS_32F_COMPATIBILITY_TARGET","artifact_kind":"ANALYSIS_VALUES","file":"32F/values.txt","observed_at":"2026-10-19T12:00:00+01:00","vendor_menu":"Analysis Values","marker_positions_content_verified":false},
    {"profile_target_id":"FACAD_RICKETTS_32F_COMPATIBILITY_TARGET","artifact_kind":"ANALYSIS_PROPERTIES","file":"32F/properties.txt","observed_at":"2026-10-19T12:01:00+01:00","vendor_menu":"Analysis Properties","marker_positions_content_verified":false},
    {"profile_target_id":"FACAD_RICKETTS_32F_COMPATIBILITY_TARGET","artifact_kind":"MARKER_POSITIONS","file":"32F/object-values.txt","observed_at":"2026-10-19T12:02:00+01:00","vendor_menu":"Object Values","marker_positions_content_verified":true},
    {"profile_target_id":"FACAD_RICKETTS_13F_COMPATIBILITY_TARGET","artifact_kind":"ANALYSIS_VALUES","file":"13F/values.txt","observed_at":"2026-10-19T12:03:00+01:00","vendor_menu":"Analysis Values","marker_positions_content_verified":false},
    {"profile_target_id":"FACAD_RICKETTS_13F_COMPATIBILITY_TARGET","artifact_kind":"ANALYSIS_PROPERTIES","file":"13F/properties.txt","observed_at":"2026-10-19T12:04:00+01:00","vendor_menu":"Analysis Properties","marker_positions_content_verified":false},
    {"profile_target_id":"FACAD_RICKETTS_13F_COMPATIBILITY_TARGET","artifact_kind":"MARKER_POSITIONS","file":"13F/object-values.txt","observed_at":"2026-10-19T12:05:00+01:00","vendor_menu":"Object Values","marker_positions_content_verified":true}
  ]
}
```

**All filenames/timestamps above are illustrative placeholders, not actual observed exports.** Replace them with the six real FACAD original filenames and actual capture timestamps. The last boolean is a **manual declaration** that the real Object Values file includes appropriate marker positions; it does not make that true. Keep all six vendor files byte-identical and within the intake folder. Only authorized data may be staged.

```bash
python -m audit.cephalo_facad_robert_evidence_stage \
  --intake /private/intake/SIX_EXPORTS.json \
  --private-output /private/new-facad-evidence
python -m unittest -v audit.test_cephalo_facad_robert_evidence_stage
```

The output must be **outside the Git repository** and start as a nonexistent directory. It contains six untouched bytes-preserving export copies under `docs/audits/evidence/facad/` and the canonical-format manifest under `docs/audits/schemas/`. It explicitly records `DIRECT_EVIDENCE_PARTIAL`, `PARTIAL` for both profiles, zero parity rows; it does not publish the exports to GitHub or attach them to any workflow artifact. Positive tests use visibly synthetic fixtures and are **never** presented as Facad clinical evidence. If any license, source hash, trace, version, timestamp, Object Values coverage, file integrity or manifest gate fails, output is rejected without a successful staging result.


## 2026-10-24 — Master-aligned private intake branch

The private intake script and its 16 negative / positive contract tests were transplanted byte-for-byte from historical FACAD research PR #974 into `research/facad-sametrace-private-intake-20261024` from exact master `46362e2986e3b6b08598f518eff95fa01f161571`. The canonical manifest and canonical validator had identical Git blobs in historical PR #974 and this master. This branch adds CI that runs tests with **synthetic, clearly labeled fixture files only**; it never downloads, installs or runs FACAD, never agrees to an EULA, and never uploads vendor source content or cases.

**Rights gate:** The FACAD vendor's publicly published terms indicate fixed licenses are computer-specific and installation in other computing environments without manufacturer consent is prohibited. Historical GitHub runners that successfully installed FACAD were disposable and do **not** convey durable authorization to a new runner. The owner must establish valid current license/consent for the actual machine used to export before any such GUI operation. An operator's `authorized_facad_use_confirmed=true` in the intake file is merely an assertion and requires independent documentary confirmation. Keep D3 isolation UNVERIFIED, no clinical edit / Save until verified.

**New result gate:** No authentic six-file export set, no Ricketts 32F or 13F patient/sample numeric analysis results, and no numeric matches have been produced by this branch. If the contract tests pass, only the **private intake tooling** is verified. Numeric parity remains 0/45 observed, workflow parity 0/7 and CLINICAL NO-GO. No merge/deploy without separate approval.

## 2026-10-24 — 45-position source-locked *manual* numerical diagnostic (NO CLINICAL PARITY)

The independent **offline, nonclinical** `audit/cephalo_facad_manual_delta_diagnostic.py` tool is new in DRAFT PR #1065. It provides a source-locked review plan for 32 named **FACAD Ricketts 32F** vendor factors (the six existing mapping entries + the 26 resolved backlog entries) and **13 numbered 13F slots**. Its source set on `master` does **not** independently contain an ordered, named FACAD 13F roster: it must not silently substitute the **Gregoret/Atlas** 13 factor list. All 45 are *readiness slots* and **zero are measured clinical parity rows**. The 7 especially sensitive 32F constructs use the exact `facad_order` locks and `direct_alias_allowed=false` from the canonical final-seven schema; the additional vendor variants retain their separate construct identity.

Readiness summary only (no vendor data, no license action):

```bash
python -m audit.cephalo_facad_manual_delta_diagnostic \
  --private-output /private/unused-new-directory/facad-readiness.json
```

A supplementary **manually transcribed synthetic candidate** may be reviewed with `--manual-input /private/trace-candidates.json`; the tool only accepts a strict opaque case ID, at most 45 exact factor order/label slots, optional DECIMAL STRING values, unambiguous `mm`/`deg` units, an explicit DC canonical ID, and separate geometry/sign/rounding booleans. Neither the fact that the operator ticks those booleans nor a computed numerical difference proves a vendor export, provenance, landmark identity, signed/rounded display equality, or clinical concordance. Entries associated with seven source-locked sensitive geometries, any other vendor-specific variant, unit mismatch, false attestation, missing value, or unverified FACAD 13F roster are **refused a numerical difference**. Any difference that is computed is labeled `RAW_MANUAL_DIFFERENCE_UNVERIFIED`; exact numeric equality **never** creates a PASS status.

The tool produces an output file **outside the repository** only if the file does not yet exist, does not access/parse FACAD installer, GUI, trial, EULA, raw vendor files, patients, archived PDFs or Digital Crown application runtime; it neither changes the existing LOT08 manifest nor publishes any data. This is preparation for a *later* independently sourced, consented six-file and same-calibration FACAD/DC numerical comparison. DO NOT use the diagnostic with real patients or clinical decisions. Current status remains **0 actual Ricketts numeric comparisons / 45 expected positions, 0 authentic new six-file exports, CLINICAL NO-GO**.

Contract tests are in `audit/test_cephalo_facad_manual_delta_diagnostic.py`; the CI `.github/workflows/facad-robert-private-intake-contract.yml` runs them **only with synthetic values** alongside the original 16 private-staging tests. No runtime or official FACAD GUI is invoked.
