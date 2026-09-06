# Digital Crown Mobile — MOB-5E Bibliothèque clinique — Goal UI

Status: **GOAL LOCKED / BEFORE IMPLEMENTATION**

## Baseline

`master` = `9cb740bc52efc9bf734c19fefc3c4f07470eba80`

## Exact visual Goal

Make the clinical library feel like a **fast chairside reference** on mobile: search first, scan second, open immediately.

Primary task:

> Find one existing protocol and reach the useful clinical content in under ~10 seconds of normal interaction.

## Mobile hierarchy

1. Header
   - `Bibliothèque`
   - `50 protocoles`
2. Search field
   - prominent and immediately visible
3. Optional compact favorite shortcut only if reusing `dc_favs`
4. Protocol list
   - primary act name
   - category
   - duration
   - difficulty
5. Protocol detail
   - back action
   - protocol identity
   - compact metadata
   - existing clinical sections in a touch-friendly reading surface
6. Canonical fixed bottom nav unchanged: 5 entries

## Interaction model

- Entry: `Plus → Bibliothèque`
- Route: `/mobile/dashboard?tab=library`
- Search is the primary navigation mechanism
- Card tap opens protocol detail inside the mobile cockpit
- Back returns to the search/list state
- No desktop category rail
- No command palette
- No Science Hub

## Text mockup

```text
CABINET
Bibliothèque                         50 protocoles

[ Rechercher un acte, code, discipline… ]

Protocoles
┌──────────────────────────────────────────┐
│ Extraction molaire                      │
│ Chirurgie · 45 min          Complexe    │
└──────────────────────────────────────────┘
┌──────────────────────────────────────────┐
│ Traitement endodontique                 │
│ Endodontie · … min          …           │
└──────────────────────────────────────────┘

        Aujourd’hui  Patients   +   Assistant  Plus
```

Protocol detail:

```text
‹ Bibliothèque
Extraction molaire
Chirurgie · 45 min · Complexe

[Checklist] [Étapes] [Risques] [Médic.] [Patient]

…existing protocol content…

        Aujourd’hui  Patients   +   Assistant  Plus
```

## Reference

Desktop reference is the existing `EliteLibrary` / `ClinicalRefContent` visual language:

- pearl/card surfaces
- compact clinical metadata
- difficulty signaling
- structured sections
- no decorative mobile redesign that changes clinical meaning

The mobile implementation should adapt hierarchy and density, not invent a separate brand language.

## Role rule

Bibliothèque appears in `Plus` for:

- `DENTISTE`
- `ADMIN`

It is not exposed to `SECRETAIRE` in MOB-5E.

## Constraints

- source = existing `CLINICAL_PROTOCOLS`
- no copied protocol data
- no rewritten drug/dose content
- no backend/API creation
- no patient/cabinet data
- no Science Hub mobile route
- touch targets ≳44 px where interactive
- fixed bottom nav must not obscure essential detail controls

## Certification viewports

Exact BEFORE and AFTER:

- 390×844
- 430×932
- 768×1024

## Observable success

- Bibliothèque absent from baseline Plus, present AFTER for Dentist/Admin
- 5-button canonical nav unchanged
- shared source reports 50 protocols
- search can find `Extraction molaire`
- opening that card shows source-derived sections/content
- 0 horizontal overflow at all three viewports
- 0 console/page runtime errors
- visual hierarchy remains legible without desktop-rail clutter

## Target visual score

`>= 9.2 / 10`

Score must be based on exact AFTER screenshots, not declared in advance.
