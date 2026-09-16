# HANDOVER — Digital Crown / Mutuelles dentaires — FAR SOURCE/GATE

Date: 2026-09-17
Repository: `hraaaaf/Digital_crown`
Branch: `docs/mutuelles-far-source-gate-20260916`
PR: `#559` — OPEN / DRAFT / NOT MERGED

## Goal

Certify one printable FAR application reference before any FAR implementation.

Success is observable only when `docs/audits/MUTUELLES_DENTAIRES_FAR_GATE.md` is upgraded from BLOCKED with a hash-bound printable binary, proven page geometry, visual Target -> Render validation, prescription isolation and exact field contract.

## Cabinet decision now recorded

The cabinet explicitly confirmed that the correct visual/model identity is:

`https://fr.scribd.com/document/1025435397/Feuille-de-Mutuelle-FAR-2021-1`

Current trust classification:

`CABINET_VALIDATED_LAYOUT_IDENTITY`

This validates the intended layout, not one exact PDF binary.

## Recovered real bytes

### Public Scribd render — doc 777249804

Downloaded successfully from the public Scribd CDN:

`https://imgv2-2-f.scribdassets.com/img/document/777249804/original/83ef2ce61d/1730193779?v=1`

Verified:

- JPEG;
- 768 x 1024 px;
- 175012 bytes;
- SHA-256 `cf6a071beb0bb8934684d0cd137b1f7b237895976ace8aea44d1bdaf49df6dd5`.

The image contains the four logical FAR areas in a 2x2 composition: Page 4, Page 1, Page 2 `ORDONNANCE`, Page 3 provider acts.

### Independent public Scribd render — doc 700464590

Downloaded successfully:

`https://imgv2-1-f.scribdassets.com/img/document/700464590/original/a669235acb/1706029303?v=1`

Verified:

- JPEG;
- 768 x 1024 px;
- 183182 bytes;
- SHA-256 `aacddaa2b8ccf3fd1a7a065939a334ee786f8ca957959b701c53300244be3154`.

It independently reproduces the same four logical pages but with different scan/crop characteristics. Automated feature registration found matches on all four logical quadrants; the two assets are not pixel-identical and are not one canonical binary.

### Low-resolution doc 742194320 asset

The exposed `original` URL resolves only to:

- 255 x 330 px;
- 2163 bytes;
- SHA-256 `b52459bb3b0283eb244ee40b8655bd2ab8ff4ba96a245bd4bcc65678d1ccaf2f`.

Tested `/1`..`/4` variants returned identical bytes. Guessed higher-resolution dimension variants returned `403`. Do not use this asset for print geometry.

## Download endpoint result

Unauthenticated/no-cookie checks only; no bypass attempted:

- Scribd download endpoint for `777249804` -> `403`;
- exact cabinet-selected `1025435397` -> `403`;
- `742194320` -> `302` to deleted page.

A Studocu signed image URL is indexed and visually corroborates Page 1/Page 4, but its exposed signature is expired/currently rejected with `403`; no separate Studocu page bytes were certified.

## Logical layout — verified

- Page 1: feuille de maladie/member/beneficiary + treating practitioner;
- Page 2: `ORDONNANCE`;
- Page 3: acts/dates/coefficients/fees/stamp-signature;
- Page 4: `SOINS ET PROTHESE DENTAIRE (INPE)` + dental chart/prosthetic table/medical control.

Scribd lists the selected/corroborating documents as 2 pages, while the form labels four logical pages. The recovered 768 x 1024 assets are preview compositions and do not prove the original physical two-page dimensions/imposition.

## Exact blocker now

The model identity is no longer the blocker.

The remaining blocker is:

**no certified printable reference geometry at sufficient fidelity**.

Therefore do not yet claim:

- exact original PDF binary;
- original physical page dimensions;
- exact original imposition;
- safe overlay coordinates;
- `OFFICIAL_PRIMARY`;
- `CABINET_VALIDATED_BINARY`.

