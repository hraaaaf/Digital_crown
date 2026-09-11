# Digital Crown — Commercial Pack Harmonization

Date: 2026-09-11
Status: ACTIVE / INCOMPLETE
Canonical file: this document
Repository: `hraaaaf/Digital_crown`
Branch: `feat/commercial-pack-harmonization`
Last verified branch HEAD before this handover commit: `3034abccf0483ce4fd56c74460a36bfa5ab6bb08`
Deployment: none requested / none authorized

## Goal

One commercial pack must produce the same entitlement and quota semantics everywhere in Digital Crown.

Success is observable only when all of the following are true:

1. GOLD / PREMIUM / ELITE limits are defined by one canonical policy.
2. ELITE is semantically unlimited. No numeric sentinel such as `999` remains for team limits.
3. License validity/device authorization stays separate from commercial subscription entitlements.
4. `CabinetType` / clinic structure stays separate from the commercial plan unless a specific compatibility rule is proven necessary.
5. Upgrade is deterministic.
6. Downgrade cannot silently create an over-quota account and cannot silently deactivate users.
7. Backend + API contract + frontend rendering are coherent.
8. Pending team members cannot be used to bypass quotas.
9. Exact-head tests and CI are green before closeout.

## Verified architecture

Three independent axes are currently supported by repository evidence:

1. **License** — installation may run or not; expiry/revocation/device authorization.
2. **Subscription plan** — `GOLD`, `PREMIUM`, `ELITE`; commercial team limits/entitlements.
3. **Structure type** — e.g. `PRIVE`, `CLINIQUE`; cabinet organization/topology.

Do not automatically derive structure type from subscription plan.

## Verified plan limits

Current intended commercial team model:

- GOLD: 1 dentist total, including owner + 2 assistants/secretaries.
- PREMIUM: 2 dentists total + 6 assistants/secretaries.
- ELITE: unlimited team.

## Verified defects

### D1 — fake unlimited

`backend/routers/team.py` currently contains:

```python
PLAN_QUOTAS = {
    "GOLD": {"dentistes": 1, "secretaires": 2},
    "PREMIUM": {"dentistes": 2, "secretaires": 6},
    "ELITE": {"dentistes": 999, "secretaires": 999},
}
```

This is not a real unlimited semantic and leaks an artificial ceiling into API/UI behavior.

### D2 — unsafe downgrade

`backend/routers/superadmin.py:set_client_plan()` currently validates only the plan name, assigns `user.subscription_plan = plan`, writes history, commits, and returns.

It does **not** verify that the current approved + pending team fits the target plan. Therefore an ELITE/PREMIUM account can be downgraded into an inconsistent over-quota state.

### D3 — quota policy duplicated in router

Commercial limits live directly in `team.py`, so another consumer can drift from the same business rules.

## Important verified detail

`backend/schemas/auth.py::QuotaOut` already declares:

```python
dentistes_max: Optional[int] = None
secretaires_max: Optional[int] = None
```

Therefore the API contract already supports `None` for unlimited. A schema migration is not required for the basic semantic fix.

## Current unknowns still to verify before frontend changes

- Exact frontend consumer(s) of `/team/quota`.
- Whether any frontend code assumes `dentistes_max` / `secretaires_max` are always numeric.
- Whether ELITE is already rendered as `Illimité` or equivalent.
- Exact existing test coverage for SuperAdmin plan changes.

Do not change UI before these are verified.

## Recommended canonical policy

Create a small backend policy module, preferably `backend/services/subscription_policy.py` unless repository conventions strongly indicate a better location.

Target shape:

```python
from dataclasses import dataclass
from typing import Optional

@dataclass(frozen=True)
class PlanPolicy:
    dentists_limit: Optional[int]
    secretaries_limit: Optional[int]

PLAN_POLICIES = {
    "GOLD": PlanPolicy(1, 2),
    "PREMIUM": PlanPolicy(2, 6),
    "ELITE": PlanPolicy(None, None),
}
```

A helper should normalize unknown/missing values safely to GOLD only where the current application already does so. Do not invent a tier ordering unless needed.

## Downgrade policy

Chosen safe behavior:

- Upgrade: allow immediately if target plan is valid.
- Same plan: idempotent success is acceptable.
- Downgrade: block if current approved + pending team exceeds the target limits.
- Return a clear 409 Conflict (or existing repository-standard equivalent) with used/allowed counts.
- Do not mutate the subscription plan when blocked.
- Do not auto-deactivate team members.

Pending members must reserve quota, matching current anti-gaming behavior.

## Roadmap

### R1 — Inventory consumers
Status: IN PROGRESS

Tasks:
- Locate frontend `/team/quota` consumer.
- Locate existing team/quota tests.
- Locate SuperAdmin plan-change tests.
- Confirm auth/login behavior for deactivated/rejected members is already covered or out of scope.

Success:
- all direct consumers of the quota contract identified.

### R2 — Canonical policy
Status: NOT STARTED

Tasks:
- add centralized plan policy.
- replace router-local numeric matrix.
- represent ELITE limits as `None`.

Success:
- no `999` team sentinel remains.
- team router reads one canonical policy.

### R3 — Team quota semantics
Status: NOT STARTED

Tasks:
- `_build_quota()` handles `None` as unlimited.
- `can_add_dentiste` / `can_add_secretaire` are always true when corresponding limit is `None`.
- approval recheck handles unlimited without numeric comparison.
- quota error messages never show `None` as a fake number.

