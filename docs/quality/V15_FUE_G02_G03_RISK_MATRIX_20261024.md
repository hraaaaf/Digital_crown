# V1.5 — FUE-G02 / FUE-G03 risk-driven executable campaign

**Status:** CANDIDATE / NOT CERTIFIED. The CI verdict and screenshots must be read on the exact PR HEAD. A test listed in this plan is not a PASS.

**Source baseline:** `master@3ab9885a19c835016c85b16153d3f2b8e3318fe3` (2026-10-24). Owner request: exercise all meaningful first-user situations for V1.5-02 Patient Identity/Photo and V1.5-03 Station Foundation. Relevant canonical Notion: [FUE plan](https://app.notion.com/p/3f177c66336281c49a48d1361307f458), [V1.5 roadmap](https://app.notion.com/p/3e677c66336281d88c82d2fbe43835fb), [campaign PRE/POST](https://app.notion.com/p/40377c66336281559289d33977d9775b).

## Safety and execution contract

- **No production patient, cabinet, live tenant, irreversible migration, device mutation, external service or remote patient-data copy.** T2 disposable SQLite runtime and synthetic patient only.
- Fail closed if `ENVIRONMENT != test` or `DIGITALCROWN_ISOLATED_RUNTIME != 1` in the integrated photo harness. Required `EVALUATED_SHA` from CI.
- Test UI/API/database evidence on the same commit. Do not infer genuine end-to-end station confirmation from a Playwright page with mocked `page.route` or `Base.metadata.create_all` fixture.
- **Gates:** FUE-0 for pure contract; FUE-I for executable bounded journey; FUE-G only where real browser + real API + permission + persisted effect are demonstrably connected. RPG-C/J/F as appropriate. RPG-P (camera/NFC/physical station/Windows LAN) is **LOT10**, always OPEN here.
- Required proof: workflow URL, job logs, exact SHA, test collected/executed/skipped counts, artifact list/size, screenshot and evidence.json, negative HTTP codes, database outcome, cleanup and residual gaps. Workflow SUCCESS cannot silently turn an unexercised scenario into PASS.
- No merge, Vercel, deployment or cabinet activation from this PR.

## FUE-G02 — patient photo, identity and lifecycle

| ID | Actor / situation | Observable oracle | Execution surface | Evidence level |
| --- | --- | --- | --- | --- |
| 02-01 | New logged-out browser, recognized workstation | Login UI required; proper cookie/session established only after auth | `certify-v15-02-photo-fresh-login.mjs` | FUE-G synthetic T2 |
| 02-02 | Patient with no photo | Initials fallback on relevant surfaces; no stale picture | `capture-v15-02-3-photo-ui-after.mjs` | Browser + T2 |
| 02-03 | Upload image / crop / confirm | Persisted private image visible from correct patient only | Photo UI + `test_patient_profile_photo_v15.py` | Browser + API |
| 02-04 | Replace photo | New content at stable authorized URL; old image not displayed | Lifecycle capture + backend | Browser + API |
| 02-05 | Delete photo | Binding cleared; secure 404 where applicable; initials restored | Lifecycle capture + backend | Browser + API |
| 02-06 | Five surfaces: Patients, Search, Agenda, Waiting room, Patient details | Same effective photo/fallback, no wrong patient | Photo lifecycle 4 phases × 5 surfaces × 390/1280 | FUE-I/G target |
| 02-07 | Desktop/mobile viewport | No overflow, hidden badges, obstructed search/actions | Lifecycle + dashboard search geometry | Browser |
| 02-08 | New browser without inherited token | No authenticated content prior to login | Fresh-login script | Browser + API |
| 02-09 | Refused upload, then retry | Dialog remains open; eventual success, no false acknowledgement | `certify-v15-02-patient-photo-actions.mjs` | Browser; simulated failure explicitly |
| 02-10 | Rapid double submit | Exactly one upload request while busy | Patient-photo actions script | Browser; request interception |
| 02-11 | Delete request while UI active | Single delete request, no stale confirmed photo | Patient-photo actions script | Browser; request interception |
| 02-12 | Wrong tenant / other patient | Upload/GET denied, zero cross-tenant leakage | `test_patient_profile_photo_v15.py` | HTTP TestClient |
| 02-13 | Bad/unsupported image and direct external URL mutation | Reject invalid content/attempt to forge photo URL | Backend photo contract | HTTP TestClient |
| 02-14 | Profile photo vs clinical timeline | Profile picture must not silently enter clinical media | Backend photo contract | HTTP TestClient |
| 02-15 | Authorized paired Pocket identity | Only paired/authorized flow can see patient photo | Backend photo contract | HTTP TestClient |
| 02-16 | Camera permission denied, disconnected camera, oversized/corrupted payload | Clear user feedback; no partial persistence | **GAP**: scenario-specific browser+API and physical camera tests not all present | OPEN |
| 02-17 | Revocation during upload, old responses after patient switch, browser close | No mutation or stale image in another patient workspace | **GAP**: dedicated E2E race/revocation assertions required | OPEN |
| 02-18 | 430/768 and native 200% text scaling, keyboard crop and screen reader | Critical controls usable and visible | **GAP**: targeted add-on screenshots/accessibility gate | OPEN |

## FUE-G03 — Station Foundation, six families

| ID | Actor / situation | Observable oracle | Execution surface | Evidence level |
| --- | --- | --- | --- | --- |
| 03-01 | First kiosk visit, FR/EN/AR RTL, timeout/return | Correct language/RTL, no clinical escape, session reset | 03.1 shell Chromium + React tests | FUE-I UI fixture |
| 03-02 | Small/large touchscreen and 200% text | No horizontal overflow, adequate targets/readability | 03.1 + 03.6 Chromium | FUE-I UI fixture |
| 03-03 | Admin: new Station, pair, name, revoke | Scoped identity, sensible errors, revoked reuse denied | 03.2 migration/security and identity visual | FUE-0/ I |
| 03-04 | Kiosk cannot escape to staff/clinical access | Fail closed | Kiosk unit + browser fixture | FUE-I UI fixture |
| 03-05 | QR/short session TTL, expiry, one-shot claim and purge | Expired/replayed claim refused; patient pointers purged | `test_station_patient_session_v15.py` | HTTP TestClient |
| 03-06 | Wrong tenant, other patient's token/session | Generic denial; no identity disclosed | Station backend tests | HTTP TestClient |
| 03-07 | Fallback identifiers collision, wrong PIN, five attempts | Generic errors, lockout survives regeneration | Station backend tests | HTTP TestClient |
| 03-08 | Fallback disabled/config invalid/name normalization | Explicit deny, no unsafe implicit identity | Station backend tests | HTTP TestClient |
| 03-09 | Patient identity UI from fresh kiosk | Explicit confirmation and reset | 03.3 patient session Chromium | FUE-I UI fixture |
| 03-10 | 0 appointment today | No appointment invented; staff assistance state durable/idempotent | Backend + 03.4 arrival React tests | API + unit |
| 03-11 | Exactly 1 appointment | Explicit confirmation and correct ARRIVED | Backend + 03.4 arrival React tests | API + unit |
| 03-12 | Multiple appointments | Must choose; cannot silently select incorrect visit | Backend + 03.4 arrival React tests | API + unit |
| 03-13 | Appointment other date/patient, deleted/ineligible status | Refused; no cross-patient or phantom status mutation | Station backend tests | HTTP TestClient |
| 03-14 | Repeated arrival request | Idempotence; no double ticket/transition | Station backend tests | HTTP TestClient |
| 03-15 | Offline on arrival/session; API unavailable | Honest unavailable state, no fake check-in | 03.4 React + 03.6 browser | Unit + UI fixture |
| 03-16 | Reception staff calls waiting patient | Correct bounded call state; permission enforced | Wall backend + React tests | HTTP TestClient + unit |
| 03-17 | Public Wall: initials/full name/number-only | Exactly configured public identity, no medical/private data | 03.5 wall Chromium | FUE-I UI fixture |
| 03-18 | Late/old wall response, unreachable network | Stale response ignored; unavailable is not empty queue | 03.5 wall React tests | Unit |
| 03-19 | Staff assistance when no RDV, duplicate request | Staff-visible and tenant-scoped, repeat-safe | Station backend tests | HTTP TestClient |
| 03-20 | Presence receipt / clinical evidence claim | Station arrival alone cannot forge staff presence | Station backend tests | HTTP TestClient |
| 03-21 | True station fresh login → QR → backend staff confirmation → real wall render, restart/revoke | Persisted state and screen linked across authenticated devices | **GAP**: integrated FUE-G03 with real browser→API→DB→wall not yet implemented in this aggregate | OPEN |
| 03-22 | Physical QR scanner, NFC, kiosk locking hardware, network/standby/screens/printer | Witness real device and power failures | **LOT10** | PHYSICAL NOT_RUN |

## Runner

The matching PR workflow `.github/workflows/v15-fue-g02-g03-risk-matrix.yml` executes:
1. **02:** real T2 backend + genuine Chromium login, photo lifecycle/propagation, edit retry/single-flight, API negative tests, 390/1280 viewport captures.
2. **03 API:** migration and station/session HTTP regressions on disposable fixtures (no claim of a full browser-backed station FUE).
3. **03 UI:** targeted unit suites, build and 03.1 / 03.2 / 03.3 / 03.5 / 03.6 Chromium visual fixture journeys. Each screenshot must retain the `fixture` qualifier.

**Explicitly missing:** hardware LOT10; full station cross-device RPG-J/X; additional 02 revocation/upload races/camera errors; 200%-native and keyboard proof beyond existing scripts; clinician/user observed acceptance; independent read-back of actual CI artifacts.

## Stop and closeout

A **RED**, a required test skipped or an absent screenshot keeps the relevant case OPEN. Read the run's steps and evidence before claiming SUCCESS. Preserve all findings, then fix only observed in-scope defects on a new HEAD, rerun affected controls and obtain required human review. **No automatic V1.5-02/03 global closure or merge.**
