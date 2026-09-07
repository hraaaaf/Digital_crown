# DIGITAL CROWN — UX CONTINUITY / FLOW HANDOFF — CANONICAL HANDOVER

Status: BEFORE RUNNING — GOAL UI LOCKED — IMPLEMENTATION NOT STARTED

## Goal

Garantir qu’après toute action exigeant une interaction suivante, cette interaction soit immédiatement visible, identifiable et utilisable sans scroll manuel de recherche.

## Success

Le chantier n’est CLOSED que si les preuves montrent :
- suppression Patient depuis scroll haut / milieu / bas → confirmation immédiatement visible ;
- CTA Annuler / Supprimer accessibles sur petits viewports ;
- fond verrouillé pendant la confirmation ;
- focus initial logique, Tab contenu dans la modale, Escape fonctionnel, focus restauré ;
- wizard N → N+1 → nouvelle étape immédiatement visible ;
- aucun scroll automatique inutile si la cible est déjà visible ;
- changements automatiques d’onglet / surface → cible utile ramenée dans le viewport ;
- aucun changement RBAC ou capacité métier ;
- BEFORE / AFTER mêmes viewports ;
- tests ciblés + build + CI verts ;
- score visuel documenté ;
- PR + merge + post-merge verts.

## Cause racine vérifiée

### PatientList

`frontend/src/features/patients/PatientList.tsx`

La confirmation Patient est aujourd’hui :
- `fixed inset-0` ;
- rendue localement dans le subtree de `PatientList` ;
- sans portal `document.body` ;
- sans verrouillage explicite du scroll ;
- sans focus trap ;
- sans autofocus logique ;
- sans restauration du focus ;
- avec `h-screen w-screen` ;
- sans stratégie explicite de hauteur maximale + scroll interne.

### MainLayout

`frontend/src/components/Layout/MainLayout.tsx`

`PatientList` est rendu sous un `motion.div` Framer Motion avec animation `y` :

```tsx
<motion.div
  initial={{ opacity: 0, y: 15 }}
  animate={{ opacity: 1, y: 0 }}
  exit={{ opacity: 0, y: -15 }}
>
  {children}
</motion.div>
```

Une transformation CSS différente de `none` établit un containing block pour les descendants `position: fixed`. La modale locale peut donc être positionnée relativement à cet ancêtre transformé au lieu du viewport.

Conclusion architecturale : le portal vers `document.body` est le correctif racine approprié pour sortir les confirmations critiques du containing block animé.

La reproduction BEFORE reste obligatoire pour mesurer le comportement utilisateur exact avant modification.

## Autres défauts vérifiés

### Setup Wizard

`frontend/src/features/admin/SetupWizard/SetupWizard.tsx`

Le passage suivant effectue essentiellement :

```ts
setCurrentStep(prev => Math.min(prev + 1, 7));
```

Aucun handoff viewport/focus n’est effectué après rendu de N+1.

### PatientDetails

`frontend/src/features/patients/PatientDetailsInner.tsx`

Plusieurs transitions changent l’onglet / surface via `setSearchParams(...)` sans doctrine globale de transfert d’attention.

## Goal UI / référence

Fichier : `docs/ux/DIGITAL_CROWN_UX_CONTINUITY_GOAL_UI.md`

Commit : `82b180d5ac3e41213a3a3c5d53d0db3919d480bc`

Doctrine :

> Le système déplace l’attention vers sa prochaine attente. L’utilisateur ne cherche jamais où continuer.

Viewports verrouillés :
- 390×844
- 430×932
- 768×1024
- 1366×700
- 1440×900

## BEFORE

Workflow : `.github/workflows/ux-continuity-before.yml`

Commit workflow : `41fbb31bc315f98d43059967424bacdfc4586d7f`

Le workflow checkout explicitement le SHA intact :
`2926c06166e4d765451bb47e04214508ef4b439c`

Il utilise uniquement le runtime SQLite jetable `scripts/t2_runtime_server.py`, sans donnée cabinet réelle.

Couverture :
- suppression Patient : 5 viewports × 3 positions de scroll = 15 cas ;
- Setup Wizard : 390×844 + 1366×700 ;
- captures PNG + mesures JSON.

