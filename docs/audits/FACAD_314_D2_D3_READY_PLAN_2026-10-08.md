# Facad 3.14 — D2/D3 execution-ready plan and gates

**Status**: D2/D3 PREPARED, **NOT RUN**, **NOT VALIDATED**.  
**Baseline**: official Quick Demo Robert Example, tracing and Bergen short Analysis visible. D0 [run #37843736004](https://github.com/hraaaaf/Digital_crown/actions/runs/37843736004), success, artifact #11579611135; D1 [run #37845377310](https://github.com/hraaaaf/Digital_crown/actions/runs/37845377310), status must be checked before any D2 execution.  
**No merge, no deployment, no trial/license manipulation or real-patient input.**  
**Reason for staged execution**: GitHub-hosted Windows is ephemeral. D2 must be inserted after known Robert bootstrap in the single Windows job; DO NOT redo the ten-minute D0 menu-census as a prerequisite. D1 can feed additional D2 controls when its artifact is reviewed.

## D2 — view, zoom, measured modes and window presentation

Goal: exercise every **safe, reversible display option** and report before/action/after/restore evidence per control. D0 discovered 9 top-level menus, 43 UIA buttons (25 active toolbar commands) and View options from real Facad UI. D2 is NOT limited to seven D0 toolbar mode clicks.

### Inventory: observed View menu names

**Reversible-first candidates** (verify enabled and genuine toggle semantics *in the actual UI*, never by assumption):

- Marker names; Marker guide; Markers; Hard tissue; Profile; Ceph/Lines; Bindings;
- Original positions; Planned positions; Tracing image; Profile photo; Predicted photo; Image #2;
- Harmony box; Status bar.

**Secondary windows/layout:** Analysis, Image/Tracing manager, Toolbars, Window > Cascade, Fit window to image, Window Layout presets. These may change focus/layout or open a dialog; use a separate controlled pass with re-entry/restore proof, not indiscriminate toggles.

**Explicitly excluded in D2**: View > Generate predicted photo (processing, unverified), Save/Print/Delete, trial/license, network or remote support, any click on patient image that places new landmarks or moves bone segments.

### Inventory: observed toolbar entry modes

- {FCD_SelectMove}, {FCD_Zoom}, {FCD_Reset_Zoom};
- {FCD_Measure_distance}, {FCD_Measure_distance_to_line};
- {FCD_Measure_angle_3pt_Par}, {FCD_Measure_angle_4pt_Par}.

For each entry mode, activate only the tool, capture state, return to **SelectMove**. A click on the image is a **separate D3 test** with a disposable example.

### Per-control evidence (strict)

One ledger row:
`control_name | enabled_before | mode_before | action_attempted | screen_before | UIA_before | screen_after | UIA_after | undo_reset_method | screen_restored | UIA_restored | result`.

**Result states**: `NOT_STARTED`, `DISABLED`, `BLOCKED`, `ACTION_ATTEMPTED`, `AFTER_CAPTURED`, `RESTORED_OBSERVED`, `POSSIBLE_VISUAL_CHANGE`, `TESTED`, `UNAVAILABLE_DEMO`.

A button click alone is **not** evidence that a view changed. If UIA TogglePattern exists, assert its state changes and returns; otherwise compare the relevant tracing/pane region in screenshots, not whole-screen screenshot hashes (mouse cursor/hover changes). Reopen original View menu and explicitly restore; stop immediately if restoration fails. Take **last whole-workspace screenshot** and compare to baseline; capture disabled states and never force-enable.

### D2 mandatory gate

1. D1 result/artefact inspected; D0 bootstrap replay only.
2. All **observed and safe** View controls accounted for with outcomes; no hidden denominator.
3. Each actually activated control has BEFORE/AFTER and RESTORE.
4. The active original case remains Robert Example / Pretreatment tracing, no new editable plan.
5. Zero unresolved change to view, tracing, window arrangement or sample state.
6. Summary contains exact counts and evidence filenames. A green job does not mean D2 clinically validated.
7. If an option is missing/disabled in Quick Demo, count **UNAVAILABLE_DEMO** with screenshot/proof; do not invent a bypass.

## D3 — disposable-case tracing edit and planning controls

**Cannot safely start before D2 restoration and D1 catalog discovery are assessed.** This plan intentionally does not authorize modification of the original Robert example.

### Precondition: isolated disposable Facad workspace

- Identify actual writable storage and sample import/export mechanisms through **documented Facad behavior**, not by guessing that `C:\Facad\Examples\Robert-2.0.fcd` holds all changes.
- Create a **disposable copy** of the bundled Robert case in a separate workspace with distinct identifier, confirm it is the active case through screenshot/UIA.
- Calculate baseline hashes/manifests of any source example and relevant writable data; ensure change and rollback remain within isolated disposable paths. Protect install and license state.
- Before first mutation, verify that the copy is editable under legal Quick Demo conditions and the original can be reopened unmodified. If not demonstrable: **D3 BLOCKED**, no action.

### D3 test slices (per operation)

| Test | Interaction on disposable case only | Required proof |
|---|---|---|
| D3-A | Place/adjust a landmark, then undo or restore | Position-before and AFTER, measurement recalculation, original unchanged |
| D3-B | Draw/remove construction, soft/hard tissue marker | Geometry BEFORE/AFTER/RESTORE and UIA/menu state |
| D3-C | Calibrate against an officially known scale in disposable source image | Physical source provenance, value, reset proof |
| D3-D | Distances and angles: 2pt / 3pt / 4pt / to-line | Points selected, displayed units, numeric reading, no invented correctness |
| D3-E | Original vs planned positions and Plan tool | Planned overlay and movement ledger, separate observational/simulated semantics |
| D3-F | Maxillary/mandibular rotation or hard tissue split | Only with documented copy/undo mechanism, explicit screen and restore |
| D3-G | Profile line/image match/blending | BEFORE/AFTER and source image provenance, no prediction claim |
| D3-H | Multi-tracing / predicted photo entry points | Only UI discovery until activation constraints and side effects are known |

For each test: original-case hash/state, disposable case identifier, feature/menu/button, prior selected mode, BEFORE screen/landmarks/values, action, AFTER screen/landmarks/values, Undo/Reset, final screenshot, storage-diff verification and failure classification.

**Absolute rule**: no clinical assessment, treatment recommendation or model-prediction claim from a graphical change; no patient data outside official example.

## D4 — report/export roadmap, ready for later

Read-only discovery: File > Edit report, Print report submenus, Cephalometry > Export > Analysis Values/Properties/Object Values/Properties, Copy as Image, image export and user-facing report/analysis editor. Exclude physical printer and external network; output to **approved temporary local paths only**, after confirming license and data permissions. Compare report content, units, displayed norms, provenance and image resolution to Digital Crown; do not assume menu visibility proves generation.

## D5 — parity prerequisites

Both products must use the **same rights-cleared fixture**, calibrated geometry, marker IDs, analysis definitions, norms tied to explicit age/sex/population/method and same viewport/resolution, with a human scientific gate. Priority matched measurements: SNA/SNB/ANB; other Bergen short rows only after identity-equivalence decisions. Separate direct observations, calculated geometry, historical norms, illustrations, predictions and clinical judgments.

## Adversarial review notes

- **Clinical/safety perspective**: stop if historical Bergen short norms leak into Digital Crown, sample edits affect original, predicted photo is called validated, or source contracts mismatch.
- **Automation/evidence perspective**: stop if skipped/disabled controls disappear from denominator, screenshots missing, restoration not proven, the workflow green-gates a block, or D0 is needlessly repeated every run.

**Outcome of this document**: D2/D3/D4 test contracts ready. Executable Windows D2/D3 automation and CI outcome still require implementation and actual evidence. No assertion of full application parity.
