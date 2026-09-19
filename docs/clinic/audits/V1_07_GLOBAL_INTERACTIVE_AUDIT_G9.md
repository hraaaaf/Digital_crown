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
Most controls are behaviorally covered.
The LicenseStatus product-truth defect is remediated in code and dedicated tests; certification still requires matched exact-head BEFORE/AFTER evidence and exact-head tests/build.

### G7 — Stock/marketplace/library
Marketplace/admin/detail pages, Library and Science Hub are behaviorally mapped.
The three Stock product-truth/safety defects are remediated in code and behavior tests: read-error ≠ empty, explicit delete confirmation, and visible add/edit/quantity/delete refusal states. Certification still requires matched exact-head visual evidence and exact-head tests/build.

### G8 — Transverse/adversarial
Functionally reconciled.
Evidence covers modal accessibility, offline truth, error-vs-empty/refusal/permissions, responsive reachability and representative single-flight mutation controls.
Certification still depends on exact-head tests/build.

## Freeze blockers

G9 cannot freeze while any of these remain:
1. G1/G6/G7 remediations are not yet backed by green matched exact-head visual evidence.
2. Exact-head frontend tests/build are not green for the final reconciled HEAD.
3. G0 final rerun/reconciliation has not been adjudicated semantically.
4. The semantic denominator is not frozen after final source changes.
5. The independent pre-freeze adversarial gate (`V1_07_PREFREEZE_TRIPLE_CHECK.md`) has not been reconciled to the same final candidate; its security/runtime findings are not part of the interactive denominator but remain mandatory before V1-08.

## Evidence reconciliation seed
`scripts/reconcile_interactive_evidence.py` generates a conservative **inspection seed**, never a coverage score or semantic denominator.

A source file leaves the priority inspection queue only when at least one of these is true:
- a gated G1→G8 test imports that exact source path directly (relative or `@/` import);
- a canonical G1→G8 audit file explicitly references that source path.

Filename/token similarity is retained only as a heuristic hint and cannot itself count as proof. Direct import or canonical reference also does not prove that every control in the source file is covered; G9 must still adjudicate control-level behavior before freeze.

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


## Additional G1 remediation
The Landing geography mismatch (“dentistes algériens”) was found during final truth review and remediated to “dentistes marocains”.

It remains part of the G9 freeze gate until the matched BEFORE/AFTER visual scenario and exact-head tests/build are green.
