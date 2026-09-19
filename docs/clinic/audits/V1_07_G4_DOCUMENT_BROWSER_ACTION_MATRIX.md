# Digital Crown V1-07 — G4 Documents Browser Action Matrix

Status: IN PROGRESS — direct browser action reconciliation

## Verified basis

- Browser denominator: run #35468756588, exact HEAD `e46bb2587acbb8435bee364d63e1d6b4c4b2d3a5`, PASS.
- T2 Runtime Browser Certification: run #35468756723, same exact HEAD, PASS; artifact digest `sha256:1299f95313ce6d75ae9d185ef5f951364e7026cd473e608072ef5d77c468a346`.
- P7 Final Patient Matrix: run #35468756801, same exact HEAD, PASS.
- Documents-related browser denominator: **95 semantic controls** = 94 document-only + `Historique`, also exposed by panoramic.

Render/presence is not action proof. A control closes only after a real browser action and an observable result/refusal. Initial disabled controls are not waived: the prerequisite must be created and the enabled control exercised.

## Reconciliation at the pre-fix browser baseline

- `PASS_BROWSER_ACTION`: **16/95**
- `PARTIAL_BROWSER_ACTION`: **4/95**
- `PENDING_DYNAMIC_PREREQ`: **3/95**
- `PENDING_BROWSER_ACTION`: **72/95**

This is **not a certification percentage**. Dynamic controls revealed after earlier actions are not yet included in the denominator.

### Direct browser PASS already proved

T2/P7/Ordonnance browser evidence directly exercises:
- Document tabs: Certificat, Devis, Document Libre, Note Honoraires, Ordonnance, Suivi Paiement.
- `Aperçu` on the four surfaces exposing it, including modal/inline dismissal.
- `Actes rapides` in accounting, followed by the dynamically revealed new-act flow.
- Document Libre: title field, content field, A5, A4, Justifié, Tableau.
- Ordonnance: medication/DCI field via AMOXICILLINE catalog lookup and explicit presentation selection.
- Ordonnance: `Renseigner` and the real clinical-context expansion.
- P7: Documents → Historique transition.

### Partial browser proof

- `Enregistrer`: proved on Document Libre; remaining document types still require direct result proof.
- `Imprimer`: proved on Note Honoraires including confirmation and actual iframe-print path; remaining exposed types still require direct proof.
- `Fermer`: proved on Libre preview; certificate instance remains.
- `Historique`: Documents transition proved; panoramic/history variants remain to reconcile.

### Dynamic prerequisites still required

- Ordonnance: `Monter le médicament` and `Descendre le médicament` are disabled with a single row; add a second row, then exercise both.
- Échéancier: `Enregistrer le plan` is initially disabled; create a valid balanced schedule, then exercise save and persistence.

## Strict remaining groups

### Ordonnance
Initial denominator gaps:
- Ajouter une ligne
- Indication de cette ordonnance
- Mentions légales
- Supprimer le médicament
- Type médicament
- Type radio ou examen
- Monter / Descendre after second-row prerequisite
- save/print business result on ordonnance

Dynamic denominator already known from Playwright:
- medication catalog presentation buttons
- clinical-context controls
- IE prophylaxis controls
- **manual form chooser** revealed only after medication identity entry

The browser audit found a real defect: the enabled manual-form trigger was wired to `onFormeOpen={() => undefined}`. The corrected candidate restores the canonical `FORMES` chooser and adds a focused component proof. Browser AFTER evidence is still required before calling it fixed.

### Note Honoraires / Devis
Pending direct browser action includes:
- + Ligne Manuelle
- Adult / Enfant
- odontogram mode controls
- all 32 tooth buttons
- Bridge & Prothèses
- Soins Ciblés / Soins Généraux
- Plan de soins / Réduire Schéma
- Procéder à l'Encaissement
- remaining save/print outcomes

Existing component/business tests are complementary only; they do not replace the browser gate.

### Certificat
Pending:
- Arrêt de travail
- Présence au cabinet
- Certificat médical
- author/date controls
- Actualiser / Fermer / Préparer impression
- generation result

### Échéancier
Pending:
- Nouveau plan
- total/advance/date/month-count fields
- Générer le tableau
- Ajouter manuellement
- enable + Enregistrer le plan
- dynamically revealed row controls, payment method, Encaisser, reminder, delete
- persistence/refusal proof

### Document Libre residual
Already browser-proved: title, content, A5, A4, Justifié, Tableau.
Pending: recipient, date/place, hide-header, Gauche, Centre, Droite, Gras, Italique, Souligné, Grand Titre, remaining output controls.

### History
Pending:
- search field
- dynamic per-document action menu controls
- edit/trash behavior and refusal/non-mutation where applicable

## Current remediation batch

1. Restore Ordonnance manual form chooser using the existing canonical `FORMES` list and legacy interaction pattern.
2. Add focused regression test for actual open/select behavior.
3. Repair Ordonnance Fidelity workflow isolation contract: explicit isolated-runtime flag + DB fingerprint.
4. Re-run exact-head build, T2 browser, P7, G4 inventory and Ordonnance Fidelity.
5. Only after those are green, promote the repaired dynamic control to browser PASS and continue the remaining Ordonnance actions, then Note Honoraires.

## Certification condition

G4 Documents can close only when:
- every enabled denominator control is `PASS_BROWSER_ACTION` or `PASS_REFUSAL_NON_MUTATION`;
- disabled initial controls have verified prerequisite-state explanations and are exercised when their prerequisite can be created;
- dynamic controls revealed by actions are appended and reconciled;
- exact-head build/browser runs are green;
- a final post-action inventory finds zero unclassified critical control.


## Executable action-pass probes added

The next candidate embeds direct Chromium action probes into the already isolated T2 runtime certification:
- `frontend/scripts/certify-v1-07-g4-ordonnance-actions.mjs`
- `frontend/scripts/certify-v1-07-g4-honoraires-actions.mjs`

Ordonnance probe exercises type toggle, add/reorder/remove, repaired manual-form chooser, dose/NS/structured+free posology, indication/legal toggle, clinical-context save and explicit IE evaluation across 390×844 and 1280×900.

Honoraires probe exercises odontogram open/adult-pediatric, all adult quick groups, representative grouped/custom acts, targeted tooth treatment with price+notes, general-care actions, manual line order/delete, treasury status/payment/global-plan controls, and directly proves whether the current `Confirmer l'Encaissement` action performs a persistence request.

No status is promoted to PASS until the exact-head T2 artifact succeeds.
