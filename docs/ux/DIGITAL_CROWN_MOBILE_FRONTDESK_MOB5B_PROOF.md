# Digital Crown — MOB-5B Frontdesk Mobile — Proof

Status: CERTIFIED CANDIDATE / AWAITING FINAL HEAD CI
Date: 2026-09-05
Repo: `hraaaaf/Digital_crown`
Branch: `ux/mobile-frontdesk-mob5b`
PR: `#358`

## Goal
Traiter une demande de rendez-vous depuis mobile en quelques gestes, avec la même donnée métier que le desktop et sans dupliquer la logique Frontdesk.

## BEFORE
Baseline immuable : `89098066ef0c943c0e084af4b9cd388d3ab0aa5b` (master après MOB-5A).

État initial vérifié : aucun tab `frontdesk` dans le dashboard mobile, aucune entrée `Plus → Frontdesk`, aucun rendu Frontdesk dans le preview mobile.

Références :
- `docs/ux/DIGITAL_CROWN_MOBILE_FRONTDESK_MOB5B_AUDIT.md`
- `docs/ux/DIGITAL_CROWN_MOBILE_FRONTDESK_MOB5B_GOAL_UI.md`

## Implémentation
- `FrontdeskView` mobile dédiée ;
- `Plus → Frontdesk` pour DENTISTE / ADMIN / SECRETAIRE ;
- deep-link canonique `?tab=frontdesk` ;
- réutilisation de `/appointments/pending`, confirm, reject et request-confirmation ;
- appel / WhatsApp uniquement depuis le téléphone métier ;
- refus via dialog mobile ;
- erreurs inline ;
- aucun faux état serveur « envoyé » pour WhatsApp ;
- preview déterministe sans API réelle ni session cabinet.

## Tests et build
Run de certification dédié : `33967809033` ✅ SUCCESS sur le candidat `ad8e926f62920076b27be4e110bede1a713977a4`.

Contrats ciblés :
- bridge routing ;
- navigation `Plus` ;
- Frontdesk view ;
- hardcoding thème mobile.

Résultat : **9 tests ciblés passés**.

Build production : ✅.

Autres gates sur le même candidat :
- T2 Runtime `33967809069` ✅ ;
- Settings Security Visual `33967809021` ✅ ;
- MOB-5A regression cert `33967809030` ✅.

La CI générale `33967809037` était encore en cours au moment de la rédaction de cette preuve et doit être verte sur le HEAD final avant merge.

## AFTER — même viewports
Artifact : `9970008232`
Digest : `sha256:b831122003e2cd71d949c45926fe0f3da6adfa82453a1b09c0111be2f752fe46`

Viewports inspectés :
- `390×844` ✅
- `430×932` ✅
- `768×1024` ✅

Assertions runtime :
- 5 boutons permanents exactement ✅
- hauteur nav 76 px ✅
- overflow horizontal : aucun ✅
- erreurs runtime : aucune ✅
- entrée : `Plus → Frontdesk` ✅
- nav canonique préservée ✅

## Comparaison Goal UI
Atteint sur le candidat certifié :
- hiérarchie patient → créneau → statut → actions ✅
- confirmer / refuser visibles et tactiles ✅
- demande de confirmation conditionnelle ✅
- appel / WhatsApp secondaires ✅
- état preview explicite sans donnée réelle ✅
- shell et thème Digital Crown cohérents ✅

Point de vigilance non bloquant : à 390 px, la seconde carte descend sous la navigation fixe, ce qui est attendu dans une liste scrollable ; aucune information n’est perdue et aucun overflow horizontal n’est présent.

## Score visuel
**9.3 / 10**

Motifs : hiérarchie nette, densité correcte, gros targets tactiles, cohérence 390/430/768. La version tablette reste volontairement une colonne large unique, adaptée au cockpit plutôt qu’un faux desktop responsive.

## Déploiement
Aucun déploiement Vercel. Aucune écriture DB de certification.

## Gate final
Ne merger #358 que si tous les checks du HEAD final incluant cette preuve sont verts.
