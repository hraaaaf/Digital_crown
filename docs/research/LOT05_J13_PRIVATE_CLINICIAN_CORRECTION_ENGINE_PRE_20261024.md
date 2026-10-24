# Digital Crown LOT05/J13 — PRE: private FDI correction engine + public-safe GitHub Actions

**2026-10-24.** Research-only on PR #1032 (DRAFT). Academic AKUDENTAL source pinned at \`92e2cc3ae5eebc9de509311a3edefb7106fca7dd\` (333 YOLO TXT records). The university source declares CC BY-NC-SA 4.0. Neither commercial rights nor independent patients nor clinical safety are demonstrated.

## Human source of truth and privacy boundary

The orthodontist gave **28/28 targeted panoramic verdicts** (not an exhaustive annotation audit) and **6/6 similarity pair visual verdicts**, all pairs considered different patients by visual assessment only. The explicit correction ledger has **19 precise FDI class changes over 17 cases**, **one exact duplicate-record deletion after verification**, and **ten cases blocked** (nine with no replacement FDI and one with ambiguously repeated boxes). The true identities of patients or examinations and independence of all train/val/test samples remain unproven.

**The GitHub repository is public.** Its code and Actions must not include the clinician's **individual image identifiers, per-image FDI decisions, bounding boxes, media or hashes**. Those are held in an **owner-private manifest outside this public repository** (not in a CI secret, logs, PR comments, Notion copy or artifact). Never upload the map.

## Scope of the implementation

\`experiments/lot05_j13_private_clinician_corrections.py\` implements two explicitly separated modes.

**Public-safe preflight, GitHub Actions:** runs **14 synthetic tests** (specific row selection, source preservation, exact duplication, valid 32-class ontology, fail-closed on missing/altered box or collisions, filesystem protection) and downloads **TXT annotations only**, at the pinned SHA in an ephemeral checkout. Requires 333 files/28 flagged/31 repeated labels/**one** exact duplicate pair; publishes **aggregate counts only**, deletes all academic temporary source labels, never uploads an artifact. The CLI rejects private manifests when \`GITHUB_ACTIONS=true\`. A green workflow **does not mean real clinical corrections have been applied**.

**Owner-private local staging:** outside GitHub/Notion, with an authorized local academic label source and the distinct **private clinician verdict manifest**. The manifest requires 19 exact changes, ten unresolved cases and one deduplication instruction. Exact normalized YOLO bounding boxes plus their original class serve as identity witnesses. Every proposed destination FDI is checked against *all labels on the same image*, not just the flagged source class: **if destination class already exists, no silent duplication is allowed**. If a source box cannot be uniquely recovered, stop. First run performs read-only aggregate private QA; optional separate \`--stage-private\` creates a brand-new owner-private 333-TXT candidate directory with source files untouched. If any requested destination collision remains, private staging blocks instead of producing a false 'clean' dataset. Files use directory 0700 / file 0600; output in a Git worktree is forbidden.

**Example for an authorized local workstation only:**

\`\`\`sh
python experiments/lot05_j13_private_clinician_corrections.py \
  --labels-dir /private/academic-333-labels \
  --private-manifest /private/clinician-review.json

# Only after preflight reports ZERO conflicts:
python experiments/lot05_j13_private_clinician_corrections.py \
  --labels-dir /private/academic-333-labels \
  --private-manifest /private/clinician-review.json \
  --stage-private /private/lot05-j13-candidate-output
\`\`\`

The candidate remains **partially adjudicated** because ten decisions are unresolved. It is neither clinical ground truth validated for every tooth, nor a cleared commercial training dataset. No automated training, patient data transfer, clinical activation, merge, Vercel, or Production change.

## Follow-up gates

1. Verify the real nineteen target-label collisions and remaining ten decisions privately before source-level modifications.
2. Resolve publisher/clinical provenance, source rights, patient group identifiers and independently held-out external blind test.
3. Only after these gates consider an experimental re-training with a new research-only evaluation; never mistake unit tests or six visually different pairs for a clinical validation.
