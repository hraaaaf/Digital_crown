# LOT05.5 Staff migration gateway

A Draft milestone linking Mapping Studio with authenticated owner-only read-only schema readiness and a bounded 100/200 synthetic in-memory rehearsal.

GET /api/migration/preflight reads only schema metadata and Alembic revision. POST /api/migration/synthetic-rehearsal accepts empty JSON only and returns a summary of fictitious rows, always rolled back. Both endpoints are protected by the canonical JWT/Workstation gate and root owner check. Source reports stay in the browser. There is no real import route or clinical upload.

This is a subset of four declared SQLAlchemy models; it does not verify the entire schema, an Alembic migration, SQLCipher, PostgreSQL, patient documents, a real backup, or staff approval. Pocket mobile does not currently provide this feature. Human BEFORE/AFTER review is needed prior to any merge. LOT05 remains NO-GO for real imports.