# TECHDOUBT — Digital Crown

## LOT05.7-A — 2026-10-18 — Réserves import clinique et preuves insuffisantes

**STATUS: OPEN / NO-GO**. L'évaluateur `legacy_import_certification_gate_v15.py` ne vérifie QUE la cohérence de métadonnées déclarées (digest, revision, compteurs, attestations auto-déclarées). Un opérateur malveillant peut inventer toutes les affirmations ; aucune authentification runtime, signature, staging source réel, attestation physique tenant, sauvegarde/restauration indépendante, rapport de dry-run réel, décision humaine ou autorisation de migration n'est établie par ce module. `claims_coherent=true` n'a AUCUNE valeur d'autorisation. La sérialisation du rapport et ses propriétés d'autorisation demeurent systématiquement False.

**Risque BLOCKER** : ne pas connecter cette fonction à une route d'activation. La future migration nécessite des preuves issues d'acteurs et processus séparés, l'impossibilité de confondre source et cible, certification d'une restauration sur copie isolée, journal de provenance lié au cabinet authentifié, double protection contre import cross-tenant, contraintes d'unicité et replay sur DB, plan de rollback/compensation, correspondances patient/praticien/RDV/actes/finances/médias, gestion juridique de confidentialité, approbation humaine distincte. Le schéma cible y est temporairement épinglé `neo000000031`; toute évolution Alembic doit bloquer et imposer une revue explicite. Les tests statiques de routes ne suffisent pas à prouver l'absence d'une route d'import via un autre routeur.

**Validation** : 05.7-A exécute uniquement tests pure-Python/AST sur contenu de dépôt, sans source ou DB clinique ; CI exacte branche PR à vérifier. Réserve maintenue jusqu'à preuves matérielles des gates 05.7-B/C et accord explicite.


## GLOBAL-G10-S / LOT10 — 2026-10-18 — Two-agent isolation requirement withdrawn

**Status: RESOLVED AS A FALSE DEPENDENCY (doctrine correction, not proof of a completed FUE).**

**Previous concern:** The merged PR #960 required two AI BLIND USER agents running in independent contexts, with separate browsers and withheld reports. That had been documented as a blocking precondition even for ordinary internal adversarial review. The product owner clarified that the **same ChatGPT conversation should perform both specialized perspectives A/B itself** rather than waiting for humans or two separate AI agents.

**Resolution rule:** `AGENTS.md`, `.claude/rules/execution-scoring-verification.md` and `docs/quality/REALITY_PROOF_GATE.md` now instruct the assistant to write two distinct, task-specific *internal adversarial* reviews, correct/test, rerun on new HEAD and confirm. This is not evidence of two genuinely independent reviewers; it is sufficient for the **internal A/B double-review procedure**. Self-review is capped at 9.4/10 and normal VERIFIED starts at 9.0/10 when required proofs/gates pass. No external reviewer or two-agent orchestration is a prerequisite.

**Distinct unclosed verification work — GLOBAL-G10-S:** Inventory V1+V1.5 routes/features, execute actual frontend/backend FUE journeys on fictitious tenants starting at login (or a public entry where applicable), preserve BEFORE/ACTION/AFTER, negative RBAC/tenant checks, exact-HEAD evidence and CI statuses. **These tests have NOT been executed by this documentation correction.** An imagined browser session or two written perspectives are not executable test proof.

**Unchanged gates:** Specifically required human clinical/regulatory/visual approvals and LOT10 hardware/person-on-device observations remain separate from conversation-based A/B review. No deployment, merge or clinical activation is authorized by this documentation.

**Historical origin:** PR #960, master merge `3cbd1d83cdbcbf97e71019a3182f4699d9645421`. This file supersedes the inaccurate "two-agent independence not yet demonstrated" as an *internal review blocker*.
