# LOT05/J11D — PRE: autonomous FDI anomaly triage, source pinned

**2026-10-23.** Research-only, PR #1032 DRAFT. User authorized autonomous pre-triage after two orthodontist image-label decisions. Do not require 28 additional image-by-image replies for the *machine* taxonomy; clinical adjudication and correction remain separate gates.

The scope is academic AKUDENTAL pinned SHA 92e2cc3ae5eebc9de509311a3edefb7106fca7dd (333 TXT annotation files, no pixels). Existing J10W established 28 flagged images and 31 duplicate FDI groups, of which one highly overlaps. J11D analyzes group geometry with per-image maxillary/mandibular median vertical positions, cross-arch distances, lateral separation, box overlap, and conflict with other already-labeled regions. Six candidate pair questions remain separate in J11A/J11B: perceptual similarity does not establish same patient.

**Output is ONLY aggregate JSON** (counts across the entire dataset and split, not IDs/filenames/boxes/pixels/hashes). Taxonomy is a screening prioritization, not an anatomical ground truth correction or an exhaustive verification of all radiographs.

Source label corrections: ZERO. Commercial rights (declared CC BY-NC-SA 4.0), patient independence, expert review of remaining cases, clinical release: NOT CLEARED. Human decisions to date: 2/28 on specific regions, 0/6 pairs; those are outside the runner and are not to be faked as CI test results.

A success means machine QA only, not valid FDI class assignments. No merge, deploy, Vercel, Production, or clinical activation.
