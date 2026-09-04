# Digital Crown — Voluntary Contextual Tutorial — TUTO-2 UX Architecture

Status: LOCKED
Parent canonical: `docs/ux/DIGITAL_CROWN_VOLUNTARY_CONTEXTUAL_TUTORIAL_CANONICAL.md`
Goal UI: `docs/ux/assets/VOLUNTARY_CONTEXTUAL_TUTORIAL_GOAL.svg`

## Goal

Transformer le Goal UI approuvé et l'audit TUTO-1 en un système réalisable qui reste 100 % volontaire.

## Architecture retenue

### Entrée

- propriétaire UI : `Header` global monté par `MainLayout` ;
- bouton discret `Aide / Guide` ;
- aucune animation d'appel, aucun badge, aucun pulse ;
- seule une action utilisateur explicite ouvre le panneau.

### Surface

- panneau latéral droit `aside` ;
- aucun overlay plein écran ;
- page métier reste interactive ;
- spotlight uniquement visuel et `pointer-events: none` ;
- largeur contrainte au viewport mobile.

### État

État runtime :

- `open` ;
- `activeGuide` ;
- `step`.

Progression persistable :

- `paused` ;
- `completed` ;
- `dismissed`.

Invariant critique : `open` n'est jamais rechargé depuis le stockage. La progression peut être lue au montage mais le panneau reste fermé après refresh, retour Dashboard et nouvelle session.

### Actions

- `Commencer` : action explicite, démarre au début ou reprend une étape volontairement mise en pause ;
- `Passer` : saute l'étape courante ; sur la dernière étape, sort du guide sans le marquer terminé ;
- `Étape suivante` : avance ;
- `Terminer` : marque le guide terminé ;
- `Reprendre plus tard` : persiste l'étape, ferme le panneau ;
- `Fermer le guide` / `Escape` : ferme uniquement la surface courante, sans auto-reprise.

### Routes

- aucune navigation au montage ;
- si l'étape appartient à une autre route, le panneau présente une action explicite `Aller à cette étape` ;
- les étapes Documents ne démarrent que depuis un dossier patient existant ;
- aucune route patient arbitraire n'est inventée.

### Permissions

- Dashboard / création patient : `hasAccess(user, 'patients')` ;
- Agenda : `hasAccess(user, 'agenda')` ;
- Documents : guide exposé seulement si `allowedDocumentStudioTabs(user)` n'est pas vide ;
- les onglets Document restent eux-mêmes filtrés par la politique canonique existante ;
- aucune étape ne doit révéler une fonctionnalité inaccessible au rôle.

### Ciblage

Priorité : ancres dédiées `data-guide` quand une modification locale est justifiée.

Réutilisation sûre d'ancres existantes :

- `data-tour="quick-action-new-patient"` ;
- `data-tour="agenda-header"` ;
- `data-tour="agenda-view-switcher"` ;
- `data-tour="patient-tabs"` ;
- `data-tour="document-tabs"`.

Pour les champs stables du formulaire patient, les sélecteurs sémantiques `name` sont acceptés en V1 pour éviter une refactorisation cosmétique sans valeur fonctionnelle.

### Dépendances

`react-joyride` n'est pas réactivé.

Raison : le besoin V1 est un panneau non bloquant + état simple + spotlight rectangulaire. Les primitives React/Zustand/Router déjà présentes couvrent ce besoin avec moins d'état implicite et moins de risque d'auto-lifecycle indésirable.

## Mapping V1

### Découvrir le Dashboard

1. recherche patient.

### Créer un patient

1. raccourci Dashboard ;
2. numéro de dossier ;
3. identité ;
4. création / anti-doublon.

### Agenda

1. raccourci Dashboard ;
2. navigation temporelle ;
3. choix de vue ;
4. création/modification dans le planning.

### Documents

1. ouvrir Documents depuis le dossier patient ;
2. choisir un type autorisé ;
3. préparer / prévisualiser / générer.

## Matrice de certification requise

Source :

- état fermé par défaut ;
- aucune dépendance `react-joyride` dans le nouveau système ;
- aucun timer dans le nouveau système ;
- bouton explicite Header ;
- panneau monté dans MainLayout ;
- filtrage permissions ;
- ancres Dashboard présentes.

Runtime :

- open ;
- close ;
- Escape ;
- skip ;
- next ;
- pause ;
- explicit resume ;
- route change ;
- refresh ;
- retour Dashboard ;
- nouvelle session ;
- preuve négative d'absence d'auto-launch.

Visuel :

- 1440 ;
- 1024 ;
- 768 ;
- 430 ;
- 390 si surface desktop exposée à ce viewport ;
- panneau ouvert ;
- spotlight ;
- page métier utilisable derrière le panneau ;
- comparaison au Goal UI approuvé.

## Interdits maintenus

- auto-launch ;
- timer ;
- forced resume ;
- overlay global ;
- relance au refresh ;
- relance au retour Dashboard ;
- relance nouvelle session ;
- Vercel sans autorisation explicite.
