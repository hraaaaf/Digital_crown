# PC-06 — Patient Finance — START HANDOVER

Status: START READY — AUDIT EXISTING FINANCE PRIMITIVES BEFORE IMPLEMENTATION
Branch: feature/patient-companion-pc06-finance
Base: master@09dd2de6f97bd276ebe140137cad51f3d8c1a010
Previous lot: PC-05 merged via PR #643
PC-05 final PR HEAD: 1c8177c1f746857c726d8ffb82d0e645541cf553
PC-05 merge commit: 09dd2de6f97bd276ebe140137cad51f3d8c1a010
Deployment: none

## Canonical scope
Next canonical lot: PC-06 — Finance patient.

Scope visible in the Patient Companion roadmap:
- online payment;
- payment schedules / échéanciers;
- payment history;
- invoice retrieval.

Do not silently expand this scope before auditing the existing finance/accounting architecture.

## Product constraint
PC-06 must expose patient finance from existing cabinet financial truth. It MUST NOT create a second invoice ledger, second payment ledger, second balance engine, or dual-write path.

## Mandatory first audit
Before implementation, inspect and map:
- invoice / note d'honoraires models and routes;
- accounting/dashboard reconciliation logic;
- patient financial history;
- payment records and statuses;
- document/archive linkage;
- any existing installment-plan primitive;
- any existing online-payment provider integration or absence thereof;
- deletion/edit propagation rules for financial documents;
- tenant and patient ownership constraints;
- existing audit trail and immutable evidence requirements.

## Safety / truth rules
- displayed balance must come from authoritative cabinet financial state;
- never claim paid/settled/refunded without durable authoritative evidence;
- remote/online payment result must remain pending until authoritative provider/cabinet confirmation;
- no optimistic paid state;
- finance data must remain tenant + patient scoped;
- no financial amount or patient identity in generic OS notification payloads;
- patient-facing downloads must reuse canonical document permissions and revocation semantics.

## Required Goal / Success / Proof before implementation
Goal:
Expose finance data and actions to Patient Companion without duplicating financial truth.

Success must be made observable after the primitive audit and must cover at minimum:
- correct patient/tenant isolation;
- exact reconciliation with cabinet-side finance truth;
- idempotent payment mutation path if online payment exists;
- accurate pending/paid/refunded state semantics;
- invoice retrieval from canonical records;
- edit/delete propagation proven;
- mobile UI responsive and accessible;
- no optimistic financial acceptance.

Proof must include:
- backend contract tests;
- finance reconciliation tests;
- permission/isolation tests;
- payment idempotency tests when applicable;
- frontend truth-boundary tests;
- BEFORE / target / AFTER visual evidence on 360x800 and 390x844 Chromium + WebKit;
- exact-head CI;
- double check + adversarial triple check;
- human visual approval before closeout/merge.

## Anti-duplication
Do not add:
- generic patient finance table mirroring invoices;
- duplicate invoice totals;
- duplicate payment status truth;
- duplicate accounting dashboard calculations;
- second payment transport when an existing primitive is suitable;
- simulated delivered/paid/settled states.

## PC-05 inherited doctrine
- zero LLM runtime;
- remote Patient Companion mutations require durable authoritative ACK;
- fail closed on revoked access;
- no Vercel deployment without explicit authorization;
- PC-FINAL remains mandatory after PC-10.

## Next exact
1. inspect existing finance/accounting/document/payment primitives;
2. write the architecture map and contradictions/gaps;
3. lock exact PC-06 Goal / Success / Proof in PC_06_START.md;
4. only then implement the minimal projection/action layer;
5. certify exact-head and visual evidence;
6. double/triple check;
7. human visual gate;
8. closeout / merge / post-merge / PC-07.
