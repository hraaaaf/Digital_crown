# Cephalo LOT06 — canonical landmark identity bridge

Status: IMPLEMENTATION CANDIDATE — fail-closed

## Decision

Persisted legacy IDs `Po`, `Co`, `Gn`, `Pog` are not renamed.

For new scientific consumers, LOT06 may expose additive identities:

- `Po → Po_anatomic`
- `Co → Co_anatomic`
- `Gn → Gn_anatomic`
- `Pog → Pog_hard`

only when the point is produced by the exact certified SRPose38 model/pipeline, or
when a manual revision has a previous certified SRPose38 observation of the same
legacy point.

## Evidence boundary

The SRPose38/DC contract fixes the channel names and Digital Crown mapping.
Peer-reviewed cephalometric landmark literature independently defines:

- Porion as the superior/upper margin of the external auditory meatus;
- Condylion as the posterosuperior point of the mandibular condyle;
- Gnathion as an anteroinferior/midpoint bony-chin landmark depending on the
  operational atlas, which must remain anatomic and never be substituted for a
  constructed Gn;
- Pogonion as the most anterior point of the bony chin/symphysis.

Therefore this bridge binds identity class only. It does not authorize a machine
porion, constructed Gn, soft-tissue Pog, or any analysis-specific alternative.

## Compatibility

Historical records retain their original IDs. A generic legacy point with no
certified provenance remains generic and cannot satisfy a canonical consumer.

This bridge is additive evidence projection, not data migration.
