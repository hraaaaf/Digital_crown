# R8 — Performance & Assistance : Goal produit et visuel

Date : 2026-08-19
Scope principal : **Réglages → IA & Système**.
Scope secondaire autorisé : **Design & Ambiance** uniquement pour déplacer l'option d'arrière-plan animé vers l'endroit où elle appartient.

## Goal

Remplacer un panneau au vocabulaire trompeur par une surface courte et vraie :
- renommer `IA & Système` en **Performance & Assistance** ;
- conserver le **Mode Performance**, dont le downstream est réel ;
- déplacer **Arrière-plan animé** vers Design & Ambiance, dont il relève visuellement ;
- conserver les **Conseils cliniques contextuels**, dont les consommateurs runtime sont désormais prouvés ;
- conserver l'option d'indicateurs patient mais remplacer le vocabulaire `fiabilité / fidélité` par une description factuelle et explicable ;
- ne supprimer aucune donnée persistée/colonne dans R8.

## Preuves consommateur exactes

Workflow `Settings R8 Runtime Consumer Audit` #1 — SUCCESS.
Artifact `settings-r8-consumer-audit`, digest `sha256:ba3b878997349559468d08fa0600ab8e37bd616fb2546318ca8b1c49afc3925e`.
HEAD de preuve : `ea04e1fec190729104f5d8a1b6a1f6fddc4530e3`.

### Mode Performance — GARDER
- persisté dans le profil puis `performanceMode` runtime ;
- consommé dans `App.tsx` et par la couche de tracé céphalométrique ;
- réduit effectivement certains effets visuels coûteux.

### Arrière-plan animé — DÉPLACER vers Design & Ambiance
- `app_background_animated` consommé par `App.tsx` et `MainLayout.tsx` ;
- fonction visuelle réelle, mais mal classée dans `IA & Système`.

### Conseils cliniques — GARDER / RENOMMER
La recherche initiale avait produit un faux négatif. Le grep repository complet prouve :
- `Sidebar.tsx` importe et monte `ClinicalTipBubble` ;
- `Step1Cephalo.tsx` importe et monte `ClinicalTipBubble` ;
- les deux lisent `clinical_tips_enabled`.

Verdict : **GARDER** sous le libellé `Conseils cliniques contextuels`, sans promettre une intelligence ou une analyse automatique supplémentaire.

### Badges patient — GARDER / RENDRE EXPLICABLE
Le grep complet prouve les consommateurs :
- `Dashboard.tsx` ;
- `PatientList.tsx` via `PatientScoreBadge`.

Le backend `patient_scoring_service.py` calcule :
- **60 % assiduité aux rendez-vous** ;
- **40 % ratio encaissé / facturé** ;
- état neutre à 50 en absence de données ;
- grade pouvant être remplacé manuellement par le praticien.

Le libellé actuel `Badges de Fiabilité Patient` et la promesse `fidélité` sont donc trop moralisants et insuffisamment précis.

Verdict R8 : renommer le réglage **`Indicateurs de suivi patient`** et expliquer exactement sa base : assiduité + situation d'encaissement. La refonte détaillée des badges eux-mêmes reste P2.5.

## Wireframe cible

```text
Performance & Assistance
Réglez les comportements d'assistance réellement appliqués par l'application.

┌ Performance ───────────────────────────────────────────────────┐
│ Mode performance                                      [ON/OFF] │
│ Réduit certains effets visuels sur les machines modestes.     │
└────────────────────────────────────────────────────────────────┘

┌ Assistance contextuelle ──────────────────────────────────────┐
│ Conseils cliniques contextuels                       [ON/OFF] │
│ Affiche les bulles disponibles dans les écrans compatibles.   │
└────────────────────────────────────────────────────────────────┘

┌ Suivi patient ─────────────────────────────────────────────────┐
│ Indicateurs de suivi patient                          [ON/OFF] │
│ Basés sur assiduité RDV (60 %) + encaissé/facturé (40 %).    │
└────────────────────────────────────────────────────────────────┘
```

Dans `Design & Ambiance` :

```text
Apparence de l'application
...
Arrière-plan animé                                      [ON/OFF]
Motif décoratif subtil appliqué à l'interface.
```

## Critères de succès

1. onglet `IA & Système` absent ; `Performance & Assistance` visible à la place ;
2. aucune promesse d'IA/diagnostic ou de `fiabilité/fidélité patient` dans cette page ;
3. Mode Performance conservé et son downstream inchangé ;
4. arrière-plan animé absent de R8 et présent dans Design & Ambiance, comportement runtime conservé ;
5. Conseils cliniques contextuels conservés ;
6. Indicateurs de suivi patient conservés avec base 60/40 explicitée ;
7. aucune suppression de champ legacy ;
8. BEFORE puis AFTER 1440/1024/768/430/390 ;
9. aucun overflow horizontal/runtime error ;
10. RBAC/CI/T2 proportionnés verts avant CLOSED.

## Hors scope

- nouvelle IA ou LLM ;
- nouveau moteur de conseils ;
- modification de l'algorithme de score patient ;
- refonte détaillée du composant `PatientScoreBadge` (P2.5) ;
- Vercel.