## Two valid continuation paths

### Path A — preferred if obtained

Recover a legitimate full-resolution PDF/scan matching the cabinet-selected model, then SHA -> bytes -> pages -> dimensions -> render -> visual inspection -> trust -> gate.

### Path B — authorized technical fallback

Create a clean printable reconstruction based on the cabinet-validated layout and corroborating render assets.

Required classification:

`CABINET_VALIDATED_RECONSTRUCTED_REFERENCE`

It must never be described as the original/official FAR binary.

Before it can authorize implementation:

1. freeze exact reconstructed binary;
2. compute SHA-256 + byte size;
3. record exact page count/dimensions;
4. visually inspect every page;
5. Target -> Render comparison against the selected model at the same logical views;
6. isolate `FAR_PRESCRIPTION`;
7. cabinet accepts the reconstructed printable output;
8. bind source/trust to its SHA;
9. only then derive overlay coordinates.

## Prescription hard boundary

`FAR_PRESCRIPTION` remains independently validated.

Never infer from dental acts/NGAP:

- molecule;
- dose;
- posology;
- duration;
- frequency.

Medication content comes only from explicit prescription data and practitioner review.

## Architecture constraint

One Mutuelles engine only:

`Patient -> Honoraires -> Preparer organisme -> Revue praticien -> Validation -> PDF -> DocumentArchive`

Forbidden:

- second Mutuelles/Honoraires engine;
- second clinical catalog;
- fuzzy NGAP;
- artificial backfill;
- silent deduction of unknown fields;
- fabricated signature/stamp;
- fabricated insurer decision;
- FAR implementation from preview coordinates;
- production mutation during source gate;
- Vercel deploy without explicit authorization;
- merge without explicit user agreement.

## Git state last verified before the evidence update

- prior branch HEAD: `5a2798ce063fd7503503e83dc863d561cee41d96`;
- master: `eb2353b68d880b89dfadd13819fb43d1c71e2f1d`;
- branch was ahead by 2 and behind master by 5;
- master-only compared changes were outside FAR docs: `backend/tests/test_agenda_availability_wiring.py` and `backend/tests/test_mobile_identity_security.py`.

Gate update commit created after that comparison:

`63d3cd03f46b98ab335203b740791638f3d8d940`

No FAR code, DB mutation, production mutation, deploy or merge was performed.

## Current gate score

- EXECUTION_SCORE: 5.9/10
- ADVERSARIAL_SCORE: 5.9/10
- retained: 5.9/10 — BLOCKED

Reason: the clinical printable-source/geometry proof remains mandatory and absent.

## Next exact

Proceed with Path B while continuing to prefer Path A if a legitimate full-resolution binary appears:

1. create a reconstructed printable reference without claiming it is official;
2. preserve the four logical roles and separate `ORDONNANCE`;
3. render and compare against the cabinet-selected target;
4. freeze SHA/pages/dimensions;
5. present the reconstruction for cabinet acceptance;
6. after acceptance only: upgrade gate and start FAR implementation on a branch reconciled with current master.

## Sequence remaining

`printable reconstruction -> render/compare -> cabinet acceptance -> SHA/page geometry/trust -> gate upgrade -> reconcile master -> FAR implementation -> tests -> UI/PDF Target↔Render -> CNSS/CNOPS/Honoraires regressions -> exact-HEAD CI -> user merge agreement -> merge -> post-merge proof -> closeout`

## Resume prompt

Continue Digital Crown / Mutuelles dentaires / FAR SOURCE-GATE from this file. Re-read `MUTUELLES_DENTAIRES_FAR_GATE.md`, verify current master/PR #559/branch HEAD, then continue Path B reconstruction unless a legitimate higher-fidelity Path A binary is available. Do not code FAR until the gate is upgraded. No merge without explicit user agreement and no Vercel deployment without explicit authorization.