Run BEFORE : `34170349446`

État au dernier contrôle : `in_progress`.

Dernière étape observée : installation frontend + Chromium en cours ; installation backend terminée avec succès.

Aucune implémentation produit n’est écrite avant cette preuve, conformément à la doctrine UI/UX.

## Architecture retenue après BEFORE

### `CrownDialog`

Minimum requis :
- `createPortal(..., document.body)` ;
- couverture `100dvh` ;
- hauteur interne bornée + `overflow-y-auto` ;
- verrouillage scroll arrière-plan ;
- focus initial ;
- focus trap ;
- Escape ;
- restauration du focus ;
- API assez petite pour migration progressive, sans refactor massif.

### `useFlowHandoff`

Minimum requis :
1. cible connue après changement d’état ;
2. mesure visibilité réelle ;
3. scroll uniquement si nécessaire ;
4. focus sur premier contrôle utile avec `preventScroll` pour éviter un second saut ;
5. marge compatible headers sticky.

## Scope produit initial

1. `PatientList.tsx` — confirmation suppression.
2. `SetupWizard.tsx` — transitions N → N+1.
3. `PatientDetailsInner.tsx` — changements de surfaces / onglets concernés.

Non-objectifs :
- pas de refactor massif des autres overlays ;
- pas de backend ;
- pas de RBAC ;
- pas de suppression de capacité ;
- aucun déploiement Vercel.

## Git / PR

Repo : `hraaaaf/Digital_crown`

Base master au démarrage :
`2926c06166e4d765451bb47e04214508ef4b439c`

Branche :
`ux/continuity-flow-handoff`

PR draft : `#368` — `UX: continuity flow handoff`

HEAD au lancement BEFORE :
`41fbb31bc315f98d43059967424bacdfc4586d7f`

CI observée au même HEAD :
- UX Continuity BEFORE `34170349446` — in_progress ;
- T2 Runtime Browser Certification `34170349423` — in_progress ;
- CI `34170349410` — in_progress au dernier contrôle.

## Next exact

1. Lire le résultat final du run BEFORE `34170349446`.
2. Si vert : télécharger l’artifact `ux-continuity-before-2926c061`, inspecter `evidence.json` + captures.
3. Si la mesure actuelle ne matérialise pas le panneau lui-même, renforcer le BEFORE sur le même SHA intact et relancer une seule fois.
4. Documenter les mesures BEFORE exactes.
5. Implémenter `CrownDialog` + tests.
6. Migrer suppression Patient.
7. Implémenter `useFlowHandoff` + tests.
8. Migrer Setup Wizard puis PatientDetails.
9. Créer AFTER avec exactement les mêmes viewports / scénarios.
10. Comparer BEFORE / AFTER + score visuel.
11. Tests ciblés + build + CI.
12. Undraft PR si toutes preuves vertes, merge, post-merge.
13. Closeout de ce canonique.

## Séquence restante

`BEFORE final → inspection artifact → (si nécessaire BEFORE renforcé) → implémentation CrownDialog → PatientList → useFlowHandoff → SetupWizard → PatientDetails → tests → AFTER → comparaison + score → CI → undraft → merge → post-merge → closeout`

## Repères de reprise

- chantier/lot : Digital Crown — UX Continuity / Flow Handoff
- Goal : prochaine interaction visible immédiatement sans recherche manuelle
- repo : `hraaaaf/Digital_crown`
- branche : `ux/continuity-flow-handoff`
- PR : `#368` draft
- base : `2926c06166e4d765451bb47e04214508ef4b439c`
- BEFORE run : `34170349446` in_progress au dernier contrôle
- deployment : aucun Vercel
- dernière preuve : contenant transformé MainLayout + modal fixed locale PatientList ; Goal UI et workflow BEFORE commités
- blocage réel : BEFORE doit terminer avant la première modification UI
- Next exact : inspecter le résultat du run BEFORE `34170349446`
- effort suivant : 🟡 moyen

---

Ce fichier reste le point de reprise canonique jusqu’au closeout.