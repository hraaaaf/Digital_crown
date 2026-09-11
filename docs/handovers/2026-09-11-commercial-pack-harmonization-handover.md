# Digital Crown — Commercial Pack Harmonization

Date: 2026-09-11
Status: ACTIVE / INCOMPLETE
Canonical file: `docs/handovers/2026-09-11-commercial-pack-harmonization-handover.md`
Repository: `hraaaaf/Digital_crown`
Branch: `feat/commercial-pack-harmonization`
Verified parent before first handover commit: `66712ca0a55f7b856dfa63ffc23487e4fa29e1a9`
First handover commit: `2af581cb50f5b213ac5c9e6ae6ccb0fb4685b43f`
Deployment: none requested / none authorized

> Note: an earlier read had observed `3034abcc...`, but the branch advanced before the handover write. The actual parent of the first handover commit is `66712ca0...`; this file uses the Git commit parent as the authoritative proof.

## Goal

One commercial pack must produce the same quota/entitlement semantics everywhere in Digital Crown.

Success requires observable proof that:

1. GOLD / PREMIUM / ELITE use one canonical policy.
2. ELITE is genuinely unlimited, with no numeric sentinel such as `999`.
3. License validity/device authorization remains separate from commercial subscription entitlements.
4. `CabinetType` / clinic structure remains independent from the commercial plan unless repository evidence proves a compatibility rule is required.
5. Upgrade and downgrade behavior is deterministic.
6. Downgrade cannot silently create an over-quota account or silently deactivate users.
7. Backend, API contract and frontend behavior are coherent.
8. Pending team members cannot bypass quotas.
9. Exact-HEAD tests and CI are green before closeout.

## Verified architecture

Three distinct axes are supported by repository evidence:

- **License**: active/expired/revoked + installation/device authorization.
- **Subscription plan**: `GOLD`, `PREMIUM`, `ELITE`.
- **Structure type**: e.g. `PRIVE`, `CLINIQUE`.

Do not derive `CabinetType` from `SubscriptionPlan` automatically.

## Verified commercial limits

- GOLD: 1 dentist total, owner included + 2 assistants/secretaries.
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

The `999` sentinel is not a real unlimited semantic.

### D2 — unsafe downgrade

`backend/routers/superadmin.py:set_client_plan()` validates the plan name and directly writes `user.subscription_plan = plan` without checking whether the current approved + pending team fits the target plan.

Therefore PREMIUM/ELITE can currently be downgraded into an inconsistent over-quota state.

### D3 — business policy duplicated inside router

Plan quotas are embedded in `team.py`, making drift possible for any other consumer.

## Important verified API detail

`backend/schemas/auth.py::QuotaOut` already supports nullable maxima:

```python
dentistes_max: Optional[int] = None
secretaires_max: Optional[int] = None
```

Therefore `None` can represent unlimited without changing this schema.

## Chosen safe downgrade policy

- Upgrade: allow immediately if target plan is valid.
- Same plan: idempotent success is acceptable.
- Downgrade: block when approved + pending team exceeds target finite limits.
- Return a clear conflict before mutation.
- Keep the current plan unchanged when blocked.
- Never auto-deactivate team members.
- Pending members reserve quota, matching current anti-gaming behavior.

## Canonical policy target

Preferred minimal design:

```python
@dataclass(frozen=True)
class PlanPolicy:
    dentists_limit: int | None
    secretaries_limit: int | None

PLAN_POLICIES = {
    "GOLD": PlanPolicy(1, 2),
    "PREMIUM": PlanPolicy(2, 6),
    "ELITE": PlanPolicy(None, None),
}
```

Suggested module: `backend/services/subscription_policy.py`, unless current repo conventions clearly justify another location.

## Roadmap

### R1 — Consumer/test inventory
Status: IN PROGRESS

- Locate exact frontend consumer(s) of `/team/quota`.
- Verify whether numeric maxima are assumed.
- Locate team/quota tests.
- Locate SuperAdmin plan-change tests.
- Confirm whether rejected/deactivated auth behavior is already covered or outside this lot.

Success: all direct quota consumers and relevant tests are identified.

### R2 — Canonical plan policy
Status: NOT STARTED

- Add centralized GOLD/PREMIUM/ELITE policy.
- Replace router-local matrix.
- Encode ELITE limits as `None`.

Success: no `999` team sentinel remains; one policy is authoritative.

### R3 — Team quota semantics
Status: NOT STARTED

- `_build_quota()` handles `None` as unlimited.
- `can_add_dentiste` / `can_add_secretaire` stay true for unlimited limits.
- Approval recheck avoids numeric comparison against `None`.
- Error messages remain meaningful for finite plans.

Success: GOLD/PREMIUM caps preserved; ELITE has no artificial ceiling.

### R4 — Safe plan changes
Status: NOT STARTED

- SuperAdmin plan update uses canonical target limits.
- Count approved + pending consistently with team quota logic.
- Block incompatible downgrade before changing the plan.
- Preserve all users/invitations.

Success: over-cap downgrade is non-mutating; compliant downgrade and upgrade succeed.

