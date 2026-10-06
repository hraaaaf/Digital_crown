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
29. **Source-label conflict quarantined**.
30. Mandibular ramus position.
31. Porion position.
32. Mandibular arc.
33. Mandibular body length.

## Factor 29 conflict

The recovered indexed Atlas table labels factor 29 with wording equivalent to “posterior facial height” while giving a `60° ± 3°` angular value. Independent published Ricketts implementations identify `60° ± 3°` as **Total Facial Height**, whereas factor 28 is the linear posterior facial height.

Digital Crown therefore does not silently normalize row 29. It is represented as:
`SOURCE_LABEL_CONFLICT_BLOCKED`
until the exact printed Atlas page is directly inspected or an equivalent primary reproduction resolves the label.

## Facad boundary

Facad release notes list `Ricketts (32 F)` and `Ricketts (13 F)` and attribute them to the 2009 Atlas. That proves vendor labels and bibliographic attribution only. It does not prove that either Facad target is identical to the Atlas 33-factor composition or to Gregoret 13.

Compatibility targets remain:
- `FACAD_RICKETTS_32F_COMPATIBILITY_TARGET`
- `FACAD_RICKETTS_13F_COMPATIBILITY_TARGET`

Both require direct Facad trace/export observation before parity can be claimed.

## Execution state after Wave A

The composition is source-locked. Runtime implementation remains partial and fail-closed. Historical norms, age/sex corrections, VERT and clinical classifications remain disabled.
