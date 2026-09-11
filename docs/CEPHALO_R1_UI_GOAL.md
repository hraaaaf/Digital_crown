# Céphalométrie R1 — Goal visuel et contrat UI

## Baseline BEFORE vérifiée

- Produit observé : `a76f2568418d0d7d9465ee24163324047b246c86`.
- Run de capture : `Cephalo R1 BEFORE` #1 / run `34540754492`.
- Viewports : 390×844, 768×1024, 1280×900.
- À 390 px : largeur document mesurée 543 px, soit +153 px de débordement horizontal.
- Le modal manuel tient dans le viewport (384 px de large, 3 px de marge latérale à 390 px).
- Le produit n’affiche actuellement aucune provenance R1 explicite.
- Le run BEFORE a échoué sur des assertions de texte trop strictes alors que les PNG et le rapport ont été produits. Cet échec est un défaut du harness, pas un crash produit.

## Goal

Rendre la calibration fiduciale R1 compréhensible et auditée sans modifier la frontière scientifique : l’UI expose l’état réel fourni par le serveur, permet l’auto-vérification seulement via le endpoint serveur sans sélection de profil côté client, garde la confirmation praticien facultative et conserve la calibration manuelle comme fallback distinct.

## Succès observable

1. Aucun overflow horizontal document à 390 / 768 / 1280.
2. Les états sont visuellement distincts :
   - `CANDIDATE_UNVERIFIED` → « Réglette détectée · à vérifier » ;
   - `AUTO_VERIFIED` → « Auto-vérifiée » ;
   - `CLINICIAN_CONFIRMED` → « Confirmée praticien » ;
   - `MANUAL_TWO_POINT` → « Calibration manuelle » ;
   - absence de preuve → « Échelle non vérifiée ».
3. Le client ne transmet jamais `profile_id`, `profile_version` ni référence physique à l’auto-calibration.
4. `AUTO_VERIFIED` rend les mesures mm utilisables immédiatement ; la confirmation praticien reste recommandée mais non obligatoire.
5. La confirmation praticien ne modifie ni le ratio ni les mesures, seulement la provenance affichée.
6. La calibration manuelle reste accessible depuis tous les états non confirmés et reste distincte d’une confirmation d’auto-calibration.

## Référence / mockup fonctionnel

```text
┌ Studio Céphalométrique ───────────────────────────────┐
│ Patient                  [Actuel][Historique] [Save] │
├───────────────────────────────────────────────────────┤
│ [1 Céphalo] [2 Moulages] [3 Synthèse] [4 Documents] │
├───────────────────────────────────────────────────────┤
│                                                       │
│ [ÉDITION ACTIVE] [RÉGLETTE DÉTECTÉE · À VÉRIFIER]    │
│                                                       │
│        ┌ Calibration assistée ─────────────────┐      │
│        │ Réglette détectée. Échelle non        │      │
│        │ vérifiée tant que le serveur n’a pas  │      │
│        │ validé la source physique.            │      │
│        │ [Vérifier automatiquement]            │      │
│        │ [Calibrer manuellement]               │      │
│        └───────────────────────────────────────┘      │
│                                                       │
└───────────────────────────────────────────────────────┘

AUTO_VERIFIED :
[✓ AUTO-VÉRIFIÉE 0.200 mm/px] [Confirmer] [Modifier manuellement]

CLINICIAN_CONFIRMED :
[✓ CONFIRMÉE PRATICIEN 0.200 mm/px] [Modifier manuellement]
```

## Tokens et hiérarchie

- Fond / surface : tokens Céphalo existants `slate-950`, `slate-900`, bordures `slate-700/50`.
- Action / focus : indigo existant.
- État vérifié : emerald existant.
- État non vérifié / candidat : amber existant.
- Pas de nouvelle palette ni de surface claire dans le studio radiologique.
- Les actions secondaires restent compactes et ne doivent jamais masquer le canevas à 390 px.

## Preuve AFTER attendue

- Captures 390×844 / 768×1024 / 1280×900 sur le HEAD produit final.
- Rapport : `scrollWidth <= innerWidth + 1` pour les 3 viewports.
- Tests frontend : dérivation des états de provenance + endpoints sans sélection de profil côté client.
- CI frontend build/tests verte.
