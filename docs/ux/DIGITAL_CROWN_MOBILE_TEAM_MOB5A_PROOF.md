# Digital Crown — MOB-5A Équipe / praticiens — Proof

Status: CERTIFIED ON PR CANDIDATE
Date: 2026-09-05
Repo: `hraaaaf/Digital_crown`
Branch: `audit/mobile-secondary-value-mob5`
PR: `#357`
Branch HEAD certified: `51f694f5066e1f6c8208e07286205e421cc226f9`
Runtime merge-ref candidate recorded by visual workflow: `d2c9c47d61b1f582524713d2900968a7b4b2a2fe`
Deployment: none

## Goal

Rendre l’aperçu Équipe / praticiens accessible depuis la navigation mobile canonique, dans le même shell que le reste de l’application, sans hardcoding de marque/typographie et sans casser les deep links ou permissions existants.

## Success criteria

- entrée `Plus → Équipe` accessible ;
- navigation canonique à 5 entrées préservée ;
- permissions héritées du contrat mobile `agenda` ;
- vue intégrée au shell mobile canonique ;
- thème/typographie pilotés par les réglages runtime ;
- aucun overflow horizontal à 390×844, 430×932 et 768×1024 ;
- aucune erreur runtime navigateur ;
- tests ciblés + build + runtime CI verts.

## BEFORE / audit

Audit source effectué avant implémentation :
- la route `/mobile/dentists` existait déjà ;
- la vue `DentistsView` utilisait encore une typographie locale `font-outfit` et un fallback de couleur de marque ;
- la vue sortait du shell/navigation canonique ;
- l’accès n’était pas exposé proprement depuis `Plus`.

Goal UI : `docs/ux/DIGITAL_CROWN_MOBILE_TEAM_MOB5A_GOAL_UI.md`.

## Implementation

- ajout de l’entrée `Équipe` dans `Plus` pour les rôles autorisés ;
- intégration de la destination dans le routage/dashboard mobile canonique ;
- deep link `dentists` conservé ;
- suppression des hardcodings locaux de police/couleur de marque dans la vue ;
- tests de bridge/routage et navigation mis à jour ;
- workflow dédié de certification visuelle ajouté.

## AFTER — certification visuelle

Workflow : `Mobile Team MOB-5A Cert`
Run : `33963384867` — **SUCCESS**
Artifact : `9968666702` — `mobile-team-mob5a-after`
Digest : `sha256:6a463707a1c7dbe2bb9623db1e3b19b631d267294ad08dc6bb32dcb729929385`

Viewports certifiés :
- `390×844` ✅
- `430×932` ✅
- `768×1024` ✅

Mesures automatiques sur les 3 viewports :
- 5 boutons permanents dans la nav ✅
- hauteur nav 76 px ✅
- overflow horizontal : aucun ✅
- erreurs runtime : aucune ✅
- font runtime observée : `Inter, system-ui, sans-serif` ✅

Inspection visuelle manuelle de l’artifact :
- titre et shell cohérents avec Digital Crown ;
- barre `Aujourd’hui / Patients / + / Assistant / Plus` intacte ;
- aucune collision ou découpe sur 390/430 ;
- 768 px volontairement aéré en preview faute de données cabinet réelles, sans faux contenu injecté ;
- état offline/demo explicite, donc aucune fausse donnée praticien présentée comme réelle.

Score visuel : **9.2 / 10**.

## Validation technique croisée

Sur le même branch HEAD `51f694f5066e1f6c8208e07286205e421cc226f9` :
- CI `33963384865` — **SUCCESS** ✅
- T2 Runtime Browser Certification `33963384839` — **SUCCESS** ✅
- Settings Security Visual Certification `33963384838` — **SUCCESS** ✅
- Mobile Team MOB-5A Cert `33963384867` — **SUCCESS** ✅
- M6-I Biometric Passkey Certification : skipped, non concerné.

## Conclusion

MOB-5A satisfait les critères observables du lot sur le candidat PR. Le lot peut être mergé sans déploiement Vercel. La prochaine implémentation produit est MOB-5B Frontdesk / demandes RDV, dont l’audit interne est déjà préparé.
