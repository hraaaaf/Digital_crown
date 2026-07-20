# Scientific Agent System Deep Review 1

Review date: 2026-07-18

Scope: Claude Code scientific-development infrastructure only. No clinical feature, database schema, migration, clinical constant, production data, or patient media was changed.

## A. Overall verdict

The initial structure was not safe to use: agents were descriptive rather than enforceable, skills lacked frontmatter, evals were cloned, implementation gates were incomplete, and schemas left critical scientific state as free text. V2 corrects those infrastructure defects.

The system is now locked for V1 use as a guarded development workflow. This lock does not validate existing Digital Crown clinical behavior and does not authorize activation of any scientific rule. Every affected domain retains P1 work that must be completed before implementation or activation.

| Area | Score |
|---|---:|
| Architecture | 8.5/10 |
| Agent design | 9.0/10 |
| Skills design | 9.0/10 |
| Scientific source strategy | 8.0/10 |
| Testing strategy | 8.5/10 |
| Safety | 9.5/10 |
| Readiness for real feature work | 7.0/10 |

## B. Agents

| Agent | Verdict | Major issue | Changes made |
|---|---|---|---|
| scientific-architect | VALID_AFTER_CHANGE | Over-invocation and implementation overlap | Read-only plan mode; limited to cross-domain contracts, shared architecture and migrations |
| pharmacology-engineer | VALID_AFTER_CHANGE | Product identity, population and dose gates incomplete | Separated DCI, product, form, strength, concentration, dose and jurisdiction contracts |
| clinical-diagnosis-engineer | VALID_AFTER_CHANGE | Clinical state transitions underspecified | Added typed observation-to-diagnosis lifecycle and clinician-confirmation boundary |
| cephalometry-engineer | VALID_AFTER_CHANGE | Formula, norm, calibration and dependency concerns conflated | Added deterministic pipeline and separate formula, profile and transitive-recalculation gates |
| radiology-engineer | VALID_AFTER_CHANGE | Evaluability and non-detection semantics absent | Added observation lifecycle, image quality, localization and review-state requirements |
| scientific-test-engineer | VALID_AFTER_CHANGE | Could create its own scientific oracle | Requires independent, traceable oracle and synthetic or approved fixtures |
| scientific-reviewer | VALID_AFTER_CHANGE | Read-only independence existed only in prose | Plan mode, read-only tools, structured decision and independent-author rule |

## C. Skills

| Skill | Verdict | Routing quality | Changes made |
|---|---|---:|---|
| scientific-source-research | VALID_AFTER_CHANGE | High | Official-first search, conflict, license and candidate-only registration |
| implement-scientific-rule | VALID_AFTER_CHANGE | High | Blocks without human-approved source, units, population and deterministic contract |
| audit-prescription-flow | VALID_AFTER_CHANGE | High | Enforced read-only end-to-end audit |
| audit-clinical-diagnosis-flow | VALID_AFTER_CHANGE | High | Enforced read-only state and coherence audit |
| implement-cephalo-measurement | VALID_AFTER_CHANGE | High | Formula and norm-profile gates separated |
| validate-cephalo-pipeline | VALID_AFTER_CHANGE | High | Added geometry, dependency, precision and report invariants |
| implement-radiology-finding | VALID_AFTER_CHANGE | High | Added modality, localization, evaluability and diagnosis separation |
| audit-panoramic-report-pipeline | VALID_AFTER_CHANGE | High | Added auth, privacy, metadata, quality and provenance checks |
| generate-scientific-golden-tests | VALID_AFTER_CHANGE | High | Prohibits self-generated expected results and patient data |
| scientific-database-migration | VALID_AFTER_CHANGE | High | User-only, additive, dry-run and non-production contract |
| review-scientific-pull-request | VALID_AFTER_CHANGE | High | Independent read-only blocking review |

## D. Scientific domains

