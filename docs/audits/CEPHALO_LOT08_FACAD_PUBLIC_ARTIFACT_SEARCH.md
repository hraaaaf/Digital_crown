# LOT08 — Facad Ricketts 32F/13F Public Artifact Search

Date: 2026-10-06  
Branch: `feat/ortho-studio-lot08-ricketts-protocol-v2`

## Goal

Determine whether public web archives, Facad documentation, or GitHub expose direct artifacts sufficient to observe the exact composition of Facad's standard analyses `Ricketts (32 F)` and `Ricketts (13 F)`.

## Verified direct vendor evidence

### Facad 3.12 release notes
Official Facad release notes state that version 3.12 added:
- `Ricketts (32 F)` — a 32 factor Ricketts analysis attributed to Fernández Sánchez & Da Silva Filho, *Atlas Cefalometría y Análisis Facial* (2009).
- `Ricketts (13 F)` — a simplified 13 factor Ricketts analysis attributed to the same Atlas.

This proves vendor labels and attribution only. It does not expose the exact row membership.

Source:
https://www.facad.com/dox/dox312/FacadTracingReleaseNotes_3.12.pdf

## Verified export surfaces by version

### Facad 3.8
Official manual exposes:
- `Cephalometry > Export > Analysis Values`
- `Cephalometry > Export > Analysis Properties`
- `Cephalometry > Export > Marker Positions`

Source:
https://www.facad.com/dox/dox38/FacadTracingRefMan.pdf

### Facad 3.13
Official manual still exposes:
- `Analysis Values`
- `Analysis Properties`
- `Marker Positions`

Source:
https://www.facad.com/dox/dox313/FacadTracingRefMan.pdf

### Facad 3.14
Official manual exposes:
- `Cephalometry > Export > Analysis Values`
- `Cephalometry > Export > Analysis Properties`
- `Cephalometry > Export > Object Values`
- `Cephalometry > Export > Object Properties`

`Object Values` includes all placed graphic objects, marker positions, and planned movements. It replaces the older export surface needed for marker-position evidence.

Source:
https://www.facad.com/dox/dox314/FacadRefMan.pdf

## Public artifact search

Searches covered:
- exact vendor labels `Ricketts (32 F)` and `Ricketts (13 F)`;
- Facad + Ricketts + TXT/XML;
- Facad + Analysis Values / Analysis Properties / Marker Positions / Object Values;
- public GitHub code search for Facad/Ricketts combinations;
- old Facad download/release/manual pages.

### Result
No publicly indexed Facad TXT/XML export, standard-analysis definition file, local-analysis file, or source/configuration artifact was found that directly reveals the exact 32F or 13F row membership.

GitHub exact-term searches returned only unrelated false positives. This is negative search evidence, not proof that no such artifact exists anywhere.

## Scientific discrepancy retained

Facad labels the reduced profile `Ricketts (13 F)` and attributes it to the 2009 Atlas. Public descriptions of the Atlas identify a `12-factor` simplified analysis. Therefore:
- Facad 13F must not be equated automatically with Atlas 12;
- Facad 13F must not be equated automatically with Gregoret-lineage 13;
- exact Facad 13F membership remains `UNOBSERVED`.

The 32F vendor label is closer to publicly described 32-factor implementations, but without a direct Facad definition/export it remains a compatibility target, not a proven Facad row lock.

## Evidence classification

- Facad 32F existence/name/source attribution: VERIFIED.
- Facad 13F existence/name/source attribution: VERIFIED.
- Export mechanisms: VERIFIED and version-sensitive.
- Exact 32F Facad membership: UNOBSERVED.
- Exact 13F Facad membership: UNOBSERVED.
- Exact signs/order/norms/rounding as emitted by Facad: UNOBSERVED.

## Next exact

Preferred proof path:
1. obtain a Facad 3.12–3.14 installation or 30-day trial;
2. load the standard `Ricketts (32 F)` analysis on one lateral tracing;
3. export Analysis Values + Analysis Properties + marker/object positions;
4. switch the same tracing to `Ricketts (13 F)`;
5. repeat the exports;
6. hash and ingest the six direct artifacts through the LOT08 evidence validator.

Until then, no Facad parity claim is allowed.
