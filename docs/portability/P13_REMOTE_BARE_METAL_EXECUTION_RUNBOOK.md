# P13-R — Remote Bare-Metal Execution Runbook

**Status:** PREPARED — execution requires AWS account/billing access. **0 P13 EP credited.**

## Goal
Run one exact Digital Crown release candidate on rented physical macOS + Windows-capable bare metal, collect truthful P13 evidence, then preserve the final local Windows 11 + USB/NAS cabinet gate.

## Success
The rehearsal is successful only when:
- the four package candidates are built from the same Git commit;
- Windows 1.0.0 and 1.0.1 installers are Authenticode signed and timestamped by the existing Digital Crown private publisher;
- macOS 1.0.0 and 1.0.1 DMGs pass the existing private distribution integrity contract;
- real remote bare-metal Mac + x86 host execute the required physical gates;
- DR leaves the source machine and survives an independent S3 round-trip with identical SHA-256;
- both evidence documents and the P13 context manifest pass `validate-rehearsal`.

This does not close P13.

## 0. Human gate
Required before provisioning:
- AWS account with billing authorization;
- quota/capacity for one EC2 Mac Dedicated Host and one x86 `.metal` instance;
- operator access to the GitHub Actions artifacts produced below.

Do not paste AWS credentials, GitHub tokens, recovery secrets, PFX content or PFX passwords into chat, evidence JSON, issues or PRs.

## 1. Freeze one candidate HEAD
Use the exact HEAD of PR #299 after its CI is green. Do not mix package artifacts from different commits.

Canonical `release_id` for P13-R:

```text
<exact Git commit SHA>
```

The final target package for evidence collection is version `1.0.1`; `1.0.0` is the baseline used to prove real update/rollback.

## 2. Produce the package pair once
Run the existing workflow manually on the frozen candidate HEAD:

```text
Portability P7/P10 Clean Hosted Certification
```

The P13 export preparation retains the already-certified build products instead of rebuilding them on AWS.

Expected macOS artifact:

```text
digitalcrown-clean-hosted-macos-proof
  DigitalCrown-1.0.0-arm64.dmg
  DigitalCrown-1.0.1-arm64.dmg
  p10-private-lifecycle-proof.json
  p7-clean-hosted-gatekeeper.json
  self-test-*.json
```

Expected Windows artifact:

```text
digitalcrown-clean-hosted-windows-proof
  DigitalCrownSetup-1.0.0.exe
  DigitalCrownSetup-1.0.1.exe
  digitalcrown-private-codesign.cer
  p10-clean-hosted-signed-pair.json
  proof.json
```

The private PFX is never uploaded. The `.cer` is public trust material only.

Before using any package, verify its SHA-256 against the workflow proof produced by the same run. If a package is rebuilt, the candidate changes and the evidence must restart from that new exact package set.

## 3. Remote hardware
Preferred baseline in Europe (Frankfurt), subject to real quota and Availability Zone capacity at allocation time:

### macOS
- first choice: `mac-m4.metal`;
- fallback: `mac2-m2.metal`;
- genuine Apple Silicon EC2 Mac Dedicated Host;
- encrypted GUI access required for the human Gatekeeper first-launch ceremony;
- never expose Screen Sharing/VNC publicly; tunnel/administer it through a restricted path.

AWS EC2 Mac Dedicated Hosts carry a minimum 24-hour allocation period. Do not allocate the host until the candidate artifacts and runbook are ready.

### Windows rehearsal
- `m6i.metal` x86_64;
- AWS Windows Server AMI is sufficient for P13-R mechanics;
- RDP restricted to the operator path/IP or another controlled administration channel.

Windows Server is rehearsal evidence only. It cannot satisfy final P13 closure.

## 4. Independent DR storage
Use an S3 bucket/prefix administered independently from either host, for example conceptually:

```text
s3://<private-p13-bucket>/p13/<release_id>/
```

Requirements:
- bucket not hosted on either source machine;
- encryption enabled;
- least-privilege instance role or short-lived operator credentials;
- no public access;
- no secret embedded in evidence;
- compute SHA-256 before upload and after download on the opposite OS;
- downloaded bundle hash must equal the original bundle hash and sidecar.

Do not count a second local directory, EBS volume attached only to the source host, or another path on the same system as independent DR.

For the context manifest use:

```json
{
  "kind": "independent_network_storage",
  "description": "private independent S3 recovery prefix",
  "source_machine_independent": true
}
```

The final local Windows 11 cabinet gate still requires USB/removable/NAS, not S3.

## 5. Windows P13-R sequence
1. Record EC2 host/instance type and Windows Server version.
2. Copy the exact Windows package pair and public `.cer` from the frozen GitHub artifact.
3. Verify both installer SHA-256 values against `p10-clean-hosted-signed-pair.json`.
4. Import **only** `digitalcrown-private-codesign.cer` into LocalMachine `Root` and `TrustedPublisher`.
5. Verify `Get-AuthenticodeSignature` returns `Valid` for both installers and timestamps are present.
6. Install `DigitalCrownSetup-1.0.0.exe`.
7. Perform first launch, `/health`, normal relaunch and second-instance behavior.
8. Create the deterministic synthetic cabinet fixture and media sentinel.
9. Create real DR bundle + sidecar; verify local SHA-256; upload to the independent S3 prefix.
10. Exercise the authenticated `1.0.0 -> 1.0.1` update through the certified update path.
11. Verify target package self-test, target version and `/health`.
12. Run one controlled interruption/failure and prove package/data rollback to a healthy state.
13. Re-apply the successful target if required so final evidence represents 1.0.1.
14. Download the opposite-OS DR bundle when testing the macOS -> Windows direction; verify exact SHA before restore.
15. Run Guided Restore through the installed/frozen application; verify DB marker + media sentinel + `/health`.
16. Exercise tampered bundle and wrong-secret rejection without real patient data.

