# Digital Crown V1.5 — LOT 06-B staff acquisition preflight

Status: isolated laboratory only. Existing LOT06-A draft PR #851. No real patient media import is enabled.

## Server contract
The additive POST /api/imaging-acquisitions/preflight is disabled by default and hard-disabled outside isolated TEST runtime. It requires a staff Bearer credential, patient permission, an enrolled same-cabinet workstation, an explicit opaque capture identifier, SHA-256 fingerprint, size, MIME/category and optional Patient/RDV references. The server verifies tenant and soft-delete state from canonical models. A contradictory Patient/RDV association is rejected; an RDV without canonical patient cannot identify a patient. Missing references require a human. Even a unique Patient/RDV is only STAFF_CONFIRMATION_REQUIRED until a trusted device capture context exists.

The response never grants uploads and has server_confirmed=false, upload_permitted=false, receipt_id=null. No SQL migrations, new tables, clinical asset creation or patient record modifications. The existing Media Core import endpoint is unchanged.

## Open blockers, NO-GO
An atomic durable idempotency ledger and short-lived device credentials are not available without additional canonical server design. The content-addressed blob store alone does not prevent duplicate logical ClinicalAsset rows. No signed upload ticket, capture session, server receipt lookup, human confirmation transaction or patient media timeline proof is implemented. The full synthetic ingestion success criterion is NOT met. Windows hardware and NTFS field tests are NOT executed. LOT04 integration gate remains open. Do not merge, deploy or activate.

Targeted regression: backend/tests/test_imaging_acquisition_preflight_v15.py and backend/tests/test_media_core_ingestion_api.py.
