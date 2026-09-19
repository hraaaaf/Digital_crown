# Digital Crown — V1-07 Global Interactive Audit — G0

Status: **IN PROGRESS / denominator not yet certified**

Exact base at start: `master@87543ccd8515dd9cdee94495dbe7001bce22331d`.

## Goal
Produce the exhaustive, reproducible inventory of V1 interactive surfaces and reconcile every user-visible control against behavioral evidence.

## Success
- every applicable V1 route/surface identified;
- every user-visible control mapped to context/state variants;
- every row mapped to behavioral proof or marked GAP;
- denominator closed before any coverage percentage is declared.

## Proof
The Inventory Factory is executed by `.github/workflows/g0-global-interactive-inventory.yml` using `scripts/inventory_interactive_controls.py`. Its artifact is the raw source inventory. That raw signal count is intentionally **not** treated as the final control denominator.

## Starting facts
- #629 merged.
- current master exact SHA: `87543ccd8515dd9cdee94495dbe7001bce22331d`.
- no post-merge workflow run/status was returned for that merge commit during G0 startup verification.
- V1-08 remains blocked until G10 closeout.
- no Vercel deployment is authorized.

## Reconciliation sequence
1. Generate the source inventory.
2. Review route/surface files and collapse duplicate static signals into one user-visible control row.
3. Add contexts/states for each control.
4. Map existing tests/certifications.
5. Mark uncovered rows as GAP.
6. Assign GAPs to G1→G8.
7. Start the first missing behavior lot immediately.

## Important
Rendering/presence-only tests do not prove the business outcome of a control. Critical mutations require, where applicable, success + refusal/error + non-mutation + double-action protection.
