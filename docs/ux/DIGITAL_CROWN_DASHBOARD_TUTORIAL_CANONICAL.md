# Digital Crown — Dashboard Tutorial UX — Canonical Roadmap

Status: OPEN
Canonical file: `docs/ux/DIGITAL_CROWN_DASHBOARD_TUTORIAL_CANONICAL.md`
Repo: `hraaaaf/Digital_crown`
Branch: `master`

## 1. Goal

Supprimer toute interruption automatique non sollicitée liée au tutoriel lors de l’ouverture de l’application ou du retour vers `/dashboard`, tout en conservant une aide volontaire, utile et contextuelle pour les utilisateurs qui en ont besoin.

### Succès observable

Le comportement suivant doit être vérifié :

1. ouverture de l’application → aucun tutoriel automatique ;
2. navigation vers une autre page puis retour `/dashboard` → aucun tutoriel automatique ;
3. refresh du Dashboard → aucun tutoriel automatique ;
4. nouvelle session utilisateur → aucun tutoriel automatique ;
5. une aide volontaire reste accessible depuis un emplacement explicite ;
6. aucune régression sur Dashboard, navigation, permissions ou responsive.

### Preuve requise

- inspection code avant/après ;
- tests automatisés ciblés ;
- test comportemental navigation + refresh + nouvelle session ;
- BEFORE / AFTER sur mêmes viewports si impact visuel ;
- comparaison visuelle et score final ;
- CI pertinente verte avant closeout.

---

## 2. État vérifié au démarrage du chantier

### Tutoriel actif sur Dashboard

`frontend/src/components/DayOneTour.tsx`

Le composant :

- est monté directement dans `frontend/src/pages/Dashboard.tsx` ;
- utilise `react-joyride` ;
- attend 1 seconde avant lancement ;
- contient 4 étapes ;
- tente de persister la fin du tour via `localStorage` ;
- utilise la clé canonique `digitalcrown_tour_completed` ;
- gère une ancienne clé `digital_crown_tour_completed`.

### Deuxième système de visite présent dans le repo

`frontend/src/components/GuidedTour/`

Fichiers principaux :

- `GuidedTour.tsx`
- `TourLauncher.tsx`
- `tourConfig.ts`

Ce second système contient environ 11 étapes couvrant :

- Bienvenue ;
- Dashboard ;
- Agenda ;
- Dossier Patient ;
- Documents ;
- Bibliothèque ;
- Configuration ;
- conclusion.

Il effectue également de la navigation inter-pages, du ciblage DOM et des pre-actions.

### Dépendance vérifiée

`frontend/package.json` contient :

`react-joyride: ^3.1.0`

### Cause racine probable du relancement permanent

`DayOneTour.tsx` utilise encore le prop historique :

`callback={handleJoyrideCallback}`

alors que React Joyride v3 utilise l’API événementielle v3 (`onEvent`).

Le composant neutralise en plus le typage avec :

`const Joyride: any = OriginalJoyride;`

Ce contournement empêche TypeScript de signaler l’incompatibilité de l’API.

Conséquence cohérente avec le comportement observé : la fin du tour n’est vraisemblablement pas persistée comme prévu ; à chaque nouveau montage de Dashboard, la clé est absente et le tour repart.

Cette cause doit encore être confirmée par test comportemental avant d’être déclarée définitivement certifiée.

---

## 3. Audit UX initial

Score initial retenu : **2/10**.

### Déclenchement — 0/10

Le tutoriel interrompt un utilisateur au retour Dashboard. Pour une application métier cabinet, ce comportement est incompatible avec une navigation fluide.

### Pertinence — 3/10

Les quatre étapes expliquent principalement des éléments déjà visibles :

- créer un patient ;
- activité récente / agenda ;
- statistiques ;
- introduction générale.

La valeur pédagogique est faible par rapport à la friction.

### Contexte — 2/10

Le tutoriel n’est pas réellement contextualisé par rôle, besoin ou niveau d’expérience.

### Copywriting — 3/10

Le contenu contient des formulations marketing et plusieurs promesses fonctionnelles qui doivent être vérifiées avant exposition utilisateur.

### Contrôle utilisateur — 1/10 dans le comportement observé

La fermeture ne produit pas l’effet durable attendu.

