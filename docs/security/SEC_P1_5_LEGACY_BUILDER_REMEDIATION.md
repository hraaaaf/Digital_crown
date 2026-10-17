# SEC-P1.5 / SEC-P0 — Legacy executable builder fail-closed remediation

## Threat and exact code finding

On current master, `scripts/build_exe.py` still invokes a separate
PyInstaller build with `backend/main.py` and, if it exists, includes
`backend/core/firebase_creds.json` in the distribution. This can expose
Firebase Admin credentials in a customer executable. The source finding
does **not** establish that any shipped build actually contains a secret.

This PR replaces that obsolete builder with a fail-closed stub. **Both**
direct CLI execution and programmatic `build_executable()` raise before
npm, subprocesses, credential copying, build folder deletion, or filesystem
changes. There is no automatic redirection to another packager.

## Relationship with existing SEC-P0

[SEC-P0 PR #898](https://github.com/hraaaaf/Digital_crown/pull/898)
already proposed the same minimal fail-closed replacement, but remains
OPEN/DRAFT on an old base. This new, **independent** remediation branch is
created from the currently verified master to avoid changing unrelated
experimental branches or rebasing an unreviewed PR behind the user.

These are ALTERNATIVE remediation PRs: **only one** should be considered for
merge, after owner approval, verified HEAD, independent review and normal
required CI. Do not merge both, do not close #898 automatically, and do not
infer that the risk has been removed from master merely because this draft
branch passes.

## Verification

- The exact retired-builder source is the fail-closed implementation already
  studied in #898. Additional regression tests cover `main()`,
  `build_executable()`, direct CLI invocation with isolated working
  directory, unchanged synthetic sentinel file, no build output or frontend,
  static absence of credential copying and shell/subprocess imports.
- Verify the official release guard remains present in
  `DigitalCrown.spec` (installable release certification) and `run.py`
  (identity verification). The tests do **not** create, certify or install
  a commercial executable.
- GitHub Actions tests run on Windows and Linux Python 3.12,
  exact PR SHA, read-only checkout, no patient data/keys/secrets,
  no build tool installed or executed.

## Remaining REQUIRED gates

1. Independent review of the exact implementation and master integration.
2. Verify all other build entrypoints and release artifacts do not bundle
   private service credentials; this test proves only that *this* builder
   can no longer do so.
3. Verify installer build from INSTALLABLE_CERTIFIED attested release with
   correct trusted source, asset inventory, Authenticode, smoke, upgrades,
   patient data continuity and rollback.
4. Explicit owner GO before merge. No deployment or visibility change.

SEC-P1.5 Ed25519 architecture threat review is a **separate stacked
laboratory PR**. No production licence logic is changed here.
