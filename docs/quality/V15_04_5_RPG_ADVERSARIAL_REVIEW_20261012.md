# V1.5-04.5 — Reality Proof + adversarial reviews (2026-10-12)

**State:** OPEN. Internal adversarial perspectives A/B; they are **not external independent reviewers**. Neither review authorizes merge, deployment or human visual approval.

## Observable goal and proof categories

Cabinet workstation authorizes an immutable, finalized fictitious patient-A PDF. A separately enrolled Station workstation creates an opaque QR/NFC session; a separate companion authenticates and claims it once. Station discovers only authorized patient-A documents and retrieves the same PDF bytes through verified TLS, renders one PDF page, then purges. A different patient's document, a different workstation, a raw QR token without station authentication, replay and post-purge retrieval must all fail closed. All CI fixtures must remain isolated from real cabinet data.

- **RPG-C:** existing FastAPI backend cases + frontend tests (authorization/denials).
- **RPG-J:** Station Playwright UI with synthetic backend and browser download; the PDF-rendering evidence is from a real TLS client using PyMuPDF, **not yet a browser receiving from the same real endpoint**.
- **RPG-X:** new `backend/tests/test_station_https_cross_process_v15.py`: Uvicorn HTTPS endpoint, independently enrolled Cabinet and Station workstation cookies, independent client OS processes, companion claim, SHA-256 comparison, PDF page rendering, purge. TLS cert is ephemeral and deliberately trusted by clients. Entire rehearsal runs on one CI machine via localhost TLS; **not two physical LAN devices** and **not two distinct GitHub jobs**.
- **RPG-F:** prior expired/revoked tests plus additional not-identified, replay, other-patient, wrong-workstation, bearer-only and purge checks.
- **RPG-P:** OPEN pending real patient-privacy-approved demonstration and human review; no real printer, Pocket or NFC hardware proof.

## Review A — access, safety and privacy (internal adversarial perspective)

| Finding | Severity when found | Disposition |
| --- | --- | --- |
| Earlier cross-process rehearsal used the same workstation cookie for sender and station, defeating the independent-device-identity goal | BLOCKER | FIXED: independent `/enroll` produces different workstation IDs and opaque cookies; wrong-workstation PDF/document list denial added |
| Identified Station screen kept patient name on display until user left even after token expiry | MAJOR | FIXED: client-side timer clears name, document controls and starts bounded purge at server-specified expiry; regression added |
| Access to another patient's document and to a PDF using only QR bearer token | BLOCKER if accepted | DENIAL assertions in the real HTTPS process journey and existing backend tests |
| Replay of patient QR and post-purge download | MAJOR if accepted | DENIAL assertions across separate OS processes and existing regressions |
| True physical NFC/print/Pocket device and two-machine LAN session not exercised | OPEN proof gate | Must remain explicitly unapproved; lab evidence must not be described as physical certification |

**Verdict A:** security-focused remediation implemented; exact-HEAD CI evidence required before recording clean review. Score provisionally **7.5/10**, not a release certificate.

## Review B — determinism, evidence and UI regressions (internal adversarial perspective)

| Finding | Severity when found | Disposition |
| --- | --- | --- |
| Earlier UI tests expected old "under construction" copy / lacked discovery mock | MAJOR | FIXED: UI mocks, positive and negative download tests; prior backend workflow green on earlier SHA |
| Earlier Playwright capture still waited for obsolete 04.4 copy | MAJOR | FIXED: Station discovery assertion, no pre-identification requests, and one mobile PDF download |
| Green single TestClient proof falsely presented as an inter-device HTTPS transfer | BLOCKER | NEW separate OS processes using actual TCP/TLS backend, distinct workstation identities, SHA and PDF rendering; candidate until CI proves it |
| An unattended kiosk retained name / document selection after expiry | MAJOR | FIXED: timed client cleanup + Vitest regression |
| No exact-HEAD green `RPG-X` proof or current human AFTER approval yet | OPEN proof gate | Run targeted CI on immutable final HEAD and deliver evidence link for explicit human approval |

**Verdict B:** test fidelity improved; exact-HEAD validation and visuals remain outstanding. Score provisionally **7.0/10**.

## Mandatory remaining gates

1. Record executable results from the new HEAD: *actual* backend cases, HTTPS subprocess evidence file, 48 synthetic Station screenshots, and build/test status; a collected but failed test is NOT PROVEN.
2. Inspect uploaded JSON evidence for independent workstation IDs, process IDs, TLS, PDF SHA-256, successful render, denial assertions and purge. No patient secrets may be copied to the artifact.
3. Compare BEFORE/AFTER same viewports; provide artifact link to human approver. Re-apply `visual-approved-by-achraf` only after explicit approval by the user on the final HEAD; any subsequent commit invalidates it.
4. For real 04.5 closeout, retain separate **physical two-PC/LAN/NFC/printer/Pocket** work as OPEN if not actually certified. Do not merge this draft candidate automatically.

**Proof discipline:** The two written perspectives were composed within the same assistant session. They must be named *internal adversarial reviews* rather than real external independent reviews. Final `CONVERGED` requires two clean exact-HEAD reviews **after** CI, with no meaningful defect left.
