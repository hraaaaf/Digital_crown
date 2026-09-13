# Audit UI/UX — Dossier patient Digital Crown

Date : 2026-09-13

## État vérifié

T1 est fermé : PR #465 squash-mergée, master post-merge `b9fc9ca6f0e978d51fa2180c30143b2c2c047200` vérifié. Le Live Preview P6 a été corrigé en vraie modale responsive et recertifié exact-head : CI #3712, T2 #2656, Catalog #1104, PostgreSQL #171 et Patient P7 #1319 = SUCCESS ; M6-I #1456 = SKIPPED attendu.

## BEFORE inspecté

Captures réelles 390x844, 430x932, 768x1024 et 1280x900 sur : Vue d’ensemble, Clinique, Imagerie RVG, Panoramique, Céphalométrie, Documents création, Documents historique, Finances, Nouveau patient, Modifier patient.

Le produit est stable sur desktop mais le mobile reste trop dérivé du desktop : chrome patient trop haut, navigations horizontales partiellement invisibles, éléments flottants qui recouvrent le contenu.

## Goal UX1

À 390/430/768, garder les fonctions actuelles mais rendre le dossier patient immédiatement lisible et navigable sans libellé tronqué ni couche globale couvrant les CTA. À 1280, préserver la densité et la stabilité existantes.

Succès observable :
- aucune destination utile uniquement hors champ sans affordance ;
- RVG / Panoramique / Céphalométrie tous lisibles ;
- les 6 types du Document Studio immédiatement découvrables ;
- CrownBot fermé/ouvert reste dans le viewport et respecte les safe areas ;
- le toast NBA ne masque plus les contrôles patient ;
- captures AFTER 390/768/1280 + tests + comparaison avant closeout.

## Référence / mockup fonctionnel

Mobile :

```text
[←] NOM Patient              [actions]
N° dossier · âge · téléphone
[ RDV ][ Examen ][ Document ][ Encaisser ]
[ Vue ] [ Clinique ] [ Imagerie ] [ Docs ] [ Finances ]
             contenu métier
```

Les onglets patient restent compacts et signalent explicitement qu’ils sont scrollables si nécessaire. En Imagerie, les 3 modalités occupent une grille visible. Dans Document Studio, les 6 types passent en grille mobile plutôt qu’en bandeau horizontal caché. Les overlays globaux utilisent le viewport, jamais une largeur fixe supérieure au mobile.

## P1 à corriger

1. Header patient mobile trop haut.
2. Navigation patient horizontale sans affordance.
3. Sous-navigation Imagerie tronquée.
4. Tabs Document Studio P1→P6 partiellement invisibles.
5. CrownBot flottant recouvre le contenu ; popup 400x600 inadéquat à 390.
6. Toast NBA bottom-right peut recouvrir les actions pendant 7 s.

## P2 / human gates séparés

- Ne pas masquer automatiquement `Ouvrir sur mobile` sans décision produit.
- Ne pas remplacer le wording interne `Étape P7 certifiée` sans mapping métier validé.
- Ne pas transformer le NBA en callout/centre de notifications sans arbitrage produit ; pour UX1, seul son placement non bloquant est réversible.

## P6 Live Preview — AFTER prouvé

- 390x844 : dialogue 390x844, overlay complet.
- 768x1024 : dialogue 736x992 à x=16/y=16.
- 1280x900 : dialogue centré 1024x836 à x=128/y=32.
- clipping = 0, page errors = 0.

Score visuel P6 : 9,2/10. Réserve : header preview encore un peu haut à 390.

## Plan de lot

### UX1-A — Shell patient mobile
Réduire le chrome avant contenu sans cacher de fonction, améliorer l’affordance des tabs patient.

### UX1-B — Navigations secondaires
Imagerie et Document Studio : zéro libellé tronqué à 390/430/768.

### UX1-C — Couches globales
CrownBot et toast NBA : aucun recouvrement de CTA ou zone clinique critique.

## Next exact

Implémenter UX1-A/B/C sur branche `ux/patient-dossier-transversal`, puis recapturer 390/768/1280, comparer au BEFORE et scorer avant PR/merge.
