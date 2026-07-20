---
name: scientific-database-migration
description: Design and implement additive scientific-schema migrations with separate backfill and activation, dry-run evidence, rollback, and no production execution.
allowed-tools: Read, Grep, Glob, Edit, Write, Bash
disable-model-invocation: true
---
# Scientific database migration

## Trigger
User-invoked only when an approved scientific contract requires persistence changes.

## Hard gate
Stop without approved schema, data owner, source/version fields, rollback plan, isolated test database, and explicit authorization. Never run against production or the active cabinet database.

## Workflow
Inspect ORM/migration conventions; create additive schema; keep backfill separate and idempotent; keep activation separate; add dry-run, before/after counts, rollback, tenant isolation, and compatibility tests. Use `DIGITALCROWN_ENV_FILE` for isolated DB tests.

## Forbidden
No destructive migration, no production execution, no automatic activation, no patient-value inspection, and no hidden default clinical values.

## Output contract
Return migration/backfill/activation plan, commands not run, isolated tests, counts, rollback, and review requirements.
