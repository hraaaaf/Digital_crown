# V1-05 / F5 — UI Goal / BEFORE Contract

**Date:** 2026-09-19  
**UI implementation status:** NOT STARTED at capture creation.

## Goal
Add a scientifically neutral superimposition entry point to F3 Longitudinal Compare and a dedicated viewer that lets the practitioner visually compare two canonical lateral cephalograms without automatic clinical interpretation.

## Success
- F3 remains the numerical longitudinal comparator.
- F5 is opened from F3 only when a valid pair can be requested.
- The viewer identifies Tn/date/source unambiguously.
- Overlay controls are limited to source/overlay visibility, opacity and alternation where useful.
- Method/applicability/calibration metadata are visible but secondary.
- Unsupported/ambiguous/growing-patient states fail neutrally and explicitly.
- No progress score, no improvement/aggravation language, no diagnostic arrows, no normative heatmap.
- 390x844, 768x1024 and 1280x900 have no horizontal overflow.
- Mobile uses a true full-screen work surface; desktop uses a large focused overlay rather than squeezing the viewer into the patient card.

## BEFORE
Exact product surface: certified F4 base `20bfe3349399bf49a2f5ece14c5f70526e9d4a1b`, using the already-certified F3 `OrthoLongitudinalComparePanel` before any F5 frontend code. The BEFORE workflow checks out this commit explicitly; it must never capture the evolving F5 HEAD.

Capture workflow:
`.github/workflows/ortho-f5-before.yml`

Viewports:
- 390x844
- 768x1024
- 1280x900

The workflow checks out the exact certified F4 merge, reuses its already-certified F3 capture harness, and records `baselineCommit` plus `productHead` equal to that SHA. This prevents a later F5 CTA/viewer change from contaminating the BEFORE evidence.

## Mockup
Reference: `docs/assets/ortho/f5-superimposition-target.svg`

The mockup is intentionally token-neutral. It defines hierarchy and layout, not new color values.

## Planned hierarchy
1. F3 header + existing evidence/numeric comparison unchanged.
2. Secondary CTA: "Superposition scientifique".
3. Dedicated viewer:
   - header: T0 vs Tn + dates;
   - canvas: source/overlay;
   - controls: opacity, source toggle, alternate;
   - metadata drawer/strip: method version, calibration, applicability;
   - neutral blocked state when F5 cannot compute.
4. Close/back action always reachable.

## Proof required AFTER
- same three viewports;
- viewer opened in capture;
- horizontal overflow false;
- keyboard focus/labels present;
- forbidden clinical interpretation vocabulary absent;
- runtime/console errors empty;
- human visual gate before merge.
