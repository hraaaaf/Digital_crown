# Digital Crown — Mobile Product — Canonical Handover

Status: CLOSEOUT IN PROGRESS
Canonical file: `docs/ux/DIGITAL_CROWN_MOBILE_PRODUCT_CANONICAL.md`
Repo: `hraaaaf/Digital_crown`
Current merged product baseline: `1316b73c70f5cc298eb1101db557d1d4abee1f85`
Deployment: none. No Vercel deployment is authorized by this chantier.

## Goal final
Faire de Digital Crown mobile un cockpit opérationnel clinique, distinct du desktop lourd, sans modèle métier parallèle et sans affaiblir RBAC, sécurité, offline, contexte patient ou prérogatives SuperAdmin.

## Doctrine verrouillée
- Mobile = cockpit opérationnel ; desktop = workflows lourds/complets.
- SuperAdmin mobile = parité complète des prérogatives actives.
- Source de vérité unique serveur/DB.
- Aucun modèle métier parallèle mobile.
- Navigation canonique : `Aujourd’hui / Patients / + / Assistant / Plus`.
- Tout changement UI : BEFORE → Goal UI → référence/mockup → implémentation → AFTER mêmes viewports → comparaison/tests → score.
- Aucun Vercel sans autorisation explicite.

## Lots produit certifiés

| Lot | État | Preuve structurante |
|---|---|---|
| MOB-2 Patient Cockpit | DONE / MERGED | PR #354, merge `5fd2a06663e941581ad422267d31a5bb69a13d11`, score 9.2 |
| MOB-3 Quick Action Hub | DONE / MERGED | PR #355, merge `23e4828729e085a4566cbfdf430025d1019e53fa`, score 9.5 |
| MOB-4 Navigation canonique | DONE / MERGED | PR #356, merge `28cf8278a31507d96b33c10f03e1635f86223454`, score 9.6 |
| MOB-5A Équipe / praticiens | DONE / MERGED / RECERTIFIED | PR #357, merge `89098066ef0c943c0e084af4b9cd388d3ab0aa5b`, recert run `34234606313`, artifact `10059360520`, digest `sha256:cac6ca025db5f6b172eca67d8aa28e2f573037556a4af7348df65162d78d0659` |
| MOB-5B Frontdesk | DONE / MERGED | PR #358, merge `21a41852182c7e74cc66c335c8d67c93a94d5871`, score 9.3 |
| MOB-5C Notifications | DONE / MERGED | PR #359, merge `aaa28ef97b22df2c5654c4e0da7efc15692787a8`, score 9.4 |
| MOB-5D Stock | DONE / MERGED | PR #360, merge `9cb740bc52efc9bf734c19fefc3c4f07470eba80`, post-merge `34041170446` ✅ |
| MOB-5E Bibliothèque clinique | DONE / MERGED | PR #361, merge `b850cff2bd03dda667d6e1b6e449230658035d62`, score 9.4 |
| MOB-5F Quick Document Studio | DONE / MERGED / CLOSED | PR #365, merge `d9d1c255be6c9878ce6b7127c7f723cfb61e38a0`, post-merge `34163696668` ✅, score 9.1 |
| MOB-5G Marketplace | DONE / MERGED | PR #362, merge `6eb93c75f91402031ecc2c8fc1f8858372a97b9b`, post-merge `34054519282` ✅, score 9.4 |
| MOB-5H SuperAdmin | DONE / MERGED | PR #363, merge `e30b858f58686f5f7bef19ca93f1c5dae42929c9`, post-merge `34142208046` ✅, score 9.3 |
| MOB-5I Salle d’attente | DONE / MERGED / CLOSED | PR #367, merge `e2522a6d8b4794e64253eb4af36500e18cd87b40`, post-merge `34170398551` ✅, score 9.3 |
| MOB-6 Routage mobile canonique | DONE / MERGED / CLOSED | PR #372, merge produit `97546777e3b4adbb8a670559553c1079aad4c2e2`, closeout #373 merge `ce2d33d2f6edfd2d6fb99e1ba45b566fc4f3ac37`, post-merge `34229494805` ✅, score 9.4 |

Science Hub reste desktop-only.

## MOB-5F — contrats documentaires verrouillés
- Ordonnance → `prescriptions`.
- Certificat → `patients`.
- Devis → `accounting`.
- Honoraires → `accounting`.
- Document libre → `clinical`.
- `can_pay` historique conserve le contrôle combiné `['accounting', 'payments']`.
- moteur canonique : `/api/documents/generate`.
- aucune nouvelle DB/générateur parallèle.

