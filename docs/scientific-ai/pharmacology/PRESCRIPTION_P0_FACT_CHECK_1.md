# Prescription P0 Fact Check 1

## Executive verdict

**LLM classification: `LLM_ACTIVE_IN_PRESCRIPTION_FLOW`.**

This is not inferred from the word `agentic`. The active release's document route directly awaits a coherence service that directly posts a clinical prompt to the local Ollama API. A controlled spy test confirmed one `analyze_with_ia` invocation for an ordonnance without network or database access.

Important qualification: the LLM does **not** select medicines, calculate doses, persist prescriptions or generate the PDF. It performs a post-generation semantic warning pass. On this machine Ollama currently responds, but advertises zero installed models; `llama3.2` is absent, so a successful inference is not currently available and the code returns an empty warning list after the HTTP error path.

## Runtime prescription call graph

See `PRESCRIPTION_RUNTIME_CALL_GRAPH.md`.

The decisive chain is:

`useDocumentGenerator.ts:431` -> `documents.generate_document` -> PDF/archive -> `clinical_coherence.analyze_coherence` -> `ai_coherence.analyze_with_ia` -> `httpx POST /api/generate`.

## LLM inventory

| Component | Provider/model | Runtime location | Prescription relevance | Classification |
|---|---|---|---|---|
| `backend/services/ai_coherence.py` | Ollama `llama3.2` | local HTTP | Direct post-generation ordonnance path | Active call path; model unavailable now |
| same service fallback | Gemini 1.5 Flash | cloud SDK | Same path only after local failure | Dormant: flag false, no key, SDK absent from inspected venv |
| `backend/services/bot/llm_parser.py` | OpenAI-compatible endpoint | local or opt-in cloud | Crown Bot only | Outside prescription path |
| `backend/services/card_extractor.py` | Ollama | local HTTP | Card extraction | Outside prescription path |
| `backend/services/ai_gateway.py` | endpoint policy | configuration helper | Not imported by ordonnance coherence path | Outside direct path |

No OpenAI, Anthropic, LangChain or Transformers SDK was found installed in the inspected project venv. Ollama is called through `httpx`, not through an Ollama Python package.

## Dependencies

| Dependency | Declared | Installed in inspected venv | Imported/called | Prescription reachable |
|---|---:|---:|---:|---:|
| `httpx` | Yes (`requirements.txt`, backend pinned requirement) | Yes | Yes | Yes |
| `google-generativeai` | Yes (root requirement) | No | Lazy import | Only if cloud flag/key; currently no |
| OpenAI SDK | No evidence | No | No | No |
| Anthropic SDK | No evidence | No | No | No |
| LangChain/LlamaIndex/Transformers | No evidence | No | No | No |

Dependency presence was not used as proof of runtime activity.

## Environment/config

Only variable names were inspected; no secret values are reproduced.

| Variable | Referenced by | Required? | Effective/runtime use |
|---|---|---|---|
| `OLLAMA_URL` | `backend/config.py`, `ai_coherence.py` | Optional override; default exists | Effective host `localhost`, port `11434`; local call has no enable flag |
| `CLOUD_AI_ENABLED` | `config.py`, `ai_coherence.py`, safety check | Required for cloud fallback | Effective `False` |
| `GEMINI_API_KEY` | `config.py`, `ai_coherence.py` | Required with cloud flag | Not configured in effective settings |
| `LLM_API_BASE`, `LLM_API_KEY`, `LLM_MODEL` | Crown Bot parser | Bot-specific | Not used by ordonnance coherence |

## Agentic service analysis

### `generate_clinical_assessment`

- Caller: `GET /api/prescriptions/agentic/assessment/{patient_id}`.
- Inputs: DB session, patient ID, appointment/act labels, doctor ID.
- Output: deterministic smart plan plus Markdown summary.
- Side effects: database reads through `prescription_service`; no external network in this service.
- LLM: no.

### `design_treatment_plan`

- Caller: `POST /api/prescriptions/agentic/design`.
- Inputs: assessment and patient context.
- Output: deterministic prescription object mapping.
- Side effects: none.
- LLM/network: no.

The service is correctly classified as `AGENTIC_DETERMINISTIC_NO_LLM`, but that does not describe the separate document-coherence path.

## Network calls

| Service | Destination | Purpose | Reachable from prescription? |
|---|---|---|---|
| `ai_coherence` | local `localhost:11434/api/generate` | Semantic clinical warnings | Yes, after document generation |
| `ai_coherence` fallback | Google Gemini | Same warnings | Conditional; disabled now |
| prescription search router | `medicament.ma` | Live product search/suggestions | Yes for search/suggestion endpoints; not an LLM |
| frontend API client | local Digital Crown API | Prescription/document actions | Yes; not external |

No external call containing patient data was made during this audit.

## Feature flags