Success:
- GOLD/PREMIUM finite limits preserved.
- ELITE can exceed PREMIUM without artificial ceiling.

### R4 — Safe upgrade/downgrade
Status: NOT STARTED

Tasks:
- make SuperAdmin plan update use canonical target limits.
- count approved + pending team exactly like team quota logic.
- block incompatible downgrade before mutation.
- preserve current users and pending invitations.

Success:
- over-cap downgrade returns conflict and leaves plan unchanged.
- compliant downgrade succeeds.
- upgrade succeeds.

### R5 — Frontend coherence
Status: NOT STARTED / ONLY IF REQUIRED

Tasks:
- if frontend assumes numeric maxima, adapt it to `null`/`None` unlimited.
- render `Illimité` instead of `999`.
- preserve finite used/max display for GOLD/PREMIUM.

UI rule if changed:
- BEFORE capture.
- written Goal.
- reference/mockup if visual change is non-trivial.
- implementation.
- AFTER at same viewports: 390 / 768 / 1280.
- visual comparison + tests + score.

Success:
- no visual `999` for ELITE.
- no broken progress/ratio computation from null maximum.

### R6 — Tests
Status: NOT STARTED

Required targeted coverage:
- GOLD dentist/secretary caps.
- PREMIUM caps.
- ELITE quota returns `None` maxima and allows additions beyond PREMIUM.
- pending members reserve quota.
- approval after a plan change cannot exceed finite target quota.
- downgrade ELITE/PREMIUM -> finite target over cap is blocked and non-mutating.
- compliant downgrade works.
- upgrade works.
- cabinet structure remains independent from commercial plan.
- device/license semantics remain untouched.

### R7 — Git / PR / CI
Status: NOT STARTED

Tasks:
- commit only coherent, reviewed changes.
- open PR against `master`.
- inspect CI once.
- while CI runs, do independent review/docs work.
- if CI fails: diagnose, patch, test, rerun safely.
- no Vercel deployment without explicit user authorization.

Success:
- exact HEAD CI green.
- PR mergeability verified.

### R8 — Closeout
Status: NOT STARTED

Tasks:
- update this canonical file with exact final HEAD / PR / runs.
- record proven behavior, not intended behavior.
- merge only after required proof.
- post-merge verify master contains the fix.

## Tests / proof policy

Never claim `fixed`, `done`, `validated`, `production-ready`, or `10/10` without proof.

Internal proof requires as applicable:
- code review,
- targeted tests,
- observed API/UI behavior,
- CI on exact HEAD,
- repo docs consistency.

## Non-goals unless new evidence appears

- Do not couple `CabinetType.CLINIQUE` to ELITE.
- Do not invent ELITE-only feature gates around files/services merely named `elite`.
- Do not alter device limits based on team-plan semantics.
- Do not deploy.
- Do not auto-deactivate users during downgrade.

## Last verified repository evidence

- Branch: `feat/commercial-pack-harmonization`
- Pre-handover HEAD: `3034abccf0483ce4fd56c74460a36bfa5ab6bb08`
- `backend/routers/team.py`: ELITE = `999/999`, pending + approved count toward quota.
- `backend/routers/superadmin.py`: direct plan mutation with no target-capacity guard.
- `backend/schemas/auth.py`: nullable maxima already supported.
- PR: none at time of handover creation.
- CI for this branch change: none at time of handover creation.
- Deployment: none.

## Next exact

1. Re-read this file.
2. Verify current branch HEAD after this handover commit.
3. Locate frontend quota consumer and existing relevant tests.
4. Implement R2 + R3 + R4 in the smallest coherent patch.
5. Add R6 targeted tests.
6. Only touch frontend if consumer verification proves it necessary.
7. Commit, open PR, inspect exact-head CI.
8. Update this file during closeout.

## New-conversation handover prompt

```text
Reprends le chantier Digital Crown — harmonisation des packs commerciaux.

Commence impérativement par lire :

docs/handovers/2026-09-11-commercial-pack-harmonization-handover.md

sur la branche :

feat/commercial-pack-harmonization

Puis vérifie immédiatement le HEAD réel de la branche avant toute modification.

Goal : un pack commercial doit produire exactement les mêmes quotas/entitlements partout, avec GOLD 1 dentiste total + 2 assistantes, PREMIUM 2 + 6, ELITE réellement illimité sans sentinel 999.

Architecture à préserver :
- licence = validité/expiration/device,
- subscription plan = GOLD/PREMIUM/ELITE,
- cabinet type = structure PRIVE/CLINIQUE,
ces trois axes restent séparés sauf preuve contraire dans le repo.

Défauts déjà vérifiés :
1. backend/routers/team.py encode ELITE avec 999/999 ;
2. backend/routers/superadmin.py permet un changement de plan sans contrôler l’effectif existant ;
3. QuotaOut dans backend/schemas/auth.py accepte déjà Optional[int], donc None peut représenter l’illimité sans migration de schéma.

Politique de downgrade choisie : bloquer proprement un downgrade incompatible, sans mutation et sans désactivation automatique. Pending + approved doivent réserver le quota.

Exécute sans demander de validation tant qu’il n’y a pas de vrai human gate :
frontend consumer/tests → policy centrale → team quota → downgrade guard → tests → commit → PR → CI → closeout du fichier canonique.

Ne déploie rien sur Vercel sans autorisation explicite.
Ne déclare rien terminé sans preuve exacte.

Format de travail : Résultat → preuve → prochaine action, puis 📍 REPÈRES avec uniquement l’état vérifié.
```
