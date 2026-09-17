# Agenda Clinique — A3 Closeout

Date: 2026-09-17

## Goal

Disponibilités praticien effectives = disponibilité cabinet ∩ disponibilité praticien, sans permettre à un praticien d'élargir les horaires du cabinet et sans régression A2.

## État validé

Validation visuelle humaine obtenue le 2026-09-16 sur les captures AFTER du HEAD produit `c286bcf9713bc9fcc5a9701a7fa75b35d94d843c`. Aucun changement visuel A3 n'a été introduit après cette validation.

Le comportement livré conserve les rendez-vous historiques sans `praticien_id` comme bloqueurs globaux multi-praticien. `legacy_unassigned` reste un contrat technique ; l'UI produit présente ces rendez-vous comme `Non assigné (historique)`.

## Preuves produit exact-head

- CI #4703 / run `35147129150`: SUCCESS.
- Agenda A3 Certification #22 / run `35147129229`: SUCCESS.
- Agenda A3 Theme Certification #16 / run `35147129160`: SUCCESS.
- PostgreSQL Alembic Schema Certification #34 / run `35147129187`: SUCCESS.
- Settings Read Truth Visual Certification #66 / run `35147129136`: SUCCESS.
- Settings Agenda R7 Visual Certification #87 / run `35147129129`: SUCCESS.
- Settings RBAC Visual Certification #389 / run `35147129167`: SUCCESS.
- Clinic P1 Multi-Practitioner Visual Certification #151 / run `35147129212`: SUCCESS.
- Agenda A2 AFTER Visual Certification V2 #37 / run `35147129149`: SUCCESS.
- T2 Runtime Browser Certification #3556 / run `35147129145`: SUCCESS.
- Mobile SuperAdmin MOB-5H Cert #120 / run `35147129292`: SUCCESS.
- AFTER artifact exact-head: `agenda-a3-after-visual-evidence`, artifact `10467149884`, digest `sha256:9410e5791cc6e288924942a7209438a8db21ff29be97379e03b54bf5cbb8ef56`.
- Settings Read Truth artifact: `10467870005`, digest `sha256:419d0a6c9a7d1e4a7b9e80068f3fe4a8d93d5881118846816701cf2a5a59a5c1`.

## Merge et régressions post-merge

- PR #542 A3 mergée; merge commit réel `ef23b7147c5ed3dfa7c06267eec797a520cb7366`.
- CI #4722 sur `ef23b714…`: échec d'un test de wiring A3 sensible au format d'import; production déjà correctement câblée.
- PR #560 a remplacé l'assertion textuelle fragile par une vérification AST; merge `c547e30d4bab4928ff64de3757bff98a83a60a53`.
- CI #4733 sur `c547e30d…`: 2035 passed / 6 skipped / 1 failed, échec mobile indépendant d'A3 (`/api/mobile/register-device`, 404).
- PR #558 a tenté d'aligner ce test sur un endpoint mobile legacy, mais `/api/mobile/appointments` est volontairement retiré (410).
- CI #4737 sur `eb2353b68d880b89dfadd13819fb43d1c71e2f1d`: nouvel échec du même test mobile, indépendant d'A3.
- Correctif mobile #563: HEAD prouvé `12fca4ede21dedb705169a290118cb09a77e523b`; T2 #3584 SUCCESS, étape ciblée numeric-sub SUCCESS; CI PR #4740 SUCCESS. Ce document ne revendique pas son merge faute de preuve de merge enregistrée ici.
- CI #4752 sur master `6075ae5f052b290258c4b66df97a05b0e61a3610`: 2165 passed / 6 skipped / 1 failed, test NGAP/Alembic obsolète (attendait `d0b000000003` comme head alors que le head unique courant est descendant `a3pa0000003`).
- PR #566 a corrigé le contrat du test: NGAP `d0b000000003` doit appartenir à la chaîne jusqu'au head courant, sans imposer qu'il reste le head.
- PR #566 mergée sur master: `24844a5d19a6bd575d175b331a1bba68bc3c0b0f`.
- Cabinet Upgrade PostgreSQL Certification #943 / run `35203491675`: SUCCESS sur `24844a5d…`.
- CI #4757 / run `35203491846`: SUCCESS sur `24844a5d…`; Frontend SUCCESS, garde production SUCCESS, Full backend regression post-merge SUCCESS.

## Perfection Pass

Revue finale après validation humaine:

- aucune review thread ouverte sur PR #542 au gate produit;
- thème A3 cohérent avec les tokens Digital Crown en default/emerald/dark;
- pas d'overflow page sur les captures certifiées;
- synchronisation des lanes multi-praticien certifiée;
- migration additive chaînée après `d0b000000003`, runtime schema head aligné sur `a3pa0000003` au lot A3;
- la chaîne Alembic est désormais testée par appartenance au head courant plutôt que par un head historique figé;
- le correctif du harness Settings Read Truth stabilise Vite/workbox sans affaiblir l'oracle métier;
- le master `24844a5d…` possède enfin la preuve post-merge globale verte requise après les régressions indépendantes successives.

Résiduel non bloquant: la surface Settings 390 px reste verticalement dense, mais lisible et sans overflow horizontal.

## Scoring

- EXECUTION_SCORE: 9.3/10
- ADVERSARIAL_SCORE: 9.2/10
- Score retenu: 9.2/10

La revue adversariale est réalisée par le même agent que l'exécution ; aucun score >=9.5 n'est revendiqué.

## Gate

A3 satisfait désormais le gate technique post-merge sur le master `24844a5d19a6bd575d175b331a1bba68bc3c0b0f`: PostgreSQL #943 SUCCESS et CI globale #4757 SUCCESS. Le présent commit documentaire doit encore passer ses propres gates puis être mergé avec l'accord explicite utilisateur sur son HEAD exact avant de déclarer A3 CLOSED dans master.
