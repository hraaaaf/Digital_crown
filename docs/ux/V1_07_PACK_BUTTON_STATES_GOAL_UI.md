# V1-07 — Pack button states — Goal UI

Date: 2026-09-19

## Goal

Make commercial-pack actions truthful and unambiguous without redesigning the normal GOLD / PREMIUM / ELITE surfaces.

## Reference / target states

### Team load failure

Current risk: a failed request is rendered as “Aucun membre”.

Target:
- keep the existing error visual language (rose alert);
- message: “Impossible de charger l’équipe. Réessayez.”;
- never render the empty-team illustration while the last load failed.

### GOLD partial quota

Current risk: owner consumes the 1/1 dentist seat, so the generic “Quota atteint — passez au plan supérieur” appears even when assistant seats remain.

Target:
- keep the same quota card;
- state exactly which role is full;
- if assistants remain available, do not imply the whole pack is exhausted.

Reference copy for GOLD 1/1 dentist + 0/2 assistants:
“Quota dentistes atteint — 2 place(s) assistante(s) disponible(s).”

### Rejected team member

Current risk: rejected member exposes a “Réactiver” action even though approval remains rejected.

Target:
- rejected badge remains;
- no Reactivate/Suspend toggle is shown for rejected identities;
- destructive delete remains available.

### In-flight mutations

Target:
- one network mutation per clicked action;
- clicked action is disabled until completion;
- no second POST/PUT/DELETE from a rapid double click;
- existing normal visual hierarchy is preserved.

### Desktop pack downgrade refusal

Target:
- keep the existing toast system;
- surface backend 409 detail with reserved dentist/assistant usage and target limits;
- no generic-only downgrade error.

### Renewal action

Target:
- visible wording says WhatsApp, not email;
- success copy comes from a confirmed backend send;
- no phone and transport failure are errors, not successes.

## Evidence protocol

Before/after viewports are identical:
- 1024 × 900
- 1440 × 1000

Scenarios:
1. TeamManager GOLD partial quota.
2. TeamManager load failure.
3. TeamManager rejected member action row.
4. Desktop SuperAdmin incompatible ELITE → GOLD downgrade.
5. Desktop SuperAdmin renewal with no phone.

No Vercel deployment is part of this protocol.
