# M6-D2 — Push PWA / OS device-bound — Closeout

Date : 2026-08-26
État : **CLOSED**

## Goal

Activer un Web Push PWA réel sans affaiblir M6-D1 : chaque souscription est liée à l'appareil mobile appairé, à l'utilisateur et au cabinet authentifiés ; la révocation reste fail-closed ; le payload affichable par l'OS reste générique et sans donnée patient.

## Succès observé

- Web Push standard avec permission déclenchée uniquement par geste utilisateur.
- Souscription serveur liée à `device_id + user_id + employer_id` dérivés de l'identité mobile authentifiée.
- Appareils révoqués et utilisateurs non autorisés exclus de l'envoi.
- Conflit d'endpoint multi-appareil puis transfert après révocation testé dynamiquement.
- RBAC financier identique au centre de notifications M6-D1.
- Payload OS fixe et générique : aucun nom patient, montant, motif ou contenu clinique/financier.
- Désinscription locale et purge serveur des endpoints 404/410.
- Clé VAPID persistante privée ; perte/rotation détectée.
- HTTPS LAN cohérent frontend + API lorsque les certificats existent.
- UI Push certifiée sur 390 / 430 / 768 avec cibles >=48 px, zéro overflow et zéro erreur runtime.

## Preuves

- PR produit : #258.
- HEAD produit certifié : `23c402bbac770f6dd1deacaf88c48bdb3f1710ea`.
- Squash merge `master` : `bad5a21f7729001e54f36ed69876ff0f91030c77`.
- CI exact-head : run `32914297032` — **SUCCESS**.
  - `Tests & durcissement` backend : SUCCESS.
  - Frontend tests + build : SUCCESS, **472/472** tests.
  - Garde production : SUCCESS.
  - M4-A / M4-B / M4-C AFTER : SUCCESS.
- BEFORE canonique : run `32901108250`, artifact `9583139456`.
- Goal : `.audit/mobile-m6-d2-goal.md`.
- Mockup : `.audit/mobile-m6-d2-mockup.svg`.
- AFTER exact-head : run `32914367676` — **SUCCESS**.
- Artifact AFTER : `9587647257`.
- Digest AFTER : `sha256:c2fd9041e9c65eb979788546f64ee8a93b383d4975d52075c8e6e7f673cd79bb`.
- Viewports AFTER : 390×844, 430×932, 768×1024.

## Validation visuelle

Comparaison BEFORE → mockup → AFTER inspectée sur les trois viewports.

- Carte Push OS intégrée sans casser la hiérarchie M6-D1.
- Microcopy privacy visible : aucune donnée patient dans la notification OS.
- Actions `Lu` / `+24 h` préservées.
- Stale-race exercée.
- Zéro overflow.
- Zéro erreur runtime.

**Score visuel verrouillé : 9,7/10.**

## Sécurité

- Endpoint Web Push HTTPS uniquement avec validation anti-SSRF.
- Capability URL Push non journalisée.
- Identité revalidée côté serveur via session mobile, tenant, utilisateur, appareil et révocation.
- Clé privée VAPID stockée dans le répertoire de configuration privé local.
- Aucun contenu patient, clinique ou financier n'est envoyé au lock-screen.

## Limite explicitement non sur-vendue

L'émulation Chromium et les tests serveur certifient l'implémentation, les états UI, la sécurité et les règles de permission. **La réception OS réelle sur un vrai iPhone et un vrai Android n'est pas prétendue ici.** Elle reste un gate de la certification complète finale Mobile Full Experience, avec installation PWA/iOS Home Screen et comportement appareil réel.

## Anomalie indépendante

`Catalog Connected Truth #294` a échoué sur le même HEAD pendant son seeding AFTER avec `ModuleNotFoundError: sentry_sdk`, avant capture navigateur. M6-D2 ne touche ni Catalog ni observabilité ; ce rouge est hors scope D2.

## Déploiement

Aucun déploiement Vercel.
