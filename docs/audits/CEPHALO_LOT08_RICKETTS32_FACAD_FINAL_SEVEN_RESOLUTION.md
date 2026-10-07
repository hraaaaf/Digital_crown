# Ricketts 32F — final seven-gap Facad compatibility resolution

Status: SOURCE_LOCKED — RUNTIME GATED

Scope: `Xi-OL`, `Xi-PM/OL`, `Upper lip len`, `STi-OL`, `Facial cone angle`, `Mand arc`, `Mand len`.

## Direct Facad evidence

Official Facad 3.14.1.1111 profile `Ricketts (32 F).cph`.
SHA-256: `d0b442b39ac7db3dc9c46d807cb3c20bd937c69783b096b484872017f9376518`.

Observed rows:
- Xi-OL — `DistLine(OL, Xi)`, norm `-3.5±3`, `changeSign=true`, `changeRightLeft=true`.
- Xi-PM/OL — `Angle4p(OLa, OLp, PM, Xi)`, norm `26±4`.
- Upper lip len — `Dist2p(ANS, STs)`, norm `24±2`.
- STi-OL — `DistLine(OL, STi)`, norm `-3±2`, `changeRightLeft=true`.
- Facial cone angle — `Angle4p(Go, Me, N, Pog)`, norm `68±3`.
- Mand arc — `Angle4p(Xi, PM, DC, Xi)`, norm `30±4`.
- Mand len — `Dist2p(Xi, PM')`, norm `78±2.5`.

Observed constructions/markers:
- `OLa = Mid-point(Is, Ii)`.
- `OL = Line(OLp, OLa)`; `OLp` longname = “Occlusal Line, posterior point”.
- `PM'` = intersection of `Xi-PM` and `A-Pog`.
- `STs` = Stomion superior; `STi` = Stomion inferior.
- `DC` = “Centre of condyle”.
- `Go` = generic Gonion.
- `PM` = Protuberance Menti / Suprapogonion.

## Digital Crown decisions

### Xi-OL
Vendor occlusal-line variant. Facad OL is not the source-locked Ricketts functional occlusal plane. Direct alias to `M_RICKETTS_OCCLUSAL_PLANE_XI_MM_V1` is forbidden; signed parity remains gated.

### Xi-PM/OL
Vendor OL versus PM-Xi. DC requires the source-locked functional occlusal plane, canonical Xi and manual `Pm_Ricketts`. Direct alias forbidden.

### Upper lip len
Hard landmark mismatch. Facad measures ANS→STs (Stomion superior). Atlas/DC requires ANS→manual labial commissure and explicitly rejects Stomion substitution.

### STi-OL
Dual mismatch. Facad uses Stomion inferior against vendor OL; Atlas/DC uses labial commissure against the source-locked functional occlusal plane.

### Facial cone angle
Vendor mandibular-plane variant. Facad uses generic Go-Me vs N-Pog. DC requires `MP_ANGLE_INFERIOR_Ricketts→Me`; generic Go-Me substitution is forbidden.

### Mand arc
Same geometric line family only. Facad uses PM-Xi and DC-Xi, but its DC marker is merely “Centre of condyle” and PM/Xi are vendor identities. DC requires manual `DC_Ricketts` with condylar-neck bisection semantics, canonical Xi and manual `Pm_Ricketts`. Presentation parity remains gated.

### Mand len
Hard endpoint mismatch. Facad measures Xi→PM', with PM' constructed as the Xi-PM / A-Pog intersection. DC corpus length is Xi→manual Pm directly. No alias.

## Result

All 26 originally unmapped Facad Ricketts 32F rows now have an explicit compatibility disposition. This does **not** mean 26 runtime aliases:
- vendor variants remain variants;
- source-specific landmark authority stays enforced;
- norms remain non-authoritative;
- numeric/sign/presentation parity stays gated where not directly proven.

No runtime activation. No clinical interpretation activation. No merge/deployment authorization.
