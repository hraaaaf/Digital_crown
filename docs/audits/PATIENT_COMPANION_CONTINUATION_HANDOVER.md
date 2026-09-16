# HANDOVER — DIGITAL CROWN / PATIENT COMPANION CONTINUATION

Repository: `hraaaaf/Digital_crown`

Primary roadmap:
`docs/audits/COMPETITIVE_ROADMAP_POST_MEDIA.md`

Closed Patient Companion canonicals:
1. `docs/audits/PATIENT_COMPANION_D0.md`
2. `docs/audits/PATIENT_COMPANION_D1.md`
3. `docs/audits/PATIENT_COMPANION_D2.md`

Start prompt for a new conversation:
`docs/audits/PATIENT_COMPANION_CONTINUATION_START_PROMPT.md`

## First truth to preserve

At D2 closeout there is **no canonical Patient Companion D3** in the repository.

The roadmap still uses the placeholder `D1+ — useful patient workflows beyond the minimum shell` for additional Patient Companion work. Do not invent or assume a D3 scope. If a future lot is intentionally named D3, first revise the roadmap/canonical contract explicitly after the scope is bounded.

## Closed state

### D0 — CLOSED

Security/authorization foundation:
- distinct Firebase patient principal;
- recipient-bound activation;
- tenant + patient isolation;
- guardian/family access model;
- future appointment read projection;
- explicit Document/Media allow-list grants;
- revocation/audit;
- no duplicate Patient/Appointment/Document/Media source of truth.

Canonical: `docs/audits/PATIENT_COMPANION_D0.md`.

### D1 — CLOSED

Patient-facing minimum useful shell:
- public patient entry independent from cabinet auth;
- dedicated Firebase patient web auth/transport;
- activation/onboarding;
- `/me` context selection;
- future appointments read-only;
- explicitly shared Document/Media metadata only;
- no raw byte serving;
- no staff sidebar/session reuse;
- responsive/human visual validation completed.

Canonical: `docs/audits/PATIENT_COMPANION_D1.md`.

### D2 — CLOSED

Staff operability from canonical patient chart:
- Companion status;
- invitation/reissue;
- temporary QR/code expiry;
- canonical Document/Media share/revoke;
- full Companion revoke;
- no new business source/store;
- no destructive migration;
- no patient appointment mutation;
- no remote gateway;
- no Vercel deployment.

PR: `#523` — merged.
Certified PR head: `206f58e6571c6fdfa2af8e726ce032d694928799`.
Merge commit: `6cc0c41fd64d40ef8929bebe11c67ecc4fc42672`.
Post-merge CI #4574 / run `35100604875`: SUCCESS.
Post-merge PostgreSQL #917 / run `35100604888`: SUCCESS.

Canonical: `docs/audits/PATIENT_COMPANION_D2.md`.

## Important repository movement after D2 merge

D2 merge commit was not the latest master forever. At handover preparation, master had already advanced through Agenda A2.

Observed master during handover preparation:
`1e9fd49af91ffafad89ad9936c6f2e372e883354`

Never assume this SHA is still current in a new conversation. Re-check GitHub first.

## Remaining competitive roadmap

Canonical order after D2:
1. Patient Companion continuation (`D1+` placeholder) — only after scope is explicitly bounded;
2. Lot E — Connect Hub;
3. Lot F — Ortho Journey;
4. Lot G — Assurance Maroc;
5. Lot H — Lab / Prosthesis Collaboration;
6. Lot I — BI / Recall / Outcomes.

F/G may be swapped only if the roadmap/product priority is intentionally changed.

## Next exact — new conversation

Before any implementation:
1. read the roadmap and D0/D1/D2 canonicals from current master;
2. verify current master SHA, open PRs, CI/certifications and any changes since this handover;
3. audit the actual Patient Companion patient-facing surface currently present in code/runtime;
4. identify real product gaps beyond D1, without duplicating internal Patient Journey, staff D2, notification/push, Agenda, Documents or Media Core;
5. propose a bounded next Patient Companion lot with Goal / Success / Proof / exclusions;
6. only then decide whether the roadmap should formally name that lot `D3` or retain another label;
7. for any UI change, capture BEFORE at 390×844 / 768×1024 / 1280×900, define Goal/reference, implement, capture AFTER at the same viewports, compare/test and score visual quality;
8. preserve DB/data/documents/features and run proportional non-regression before merge;
9. never deploy Vercel without explicit user authorization.

## Hard boundaries inherited from D0/D1/D2

- no second Patient source;
- no second Appointment source;
- no second Document/Media source;
- no cabinet JWT reuse for patients;
- no unscoped/public Document or Media fallback;
- no plaintext invitation secret persistence;
- no patient appointment mutation unless a future lot explicitly designs and certifies a safe bounded contract;
- no employee delegation unless separately scoped and certified;
- no remote gateway unless separately scoped and threat-modelled;
- no destructive migration;
- no real cabinet DB touched during development/certification;
- no Vercel deployment without explicit authorization.

## Continuity rule

Do not stop after an audit if the next safe action is obvious. Audit → bound scope → implement → test → visual proof if applicable → PR → exact-head checks → merge after required owner gate → post-merge proof → canonical closeout → next lot.

If the next Patient Companion scope is intentionally not selected, proceed to Lot E only after an anti-duplication audit of existing notification/push/preferences infrastructure.