### Architecture — 2/10

Deux systèmes de tutoriel coexistent : `DayOneTour` et `GuidedTour`. Cette duplication augmente dette, incohérences et risques de régression.

---

## 4. Décision produit retenue

### Décision principale

**Supprimer l’auto-tour `DayOneTour` du Dashboard.**

Ne pas investir dans une refonte esthétique du tutoriel automatique actuel.

### Modèle cible

1. aucun tutoriel forcé au premier lancement ;
2. aucun tutoriel forcé au retour Dashboard ;
3. interface Dashboard suffisamment auto-explicative ;
4. micro-aides contextuelles uniquement sur les fonctions réellement complexes ;
5. une entrée volontaire du type `Aide` / `Découvrir Digital Crown` peut lancer un guide manuel ;
6. le second système `GuidedTour` doit être audité avant toute réutilisation.

---

## 5. Périmètre du chantier

### Inclus

- suppression de `DayOneTour` du cycle automatique du Dashboard ;
- nettoyage des imports / dépendances devenues inutiles si prouvé ;
- audit d’usage de `react-joyride` avant éventuelle suppression du package ;
- audit du dossier `GuidedTour` ;
- conservation, simplification ou suppression de `GuidedTour` selon usage réel ;
- définition d’une aide volontaire minimale si elle existe déjà ou peut être intégrée proprement sans dette ;
- tests ciblés ;
- validation visuelle si changement UI visible ;
- documentation et closeout canonique.

### Hors périmètre sauf nécessité démontrée

- refonte générale du Dashboard ;
- redesign complet du Help Center ;
- modification métier Patient / Agenda / Documents ;
- nouvelles fonctionnalités IA ;
- déploiement Vercel.

---

## 6. Séquence d’exécution canonique

### T1 — Baseline et BEFORE

Goal : figer l’état visuel et comportemental actuel.

Actions :

- identifier les viewports représentatifs ;
- capturer Dashboard avant changement ;
- reproduire le tutoriel au premier accès ;
- reproduire le relancement au retour Dashboard ;
- vérifier comportement après refresh ;
- noter la clé `localStorage` avant/après fermeture.

Succès : comportement actuel documenté et reproductible.

Preuve : captures + observations + état localStorage.

### T2 — Retirer l’auto-tour

Goal : aucun tutoriel automatique sur Dashboard.

Action principale :

- retirer `<DayOneTour />` de `Dashboard.tsx` ;
- retirer l’import correspondant ;
- ne pas modifier d’autres comportements Dashboard sans nécessité.

Succès : Dashboard s’ouvre directement, sans overlay ou popover de visite.

Preuve : test runtime + tests frontend.

### T3 — Nettoyer la dette DayOneTour

Goal : ne conserver aucun code mort injustifié.

Actions :

- rechercher toutes les références à `DayOneTour` ;
- si aucune autre utilisation : supprimer le composant ;
- rechercher les autres usages de `react-joyride` ;
- supprimer la dépendance uniquement si aucun usage réel ne subsiste ;
- supprimer les clés legacy uniquement si cela ne casse aucun mécanisme de migration encore utile.

Succès : aucun code mort créé par le changement.

Preuve : recherche repo + build.

### T4 — Audit du second GuidedTour

Goal : décider sur preuve s’il mérite d’être conservé.

Vérifier :

- usages réels de `TourLauncher` ;
- usages réels de `GuidedTour` ;
- exactitude des 11 étapes ;
- sélecteurs DOM encore valides ;
- navigation inter-pages ;
- comportement si aucun patient n’existe ;
- permissions / RBAC ;
- responsive ;
- textes et promesses fonctionnelles ;
- références IA obsolètes ou incompatibles avec l’état actuel de Digital Crown.

Décision attendue :

A. conserver en guide volontaire simplifié ;
B. simplifier fortement ;
C. supprimer entièrement.

Recommandation actuelle : **B ou C**, jamais auto-lancé.

### T5 — Aide volontaire minimale

Goal : garder un moyen de découvrir l’application sans intrusion.

Solution minimale privilégiée :

- entrée explicite dans une zone d’aide existante si disponible ;
- ou bouton `Découvrir Digital Crown` dans un emplacement non intrusif ;
- aucun badge clignotant permanent ;
- aucun lancement automatique.

