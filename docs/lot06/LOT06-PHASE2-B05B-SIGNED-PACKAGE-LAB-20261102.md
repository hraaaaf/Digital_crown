# LOT06 Phase2 B05-B — signed package candidate (LAB only)

Parent [B05-A PR #1200](https://github.com/hraaaaf/Digital_crown/pull/1200) GREEN LAB SHA 3dd0643e234fa756b9f1dea2e113c568b39f3bff. Single [Notion LOT06 canonical](https://app.notion.com/p/3e677c66336281639beae2a946df1483); this technical runbook is not a second canonical roadmap.

## Proof target
GitHub-hosted Windows disposable runner publishes the real fixture .NET 8 service as win-x64 self-contained exe, copies existing B03 reader and gateway Python source, then generates an **ephemeral in-memory Ed25519 signer**. A canonical JSON manifest lists **every** file path, length and SHA256 digest. Its Ed25519 signature is verified against a **separate trusted public key**, never taken from the package. The private signing key is not written to disk. All file paths must be inside the package; Windows reparse/symlink entries are forbidden.

FUE: baseline signature PASS, executable changed DENIED, helper changed DENIED, manifest modified DENIED, signature modified DENIED, extra file DENIED, removed file DENIED, unrelated public key DENIED, generation below independently required minimum DENIED, restored bytes PASS, cleanup PASS. Exact SHA B05-B workflow plus inherited B05-A/B03/B02/Scope needed for a whole-chain GREEN statement.

## Critical boundaries
This test proves only a **signed candidate admission policy** in ephemeral CI. The signed package is **not what B05-A SCM launches**. This is **not Authenticode**, Windows installer, production publisher certificate, independently provisioned trust anchor, TPM/CNG key, durable anti-rollback witness, security audit, or a validated signature check immediately before real process execution. The .NET executable is self-contained but the **Python runtime, pip packages, other Python imports and key lifecycle are not bundled**. Full installer/upgrade/uninstall, privileged service packaging, supply chain, production signing, key revocation/rotation and physical scanner remain OPEN. No patient information, no product/clinical route, no merge/deploy/cabinet installation.

READY_TO_MERGE=false
PRODUCT_READY=false
CLINICAL_GO=false
