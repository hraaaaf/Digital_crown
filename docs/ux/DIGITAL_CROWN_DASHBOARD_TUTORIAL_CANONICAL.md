# Digital Crown — Dashboard Tutorial UX — Canonical Roadmap

Status: OPEN
Canonical file: `docs/ux/DIGITAL_CROWN_DASHBOARD_TUTORIAL_CANONICAL.md`
Repo: `hraaaaf/Digital_crown`
Branch: `master`

## Goal final

Supprimer toute interruption automatique non sollicitée liée au tutoriel Dashboard, éliminer la dette associée, puis conserver uniquement une aide volontaire et contextuelle si elle apporte une valeur réelle.

## Succès observable final

1. ouverture de l’application → aucun tutoriel automatique ;
2. retour vers `/dashboard` → aucun tutoriel automatique ;
3. refresh Dashboard → aucun tutoriel automatique ;
4. nouvelle session → aucun tutoriel automatique ;
5. aucune régression Dashboard / navigation / RBAC / responsive ;
6. si une aide subsiste, elle est volontaire, exacte et adaptée aux permissions ;
7. AFTER visuel et score final documentés avant fermeture du chantier.

## État initial vérifié

- `Dashboard.tsx` montait `DayOneTour` directement ;
- `DayOneTour` utilisait `react-joyride ^3.1.0`, un timer de 1 s et `localStorage` ;
- son API contenait encore des props historiques incompatibles avec Joyride v3, notamment `callback` ;
- un second système existe sous `frontend/src/components/GuidedTour/` ;
- score UX initial : **2/10** ;
- décision produit : ne pas améliorer esthétiquement l’auto-tour, le supprimer du flux automatique.

## Roadmap en 4 lots

### T1 — Neutralisation — CLOSED

Goal : empêcher immédiatement tout auto-déclenchement du tutoriel Dashboard.

Implémentation vérifiée :

- `DayOneTour` ne lance plus Joyride ;
- suppression de ses effets timer / `localStorage` / auto-run ;
- garde de régression ajoutée ;
- certification visuelle Dashboard exécutée.

Preuves :

- branche : `ux/dashboard-tutorial-t1-neutralization` ;
- ancienne PR draft : `#338`, fermée non mergée uniquement à cause d’un bug du connecteur Ready-for-review ;
- PR de remplacement : `#341` ;
- HEAD T1 avant merge : `2904cd224542602b68749d2e32a134a78680c8df` ;
- CI PR : run `33679414337` → SUCCESS ;
- Dashboard Visual Certification : run `33679414473` → SUCCESS ;
- merge squash : `99176cb6e48d04a89638c97fc6fbd265e66dc962` → SUCCESS.

Conclusion T1 : **CLOSED avec preuve**.

### T2 — Nettoyage — NEXT

Goal : supprimer la dette devenue inutile et décider du sort du second système de visite.

Actions :

1. retirer l’import et le montage résiduel `<DayOneTour />` de `Dashboard.tsx` ;
2. rechercher toutes les références `DayOneTour` ;
3. supprimer le composant s’il n’a plus aucun usage ;
4. auditer les usages réels de `GuidedTour`, `TourLauncher`, `tourConfig` ;
5. vérifier tous les usages de `react-joyride` avant toute suppression de dépendance ;
6. vérifier exactitude des sélecteurs DOM, navigation, RBAC, responsive et textes exposés ;
7. décider sur preuve : conserver manuel simplifié / simplifier fortement / supprimer.

Succès : aucun code mort injustifié et aucun second auto-launch caché.

Preuve : recherche repo + tests ciblés + build + CI pertinente.

### T3 — Aide volontaire

Goal : conserver uniquement une aide qui apporte une valeur claire sans interrompre le travail clinique.

Principes :

- aucun lancement automatique ;
- privilégier micro-aide contextuelle pour fonctions réellement complexes ;
- réutiliser une zone d’aide existante avant d’ajouter une nouvelle UI ;
- aucune promesse IA ou fonctionnelle non vérifiée ;
- respect strict des permissions du rôle courant.

Succès : l’utilisateur peut obtenir de l’aide volontairement sans friction sur le flux normal.

### T4 — Certification UX & closeout

Goal : prouver le comportement final et fermer le chantier.

Preuves requises :

- tests ouverture / retour Dashboard / refresh / nouvelle session ;
- tests rôles principaux si comportement conditionnel ;
- build frontend ;
- AFTER sur mêmes viewports pertinents ;
- comparaison BEFORE / AFTER ;
- score UX final ;
- CI verte ;
- canonique mis à jour ;
- merge + post-merge vérifié.

Ne pas déclarer CLOSED avant toutes les preuves applicables.

## Critères de non-régression

Le chantier ne doit pas casser : auth, chargement Dashboard, RBAC, recherche patient, quick actions, agenda, finance, cabinet health, responsive, navigation React Router, performance perceptible.

## Règles UX

1. pas d’interruption automatique d’un utilisateur récurrent ;
2. apprentissage par usage > visite générale ;
3. micro-aide contextuelle > tunnel de tutoriel ;
4. aide volontaire et skippable ;
5. aucune navigation automatique inter-pages sans action explicite ;
6. aucune capacité annoncée sans preuve ;
7. permissions respectées ;
8. aucune animation décorative persistante destinée seulement à attirer vers l’aide.

## État actuel

Chantier : OPEN

Terminé :

- audit initial ;
- score UX initial 2/10 ;
- décision produit ;
- **T1 Neutralisation CLOSED** ;
- CI PR verte ;
- certification visuelle Dashboard verte ;
- merge T1 effectué sur `master`.

En cours :

- post-merge du commit `99176cb6e48d04a89638c97fc6fbd265e66dc962` à surveiller si des runs master se matérialisent ;
- aucun déploiement Vercel.

Restant :

1. T2 Nettoyage ;
2. T3 Aide volontaire ;
3. T4 Certification UX & closeout.

## Next exact

**T2 : retirer le montage résiduel `DayOneTour` de `Dashboard.tsx`, rechercher tous les usages `DayOneTour` / `GuidedTour` / `TourLauncher` / `react-joyride`, puis supprimer uniquement la dette prouvée morte et exécuter les tests ciblés.**

## Handover compact

À toute reprise :

1. lire ce fichier ;
2. vérifier `master` / HEAD / derniers runs ;
3. confirmer que T1 est bien présent sur `master` via merge `99176cb6…` ;
4. reprendre directement au `Next exact` ;
5. ne pas refaire l’audit initial sauf contradiction nouvelle.

Aucun déploiement Vercel sans autorisation explicite.