- No `LLM_ENABLED`, `AI_ENABLED`, `AGENTIC_ENABLED`, `PRESCRIPTION_AI`, `USE_AI` or `ENABLE_AI` gate protects the local ordonnance coherence call.
- `CLOUD_AI_ENABLED` protects only the Gemini fallback.
- Ollama is attempted whenever `analyze_coherence` reaches a patient and the cache does not already contain a response.

## Runtime verification

1. Active runtime evidence: port `8005` process and release activation record share the exact 2026-07-17 15:26:06 start time; the release contains the direct LLM path.
2. Controlled spy: synthetic ordonnance context invoked `analyze_with_ia` exactly once; zero external network and zero real database calls.
3. Local service status: Ollama reachable; zero models; `llama3.2` unavailable.
4. Production endpoint was not called because that would require a real authenticated patient context and could generate/persist a real PDF.
5. Temporary instrumentation was removed after the test.

## P0 fact-check

| P0 | Verdict | Evidence | File/Symbol | Runtime impact | Next action |
|---|---|---|---|---|---|
| LLM involved in pharmacological evaluation | **CONFIRMED, wording narrowed** | Direct route/service/HTTP chain plus spy invocation | `documents.generate_document`; `ClinicalCoherenceService.analyze_coherence`; `AICoherenceService.analyze_with_ia` | Post-generation, non-blocking semantic warnings; no dose generation | Separate LLM warnings from deterministic safety authority; decide whether to remove or make explicitly optional in a future mission |
| Default/estimated weight | **CONFIRMED** | Backend uses 70 kg; frontend derives weight from age | `prescription_service.resolve_smart_prescription`; `clinical_rules.analyze_case`; `estimateWeightFromAge`; `getAgeAwareDosing` | Can affect deterministic pediatric suggestions | Future safety-gates mission |
| Silent substitutions | **CONFIRMED** | Preset mapper changes amoxicillin/Augmentin to RODOGYL and ANTADYS to paracetamol | `PrescriptionAgenticStudio.applyPresetWithSafety` | Medication identity/dose text changes without explicit confirmation step | Future safety-gates mission |
| Duplicated pharmacological rules | **CONFIRMED** | Separate active rules in backend engine, frontend engine, presets and seeds | `ClinicalRulesEngine.MAROC_PHARMACOPEIA`; `MEDICATION_RULES`; presets; `backend/seed.py` | Divergent behavior across layers | Future rule-authority consolidation |
| Validation after PDF | **CONFIRMED WITH SCOPE** | Backend PDF/archive precede backend deterministic+LLM coherence; frontend has separate pre-submit checks | `documents.generate_document:128-154,243`; `useDocumentGenerator.ts:404-420` | Backend warnings cannot block already generated/persisted PDF | Move authoritative deterministic validation before output in future mission |
| Conflicting clindamycin prophylaxis | **CONFIRMED AS CODE/SOURCE CONFLICT** | Active rule text requires clindamycin 600 mg while registered current ADA/AHA candidate says clindamycin is no longer recommended for prophylaxis | `clinical_rules_engine.py:277,365`; source `ada-antibiotic-prophylaxis` | Conflicting guidance is presented as mandatory | Clinician-led rule reconciliation; no code change in this audit |

## Corrections to previous audit

- **Not a false positive:** an LLM call is genuinely reachable from ordonnance document generation.
- **Overbroad wording corrected:** the LLM does not calculate or choose the dose. It is prompted to evaluate age-related dosing and contraindications and returns warnings only.
- **Runtime availability clarified:** Ollama is running but no model is installed, so the active path currently attempts and fails closed to `[]`; successful inference was not observed.
- **Agentic terminology corrected:** `prescription_agentic_service.py` is deterministic and contains no LLM call.
- **Validation wording narrowed:** frontend deterministic checks run before submission, while backend coherence runs after PDF generation/persistence.

## Independent reviewer challenge

```yaml
decision: approve_with_reservations
blocking_findings: []
major_findings:
  - "The active call path is proven, but successful llama3.2 inference is currently impossible because no model is installed."
minor_findings:
  - "Direct process working-directory introspection was unavailable; release attribution relies on matching activation/process timestamps and identical release code."
missing_tests:
  - "A future isolated route integration test should spy on ai_coherence while using a dedicated synthetic DB/env file."
scientific_uncertainties:
  - "No conclusion is made about the clinical validity of any LLM warning."
required_actions:
  - "Preserve the distinction between deterministic agentic suggestions and LLM post-generation warnings."
```

Counterevidence was actively sought: dormant imports, feature flags, absent model, cache bypass, frontend reachability and immutable release contents. None makes the LLM code dead; the missing model limits successful inference, not route reachability.

## Final status

`PRESCRIPTION_RUNTIME_FACT_CHECK_COMPLETE`

