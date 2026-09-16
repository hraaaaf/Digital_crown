# MUTUELLES DENTAIRES — FAR SOURCE / GATE

Date: 2026-09-17
Status: **BLOCKED — PRINTABLE REFERENCE NOT YET CABINET-ACCEPTED**
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
11. the cabinet explicitly accepts the printable reconstructed reference if Path B is used;
12. no implementation starts before this gate is upgraded from BLOCKED.

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

This asset is useful as a **layout/render reference**, but it is not proven to be either physical page of the original 2-page PDF and is not high-resolution enough to certify final print geometry by itself.

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

The indexed `original/.../1?v=1` URL was actually downloaded, but resolves only to:

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

Therefore original physical print geometry remains unverified.

## Reconstructed preview generated — Path B proof artifact

Using only the recovered `777249804` public render asset, two **non-official preview binaries** were generated to make the implied imposition inspectable without pretending to own the original FAR PDF.

### Two-side preview

Filename:

`FAR_RECONSTRUCTED_PREVIEW_2UP.pdf`

Construction:

- page 1: top half of the 768x1024 render -> logical `Page4 | Page1`;
- page 2: bottom half -> logical `Page2 | Page3`;
- custom geometry: `768 x 512 pt` per page;
- this geometry preserves source-preview pixels 1:1 and is **not** asserted to be the original FAR paper size.

Verified binary:

- page count: `2`;
- byte size: `575527`;
- SHA-256: `61202c763817e5dc8a037fa178f6ef5785ae527adf23ecd7b7a4ee54c4902cbd`.

### Four-logical-page inspection preview

Filename:

`FAR_RECONSTRUCTED_PREVIEW_LOGICAL_4P.pdf`

Construction/order:

`Page1 -> Page2 ORDONNANCE -> Page3 acts -> Page4 dental`.

Verified binary:

- page count: `4`;
- custom geometry: `384 x 512 pt` per page;
- byte size: `557916`;
- SHA-256: `7e115403fc25cacf3039a7e80704c97c5c1e638955f48906519926e47662566a`.

These previews are explicitly **audit/reconstruction artifacts only**. They are not yet a printable application reference and are not stored in the Git repository. They exist in the temporary source-recovery workspace so the next step can be cabinet visual acceptance or replacement by a higher-fidelity source.

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
- no reconstructed preview labelled as an original FAR document;
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
- all four logical roles visible, including isolated `ORDONNANCE`;
- deterministic two-side and four-logical-page reconstruction previews with exact hashes and page geometry.

What is still missing:

- a cabinet-accepted printable application reference at sufficient fidelity;
- exact final page dimensions chosen for that printable reference;
- Target -> Render acceptance for that reference;
- exact overlay geometry derived from the accepted printable reference.

The blocker has therefore narrowed to **cabinet acceptance / printable fidelity**, not model identity.

## Next exact

Present the Path B reconstruction to the cabinet for visual acceptance, or replace it with a legitimate higher-fidelity Path A PDF/scan if one becomes available.

If the reconstructed output is accepted, the next source-gate pass must:

1. freeze the exact accepted binary;
2. classify it `CABINET_VALIDATED_RECONSTRUCTED_REFERENCE`;
3. select and record final printable page dimensions without distorting the validated geometry;
4. render the final binary and compare Target -> Render;
5. bind trust to SHA-256;
6. map exact overlay coordinates;
7. upgrade this gate;
8. reconcile the implementation branch with current master;
9. only then begin FAR implementation.

## Repository state observed in this pass

- repository: `hraaaaf/Digital_crown`;
- branch: `docs/mutuelles-far-source-gate-20260916`;
- master observed: `eb2353b68d880b89dfadd13819fb43d1c71e2f1d`;
- PR `#559`: OPEN / DRAFT / mergeable at last check;
- branch before this update: `ae9d9bc6d09b02858b7a9cfa4a1272d823b98c8b`;
- compare before this update: branch ahead `4`, behind master `5`;
- exact-HEAD CI on `ae9d9bc6...`: main `CI` success and `T2 Runtime Browser Certification` success; unrelated workflows skipped.

No FAR code, DB mutation, production mutation, deployment or merge was performed in this source pass.

## Scoring

- EXECUTION_SCORE: **5.9/10**
- ADVERSARIAL_SCORE: **5.9/10**
- Retained: **5.9/10 — BLOCKED**

Rationale: the visual identity and preview bytes are now well evidenced, but the cabinet has not yet accepted a printable reconstructed reference and original print geometry remains unproven. The clinical printable-source gate therefore remains blocking.
