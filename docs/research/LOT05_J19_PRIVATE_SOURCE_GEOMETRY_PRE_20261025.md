# LOT05/J19 — J16 private source geometry preflight (PRE)

Adds a versioned **read-only** bridge from the J16 private manifest to the existing J13 source inventory, geometry witness locator and target-class collision checks. Uses J17 schema/ontology and optional V22 hash integrity gate. Reports only aggregate totals; refuses public CI private inputs; never calls stage_private, modifies labels, logs identifiers or exports corrected datasets.

Public CI exercises four fully synthetic tests. The real owner-private 333 source TXT labels are not in the local workspace, so **real J19 source geometry and collision QA is NOT executed or validated**. One clinical collision and one duplicate-deletion review remain blocked, as do the two primary-tooth decisions. Real source QA, clinician adjudication, commercial license and patient independence are separate gates. PR remains DRAFT; no merge, training, or deployment.

Private owner-only invocation: `python experiments/lot05_j19_private_source_geometry_preflight.py /private/J16.json /private/academic_labels /private/V22.json`.