### R5 — Frontend coherence
Status: NOT STARTED / ONLY IF REQUIRED

Only modify frontend if R1 proves it necessary.

If changed:
- display `Illimité` for null maxima,
- avoid null ratio/progress bugs,
- preserve finite used/max display for GOLD/PREMIUM.

Mandatory UI protocol if visual code changes:
BEFORE → written Goal → reference/mockup if needed → implementation → AFTER at 390/768/1280 → comparison/tests → visual score.

### R6 — Targeted tests
Status: NOT STARTED

Required coverage:
- GOLD dentist/secretary caps.
- PREMIUM caps.
- ELITE returns null maxima and can exceed PREMIUM counts.
- pending members reserve quota.
- approval after a plan change cannot exceed finite quota.
- over-cap downgrade blocked and non-mutating.
- compliant downgrade succeeds.
- upgrade succeeds.
- cabinet structure remains independent.
- license/device semantics remain untouched.

### R7 — Git / PR / CI
Status: NOT STARTED

- Commit coherent changes only.
- Open PR against `master`.
- Inspect CI once.
- While CI runs, complete independent review/docs work.
- On failure: diagnose → patch → test → rerun safely.
- No Vercel deployment without explicit authorization.

Success: exact-HEAD CI green and PR mergeability verified.

### R8 — Closeout
Status: NOT STARTED

- Update this canonical file with exact final HEAD / PR / runs.
- Record proven behavior only.
- Merge after required proof.
- Verify post-merge master contains the fix.

## Current unknowns

- Exact frontend quota consumer(s).
- Whether frontend already renders ELITE as `Illimité`.
- Exact existing SuperAdmin plan-change test coverage.

These must be verified before touching UI.

## Non-goals unless new evidence appears

- Do not couple `CLINIQUE` to ELITE.
- Do not invent ELITE-only feature gates from filenames such as `elite_manager.py`.
- Do not treat team unlimited as device unlimited.
- Do not auto-deactivate users on downgrade.
- Do not deploy.

## Proof policy

Never declare fixed/done/validated/production-ready without proof.

Internal proof should combine, as applicable:
- code review,
- targeted tests,
- observed API/UI behavior,
- exact-HEAD CI,
- repository documentation consistency.

## Verified repository state at canonicalization

- Repository: `hraaaaf/Digital_crown`
- Branch: `feat/commercial-pack-harmonization`
- First handover commit: `2af581cb50f5b213ac5c9e6ae6ccb0fb4685b43f`
- Its verified parent: `66712ca0a55f7b856dfa63ffc23487e4fa29e1a9`
- `team.py`: ELITE `999/999`; approved + pending count toward quota.
- `superadmin.py`: direct plan mutation without target-capacity guard.
- `auth.py::QuotaOut`: nullable maxima already supported.
- PR for commercial harmonization: none verified at canonicalization.
- Deployment: none.

## Next exact

1. Re-read this file.
2. Verify the current real branch HEAD before editing.
3. Finish R1 inventory.
4. Implement R2 + R3 + R4 as the smallest coherent patch.
5. Add R6 tests.
6. Touch frontend only if R1 proves necessary.
7. Commit → PR → exact-HEAD CI.
8. Update this file at closeout.

## New-conversation handover prompt

```text
Reprends le chantier Digital Crown — harmonisation des packs commerciaux.

Commence impérativement par lire :

docs/handovers/2026-09-11-commercial-pack-harmonization-handover.md

sur la branche :

feat/commercial-pack-harmonization

Puis vérifie immédiatement le HEAD réel de la branche avant toute modification.

Goal : un pack commercial doit produire les mêmes quotas/entitlements partout : GOLD = 1 dentiste total + 2 assistantes, PREMIUM = 2 + 6, ELITE = réellement illimité sans sentinel 999.

Architecture à préserver :
- licence = validité/expiration/device,
- subscription plan = GOLD/PREMIUM/ELITE,
- cabinet type = structure PRIVE/CLINIQUE.
Ne mélange pas ces axes sans preuve repo.

Défauts déjà vérifiés :
1. backend/routers/team.py encode ELITE avec 999/999 ;
2. backend/routers/superadmin.py change le plan sans contrôler l’effectif existant ;
3. backend/schemas/auth.py::QuotaOut accepte déjà Optional[int], donc None peut représenter l’illimité.

Politique de downgrade retenue : bloquer proprement un downgrade incompatible avant mutation, sans désactivation automatique. Approved + pending réservent le quota.

Exécute sans demander de validation tant qu’il n’y a pas de vrai human gate :
R1 frontend/tests → R2 policy centrale → R3 team quota → R4 downgrade guard → R6 tests → commit → PR → CI → R8 closeout.

Si UI modifiée : BEFORE → Goal → référence/mockup si nécessaire → implémentation → AFTER 390/768/1280 → comparaison/tests → score visuel.

Ne déploie rien sur Vercel sans autorisation explicite.
Ne déclare rien terminé sans preuve exacte.

Format : Résultat → preuve → prochaine action, puis 📍 REPÈRES avec seulement l’état vérifié.
```
