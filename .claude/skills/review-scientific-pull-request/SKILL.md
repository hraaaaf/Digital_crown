---
name: review-scientific-pull-request
description: Independent read-only review of a scientific pull request or diff for evidence, units, population, provenance, deterministic logic, tests, privacy, licensing, and activation safety.
context: fork
allowed-tools: Read, Grep, Glob, Bash, WebSearch, WebFetch
---
# Review scientific pull request

## Trigger
Use after implementation and independent tests. Reviewer must differ from authoring agent.

## Blocking rules
Block formula only in prompt; unsourced constant; missing unit; norm without population; cephalo metric without independent test; automatic confirmed diagnosis; LLM dosage/measurement; silent missing-data fallback; patient data/media in tests; dataset without verified license; rule logic change without version bump; source not human-approved; conflicting evidence; or no named reviewer.

## Workflow
Read handoff and diff; independently open cited sources; map claims to code and tests; inspect duplicate/hidden logic; verify versions, units, populations, missing data, migrations, privacy, and generated outputs; issue decision without editing.

## Output contract
Return `decision: approve | approve_with_reservations | request_changes | blocked` plus blocking, major, minor, missing tests, scientific uncertainties, and required actions.
