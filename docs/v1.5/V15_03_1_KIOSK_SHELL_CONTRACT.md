# V1.5-03.1 — Kiosk Shell Contract

Status: implementation contract for V1.5-03.1 only.

## Goal
Provide a dedicated public-facing Station shell that is visually complete, touch-first and locked away from clinical navigation. Do not implement patient identification, appointment arrival, queue ordering, Wall Display, or self-service documents in this sub-lot.

## Invariants
1. /station never renders MainLayout, clinical navigation, patient data, appointment data, finance data, settings, or links to protected clinical routes.
2. A workstation configured in station mode remains server-authoritatively locked by WorkstationModeGate.
3. Leaving Station requires the existing hidden admin activation plus server-verified owner PIN escape. No client-only bypass.
4. Public interaction inactivity returns the shell to its public home state and clears any ephemeral UI state. The timeout is configurable by the shell consumer and clamped to 30–120 seconds.
5. The public shell exposes a permanent FR / AR / EN language selector. Arabic renders RTL; FR and EN render LTR. V1.5-03.1 uses explicit bounded copy only; it does not add runtime translation.
6. Touch targets are at least 44px high and usable without hover.
7. Public actions in 03.1 are placeholders/navigation states only: “J’ai rendez-vous”, “Retirer un document”, “Besoin d’aide”. They must not call clinical APIs in this sub-lot.
8. No camera capture, CIN reading, queue engine, patient lookup, document delivery, or wall-display behavior is implemented in 03.1.
9. If workstation bootstrap cannot be read, the restrictive Station recovery surface may render, but no clinical route becomes available.
10. Visual evidence must cover 390 / 430 / 768 / 1280 and 200% root text scaling with zero horizontal overflow and zero page errors.

## Success
- public Station home is clearly distinct from Cabinet;
- no clinical escape path is visible;
- hidden admin gesture and PIN flow remain functional;
- idle timeout returns to public home and clears transient shell state;
- FR / AR / EN switch is keyboard/touch accessible and Arabic direction is correct;
- exact-head unit tests, build and AFTER visual evidence pass.

## Explicit non-goals
- 03.2 workstation enrollment/revocation UX;
- 03.3 patient identity, QR/NFC protocol and anti-replay tokens;
- 03.4 appointment arrival bridge;
- 03.5 Wall Display and patient calling;
- 03.6 final cross-cutting security/offline certification.
