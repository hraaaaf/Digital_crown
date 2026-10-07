# LOT08 McNamara Facad gap resolution

Status: **SOURCE-LOCKED — RUNTIME GATED**

Date: 2026-10-07

## Result

The six previously unmapped rows from Facad `McNamara.cph` are resolved as either canonical geometry matches or explicit vendor variants. No runtime clinical activation is authorized.

### Canonical geometry matches
- `Max-Mand diff` uses the same subtraction family `Co-Gn - Co-A`, but Facad documents `Co` as **Condyle, posterior point** while Digital Crown `Co_anatomic` is Condylion/posterosuperior. Therefore strict canonical aliasing to `M_CO_GN_MINUS_CO_A_MM_V1` is forbidden until landmark identity is proven.
- `LAFH = ANS-Me` -> `M_ANS_ME_MM_V1`.

### Vendor variants that must not be silently promoted
- `Is-A`: Facad uses `ProjLine(FH, A, Is)` with upper-incisor tip `Is`. Digital Crown's McNamara source-lock requires the upper-incisor facial crown surface for `M_U1_A_VERTICAL_MM_V1`. Strict equivalence is forbidden.
- `Ii to A-Pog`: Facad uses `Dist3p(Pog, A, Ii)` with `changeRightLeft=true`, i.e. lower-incisor tip plus signed/right-left behavior. Digital Crown's McNamara contract requires `L1_facial_surface` for `M_L1_FACIAL_SURFACE_APOG_MM_V1`. Strict equivalence is forbidden.
- `Nasolabial`: Facad uses `Angle3p(SN, MS, Ls)`, where `MS = Steiner's S-point (columnella tangent point)` and `SN = Subnasale; Retronasale`. McNamara literature is described with Prn'/Sn/Ls or tangents to the nasal base and upper lip. This Facad row is a vendor soft-tissue variant and must not alias the quarantined legacy `Angle_Nasolabial`.
- `Ls Cant`: Facad uses the angle between `Line(Ls,N)` and `N-perpendicular`. Independent McNamara-style literature describes upper-lip cant using a tangent to the upper lip versus N-perpendicular. These are not the same geometry.

## Vendor evidence
- gap probe run `37614595578`, artifact `11479502780`, digest `sha256:634861473da5928654b2887c4d3cfc141cd29a26c1b6067b4a4c837ef1c73fb4`.
- soft-tissue dependency probe run `37614708086`, artifact `11479682810`, digest `sha256:68faa24e8e9158dfe3f02d901bd0a541e52a991515f4e3121cf048a92d1f5514`.

## Scientific boundary
- Primary McNamara authority: 1984, DOI `10.1016/S0002-9416(84)90352-X`.
- Modern peer-reviewed parameter reconstruction corroborates McNamara nasolabial `Prn'-Sn-Ls`, Co-A, Co-Gn, ANS-Me, U1-A vertical and L1-A-Pog.
- Independent soft-tissue literature describes upper-lip cant as upper-lip tangent vs N-perpendicular.

## Runtime gates
1. no Facad norm becomes classification authority;
2. no same-trace numeric parity claim without direct Facad export;
3. no incisal-tip vendor variant may alias a McNamara facial-surface measurement;
4. no `Nasolabial` alias to the quarantined legacy field;
5. preserve Facad `changeRightLeft` semantics for `Ii to A-Pog`;
6. no runtime activation in this lot.

## Orientation/sign invariant

The Facad serialized argument order is preserved as evidence:

- `Is-A = ProjLine(FH, A, Is)`; projected displacement order is `A -> Is`.
- `Ii to A-Pog = Dist3p(Pog, A, Ii)` with `changeRightLeft=true`; A-Pog line argument order and target-point identity must not be silently reordered.

These are compatibility invariants only. Same-trace numeric parity remains required before a signed runtime implementation can claim Facad equivalence.


## Adversarial hardening — edge family and Angle3p order

- `Ii to A-Pog` uses the lower incisor tip `Ii`. Digital Crown already has the edge-based geometry family `M_L1_EDGE_APOG_MM_V1`; that family match is now explicit. It still must **not** alias the strict McNamara facial-surface measure `M_L1_FACIAL_SURFACE_APOG_MM_V1`.
- Facad `Angle3p` semantics make the first marker the center/apex. Therefore `Nasolabial = Angle3p(SN, MS, Ls)` is locked as center `SN`, with rays `SN->MS` and `SN->Ls`; positive rotation is clockwise. Reordering these markers is forbidden.
- Same-trace numeric parity remains required before any signed/vendor-compatibility runtime claim.


## Condylar identity split

Facad's official landmark guide defines `Co` as **Condyle, posterior point**. Digital Crown's `Co_anatomic` identity is anatomical Condylion/posterosuperior condylar point. The shared label `Co` and shared subtraction structure are insufficient to establish geometric equivalence.

Therefore `Max-Mand diff` is retained as a vendor formula-family match with strict McNamara/Condylion equivalence unproven; no direct alias is allowed.
