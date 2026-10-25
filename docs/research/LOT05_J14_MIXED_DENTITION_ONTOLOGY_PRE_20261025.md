# LOT05/J14 — Mixed-dentition ontology gate (PRE, 2026-10-25)

**Research-only. Public-safe synthetic tests. No original images or sample-specific clinical decisions committed to this public repository.**

## Purpose and boundary

The source AKUDENTAL model maps only 32 permanent teeth (quadrants 1–4; tooth positions 1–8). The FDI notation ALSO has 20 valid primary-tooth codes (quadrants 5–8; tooth positions 1–5). In particular, **53** and **63** are both primary canines; these must NEVER be silently reinterpreted as permanent FDI 13 or 23.

A clinician's tentative identification is not confirmed ground truth. Public-safe synthetic scenarios validate that both **primary** and **tentative** classifications block automatic training/staging in the legacy FDI32 ontology. A permanent confirmed class passes only this narrow gate and still requires owner-private bbox, duplicate and collision QA; the gate never certifies any image.

## Implementation

- `experiments/lot05_j14_mixed_dentition_ontology_gate.py` gives strict ASCII FDI parsing, `confirmed / tentative / unresolved` certainty, and explicit fail-closed classification.
- `experiments/test_lot05_j14_mixed_dentition_ontology_gate.py` contains **13 synthetic tests**, no patient information, JPEGs, private manifests, bounding-box data or source image IDs.
- Tests run in the existing experimental J13 public-safe Actions workflow, in addition to its 15 existing synthetic tests and pinned 333-label text-only source census.
- Owner-private record V22, with 33 active permanent relabel candidates, 1 confirmed deciduous tooth outside the class map, and 1 tentatively identified deciduous tooth, remains OUTSIDE public GitHub/Notion/Actions.
- This J14 guard is a standalone prerequisite for eventual integration into private staging; it does NOT upgrade model outputs to 52 classes, does NOT apply private decisions, and does NOT remove clinical uncertainty.

## Unresolved gates

Clinical confirmation of the tentative primary/permanent distinction on the authentic university radiograph; decision on mixed-dentition training ontology and data rights; compatibility of private manifest schema with staging; patient-independent splits, external blind evaluation, publisher licensing for commercial use. No merge, Vercel/Production deploy, training run, or clinical activation.
