# MUTUELLES DENTAIRES — FAR SOURCE / GATE

Date: 2026-09-17
Status: **BLOCKED — SOURCE PDF / PRINT GEOMETRY NOT YET CERTIFIED**
Scope: FAR only. No FAR implementation is authorized by this gate.

## Goal

Establish a reliable source and field contract for the Mutuelle des Forces Armées Royales (FAR) dental workflow before implementation, while keeping the existing Mutuelles engine as the single engine and treating the prescription area/page as an independent clinical sub-document.

## Success criteria

The FAR SOURCE/GATE becomes implementation-authorizing only when all of the following are true:

1. one exact application reference binary is available as bytes;
2. exact SHA-256 and byte size are recorded;
3. physical page count and dimensions used by the application are recorded;
4. every physical page is visually inspected;
5. logical role of every page is recorded;
6. prescription content is isolated as a separate logical role and contract;
7. source provenance/trust is classified and bound to the exact SHA-256;
8. allowed / forbidden auto-filled fields are mapped;
9. common Mutuelles engine coverage is checked and only the minimum FAR-specific extension is permitted;
10. the printable geometry is proven sufficiently reliable for overlays / final PDF output;
11. no implementation starts before this gate is upgraded from BLOCKED.

## Cabinet-validated layout identity

Chosen layout identity: **MFAR — “Feuille de Mutuelle FAR 2021-1”**.

On 2026-09-17 the cabinet explicitly confirmed that this exact Scribd listing is the correct visual/model identity:

`https://fr.scribd.com/document/1025435397/Feuille-de-Mutuelle-FAR-2021-1`

Trust classification for that confirmation:

**`CABINET_VALIDATED_LAYOUT_IDENTITY`**

This validates the intended form/layout identity. It does **not** validate one exact downloadable PDF binary byte-for-byte and must not be upgraded to `CABINET_VALIDATED_BINARY` without explicit validation of exact bytes bound to a SHA-256.

## Corroborating public copies

The same logical form is independently reproduced by several public user uploads, including:

- Scribd `1025435397/Feuille-de-Mutuelle-FAR-2021-1` — cabinet-selected identity;
- Scribd `777249804/Feuille-de-Mutuelle-FAR-2021`;
- Scribd `742194320/FAR-Recto-Verso`;
- Scribd `700464590/Page-1-Feuille-de-Maladie`;
- Scribd `796381015/Feuille-de-Mutuelle-FAR-2021`;
- Scribd `830287170/Feuille-de-Maladie-FAR`;
- Studocu `feuille-de-soins-dentaire-inpe-mutuelle-des-far/137649272`.

These are secondary user uploads, not official primary FAR publications.

No official primary downloadable binary was found during the source-search passes.

## Recovered render assets — verified bytes

### Scribd render asset — document 777249804

Public CDN asset actually downloaded:

`https://imgv2-2-f.scribdassets.com/img/document/777249804/original/83ef2ce61d/1730193779?v=1`

Verified properties:

- HTTP: `200`;
- media type: `image/jpeg`;
- dimensions: `768 x 1024 px`;
- byte size: `175012`;
- SHA-256: `cf6a071beb0bb8934684d0cd137b1f7b237895976ace8aea44d1bdaf49df6dd5`.

Visual content shows the four logical FAR pages/areas in a 2x2 preview composition: Page 4, Page 1, Page 2 `ORDONNANCE`, Page 3 acts/providers.

This asset is therefore useful as a **layout/render reference**, but it is not proven to be either physical page of the original 2-page PDF and is not high-resolution enough to certify final print geometry.

### Independent Scribd render asset — document 700464590

Public CDN asset actually downloaded:

`https://imgv2-1-f.scribdassets.com/img/document/700464590/original/a669235acb/1706029303?v=1`

Verified properties:

- HTTP: `200`;
- media type: `image/jpeg`;
- dimensions: `768 x 1024 px`;
- byte size: `183182`;
- SHA-256: `aacddaa2b8ccf3fd1a7a065939a334ee786f8ca957959b701c53300244be3154`.

It independently reproduces the same four logical areas but with different scan/crop/composition characteristics. Automated feature registration found matches on all four logical quadrants, but the two assets are not pixel-identical and must not be treated as one canonical binary.

### Low-resolution Scribd asset — document 742194320

The indexed `original/.../1?v=1` URL was also actually downloaded, but resolves only to:

- JPEG `255 x 330 px`;
- `2163` bytes;
- SHA-256 `b52459bb3b0283eb244ee40b8655bd2ab8ff4ba96a245bd4bcc65678d1ccaf2f`.

The tested `/1`, `/2`, `/3`, `/4` variants all returned the same bytes. Dimension-specific guessed variants returned `403`. This asset is unsuitable for print/overlay geometry.

## Download endpoint checks

Unauthenticated, no-cookie checks were performed without bypassing authentication/paywalls:

- `https://www.scribd.com/document_downloads/777249804` -> HTTP `403`;
- `https://www.scribd.com/document_downloads/1025435397` -> HTTP `403`;
- `https://www.scribd.com/document_downloads/742194320` -> HTTP `302` to a Scribd deleted page.

A Studocu signed `bg1.png` URL was visible in indexed search results, but direct retrieval with the exposed signature returned HTTP `403`; no claim of separate-page bytes is made from it.

