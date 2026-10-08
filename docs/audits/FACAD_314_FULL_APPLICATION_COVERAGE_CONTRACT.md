# FACAD 3.14 Quick Demo — full application reverse-benchmark coverage contract

**Status: OPEN — inventory/test campaign, not completed benchmark.**  
**Subject:** legally installed official Facad Quick Demo 3.14.1.1111; official bundled sample `Robert Example`, no real patient data.  
**Objective:** observe and reproduce *every accessible feature*, analysis, dialog and workflow, with capture- and state-based proof. Source code and UIA metadata are not substitutes for successful interactions.

## Observed starting point

- [Facad editor verified on run #37841266986](https://github.com/hraaaaf/Digital_crown/actions/runs/37841266986), commit `03220c036ebc65896ff5fd307a4e0d74ac063d52`, artifact #11578251769.
- Actual editor BEFORE: Robert Example > Examination 1 > Pretreatment tracing; split **Analysis** / **Tracing** panes and **Bergen short** table with 12 listed measures.
- **Nine top-level menus** visible by UIA: File / Edit / Tracing / View / Cephalometry / Image / Tools / Window / Help.
- **30 Facad-named toolbar buttons** in the AFTER UIA tree (listed below). Presence ≠ enabled, tested, or safe.
- First 5 menus observed in a prior run: File (16 non-top names), Edit (3), View (19), Tools (16), Help (8). These raw counts include submenus and are **not** guaranteed unique actionable functions. Remaining 4 menus never inventoried as of initial contract.
- GitHub-hosted Windows runner is ephemeral. The automation must group interactions after the established sample bootstrap instead of silently claiming session persistence.

## State machine and evidence

Every named element must have a row containing:

`feature_id | menu_path | control_name | UIA_type | enabled | sample_state_before | risk_class | attempted_action | observed_state_after | screenshot_before | screenshot_after | UIA_before | UIA_after | restored | evidence_artifact | verdict`

Allowed verdicts: **DISCOVERED**, **OPENED**, **TESTED**, **BLOCKED**, **DISABLED**, **SKIPPED_RISK**, **UNAVAILABLE_DEMO**, **FAILED**, **NOT_YET_TESTED**. No generic PASS from a green job; each interactive action must have a distinct BEFORE/AFTER state, or be explicitly **not proven**.

Progress is evaluated over **actual discoveries**, not expected button counts. Report `discovered_count`, `enabled_count`, `interactions_attempted`, `visually_verified`, `functional_tested`, `disabled`, `blocked`, `skipped_risk`, `remaining`. For analyses additionally report `catalog_size`, `opened_types`, `selected_types`, `visible_measurements`, `normative_source_status` and `unsupported_demo`.

## Nine menu families, all leaf commands and nested branches

1. **File** — patient/work list, patient info, open/close, new, save/save as, print/print report/print setup, edit report, analysis editor, plugins, session lifecycle. Distinguish view-only dialogs vs writes, printing, licensing and external integration.
2. **Edit** — Undo, Redo, Copy and other actual discovered items; create ephemeral modifications only on disposable official sample copies, with restore proof.
3. **Tracing** — inspect **every** level and nested submenu; marker creation/editing, lines/planes/profiles, tracing correction, control modes, saved tracing workflow if available.
4. **View** — original/planned positions, layers, profile/photo/tracing toggles, overlays, predicted photo, status, toolbars and nested options. Toggle each reversible option separately, capture display change, restore.
5. **Cephalometry** — **all** built-in analysis selection options, author/edit analysis UI, measure list, normative columns, selection/compare; systematically enumerate **entire** analysis catalog including scrolling and dependent dialog states, never infer availability from naming.
6. **Image** — brightness, contrast, crop/blend/match/import/transform/calibration and any actual submenus, with reversible sample operations only.
7. **Tools** — each measuring mode, draw/place, select/move, planning, hard-tissue split, profile, rotate center, calibration and settings; limit side effects to disposable sample state.
8. **Window** — each pane, arrangement/layout, maximize/minimize/switching and window-level controls; compare viewports.
9. **Help** — About, documentation and version verification. License/update/remote-support actions are *identified but not automatically invoked*.

For each menu: screenshot with popup visible, full accessibility hierarchy of popup, nested hover expansions, leaf-control classification, enabled state, whether a click changes view, opening of any secondary dialog, and cancellation/close restoration.

## 30 toolbar commands directly observed in the Facad tracing editor

| Group | UIA button IDs | First safe interaction rule |
|---|---|---|
| Calibration / measure (5) | `{FCD_Calibrate}`, `{FCD_Measure_distance}`, `{FCD_Measure_distance_to_line}`, `{FCD_Measure_angle_3pt_Par}`, `{FCD_Measure_angle_4pt_Par}` | Test entry modes; measurements later on a disposable sample with known calibration |
| Planning / transforms (7) | `{FCD_Plan}`, `{FCD_Split_hard_tissue}`, `{FCD_Place_distractor}`, `{FCD_Paint}`, `{FCD_Create_profile_line}`, `{FCD_Match_images}`, `{FCD_Adjust_tracing_position}` | Mode/preview first, then sandboxed interaction and reset verification |
| Tracing construction (6) | `{FCD_SelectMove}`, `{FCD_Place_marker}`, `{FCD_Draw_hard_tissue}`, `{FCD_Manual_draw}`, `{FCD_Draw_implant_line}`, `{FCD_Place_tooth}` | Non-destructive entry first; adding geometry requires disposable copy |
| Display (4) | `{FCD_Zoom}`, `{FCD_BrightnessContrast}`, `{FCD_Reset_Zoom}`, `{FCD_Blend_images}` | Try UI effects, capture BEFORE/AFTER, reset |
| Patient/session/document (8) | `{FCD_Patient_Work_List}`, `{FCD_New_patient}`, `{FCD_Open_patient}`, `{FCD_Save_Patient}`, `{FCD_Close_patient}`, `{FCD_Print_active_window}`, `{FCD_Copy}`, `{FCD_Undo}` | Inventory and safe open/cancel; no unattended writes/printing |

**Correction to grouping:** the IDs listed above are 5 + 7 + 6 + 4 + 8 = **30** (matches the verified UIA artifact). Distinct menu items can duplicate toolbar actions; coverage tracks each entry point and shared underlying capability.

## Analysis exhaustive census

Starting analysis = `Bergen short`, observed measures: SNA, SNB, ANB, SNPog, NSBa, ML/NSL, NL/NSL, ML/NL, InterIncisal, ILs/NSL, ILi/ML, Pog-NB (12). These values/norms belong to **the displayed Facad example analysis**, not a Digital Crown normative profile.

For **each built-in or demo-accessible analysis** found in the catalog:

1. Record exact analysis name/version/source if exposed, disabled/unavailable state and categorical grouping.
2. Select on the *official sample* without saving, record layout, measurement identifiers, values, units, norm columns, interpretation/quality flags, missing inputs and printed/preview availability.
3. Capture window and UIA table rows; scroll through all measures, with counts and duplicate detection. Capture bottom-of-table state.
4. Compare only after contracting equivalent landmark IDs, angle/line conventions and calibration in Digital Crown. **Name equality is not parity.**
5. Leave the original sample unchanged. If selection is persisted automatically, use a verified disposable copy first.

## Campaign execution waves and independent gates

| Wave | Real goal | Required proof |
|---|---|---|
| **D0 — Full menu & toolbar census** | 9/9 main menus, every visible submenu, every toolbar ID and enabled state | Menu screenshot + tree; CSV/JSON coverage; explicit failure status |
| **D1 — Analysis catalog** | Complete demo-visible analysis list, measures, norms and versions | Catalog open + full scrolling + UIA/screenshot evidence, one record per analysis |
| **D2 — Reversible modes + presentation** | Every permitted view/measurement mode; tab, window, layers and zoom | BEFORE/AFTER, tool state, Reset evidence |
| **D3 — Sample-only editing/planning** | Drawing, point correction, planning, splits, facial/soft-tissue visualization | Disposable example copy, before/after/reset, no unsaved drift |
| **D4 — Reports/files/dialogs** | Print preview/export/report settings and information screens | Only file-local nonprinter destinations with approval; screenshots, paths and cancel evidence |
| **D5 — Digital Crown parity** | Same authorized sample or deterministic fixture: numerical, visual and end-to-end UX | Same landmarks/calibration/protocols/viewports, results within preregistered tolerances and human scientific review |

Current first automation wave is **D0 with early read-only portions of D1/D2**, launched as [run #37843736004](https://github.com/hraaaaf/Digital_crown/actions/runs/37843736004). It **does not** justify declaring D0–D5 complete. Any unsupported/demo-locked operation receives a grounded reason rather than fabricated success.

## Safety / adjudication

- No patient identifiable material outside bundled examples; no real practice patient data.
- Do not bypass licensing, activate entitlements, manipulate trial dates, initiate remote support, send network payloads or print to a real device.
- Never infer valid clinical predictions from graphical simulations; normative sources need explicit population/age/sex/analysis-version validation.
- A destructive or irreversible operation may be *cataloged* yet explicitly **SKIPPED_RISK** until a controlled disposable environment and user authorization are in place.
- Review A — **clinical adversarial**: search invented norms, wrong point equivalences, unsafe planning/diagnoses, and ghost projections mislabeled as outcomes.
- Review B — **functional/UX adversarial**: search missed nested controls, misleading green gates, untested disabled buttons, restore failure, screen/viewport mismatch and unsupported demo branches.
- **Convergence:** same final HEAD, evidence per action, no critical findings, executed tests and two clean independent perspectives. This document is a plan, **not** an independent review or certification.

Next step after the first run: inspect all generated screenshots/logs; fill the real census, fix only observed mapper defects, then select the narrowest next wave. No merge or Vercel deployment without explicit approval.
