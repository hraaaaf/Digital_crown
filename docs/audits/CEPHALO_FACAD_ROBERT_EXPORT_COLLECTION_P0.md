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
