# PC-08 — Secure Messaging — UI Target

Status: TARGET LOCKED BEFORE PRODUCT UI CODE
Date: 2026-09-22
Branch: `feature/patient-companion-pc08-secure-messaging`
Architecture: `PC_08_SECURE_MESSAGING_ARCHITECTURE_MAP.md`

## Goal

Expose secure asynchronous messaging without making it look like an instant messenger that promises realtime delivery.

Visual priority:
1. truth of state;
2. readable clinical communication;
3. obvious access identity when several Patient Companion accesses exist;
4. compact mobile composition;
5. zero overlap/overflow.

## Patient Companion target

Insertion: Patient Companion home, after the high-priority safety/notification area and before lower-priority wallet content.

### Header
- eyebrow: `MESSAGES SÉCURISÉS`;
- title: `Cabinet`;
- shield/message icon;
- small sync affordance, not a presence/online indicator;
- supporting copy: messages are synchronized securely with the cabinet.

### Thread
- max-width constrained bubbles;
- patient outgoing aligned right;
- cabinet incoming aligned left;
- body rendered as plain text with preserved wrapping;
- compact timestamp below body;
- receipt label only from canonical evidence:
  - `En attente`;
  - `Reçu par le cabinet`;
  - `Lu par le cabinet`;
  - incoming `Reçu sur cet appareil` / `Lu` where applicable;
- offline/pending bubble remains visible and visually distinct;
- no typing indicator;
- no “en ligne” badge;
- no avatar photo required.

### Composer
- multiline text area;
- explicit character/byte-safe boundary feedback;
- primary send button >=44 px;
- disabled only when empty/oversize/busy;
- offline copy says the message remains encrypted on this device until retry;
- no attachment button in PC-08 initial slice.

### Empty state
- neutral shield/message illustration using existing iconography;
- copy explains secure asynchronous contact;
- no promise of emergency response.

### Mobile geometry
Required proof:
- Chromium 360×800;
- Chromium 390×844;
- WebKit 360×800;
- WebKit 390×844.

Acceptance:
- no horizontal overflow;
- composer remains reachable;
- bubbles wrap long unbroken content;
- controls >=44 px;
- sticky behavior must not hide the final message/composer;
- keyboard-safe layout must degrade to normal document flow rather than overlap.

## Staff target

Insertion:
`PatientDetails -> Companion -> PatientCompanionPanel`.

The staff surface remains inside the patient dossier; PC-08 does not create a second global inbox.

### Access selector
When more than one active access exists:
- explicit relationship chip: Patient / Parent / Tuteur / Aidant;
- explicit selector before thread;
- no silent sharing between accesses.

When one active access exists:
- relationship remains visible but selector can collapse to a label.

### Thread card
- title: `Messages sécurisés`;
- chronological canonical thread;
- patient messages left, cabinet replies right;
- sender relationship visible on patient-originated messages;
- message content plain text;
- canonical timestamps;
- staff outbound state:
  - `Envoyé depuis le cabinet` before patient receipt;
  - `Reçu sur l’appareil` after explicit patient receipt;
  - `Lu` after explicit patient read;
- patient outbound state:
  - `Reçu par le cabinet`;
  - `Lu par le cabinet` after staff read mutation.

### Staff composer
- same 4096-byte contract;
- send action >=44 px;
- no attachment;
- no “delivered” wording on successful persistence;
- multiple-click/retry protected by client_message_id.

## Visual direction

Reuse existing Digital Crown surfaces:
- rounded 2xl / 1.75rem cards;
- `border-border-main`, `bg-card-bg`, `bg-background`;
- primary clinical blue for actions;
- emerald only for proven positive state;
- amber for pending/offline;
- rose only for terminal failure/rejection;
- no new color system;
- no chat-app imitation with decorative gradients.

## BEFORE evidence

Must be captured from PR base `master@f96f7abee2fb1994b3ac72ef00603a704961e59b` before product UI code:
- patient home at 360×800 / 390×844 on Chromium + WebKit;
- staff Companion panel at 390×844 / 768×1024 / 1280×900 on Chromium.

The BEFORE must prove no PC-08 secure-message section is present.

## AFTER evidence

Capture the same patient and staff viewports from exact PR HEAD.
The AFTER must additionally prove:
- PC-08 section present;
- no horizontal overflow;
- no runtime/console errors;
- pending and authoritative receipt states use distinct wording;
- multi-access selector visible in fixture with two relationship types;
- long body wraps safely.

## Human gate

Stop before merge with:
- BEFORE;
- target;
- AFTER;
- target↔render comparison;
- severe visual score;
- exact-head test/CI evidence.

No Vercel deployment.
