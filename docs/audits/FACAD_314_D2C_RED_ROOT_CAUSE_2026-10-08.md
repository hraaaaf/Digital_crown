# Facad 3.14 — D2C RED analysis and D1B decoupling

**Source run:** [#37854309934](https://github.com/hraaaaf/Digital_crown/actions/runs/37854309934), failed on `f7205131684200dadb750b929221e93ad73f85a5`, artifact #11584160315.

## Observed (not inferred)

- D2C script attempted three enabled View options: **Marker guide**, **Original positions**, **Planned positions**. The UIA `TogglePattern` state is `On` before clicking and `UNKNOWN` after clicking for each; the second click returns `On`. This fails the old `3/3` strict state-transition gate with `0/3` certified, even though no unresolved interaction exception occurred.
- **Independent screenshot verification**: compare 1024×768 captured RGB PNG pairs on the tracing crop x=556..984, y=113..694. Channel-difference threshold greater than 10, full-resolution pixel count:

| View item | BEFORE→AFTER changed pixels | BEFORE→RESTORE changed pixels | Verdict |
|---|---:|---:|---|
| Marker guide | 0 | 0 | UIA attempted; **no visual change demonstrated** in tracing ROI |
| Original positions | 11,548 | 0 | **Visible change/restoration verified**; original tracings appear blue in AFTER |
| Planned positions | 0 | 0 | UIA attempted; **no visual change demonstrated** in tracing ROI |

The cropped output is not a clinical functionality validation. The two no-change entries may affect invisible guides/other portions of the UI; absence of a crop change does not mean feature defect.

- D2C strict state gate stopped execution **before D1B began**. There are no D1B execution artifacts and no evidence of 65 selections from this run.
- The workflow's `finally` did execute: `d3-app-copy-probe.txt` confirms exact original and scratch-file SHA-256 values match before and after the read-only session, **both `UNCHANGED=True`**. Facad shared application persistence remains `UNVERIFIED`, clinical edits still prohibited.

## Exact corrective action

The three D2C View actions are not prerequisites for the *independent, read-only* catalog selection test. A UIA state `UNKNOWN` when an overlay becomes hidden is not a reliable test oracle. Do not weaken the D2C 3/3 gate to claim a full pass. Keep D2C `OPEN` with one documented visual positive and two `NOT_PROVEN` cases.

The new workflow commit `86441906332bff4632ceb25ab74a51788a4fa409` intentionally **skips D2C** and runs the D1B script only, after the known Robert bootstrap, with guaranteed original/copy SHA recording. D1B selects the catalog's 65 Standard lateral entries using UIAutomation `SelectionItemPattern`, screenshots each, **never clicks the Load button**, tests Local tab, explicitly presses Cancel and checks the original Bergen short measures remain visible.

[**Run #37855445127**](https://github.com/hraaaaf/Digital_crown/actions/runs/37855445127) is the new proof attempt. A green result alone does not prove successful review of all 65 images; artifact ledger and UIA status must be checked.

## Adversarial perspectives (internal)

- **Evidence adversary:** Red does not mean Facad feature fails; it means the oracle was inadequate. Only Original positions has an independent visible transition and restoration in the examined region. No 65 analysis selections occurred.
- **Clinical/safety adversary:** switching presentation layers does not establish planned-position correctness. Selecting an analysis name in the catalog must not be reported as loading/running that analysis or measuring a case. Patient source and clone remain untouched. Normative values and diagnoses stay out of this test.

**Remaining:** D1B run evidence, load/test 65 profiles only on controlled disposable example under explicit safety checks, D2 remaining control interactions, D3 app-level isolated mutation, D4 output proof, D5 parity. No merge or deployment.
