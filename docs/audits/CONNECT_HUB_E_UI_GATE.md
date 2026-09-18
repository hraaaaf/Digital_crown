# Digital Crown — LOT E — Connect Hub UI Gate

Status: **CLOSED — BEFORE/AFTER certified and human-approved**
Architecture: `docs/audits/CONNECT_HUB_E_ARCHITECTURE.md`
Baseline product SHA: `49db132882ba5b352ae761bda34e1a9fa3d82e27`

## Verified BEFORE surface

The cabinet shell currently fragments communication/attention signals:

- `Header.tsx` exposes a bell whose popover is specifically **Alertes de trésorerie** and links to accounting.
- `Sidebar.tsx` separately polls `/intelligence/alerts/today` and exposes the count as the dashboard badge.
- There is no verified cabinet-side unified communication surface in this shell.

The existing bell and sidebar are therefore the exact baseline interaction surfaces for LOT E.

## UI Goal

Turn the existing cabinet attention entry point into a compact **Connect Hub** that gives the practitioner one truthful, scannable place to understand communications requiring attention, while preserving Digital Crown's existing shell, design tokens and canonical source/action boundaries.

The UI must make the distinction visible between:

1. **À traiter** — actionable items backed by an existing canonical source/action;
2. **Informations** — source state that does not imply a delivery action;
3. **Canal / état** — only when the underlying source actually proves it;
4. **Non vérifié** — explicit when external delivery/receipt is not proved.

## Reference / mockup contract

Desktop/tablet:

- Keep one bell/attention trigger in the existing header; do not add a competing global nav system.
- Opening it reveals a premium anchored panel titled **Connect Hub**.
- Top row: concise total requiring attention + optional filters that are derived from canonical source categories, not duplicated state.
- Main body: vertically scannable items with source/category, patient/cabinet context only when authorized, concise action/state, and canonical destination/action.
- Treasury remains a source/category inside the hub rather than a separate semantic meaning for the bell.
- Empty state must state that there is nothing requiring attention, not that every external message was delivered.

Mobile 390px:

- Keep the header trigger reachable with a minimum practical touch target.
- Connect Hub opens as a width-safe sheet/panel with no horizontal document overflow.
- Primary information and action remain readable without relying on hover.
- No patient-sensitive preview may leak outside the authenticated/authorized shell.

Visual language:

- Reuse existing Elite tokens: `rounded-elite`, card/glass surfaces, `primary`, `text-main`, `text-muted`, `border-main`, existing shadows and typography.
- No new arbitrary visual system, gradients or decorative dashboard inside the panel.
- Hierarchy comes from spacing, typography, badges and restrained source icons.

## BEFORE certification contract

Capture the **exact baseline SHA** `49db132882ba5b352ae761bda34e1a9fa3d82e27`, not the implementation branch product code.

Certified viewports, matching the existing repository visual harness convention:

- `390x844`
- `768x1024`
- `1280x900`

For every viewport the harness must prove:

- shell renders without page/console errors attributable to the harness;
- no horizontal document overflow;
- the header bell exists;
- opening the bell exposes **Alertes de trésorerie**;
- the baseline does **not** contain a visible `Connect Hub` surface;
- screenshots exist for shell closed and bell popover open;
- external egress is blocked or deterministically stubbed;
- report records the exact baseline SHA and phase `BEFORE`.

Required artifacts:

- `before-shell-390x844.png`
- `before-bell-open-390x844.png`
- `before-shell-768x1024.png`
- `before-bell-open-768x1024.png`
- `before-shell-1280x900.png`
- `before-bell-open-1280x900.png`
- `report.json`

## AFTER comparison contract

AFTER must use the same three viewports and comparable shell state. It must prove:

- one global Connect Hub trigger, not two competing notification entry points;
- treasury remains reachable inside the unified surface;
- no horizontal overflow;
- keyboard/touch accessibility of trigger, close/dismiss and primary item actions;
- truthful status labels — no mock/simulated transport represented as delivered;
- authorized context only;
- Target ↔ Render comparison against this contract and the certified BEFORE.

Real BEFORE/AFTER screenshots were inspected at all three canonical viewports. Final observed visual score: **9.2/10**, above the project minimum 9.1/10.

## Certified evidence

BEFORE:
- baseline product SHA: `49db132882ba5b352ae761bda34e1a9fa3d82e27`;
- workflow run `35202983003`: SUCCESS;
- artifact `10488787031`, `connect-hub-e-before-exact-baseline`;
- digest `sha256:dac724723b62dd8cc8f6bedecf749dca4e0d27085f6aeb882197d474096edffa`;
- captured viewports: 390×844, 768×1024, 1280×900.

AFTER:
- product HEAD `ad171dd559bd6af517e57ea945de4c03317c1b72`;
- Connect Hub E AFTER #10 / run `35241949717`: SUCCESS;
- artifact `10505184198`, `connect-hub-e-after-exact-head`;
- digest `sha256:d9dcacb39eeca88a44ae3740d3097c8f887e865e5516089398178efcefffed39`;
- same three viewports inspected;
- no horizontal overflow observed in the certification report;
- mobile panel refined to symmetric safe margins;
- source-state truth language retained;
- visual score: **9.2/10**;
- human visual approval recorded in the project conversation before merge.

## Gate

**CLOSED.** BEFORE → Goal/reference → implementation → AFTER → comparison → automated checks → human approval were completed. No further visual change is required for LOT E closeout.
