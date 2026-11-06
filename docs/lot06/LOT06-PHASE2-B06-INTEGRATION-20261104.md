# LOT06 Phase2 B06 — Integrating product boundary with a clinical acquisition FUE-I (candidate, 2026-11-04)

## Goal / scope

Single stacked candidate on B05-D1 GREEN LAB commit `705b9951d672d5776cbd22c3633623f4332018fa`, retaining the single [canonical LOT06 Notion](https://app.notion.com/p/3e677c66336281639beae2a946df1483).

**Target clinical journey:** native scanner capture → unassigned encrypted inbox → authenticated staff image preview → dual patient identity markers and explicit acknowledgement → Media Core encrypted ClinicalAsset → durable signed ACK with replay without duplicates.

**What this pass actually implements:** one real correction to the existing LAB review UI: the LAB image preview is fetched through the authenticated Digital Crown API (Bearer/cookies handled by the shared client), checked for exact byte length, PNG MIME and SHA-256 digest, then displayed from a short-lived local blob URL; the confirm button stays blocked until that exact image fires load for the *same capture, patient, hash, challenge and URL*. An external preview URL, preview load error, stale or rotated challenge, wrong dossier or DOB, absent explicit checkbox, expired context and failed server confirmation remain blocked. The LAB UI is NOT mounted in clinical product navigation.

One same-server SQLCipher/FastAPI FUE-I now exercises the ACTUAL product read-only patient endpoint side-by-side with existing isolated signed-media staff review, preview, two markers, encrypted ClinicalAsset and durable idempotent ACK. It asserts the product ingress is *still closed* before and after the LAB success, no auto-patient link, and no accidental POST/clinical confirm API. The CI additionally executes existing Windows real SCM restricted-SID spool verification, B05-D1 Authenticode ZIP negative cases and React review tests **on the same candidate SHA**.

## Proof required (not presupposed)

- `same-server-sqlcipher-product-fue`: real localhost HTTP JWT/workstation + SQLCipher positive/negative FUE + no duplicate asset/receipt/audit/outbox.
- `preview-review-ui`: React tests for wrong identity, missing preview, off-origin preview, load error, challenge rotation, server rejection, closed production state; no approval based only on filled fields.
- `windows-real-service-and-b05-package`: actual disposable Windows SCM service, ciphertext verification and bounded temporary Authenticode trust; reject different-but-Windows-valid signer and tampering.
- Check exact SHA, real job logs, expected collected/executed tests and absent unexpected skips; GREEN CI alone does not close B06.

## Explicit remaining blockers

1. **Native adapter:** the current B03 real Windows SCM fixture only returns `Q→U` (no usable image identity) and `S→S0..S9/E*` for **synthetic LAB count**; it has no product API handing a verified specific capture to the application. Product status is intentionally `NATIVE_IPC_NOT_CONNECTED`.
2. **Production staff review:** existing SQLCipher staff challenge/confirmation endpoints are LAB mounted only. No actual product authenticated preview/confirm transaction exists yet; an HTTP test client is NOT a human validation.
3. **Storage / ACK:** SQLCipher signed receipt/asset/audit/outbox is demonstrated in isolated fixtures, not reconciled under a common on-prem production schema with real device identity, power cut, backup and rollback.
4. **Windows release:** Authenticode CI certificate is self-signed and disposable. No actual approved publisher trust, full Python/runtime dependencies, hardened installer/upgrade, physical TPM/CNG lifecycle, second Windows machine, scanner or cabinet approval.
5. **UX:** no observed product AFTER browser screenshots at required viewports or 200% zoom; no human UAT. Do not claim FUE-G or release readiness.
6. **Security gap for eventual product image:** the LAB preview now uses the authenticated API client, exact byte-size/digest matching, and short-lived blob URL, but the product still needs a proven server-side native capture authority and session/preview token binding, an approved secure browser context for WebCrypto, and real human UX observation. A visual load event is NOT proof of human inspection.

## Release boundaries

`READY_TO_MERGE=false`
`PRODUCT_READY=false`
`CLINICAL_GO=false`

No automatic patient association. No deployment, merge, release, clinic installation, data migration, production patient fixture or artificial approval of clinical controls. Next implementation on THIS consolidated product integration branch: adapt real Windows service and authenticated local API with per-capture identity and safe preview, then mount the verified staff review + durable receipt using a server-owned authority, followed by real FUE-G. Human authorization is separate for critical activation and cabinet operations.


## B06 continuation — native per-capture inventory (2026-11-04)

**Actual scope (candidate pending exact-head CI):** the real disposable SCM LocalService fixture gains an `I` command, separate from existing `Q→U` and `S→S0..S9`. Under its Windows service SID the helper reopens and AES-GCM-authenticates the HotFolder ciphertext; it validates digest/size/MIME, verifies the item is still pending and emits one fixed **86-byte** unassigned metadata frame `I1` + local item ID + size + SHA256 + MIME/category codes. It never emits bytes, filename, selected patient or appointment. Verified empty queue yields `N0`; corrupted/unauthorized/invalid read yields a DENY and must never masquerade as `N0`. The local item ID is **not** a cryptographic device/capture claim and is not sufficient to approve transfer.

The new backend `imaging_acquisition_native_inventory_v15.read_native_unassigned` speaks that pipe as the existing OS principal. It is guarded by Windows + GitHub-hosted disposable test flags and the observed ACL. **Not mounted into backend.main, not exposed as a patient API.** All wire fields have canonical fixed-length validation; deliberately no media bytes, patient selection, device signature, approval, TLS claim, ACK or write operations. CI runs real LocalService and approved Windows user, rejects a second user, corrupt ciphertext and wrong-key, validates stability across service restart, and reuses existing SQLCipher/HTTP/JWT human ceremony tests. All tests are synthetic; physical equipment NOT_RUN.

This is a concrete Windows→local-application metadata bridge, **not** a complete clinical ingestion path: the product still reports `NATIVE_IPC_NOT_CONNECTED`. To make it product-capable, next implement a service-owned per-capture authenticated transfer handle/preview protocol with strong device key attestation, bind short-lived staff review to the exact bytes, and atomically commit Media Core asset/receipt/outbox with crash/restore evidence, using a release-approved installer. No right to associate a patient from the returned numeric item ID.

**Gates:** `READY_TO_MERGE=false` · `PRODUCT_READY=false` · `CLINICAL_GO=false`. UI visual approval remains a separate human decision. No merge/deployment/cabinet action.

## B06 continuation — raw media transfer over restricted Windows SCM pipe (2026-11-04)

**Scope, pending exact-HEAD FUE:** experimental `M` opcode for *a single, still-unassigned, AES-GCM-verified* capture, requested by fixed ID/SHA256/offset/count on an ephemeral GitHub-hosted Windows runner, never cabinet. Wire: ASCII `M + id(10d) + sha256(64hex) + offset(8d) + count(4d)`, exactly 87 bytes; response `D + count(4d) + binary fragment`, or exact `E0000` refusal. The Windows pipe ACL continues to permit only the synthetic separately-created approved Windows account SID, service LocalService SID and SYSTEM. The service reads the encrypted spool and revalidates pending status, SHA256 and MIME before each fragment. The process does not log or store the cleartext on disk. Client checks original inventory and complete assembled byte count, digest and structural PNG validity, then checks inventory again. Media never gains any automatic patient/appointment association, ClinicalAsset, ACK or upload authority.

Deliberate bounded prototype: **PNG only, 16 KiB maximum synthetic image per capture, 2048-byte maximum fragment**, per-fragment LocalService subprocess; this is NOT performant for a real radiograph and MUST NOT be made a product endpoint. Host requires TEST, isolated runner and separate `DC06_B06_NATIVE_MEDIA_LAB=1` gate; no production or clinic paths. The service Windows account authorization is NOT sufficient clinical device or staff authentication (no hardware TPM/approved publisher/one-time staff-bound secret). The clinical product remains `NATIVE_IPC_NOT_CONNECTED`.

Negative FUE required on actual Windows: valid binary PNG readback and SHA256, forged id and digest refused **by the service**, service restart stable, wrong key / corrupted ciphertext rejected with explicit error, second Windows account cannot read, malformed frame and oversized range denied by parsers; re-run existing B03/B05 and HTTP SQLCipher/ack/UI regressions on exact candidate SHA. A test-only client invokes these probes and prints **fixed non-PHI markers**, never the media bytes. These are not human screenshot/UAT evidence and do not certify physical scanner, rollback, power-loss or cabinet restore.

Next true product work: replace per-chunk helper with performant persistent service protocol; use an approved service/device root of trust, SID and caller authentication, per-capture replay-safe staff-scoped capability, secure local app preview and explicit two-identifier patient binding, then atomic ClinicalAsset/receipt/outbox and real recovery/FUE-G. No merge/deployment without separate authorization.

`READY_TO_MERGE=false` · `PRODUCT_READY=false` · `CLINICAL_GO=false`.


## B06 staff preview / genuine multi-fragment Windows FUE — 2026-11-04

This candidate extends the real SCM Windows fixture from its previous 79-byte
PNG (one transport fragment) to a generated **synthetic, 6+ KiB valid PNG**
containing a benign ancillary tEXt chunk. It requires at least **four actual
2048-byte Win32 SCM pipe transfers**, not merely the preexisting two-fragment
Python protocol unit test. Every fragment is freshly AES-GCM verified under
the LocalService SID and the reassembled PNG must match the original SHA-256,
size and structural validation. Wrong capture ID, wrong digest, wrong AES key,
ciphertext corruption, wrong Windows user, restart and B05 signer/package
oracles remain REQUIRED on the exact changed HEAD.

Separate TEST-only staff preview hardening: the JWT + workstation + patient
preflight alone no longer permits the media GET. The isolated review server
requires the active, unexpired, unconsumed SQLCipher challenge of the same
staff, patient, workstation, capture digest and byte size. The UI supplies the
challenge as an authenticated `X-DC-Review-Challenge` request header, **not
a URL query parameter**. HTTP FUE denies absent/mismatched challenge, missing
review, expired review and post-confirm preview. This prevents previews from
remaining accessible beyond the current explicit staff review ceremony. It is
still a LAB authorization, **not** clinic device attestation or human approval.

CI must report the actual Windows four-fragment marker and all negative
oracles, HTTP/JWT/SQLCipher negatives and UI tests on the same HEAD; do not
promote code changes alone into a GREEN certification. Neither isolated
LAB review nor Win32 transport is mounted in production
`backend.main`: real product continues `NATIVE_IPC_NOT_CONNECTED`.

Remaining gates: approved publisher/service+device trust, secure
session-bound per-capture capability, real clinical media transport beyond
16 KiB, true on-prem patient selection/review + encrypted ClinicalAsset and
durable ACK, crash/replay/restore and second-host/scanner/TPM/human FUE-G.

`READY_TO_MERGE=false` · `PRODUCT_READY=false` · `CLINICAL_GO=false`.



## B06 continuation — server-held Ed25519 device proof × staff review challenge (2026-11-04)

The LAB review was already staff-JWT/workstation/challenge scoped, and the
separate signed upload/receipt verified a pinned Ed25519 device identity.
Previously the *preview* did not require that independently signed proof.
This pass reuses the **existing** test-only SQLCipher device enrollment:
`verify_pending_device_capture_proof(db, claim, device_proof)` validates
the registered, active Ed25519 device key and its generation/station,
the pending immutable capture ID, selected patient/staff/tenant, SHA-256,
byte count, and the test-device-only challenge. It refuses key substitution,
device revocation, expired or consumed pending capture and any invalid proof.
It runs at **LAB review begin, explicit confirmation and preview**. The
signature is supplied by a **server-owned test fixture closure**, never a
query parameter, browser header or automatic patient identifier.

The existing staff authority independently requires JWT + workstation cookie,
patient access, the selected dossier/DOB markers, an expiring one-use SQLCipher
challenge bound to the same capture and active staff, and explicit confirmation.
The media bytes passed to LAB mount must match the signed claim digest and
length. This is **two independent authorities for LAB**, not a certified
physical scanner enrollment or an authenticated Windows host/device bridge.
A browser's copied review challenge cannot replace the device proof, and a
device signature cannot act as a staff confirmation.

Exact-head FUE required: real SQLCipher/localhost HTTP refusing preview,
begin or confirm after pinned key substitution, generation change or device
deactivation; the underlying proof rejects wrong staff, workstation, patient,
capture ID, digest, byte count, generation, foreign key; successful prior
LAB review + encrypted Media Core signed ACK and Windows multi-fragment
SCM/Authenticode must regress on SAME SHA. Product `backend.main` still
does not mount the LAB preview/transfer and patient status stays
`NATIVE_IPC_NOT_CONNECTED`.

**Still OPEN:** verified signed capture issued by the *actual* Windows
service instead of a disposable fixture closure; TPM/hardware enrollment,
release signer and physical scanner; scalable real DICOM/JPEG/PNG/PDF media;
actual staff login session-bound native capability in backend runtime,
one atomic on-prem media/receipt/outbox transaction with interruption/retry,
visual FUE-G and owner authorization.

`READY_TO_MERGE=false` · `PRODUCT_READY=false` · `CLINICAL_GO=false`.


## B06 — device-signed patient-unassigned manifest before human selection (2026-11-04)

**Architectural correction (pending exact-HEAD proof):** the LAB test-device
Ed25519 signature previously covered a staff-/patient-bearing `claim` even
for preview. This is the wrong authority for a physical scanner, which must
never decide the eventual patient. The new **independent, immutable and
patient-free signed capture manifest** contains exactly: enrolled tenant,
device, station, generation, opaque capture ID, verified media SHA-256,
byte length, image/png MIME, random nonce, issuance and expiry. Its
canonical JSON includes domain-separated purpose, no staff, patient,
dossier, DOB, appointment or asset ID. The private signing key stays in
the disposable synthetic device fixture; server SQLCipher stores the
manifest and signature, checks the enrolled pinned Ed25519 public key
and rejects key substitution, changed digest/size, expiry and reused
nonces. No browser/device client gets to submit the proof while reviewing.

The LAB review now validates this **unassigned** signature when starting,
previewing and confirming. Confirmation consumes the manifest **inside
the same SQLCipher transaction** that marks the staff review consumed,
records independent device-review approval and its audit. A rollback
restores the manifest for safe retry; replay after confirmation cannot
reopen preview or bind the same capture to another patient. The separate
legacy 03M laboratory upload/receipt STILL uses its prior patient-/staff-
coupled signed claim: the end-to-end production authority is therefore
**not yet migrated**. This change only corrects the *pre-patient* proof
and staff review boundary, not the clinical publisher.

**FUE required on final SHA**: independent SQLCipher tests for signature
byte fields excluding patient/staff, forged device key, crossed device,
capture, station, generation, size/digest, duplicate nonce, expired and
revoked manifest, transaction rollback and one-time consumption, plus
existing localhost JWT + review + patient double-markers + encrypted
ClinicalAsset/ACK replay, Windows real SCM multi-fragment/Authenticode,
and React tests. The actual product endpoint must remain
`NATIVE_IPC_NOT_CONNECTED` and the human visual workflow cannot be
bypassed. Existing Windows child process 15-second timeout was observed
on the prior PR HEAD despite an identical-SHA successful retry; keep
CI reliability as an open risk.

**Clinical gaps:** real scanner-signed manifest via service-owned pinned
device key/TPM, native staff session capability, non-test enrollment,
full-size radiography, independent authorization/transaction receipt,
crash/recovery/second host, visual human approval. No physical hardware
test was performed.

`READY_TO_MERGE=false` · `PRODUCT_READY=false` · `CLINICAL_GO=false`.


## B06 implementation block 1/5 — product backend ↔ Windows SCM unassigned inventory (2026-11-04)

**This is LOT06 software implementation, NOT a physical LOT10 test.**

Product route `GET /api/imaging/acquisition/unassigned` is now mounted
in **actual `backend.main`**. The endpoint is GET-only, served on loopback,
and requires actual authenticated JWT permission `patients` and a valid
current tenant's enrolled workstation cookie (station-locked mode DENIED).
The response contains **only one unassigned record's canonical opaque ID,
SHA-256, byte count, MIME and category**. No patient/dossier/appointment,
raw image, filesystem path, pipe name or per-patient suggestion; no POST,
ClinicalAsset or receipt. No-store/no-sniff response headers. With no
trusted local native bridge explicitly attached to the server, it responds
`NATIVE_IPC_NOT_CONNECTED` and an empty queue — with no false claim that
the service is installed or trusted. Failed native inventory reads return
503, **not** a fake empty queue.

`backend/services/imaging_acquisition_native_bridge_v15.py` encapsulates a
tenant/workstation-bound backend service adapter with real Win32 functions
`read_native_unassigned` and `read_native_capture_bytes`. The latter is
**server-side only** in block 1: it refuses changed inventory before/after
read, mismatched hash, byte length or MIME, and exceeds neither the currently
certified 16 KiB Win32 LAB limit nor its PNG-only media scope. No raw bytes
are exposed by any B06-1 HTTP endpoint. The actual Windows SCM CI fixture
now calls the same backend inventory adapter under the separate authorized
Windows account, verifying real AES-GCM spool metadata and rejecting foreign
tenant ID at the product service boundary.

**Mandatory fail-closed bootstrap separation:** product `backend.main`
does not automatically install, attach or discover an IPC pipe from a
browser, HTTP request, environment toggle, filename or untrusted installer.
The trusted object must be supplied via
`app.state.dc06_unassigned_bridge` **only after future verified
service installation and attestation**, not by front-end callers. The
existing Win32 wire client remains explicitly LAB-gated to an approved
GitHub-hosted Windows test environment. Thus this step **connects
the software APIs and proves data flow with mocks and the genuine Windows
SCM test**, but does **not** activate a real cabinet native service. The
existing patient-scoped status remains `NATIVE_IPC_NOT_CONNECTED` and
`clinical_receipt_authorized=false` intentionally until staff-bound
preview and patient confirmation in block 2/5 and durable integration in
block 3/5.

**B06-1 FUE required** at exact SHA: no JWT 401/403, missing or wrong
station 423, no attached bridge returns non-authorizing disconnected
status, tenant/station mismatch denied, canonical inventory with no
patient fields, actual SHA/size/MIME byte checks, race/swapped capture
denied, malformed/failed peer gives 503, GET no-store, POST 405, raw
media URL 404, zero receipt/asset writes. Real Windows SCM/LocalService
unassigned read & multi-fragment SHA, wrong key/corruption/second user,
Authenticode signer/ZIP and React must remain GREEN.
No hardcoded theme styles. Do not merge/deploy/install on this pass.

**LOT10 ONLY:** scanner physical, TPM hardware, true second workstation,
power interruption and cabinet human acceptance; these are NOT LOT06
feature-development blockers. LOT06 remains responsible for testable
production integration plus automated CI and non-physical UI review.

`READY_TO_MERGE=false` · `PRODUCT_READY=false` · `CLINICAL_GO=false`.


### B06-1 Windows import regression / corrective boundary — 2026-11-04

Initial three-job B06 run on HEAD `6794cf73` was **FAILURE** on
Windows, although Linux SQLCipher/HTTP **68/68 PASS** and React PASS.
The failure was **not** from AES-GCM or SCM: importing
`backend.services.imaging_acquisition_native_bridge_v15` into the
minimal separate-user Windows helper triggers `backend.__init__`, which
imports SQLAlchemy (not installed in that hermetic client). The child
exited 1 at Python import before its native media probe.

Architectural fix: move the identical class implementation into
`tools/imaging_gateway/native_product_bridge_v15.py`, a deliberately
**ORM-free** shared native adapter. The product backend service facade
reexports the same class; Windows helper imports the shared gateway
module directly, without bringing ORM, API, or clinical DB packages to
the LocalService/peer test. Existing Win32/SID DACL/AES checks unchanged.
The exact-head Windows CI must now reach
`DC06_B06_PRODUCT_NATIVE_BRIDGE_REAL_SCM_SCOPED_INVENTORY_PASS`
and all original negative oracles. Never install SQLAlchemy into the
trusted Windows IPC client just to hide this architecture regression.


### B06-1 Windows separate-account process launch bound — 2026-11-04

After the ORM-free import correction, B06 CI #41895638025 backend **68 PASS**
and React SUCCESS, but the hosted Windows runner failed **before any B06
media probe**, at the disposable SCM harness's first separate-user child
process launch `C05B03R_CHILD_15S_TIMEOUT`. This is a recurring runner
startup fragility previously observed in B06 and does not prove a bad
AES-GCM response. To preserve deterministic fail-closed behavior without
adding retries, the one-process launch upper bound increases from
15,000 ms to **30,000 ms**; after that, the child is killed and the FUE
still fails `C05B03R_CHILD_30S_TIMEOUT`. No service authentication, pipe
ACL, crypto, media validation or product route was weakened. Only exact-HEAD
success with a real Windows SCM + B05 Authenticode can certify this pass;
the previous failed attempt remains evidence.


## B06 bloc 2/5 — product staff preview and two-marker selection (2026-11-04)

**Software scope, NOT real physical LOT10 testing.** Actual `backend.main`
now keeps its authenticated unassigned queue (B06-1) AND mounts review
endpoints in the same product router:

- `POST /api/imaging/acquisition/review`: staff explicitly selects an
  existing patient ID AND a verified pending capture ID/digest. Server uses
  `require_permission("patients")`, real tenant-scoped WorkstationMode
  cookie, loopback network, a matching bearer session, patient-access and
  preflight. The verified native bridge checks SHA256/size/PNG before an
  ephemeral review capability is created. It returns patient name and
  the *two actual database markers* (dossier and birthdate) only to the
  authorized selected staff, and a 90-second one-use challenge.
- `GET /api/imaging/acquisition/review/{review_id}/preview`: only the
  same staff+tenant+workstation+bearer session and matching challenge
  may read the verified PNG; the backend rechecks native inventory before
  and after the transfer and the precise digest/size, then returns
  `no-store`/nosniff. Never issue an unrestricted or external media URL.
- `POST /api/imaging/acquisition/review/{review_id}/confirm`: explicit
  true consent flag, exact selected patient, typed dossier+DOB, capture
  digest, unexpired one-use staff challenge AND a fresh validated media
  read; then atomically consumes the **ephemeral** selection lease.
  A second selection/confirmation of the same opaque capture ID is denied
  within the process even if its digest changes.
- `DELETE /api/imaging/acquisition/review/{review_id}`: authenticated
  exact-session cancellation of a pending review; rejects wrong challenge
  or replay, permits a fresh explicit attempt after cancellation.

The real patient **Media** tab renders
`ImagingAcquisitionProductReviewV15`, only when the genuine product
unassigned-inventory route reports one valid PNG in the active workstation.
It never chooses a patient from filename/appointment/device. The staff
must press **Examine this capture for this patient** on the explicitly
opened patient route, visually load a browser-side SHA256/size/MIME-verified
preview and manually enter dossier and birth date + tick the confirmation
checkbox. New capture, patient or token invalidates previous UI checks.
Component uses theme tokens (no hardcoded palette).

**Important fail-closed boundary:** `ProductReviewStore` is process-local
and intentionally volatile, not a durable approval: after restart/worker
change the capability fails. It does not create patient-asset association,
ClinicalAsset, audit/outbox, medical media publication or clinical ACK.
This is exactly block 2/5; durable media and cross-process authorization
belong to block 3/5. The service-side Win32 provider remains unattached
on actual product startup and the hosted Windows pipe stays test-only
until installation/trust can be established. The pre-existing product
patient status still reports `NATIVE_IPC_NOT_CONNECTED` and
`clinical_receipt_authorized=false`. No real cabinet activation.

**Exact-SHA FUE required**: actual HTTP/JWT/SQLCipher product route
401/403/423, foreign patient/capture rejection, wrong digest, missing
bearer, cross session, wrong preview challenge, tampered media, wrong
dossier/DOB, no checkbox, one-use consumption/cancel, zero ClinicalAsset
or receipt, POST 405 on inventory; React verified onLoad and SHA, no
automatic patient selection, expiration/stale route fail-closed; Windows
SCM + AES-GCM multi-fragment/restart/negative access + Authenticode
unchanged. Human *visual approval* and code-level accessibility remain
separate UI gates. Physical scanner/TPM/2nd workstation/power-cut are
**LOT10 exclusively**. Do not infer physical proof from Windows CI.

`READY_TO_MERGE=false` · `PRODUCT_READY=false` · `CLINICAL_GO=false`.


## PRE — B06 bloc 3/5 — ClinicalAsset chiffré + ACK durable (2026-11-04)

Base vérifiée à l'ouverture : PR #1210 OPEN/DRAFT, HEAD B06-2 `4d3ea038ca288ddab9e68a47a39b7f02d8762ba1`. B06-2 = confirmation éphémère : aucune association, aucun ClinicalAsset ni ACK ; sa réussite 71 backend / 16 React / Windows SCM reste limitée au LAB. Les workflows transversaux de ce SHA sont terminés : B03 et CB-02 SUCCESS ; Portability Runtime FAILURE (hors preuve B06, investigation séparée) ; Human Visual Approval FAILED. Le canonique Notion LOT06 et les garde-fous FUE-first ont été relus.

GOAL B06-3 : associer une capture native vérifiée au patient expressément choisi et revérifié par le personnel, écrire un ClinicalAsset Media Core chiffré + une décision d'approbation auditée + un ACK récupérable et idempotent ; prouver refus patient/tenant/poste/session/digest/rejeu, échec/rollback, crash/reprise et absence de doublon à l'aide de données synthétiques et SQLCipher réel. Le succès exige un chemin produit authentifié et une transaction durable cohérente, non un seul banc de tests isolé.

Avant toute mutation de schéma : réévaluer modèle Media Core, migrations existantes et autorisation canonique LOT04/SQL ; si la migration/le contrat requis n'est pas autorisé ou la preuve de récupération n'existe pas, préserver le fail-closed et marquer B06-3 OPEN plutôt que simuler un ACK. Aucun média patient réel, secrets réels ou pilote ; aucun merge master, activation clinique, installation cabinet ou déploiement. LOT10 reste exclusivement le laboratoire matériel/terrain. `READY_TO_MERGE=false`, `PRODUCT_READY=false`, `CLINICAL_GO=false`.


## POST — B06 bloc 3/5 : chemin ClinicalAsset/ACK durable, gate de schéma non levé (2026-11-04)

**État honnête : B06-3 IMPLEMENTED_CANDIDATE / OPEN, non activé ; B06-2 GREEN LAB conservé.** Sur la PR #1210 DRAFT, création de `backend/services/imaging_acquisition_durable_v15.py` et raccordement conditionnel des routes de revue produit, du panneau Médias patient et des FUE SQLCipher ; aucun déploiement ni merge. La fonctionnalité durable n'est activable que via état serveur approuvé, absent de `backend/main.py`. Les tables `dc06_b06_product_receipts`, `_audit`, `_outbox` sont **des descriptors de schéma test-only** : pas de migration Alembic ni de `create_all` en chemin produit.

### Invariants implémentés / à prouver au HEAD final

- Sélection staff explicite, challenge/session/poste/JWT, deux marqueurs dossier + date de naissance, capture vérifiée par lecteur natif SHA-256 ; données binaires sans nom de patient dans le flux natif.
- Écriture du ClinicalAsset Media Core et blob AES-GCM authentifié puis ledger `(tenant,station,capture)`, audit, outbox et reçu Ed25519 dans une transaction SQLCipher `BEGIN IMMEDIATE` ; rollback sans ACK/asset, éventuel orphan **chiffré seulement** ; contrôle du tenant/patient/staff sous verrou ; clé de signature dérivée de `CABINET_MASTER_KEY_HEX`, rotation à cadrer avant pilotage.
- ACK ré-interrogeable par patient/empreinte/staff/poste et vérifié sur les octets déchiffrés, même si le scanner ou le cache de revue est arrêté. Rejeu inter-patient/digest refusé, statut de cabinet `clinical_receipt_authorized=false` explicite. L'interface ne confond pas revue temporaire et association durable et récupère un ACK perdu sans second upload.
- Protection : schéma manquant / switch absent => 503, jamais une persistance fictive. Aucun établissement de confiance réel du périphérique/SCM ni test LOT10 physique dans ce sous-lot.

### Batterie FUE et preuves provisoires

- React 18/18 PASS sur les HEADs de travail du B06-3, dont reçu durable et récupération après perte de réponse ; Windows SCM/Authenticode SUCCESS dans les mêmes runs. Pas de capture visuelle humaine approuvée.
- Run B06 #41917593370 au HEAD `325f56bf0eaaf286a3ec095e2910c59fcbaf92be` : 74/75 backend PASS, un seul échec d'**oracle de statut** dans le test nouveau : après retrait volontaire de l'IPC, la tentative de nouvelle capture retourne 503 (fail-closed) et non 409 (capture déjà prise). Le test a été corrigé pour exiger 409 avec IPC présent et 503 hors ligne ; pas de constat de défaut du chiffrement ou de l'ACK dans ce run.
- **Convergence finale PENDING** : refaire backend/React/Windows sur le SHA final après correction et mise à jour canonique, contrôler collecte/exécution/skips ; ne jamais transformer ces 74 PASS partiels en 75/75 certifiés sans CI du HEAD final.

### Gate non résolu / suites précises

1. Faire approuver par propriétaire des données et LOT04 le schéma durable (unicité capture, références, immutabilité du ledger, migration/rollback/restauration SQLCipher et backfill anciens cabinets). Aucun SQL DDL implicite.
2. Prouver le binding native SCM ↔ session ↔ patient dans un runtime de packaging autorisé, refus clé révoquée et retour après panne réelle, clé et signature en rotation, données synthétiques uniquement.
3. Corriger et faire **approuver humainement** les screenshots BEFORE/AFTER, navigation clavier/focus et zoom 200% de l'onglet Médias ; un green React n'est pas une preuve visuelle humaine.
4. Exécuter FUE-I/G sur un poste de test autorisé, puis seulement les épreuves physiques du LOT10 quand leur gate est atteint. Pas d'activation ni d'avis de conformité.

`READY_TO_MERGE=false`; `PRODUCT_READY=false`; `CLINICAL_GO=false`; `LOT10_PHYSICAL_VALIDATED=false`.


## FUE FINAL CONFIRMATION — B06-3 LAB, code HEAD `a938564d75e4c16f828b31d61a422a1831eb67d1` (2026-11-04)

**CERTIFIABLE LAB RESULT, NOT CABINET RELEASE:** GitHub run [#41918287716](https://github.com/hraaaaf/Digital_crown/actions/runs/41918287716) : 3/3 jobs SUCCESS sur le SHA exact : SQLCipher backend **75/75 PASS** (0 skip sur suite collectée), frontend React **18/18 PASS** (3 fichiers), Windows 2022 SCM/service/identité/AES-GCM/restart/tamper/wrong key + Authenticode ZIP/manifeste/signataire non épinglé refusés **SUCCESS**. Des logs source portent `DC06_B06_3_SCHEMA_MISSING_AND_DISABLED_ZERO_WRITES_PASS`, `DC06_B06_3_PRODUCT_SQLCIPHER_ASSET_SIGNED_ACK_RESTART_REPLAY_PASS`, `DC06_B06_3_ATOMIC_ROLLBACK_ENCRYPTED_ORPHAN_SAFE_PASS`, `DC06_B06_3_TAMPERED_SIGNED_ACK_DENIED_PASS`, `DC06_B06_NATIVE_MEDIA_RESTART_SHA_STABLE_PASS`.

Au même SHA, Portability Runtime SUCCESS et LOT06 C05B-03K/L + C05B-03M SUCCESS. **Human Visual Approval FAILURE** ; CB-02 B et B03 transversaux encore actifs au moment de cette preuve (leur statut peut évoluer). Le code/lab est **GREEN LAB B06-3**, mais le lot reste **OPEN** : aucune migration approuvée, aucun `main.py` flag d'activation, aucune preuve visuelle humaine ni LOT10 physique. Les certificats Windows sont explicitement jetables de laboratoire, pas un publisher cert de production.

Cette insertion est **documentaire uniquement** ; la batterie `lot06-phase2-b06-integration-fue.yml` se réexécute sur le nouveau HEAD après ce changement de document. Seul le run du nouveau HEAD peut constituer une preuve one-HEAD finale si le contrôle strict l'exige. Aucun merge/déploiement/activation. `READY_TO_MERGE=false`, `PRODUCT_READY=false`, `CLINICAL_GO=false`.


## PRE — B06 bloc 4/5 : contrat de schéma / compatibilité locale / visuel (2026-11-04)

**HEAD PRE** `ddc53c89a819af07762d84794b6105b57f6697bf`, PR #1210 OPEN/DRAFT. Le run [#41918952406](https://github.com/hraaaaf/Digital_crown/actions/runs/41918952406) est définitivement **3/3 SUCCESS** (rerun Windows du même HEAD), backend 75/75, React 18/18, SCM/Authenticode PASS. B02, B03, CB-02 et Portability Runtime également SUCCESS sur ce HEAD. Human Visual Approval `#41918956352` = FAILURE attendue `PR HEAD changed: approval revoked; new screenshots and explicit approval required` ; aucun contournement ni label forgé.

**ARCHITECTURE RISK / BLOCKER C :** le cabinet V1 installé documenté dans `docs/clinic/CABINET_UPGRADE_COMPATIBILITY_GATE.md` exploite PostgreSQL 18.2, tandis que B06-3 `_sqlcipher()` refuse tout moteur non-SQLCipher. Le guide de LOT06-acceptance #851/#909/#1172 prescrit précisément de réconcilier SQLite/SQLCipher et PostgreSQL avant migration. Aucun choix de cible n'a été approuvé ici. Le code SQLCipher-only peut être certifié LAB mais ne peut pas être déclaré installable au cabinet PostgreSQL.

**Scope de ce passage réversible (aucune mutation réelle)** : certifier un contrat d'intégrité du ledger SQLCipher B06 sur fixture isolée (tables, clés, unicité, immutabilité, refus de schéma tronqué/falsifié), oracle de refus PostgreSQL/plain SQLite, et rédiger décision opérateur explicite PostgreSQL vs SQLCipher + conditions restauration/rollback sans inventer un GO. Si un schéma additionnel change la fixture de laboratoire, un test doit le provisionner explicitement ; `backend.main` doit rester sans `create_all`/bootstrap durable.

**GATES REQUIRED :** preuves FUE exact-HEAD, 0 données réelles, human visual approval réellement humain, architecture/migration approuvée, aucun merge, installer, déploiement, pilote ou test LOT10 physique. `READY_TO_MERGE=false`, `PRODUCT_READY=false`, `CLINICAL_GO=false`.


## POST — B06 bloc 4/5 : contrat de schéma sécurisé, moteur cabinet non choisi (2026-11-04)

**Verdict précis : B06-4 SQLCipher SCHEMA CONTRACT = GREEN LAB ; B06-4 PRODUCT = OPEN.**

**Code HEAD certifié :** `57bca1eeb5c71af0d02911d7a3d0573335392d74` ; [run B06 #41924917294](https://github.com/hraaaaf/Digital_crown/actions/runs/41924917294) = **3/3 jobs SUCCESS sur le même SHA** :
- Backend SQLCipher **77/77 PASS**, nouveau FUE `DC06_B06_4_REJECTS_INCOMPLETE_SCHEMA_AND_IMMUTABLE_ACK_AUDIT_PASS` et `DC06_B06_4_PLAINTEXT_SQLITE_REFUSED_PASS` ; revue produit précédente, hash, attestation temporaire, ClinicalAsset AES-GCM, récupération de l'ACK, rollback et refus de rejeu régressions PASS.
- React **18/18 PASS** sur trois fichiers ; aucun nouveau delta visuel dans B06-4.
- Windows SCM/LocalService, AES-GCM, redémarrage/clé erronée/corruption/autre utilisateur, signature Authenticode et manifeste fermé **SUCCESS**. Certificats LAB éphémères uniquement.
- Première passe B06-4 `366cb3a`, 75/77 backend PASS : deux échecs d'oracle car le driver `sqlcipher3.dbapi2.IntegrityError` émerge directement au lieu d'un wrapper SQLAlchemy. L'implémentation refusait correctement les UPDATE ; le harnais a été corrigé pour accepter **uniquement l'exception d'intégrité native ou SQLAlchemy**, sans relâcher les triggers. Le run rouge reste conservé en preuve.

**Modifications de code :** dans `backend/services/imaging_acquisition_durable_v15.py`, l'ancien contrôle « trois tables existent » est remplacé par la vérification en lecture seule des noms de colonnes, nullabilité, clés primaires et index UNIQUE (`asset_id`, `receipt_id`) et des six triggers anti-UPDATE/DELETE à SQL contrôlé sur reçus, audit et outbox. Aucune réparation automatique, DDL, Alembic ou `create_all` en `backend.main`. Le nouvel oracle exige les garde-fous en fixture SQLCipher synthétique et vérifie qu'une modification est effectivement rejetée. Le fait de créer des tables aux noms attendus, sans triggers, est maintenant un refus 503.

### Décision d'architecture requise avant B06-4 PRODUCT

**Conflit vérifié documentaire :** `docs/clinic/CABINET_UPGRADE_COMPATIBILITY_GATE.md` décrit le cabinet V1 déjà installé sur **PostgreSQL 18.2 local**, avec migration Alembic explicite avant démarrage ; `imaging_acquisition_durable_v15.py` est conçu **SQLite/SQLCipher seulement** (PRAGMA + `BEGIN IMMEDIATE`). Le moteur actuellement installé *aujourd'hui* n'a pas été interrogé physiquement pendant cette passe ; ne pas confondre baseline documentaire et inventaire cabinet 2026-11-04.

**Recommandation sous réserve d'inventaire : conserver PostgreSQL local** sur le poste actuel et construire un adaptateur durable transactionnel PostgreSQL dans une suite isolée, avec schéma additif explicite, unicité et contrôle de concurrence, audit append-only, restauration de backup et FUE réels du serveur local. C'est moins risqué qu'une conversion complète des dossiers patients PostgreSQL→SQLite uniquement pour B06. Si l'autorité choisit SQLCipher, cela nécessite une **décision distincte de migration du moteur complet**, y compris préservation de tous les dossiers/liens/archives/médias/IDs, restore complet et approbation spécialisée ; aucun GO ici.

**FUE / gates encore REQUIRED avant l'activation logicielle :**
1. Inventaire read-only du véritable backend cabinet et autorisation explicite du propriétaire pour le schéma cible ; examen de coordination LOT04, index/FK/append-only, plan rollback/backfill et absence de modification historique.
2. Migration **seulement en clone isolé**, tests de panne/reprise et restauration DB/médias ; aucune migration patient réelle ni conversion silencieuse.
3. Intégration du service natif de confiance/SCM sans injection test `app.state`, autorité périphérique + staff + session, récupération ACK avec renouvellement/rotation des clés et preuve de visibilité dans la timeline patient.
4. Screenshots BEFORE/TARGET/AFTER sur écran effectivement implémenté, 200% zoom et focus/clavier, puis **Human Visual Approval explicite par le propriétaire sur le HEAD final**. Le workflow trusted refuse le SHA modifié comme prévu : NE PAS créer/apposer de faux label.
5. Exécuter FUE-I/G sur moteur **choisi et validé** ; les tests physiques appareil/TPM/second poste/coupure secteur appartiennent au LOT10 et restent NOT_RUN dans ce sous-lot.

**Batterie actuellement clôturée :** 77 backend + 18 React + Windows SUCCESS est une preuve de laboratoire du contrat SQLCipher, **pas** une validation d'un cabinet PostgreSQL ni une autorisation de migration. Les certificats Windows de test ne constituent pas une signature éditeur de production.

`READY_TO_MERGE=false` · `PRODUCT_READY=false` · `CLINICAL_GO=false` · `LOT10_PHYSICAL_VALIDATED=false`. PR #1210 DRAFT et non fusionnée. Aucun déploiement, aucune activation cabinet.


## PRE — B06-4B : PostgreSQL clone FUE / rollback invariants (2026-11-04)

**Current source** PR #1210 OPEN/DRAFT, HEAD `169a608d3b0fb9c90407d3ee0efc6464b5dc2e57`. [B06 #41925461995](https://github.com/hraaaaf/Digital_crown/actions/runs/41925461995) 3/3 SUCCESS (77 backend / 18 React / Windows). Same-HEAD Portability Runtime, CB-02, 03K/L, 03M SUCCESS. Independent B03 Windows [#41925470235](https://github.com/hraaaaf/Digital_crown/actions/runs/41925470235) FAILURE during synthetic spool seed `DC06B03_SYNTHETIC_REAL_SPOOL_SEED_FAILED`; this is an outstanding regression/runner reliability signal, not an authorized waiver. Human Visual Approval FAILURE remains deliberate gate.

**GOAL:** test the documented on-prem PostgreSQL engine as a **disposable CI service/clone only** for the unchanged B06 receipt/audit/outbox layout, primary/unique constraints, append-only enforcement, transaction rollback/replay, and verify the current product durable service still REFUSES PostgreSQL. Convert findings into a concrete, operator-approval-required PostgreSQL migration/adapter contract. Reuse existing Media Core primitives and minimize parallel code. No actual cabinet database, no patient data, no migration Alembic in this pass, no product PostgreSQL enablement, no claim of integrated PG ClinicalAsset or clinical release.

**REQUIRED safety:** sandbox must be synthetic, loopback-only and fail closed without exact test env; no runtime DDL/automatic fallback; no approval of PostgreSQL backend or schema silently. If tests expose a mismatch, mark the PG contract OPEN rather than assert parity. `READY_TO_MERGE=false`, `PRODUCT_READY=false`, `CLINICAL_GO=false`.


## POST — B06-4B : contrat PostgreSQL 18 certifié sur clone synthétique CI (2026-11-04)

**HEAD code** `bd1344db50804755f632b9193b46020bc0a19d3f`; [GitHub run #41927177139](https://github.com/hraaaaf/Digital_crown/actions/runs/41927177139) **3/3 jobs SUCCESS** :
- Backend produit/SQLCipher **77/77 PASS**, mêmes HTTP/JWT/ClinicalAsset/ACK/FUE LAB qu'au B06-4.
- **PostgreSQL 18 jetable 4/4 PASS** via `isolated_fue_lot06c/test_b06_postgres_clone_contract_v15.py` et un service PostgreSQL Actions `dc06_b06_ci` à compte `dc06_synthetic` et schéma éphémère distinct par test. Preuves de logs : `DC06_B06_4B_PG18_CLONE_ATOMIC_ROLLBACK_AND_3_UNIQUE_KEYS_PASS`, `DC06_B06_4B_PG18_CLONE_APPEND_ONLY_UPDATE_DELETE_TRUNCATE_DENIED_PASS`, `DC06_B06_4B_PG18_CLONE_CONCURRENT_CAPTURE_SINGLE_BUNDLE_PASS`, `DC06_B06_4B_REAL_PG_SERVICE_PRODUCT_FAIL_CLOSED_ZERO_WRITES_PASS`.
- React **18/18 PASS** et Windows SCM/LocalService, AES spool + Authenticode package **SUCCESS**.
- Rejets SQL PostgreSQL `duplicate key`, `DC06_B06_LEDGER_IMMUTABLE` et `PRAGMA` incompatibles, observés dans les logs d'un test négatif, sont **attendus et assertés**. Le PG test valide la structure et la concurrence, pas une insertion produit dans PostgreSQL.

**Périmètre réellement testé.** Le même ensemble de descripteurs SQLAlchemy `receipts/audit/outbox` se crée dans un **schéma PG de laboratoire**, avec 9 triggers temporaires anti-UPDATE/DELETE/TRUNCATE. Le test vérifie :
1. rollback transac complet `0/0/0`, puis insertion `1/1/1` ;
2. unicité `(tenant,station,capture)`, `asset_id` et `receipt_id` malgré tentatives de double insertion ;
3. interdiction effective d'`UPDATE`, `DELETE`, `TRUNCATE` sur les trois tables ;
4. concurrence deux writers : **un et un seul bundle** stocké ;
5. service produit `is_committed`/`receipt_for`/`commit_capture` sur vrai engine PG => `DURABLE_SQLCIPHER_REQUIRED`, zéro écriture de tables B06.
Le garde `_guarded_ci_dsn()` exige les trois indicateurs TEST/isolated/PG-LAB et une URL strictement identifiée au compte, base et hôte loopback. Aucune donnée de cabinet n'est appelée ; une CI verte ne démontre ni réelle migration PostgreSQL ni durabilité après panne secteur.

**Limites critiques restant OPEN :** cette fixture ne crée pas `ClinicalAsset`, patients ni utilisateurs dans PostgreSQL ; elle **n'est pas** un adaptateur de publication PG ni une migration Alembic. Les références `asset_id` et `staff/patient` n'ont **pas encore** de FK certifiées PG sur ce candidat, la signature ACK `0` est volontairement synthétique, aucune écriture AES-GCM/Media Core via PostgreSQL et aucun nouveau boot cabinet validé. Un utilisateur privilégié PG pourrait supprimer ces triggers ; ce test démontre la protection SQL normale, pas une immutabilité face à un superuser. Concurrence simple, pas de preuve de crash/process kill/PITR/WAL replay/restore.

**Décision recommandée :** avant de construire/activer un backend clinique PG, confirmer en lecture seule le moteur courant du cabinet et approuver une proposition LOT04/DB : schéma versionné avec FK et contraintes, migrations additives, autorité et locking `SELECT FOR UPDATE`/advisory ou gestion d'unicité, sauvegarde/restauration DB+médias sur clone, clés et ACK signés et révocation, et preuve HTTP/JWT + staff+patient+ClinicalAsset sur **même transaction PG**. Ne pas migrer toute la base à SQLCipher juste pour B06 sans décision distincte. Les migrations cabinet, merges, déploiements, connexion scanner et validation visuelle restent interdits sans autorisation correspondante. L'indépendant Windows B03 `#41925470235` présente un échec antérieur à la seed spool synthétique ; cela reste un risque de fiabilité séparé, bien que le Windows **B06 exact-HEAD** soit GREEN.

**Next : B06-4C — architecture du véritable adaptateur PG et protocole rehearsal sur copie isolée, puis B06-5/5 produit/UX après approbation.** Le `Human Visual Approval` est toujours un gate humain non approuvé ; ne jamais le contourner. Les essais physiques restent LOT10.

`READY_TO_MERGE=false` · `PRODUCT_READY=false` · `CLINICAL_GO=false` · `LOT10_PHYSICAL_VALIDATED=false`.

## POST B06-4B (2026-11-04)

CI [#41927177139](https://github.com/hraaaaf/Digital_crown/actions/runs/41927177139): 77/77 SQLCipher, 4/4 PostgreSQL 18.6 ephemeral, 18/18 React, Windows SUCCESS. Ledger-only synthetic FUE; PostgreSQL product/clinical go BLOCKED. No merge, deployment, migration or cabinet changes. `READY_TO_MERGE=false`, `PRODUCT_READY=false`, `CLINICAL_GO=false`.


## PRE B06-4C — PostgreSQL real-ORM synthetic product-route rehearsal, 2026-11-04

**Current HEAD** `b0a13b0fe97c678539cadb4ba4af9b398888bc44`; [B06 #41928205095](https://github.com/hraaaaf/Digital_crown/actions/runs/41928205095) = 3/3 SUCCESS, backend SQLCipher 77 PASS + PostgreSQL ledger-only 4 PASS, React 18 PASS, Windows SUCCESS. Independent B03 and Portability SUCCESS. Human Visual Approval FAILURE expected (no human visual sign-off). PR #1210 DRAFT.

**Goal:** prove, on disposable PostgreSQL 18 and synthetic actual ORM models, that authenticated product review + station + staff + patient two markers can persist AES-GCM ClinicalAsset + signed durable ACK + audit + outbox in one PostgreSQL transaction, with failpoints, recovery, denial and concurrent duplicate guards. Prototype the PostgreSQL transaction adapter **inside an isolated test module only**, injected by the lab fixture into the actual FastAPI route; leave SQLCipher-only product implementation and real cabinet/boot unchanged until architecture/migration authorization. Do not silently choose a cabinet engine. Continue to enforce the PostgreSQL production refusal established in B06-4B. Tests must distinguish product-route logic from authorized production PostgreSQL persistence.

**Required FUE:** actual Postgres backend, JWT + workstation cookie + secondary patient markers, signed ACK verified against C2 encrypted bytes and ClinicalAsset timeline query, rollback 0/0/0/0, replay/recovery/negative tenant and tamper, and honest recorded gaps (role privileges, DB media restore, real device and human UI). Never access clinic DB, patient data, installer, deployment, migration or merge. `READY_TO_MERGE=false`; `PRODUCT_READY=false`; `CLINICAL_GO=false`.


## POST B06-4C — PostgreSQL real-ORM HTTP synthetic integration (2026-11-05 UTC)

**Verdict: B06-4C = GREEN LAB (test-only candidate); PostgreSQL product/cabinet = OPEN / NO-GO.**
Code HEAD `c9551e0a9fd73b34033d40164f4f91e93b30917b`, [B06 exact-HEAD #41938330812](https://github.com/hraaaaf/Digital_crown/actions/runs/41938330812) **3/3 SUCCESS**:
- SQLCipher backend product/HTTP regression **77/77 PASS**;
- PostgreSQL 18.6 lab ledger B06-4B **4/4 PASS**;
- **NEW PostgreSQL B06-4C 4/4 PASS** in `isolated_fue_lot06c/test_b06_postgres_product_route_lab_v15.py`, using the genuine authenticated FastAPI route and actual SQLAlchemy User/Patient/WorkstationMode/RevokedToken/ClinicalAsset tables inside the CI disposable schema;
- React **18/18 PASS**; Windows SCM/LocalService/AES + Authenticode package SUCCESS.
- Independently on same code SHA: B03 Windows [#41938337690](https://github.com/hraaaaf/Digital_crown/actions/runs/41938337690), Portability [#41938337637](https://github.com/hraaaaf/Digital_crown/actions/runs/41938337637), CB-02 [#41938337628](https://github.com/hraaaaf/Digital_crown/actions/runs/41938337628), 03K/L [#41938337731](https://github.com/hraaaaf/Digital_crown/actions/runs/41938337731), 03M [#41938337629](https://github.com/hraaaaf/Digital_crown/actions/runs/41938337629) SUCCESS. `UI Human Visual Approval` [#41938333306](https://github.com/hraaaaf/Digital_crown/actions/runs/41938333306) FAILURE, gate humain strict non approuvé.

**New evidence FUE-I/G:** `DC06_B06_4C_PG18_REAL_HTTP_JWT_STATION_PATIENT_SIGNED_C2_TIMELINE_RESTART_PASS` confirms JWT auth, workstation cookie, two patient markers, actual PostgreSQL ClinicalAsset AES-GCM bytes, Ed25519 signed ACK, audit and outbox, visibility in the existing MediaCore timeline query, recovery after volatile review/native bridge restart, negative unbound patient/digest paths, 1/1/1/1 rows. `DC06_B06_4C_PG18_ASSET_LEDGER_AUDIT_OUTBOX_ROLLBACK_PASS` for failpoints after asset, after receipt, after audit confirms **0/0/0/0** committed rows on failed transaction and successful retry **1/1/1/1**. A partially-written encrypted orphan blob can remain after DB rollback (existing C2 contract), never a patient-linked DB asset/ACK. B06-4B independently proves ordinary DB conflict and append-only DML/DDL-TRUNCATE denials.

**Honest debugging record:** first B06-4C run [#41937924265](https://github.com/hraaaaf/Digital_crown/actions/runs/41937924265) failed because lab PostgreSQL fixture omitted `revoked_tokens`, causing JWT 401 before workstation guard; this was a **test fixture problem**, not acceptable evidence that the station was denied. Final code restored the real auth table in synthetic fixture, and four PostgreSQL HTTP FUE passed on code HEAD. No security gate was relaxed.

**Guardrails:** the PG adapter lives **only** in `isolated_fue_lot06c/b06_postgres_product_candidate_lab.py` and is monkeypatched into genuine HTTP route by synthetic test. Real product `backend/services/imaging_acquisition_durable_v15.py` remains SQLCipher-only, PostgreSQL refused with zero writes. No `backend/main.py`, Alembic, real DB, patient data, deploy, merge, physical scanner or operating-system trust activation. PG schema has lab-only composite FK (tenant/patient/asset) and anti-mutation triggers; user/database account is fixture owner, not demonstrated least-privilege. This was a brand-new empty synthetic PG schema **not** a cabinet dump/restore. A test does not certify long-term power-cut recovery, background outbox delivery, key rotation/revocation, PostgreSQL production migration, DBA-proof immutability, multiple worker concurrency for the *product candidate*, UI appearance or human authorization.

**Next B06-4D (OPEN product architecture) before B06-5/5:** read-only true cabinet engine inventory, explicit LOT04/owner selection and additive Alembic SQL schema + separate DB roles; restore DB AND media on representative isolated clone, signer rotation/backup, multi-worker stale authority and crash/ACK recovery, then qualified visual BEFORE/TARGET/AFTER screenshots, 200% zoom/keyboard/focus and explicit owner approval on exact HEAD. LOT10 hardware physical remains separate. Never label a lab candidate installable.

`READY_TO_MERGE=false` · `PRODUCT_READY=false` · `CLINICAL_GO=false` · `LOT10_PHYSICAL_VALIDATED=false`.


## PRE B06-4D — adversarial architecture and no-product PG review, 2026-11-05

**Verified exact baseline:** PR #1210 OPEN/DRAFT, branch `feat/lot06-phase2-b06-product-integration-20261104`, original B06-4C POST HEAD `243d23e9bbe925d27ba5af3681565a078f001284`; B06 workflow [#41939323313](https://github.com/hraaaaf/Digital_crown/actions/runs/41939323313) COMPLETED/SUCCESS, 3/3 jobs (Linux SQLCipher/PostgreSQL CI lab, React, Windows SCM/Authenticode). Candidate PostgreSQL adapter stays in `isolated_fue_lot06c/` and is not product-activated.

**Goal/Success/Proof:** review B06-4C and design an approvable B06-4D architecture decision, with tests for cross-tenant and stale authorizations, SQL-role separation, transaction/ciphertext orphan cases, crashes, concurrent replay, DB+media restore, signer rotation and human visual workflow. Record verified evidence and explicit UNKNOWN/HUMAN_GATE_REQUIRED, without asserting an actual cabinet clone or clinical readiness.

**Boundaries:** no real patient/cabinet access, migrations, Alembic, PostgreSQL product adapter, real hardware, merge, deployment, human approval simulation or forced DB engine choice. `READY_TO_MERGE=false`; `PRODUCT_READY=false`; `CLINICAL_GO=false`; `LOT10_PHYSICAL_VALIDATED=false`.


## POST B06-4D-A — five PG signed-ACK recovery adversarial FUE, 2026-11-05

**Exact code HEAD** `d1f0a4d623ab4c5da0323d3db33acc92bf1bda34` on [PR #1210 OPEN/DRAFT](https://github.com/hraaaaf/Digital_crown/pull/1210). [B06 run #41993779747](https://github.com/hraaaaf/Digital_crown/actions/runs/41993779747) COMPLETED/SUCCESS **3/3 jobs**, log-inspected: SQLCipher 77/77 PASS; disposable PG ledger B06-4B 4/4 PASS; B06-4C + B06-4D adversarial PG HTTP/ORM **9/9 PASS**, 5 new cases `DC06_B06_4D_PG18_ACK_RECOVERY_ADVERSARIAL_DENIED_PASS` for encrypted blob corruption, missing encrypted blob, changed workstation cookie, missing bearer, and staff revoked after commit; React 18/18 PASS; Windows SCM and Authenticode SUCCESS. The new tests ensure no signed ACK is returned when its encrypted media or current authorization proof is absent, and the four DB records remain 1/1/1/1 (no duplicate/mutation). **Laboratory-only**, real human typing and cabinet activation not inferred.

**Architecture risk review (not implementation approval):**
- **MAJOR — Cross-resource atomicity / recovery:** PostgreSQL atomically commits ClinicalAsset, receipt, audit and outbox, but AES-GCM ciphertext is written to a separate filesystem before the DB commit. An encrypted orphan may remain after DB rollback. Need scoped orphan reconciliation, durability and isolated DB+media backup/restore proving referential consistency after process crash/power loss. The new tests cover *post-commit* missing/corrupt blobs; they do not prove crash-safe filesystem+DB coordination.
- **MAJOR — Privilege and schema trust:** the synthetic PostgreSQL service runs as fixture owner; no separate runtime/migrator database principals or demonstrated least-privilege. `_lab_schema` checks expected trigger/FK names, not complete definitions/privilege matrix. No DBA-proof append-only or RLS/tenant boundary certification. Additive Alembic migration and role matrix remain human/LOT04-gated.
- **MAJOR — Key lifecycle:** current Ed25519 `_signer()` derives its key from current `CABINET_MASTER_KEY_HEX` (no verified historical key-ID/rotation path). Existing ACK recovery after key rotation, media key rotation, encrypted backup of keys and signer revocation are **NOT_RUN**. Do not confuse one-key 9/9 synthetic success with long-term recoverability.
- **HUMAN_GATE_REQUIRED — Actual cabinet target/UX:** V1 cabinet compatibility record identifies local PostgreSQL 18.2 at historical audit; current installed engine not re-inventoried. No fresh representative *isolated* cabinet clone, real Windows visual BEFORE/TARGET/AFTER, keyboard/200% zoom, clinician approval, device LOT10 physical test, outbox consumption, product multi-worker authority race or power-cut FUE. LOT06-N architecture D approval is DESIGN-ONLY and does not authorize PostgreSQL production activation.

**Recommended conditional design (proposal, not GO):** retain existing local PostgreSQL architecture *if read-only current inventory confirms it*, rather than migrate all patient records to SQLCipher solely for B06. Prepare an explicit LOT04/operator-reviewed additive schema proposal with separate runtime/migration roles and composite patient/tenant FK, durable encrypted-media reconciliation and DB+media restore, key versioning/history, process crash/multiworker replay, and visual human release protocol. No silent engine switch.

**Gate:** `B06-4D-A_ADVERSARIAL_FUE=GREEN_LAB`; **B06-4D PRODUCT ARCHITECTURE = OPEN / NO-GO**. `READY_TO_MERGE=false`; `PRODUCT_READY=false`; `CLINICAL_GO=false`; `LOT10_PHYSICAL_VALIDATED=false`. No product adapter, Alembic, cabinet access, patient data, merge or deployment touched. **Next exact:** request explicit owner/LOT04 approval of target engine and role/key schema plan, then run a controlled synthetic rehearsal and *separately approved* representative isolated clone; complete FUE-I/G UI human gate before B06-5/5.


## PRE B06-4D-B — PostgreSQL roles, key lifecycle & backup architecture lab, 2026-11-05

**Verified baseline:** PR #1210 OPEN/DRAFT HEAD `d146217457c1f408c4e37db469c89c90b0b471ee`; exact-HEAD B06 workflow [#41994376088](https://github.com/hraaaaf/Digital_crown/actions/runs/41994376088) COMPLETED/SUCCESS 3/3 jobs. The current product still enforces SQLCipher-only and the PostgreSQL candidate is test-only.

**Goal:** on a strictly pinned PostgreSQL 18 disposable laboratory schema, validate *separate* least-privileged runtime/migrator DB roles with explicit negative privilege FUE, and demonstrate existing one-master-key ACK recovery behavior under synthetic rotation/restoration; prepare a conditional ADR for DB engine, SQL schema, media backup, key rotation and rollback, not an approval.

**Success criteria:** runtime role cannot ALTER/CREATE/UPDATE/DELETE/TRUNCATE protected ledger, cannot elevate ownership, while read and intended insert grants are documented; migration role remains distinct and never used by product; PostgreSQL tests and existing SQLCipher, React and Windows tests remain green on exact code SHA. Rotated-key negative FUE must fail closed and re-use of original test key must restore synthetic ACK; absence of a versioned historical keyring remains a documented MAJOR, not declared solved.

**Restrictions:** test module, ADR and CI only; no real cabinet access, clinic patient data, schema migrations/Alembic, actual role creation outside disposable CI, production keyring, activation, merge or deploy. Do not silently choose PostgreSQL for the cabinet. `READY_TO_MERGE=false` / `PRODUCT_READY=false` / `CLINICAL_GO=false` / `LOT10_PHYSICAL_VALIDATED=false`.


## POST B06-4D-B — PostgreSQL role separation and key rotation negative FUE, 2026-11-05

**Exact code HEAD** `c6b45519f4ca1ffac13103f46b598430614b5207`, PR [#1210 OPEN/DRAFT](https://github.com/hraaaaf/Digital_crown/pull/1210). [LOT06 B06 run #41996690105](https://github.com/hraaaaf/Digital_crown/actions/runs/41996690105) **COMPLETED/SUCCESS 3/3 jobs**. Actual Linux CI logs inspected: SQLCipher **77/77 PASS**, PostgreSQL B06-4B schema **4/4 PASS**, B06-4C/B06-4D FastAPI/ORM PG **11/11 PASS** (9 prior + 2 B06-4D-B), React **18/18 PASS**, actual Windows SCM/AES spool and Authenticode **SUCCESS**. GitHub CI Scope Gate on this code SHA SUCCESS.

**New exact lab FUE proof** in `isolated_fue_lot06c/test_b06_postgres_product_route_lab_v15.py`:
- `DC06_B06_4DB_PG18_SEPARATE_ROLES_RUNTIME_DDL_DML_DENIED_PASS`: two unique schema-local test `NOLOGIN` PostgreSQL roles (runtime, migrator) created/removed within the disposable `dc06_b06_ci` database. `SET LOCAL ROLE` proves runtime can SELECT and is configured for INSERT on ClinicalAsset/receipt/audit/outbox; cannot CREATE, ALTER, UPDATE, DELETE or TRUNCATE receipt/audit/outbox; PostgreSQL `42501 permission denied`/`must be owner` observed (not only protection via owner triggers). Separate migrator may CREATE and DROP an isolated smoke table. All four patient/receipt/audit/outbox rows stay 1/1/1/1. Roles have **not** been tested using different client logins/credentials or the actual product writer under least privilege.
- `DC06_B06_4DB_PG18_UNVERSIONED_KEY_ROTATION_FAIL_CLOSED_PASS`: synthetic exact-key replacement causes previously signed ACK retrieval to refuse HTTP 409, with zero DB mutation; restoring the prior synthetic key re-enables the exact same signed ACK and encrypted media. **This is a negative current-state proof, NOT a versioned keyring, NOT key rotation support.**

### ADR B06-4D-B — conditional architecture proposal, HUMAN GATE OPEN

**Engine:** the historical on-prem cabinet inventory indicates PostgreSQL 18.2 locally. This is *not* a fresh on-prem engine inventory. Recommend an additive PostgreSQL option over wholesale conversion of patient data to SQLCipher **only after LOT04 and product-owner approval of actual engine/scope**. Current `backend/services/imaging_acquisition_durable_v15.py` keeps PostgreSQL refused; test adapter stays exclusively in isolated fixtures. LOT06-N architecture D approval is DESIGN-ONLY and must not be repurposed as this PostgreSQL GO.

**Privileges and schema:** a distinct migrator/owner performs explicit reviewed additive schema changes; application DB role is non-owner, cannot change/erase ledger history, and gets only justified DML, sequence, auth and asset privileges. Verify PostgreSQL login under an actual least-privileged service principal, `PUBLIC` and inherited grants, FK composite tenant/patient/asset and audit/outbox-to-receipt constraints, indexes, trigger definitions and uniqueness. Do not rely on owner-created triggers as DBA-resistant tamper proof or on name-only trigger attestation. Role creation, DDL and `SET LOCAL ROLE` in this pass are *strictly in the disposable CI database*, not product.

**Keys and media:** existing `CABINET_MASTER_KEY_HEX` feeds derivation for both AES-GCM media and Ed25519 ACK signer. Before any real rotation, propose distinct purpose keys with versioned key identifiers, authenticated historical verification public keys, protected access to old media decryption keys and approved revocation/rewrap/rollback. A blob write on separate filesystem is not atomic with PostgreSQL commit: ensure no clinical ACK without verified bytes, safely reconcile encrypted orphan blobs without unapproved deletion, and test crash durability.

**Backup/restore:** plan an operator-approved consistent capture of DB + media tree + cryptographic metadata/key escrow, with hashes, fixed ingestion boundary and isolated restore verifying ClinicalAsset links, key versions, signed ACK, tenant isolation and replays. PostgreSQL `pg_dump` is a DB snapshot and by itself does not preserve external media or cluster-wide roles; role provisioning/restore must be included. **NO cabinet clone run in this pass.**

**Primary technical sources checked 2026-11-05:** [PostgreSQL 18 Privileges](https://www.postgresql.org/docs/18/ddl-priv.html), [GRANT](https://www.postgresql.org/docs/18/sql-grant.html), [SET ROLE](https://www.postgresql.org/docs/18/sql-set-role.html), [SQL Dump/restore](https://www.postgresql.org/docs/18/backup-dump.html). These support mechanics, not approval of Digital Crown implementation.

**Result/gates:** `B06-4D-B_FUE=GREEN_LAB` with 2/2 new targeted FUE; `B06-4D_PRODUCT_ARCHITECTURE=HUMAN_GATE_REQUIRED`; `READY_TO_MERGE=false`, `PRODUCT_READY=false`, `CLINICAL_GO=false`, `LOT10_PHYSICAL_VALIDATED=false`. No actual patient, cabinet, Alembic migration, product PostgreSQL enablement, merge, deploy or hardware integration.

**Next exact B06-4D-C (OPEN, future safe scope):** actual separate-login low-privilege PostgreSQL service and restore of a **synthetic** DB+encrypted-media bundle, with negative tenant, crash, backup and replay FUE; only after a separate explicit LOT04/owner gate consider representative isolated cabinet clone + visual/human FUE and B06-5/5. No release GO is inherited from these lab results.


## PRE B06-4D-C — real separate LOGIN roles and synthetic DB+AES media restore FUE, 2026-11-05

**Verified baseline:** PR #1210 OPEN/DRAFT exact HEAD \`98906ca3d02c92625dca7a43a1a2ef21ebfd7a0e\`; [same-HEAD B06 CI #41997290142](https://github.com/hraaaaf/Digital_crown/actions/runs/41997290142) COMPLETED/SUCCESS 3/3; [Human Visual Approval #41997293479](https://github.com/hraaaaf/Digital_crown/actions/runs/41997293479) COMPLETED/FAILURE (legitimate human gate). Product PG is still closed and the B06-4D-B privileged role-switch evidence is GREEN LAB, not true client-login evidence.

**Goal:** only inside the strict GitHub-hosted Docker PostgreSQL 18 laboratory service \`dc06_b06_ci\` at \`127.0.0.1:5432\`, create genuinely distinct password-authenticated LOGIN runtime and migrator roles with isolated schema-limited privileges and demonstrate a real runtime client login executing authenticated synthetic capture writer/ACK while schema mutation and historical ledger DML fail. Separately perform a matched PostgreSQL dump/restore and AES-GCM media bundle recovery for a fully synthetic capture; reject bad backup/missing file/bad key, verify same signed ACK, no duplicate and patient boundary after restoration. In case PG 18 dump tools are unavailable, report explicit PARTIAL rather than pretending an application row replay proves physical PG backup.

**Evidence criteria:** exact source SHA and Linux job logs with per-FUE markers, at least one real \`session_user=current_user=non-owner LOGIN\` socket/authenticated connection through the actual lab candidate FastAPI writer, and PostgreSQL 18 \`pg_dump\` + \`pg_restore\` from the *disposable GitHub runner service* with AES-GCM bytes + SHA-256 recovery after stop/restart; preserve 1/1/1/1 DB rows, typed patient confirm, reject unauthorized scope. Distinguish synthetic graceful restore from a true power cut.

**Immutable boundaries:** change only \`isolated_fue_lot06c/\` test harness/candidate and this single canonical GitHub document; no production code, real cabinet connection, patient data, product PostgreSQL activation, Alembic, installer, actual key rotation, merge, deployment or human approval forgery. Keep exact host/db/flags pin, clean up ephemeral roles/schema and media, never relax real product SQLCipher fail-closed. \`READY_TO_MERGE=false\`; \`PRODUCT_READY=false\`; \`CLINICAL_GO=false\`; \`LOT10_PHYSICAL_VALIDATED=false\`.


## POST B06-4D-C — restricted PG18 LOGIN + true pg_dump/restore with synthetic encrypted media, 2026-11-05

**Exact code HEAD:** \`9edc3c91a19eb22264f6b368b2c7c8feebb4e90c\`, [PR #1210 DRAFT/unmerged](https://github.com/hraaaaf/Digital_crown/pull/1210). [B06 workflow #42001241125](https://github.com/hraaaaf/Digital_crown/actions/runs/42001241125) **COMPLETED/SUCCESS 3/3 jobs**, inspected actual Linux job logs: SQLCipher 77/77 PASS; PostgreSQL 18.6 ledger 4/4 PASS; PostgreSQL actual FastAPI/JWT/SQLAlchemy candidate 13/13 PASS (11 existing + 2 B06-4D-C); React 18/18 PASS; Windows SCM/LocalService and Authenticode success. Logs explicitly contain \`DC06_B06_4DC_PG18_SEPARATE_PASSWORD_LOGIN_REAL_WRITER_PASS\` and \`DC06_B06_4DC_PG18_PGDUMP_MEDIA_RESTORE_SIGNED_ACK_PASS\`.

**FUE #1 — actual, distinct PostgreSQL LOGIN roles (NOT impersonated SET ROLE):** exclusively in disposable \`dc06_b06_ci\` localhost GitHub PostgreSQL service, derive two ephemeral role names and generated test-only passwords from the isolated per-test schema. Establish separate physical password-authenticated PG connections with \`session_user=current_user=runtime\` and \`session_user=current_user=migrator\`, explicitly verify role is non-superuser, no CREATEROLE/CREATEDB, and has no schema CREATE permission. Route the **real FastAPI JWT/workstation/two-marker capture commit test** through the runtime connection to the test-only PostgreSQL adapter; ClinicalAsset AES-GCM, receipt, audit and outbox commit 1/1/1/1; idempotent signed ACK read and wrong-patient refusal. On this socket PostgreSQL 42501 denies runtime CREATE/ALTER, receipt UPDATE, audit DELETE, outbox TRUNCATE and ClinicalAsset patient reassignment; separate migrator socket can create/drop its own synthetic smoke table. Both test roles are dropped at teardown. **New detail surfaced by genuine ORM:** ClinicalAsset's INSERT + storage UPDATE automatically updates \`updated_at\`, so runtime requires tightly scoped UPDATE on only \`sha256, byte_size, storage_key, storage_format, stored_at, updated_at\`; no UPDATE grants on the immutable receipt/audit/outbox tables or patient/tenant/staff/provenance fields.

**FUE #2 — genuine PG18 dump/restore + encrypted media:** a synthetic signed ACK and AES-GCM ClinicalAsset are created, actual PostgreSQL 18 \`pg_dump -Fc -n <ephemeral-schema>\` runs inside the GitHub CI container, and an encrypted-media directory is copied with SHA-256 manifest. Verify a tampered DB archive is rejected before destructive recovery; deliberately remove disposable schema and media, then \`pg_restore --exit-on-error\` into the same synthetic disposable DB with table/trigger/FK data. The restored DB has original 1/1/1/1 records, but ACK recovery **correctly returns HTTP 409** until matching ciphertext is restored. Copy media back, verify ciphertext fingerprint and original decrypted bytes, then HTTP GET retrieves the **identical signed ACK** twice without duplication; wrong patient remains refused. This is a real PostgreSQL logical restore of a purely synthetic single-schema dataset, **not** an on-prem backup validation, physical crash test, or encrypted transport/off-host escrow.

**Preserved red test and diagnosis:** [run #42000568391](https://github.com/hraaaaf/Digital_crown/actions/runs/42000568391) FAILURE on code \`616444f\`: 77/77 SQLCipher, 4/4 PG ledger, **11/12 PG HTTP**, React and Windows SUCCESS; real restricted-role writer correctly received PG permission denied on ORM-generated \`updated_at\` UPDATE and returned HTTP 503. Minimal test-only grant correction at [\`9edc3c9\`](https://github.com/hraaaaf/Digital_crown/commit/9edc3c91a19eb22264f6b368b2c7c8feebb4e90c) made 13/13 PG FUE green without granting wider ledger or patient mutation rights. This was an incomplete lab grants matrix, not a product relaxation; first red evidence retained.

**Architecture gates still OPEN / MAJOR:**
- These privileges and SQL role creations are only in the ephemeral lab, no actual cabinet installation, production grants, Alembic, or product PostgreSQL writer. The permitted ClinicalAsset storage-column updates are not backed by demonstrated PostgreSQL row-level tenant policies; ORM/service guards enforce scope, but malicious direct SQL cross-tenant storage-column mutation remains a design/security review item. A migrator/owner can still bypass runtime append-only constraints; database-owner/DBA-proof immutability has not been claimed.
- The archive's media/key manifest does **not** implement protected key escrow, a versioned keyring, a coordinated online snapshot, multiworker crash/power-cut durability, external backup rotation, consumer outbox delivery or a representative cabinet clone restore. A single synthetic same-host tidy recovery must not be misrepresented as production disaster recovery.
- The existing \`CABINET_MASTER_KEY_HEX\` supplies current AES-GCM/Ed25519 derived material and historical rotation is still unsupported. Future B06-4D-D should prove versioned historical verification/re-encryption after key change, safe backups and release-approved revocation/restore. Native SCM/product IPC still test-only; no genuine scanner, approved publisher/TPM or Human Visual Approval.

**Verdict:** \`B06-4D-C_SYNTHETIC_RESTRICTED_LOGIN_AND_PG_DUMP_RESTORE=GREEN_LAB\`; \`B06-4D_PRODUCT_ARCHITECTURE=OPEN\`; \`READY_TO_MERGE=false\`; \`PRODUCT_READY=false\`; \`CLINICAL_GO=false\`; \`LOT10_PHYSICAL_VALIDATED=false\`. No clinic connection, patient data, Alembic, product adapter activation, merge, deployment or installer. **Next exact:** B06-4D-D historical versioned keys and controlled DB+media+key restore on disposable synthetic fixture, PLUS formal owner/LOT04 architecture decision and separately authorized representative isolated clone, prior to B06-5/5 and human visual FUE-G.


## PRE B06-4D-D — historical key retention and cryptographic recovery, 2026-11-05

**Verified baseline:** PR #1210 DRAFT, HEAD `11a0df02811d02bc7cbe49faecf25341a5861340`; B06 same-HEAD [run #42001948276](https://github.com/hraaaaf/Digital_crown/actions/runs/42001948276) SUCCESS 3/3 with B06-4D-C real login and pg_dump/media recovery; Human Visual Approval is still an intentionally failing human gate. The real media product uses unversioned `CABINET_MASTER_KEY_HEX` or `SECRET_KEY` with HKDF-derived AES-GCM/HMAC; Ed25519 receipt signing is likewise tied to the active key. A change of master key therefore must not be represented as automatically supporting historical decrypt/verify.

**B06-4D-D mission, lab-only:** add deterministic synthetic FUE proving that after master-key change old ciphertext/receipt fail closed; a wrong historical key does not restore them; explicit restoration of the matching historical key recovers exact original media and ACK without duplication; a separate versioned synthetic recovery manifest identifies key ID without embedding key material, and refuses absent/mismatched key versions, modified ciphertext or forged manifest. The test should distinguish *restoring a historical key in a disposable environment* from real production key rotation/re-encryption. No plaintext keys in logs, GitHub, Notion, or backup bundles.

**Limits:** no production keyring implementation or schema migration; no clinic or patient data; only `isolated_fue_lot06c/` tests and this one canonical GitHub document, with Notion PRE/POST; no Vercel, merge, cabinet or human signoff. Verdict pending exact-HEAD FUE logs. `READY_TO_MERGE=false`; `PRODUCT_READY=false`; `CLINICAL_GO=false`; `LOT10_PHYSICAL_VALIDATED=false`.

## POST (execution checkpoint, not certification) B06-4D-D — 2026-11-05

**Code SHA** `afccb1db691751ba699382b251905570f3ca23fd` added one six-case parametrized synthetic FUE to `isolated_fue_lot06c/test_b06_postgres_product_route_lab_v15.py`: missing historical key, wrong historical key, mismatched versioned key ID, modified authenticated manifest, altered AES-GCM ciphertext, and correct historical key restored with exact media and signed ACK HTTP replay. The lab-only recovery manifest binds the disposable database, tenant/patient, capture, storage locator, ciphertext SHA-256 and ACK digest, with independent ephemeral HMAC. It includes a **key identifier only**, no historical key material. The test deliberately verifies that after switching back to the new active key the old ACK is again unavailable: **this is not persistent multi-key product support or approved rotation**.

**CI state at checkpoint:** [run #42005105231](https://github.com/hraaaaf/Digital_crown/actions/runs/42005105231) for code SHA `afccb1d` is **PENDING** with no jobs assigned as observed; therefore **0/6 new B06-4D-D FUE have been certified**, no claim of GREEN. Historical B06-4D-C same-HEAD [run #42001948276](https://github.com/hraaaaf/Digital_crown/actions/runs/42001948276) remains SUCCESS 3/3, but does not certify these new tests. GitHub CI must be revisited and the exact HEAD logs read before upgrading this verdict.

**Remaining critical architecture gaps:** current product ciphertext and receipt are unversioned; no durable historical keyring, key escrow/retention policy, key ID in persisted ClinicalAsset, online re-encryption, coordinated DB/media/key backup, tenant RLS, representative cabinet clone, actual physical crash test, formal LOT04/owner signoff or human visual approval. The HMAC manifest is only an isolated FUE harness, not a deployable backup/restore design. `B06-4D-D=PENDING_CI`; `READY_TO_MERGE=false`; `PRODUCT_READY=false`; `CLINICAL_GO=false`; `LOT10_PHYSICAL_VALIDATED=false`. No cabinet access, migrations, production code, merge or deployment.

**Next:** recheck [B06 #42005105231](https://github.com/hraaaaf/Digital_crown/actions/runs/42005105231) and diagnose/fix failures test-only if any, then POST certify exact code SHA and documentary SHA separately. Architecture and clinical integration require explicit approvals.

## PRE B06-4D-E — architecture decision record only, 2026-11-05

Baseline checked on [PR #1210](https://github.com/hraaaaf/Digital_crown/pull/1210): DRAFT/unmerged, HEAD `9a08e19ede3306f529de17fb629f8f1f77394a8b`. [B06 run #42005263803](https://github.com/hraaaaf/Digital_crown/actions/runs/42005263803) completed SUCCESS 3/3, 77 SQLCipher, 4 PG contract, 19 PG HTTP/ORM including 6 historical-key laboratory cases. This certifies only the synthetic fixture. No product keyring exists.

**Scope B06-4D-E:** documentary ADR in this one canonical LOT06 file, with proposed key-versioning format, tenant isolation/RLS security boundary, crash-consistent DB+encrypted media+keys backup/restore threat model, approval ownership and explicit FUE acceptance matrix. **No code, schema, runtime, clinic, migration, merge, deployment or automatic architecture approval.** Confirm source reality against `backend/services/clinical_asset_storage.py`, `backend/services/imaging_acquisition_durable_v15.py`, `backend/models_media_core.py`, and isolated PostgreSQL fixtures. Verdict PENDING until POST and exact documentary HEAD CI.


## ADR B06-4D-E — historical key lifecycle, tenant authority and recoverable acquisition (PROPOSED / NOT APPROVED), 2026-11-05

**Decision status:** \`PROPOSED_HUMAN_GATE\`. This ADR is a design recommendation, not permission to migrate the cabinet or replace SQLCipher with PostgreSQL. Product invariants: local-first, zero LLM runtime, unassigned captures remain non-clinical until explicit authenticated staff/patient assignment, and acquisition must fail closed. The product source of truth remains \`backend/services/imaging_acquisition_durable_v15.py\` (SQLCipher-only); \`isolated_fue_lot06c/b06_postgres_product_candidate_lab.py\` is disposable-test-only.

### Evidence and actual gaps

1. \`backend/services/clinical_asset_storage.py\` currently derives AES-GCM and opaque tenant storage locators from the active \`CABINET_MASTER_KEY_HEX\` or \`SECRET_KEY\` via HKDF; format is \`DCM1\`/\`AESGCM_V1\`, with AAD binding tenant and digest. Locator validation recomputes the tenant token with the **current** key. Changing the active key changes both decryptability **and locator validation**. There is no persisted \`media_key_id\` or historical locator key version.
2. \`backend/services/imaging_acquisition_durable_v15.py\` derives Ed25519 signer from active \`CABINET_MASTER_KEY_HEX\`, with fixed \`dc06-b06-ack-v1\` signed payload and no persisted \`signing_key_id\`. Existing receipt ledger is append-only by SQLite triggers and PG test-only triggers, not DBA-proof WORM.
3. \`backend/models_media_core.py\` stores tenant-scoped \`ClinicalAsset\` metadata and \`AESGCM_V1\` format, but does not persist key version. Lab PG composite tenant/patient/asset FKs and restricted LOGIN were validated, **not** product schema/RLS. The lab recovery HMAC manifest is ephemeral and the old key was manually restored to the environment; it is not a durable or deployable keyring.
4. On exact documentary HEAD \`9a08e19ede3306f529de17fb629f8f1f77394a8b\`, [B06 run #42005263803](https://github.com/hraaaaf/Digital_crown/actions/runs/42005263803) SUCCESS 3/3: SQLCipher 77, PG contract 4, PG HTTP/ORM 19 (including 6 key-recovery negative/positive FUE), React and Windows success. **This supports laboratory feasibility only.**

### Decision proposal — three separate key purposes and explicit version binding

- **Separate cryptographic purposes:** \`media_aead_key_id\` for AES-GCM decryption; \`locator_hmac_key_id\` for opaque tenant path derivation; \`receipt_signing_key_id\` for Ed25519 verification. Use purpose-separated derivation with explicit domain labels and per-version key IDs. A new signing key must not silently change the media key or the locator; do not reuse raw master material as a data key. Verify existing \`DCM1\` and legacy receipt payloads via a strictly scoped legacy compatibility reader before any proposed \`DCM2\`/ACK-v2 write format.
- **Envelope design:** a new ciphertext header should authenticate \`format_version\`, \`media_key_id\`, nonce, tenant, digest, and asset binding as AEAD AAD; validate identifiers against an allowlisted, authenticated local key registry, not user input or unauthenticated file header. Persist key IDs with the ClinicalAsset metadata and receipt ledger as an **additive, separately reviewed** migration; consider historical immutable locator IDs rather than recomputing old paths from the current key. Reject unknown/retired-for-decrypt keys, mismatched tenant/patient, invalid signatures, missing ciphertext and mixed-version metadata with sanitized error. Do not allow legacy downgrade or signature algorithm substitution.
- **Historical verification vs decryption:** retain historical **public** Ed25519 verification keys for old receipts for the approved retention period; historical media decryption keys require protected escrow/backup and explicit access control. Signing private keys can be retired independently of public verification. Define states \`ACTIVE_WRITE\`, \`READ_ONLY_HISTORICAL\`, \`REVOKED\` with separate policy for compromised keys (a compromised key cannot be blindly trusted merely because its historical signature verifies). No automatic deletion of old decrypt keys while referenced ciphertext remains.
- **Rotation protocol (not implemented):** (1) inventory asset/receipt references per version; (2) generate and protect new purpose-specific keys; (3) dual-read/old-read and new-write only after an approved migration gate; (4) resumable tenant-scoped re-encryption with fresh nonce and atomic metadata pointer switch; (5) verify bytes, digests, tenant AAD, receipt signatures, audit and rollback; (6) retire historical decrypt keys only when zero live references and verified restore/retention policy permit. Never mutate an already signed receipt in place; use an append-only migration/attestation event if provenance requires it. Preserve old encrypted blobs until verified cutover and approved garbage collection. **No code activation under this ADR.**

### Backup/restore threat model — DB, ciphertext, registry and signing trust must travel together

| Threat / failure | Required control and acceptance evidence (not yet demonstrated) |
| --- | --- |
| DB snapshot at T1, ciphertext at T2 | Define an application-level consistent checkpoint or durable manifest of exact committed receipt IDs and blob digests; write-quiescence or snapshot protocol; FUE interleaved capture while snapshotting, then restore exactly committed captures only |
| Key registry lost while DB/media survive | Encrypted offline escrow of historical decrypt keys, public verify-key catalog, authenticated manifest and tested recovery under dual control; no plaintext keys in repo, CI logs, backup media or Notion |
| Partial disk write / crash / power loss | fsync/atomic rename semantics appropriate to OS/filesystem, crash fault injection before/after media publish, DB commit, outbox, restart reconciliation; no acknowledged receipt without recoverable authenticated media |
| Archive or manifest tampering, wrong tenant, rollback | Authenticated, versioned manifest with monotonic backup generation and anti-rollback anchor stored independently; check database identity, tenant scope, schema version, ciphertext SHA-256 and signature trust roots **before** destructive restore |
| Ransomware, theft, accidental deletion | Offline/off-host encrypted backups with separate access controls, immutable or write-protected copies, retention/rotation and restore rehearsals; local-first does not mean a single local backup |
| Lost or compromised active signing key | Historical public-key trust, key revocation procedure, audit and explicitly scoped compromise response; old signature validity does not prove a key was uncompromised |
| Recovery into wrong cabinet or environment | Cabinet-bound restore authorization, offline identity confirmation, schema and key fingerprint checks, clean disposable restore first; fail closed on mismatches |
| Restore succeeded but outbox not delivered | Idempotent replay of event delivery keyed by immutable receipt ID; prove no duplicate clinical attachment, audit or outbound event |
| Key recovery or backup under malicious local admin | Define trust boundary: database owner/OS admin may bypass application GRANT and local file ACL. Claims of tamper resistance require external trust anchor/off-host verification and owner threat-model approval |

**Restore gate:** validate archive and key manifest authenticity, destination identity, exact schema and media inventory; restore into an isolated scratch instance; verify ciphertext decryptability, historical ACK signatures and tenant/patient binding; compare manifest/ledger counts; test replay/idempotency; only then propose controlled cabinet restore with operator approval and rollback plan. Set explicit RPO/RTO **with owner**; none are evidenced or assumed here.

### PostgreSQL tenant isolation and role boundary (only if LOT04 approves PostgreSQL)

- Prefer a **single** supported local database engine chosen by a fresh LOT04 cabinet inventory; no dual-write SQLCipher/PG production path without a separately designed reconciliation protocol. SQLCipher-only remains the live B06 boundary.
- Separate runtime LOGIN from migrator/owner. Runtime must not have \`CREATEROLE\`, \`CREATEDB\`, schema \`CREATE\`, ledger UPDATE/DELETE/TRUNCATE, or permission to bypass RLS. Grant only necessary asset storage-column UPDATE (actual ORM currently touches \`updated_at\`); **do not mistake column-only UPDATE for row-level tenant isolation**.
- Proposed PostgreSQL \`ENABLE ROW LEVEL SECURITY\` plus \`FORCE ROW LEVEL SECURITY\` on relevant tenant-bearing tables, \`USING\` and \`WITH CHECK\` policies bound to a trusted per-transaction tenant context. Never trust arbitrary client-set session variables as sole authority: DB runtime identity, application-authenticated tenant claims and pool checkout/reset protocol require joint review. Explicitly test \`SET ROLE\`, direct SQL, connection pooling context leak, concurrent tenants, absent tenant context and privileged owner bypass.
- Enforce composite FK \`(tenant, patient, asset)\` and receipt/audit/outbox linkage, immutable ledger triggers and constrained role grants; test owner/migrator bypass and document it. No promise of DBA-proof immutability. Migration must be additive, rehearsed, reversible, checksum-pinned and independently approved; never auto-run Alembic from a request or device event.
- Preserve SQLCipher encryption/local media protections if PostgreSQL is not selected. PostgreSQL's ordinary server storage is **not** a drop-in substitute for SQLCipher at-rest encryption; require a separate at-rest and backup encryption decision.

### Explicit acceptance FUE matrix (future, not executed in this ADR)

| FUE | Success condition | Gate |
| --- | --- | --- |
| KEY-01 legacy read | Unchanged historical \`DCM1\` media and ACK-v1 verify under historical IDs after active-key switch; wrong key, missing ID, compromised/revoked key fail closed | Cryptography + LOT04 |
| KEY-02 versioned write | New media/receipt IDs authenticated in DB and envelope; no cross-version substitution, nonce reuse, AAD bypass, downgrade or signature confusion | Security review |
| KEY-03 rotation/restart | Crash at every re-encrypt phase; resume without orphaned active pointers or altered signed receipts; all old assets readable until approved retirement | Windows + storage |
| KEY-04 key loss | Missing historical decrypt key blocks only affected version, without exposing plaintext or silently rewriting metadata; controlled escrow restore restores exactly those assets | Owner + operator |
| BAK-01 coherent restore | Simultaneous synthetic DB/media/keys snapshot with concurrent captures; verified scratch restore exact ACK, no phantom or duplicate outbox | LOT04 + storage |
| BAK-02 hostile restore | Tampered manifest, stale backup, wrong cabinet, corrupted blob, absent escrow, rollback and power-loss tests fail closed with audit | Security + operator |
| TEN-01 direct SQL isolation | Two real restricted LOGIN connections and two tenants; read/insert/update/cross-tenant reassignment rejected by PG policies and FKs, including pooled context leaks | LOT04 + security |
| TEN-02 privileged threat | Owner/migrator bypass documented and operationally isolated; off-host evidence for any immutability guarantee | Owner |
| OPS-01 representative clone | Owner-authorized isolated cabinet clone, encrypted and scrubbed where appropriate, validated rollback/restore, approved RPO/RTO, no real patient exposure to CI | Owner + LOT04 |
| VIS-01 product and physical | Human Visual FUE-G and real hardware/Windows service/LOT10 physical validation; no automatic gate override | Human reviewer |

### Decision requests to owner and LOT04 (all OPEN)

1. **Engine:** keep product SQLCipher-only or approve additive PostgreSQL local architecture after current workstation inventory, storage-at-rest review and rollback plan? No engine migration authorized by this ADR.
2. **Key custody:** identify actual cabinet key store (OS DPAPI/TPM or equivalent, offline escrow), dual-control custodians, retention duration, emergency compromise procedure and authorized recovery operator. No hardcoded credentials.
3. **Tenant threat model:** one cabinet/tenant per local instance or multiple employers per database? Specify adversary including local administrator and operator access, then approve or reject PG RLS design.
4. **Operational recovery:** approve RPO/RTO, offline backup destination, retention/anti-rollback policy, physical test station and representative clone scope. Do not invent service guarantees.
5. **Release gate:** authorize a separate code implementation lot and independent security/clinical review only after above answers; keep PR #1210 Draft and clinical/physical/human gates NO-GO.

**ADR verdict:** \`B06-4D-E_ADR=DRAFT_FOR_HUMAN_DECISION\`; \`B06-4D-D_FUE=GREEN_LAB\`; \`KEYRING_PRODUCT_IMPLEMENTED=false\`; \`TENANT_RLS_VALIDATED=false\`; \`CONSISTENT_BACKUP_VALIDATED=false\`; \`LOT04_OWNER_APPROVAL=false\`; \`READY_TO_MERGE=false\`; \`PRODUCT_READY=false\`; \`CLINICAL_GO=false\`; \`LOT10_PHYSICAL_VALIDATED=false\`. **Next:** obtain explicit LOT04/owner architecture decisions; only then scope B06-4D-F versioned key implementation on disposable fixtures, with exact-SHA FUE and human gate preserved.


## PRE LOT04 architecture decision evidence pass — 2026-11-05

**Baseline:** PR #1210 Draft, HEAD `e74ce05922ec69655e50b0999be69575a8b88a16`, exact HEAD B06 CI #42006722273 SUCCESS 3/3; B06-4D-E ADR is proposed but NOT approved. The user's 'Go' authorizes a read-only architecture evidence pass and a recommendation, not a specific engine migration, cabinet inventory, cryptographic deployment, merge or human clinical approval. Inspect existing on-prem documentation and LOT04 closeout before a bounded POST. Single canonical GitHub file and Notion PRE/POST; no product code edits.

## POST LOT04 architecture evidence pass — 2026-11-05

**Read-only source reconciliation on exact PR HEAD \`27e53a0a82e71d00dfeae5d79253f4ac8816ebb1\`:**
- \`docs/CABINET_ONPREM_GUIDE.md\` explicitly supports \`ENVIRONMENT=cabinet\` solo SQLite/SQLCipher, isolated multi-PC S+A+B PostgreSQL FUE-G, and \`ENVIRONMENT=production\` PostgreSQL-only. The guide describes \`%APPDATA%/DigitalCrown/\` media/backups and notes a separate human \`INSTALLABLE_CERTIFIED\` gate. It does **not** prove which database is active in the actual current clinic.
- \`docs/NEW_CABINET_INSTALL_PATH.md\` confirms solo encrypted SQLCipher and multi-postes PostgreSQL 15+ as distinct supported installation modes; \`ENVIRONMENT=cabinet\` can accept either and \`production\` rejects SQLite. Its historical manual multi-PC commands are not executable certification, and the multi-PC test must be on an isolated bench with approved release, HTTPS trust and restricted DB login.
- \`docs/handovers/2026-10-14-lot04-pocket-residual-pr-closeout.md\` records software merge #882 and PostgreSQL 18/Windows CI SUCCESS on historical master \`55b1985\`, **not** full cabinet clinical certification or evidence of current live engine.
- \`docs/quality/V15_05_SQL_MIGRATION_CONTRACT.md\` distinguishes schema/dry-run preparations from authorized clinical data import; backup primitives are not proof of successful restore, and live Alembic/create_all/import is explicitly prohibited without a separate gate.

**Correction to B06-4D-E ADR engine recommendation:** do **not** impose PostgreSQL on every cabinet. Keep a shared application-level cryptographic key-versioning/receipt and recovery contract with two reviewed persistence implementations: (a) SQLCipher local solo mode, (b) PostgreSQL local multi-postes or production mode when LOT04 confirms and authorizes it. Do not introduce dual-write, silent migration or automatic engine selection. In both cases encrypted media and cryptographic key escrow must be independently backed up and verified. PostgreSQL-specific RLS/role/tenant FUE applies only to the PostgreSQL implementation; equivalent SQLCipher isolation must be assessed through application authority and local file/OS boundaries, not fictional PG RLS.

**Owner decision gate, unresolved:** (1) identify the actual engine of the specific cabinet using an owner-approved read-only inventory (not attempted); (2) choose supported target installation topology (solo or multi-PC) and permitted runtime environment; (3) authorize a purpose-separated versioned key design, key custody/escrow and retention; (4) define RPO/RTO and approve isolated restore rehearsal; (5) independently authorize any additive schema/code work, representative clone and physical/human gate. No evidence in these files grants such approvals.

**Verdict:** \`LOT04_READONLY_DOCUMENTARY_RECONCILIATION=COMPLETE\`; \`CABINET_LIVE_ENGINE_VERIFIED=false\`; \`LOT04_OWNER_APPROVAL=false\`; \`B06-4D-E_ADR=PROPOSED_NOT_APPROVED\`; \`READY_TO_MERGE=false\`; \`PRODUCT_READY=false\`; \`CLINICAL_GO=false\`. No clinic connection, no patient data, no code/migration/merge/deployment. **Next:** owner-authorized, non-secret, read-only current-cabinet engine/topology inventory; then decide whether B06-4D-F is an isolated contract prototype only or a separately approved implementation.


## PRE B06-4D-F0 — non-secret read-only runtime engine identification contract, 2026-11-05

Baseline: PR #1210 Draft, `dfa75c1`, prior CI #42007847209 IN_PROGRESS (not GREEN yet). Scope: inspect source-level startup/engine guards and author a **read-only operator inventory procedure** that does not collect credentials, connection strings, patient data or touch live cabinet. No access to actual workstation is available or authorized. No product code/migration, merge or deployment. POST must distinguish repository source evidence from live engine proof. Notion PRE/POST mandatory.

## POST B06-4D-F0 — source-verified, non-secret engine identification procedure (NOT a live inventory), 2026-11-05

**Source evidence:** \`backend/main.py::validate_environment_invariants\` explicitly blocks SQLite only for \`ENVIRONMENT=production\`, not \`cabinet\`; \`backend/tests/test_cabinet_mode.py\` covers production SQLite refusal, cabinet SQLite/SQLCipher acceptance, and debug/CORS gates. \`backend/core/runtime_safety.py\` provides \`canonical_database_target\` and \`database_target_fingerprint\` to compare SQLCipher and SQLite target identities without exposing a password, and protects known cabinet targets from development isolation bypass. \`backend/core/new_cabinet_setup.py\` checks a **new** cabinet's absolute \`clinical_vault.db\` path; this is not evidence of the currently installed cabinet. Source inspections are not a runtime attestation.

**Proposed owner-operated read-only inventory protocol (not executed):**
1. On the *actual authorized workstation*, first record only OS family, installed **certified release ID**, installation topology (single workstation vs server + annexes), service executable path classification (not full personal path), and whether the active runtime is \`cabinet\` or \`production\`. Do not start/stop services, inspect clinical records or run scripts from the editable checkout.
2. A trusted operator must inspect the **active process's effective configuration** using a vetted local diagnostic that returns **only** the allowlisted fields \`environment\`, \`db_engine_family\` (\`sqlite/sqlcipher\` or \`postgresql\` or \`unknown\`), \`db_target_fingerprint\` (SHA-256 of password-free canonical target), \`release_id\`, and \`capture_time\`. It must never print \`DATABASE_URL\`, host/database name, credentials, keys, .env, patient identifiers or paths. The existing \`database_target_fingerprint\` is a code helper, **not proof that a safe operator diagnostic already exists**. A standalone implementation would need independent security review and operator permission.
3. Compare the result to the certified release's expected configuration and read-only operator documentation. Distinguish configured engine from an **observed successful runtime connection**; if the latter cannot be proven safely, label \`ENGINE_CONFIG_ONLY\`. No DB write, SQL query against patient tables, key dump, backup trigger, network scan or connection-string copy.
4. Have the owner sign off the result (topology, engine family, release ID, timestamp, fingerprint) and file only the **redacted attestation** in the canonical governance record. A fingerprint is still a stable infrastructure identifier: share only inside the authorized team, not public logs.
5. If the effective config cannot be determined without secrets or privileged access, **STOP: \`LIVE_ENGINE=UNKNOWN\`**. Never infer live engine from \`ENVIRONMENT=cabinet\`, old docs, a local \`clinical_vault.db\` file, GitHub CI, or \`DATABASE_URL\` found in an unrelated checkout.

**Acceptance FUE for future isolated diagnostic (not executed):** F0-01 solo SQLCipher reports correct engine and fingerprint without secrets; F0-02 PG multi-PC correct and no server name leakage; F0-03 \`cabinet\` ambiguous by design, no false PG assertion; F0-04 config and connected engine mismatch fail closed; F0-05 absence of authorization/release attestation refuses; F0-06 logs/exception outputs scanned for URL/password/key/PII; F0-07 no DB or media write and no service restart. Run on synthetic isolated fixtures only before owner-approved workstation observation.

**Outcome:** \`B06-4D-F0_SOURCE_REVIEW=COMPLETE\`; \`B06-4D-F0_LIVE_DIAGNOSTIC_IMPLEMENTED=false\`; \`CABINET_LIVE_ENGINE_VERIFIED=false\`; \`OWNER_AUTHORIZED_MACHINE_INVENTORY=false\`; \`LOT04_OWNER_APPROVAL=false\`; \`READY_TO_MERGE=false\`; \`PRODUCT_READY=false\`; \`CLINICAL_GO=false\`. No actual workstation access, no clinic operations, no product changes, no migration, no merge or deployment. **Next:** owner permission for a safe diagnostic design and read-only runtime attestation; alternatively scope a wholly synthetic B06-4D-F1 keyring contract prototype without claiming live compatibility.


## PRE B06-4D-F1 — accelerated synthetic crypto contract implementation, 2026-11-05

Owner clarification: no clinical data currently to preserve; optimize delivery velocity. Baseline `feea87f` CI #42008115265 SUCCESS 3/3. Implement a **small standalone, isolated synthetic crypto v2 contract** with versioned AES-GCM media keys, independent HMAC locator keys, strict key IDs and authenticated AAD; retain existing DCM1 product behavior unchanged until independent integration FUE. Add focused synthetic tests including wrong key, wrong tenant, tamper, missing key and locator stability across encryption-key rotation. No actual clinic data, migration, product activation, merge or deploy. Update Notion PRE/POST and exact SHA CI.

## POST B06-4D-F1 — synthetic-only versioned media crypto implementation, 2026-11-05

**Implementation on this PR branch, no product activation:**
- \`isolated_fue_lot06c/b06_versioned_crypto_synthetic.py\`: standalone DCM2 AES-256-GCM envelope containing a validated media key ID, nonce and authenticated ciphertext. Tenant ID, SHA-256 digest and envelope header are bound in AEAD AAD. Missing/incorrect historical key, invalid header, wrong tenant/digest, tampering and invalid key ID fail closed. Separate 32-byte HMAC locator keys avoid locator churn when only the encryption key rotates.
- \`isolated_fue_lot06c/test_b06_versioned_crypto_synthetic.py\`: ten named synthetic FUE scenarios (F1-01 through F1-10; F1-07 parametrized five invalid IDs), covering versioned roundtrip, key rotation, locator stability, missing/wrong historical keys, cross-tenant swap, tamper, invalid IDs, digest mismatch, truncated envelopes and no legacy downgrade.
- No key bytes in the repository are production credentials: test constants are public, synthetic and deterministic. Product DCM1 and ACK-v1 code, schema, installer, API and real clinic configuration remain untouched.

**Important release boundary:** This is a **standalone contract prototype**, not yet integrated with \`clinical_asset_storage.py\`, \`ClinicalAsset\` or the durable receipt signer. The new FUE test file is committed, but no claim that a CI workflow actually executes it until an exact-SHA job log proves that. Do not call \`PRODUCT_READY\`, \`KEYRING_PRODUCT_IMPLEMENTED\` or \`CLINICAL_GO\` true. Avoid a compatibility migration for nonexistent clinical history unless a real requirement emerges.

**Next accelerated step:** wire isolated F1 pytest into the LOT06 exact-HEAD workflow and certify it; then integrate DCM2 with storage and receipt key IDs on disposable SQLCipher/PG fixtures in one bounded product sublot, preserving legacy fail-closed behavior and FUE evidence. No merge/deploy without explicit owner authorization.


## PRE B06-4D-F1 CI wiring — 2026-11-05

Baseline HEAD `9c3f9ed`, B06 #42011480767 GREEN 3/3 but logs prove 77 SQLCipher + 4 PG schema + 19 PG route tests only; **F1 synthetic crypto tests not executed**. Inspect `.github/workflows/lot06-phase2-b06-integration-fue.yml`; add explicit F1 test file and implementation to path filters and run isolated pytest on exact SHA in existing Ubuntu synthetic job. No product storage changes, merge, deploy or clinical data. Notion PRE/POST and exact-SHA CI required.


## POST B06-4D-F1 CI wiring — 2026-11-05

Workflow `.github/workflows/lot06-phase2-b06-integration-fue.yml` updated in `39f1ee4`: add synthetic F1 module and test paths to push triggers and dedicated `B06-4D-F1 synthetic versioned crypto FUE exact SHA` step in existing isolated Ubuntu job. Step asserts `git rev-parse HEAD == GITHUB_SHA`, runs `python -m pytest -q -s --maxfail=1 isolated_fue_lot06c/test_b06_versioned_crypto_synthetic.py` and prints `DC06_B06_F1_VERSIONED_CRYPTO_SYNTHETIC_FUE_PASS` only after success. This fixes previously untested F1; **CI verdict pending exact HEAD job log**. No product DCM1 integration, schema/migration, real clinical data, merge or deploy. `F1_TESTS_CI_CERTIFIED=false` until proof; `READY_TO_MERGE=false`; `CLINICAL_GO=false`.


## PRE B06-4D-F2 — 2026-11-05

Baseline exact HEAD `2e25471`; F1 CI #42012440563 14/14 GREEN, existing B06 3/3. Owner confirms no real clinical history, delivery speed prioritized. Implement opt-in DCM2 product storage adapter using independent versioned media and locator keys and synthetic FUE, without changing default legacy DCM1 or real cabinet. Notion PRE/POST and exact SHA CI required. No merge or deploy.

## POST B06-4D-F2 — opt-in product DCM2 store/read, 2026-11-05

Implemented `backend/services/clinical_media_crypto_v2.py` product primitive and opt-in branch in `backend/services/clinical_asset_storage.py`: `DC_MEDIA_V2_OPT_IN=true` writes DCM2 AES-GCM envelopes, media key ID in authenticated header, tenant+digest AAD, independent versioned HMAC locator namespace, and `AESGCM_V2` metadata. Existing default DCM1 writes/reads remain unchanged. V2 reads are selected by stored format, not by the write switch. Strict configuration requires `DC_MEDIA_V2_ACTIVE_KEY_ID`, `DC_MEDIA_V2_LOCATOR_KEY_ID`, `DC_MEDIA_V2_MEDIA_KEY_HEX` and `DC_MEDIA_V2_LOCATOR_KEY_HEX` (distinct 32-byte keys). No secrets are committed. Unknown/wrong key, wrong tenant, wrong locator and tampering fail closed. No migrations or live activation.

Seven product adapter synthetic FUE in `isolated_fue_lot06c/test_b06_f2_product_storage_v2.py`: DCM2 store/read, dedupe/tamper, wrong media key, wrong locator key, cross tenant, missing config/no writes, and reading V2 when write switch disabled. CI workflow `.github/workflows/lot06-phase2-b06-integration-fue.yml` now executes the F2 file on exact SHA and prints `DC06_B06_F2_PRODUCT_STORAGE_V2_SYNTHETIC_FUE_PASS` after success.

**Known boundary:** This is an opt-in first-key product adapter, NOT a complete historical keyring or Ed25519 receipt-key versioning. Old V2 media-key IDs are not yet resolvable from an escrow registry after rotation; changing the locator key ID invalidates lookup for existing V2 blobs. Do not rotate either key in production until historical key registry/retention is implemented. No schema migration needed because `storage_format` is an existing text field. Clinical capture ACK signer remains v1. **F2 CI still pending; no claim GREEN before logs.** `READY_TO_MERGE=false`, `CLINICAL_GO=false`.


## PRE B06-4D-F3 — retained historical keys, 2026-11-05

Baseline F2 HEAD `b8a7469`, exact SHA B06 CI #42018635157 GREEN 3/3; F2 7/7, F1 14/14. Implement retained historical media and locator keys for DCM2 read after rotation, while new writes use active IDs only. Synthetic FUE and exact-SHA CI required; DCM1 default, no clinical activation, merge or deploy.


## POST B06-4D-F3 — retained historical DCM2 keys, 2026-11-05

Implemented explicit retained-key maps `DC_MEDIA_V2_RETAINED_MEDIA_KEYS_JSON` and `DC_MEDIA_V2_RETAINED_LOCATOR_KEYS_JSON` (JSON key ID to 32-byte hex). Active IDs remain the sole write keys; reads resolve historical media ID from authenticated DCM2 header and historical locator ID from validated opaque tenant path. Unknown IDs, malformed registries, cross-purpose key reuse and conflicting active IDs fail closed. Four new F3 cases appended to the existing seven product synthetic FUE: historical read after both rotations, missing media key, missing locator key, conflicting active registry. Workflow B06 runs all 11 F2/F3 tests on exact SHA. **CI pending; no claim F3 GREEN until job logs.** No clinical key escrow, secure backup mechanism, ACK signer rotation, merge, deployment or live activation. `READY_TO_MERGE=false`, `CLINICAL_GO=false`.


## PRE B06-4D-F4 — secure keyring configuration gate, 2026-11-05

F3 exact HEAD `66bac52`, run #42022380767 GREEN 3/3, 11/11 F2/F3, 14/14 F1. F4 objective: remove insecure inline historical-key JSON from environment by supporting local private keyring file with strict permissions, fail-closed malformed/insecure config, synthetic FUE and exact-SHA CI. Keep existing opt-in mode, no merge/deploy/clinical activation.


## POST B06-4D-F4 — private local keyring file, 2026-11-05

Added opt-in `DC_MEDIA_V2_KEYRING_FILE` for local JSON with `active_media_id`, `active_locator_id`, `media_keys`, `locator_keys` (historical IDs included). On POSIX requires regular file (not symlink), owner == process EUID, no group/other permissions, size <= 16KiB; rejects mixed inline environment secrets, malformed map, missing active IDs, cross-purpose key reuse. Existing environment-key mode remains available for compatibility; Windows file mode explicitly unsupported until ACL-specific implementation. Seven synthetic F4 tests in `isolated_fue_lot06c/test_b06_f4_private_keyring.py`, exact SHA CI step added. **F4 CI pending; not certified GREEN**. This is configuration hardening, not an encrypted/escrowed backup or robust atomic file-opening/TOCTOU guarantee; do not treat it as full key custody. `READY_TO_MERGE=false`, `CLINICAL_GO=false`; no deploy or merge.


## PRE B06-4D-F5 — atomic file open and Windows ACL gate, 2026-11-05

F4 exact SHA `d988064` CI #42027167418 GREEN 3/3, F4 7/7. F5 target: eliminate POSIX lstat/open TOCTOU with O_NOFOLLOW+fstat and add fail-closed Windows ACL-aware file mode (no permissive fallback). Synthetic-only FUE, exact SHA CI, no merge/deploy/clinical activation.


## POST B06-4D-F5A — atomic POSIX keyring read, 2026-11-05

Hardened private file loader to require absolute path, O_NOFOLLOW and O_DIRECTORY dirfd traversal for each parent component, open final file with dir_fd, fstat the opened descriptor, validate owner/mode/type/size and bound read to 16KiB before JSON decode. Prevents precheck-to-open symlink swap and intermediate symlink traversal on POSIX; F4 existing seven tests adjusted for atomic-open denial and F5 adds three tests for relative path, oversized file, and symlink swap. Workflow runs 10 F4/F5 tests on exact SHA, marker `DC06_B06_F5_ATOMIC_NOFOLLOW_KEYRING_FUE_PASS`. **CI pending, no F5 GREEN claim.** Windows ACL-safe file mode is still explicitly denied; Windows F5B remains necessary. No false claim of Windows compatibility, no key backup/escrow, no merge/deploy/clinical activation. `READY_TO_MERGE=false`, `CLINICAL_GO=false`.


## PRE B06-4D-F5B — Windows ACL adversarial gate, 2026-11-05

F5A GREEN exact HEAD `3cda3a0`, CI #42034452238 3/3, F4/F5A 10/10. Scope: Windows native ACL negative tests and a fail-closed guard for DCM2 private-keyring path; never enable Windows loader until safe open and security descriptor checks are implemented and verified. CI exact SHA; no merge/deploy/clinical activation.


## POST B06-4D-F5B-A — Windows native ACL negative gate, 2026-11-05

Created `isolated_fue_lot06c/windows_f5b_private_keyring_acl_fue.ps1`, exercised by existing Windows 2022 exact-SHA CI job: synthetic private file ACL acceptance, Everyone read access denial, inherited ACL denial, symlink/reparse denial when test-runner privilege permits, and verification that product Windows loader remains fail-closed. No clinical data or secrets. **This is a Windows ACL threat-model test, not a production Windows loader.** Windows secure file-handle open and ACL validation are not integrated into Python product runtime; `WINDOWS_PRIVATE_KEYRING_IMPLEMENTED=false`. CI pending; no F5B GREEN claim. Next F5B-B requires native Windows secure open+descriptor validation, reparse/path handling and adversarial race tests before enabling. No merge/deploy/clinical activation, `READY_TO_MERGE=false`, `CLINICAL_GO=false`.


## PRE B06-4D-F5B-B — native Windows handle and ACL-bound read, 2026-11-05

F5B-A exact HEAD `78fb82d`, CI #42049169242 GREEN 3/3; native ACL FUE markers confirmed. Implement Windows native handle-bound ACL verification without path-based precheck/open race, adversarial FUE and exact-SHA CI. Fail closed if any platform capability or security check is unavailable; no clinical enable, merge or deploy.


## POST B06-4D-F5B-B1 — Windows native handle probe (NOT product activation), 2026-11-05

Added `backend/services/windows_keyring_handle_probe.py`: isolated Windows ctypes `CreateFileW` with final-component `FILE_FLAG_OPEN_REPARSE_POINT`, `GetFileInformationByHandle` reparse/directory/size checks and bounded `ReadFile` from the same handle; synthetic-only FUE `isolated_fue_lot06c/windows_f5bb_handle_probe_fue.ps1` tests read, oversized, relative path, final symlink and confirms product still denies Windows file keyrings. CI exact SHA Windows job wired. **Security boundary:** intermediate directory reparse traversal remains possible; no handle-bound owner/ACL security descriptor verification. Therefore module is NOT imported into the product loader and `WINDOWS_PRIVATE_KEYRING_IMPLEMENTED=false`. F5B-B2 remains OPEN. CI pending, no GREEN claim; no merge/deploy/clinical activation, `READY_TO_MERGE=false`, `CLINICAL_GO=false`.


## PRE B06-4D-F5B-B2 — Windows handle ACL/parent traversal and B1 red CI fix, 2026-11-05

B1 CI #42059957792 exact SHA `b0e4c83` **RED** (Windows job fails because standalone test imports `backend.__init__` requiring uninstalled SQLAlchemy; Linux jobs GREEN). No claim B1 passed. First isolate standalone Windows test import by direct file loading, then harden handle-bound Windows ACL/parent reparse checks under synthetic FUE. Keep product Windows file loader denied until proof of exact SHA, proper owner, DACL and reparse semantics. No merge/deploy/clinical activation.


## POST B06-4D-F5B-B2 lab — Windows native handle-bound DACL and ancestor safety, 2026-11-05

**Baseline correction:** B1 exact SHA `b0e4c83` CI #42059957792 RED (Windows Python package import required SQLAlchemy, not installed in isolated Windows runner). Windows script now loads probe directly with `importlib.util.spec_from_file_location`, without importing `backend.__init__` (`0a692955`). Windows native probe (`d350f9a`) opens each ancestor and final file separately using `FILE_FLAG_OPEN_REPARSE_POINT`, retains ancestor handles without write/delete sharing during final read, checks all handles for reparse attributes, then validates final handle owner=current user or SYSTEM, DACL protected (no inheritance), only current user/SYSTEM allowed ACE principals, and bounded read on that same handle. FUE includes private file read, >16KiB denied, relative path denied, Everyone allowed ACE denied, inherited DACL denied, final symlink and parent junction **mandatory** adversarial negatives (`98be743`). PRODUCT CRYPTO LOADER STILL WINDOWS FAIL-CLOSED (`KEYRING_FILE_PLATFORM_UNSUPPORTED`); no unsupported claims of production readiness, DPAPI/escrow/backup or clinical rotation. Synthetic Windows CI on exact HEAD required before certifying; **CI PENDING**. `WINDOWS_PRIVATE_KEYRING_IMPLEMENTED=false`, `READY_TO_MERGE=false`, `CLINICAL_GO=false`. No merge or deployment.


## PRE B06-4D-F5B-C — Windows product DCM2 keyring opt-in integration, 2026-11-05

F5B-B2 exact SHA `0020dbf`, CI #42064800991 SUCCESS 3/3, nine Windows probe FUE markers confirmed. Integrate audited handle-bound Windows reader behind existing explicit `DC_MEDIA_V2_KEYRING_FILE` opt-in in `clinical_media_crypto_v2.py`, preserve POSIX and env-only behavior, mixed-source fail-closed, reject invalid UTF-8/JSON and ACL/reparse threats, add real product-loader Windows synthetic FUE. Require exact-SHA Windows CI before GREEN; no merge, deploy or clinical activation.


## POST B06-4D-F5B-C — Windows product DCM2 file-keyring opt-in integration, 2026-11-05

Integrated native handle-bound Windows keyring reader into `backend/services/clinical_media_crypto_v2.py` under existing explicit `DC_MEDIA_V2_KEYRING_FILE` only (`a13a5f3`). Windows path reads <=16KiB bytes from validated handle, decodes UTF-8, JSON validates, maps native deny to `MediaCryptoV2Denied`; no plaintext fallback, existing mixed-source checks preserved, POSIX behavior unchanged. Updated F5B-B2 probe guard to require integration (`19c88aa`). New synthetic Windows product FUE `isolated_fue_lot06c/windows_f5bc_product_keyring_fue.ps1` tests real configured_keyring valid retained-key read, env mixed-source deny, and broad Everyone ACL deny (`a1c80e3`); exact-SHA Windows CI workflow wired (`cbfd648`). **CI pending, no GREEN claim.** No production clinical enable, no merge/deploy, no key escrow/recovery yet. `READY_TO_MERGE=false`, `CLINICAL_GO=false`.


## CERTIFICATION F5B-C GREEN + PRE F5B-D recovery validation, 2026-11-05

F5B-C exact SHA `a5a8b0451084e79dcad2fa1ef02d9eaf27cb9d3b`, CI #42073342776 COMPLETED SUCCESS 3/3 (Windows, SQLCipher, UI). Windows job logs include 13 F5BB/F5BC PASS markers; Windows product DCM2 file keyring integration proven synthetic. Next F5B-D: implement *offline synthetic* recovery verification for full active+retained media/locator keyring, verify DCM2 decryption/locator continuity after restore, tamper/wrong-secret rejection, and explicit recovery/escrow boundary. Do not store plaintext key backup in repo, logs or artifacts; no automatic backup, no clinical activation, no merge/deploy. `READY_TO_MERGE=false`, `CLINICAL_GO=false`.


## POST B06-4D-F5B-D1 — explicit offline encrypted keyring recovery laboratory, 2026-11-05

Created `backend/services/clinical_media_keyring_recovery.py` (`c118610`, schema hardening `9a88105`): explicit in-memory-only `seal_keyring`/`open_keyring`, AES-256-GCM authenticated envelope with random salt/nonce, scrypt KDF, bounded input, full active+retained media/locator JSON schema checks and key-purpose separation. **No automatic backup or disk writing; no plaintext secret output; password custody is external.** Synthetic `isolated_fue_lot06c/f5bd_offline_keyring_recovery_fue.py` (`612452a`) tests randomized encrypted roundtrip, historical and active DCM2 decrypt continuity, both locator IDs, wrong password, tamper, truncated envelope and invalid active key. Exact-SHA Windows CI workflow wired (`635e76f`). **CI pending; F5B-D1 not GREEN**. Explicit limitation: encrypted envelope alone does not prove offsite custody, password recovery, restore-to-locked-down-file, or operator runbook. Next F5B-D2: secure on-disk restore with ACL/owner, operator FUE and recovery procedure. `READY_TO_MERGE=false`, `CLINICAL_GO=false`; no merge/deploy.


## F5B-D1 GREEN + PRE F5B-D2 Windows disk restore FUE, 2026-11-05

F5B-D1 CI #42077908955 SUCCESS 3/3 exact SHA `37957a102f2eeb24bccff44442b5394453fc5666`. Next D2: Windows operator-only *synthetic* restore to a newly created file with protected private DACL before any key bytes are written, no overwrite of existing target, no symlink/junction ancestor, no plaintext temp in repo/artifacts, read-back via the F5B-C production keyring loader and negative tests for existing destination and broad parent reparse. A secure Windows native file creation primitive must fail closed if owner/DACL cannot be established. No merge/deploy/clinical activation, `CLINICAL_GO=false`.


## POST F5B-D2 Windows secure disk restore LAB, 2026-11-05

Added `backend/services/windows_keyring_restore.py` (`4fd87cb`) Windows-only explicit operator primitive. For a fresh absolute local-drive target, obtains current Windows token SID and builds protected owner/current-user+SYSTEM DACL via SDDL *before* `CreateFileW(CREATE_NEW)`; retains opened ancestor handles while checking each reparse attribute, opens target exclusively with no sharing, writes bounded <=16KiB payload through same handle and flushes, never overwrites. On failed write best-effort deletes partial file; does not log key bytes. Added Windows synthetic FUE `isolated_fue_lot06c/windows_f5bd2_private_restore_fue.ps1` (`8a80652`): in-memory encrypted envelope decrypt -> new private file -> real DCM2 product loader readback active+retained keys, existing target denied, relative path denied, parent junction denied. CI wired exact SHA (`00ddf04`). **CI pending, not GREEN.** This is a laboratory operator primitive, not automatic backup, no password escrow or independent offsite restoration proof. Must audit Windows ACL/creation/rollback failure semantics and perform operator recovery drill before `CLINICAL_GO`; no merge/deploy. `READY_TO_MERGE=false`, `CLINICAL_GO=false`.


## PRE F5B-D3 — adversarial security audit and recovery drill, 2026-11-05

D2 CI #42080159792 SUCCESS 3/3 exact SHA `d9a6331960ea90e8aa289643d6762801e2837423`, five Windows D2 PASS markers. Audit findings requiring remediation before operator drill: `restore_new_private_file` accepts arbitrary bytes without verifying canonical full keyring schema (could persist unusable secrets); on failed write it closes handles then unlinks by pathname (race can delete a replacement path); Windows ancestor handles are absolute-path traversal rather than handle-relative opens, so do not claim formal TOCTOU elimination. Plan: validate keyring bytes and fail closed before disk creation; remove pathname-based cleanup on failure and document quarantining of incomplete private files; extend Windows negative FUE and simulate encrypted backup -> restore -> readback. Keep lab-only, `CLINICAL_GO=false`, no merge/deploy.


## POST F5B-D3 security hardening and synthetic operator drill, 2026-11-05

Security patch `6e31296`: before any Windows file creation, parse UTF-8 JSON and validate full active+retained media/locator schema with existing recovery validator; reject malformed/incomplete registry with `RESTORE_KEYRING_INVALID`. Remove pathname-based unlink after closing the exclusive handle: failed writes leave a protected file for manual quarantine; never auto-retry/overwrite. Windows synthetic recovery drill expanded (`3323c44`): encrypted backup -> offline decrypt -> private `CREATE_NEW` restore -> production DCM2 loader readback of active and retained keys, deny existing target, relative path, junction parent, malformed JSON and incomplete registry *before writing*.

**Operator procedure — LAB ONLY:** (1) isolate an offline Windows workstation; (2) confirm encrypted recovery envelope and password are independently available and controlled by two authorized operators; (3) restore only into a fresh, dedicated local NTFS folder, never an existing path; (4) verify product loader can read active and historical key IDs and decrypt synthetic test artifacts; (5) retain recovery envelope and password separately offsite; (6) on any interrupted write, quarantine private incomplete target and investigate, do not overwrite; (7) never print, commit, email, or upload plaintext keys. This is a synthetic runbook, **not** a real disaster recovery certification; independent offsite custody, dual-control drill and threat-model review still pending.

Residual risk: parent directory traversal is absolute-path component-wise with pinned handles, not a formal handle-relative Windows NT traversal; no adversarial concurrent path-swap proof. **F5B-D3 CI pending**. `READY_TO_MERGE=false`, `CLINICAL_GO=false`. No merge, deploy, or clinical activation.


## PRE F5B-D3 CI repair, 2026-11-05

Exact-SHA run #42081751020 Windows FAILED: junction-parent negative test supplied invalid JSON `{"synthetic":true}`; new schema validator correctly returned `RESTORE_KEYRING_INVALID` before reaching the parent-junction guard. Other F5BD3 malformed/incomplete prewrite and F5BD2 readback/overwrite/relative markers PASS. Fix test fixture to use a valid synthetic full keyring so the intended junction denial is actually exercised; do not weaken production validation. No GREEN claim.


## POST F5B-D3 Windows CI fixture repair, 2026-11-05

Replaced invalid `{"synthetic":true}` in parent junction adversarial FUE with complete valid synthetic active+retained media/locator keyring (`698c11f`), so the junction guard is reached and must reject the path. Product secure restore validator unchanged. New exact-SHA CI pending; `CLINICAL_GO=false`, no merge/deploy.


## PRE F5B-D4 — independent recovery readiness gate, 2026-11-05

Baseline: PR #1210 OPEN/DRAFT exact head `cde31664aaa3d263084ea7e58e929fe891b411d0` before this documentary PRE. CI B06 #42082740002 completed SUCCESS 3/3; CI Scope #42082750748 completed SUCCESS on the identical SHA. The Windows job emitted all seven F5BD3/D2 negative and positive restore markers. This certifies the bounded synthetic lab F5B-D3 test, not independent disaster recovery.

Goal: independently assess the recovery evidence gap and define a reproducible non-clinical operator drill for DCM2 keyring restoration, including evidence-oracle independence, dual-custody/offsite checks, synthetic historical decrypt/locator continuity, fail-closed negatives and an unambiguous human sign-off. Inspect recovery code and exact-head Windows logs; no patient data, cabinet access, physical operator impersonation, clinical activation, merge or deployment. A real offsite Windows operator drill requires an authorized isolated station and custodians; physical/field execution is reserved to LOT10 where applicable. `CLINICAL_GO=false` and `READY_TO_MERGE=false` until separately proven and approved.


## POST F5B-D4 — independent recovery acceptance protocol (NOT EXECUTED), 2026-11-05

### Result / exact evidence

Source baseline `cde31664aaa3d263084ea7e58e929fe891b411d0` verified against [B06 run #42082740002](https://github.com/hraaaaf/Digital_crown/actions/runs/42082740002): exact `head_sha`, completed SUCCESS, 3/3 jobs SUCCESS, Windows job `127439753807` 7/7 F5BD3/D2 markers PASS, no unexpected skip within those steps. [Scope run #42082750748](https://github.com/hraaaaf/Digital_crown/actions/runs/42082750748) same SHA, SUCCESS. Source read: `clinical_media_keyring_recovery.py`, `windows_keyring_restore.py`, `windows_keyring_handle_probe.py` and `windows_f5bd2_private_restore_fue.ps1`. Windows FUE creates its own synthetic keyring, seals and decrypts that envelope in the same job, then checks product readback. It is **not independent backup custody, independent oracle, offsite retrieval, independent operator execution or a full-cabinet restore**. Zero offsite/operator evidence was supplied during this pass. No new tests executed in this documentation-only pass.

### One bounded DCM2 independent operator drill — acceptance contract

1. **Authorize and isolate.** Obtain written authorization for an offline, non-clinical Windows test station with a fresh NTFS directory, separate operator and observer, and explicitly synthetic data only. Record OS version, test-release/source SHA, package/build SHA-256, timestamp, station ID (non-identifying pseudonym), and named sign-offs. Do not use live cabinet, PHI or production keys.
2. **Independent custody/oracle.** A custodian not executing the restore provides a PRE-EXISTING encrypted DCM2 active+retained keyring envelope from external storage and a separately delivered recovery password. Preserve independently established ciphertext SHA-256 and expected **synthetic media ciphertext digest + locator outputs**, sealed BEFORE the run. The operator must not generate the backup, secret or expected outputs during the drill. Record custody attestations and media/pw separation; never expose keys/passwords/cleartext in the evidence bundle.
3. **Recover offline.** Verify the encrypted-envelope digest against the precommitted manifest, decrypt only in isolated memory, restore full schema to a NEW private file via the native Windows primitive, reject existing destination and unsafe paths, confirm owner/protected DACL and file integrity using an independently approved verifier. A failed or interrupted write leaves a private file for explicit quarantine, never overwrite or pathname unlink.
4. **Prove continuity with independent expected values.** Restart the process, load restored keyring with the actual product DCM2 file loader, decrypt both active and retained **synthetic** DCM2 ciphertexts and check byte digests, verify active and historical locator outputs match their precommitted oracle. Prove no mismatch becomes a successful empty result.
5. **Adversarial denial.** From separately staged fixtures test wrong password, modified/truncated envelope, missing historical key, malformed/incomplete JSON, destination overwrite, relative path, parent junction/reparse, permissive/inherited DACL and an interrupted write. Verify each returns a bounded DENY, never a usable restored keyring, false PASS or leaked secret. For the Windows concurrent parent-swap/absolute traversal residual, an explicit independent threat review and adversarial proof or an accepted compensating constraint is required before relying on the restore primitive clinically.
6. **Evidence and decision.** Store only non-secret test metadata: run ID/date, source/build SHA, Windows/NTFS, offsite ciphertext digest, custody attestation references, independent oracle provenance, step-level PASS/FAIL, negative-case results, restart/retained-key results, sanitised event logs, observed recovery duration, operator and independent observer sign-offs, unresolved deviations and rollback/quarantine disposition. Do NOT upload password, keyring, decrypted file, patient data, real media or sensitive machine paths to GitHub/Notion. Define RPO/RTO with owner before any broader clinic continuity claim.

**Pass iff:** steps 1–6 are independently evidenced, every mandatory negative refuses, active+historical key/media/locator continuity matches PRE-EXISTING expected values after restart, no sensitive leakage, no unreviewed BLOCKER/MAJOR, and human authorisation/sign-offs are recorded. **Otherwise FAIL/UNKNOWN; do not infer success from the CI FUE.** The DCM2 drill alone does not certify consistent database + encrypted media + receipt/ACK restore, rollback/replay, installation trust or a real cabinet. Such physical/field evidence is tracked under LOT10 when applicable, without reclassifying missing LOT06 software tests as physical obligations.

### Closeout state

`F5B_D3_SYNTHETIC_CI_GREEN=true` on baseline source SHA `cde3166` only; `F5B_D4_INDEPENDENT_OPERATOR_DRILL=NOT_RUN`; `OFFSITE_ESCROW_VERIFIED=false`; `INDEPENDENT_ORACLE_VERIFIED=false`; `FULL_CABINET_RESTORE_VERIFIED=false`; `WINDOWS_PARENT_SWAP_RISK=OPEN`; `READY_TO_MERGE=false`; `PRODUCT_READY=false`; `CLINICAL_GO=false`. PR #1210 remains Draft and unmerged. No product edit, no merge/deployment/clinical operation. Documentation commits create a **new HEAD** and require fresh exact-HEAD CI before any claim about that HEAD. Next exact action: independent authorized operator+custo​dian execute the offline DCM2 drill with precommitted synthetic ciphertext oracle; independently review the parent-swap threat; collect sanitized evidence and human sign-off, then run separately applicable full restore/release gates.


## PRE F5B-D4b — fixed-oracle independent-of-runner CI FUE, 2026-11-05

User GO to reuse existing GitHub-hosted ephemeral `windows-2022` CI runner; baseline exact head `c68e43b31288ed86442b3619977930f2a21cd82b`, B06 #42096968335 SUCCESS 3/3, Scope #42096981970 SUCCESS. Gap: current F5B-D3 backs up and restores material it just produced in the same job. Add a prebuilt, public synthetic ciphertext corpus and separately committed expected media/locator digest oracle with a pinned fixture SHA; restore to new Windows private file and validate active+retained decrypt through a fresh process, with adversarial refusals. This is independent of generation during the CI run, not independently custodial/offsite or human-executed. Do not claim clinical recovery, physical P13/LOT10 gate, parent-swap closure, or full SQLCipher/DB+media+ACK restore. No patients, production keys, real password, merge, deployment or clinical enable. `READY_TO_MERGE=false`; `PRODUCT_READY=false`; `CLINICAL_GO=false`. Exact-HEAD CI required before GREEN.


## POST F5B-D4b — prebuilt fixed-oracle Windows FUE integrated (CI awaiting exact final SHA), 2026-11-05

**Changes on PR #1210 only (Draft, no merge):**
- Prebuilt **synthetic** fixed vector file `isolated_fue_lot06c/f5bd4_fixed_synthetic_oracle.json`: AES-GCM recovery envelope, SHA-256 of encrypted envelope, two prebuilt AES-GCM media ciphertexts (old `media1` and active `media2`), two independent expected locator HMACs (`loc1` / `loc2`), and their plaintext digests; frozen before the new GitHub CI run. All secrets within fixture are intentionally PUBLIC synthetic test data, not real clinic credentials, and fixture `provenance` expressly disclaims offsite human custody.
- `isolated_fue_lot06c/f5bd4_fixed_recovery_windows_fue.py`: pins the exact raw fixture SHA-256 `3de7f99acfba9b5bcc7df3394dc5272ace316c62c2331cd2e3091a80c257bd2e` to detect fixture drift; never calls `seal_keyring` in the passing recovery path; authenticates the prebuilt envelope with real recovery code, native Windows `CREATE_NEW` private file restore, then starts a **fresh Python process** using product `configured_keyring` to decrypt both prebuilt media ciphertexts, check SHA-256 and HMAC locator values. Negative checks: wrong password, envelope tamper, truncate, invalid JSON before write, existing destination no-overwrite, relative target deny, media ciphertext tamper, and missing retained media key => explicit `KEY_UNAVAILABLE` for the historical artifact. Existing F5B-D3 Windows junction and ACL tests remain mandatory in same job.
- `.github/workflows/lot06-phase2-b06-integration-fue.yml` reuses existing GitHub-hosted `windows-2022` runner and exact-GITHUB_SHA fail guard for one new F5B-D4b step; both new files added to push path trigger.
- No production backend code modified, no real patient data/real keys, no deployment or merge.

**Evidence standard and unresolved:** This is *independent of fixture generation during the CI job*, with a fixed expected oracle, NOT an independently held offsite backup, operator/custodian attestations, a truly persistent cabinet Windows host, full SQLCipher DB+media+ACK disaster recovery, or proof against concurrent Windows directory parent swaps. A fresh Python process is NOT a real on-prem service restart. `F5B_D4B_WINDOWS_PREBUILT_ORACLE_FUE=CI_PENDING`; `F5B_D4_INDEPENDENT_OPERATOR_DRILL=NOT_RUN`; `OFFSITE_ESCROW_VERIFIED=false`; `FULL_CABINET_RESTORE_VERIFIED=false`; `WINDOWS_PARENT_SWAP_RISK=OPEN`; `READY_TO_MERGE=false`; `PRODUCT_READY=false`; `CLINICAL_GO=false`. Only call GREEN after checking CI job step/log markers on the new exact final SHA; no premature certification.


## PRE F5B-D4b Windows CI RED repair — 5 novembre 2026

Le run exact SHA [#42108539008](https://github.com/hraaaaf/Digital_crown/actions/runs/42108539008), job Windows `127530228469`, a exécuté F5B-D3/D2 avec tous les marqueurs PASS avant le nouveau F5B-D4b, mais celui-ci échoue **avant restauration** en `AssertionError: FIXTURE_DRIFT` à la ligne 28 du test. La version GitHub du fixture fait 1970 octets, CRC32 `41fb7785`, identique au vecteur pré-validé hors CI ; le SHA local de référence est `3de7f99a...`. Cause probable sur GitHub Windows checkout : conversion automatique LF→CRLF sur fichier JSON texte. Vérifier/réparer *la canonisation explicite des fins de ligne avant comparaison SHA* sans supprimer la preuve d'intégrité ni changer l'oracle précommis ; rejeter les CR non conformes, sans aucun assouplissement du contrôle. Nouveau HEAD et CI Windows exigés avant GREEN. `F5B_D4B=RED_AT_FIXTURE_PIN` ; `CLINICAL_GO=false`, pas de merge/deploy.

## POST F5B-D4b Windows RED fixture checksum repair (CI pending), 2026-11-05

Previous exact-head CI #42108539008 Windows job #127530228469 failed at **first line** of new F5B-D4b test (`FIXTURE_DRIFT`), before decrypt/restore. Source fixture on GitHub matched locally frozen public test vector byte-for-byte (1970 bytes, CRC32 `41fb7785`); probable cause is `windows-2022` Git checkout LF→CRLF conversion on JSON text. The existing F5B-D3/D2 Windows checks passed and must remain intact. Patch `88665c8`: normalize **only CRLF→LF** and explicitly reject any remaining bare CR *before* checking the unchanged pinned fixture SHA-256 `3de7f99acfba9b5bcc7df3394dc5272ace316c62c2331cd2e3091a80c257bd2e`; JSON parsed from verified canonical bytes. **No weakening or removal of SHA checks, no test-data change, no product code touched.** Await NEW exact-final-HEAD Windows CI and verify ALL F5B-D4b markers before any GREEN. `F5B_D4B=CI_PENDING_AFTER_FIX`; `F5B_D4_INDEPENDENT_OPERATOR_DRILL=NOT_RUN`; `READY_TO_MERGE=false`; `CLINICAL_GO=false`; no merge, release, or deployment.


## PRE F5B-D4c — Portability P1 gate repair and legitimate UI review, 2026-11-05

Owner instruction: "Je ne valide que ce qui touche a l'UX/UI ! Vas-y corrige les deux." Baseline PR #1210 DRAFT/OPEN exact head `1251b8826fa7e7839ead6a0c91acef20205fde65`; B06 #42109352876 SUCCESS 3/3 and Scope #42109365094 SUCCESS. Portability #42109365300 FAILED all Windows/macOS/Ubuntu at `scripts/portability_p1_check.py` due four direct `os.name` uses in `clinical_media_crypto_v2.py`, `windows_keyring_handle_probe.py`, `windows_keyring_restore.py`. Fix via **existing** `backend.core.platform.get_platform_adapter()` OS abstraction, keeping fail-closed security and new exact-head tests.

Visual approval #42109359083 FAILED because approval is SHA-bound and reset after new HEAD. PR inventory includes genuine product-visible TSX under `frontend/src/features/patients`; **only the user may human-approve UX/UI**; auto-green or label fabrication prohibited. Existing protected `pull_request_target` workflow executes trusted *default branch*, not PR copy. Inspect UI evidence and prepare review; no visual approval bypass.

No merge, deploy, publish, clinic or patient data. `READY_TO_MERGE=false`, `PRODUCT_READY=false`, `CLINICAL_GO=false`. Single canonical LOT06 document maintained PRE/POST.

## POST F5B-D4c — Portability P1 refactor + strictly owner-only visual approval, 2026-11-05

**Applied only in PR #1210 DRAFT, no merge:**
- `backend/services/clinical_media_crypto_v2.py` routes Windows versus supported POSIX keyring reader through **existing** `backend.core.platform.get_platform_adapter()` (`PlatformAdapter.is_windows`, `kind in {"linux","macos"}`); unknown OS fail-closed. Existing native Windows ACL/reparse and POSIX `O_NOFOLLOW` semantics remain mandatory.
- `backend/services/windows_keyring_handle_probe.py` and `backend/services/windows_keyring_restore.py` use `get_platform_adapter().is_windows` instead of direct `os.name` (no change to native Win32 primitives/ACL policy or error codes).
- Standalone F5B-B1/B2 Windows probe FUE `isolated_fue_lot06c/windows_f5bb_handle_probe_fue.ps1` now supplies a **synthetic backend namespace package** before loading the real module. This avoids importing `backend/__init__.py` / unrelated SQLAlchemy in the lightweight Windows CI while importing **real** `backend/core/platform.py`. Same adversarial assertions, no bypass.
- `.github/workflows/lot06-phase2-b06-integration-fue.yml` adds the native probe source and Windows harness to push triggers: all future changes to these security files must rerun B06 Windows FUE (was missing).
- **Human UI gate audited, not forged or disabled.** Trusted `pull_request_target` workflow runs its script from default branch, and PR #1210 really changes visible `frontend/src/features/patients/` components. Thus `UI_HUMAN_APPROVAL=PENDING_OWNER_REVIEW` is the valid status even if backend/docs-only commits changed HEAD. The owner only validates UX/UI; no request for their technical approval. Reviewer must inspect product-visible changes and independently supply explicit authorized label event to re-approve exact HEAD. No auto-approval, no label spoof, no altered privileged workflow.

**Before technical certification**: old source HEAD `1251b8826fa7e7839ead6a0c91acef20205fde65` had Portability P1 RED all three OS in #42109365300 for four direct `os.name` accesses; UI human gate RED for revoked SHA-bound approval. **Current final CI outcome = PENDING at doc update**; verify exact FINAL HEAD and Portability all Windows/macOS/Linux, B06 3/3 and F5B-D4b markers, Scope. Do not claim GREEN until observed.

**Safety:** `CLINICAL_GO=false`, `READY_TO_MERGE=false`, `PRODUCT_READY=false`, `F5B_D4_INDEPENDENT_OPERATOR_DRILL=NOT_RUN`, `OFFSITE_ESCROW_VERIFIED=false`, `WINDOWS_PARENT_SWAP_RISK=OPEN`, `FULL_CABINET_RESTORE_VERIFIED=false`. No release, merge, Vercel, cabinet migration, patient data, or clinical enable.


## PRE B06 UX separation / theme inheritance — 2026-11-05

User mandate: all UI colors must inherit from application semantic theme tokens; no DEV/LAB/mode engineering labels, SHA-256 hashes or internal crypto receipt IDs are to be visible to the dentist on a product patient screen. Owner is the sole human approver of actual UX/UI; agents maintain all technical gates without fabricating UI signoff.

Source audit on exact HEAD `7406ab72af6d5c9bf734579273ff40b67a795066` confirmed `frontend/src/features/patients/components/ImagingAcquisitionProductReviewV15.tsx` is mounted on real patient Media route and displays `SHA-256 : {capture.digest}`, internal receipt ID and `Activation cabinet non autorisée.`. Those are implementation/governance details, not clinical UX. `frontend/src/features/patients/PatientDetailsInner.tsx` still contains unrelated but same visible patient page orthodontic CTA with `bg-[#003380]`/`hover:bg-[#002266]`. The isolated LAB `ImagingAcquisitionReviewPanelV15.tsx` is not mounted on patient route; retain LAB warnings there, keep isolation. Scope: copy/presentation and theme token CSS only; preserve digest verification, idempotent ACK, ACL/crypto/gates; add existing React FUE asserting no debug copy leaks. CI on exact final SHA required. No merge/deploy or clinical authorization. `READY_TO_MERGE=false`; `PRODUCT_READY=false`; `CLINICAL_GO=false`.


## POST B06 UX token inheritance + no DEV leakage in dentist-facing UI — 2026-11-05

Implementation on PR #1210 DRAFT, with synthetic-only previews and unchanged clinical safety boundary:

1. **No engineering data in practitioner copy:** `frontend/src/features/patients/components/ImagingAcquisitionProductReviewV15.tsx` no longer renders full SHA-256 digest, internal signed `DC06-...` receipt ID, or `Activation cabinet non autorisée` in success messaging; it never prints key/challenge identifiers. Retained **all** cryptographic digest checks, verified image conditions, two independent patient markers, signed ACK validation, idempotent receipt lookup after lost reply, and explicit no-persist behavior for the non-durable path. Copy now states clearly when image is saved and when it is **not** saved, without implementation jargon. Clinical UX button labels and confirmation copy were made practitioner-facing (`Ajouter l’image au dossier`, `Terminer la vérification`).
2. **Theme tokens only:** fixed hardcoded orthodontic CTA color `bg-[#003380]`/hover `bg-[#002266]` in `PatientDetailsInner.tsx` to `bg-primary text-on-primary hover:bg-secondary`, inheriting `--primary`, `--text-on-primary` and `--secondary` from active theme; replaced 7 undefined `bg-card-bg` classes on the patient page and 1 in acquisition review with the declared Tailwind token `bg-card` mapping `--card-bg`; replaced hardcoded LAB warning `text-amber-700` with semantic `text-warning`. No new fixed color values.
3. **FUE regression updated** in `ImagingAcquisitionProductReviewV15.test.tsx`: asserts both durable ACK and lost-response recovery retain safe clinical message but never expose internal `receipt_id`, `SHA-256`, `Reçu durable`, `Activation cabinet non autorisée`. Existing consent/previews/digest/token/duplicate negative tests unchanged in purpose; button assertions match revised practitioner copy.
4. **LAB isolation preserved:** `ImagingAcquisitionReviewPanelV15.tsx` remains a LAB-only component **not mounted in the actual patient route**. It deliberately retains strict LAB warning *in that isolated surface only*; this does not permit LAB screens in a dentist's cabinet. The product actually mounts `ImagingAcquisitionProductReviewV15`, not the LAB component. No code path to enable LAB added.

**Baseline source HEAD** `7406ab72af6d5c9bf734579273ff40b67a795066`. Changes: UI copy `7356a5e`, tests `edf32c8`, patient CTA `0412771`, isolated LAB warning `5bcd63f`, semantic card review `eb38872`, semantic card patient `5b7b487`, clinical copy follow-up `f6db551`, updated tests `2dff5a2`. Static audit at `2dff5a2` confirmed zero local hex utility colors, zero `bg-card-bg` across three reviewed components, and no identified developer text in the mounted product review. **Do not equate static audit with whole-app visual certification or browser screenshot evidence.**

**Exact-HEAD certification pending** after this POST documentation commit: verify B06 3/3, Scope, Theme waves and visual approval gate; user is sole UX/UI human approver. Do NOT forge `visual-approved-by-achraf`, autoapprove, merge, install, deploy, or enable clinic. The real physical independent restore drill, parent-swap risk and full recovery remain OPEN. `READY_TO_MERGE=false`; `PRODUCT_READY=false`; `CLINICAL_GO=false`.


## PRE B06 practitioner UX polish / tokens and strict two-marker identity, 2026-11-05

Owner asked "Corrige alors" after critical review of four demonstrative HTML/Chromium illustrations rated 7/10. Target actual `frontend/src/features/patients/components/ImagingAcquisitionProductReviewV15.tsx` mounted on patient Media tab, PR #1210 OPEN/DRAFT baseline HEAD `da0e6887d70580de974fead1e47e0594c58efcad`. Preserve B06 signed ACK, image size/mime/digest verification, binding to exact selected patient, *two manually typed* dossier and birth date, checkbox and explicit human action, fail-closed unverified image and challenge, no automatic patient association. Do **not** prefill either identity field or weaken guard merely to reduce friction.

Improve **visual** cognitive load with clear preview → patient identity → confirmation hierarchy, readable mobile one-column and desktop two-column layout, visually distinct primary/secondary actions and focus/disabled states. All colors must inherit existing theme tokens, no hex values or DEV/LAB artifacts on the dentist surface. Add React assertions for hierarchy/visible UX and retained gates. No backend, auth, merge, deployment, product/clinical authorization, or fabricated visual approval. B06/Portability/Scope were green only on prior SHA; new exact-head FUE required; `READY_TO_MERGE=false`; `CLINICAL_GO=false`.


## POST B06 practitioner UX hierarchy correction (desktop / mobile), 2026-11-05

PR #1210 DRAFT, unmerged; baseline SHA `da0e6887d70580de974fead1e47e0594c58efcad`. Following the owner's "Corrige alors" after critique (poor visual image/identity/action hierarchy and perceived burden of two identity fields), **implemented in actual mounted React component** `frontend/src/features/patients/components/ImagingAcquisitionProductReviewV15.tsx`:

- Information hierarchy now 1. `Contrôler l'image` (image and verified/unavailable status) → 2. `Vérifier l'identité du patient` (distinct selected-patient summary, then two clearly labelled mandatory input controls) → explicit confirmation checkbox → visually dominant primary CTA and secondary Cancel. Responsive one column on mobile, two columns on desktop.
- Refined pending capture, failure, non-durable reviewed and durable stored states with theme-semantic `bg-primary`, `text-on-primary`, `hover:bg-secondary`, `bg-card`, `bg-background`, `border-border-main`, `bg-danger-surface`, `bg-warning-surface`, `bg-info-surface`, `bg-success-surface`. No hex literal or independent color; keyboard `focus-visible`, native disabled and 44px minimum actions.
- **No clinical gate weakened:** no prefilling, no removal of typed dossier and typed date-of-birth, no bypass of checkbox/image onLoad/SHA-256/mime/size, patient binding, session/challenge, durable signed-ACK and no-repeat-on-lost-reply rules. The UI retains a *different message for transient-only verified versus durable associated* (no false saved indicator), and internal SHA/receipt IDs are not printed.
- Updated real React test suite `ImagingAcquisitionProductReviewV15.test.tsx` to assert two step headings, empty required identity fields, semantic primary action and no visible LAB/dev strings; all prior security/negative scenarios preserved. Test heading escaping corrected in `c72d185`.

**Code commits:** `13b1beb` product hierarchy + responsive tokenized UI; `d9df3a9` regression assertions; `c72d185` test string fix. **Exact HEAD CI = PENDING** until post-documentation workflow results are read. Owner solely validates UX/UI from actual application screenshots; HTML demonstration screenshots shown earlier are not accepted as React product evidence. `READY_TO_MERGE=false`, `PRODUCT_READY=false`, `CLINICAL_GO=false`; no release/deploy/merge.


## PRE B06 React Chromium screenshot FUE (real mounted component, synthetic API), 2026-11-06

Owner says "Oki go": run real screenshot acceptance evidence, not previously shown hand-rebuilt static HTML. Baseline PR #1210 DRAFT exact head `75a6b2f17d4c6e5a0b117a1968d75316e0c080f0`; B06 Windows/SQLCipher/UI 3/3 GREEN, Portability Windows/macOS/Linux 3/3 GREEN, Scope Gate and Theme Waves 09/10/11 GREEN, Staff Migration GREEN, no technical runs active on this baseline. Owner's visual approval remains missing; the trusted `pull_request_target` human gate is fail-closed as intended.

Plan: add bounded disposable GitHub Actions screenshot workflow with `npm ci` + Chromium Playwright + Vite using exact **product source** `frontend/src/features/patients/components/ImagingAcquisitionProductReviewV15.tsx` and **real theme CSS** `frontend/src/index.css`. Use ONLY test-mode synthetic local PNG/dossier/short-lived mock API, explicitly no cabinet backend, no patient data, no clinical write. Capture pending, blank mandatory dual-ID review, verified image + manually filled IDs/checkbox (no commit) at 390/430/1280 plus dark-theme spot check. Assert responsive overflow, both fields, disabled-before / enabled-after, semantic token differences, no DEV strings, browser exceptions and exact SHA, upload timestamped artifact. This is real browser **React component** evidence but NOT an end-to-end patient page or actual hardware. Complete new exact-HEAD FUE; keep single GitHub canonical and same Notion canonical updated PRE/POST. No merge, Vercel, clinic activation, or fabricated human approval; `READY_TO_MERGE=false`, `CLINICAL_GO=false`.


## POST B06 actual React Chromium visual-evidence harness — 2026-11-06

To satisfy owner "Oki go" after technical green, added:
- `frontend/scripts/capture-lot06-b06-react-visual.mjs`: gated `ENVIRONMENT=test` + `DIGITALCROWN_ISOLATED_RUNTIME=1` + `DC06_B06_VISUAL_LAB=1` + exact source SHA. Starts localhost Vite and Chromium with the **real compiled product** `ImagingAcquisitionProductReviewV15.tsx` and `src/index.css`, substituting **only** the API import for one synthetic short-lived PNG, typed synthetic patient dossier/DOB, and one non-durable/locked mock capture. It **never calls commit**, loads the same SHA-verified image in the browser and checks two blank inputs + disabled CTA, then enters both labels and explicit checkbox to prove the CTA only becomes enabled. Captures pending (390/1280), pre-confirmation review (390/430/1280, dark390), ready-to-confirm (390/1280), plus machine-readable responsive/theme/DEV-leak report. Direct sample fixtures are ephemeral runner files and are deleted after use. No runtime/dev toggle in dentist app, no color literal in the component, no real patient/cabinet/backend, no actual media association.
- `.github/workflows/lot06-b06-react-visual-evidence.yml`: disposable Ubuntu GitHub Actions runner installs locked frontend packages and Playwright Chromium, verifies exact `github.sha`, renders directly from TSX and uploads `lot06-b06-actual-react-chromium-visual` for 14 days.

This is **genuine mounted React component** browser screenshot evidence on a synthetic API, not a reconstruction of JSX in HTML and not authenticated whole-app patient integration; it does NOT confer clinic approval, real native device FUE, or owner's visual signoff. Existing B06 and portability checks still required on the final SHA; trusted `pull_request_target` owner visual gate remains fail-closed. Branch PR #1210 DRAFT/unmerged, no deploy/release/activation. At this documentation POST, visual CI run #42135695175 was QUEUED for code candidate `5bbfd628`; **the current final HEAD and its CI will change with this documentation commit**, so do not claim PASS until later verified on the final exact HEAD. `READY_TO_MERGE=false`, `PRODUCT_READY=false`, `CLINICAL_GO=false`.


## PRE B06 visual CI JavaScript syntax repair — 2026-11-06

Visual CI #42135782142 failed **at Node parse before page/browser capture** in `frontend/scripts/capture-lot06-b06-react-visual.mjs:188`, `SyntaxError: missing ) after argument list`. The selector `document.querySelector('[aria-label="Revue d\\'acquisition non attribuée"]')` has an incorrectly escaped apostrophe inside the JS literal. The prior `npm ci` and Playwright Chromium installation succeeded. This is purely the **synthetic visual screenshot harness**, not product JSX or B06 clinical code. Scope: use an unambiguous syntax-safe `section[aria-label]` selector for the visual overflow assertion; add `node --check` **before expensive npm/Chromium installation** to catch future parser regressions. Do not change source product component or any clinical gate; re-run exact final HEAD CI. B06 main #42135782511 still independent. Approval remains solely with owner, no fake GREEN/merge/deploy.


## POST B06 screenshot harness syntax repair, 2026-11-06

GitHub run #42135782142 (source HEAD `5ff29b954d3ba393b4762c73a0e50349d168ac7d`) FAILED at Node syntax compilation **before** Chromium capture, `SyntaxError: missing ) after argument list` at line 188 of screenshot harness: double-backslash before apostrophe inside single-quoted `document.querySelector(...)`. Packages/Chromium installation was successful, no screenshot artifact generated. Narrow corrected `frontend/scripts/capture-lot06-b06-react-visual.mjs` to select the existing unique `section[aria-label]` for responsive overflow assertion without string-escaping pitfalls; workflow now runs fast `node --check` before `npm ci` / Chromium download. Real product React component, security/identity controls, CSS theme and mock API contract **unchanged**. Script source updated commit `4a6e789`; workflow parser guard `7ddc815`. New exact-final-head tests and screenshot artifact still required; do not claim PASS without completed CI and actual file. PR DRAFT/unmerged; owner UX approval pending, no clinic use/release/merge/deploy.


## POST B06 source-exact React Chromium screenshot infrastructure, 2026-11-06

At owner command "Oki go" the original PR #1210 HEAD `75a6b2f17d4c6e5a0b117a1968d75316e0c080f0` had **B06 3/3 / Portability 3/3 / Scope / Theme 09–11 / Staff migration** all completed SUCCESS and the owner-only visual approval gate correctly fail-closed. A real source-importing synthetic React/Chromium screenshot harness already existed: `frontend/scripts/capture-lot06-b06-react-visual.mjs` plus `.github/workflows/lot06-b06-react-visual-evidence.yml`; this was reused rather than replicated. An unnecessary duplicate runner was removed immediately. The existing workflow was hardened: checkout explicitly pins `ref: ${{ github.sha }}`, and upload artifacts now uses `if-no-files-found: error`, preventing green without visual images.

The existing harness renders **actual** `ImagingAcquisitionProductReviewV15.tsx` and real `frontend/src/index.css` through Vite+React with an isolated *in-memory synthetic API only*; generates sample PNG, computes real SHA-256, then captures desktop 1280px, mobile 390/430px and dark theme; tests empty dual-marker inputs, disabled action until both manually typed plus checkbox, responsive overflow, no debug labels and different computed token colors between light/dark. It never makes a real clinical write, and is not a full clinic-authenticated route/hardware test. Images are uploaded as Actions artifact `lot06-b06-actual-react-chromium-visual`, with SHA in `summary.json`. Runner uses `ENVIRONMENT=test`, `DIGITALCROWN_ISOLATED_RUNTIME=1`, `DC06_B06_VISUAL_LAB=1`; no production flag or runtime LLM.

**Evidence status at writing:** [GitHub visual workflow run #42138385460](https://github.com/hraaaaf/Digital_crown/actions/runs/42138385460) still QUEUED, so **no screenshot successfully verified yet**, and no owner UX/UI approval. New final HEAD must be rechecked after this canonical POST commit; do not inherit previous technical CI or claim GREEN without matching SHA. `READY_TO_MERGE=false`, `PRODUCT_READY=false`, `CLINICAL_GO=false`. No merge, deployment, patient data, production enablement or human approval spoofing.


## PRE B06 additional visual FUE: locale FR, viewport 768, text scaling 200% — 2026-11-06

Reprise depuis Notion canonique: exact source HEAD `4c434a043d035e75cb77f6ae2eba319f9260e0ff`; B06 #42138582816 (3/3 success), Chromium #42138582846 (success; 8 PNG + summary, artifact 13466064540). Owner UX/UI approval is still PENDING. The existing images reveal browser date input shown as `mm/dd/yyyy` because the disposable Chromium context did not set a French locale. They do not exercise 768px or 200% text scaling, both relevant to the Digital Crown visual gate.

**Goal:** Extend the one existing isolated React Chromium screenshot harness (not create another runner) to capture and assert 768px, French browser locale and a 390px / 200%-text-scale scenario with no horizontal overflow, preserving two EMPTY manually typed identifiers, checkbox, verified image and no clinical writes. Only modify `frontend/scripts/capture-lot06-b06-react-visual.mjs`. No API/clinical backend/product change. FUE-0 syntax and exact-new-HEAD CI plus inspectable PNG+JSON required. Synthetic-browser evidence does NOT assert the actual operator browser locale or replace owner approval. Do not fabricate human signoff, merge, deploy or install. `READY_TO_MERGE=false`; `PRODUCT_READY=false`; `CLINICAL_GO=false`.


## POST B06 additional visual FUE harness (candidate; final-head CI pending) — 2026-11-06

The **existing** `frontend/scripts/capture-lot06-b06-react-visual.mjs` is the only visual runner. Commit `56488c89c0e78ff2ba4cdba2965bd8f84946154a` extends Chromium variants from 4 to **6**: original 390/430/1280 light + 390 dark, plus 768 light and 390 light with explicitly applied 200% root-text scaling. All browser contexts use `fr-FR` locale and the script requires a French browser-language report; it asserts actual computed root font size >=31.5px in 200% probe, no horizontal/panel overflow, actual loaded verified synthetic image, two **initially empty** manually typed patient markers, disabled CTA before checkbox, enabled only after checkbox, zero commit, no visible DEV copy and genuine light/dark theme difference. Full-page PNG+JSON artifacts retain exact source HEAD and now record locale/textScalePercent. Product frontend/API/clinical backend code and theme tokens are **unchanged**; this is a synthetic-browser probe, not full authenticated cabinet E2E, physical scanner or operator UAT.

**Evidence gate:** new final commit from this POST requires `node --check`, B06 Windows/SQLCipher/React exact-SHA CI and **actual** Chromium run/artifact inspection; never inherit previous SHA success. If 200% exposes overflow, correct only the demonstrated issue and rerun. The native date-control format is locale-dependent, so a French Chromium screenshot is not proof of browser settings on an installed clinic workstation. **UX_UI_OWNER_APPROVAL=PENDING**; `READY_TO_MERGE=false`; `PRODUCT_READY=false`; `CLINICAL_GO=false`. No merge, deploy, clinic or human approval spoofing.


## PRE J4/F5B-D4c — Windows held-parent rename and attribute-write adversarial FUE, 2026-11-06

Owner GO “Vas y J4” on PR #1210 baseline `ce017616a0670d36c3521d14d55e8ba47c566aff` (Draft/unmerged; UX approval gate was GREEN on that earlier SHA). Actual native `windows_keyring_restore.py` retains checked, no-write/no-delete-sharing parent directory handles during CREATE_NEW, but prior Windows adversarial test only covers an already-existing junction and is not a live independent parent-swap proof. F5B-D4b has a prebuilt synthetic ciphertext+fixed-oracle fresh-process restore FUE, **not** separate offsite custody or human participation. J4 action is bounded to extending the existing `isolated_fue_lot06c/windows_f5bd2_private_restore_fue.ps1` Windows runner: separate child process must fail renaming the held parent and fail opening it with WRITE_ATTRIBUTES; verify its namespace is unchanged, then successfully restore only into the original parent. Do not add a product code hook or loosen path/ACL protections. New exact-SHA Windows 3/3 and Scope/Portability CI required. This checks a narrow sharing barrier, **not** proof against all concurrent junction swaps or offsite real-host recovery. No operator/custodian signoff, no patient, merge, deploy or clinical release. `F5B_D4_INDEPENDENT_OPERATOR_DRILL=NOT_RUN`, `OFFSITE_ESCROW_VERIFIED=false`, `WINDOWS_PARENT_SWAP_RISK=OPEN`, `READY_TO_MERGE=false`, `CLINICAL_GO=false`.


## POST J4/F5B-D4c — Windows live held-parent adversarial FUE added (exact-HEAD CI pending), 2026-11-06

**Code commit** \`bb21ed496c27ba1b30abcde44be27af69979f483\` modifies only the EXISTING \`isolated_fue_lot06c/windows_f5bd2_private_restore_fue.ps1\` Windows harness. One fresh \`held-parent\` directory is opened using precisely the production RESTORE parent-handle flags: \`FILE_READ_ATTRIBUTES | READ_CONTROL\`, \`FILE_SHARE_READ\` (without WRITE/DELETE sharing), \`FILE_FLAG_OPEN_REPARSE_POINT | FILE_FLAG_BACKUP_SEMANTICS\`. While it is held open, an **independent child Python process** (a) tries to rename the parent and (b) tries \`CreateFileW(FILE_WRITE_ATTRIBUTES)\` on that directory; any successful rename or write-handle open fails the CI. The parent namespace must stay unchanged; the real production \`restore_new_private_file\` must create its synthetic keyring in the original directory and its content must match. Prints three exact markers only after corresponding assertions: \`DC06_J4_PARENT_RENAME_DENIED_PASS\`, \`DC06_J4_PARENT_WRITE_ATTRIBUTES_DENIED_PASS\`, \`DC06_J4_PARENT_NAMESPACE_AND_RESTORE_PASS\`. Uses no real key or patient data, no production hook, no change to \`windows_keyring_restore.py\`, no token or UI edit. Static check: 3 balanced PowerShell here-strings, all markers in existing harness; **Windows run not yet confirmed** at this documentary POST.

**Scope/limit:** proves two *specific* Windows sharing barriers when a parent-directory handle is held, but not that all cross-directory reparse races, unusual filesystem features, or an external attacker are eliminated. Never upgrade \`WINDOWS_PARENT_SWAP_RISK\` to CLOSED solely from this test; threat review + more adversarial evidence required. Independent offsite operator/custodian drill is not possible on synthetic ephemeral GitHub runner and remains \`NOT_RUN\`, external custody unverified. Existing prebuilt fixed-oracle Windows FUE remains separate and should still run.

**Exact-SHA governance:** The PRE canonical commit was \`d86fe60c596796ef1fcf3a449cf77a0e9a05132f\`, test commit \`bb21ed496c27ba1b30abcde44be27af69979f483\`; this POST creates a **new final SHA**, must verify full Windows B06 3/3, Scope, Portability and owner visual gate on that exact new HEAD. Prior visual approval from \`ce017616\` cannot certify any new HEAD without an authenticated new label event even though product UI is unchanged. Keep PR #1210 Draft/unmerged, do not merge/deploy/enable.

**Release state unchanged:** \`F5B_D4_INDEPENDENT_OPERATOR_DRILL=NOT_RUN\`; \`OFFSITE_ESCROW_VERIFIED=false\`; \`INDEPENDENT_ORACLE_VERIFIED=false\` for separate custodian; \`FULL_CABINET_RESTORE_VERIFIED=false\`; \`WINDOWS_PARENT_SWAP_RISK=OPEN\`; \`READY_TO_MERGE=false\`; \`PRODUCT_READY=false\`; \`CLINICAL_GO=false\`.

**NEXT:** confirm exact-SHA Windows job markers and all CI runs, record audit evidence. Any RED is a real blocker requiring narrow targeted fix. Then independent human/custodian drill when authorized station available, without hallucinating signoff.


## PRE J4/F5B-D4c exact-SHA Windows RED diagnosis, 2026-11-06

Run [#42193603430](https://github.com/hraaaaf/Digital_crown/actions/runs/42193603430) at `411d5ac83e2e7c172da43842a88ef134907c811d`, Windows job `127811748215`: all prior Windows SCM/ACL/read/product and offline recovery checks including parent-junction refusal PASS, but new J4 child adversarial subprocess failed with `subprocess.CalledProcessError`. The current harness uses `capture_output=True, check=True` and suppresses the child stderr/stdout, so there is **no evidence yet** distinguishing a real successful rename/WRITE_ATTRIBUTES attack from a test failure. Downstream fixed-oracle D4b was SKIPPED because of this RED. Narrow next change: surface bounded **non-sensitive error class and marker state** from the child on failure, still fail-closed, with no change to product cryptography or Windows security. Re-run exact-SHA CI. J4 is RED, not certified. `WINDOWS_PARENT_SWAP_RISK=OPEN`, `READY_TO_MERGE=false`, `CLINICAL_GO=false`.


## POST J4/F5B-D4c diagnostic-only RED hardening — 2026-11-06

At exact HEAD `411d5ac83e2e7c172da43842a88ef134907c811d`, GitHub Windows run #42193603430 job #127811748215 reached the J4 child after all prior F5BD2 positive, ACL, and static-junction adversarial FUE passed. Child exited non-zero, but `subprocess.run(check=True, capture_output=True)` concealed its reason; cannot claim parent rename/write succeeded or denied. Diagnostic repair commit `77d0ef5b092010a83ee5a1dcb0563a5a2061f1e3` changes only the same Windows FUE script: `check=False`, if non-zero print ONLY a bounded recognized failure tag / exception class and two booleans reporting whether deny markers were seen, then still raise fail-closed. No test expectation, native production security, secrets, product UI, patient or backend code changed. **New exact-final-head B06 Windows CI required** to identify attack behavior; no GREEN until the new Windows job passes all three new J4 markers. Parent swap risk remains OPEN, offsite independent custodians not tested. `F5B_D4_INDEPENDENT_OPERATOR_DRILL=NOT_RUN`, `OFFSITE_ESCROW_VERIFIED=false`, `FULL_CABINET_RESTORE_VERIFIED=false`, `READY_TO_MERGE=false`, `PRODUCT_READY=false`, `CLINICAL_GO=false`. Owner's old SHA-bound UI approval is stale after code commits and must not be presented as a success on the new HEAD; do not merge/deploy/activate.


## PRE J4/F5B-D4d — Confirmed Windows parent rename: handle-relative FILE_CREATE remediation, 2026-11-06

New exact-head [Windows run #42194390241](https://github.com/hraaaaf/Digital_crown/actions/runs/42194390241) at `34c81429d7b53708bd8d2b44d9d4c3d7f7a8474f`, job `127814195105`, unambiguously prints `DC06_J4_ATTACKER_DIAGNOSTIC_PARENT_SWAP_RENAME_ALLOWED`. A separate child has actually renamed the previously handle-checked directory despite `FILE_SHARE_READ` only. The old assumption that holding the handle blocks all namespace rename was false. **P1 fail-closed risk; J4 RED.** `windows_keyring_restore.py` currently re-resolves the final filename through `CreateFileW(str(path))` after checking parents, admitting a pathname-swap window. PRE scope: replace only final filename creation with user-mode Windows `NtCreateFile` using `OBJECT_ATTRIBUTES.RootDirectory=opened_checked_parent_handle`, exactly one file name, `FILE_CREATE` exclusive, no reparse following, same protected user+SYSTEM security descriptor. Never fall back to the unsafe absolute filename. The current synthetic Windows harness must prove a rename + malicious replacement junction cannot redirect a relative file create outside the **original opened parent handle**, while existing ACL, replay, wrong key, junction and D4b tests remain mandatory. This mitigation will need new exact-SHA Windows CI; no claim of full Windows/NTFS threat proof, offsite recovery, human custody or clinic activation. `WINDOWS_PARENT_SWAP_RISK=OPEN`, `READY_TO_MERGE=false`, `CLINICAL_GO=false`.


## POST J4/F5B-D4d — handle-relative Windows recovery create + adversarial trap FUE (exact-HEAD CI pending), 2026-11-06

The earlier Windows run [#42194390241](https://github.com/hraaaaf/Digital_crown/actions/runs/42194390241), job `127814195105`, **proved a parent directory can be renamed by another process while a FILE_SHARE_READ-only checking handle remains open**: `DC06_J4_ATTACKER_DIAGNOSTIC_PARENT_SWAP_RENAME_ALLOWED`. The product's former `CreateFileW(str(path))` final create would re-resolve the untrusted old parent path. This is a real P1 test failure, not a harmless harness issue.

**Production remediation candidate** `backend/services/windows_keyring_restore.py`, commit `b8dfff563e424f27c8b54eca532828cc88c9857e`: replace only final `CreateFileW(str(path))` with a private `_create_new_under_checked_parent(parent_handle, leaf, protected_descriptor)` that invokes documented Windows user-mode `NtCreateFile` with `OBJECT_ATTRIBUTES.RootDirectory=opened[-1]`, one relative leaf, exclusive `FILE_CREATE`, no-follow final reparse, no text-path fallback, same protected user+SYSTEM SDDL, and existing WriteFile/Flush/Close path. Ntdll failure refuses `RESTORE_CREATE_NEW_DENIED`. All original path checks, protected ACL, max payload, parent reparse checks, no-overwrite semantics remain. No product activation / patient data / frontend token changes.

**Adversarial test** `isolated_fue_lot06c/windows_f5bd2_private_restore_fue.ps1`, commit `89a5264bf2248d94b8e628c654b7592ba176ec93`: same real Windows parent handle is held, independent child **actually renames** the legitimate parent; a junction is placed at the obsolete path pointing to an outside synthetic trap folder. The **same production native helper** is called relative to the original handle with the private owner/current-user+SYSTEM descriptor, verified WriteFile/Flush, and product native nofollow ACL readback. PASS only if the keyring is in the renamed ORIGINAL directory and no file is present in the trap junction target. Three markers: `DC06_J4_PARENT_RENAME_CONFIRMED_PASS`, `DC06_J4_ATTACKER_REPLACEMENT_JUNCTION_CONFIRMED_PASS`, `DC06_J4_HANDLE_RELATIVE_PARENT_ISOLATION_PASS`. Any setup, descriptor, NtCreateFile or assertion failure must RED. This is a **bounded exact-source lab proof of final-create binding**, not proof that every upstream ancestor traversal, NTFS feature or external offsite restore is secure.

**Do not claim GREEN without new exact-final-HEAD Windows B06 3/3, Scope and Portability runs.** Previous owner UI visual approval relates only to `ce017616` and is not proof for new HEAD. `F5B_D4_INDEPENDENT_OPERATOR_DRILL=NOT_RUN`; `OFFSITE_ESCROW_VERIFIED=false`; `FULL_CABINET_RESTORE_VERIFIED=false`; `WINDOWS_PARENT_SWAP_RISK=OPEN` pending new proof and threat review; `READY_TO_MERGE=false`; `PRODUCT_READY=false`; `CLINICAL_GO=false`. PR #1210 Draft/unmerged, no deploy, real keys, actual patient or cabinet.


## PRE J4/F5B-D4e — Exact Windows ctypes UNICODE_STRING type repair after RED, 2026-11-06

**Evidence:** PR #1210 final candidate `e436357c2782a74c5c9432bc5ce2cde1b1a4ee62`; [B06 Windows run #42196021246](https://github.com/hraaaaf/Digital_crown/actions/runs/42196021246), job #127819359406, **FAILED** inside existing F5B-D2 positive restore setup, not at parent-swap trap: Python `TypeError: incompatible types, c_wchar_Array_14 instance instead of c_wchar_p instance`, on `_UnicodeString(len(encoded),len(encoded)+2,name_buffer)`, line 71 `backend/services/windows_keyring_restore.py`. React preview and SQLCipher product jobs on this HEAD are SUCCESS; Windows previously passed SCM, F5B ACL/no-follow and offline key continuity until the NtCreateFile name constructor failed. Downstream D4b and attacker rename/trap FUE were not reached. This is a ctypes constructor incompatibility, **not proof that new NtCreateFile protection passed**. Root P1 parent-swap risk remains OPEN.

**Narrow intended change:** use `ctypes.cast(name_buffer,wintypes.LPWSTR)` for the `UNICODE_STRING.buffer` field while keeping the allocated `name_buffer` alive in the same call scope. No change to Windows native rights/share/disposition, security descriptor, file validation, Python test expectations, fail-closed behavior, or release gates. Minimal ctypes structure reproduction passed for this cast on Python, not a native Windows test. Fresh exact-SHA Windows B06 3/3, Scope and Portability proof required. Existing owner UX SHA approval is stale, do not autoapprove. No merge, deploy, patient data or clinical activation. `READY_TO_MERGE=false`; `PRODUCT_READY=false`; `CLINICAL_GO=false`.


## POST J4/F5B-D4e — ctypes LPWSTR constructor repair committed (exact-HEAD CI pending), 2026-11-06

Windows B06 [run #42196021246](https://github.com/hraaaaf/Digital_crown/actions/runs/42196021246) at old HEAD `e436357c2782a74c5c9432bc5ce2cde1b1a4ee62`: Windows job FAILURE due explicit `TypeError` passing `c_wchar_Array` into `_UnicodeString.buffer: wintypes.LPWSTR`. React and synthetic SQLCipher product SUCCESS. No evidence was gathered at this HEAD for NtCreateFile final create, renamed parent/junction trap, or prebuilt oracle D4b as the Windows job aborted before these steps.

**Code correction commit `f3a25e06081e2d9e5d8d928336681711a1a382cd`:** in `backend/services/windows_keyring_restore.py`, change ONLY `_UnicodeString(...,name_buffer)` to `_UnicodeString(...,ctypes.cast(name_buffer,wintypes.LPWSTR))`; allocated buffer stays in the same function scope for the call. No changes to security attributes, NT options, owner/DACL, path validation, no-create-overwrite, trap FUE or fail-closed behavior. Confirmed Python ctypes constructor type in a minimal test; **native Windows NtCreateFile still requires new CI**.

**Final document commit of this POST creates a new exact HEAD**; track Windows B06 3/3 (with full J4 trap markers and D4b fixed oracle), CI Scope and Portability before GREEN. Do not inherit old results or restore the previous SHA-bound owner label without authentic new approval. J4 remains `CI_PENDING / WINDOWS_PARENT_SWAP_RISK=OPEN`, `F5B_D4_INDEPENDENT_OPERATOR_DRILL=NOT_RUN`, `OFFSITE_ESCROW_VERIFIED=false`, `FULL_CABINET_RESTORE_VERIFIED=false`, `READY_TO_MERGE=false`, `PRODUCT_READY=false`, `CLINICAL_GO=false`. No merge/deploy/installer/clinic.


## PRE J4/F5B-D4f — Two distinct GitHub-hosted Windows VM jobs, synthetic escrow transfer, 2026-11-06

Owner GO: “Vas y utilise deux VM SUR GITHUB ACTIONS”. Baseline PR #1210 Draft/unmerged exact `06aeac6ab10a9abde3f14fb8b011f41b7c544b54`; B06 [#42199180181](https://github.com/hraaaaf/Digital_crown/actions/runs/42199180181) 3/3 SUCCESS, Scope #42199186613 and Portability #42199186810 SUCCESS. The current D4b test uses a prebuilt PUBLIC synthetic JSON corpus pinned to SHA-256 `3de7f99acfba9b5bcc7df3394dc5272ace316c62c2331cd2e3091a80c257bd2e`. It is not genuinely offsite or independently human-held.

**New bounded objective:** add a *separate* GitHub Actions FUE with two truly distinct GitHub-hosted `windows-2022` job VMs, explicit job dependency `needs: custodian`, synthetic encrypted-backup artifact staging by VM1, cross-VM artifact download by VM2, verifying the staged ciphertext and custody receipt against the already pinned independent-of-current-run fixture on checkout; then call existing real `f5bd4_fixed_recovery_windows_fue.py` recovery and negative cases with the staged ciphertext, which restores using the real Windows `restore_new_private_file` and fresh-process product loader. Distinct job runners are genuine, custody independence is only SIMULATED. The artifact will have no real key/password; public fixture already contains a public fake password, never claim secret separation/offsite. Operator shall produce sanitised verdict JSON artifact. No fabricated offsite/human proof, physical machine, database+media+ACK full restore, or owner signoff. New commits invalidate prior exact-SHA CI and owner visual approval. FUE and Notion PR review evidence required before any GREEN. No merge/deploy/clinical activation; `F5B_D4_INDEPENDENT_OPERATOR_DRILL=NOT_RUN`, `OFFSITE_ESCROW_VERIFIED=false`, `FULL_CABINET_RESTORE_VERIFIED=false`, `READY_TO_MERGE=false`, `PRODUCT_READY=false`, `CLINICAL_GO=false`.


## POST J4/F5B-D4f — Two separate GitHub-hosted Windows VMs cross-job encrypted synthetic backup rehearsal (CI pending), 2026-11-06

**Implemented on PR #1210 OPEN/DRAFT/unmerged**: PRE document commit `5380f037ed01cf4d661c2c9145e7fdba3000b8f1`; new runner test script `isolated_fue_lot06c/f5bd4_two_vm_restore_lab.py` commit `02c2aa787e96182b7b0213dc1c40f809a332c19d`; new workflow `.github/workflows/lot06-j4-two-vm-restore-fue.yml` commit `f09e6cb8221d7286f97cef35c13439a6f0809799`. New workflow name: `LOT06 J4 two Windows VM synthetic escrow and recovery FUE (NO CLINICAL GO)`.

**VM1 `custodian`:** real separate GitHub-hosted Windows 2022 ephemeral runner, exact `GITHUB_SHA` checkout, reads precommitted PUBLIC synthetic F5B-D4b fixture, verifies its pinned SHA-256 `3de7f99acfba9b5bcc7df3394dc5272ace316c62c2331cd2e3091a80c257bd2e`, stages AES-GCM encrypted backup bytes only and non-secret custody manifest (origin job/run id, ciphertext SHA-256/source/oracle pin), uploads via `actions/upload-artifact@v4` with one-day retention, without production data or private credentials.

**VM2 `operator`:** a NEW GitHub-hosted Windows 2022 ephemeral runner with `needs: custodian`, own checkout/exact SHA, `actions/download-artifact@v4` from VM1. Checks role/run/source and encrypted ciphertext digest against the previously committed oracle, fail-closed on tampered bytes, then routes the downloaded blob through the **existing** `f5bd4_fixed_recovery_windows_fue.py::main` (monkeypatches only its top-level input `fixture` to return downloaded encrypted bytes with the original precommitted expected oracle; NOT the real crypto, Windows writer or fresh-process product readback). Existing Windows `restore_new_private_file` with handle-relative `NtCreateFile`, negative refusals and independent fresh Python process product readback, both active/retained media and locators are reused, not copied/rewritten. VM2 uploads only sanitised `dc06-j4-two-vm-synthetic-verdict` JSON with flags clearly `independent_human_custodian_attested=false`, `offsite_escrow_verified=false`, `full_cabinet_restore_verified=false`, `clinical_go=false`.

**Proof needed:** GitHub workflow has been recognised and a first [run #42231629534](https://github.com/hraaaaf/Digital_crown/actions/runs/42231629534) queued on interim HEAD `f09e6cb`. This POST creates a NEW final source SHA and a NEW workflow run due to the workflow path filter; only final HEAD run may justify GREEN. Must verify **TWO separate SUCCESS job IDs**, upload/download artifact proof, VM1/VM2 positive synthetic markers, full existing D4b negative battery, verdict artifact, and ordinary B06 3/3/Scope/Portability exact final HEAD if triggered. No premature GREEN.

**Important limit:** Two genuinely distinct GH-hosted VMs and GitHub artifact transport can prove reproducible cross-job Windows backup/restore under different machines, but NOT **independent human custody, offsite escrow, separated real recovery secret, clinic disaster recovery, or physical scanner/TPM**. Existing fixture and its password are intentionally PUBLIC synthetic data committed in repo. `F5B_D4_INDEPENDENT_OPERATOR_DRILL=NOT_RUN`, `OFFSITE_ESCROW_VERIFIED=false`, `INDEPENDENT_ORACLE_VERIFIED=false` for human custody, `FULL_CABINET_RESTORE_VERIFIED=false`, `WINDOWS_PARENT_SWAP_RISK=OPEN_PENDING_INDEPENDENT_THREAT_REVIEW` (targeted race mitigated in LAB), `READY_TO_MERGE=false`, `PRODUCT_READY=false`, `CLINICAL_GO=false`. This new code commit also supersedes old owner UX visual approval (SHA-bound), do not auto-add labels. No merge/deploy/clinical operations.


## PRE J4/F5B-D4g — Owner-requested independent security review of Windows restore + two-VM FUE, 2026-11-06

**Review scope and head before this documentary commit:** PR #1210 OPEN/DRAFT/unmerged, `0483662abca5fb4ac52f078b2b6b454bc842ed9b`, [2VM #42231844907](https://github.com/hraaaaf/Digital_crown/actions/runs/42231844907) 2/2 SUCCESS, [B06 #42231845358](https://github.com/hraaaaf/Digital_crown/actions/runs/42231845358) 3/3 SUCCESS; Scope #42231855141 and Portability #42231854609 SUCCESS at that head. All are synthetic LAB, no human/offsite claim. User explicitly asked to use specialist reviewer agents from `AGENTS.md`; verified repo `.claude/agents` contains scientific/clinical specialists only (scientific-reviewer is high/read-only and must differ from author), **no Windows/NTFS security agent**. Requested GitHub Copilot pull request review as a genuinely distinct bot through GitHub reviewer API; no submitted reviewer result at start. Never call a self-review or role-play an independent external review.

**Adversarial-review checklist:** (A) `backend/services/windows_keyring_restore.py` Win32 ancestor traversal and possible rename/junction substitution of an *intermediate* ancestor despite final leaf handle-relative `NtCreateFile` binding; root/child object identity consistency; private DACL and fail-closed; (B) `f5bd4_two_vm_restore_lab.py` precommitted oracle/sha, actual downloaded artifact used by production restore, tamper negative test invoking **same** validation function, role/run identity, child fresh-process proof; (C) GitHub workflow job isolation, artifacts and supply-chain, no clinical artifact leaks; (D) compare security claims to observed exact SHA CI and human gates. Findings classified BLOCKER/MAJOR/MINOR, with concrete path/line, reproducibility and FUE; no safety claim from a mere test marker. Source authority `AGENTS.md`, `.claude/rules/execution-scoring-verification.md`, and synthetic proof only.

**Initial independently checkable source concern:** product `windows_keyring_restore.py` opens each ancestor using **absolute** `CreateFileW(str(Path(*path.parts[:depth])))` at lines 217-228 and checks only each resulting handle's own reparse bit, then uses the last handle relative `NtCreateFile`. A rename+junction swap of an earlier ancestor between opens may cause a new absolute resolution to traverse elsewhere; existing J4 test swaps the **last** parent only. This is a **suspected upstream race**, NOT yet empirically proven exploitable on Windows. Two-VM FUE at lines 113-118 currently hashes altered synthetic data and asserts its hash changed, but never calls the same admission validator with it; the claim that a tampered transfer was actually refused is a **source-proven false-positive test**. Neither finding is negated by existing green CI. Review result stays `OPEN` until robust mitigation/test evidence. No code or release changes authorized beyond bounded synthetic review/FUE and safe corrective changes. Old owner UI approval remains stale, no merge/deploy or clinical activation.


## POST J4/F5B-D4g — Adversarial review FOUND real upstream-ancestor TOCTOU P1 — BLOCKED (2026-11-06)

**Governance/agent roster:** Reviewed `AGENTS.md`, `.claude/rules/execution-scoring-verification.md`, and `.claude/agents/scientific-reviewer.md` (high/read-only, MUST be a different reviewer from author). Existing 8 `.claude/agents` roles are scientific/clinical, none a Windows/NTFS security agent. GitHub Copilot separate reviewer request was sent through GitHub review-request API, but `list_pull_request_reviews` has ZERO submitted reviews at this decision. No impersonated distinct expert or human custody approval.

**BLOCKER P1 DC06-J4-001 — PROVEN real Windows ancestor redirect** at product `backend/services/windows_keyring_restore.py:217-231`. Ancestors are opened by recomputed absolute `CreateFileW` paths; checking each handle's final reparse bit does NOT prove later handles are descendants of the previously verified handle. Final leaf `NtCreateFile(RootDirectory=opened[-1])` protects only a swap of last parent, not earlier ancestor names. The new `isolated_fue_lot06c/windows_j4_ancestor_swap_review_fue.py` exercises the ACTUAL `restore_new_private_file` function with test-only interposition exactly before the next real Win32 ancestor-open call. An **independent attacker subprocess** renamed the held ancestor and planted a true Windows junction pointing outside, before the real opening proceeds. [Adversarial Windows run #42235111157](https://github.com/hraaaaf/Digital_crown/actions/runs/42235111157), job #127950579150, HEAD `125e03e8b3dcdc33dd2771044af9259d5f3a3726` **FAILED because the product ACTUALLY WROTE into the outside trap**, with log markers `DC06_J4_ANCESTOR_RENAME_AND_JUNCTION_INDEPENDENT_PROCESS_PASS`, `DC06_J4_UPSTREAM_ANCESTOR_JUNCTION_REDIRECT_REPRODUCED_P1`, `AssertionError: DC06_J4_UPSTREAM_ANCESTOR_ISOLATION_BROKEN`. Attacker requires local rename/junction rights at targeted path. No patient or real cabinet exploitation claimed. This is a genuine security failure, NOT a test setup failure. Security review remains BLOCKED regardless of previously green B06/2VM.

**MAJOR evidence gap DC06-J4-002 — read-path absolute traversal:** `backend/services/windows_keyring_handle_probe.py:199-208` separately opens ancestor directories and final file via absolute `CreateFileW`; comment falsely assumes kept FILE_SHARE_READ handles block rename (already disproved). A specific reader attack is NOT_RUN / unproven; source-derived risk must be reviewed and protected before clinical use.

**MAJOR false-positive test DC06-J4-003 — fixed in source:** `isolated_fue_lot06c/f5bd4_two_vm_restore_lab.py:113-118` previously flipped a byte, compared its digest to the oracle and printed `DC06_J4_VM2_TAMPERED_TRANSFER_PREWRITE_DENIED_PASS` without actually running the altered bytes through transfer validation. Commit `a6ce37f9ca5b8f21b56aa627b4e94fcbf91816ed` factors the existing admission validator into `_validate_encrypted_transfer` and exercises that exact function for corrupted bytes, requiring `DC06_J4_BACKUP_PIN_OR_TRANSFER_DENIED`. Fresh final-HEAD 2VM CI needed before claiming corrected PASS. All public synthetic fixture/password/GitHub-escrow limits remain explicit.

**Decision:** `SECURITY_REVIEW=BLOCKED_P1`, `WINDOWS_PARENT_SWAP_ANCESTOR_RISK=PROVEN_LAB`, `J4_FINAL_PARENT_SWAP_SCENARIO=MITIGATED_LAB_ONLY`, `F5B_D4_INDEPENDENT_OPERATOR_DRILL=NOT_RUN`, `OFFSITE_ESCROW_VERIFIED=false`, `FULL_CABINET_RESTORE_VERIFIED=false`, `READY_TO_MERGE=false`, `PRODUCT_READY=false`, `CLINICAL_GO=false`. An older green run is NOT a substitute for passing newly written adversarial tests. PR #1210 stays OPEN/DRAFT/unmerged. No Vercel/deploy/installer/cabinet/production keys/patients.

**GOAL:** challenge J4 Windows and 2VM assumptions independently from happy-path CI. **Success observable:** reproducible adversarial result plus honest gate verdict, not a release PASS. **PROOF:** link/run SHA above and precise product source lines. **EXECUTION_SCORE=5.8/10, FUE_EVIDENCE_SCORE=5.7/10, RETAINED_SCORE=5.7/10** (min, security blocker cap 5.9; divergence 0.1), not VERIFIED. **NEXT:** use nofollow component-by-component handle-relative directory opens starting from verified drive-root; prove original handle-chain continuity under real ancestor rename+replacement junction via `DC06_J4_UPSTREAM_ANCESTOR_NO_ESCAPE_PASS`; separately audit/verify the reader path and update product. Rerun exact-HEAD ancestor review, original F5B-D2, two-VM tamper, B06 3/3, Scope and Portability. Then obtain distinct expert review and owner-specific UX SHA approval if required. Human offsite custodial DR remains a separate NOT_RUN gate.


## PRE J4/F5B-D4h — Fix experimentally proven ancestor rename+junction Windows P1, 2026-11-06

**Owner GO:** “Okay corrige”. Baseline PR #1210 OPEN/DRAFT, exact head `4c502cc7f0cda74cc327b8da60e01fe676923925`, Windows upstream adversarial [run #42235864267](https://github.com/hraaaaf/Digital_crown/actions/runs/42235864267) RED with *actual outside-trap write*. Prior 2VM #42235864370 2/2 SUCCESS and standard B06 #42235864375 3/3 SUCCESS do NOT mitigate this P1. Canonical source and Notion PRE read. High-risk native security, data synthetic only.

**GOAL:** eliminate all post-volume-root absolute re-resolution of directory ancestors in both Windows keyring restore and the Windows keyring secure reader. Opening the drive root once is permissible; then every successive one-component name is to be opened with native NtCreateFile OBJECT_ATTRIBUTES.RootDirectory=verified prior handle, FILE_OPEN/FILE_OPEN_REPARSE_POINT, directory/file type check, and protected ACL check on the final file. The existing exclusive create with FILE_CREATE and protected user+SYSTEM DACL must remain intact. Preserve fail-closed and no overwrite.

**Required adversarial FUE:** adapt the independent-attack-subprocess ancestor swap hook to the *new* NtCreateFile relative child open, not remove it; prove the attack actually occurs, verify no write in trap and read-path no spoofed keyring content. Must gate new `DC06_J4_UPSTREAM_ANCESTOR_NO_ESCAPE_PASS`, separate reader no-spoof marker. Maintain old final parent J4 test, native D4b+2VM and B06 Windows/SQLCipher/React, Scope, Portability exact final head. No human/offsite or clinic claim. `READY_TO_MERGE=false`, `PRODUCT_READY=false`, `CLINICAL_GO=false`; no merge/deploy/installer.


## POST J4/F5B-D4h — native Windows P1 ancestor redirect fixed in product AND reader; exact-final-HEAD CI pending (2026-11-06)

**Owner authorized** the correction. The previous unmodified Windows production restore failed a real rename/junction attack and escaped into a trap on [RED #42235864267](https://github.com/hraaaaf/Digital_crown/actions/runs/42235864267), job #127953169254. This proof remains unchanged and visible in the commit history, `techdoubt.md`, PR and Notion. The dangerous ancestor path was present in both write and read modules.

**P1 product changes:**
- `backend/services/windows_keyring_handle_probe.py`: now owns a **single shared native one-component opener** `_open_relative_component()` with `NtCreateFile` and `OBJECT_ATTRIBUTES.RootDirectory=previously verified parent HANDLE`, a `UNICODE_STRING` holding only ONE validated leaf, `OBJ_DONT_REPARSE | OBJ_CASE_INSENSITIVE`, `FILE_OPEN_REPARSE_POINT`, `FILE_OPEN` and required directory / regular file type checks. Helper `_open_checked_directory_chain()` resolves the trusted local volume root with ONE absolute `CreateFileW`, then EVERY descendant directory against the prior checked handle with preserved chain identity. The directory share allows READ|WRITE|DELETE deliberately so the security proof includes actual concurrent rename even with checked handles open, rather than relying on a brittle share lock. The file read opens the final leaf relative to the verified parent, checks native attributes, a protected user+SYSTEM DACL, size limits, reads from the SAME verified file handle and closes every handle on exit.
- `backend/services/windows_keyring_restore.py`: REPLACES the vulnerable repeated absolute ancestor `CreateFileW` loop by the exact same `_open_checked_directory_chain()`, mapping low-level failures to bounded `WindowsRestoreDenied` fail-closed results; keeps existing user+SYSTEM protected SDDL, isolated correct token lookup, max canonical JSON prevalidation, relative-to-parent exclusive `NtCreateFile(FILE_CREATE)` final leaf, FlushFileBuffers and no-overwrite, no pathname unlink after error. No production secret or patient data was used. No UI or theme tokens changed.
- `isolated_fue_lot06c/windows_j4_ancestor_swap_review_fue.py`: adversarial FUE retargeted from obsolete absolute-path `CreateFileW` hook to the actual native `NtCreateFile` one-component "child" call. **One independent OS attacker process** renames the ancestor and creates a genuine Windows NTFS junction while the verified ancestor handle is held; test FAILS if attacker setup is not genuinely reproduced or any created file escapes into the outside trap. An analogous READ probe installs a different valid private-DACL synthetic keyring in a trap and fails on spoofed read. Assertions are not simulated with static/mocked outputs. FUE explicitly requires BOTH `DC06_J4_UPSTREAM_ANCESTOR_NO_ESCAPE_PASS` and `DC06_J4_READ_UPSTREAM_ANCESTOR_NO_SPOOF_PASS` after actual rename+junction setup.

**Native adversarial empirical proof:** [GREEN #42239156792](https://github.com/hraaaaf/Digital_crown/actions/runs/42239156792) job #127964552108 at source head `b9d667d6312372d892b64fc21986ec55273f8413`, **SUCCESS** on authentic Windows runner, with attack setup printed TWICE `DC06_J4_ANCESTOR_RENAME_AND_JUNCTION_INDEPENDENT_PROCESS_PASS`, positive `DC06_J4_UPSTREAM_ANCESTOR_NO_ESCAPE_PASS ORIGINAL_HANDLE` and `DC06_J4_READ_UPSTREAM_ANCESTOR_NO_SPOOF_PASS ORIGINAL_HANDLE`. The scenario remains reproducible, and the fix protects object identity rather than hiding attack through denial of rename. The earlier green 2VM [#42239041365](https://github.com/hraaaaf/Digital_crown/actions/runs/42239041365) had **2/2 SUCCESS** using the same native security code (previous SHA `ff772da` before test diagnostic change). This posterior documentation **creates a NEW exact HEAD**, and all relevant final checks MUST be verified against that SHA, not inherited without comparison.

**Risk ledger:** `techdoubt.md` updated; root cause confirmed and narrowly MITIGATED LAB on both Windows WRITE and READ. `WINDOWS_ANCESTOR_REDIRECT_P1=MITIGATED_LAB` but a separate specialist's independent source review is NOT yet returned and all remaining filesystem/ACL threat scenarios are not proven universally safe. GitHub Copilot review request has no recorded submitted review at last check; do not impersonate reviewer. Prior owner visual signoff was SHA-bound to a different HEAD, and the full offsite/human-custodian drill still is `NOT_RUN`. `OFFSITE_ESCROW_VERIFIED=false`, `FULL_CABINET_RESTORE_VERIFIED=false`, `READY_TO_MERGE=false`, `PRODUCT_READY=false`, `CLINICAL_GO=false`. PR #1210 remains DRAFT/unmerged; no deployment or clinic operation.

**Final validation queue:** exact-final-HEAD [ancestor Windows CI](https://github.com/hraaaaf/Digital_crown/actions/workflows/lot06-j4-independent-ancestor-review.yml), [2VM Windows CI](https://github.com/hraaaaf/Digital_crown/actions/workflows/lot06-j4-two-vm-restore-fue.yml), [B06 Windows+SQLCipher+React](https://github.com/hraaaaf/Digital_crown/actions/workflows/lot06-phase2-b06-integration-fue.yml), CI Scope, Portability. On exact HEAD, inspect job conclusions AND actual attack markers, read provenance, tampered transfer refusal, negative restore cases; note any RED and fix it before considering this narrow software P1 resolved. No clinical certification, merge, release, installer or Vercel action without separately authorized human gates.

**Scores:** Candidate execution / FUE scores held pending all required exact-HEAD CI; do NOT assign VERIFIED solely on prior candidate GREEN. **GOAL** eliminate real upstream write/read race; **NEXT** final source SHA gate and distinct human review. D4 independent offsite/human and full DB+media+ACK remain outside the two-VM synthetic proof.


## PRE J5/B06 UX corrections — French date + 200% text zoom, 2026-11-06

**Owner GO**: “Si c’est largement suffisant just do it” for internal engineering review (not an invented external signoff), then “Pour les deux reserves UX faut les corriger”. Starting PR #1210 OPEN/DRAFT/unmerged at exact head `fe46d7149ecc21c38d0cff7be25215252ee1fae0`. Previous actual React Chromium [#42239855511](https://github.com/hraaaaf/Digital_crown/actions/runs/42239855511) 11 PNG + summary artifact #13515021690: native date input rendered `mm/dd/yyyy` even in synthetic `fr-FR` browser, and 200%-text viewport feels cramped. Internal FUE/CI are sufficient to progress the coding pass, but cannot impersonate owner screenshot approval, clinic release authority or a distinct specialist. Source-of-truth `AGENTS.md`, visual closeout rule and canonical Notion PRE read.

**GOAL/target**: display AND re-enter birth dates in stable `JJ/MM/AAAA` for French UI on any locale/OS, without changing the canonical API request `date_naissance: YYYY-MM-DD` or weakening the exact two-marker and explicit-checkbox gate. Reject malformed/impossible dates including leap/calendar, not merely wrong strings. Preserve familiar calendar UX clarity and accessible labels/input modes. Replace native `type=date` with an explicit French text entry and parsing/formatting. Use only existing semantic theme tokens. Make high zoom at 390px actually readable via reduced nested paddings, min-width/word wrap and controls that can wrap without overflow, NEVER scale down the user's chosen text size.

**Acceptance FUE battery**: React unit test valid `04/03/2000` → ISO `2000-03-04` backend, reject `03/04/2000`, ISO literal, invalid dates, impossible leap day and incomplete entry, confirmation requires verified preview, exact dossier, exact DOB and checkbox; check birth date reference rendering French, no `mm/dd/yyyy`. Extend existing real React Chromium harness to fill French date, assert exact French placeholder and text, check viewport 390/430/768/1280 light, 390 dark, 390 200% text, verify overflow of page/form/CTA+checkbox, gather BEFORE/AFTER screenshots and actual copy. Run UI visual action, B06 Windows/SQLCipher/React, J4 native ancestor, 2VM synthetic, CI Scope and Portability at exact new HEAD; do not declare result until logs and artifact confirmed.

**No-go**: No auto visual approval label, separate independent Windows review claim, merge, deploy, cabinet installation or real clinical data; `READY_TO_MERGE=false`, `PRODUCT_READY=false`, `CLINICAL_GO=false`. Human custodian offsite/whole cabinet recovery remains NOT_RUN.


## POST J5/B06 UX — Corrected FR birthday entry and 200% text view, 2026-11-06

**Owner scope:** owner explicitly decided “Si c’est largement suffisant just do it” for internal review and “Pour les deux réserves UX faut les corriger”. This authorizes bounded code/UI modifications and testing; not a fabricated independent Windows auditor, not a new explicit owner visual screenshot approval, merge, clinical release, or deployment. PR #1210 remains Draft/open, all data synthetic.

**Product correction and source**: `frontend/src/features/patients/components/ImagingAcquisitionProductReviewV15.tsx` now displays the validated backend ISO `date_naissance` as readable `DD/MM/YYYY`, with an explicit `JJ/MM/AAAA` input/placeholder/help line (text, numeric keyboard, maxLength 10). `parseBirthDateFr` accepts ONLY exact ten-character French format and actual Gregorian calendar dates (leap-year logic, month bounds, days per month); no reliance on OS/browser's `input type=date` native locale. The confirmation gate uses parsed ISO equality against the signed review birth date and remains disabled until image hash/loaded preview, matching patient/dossier, and the explicit consent checkbox. The existing actual backend POST continues to send canonical `YYYY-MM-DD`, **never French text**. Safety rejection regression tests include malformed `2000-03-04` typed into UI, day/month inversion `03/04/2000`, impossible `31/02/2000`, invalid nonleap `29/02/2001`, month 13, day 0, year 0000 and incomplete `4/3/2000`. Successful `04/03/2000` posts `2000-03-04`. No changes to backend clinical API or SHA/binding logic.

**Zoom remediation**: same product component decreases nested card and image padding on mobile, uses `min-w-0`, intrinsic wrapping and tight semantic spacing for actions/checkbox; respects semantic theme tokens (`bg-card`, `text-text-main`, `bg-primary`, `border-border-main`, etc.) without hard-coded palette, font shrinkage or low contrast. `frontend/scripts/capture-lot06-b06-react-visual.mjs` now asserts actual DOB reference French `04/03/2000`, exact placeholder `JJ/MM/AAAA`, native input eliminated, denies wrong dates before checkbox, then enters exact DOB and checks disabled/enabled states with explicit checkbox; checks page and panel overflow AND individual buttons' horizontal clipping at all six view variants.

**Observed actual browser proof on candidate source HEAD `a1453ec2dd974c1cc9720acd1e8cbfef46b59472`:** [Chromium #42245193299](https://github.com/hraaaaf/Digital_crown/actions/runs/42245193299) `actual-react-chromium SUCCESS`, [artifact #13517319642](https://github.com/hraaaaf/Digital_crown/actions/runs/42245193299/artifacts/13517319642) containing **11 PNG + summary JSON**, six variants 390/430/768/1280/dark/390 zoom 200%. All `frenchDateInput='JJ/MM/AAAA'`, `frenchDatePreview='04/03/2000'`, `invalidDatesDenied=true`, `actionOverflow=0`, `overflow=false`, `explicitCheckbox=true`, `commitsExecuted=0`. Actual 390px review screenshot heights BEFORE `1111px` / AFTER `1076px`; text-200% BEFORE `3269px` / AFTER `2981px` (approx **8.8% less vertical scroll**) while retained 200% root text size. 1280x900 and dark visual screenshots also inspected; no new overflow. This is a **real React component mounted with synthetic lab API**, NOT the full authenticated clinic patient journey or human approval. The baseline captures are [Chromium #42239855511](https://github.com/hraaaaf/Digital_crown/actions/runs/42239855511) artifact #13515021690, exact prior source SHA `fe46d7149ecc21c38d0cff7be25215252ee1fae0`. Before/after artifacts and readable comparison images are available in conversation files, GitHub artifacts linked here.

**Safety/review:** internal adversarial review of date parsing and explicit two-marker/checkbox gate is completed as **internal technical evidence only**; no other AI role/person is asserted to have delivered an independent external Windows/NTFS signoff. Before post-documentation B06 technical workflow [#42245034704](https://github.com/hraaaaf/Digital_crown/actions/runs/42245034704) showed frontend preview unit test GREEN with changed date inputs; there is no clinical/installer release. This POST creates a NEW HEAD and the exact HEAD CI (Chromium, B06 3 jobs Windows/SQLCipher/React, J4 ancestor, 2VM, Scope/Portability) must be checked AGAIN; no score of final release is assigned before proof.

**Final gate semantics**: `UX_RESERVATION_DATE_FR=FIXED_AND_CHROMIUM_PASS_CANDIDATE`, `UX_RESERVATION_ZOOM_200=FIXED_AND_CHROMIUM_PASS_CANDIDATE`, `B06_VISUAL_OWNER_APPROVAL=PENDING` (fresh owner SHA-bound approval after inspect; prior label expired), `INDEPENDENT_WINDOWS_REVIEW=INTERNAL_ONLY_NO_EXTERNAL_SUBMISSION`, `F5B_D4_INDEPENDENT_OPERATOR_DRILL=NOT_RUN`, `OFFSITE_ESCROW_VERIFIED=false`, `FULL_CABINET_RESTORE_VERIFIED=false`, `READY_TO_MERGE=false`, `PRODUCT_READY=false`, `CLINICAL_GO=false`. No merge, deployment, clinical activation or patient data. **NEXT** verify exact-new-HEAD UI/CI and hand owner actual AFTER screenshots for authentic visual approval; separately retain external custodial gates.


### ADDENDUM POST J5/B06 — Numeric-only mobile birth-date entry and final exact-HEAD gate

**Internal reviewer identified a usability gap AFTER earlier screenshot PASS**: on an iOS numeric keyboard the "/" character is not always directly available. The React controlled birth-date text field now auto-inserts French separators as the operator types eight digits (`04032000` → `04/03/2000`), without accepting ambiguous day/month values or altering backend ISO `date_naissance`. `formatBirthDateInput` strips non-digits for numeric keypad and adds slashes after day/month; `parseBirthDateFr` still checks the strict ten-character French date and genuine Gregorian calendar before comparison to the server-provided ISO. The confirmation gate remains hash/preview + dossier + DOB + explicit checkbox, fail-closed. Unit regression `ImagingAcquisitionProductReviewV15.test.tsx` now fills digits without slashes, asserts the exact formatted input value, verifies all negative cases and original ISO API POST. Chromium browser FUE `capture-lot06-b06-react-visual.mjs` also now fills digits-only, asserts the formatted visible `04/03/2000` and enforces invalid dates rejected and no horizontal action overflow. This is one bounded UI-only refinement, no extra dependency and theme tokens unchanged.

**Proof status at this documentation commit:** previous actual Chrome [#42245193299](https://github.com/hraaaaf/Digital_crown/actions/runs/42245193299) SUCCESS with both French display and improved 200% layout **BEFORE numeric auto-format**, 11 inspected PNG; actual numeric autoformat Chromium [#42246362120](https://github.com/hraaaaf/Digital_crown/actions/runs/42246362120) and B06 React/SQLCipher/Windows [#42246319362](https://github.com/hraaaaf/Digital_crown/actions/runs/42246319362) **QUEUED/IN_PROGRESS** as last checked. This addendum creates a NEW final HEAD; all exact-SHA CI must be checked at that final HEAD before a final GREEN. Do not misreport earlier GREEN as approval of the numeric-input change. Once complete, evaluate root font 200% (not scale-down), mobile/desktop/dark, six browser results, ISO POST and actual screenshot evidence.

**Review status:** owner authorized internal review sufficiency for implementation, NOT a third-party attested Windows/NTFS review, human UI visual approval, offsite independent custodial recovery or clinical release. PR #1210 remains OPEN/DRAFT/unmerged. `READY_TO_MERGE=false`, `PRODUCT_READY=false`, `CLINICAL_GO=false`. No merge, label, deploy, installer or patient data. **NEXT:** final exact HEAD Chromium + B06 + Windows ancestor + two-VM + Scope/Portability checks and newly generated owner AFTER captures; J4 human offsite remains separate.


### POST J5 QA correction — browser invalid-date refusal must be discriminating

Internal adversarial inspection of the **visual test** caught a false-pass risk: its invalid-date loop was running BEFORE the mandatory explicit-checkbox tick; an always-disabled submit would have passed these negative assertions even if the date parser were broken. This was NOT a demonstrated clinical product error (the React unit FUE independently checked negative dates **with checkbox checked**), but it was an invalid browser-level proof.

Fix committed in `frontend/scripts/capture-lot06-b06-react-visual.mjs`: after entering the correct dossier and digits-only birth date (`04032000` → `04/03/2000`), the test first confirms the button is disabled without checkbox, then **checks the checkbox and observes the ENABLED positive control**, THEN submits all negative date cases and asserts the action becomes disabled, then restores the valid date and checks the action is enabled again. It also changes to a wrong patient dossier and asserts disabled with checkbox checked, restores correct dossier and asserts enabled. A browser PASS can now prove the invalid-date and wrong-dossier gate **independently of the checkbox** and does not merely test that a disabled button remains disabled.

Actual Chromium [#42246974426](https://github.com/hraaaaf/Digital_crown/actions/runs/42246974426) SUCCESS at earlier SHA `ff63ecaea71cc8a7620a55e7015309717734e563` with full numeric autoformat on all six viewports and [artifact #13518841832](https://github.com/hraaaaf/Digital_crown/actions/runs/42246974426/artifacts/13518841832), 11 PNG+JSON downloaded/inspected; the **stronger negative sequencing** was added AFTER that run in script commit `0381f490b900d7c605cf0175c354ff4478fd7880` and MUST pass at the new exact-final-head. Reuse the prior screenshot images as BEFORE, not as proof of this new test sequence. No product UI/crypto/Windows/DB code changed in this small QA correction, but no exact-SHA release conclusion may be inherited. All human/offsite/no-merge gates remain unchanged.


## PRE/POST J4 F5B-D4i — forged receipt + ciphertext denial (2026-11-06)

**Decision owner:** "Green go" to continue J4 security closure in LOT06. **Baseline:** PR #1210 OPEN/DRAFT @ `2d5fd284c453151ceec39d140aabce4155d9f1f6`, older native ancestor Windows #42246974204 SUCCESS, two separate Windows runners #42246974636 2/2 SUCCESS, B06 at that SHA #42248134103 3/3 SUCCESS, J5 owner visual decision APPROVED_IN_CHAT scoped to existing component. The offsite human escrow/custodian drill is NOT_RUN; never call GitHub artifact transfer "offsite custody". Production patient media and keys never used.

**Goal:** close a distinct *negative oracle* gap: forged custody receipt jointly with tampered backup. In `isolated_fue_lot06c/f5bd4_two_vm_restore_lab.py`, the VM2 operator previously corrupted the transferred ciphertext but retained the authentic signed/pinned receipt; now an adversarial case ALSO replaces the receipt's ciphertext hash and byte count to match corrupted bytes. The EXACT admission function `_validate_encrypted_transfer` must reject the coherent-looking forged pair against the independent precommitted fixture oracle BEFORE the actual Windows restore; wrong code or false-accept fails the process, and only a genuine denial prints `DC06_J4_VM2_FORGED_RECEIPT_PREWRITE_DENIED_PASS`. Existing unmodified-receipt tamper, native Windows restore/ACL, protected file creation, overwrite and fresh-process media negative tests remain.

**Code result:** [commit 675901139f489fe8b2026d1d1bdeb5c4e108edb8](https://github.com/hraaaaf/Digital_crown/commit/675901139f489fe8b2026d1d1bdeb5c4e108edb8), 15 lines of LAB FUE only, new blob `ddff73eb1949b008d3cd37ce9e032b052c061af3`. Product Windows primitive and patient handling were not modified. This documentary commit intentionally triggers both J4 ancestor + two-Windows-runner workflows and the B06/Scope gates where path triggers match; do NOT claim pass until the exact final SHA and job logs are checked. Verify separate job markers and artifact verdict, not just top-level green. Preserve final-HEAD CI by recording subsequent results in PR comments and canonical Notion rather than making another paper-only SHA.

**Gate:** `J4_FORGED_RECEIPT_FUE=CODED_CI_PENDING`, `INDEPENDENT_HUMAN_CUSTODIAN=NOT_RUN`, `OFFSITE_ESCROW_VERIFIED=false`, `FULL_CABINET_RESTORE_VERIFIED=false`, `READY_TO_MERGE=false`, `PRODUCT_READY=false`, `CLINICAL_GO=false`; no automatic new overall LOT06 approval, no merge, clinic install, deployment or Vercel. **NEXT:** capture real final-head J4 2VM, ancestor and B06 CI; failures -> diagnose and fix, success -> document source SHA and leave the offsite physical/human recovery gate honest.


## LOT06 B06-BS1 — PRE/POST candidate SCM identity evidence before synthetic native bridge, 2026-11-06

**Owner mission GO:** “Go” to continue the local Windows SCM bootstrap **LAB-only** after [J4 #42258380653](https://github.com/hraaaaf/Digital_crown/actions/runs/42258380653) and [B06 #42258380755](https://github.com/hraaaaf/Digital_crown/actions/runs/42258380755) GREEN at preceding head `bfeff5161fe845ee14d27d02e6b3605cb8e33700`. PR #1210 remains OPEN/DRAFT, no merge or deploy.

**PRE reality:** `backend/main.py` deliberately leaves `app.state.dc06_unassigned_bridge` unset on actual product startup; `backend/routers/imaging_acquisition_unassigned_v15.py` returns `NATIVE_IPC_NOT_CONNECTED` without an injected server-owned trusted bridge, while durable commit requires an explicitly approved SQLCipher schema/provisioning gate. The existing Windows SCM fixture is compiled with a **disposable unsigned LAB** DLL, a synthetic random AES key and a restricted LocalService SID, not the approved product publisher, hardware TPM or clinical scanner. A name/pipe/path or GitHub green badge ALONE cannot authorize it.

**Goal / change (non-product):** `isolated_fue_lot06c/windows_scm_service_sid_fue_c05b03r.ps1` adds `Assert-B06LabScmIdentity`, invoked **after** actually starting the disposable service and **before** the native inventory/media probes, gated by already-existing Windows/GITHUB/test-only guards and `DC06B06_NATIVE_MEDIA=1`. The gate reads live OS `Win32_Service` and `Win32_Process`: Running, NT AUTHORITY\\LocalService, nonzero process PID, exact preconfigured SCM binary command and pipe, matching current process executable/DLL/pipe, actual `sc showsid` service SID, restricted `sc qsidtype`, plus current SHA256 of the expected LAB DLL compared to a pin taken from the just-built fixture. On success print `DC06_B06_BOOTSTRAP_LIVE_SCM_IDENTITY_PASS`. Independently mutate the claimed package hash, pipe, service SID and service name with all other context still valid; each must be rejected for the **specific expected reason**, not by unrelated exception or an always-blocked oracle, before `DC06_B06_BOOTSTRAP_FORGED_HASH_DENIED_PASS`, `...PIPE...`, `...SID...`, `...SERVICE...` markers. No clinical runtime bridge is mounted by the test.

**Source changes:** security FUE-only commit `1d3c795c4b490dc610f4fa30be34534ec75167fa`, then corrected the exact PowerShell LocalService account path separator `6c0133bb6a817384e81cceda2a2611fb12f5a012`; test harness source blob `642a5b2019354b44a3191ff214e9212f53171e21`. No `backend/main.py`, product route, Windows product service code, frontend, DB schema, patient/crypto/keyring or clinical semantics were changed. Existing J5 owner-approved frontend TSX blob remains `289e72fd5b533984376eb9f17d214da0bd587261`.

**Proof pending until final-HEAD workflows end:** [B06 three-job Windows/SQLCipher/React FUE](https://github.com/hraaaaf/Digital_crown/actions/workflows/lot06-phase2-b06-integration-fue.yml) must be 3/3 SUCCESS, its **real** Windows SCM job log must include every new positive/negative marker and pre-existing approved/denied other-user, restart, AES, ACL, wrong-key and tamper markers; check branch HEAD and final SHA. PR Scope/Portability as applicable. This gate is not an authentically signed product installer: compare-to-in-memory-pin is only a synthetic LAB integrity oracle and is NOT a release publisher attestation. Do not confuse proof of a test-created SCM service with approval to activate a local clinical scanner. Record exact finished run URLs and conclusion in PR/Notion without making a post-CI paper-only HEAD.

**Hard gates:** `LAB_NATIVE_SCM_BOOTSTRAP=CODED_CI_PENDING`, `INDEPENDENT_WINDOWS_SECURITY_REVIEW=NOT_ATTESTED`, `APPROVED_PRODUCT_INSTALLER=NOT_VERIFIED`, `OFFSITE_ESCROW_VERIFIED=false`, `FULL_CABINET_RESTORE_VERIFIED=false`, `READY_TO_MERGE=false`, `PRODUCT_READY=false`, `CLINICAL_GO=false`. No Vercel, merge, deployment, physical cabinet, hardware, migrations, secrets or real patient data. **NEXT:** inspect exact-final-SHA Windows logs and refine if RED; then separately design an installer-signed product attester/SCM bootstrap trusted by the local backend, subject to critical review/approval.