## MOB-6 — politique de routage verrouillée
Top-level mobile : `/dashboard`, `/agenda`, `/patients`, `/accounting`, `/stock`, `/approvisionnement`, `/bibliotheque`, `/salle-attente`, `/super-admin`.

Les deep-links riches restent desktop tant qu’une destination mobile ne peut pas préserver exactement l’entité ciblée.

Preuves :
- BEFORE `34211312980` / artifact `10049990601` / digest `sha256:c89e86a107100e1596187291f9650c12bf716ffcc95c225efd4e670230b1eef4` ;
- AFTER `34211780896` / artifact `10050137272` / digest `sha256:dc1e5a72d02f668cf537ec9fa28341940d34df7388603da6974eeac393d82ec7` ;
- 390/430/768, 0 overflow, 0 page error, 0 console error.

## MOB-7 — Certification globale Mobile Product — DONE / MERGED / POST-MERGE VERIFIED

### Goal
Certifier la surface logicielle mobile complète actuelle sur un même candidat immuable, sans confondre preuve CI et comportement physique réel.

### Gap détecté puis fermé
Le double-check a identifié une asymétrie MOB-5A : pas de test dédié de `DentistsView` ni `/mobile/dentists`.

Correction :
- `backend/tests/test_mobile_team_mob5a.py` ;
- `frontend/src/features/mobile/Dashboard/views/DentistsView.test.tsx` ;
- intégration au workflow global `.github/workflows/mobile-final-certification.yml`.

### Preuves finales MOB-7
- final PR HEAD : `a406d81b56e1c7b7b9a04a765391a0a32d560556` ;
- global software run `34234600211` ✅ ;
- backend M6 + MOB-5A/F/H/I ✅ ;
- frontend M4/M6 + MOB-5A→I + MOB-6 + build ✅ ;
- offline/sync/retry/revocation ✅ ;
- pairing ECDH + RBAC fail-closed ✅ ;
- T2 `34234606588` ✅ ;
- CI PR `34234606403` ✅ ;
- MOB-5A dedicated `34234606313` ✅ ;
- PR `#374` merged ;
- merge exact `1316b73c70f5cc298eb1101db557d1d4abee1f85` ;
- post-merge master `34237128357` ✅ SUCCESS.

## Preuves visuelles
MOB-7/MOB-8 ne modifient pas l’UI. Les BEFORE/AFTER, viewports, artifacts, digests et scores des lots restent les autorités visuelles. Aucun score global fictif n’est recalculé.

## Gates physiques séparés
Non certifiés par CI :
1. Face ID réel ;
2. Touch ID réel si supporté ;
3. biométrie Android réelle ;
4. Push réel PWA background/closed.

Ils ne doivent jamais être présentés comme certifiés sans preuve appareil.

## Limites connues non déclarées corrigées
- conflit de dépendances historique `httpx==0.27.2` avec `firebase-admin 7.5.0` / `ultralytics-platform` : ne pas déclarer corrigé sans preuve dédiée ;
- seuil MOB-5F <30 s non chronométré : ne pas le présenter comme mesure certifiée ;
- légère réserve visuelle historique à 390 px sur MOB-5F avant scroll.

## MOB-8 — Final Closeout — IN PROGRESS
Baseline : `1316b73c70f5cc298eb1101db557d1d4abee1f85`.

Le produit mobile software est certifié et le post-merge MOB-7 est vert. Il reste uniquement le closeout documentaire MOB-8 : PR docs-only, CI/T2, merge et dernier post-merge master.

Preuve dédiée : `docs/ux/DIGITAL_CROWN_MOBILE_PRODUCT_MOB8_CLOSEOUT.md`.

## Garde-fous permanents
- ne pas casser les context bridges ;
- ne pas casser offline/sync/revocation ;
- ne pas affaiblir sécurité/biométrie/RBAC ;
- ne pas exposer de données hors permission/tenant ;
- ne pas mélanger mockup et preuve AFTER ;
- ne jamais annoncer une certification physique depuis une CI navigateur ;
- ne pas déployer sur Vercel sans autorisation explicite.

## Next exact
Ouvrir la PR MOB-8 depuis `docs/mobile-product-mob8-closeout` vers `master`. Si CI/T2 sont verts : merge, vérifier le dernier post-merge master, puis passer ce fichier et le closeout à `CLOSED` sur le merge final.
