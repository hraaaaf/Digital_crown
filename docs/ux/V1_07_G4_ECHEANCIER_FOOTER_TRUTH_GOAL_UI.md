# V1-07 G4 — Suivi Paiement footer truth UI goal

## BEFORE
Current source contract for `activeTab === 'echeancier'` routes all footer generation through `/installments/generate-preview`. The footer button is still labelled `Enregistrer`, while actual plan persistence is performed separately by `Enregistrer le plan`.

## Goal
The footer must not imply persistence when it only generates a PDF representation.

## Target
- Rename footer `Enregistrer` → `Générer PDF` only for `echeancier`.
- Keep `Enregistrer le plan` as the sole explicit persistence action for the payment plan.
- Keep `Imprimer` for the print path.
- No backend behavior change.

## AFTER acceptance
Matched 390×844 and 1280×900:
1. `Enregistrer le plan` persists the balanced plan and reloads persisted rows;
2. footer `Générer PDF` calls `/installments/generate-preview` only;
3. no document/archive/payment mutation occurs on `Générer PDF`;
4. `Imprimer` uses the same generated PDF and retains explicit print warning;
5. no overflow/page errors;
6. wording clearly distinguishes persistence from PDF generation.

Visual score rubric: 3 truthfulness + 2 hierarchy + 2 responsive/touch + 2 behavioral consistency + 1 runtime-clean. Target 10/10 only with browser proof.
