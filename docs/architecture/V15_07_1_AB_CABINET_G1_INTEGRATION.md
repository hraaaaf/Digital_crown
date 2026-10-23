# LOT07 / 07.1.A+B — G1 real Cabinet lab on the nine-layout foundation

**Status: separate STACKED DRAFT, not merged or deployed.** Depends on the dormant nine-layout foundation PR #1038 (HEAD d686f3341d7c609b7ea10ee5637686d99f6c660b). This slice is a genuine patient/media React adapter on **Cabinet DEV only**. Do not claim that all nine dispositions, a full MultiView authorizer, user-post layout persistence, or 07.1.E are ready.

## Reuse existing G1 without blind stacking

- Existing real [#897](https://github.com/hraaaaf/Digital_crown/pull/897) and [#913](https://github.com/hraaaaf/Digital_crown/pull/913) are unmerged and built on older stacked prerequisites #895/#896. Reused **surgically**: authenticated parent patient context, existing PatientMediaTimeline and OrthoLongitudinalComparePanel, responsive 1280 CSS px, ratio 37–63 and same-patient protection. No wholesale import of old UI shells or permission assumptions.
- The actual parent route PatientDetailsInner.tsx gets only a **DEV-only** integration condition inside its media tab and a route-ID mismatch fail-closed guard borrowed from #913. In other modes existing single PatientMediaTimeline remains unchanged. No new production route. Lab flag requires import.meta.env.DEV and VITE_V15_07_1_MULTIVIEW_LAB=1; disabled by default.
- The lab re-GETs the actual current patient through the existing authenticated /patients/{id}, verifies response ID/shape against route and signed-in actor, and reads real /workstation/bootstrap identity via workstationModeService. Missing/unenrolled/non-Cabinet station or revoked patient permission blocks all clinical slot mounts. No PHI stored in layout state.
- Live composition uses one patient route, exactly one PatientMediaTimeline, a plain read-only dossier summary from the freshly authorized response and optional existing OrthoLongitudinalComparePanel only with hasAccess(user,'cephalo'). Never mounts two CephaloWorkspace instances; scientific F5 remains unactivated.
- Five pilot modes: **two columns**, **two rows**, **single media focus**, **three columns**, and **one large + two small** (last two only with existing longitudinal permission and adequate width). **All 9 canonical product presets are displayed as disabled** examples: do not confuse product catalog with 9 live clinical layouts.
- Selection, **schematic no-clinical preview**, Apply/Cancel/Reset, exchange order and native range resize by mouse/keyboard with 37–63 ratios are local and nonpersistent. Geometry uses measured workspace width; under 1280 CSS px original single media module is preserved. Deny unreadably narrow layouts.
- React slot children re-key across tenant/user/workstation/patient changes; fresh patient reads are ignored on effect cleanup. Client gates do **not** replace backend auth or full cancellation of all nested async requests.

## Risk / evidence

Vitest with mock components cannot establish an authenticated clinical browser journey. Before any merge or activation, require isolated authenticated FastAPI T2 + actual browser FUE-I on final SHA, patient A→B with late requests and drafts, account/role/tenant denials, session revocation, blob cleanup, actual Windows 200% and comparable BEFORE/TARGET/AFTER at 1280/1440/1920/2560; real owner visual approval. No real patient or cabinet DB test data. Full 07.1 and all nine layouts remain OPEN.

**Next:** evaluate targeted CI exact SHA Vitest, TypeScript and production build and prepare authenticated end-to-end proof in further slice; separate owner merge GO required. 07-D/07-E remain frozen.
