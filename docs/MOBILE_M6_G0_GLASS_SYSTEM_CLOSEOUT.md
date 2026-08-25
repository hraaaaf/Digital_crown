# Digital Crown — Mobile M6-G0 Glass System — Closeout

Date : 2026-08-25

## Goal

Appliquer au produit mobile réel un glassmorphism premium, discret et cohérent, en réutilisant les tokens du design system existant, sans modifier les flows, données, routes, permissions ni stockage.

## Produit certifié

- PR : #249
- HEAD produit : `d5c13f02233304c809984052ff518b1e78807a6a`
- Base produit : `13b79f572b6a62f6c743f75f4d93b841454d3417`
- Scope : 1 commit / 4 fichiers / 0 changement métier
- Merge : `1dd5de04602e3a0e4cdc97c690cabe1d06ea5d66`

Fichiers produit :

- `frontend/src/main.tsx`
- `frontend/src/styles/mobileGlassSystem.css`
- `frontend/src/features/mobile/Dashboard/MobileDashboard.tsx`
- `frontend/src/features/mobile/Onboarding/OnboardingScanner.tsx`

## BEFORE

- Run : `32848140147` — SUCCESS
- Produit exact : `13b79f572b6a62f6c743f75f4d93b841454d3417`
- Artifact : `9563188564`
- Digest : `sha256:f0c5123f6561f269b462ce1e3d9671377a4d6b1be7055aad2d8ac4b133f2e7e2`
- 5 captures : Onboarding 390, Dashboard 390/768, Contexte RDV 390/768
- Défaut visuel confirmé : surfaces structurantes propres mais trop plates/opaques pour le standing visé.

## Référence visuelle verrouillée

Direction : verre dépoli léger, profondeur douce, bordure lumineuse subtile, palette clinique froide, CTA principaux opaques, sans glassifier les inputs ni les micro-badges.

## Implémentation

- source de vérité conservée : `--glass-bg` / `--glass-border` ;
- surfaces structurantes uniquement : onboarding, dashboard, cartes, navigation, modales et contextes mobiles ;
- blur 18 px + saturation modérée + ombre douce ;
- pas de blur additionnel sur micro-badges ;
- pas de `background-attachment: fixed` ;
- high-contrast : surfaces opaques, gradients neutralisés, blur désactivé ;
- fallback sans `backdrop-filter` ;
- support `prefers-reduced-transparency` ;
- aucune logique métier modifiée.

## Préparation

- Run final : `32849294785` — SUCCESS
- scope exact validé ;
- frontend build validé avant création du commit produit final.

## AFTER

- Run exact-head : `32849502779` — SUCCESS
- Artifact : `9563723488`
- Digest : `sha256:a162eba05d358cae6108c2401c409d8f3215444ab591ea0f0fa994622f2e5d57`
- 5 captures AFTER inspectées : Onboarding 390, Dashboard 390/768, Contexte RDV 390/768
- 0 overflow ;
- 0 erreur runtime ;
- fallback high-contrast certifié ;
- score visuel : **9,4/10**.

## CI exact-head

Tous verts sur `d5c13f02233304c809984052ff518b1e78807a6a` :

- CI #1845 — run `32849572994`
- T2 Runtime Browser Certification #1001 — run `32849573068`
- Catalog Connected Truth Certification #274 — run `32849572969`
- Patient P7 Final Certification #300 — run `32849572989`
- Settings Security Visual Certification #38 — run `32849572859`

## Décision

**M6-G0 CLOSED.** Le système glass premium devient la fondation visuelle mobile pour les lots suivants.

Aucun Vercel n'a été déclenché.
