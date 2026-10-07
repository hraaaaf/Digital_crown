# Ricketts 32F — Facad PTV / cranial cluster resolution

Status: SOURCE_LOCKED — RUNTIME GATED

Scope: `Ms-PtV`, `Cranium ant len`, `PFH`, `Ramus Xi pos`, `Porion pos`.

## Direct Facad evidence

Official Facad 3.14.1.1111 profile `Ricketts (32 F).cph`.
SHA-256: `d0b442b39ac7db3dc9c46d807cb3c20bd937c69783b096b484872017f9376518`.

Observed rows:
- Ms-PtV — `ProjLine(FH, Pt, Ms-d)`, norm `19±3`.
- Cranium ant len — `Dist2p(CC, N)`, norm `61±2.5`.
- PFH — `Dist2p(CF, Go)`, norm `63±3.5`.
- Ramus Xi pos — `Angle3p(CF, Xi, P)`, norm `76±3`.
- Porion pos — `DistLine(PtV, P)`, norm `-33.5±2`, `changeRightLeft=true`.

Observed constructions:
- `FH = Line(P, Or)`.
- `PtV = Normal(FH, Pt)`.
- `CF = Inter2ln(FH, PtV)`.
- `CC = Intersect(N, Ba, Pt, Gn)`.
- `Xi = Intersect(R23, R14, R13, R24)`.

Observed marker identities relevant to strictness:
- `Pt` = “Pterygo-maxillary fissure; Foramen rotundum”.
- `Ms-d` = “Molar superior, most distal point”.
- `Go` = generic Gonion.
- `Gn` = direct Gnathion.
- `P` = Porion; `Or` = Orbitale.

## Digital Crown decisions

### Ms-PtV
Vendor variant only. Digital Crown `M_U6_PTV_MM_V1` requires source-specific manual `PR_Ricketts_PTV` and `U6_DISTAL_Ricketts` with Ricketts A6 semantics. Facad `Pt` and generic `Ms-d` cannot be silently aliased.

### Cranium ant len
Geometry family only. Both measure CC-N, but Facad CC uses direct `Pt` + direct `Gn`; Digital Crown Atlas2009 CC uses `Pt_Ricketts` + canonical constructed Ricketts Gn. Direct alias is forbidden until those identities are proven.

### PFH
Geometry family only. Facad uses generic `Go` and vendor `CF`; Digital Crown requires source-specific manual `GO_Ricketts_PFH` and canonical CF built from source-locked PTV.

### Ramus Xi pos
The line family matches FH vs CF-Xi because Facad CF and P both lie on FH. Strict alias remains gated by Facad CF/PTV anchor identity and exact Angle3p presentation parity.

### Porion pos
Geometry family only. Both represent Porion relative to a PTV perpendicular to FH, but Facad PTV is anchored at vendor `Pt`; Digital Crown uses manual `PR_Ricketts_PTV`. Signed parity is also gated.

## Safety boundary

No runtime activation.
No Facad norm becomes classification authority.
No vendor Pt→PR_Ricketts_PTV alias.
No Ms-d→Ricketts A6 alias.
No direct Gn→constructed Gn alias.
No generic Go→GO_Ricketts_PFH alias.
No numeric/sign parity claim without same-trace evidence.
