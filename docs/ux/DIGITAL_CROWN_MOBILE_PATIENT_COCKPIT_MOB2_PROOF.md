# Digital Crown — Mobile Patient Cockpit — MOB-2 Proof

Status: CERTIFIED
Date: 2026-09-04
Repo: `hraaaaf/Digital_crown`
Branch: `ux/mobile-patient-cockpit-mob2`
Certified candidate: `2a01e58d4bf3e3deff833723a52e3449bb26e4ac`
Deployment: none. No Vercel deployment authorized or performed.

## Goal

Implémenter un Patient Cockpit mobile permettant au praticien de rechercher un patient, voir son contexte critique et lancer les actions utiles rapidement, sans transformer le téléphone en dossier patient desktop réduit.

## Success

MOB-2 est certifié seulement si :

- thème et `font_fr` proviennent des Réglages cabinet ;
- recherche + synthèse patient sont disponibles ;
- alerte médicale est prioritaire ;
- appel / WhatsApp sont utilisables ;
- prochain RDV est visible ;
- finance est filtrée par permissions ;
- photo / scan / document / panoramique réutilisent les context bridges mobiles ;
- changement de patient purge l’état précédent avant chargement ;
- contextes opaques restent liés au tenant, utilisateur et appareil ;
- offline est explicite ;
- non-régression M4/M6 proportionnée passe ;
- build, syntaxe backend et runtime passent ;
- AFTER 390 / 430 / 768 existe et est comparé au BEFORE + Goal UI.

## BEFORE

Run: `33880152997` ✅
HEAD: `3ecfa47c449d9724d9517003499ec3e3ec4f730d`
Artifact: `9939517547`
Digest: `sha256:7a3b97a4e7b1b7fe652d40f9496fca88dcf2a441149437ed00f403334e7c226f`
Viewports: `390×844`, `430×932`, `768×1024`.

## Certified AFTER

Run: `33889545163` ✅
HEAD: `2a01e58d4bf3e3deff833723a52e3449bb26e4ac`
Artifact: `9943369750`
Digest: `sha256:b4d274590a3349cbcab8a71faeb25e880acc3aee4ab818420fab8918813777fd`
Viewports: `390×844`, `430×932`, `768×1024`.

Artifact contents:

- `after-dashboard-390x844.png`
- `after-dashboard-430x932.png`
- `after-dashboard-768x1024.png`
- `after-patient-cockpit-390x844.png`
- `after-patient-cockpit-430x932.png`
- `after-patient-cockpit-768x1024.png`
- `result.txt`
- `vite.log`

## Automated proof on exact candidate

Workflow `Mobile Theme Runtime Certification`, run `33889545163`:

- runtime theme / offline / inter-patient isolation ✅
- proportional M4/M6 frontend non-regression ✅
- Patient Cockpit tenant / finance / device gates ✅
- proportional M6 backend bridge non-regression ✅
- production frontend build ✅
- backend route syntax ✅
- Chromium evidence runner ✅
- dashboard + Patient Cockpit AFTER captures ✅
- exact PNG dimensions ✅
- artifact upload ✅

Targeted frontend matrix reused where relevant:

- M4-A patient contextual bridge
- M4-B panoramic contextual bridge
- M4-C document contextual bridge
- M6.2 offline queue / retry / refresh / revocation
- M6.4 contextual bridge
- M6-E patient communication
- M6-F document share
- M6-H image viewport

Targeted backend matrix reused where relevant:

- M6-A clinical photo
- M6-B document scan

## Security corrections verified

- Patient read model is tenant-scoped and encrypted.
- Finance follows the same `accounting` / `payments` permission contract as P6.
- Selecting another patient purges previous patient identity/resources before network loading.
- Late responses from the prior selection are ignored by effect cleanup.
- Patient Cockpit context creation requires a mobile `device_id`.
- Context response exposes an opaque key, not patient/resource identifiers.
- Context binding records tenant, target user, device, resource type and resource id server-side.
- Misleading `expires_in=1800` response field was removed because expiry was not directly enforced by the resolved-context contract.

## Visual comparison

Reference: `docs/ux/assets/MOBILE_PATIENT_COCKPIT_GOAL_V1.svg`.

Observed across 390 / 430 / 768:

- visual language remains consistent with the existing Digital Crown mobile shell;
- identity hierarchy is strong;
- medical alert is immediately visible;
- Appeler / WhatsApp are prominent;
- clinical quick actions are readable and touch-friendly;
- 768 px remains a mobile/tablet cockpit rather than a desktop replica;
- no horizontal overflow or runtime error was accepted by the certification gate.

Known visual deviations from the MOB-1 mockup:

1. clinical quick actions appear before the next appointment;
2. the search input is replaced by `Tous les patients` after a patient is selected;
3. the target bottom navigation is intentionally not implemented in MOB-2 because it belongs to MOB-4;
4. quick payment / `Encaisser` is intentionally not part of MOB-2 closeout because it belongs to MOB-3.

### Visual score

**9.2 / 10 for MOB-2 scope.**

The score is not 10/10 because the information order differs from the mockup and the selected-patient state trades persistent search for a back-to-search action. Neither gap blocks the MOB-2 Goal.

## Conclusion

MOB-2 software and visual scope is certified on immutable candidate `2a01e58d4bf3e3deff833723a52e3449bb26e4ac`.

No physical biometric/push behavior is inferred from this certification. Those remain governed by the global mobile certification matrix.

## Next exact

Close MOB-2 in `DIGITAL_CROWN_MOBILE_PRODUCT_CANONICAL.md`, align the MOB-1 Goal UI status, open the PR, validate PR CI, merge if green, verify post-merge, then start MOB-3 with its own BEFORE → Goal UI → mockup gate before implementation.
