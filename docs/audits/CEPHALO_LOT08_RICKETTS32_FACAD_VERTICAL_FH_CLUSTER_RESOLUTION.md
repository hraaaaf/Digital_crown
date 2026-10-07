# Ricketts 32F — Facad vertical / Frankfort cluster resolution

Status: SOURCE_LOCKED — RUNTIME GATED

Scope: `LFH`, `Max depth`, `Max hgh`, `NL/FH`, `CBL/FH`.

## Direct Facad evidence

Official Facad 3.14.1.1111 profile `Ricketts (32 F).cph`:
SHA-256 `d0b442b39ac7db3dc9c46d807cb3c20bd937c69783b096b484872017f9376518`.

Observed definitions:
- LFH — `Angle3p(Xi, ANS, PM)`, norm `47±4`.
- Max depth — `Angle4p(A, N, P, Or)`, norm `90±3`.
- Max hgh — `Angle3p(CF, N, A)`, norm `56±3`.
- NL/FH — `Angle2ln(FH, NL)`, norm `1±3.5`.
- CBL/FH — `Angle4p(N, Ba, Or, P)`, norm `27±3`.

Observed constructions:
- `FH = Line(P, Or)`; P = Porion, Or = Orbitale.
- `NL = Line(PNS, ANS)`.
- `PtV = Normal(FH, Pt)`.
- `CF = Inter2ln(FH, PtV)`.
- `Xi` is the intersection of the two ramal-rectangle diagonals assembled from R1/R2 lines parallel to PtV and R3/R4 lines parallel to FH.

The Facad Reference Manual defines `Angle3p` with the first marker as the center/apex. Therefore `LFH = Angle3p(Xi, ANS, PM)` is the ANS-Xi-PM angle with vertex Xi.

## Digital Crown decisions

### LFH
Same canonical geometry family as `M_ORAL_GNOMON_ANS_XI_PM_DEG_V1`.
No direct alias until same-trace numeric/display parity is observed.

### Max depth
Same anatomical line family as `M_RICKETTS_MAXILLARY_DEPTH_NA_FH_DEG_V1`: N-A vs anatomical FH P-Or.
No direct alias until Facad Angle4p presentation parity is observed.

### Max hgh
Same N-CF-A geometry family as `M_RICKETTS_MAXILLARY_HEIGHT_NCFA_DEG_V1`, but strict CF identity remains gated.
Facad CF is built from a Pt-based PTV; the inspected CPH identifies Pt as “Pterygo-maxillary fissure; Foramen rotundum”. That is insufficient by itself to prove exact identity with DC `PR_Ricketts_PTV`.

### NL/FH
Same FH and palatal-line anatomy as `M_RICKETTS_PALATAL_PLANE_FH_DEG_V1`.
DC uses a directional signed convention tied to versioned image-orientation evidence, so sign parity is not inferred from Facad Angle2ln.

### CBL/FH
Same anatomical line family as `M_RICKETTS_CRANIAL_DEFLECTION_FH_BAN_DEG_V1`.
Facad uses N→Ba and Or→P; DC uses Ba→N and P→Or and reports an acute non-oriented angle. Reversing both lines preserves the line geometry, but exact vendor presentation still requires same-trace proof.

## Safety boundary

No runtime activation.
No Facad norm becomes classification authority.
No direct alias based on label alone.
No signed/oriented equivalence without evidence.
Maxillary-height CF/PTV anchor identity remains explicit.
