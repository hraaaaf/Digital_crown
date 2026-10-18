# CEPH-FAC-PARITY / P2ter++ — FUE-I exploratory Cabinet, first useful PDF

Version: 2026-10-18. Applies **only** to PR #957; methodology consulted from AGENTS.md and PR #783 (laboratory read-only). No FACAD or broader V1.5 setup workflow and no change to the #783 laboratory.

**Persona:** cabinet dentist opening the Cephalometry workspace for the first time, on a fresh browser (no auth/localStorage carried over). **Environment:** isolated T2 with legitimate JWT/workstation enrollment and existing synthetic patient + two versioned analyses seeded. Not an empty patient and not real clinical data.

**First Value:** after login and selecting the older study in History, the user receives an actual downloadable draft PDF whose authenticated response binds patient + analysis ID + scientific revision; then uses the archive button to retrieve a verified official PDF replay for exactly this revision. This is FUE-I for the completed P2ter++ archive workflow, **not FUE-G** for the whole cephalometric journey or clinical approval.

**Viewports:** 390×844 mobile responsive web and 1280×900 desktop. The native mobile application is NOT asserted. On mobile the implemented `data-cephalo-mobile-step-selector` must be visible and usable; the desktop uses the Step 4 button.

**Check-by-check evidence:** real hub login, Cabinet, first study selection, mobile/desktop step control, viewport overflow, first downloaded PDF bytes and headers, official PDF replay using a genuine UI button. Every step records PASS/FAIL/NOT_TESTED, elapsed milliseconds, screenshot on failure; capture BEFORE hub, BEFORE study choice, BEFORE first value, AFTER first value, AFTER archive, consistent viewport. The report is attached to the existing experimental Cabinet workflow and stamped with exact Git SHA. PDF scientific authenticity is not assessed by UX evidence.

**Severe UX score:** retain N/A until a reviewer has inspected full BEFORE/AFTER images, interaction clarity, accessibility, errors and recovery; a successful technical matrix is not 10/10. Score each item severely /10 when inspected. FUE-I PASS must not substitute for two independent adversarial reviews or CONVERGED=true.

**Deliberately missing/not certified:** genuine *first new patient* and first radio upload, end-user onboarding without seeded data, full multi-step clinical data entry, cross-user permission exploration in real browser, mobile native app, 768×1024 tablet, crash recovery, native SQLCipher/Postgres, truly simultaneous UI two-tab buttons, photos durable after navigation. These are NOT TESTED/N/A, not silently GREEN. See `techdoubt.md`.

**No merge, deployment, production workstation mutation, PR #783 edit or new roadmap lot.** Roadmap 41/99.
