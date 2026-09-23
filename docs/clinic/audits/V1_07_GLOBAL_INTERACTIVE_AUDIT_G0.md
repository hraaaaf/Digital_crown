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

## Inventory Factory result — run #35449765657

Exact scanned HEAD: `de4656abb7c29e53108be6b691ebfff2aefb94b2`.

- workflow: **SUCCESS**
- artifact: `g0-global-interactive-inventory`
- artifact ID: `10585779417`
- artifact digest: `sha256:29bcba6ed70f736285dff35856d002d47cab77f568547d2e33fc8bbc84d2c33c`
- source files scanned: **418**
- route declarations: **40**
- unique explicit route paths: **38**
- raw static interaction/action signals: **3653**
- literal JSX `<button>` elements: **1035**
- `<select>` elements: **86**
- React `Link/NavLink` elements: **57**
- forms: **28**
- existing test files discovered: **195**

These figures are machine evidence, **not yet the final semantic denominator**. Shared components can render multiple distinct controls at runtime (for example one `NavItem` implementation rendered for many sidebar destinations), while a single JSX button may emit several overlapping static signals. G0 therefore requires a runtime rendered-control pass before denominator freeze.

## Final-factory hardening after initial run
The initial successful run above is historical evidence only and **does not freeze G0**. Before the final rerun, the factory was broadened to avoid silent omissions:
- generic native `<input>` controls (not only input buttons);
- plain HTML `<a>` anchors;
- native `<summary>`, `contentEditable`, keyboard actions and common custom-control roles/components;
- root/wildcard shell routes explicitly classified under G1 instead of falling through to G8 review.

These additions may increase raw signal counts. That increase is expected and is **not** a regression or a coverage percentage; only G9 semantic adjudication can freeze the denominator.