Succès : utilisateur peut lancer volontairement l’aide, sans impact sur le flux normal.

### T6 — Tests

Tests minimum :

1. rendu Dashboard sans tour ;
2. navigation Dashboard → autre page → Dashboard ;
3. refresh Dashboard ;
4. nouvelle session ;
5. utilisateur avec ancien `localStorage` ;
6. utilisateur sans aucune clé tour ;
7. rôles principaux si comportement conditionnel ;
8. build frontend ;
9. tests unitaires / intégration ciblés ;
10. lint pertinent.

### T7 — AFTER visuel

Obligatoire si un élément visuel est retiré, déplacé ou ajouté.

Même viewports que BEFORE.

Comparer :

- obstruction du Dashboard ;
- hiérarchie ;
- premier écran utile ;
- navigation ;
- mobile / desktop ;
- éventuel accès à l’aide.

Score visuel final uniquement après comparaison.

### T8 — Closeout

Avant fermeture :

- tests verts ;
- comportement observé conforme ;
- AFTER validé ;
- README/docs uniquement si nécessaire ;
- ce fichier canonique mis à jour ;
- commit/PR/merge selon flux Git retenu ;
- validation post-merge si merge effectué.

Ne pas déclarer CLOSED avant preuve.

---

## 7. Critères de non-régression

Le chantier ne doit pas casser :

- auth ;
- chargement Dashboard ;
- RBAC ;
- recherche patient ;
- quick actions ;
- agenda ;
- finance ;
- cabinet health ;
- responsive ;
- navigation React Router ;
- performance perceptible.

---

## 8. Règles UX du chantier

1. pas d’interruption automatique d’un utilisateur récurrent ;
2. privilégier apprentissage par usage ;
3. micro-aide contextualisée > visite générale ;
4. aide toujours skippable et volontaire ;
5. ne jamais déplacer automatiquement l’utilisateur entre pages sans action explicite ;
6. ne jamais annoncer une capacité non vérifiée ;
7. respecter les permissions du rôle courant ;
8. pas d’animation décorative persistante destinée uniquement à attirer vers le tutoriel.

---

## 9. Risques connus

### R1 — Suppression d’une aide réellement utilisée

Mitigation : conserver une entrée volontaire si un besoin utilisateur est démontré.

### R2 — `GuidedTour` dépend de sélecteurs obsolètes

Mitigation : audit DOM avant réutilisation.

### R3 — Guides qui exposent des modules indisponibles selon rôle

Mitigation : filtrage par permission ou suppression du guide transversal.

### R4 — Textes fonctionnellement faux ou obsolètes

Mitigation : validation contre code et comportement réel avant exposition.

### R5 — package `react-joyride` retiré alors qu’encore utilisé

Mitigation : recherche repo complète avant suppression de dépendance.

---

## 10. État actuel

Chantier : OPEN

Terminé :

- audit code initial ;
- identification de `DayOneTour` ;
- identification du second système `GuidedTour` ;
- identification de `react-joyride ^3.1.0` ;
- diagnostic probable de l’incompatibilité API v2/v3 ;
- score UX initial 2/10 ;
- décision produit : supprimer l’auto-tour.

En cours :

- aucun changement de code encore appliqué dans ce chantier.

Restant :

1. BEFORE comportemental / visuel ;
2. suppression auto-tour ;
3. nettoyage dette ;
4. audit GuidedTour ;
5. aide volontaire minimale si justifiée ;
6. tests ;
7. AFTER ;
8. score final ;
9. closeout ;
10. Git/merge/post-merge selon flux retenu.

---

## 11. Next exact

**Capturer le BEFORE du Dashboard et reproduire précisément le relancement du tutoriel, puis retirer `DayOneTour` du Dashboard et exécuter les tests ciblés.**

---

## 12. Handover compact

À toute reprise :

1. lire ce fichier ;
2. vérifier branche / HEAD ;
3. vérifier si `DayOneTour` est encore monté dans `Dashboard.tsx` ;
4. vérifier l’usage réel de `GuidedTour` ;
5. vérifier les derniers tests / CI ;
6. reprendre au `Next exact` sans refaire l’audit déjà prouvé.

Aucun déploiement Vercel sans autorisation explicite.
