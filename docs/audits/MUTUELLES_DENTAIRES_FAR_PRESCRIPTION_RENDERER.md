# FAR prescription renderer — V4 visual contract

## Goal

Copy only explicit fields from an archived Digital Crown ordonnance into logical Page 2 `ORDONNANCE` of the cabinet-validated FAR 2021-1 derived reference, without inference and without changing the clinical source of truth.

## Frozen source

- Classification: `CABINET_VALIDATED_DERIVED_REFERENCE`
- SHA-256: `c953d74f25ee5e3160683f16c45783448d55ea89640c710653a3e2cbf782bf42`
- Physical page: 2 / logical Page 2 left half

## V4 visual decision

Cabinet review accepted the V4 direction:

- patient name aligned with the printed `Nom et prénom du malade` row;
- patient name shifted right by the requested visual spacing;
- fixed PDF font, independent from Digital Crown UI theme;
- medication line: 9 pt;
- posology line: 8.2 pt;
- patient name: 9.6 pt;
- no silent truncation: unrepresentable content fails closed.

## Coordinates

PDF points on physical page index 1:

- patient name: `(292, 76)`
- first medication: `(145, 108)`
- first posology: `(155, 124)`
- subsequent medications: `+40 pt` vertically

## Safety contract

- exact template SHA required;
- archived source ordonnance id required;
- explicit medication name required;
- no molecule/dose/form/posology inference;
- maximum six medication blocks in this calibrated profile;
- overflow fails closed rather than truncating clinical text;
- no signature/cachet/insurer-decision rendering.

## Status

Renderer implementation started on `feat/far-prescription-renderer`. Wiring into the document/archive flow, executable CI proof and application AFTER capture remain required before merge.
