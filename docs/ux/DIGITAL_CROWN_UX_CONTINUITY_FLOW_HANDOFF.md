# DIGITAL CROWN — UX CONTINUITY / FLOW HANDOFF — CANONICAL HANDOVER

Status: AUDIT VERIFIED — IMPLEMENTATION NOT STARTED

## Goal

Garantir que, après toute action qui exige une interaction suivante, cette prochaine interaction soit immédiatement visible, identifiable et utilisable sans scroll manuel de recherche.

Le chantier couvre en priorité :
- confirmations / modales critiques ;
- transitions multi-étapes ;
- changements automatiques d’onglet / sous-flow ;
- petits écrans et mobile ;
- navigation clavier et focus.

## Success

Le lot ne peut être déclaré CLOSED que si les preuves montrent :
- suppression Patient déclenchée après scroll haut / milieu / bas → confirmation immédiatement visible ;
- petits laptops et mobiles → CTA de confirmation toujours accessibles ;
- wizard étape N → N+1 → nouvelle étape immédiatement visible ;
- changements automatiques d’onglet / surface → cible utile ramenée dans le viewport si nécessaire ;
- aucun scroll forcé inutile lorsque la cible est déjà visible ;
- focus initial logique ;
- Tab contenu dans la modale ;
- Escape ferme la modale ;
- focus restauré après fermeture ;
- pas d’overflow horizontal ni de régression fonctionnelle ;
- BEFORE / AFTER capturés aux mêmes viewports ;
- tests ciblés + build + CI verts ;
- closeout documentaire + merge + post-merge verts.

## Audit vérifié

### 1. Confirmation de suppression Patient — P1 UX

Fichier : `frontend/src/features/patients/PatientList.tsx`

Constats vérifiés :
- la confirmation est bien une modale `fixed inset-0` ;
- elle est rendue directement dans le subtree de `PatientList` ;
- pas de `createPortal(..., document.body)` ;
- pas de verrouillage explicite du scroll du document ;
- pas de focus trap ;
- pas d’autofocus vers une cible logique ;
- pas de restauration du focus après fermeture ;
- utilisation de `h-screen w-screen` plutôt qu’une stratégie `dvh` robuste ;
- pas de stratégie explicite `max-height + overflow-y-auto` pour viewport court.

Conclusion : le défaut n’est pas un simple oubli de `position: fixed`. L’implémentation locale reste fragile selon le contexte CSS et le viewport.

Important : aucun facteur unique n’a encore été prouvé comme cause exclusive du déplacement observé. Une reproduction BEFORE est obligatoire avant correction.

### 2. Flows multi-étapes — défaut confirmé

Fichier : `frontend/src/features/admin/SetupWizard/SetupWizard.tsx`

Le passage à l’étape suivante fait essentiellement :

```ts
setCurrentStep(prev => Math.min(prev + 1, 7));
```

Aucun mécanisme global de :
- `scrollIntoView` ;
- repositionnement du viewport ;
- focus vers la nouvelle étape ;
- transfert d’attention vers le premier contrôle utile.

### 3. Changements de surfaces / onglets

Fichier : `frontend/src/features/patients/PatientDetailsInner.tsx`

Plusieurs transitions changent l’onglet ou la surface via `setSearchParams(...)`, sans doctrine globale de transfert du viewport / focus vers le nouveau contenu.

### 4. Cause racine architecturale

Le produit sait changer d’état, mais ne possède pas encore de doctrine globale pour déplacer l’attention utilisateur vers ce nouvel état.

Les overlays / modales sont fragmentés entre implémentations locales. Aucun primitive global `ConfirmDialog` / `Modal` / `Portal` n’a été identifié dans les composants communs pendant l’audit.

## Recommandation d’architecture

### A. Primitive globale `CrownDialog` / `CrownConfirmDialog`

Contrat attendu :
- portal vers `document.body` ;
- couverture viewport fiable avec `100dvh` ;
- scroll interne de la modale si hauteur insuffisante ;
- verrouillage du background scroll ;
- focus trap ;
- Escape ;
- focus initial sûr ;
- restauration du focus ;
- responsive mobile / petit laptop ;
- aucune modification des permissions ou capacités métier existantes.

### B. Primitive / hook `useFlowHandoff()`

À chaque transition N → N+1 ou changement de surface :
1. déterminer la nouvelle cible utile ;
2. vérifier si elle est suffisamment visible ;
3. si non visible, `scrollIntoView` avec comportement contrôlé ;
4. positionner le focus sur le premier contrôle utile ;
5. ne pas scroller si la cible est déjà visible.

### C. Longs formulaires

Évaluer des CTA `Suivant` / `Confirmer` sticky lorsque cela réduit réellement la friction, sans masquer le contenu ni créer une seconde barre d’action concurrente.

## Doctrine UX verrouillée

Principe :

> Après toute action nécessitant une interaction suivante, cette interaction doit être visible immédiatement et identifiable sans recherche manuelle dans la page.

Exceptions acceptables :
- aucune cible unique n’existe ;
- le scroll automatique détériorerait clairement le contexte utilisateur ;
- l’action suivante est volontairement différée.

