# Digital Crown — LOT V1.5-07 / 07.1.A+B — MultiView registry and layout foundation

**STATUS: DRAFT CANDIDATE / FUE-0 ONLY.** The owner's 22 October 2026 GO authorizes the isolated code/test proposal, not its merge, production activation, real clinic access, Vercel or any scientific/medical interpretation.

## Source decisions, not invented features

- [LOT07-A Notion: nine French starting dispositions + personal layouts + all ideas retained 15 October](https://app.notion.com/p/3e677c66336281639049f4cc7be1e5ae).
- [LOT07.1 Notion: shared Desktop C scope, patient A only, 07.1.A then 07.1.B](https://app.notion.com/p/3f977c66336281648581cad81ea058e9).
- [Canonical V1.5 roadmap, LOT07](https://app.notion.com/p/3e677c66336281d88c82d2fbe43835fb).

This contract models exactly these default dispositions, in French and as editable starting points: Vue d'ensemble (owner favourite: Dossier + Agenda + Imagerie), Consultation, Agenda du cabinet, Imagerie, Comparaison orthodontique (two independent Céphalo timepoint slots plus Photos), Planification des traitements, Suivi clinique, Gestion administrative, and Présentation au patient. It also models seven layout **geometries**: single, two columns, two rows, three columns, dominant+two, grid 2×2, focus+rail. These are NOT nine hard-coded UI/business forks.

## Reuse / historical work preserved

G1 was genuinely coded and browser-tested on a branch: [PR #897 two real modules](https://github.com/hraaaaf/Digital_crown/pull/897) and [#913 Patient/Media follow-up](https://github.com/hraaaaf/Digital_crown/pull/913). They remain unmerged and **stacked on older prerequisite branches**. Do not blindly cherry-pick them into current master. Historical G1 actually runs a two-pane patient + authenticated media view on >=1280 CSS px, 37–63% bounded resizing via pointer and keyboard, exchange, reset, and T0/T1 comparison from existing PatientMediaTimeline, behind default-off feature flag; it does not implement all nine layouts.

The present new candidate starts from current master rather than any old PR. It supplies a separate, dormant, reusable layout model + geometry grid + React composition frame and targeted tests. **No App, PatientDetailsInner, Command, API, database, RBAC, theme or mobile code is changed.** The component StudioLayoutFrame is deliberately not mounted by any route: a passing contract CI is FUE-0, NOT an authenticated Cabinet FUE-I or preview of live clinical data.

## Guardrails to be completed before integrated use

1. A future Cabinet adapter must supply **server-authorized** module capabilities, tenant-verified current session, trusted workstation identity, and one active patient. Client-side module filtering in this candidate is only an additional defensive gate; it cannot authorize any data request.
2. On switching A→B, first resolve drafts, cancel/reject stale async operations, revoke blobs/popouts and reset viewer stores. No two patients can coexist. The current candidate does **not** implement the real user/patient transition lifecycle.
3. Two Céphalo views must have proven isolated per-slot state before mounting; default refuses duplicate instances. Never mount two copies of current global CephaloWorkspace while reusing the same store. Scientific F5 preview remains OFF and is not clinically approved.
4. Desktop-only viewport policy: CSS width >=1280, with coarse module minimum-width refusal for unreadable layouts (e.g. 3 columns Céphalo at 1440). Real 200% Windows browser zoom, keyboard, contrast, focus and minimum clinically legible dimensions still require runtime evidence. No Pocket/mobile/tablet/Station/Hub/Companion split.
5. A pure preference allowlist projects only user/workstation IDs, geometry, module/slot identifiers and bounded ratio 37–63. It **never stores patient, images, timepoints, drafts, server data or tokens.** This is a serialization contract, NOT persistent storage. The actual persistence and isolation per user+workstation require a separate backend/identity design and tests.
6. Preview/Apply/Cancel, personal favorites, timepoint selection, adaptive panel controls, keyboard/pointer divider, patient presentation popout and external dual-monitor validation require their own product/UI slices. The existing two-view G1 code is the primary implementation reference for real pointer/keyboard resize.

## Acceptance of this limited slice

RPG-C / FUE-0: Vitest checks nine preset names/order, seven geometries, rejection of invalid and unauthorized slots, absent session/user/workstation/tenant/patient, CSS mobile/zoom widths, multi-Céphalo isolation, minimum width, safe projection and zero renderer invocation under denied conditions. Typecheck full current frontend and production build on the exact source SHA. Ensure branch diff is restricted to dormant foundation files, tests, workflow and this document. The CI does not claim execution of authenticated clinical journeys.

**Next:** actual 07.1.A adapter to the real, authorized Cabinet React components using surgical G1 reconciliation (#897/#913); prove authenticated patient A→B, negative tenant/role, missing/stale media, native desktop 200%, BEFORE/TARGET/AFTER for nine dispositions, and visual owner approval. Only then move from FUE-0 to FUE-I and consider merge. 07-D/07-E and clinic release remain frozen; no automatic merge authority.
