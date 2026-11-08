# V1.5-08.1 — Queue Core domain contract

Status: implementation candidate; review and exact-HEAD verification pending.
Canonical gates: G1–G5 validated in Notion; this document records the 08.1 subset.
Base: `389d5ebcc64f2c409429dc3e2ed9c8625bb23829`.

## Scope and isolation

`queue_core` is a standalone Python package. Its domain and SQLAlchemy metadata do not import or reference the Digital Crown clinical database, its models, tables, migrations, or mobile waiting-room facade. The persistence contract declares a separate Queue schema; 08.1 does not open a database connection, create a durable database, run migrations, select an engine, or define encryption/runtime installation. The in-memory SQLite test is disposable and synthetic.

No API, authentication/RBAC implementation, QR issuance/consumption, webhook, UI, Windows installer, integration, or production deployment is delivered here. Those remain in later 08.x work. G3 retention values are recorded below as policy metadata only; no personal data is stored by these tests.

## Visit states and transitions

States: `PLANNED`, informational `EN_ROUTE`, `WAITING`, `CALLED`, `CHAIR`, `DONE`, `CANCELLED`, `NO_SHOW`. `ARRIVED` is an immutable event fact, not a visit status. A successful check-in produces `ARRIVED` and `WAITING_ENTERED` in one transaction plan, with one timestamp, actor and method. `EN_ROUTE` never proves physical presence.

| Command | From → to | Required audit / invariant |
|---|---|---|
| Check in | PLANNED or EN_ROUTE → WAITING | Authorized actor, UTC timestamp, method, new sequence; ARRIVED + WAITING_ENTERED committed atomically |
| Re-entry | NO_SHOW → WAITING | Human staff confirmation with explicit reason; new ARRIVED and sequence; never reuse prior position or accept kiosk re-entry automatically |
| Call | WAITING → CALLED | Human action on an eligible visit selected against the COMPLETE authoritative queue snapshot under server lock; mismatch requires queue.override AND reason, recorded before CALLED; no automatic call/re-call |
| Recall | CALLED → CALLED | `RECALLED` event only; no hidden state transition |
| Unlocated after call | CALLED → CALLED | `UNLOCATED_AFTER_CALL` exception event with reason; never `NO_SHOW` |
| Seat | CALLED → CHAIR | Resource compatibility and availability; resource claim and state change commit atomically |
| Complete | CHAIR → DONE | Resource release and DONE commit atomically |
| Return to queue | CALLED → WAITING | Explicit reason and new sequence |
| Exceptional return | CHAIR → WAITING | Explicit reason; resource release and new sequence commit atomically |
| Cancel | PLANNED / WAITING / CALLED → CANCELLED | Explicit reason; terminal state |
| Mark no-show | PLANNED / EN_ROUTE → NO_SHOW | Appointment only, scheduled time reached, no arrival fact; mandatory typed HUMAN actor, authorized manual action and reason; EN_ROUTE is not presence |

`DONE` and `CANCELLED` are terminal. No-show after an `ARRIVED` event is forbidden. Any resource write and corresponding event/state change are a single transaction obligation for the later command service.

All timestamps are timezone-aware instants normalized to UTC. Tenant display timezone must be an explicit valid IANA identifier. Lateness has no ranking or state effect unless separately configured; no default lateness threshold is introduced here.

## Ranking contract and oracle

At each server evaluation, compute callable rank from current `WAITING` visits; do not persist a daily order. Filter by tenant, queue, confirmed arrival **not later than the evaluation instant**, resource compatibility and current resource availability. Appointments with `scheduled_at <= evaluated_at` sort first by appointment instant, **confirmed arrival instant**, stable queue sequence, then visit ID. Admitted walk-ins follow by **confirmed arrival instant**, sequence, then visit ID. Waiting-entry instant remains a separate audit fact (including after manual return to waiting), not a replacement for ARRIVED in the G1 tie-break. Future appointments are not callable. Human override must be explicit, authorized, reasoned and audited. An authorized staff member may not call a lower-ranked candidate by omitting the reason or by merely having the override permission; an `ORDER_OVERRIDE` event must accompany the exceptional call. A visit already in `CALLED` is engaged and is never automatically reordered or recalled. Ranking carries no clinical priority.

`call_visit` consumes an explicit **candidate set, resource and evaluation instant** and rejects ineligible/stale choices. This pure 08.1 function CANNOT verify that an untrusted caller supplied the complete candidate set: the future **08.3 server service MUST load all authorized tenant/queue candidates from its own DB under the transaction lock**, rank them, and commit the selected transition/event atomically; a client-provided ranking or filtered subset must NEVER be treated as the authoritative queue. Likewise, G2 role grants and QR signature validation are outside 08.1 and MUST be enforced upstream.

