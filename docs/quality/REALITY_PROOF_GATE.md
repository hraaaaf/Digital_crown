# Digital Crown — Reality Proof Gate (RPG) v0.1

## Objective
Prove the *observable outcome* of each V1.5 lot/sub-lot, not just the presence of tests or a green CI. This extends (never replaces) FUE-0 / FUE-I / FUE-G, adversarial reviews, and human/physical approval.

## Applicability by risk
- **RPG-C (contract)**: every sub-lot. Executed assertions, explicit collection/execution counts, negative permissions, deterministic fictitious fixtures.
- **RPG-J (journey)**: every user-visible or cross-service flow. Actual backend + frontend where relevant, fresh profile and isolated environment, evidence of outcome (not HTTP 200 alone).
- **RPG-X (cross-device)**: any producer/consumer, sync, migration, document transfer or networked workflow. Independent authenticated actors/processes; distinct jobs/runs when shared immutable artifact handoff is feasible. TLS and actual receipt/display where specified. Do not call a shared FastAPI TestClient a two-machine simulation.
- **RPG-F (fault/privacy)**: patient data, persistence, access, offline, migrations and destructive operations. Wrong tenant/patient, expiry, replay, revocation, concurrent sessions, restart, offline, purge; fail-closed.
- **RPG-P (physical/human)**: hardware-dependent proof (NFC, printers, physical LAN, camera, scanner) cannot be certified by synthetic CI. Mark OPEN until witnessed on actual devices.

## Evidence contract (per lot and sub-lot)
Record: lot ID, requirement, risk, **FUE-A/FUE-B outcomes and evidence (or FUE-0 N/A)**, actors, isolated fixtures, producer and consumer, exact SHA, CI run/job URLs, executed test counts, skipped tests and reasons, transport/TLS details, expected vs observed outcome, SHA-256 for files, screenshots/traces for UI, denial matrix, cleanup/purge, **one transversal adversarial review report**, physical/human limitations and next action. Missing mandatory evidence = OPEN, not GREEN/CLOSED. Tests only collected but not executed = NOT PROVEN.

## Two executed FUE journeys + ONE transversal adversarial review
- **FUE-A = first useful outcome as a task-relevant new user**, testing workflow clarity, navigation, accessibility, positive result and recovery. **FUE-B = a complementary user/role and risk**, testing refusal, RBAC, wrong patient/tenant, persistence and fault behavior where applicable. ChatGPT orchestrates both from this conversation; neither a human reviewer nor a second AI agent is required. These are **two FUE tests, not two reviews**. For FUE-0 (code/contract/API only), test the technical contract; do not fabricate a user-visible browser flow.
- **Real user-journey evidence is mandatory for FUE-I/G**: actual frontend and backend, disposable fictitious test identities/data, **real UI login** (or specified public entry), BEFORE/ACTION/AFTER with a verified persisted business outcome, negative checks, fail/recovery, exact SHA and artifacts. A text-only persona roleplay is **NOT RUN**, not PASS. Limit viewports to the actually supported product surfaces. Report each FUE separately with PASS/FAIL/BLOCKED/NOT_APPLICABLE, evidence and severity.
- **ONE transversal adversarial review AFTER the FUE**: the same conversation challenges BOTH executed FUE and underlying contracts, source/data lineage, privacy/security, missed tests, false-green CI, failures and regressions; issue one combined report and score (not two A/B reviewer scores). Fix scope-safe defects, rerun impacted FUE/tests on the new HEAD, repeat the **single transversal review** and confirm the exact HEAD. Never wait for two independent reviewers.
- **Human approval, scientific/clinical review and RPG-P remain distinct**: real LOT10 people/devices start from login for authenticated workflows; specific scientific, legal or visual human sign-off is required only when its own explicit gate applies. Synthetic FUE + transversal review cannot certify physical devices or clinical correctness.

## Gates
1. Define observable success and failure before implementation.
2. Execute the smallest risk-appropriate RPG-C/J/X/F/P including FUE-A and FUE-B for user-visible flows (FUE-0 technical instead where appropriate), then **one transversal adversarial review** of the evidence on the exact HEAD; fix findings, rerun impacted tests/FUE and the same single review on any new HEAD.
3. Validate immutable producer→consumer artifact and identity binding; never transfer real patient data to CI.
4. Inspect artifacts and run/job steps; compare same viewports BEFORE/AFTER for UI; no skipped required assertion.
5. Close only with exact-HEAD evidence, documented residual risk and human approval when required. GREEN is not CONVERGED, and CONVERGED is not deployed.

## V1.5 mapping (minimum)
00 Hub: RPG-C/J; 01 topology: RPG-C/J/X/F (RPG-P deferred); 02 photo: RPG-C/J/F; 03 Station: RPG-C/J/F (RPG-P deferred); 04 documents: RPG-C/J/X/F (RPG-P deferred); 05 SQL migration: RPG-C/X/F on isolated database copies; 06–09: laboratory gates per canonical lot; **10: RPG-P physical certification** of real multi-PC, camera/NFC, Station/phone LAN/TLS and printing as applicable. **RPG-P OPEN does not automatically block a previous lot's software-only merge, but always blocks PHYSICAL PASS and hardware/clinical activation.**

## Reference: 04.5 sender→receiver
Sender cabinet authorizes fictitious patient A's PDF A; separate receiver Workstation identifies A, receives PDF over HTTPS and renders it; compare SHA-256 to producer. Patient B and revoked/expired station must not access A. Two distinct runs need a secure, immutable artifact handoff and evidence that the receiver fetched from a running HTTPS endpoint, not a copied local file. Until both processes/runs and browser rendering are observed, mark RPG-X/J OPEN.
