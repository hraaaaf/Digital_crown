# Facad 3.14 Quick Demo — D2 visual proof, status and next gate

**Date:** 2026-10-08  
**Status:** **D2 partially supported by actual BEFORE/AFTER/RESTORE evidence; comprehensive D2 OPEN. D3 mutation BLOCKED.**  
**Source run:** [#37846709636](https://github.com/hraaaaf/Digital_crown/actions/runs/37846709636), **SUCCESS** at `a66e607d9f5b264af4b3d375f73b8201cc206d19`, artifact **#11579739020** (`facad-314-quick-demo-bootstrap-a66e607d9f5b264af4b3d375f73b8201cc206d19`).

## Grounded findings

The run `d2-status.txt` reports `D2_VIEW_CANDIDATES=12`, `VIEW_VERIFIED_TOGGLE_RESTORE=0/12` by its *UIA state check*, 5 with screenshots, 7 explicitly `SKIPPED_NO_STATE_PROOF`, and `D2_MODE_CLICKS=6`. These are distinct from four **pixel-observed** reversible changes. No automatic inference from green CI is permitted.

Image comparisons were run on the **real 1024×768 PNG evidence**, RGB channel delta >10, count of pixels with any changed channel. Tracing region crop: **x=556..984, y=113..694**, excluding top menus and Windows taskbar. Status crop separately within the app's bottom strip. Comparison is screen-state evidence only, **not a functional or scientific calculation test**.

| Control | Pixels changed BEFORE→AFTER, tracing crop | Pixels changed BEFORE→RESTORED, tracing crop | Evidence verdict |
|---|---:|---:|---|
| View > Hard tissue | 8,122 | 0 | Red hard-tissue geometry hidden then perfectly restored in crop |
| View > Profile | 1,321 | 0 | Visible profile geometry change, restored in crop |
| View > Ceph/Lines | 1,477 | 0 | Visible cephalometric line change, restored in crop |
| View > Marker guide | 0 | 0 | Activation attempted, **NO visible change proved** in tracing crop |
| View > Status bar | 0 | 0 | Tracing crop unchanged by design; app status-strip crop shows **change and restoration** |

The seven `SKIPPED_NO_STATE_PROOF` options: Marker names, Markers, Bindings, Tracing image, Profile photo, Image #2, Harmony box. Deferred separately: Original positions, Planned positions, Predicted photo, Generate predicted photo, secondary windows. **Do not claim these tested.**

The six mode toolbar entries were clicked and returned to SelectMove, with screenshots, **without clicking the radiograph**: SelectMove, Zoom, Measure distance, Measure distance to line, Measure angle (3 points), Measure angle (4 points). They are **mode activation tests**, not verified distance/angle results.

## Safety / D3 prerequisite

Prior D3 preflight looked in `C:\Facad\Examples\Robert-2.0.fcd` and logged `SAMPLE_SOURCE_PRESENT=false`. This was a **harness path mistake**, not evidence that the patient example was missing. The actual workflow already resolves and launches `facad-quick-demo/release/Examples/Robert-2.0.fcd` from the official release extraction. New test receives that same exact `$case` path and hashes original/copy/original, but **does not yet mutate either**. Source and copied file equality is not proof of application-level isolation (Facad may have additional writable persistence).

## Next exact run

Commit `10be5b86dd707f161165c0d467c74155490062a9` starts [#37848294942](https://github.com/hraaaaf/Digital_crown/actions/runs/37848294942):

- Validate four observed D2 reversibility changes in the same ROIs using automated RGB pixel sampling: three tracing overlays plus Status bar; gate fails if visible change or restoration not proven.
- Keep Marker guide and all other inconclusive View entries **open**, not manufactured as PASS.
- D3 preflight uses exact official release sample path and stores SHA256 proof for a scratch copy. **No clinical edit**, plan, save, license action or network call.

**Remaining:** D1 has discovered 65 Standard lateral analysis names but has *not* opened 65 profiles individually nor cataloged all measurement rows and modalities. D2B, D3 controlled edit under proven isolation, D4 report/export and D5 clinical/UX comparison remain open. No merge or deployment.

## Adversarial internal perspectives

- **Proof reviewer:** CI green cannot mean 12/12 View pass when the UIA gate reports 0/12 and only 4 screenshot pairs show visible change/restoration; photographic ROI test is stronger for display controls but narrower than operational correctness.
- **Clinical/safety reviewer:** No added landmarks, no modified cephalometric measurements, no transferring Facad norms into Digital Crown, no patient rewrite. Any stateful planning must use an application-level isolated disposable example first.

**Status:** D2 partially evidenced, not CONVERGED, no independent third-party review.
