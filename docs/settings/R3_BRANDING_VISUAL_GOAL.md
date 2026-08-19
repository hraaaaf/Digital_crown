# R3 — Design & Ambiance — Goal visuel

Date : 2026-08-19
Repo : `hraaaaf/Digital_crown`
Baseline master : `4e56b7507bab2b556f1308b62984e3526f1cb4e5`

## BEFORE

Référence visuelle certifiée : workflow `Settings Branding Visual Certification #24`, HEAD `99de2c4aee19f389bdbd0eee46cae072747babdb`, SUCCESS.
Viewports disponibles : 1440 / 1024 / 768 / 430 / 390.

Constat visible : le contrôle `Apparence app | Documents` ressemble à un sélecteur de configuration. Or le code confirme qu'il ne modifie que la vue passée à `StudioPreview`; `StudioControls` reçoit le même profil dans les deux états.

## Goal

Clarifier que le contrôle change uniquement l'aperçu affiché, sans inventer deux thèmes ni modifier les réglages réels.

## Wireframe retenu

```text
[ Ambiance active ]                 APERÇU [ Application | Document ]   [ ↺ Réinitialiser ]
                                     Ce sélecteur change uniquement
                                     l'aperçu affiché.

[ Contrôles du Studio ]             [ Aperçu en direct ]
                                     Tableau de bord / Document A4
```

Mobile : même hiérarchie, avec le bloc `APERÇU` replié naturellement sur une ligne séparée sans overflow horizontal.

## Critères de succès

1. Les boutons ne s'appellent plus `Apparence app` / `Documents`, mais `Application` / `Document` sous un libellé explicite `Aperçu`.
2. Une microcopie visible indique : `Ce sélecteur change uniquement l’aperçu affiché.`
3. Aucun réglage du profil n'est séparé ou dupliqué par scope.
4. Aucun changement fonctionnel R4 sur les modèles documentaires.
5. 1440 / 1024 / 768 / 430 / 390 : aucun overflow horizontal, aucun chevauchement.
6. Le switch continue à piloter `StudioPreview` entre Tableau de bord et Document A4.
7. Les tests existants de persistance Branding restent verts.

## Hors scope R3

- taxonomies de modèles documentaires ;
- faux renderer documentaire ;
- rendu PDF réel ;
- QR, papier-en-tête, D-pad, marges et templates.

Ces sujets restent R4/R5 selon `SETTINGS_PRODUCT_COMPASS.md`.
