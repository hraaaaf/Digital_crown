# TECHDOUBT — Digital Crown

## GLOBAL-G10-S / LOT10 — 2026-10-18 — Two-agent isolation requirement withdrawn

**Status: RESOLVED AS A FALSE DEPENDENCY (doctrine correction, not proof of a completed FUE).**

**Previous concern:** The merged PR #960 required two AI BLIND USER agents running in independent contexts, with separate browsers and withheld reports. That had been documented as a blocking precondition even for ordinary internal adversarial review. The product owner clarified that the **same ChatGPT conversation should perform both specialized perspectives A/B itself** rather than waiting for humans or two separate AI agents.

**Resolution rule:** `AGENTS.md`, `.claude/rules/execution-scoring-verification.md` and `docs/quality/REALITY_PROOF_GATE.md` now instruct the assistant to write two distinct, task-specific *internal adversarial* reviews, correct/test, rerun on new HEAD and confirm. This is not evidence of two genuinely independent reviewers; it is sufficient for the **internal A/B double-review procedure**. Self-review is capped at 9.4/10 and normal VERIFIED starts at 9.0/10 when required proofs/gates pass. No external reviewer or two-agent orchestration is a prerequisite.

**Distinct unclosed verification work — GLOBAL-G10-S:** Inventory V1+V1.5 routes/features, execute actual frontend/backend FUE journeys on fictitious tenants starting at login (or a public entry where applicable), preserve BEFORE/ACTION/AFTER, negative RBAC/tenant checks, exact-HEAD evidence and CI statuses. **These tests have NOT been executed by this documentation correction.** An imagined browser session or two written perspectives are not executable test proof.

**Unchanged gates:** Specifically required human clinical/regulatory/visual approvals and LOT10 hardware/person-on-device observations remain separate from conversation-based A/B review. No deployment, merge or clinical activation is authorized by this documentation.

**Historical origin:** PR #960, master merge `3cbd1d83cdbcbf97e71019a3182f4699d9645421`. This file supersedes the inaccurate "two-agent independence not yet demonstrated" as an *internal review blocker*.


### DEMO-REFERENCE-CABINET — 2026-10-18 — PR #968 DRAFT (chantier distinct)
- Jeu fictif 12 patients, 36 RDV, 36 PDF : code seed manuel livré, **pas de DB persistante créée**, pas de test réel UI ou archive/media mapping ; ne pas déclarer DEMO opérationnelle.
- **BLOCKER avant réutilisation inter-lots :** exécution end-to-end sur DB neuve et réellement migrée, SQLCipher sécurisé, aucun tenant préexistant ; tester lecture réelle des 36 PDF via API et agenda aux viewports mobile/desktop lorsque fonctionnalité mobile confirmée.
- Le seed doit être validé par test d'intégration SQL et transaction/media, idempotence, collisions de créneaux, fuseau Africa/Casablanca, authentification, absence d'envoi SMS/email. CI smoke [#39163397642](https://github.com/hraaaaf/Digital_crown/actions/runs/39163397642) lancée, résultat non connu à la rédaction.
- Sécurité : pas d'identifiants statiques ni de données patients réelles ; isoler base et média ; refus si doute. Revue adversariale interne A/B sur HEAD final encore nécessaire.
- Ce chantier ne modifie ni la PR clinique #955 ni sa roadmap 41/99 ; aucun merge/deploy sans autorisation.

- **CI integration failure on HEAD `4e7cd634`**: [run #39163567310](https://github.com/hraaaaf/Digital_crown/actions/runs/39163567310), missing `email-validator` while importing Pydantic models; fail-closed guard/PDF job SUCCESS, SQLCipher seed job FAILURE before DB creation. Dependency added in commit `613248735dcadd1239cf115f4fdfe8274c0a7f6d`; **new run not yet verified**. Until a full seed + 12/36/36 + SHA-256 test succeeds on final HEAD, fixture is NOT certified. The workflow currently uses `Base.metadata.create_all` on a disposable DB, **not Alembic migration**, so a green run would not certify migrated production schema. UI login, agenda, PDF via HTTP, desktop/mobile and A/B adversarial reviews remain unverified.
