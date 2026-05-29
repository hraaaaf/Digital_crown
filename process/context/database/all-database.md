# Database Context

This file is the canonical Database context entrypoint for DigitalCrown.

Use it after `process/context/all-context.md` when the task needs schema changes, migrations, or database client setup.

---

## Scope

This group covers:

- SQLite database structure (`digital_crown.db` and `clinical_vault.db`)
- SQLAlchemy schemas, model definitions, and relationships in `backend/models.py`
- Alembic database migration procedures and configurations (`alembic.ini`, `alembic/`)
- Database seeding procedures for development and clinical defaults

It does not cover:

- Supabase remote synchronization mechanics (that belongs in `auth/` context)
- Local storage or browser cache configurations (that belongs in `uxui/` context)

## Read When

Read this entrypoint when:

- adding or modifying tables, columns, or relationships in the database
- creating or running database migrations (Alembic)
- troubleshooting database queries, locking issues, or schema mismatches
- working with seeding scripts (`seed.py`, `seed_clinical.py`, `seed_templates.py`)

## Quick Routing

- use `backend/models.py` to inspect SQLAlchemy class mappings and indexes
- use `alembic.ini` and `alembic/env.py` for migration scripts configuration
- use `backend/database.py` for connection engine setup and session creation

## Source Paths

- `process/context/database/all-database.md`

## Update Triggers

Update this group when:

- the database models in `backend/models.py` change significantly
- database engine or driver setup in `backend/database.py` is updated
- Alembic config files or directories are restructured
