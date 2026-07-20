# Agent review

## Verdict

The original seven agents were descriptive prompts, not enforceable operating contracts. V2 adds supported Claude Code frontmatter, minimal tools, high effort, skill preload, explicit gates, and independent handoff. No agent may approve clinical truth.

| Agent | Verdict | Major issue found | V2 correction |
|---|---|---|---|
| scientific-architect | VALID_AFTER_CHANGE | Invoked too broadly | Read-only; cross-domain/shared-contract/migration design only |
| pharmacology-engineer | VALID_AFTER_CHANGE | Missing product and population gates | Explicit identity/product/dose separation |
| clinical-diagnosis-engineer | VALID_AFTER_CHANGE | Clinical states incomplete | Typed symptom through confirmed-diagnosis chain |
| cephalometry-engineer | VALID_AFTER_CHANGE | No calibration, dependency or profile contract | Deterministic pipeline and separate formula/profile gates |
| radiology-engineer | VALID_AFTER_CHANGE | No evaluability/non-detection semantics | Typed review lifecycle; non-detection is not absence |
| scientific-test-engineer | VALID_AFTER_CHANGE | Could invent its own oracle | Independent-oracle gate and synthetic-only policy |
| scientific-reviewer | VALID_AFTER_CHANGE | Read-only existed only in prose | Plan permission, read tools, independent-author rule |

## Ownership and overlap

The architect owns contracts, not implementation. One domain engineer owns one rule. The test engineer owns independent evidence, not medical truth. The reviewer owns the decision record, not edits or human approval. Source research registers candidates only.

Two agents must not edit one rule concurrently. Subagents cannot spawn subagents, so the main Claude Code session sequences domain engineer, test engineer, then reviewer.

## Tool and model review

model: inherit avoids stale model IDs. effort: high applies to scientific agents. Architecture and review use plan mode and read-only tools. No bypass mode exists.

Cosmetic requests containing clinical words are excluded. Missing evidence, contradictions, unknown units/population/formula, and license uncertainty terminate implementation.

