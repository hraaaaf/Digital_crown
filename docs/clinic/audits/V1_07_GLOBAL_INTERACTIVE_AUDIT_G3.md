# Digital Crown V1-07 — Global Interactive Audit — G3

Status: IN PROGRESS

## Goal
Certify Agenda, frontdesk, waiting-room and notification interactions exposed by G0, independently of pending G2 CI.

## Success
- agenda navigation/view switching is behaviorally proved;
- appointment create/edit/refusal paths are proved;
- pending/frontdesk request actions are proved;
- import path is proved;
- waiting-room status transitions are proved;
- notifications read/snooze/navigation/error states are proved;
- exact-head frontend tests + build are green before G3 certification.

## Verified G3 surfaces

### Agenda shell
- `frontend/src/pages/AgendaPage.tsx`
- `frontend/src/features/agenda/AgendaStudio.tsx`

Controls found:
- previous/next/today date navigation;
- Day / Week / Month / Multi switching;
- Frontdesk request modal;
- Google Agenda import modal;
- pending-request filter;
- holiday blocking;
- practitioner-scoped appointment requests;
- multi-practitioner fetch and PREMIUM refusal state.

### Appointment mutation
- `frontend/src/features/agenda/AgendaModal.tsx`
- create/edit appointment boundaries;
- conflict checks;
- save/refusal behavior;
- practitioner context preservation.

### Frontdesk / pending
- `frontend/src/features/agenda/FrontdeskModal.tsx`
- `frontend/src/features/agenda/PendingRequestCard.tsx`
- pending request create/accept/reject/reschedule-related controls as exposed by implementation.

### Import
- `frontend/src/features/agenda/GoogleImportModal.tsx`
- file select;
- event select/all;
- confirm import;
- error/refusal;
- close/cancel.

### Mobile
- `frontend/src/features/mobile/Dashboard/views/AgendaView.tsx`
- `frontend/src/features/mobile/Dashboard/views/FrontdeskView.tsx`
- `frontend/src/features/mobile/Dashboard/views/NotificationsView.tsx`
- `frontend/src/features/mobile/Dashboard/views/WaitingRoomView.tsx`

### Existing reusable evidence
Existing tests include:
- `FrontdeskModal.test.tsx`
- `PendingRequestCard.test.tsx`
- `FrontdeskView.test.tsx`
- `NotificationsView.test.tsx`
- waiting-room mobile tests
- agenda truth/schedule/availability tests elsewhere in the repo.

Reuse is allowed only when the existing test proves the same business result; render presence alone is insufficient.

## G3 certification gate
Do not certify until:
1. critical missing behavioral matrices are added;
2. exact-head frontend test suite passes;
3. exact-head frontend build passes;
4. evidence is recorded here and in Notion.


## Behavioral proof added

1. `frontend/src/features/agenda/AgendaStudio.g3Interactive.test.tsx`
   - day/week/month/multi switching;
   - multi-practitioner fetch;
   - Frontdesk and Google import modal open/close;
   - pending request section/filter;
   - holiday blocking after backend ACK;
   - patient-prefill appointment modal.

2. `frontend/src/features/agenda/AgendaModal.g3Interactive.test.tsx`
   - create/update/delete appointment mutations;
   - scheduling type and status payload;
   - backend refusal without false success;
   - explicit delete confirmation.

3. `frontend/src/features/agenda/FrontdeskModal.g3Interactive.test.tsx`
   - exact pending-request payload;
   - backend refusal;
   - cancel non-mutation.

4. `frontend/src/features/agenda/PendingRequestCard.g3Interactive.test.tsx`
   - request-confirmation / confirm / reject after ACK;
   - reject cancel;
   - refusal preserves pending state.

5. `frontend/src/features/mobile/Dashboard/views/FrontdeskView.g3Interactive.test.tsx`
   - load/refresh;
   - confirm/reject/request-confirmation;
   - explicit reject dialog;
   - backend refusal preservation.

