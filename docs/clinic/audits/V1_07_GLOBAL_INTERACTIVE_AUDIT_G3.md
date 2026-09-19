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
