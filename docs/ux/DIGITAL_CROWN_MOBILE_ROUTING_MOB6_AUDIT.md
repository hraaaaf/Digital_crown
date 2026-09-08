# DIGITAL CROWN — MOB-6 Canonisation du routage mobile — Audit

## Baseline
- master initial : `301454a367b8b7952d0fef94e86c40e8e4a248e2`
- branche produit : `ux/mobile-routing-mob6`

## Goal
Supprimer l’ambiguïté entre la PWA mobile dédiée et le shell desktop responsive, sans casser l’accès desktop, l’onboarding, l’offline, la biométrie, les context bridges ni les routes publiques.

## Succès observable
- une entrée mobile ne tombe plus silencieusement dans le shell desktop pour les parcours déjà couverts ;
- les routes `/mobile/*` inconnues restent dans le domaine mobile ;
- desktop reste inchangé ;
- aucun deep-link riche n’est redirigé si son contexte exact ne peut pas être préservé ;
- BEFORE/AFTER 390×844, 430×932 et 768×1024 sans overflow/page/console error ;
- CI PR et T2 verts ;
- post-merge master vert avant CLOSED.

## Baseline vérifiée
`SmartRootRouter` appliquait la détection mobile uniquement à `/`. Les deep-links directs `/patients`, `/agenda`, `/stock`, etc. restaient dans le pipeline desktop. Une route `/mobile/*` inconnue pouvait également atteindre le wildcard desktop.

BEFORE final :
- run `34211312980` — SUCCESS ;
- code testé `d5bf9439e8eae60c1d0c8616a92353041fb5ac9a` ;
- artifact `10049990601` ;
- digest `sha256:c89e86a107100e1596187291f9650c12bf716ffcc95c225efd4e670230b1eef4` ;
- 9/9 probes : `/patients`, `/agenda`, `/stock` × 390/430/768 restent desktop ;
- onboarding mobile absent ; 0 overflow ; 0 page error.

## Implémentation certifiée
- canonisation au bootstrap dans `main.tsx` avant auth/rendu ;
- règle mobile historique conservée ;
- URLs résolues via `MOBILE_BRIDGE_ROUTES` ;
- `waiting-room` ajouté au bridge canonique ;
- `/mobile/*` inconnu retombe vers Agenda mobile ;
- `MobileProtectedRoute`, cache offline et biométrie inchangés ;
- routes publiques/auth non redirigées ;
- deep-links riches préservés desktop.

### Scope certifié
`/dashboard`, `/agenda`, `/patients`, `/accounting`, `/stock`, `/approvisionnement`, `/bibliotheque`, `/salle-attente`, `/super-admin`.

## Certification finale
- AFTER run `34211780896` — SUCCESS ;
- HEAD certifié `e62217739c14c46747c159d9c3be9f76668c7a30` ;
- routing contract SUCCESS ; frontend build SUCCESS ; browser 390/430/768 SUCCESS ;
- 0 overflow ; 0 page error ; 0 console error ;
- artifact `10050137272` ;
- digest `sha256:dc1e5a72d02f668cf537ec9fa28341940d34df7388603da6974eeac393d82ec7` ;
- score visuel/comportemental **9.4/10**.

## PR / merge / post-merge
- PR produit `#372` ;
- HEAD final PR `8904dae5d82e218d5c73273042d85b966d929f11` ;
- CI PR `34212226491` — SUCCESS ;
- T2 `34212226402` — SUCCESS ;
- merge exact `97546777e3b4adbb8a670559553c1079aad4c2e2` ;
- post-merge master `34226941958` — SUCCESS.

## Risques préservés
- routes publiques/auth non redirigées ;
- `/mobile/onboarding` reste hors biométrie ;
- `MobileProtectedRoute` inchangé ;
- cache offline inchangé ;
- biométrie inchangée ;
- deep-links riches préservés ;
- aucun déploiement Vercel.

Statut : `AUDIT VERIFIED — MERGED — POST-MERGE VERIFIED — CLOSED`.
