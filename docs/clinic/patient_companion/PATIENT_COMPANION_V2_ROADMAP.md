# Patient Companion V2 — Local-First Roadmap

Status: PRODUCT APPROVED — PC-00/PC-01 MERGED — REMOTE TRANSPORT GATE B CODE/TEST CERTIFIED; FINAL DOCS-ONLY EXACT-HEAD CERTIFICATION PENDING

## Doctrine

Patient Companion is not a cloud copy of the cabinet record.

Canonical flow:

**Digital Crown cabinet = clinical source of truth**
→ **one-time QR/manual bridge**
→ **encrypted vault on the patient's phone**

Firebase may remain part of Digital Crown identity/licensing elsewhere, but Patient Companion clinical payloads must not be stored or transported through Firebase by convenience.

## PC-00 — Local Bridge + Encrypted Device Vault

Goal:
- runtime-mounted Patient Companion API;
- one-time QR/manual pairing;
- device-scoped Patient Companion identity;
- encrypted local IndexedDB vault;
- offline shell;
- context switcher;
- revocation stops future synchronization.

No clinical dataset is duplicated yet beyond safe context/session metadata.

## PC-01 — Local Patient Wallet Sync

Goal:
- synchronize explicitly shared appointments, documents and media from cabinet to phone;
- store synced data only inside the encrypted Patient Companion vault;
- show last successful sync and data freshness;
- remain readable offline.

Rules:
- no parallel plaintext cache;
- no numeric patient IDs in public URLs;
- only staff-approved share grants;
- incremental sync;
- deleted/revoked resources stop future sync;
- remote revocation cannot claim to erase a patient-held offline copy.

## Cabinet connection model — decision recorded at PC-00

Two different meanings of “connected” must stay separate:

1. **Paired / trusted device** — the phone keeps its encrypted local Patient Companion vault and device credential. This survives cabinet downtime and app reopen.
2. **Cabinet reachable now** — the phone can currently reach the on-prem Digital Crown API and synchronize. PC-00 exposes an explicit on-demand reachability check; PC-01 will own actual sync/freshness.

Current device credential lifetime is finite (30 days). PC-01 must add a safe renewal/re-pairing policy before claiming persistent long-term connectivity.

### WhatsApp

WhatsApp is **not** the canonical clinical transport between Patient Companion and Digital Crown.

Allowed use:
- optional notification/deep-link channel (“votre cabinet vous a envoyé une mise à jour”, appointment reminder, invitation to open Patient Companion);
- no clinical payload, document, photo, medical questionnaire, payment history or secure chat content in the WhatsApp message itself;
- never the source of truth for appointment state.

Why:
- it introduces a third-party messaging dependency into a product whose clinical source is on-prem;
- it does not solve the authenticated synchronization problem between the patient vault and cabinet;
- it would fragment the audit trail if used as the real two-way clinical channel.

Therefore: **do not implement WhatsApp transport in PC-00 or PC-01.**
Revisit WhatsApp only after the remote transport gate, as an optional notification surface rather than the clinical data plane.

## REMOTE TRANSPORT GATE — before PC-02

PC-02+ introduces actions initiated while the patient may be outside the cabinet LAN.

Decision recorded 2026-09-19: **Option B — end-to-end encrypted opaque relay**. Implementation/certification is tracked in PR #638 and must close before PC-02 merge.

Allowed architectural families to evaluate:
1. **Direct secure cabinet endpoint** — cabinet exposes a hardened, authenticated endpoint over a controlled tunnel/domain.
2. **End-to-end encrypted relay** — cloud relay carries opaque ciphertext/commands only; relay cannot read clinical payloads.

Not allowed:
- exposing SQLite/media shares directly to Internet;
- using Firebase/another SaaS as a plaintext clinical database;
- silently converting Digital Crown into SaaS;
- assuming LAN reachability for remote patient actions.

This is a real architecture/security human gate. PC-00 and PC-01 do not depend on resolving it.

## PC-02 — Self-Service Agenda

After transport gate:
- cabinet-authorized appointment types/slots only;
- create/reschedule/cancel commands;
- idempotent writes;
- conflict checks remain server-authoritative;
- offline phone may queue a request but must never display an unconfirmed appointment as confirmed.

## PC-03 — Medical Questionnaires

- versioned questionnaires;
- local draft in encrypted vault;
- explicit submit;
- cabinet review before clinical merge where appropriate;
- provenance + audit.

## PC-04 — Consent Vault Patient-Facing

- shared consent package;
- remote signature only after legal/evidence requirements are validated;
- version, timestamp, signer context, audit trail;
- signed artifacts synchronized back to cabinet.

## PC-05 — Notifications

- appointment/reminder/action-needed events;
- notification metadata minimized;
- sensitive content stays inside encrypted app context;
- transport must not expose clinical details.

## PC-06 — Patient Finance

- invoices, schedule, payment history synced to wallet;
- online payment via Morocco-compatible PSP;
- card data never stored by Digital Crown;
- webhook/idempotence/reconciliation server-authoritative.

## PC-07 — Emergency Photo

- guided patient capture;
- encrypted local staging;
- explicit upload;
- cabinet review queue;
- provenance;
- never present automated interpretation as diagnosis.

## PC-08 — Secure Messaging

- async cabinet/patient messages;
- encrypted local history;
- attachment allowlist;
- retention;
- clear emergency disclaimer;
- transport architecture from remote gate reused.

## PC-09 — Teleconsultation

- integrate a suitable video provider or secure direct session;
- do not build a video stack from scratch;
- patient/RDV binding;
- no automatic clinical recording.

## PC-10 — Satisfaction / Testimonials

- private feedback by default;
- separate explicit consent before publication;
- no automatic public testimonial.

## Delivery waves

Wave A:
PC-00 → PC-01

Gate:
Remote transport architecture

Wave B:
PC-02 → PC-03 → PC-04 → PC-05

Wave C:
PC-06 → PC-07 → PC-08

Wave D:
PC-09 → PC-10

## Product comparison consequence

Dentapoche-style cloud-connected functions are not copied mechanically. Digital Crown matches patient utility while preserving the on-prem/local-first identity of the product. A feature counts as matched only when the user experience is available without violating this doctrine.
