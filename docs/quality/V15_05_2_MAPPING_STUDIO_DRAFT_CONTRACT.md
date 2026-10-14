# V1.5-05.2-A — Mapping Studio: explicit draft contract (NO APPROVAL)
Source of authority: locked Notion V1.5-05 decisions **04–07, 10, 15, 32, 44–50, 51–52, 58–60, 63**. Stacked on [05.1 PR #850](https://github.com/hraaaaf/Digital_crown/pull/850), target branch stays isolated until LOT04 integration gate.

## Boundaries
05.2-A is a **metadata-only Mapping Studio engine**, not a rendered UI, server API, authorization mechanism, data loader or migration. This increment introduces **no runtime import hook, persistence, schema change or real patient data**. It does not alter any Station/Pocket/printing components. The target snapshot used by the engine is injected by the caller; **not certified canonical** until a trusted, authenticated target adapter checks SQLAlchemy/Alembic metadata and tenant. A user-supplied snapshot is never sufficient to authorize an import.

## Inputs / outputs
- Source: 05.1 immutable `InspectionReport` including source file SHA-256 and named tables/columns, *not* patient rows. Never execute the original .sql. Reject duplicate/ambiguous metadata identifiers.
- Target: `TargetSnapshot(tables, schema_revision)` with explicit tables/columns; no inferred model names. Fingerprint is calculated over the normalized manifest. Provenance/trust remains external until 05.2-B.
- Proposal: `propose_mapping(source, target) -> MappingProposal`: one visible candidate per uniquely identical table/column name (case-insensitive only when unambiguous); otherwise `None/UNMAPPED`. Suggestions are **never** silently copied to decisions. No fuzzy/semantic/AI matching.
- Human draft: `build_mapping_draft(source, target, decisions, source_software, source_version, profile_version)`. A decision is required for **every** source table and **every** source column including explicit `None` for "do not import". Validate all identifiers exist in both bound snapshots; reject duplicate destinations, credential/secret fields even if manually selected, orphan column bindings, unexpected or omitted table/column decisions. Decision record contains only metadata and source/target digests.
- Revalidation: `revalidate_mapping_draft(draft, source, target)` checks exact source dump SHA and schema hashes and returns **review required regardless of outcome**. Saved mapping profiles will become reusable templates only, never automatic approval.

## Non-negotiable flags
No method in this module authenticates users or grants a real approval. Returned records always expose `admin_approved=false`, `dry_run_completed=false`, `import_permitted=false`, even when *all* decisions are recorded. Real approval needs the future backend actor from session, tenant guard and a record tied to exact source/target hashes, and separately a passing 05.3 dry-run, before any writing.

## Deliberately deferred
05.2-B: UI staff desktop, mobile availability check and paired BEFORE/AFTER viewports as applicable, saved/versioned profiles with authenticated admin validation, technician privacy mode, source-software detection, encrypted local retention. 05.3: data-level dry-run, anomalies, duplicates, mapping transformations and privacy-minimized CSV/JSON. 05.4–05.7: any real import, backup/restore, idempotence, rollback and sample verification. No current human UI validation is claimed.

## Tests & two review perspectives
Fixtures remain synthetic; both tests and CI must assert zero import permission, no secrets, no fuzzy guesses, explicit unmapped decisions, rebinding reject, duplicate collision reject, fresh dump reject. A security review targets privilege spoofing / credential mapping / cross-tenant confusion. A fidelity/UX review targets silent mapping, hidden unknowns, wrong schemas, false proof, gaps against Notion and mobile. An isolated successful unit matrix is not a certification of the complete wizard.
