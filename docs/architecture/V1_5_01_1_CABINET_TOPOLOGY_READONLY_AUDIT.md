# V1.5-01.1 — Cabinet topology & workstation roles — read-only audit

Date: 2026-09-30
Base audited: `master@9406bc0f5399536cc49d0e60509efa964448b005`
Scope: V1.5-01 only. No V1.5-02+ implementation is authorized by this document.

## Goal

Establish the smallest evidence-backed delta required to make cabinet topology, workstation roles, LAN configuration/discovery and installer diagnostics explicit without weakening the V1.5-00 security boundary.

## Success

A requirement-to-code matrix distinguishes existing capability from real gaps, and every proposed implementation is bounded to a proved V1.5-01 gap.

## Proof inspected

- `STATE.md`
- `AGENTS.md`
- `docs/architecture/V1_5_00_1_HUB_DISPATCHER_READONLY_AUDIT.md`
- `docs/architecture/V1_5_00_2_HUB_SHELL_CLOSEOUT.md`
- `docs/architecture/V1_5_00_3_WORKSTATION_MODE_REVIEW.md`
- `docs/architecture/V1_5_00_4_FINAL_INTEGRATION_AUDIT.md`
- `run.py`
- `backend/main.py`
- `backend/routers/workstation_mode.py`
- `backend/routers/mobile.py`
- `backend/routers/mobile_legacy.py`
- `docs/CABINET_ONPREM_GUIDE.md`
- `README.md`

## Requirement → current code → proof → gap → action

| Requirement | Current code / proof | Real gap | V1.5-01 action |
|---|---|---|---|
| PC server role | `run.py::_resolve_runtime_network()` owns backend bind/TLS contract; packaged first boot writes `CABINET_HOST=127.0.0.1`. | No canonical topology role names or installer-readable description of which machine is the server authority. | Add a pure topology contract and installer diagnostics that report role + transport state without exposing secrets. |
| Annex workstation role | `backend/routers/workstation_mode.py` provides opaque workstation identity and UX modes (`cabinet`, `station`, `control_center`). | UX mode is not a physical/network topology role. No explicit annex-workstation contract. | Define topology roles separately from UX modes. Do not overload `WorkstationMode.default_experience`. |
| Reception role | Frontdesk exists as an application surface; workstation mode can lock a station experience. | No topology-level `reception` workstation role or documented relationship to server authority. | Define/document `reception` as a client workstation role, not a new authorization role. |
| Connected devices | Mobile pairing has tenant/device identity and revocation. | Mobile/device pairing is not a general LAN device inventory and must not be silently generalized. | Document connected-device boundary; expose only transport/discovery facts needed by installer. |
| LAN exposure | `run.py` fails closed: cabinet/production non-loopback host requires explicit HTTPS cert/key. | No single reusable resolver describing effective LAN readiness and reasons for refusal. | Extract/introduce a pure diagnostic contract while preserving the fail-closed launcher behavior. |
| LAN discovery | `mobile_legacy.py::_detect_lan_ip()` uses UDP route probing and falls back to loopback; `get_lan_base_url()` currently constructs **HTTP** LAN URLs and reads `PORT`, while launcher reads `CABINET_PORT`. | Split-brain network resolution; legacy mobile URL can disagree with launcher and TLS policy. This is a proved correctness/security gap. | Replace legacy URL construction with the canonical network contract; HTTPS when enabled, canonical cabinet port, no invented reachable LAN URL when not LAN-ready. |
| Installer diagnostics | Health endpoints and runtime logs exist; on-prem guide gives manual curl checks. | No concise topology/network diagnostic payload explaining loopback-only vs LAN-ready, TLS state, effective port and remediation category. | Add a non-secret diagnostic helper/API suitable for installer troubleshooting, with targeted tests. |
| Installation docs | `docs/CABINET_ONPREM_GUIDE.md` contains historical statements about automatic LAN bind / SQLite solo that conflict with current runtime/README. | Documentation can direct an installer toward behavior the runtime intentionally refuses. | Correct only the V1.5-01 topology/network sections and explicitly defer unrelated packaging/database cleanup. |

## Security boundary retained

1. No automatic `0.0.0.0` exposure.
2. No cabinet/production LAN exposure without explicit HTTPS/TLS material.
3. No secret/certificate private-key material in diagnostics.
4. Topology role must not grant application permissions.
5. Workstation UX mode and topology role remain distinct concepts.
6. No network scan of arbitrary hosts is required for V1.5-01; passive/local configuration and explicit endpoint discovery are sufficient.

## Proved implementation delta

1. Canonical pure network/topology resolver shared by launcher and mobile LAN URL generation.
2. Explicit topology role vocabulary: `server`, `workstation`, `reception`, `connected_device` (descriptive only).
3. Installer-readable diagnostics for effective host/port/scheme, LAN readiness, TLS readiness and bounded remediation codes.
4. Targeted backend/unit tests for resolver fail-closed behavior and mobile URL consistency.
5. V1.5-01 installation/topology documentation correction.

Anything beyond these points requires new evidence and is not authorized by this audit.
