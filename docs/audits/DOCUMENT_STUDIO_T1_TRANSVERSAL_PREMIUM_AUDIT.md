# Document Studio — T1 Audit transversal premium

Date: 2026-08-16
Baseline code: `0a720dace83613cfc9fb0e0ae1c754e19c447c28` (P7-G head)
Scope: shared Document Studio boundaries after P1–P7 engineering work.

## 1. Proof contract

This audit separates:
- **CODE VÉRIFIÉ**: statically inspected source on the exact baseline above.
- **TEST EXÉCUTÉ**: only when an actual test run is observed.
- **INTERACTION RUNTIME**: only when reproduced in the authenticated product.
- **CERTIFICATION**: only after the required runtime/CI/manual gates pass.

No current CI PASS or runtime certification is inferred from historical runs.

## 2. Real shared architecture

- `/patients/:id` renders `PatientDetails`.
- The admin tab renders `<DocumentHub patientId={id!} patientName={fullName} editData={editingDoc} />` without a React `key` bound to the patient id.
- `DocumentHub` owns local drafts/previews for prescription, certificate, libre, plan and shared intelligence state.
- P3/P4 financial drafts live in the global Zustand `useAccountingStore`; the store exposes `reset()` but `DocumentHub` / `AccountingStudio` do not reset it on patient change.
- `DocumentHub` fetches patient details asynchronously and writes them directly into shared state.
- URL-driven `documentTab` changes call `setActiveTab` directly rather than the canonical guarded tab-change path.
- Cross-page “intelligence” derives safety/clinical recommendations from free-text patient antecedents and from financial act labels.

## 3. Matrix

### GARDER

- Patient header in `PatientDetails` remains the primary visible patient identity.
- P1/P6/P7 already have dedicated dirty-state work that T1 should unify rather than replace.
- P3/P4 share one explicit accounting store and already expose a reset primitive.
- Deterministic prescription safety endpoint remains distinct from UI-only free-text heuristics.

### CORRIGER — P0

#### T1-P0-1 — Cross-patient financial draft persistence

**CODE VÉRIFIÉ**

`PatientDetails` can keep the same component tree while the `/patients/:id` route parameter changes. `DocumentHub` is rendered without `key={id}`. `useAccountingStore` is global and contains patient-sensitive items, payment mode/status, installments, odontogram selections and suggestions. Its `reset()` is not called on `patientId` change by the inspected shared components.

**Risk:** a draft created for patient A can remain in the shared financial store when the UI is now on patient B.

**Required target:** patient identity is an isolation boundary. Financial/editor state must never cross it. Reset must be deterministic and tested.

#### T1-P0-2 — Stale patient-details response can overwrite current patient context

**CODE VÉRIFIÉ**

The `DocumentHub` patient-details effect starts `api.get(/patients/{patientId})` and applies `setPatientDetails(res.data)` without an effect-local cancellation/sequence guard.

**Risk:** after rapid A→B navigation, a late A response can overwrite B's context and feed shared intelligence/generation state.

**Required target:** stale responses are ignored; patient context is cleared/reset immediately at boundary change.

#### T1-P0-3 — Free-text antecedents generate prescriptive/clinical recommendations

**CODE VÉRIFIÉ**

“Ghost Complications” substring-matches `antecedents_medicaux` and emits statements such as strict antibiotic coverage or radiography contraindication. Another shared heuristic offers generation of an analgesic/antibiotic protocol from financial surgical-act labels.

**Risk:** unstructured text and financial labels are not authoritative clinical facts and must not directly create prescriptive recommendations.

**Required target:** free-text/financial detections may only surface a neutral verification warning. Medication, imaging or treatment advice requires an authoritative validated clinical rule/data path.

#### T1-P0-4 — Programmatic tab changes bypass dirty guards

**CODE VÉRIFIÉ**

`documentTab` search-param synchronization calls `setActiveTab` directly. This bypasses the `handleTabChange` dirty guard used by interactive tabs.

**Risk:** URL/event-driven navigation can discard unsaved content even when manual navigation is protected.

**Required target:** every tab transition uses one guarded transition contract, with an explicit internal force path only after discard/commit.

### AMÉLIORER / P1

- Unify dirty-state reporting for all P1–P7 editors instead of page-specific partial guards.
- Remove static “server OK” or capability claims not backed by live state/proof.
- Remove unsupported preview claims such as generic “standards professionnels” / “signature numérique intégrée” unless the exact feature is evidenced.
- Make preview width responsive; avoid fixed desktop assumptions around side preview.
- Ensure all icon-only controls and tab controls have keyboard/focus/accessible names.
- Preserve visible patient identity in compact/mobile Document Studio states.
- Reset page-specific local previews, suggestions and archived edit hydration when patient changes.

### SIMPLIFIER / SUPPRIMER

- Do not maintain multiple independent tab-transition mechanisms.
- Do not keep “Ghost” marketing terminology for clinical safety logic in the certified path.
- Do not duplicate prescription suggestions from accounting context when a validated prescription safety engine already exists.

## 4. Target transversal contract

1. **Patient boundary:** patient id change invalidates every patient-scoped draft, preview, suggestion and async response from the old patient.
2. **Navigation boundary:** all tab transitions go through one dirty-aware transition function.
3. **Clinical boundary:** free-text antecedents and financial descriptions can flag “à vérifier”, never prescribe or infer contraindications/treatment by themselves.
4. **Truthful UI:** health/capability/status badges reflect real state or are removed.
5. **Responsive/a11y:** core authoring and preview are usable at 390/430/1280 widths with keyboard-visible controls.
6. **Proof:** T1 is not certified until targeted tests + full frontend build/tests + authenticated runtime cross-patient/navigation checks pass.

## 5. Corrective lots — critical path

- **T1-A Patient isolation:** reset patient-scoped local/Zustand state, stale-response guard, cross-patient regression tests.
- **T1-B Unified navigation guard:** route URL/custom-event/manual transitions through one dirty-aware contract.
- **T1-C Clinical inference boundary:** neutralize free-text/financial prescriptive heuristics; keep only verification warnings.
- **T1-D Truthful status/preview:** remove or wire static server/capability claims.
- **T1-E Responsive/a11y:** responsive preview, focus/labels, compact patient identity.
- **T1-F Final transversal recertification:** targeted harness + full frontend suite/build + authenticated runtime matrix.

## 6. Runtime gates still open

Required before final T1 certification:
- A→B patient switch while P3/P4 draft is populated: no old item/payment/installment survives.
- A→B switch with delayed A patient response: B context remains authoritative.
- Dirty P1/P3/P4/P6/P7 + manual and programmatic tab changes: same discard/continue behavior.
- No free-text antecedent can directly generate medication/imaging/treatment advice.
- 390/430/1280 responsive matrix.
- Keyboard/focus smoke check.
- Full frontend test suite and production build on the exact final head.

## 7. Current status

Audit baseline only. Findings above are **CODE VÉRIFIÉ** unless explicitly labelled otherwise. No T1 runtime PASS or certification is claimed.