Dans ces cas, le comportement doit être explicitement documenté et testé.

## Méthode UI/UX obligatoire

Avant tout changement visuel :
1. BEFORE mêmes viewports ;
2. Goal écrit ;
3. mockup / référence de comportement ;
4. implémentation ;
5. AFTER mêmes viewports ;
6. comparaison ;
7. tests ;
8. score visuel.

Viewports minimum recommandés pour ce chantier :
- mobile étroit : 390×844 ;
- mobile large : 430×932 ;
- tablette : 768×1024 ;
- petit laptop : viewport desktop court à définir lors du BEFORE.

## Scope initial

Priorité 1 :
- `PatientList.tsx` — suppression Patient ;
- `SetupWizard.tsx` — transitions étape N → N+1 ;
- `PatientDetailsInner.tsx` — changements d’onglet / surface déclenchés par action.

Priorité 2 :
- inventaire des autres modales / sheets locales ;
- migration progressive vers le primitive global uniquement si cela réduit la duplication sans risque de régression.

Interdit : refactor massif non nécessaire avant preuve du comportement.

## État repo vérifié au démarrage

Repo : `hraaaaf/Digital_crown`

Branche : `master`

HEAD vérifié pendant l’audit :
`fd19dab006d46f274946fd932927b9ac4821d3ec`

Ce HEAD correspond au merge PR #366 :
`docs(mobile): close MOB-5F Quick Document Studio`

Aucune PR n’a été créée pour ce chantier UX Continuity au moment de ce handover.

Aucun déploiement Vercel demandé ou autorisé pour ce chantier.

## Preuves audit déjà disponibles

- `frontend/src/features/patients/PatientList.tsx` : confirmation locale + logique de saisie du nom exact + absence des mécanismes de focus / portal listés ci-dessus ;
- `frontend/src/features/admin/SetupWizard/SetupWizard.tsx` : transition `setCurrentStep(...)` sans handoff viewport/focus ;
- `frontend/src/features/patients/PatientDetailsInner.tsx` : transitions `setSearchParams(...)` sans handoff global ;
- arbre `frontend/src/components` : aucun primitive global ConfirmDialog / Modal / Portal identifié pendant l’audit.

## Next exact

1. Re-vérifier repo / HEAD / PR / CI avant toute modification.
2. Capturer un BEFORE reproductible du cas suppression Patient, sur plusieurs positions de scroll.
3. Capturer un BEFORE du Setup Wizard N → N+1 sur viewport court.
4. Écrire le Goal UI précis et la référence comportementale.
5. Implémenter le minimum global fiable : `CrownDialog` + mécanisme `FlowHandoff`.
6. Migrer d’abord Patient suppression + Setup Wizard + transitions PatientDetails concernées.
7. Tester focus / clavier / Escape / scroll / petits viewports.
8. Produire AFTER mêmes viewports et comparaison BEFORE / AFTER.
9. Lancer tests ciblés + build + CI.
10. Documenter score visuel et écarts restants.
11. Ouvrir PR, valider CI, merger si vert, vérifier post-merge.
12. Mettre à jour ce fichier canonique avec preuves exactes et état final.

## Séquence restante

`BEFORE reproductible → Goal UI → primitive globale minimale → migration Patient suppression → migration Setup Wizard → migration transitions PatientDetails → tests ciblés → AFTER mêmes viewports → comparaison + score → CI → PR → merge → post-merge → closeout canonique`

## Handover compact

GOAL : supprimer la friction où l’utilisateur doit chercher manuellement la prochaine interaction après une action ou une transition.

ÉTAT VÉRIFIÉ : audit terminé ; problème transversal confirmé dans le code ; aucune implémentation de correction encore commencée.

CAUSE RACINE : absence de doctrine globale de viewport/focus handoff + overlays locaux non unifiés.

PRIORITÉ : P1 UX.

SCOPE PREMIER LOT : suppression Patient, Setup Wizard, transitions PatientDetails.

RÈGLE PRODUIT : aucune prérogative ou capacité métier supprimée ; uniquement comportement UX / focus / viewport / confirmation.

BLOCAGE RÉEL : aucun blocage externe. La seule étape préalable obligatoire est la capture BEFORE conformément à la doctrine UI/UX.

NEXT EXACT : re-vérifier HEAD puis capturer BEFORE suppression Patient et Setup Wizard avant toute modification.

## Repères

- chantier/lot : Digital Crown — UX Continuity / Flow Handoff
- Goal : prochaine action visible immédiatement sans scroll manuel de recherche
- repo : `hraaaaf/Digital_crown`
- branche : `master`
- PR : aucune au moment de création du canonique
- HEAD audit : `fd19dab006d46f274946fd932927b9ac4821d3ec`
- CI : aucune CI spécifique à ce chantier lancée au moment de création
- deployment : aucun Vercel
- dernière preuve : audit code PatientList / SetupWizard / PatientDetails
- blocage réel : aucun
- Next exact : vérifier HEAD courant puis capturer BEFORE
- effort suivant : 🟡 moyen

---

Ce fichier est le point de reprise canonique du chantier jusqu’à closeout.