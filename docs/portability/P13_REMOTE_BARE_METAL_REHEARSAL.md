# P13-R — Remote Bare-Metal Rehearsal

**Status:** PREPARED — rehearsal only. **No P13 EP credited.**

## Goal
Exercise the P13 release candidate on real rented physical hardware before the final cabinet gate, without confusing datacenter bare metal with a Windows 11 cabinet workstation.

## Success
P13-R is successful when the same release candidate is exercised on:

1. one real Apple Silicon bare-metal Mac;
2. one real x86 bare-metal Windows-capable host;
3. package install, first launch, normal relaunch and `/health`;
4. single-instance behavior;
5. deterministic synthetic cabinet fixture;
6. authenticated update and rollback;
7. DR bundle + SHA-256 sidecar on storage independent from the source machine;
8. cross-OS restore where the portable contract applies;
9. controlled tamper/wrong-secret/failure gates;
10. machine evidence files plus a context manifest that passes the rehearsal guard.

P13-R success does **not** close P13.

## Recommended remote targets

### macOS
Use real Apple Silicon EC2 Mac bare metal. Record provider and exact instance type. The closure guard accepts remote Mac evidence only when the instance type ends in `.metal` and the collected architecture is Apple Silicon (`arm64`/`aarch64`).

### Windows
Use an x86 `.metal` host for the rehearsal. Windows Server can be useful here to exercise packaging/runtime/DR/update mechanics, but it is not accepted as the final cabinet OS proof.

Windows 10/11 BYOL may be used where licensing permits, but P13 final closure still requires the local cabinet gate below.

## Verified AWS provisioning baseline — 2026-08-29
Primary AWS documentation was rechecked before provisioning guidance was frozen.

For Europe (Frankfurt), `eu-central-1` currently lists the `Mac2-m2`, `Mac-m4` and `M6i` instance families. The EC2 instance-type specification defines `mac2-m2.metal`, `mac-m4.metal` and `m6i.metal`; `M6i` is x86_64, supports Windows and supports Dedicated Hosts.

Recommended simplest rehearsal pair:
- macOS: `mac-m4.metal` when capacity is available; `mac2-m2.metal` is the fallback;
- Windows rehearsal: `m6i.metal` with an AWS Windows Server AMI;
- Region: `eu-central-1` unless actual quota/AZ capacity requires another supported Region.

This deliberately avoids Windows 11 BYOL for P13-R. AWS documents Windows 11 desktop BYOL as requiring qualifying Microsoft VDA E3/E5 user licensing plus dedicated infrastructure. Because the final Windows 11 proof remains local anyway, importing a desktop BYOL image into AWS adds licensing work without closing any additional P13 gate.

EC2 Mac runs through a Dedicated Host and AWS enforces a minimum 24-hour host allocation/billing period. Region support does not guarantee capacity in every Availability Zone, so quota and host capacity must be checked immediately before allocation.

Sources of truth for this baseline:
- AWS EC2 instance types by Region;
- AWS EC2 general-purpose instance specifications;
- AWS EC2 Mac Instances / EC2 Mac FAQs;
- AWS Prescriptive Guidance — Microsoft licensing on AWS.

## Storage boundary
A second directory or second volume presented as source-machine internal storage is not sufficient.

For P13-R, the context manifest must record an off-machine destination with:
- `source_machine_independent=true`;
- a non-secret description;
- one of `usb`, `removable`, `nas`, or `independent_network_storage`.

The evidence bundle itself still carries the `.dcbundle`, sidecar and media hashes through `scripts/p13_real_cabinet_evidence.py`.

## Context manifest
Create a non-secret JSON file such as `p13-context.json`:

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
      "description": "independent mounted recovery destination",
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
      "description": "independent mounted recovery destination",
      "source_machine_independent": true
    }
  }
}
```

Do not put account IDs, credentials, recovery secrets, private keys or PFX passwords in this file.

## Validate P13-R
First validate each machine and the pair with the canonical collector:

```text
python scripts/p13_real_cabinet_evidence.py validate --file p13-windows.json --require-pass
python3 scripts/p13_real_cabinet_evidence.py validate --file p13-macos.json --require-pass
python scripts/p13_real_cabinet_evidence.py validate-pair --first p13-windows.json --second p13-macos.json
```

Then enforce the rehearsal boundary:

```text
python scripts/p13_real_cabinet_closure_guard.py validate-rehearsal --first p13-windows.json --second p13-macos.json --context p13-context.json
```

Expected success marker:

```text
P13_REMOTE_BARE_METAL_REHEARSAL_VALID=PASS_ATTESTED
```

## Final local cabinet gate
P13 final closure additionally requires:

1. Windows evidence collected on `execution_context=cabinet_local`;
2. the collected Windows OS caption identifies Windows 11;
3. the Windows off-machine destination is `usb`, `removable`, or `nas`;
4. operator attestation is explicit;
5. the same release candidate remains used for the Windows/macOS evidence pair.

A remote Windows `.metal` host, including Windows Server, cannot satisfy this final Windows cabinet gate.

The Mac evidence may remain remote bare-metal if it is genuine Apple Silicon `.metal` hardware and all physical first-launch/runtime/DR/update gates are actually observed.

Final guard:

```text
python scripts/p13_real_cabinet_closure_guard.py validate-closure --first p13-windows.json --second p13-macos.json --context p13-context.json
```

Expected success marker:

```text
P13_CLOSURE_GUARD_VALID=PASS_ATTESTED
```

## Boundary
The guard validates evidence structure and explicit operator attestations. It does not magically turn a datacenter host into a dental cabinet, because apparently computers are not yet capable of being embarrassed by that sentence.

No Vercel.