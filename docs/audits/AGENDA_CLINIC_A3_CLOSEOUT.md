# Agenda Clinique — A3 Closeout

Date: 2026-09-16

## Goal

Disponibilités praticien effectives = disponibilité cabinet ∩ disponibilité praticien, sans permettre à un praticien d'élargir les horaires du cabinet et sans régression A2.

## État validé

Validation visuelle humaine obtenue le 2026-09-16 sur les captures AFTER du HEAD `c286bcf9713bc9fcc5a9701a7fa75b35d94d843c`.

Le comportement livré conserve les rendez-vous historiques sans `praticien_id` comme bloqueurs globaux multi-praticien. `legacy_unassigned` reste un contrat technique ; l'UI produit présente ces rendez-vous comme `Non assigné (historique)`.

## Preuves exact-head avant closeout documentaire

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

## Perfection Pass

Revue finale après validation humaine:

- aucune review thread ouverte sur PR #542;
- aucune CI requise rouge sur le HEAD validé;
- thème A3 cohérent avec les tokens Digital Crown en default/emerald/dark;
- pas d'overflow page sur les captures certifiées;
- synchronisation des lanes multi-praticien certifiée;
- migration additive chaînée après `d0b000000003`, runtime schema head aligné sur `a3pa0000003`;
- le correctif du harness Settings Read Truth stabilise Vite/workbox sans affaiblir l'oracle métier.

Résiduel non bloquant: la surface Settings 390 px reste verticalement dense, mais lisible et sans overflow horizontal.

## Scoring

- EXECUTION_SCORE: 9.3/10
- ADVERSARIAL_SCORE: 9.2/10
- Score retenu: 9.2/10

La revue adversariale est réalisée par le même agent que l'exécution ; aucun score >=9.5 n'est revendiqué.

## Gate

A3 est prêt pour closeout Git/merge sous réserve de conserver les preuves vertes après ce commit documentaire et d'une autorisation explicite avant merge.
