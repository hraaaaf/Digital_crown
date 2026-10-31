# Digital Crown V1.5 — LOT06 C05B-03I · Cabinet Multi-acteurs

STATUS: PREPARATION OFFLINE, NOT PRODUCT CERTIFIED. No merge, deploy, Tailnet, real patients or clinical ACK.

Source of truth: current Digital Crown master at 37feed145a216c56d096ea611d0a2a456cb4ce43; previous C05B-03H real Ubuntu/Tailscale lab passed at 8f99cbd4fc5045c530d73270ae4dbecdb4ac8c24 (run 41143220856, 8/8) but covered ONLY HotFolder transfers.

Topology: local preflight uses 1 isolated SQLite cabinet, 2 simulated patient mobile actor threads, 1 dentist thread, 1 camera thread. Five LOGICAL roles; zero real phones/VMs for this new phase.

Existing actual product services: PC08 patient_companion_messages: message.send/sync, idempotency and scoped thread; PC02 patient_companion_agenda: create/list/slots with lock_cabinet_booking, appointment conflict guard; PC07 patient_emergency_photo: patient-origin chunks to canonical Media Core. An operator requesting photos from a DENTAL DEVICE is a separate missing adapter and MUST NOT be claimed by PC07.

FUE-03I-01: two authenticated mobiles send messages while dentist reads; enforce per-patient and tenant access, no duplicate or fake read receipt. PRODUCT E2E PENDING.
FUE-03I-02: two separate DB sessions book the same practitioner/time: exactly 1 committed, other rejected; never two positive ACKs. PRODUCT MULTI-CONNECTION PENDING.
FUE-03I-03: dentist DB read/write while messages, booking and images execute; no torn writes, report actual p95/locks. PRODUCT LOAD PENDING.
FUE-03I-04: practitioner-issued photo request with opaque ID, linked tenant/patient, device checksum, canonical Media Core persisted, ACK only after commit. MISSING DEVICE ADAPTER; protocol simulation only.
FUE-03I-05: broken network, retry, revoked access, wrong patient, duplicate media, aborted commit fail closed. PRODUCT NEGATIVE E2E PENDING.

LOCAL EXECUTION: ENVIRONMENT=test DIGITALCROWN_ISOLATED_RUNTIME=true C05B03H_NETWORK_POLICY_APPROVED=false python isolated_fue_lot06c/qa_clinic_multi_actor_local_v15.py
LOCAL OUTPUT: C05B03I_LOCAL_SYNTHETIC_CONTRACT_PREFLIGHT_PASS means simulator only; product_ready=false and clinical_ack_issued=false mandatory.
PRODUCT DOMAIN PRECHECK (dependencies required): python -m pytest backend/tests/test_lot06_c05b03i_product_contract.py -q

Next: run domain tests on isolated checkout; connect real FastAPI + DB separate sessions, then camera requested-photo adapter; freeze p95 thresholds before any full network run. No patient traffic through Tailscale. Only after human authorization temporarily flip gate true for five VM FUE, reset false afterwards. Three independent mobile runner VMs plus dentist/device/server means six VMs.
