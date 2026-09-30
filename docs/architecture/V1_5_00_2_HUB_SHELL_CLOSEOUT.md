# V1.5-00.2 ? Hub shell + routing closeout

Date: 2026-09-30
Repository: hraaaaf/Digital_crown
Base before implementation: db1cadd74eb60d3e11e6c31d5da6780fefaacbb4
PR: #719
PR head approved by Achraf: d257202d6a882c23fac8597084cdb0a1b4087f46
Merge commit: 9b135e5dbad3b13b289cf2de78784959060f52b3
Status: CLOSED

## Goal

Add the first real Digital Crown Hub shell and routing without duplicating Cabinet, Mobile or Patient Companion.

## Delivered

- authenticated desktop root dispatches to `/hub`;
- `/hub`, `/cabinet`, `/station`, `/control-center` exist;
- `/cabinet` remains behind the existing `ProtectedRoute` and Cabinet RBAC/init boundary;
- Station and Control Center are shells only;
- Cabinet header exposes `Changer d'espace`;
- Hub contains no business or patient data;
- Mobile and Patient Companion remain separate;
- legacy `appMode` is not reused as workstation-mode state;
- canonical clinic identity is read from `/api/clinics/me`;
- main experience title is neutral `Digital Crown` with dynamic `CABINET` / `CLINIQUE` badge;
- backend identity failure leaves the Hub available with an explicit offline state.

## Security boundary

00.2 does not claim secure Station lock, permanent workstation-mode persistence, owner/admin PIN enforcement, trusted workstation identity, or server-authorized workstation-mode mutation. Those belong to 00.3.

`localStorage` and direct URL navigation are not authorization authorities. Direct `/cabinet` remains protected by authentication. Station remains non-operational until the 00.3 mode-poste/PIN contract exists.

## Theme-token correction

The initial visual pass was rejected because Hub surfaces still contained visual hardcodes. Before approval, those were removed in favor of canonical semantic/theme primitives: `rounded-elite-*`, `shadow-elite*`, `transition-elite`, `primary`, `card`, `text-main`, `text-muted`, and `border-main`.

Regression protection in `v15HubRoutingContract.test.ts` rejects arbitrary bracket visual classes and direct Tailwind palette classes in Hub surfaces.

## Verification

Exact merged master verification performed after merge on `master@9b135e5dbad3b13b289cf2de78784959060f52b3`:

- targeted Hub tests: 2 files / 7 tests PASS;
- `npm run build:test`: PASS;
- 4745 modules transformed;
- PWA generated;
- build manifest commit: `9b135e5dbad3b13b289cf2de78784959060f52b3`;
- Hub hardcode scan: NONE.

Adversarial browser review on merged master:

- Hub offline/anonymous: accessible without business data;
- direct `/station`: shell only, no Hub escape button;
- direct `/control-center`: shell only, Hub return available;
- tampered `localStorage.appMode=station` + direct `/cabinet`: redirected to `/login`;
- persisted Prestige theme inherited correctly;
- direct mobile `/hub` at 390px: no horizontal overflow.

## Visual proof and human gate

GitHub Playwright visual proof for the approved PR head completed successfully. PR #719 carries label `visual-approved-by-achraf`; the subsequent `Human visual approval (Achraf)` run completed SUCCESS before merge.

The visual artifact was produced from the PR merge ref corresponding to approved head `d257202d?`. Comparison to final merge commit `9b135e5d?` shows no frontend differences; the intervening master-side differences are documentation-only.

Severe review scores after merge:

- internal double-check: 8.6/10;
- internal triple-check: 8.4/10.

Deductions were for stale closeout metadata and one fallback mojibake found after merge, not for a discovered authentication bypass. The follow-up closeout patch corrects both and hardens the visual workflow fail-closed.

## Next exact

Start V1.5-00.3 only from verified current `master`, using the canonical handover. 00.3 owns workstation identity/persistence, admin + owner-PIN protected permanent mode changes, Station exit protection, auditability, and precedence of workstation identity over viewport-only routing for dedicated tablet/kiosk devices.
