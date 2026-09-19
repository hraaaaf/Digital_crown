# V1-07 — LOT 3 SuperAdmin — Goal UI

Date: 2026-09-19

## Goal
Make desktop/mobile SuperAdmin commercial actions truthful for GOLD, PREMIUM and ELITE while preserving existing layout and confirmation semantics.

## BEFORE risks
- desktop incompatible downgrade can replace the precise backend 409 detail with a generic error;
- renewal button says Email while backend sends WhatsApp;
- no-phone or transport failure can be represented as success by the backend.

## Target
- desktop downgrade shows the exact backend reason;
- renewal action is labelled WhatsApp;
- no phone = 409, transport failure = 502, success only after confirmed transport success;
- desktop/mobile pack selectors and licence/CRM actions stay wired to the real request contracts.

## Evidence
Matched BEFORE/AFTER viewports:
- 1024 × 900
- 1440 × 1000

Desktop visual scenarios:
1. incompatible ELITE → GOLD downgrade;
2. renewal with no phone.

Mobile behavior is covered by exact request-layer and confirmation tests; no mobile production UI change is introduced in LOT 3.

No Vercel deployment.
