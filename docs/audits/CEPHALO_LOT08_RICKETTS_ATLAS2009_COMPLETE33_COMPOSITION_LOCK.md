# LOT08 — Ricketts Atlas 2009 complete 33 composition lock

Date: 2026-10-06
Protocol: `RICKETTS_ATLAS_2009_COMPLETE_33_PROTOCOL_V1`

## Authority

Fernández Sánchez J, Da Silva Filho OG. *Atlas cefalometría y análisis facial*. Ripano, Madrid, 2009. ISBN 978-84-936756-7-7. Chapter 13, `Cuadro 13.1 — Descripción de los 33 factores`.

Bibliographic identity is independently corroborated by library catalogues and WorldCat.

## Exact recovered 33-factor composition

Field I — dental/occlusal:
1. Molar relationship.
2. Canine relationship.
3. Horizontal incisor overjet.
4. Vertical incisor overbite.
5. Lower-incisor extrusion.
6. Interincisal angle.

Field II — maxillomandibular:
7. Point-A convexity.
8. Lower facial height.

Field III — dentoskeletal:
9. Upper first molar position.
10. Lower-incisor protrusion.
11. Upper-incisor protrusion.
12. Lower-incisor inclination.
13. Upper-incisor inclination.
14. Occlusal-plane to Xi distance.
15. Occlusal-plane inclination.

Field IV — esthetic:
16. Lip protrusion.
17. Upper-lip length.
18. Labial commissure / occlusal-plane distance.

Field V — craniofacial:
19. Facial depth.
20. Facial-axis angle.
21. Facial-taper/cone angle.
22. Maxillary depth.
23. Maxillary height.
24. Palatal plane.
25. Mandibular plane.

Field VI — internal structures:
26. Cranial deflection.
27. Anterior cranial compression/length.
28. Posterior facial height.
29. **Total facial height** — source-label conflict resolved from the duplicated posterior-facial-height transcription by dimensional consistency and independent Ricketts implementations (`Ba-N / Pm-Xi`, angular).
30. Mandibular ramus position.
31. Porion position.
32. Mandibular arc.
33. Mandibular body length.

## Factor 29 conflict — resolved

The recovered indexed Atlas table duplicates wording equivalent to “posterior facial height” at factor 29 while giving a `60° ± 3°` angular value. Factor 28 is already the linear posterior facial height `Go-CF`.

Independent comprehensive Ricketts implementations identify the `60° ± 3°` angular variable as **Total Facial Height**, defined by `Na-Ba / Pm-Xi`. Digital Crown therefore records factor 29 as `M_RICKETTS_TOTAL_FACIAL_HEIGHT_BAN_XIPM_DEG_V1`.

This is an explicit conflict resolution, not a silent normalization: the duplicated Atlas-index label, unit mismatch, neighboring factor semantics, and independent Ricketts geometry are preserved in the source-lock record.

## Facad boundary

Facad release notes list `Ricketts (32 F)` and `Ricketts (13 F)` and attribute them to the 2009 Atlas. That proves vendor labels and bibliographic attribution only. It does not prove that either Facad target is identical to the Atlas 33-factor composition or to Gregoret 13.

Compatibility targets remain:
- `FACAD_RICKETTS_32F_COMPATIBILITY_TARGET`
- `FACAD_RICKETTS_13F_COMPATIBILITY_TARGET`

Both require direct Facad trace/export observation before parity can be claimed.

## Execution state after Wave A

The composition is source-locked. Runtime implementation remains partial and fail-closed. Historical norms, age/sex corrections, VERT and clinical classifications remain disabled.
