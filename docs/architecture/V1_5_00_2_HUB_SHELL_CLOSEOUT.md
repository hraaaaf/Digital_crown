# V1.5-00.2 — Hub shell + routing closeout

Date: 2026-09-30
Repository: hraaaaf/Digital_crown
Worktree: C:\Users\lenovo\Documents\Cabinet\DigitalCrown-v1.5-00
Branch: feat/v1.5-00-2-hub-implementation
Base: db1cadd74eb60d3e11e6c31d5da6780fefaacbb4`r`nImplementation HEAD: 79fea6647283dc9553e89ad102c5d137e4a05883

## Goal / Success / Proof

Goal: add the first real Digital Crown Hub shell and routing without duplicating Cabinet, Mobile or Patient Companion.

Success:
- authenticated desktop root dispatches to /hub;
- /hub, /cabinet, /station, /control-center exist;
- Cabinet still uses the existing protected business surface;
- Mobile and Patient Companion remain separate;
- Hub remains renderable when cabinet backend identity lookup fails;
- Cabinet header exposes Changer d'espace;
- legacy appMode is not reused for workstation mode;
- UI observed locally at 390x844 / 768x1024 / 1280x900.## BEFORE

Exact pre-00.2 source: db1cadd74eb60d3e11e6c31d5da6780fefaacbb4.

Observed locally on the remote workstation:
- no Hub product surface;
- /hub stayed in the legacy startup/protected path;
- no workstation dispatcher;
- no stable Cabinet / Station / Control Center entries.

Retained local BEFORE captures:
- artifacts/v1.5-00.2-local/before/hub-390x844-final.png
  SHA256 F347EBBF9C4C511081C235CFB5C6D4EB4BB002A5D6BFB48F5F1D4471BD0640FB
- artifacts/v1.5-00.2-local/before/hub-768x1024-final.png
  SHA256 630DED6A9DED18000375ADCE47EC0720D486034F2B1C221D1F5B0B8A9FF6988E
- artifacts/v1.5-00.2-local/before/hub-1280x900-final.png
  SHA256 9780C636FCF8BABD636400C3E54A1BB0B27A945377075385DEC922D684E24783## DURING

Implemented locally on DESKTOP-3MAJEEH:
- lazy-loaded Hub and workstation placeholder surfaces;
- /hub data-free dispatcher;
- /cabinet protected alias to existing dashboard/Cabinet surface;
- /station placeholder with no patient escape control;
- /control-center placeholder;
- authenticated desktop root -> /hub;
- Cabinet header -> Changer d'espace;
- canonical clinic identity fetched from API_BASE + /api/clinics/me with current runtime auth token;
- backend failure leaves the Hub available and shows an explicit offline state;
- three premium experience cards: Cabinet / Accueil / Technique.

Security boundary retained:
- Hub does not grant permissions;
- /cabinet remains behind existing auth/init/RBAC protection;
- Station is not declared secure/operational yet;
- workstation persistence and owner-PIN enforcement are deferred to 00.3.## AFTER

Observed locally with Playwright against the remote worktree.

Deterministic online identity fixture:
- cabinet: Centre Dentaire Benmoussa;
- type: CLINIQUE.

Results:
- 390x844: Hub present, 3 cards, no horizontal overflow, no JS errors;
- 768x1024: Hub present, 3 cards, no horizontal overflow, no JS errors;
- 1280x900: Hub present, 3 cards, no horizontal overflow, no JS errors.

Offline behavior also tested:
- backend identity request fails;
- Hub remains usable;
- explicit offline banner renders;
- Control Center remains reachable;
- targeted unit/integration tests pass.`r`n`r`nRetained final AFTER captures:
- artifacts/v15-00-2-refined/hub-390x844.png
  SHA256 DFCBF81DA474C3C79F0AB50E66BF8B10C54B43BEEE411A4EE6BBE49FF420CC70
- artifacts/v15-00-2-refined/hub-768x1024.png
  SHA256 05C5D98440CC5C4169DDD144129D968F667F9155B199BA3ECF42006C18E56AC2
- artifacts/v15-00-2-refined/hub-1280x900.png
  SHA256 4739EF894CDF4CB783F88C0EB1CA67A8AD090C9D58D6998C3B922D5B9F0E9A54

## Local verification

Targeted tests:
- HubPage.test.tsx
- v15HubRoutingContract.test.ts
- result: 2 test files / 5 tests PASS.

Earlier local build after Hub introduction:
- npm run build:test
- 4709 modules transformed;
- HubPage and WorkstationExperiencePage chunks generated;
- PWA assets generated;
- build result PASS.
- Final exact-state build on `79fea6647283dc9553e89ad102c5d137e4a05883`: PASS; 4709 modules transformed; PWA generated.`r`n`r`n## Severe visual review

Internal double-check:
- mobile: 9.0/10
- tablet: 9.0/10
- desktop: 9.1/10

Internal triple-check:
- 8.9/10 overall.
- Remaining limitation is intentional: Station and Control Center are shells, not completed workstation modes.
- No claim of secure Station lock or permanent workstation mode is made in 00.2.

## Next exact

Start V1.5-00.3 — controlled workstation-mode memory:
- separate workstation mode from appMode;
- workstation identity independent of logged-in user;
- server-authorized permanent mode changes;
- admin + owner-PIN gate;
- direct URL/storage tampering must not grant Cabinet authorization;
- Station remains fail-closed until the protected mode-change contract exists.
## Theme-token correction after human review

The first 00.2 visual pass was rejected because Hub surfaces still contained visual hardcodes. The implementation was corrected before human approval:
- arbitrary radius classes removed in favor of `rounded-elite-sm` / `rounded-elite-lg`;
- non-token shadow removed in favor of `shadow-elite-hover`;
- arbitrary font-size/letter-spacing classes removed in favor of canonical Tailwind/theme scale;
- direct amber warning palette removed; offline state now derives from `primary` theme tokens;
- malformed Windows-encoded French copy repaired;
- token contract test added and fails on arbitrary bracket classes or direct palette classes in Hub surfaces.

Local proof after correction:
- forbidden visual hardcode scan: NONE;
- targeted tests: 2 files / 6 tests PASS;
- `npm run build:test`: PASS, 4709 modules, PWA generated;
- theme proof: Elite / Emerald / Prestige all render 3 Hub cards with zero horizontal overflow and zero JS errors;
- runtime variables observed changing with theme: `--primary`, `--bg-medical-pearl`, `--card-bg`, `--text-main`, `--border-color`.

Human visual approval must be based on the post-token-correction screenshots, not the earlier 00.2 captures.
