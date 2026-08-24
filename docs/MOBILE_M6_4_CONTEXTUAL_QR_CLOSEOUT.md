# Mobile M6.4 — Contextual QR Bridge — CLOSEOUT

Date: 2026-08-24
Status: CLOSED
Classification roadmap: correction prioritaire / fondation du Mobile Bridge. **Ce lot ne ferme pas le M4 original**, qui exige encore le contexte ressource exact Patient / Radio / Document / RDV.

## Goal

Sécuriser et rendre explicite le passage desktop → mobile : choisir un utilisateur mobile autorisé et une destination autorisée, transmettre uniquement un secret éphémère sans PHI, puis résoudre et revalider la destination côté serveur après l'appairage.

## Résultat livré

- `/api/mobile/bridge-options` : cibles et destinations dérivées du RBAC serveur.
- `/api/mobile/bridge-pairing` : utilisateur cible + destination, token QR opaque haute entropie, code manuel séparé, TTL court.
- Aucune donnée patient/clinique ni identifiant de ressource sensible dans le QR.
- `/api/mobile/bridge-destination` : résolution après claim, identité user/tenant/device vérifiée, permissions actuelles réévaluées.
- Retrait de permission après génération : fallback sûr vers Agenda.
- SuperAdmin uniquement via vérité serveur SuperAdmin.
- Destinations allowlistées : Agenda, Finance, Labo, Assistant, Sécurité, Équipe praticiens, SuperAdmin.
- Security desktop : utilisateur + destination + CTA explicite.
- Onboarding : destination serveur affichée après succès, token retiré de l'URL.
- Dashboard : deep-link via React Router `useLocation().search`; destination invalide → Agenda.
- Corrections tactiles onboarding sur 390/430/768.

## Preuves exact-head

- Branche : `mobile/m64-contextual-qr-bridge`.
- PR : #234.
- Base : `a07e7b9c9e6e87ec260eb7ebcb8bb630e836fd8e`.
- HEAD certifié : `caaeabc1de9c10bc056ea1063ec83295b099b771`.
- Intégrité avant merge : 1 commit / 9 fichiers / ahead 1 / behind 0.
- Merge master : `ea0f6e41f055b90d8bceabb5e100dbe008230f16`.
- CI #1793 : SUCCESS.
- Backend : **2791 passed, 8 skipped, 4 warnings, 0 failed**.
- Frontend tests + build : SUCCESS.
- Garde production négative : SUCCESS.
- Settings Security Visual #27 : SUCCESS.
  - `certify` : SUCCESS.
  - `m64-e2e` : SUCCESS.
- T2 Runtime Browser #961 : SUCCESS.
- Catalog Connected Truth #234 : SUCCESS.
- Patient P7 #260 : SUCCESS.
- Aucun Vercel.

## UI/UX — BEFORE → cible → AFTER

### BEFORE

- Bridge desktop : 768x1024 et 1280x900.
- Onboarding : 390x844, 430x932, 768x1024.
- 0 erreur runtime au baseline.
- Défauts mesurés : aucun contexte de destination ; helper iOS ~17 px ; formulaire/code géométriquement coupé à 390 px.

### Cible / mockup

- Utilisateur cible explicite.
- Destination explicite.
- CTA de génération dominant.
- Contrôles tactiles ≥44 px.
- Aucun PHI dans le QR.
- Après appairage : ouverture de la destination résolue par le serveur.

### AFTER exact-head

Artifact `mobile-m64-final-after`, HEAD `caaeabc1de9c10bc056ea1063ec83295b099b771` :

- 13/13 captures produites.
- 0 erreur console/page/runtime.
- 0 overflow horizontal.
- 0 contrôle critique sous 44 px.
- `safePairingBodies=true`.
- protocole `claim-token → bridge-destination` observé.
- Finance visible 3/3 sur 390x844, 430x932, 768x1024.
- Inspection humaine réalisée sur bridge 1280/768, onboarding 390, succès pairing 390 et arrivée Finance 390.

**Score UI/UX : 9,5/10.**

Le lot n'est pas noté 10/10 : il ne couvre ni le benchmark performance dédié ni le Mobile Bridge ressource complet du M4 original.

## Défauts découverts et corrigés pendant la certification

1. Dashboard lisait `window.location.search` : vraie navigation React Router vers Finance non appliquée dans le contexte router. Correction : `useLocation().search` + test anti-régression.
2. Harness E2E montait initialement le dashboard sans la garde de pairing réelle : scénario aligné sur `MobileProtectedRoute`.
3. Fixture E2E utilisait un faux access token non-JWT, provoquant correctement un refresh puis une invalidation ; remplacée par un JWT synthétique décodable à expiration future. Aucun assouplissement des erreurs console.

## Limites / suite

Le M4 original reste **IN PROGRESS**. Il exige encore :

- Patient précis → QR → ce patient ;
- Radio précise → QR → cette radio ;
- Document précis → QR → ce document ;
- RDV précis → QR → ce rendez-vous ;
- expiration, révocation, retour arrière, ressource supprimée, non-autorisé, non-pairé et backend local inaccessible certifiés au niveau ressource.

Aucun Vercel.
