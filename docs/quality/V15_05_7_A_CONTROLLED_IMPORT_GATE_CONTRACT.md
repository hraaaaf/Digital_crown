# LOT05.7-A — Controlled Import: non-authorizing evidence gate (DRAFT)

**Scope / status:** migration-planning evidence only, on an isolated branch. The prior LOT05 preparatory/synthetic implementation stays intact. **NO-GO** for real clinical import, archive/media/finance import, or deployment. `import_permitted=false` is structural, including when every claim is coherent. No new route, UI, ORM model, migration or cabinet DB access is introduced in 05.7-A.

## Preconditions and authority separation

1. Source must be an authorized offline copy placed by an operator in isolated encrypted staging. Source identity, owner, acquisition method, copy-only attestation, 64-character SHA-256 fingerprint and engine-specific parser support must be independently established. Never accept live connection secrets or a client-supplied filesystem path as authority. The 05.1 inspector only inventories a limited SQL/SQLite subset and is not a full vendor adapter.
2. Principal must be authenticated via runtime session, workstation authority and **cabinet owner** checks; the tenant identity must come from the server context, never from source data or submitted claims. Owner consent to inspect is not permission to import. Identity ambiguity requires a human decision with provenance before any write.
3. Each explicit mapping profile is cryptographically bound to the immutable source file fingerprint, inspected source schema fingerprint, observed full physical target schema and exact Alembic revision. Suggestions, ORM-declared manifests and in-memory drafts are **not** approvals. Practitioner credentials, permissions and authentication flags can never be sourced from legacy records.
4. A separate dry-run must bind the **same source + mapping + target** and enumerate source/target entity counts, orphan relations, duplicate candidate groups, out-of-scope rows, media files, unmapped required fields, ambiguous chronology/timezones, payment reconciliation variances and PHI-safe diagnostic codes. Any unresolved critical issue halts the future import. A clean *synthetic* report does not certify a real dump.
5. Before a future import, **backup and actual restore** of the intended target must be executed and verified by independent digest/row-integrity/tenant checks, including foreign keys and a documented recovery point. LAB-only `sqlite3.backup`/rollback is not evidence for cabinet SQLCipher or PostgreSQL recovery. Define acceptable RPO/RTO with the operator; do not infer them.
6. Future write mechanism (NOT in 05.7-A) must be tenant-scoped and replay-safe on `(tenant_id, source_system, source_instance, entity_type, legacy_id)`, enforce uniqueness server-side, bind children to same-tenant parents, write transactional chunks with checkpoints and fail-closed resume/cancellation **between** chunks. Explicitly distinguish resume from restore/rollback and never promise atomicity across an entire multi-batch migration without a verified compensation strategy.
7. Post-import gate requires independent entity-by-entity reconciliation (including money as source-valued, never invented), foreign-key integrity, media byte integrity and metadata, human-selected sample verification, incident/rollback rehearsal, source preservation, traceable signed owner approval and legally reviewed retention/deletion policy. No auto-activation.

## 05.7-A executable boundary

`backend/services/legacy_import_certification_gate_v15.py` accepts `UntrustedImportEvidence`, an **untrusted aggregate of synthetic metadata and self-reported controls**. It rejects invalid IDs, missing/mismatched source or profile hashes, stale target revisions, unresolved anomalies and absent control claims. It returns only non-PHI blocker codes. A coherent aggregate means **reported metadata is internally consistent**, nothing more; the six always-open blockers explicitly identify missing real-world authority, authenticated runtime binding, provenance, restoration, tenant certification and human signoff. No statement in this module can grant an import permission.

`backend/tests/test_legacy_import_certification_gate_v15.py` checks adversarial invalid inputs and the API surface of the already-integrated synthetic gateway. A targeted CI workflow tests exact PR SHA on Python 3.11 and 3.12. It is a *targeted LOT05.7-A check*, not a global gate expansion or clinical certification.

## Stop conditions / human gate

**BLOCKER** until supported source formats and provenance are validated, authenticated owner and workstation gates operate on the intended tenant, complete physical schema is certified on that tenant, real backup **and actual restore** succeed, full source mapping and financial/media anomalies have been adjudicated, idempotence and crash recovery have been proven on isolated representative copies, and the owner grants a separate, explicit clinical-import decision after reviewing evidence. Import UI remains disabled. Only authorized technicians should handle any clinical backup; do not attach it to GitHub, Notion, CI, browser or chat.

**Deferred**: concrete destination schema/provenance persistence contract, source-specific adapters and safe date/currency interpretation, retention controls, RPO/RTO, signed approval protocol and restoration feasibility. See `techdoubt.md`. LOT10 terrain remains a separate final verification, not a shortcut to a LOT05.7 safety gate.

## Review rubric

- **A — security/integrity:** look for an untrusted flag mistaken for authority, owner/tenant impersonation, path or digest confusion, replay/cross-tenant write, transaction fail-open, hidden PHI in reports, actual source credential exposure.
- **B — evidence/recovery/product:** look for fake-green tests, a missing real restore, fiscal/media/patient gaps, Alembic drift, ambiguous “ready” wording, wrongful conversion of LOT05 synthetic proof into clinical certification, accidental mobile UI or extra lot scope.

**Required for this slice:** unit tests + exact HEAD + diff isolation + two distinct internal adversarial perspectives. **Not available as proof here:** independent external reviewer, on-prem recovery, live source adapter, production authorization, client-visible UX changes, native mobile module or clinical go-live.
