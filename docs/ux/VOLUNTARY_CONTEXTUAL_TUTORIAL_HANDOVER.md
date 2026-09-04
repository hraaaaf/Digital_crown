# HANDOVER — Digital Crown Voluntary Contextual Tutorial

## Fichier canonique

`docs/ux/DIGITAL_CROWN_VOLUNTARY_CONTEXTUAL_TUTORIAL_CANONICAL.md`

## Repo

`hraaaaf/Digital_crown`

## Branche de préparation

`ux/voluntary-contextual-tutorial-canonical`

## Base master au démarrage

`84b9c0ea1fc7b4d10ea7182535053869e1a2b17a`

## Goal

Créer un nouveau tutoriel Digital Crown utile, contextuel et **100 % volontaire** : aucune ouverture automatique, aide déclenchée explicitement par l'utilisateur, guides courts, reprenables et non bloquants.

## Référence visuelle approuvée

Mockup utilisateur validé le 3 septembre 2026 :

`Voluntary Contextual Tutorial — Dashboard Guide Mockup v1`

Original validé : `a_clean_modern_saas_dashboard_ui_mockup_wide_des_1.png`, 1448×1086.
SHA-256 : `fbdc815dca91b051a44667db10958493ee225c1bc2b3857b518c82488285cc59`.

Référence versionnée repo :

`docs/ux/assets/VOLUNTARY_CONTEXTUAL_TUTORIAL_GOAL.svg`

Le canonique contient le visuel via Markdown et les invariants UI qui font foi.

## État précédent vérifié

Le chantier précédent `Dashboard Tutorial UX` est CLOSED.

Master de closeout précédent : `84b9c0ea1fc7b4d10ea7182535053869e1a2b17a`.

Preuves :

- aucun `DayOneTour` ;
- ancien `GuidedTour` / `TourLauncher` retiré ;
- `GuideTower` retiré ;
- timers Clinical Tips automatiques retirés ;
- Dashboard Visual Certification `33779398362` : 5/5 artifacts verts ;
- Runtime `33782891558` SUCCESS ;
- CI closeout `33782891425` SUCCESS ;
- aucun déploiement Vercel.

## Nouveau chantier

### TUTO-1 — Audit des parcours critiques — OPEN

Auditer le code réel pour :

1. créer un patient ;
2. retrouver un patient ;
3. agenda / rendez-vous ;
4. documents ;
5. éventuels réglages/workflows complexes réellement candidats.

Objectif TUTO-1 : produire une shortlist justifiée des guides utiles et identifier le meilleur point d'entrée `Aide/Guide` avant toute implémentation.

### TUTO-2 — UX architecture — PENDING

Définir panel/spotlight, progression, routes, persistance, reprise, accessibilité, responsive et règles par rôle.

### TUTO-3 — Implémentation — PENDING

Implémenter le système minimal suffisant. Ne pas réactiver `react-joyride` par réflexe.

### TUTO-4 — Certification — PENDING

BEFORE → Goal → mockup → implémentation → AFTER mêmes viewports → comparaison + runtime + tests → score.

## Règles non négociables

- jamais d'auto-launch ;
- jamais de timer d'apparition ;
- jamais de reprise forcée ;
- jamais d'overlay global bloquant ;
- jamais de relance automatique après refresh/retour Dashboard/nouvelle session ;
- pas de déploiement Vercel sans autorisation explicite ;
- ne pas mélanger avec Documents A5, SEC-1, Mobile ou Portability.

## Next exact

Lire d'abord `docs/ux/DIGITAL_CROWN_VOLUNTARY_CONTEXTUAL_TUTORIAL_CANONICAL.md`, vérifier `master`/branche/PR/HEAD/CI, puis exécuter **TUTO-1** : audit code + routes + composants des quatre parcours du mockup et du futur point d'entrée `Aide/Guide`.

## Séquence restante

TUTO-1 audit → TUTO-2 architecture UX → TUTO-3 implémentation → tests source/runtime → AFTER mêmes viewports → comparaison au Goal UI → score → closeout canonique → merge → post-merge.
