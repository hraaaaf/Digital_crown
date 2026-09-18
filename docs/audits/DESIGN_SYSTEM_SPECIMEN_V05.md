# Digital Crown — Design System specimen v0.5

## Goal
Create one reproducible technical specimen from the real Digital Crown tokens and repeated UI patterns, without changing any production route, clinical behavior, API, database, or patient data.

## Success
- isolated React component only;
- no import from App.tsx/main.tsx;
- no route mounted;
- semantic global tokens reused;
- primary/secondary/destructive actions represented;
- standard and compact form densities represented;
- empty/loading/error states represented;
- destructive confirmation represented;
- default/dark/high-contrast selectors represented.

## Proof boundary
This commit is **not** a visual certification. It intentionally does not mount the specimen into the product. Therefore no AFTER screenshot is claimed yet.

File:
`frontend/src/design-system/DesignSystemSpecimen.tsx`

## Safety
The specimen has:
- no API client;
- no backend call;
- no persistence;
- no patient fixture;
- no product route;
- no import from production entrypoints.

## Next gate
Create a deterministic preview/certification harness that mounts only this specimen, then capture 390×844, 768×1024 and 1280×900 in default/dark/high-contrast. Compare against the Design Compass before considering shared primitive extraction.
