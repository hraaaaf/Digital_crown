# V1.5-04.5 — Field Gate: two-device document handoff (OPEN)

**State:** HUMAN/PHYSICAL CERTIFICATION NOT PERFORMED. This checklist is not evidence of an executed field run. The device connector reported offline on 2026-10-12; no cabinet machine or physical phone was operated.

## Actors and constraints
- **Cabinet producer:** authenticated practitioner workstation, canonical on-premise database.
- **Station:** separate enrolled/locked shared workstation on the cabinet LAN, with its own registered workstation cookie.
- **Patient phone:** real paired Patient Companion, distinct physical device, patient-owned; same trusted HTTPS cabinet address; fictitious patient fixture only.
- **Immutable PDF:** care sheet produced/finalized with trusted audit event, explicitly authorized for withdrawal by its practitioner. Record only SHA-256 and document ID in secured evidence, never real patient identity or bearer tokens.
- **Traffic:** TLS is valid and trusted by the phone; no security-warning click-through or `verify=False`. Workstation Station and Companion must never share credentials.

## Procedure (witness must capture results, not merely check boxes)
1. Verify exactly the final candidate HEAD, the cabinet build identity, and connected device/time. Confirm the fixture database is isolated and never a real patient record. Check Station Downloads directory initially empty of the test PDF.
2. On Cabinet workstation, finalize and explicitly authorize the fictitious PDF. Record expected SHA-256 on the Cabinet, without copying bearer tokens into screenshots or logs.
3. On Station (second workstation), open Documents. Verify no browser download control and no clinical PDF response. Start an opaque QR/NFC identity session. Save visible BEFORE capture and backend refusal evidence for direct Station PDF GET (**423**).
4. On the paired Patient Companion **phone**, scan QR; assert the URL is HTTPS and the token is not exposed after entry. Claim identity once using the exact patient context. Reuse the same QR; the replay must fail.
5. On the Station, check only the human-readable availability signal (not the PDF). On the phone, confirm the authorized care sheet appears. Tap **Télécharger ma feuille de soins**. Confirm the PDF opens and renders on the phone, compare its SHA-256 to the Cabinet producer.
6. Assert no PDF file or browser Blob download occurred on Station. Observe Station Downloads, browser devtools Network and any local print-spool staging (if printer policy is enabled; it is NOT enabled in this candidate).
7. Attempt the same delivery with patient B's Companion token, wrong Station cookie, revoked Companion access, expired Station session, and no staff authorization. All must deny, without preview or file bytes.
8. Purge via Station exit or TTL and retry the phone URL: must deny without PDF bytes. Repeat with WAN/LAN unplugged before receipt; errors must be intelligible and fail closed. Restore network: do not silently revive expired access.
9. On both devices, verify the visual layouts FR/EN/AR at mobile 390/430 and Station 768/1280 if applicable; compare baseline and AFTER screenshots at the same viewport, check no horizontal overflow and no accidental appointment-arrival action. Record a visible witness decision.
10. Apply `visual-approved-by-achraf` to PR #844 **only after** the owner explicitly approves AFTER screenshots from the exact HEAD. Any additional commit invalidates approval.

## Evidence contract
Run identifier, candidate HEAD, CI run + artifacts, witness, two distinct physical device identifiers (non-sensitive), actual LAN/HTTPS origin, observed TLS version, actual producer+consumer SHA-256, document page render count, denial statuses, purge demonstration, offline recovery, before/after filenames and screenshot dimensions, physical NFC result (if available), real printer result (if selected), privacy inspection of Station Downloads and print cache.

## Pass/fail
- **Pass:** all mandatory observed steps, including no PDF on the Station and actual phone receipt with matching hash, independent devices and trusted TLS; human approval on exact SHA.
- **Fail/OPEN:** simulated screenshots or one-runner TLS only, missing physical device, mismatched hash, local kiosk PDF, failed denial, missing witness, missing printer/NFC verification when those modalities are claimed.
- **No merge or production activation** on an OPEN required field gate. A standalone printer integration is intentionally not introduced in 04.5 without a locally configured secure print/spool deletion contract.

## GitHub proof
The workflow `.github/workflows/v15-04-4-station-document-qr-nfc.yml` supplies isolated network and screenshot rehearsals. Its green status does **not** certify the physical checklist above.