| Domain | Ready? | Blocking gaps | Next mission |
|---|---|---|---|
| Pharmacology | Infrastructure only | Moroccan product authority/data rights, current dose provenance, medication-file provenance | PHARMACOLOGY-SOURCE-AND-RULE-AUDIT-1 |
| Clinical diagnosis | Infrastructure only | Current state transitions, clinician confirmation, terminology versions and reuse rights | CLINICAL-DIAGNOSIS-STATE-MACHINE-AUDIT-1 |
| Cephalometry | Infrastructure only | Formula-by-formula contracts, Moroccan profile applicability, transitive dependency proof | CEPHALOMETRY-MEASUREMENT-CONTRACTS-1 |
| Radiology | Infrastructure only | Model provenance, licensed taxonomy, evaluability and review-state audit | PANORAMIC-PROVENANCE-AND-TAXONOMY-AUDIT-1 |

## E. Sources

The registry contains 23 traceable records: 17 `candidate`, 2 `needs_review`, and 4 `license_uncertain`. No record is `approved-by-clinician`.

| Classification | Result |
|---|---|
| Accepted | 17 candidate records accepted for future review, not clinical activation |
| Rejected | No retained record is used as a sole basis after rejection |
| Superseded | No source marked superseded; version conflicts remain explicit |
| Conflicting | AAE diagnostic terminology transition and jurisdiction/population differences require resolution |
| License uncertain | ISO, SNOMED and dataset/reuse-dependent material remains gated |

## F. Top blockers

1. Obtain an authoritative, reusable Moroccan medication authorization/product source or written AMMPS data agreement.
2. Trace every existing dose constant to versioned, population-appropriate evidence and human review.
3. Establish provenance, update semantics and reuse rights for `backend/data/medications_ma.json`.
4. Define exact landmark, directed formula, unit and sign contracts for every current cephalometric metric.
5. Clinically review Moroccan cephalometric study applicability before defining any norm profile.
6. Prove transitive recalculation from landmark edits through measurements, interpretation and PDF.
7. Reconstruct provenance, license, classes and preprocessing for the panoramic model artifacts.
8. Define a clinician-reviewed panoramic observation taxonomy separate from diagnosis.
9. Prove that findings and LLM output cannot silently become confirmed diagnoses.
10. Select exact terminology versions and licenses for endodontic, periodontal, trauma, tooth-numbering and SNOMED mappings.

## G. Corrections performed

- Added supported frontmatter, least-privilege tools, high effort, skill preload and explicit handoffs to seven agents.
- Rewrote eleven distinct skills with hard blockers, output contracts and read-only audit boundaries.
- Replaced cloned evals with positive, negative, ambiguous, collision and dangerous-under-specification cases.
- Upgraded seven schemas to structured V2 contracts with IDs, versions, provenance, units, population, approvals, limitations and test references.
- Rebuilt the source registry as candidate-only with access dates, jurisdiction, population, license and limitations.
- Added six domain/agent review reports and an actionable P0-P3 backlog.
- Added scoped scientific rules, a deterministic handoff protocol and concise routing documentation.
- Strengthened the validator and added five targeted tests for both success and refusal paths.

## H. Tests

| Command | Result |
|---|---|
| `python scripts/validate_scientific_ai_assets.py` | PASS: `SCIENTIFIC_AGENT_SYSTEM_LOCKED_V1` |
| `python -m pytest tests/scientific_ai/test_validate_scientific_ai_assets.py -q --basetemp <isolated-path>` | PASS: 5 passed |
| Asset counts | PASS: 7 scientific agents, 11 skills, 11 evals, 7 schemas, 6 reviews |
| `git diff --check` | PASS |

The default Windows pytest temporary directory was inaccessible in the sandbox. The same isolated tests passed outside that sandbox restriction; they did not load application database fixtures.

## I. Git

- Branch: `master`
- Initial unrelated state preserved: modified `STATE.md`; untracked `.codex/` and `AGENTS.md`.
- Scientific infrastructure remains uncommitted and unpushed as required.
- No backend/frontend clinical behavior, database schema, migration, clinical constant, patient data or patient media was changed.

Because the scientific assets are untracked, `git diff --stat` does not enumerate them until staging. `git status --short` remains the authoritative inventory; no staging was performed.

## J. Final status

SCIENTIFIC_AGENT_SYSTEM_LOCKED_V1

This status locks the agent infrastructure only. It is not scientific, clinical or regulatory validation of Digital Crown.