No authentication/paywall bypass was attempted.

## Verified logical layout facts

The cabinet-validated/corroborated form contains:

- `Page 1` — feuille de maladie / member and beneficiary information, treating practitioner identification;
- `Page 2` — `ORDONNANCE` with patient name and prescription area;
- `Page 3` — health-provider acts / dates / coefficients / fees / practitioner stamp-signature area;
- `Page 4` — `SOINS ET PROTHESE DENTAIRE (INPE)`, dental chart, dental/prosthetic work table, medical-control area.

Scribd indexes the chosen/corroborating uploads as **2 pages**, while the form itself carries logical labels Page 1 through Page 4. The recovered 768x1024 preview assets compose all four logical pages into one preview image; they do not prove the exact two physical PDF page dimensions/imposition.

Therefore physical print geometry remains unverified.

## Prescription isolation

The `ORDONNANCE` content is a separate clinical role: `FAR_PRESCRIPTION`.

Mandatory constraints:

- no molecule inferred from dental acts or NGAP;
- no dose inferred from dental acts or NGAP;
- no posology, duration or frequency inferred from dental acts or NGAP;
- medication content must come from explicit prescription data and require practitioner review;
- prescription validation must be independent from dental-claim validation;
- if a combined final PDF is required, it may be assembled only after independent validation of each logical sub-document.

## Allowed field families — provisional until printable reference geometry is certified

Potentially sourced from existing explicit cabinet/patient/practitioner data, subject to field-by-field verification:

- patient/member identity already explicitly stored;
- beneficiary identity/relationship when explicitly known;
- practitioner identity and INPE when explicitly configured;
- dates actually present in the source workflow;
- dental acts, tooth positions, coefficients and fees only from existing clinical/financial truth sources used by the Mutuelles engine;
- explicit prescription data entered/reviewed by the practitioner.

## Forbidden / fail-closed

- no guessed member/account/grade/unit data;
- no guessed relationship/beneficiary status;
- no fuzzy NGAP mapping;
- no artificial backfill;
- no auto-created signature or stamp;
- no invented insurer decision or approval;
- no prescription molecule/dose/posology/duration/frequency inferred from acts or NGAP;
- no coordinates or overlay geometry copied from CNSS/CNOPS;
- no FAR implementation from low-resolution preview geometry;
- no source labelled `OFFICIAL_PRIMARY` without primary proof;
- no source labelled `CABINET_VALIDATED_BINARY` unless exact bytes are explicitly cabinet-validated and bound to their SHA-256;
- no production mutation;
- no Vercel deployment without explicit user authorization;
- no merge without explicit user agreement.

## Common-engine constraint

FAR must reuse the existing Mutuelles flow and truth sources:

`Patient -> Honoraires -> Preparer organisme -> Revue praticien -> Validation -> PDF -> DocumentArchive`

Expected reuse includes the existing submission draft, Honoraires financial truth, clinical catalog, regulatory mapping layer, immutable/hash-addressed source handling, practitioner validation, anti-stale revalidation, hash-bound PDF finalization and DocumentArchive.

A second Mutuelles/Honoraires engine or second clinical catalog is forbidden.

## Gate decision

**BLOCKED for implementation.**

What is now proven:

- correct cabinet-selected visual/layout identity;
- multiple independent corroborating uploads;
- exact bytes, SHA-256, byte size and dimensions for two independent public render assets;
- all four logical roles visible, including isolated `ORDONNANCE`.

What is still missing:

- an exact printable application reference at sufficient fidelity;
- certified physical page count/dimensions/imposition for that reference;
- exact overlay geometry derived from that printable reference.

The blocker has therefore narrowed from “unknown model / no bytes” to **“no certified printable reference geometry”**.

## Next exact

Use one of these two valid paths:

A. recover a legitimate full-resolution PDF/scan matching the cabinet-validated model; or

B. create a clean reconstructed printable reference from the validated layout, classify it explicitly as `CABINET_VALIDATED_RECONSTRUCTED_REFERENCE`, visually compare it against the cabinet-selected target, bind exact SHA-256/page geometry to the reconstructed binary, and only then use that binary for overlays.

For path B, reconstruction must not be presented as an official FAR original. It becomes acceptable only after real Target -> Render comparison and cabinet acceptance of the reconstructed printable output.

## Repository state observed before this update

- repository: `hraaaaf/Digital_crown`;
- branch: `docs/mutuelles-far-source-gate-20260916`;
- prior branch HEAD: `5a2798ce063fd7503503e83dc863d561cee41d96`;
- current master observed: `eb2353b68d880b89dfadd13819fb43d1c71e2f1d`;
- compare before write: branch ahead `2`, behind master `5`;
- master-only changes observed in compare are outside these FAR docs (`backend/tests/test_agenda_availability_wiring.py`, `backend/tests/test_mobile_identity_security.py`).

No FAR code, DB mutation, production mutation, deployment or merge was performed in this source pass.

## Scoring

- EXECUTION_SCORE: **5.9/10**
- ADVERSARIAL_SCORE: **5.9/10**
- Retained: **5.9/10 — BLOCKED**

Rationale: source identity is now cabinet-validated and real render bytes were recovered, but a required clinical printable-source proof remains absent. Under the project scoring rule, that blocker prevents VERIFIED status and caps the retained score at 5.9.
