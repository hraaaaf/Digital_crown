# Prescription Runtime Call Graph

Audit date: 2026-07-18
Scope: repository and active local release; no clinical behavior changed.

## Runtime identity

- Port `8005` listener: PID `16432`, started 2026-07-17 15:26:06.
- Matching activation record: `C:/Users/lenovo/DigitalCrown-Runtime/releases/20260717-152519-bde81f51befd/runtime-activation.json`, activated at the same second with `reload=false` and backend path inside that immutable release.
- The release contains the same prescription/coherence call path documented below.
- `active-release.txt` is absent. Process start time plus the activation record provide high-confidence release attribution; no patient request was sent to prove it.

## Main prescription document path

```text
PrescriptionAgenticStudio / DocumentStudio
  -> useDocumentGenerator.buildPayload()
  -> useDocumentGenerator.runGeneration()
  -> POST /api/documents/generate
  -> documents.generate_document()
  -> asyncio.to_thread(_generate_pdf_in_thread)
  -> DocumentFactory.create_ordonnance()
  -> OrdonnanceGenerator.generate()
  -> optional archive_document(... clinical_data=req.data)
  -> ClinicalCoherenceService.analyze_coherence()
      -> deterministic _check_ordonnance_coherence()
      -> AICoherenceService.analyze_with_ia()
          -> mask_patient_context()
          -> cache lookup
          -> HTTP POST http://localhost:11434/api/generate (model llama3.2)
          -> optional Gemini fallback only when CLOUD_AI_ENABLED and key are set
  -> response {pdf_url, warnings, ...}
  -> frontend displays returned warnings after PDF exists
```

| Step | File / symbol | Calls next | LLM? | Evidence |
|---|---|---|---|---|
| UI payload | `frontend/src/features/admin/DocumentStudio/useDocumentGenerator.ts:271` `buildPayload` | local API | No | Medication name, dose, form and instructions are serialized at lines 287-299 |
| UI generation | same file, line 431 | `POST /documents/generate` | No | Direct runtime API call |
| API route | `backend/routers/documents.py:71` `generate_document` | PDF factory | No | Registered under `/api/documents` in `backend/main.py:433` |
| PDF | `backend/routers/documents.py:79-128` | `DocumentFactory.create_ordonnance` | No | PDF is generated at line 128 |
| Persistence | `backend/routers/documents.py:131-154` | `archive_document` when applicable | No | Prescription data may be archived before coherence |
| Coherence | `backend/routers/documents.py:243` | `coherence_service.analyze_coherence` | Yes downstream | Unconditional after generation for supported document requests |
| Deterministic checks | `backend/services/clinical_coherence.py:23-27` | local checks | No | Ordonnance branch calls `_check_ordonnance_coherence` |
| Semantic checks | same file, lines 29-55 | `ai_coherence.analyze_with_ia` | Yes | Direct awaited call at line 49 |
| Local LLM | `backend/services/ai_coherence.py:65-86` | Ollama HTTP API | Yes | `httpx.AsyncClient.post` to `/api/generate`, model `llama3.2` |
| Cloud fallback | same file, lines 88-132 | Gemini SDK | Conditional | Requires both `CLOUD_AI_ENABLED=True` and a key; current effective config is false/no key |
| UI result | `useDocumentGenerator.ts:448-454` | warning state | LLM-derived warnings possible | Returned warnings are displayed after the PDF response |

## Agentic suggestion path

```text
PrescriptionAgenticStudio useEffect
  -> GET /api/prescriptions/agentic/assessment/{patient_id}
  -> prescription_agentic.generate_clinical_assessment()
  -> prescription_service.resolve_smart_prescription()
  -> clinical_rules.analyze_case() + database habits

User requests plan
  -> POST /api/prescriptions/agentic/design
  -> prescription_agentic.design_treatment_plan()
  -> deterministic mapping of suggested drugs
```

`backend/services/prescription_agentic_service.py` imports no LLM SDK/service and performs no network call. Its two public methods use SQLAlchemy, `prescription_service`, `clinical_rules` and deterministic formatting. The name `agentic` is a product/architecture label, not an LLM implementation.

## Data sent to the coherence LLM

The local Ollama prompt receives:

- masked age bracket, gender and medical antecedents from `pii_masker.mask_patient_context`;
- complete document type and `doc_data`, including prescription medication fields;
- recent act labels;
- doctor habit summary.

Names and contact fields are excluded by the masker, but antecedents, medication data and recent acts remain sensitive clinical data. Current cloud fallback is disabled. If enabled in the future, the same constructed prompt is passed to Gemini.

## Ordering consequence

The LLM does not generate the medicine list or calculate a dose in this path. Its prompt asks it to evaluate contraindications, omissions and age-related dose coherence, and its JSON output can add UI warnings. These warnings are non-blocking because PDF generation and optional persistence happen first.

