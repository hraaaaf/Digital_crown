# FACAD trial — next Windows run, scope and gates (2026-10-11)

## Verified runner, not a locally installed desktop
- The existing workflow [facad-314-f02-2-readonly.yml](https://github.com/hraaaaf/Digital_crown/blob/feat/cephalo-facad-direct-parity-runtime-probe/.github/workflows/facad-314-f02-2-readonly.yml) on `feat/cephalo-facad-direct-parity-runtime-probe` already downloads official `Facad-Installer-3.14.1.1111.exe`, installs Quick Demo on `windows-latest`, checks PowerShell syntax and uploads evidence. `workflow_dispatch` exists.
- Existing scripts: `scripts/facad_314_f02_2_readonly_view_probe.ps1`, `scripts/facad_314_f02_3_passive_anatomy_menu.ps1`, `scripts/facad_314_f04_1_passive_export_menus.ps1`; the last script opens only File/Edit/Cephalometry/Tools roots, takes screenshots and UIA, and explicitly logs `LEAF_CLICK_INVOKED=false`, `SAVE_INVOKED=false`, `SHARED_APP_STORAGE_ISOLATION=UNVERIFIED`.
- The latest relevant completed runs are already green; a rerun of the **same SHA** produces no new measurement or interaction coverage. A run is **not** currently dispatched by this research-only documentation commit.

## Targeted next run: FAC-TRIAL-A/C/D (read-only only)
1. Reuse official Quick Demo and existing D3 preflight. Assert process identity, demo sample provenance and no real patient data.
2. A: screenshot and UIA of Marker guide, Planned positions, Tracing and View roots. Compare identical viewports BEFORE/AFTER, and classify menu item toggles as UIA metadata only until visual change proven.
3. C: screenshot and UIA of File/Edit/Cephalometry/Tools and the passive `Values`/`Properties` tabs; record which of Analysis Values, Analysis Properties, Marker Positions and Object Values is **actually observed**. No leaf click, Save, Load, Export, PDF creation or simulated patient.
4. D: hash official sample and disposable copy BEFORE/AFTER; check process-aware file writes and storage isolation. If unverified, record `D3_OPEN_RED`, do not mutate.
5. Upload screenshots, UIA, CSV, SHA manifests, parser checks, per-probe verdict, exact source SHA, and the run URL. Compare artifact to existing runs #37967170536 and #38102158028.

## Required engineering before dispatch
- Add only bounded passive tab inventory to the existing PowerShell script; inspect script for process/foreground checks, file write safety and no unsafe interactions.
- Modify a dedicated Windows workflow or its script on an isolated branch, with a trigger that actually runs the new branch. The current workflow's push trigger covers **only** `feat/cephalo-facad-direct-parity-runtime-probe`; a commit on the research branch will **not** trigger it.
- Do not change `master`, merge, deploy or alter the trial licence.
- No fake progress: `NEW_RUN_NOT_LAUNCHED`, `FACAD=19/39`, `D3_OPEN_RED`.

## Scientific track FAC-TRIAL-B in parallel
Work from C02's 34-page page-scoped source index, the 65-analysis crosswalk and authorized official manuals. Label every operator/dependency/normal range as SOURCE_VERIFIED, VENDOR_OBSERVED, or UNKNOWN. No formula inference from word co-occurrence.

## Trial urgency
User says trial length is 7 days, **activation and expiry date not verified**. GitHub hosted Windows VMs are ephemeral and availability of FACAD Quick Demo does not establish a reusable or extendable licence. Record the licence expiry as displayed; do not circumvent licensing.
