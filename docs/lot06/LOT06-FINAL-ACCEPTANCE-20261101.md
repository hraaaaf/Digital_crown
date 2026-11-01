# Digital Crown — LOT06 exit assessment (2026-11-01)

**Status: LAB_SECURITY_H05_PASS / INTEGRATED_PRODUCT_BLOCKED / CLINICAL_NO_GO.**
This is an evidence map, **not** permission to merge, deploy, install on a clinic computer or ingest patient data.

## Canonical goal

Actual device capture → correct patient association → Digital Crown server acceptance → dossier media + audit → interruption/retry without duplicate. Operator interface **desktop only**. Physical imaging device acceptance is scheduled in LOT10 (10.4), but LOT06 is not product-complete merely because the field test is deferred.

## Executed evidence, limited scope

- [PR #851](https://github.com/hraaaaf/Digital_crown/pull/851) OPEN/DRAFT — A–G hotfolder, synthetic adapters and TEST preflight; tip at audit `4d1391e7`, not merged into product.
- [PR #899](https://github.com/hraaaaf/Digital_crown/pull/899), [#900](https://github.com/hraaaaf/Digital_crown/pull/900) OPEN/DRAFT — synthetic CAS witness/checkpoint experiments, not independent physical antirollback.
- [PR #901](https://github.com/hraaaaf/Digital_crown/pull/901) OPEN/DRAFT — laboratory source reconciliation, separate base/history.
- [PR #909](https://github.com/hraaaaf/Digital_crown/pull/909) OPEN/DRAFT — TEST-only supervised background bridge, Windows NTFS F01 experimental, media validation and shutdown corrections. Latest observed tip `78c7983d`. CI can be GREEN while live service-SID product isolation remains absent.
- [PR #1172](https://github.com/hraaaaf/Digital_crown/pull/1172) OPEN/DRAFT — independent SQLCipher authority and Windows DPAPI/ACL/LocalService synthetic FUE, base P1-05; [run #41266223923](https://github.com/hraaaaf/Digital_crown/actions/runs/41266223923) at `2eb9235b` **26 Linux + 7 Windows = 33 PASS**, before post-run cleanup strengthening. Run belongs to that exact SHA, not newer commits.

**No shared integrated release SHA exists across the listed PR histories.**
The [source-vs-patient-network reconciliation script](../../scripts/ci/lot06_c05b03_integration_reconcile.py) explicitly returns `integrated_fue_executed=false`, `ready_to_merge=false`, `product_ready=false` and `clinical_go=false`.

## Actual blockers before LOT06 integrated acceptance

1. **One canonical schema/authority integration**: select and reconcile SQLCipher on-prem target versus previous PostgreSQL laboratory prototypes, migrations/backfill/rollback on isolated copy, no cabinet DB changes without separate GO.
2. **Real device-to-canonical-patient path**: enabled local agent/adapter under an approved service principal, real staff auth and explicit patient confirmation when ambiguous, server-side hash/size/media revalidation, atomic ClinicalAsset+receipt+audit/outbox transaction; end-to-end positive and negative FUE on ONE HEAD.
3. **Dedicated Windows principal / access controls**: ensure actual production service executable, installer, effective token and NTFS DACL protect SQLite main/WAL/SHM/journal and spool against same interactive user; the H05 LocalService *negative test* does not install or secure the production bridge.
4. **Crash + recovery / backup trust**: prove ACK loss, concurrent duplicates, abnormal process termination, power or disk interruption with server reconciliation; external monotonic/witness and recovery where claimed. No false antirollback guarantees.
5. **Physical certification in LOT10.4**: real RVG/hot-folder/TWAIN/WIA/DICOM or manufacturer SDK device, driver supported, image quality and metadata, patient association, reboot/service startup and actual cabinet installation. Hardware requires real site/equipment and explicit authorization.
6. **Independent security/UX review and human gate**: repeat review against integrated HEAD; previous independent [review of #909](https://app.notion.com/p/3fc77c663362815683c5db1c05c9071e) was FAIL on an older SHA. Reassess changes, do not silently mark that review resolved.

## Closeout decisions

- Isolated synthetic portions A–P and C05B-03 may be maintained with their separately evidenced CI claims.
- **LOT06 product completion: NO** until all integration criteria above are verified.
- **LOT06 security laboratory H05: YES** to specifically scoped tests, not certification for medical use.
- **No merge/deploy/service installation/clinic migration/real capture in this pass.** Keep PRs Draft.
- Next actionable engineering track: reconcile #909 bridge and #1172 SQLCipher authorisation on an explicitly approved unified integration branch, then execute one CI/FUE matrix and human review. Physical acceptance stays LOT10.4.

**Gates:** `PRODUCT_READY=false` · `CLINICAL_GO=false` · `ready_to_merge=false`.