Oracle in UTC (tenant IANA timezone separately supplied): A appointment 09:00 arrived 08:45; B appointment 09:00 arrived 09:05; W admitted walk-in arrived 09:02; C appointment 09:10 arrived 09:00. At 09:05: `A → B → W`, C excluded. At 09:10 with none called: `A → B → C → W`. If W was called earlier, W remains engaged and is not recalled by recomputation.

## Event and persistence contract

Every accepted transition emits versioned, timestamped event facts with tenant and visit references, actor kind/reference, before/after state, and reason where required. A rejected command must not emit state-changing events. Aggregate version uniqueness is declared per tenant/visit reference. The event table intentionally does not cascade with identifiable visit rows so minimized audit can outlive visit retention; it remains tenant-bound. There is no unrestricted event JSON payload and no clinical foreign key. Append-only enforcement and the transaction boundary are obligations of the later persistence service; 08.1 has no database triggers, engine, or write path and does not claim to enforce them at runtime.

**Persistent chair ownership (G1):** `queue_visits.held_resource_id` records the currently held resource. It is scoped by the composite `(tenant_id, held_resource_id)` foreign key to `queue_resources`, unique per tenant while held, and constrained to be non-NULL *if and only if* `status = CHAIR`. Compatibility assignments in `queue_visit_resources` are NOT proof of chair occupancy. The later 08.3 command service MUST check compatibility and atomically claim/release this column together with visit state and audit events; no durable transaction runtime exists in 08.1.

**Persistent check-in provenance (G1/G2):** `queue_event_log.method` stores `STAFF` or `KIOSK_QR` for ARRIVED and WAITING_ENTERED, never for unrelated event types. Domain event validation and SQL constraints reject missing or invalid provenance in synthetic tests. `queue_event_log.resource_id` likewise captures the opaque resource reference on RESOURCE_CLAIMED and RESOURCE_RELEASED (mandatory for these events, forbidden on others), so released chair audit survives subsequent ownership changes; no foreign key binds this minimized audit to deletable resource rows. Token validation/device identity still belongs to 08.2, and durable append-only transaction enforcement belongs to 08.3.

Separate schema tables: tenants, queues, resources, visits, visit-resource compatibility, minimized event log, external **appointment** references. Composite tenant foreign keys scope queue/resource/visit links. Appointment source reference must be unique across visits per tenant/source/external ID, not just per visit, preventing a single external appointment from silently becoming two Queue visits. The 08.1 reference contract permits only `APPOINTMENT` entity kind; repeating patient identity mappings are deliberately deferred to LOT09. The model is a contract, not an executable migration. Any physical database format, engine, encryption/key custody, backup mechanism, purge executor, or startup/bootstrap design requires separate technical validation before persistent personal data is introduced.

G3 policy carried forward for future implementation: identifiable visit and external-reference data 30 days after closure; minimized audit 12 months; operational logs/ledger 7 days; encrypted backups 7 daily plus 4 weekly; lab targets RPO 1h/RTO 2h. Legal review is required before real-patient use. These retention and recovery controls are not claimed as implemented by 08.1.

## FUE-0 evidence plan

FUE-0 applies because this sub-lot supplies contracts, pure domain rules, schema metadata and tests only; there is no runnable user-facing workflow. Tests use synthetic identities and times and assert: arrival/event atomic plan; informational EN_ROUTE; no-show boundaries; `UNLOCATED_AFTER_CALL`; override permission; exceptional chair release/requeue; 09:05/09:10 dynamic oracle; tenant/resource filtering; schema isolation and ephemeral schema creation. No browser screenshots are applicable; no UI exists in this sub-lot. For this correction pass, local Windows Python tests and review of the exact local Git commit are the executable FUE-0 evidence; do not claim new GitHub Actions evidence from a skipped workflow. Previous CI for the original PR HEAD remains historical evidence only, not proof of corrections. These tests cannot certify completeness of server-side candidate snapshots, DB transactions, live RBAC, durable append-only events, LAN TLS or Windows installer; these remain later required gates.

## Explicitly deferred

08.2 local identities/RBAC/devices/QR; 08.3 transactional engine and runtime; 08.4 REST/SSE/webhooks/idempotency; 08.5 interfaces/FUE-G; 08.6 adversarial/offline/recovery/acceptance; technical Windows installation; legal review; LOT10 physical wall certification. No clinical integration, destructive migration, Internet requirement, LLM, Vercel deployment or cabinet deployment is included.
