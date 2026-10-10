# FAC-03 D3E.19 — Offline ISO staging design & proof-boundary review

**2026-10-10. SOURCE-ONLY / NON EXECUTABLE. No actual ISO, Hyper-V machine, Facad/Ilexis run, audit policy change, ETW, native collection, patient data, license data, merge or deployment.**

## Decision and alternatives
D3E.18 `f4c49b332f54113244574a0a87b76ca2f60f2e5d` establishes a non-launchable WSB template with networking, clipboard and mapped folders disabled. It does not solve importing the officially sourced Quick-demo Robert dataset. Avoid reopening those surfaces to bypass this blocker.

Candidate for *review*, not adoption: **disposable Hyper-V Generation 2 Windows guest**, no NIC/vSwitch, Secure Boot proposed, disabled Enhanced Session, no clipboard/drives/printers/USB redirection, disabled Guest Service Interface and disabled PowerShell Direct service. Create an **offline ISO before VM boot** using only a permitted official package and a strictly non-clinical sample. Read-only virtual DVD ingress, no dynamic host folder. Mounting ISO is a designed guest ingestion boundary, **not proof of host security or byte authenticity**. If source licensing/activation requires connectivity or host secrets, remain blocked.

Microsoft documents [Set-VMDvdDrive](https://learn.microsoft.com/en-us/powershell/module/hyper-v/set-vmdvddrive), [Hyper-V integration services](https://learn.microsoft.com/en-us/windows-server/virtualization/hyper-v/integration-services), [management of those services](https://learn.microsoft.com/en-us/windows-server/virtualization/hyper-v/manage/manage-hyper-v-integration-services), and [Enhanced Session resources](https://learn.microsoft.com/en-us/windows-server/virtualization/hyper-v/enhanced-session-mode). Guest Service Interface enables bidirectional Copy-VMFile even without a shared folder; PowerShell Direct permits host-guest management without a virtual network; Enhanced Session can redirect clipboard, storage, printers and peripherals. These must be checked at runtime **from both host and guest** before claiming confinement. This note does not create a PowerShell installer or perform those checks.

## Staging/provenance acceptance matrix (nothing yet proven)
1. Official publisher release and permitted source download established independently; signature, download origin, hash and chain-of-custody cross-checked against independent reference. Vendor package/license and sample usage explicitly permit this experiment. If sample is not provably nonclinical, STOP.
2. Source ISO content allowlist; no customer/patient data, tenant or user credentials, private keys, clinical license, host traces or sensitive machine metadata. Staging preparation occurs outside the clinical workstation; ISO digest + source digest are recorded **privately** in an approved evidence store, not in public CI.
3. Offline guest boot with no NIC or virtual switch, Guest Service Interface disabled, PowerShell Direct disabled, Basic Session only, no host drives/devices, and host/guest negative reachability tests. Checkpoints, host VHD/ISO disposal and host isolation rules need independent approval. Read-only DVD media does not make a malicious installer benign.
4. **Evidence extraction remains UNSOLVED**. Do not turn on guest file copy, network, mounts or clipboard to retrieve ETW. No raw ETL/EVTX/XML/paths/PIDs/sample files in GitHub Actions artifacts. Separate review must authorize and prove an appropriately minimized egress or decide this method is infeasible. This is a **BLOCKER**, not an implementation detail.
5. ETW Kernel-File is still **guest-wide**; attribution of a real Ilexis writer, completed write, event coverage/loss bounds, cold/warm independent arms and counterfactual controls require future native evidence. No conclusions about isolation of FACAD shared application storage follow from this design.

## Source-only contract and tests
- Contract `docs/audits/FACAD_314_D3E19_ISO_STAGING_CONTRACT.json` contains ONLY fixed proposed design choices, no source URL or hashes invented, and all 37 verification/authorization claims are exactly false.
- Python gate `scripts/facad_314_d3e19_iso_staging_gate.py` uses an exact allowlist, rejects unknown keys/duplicate JSON keys/wrong types/false proof and prints no machine identifiers. Passing it means only that the **static design and its uncertainty declarations** remain coherent.
- Tests `scripts/test_facad_314_d3e19_iso_staging_gate.py` challenge design relaxation and proof inflation. Workflow is Linux Python only; no ISO build, no VM, no new Windows action.

## Two adversarial internal perspectives (not independent reviewers)
**A — Privacy / host-exposure perspective:** An ISO path removes persistent guest-host folder sharing from the *design*, but Hyper-V management and integration channels, compromised media, source authenticity, retention and egress may defeat the goal. **BLOCKER: runtime isolation, staging provenance and output gate lack proof.** Rating of this design is provisional and cannot be called security-certified.

**B — Evidence / scientific perspective:** A single guest may reduce unrelated ETW noise but does not limit ETW to a file, prove real application writer causality or that a write completed. Silent event loss or absent matching events must never mean no writer. **BLOCKER: no native oracle and no scientific independent review.**

Independent human/privacy and scientific reviewers must read the exact same candidate HEAD, assess attack surface and clinical meaning, and record findings before any future native experiment. `CONVERGED=false`.

## Next and stop conditions
Once source-only CI completes, preserve FAC-03 D3 OPEN/RED and all 24 D3E.18 native gates unverified. Separate specific human authorization is necessary for creating/running a VM, acquiring/installing official FACAD, collecting traces or exporting anything from the guest. No production behavior, clinical editing or release authorization is implied. **No Vercel, merge or real patient data.**
