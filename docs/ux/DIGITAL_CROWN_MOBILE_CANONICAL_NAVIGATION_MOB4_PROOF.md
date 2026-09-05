# Digital Crown — Mobile Canonical Navigation — MOB-4 Proof

Status: CERTIFIED
Lot: MOB-4
Branch: `ux/mobile-canonical-navigation-mob4`

## Goal

Remplacer la navigation mobile orientée modules par une navigation cockpit à cinq entrées permanentes, sans casser les vues ni les deep links existants.

## BEFORE — VERIFIED

Run `33945615036` ✅
- HEAD : `6e1c5ffe3314b7621ae22202091e978025f18a23`
- artifact : `9963244367`
- digest : `sha256:6c2416c3454270a0dcfe863c1b834fbea75d658437cc060c46741d8013cfb35d`
- viewports : `390×844`, `430×932`, `768×1024`
- navigation observée : `Agenda / Finance / Envois Labo / Assistant / Sécurité`
- mode démo déterministe, aucune donnée cabinet.

## Goal UI

Référence : `docs/ux/DIGITAL_CROWN_MOBILE_CANONICAL_NAVIGATION_GOAL_UI.md`.

Cible :
1. `Aujourd’hui` → `agenda`
2. `Patients` → `patients`
3. `+` → Quick Action Hub MOB-3
4. `Assistant` → `bot`
5. `Plus` → destinations secondaires autorisées

Le mockup a été construit sur le BEFORE réel 390×844. Le dashboard n’a pas été reconstruit.

## Implémentation

- `MobileBottomNav` expose la navigation canonique à 5 entrées ;
- `Patients` devient une entrée permanente ;
- le bouton central `+` pilote le Quick Action Hub MOB-3 existant ;
- aucun second moteur d’actions n’est ajouté ;
- Finance / Labo / Sécurité sont déplacés dans `Plus` selon rôle ;
- les anciens deep links `?tab=agenda|finance|lab|bot|securite` restent acceptés ;
- `patients` devient également un deep link dashboard canonique ;
- thème et typographie restent issus des tokens Réglages cabinet.

## AFTER — VERIFIED

Run `33953721202` ✅ SUCCESS
- candidat exact : `4c04d09bf8102b80fcab25e88d58db5d30e0358f`
- artifact : `9965680255`
- digest : `sha256:99ae384612cdffffbb7226ee088f516d564e854900db1b91ceef47bd06afd9b2`
- viewports : `390×844`, `430×932`, `768×1024`
- tests MOB-4 ✅
- build production ✅
- Chromium evidence ✅
- PNG dimensions ✅
- `Aujourd’hui / Patients / + / Assistant / Plus` observé aux 3 viewports ✅
- 5 boutons permanents exactement ✅
- aucun overflow horizontal ✅
- aucune erreur runtime / console app ✅
- ancien FAB Agenda présent dans le DOM mais `visibility:hidden` + `pointer-events:none` ✅
- anciens deep links préservés ✅
- aucun déploiement Vercel.

### Géométrie runtime

- 390×844 : nav `x=12 y=756 w=366 h=76`, bouton central `60×60`, centré ;
- 430×932 : nav `x=12 y=844 w=406 h=76`, bouton central `60×60`, centré ;
- 768×1024 : nav `x=24 y=936 w=720 h=76`, bouton central `60×60`, centré.

## Inspection visuelle

Les trois AFTER ont été inspectés contre le BEFORE et le mockup réel.

Constats :
- hiérarchie plus claire et plus orientée usage quotidien ;
- `Aujourd’hui` et `Patients` sont immédiatement accessibles ;
- le `+` est visuellement central et distinct ;
- `Assistant` reste permanent ;
- `Plus` absorbe les modules secondaires sans surcharger la barre ;
- pas de rupture visible à 390 / 430 / 768.

Score visuel runtime : **9.6 / 10**.

Écart mineur non bloquant : à 390 px, le bouton central empiète volontairement au-dessus de la barre pour renforcer sa priorité. Ce comportement correspond à la cible et ne masque aucun label.

## Verdict

**MOB-4 CERTIFIED.**

La navigation canonique mobile est prouvée sur 390 / 430 / 768, les deep links historiques restent compatibles, et aucun déploiement n’a été effectué.
