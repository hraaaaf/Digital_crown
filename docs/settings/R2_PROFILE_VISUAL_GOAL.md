# R2 — Profil Cabinet — Goal visuel verrouillé

Date : 2026-08-19
Chantier : Réglages — Product Review & Simplification
Boussole : `SETTINGS_PRODUCT_COMPASS.md`

## Baseline vérifiée

Source : workflow GitHub Actions **Settings Visual Baseline**, run `31986511197` / run number `#1`, conclusion `SUCCESS`, head `044405838a47d27550f863a92e2092f12e19185d`.

Artifact : `settings-visual-baseline` (`9273960527`).

Viewports de référence Profil admin :
- `admin-profil-1440x1200.png`
- `admin-profil-768x1200.png`
- `admin-profil-390x1200.png`

Vérification de dérive : `ProfileTab.tsx` n'apparaît pas parmi les fichiers modifiés entre la baseline S1 et `master` lors du compare effectué avant R2 ; cette baseline reste donc la référence visuelle du contenu Profil avant R2.

## Goal

Conserver l'identité visuelle actuelle et toutes les fonctions utiles du Profil Cabinet, mais réduire la longueur, la charge mentale et les promesses trompeuses.

## Critères de succès

1. Identité, structure, praticien FR/AR, spécialités, adresse, logo, INPE, ICE/IF et contacts restent accessibles.
2. L'éditeur manuel d'en-tête bilingue devient un réglage avancé replié, sans supprimer sa puissance.
3. Pour un utilisateur standard, aucune donnée personnelle Benmoussa n'est proposée comme modèle par défaut ; l'action réinitialise depuis les informations réelles du cabinet.
4. Pour le superadmin propriétaire, le preset Benmoussa reste disponible.
5. Le bloc logo décrit uniquement le traitement réellement effectué : normalisation/redimensionnement raster, conversion PNG et préservation de transparence existante ; aucune promesse de détourage IA ni vectorisation inexistante.
6. La page reste utilisable en 1440 / 768 / 390 sans régression visuelle manifeste.
7. Aucun déploiement Vercel.

## Wireframe choisi — Option A / chirurgie minimale

```text
┌ Identité officielle ───────────────────────────────┐
│ Structure / praticien FR + AR                     │
│ Titre professionnel                               │
│ Spécialités bilingues                             │
│ Adresse                                           │
│ Logo du cabinet + traitement réel expliqué       │
│ INPE / ICE / IF                                   │
└───────────────────────────────────────────────────┘

┌ En-tête bilingue — Avancé ─────────────── [auto] ┐
│ ▸ Personnaliser l'en-tête bilingue                │
│   (éditeur FR/AR visible seulement à l'ouverture) │
└───────────────────────────────────────────────────┘

┌ Contacts & visibilité ────────────────────────────┐
│ Fixe / Mobile / WhatsApp / Instagram              │
└───────────────────────────────────────────────────┘

                                    [Sauvegarder]
```

## Alternatives écartées

- Wizard multi-étapes : trop lourd pour une page de configuration occasionnelle.
- Preview document permanent à droite : duplique le rôle de Design & Ambiance / Document Studio et alourdit R2.

Décision : **Option A**, car elle atteint le Goal avec le moins de changement structurel.
