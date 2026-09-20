# PC-03 — UI Target

## BEFORE
PC-02 home: appointments/resources + self-service agenda. No questionnaire surface.

## Goal
Add a compact "Questionnaires" card to Patient Companion home, consistent with the existing mobile visual language.

## Target
- section title: "Questionnaires médicaux";
- each card shows title, version-independent human label, estimated state only: À compléter / Envoyé · en attente de revue / Revu par le cabinet;
- primary action: "Remplir" or "Voir l'envoi";
- form is one-column mobile-first;
- supported question types in PC-03 initial scope: yes/no, single choice, short text;
- mandatory items are explicit;
- submission confirmation states: "Envoyé au cabinet · en attente de revue";
- offline/transport failure states must never say "envoyé" before an authenticated ACK;
- no red clinical alerts, diagnosis, risk scores or automated interpretation.

## Viewports
Chromium + WebKit at 360x800 and 390x844.

## Visual acceptance
No horizontal overflow, no clipped actions, no ambiguous clinical status, no confusion between patient-reported and clinician-reviewed data.
