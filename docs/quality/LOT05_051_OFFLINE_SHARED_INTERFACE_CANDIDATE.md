# LOT05.1 — Offline source intake / shared interface contract (candidate)

Status: **PROPOSED / FUE-0 DOCUMENTATION ONLY**. Base: `master@12dc65e8ee517897e76b7d2e37af58236c6b771f` (2026-11-12). Canonical authority: [Notion V1.5 roadmap](https://app.notion.com/p/3e677c66336281d88c82d2fbe43835fb). This file **does not** replace `V15_05_SQL_MIGRATION_CONTRACT.md` or authorize a clinical migration.

## Goal / SUCCESS / PROOF
Goal: define the smallest read-only, versionable handoff between 05.1 source intake, 05.2 mapping and 05.6 media intake without rewriting existing inspectors or widening the authorized runtime. Success: each consumer can distinguish a declared format from verified provenance, raw/private schema metadata from public safe aggregates, and **UNKNOWN** from false claims of zero collisions or approval. Proof target: FUE-0 contract review against exact-HEAD code plus synthetic negative tests on a later implementation PR. No FUE-I/G, CI, or product behavior is claimed by this document.

## Observed capabilities on the base HEAD

| Source | Existing callable/model | Verified scope by source inspection | Not established |
| --- | --- | --- | --- |
| Cold SQLite `.db/.sqlite/.sqlite3` | `legacy_sql_inspector_v15.inspect_staged_copy` | Read-only table/column inspection, explicit offline attestation, SHA, staging containment, reject WAL/sidecars | Real vendor export compatibility; row import |
| `.sql` | Same inspector, declared PostgreSQL/MySQL/MariaDB/SQLite | Bounded `CREATE TABLE` DDL lexing only; SQL never executed | Native database archive, INSERT/COPY decoding, semantic completeness |
| Operator CLI | `legacy_sql_vendor_inventory_v15.inventory_declared_legacy_copy` | Safe aggregate counts; requires source software/version *declarations*; rejects non-DDL SQL | Attestation as independently verified vendor origin |
| Synthetic CSV/TSV | `legacy_migration_csv_envelope_lab_v15.inspect_synthetic_csv_envelope` | Explicit comma/semicolon UTF-8 CSV and tab UTF-8 TSV syntax in FAKE-only lab | Production adapter, official vendor provenance or clinical mapping |
| Mapping | `legacy_sql_mapping_v15.MappingDraft` / `revalidate_mapping_draft` | Source-file/schema + destination-schema SHA bindings, explicit UNMAPPED, tamper detection | Real authenticated admin approval or actual importer authorization |

File-level inspection is **not** execution proof. The old `05.1` and `05.7C-A/2A` implementation labels must not be mistaken for completion of the current 05.1 **product** milestone.

## Proposed shared read-only DTO — version 1 (NOT YET IMPLEMENTED)

```text
OfflineSourceEvidenceV1:
  contract_version: 1
  source_kind: sqlite_cold_copy | sql_text_ddl | synthetic_csv | synthetic_tsv
  declared_dialect: sqlite | postgresql | mysql | mariadb | null
  declared_source_software: operator-only/local-private (never evidence of compatibility)
  declared_source_version: operator-only/local-private
  source_sha256: SHA-256 of unchanged source bytes
  source_size_bytes: positive integer
  schema_sha256: local/private digest where a supported schema was derived, else null
  provenance_status: OPERATOR_ATTESTED_UNVERIFIED | UNKNOWN
  syntax_status: INSPECTED_SCHEMA_ONLY | LAB_SYNTAX_ONLY | REFUSED
  public_summary: sanitized table/column/row aggregate counts only where proven
  private_schema_handle: ephemeral local-only reference, NOT exportable to logs/Notion/CI
  warnings: fixed enumerated codes; no user-controlled fragments
  source_vendor_verified: false
  mapping_human_approved: false
  target_backup_verified: false
  target_collisions: null
  target_rows_written: 0
  import_permitted: false
```

This is an architectural DTO proposal, **not** an endpoint or already supported serialized type. For source intake, row_count should be null/UNKNOWN except where explicitly measured by a restricted synthetic lab, never asserted as zero. A digest alone cannot prove physical source provenance; locally retained evidence may record operator, date, acquisition method, immutable copy procedure and authorized storage, under a separate access-controlled design and privacy review.

## Consumers and no-write interface boundaries

- **05.1 owns**: staged file validation, safe syntax/schema inventory, exact-byte digest, refusal codes. It does not return credentials, patient records or media bytes.
- **05.2 owns**: local/private schema-to-target schema projection; bind mapping draft to source file/schema SHA and target schema SHA/revision; UNMAPPED explicit; human review and RBAC outside this document. Must not treat a source inspection or proposal as approved.
- **05.6 owns**: isolated media manifest design with source copy identity, content SHA-256, candidate patient-association source identifier held *locally*, orphan/conflict state UNKNOWN unless independently checked. No automatic linking to patient/tenant from a filename or an unapproved mapping.
- **05.3–05.5/05.7 consume only after separate gates**: target tenant, immutable mapping decision, transaction/reconciliation and restore evidence; none are unlocked by this DTO.

## Deny-by-default acceptance matrix (future FUE-0/FUE-I)

1. Missing offline attestation, staging escape, symlink/hardlink, unstable bytes => REFUSED, 0 writes.
2. SQLite WAL/SHM sidecars or non-cold snapshot => REFUSED; never silently ignore pending transactions.
3. Non-DDL SQL / native archive / unsupported encoding => REFUSED for the restricted public CLI, not a successful native export adapter.
4. CSV formula-like unsafe cell, duplicate/unsafe header, field-count drift => REFUSED in synthetic envelope.
5. Source digest drift or target schema drift => mapping invalidated; manual re-review required.
6. Unknown vendor, missing media association or target collision not checked => UNKNOWN, never inferred compatible or 0.
7. Unauthenticated reviewer / cross-tenant content / real patient data presented as test => STOP, no API/target write.
8. Public report / logs / GitHub / Notion => no patient values, schema identifiers, source path, original media, credentials or unique identifiers.

## Sequence / gate

1. 05.1 product FUE-I must first verify operator workflow and format availability using *officially generated synthetic* sources; an operator declaration is not vendor proof. Prefer cold SQLite and SQL DDL for metadata inventory **only**, with CSV/TSV as separately scoped synthetic syntax evidence.
2. Freeze this minimal read-only DTO or an evidence-backed alternative before 05.2 and 05.6 write cross-module adapters. Any change affecting patient identities, target storage, RBAC or schema is an explicit HIGH-effort gate.
3. No import, DB migration, merge, deployment, clinical activation or real patient dataset is authorized by this candidate. Product 05.1 remains OPEN pending actual executable FUE-I, negative tests, exact HEAD and owner review.

Canonical handover: this document + `docs/quality/V15_05_SQL_MIGRATION_CONTRACT.md` + Notion V1.5 roadmap; source code remains the authority for implemented behavior.