6. `frontend/src/features/mobile/Dashboard/views/NotificationsView.g3Interactive.test.tsx`
   - load/refresh/filter;
   - finance/patient navigation;
   - read/snooze after ACK;
   - mutation refusal preservation;
   - load error vs truthful empty.

7. `frontend/src/features/agenda/GoogleImportModal.g3Interactive.test.tsx`
   - ICS parse;
   - selection controls;
   - exact bulk payload;
   - invalid file;
   - backend refusal;
   - cancel/change-file non-mutation.

8. `backend/tests/test_mobile_waiting_room.py` extended
   - EN_ATTENTE ↔ EN_SALLE_ATTENTE;
   - EN_COURS ↔ EN_FAUTEUIL.

9. `frontend/src/features/mobile/Dashboard/views/AgendaView.g3Interactive.test.tsx`
   - day/week/month controls;
   - date selection;
   - add appointment modal;
   - delegated status/WhatsApp/delete/signature actions;
   - loading/error/true-empty states.

Status remains IN PROGRESS pending exact-head test/build proof and any remaining AgendaModal secondary-control reconciliation.


10. `frontend/src/features/agenda/AgendaModalSecondary.g3Interactive.test.tsx`
    - patient search/select/create/edit;
    - WhatsApp reminder action;
    - quick-add missing act after backend ACK;
    - on-demand suggestions;
    - overlap/conflict display.

G3 independent functional matrices are now substantially reconciled. Exact-head CI/test/build remains the certification gate.


11. `frontend/src/features/mobile/Dashboard/views/WaitingRoomView.g3Interactive.test.tsx`
    - waiting-only filtering;
    - chronological order;
    - truthful waiting count;
    - Au fauteuil → EN_COURS delegation;
    - truthful empty state.

G3 functional matrices are now consolidated. Certification remains blocked only by exact-head tests/build and any failures they reveal.


## Browser escalation
G3 requires a real Chromium action pass in addition to component matrices: Agenda navigation/views, appointment create/edit/delete, Frontdesk, import, notifications and waiting-room actions must be exercised with observable ACK/refusal/non-mutation outcomes. Runtime-discovered dynamic controls join the denominator.


## Deep interaction reconciliation — 2026-09-23

### View switching
The browser action gate now proves the actual rendered consumer after each control:
- Jour -> `agenda-day-view`;
- Semaine -> `agenda-week-view`;
- Mois -> `agenda-month-view`;
- Multi -> visible `Vue multi-praticien`.

The view switch is no longer accepted from the click alone.

### Pending-only product defect
The visible `Afficher seulement` control previously mutated only its own label:
- `showPendingOnly` existed;
- no render/data branch consumed it;
- the active Agenda view remained present.

This was a real ghost-control defect.

Remediation:
- while pending-only is active, `agenda-active-view` is not rendered;
- pending request cards remain visible;
- `Afficher tout` restores the previously active Agenda view;
- component and Chromium proofs require hide + restore behavior.

### Matched visual evidence
Because the correction changes the visible page after an interaction, G3 carries a matched BEFORE/AFTER visual gate:
- true BEFORE source: `AgendaStudio.tsx` from `aef6a80afbdfcb5045fb681aae329a1fbe7793fc`;
- AFTER source: exact workflow checkout HEAD;
- same action: click `Afficher seulement` with one deterministic pending request;
- viewports: 360×800, 390×844, 768×1024, 1280×900;
- capture script: `frontend/scripts/capture-v1-07-g3-pending-only-visual.mjs`;
- artifact: `g3-pending-only-visual`.

The visual change is not certified until the artifact is produced, inspected, compared and scored.

## Remaining semantic depth gaps
G3 remains semantically open until applicable control contracts are closed, notably:
- appointment create/edit/delete real success ACK paths in Chromium where not already covered by reusable exact behavior proof;
- Google import successful import path;
- Notifications and Waiting Room real-Chromium action pass, not component matrices alone;
- any runtime-discovered dynamic control not yet reconciled.
