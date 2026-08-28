# Digital Crown — Mobile Preview Demo Isolation — Closeout

Date : 2026-08-28

## Goal

Permettre sur le Preview Vercel dédié uniquement d'entrer dans une surface Mobile de démonstration sans QR, backend cabinet, PHI ni credentials réels, tout en conservant l'appairage réel intact.

## État

CLOSED pour le lot Preview Demo Isolation. Ce closeout ne crédite aucune preuve de certification terrain iPhone/Android réelle du produit.

## Preuves vérifiées

- PR #287 mergée dans `master` via `8afbfd87864ffef5059aefd825950050a31d1429`.
- HEAD certifié avant merge : `fafd72ba18aa96c31397dcb7e9885040a55d3e58`.
- CI #1983 / run `33171988852` : SUCCESS.
- Frontend tests + build : SUCCESS.
- Garde production, M4-A, M4-B et M4-C : SUCCESS.
- Preview Vercel de démonstration vérifié READY ; aucun déploiement production autorisé ou réalisé dans ce lot.
- `git.deploymentEnabled` refermé à `false` après les déploiements Preview one-shot.
- AFTER sur vrai iPhone reçu le 2026-08-28 : onboarding Compagnon Mobile avec séparation explicite du mode démo, puis dashboard réel Digital Crown en mode démo.
- Libellés Preview finaux sans identité patient réaliste : `Patient 01` et motifs génériques.
- Aucun overflow horizontal visible sur la preuve iPhone finale.
- Score visuel final : 9,6/10.

## Isolation

- Mode démo explicitement identifié `MODE DÉMO — PREVIEW VERCEL`.
- Texte : `Aucune donnée cabinet • aucune session réelle`.
- Appairage QR/code réel conservé dans l'onboarding et séparé du chemin démo.
- Fixtures de démonstration sans PHI.
- Le chemin démo n'initialise pas `App`/auth-store comme une session réelle.
- Dashboard Preview isolé des appels backend cabinet ; CSP démo avec `connect-src 'none'`.
- Aucun faux JWT, token cabinet ou credential MobileStorage n'est présenté comme session réelle.

## UI/UX

Séquence obligatoire réalisée : BEFORE iPhone → Goal visuel → mockup/référence → implémentation → AFTER iPhone → comparaison.

Résultat final : identité visuelle Digital Crown conservée, CTA démo clair, vrai pairing secondaire mais présent, dashboard cohérent avec le produit. Score final 9,6/10.

## Limites explicites

Ce lot est un outil d'essai distant. Il ne certifie pas : biométrie physique Face ID/Touch ID/Android, Push OS réel, offline→reconnect terrain, révocation terrain ni l'ensemble des parcours critiques sur appareils physiques.

## Next exact

Certification terrain Mobile Full Experience sur vrai iPhone + Android : biométrie réelle, Push réel, offline→reconnect, révocation, pairing sécurisé et parcours critiques finaux, puis closeout global si aucun P0/P1.
