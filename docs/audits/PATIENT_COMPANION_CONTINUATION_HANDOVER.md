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

## Final verified closeout snapshot

Patient Companion D0 = CLOSED.
Patient Companion D1 = CLOSED.
Patient Companion D2 = CLOSED.

D2 product PR:
- PR `#523` — MERGED;
- certified PR head `206f58e6571c6fdfa2af8e726ce032d694928799`;
- merge commit `6cc0c41fd64d40ef8929bebe11c67ecc4fc42672`;
- post-merge CI `#4574` / run `35100604875` — SUCCESS;
- post-merge Cabinet Upgrade PostgreSQL `#917` / run `35100604888` — SUCCESS.

D2 canonical closeout / continuation handover:
- PR `#536` — MERGED;
- PR head `d9239a11e4df6dbaa359b83aa49a257c9e94d9d3`;
- merge commit `63d3902656d0525dccac60cbc15cf2aa21b1ffd9`;
- post-merge CI `#4593` / run `35104004274` — SUCCESS;
- post-merge Cabinet Upgrade PostgreSQL `#919` / run `35104004119` — SUCCESS.

Repository hygiene:
- obsolete pre-D2 handover PR `#521` was closed unmerged after D2 closeout so it cannot reintroduce stale scope.

## Current master movement at this handover refresh

Observed current `master` while refreshing this handover:
`fb3a870e2fba92a005a3e3de57ee378042b23be3`

This commit is a descendant of the D2 closeout merge `63d3902656d0525dccac60cbc15cf2aa21b1ffd9` and came from unrelated Pharmacology CI work (`#537`).

A compare from the D2 closeout merge to this observed master showed no Patient Companion file change. Therefore the D0/D1/D2 product state and continuation contract remain intact at this refresh.

Never assume this SHA is still current in a new conversation. Re-check GitHub first.

## First truth to preserve

There is **no canonical Patient Companion D3** in the repository at this handover.

The roadmap still uses the placeholder `D1+ — useful patient workflows beyond the minimum shell` for additional Patient Companion work. Do not invent or assume a D3 scope. If a future lot is intentionally named D3, first bound the scope and explicitly revise the roadmap/canonical contract.

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

Canonical: `docs/audits/PATIENT_COMPANION_D2.md`.

## Remaining competitive roadmap

Canonical order after D2:
1. Patient Companion continuation (`D1+` placeholder) — only after scope is explicitly bounded;
2. Lot E — Connect Hub;
3. Lot F — Ortho Journey;
4. Lot G — Assurance Maroc;
5. Lot H — Lab / Prosthesis Collaboration;
6. Lot I — BI / Recall / Outcomes.

F/G may be swapped only if roadmap/product priority is intentionally changed.

## Next exact — new conversation

Before any implementation:
1. read from current master:
   - `docs/audits/COMPETITIVE_ROADMAP_POST_MEDIA.md`;
   - `docs/audits/PATIENT_COMPANION_D0.md`;
   - `docs/audits/PATIENT_COMPANION_D1.md`;
   - `docs/audits/PATIENT_COMPANION_D2.md`;
   - this handover;
2. verify current master SHA, relevant open PRs, CI/certifications and divergence since this handover;
3. audit read-only the actual Patient Companion patient-facing surface and backend contracts;
4. identify real gaps beyond D1 without duplicating Patient Journey, D2 staff administration, Agenda, Documents, Media Core or notification/push/preferences infrastructure;
5. propose a bounded next Patient Companion lot with Goal / Success / Proof / exclusions / risks;
6. only then decide whether the roadmap should formally name that lot `D3` or retain another label;
7. if the scope is safe and does not require a human gate, continue automatically into implementation/testing/proof;
8. for any UI change: BEFORE 390×844 / 768×1024 / 1280×900 → written Goal/reference → implementation → AFTER same viewports → comparison/tests → visual score;
9. preserve DB/data/patients/documents/media/features and run proportional non-regression;
10. no Vercel deployment without explicit authorization.

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

Do not stop after an audit if the next safe action is obvious.

Audit → bound scope → implement → test → visual proof if applicable → PR → exact-head checks → merge after required owner gate → post-merge proof → canonical closeout → next lot.

If no new Patient Companion workflow is retained, proceed to Lot E only after an anti-duplication audit of existing notification/push/preferences infrastructure.
