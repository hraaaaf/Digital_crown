---
paths:
  - "backend/**/*{prescription,medication,clinical,diagnos,odontogram,cephalo,panoramic,radiolog,vision}*"
  - "frontend/src/**/*{Prescription,Clinical,Diagnostic,Odontogram,Cephalo,Panoramic,Radiolog}*"
  - "docs/scientific-ai/**"
  - ".claude/agents/*scientific*"
  - ".claude/agents/*-engineer.md"
  - ".claude/skills/**"
---
# Scientific engineering

- Route by task semantics, not clinical keywords in labels or CSS.
- Use the domain agent for established local contracts; add scientific-architect only for cross-domain/shared-contract/migration design.
- Check source registry records and original sources before editing scientific logic.
- No unsourced constants, medical logic in prompts, LLM dosage, or LLM cephalometric measurement.
- Preserve units, population, applicability, versions, provenance, explicit missing-data/contradiction behavior, and clinician confirmation.
- Formula sources and normative-profile sources are separate artifacts.
- `not_detected` never means pathology absent; observation, finding, differential, and diagnosis remain distinct.
- A rule cannot activate unless every supporting claim has traceable human clinical approval.
- Add independent tests and invoke a different scientific-reviewer before merge. Tests passing is not scientific validation.
- Never use production patient data/media, download datasets, run production migrations, or bypass permissions.
