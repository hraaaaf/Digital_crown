# PC-07 — Emergency Photo — START

Status: AUDIT REQUIRED BEFORE CODE
Branch: feature/patient-companion-pc07-emergency-photo
Base: master@b4e40fa1f3a63d4d7bf4d91223fa376902dcd7a2

## Canonical source
`PATIENT_COMPANION_CANONICAL.md` defines PC-07 as **Emergency Photo**.

## Initial Goal
Define and then implement the smallest safe Patient Companion emergency-photo flow that reuses existing Digital Crown media and remote-transport primitives instead of creating a parallel media/data plane.

## Initial Success criteria
These remain provisional until the primitive audit is complete:
- patient and tenant ownership cannot be bypassed;
- image acceptance is explicit and validated;
- no public media exposure;
- no false `sent/received` state before durable cabinet ACK;
- failed/offline transmission remains recoverable without data loss;
- no LLM/image interpretation;
- mobile capture/upload is usable at 360px width;
- exact-head automated and visual certification exists.

## Initial Proof plan
- architecture map;
- backend + transport tests;
- permission/isolation tests;
- media validation tests;
- frontend state tests;
- Chromium/WebKit visual evidence;
- adversarial review;
- human visual approval.

## Gate
Do not implement until the audit identifies the canonical media/storage route and proves whether the existing remote transport can carry or reference media safely.
