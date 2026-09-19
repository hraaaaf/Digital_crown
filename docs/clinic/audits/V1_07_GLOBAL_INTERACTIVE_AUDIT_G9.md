# Digital Crown V1-07 — Global Interactive Audit — G9

Status: IN PROGRESS — FREEZE BLOCKED

## Goal
Reconcile G0 static inventory with G1→G8 behavioral evidence, isolate every unresolved gap, and freeze a truthful semantic denominator only when no known critical control remains untested or defective.

## Current reconciliation state

### G0
Status: denominator not certified.
Raw inventory remains a discovery signal only:
- 418 source files scanned;
- 40 route declarations;
- 38 unique explicit routes;
- 3653 raw static interaction/action signals;
- 195 existing test files at initial G0 run.

Raw signals are not the semantic denominator because shared components and overlapping static signals can both overcount and undercount real user controls.

### G1 — Shell/auth/onboarding
Functional matrices exist.
Certification still depends on exact-head tests/build and inherited CI proof.

### G2 — Dashboard/patients/dossier boundaries
Functional matrices cover Dashboard, patient list/create/edit/import, dossier navigation/permissions/deep-links and form variants.
Certification still depends on exact-head tests/build.

### G3 — Agenda/frontdesk/notifications
Functional matrices cover agenda shell, appointment create/edit/delete, frontdesk/pending/import, mobile frontdesk/notifications/waiting room.
Certification still depends on exact-head tests/build.

### G4 — Deep clinical/business
Functionally reconciled.
Behavioral proof covers Document Studio, ordonnance, certificates/libre, devis, honoraires, installments, patient finance/payment, clinical odontogram, conclusions, treatment plan, 9 clinical wizards, RVG, panoramic and cephalometry.
Certification still depends on exact-head tests/build.

### G5 — Cabinet/settings/team/security
Functionally reconciled.
Settings tabs, backup/restore and practitioner context are mapped; TeamManager reuses reconciled LOT2 proof.
Certification still depends on exact-head tests/build.

### G6 — Commercial/SuperAdmin/licences
Most controls behaviorally covered.
BLOCKER: LicenseStatusPage hardcodes “Elite” for every expired account despite no available subscription-plan truth.

### G7 — Stock/marketplace/library
Marketplace/admin/detail pages, Library and Science Hub are behaviorally mapped.
BLOCKERS in Stock:
1. read failure can render as truthful empty;
2. permanent delete has no confirmation;
3. mutation failures lack explicit user-facing refusal/error state.

### G8 — Transverse/adversarial
Functionally reconciled.
Evidence covers modal accessibility, offline truth, error-vs-empty/refusal/permissions, responsive reachability and representative single-flight mutation controls.
Certification still depends on exact-head tests/build.

## Freeze blockers

G9 cannot freeze while any of these remain:
1. G6 LicenseStatus product-truth defect.
2. G7 Stock read/delete/mutation-error defects.
3. Exact-head frontend tests/build not green for the final reconciled HEAD.
4. G0 semantic denominator not frozen after final source changes.

## Semantic denominator rule
A user-visible control counts once per distinct business behavior/state contract, not once per static source match.
Shared-component instances are reconciled by business context.
Overlapping signals (button + onClick + mutation API signal) are one semantic control unless they expose distinct actions.

## Freeze success
G9 is complete only when:
- all known blockers are resolved;
- exact-head behavioral suite/build are green;
- G0 is rerun on the final candidate;
- every final semantic control maps to behavioral proof or an explicit non-applicable rationale;
- zero known critical untested controls remain.

No coverage percentage is claimed before that point.


## Blocker remediation status
Previously identified G6/G7 product defects are now remediated in code and behavioral tests.

They are not yet removed from the G9 freeze gate until:
- matched BEFORE/AFTER visual evidence is green;
- exact-head frontend tests/build are green;
- G0 is rerun on that final candidate.

No coverage percentage is claimed yet.
