# HANDOVER — Digital Crown / Mutuelles dentaires — FAR SOURCE/GATE

Date: 2026-09-16
Repository: `hraaaaf/Digital_crown`
Branch: `docs/mutuelles-far-source-gate-20260916`
PR: `#559` — OPEN / DRAFT / NOT MERGED
Branch HEAD before this handover commit: `8ecc1a6f3298d45dbbbc7f1d60e1dfb3dc9ca277`
Latest verified master while preparing the gate: `ef23b7147c5ed3dfa7c06267eec797a520cb7366`

## Goal

Complete a reliable FAR SOURCE/GATE before any FAR implementation.

Exact outcome required:

1. recover the exact FAR reference binary;
2. compute SHA-256 and byte size;
3. establish physical PDF page count and dimensions;
4. visually inspect every page;
5. map physical pages to logical form roles;
6. isolate and certify the `ORDONNANCE` role independently;
7. bind provenance/trust to the exact binary SHA;
8. map allowed and forbidden fields;
9. verify reuse of the existing Mutuelles engine;
10. only then authorize implementation.

Success is observable only when `docs/audits/MUTUELLES_DENTAIRES_FAR_GATE.md` is upgraded from BLOCKED with exact binary proofs.

## Mandatory start order in the next conversation

Read:

1. `docs/audits/MUTUELLES_DENTAIRES_FAR_START_PROMPT.md`
2. `docs/audits/MUTUELLES_DENTAIRES_FAR_GATE.md`
3. this handover
4. `docs/audits/MUTUELLES_DENTAIRES_INTEGRATION_ROADMAP.md`
5. `docs/audits/MUTUELLES_DENTAIRES_CNOPS_TO_FAR_HANDOVER.md`
6. `docs/audits/MUTUELLES_NGAP_DENTAL_REFERENCE.md`

Then re-check GitHub `master`, PR #559, branch HEAD and compare/mergeability before any write because master is moving through parallel Digital Crown work.

## Verified current state

### Repository / Git

The earlier FAR start point `4cffca14...` is obsolete.

During this pass master first advanced to:

`96a5d1a68ac027f112e0ca349ed6f2f0abbe3243`

Then Agenda A3 merged and master advanced again to:

`ef23b7147c5ed3dfa7c06267eec797a520cb7366`

The FAR branch was reconciled onto that latter master before re-adding the gate.

Verified compare before this handover:

- base: `ef23b7147c5ed3dfa7c06267eec797a520cb7366`
- FAR gate HEAD: `8ecc1a6f3298d45dbbbc7f1d60e1dfb3dc9ca277`
- status: ahead
- ahead_by: 1
- behind_by: 0
- changed files: exactly 1, `docs/audits/MUTUELLES_DENTAIRES_FAR_GATE.md`

PR #559 is OPEN + DRAFT and not merged. It was temporarily auto-closed when the branch ref was reconciled to master, then reopened after the gate commit was recreated. Do not merge without explicit user agreement.

No FAR code, DB mutation or deployment has been performed.

### CI

At HEAD `8ecc1a6f...`, `fetch_commit_workflow_runs` returned no workflow runs at the time checked. Do not interpret absence as green CI. Re-check when relevant.

## FAR source identity

Chosen/fixed layout identity from the project context:

**MFAR — `Feuille de Mutuelle FAR 2021-1`**

This identity is strongly corroborated by multiple independent web uploads, but one exact binary has NOT yet been certified byte-for-byte.

Corroborating sources used in the gate:

- Scribd document `1025435397/Feuille-de-Mutuelle-FAR-2021-1`
- Scribd document `742194320/FAR-Recto-Verso`
- Studocu `feuille-de-soins-dentaire-inpe-mutuelle-des-far/137649272`

These are secondary user-upload sources, not official primary FAR publications.

Verified/corroborated logical content includes:

- Page 1 — member/beneficiary / feuille de maladie information;
- Page 2 — `ORDONNANCE`;
- Page 3 — acts/dates/coefficients/fees/practitioner area;
- Page 4 — `SOINS ET PROTHESE DENTAIRE (INPE)` with dental chart and dental/prosthetic work areas.

Important ambiguity still open:

The web uploads are indexed as **2 PDF pages** while the reproduced form itself carries logical labels Page 1 through Page 4. Physical imposition, dimensions and exact geometry must therefore be derived from the recovered binary, not guessed.

## Exact blocker

**Exact FAR binary bytes are still missing.**

Therefore these facts are NOT verified:

- SHA-256;
- byte size;
- exact physical page count from the chosen bytes;
- page dimensions;
- exact page/imposition geometry;
- overlay coordinates;
- byte-bound provenance/trust.

No source may be labelled `OFFICIAL_PRIMARY` without real primary proof.
No source may be labelled `CABINET_VALIDATED_BINARY` unless the cabinet explicitly validates those exact bytes and that validation is bound to the SHA-256.

## Download/search attempts

Scribd and Studocu downloads require authentication for the accessible copies.

