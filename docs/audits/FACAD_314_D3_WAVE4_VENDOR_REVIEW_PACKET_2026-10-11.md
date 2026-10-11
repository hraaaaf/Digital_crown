# FACAD 3.14 — D3 WAVE 4 | Vendor rights and independent release-review packet

**2026-10-11 | SOURCE-ONLY | NO-GO FOR NATIVE WRITES / REAL-PATIENT DATA / CLINICAL EXPORT | NOT AN AUTHORIZATION**

## New vendor-rights evidence (SEC-01)

- First-party FACAD subscription conditions: https://www.facad.com/wp/webshop/ . They describe a fixed user licence assigned to one computer and state that copying/installing in other computer environments requires Ilexis's agreement.
- Official download guidance: https://www.facad.com/wp/downloads2/ . An offered trial does **not** by itself show that transient GitHub-hosted Windows installations, reverse analysis, third-party automated collection or clinical data export are permitted.
- **Observed conflict to adjudicate:** experimental GitHub Quick Demo runs have installed the software on ephemeral Windows runners. This prior technical evidence does **not** establish the operator had the required vendor authorization for that environment or use. Do not label the runs illegal without the actual terms/licence and permission review, but suspend **new native experimental installations/writer attempts** pending documented permission.
- A staff member authorized to represent the project must obtain the written vendor response and obtain legal/privacy review. An AI cannot countersign these.

### Permission inquiry — prepared draft, NOT SENT

To: support@facad.com (confirm receiving address with vendor before use)

Subject: Request for written authorization and non-clinical benchmark conditions — FACAD 3.14

We are documenting a research-only comparison of cephalometric geometry using a vendor-provided nonclinical sample. Before running any additional tests, please confirm in writing:

1. Whether FACAD 3.14 Quick Demo may be installed/executed on short-lived GitHub-hosted Windows runner instances, and whether this is an agreed computer environment under the applicable licence.
2. Whether measurement-definition inspection, reading displayed reference values, and a nonclinical, same-tracing numerical comparison to an independently developed analysis engine are permitted; please specify any restrictions on automation and publication of aggregate results.
3. Whether Ilexis can provide an authorized, de-identified/synthetic case plus definitions/construction rules (including C01/C02 reference pages) and calibration specifications.
4. Whether an entirely offline dedicated non-clinical lab computer/VM is allowed, and the approved licence/activation method.
5. What records we may retain as proofs, what may be disclosed publicly, and whether any user licence or non-disclosure agreement is necessary.

We will not process patient records or run write/export experiments until rights, isolation and the evidence-handling protocol have been independently approved.

Regards,
[authorized project representative; not populated or sent]

## Formal D3 preflight packet (6 BLOCKER)

| Gate | Independent acceptance evidence required | State |
|---|---|---|
| SEC-01 | Dated vendor written grant covering *exact* hardware/VM/CI, licence, nonclinical fixture, study and retention; legal reviewer | **MISSING** |
| SEC-02 | Authorized dedicated nonclinical host + guest actual two-sided Hyper-V/management/network/device/clipboard/Powershell Direct/Guest Services controls and negative tests, independently witnessed | **MISSING** |
| SEC-03 | Signed, minimal, data-classified, anti-identification egress design with direction, transport, retention/destruction, reviewer approval | **MISSING** |
| SCI-01 | Actual FACAD writer attribution with independently defensible causal evidence, temporal ordering and completed write, under approved experiment | **MISSING** |
| SCI-02 | Bounded instrumentation capture with reviewed completeness/loss and confidentiality; no raw host-wide ETW/EVTX exported to CI | **MISSING** |
| SCI-03 | Two *different* human reviewers (security/privacy and clinical/scientific), both on the **same immutable exact candidate SHA**, findings addressed, re-review on new HEAD | **MISSING** |

## Evidence receipt template (NO pre-filled attestations)

Required fields: blocker_id, artifact SHA-256, authorized custodian, issuer, source location classified PRIVATE, acquisition date, licence/consent authority where applicable, immutable Git commit reviewed, reviewer identifier and signature, negative-test outcomes, retention/deletion deadline, redacted public summary. Do not attach secrets, tokens, patient data, raw event logs, full host paths or private C01/C02 manuals to the repository.

**GO criteria:** six gates with separately verifiable owner/reviewer approvals, no open BLOCKER/MAJOR, approved nonclinical environment and separately authorized bounded native protocol. CI success only checks source contracts; it must **not** promote any gate without those receipts. If Ilexis rejects or does not grant the experiment, use only independently constructed synthetic geometry and any publisher-authorized benchmark fixture; this alternative cannot prove real native writer provenance.

## In-scope review score (two internal perspectives, not human independent reviewers)

- Security/privacy **6/10 (design), 0/10 live isolation**: permission gap still BLOCKER; no verified guest-host boundary or egress/destruction.
- Scientific **6/10 (question design), 0/10 vendor numeric parity**: no same-tracing source oracle, validated operator implementation or independent clinician attestation.

**Canonical:** `D3_OPEN_RED`; `WRITTEN_VENDOR_AUTHORIZATION=NOT_PRODUCED`; `HUMAN_REVIEWERS=0_OF_2`; `LIVE_VENDOR_WRITE_PROVEN=false`; `SHARED_APP_STORAGE_ISOLATION=UNVERIFIED`; `CONVERGED=false`. No merge/deploy.
