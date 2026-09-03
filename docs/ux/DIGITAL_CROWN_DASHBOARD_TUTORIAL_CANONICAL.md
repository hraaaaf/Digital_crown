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
- un second système existait sous `frontend/src/components/GuidedTour/` ;
- score UX initial : **2/10** ;
- décision produit : ne pas améliorer esthétiquement l’auto-tour, le supprimer du flux automatique.

## Roadmap en 4 lots

### T1 — Neutralisation — CLOSED

Goal : empêcher immédiatement tout auto-déclenchement du tutoriel Dashboard.

Preuves :

- branche : `ux/dashboard-tutorial-t1-neutralization` ;
- PR : `#341` ;
- HEAD T1 avant merge : `2904cd224542602b68749d2e32a134a78680c8df` ;
- CI PR : run `33679414337` → SUCCESS ;
- Dashboard Visual Certification : run `33679414473` → SUCCESS ;
- merge squash : `99176cb6e48d04a89638c97fc6fbd265e66dc962` → SUCCESS.

Conclusion T1 : **CLOSED avec preuve**.

### T2 — Nettoyage — CLOSED

Goal : supprimer toute dette de tutoriel automatique devenue inutile et empêcher sa réintroduction silencieuse.

Première passe :

- import et montage `DayOneTour` supprimés du Dashboard ;
- `DayOneTour.tsx` et son test obsolète supprimés ;
- PR `#344` mergée via `0d31328e1749a7dd35ec4d8b248e511a94f379c0` ;
- CI `33740817443`, visuel `33740817401` et runtime `33740817497` → SUCCESS.

Extension T2 vérifiée :

- branche : `ux/dashboard-tutorial-t2-dormant-cleanup` ;
- PR : `#348` ;
- suppression de `GuidedTour.tsx`, `TourLauncher.tsx` et `tourConfig.ts` ;
- suppression du dernier montage actif `TourLauncher` dans `frontend/src/features/admin/DocumentStudio/EliteDock.tsx` ;
- garde repo-wide ajouté contre les marqueurs du système automatique retiré ;
- garde corrigé pour exclure son propre fichier du scan ;
- `GuideTower.tsx` préservé : aide contextuelle manuelle, ouverte uniquement par action utilisateur ;
- `react-joyride` reste déclaré dans package/lock comme dette de dépendance morte distincte, sans chemin d’auto-launch démontré.

Preuves finales T2 :

- HEAD final PR #348 : `d4a15fe5793e76ef4ad27f8936d9dc9444b4d933` ;
- CI : run `33776815043` → SUCCESS ;
- T2 Runtime Browser Certification : run `33776814922` → SUCCESS ;
- Dashboard Visual Certification : run `33776815018` → SUCCESS ;
- squash merge PR #348 : `a419fd1dab7e3573b58845578a03735bd33eb48d` ;
- post-merge `master` vérifié exactement sur `a419fd1dab7e3573b58845578a03735bd33eb48d` ;
- `GuidedTour.tsx` absent sur `master` ;
- `TourLauncher.tsx` absent sur `master` ;
- `GuideTower.tsx` présent sur `master` et sans auto-launch.

Conclusion T2 : **CLOSED avec preuve**.

### T3 — Aide volontaire — NEXT

Goal : conserver uniquement une aide qui apporte une valeur claire sans interrompre le travail clinique.

Principes :

- aucun lancement automatique ;
- privilégier micro-aide contextuelle pour fonctions réellement complexes ;
- réutiliser une zone d’aide existante avant d’ajouter une nouvelle UI ;
- aucune promesse IA ou fonctionnelle non vérifiée ;
- respect strict des permissions du rôle courant ;
- si aucune aide globale n’apporte assez de valeur, ne rien ajouter au Dashboard.

Actions :

1. auditer les surfaces d’aide déjà existantes, avec priorité à `GuideTower.tsx` ;
2. vérifier où cette aide est réellement montée et sa visibilité par rôle ;
3. auditer chaque texte fonctionnel contre les capacités réellement prouvées ;
4. choisir la solution minimale : conserver/corriger l’aide manuelle existante ou ne rien ajouter ;
5. si UI modifiée : BEFORE → Goal visuel → référence/mockup → implémentation → AFTER mêmes viewports → comparaison ;
6. tester RBAC, navigation et absence d’auto-launch.

Succès : l’utilisateur peut obtenir de l’aide volontairement si elle est utile, sans aucune friction sur le flux normal.

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
- **T2 Nettoyage CLOSED** via PR #344 + PR #348 et post-merge vérifié.

En cours :

- aucun lot d’implémentation actif au moment de ce closeout ;
- aucun déploiement Vercel.

Restant :

1. T3 Aide volontaire ;
2. T4 Certification UX & closeout.

## Next exact

**Auditer `GuideTower.tsx` et ses points de montage/permissions, vérifier ses textes contre les capacités prouvées, puis choisir la solution T3 minimale avant toute modification UI.**

## Handover compact

À toute reprise :

1. lire ce fichier ;
2. vérifier `master` / HEAD / derniers runs ;
3. confirmer T1 merge `99176cb6…`, T2 première passe `0d31328e…` et T2 final `a419fd1…` ;
4. reprendre directement au `Next exact` ;
5. ne pas déclarer le chantier CLOSED avant T3/T4 et preuves finales applicables.

Aucun déploiement Vercel sans autorisation explicite.