A strategy change was started: target only direct file/image assets or other mirrors rather than repeatedly searching locked document platforms.

A temporary Sprite named `far-source-fetch-20260916` was created to test retrieval of a Scribd asset URL. The first command invocation failed because the command wrapper was malformed; this is a tooling/quoting failure, NOT evidence that the asset is unavailable.

A corrected shell script `fetch_far.sh` was then written inside that Sprite, but **it has not yet been executed**. This is the immediate executable continuation if the Sprite remains available. Do not claim the asset was downloaded unless the script actually succeeds and the resulting bytes are inspected.

Candidate asset URL embedded in that script was a guessed Scribd CDN pattern for document `742194320`. Because the asset path/hash itself was not independently proven, a successful HTTP response would still need image/content verification before use.

After two similar retrieval failures, change strategy rather than repeatedly guessing CDN URLs: inspect page source/network metadata where legitimately accessible, search direct mirrors/caches, or obtain the cabinet scan.

## Gate file already created

`docs/audits/MUTUELLES_DENTAIRES_FAR_GATE.md`

Current gate decision:

**BLOCKED — SOURCE BINARY NOT YET CERTIFIED**

Current scores:

- EXECUTION_SCORE: 5.9/10
- ADVERSARIAL_SCORE: 5.9/10
- retained: 5.9/10 — BLOCKED

Reason: clinical/data source trust blocker. The exact binary proof required for implementation is absent.

## Architecture constraints — preserve exactly

There is one Mutuelles engine:

`Patient -> Honoraires -> Preparer organisme -> Revue praticien -> Validation -> PDF -> DocumentArchive`

Reuse the existing submission draft, Honoraires financial truth, clinical catalog, regulatory mapping layer, immutable/hash-addressed source handling, practitioner validation, anti-stale revalidation, hash-bound PDF finalization and DocumentArchive.

Forbidden:

- second Mutuelles/Honoraires engine;
- second clinical catalog;
- fuzzy NGAP;
- artificial backfill;
- silent deduction of unknown fields;
- fabricated signature/stamp;
- fabricated insurer decision/approval;
- production mutation during this source gate;
- Vercel deployment without explicit authorization;
- merge without explicit user agreement.

## Prescription hard boundary

The `ORDONNANCE` portion is a separate clinical sub-document/role, provisionally `FAR_PRESCRIPTION` until the exact binary confirms the geometry.

Never infer from dental acts/NGAP:

- molecule;
- dose;
- posology;
- duration;
- frequency.

Medication content must come from an explicit prescription source and require practitioner review. Prescription validation must be independent from dental claim validation. If the final FAR binary requires a combined PDF, reassemble only after independent validation of its logical sub-documents.

## UI/visual requirement for later implementation

For every FAR visual change:

BEFORE real -> written Goal -> exact reference/mockup -> implementation -> AFTER at the same viewports -> Target vs Render comparison -> tests -> visual score.

The prescription page/role requires its own visual certification. No visual fidelity score above 7.5 without a real Target vs Render comparison.

## Next exact

1. Re-check current master and PR #559 state because master may have moved again.
2. Continue direct binary retrieval, beginning with the already prepared Sprite script only if the Sprite is still available.
3. If that path fails, switch strategy immediately to direct mirror/cache/page-asset discovery; do not loop on Scribd/Studocu login walls.
4. Once bytes are obtained: compute SHA-256 + byte size.
5. Determine exact page count + dimensions.
6. Render and visually inspect every physical page.
7. Map physical pages to logical Page 1/2/3/4 roles and isolate `ORDONNANCE`.
8. Verify provenance/trust and bind it to SHA.
9. Update `MUTUELLES_DENTAIRES_FAR_GATE.md` with exact field/geometry evidence.
10. Only if all source gates pass, begin FAR implementation on a correctly based branch.

## Sequence remaining

`exact binary -> SHA/size -> PDF geometry -> page-by-page visual inspection -> ordonnance isolation -> provenance/trust -> exact allowed/forbidden field map -> common-engine delta -> gate upgrade -> implementation -> tests -> UI Target↔Render proof -> regression certification CNSS/CNOPS/Honoraires -> exact-HEAD CI -> user merge agreement -> merge -> post-merge proof -> closeout`

If the exact binary cannot be recovered from legitimate public sources, the true human gate is: obtain/upload a clean cabinet FAR scan/PDF and explicitly validate those exact bytes as the cabinet reference.

## Resume prompt

Continue Digital Crown / Mutuelles dentaires / FAR SOURCE-GATE from `docs/audits/MUTUELLES_DENTAIRES_FAR_HANDOVER.md`. Re-read the FAR start prompt and gate first, then verify current master/PR #559/branch HEAD. Do not code FAR until an exact binary is recovered and certified. Continue direct binary retrieval without looping on Scribd/Studocu login walls. Once bytes exist, SHA-256 -> size/pages/dimensions -> visual inspection every page -> isolate ORDONNANCE -> provenance/trust -> update gate -> only then implementation. No merge without explicit user agreement and no Vercel deployment without explicit authorization.