Public trust bootstrap command, as Administrator:

```powershell
certutil -f -addstore Root .\digitalcrown-private-codesign.cer
certutil -f -addstore TrustedPublisher .\digitalcrown-private-codesign.cer
```

## 6. macOS P13-R sequence
1. Record Mac model, Apple Silicon architecture and exact macOS version/build.
2. Copy the exact DMG pair from the frozen GitHub artifact.
3. Verify SHA-256 values before installation.
4. Mount/install `DigitalCrown-1.0.0-arm64.dmg`.
5. Verify `codesign --verify --deep --strict`.
6. Observe default Gatekeeper rejection expected for private ad-hoc distribution.
7. In the real GUI session, perform the administrator-controlled `Open Anyway` ceremony once.
8. Verify first launch, `/health`, normal relaunch and second-instance behavior.
9. Create the deterministic synthetic cabinet fixture and media sentinel.
10. Download the Windows-created DR bundle from independent S3; verify exact SHA before restore.
11. Run Guided Restore; verify DB marker + media sentinel + `/health`.
12. Create the reverse macOS DR bundle, verify SHA/sidecar and upload it to independent S3.
13. Exercise the authenticated `1.0.0 -> 1.0.1` private update path.
14. Verify target package self-test, target bundle version and `/health`.
15. Run one controlled interruption/failure and prove rollback to a healthy state.
16. Exercise tampered bundle and wrong-secret rejection.

No Developer ID, notarization, stapling or Apple approval is claimed.

## 7. Collect evidence
Run the canonical collector on the final healthy 1.0.1 state.

Windows:

```text
python scripts/p13_real_cabinet_evidence.py collect --operator <initials> --release-id <exact-head-sha> --package DigitalCrownSetup-1.0.1.exe --health-url <loopback-health-url> --data-path <cabinet-data-path> --dr-bundle <snapshot.dcbundle> --dr-sidecar <snapshot.dcbundle.sha256> --media-sentinel <synthetic-media-file> --output p13-windows.json
```

macOS:

```text
python3 scripts/p13_real_cabinet_evidence.py collect --operator <initials> --release-id <exact-head-sha> --package DigitalCrown-1.0.1-arm64.dmg --app-path <Digital Crown.app> --health-url <loopback-health-url> --data-path <cabinet-data-path> --dr-bundle <snapshot.dcbundle> --dr-sidecar <snapshot.dcbundle.sha256> --media-sentinel <synthetic-media-file> --output p13-macos.json
```

Record each observed P13 gate with `set-gate`. Do not mark a gate `PASS` unless it was actually observed on that machine.

## 8. Context manifest
Example remote rehearsal context:

```json
{
  "schema": "digital-crown-p13-context-v1",
  "windows": {
    "execution_context": "remote_bare_metal_rehearsal",
    "provider": "aws",
    "instance_type": "m6i.metal",
    "operator_attested": true,
    "dr_destination": {
      "kind": "independent_network_storage",
      "description": "private independent S3 recovery prefix",
      "source_machine_independent": true
    }
  },
  "macos": {
    "execution_context": "remote_bare_metal_rehearsal",
    "provider": "aws",
    "instance_type": "mac-m4.metal",
    "operator_attested": true,
    "dr_destination": {
      "kind": "independent_network_storage",
      "description": "private independent S3 recovery prefix",
      "source_machine_independent": true
    }
  }
}
```

Use the actual Mac instance type if the M2 fallback is used.

## 9. Validate rehearsal

```text
python scripts/p13_real_cabinet_evidence.py validate --file p13-windows.json --require-pass
python3 scripts/p13_real_cabinet_evidence.py validate --file p13-macos.json --require-pass
python scripts/p13_real_cabinet_evidence.py validate-pair --first p13-windows.json --second p13-macos.json
python scripts/p13_real_cabinet_closure_guard.py validate-rehearsal --first p13-windows.json --second p13-macos.json --context p13-context.json
```

Required final rehearsal marker:

```text
P13_REMOTE_BARE_METAL_REHEARSAL_VALID=PASS_ATTESTED
```

A rehearsal result is not P13 closure.

## 10. Final cabinet gate after P13-R
On a real local cabinet-class Windows 11 machine:
- use the same frozen candidate unless a real defect forces a new candidate and full affected evidence repeat;
- install the Digital Crown public `.cer` only;
- exercise real USB/removable/NAS DR;
- verify installed runtime, single instance, synthetic cabinet continuity, update/rollback and recovery;
- collect Windows evidence with `execution_context=cabinet_local`;
- run `validate-closure`.

Only after all mandatory physical gates and the closure guard pass may P13 receive 13 EP.

## 11. Cleanup
After evidence is safely retained:
- remove package copies and evidence containing operational metadata from temporary hosts as appropriate;
- remove the temporary public trust certificate from the Windows Server rehearsal host if the host is retained;
- terminate the Windows rehearsal instance;
- release the EC2 Mac Dedicated Host as soon as AWS permits after the minimum allocation period;
- retain only non-secret canonical evidence references required for P13 closeout;
- keep the S3 evidence prefix private and lifecycle it according to the evidence-retention decision.

No Vercel.