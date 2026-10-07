# LOT08 Steiner Facad gap resolution — S-line and derived Ii/Pog relation

Status: **SOURCE-LOCKED — RUNTIME ACTIVATION GATED**

Date: 2026-10-07

## Goal / success / proof

**Goal** — resolve the three Facad `Steiner.cph` rows that remained unmapped after the conservative Facad → Digital Crown inventory: `Ii-Pog // NB`, `Ls-SL`, and `Li-SL`.

**Success** — distinguish derived arithmetic from new geometry, source-lock the S-line endpoints, and forbid any silent alias from Facad's Steiner S-point to a Digital Crown landmark whose identity is not proven.

**Proof** — official Facad 3.14.1.1111 CPH probes plus the Digital Crown landmark contract and independent peer-reviewed descriptions of Steiner's S-line.

## Direct Facad observations

Official Facad `Steiner.cph` exposes:

- `Ii-Pog // NB`: `calc_type=Sub`, operands `Ii-NB` and `Pog-NB`, norm `0±2`.
- `Ls-SL`: `calc_type=DistLine`, references `SL` and `Ls`, norm `0`.
- `Li-SL`: `calc_type=DistLine`, references `SL` and `Li`, norm `0`.
- `SL`: `calc_type=Line`, endpoints `PGs` and `MS`.
- `PGs`: `Soft tissue Pogonion`.
- `MS`: `Steiner's S-point (columnella tangent point)`.

Evidence:
- gap probe run `37602332789`, artifact `11473615833`, digest `sha256:35201612eeb1fd6a90a174fe73a33b676a9d531d7ce1019967cd1c88ab2f5bad`.
- S-line endpoint probe run `37602712135`, artifact `11474115025`, digest `sha256:f48cbf19f435674b2e455de2e4fae69fdd2d43481ce03cd5e516cdd99141ab95`.

## Independent scientific support

Peer-reviewed descriptions converge on the S-line as a line from the soft-tissue pogonion to a columellar Steiner point, commonly described as the midpoint of the columella or the midpoint/inflection of the S-shaped nasal-columellar contour.

Official vendor landmark source: Facad 3.12 User Guide (`https://www.facad.com/dox/dox312/FacadUsersGuide_ENG.pdf`) defines `MS`, `PGs`, `Iil`, and `Ii` explicitly.\n\nSupporting independent sources:
- `PMC6066709` — upper/lower lip to Steiner S-line; line described as pogonion to columella.
- `PMC13526246` — S-line joins midpoint of columella to soft-tissue pogonion.
- `PMC4520143` — S-line drawn from soft-tissue pogonion to midpoint of nasal columella.
- `PMC8919757` — Steiner S1-line from soft-tissue pogonion to columella of the nose.

These sources support the line family and endpoint concept. They do **not** prove that Digital Crown's local `Cm` detector output is the exact Steiner S-point.

## MS identity decision

Digital Crown currently exposes local ID `Cm` / “Columella”, but the landmark source-lock explicitly classifies legacy automatic landmark mappings as `LEGACY_AUTO_UNVERIFIED` and states that name resemblance does not grant clinical authority.

Therefore:

- Facad's endpoint is frozen as `MS_STEINER_FACAD_TANGENT_POINT_V1`, a vendor-specific scientific identity.
- `Cm -> MS_STEINER_FACAD_TANGENT_POINT_V1` alias is **FORBIDDEN unless exact equivalence is independently proven**.
- `Sn_soft -> MS_STEINER_FACAD_TANGENT_POINT_V1` is forbidden.
- `Prn -> MS_STEINER_FACAD_TANGENT_POINT_V1` is forbidden.
- acquisition must be explicit manual placement or a separately source-locked construction/detector.
- missing `MS_STEINER_FACAD_TANGENT_POINT_V1` must fail closed.

This is additionally supported by contemporary landmark literature where `Cm` may denote an anterior-inferior columellar point used for the nasolabial angle, which is not definitionally identical to the Steiner midpoint/tangent point.

## Canonical construction target

Future geometry may use:

`SL_STEINER_POGSOFT_MS_V1 = infinite line(Pog_soft, MS_STEINER_FACAD_TANGENT_POINT_V1)`

No runtime activation is authorized by this document.

## Gap resolutions

### Ii-Pog // NB

Classification: **DERIVED RELATION — NO NEW GEOMETRY**.

Facad directly encodes subtraction of `Ii-NB` and `Pog-NB`. Digital Crown has candidate inputs `M_L1_NB_MM_V1` and `M_POG_NB_MM_V1`.

Facad's official 3.12 landmark guide defines `Iil` as the lower-incisor labial outline. This is semantically compatible with Digital Crown's explicit `L1_facial_surface` dependency, but direct same-trace numeric equivalence is still required before claiming Facad parity. No new standalone geometry is required.

### Ls-SL

Classification: **MEASUREMENT DEFINITION PROVEN; RUNTIME BLOCKED BY EXPLICIT MS**.

Required identities: `Ls_soft`, `Pog_soft`, `MS_STEINER_FACAD_TANGENT_POINT_V1`.
Required construction: `SL_STEINER_POGSOFT_MS_V1`.
Operation: perpendicular distance from upper lip to S-line.

Facad runtime sign convention is not yet observed on a same-trace patient export. Do not claim signed numeric parity.

### Li-SL

Classification: **MEASUREMENT DEFINITION PROVEN; RUNTIME BLOCKED BY EXPLICIT MS**.

Required identities: `Li_soft`, `Pog_soft`, `MS_STEINER_FACAD_TANGENT_POINT_V1`.
Required construction: `SL_STEINER_POGSOFT_MS_V1`.
Operation: perpendicular distance from lower lip to S-line.

Facad runtime sign convention is not yet observed on a same-trace patient export. Do not claim signed numeric parity.

## Norm policy

The Facad values `0` and `0±2` are observed vendor profile references, not universal Digital Crown normative authority. They remain reference/provenance data only until population/applicability is separately validated.

## Runtime safety gate

Before implementation/promotion:

1. explicit `MS_Steiner` acquisition path;
2. no silent alias to `Cm`, `Sn_soft`, or `Prn`;
3. dependency geometry of `Ii-NB` confirmed;
4. signed-distance convention defined for DC and direct Facad numeric parity kept separate;
5. fail-closed tests for missing `MS_Steiner`;
6. no norm-based classification without a dedicated normative gate.


## Historical attribution boundary

This compatibility lot does not source-lock the exact original Steiner publication/version that first introduced the soft-tissue S-line. Therefore the Facad S-line rows are **not** promoted into the canonical historical `STEINER_STATIC_PROTOCOL_PROFILE_V1` by this work.

Allowed claim: Facad's shipped Steiner profile defines these rows and their geometry as documented above, with independent scientific literature supporting the S-line concept.

Forbidden claim until a primary historical source is locked: that `Ls-SL` / `Li-SL` belong to a specific Steiner 1953/1959 canonical layer.


## Variant-equivalence warning

The Facad vendor definition is specifically a **columella tangent point**. Independent literature uses several descriptions for the Steiner endpoint, including the midpoint of the columella and the midpoint/inflection of the S-shaped curve between the nasal base and tip. This lot does not prove those constructions are identical.

Therefore the vendor tangent-point identity must not be silently replaced by a midpoint, inflection point, generic `Cm`, `Sn_soft`, or `Prn`. Historical/vendor variant equivalence remains `UNPROVEN`.
