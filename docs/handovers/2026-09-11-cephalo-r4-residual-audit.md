# Cephalometry R4 — residual CRANIOM audit

Date: 2026-09-11
Status: ACTIVE AUDIT

## Goal
Close the residual R4 inventory by separating executable CRANIOM variables from scientifically blocked variables. No blocked variable may be approximated with a different landmark, reference frame or protocol.

## Verified active / already implemented
- Situation A / Nasion vertical
- Situation B / Nasion vertical
- A'B' on Frankfort
- Facial depth S / Nasion vertical
- U1 / Frankfort
- L1 / Downs Go-Me, explicitly versioned
- Interincisal U1/L1 long-axis angle, pending PR #413 certification/merge

## Residual source gates

### Overjet / overbite
CRANIOM teaching material explicitly lists both measurements and their sample distributions. General cephalometric literature defines overjet as horizontal incisal separation and overbite as vertical incisal overlap. The current runtime projects the incisal vector on Frankfort and the perpendicular to Frankfort.

Decision: BLOCKED_SOURCE_FRAME.
Reason: the audited CRANIOM sources do not explicitly prove that CRANIOM defines these two distances in the Frankfort/perpendicular frame used by the current runtime. Do not type the runtime implementation as CRANIOM until that frame is source-verified.

### Upper incisal edge / Stomion
CRANIOM material explicitly defines the upper-incisal-edge / Stomion vertical variable.

Decision: BLOCKED_LANDMARK.
Reason: Stomion is absent from the certified SRPose38 runtime landmark vocabulary. No soft-tissue proxy or substitute is allowed.

### SN / mandibular plane
CRANIOM material explicitly lists facial vertical form using S-N and a mandibular plane.

Decision: BLOCKED_CONSTRUCTION_SOURCE.
Reason: the exact mandibular-plane construction for this CRANIOM variable is not sufficiently source-locked in the audited material. Do not silently reuse a Tweed, Steiner or generic Go-Me/Go-Gn plane.

### Ar.Gs / Gi.Me mandibular form
CRANIOM material explicitly lists the mandibular-form variable using Ar.Gs and Gi.Me.

Decision: BLOCKED_LANDMARK.
Reason: Gi and Gs are absent from SRPose38. Ar is not equivalent to Gs; Go is not equivalent to Gi.

### A''B'' horizontal-gaze / NHP
CRANIOM material explicitly distinguishes A''B'' projected on the horizontal gaze plane from A'B' projected on Frankfort.

Decision: BLOCKED_PROTOCOL.
Reason: no certified natural-head-position / horizontal-gaze reference protocol exists in the runtime. A'B' must not be relabeled as A''B''.

## R4 closure condition
R4 can be closed once PR #413 is certified and merged, provided no additional residual variable passes both source and runtime-data gates. The blocked items above remain explicit future prerequisites and are not implementation debt that may be approximated.

## Safety
ZERO LLM. No norms, diagnosis, classification or treatment activation. No Vercel deployment.
