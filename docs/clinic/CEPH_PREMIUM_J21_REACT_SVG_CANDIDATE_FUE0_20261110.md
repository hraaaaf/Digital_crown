# CEPH-PREMIUM J2.1 — React/SVG pixel-scene candidate, FUE-0 only — 2026-11-10

## Scope and safeguards
This increment adds a frontend **nonclinical test candidate** for the authenticated scene API from PR Draft #1253. It is **not imported or rendered by active Digital Crown clinical UI**, and no native Desktop packaging/release changes have been made.

- `frontend/src/features/ortho/cephPremiumSceneFUEClient.ts`: uses the existing cabinet-local axios client for the scene GET/CAS POST and authenticated protected original-media content endpoint. Calls require **both** `import.meta.env.DEV === true` and `VITE_CEPH_J21_SCENE_FUE === 'true'`, otherwise refuse before HTTP. Validates tenant/study/patient/original asset, SHA-shaped identities, source pixel dimensions, all landmarks within original pixels, and nonclinical proof fields. Fetches original bytes and compares **actual browser SubtleCrypto SHA-256** to source digest before allowing display. EXIF orientation 2–8 is **explicitly refused in this first UI candidate**, not silently rotated; backend M2 covers all orientations in a separate lab.
- `frontend/src/features/ortho/components/CephPremiumSceneFUEViewer.tsx`: *not mounted*, isolated React component. Displays authenticated verified source bytes in an SVG with original native pixel viewBox; pointer transforms use inverse SVG screen matrix to obtain source pixels; keyboard arrow correction for selected landmark; edited landmark becomes `PRACTITIONER_EDIT`, confidence reset; measurements become `UNAVAILABLE`; CAS revision POST followed by independent GET comparing saved/reopened SHA. Errors hide the original until a valid authenticated source read.
- `frontend/src/features/ortho/cephPremiumSceneFUEClient.test.ts` and `frontend/src/features/ortho/components/CephPremiumSceneFUEViewer.test.tsx`: Vitest/React Testing Library **mock frontend tests only**. Not an actual browser or Desktop screenshot. The mocked-server tests do not verify the combined HTTP→React behavior.
- Same PR GitHub workflow adds a separate frontend-only job `m2-react-svg-scene-fue-contract` for six mock-only tests, exact SHA, absence of app imports and JUnit/JSON evidence marked `native_desktop_fue_complete=false`.

## Local observable gate
On Windows dev test setup after `npm ci --ignore-scripts`: **6/6 targeted Vitest tests PASS**. First React mock test required correcting its synthetic URL object cleanup before proper unmount; the final rerun passed all six. A TypeScript compiler full-project check was started; its final exit/result must be recorded separately and no typecheck PASS should be inferred before completion.

## Boundaries / STOP
Not an implemented J2.1 M2–M6 product milestone or FUE-G. No actual clinic media, no runtime LLM, no ONNX inference, no approved index→anatomy, mm calibration, six auto-contours, diagnosis or PDF. Reuse of the historical public ANUG film belongs to detached earlier lab, **not** to the new SVG mocked test. No migration, clinical routing, merge or deployment.

## NEXT
1. Validate frontend CI on exact new SHA and check any typecheck or JS bundling failures.
2. In an explicitly disposable local app runtime, mount the candidate in a **test-only** viewer with the authenticated source API; execute real browser click/keyboard/crop and capture BEFORE/ACTION/AFTER at 390/430/768/1280 using synthetic or permitted public images. Do not call it Desktop FUE if outside the native app.
3. Run actual native Digital Crown Desktop installable FUE-G with real authentication, local DB/media, original→edit→save→app restart→reopen, SVG/source SHA invariants, A/B/X controls, backup/restore if applicable. Clinical expert gate remains separate.
