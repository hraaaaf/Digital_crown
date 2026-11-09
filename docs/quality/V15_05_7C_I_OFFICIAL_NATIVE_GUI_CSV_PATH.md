# V1.5 LOT05.7C-I — Open Dental official native GUI CSV path / NO INSTALL OR IMPORT

**Date:** 2026-11-09
**Decision:** Document an independently verified **publisher-native GUI export route** and the exact boundary to a future disposable, fictitious-only lab. This document does not authorize trial installation, license acceptance, a database service, patient access, CSV generation, or import into Digital Crown.

## GOAL / SUCCESS / PROOF

- **GOAL:** differentiate a real GUI-origin `.csv` from a CSV derived offline from the MyISAM demo table.
- **SUCCESS of this documentation lot only:** official navigation and export controls are identified by the publisher, with privacy, service and human gates noted.
- **PROOF:** vendor documentation at the following stable links; no desktop execution is claimed:
  1. [Open Dental — Trial Version](https://www.opendental.com/site/trial.html): trial version 25.3.48 offers blank `opendental` and `demo` fictional-patient databases, maximum 30 patients, no API. Installer sequence explicitly states click **Install**, then **OpenDental Setup Wizard**, *then* separate MariaDB installation and database selection after setup. Do not conflate the first **Windows Installer / Preparing to install...** dialog with the Setup Wizard.
  2. [Open Dental — Patients Report](https://www.opendental.com/manual/reportpatientraw.html): from **Reports → Standard**, in **Lists** choose **Patients – Raw**, choose columns, optional **WHERE** filters, then **OK** to run the report; its results are displayed inside **User Query**.
  3. [Open Dental — User Query](https://opendental.com/manual/queryoverview.html): Query Results window provides **Export .csv**, a comma-delimited file; `Raw` format preserves untransformed source numbers/values (including `PatNum`); optional `OpenDentalExports` default export path; permission `User Query` or `User Query Admin` depends on the actions.
  4. [Open Dental — Reports](https://www.opendental.com/manual/reports.html): Reports → User Query is also a **direct** route, distinct from the Patients – Raw standard report route.

## Canonical publisher-native end-to-end route — NOT YET EXECUTED

1. On a **disposable, isolated, fake-only Windows environment**, launch the official signed trial, verify vendor SHA/AuthentiCode, no pre-existing MySQL/MariaDB service. **HUMAN GATE** before passing the observed Windows Installer preparation dialog or taking any further installer action. No patient data, network share or local workstation.
2. An authorized installation would have to finish the true **OpenDental Setup Wizard**, the separate MariaDB stage, then select the publisher-provided **demo** database of fictional patients. **This has NOT been authorized or run.** EULA/Next/Finish, MariaDB setup, and database installation are *separate explicit gates*.
3. In running Open Dental: **Reports → Standard → Lists → Patients – Raw**, choose essential patient columns with `PatNum`, select a **Raw** query representation, `OK`, then in the **User Query results** click **Export .csv**. This is the explicitly documented publisher-native GUI path. **Not performed or visually witnessed.**
4. A future acceptable proof must include a locally verified publisher-generated CSV, source screen captures showing the **demo** database and GUI export action, byte hash + schema/header + row count, and source lineage. **Do not export real clinical data to any CI artifacts or connected cloud systems.**
5. Compare the publisher-generated CSV against the existing fake-only MyISAM-derived sample as distinct data sources. The latter is **NOT** a GUI export and cannot be relabeled.
6. Mapping into Digital Crown requires subsequent distinct clinical/privacy gates, backup + restore and local transactional rollback proofs; **never permit patient import based on this documentation or on synthetic-only green CI**.

## Current verifiable state

- [PR #1240](https://github.com/hraaaaf/Digital_crown/pull/1240) LAB read-only merged, no publisher-click executable added to `master`.
- [Prior disposable actual post-click evidence run #42610191050](https://github.com/hraaaaf/Digital_crown/actions/runs/42610191050): first native HWND visually **Windows Installer / Preparing to install... / Cancel**, **not** the OpenDental Setup Wizard. Publisher-only image artifact #13669189687; original image SHA256 `ca1157a1cd0531fe01f5e29abfb2e40c83f650c3f1dfd6ebcff8592d22ad7440`.
- Native GUI `Patients – Raw → User Query → Export .csv`: **NOT RUN / NOT VERIFIED**.
- Setup Wizard, EULA, MariaDB, demo DB loading, import, real patient dataset, production: **NO-GO**.
- Unrelated [theme PR #1242](https://github.com/hraaaaf/Digital_crown/pull/1242): **OWNER REJECTED DARK LOGO / DRAFT / PARKED**, not a LOT05 success.

## NEXT exact, requiring a distinct owner gate

Prepare a disposable, controlled *observation-only* procedure to distinguish the transient **Windows Installer** stage from the actual **OpenDental Setup Wizard**, without EULA acceptance, `Next`, MariaDB or DB setup. The next executable installer interaction must be described and separately authorized before any physical click. Never infer GUI CSV success from a raw database table or an offline exporter.
