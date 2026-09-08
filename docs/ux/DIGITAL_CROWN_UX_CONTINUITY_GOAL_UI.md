# DIGITAL CROWN — UX CONTINUITY / FLOW HANDOFF — GOAL UI

Status: GOAL LOCKED — BEFORE PENDING

## Goal UI

Après toute action qui exige une interaction suivante, cette interaction doit être immédiatement visible, identifiable et utilisable sans scroll manuel de recherche.

## Success observable

### Suppression Patient
- déclenchée après scroll haut / milieu / bas ;
- confirmation immédiatement dans le viewport ;
- CTA Annuler / Supprimer accessibles sur viewport court ;
- aucun déplacement manuel requis pour atteindre la confirmation ;
- fond non scrollable pendant l’overlay ;
- focus initial logique ;
- Tab reste dans la modale ;
- Escape ferme ;
- focus restauré après fermeture.

### Setup Wizard
- après `Continuer`, l’étape N+1 devient immédiatement visible ;
- si le haut de la nouvelle étape est hors viewport, repositionnement contrôlé ;
- si la cible est déjà suffisamment visible, aucun scroll inutile ;
- focus transféré vers le premier contrôle utile de la nouvelle étape.

### PatientDetails
- une action qui change automatiquement d’onglet / surface ramène la cible utile dans le viewport si nécessaire ;
- aucun changement de permission ou de capacité métier.

## Référence comportementale

Doctrine :

> Le système déplace l’attention vers sa prochaine attente. L’utilisateur ne cherche jamais où continuer.

### Overlay attendu
1. L’action déclenche la confirmation.
2. L’overlay est rendu hors des contextes de layout via portal `document.body`.
3. L’overlay couvre `100dvh`.
4. Le panneau garde une hauteur maximale compatible avec le viewport et scrolle en interne si nécessaire.
5. Le document derrière est verrouillé.
6. Le focus est contenu dans l’overlay puis restauré à la fermeture.

### Transition attendue
1. L’état passe de N à N+1.
2. Le système identifie la surface cible.
3. Il mesure sa visibilité.
4. Il ne scrolle que si nécessaire.
5. Il place le focus sur la première cible utile sans provoquer un second saut parasite.

## Viewports de certification

- 390×844
- 430×932
- 768×1024
- 1366×700 petit laptop
- 1440×900 desktop de contrôle

## Périmètre initial

- `frontend/src/features/patients/PatientList.tsx`
- `frontend/src/features/admin/SetupWizard/SetupWizard.tsx`
- `frontend/src/features/patients/PatientDetailsInner.tsx`

## Non-objectifs

- aucun refactor massif des modales existantes ;
- aucune modification backend ;
- aucune modification RBAC ;
- aucune suppression de prérogative ;
- aucun déploiement Vercel.

## Preuve requise avant implémentation

Un workflow BEFORE doit checkout explicitement le SHA de base `2926c06166e4d765451bb47e04214508ef4b439c`, reproduire la suppression Patient depuis plusieurs positions de scroll et reproduire le handoff Setup Wizard sur viewport court, puis publier captures + mesures JSON.