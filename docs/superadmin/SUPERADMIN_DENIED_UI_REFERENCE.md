# Superadmin denied UI reference

## Goal
When the authoritative Superadmin API returns HTTP 403 for an authenticated user, render no Superadmin shell, metrics, client data, activation form, navigation or privileged controls.

## Reference state
A single neutral access state centered in the viewport:

- shield icon;
- title: `Accès Superadmin non autorisé`;
- short explanation: `Votre session ne dispose pas d’une autorisation plateforme.`;
- no retry or privilege-escalation action;
- no `user.is_superadmin` frontend gate. Backend 403 remains the source of truth so delegated platform operators continue to work.

## Visual success
Same deterministic denied scenario as BEFORE at 390×844, 430×932, 768×1024 and 1280×800:

- denied state visible;
- `SuperAdmin`, `Gestion Globale des Licences & Clients`, `Total Clients` and `Générer un code d'activation` absent;
- no horizontal overflow;
- no browser page errors.

BEFORE reference product SHA: `6e2280214ff6cefc8512b1978179bfe9d0209049`.
