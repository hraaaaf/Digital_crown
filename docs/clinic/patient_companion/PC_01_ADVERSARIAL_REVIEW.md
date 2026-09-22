# PC-01 — Adversarial Review

Status: IN PROGRESS — dedicated visual/offline certification pending.

## Goal under review

Synchronize only server-authorized appointments and share metadata into the existing encrypted Patient Companion vault, then render the last successful snapshot offline.

## Findings

### F-01 — Partial sync could corrupt wallet freshness
Risk: appointments succeeds while shares fails, yet a partial snapshot could appear current.
Control: PatientCompanionSync fetches both with Promise.all and calls saveWallet only after both succeed.
Evidence: unit test asserts failed sync never calls saveWallet.
Status: implemented; exact-head CI pending.

### F-02 — PC-01 must not create a plaintext cache
Risk: convenience cache in localStorage/sessionStorage or separate IndexedDB object would bypass PC-00 vault guarantees.
Control: PatientWalletSnapshot is embedded in PatientCompanionVaultState.cache and therefore passes through the same AES-GCM envelope.
Required runtime proof: encrypted envelope contains ciphertext but not representative appointment/document plaintext, token absent from Web Storage, AES-GCM key non-extractable.
Status: workflow added; runtime proof pending.

### F-03 — Offline reopen must not silently call cabinet
Risk: “offline wallet” that requires startup network is not actually offline.
Control: PatientCompanionApp loads PatientCompanionStorage first and renders cached wallet without automatic sync.
Required runtime proof: reload after network route abort still shows appointment/share and emits zero API requests.
Status: workflow added; proof pending.

### F-04 — Stale data could look live
Risk: patient assumes locally cached appointment/share state is current.
Control: last successful sync timestamp is displayed. Offline sync failure explicitly states that the last local copy is retained.
Remaining UX hardening: visual certification must confirm freshness is readable at 360×800 and 390×844.
Status: implemented; visual proof pending.

### F-05 — Expired device session must not destroy patient-held wallet
Risk: 30-day credential expiry could make legitimate locally-held data disappear.
Control: expiry blocks synchronization only; local wallet remains readable and UI asks for re-pairing for future sync.
Status: implemented.

### F-06 — Token lifetime is not persistent connectivity
Risk: product could promise “always connected” while current device JWT expires after 30 days.
Control: canonical docs explicitly prohibit indefinite-connectivity claim. Secure renewal/re-pairing remains future work.
Status: documented.

### F-07 — Revocation cannot guarantee remote erasure
Risk: misleading claim that cabinet revocation deletes already-synced data from an offline patient phone.
Control: architecture only claims revocation stops future server access/sync. No remote-erasure guarantee.
Status: preserved.

### F-08 — WhatsApp could become an unaudited clinical side-channel
Risk: appointments/documents/photos/questionnaires leak outside Patient Companion and split source of truth.
Control: WhatsApp is excluded as clinical transport. Future optional notification/deep-link only, with no clinical payload.
Status: roadmap locked.

### F-09 — Shares endpoint currently synchronizes metadata, not binary payloads
Risk: UI could imply a document/media is locally downloadable when only metadata exists.
Control: current PC-01 UI shows shared resource cards but no fake download/open action.
Status: correct for current scope.
Future: binary encrypted resource retrieval requires an explicit authorized endpoint/cache contract before claiming offline document contents.

### F-10 — PC-01 dependency could outrun PC-00 corrections
Risk: merge a wallet on an uncertified pairing foundation.
Control: PR #636 targets feature/patient-companion-pc00 and remains draft. It must reconcile the final PC-00 HEAD before certification/merge.
Status: enforced procedurally.

## Required close gates

1. dedicated PC-01 visual workflow green on exact head;
2. Chromium + WebKit, 360×800 + 390×844;
3. matched BEFORE = PC-00 candidate / AFTER = PC-01;
4. encrypted envelope probe green;
5. offline reload with zero API calls green;
6. screenshots inspected, not merely generated;
7. PC-00 closeout/merge;
8. PC-01 reconciliation onto final PC-00;
9. final exact-head CI;
10. canonical/Notion/handover closeout.

No PASS is asserted until all gates are proven.


## Additional hardening — 2026-09-19

A follow-up contract inspection found that the media branch of `GET /contexts/{access_id}/shares` still returned the internal numeric `ClinicalAsset.id`, despite the document branch and frontend wallet schema having been hardened.

Remediation:
- removed the media `resource_id` from the patient-facing response;
- retained opaque `share_id` as the patient-visible share handle;
- static contract test now rejects `"resource_id": resource.id` in the patient shares router.

Latest code/test HEAD before this documentation checkpoint:
`ef2ba3113a34199ae921099a1a61175985bdcd5f`

Exact-head CI/visual certification is pending. No PASS is claimed for this new HEAD yet.
