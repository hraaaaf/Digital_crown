# LOT08 — Facad Ricketts 32F dental/occlusal compatibility cluster

Date: 2026-10-07
Status: **SOURCE-LOCKED — RUNTIME GATED**

## Result

Nine previously unmapped rows from the official Facad 3.14.1.1111 `Ricketts (32 F).cph` are dispositioned without activating Facad norms or runtime aliases.

### Vendor occlusal line boundary

Facad defines:
- `OLa = midpoint(Is, Ii)`;
- `OLp = Occlusal Line, posterior point`;
- `OL = Line(OLp, OLa)`.

This is not the Digital Crown source-locked Ricketts functional occlusal plane, which is anchored by explicit premolar/molar occlusion. Therefore `Molar rel`, `Canine rel`, `Overjet`, `Overbite`, and `Ii-OL` are vendor-plane variants and must not alias the canonical FOP measurements.

### A-Pog rows

- `Ii to A-Pog = Dist3p(Pog,A,Ii)` with `changeRightLeft=true` -> same geometry family as `M_L1_EDGE_APOG_MM_V1`, signed parity still gated.
- `Is to A-Pog = Dist3p(Pog,A,Is)` with `changeRightLeft=true` -> same geometry family as `M_RICKETTS_U1_APOG_PROTRUSION_MM_V1`, signed parity still gated.
- `ILi/A-Pog = Angle4p(Pog,A,Iia,Ii)` -> same line family as `M_RICKETTS_L1_APOG_INCLINATION_DEG_V1`, presentation/sign parity still gated.
- `ILs/A-Pog = Angle4p(Isa,Is,A,Pog)` -> same line family as `M_RICKETTS_U1_APOG_INCLINATION_DEG_V1`, presentation/sign parity still gated.

## Evidence

Official Facad payload evidence:
- reverse run `37595714768`;
- artifact `11469783515`;
- artifact digest `sha256:812b39f6effad24cf7e3cd95f71089207da68a594dce5e15a4ba2d7f014c9bd5`;
- `Ricketts (32 F).cph` SHA-256 `d0b442b39ac7db3dc9c46d807cb3c20bd937c69783b096b484872017f9376518`.

Facad Reference Manual 3.13 defines `Dist3p`, `DistLine`, `Angle4p`, `ProjLine`, and `Proj90Line`; same-trace numeric evidence remains required before a signed compatibility claim.

## Safety boundary

No runtime activation. No Facad norm classification. No replacement of the scientific Atlas/Ricketts contracts by vendor profile semantics. Same-trace numeric/sign parity remains required before any direct alias.
