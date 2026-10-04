# Orthodontic Studio LOT07-A0 — Workbench baseline

Status: READ-ONLY BASELINE
Base: `75943271add87f0f10b93497531e5229f5e5e07f`
Branch: `feat/ortho-studio-lot07-workbench`

## Goal
Inventory the real pre-LOT07 orthodontic workspace without changing LOT06 scientific formulas.

## Existing assets
- Cephalo renderer/controller: `CephaloTracingLayer.tsx` + `CephaloTracingLayerBase.tsx`.
- Landmark edit interaction and persistence hooks.
- Magnifier/fullscreen and analysis-mode filtering.
- Ghost/T1/T2 display data with opacity/color support.
- Analysis workbench panel and measurement focus behavior.
- Existing superimposition viewer with overlay opacity.
- Existing Ortho store already carries patient photo records and upload helpers.
- Existing longitudinal/cockpit modules and PDF/report paths.

## Observed gaps
1. **No registry-driven layer manager** for Landmarks / Plans / Hard tissue / Teeth / Soft tissue / Measurements / T1 / T2.
2. **No demonstrated undo/redo contract** for landmark/structure edits.
3. **No versioned anatomical-structure contract** separating measurement-authoritative geometry from display-only contours/templates.
4. `CephaloAnalysisWorkbenchPanel` and renderer still contain frontend mappings/constructions that must be replaced or quarantined behind the LOT06 canonical dependency graph.
5. Tooth/soft-tissue drawing contains display-oriented templates/interpolation; it must never become scientific authority by accident.
6. T1/T2 UI exists, but the longitudinal scientific registration contract is not established by LOT07 itself.
7. Photo state exists, but current slots/persistence are not yet the canonical five-view orthodontic record protocol; localStorage previews are not a sufficient clinical record store.
8. No explicit model/scan record contract (STL/PLY/OBJ or reconstructed model) in the workbench.
9. No demonstrated tracing SVG/image export contract tied to structure/provenance state.
10. Mobile/tablet precision-edit policy and 200% text evidence still need LOT07 AFTER validation.

## Product boundary fixed after LOT06
LOT07 owns the **case/tracing workbench and record interfaces** only.
It does not implement:
- new cephalometric formulas or norms;
- photo-derived crowding;
- Bolton/model analysis;
- five-photo 3D reconstruction;
- diagnosis or treatment planning.

Those capabilities are downstream LOT08–LOT11 consumers of the record interfaces.

## Required LOT07 contracts
- `ortho_case_record_contract_v1`
- `cephalo_anatomical_structure_contract_v1`
- `ortho_layer_registry_v1`
- LOT06 canonical measure→geometry dependency adapter
- auditable edit history / undo-redo contract
- export serialization contract

## Visual gate
Before any significant UI mutation: capture BEFORE at 390/430/768/1280.
After implementation: capture the same viewports + 200% text and compare Target↔Render.
No visual PASS claim without observed AFTER.

## Gate
`ORTHO_STUDIO_WORKBENCH_VERIFIED`
