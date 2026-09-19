# V1-07 G4 — Honoraires treasury truth UI goal

## BEFORE
Source contract on current candidate: the footer action labelled `Confirmer l'Encaissement` only executes `setIsTreasuryModalOpen(false)`. It does not call a payment/document/installment persistence endpoint. The configured payment state remains local until the Note Honoraires is generated/saved.

## Goal
The action label must describe what it actually does. Closing the modal after configuring status/mode/installments must not imply that money was persisted or collected.

## Target
- Rename `Confirmer l'Encaissement` → `Appliquer à la note`.
- Add concise explanatory copy: `Ces réglages seront enregistrés avec la note lors de son enregistrement.`
- Keep `Fermer` as a non-destructive dismiss action.
- No backend behavior change in this UI-only truth fix.

## AFTER acceptance
Matched 390×844 and 1280×900:
1. modal opens normally;
2. payment configuration controls remain unchanged;
3. `Appliquer à la note` closes the modal and keeps configured local state;
4. no payment/document/installment persistence request occurs on this click;
5. copy explicitly states persistence happens on document save;
6. no overflow/page errors;
7. final Note Honoraires `Enregistrer` remains the persistence boundary.

Visual score rubric: 3 truthfulness + 2 hierarchy/readability + 2 responsive/touch + 2 state continuity + 1 no-overflow/runtime-clean. Target 10/10 only with browser proof.
