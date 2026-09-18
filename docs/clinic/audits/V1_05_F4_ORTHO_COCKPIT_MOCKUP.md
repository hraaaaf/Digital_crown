# V1-05 F4 — Ortho Cockpit Mockup / Reference

Status: PRE-IMPLEMENTATION

## Desktop 1280 concept

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ SUIVI ORTHODONTIQUE                     ACTIF · ALIGNEMENT                  │
│ Début 18 mars 2026 · 4 contrôles structurés                                │
├──────────────────────┬──────────────────────────┬────────────────────────────┤
│ ÉTAT ACTUEL          │ DERNIER CONTRÔLE         │ SUITE & PREUVES            │
│ Phase Alignement     │ 18 sept. 2026            │ Contrôle prévu 12 oct.     │
│ Statut Actif         │ Événement: —             │ RDV confirmé 14 oct.       │
│ T1 · 18 sept.        │ Étape: arc 0.016 NiTi    │ T1 · Céphalo · Pano        │
│                      │                          │ [Voir comparaison]         │
├──────────────────────┴──────────────────────────┴────────────────────────────┤
│ À SUIVRE · Prochaine étape planifiée présente                               │
└──────────────────────────────────────────────────────────────────────────────┘
```

Rules:
- values are neutral facts, not colored as good/bad progress.
- attention row uses restrained neutral/warning semantics only for missing/factual workflow state.
- F3 remains a separate surface immediately below.

## Tablet 768 concept

```
┌──────────────────────────────────────┐
│ SUIVI ORTHODONTIQUE · ACTIF          │
│ Alignement · début 18 mars           │
├──────────────────┬───────────────────┤
│ État actuel      │ Dernier contrôle  │
│ T1               │ 18 sept.          │
│ 4 contrôles      │ Étape suivante…   │
├──────────────────┴───────────────────┤
│ Prochain contrôle / vrai RDV         │
│ Dernières preuves · Céphalo · Pano   │
│ [Voir comparaison]                   │
└──────────────────────────────────────┘
```

## Mobile 390 concept

```
┌──────────────────────────────┐
│ SUIVI ORTHODONTIQUE          │
│ ACTIF · ALIGNEMENT           │
│ Début 18 mars · 4 contrôles  │
├──────────────────────────────┤
│ Dernier contrôle · 18 sept.  │
│ Étape suivante …             │
├──────────────────────────────┤
│ Contrôle prévu · 12 oct.     │
│ RDV réel · 14 oct.           │
├──────────────────────────────┤
│ T1 · Céphalo · Pano          │
│ Voir comparaison →           │
└──────────────────────────────┘
```

## Visual constraints
- reuse `bg-card-bg`, `border-border-main`, `text-main`, `text-text-muted`, `primary`
- no direct emerald/red outcome semantics
- rounded-xl / rounded-2xl hierarchy, not nested-card overload
- 44px minimum for primary drill-down target
- no horizontal overflow
- focus-visible states required
- high-contrast meaning must survive without subtle color

## Rejected directions
- KPI tiles (“progress 72%”, “success”, “risk”)
- timeline duplication
- large analytics dashboard
- mini-copy of F3 measurement table
- next_control_at presented as a booked appointment
