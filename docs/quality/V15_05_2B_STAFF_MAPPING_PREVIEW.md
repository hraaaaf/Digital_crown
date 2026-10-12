# V1.5-05.2-B/1 — Staff Mapping Studio, inert preview only

**Canonical decisions:** V1.5-05 Notion 01–65, especially 04–10, 15, 32, 47–52, 58–60. **Stack:** #850 → #853 → new 05.2-B/1 Draft; LOT04 integration and human merge gates stay closed.

## Architectural inspection
- Desktop staff routes live in `frontend/src/App.tsx` under `ProtectedRoute`, `WorkstationModeGate`, `ProtectedRoutes`, and `PermissionRoute`. Existing `hasAccess(user,'admin')` is *frontend navigation only*, **not a backend approval**. Added `/migration-sql` solely under this pre-existing UI permission; added corresponding Sidebar link only for admin role.
- `/mobile/*` is a separate paired PWA. The Mapping Studio is **not** added to patient companion, station, or paired PWA/mobile menus. The staff web layout is responsive on narrow screens, but does not imply mobile-client capability or approval. New UI tested at 390x844, 768x1024, 1280x900 in isolated browser proof.
- `MappingStudio` props can accept sanitized 05.1-shaped source metadata and a target manifest, but **neither is fetched by this UI**. Standalone route displays **synthetic-only examples**; the target schema revision is deliberately marked DEMO. The adapter to real SQLAlchemy/Alembic and authenticated backend/tenant approval is **not implemented**.
- Every table and column requires an explicit decision, including `UNMAPPED`. Strict exact-casefold-name hints never fill the select fields. Table destination changes reset all column decisions; collisions are blocking; credential-named columns can only be skipped. All drafts are memory-only within component state and reset on refresh.
- UI contains no API/network/database/storage calls and has no import action. Summary renders a **disabled** "Importer" affordance, never an operational import button. Frontend guards never authorize imports.
- A separate *dev-only* Vite HTML entrypoint `frontend/mapping-studio-proof.html` can render the exact component with no staff backend, only synthetic data. That page is **not** an input in the production Vite build. Its CSP denies network connections and form posts.

## Gates
- CI exact PR SHA, 10 interactive Vitest/jest-dom tests, TypeScript typecheck, 05.2-A 25 tests and 05.1 28 tests regression; viewport screenshots with Playwright if CI browser install works. Be strict: green workflow does not certify actual patient data, production settings nor actual mobile PWA.
- **BEFORE:** at parent #853 the feature and /migration-sql route do not exist; compare base diff, no existing page to screenshot at equivalent route. **TARGET:** non-authorizing stepper, responsive staff cards, clear demo/no-go banner, all fields reviewed. **AFTER:** screenshot and check overflow at 390x844, 768x1024, 1280x900; attach artifacts to CI. If CI browser proof unavailable, leave visual gate OPEN.
- No UI user-account authority, data-level dry-run, secure saved profiles, authenticated schema-source endpoint, backup, rollback, reconciliation, or operational import. These belong to 05.2-B/2 and 05.3–05.7, and require separate security review.

## No-go
Do not merge, deploy, or migrate any real data. Do not claim actual source availability, target model compatibility, human admin validation, backend auth, secure profile retention, or overall LOT05 convergence.
