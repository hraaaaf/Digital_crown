# Patient P7 — consolidation stack

Ce fichier décrit uniquement la consolidation préparatoire au gate final. Il ne déclare pas P7 terminé.

- Base produit conservée : P6 final `2a0ac2ade90f2bae99c6e7c11302755d856a730e`.
- P5 courant est déjà inclus dans P6.
- P2 : produit déjà inclus ; certificat réintégré dans l'arbre final.
- P3 : `ClinicalHub.tsx`, `PatientP3ClinicalAssistantBoundary.test.ts`, `AssistantOrtho.tsx`, `AssistantParo.tsx`, `AssistantProthese.tsx` réintégrés depuis `02126a646322d1c1d98351ea33489384be49ab57`.
- P4 : aucun écrasement de `PatientDetailsInner.tsx`; la version P6 conserve le RBAC strict Imagerie et ajoute le RBAC Finances.
- Test P0 final fusionné : assertions Clinique P3 final + assertions financières/neutralité/PDF P6.
- Gate P7 ajouté : tests ciblés P0→P6, build, persistance relue, 40 captures.
- Aucun Vercel.
