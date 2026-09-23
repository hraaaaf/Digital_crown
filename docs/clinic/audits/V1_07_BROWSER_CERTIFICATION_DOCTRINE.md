# Digital Crown V1-07 — Browser Certification Doctrine G1→G8

Status: ACTIVE

## Goal
Use the installed Playwright/Chromium runtime to certify real user-visible behavior across every interactive V1-07 gate, not only G4.

## Rule
Component/Vitest evidence remains useful but cannot alone certify a visible interactive control.

For G1→G7, certification requires:
1. real Chromium inventory at compact + desktop viewports;
2. every enabled semantic control reconciled to a Playwright action;
3. observable navigation, persisted result, visible state change, or refusal/non-mutation proof;
4. dynamic controls revealed after clicks appended to the denominator;
5. initially disabled controls exercised once their prerequisite can be created;
6. exact-head tests/build green.

G8 remains the transverse/adversarial browser layer: error vs empty truth, permissions, accessibility, offline state and single-flight mutations.

## Execution order
G2 Dashboard/Patients → G5 Settings/Team/Backup → G3 Agenda/Frontdesk/Notifications → G6 SuperAdmin/licences/trial → G7 Stock/Marketplace/Library → G1 public/auth/onboarding. G4 continues with its existing deeper browser action matrix.

## Factory
- `frontend/scripts/inventory-v1-07-g1-g7-browser-controls.mjs`
- `.github/workflows/v1-07-g1-g7-browser-inventory.yml`

Inventory is denominator evidence only, never certification. Each G requires an action-pass matrix before G9 freeze.

## G9/G10
G9 may freeze only after final runtime inventories are semantically reconciled to browser action proof or verified N/A rationale. G10 must use that exact-head browser evidence before merge/post-merge.
