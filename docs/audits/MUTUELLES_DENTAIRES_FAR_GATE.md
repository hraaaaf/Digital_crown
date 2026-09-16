# MUTUELLES DENTAIRES — FAR SOURCE / GATE

Date: 2026-09-16
Status: **BLOCKED — SOURCE BINARY NOT YET CERTIFIED**
Scope: FAR only. No FAR implementation is authorized by this gate.
Base master observed before this gate: `ef23b7147c5ed3dfa7c06267eec797a520cb7366`.

## Goal

Establish a reliable source and field contract for the Mutuelle des Forces Armées Royales (FAR) dental workflow before any implementation, while keeping the existing Mutuelles engine as the single engine and treating the prescription area/page as an independent clinical sub-document.

## Success criteria

The FAR SOURCE/GATE becomes implementation-authorizing only when all of the following are true:

1. exact reference binary is available as bytes;
2. exact SHA-256 and byte size are recorded;
3. exact PDF page count and dimensions are recorded;
4. every page is visually inspected;
5. logical role of every page is recorded;
6. prescription content is isolated as a separate logical role and contract;
7. source provenance/trust is classified and bound to the exact SHA-256;
8. allowed / forbidden auto-filled fields are mapped;
9. common Mutuelles engine coverage is checked and only the minimum FAR-specific extension is permitted;
10. no implementation starts before this gate is upgraded from BLOCKED.

## Current source candidate

Chosen layout identity: **MFAR — “Feuille de Mutuelle FAR 2021-1”**.

Historical project context confirms that the layout/form identity was chosen and fixed, but there is **no evidence of prior validation of one exact binary byte-for-byte**. Therefore the current trust level is **secondary / visually corroborated, binary unvalidated**. It must not be labelled `CABINET_VALIDATED_BINARY` yet.

### Corroborating web copies

- Scribd: `https://www.scribd.com/document/1025435397/Feuille-de-Mutuelle-FAR-2021-1`
  - indexed as 2 pages;
  - title matches the chosen form;
  - extracted text contains `SOINS ET PROTHESE DENTAIRE (INPE)` and `ORDONNANCE`;
  - source is a user upload, not an official FAR publication.
- Scribd: `https://www.scribd.com/document/742194320/FAR-Recto-Verso`
  - indexed as 2 pages;
  - independently reproduces the same FAR form content and labels;
  - source is a user upload, not an official FAR publication.
- Studocu: `https://www.studocu.com/row/document/ecole-nationale-des-sciences-appliquees-de-fes/mecanique-lagrangien/feuille-de-soins-dentaire-inpe-mutuelle-des-far/137649272`
  - independent visual/text corroboration of the dental claim layout;
  - not an official FAR source.

No official primary downloadable binary was found during this source-search pass.

## Verified layout facts from corroborated previews/text

The candidate form contains logical areas/pages labelled across the source as:

- `Page 1` — feuille de maladie / member and beneficiary information, treating practitioner identification;
- `Page 2` — `ORDONNANCE` with patient name and prescription area;
- `Page 3` — health-provider acts / dates / coefficients / fees / practitioner stamp-signature area;
- `Page 4` — `SOINS ET PROTHESE DENTAIRE (INPE)`, dental chart, dental/prosthetic work table, medical-control area.

The web platforms index the uploaded document as **2 pages**, while the reproduced form content itself carries logical labels Page 1 through Page 4. The exact physical PDF geometry and imposition remain **unverified until the actual bytes are recovered**.

## Prescription isolation

The `ORDONNANCE` content must be treated as a separate clinical role, provisionally named `FAR_PRESCRIPTION` until the exact binary is inspected.

Mandatory constraints:

- no molecule inferred from dental acts or NGAP;
- no dose inferred from dental acts or NGAP;
- no posology, duration or frequency inferred from dental acts or NGAP;
- medication content must come from explicit prescription data and require practitioner review;
- prescription validation must be independent from the dental-claim page validation;
- if a combined final PDF is required by the exact form, it may be assembled only after independent validation of each logical sub-document.

## Allowed field families — provisional until exact binary inspection

Potentially sourced from existing explicit cabinet/patient/practitioner data, subject to field-by-field verification against the exact binary:

- patient/member identity already explicitly stored;
- beneficiary identity/relationship when explicitly known;
- practitioner identity and INPE when explicitly configured;
- dates actually present in the source workflow;
- dental acts, tooth positions, coefficients and fees only from the existing clinical/financial truth sources already used by the Mutuelles engine;
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
- no FAR implementation based only on screenshots/previews;
- no trust classification higher than the evidence supports;
- no production mutation;
- no Vercel deployment without explicit user authorization;
- no merge without explicit user agreement.

## Common-engine constraint

FAR must reuse the existing Mutuelles flow and truth sources:

`Patient -> Honoraires -> Preparer organisme -> Revue praticien -> Validation -> PDF -> DocumentArchive`

Expected reuse includes the existing submission draft, Honoraires financial truth, clinical catalog, regulatory mapping layer, immutable/hash-addressed source handling, practitioner validation, anti-stale revalidation, hash-bound PDF overlay/finalization and DocumentArchive.

A second Mutuelles/Honoraires engine or second clinical catalog is forbidden.

## Current proofs

Verified in this pass:

- master had advanced and was re-read before writing: `ef23b7147c5ed3dfa7c06267eec797a520cb7366`;
- the chosen layout identity is consistently reproduced by multiple independent web uploads;
- `ORDONNANCE` and `SOINS ET PROTHESE DENTAIRE (INPE)` are present in the corroborated form;
- current historical evidence validates the layout choice, **not** one exact binary;
- no exact PDF SHA-256, byte size, dimensions or page geometry are currently proven.

## Gate decision

**BLOCKED for implementation.**

Reason: the exact reference binary has not yet been recovered/certified. The current evidence is sufficient to lock the intended layout identity and the separate-prescription architectural constraint, but insufficient to create reliable overlay coordinates or a hash-bound source contract.

## Next exact

Recover the exact FAR form as a real PDF/scan binary (preferred: the exact cabinet copy or a directly downloadable matching file), then in one pass:

1. compute SHA-256 and byte size;
2. record PDF page count and exact dimensions;
3. visually inspect every page;
4. map each physical page to its logical role(s);
5. confirm the prescription location and geometry;
6. bind the trust classification to that SHA-256;
7. upgrade this gate with the exact allowed/forbidden field map;
8. only then authorize FAR implementation.

## Scoring

- EXECUTION_SCORE: **5.9/10**
- ADVERSARIAL_SCORE: **5.9/10**
- Retained: **5.9/10 — BLOCKED**

Rationale: the clinical source identity is strongly corroborated, but the required exact binary proof is absent; by project scoring rules a clinical/data trust blocker caps the lot at 5.9 and prevents VERIFIED status.
