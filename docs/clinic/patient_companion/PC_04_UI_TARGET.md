# PC-04 — Consent Vault patient-facing — UI TARGET

Status: TARGET LOCKED
Base reference: Patient Companion PC-03 on master@86fc61a572f303c812f1999c887e35574df0bb49

## Goal
Add a compact Consent Vault section that lets an authorized patient review a cabinet-issued consent/document and record a patient signature against the exact document version, without implying a qualified electronic signature.

## BEFORE reference
Current Patient Companion home after PC-03:
- activation/context header;
- shared resources;
- questionnaires;
- agenda;
- no patient-facing consent-signature card.

## AFTER target
Add a **Consentements** card before the generic shared-resources list.

Each consent row exposes only:
- document title;
- document version;
- state: `À signer`, `Signature enregistrée`, `Expiré` or `Révoqué`;
- a clear `Lire et signer` action only while signable.

When opened:
1. short truth notice: “Votre signature sera liée à cette version exacte du document.”
2. explicit boundary: “Preuve applicative Digital Crown — ce statut n’est pas présenté comme une signature électronique qualifiée.”
3. signature canvas reusing the proven M6-C interaction pattern;
4. `Effacer` and `Enregistrer` controls >=48 px;
5. no success state before durable cabinet ACK;
6. transport/offline failure explicitly remains “non envoyé”.

## Evidence target
Same matched viewports:
- Chromium 360x800
- Chromium 390x844
- WebKit 360x800
- WebKit 390x844

Assertions:
- no horizontal overflow;
- touch controls >=48 px;
- empty signature cannot be submitted;
- exact state transition only after ACK;
- no raw internal document/patient/tenant identifiers exposed.

## Visual reference
Reuse Patient Companion card language and M6-C signature-pad ergonomics. Do not import the cabinet/mobile visual shell.
