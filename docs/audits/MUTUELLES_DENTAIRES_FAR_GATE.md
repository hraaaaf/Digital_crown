# MUTUELLES DENTAIRES — FAR SOURCE / GATE

Date: 2026-09-17
Status: **SOURCE_GATE_PASSED — IMPLEMENTATION AUTHORIZED UNDER DERIVED-REFERENCE TRUST**
Scope: FAR dental only. This gate does not claim official FAR provenance.

## Goal

Certify one printable FAR application reference and its fail-closed data contract before FAR code, while preserving the existing single Mutuelles/Honoraires engine and isolating the prescription as a separate clinical role.

## Cabinet decision

The cabinet selected the MFAR “Feuille de Mutuelle FAR 2021-1” layout and explicitly accepted the calibrated reconstruction produced in this workstream as the printable application reference.

The accepted reference is **not** an original/official FAR PDF. Trust is therefore:

`CABINET_VALIDATED_DERIVED_REFERENCE`

Never promote it to `OFFICIAL_PRIMARY` or describe it as an original FAR binary without new primary-source proof.

## Frozen printable reference

Filename: `FAR_CABINET_VALIDATED_DERIVED_REFERENCE_FINAL.pdf`

Verified exact bytes:

- SHA-256: `c953d74f25ee5e3160683f16c45783448d55ea89640c710653a3e2cbf782bf42`
- byte size: `759862`
- physical pages: `2`
- page 1 geometry: `841.8897705 x 595.2755737 pt`
- page 2 geometry: `841.8897705 x 595.2755737 pt`
- format: A4 landscape

Both physical pages were rendered from the frozen PDF and visually inspected after the cabinet accepted the calibrated reconstruction.

Logical imposition:

- physical page 1: logical `Page 4 | Page 1`
- physical page 2: logical `Page 2 ORDONNANCE | Page 3`

The original FAR physical geometry remains unknown; the geometry above is the exact application geometry of the cabinet-accepted derived reference.

## Source corroboration

The layout identity was corroborated by separate public reproductions, including Scribd documents `1025435397`, `777249804`, `742194320`, `700464590`, `796381015`, `830287170` and a Studocu reproduction. These are secondary reproductions and are not primary FAR publications.

Two downloaded high-resolution render assets were hash-locked during the source pass:

- `777249804`: 768x1024 JPEG, 175012 bytes, SHA-256 `cf6a071beb0bb8934684d0cd137b1f7b237895976ace8aea44d1bdaf49df6dd5`
- `700464590`: 768x1024 JPEG, 183182 bytes, SHA-256 `aacddaa2b8ccf3fd1a7a065939a334ee786f8ca957959b701c53300244be3154`

No authentication/paywall bypass was used and no official primary downloadable FAR binary was recovered.

## Logical document roles

- `Page 1`: member/beneficiary administrative information and treating-practitioner INPE.
- `Page 2`: `FAR_PRESCRIPTION` — independent clinical prescription role.
- `Page 3`: general provider acts area. Digital Crown must not duplicate dental rows here when Page 4 is the dental truth surface.
- `Page 4`: dental/prosthetic care table, dental chart and medical-control area. This is the dental-claim overlay surface.

## Prescription hard boundary

`FAR_PRESCRIPTION` remains independently validated.

Forbidden deductions from dental acts/NGAP:

- molecule;
- dose;
- posology;
- duration;
- frequency.

Prescription content may come only from explicit prescription data reviewed by the practitioner. A combined printable document may be assembled only after independent validation of the dental claim and prescription sub-document when prescription content is present.

## Allowed automatic data

Only explicit existing truth sources may be used:

- patient/beneficiary identity and birth date;
- practitioner identity and explicit INPE;
- actual service dates;
- dental acts, tooth positions, exact NGAP code/coefficient and Honoraires amount;
- computed total derived from exact Honoraires lines;
- explicit FAR administrative fields entered/reviewed by the practitioner/operator;
- explicit prescription content from its dedicated source.

## FAR administrative fields that must fail closed when absent

The FAR form visibly requires member facts that cannot be guessed from ordinary patient data. Implementation must model them explicitly rather than overload unrelated CNSS/CNOPS fields:

- member national ID;
- member account number;
- member telephone;
- member full name;
- member grade;
- member unit;
- member address;
- beneficiary full name;
- beneficiary birth date;
- relationship to member (`ADHERENT`, `CONJOINT`, `ENFANT`) explicitly selected;
- claim context (`MALADIE`, `MATERNITE`, `ACCIDENT`) explicitly selected;
- practitioner INPE.

No grade/unit/account/relationship/context may be inferred.

## Forbidden / fail-closed

- guessed member/account/grade/unit/telephone;
- guessed relationship or claim context;
- fuzzy NGAP mapping;
- artificial backfill;
- fabricated signature/cachet;
- fabricated insurer decision;
- prescription inferred from dental acts/NGAP;
- CNSS/CNOPS overlay coordinates reused for FAR;
- treating a derived reference as official primary;
- production mutation;
- Vercel deployment without explicit user authorization;
- merge without explicit user agreement.

## Architecture lock

Reuse exactly one engine:

`Patient -> Honoraires -> Preparer organisme -> Revue praticien -> Validation -> PDF -> DocumentArchive`

Reuse: `InsuranceSubmissionDraft`, Honoraires financial truth, `CatalogAct`, NGAP exact mapping, immutable/hash-addressed template store, practitioner validation, anti-stale revalidation, hash-bound PDF rendering and `DocumentArchive`.

A second Mutuelles/Honoraires engine or second clinical catalog is forbidden.

## Implementation authorization

The SOURCE/GATE is passed for implementation against the exact hash above, subject to these mandatory implementation gates:

1. add an explicit runtime trust value for `CABINET_VALIDATED_DERIVED_REFERENCE` and require cabinet validator identity;
2. bind FAR template/profile to exact SHA-256 `c953d74f...` and exactly 2 A4-landscape pages;
3. implement FAR-specific explicit administrative fields/policy without guessing;
4. populate dental rows on logical Page 4 only;
5. keep Page 2 prescription content separate and fail closed;
6. add positive and negative tests for trust/hash/page count/admin/overlay/prescription boundaries;
7. prove CNSS/CNOPS regressions remain green;
8. run exact-HEAD CI and visual Target -> Render proof before merge.

## Repository state at gate upgrade

- repository: `hraaaaf/Digital_crown`
- branch: `docs/mutuelles-far-source-gate-20260916`
- branch reconciled with master `7d936cc76257911d03e98f7788f25056399783d3` before this gate upgrade
- PR `#559`: OPEN / DRAFT
- no merge authorized
- no Vercel deployment authorized

## Scoring

- SOURCE EXECUTION_SCORE: **9.0/10**
- SOURCE ADVERSARIAL_SCORE: **8.7/10**
- retained source score: **8.7/10 — SOURCE_GATE_PASSED**

The score is intentionally below 10 because the accepted application reference is reconstructed/derived rather than an official primary FAR binary.

## Next exact

Implement the minimum FAR runtime extension on this reconciled branch, then prove backend contracts, rendered PDF placement, prescription isolation and CNSS/CNOPS non-regression before requesting merge approval.
