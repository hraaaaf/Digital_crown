# LOT08 Tweed Facad gap resolution — Wits and OL/FH

Status: **SOURCE-LOCKED — RUNTIME GATED**

Date: 2026-10-07

## Direct Facad observations

`Tweed.cph` ships both `Wits` and `OL/FH`, but vendor-profile membership is not treated as historical Tweed authorship.

- `Wits`: `ProjLine(OL, B, A)`, norm `0-4`.
- `OL/FH`: `Angle2ln(FH, OL)`, norm `8-12`.
- `FH`: `Line(P, Or)` where Facad documents `P = Porion`, `Or = Orbitale`.
- `OL`: `Line(OLp, OLa)`.
- `OLa`: constructed `Mid-point(Is, Ii)` — midpoint of upper/lower incisor tips.
- `OLp`: manual marker, documented by Facad as `Occlusal Line, posterior point`.

Evidence:
- geometry probe run `37613466736`, artifact `11479156059`, digest `sha256:0c38c1a672a6865431e48454b9ad04afc7ad22c0f5072ec858a3b2222529d555`;
- endpoint probe run `37613642979`, artifact `11479441309`, digest `sha256:bbf9828bc5a42aefd61995ac9c51a9fc9b95190a4de77cfd94f59abd8810d327`.

Facad Reference Manual semantics: `ProjLine` projects the distance between two markers onto a named line; `Angle2ln` measures the angle between two named lines.

## Wits authority boundary

Primary authority is Jacobson 1975, DOI `10.1016/0002-9416(75)90065-2`. Jacobson's Wits appraises AP jaw discrepancy by projecting A and B to the occlusal plane and measuring AO-BO along that plane.

Independent peer-reviewed descriptions of the original/functional Wits plane use posterior premolar/molar occlusion. Facad's shipped `Tweed.cph` instead defines its `OL` with an anterior midpoint between the upper/lower incisor tips and a manual posterior point.

Therefore Facad's row is frozen as a **vendor compatibility variant**, not strict Jacobson parity:

`M_FACAD_TWEED_WITS_BISECTED_OL_MM_V1`

Digital Crown's old `Wits_Appraisal` entry remains quarantined and must not be silently reused: its `Occ_Ant`/`Occ_Post` provenance was never source-locked.

## OL/FH authority boundary

`OL/FH` uses Facad `FH = P-Or` and the same vendor `OL = OLp-OLa`.

Downs 1948 is the primary historical authority for the cant of the occlusal plane to Frankfort. Independent descriptions of Downs use a bisected occlusal plane involving incisal overbite and posterior occlusion. Facad's anterior midpoint is explicit, but `OLp` is only a manual posterior occlusal marker in the CPH/guide evidence inspected here.

Therefore the Facad row is source-locked as a vendor compatibility measurement, but **strict Downs equivalence remains unproven**:

`M_FACAD_TWEED_OL_FH_DEG_V1`

## Tweed profile boundary

Digital Crown's source-locked Tweed core remains the diagnostic triangle: FMA, IMPA, FMIA. Merrifield Z is a separate extension. `Wits` and `OL/FH` are Facad vendor-profile extensions only; this work does not add them to historical Tweed membership.

## Runtime gate

Before either Facad-compatible row can execute:

1. explicit manual/source-bound `OLp_Facad_Tweed` must exist;
2. `OLa` must be built from exact `U1_incisal` and `L1_incisal` identities;
3. no alias to legacy `Occ_Ant`/`Occ_Post`;
4. Frankfort must bind to explicit `Po_anatomic` + `Or`; no ear-rod substitution;
5. same-trace Facad numeric parity must be tested before claiming parity;
6. Facad vendor reference ranges must not become runtime classification authority.

## Scientific classification

- `Wits`: `FACAD_VENDOR_VARIANT_SOURCE_LOCKED__JACOBSON_STRICT_EQUIVALENCE_FORBIDDEN`.
- `OL/FH`: `FACAD_VENDOR_OCCLUSAL_CANT_SOURCE_LOCKED__DOWNS_STRICT_EQUIVALENCE_UNPROVEN`.
- Both: no runtime activation in this lot.