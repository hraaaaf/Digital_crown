# PC-01 — Local Patient Wallet Sync — START

Status: STARTED IN PARALLEL WITH PC-00 CI

Base candidate: PC-00 @ 0495ebba61d7b0089159e064d2951942b9951f6f
Dependency rule:
- implementation may proceed on top of the PC-00 candidate;
- PC-01 must not merge before PC-00 is merged/certified;
- any PC-00 corrective commit must be reconciled before PC-01 certification.

## Goal
Synchronize only explicitly shared patient resources from the on-prem cabinet into the encrypted Patient Companion vault, expose freshness, and keep the wallet readable offline.

## Success
1. Patient Companion loads the active authorized context from the local encrypted vault.
2. When cabinet is reachable, it fetches only server-authorized appointments/shares.
3. Synced wallet payload is persisted only inside the encrypted vault.
4. Offline reopen renders the last encrypted snapshot with an explicit last-sync timestamp/stale state.
5. Revoked/deleted resources stop future synchronization; UI never claims remote revocation erased a prior patient-held offline copy.
6. Device session expiry/renewal behavior is explicit; no “connected forever” claim.
7. No WhatsApp clinical transport. WhatsApp remains future optional notification/deep-link only.
8. BEFORE/AFTER evidence at 360×800 and 390×844 plus tests.

## Scope
- wallet cache schema per access_id;
- sync/freshness service;
- appointments;
- staff-shared documents/media metadata and authorized retrieval contract;
- explicit Sync button/state;
- offline rendering;
- expired-session handling / re-pairing path;
- tests + visual evidence.

## Non-scope
- remote appointment booking/modification/cancellation (PC-02);
- questionnaires;
- remote signature;
- notifications;
- payment;
- patient upload;
- secure chat;
- teleconsultation;
- WhatsApp as data plane.

## Security invariants
- cabinet remains source of truth;
- no Firebase/SaaS plaintext clinical payload;
- no localStorage/sessionStorage patient payload;
- no numeric patient id in public route;
- bearer token remains inside encrypted Patient Companion vault;
- no silent background Internet exposure of the cabinet;
- no Vercel deployment.

## First implementation sequence
1. inspect existing patient appointment/share endpoints and response shapes;
2. define versioned encrypted wallet snapshot;
3. implement sync with server-authoritative filtering;
4. render offline wallet/freshness;
5. add expiry/re-pair UX;
6. tests;
7. BEFORE/AFTER certification;
8. adversarial review;
9. reconcile PC-00 final HEAD;
10. PR/certification only after dependency is clean.
