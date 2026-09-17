# HANDOVER — Digital Crown / Mutuelles dentaires — FAR

Date: 2026-09-17
Repository: `hraaaaf/Digital_crown`
Branch: `docs/mutuelles-far-source-gate-20260916`
PR: `#559` — OPEN / DRAFT / NOT MERGED

## Goal

Implement FAR dental support inside the existing single Mutuelles engine from the exact cabinet-accepted derived reference, while keeping prescription content clinically separate and fail-closed.

## Source gate

`docs/audits/MUTUELLES_DENTAIRES_FAR_GATE.md`

Status: `SOURCE_GATE_PASSED`.

Frozen application reference:

- filename `FAR_CABINET_VALIDATED_DERIVED_REFERENCE_FINAL.pdf`
- SHA-256 `c953d74f25ee5e3160683f16c45783448d55ea89640c710653a3e2cbf782bf42`
- size `759862` bytes
- `2` physical pages
- A4 landscape `841.8897705 x 595.2755737 pt`
- physical page 1 = logical Page 4 | Page 1
- physical page 2 = logical Page 2 ORDONNANCE | Page 3

Trust is `CABINET_VALIDATED_DERIVED_REFERENCE`, never `OFFICIAL_PRIMARY`.

## Architecture lock

One engine only:

`Patient -> Honoraires -> Preparer organisme -> Revue praticien -> Validation -> PDF -> DocumentArchive`

Reuse existing `InsuranceSubmissionDraft`, Honoraires truth, `CatalogAct`, NGAP exact mapping, source store, practitioner validation, anti-stale finalization and archive.

## Required FAR extension

1. add explicit derived-reference trust accepted only with cabinet validator identity;
2. bind FAR template/profile to the exact SHA and 2-page geometry;
3. model FAR-only explicit member facts instead of overloading unrelated fields: account number, phone, grade, unit;
4. add explicit claim context `MALADIE|MATERNITE|ACCIDENT`;
5. preserve explicit relationship `ADHERENT|CONJOINT|ENFANT`;
6. overlay Page 1 administrative fields and logical Page 4 dental rows;
7. do not duplicate dental lines on logical Page 3;
8. keep logical Page 2 as `FAR_PRESCRIPTION` with independent validation/source;
9. no molecule/dose/posology/duration/frequency inferred from acts/NGAP.

## Required tests

Positive and negative coverage for:

- derived trust accepted only for exact cabinet-validated source manifest;
- wrong hash/trust/page count rejected;
- missing FAR member facts fail closed;
- unknown relationship/context fail closed;
- overlay bound to FAR SHA and page indices;
- signature/cachet/insurer zones never generated;
- prescription not populated from dental acts;
- CNSS and CNOPS existing contracts remain green;
- exact-head CI before merge.

## Git state

The FAR branch was reconciled with master `7d936cc76257911d03e98f7788f25056399783d3` before the source-gate upgrade.

No merge and no Vercel deployment are authorized without explicit user agreement.

## Next exact

Implement runtime trust + FAR admin policy + FAR overlay profile + tests. Then inspect rendered PDF, perform CNSS/CNOPS regression and exact-head CI.

## Sequence remaining

`runtime trust -> FAR admin schema/policy -> FAR template/profile -> router wiring -> prescription boundary -> backend tests -> rendered PDF proof -> CNSS/CNOPS regression -> frontend FAR review/action -> responsive AFTER -> exact-head CI -> explicit merge agreement -> merge -> post-merge proof -> closeout`
