# Catalogue avancé — Catalogue connecté — CLOSEOUT

Date : 2026-08-21
Repo : `hraaaaf/Digital_crown`
PR : #195 — MERGED
Merge : `5f6187b30906e5f51b6176fa3143702d4b6d62ed`

## Goal

Connecter le catalogue cabinet R6 à la recherche clinique et au Master Plan tout en figeant par valeur le nom, le code et le tarif au moment de l'ajout, sans casser les historiques ni les cores déjà certifiés.

## Résultat produit vérifié

- `/actes/catalog/search?q=` conserve son contrat public et lit le catalogue tenant du cabinet ;
- `quick-add` écrit dans ce catalogue tenant ;
- recherche clinique par nom/code/spécialité ;
- nom et tarif préremplis puis modifiables avant ajout ;
- Master Plan persiste `act_id`, code, nom et prix capturés ;
- modification ou désactivation ultérieure du catalogue ne change pas le snapshot historique ;
- statut/date historique restent modifiables après désactivation ;
- act cross-tenant refusé pour un nouveau snapshot ;
- labels `Acte du catalogue`, `Nom retenu`, `Tarif DH` reliés sémantiquement aux inputs ;
- P7 Clinique et Prescriptions restent délégués à des cores byte-identiques.

## BEFORE

SHA immuable : `e0be81e25833782a2cfc3ebddff68983d2624f9c`.

Viewports : 1440x1200, 768x1200, 390x1200, 360x1200, 320x1200.

BEFORE recapturé dans le run final #8 sur les mêmes viewports que l'AFTER.

## Historique de diagnostic utile

- #2 : régression de forme legacy du Master Plan corrigée sans snapshot `null` injecté ;
- #3 puis P7 #26 : harnesses lisant la façade `ClinicalHub.tsx` au lieu du core byte-identique, corrigés ;
- #5/#6 : snapshot persisté mais non sérialisé dans la réponse HTTP fraîche, remplacé par sérialisation SQL explicite ;
- CI #1501 : `quick-add` réécrivait silencieusement le prix existant, contrat restauré ;
- #7 : tests/backend/build verts mais AFTER bloqué car labels visibles non associés aux inputs ; correctif accessibilité minimal sur `ClinicalHub.tsx` uniquement.

Après deux échecs similaires, la stratégie a été changée vers correction consolidée plutôt que micro-pushes successifs.

## HEAD produit certifié

`f0238b8245b61430ca64714f74aa87a580c7d37a`

Dernier delta depuis le parent CI vert `056f696961fcaad4590be929f840c260c7082c35` : un seul fichier frontend, `ClinicalHub.tsx`, +8/-3, uniquement ids + associations `htmlFor` des trois labels. Aucun backend touché.

## AFTER final

Catalog Connected Truth Certification #8 `32474152651` — **SUCCESS**.
Artifact `9443760454`.
Digest `sha256:09e14f0391143bf7faf28ce38f1ea84d034139dec32fc8b39313dae8c0973ca9`.

Viewports inspectés : 1440 / 768 / 390 / 360 / 320.

- captures AFTER : 5/5 ;
- overflow : 0/5 ;
- page errors : 0/5 ;
- HTTP 5xx : 0/5 ;
- sélecteur actif à 650 DH après réactivation ;
- score visuel : **9,5/10**.

Les troncatures restantes visibles à 320/360 concernent principalement le header clinique préexistant, pas le nouveau bloc Catalogue.

## Preuve métier immuable

Scénario certifié :
1. ajout au plan depuis le catalogue à **500 DH** ;
2. source catalogue modifiée à **650 DH** puis désactivée ;
3. plan historique toujours à **500 DH** ;
4. statut historique passé à `done` pendant désactivation ;
5. source réactivée à **650 DH** ;
6. sélecteur courant propose **650 DH** tandis que l'historique reste **500 DH**.

## Gates exact HEAD produit

- Catalog Connected Truth Certification #8 `32474152651` — SUCCESS ;
- CI #1509 `32474152694` — SUCCESS ;
- T2 Runtime Browser Certification #734 `32474152628` — SUCCESS ;
- Patient P7 Final Certification #33 `32474152905` — SUCCESS.

CI #1509 : garde production, backend full test suite, frontend tests et build — SUCCESS.

## Merge et post-merge

- PR #195 passée ready puis squash-mergée ;
- merge GitHub vérifié : `5f6187b30906e5f51b6176fa3143702d4b6d62ed` ;
- `master` contient le produit certifié et ce closeout ;
- `SETTINGS_PRODUCT_COMPASS.md` est mis à jour à **12/15 = 80,0 %** ;
- next : **Indicateurs patient explicables**.

## Décision

**Catalogue avancé / Catalogue connecté = CLOSED / CERTIFIÉ / MERGED.**

Aucun Vercel.
