# PC-07 — Emergency Photo — UI Target

Status: TARGET LOCKED BEFORE VISUAL CERTIFICATION

## Goal
Permettre au patient d'envoyer rapidement une photo d'urgence au cabinet sans ambiguïté sur la réception, sans diagnostic automatique et sans exposition de données techniques.

## Reference wireframe

```
┌──────────────────────────────────┐
│ [camera] Photo d’urgence         │
│ Envoyez une photo au cabinet     │
│ sans diagnostic automatique.     │
│                                  │
│ [ Prendre ou choisir une photo ] │
│                                  │
│ [shield] photo chiffrée pendant  │
│ le transport, enregistrée après  │
│ confirmation du cabinet          │
└──────────────────────────────────┘

Preview:
┌──────────────────────────────────┐
│          [ photo preview ]       │
│                                  │
│ [ Reprendre ] [ Envoyer cabinet ]│
└──────────────────────────────────┘

Pending:
┌──────────────────────────────────┐
│ Envoi transmis · confirmation    │
│ du cabinet encore en attente.    │
│ [ Vérifier / réessayer ]         │
└──────────────────────────────────┘

Success:
┌──────────────────────────────────┐
│ ✓ Photo reçue par le cabinet.    │
│ [ Envoyer une autre photo ]      │
└──────────────────────────────────┘
```

## Truth rules
- aucun `reçue` avant ACK cabinet;
- pending explicite si ACK non reçu;
- retry réutilise la même idempotency key;
- aucun diagnostic ou interprétation;
- aucun identifiant interne visible.

## Mobile requirements
- viewports: 360x800 and 390x844;
- Chromium + WebKit;
- actions >=44px;
- zero horizontal overflow;
- preview contained without crop destructive;
- section usable one-handed;
- text remains readable without wrapping critical CTA labels.

## BEFORE
Base reference: master@b4e40fa1f3a63d4d7bf4d91223fa376902dcd7a2.
Expected: no `[data-pc07-emergency-photo]` surface.

## AFTER
Candidate must show:
- idle;
- preview;
- pending;
- success;
at 360x800 and 390x844 on Chromium + WebKit.

## Visual scoring
- hierarchy / clarity: 25%
- truthful state communication: 25%
- mobile ergonomics: 20%
- spacing / readability: 15%
- consistency with Patient Companion: 15%

No 9.5+ score without independent review.
