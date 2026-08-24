# Digital Crown — Mobile Full Experience — roadmap récupérée

Date de récupération : 2026-08-24
Statut : reconstruction prudente depuis les preuves GitHub disponibles.

## Règle

Ce document ne réinvente pas les anciens labels absents de `master`. Seuls les lots dont le nom et l'état sont prouvés par PR, closeout ou harness sont inscrits.

## Preuves historiques retrouvées

- **M1 — baseline mobile** : audit-only PR #225. 8 surfaces (`onboarding`, `agenda`, `finance`, `lab`, `assistant`, `security`, `dentists`, `superadmin`) × 390/430/768. Il s'agit d'une baseline, pas d'un lot produit revendiqué CLOSED.
- **M6.1 — Security-first pairing and device sessions** : CLOSED, PR #229 + hotfix #230.
- **M6.2 — Offline Truth** : CLOSED, PR #231, closeout `docs/MOBILE_M6_2_OFFLINE_TRUTH_CLOSEOUT.md`.
- **M6.3 — Patient/RDV canonique + Agenda UX** : CLOSED, PR #232, closeout `docs/MOBILE_M6_3_PATIENT_AGENDA_CLOSEOUT.md`.

Les anciens labels M0/M2/M3/M4/M5 ne sont pas suffisamment récupérables depuis `master` et ne sont donc ni nommés ni crédités ici.

## M6.4 — Contextual QR Bridge — ACTIVE

### Pourquoi ce lot est le prochain prouvé

La PR M6.1 excluait explicitement le `contextual QR bridge`. M6.2 puis M6.3 ont fermé leurs scopes respectifs. Le code courant confirme que cette dette reste réelle :

1. `GET /api/admin/zka-key-qr` génère uniquement un QR vers `/mobile/onboarding?token=...` ; aucune destination mobile n'est transportée.
2. Le backend accepte `target_user_id`, mais `MobileSecurity.tsx` appelle l'endpoint sans ce paramètre : l'identité cible n'est pas sélectionnable dans l'UI.
3. `OnboardingScanner` redirige toujours vers `/mobile/dashboard` après appairage.
4. `useMobileDashboard` initialise toujours `activeTab='agenda'` et ne lit aucun deep-link.
5. Les surfaces mobiles réelles déjà disponibles sont : Agenda, Finance, Labo, Assistant, Sécurité, Équipe praticiens et SuperAdmin.

### Goal

Transformer le QR mobile d'un simple code d'appairage en **pont explicite vers l'expérience mobile complète**, sans exposer de donnée patient dans le QR et sans contourner les permissions.

### Succès

- l'admin choisit explicitement l'utilisateur mobile cible avant génération ;
- le QR porte uniquement un secret éphémère + une destination mobile allowlistée, jamais un nom patient, patient_id, téléphone ou donnée clinique ;
- destinations initiales : `agenda`, `finance`, `lab`, `assistant`, `security`, `dentists`, `superadmin`, avec fallback sûr `agenda` ;
- après appairage, la destination demandée est réellement ouverte ;
- `/mobile/dashboard` sait hydrater son onglet depuis un deep-link allowlisté ;
- destination incompatible/non autorisée/altérée => fallback sûr, jamais bypass RBAC ;
- identité ciblée affichée dans le panneau desktop avant révélation du QR ;
- 390/430/768 mobile + 768/1280 bridge desktop : zéro overflow, zéro erreur runtime, contrôles tactiles >=44 px ;
- tests backend + frontend + CI exact-head + AFTER avant merge.

### Preuve

BEFORE + mockup + implementation + AFTER doivent être obtenus avant de déclarer M6.4 CLOSED.

## Progression globale

Non chiffrable proprement tant que les anciens labels M0/M2–M5 ne sont pas récupérés. Aucun pourcentage n'est inventé.

Aucun Vercel.
