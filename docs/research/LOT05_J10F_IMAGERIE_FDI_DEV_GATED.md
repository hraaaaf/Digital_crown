# Digital Crown — LOT05 / 05.7-J10F — Imagerie/Panoramique FDI research integration (2026-10-22)

**Owner request:** “Vas y do it.” This sublot integrates a **non-clinical, development-only FDI correction workspace** into the actual patient Imagerie → Panoramique screen. It does **not** enable commercial inference or store model output in a patient record. Source experiment and selected model validation: [PR #1012](https://github.com/hraaaaf/Digital_crown/pull/1012), and [real 40-film FDI benchmark](https://github.com/hraaaaf/Digital_crown/actions/runs/39764642070). This PR is stacked on #1012, isolated DRAFT; nothing merged.

## What is actually connected to the real application

- `frontend/src/features/panoramic/PanoramicStudio.tsx` adds a gated **“Laboratoire FDI · recherche”** button. The dialog mounts the React component `FDIResearchPanel.tsx`. Existing panoramic patient upload, authorized image viewing, history, reporting and RBAC are **unchanged**.
- The button is **invisible and inactive in production builds** and all normal development sessions unless **both** `import.meta.env.DEV` and `VITE_FDI_RESEARCH_WORKSPACE=enabled` hold. It never bypasses the enclosing patient Panoramique authorization check already enforced by `PatientDetailsInner.tsx`.
- The research panel only receives its own **artificial synthetic radiograph** or a separately selected **research-authorized local image**. **It does not receive the loaded patient's radiograph, patient ID, patient record, or authenticated image URL.** No calls to FastAPI, Firebase, Hugging Face or other network services; no patient DB writes, no localStorage/sessionStorage.
- Proposals can be imported from a local `digital-crown-fdi-review-v1` JSON generated separately by the J10E pinned offline ONNX research bridge. All start unconfirmed. A dentist can drag, change geometry, change FDI labels, add a missed permanent tooth, remove false candidates and explicitly confirm a tooth. Duplicate confirmed FDI codes fail closed. **Any change to label or box revokes confirmation and selected acts.**
- Manual catalogue demonstration: clinician types an act and specialty, adds definition **in memory only**, links it to an explicitly confirmed tooth; no automatic act inference. JSON export excludes unconfirmed proposals and carries `RESEARCH_ONLY_NOT_SAVED_TO_PATIENT`, cannot be imported into patient chart by this feature. Adult permanent 11–48 only; mixed/primary not inferred.

### Local developer research launch

Launch the frontend using its existing developer workflow with this nonproduction flag:

```powershell
$env:VITE_FDI_RESEARCH_WORKSPACE = "enabled"
cd frontend
npm run dev
```

Navigate (while authenticated with existing Panoramique rights) to Patient → Imagerie → Panoramique. Click **Laboratoire FDI · recherche**. Use **Exemple synthétique** to test corrections, or an authorized non-patient research image plus the matching ONNX-generated JSON. **Never use cabinet/patient radiographs with experimental non-clinical tooling.** The flag does not enable or load a model binary in Digital Crown; actual inference remains separately offline in the research bridge.

### CI verification plan

`.github/workflows/lot05-j10f-imagerie-fdi-research.yml`:
1. Ubuntu frontend: `npm ci`, `tsc --noEmit`, focused React/Vitest tests, existing PanoramicStudio nonregression tests, production-mode Vite build with flag disabled, absence of network/clinic persistence or .pt/.onnx weight in repo.
2. **Windows 2025** native CPU research runner: downloads author-released AKUDENTAL images into ephemeral research workspace; verifies source Git SHA; builds ONNX from checksum-pinned public FDI author model and compares ONNX predictions vs `.pt` on 2 already-public films. Keeps only aggregate metrics, no model, patient, image or predictions artifact. CPU Windows parity is a technical gate, **not** installation/service reliability or clinical approval.

## Non-negotiable blockers

**Licensing: the author model is published CC BY-NC-SA 4.0** with an explicit no-clinical-decisions warning ([model card](https://huggingface.co/miquic/app-odonto-fdi-yolov8s)). Approval by Digital Crown owner to select the model does not transfer commercial rights to the weights, nor satisfy clinical-validation obligations. Do not bundle .pt/.onnx in paid Windows installer; do not enable a production inference endpoint; do not claim diagnosis or autonomous FDI accuracy. The real benchmark had **840 / 1,036 correct tooth FDI-and-position pairs (81.1%)**, only **3/40 entire radiographs entirely correct**. Human clinician review is compulsory, and the experimental UI doesn't remove this limitation.

**Remaining product work** is a separately authorized clinically/governed implementation: obtain commercial rights, study patient-appropriate safety/privacy and Windows installer, authenticated image annotations with RBAC, persistence/audit/backup of clinician-confirmed data, act catalogue migrations, clinical acceptance on representative films, independent review and regulatory assessment. J10F is a safe research entrypoint, not full end-to-end patient use.

**NO merge, Vercel, installer, patient data change or clinical activation. V1.5 NO-GO.**
