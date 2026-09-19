# V1-07 G1 — Landing Geography Truth UI Target

## BEFORE — verified source defect
The public hero says Digital Crown is designed for **“les dentistes algériens”** while the V1 product target is Morocco.

## Goal
Align the public landing copy with the actual V1 market without changing layout, navigation, CTA behavior or styling.

## Success
- hero copy says **“les dentistes marocains”**;
- the obsolete **“dentistes algériens”** copy is absent;
- matched BEFORE/AFTER screenshots exist at the same viewports;
- no horizontal overflow is introduced;
- exact-head tests/build are green.

## Target reference / mock
Keep the existing hero layout and typography unchanged.

Target sentence:
> DigitalCrown centralise patients, agenda, facturation et dossiers cliniques dans une interface moderne conçue pour les dentistes marocains.

No other visual or interaction change is intended.

## Visual evidence
Shared deterministic workflow:
- `.github/workflows/v1-07-truth-safety-visual-evidence.yml`

Scenario:
- `landing-geography`

Matched viewports:
- 390 × 844
- 768 × 1024
- 1440 × 1000

True BEFORE must come from the PR base SHA using the audit-only harness.
AFTER must come from exact PR HEAD.
