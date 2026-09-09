# P13 — Physical cabinet certification runbook

Last verified: 2026-09-09.

## Goal
Certify the same Digital Crown release candidate on a real Windows 11 cabinet target and a real macOS Apple Silicon target, with real off-machine recovery evidence and operator-observed lifecycle gates.

## Success
P13 closes only when:
- Windows evidence is collected on `execution_context=cabinet_local`;
- Windows OS evidence identifies Windows 11;
- Windows DR destination is a real `usb`, `removable`, or `nas` target independent from the cabinet machine;
- macOS evidence is Apple Silicon; a remote `.metal` Mac is acceptable only when all mandatory observations are genuinely attested;
- both evidence files use the same non-empty `release_id`;
- every required physical gate is `PASS`, except the six explicitly CI-substitutable failure gates which may be `CI_SUBSTITUTED` with an evidence note;
- `scripts/p13_real_cabinet_evidence.py validate-pair` passes;
- `scripts/p13_real_cabinet_closure_guard.py validate-closure` prints `P13_CLOSURE_GUARD_VALID=PASS_ATTESTED`.

No real patient data is permitted in the certification fixture or evidence.

## Required physical gates
The collector requires these 15 gates on each platform:
1. `clean_install`
2. `first_launch`
3. `normal_relaunch`
4. `single_instance`
5. `synthetic_fixture`
6. `off_machine_dr`
7. `cross_os_restore`
8. `authenticated_update`
9. `rollback`
10. `wrong_secret_rejected`
11. `tampered_bundle_rejected`
12. `offline_destination_fail_closed`
13. `unready_second_instance_recovery`
14. `insufficient_space_fail_closed`
15. `interrupted_operation_recoverable`

Only gates 10–15 may use `CI_SUBSTITUTED`, and each substitution must contain a concrete evidence note. Gates 1–9 require real operator-observed `PASS`.

## Release candidate
Choose one immutable release identifier before either physical run, for example:

`DC-P13-2026-09-09-<short-sha>`

Use the exact same `release_id` in Windows and macOS evidence. Record the package SHA-256 automatically with the collector.

## Windows 11 cabinet-local execution
Prerequisites:
- real Windows 11 cabinet machine;
- signed Digital Crown Windows installer for the chosen release candidate;
- genuine USB/removable/NAS destination physically independent from the cabinet machine;
- synthetic cabinet fixture only;
- DR `.dcbundle` + SHA-256 sidecar;
- media sentinel file whose continuity can be checked after restore;
- running Digital Crown health endpoint returning HTTP 200 with `status=ok` and `db=ok`.

Collect initial evidence:

```powershell
python scripts/p13_real_cabinet_evidence.py collect `
  --operator "<operator>" `
  --release-id "<release-id>" `
  --package "<installer.exe>" `
  --health-url "http://127.0.0.1:<port>/health" `
  --data-path "<cabinet-data-path>" `
  --dr-bundle "<off-machine-bundle.dcbundle>" `
  --dr-sidecar "<off-machine-bundle.sha256>" `
  --media-sentinel "<media-sentinel-file>" `
  --output "p13-windows-evidence.json"
```

The collector must record a real Windows model/build and Authenticode `Status=Valid` with a signer thumbprint.

## macOS Apple Silicon execution
Prerequisites:
- real Apple Silicon Mac, or genuine remote Apple Silicon `.metal` only under the closure-guard rules;
- exact corresponding macOS package for the same release candidate;
- installed `.app` path;
- independent off-machine destination;
- synthetic fixture, DR bundle + sidecar, media sentinel;
- running health endpoint returning HTTP 200 with `status=ok` and `db=ok`.

Collect initial evidence:

```bash
python3 scripts/p13_real_cabinet_evidence.py collect \
  --operator "<operator>" \
  --release-id "<release-id>" \
  --package "<package.dmg>" \
  --app-path "/Applications/Digital Crown.app" \
  --health-url "http://127.0.0.1:<port>/health" \
  --data-path "<cabinet-data-path>" \
  --dr-bundle "<off-machine-bundle.dcbundle>" \
  --dr-sidecar "<off-machine-bundle.sha256>" \
  --media-sentinel "<media-sentinel-file>" \
  --output "p13-macos-evidence.json"
```

The collector must record Apple Silicon architecture/model, macOS version/build, bundle id/version and strict `codesign --verify` success.

## Recording each observed gate
After each observation, record it immediately. Example:

```bash
python scripts/p13_real_cabinet_evidence.py set-gate \
  --file p13-windows-evidence.json \
  --gate clean_install \
  --status PASS \
  --note "Fresh install completed on cabinet-local Windows 11; application launched without console/error."
```

Repeat for all gates on both evidence files. Notes must describe what was actually observed; never write credentials, recovery secrets, signing keys, passwords, or patient data.

## Structural validation during execution
```bash
python scripts/p13_real_cabinet_evidence.py validate --file p13-windows-evidence.json
python scripts/p13_real_cabinet_evidence.py validate --file p13-macos-evidence.json
```

Before closure:

```bash
python scripts/p13_real_cabinet_evidence.py validate --file p13-windows-evidence.json --require-pass
python scripts/p13_real_cabinet_evidence.py validate --file p13-macos-evidence.json --require-pass
python scripts/p13_real_cabinet_evidence.py validate-pair --first p13-windows-evidence.json --second p13-macos-evidence.json
```

## Closure context
Create `p13-context.json` without secrets:

```json
{
  "schema": "digital-crown-p13-context-v1",
  "windows": {
    "execution_context": "cabinet_local",
    "operator_attested": true,
    "dr_destination": {
      "kind": "usb",
      "description": "Real independent removable destination used for the witnessed DR run",
      "source_machine_independent": true
    }
  },
  "macos": {
    "execution_context": "cabinet_local",
    "operator_attested": true,
    "dr_destination": {
      "kind": "usb",
      "description": "Real independent removable destination used for the witnessed DR run",
      "source_machine_independent": true
    }
  }
}
```

For a genuine remote Apple Silicon bare-metal rehearsal, use `execution_context=remote_bare_metal_rehearsal` plus non-empty `provider` and an `instance_type` ending in `.metal`. Remote rehearsal alone credits 0 EP.

## Final closure command
```bash
python scripts/p13_real_cabinet_closure_guard.py validate-closure \
  --first p13-windows-evidence.json \
  --second p13-macos-evidence.json \
  --context p13-context.json
```

Expected final proof:

`P13_CLOSURE_GUARD_VALID=PASS_ATTESTED release_id=<release-id>`

## Evidence handling
- Evidence files must contain synthetic data only and no secrets.
- Store hashes and operator observations, not secret material.
- Preserve the exact package binaries, DR bundle/sidecar and media sentinel outside the repository when they contain cabinet runtime material.
- Commit only safe redacted JSON evidence if repository policy permits it; otherwise record immutable hashes and external evidence identifiers in the P13 closeout.

## Credit rule
P13 remains **0/13 EP** until the final closure guard passes with the full physical/human evidence pair. No partial EP.
