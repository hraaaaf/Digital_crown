# Cephalo 2.0 — LOT06 Scalable Analysis Architecture

Status: IMPLEMENTATION CANDIDATE — gate still open

## Product direction

The engine must be structurally capable of supporting hundreds of analyses without
creating hundreds of independent scientific engines.

The scalability model is:

`analysis pack → canonical measurement IDs → executable measurement contract → landmarks / constructions → versioned geometry implementation`

An analysis pack is therefore data, not a new formula layer.

## Scientific boundary

Architectural capacity for 400+ analysis packs does **not** mean 400 analyses are
scientifically approved. A measurement is selectable only when its LOT06 executable
contract is source-locked and promoted. Blocked or ambiguous measurements remain
fail-closed.

Pack membership is a separate scientific question. The current named packs are
`PROVISIONAL_MEMBERSHIP`: their measurement lists are useful architecture candidates
anchored to LOT01 family contracts, but they are not yet source-locked as exact complete
clinical analysis compositions. LOT08/09 must never infer clinical approval from the
pack label.

## Single dependency authority

`backend/services/cephalo_dependency_graph.py` derives dependencies only from
`cephalo_vnext_lot06_executable_measurement_contract_v1.json`.

The analysis-pack registry stores only canonical measurement IDs. It does not repeat
landmarks, lines, planes, formulas or frontend drawing aliases.

This is the contract LOT07 must consume for Measure ↔ Geometry Focus.

## Current packs

The first registry contains provisional Steiner, Tweed-DC, McNamara, COM and Ricketts
compositions. Each carries explicit LOT01 family contract references and a composition
state.

Ricketts is additionally fail-closed because the currently covered Ricketts measurements
remain blocked by landmark identity or angle-convention debt.

`Tous` is represented as a display preset, not as a new scientific analysis.

## Scale proof

The registry validator is generic and contains no analysis-name switch. A deterministic
test validates a synthetic registry of 401 packs using the same engine path. This proves
composition architecture capacity only; it is not clinical evidence for those synthetic
packs.

## LOT06 gate impact

This removes the need for LOT07 to maintain a parallel scientific
measure→landmark/line mapping. The existing frontend hardcoded mapping remains technical
debt until LOT07 consumes this graph; it must not become the scientific authority.
