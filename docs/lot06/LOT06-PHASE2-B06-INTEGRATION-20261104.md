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
