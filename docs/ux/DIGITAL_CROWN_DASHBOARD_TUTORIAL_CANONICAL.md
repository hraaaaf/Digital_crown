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

### T2 — Nettoyage — ACTIVE

Goal : supprimer toute dette de tutoriel automatique devenue inutile et empêcher sa réintroduction silencieuse.

Première passe mergée :

- import et montage `DayOneTour` supprimés du Dashboard ;
- `DayOneTour.tsx` et son test obsolète supprimés ;
- garde de régression ajouté ;
- PR `#344` mergée sur `master` via `0d31328e1749a7dd35ec4d8b248e511a94f379c0` ;
- CI `33740817443`, visuel `33740817401` et runtime `33740817497` → SUCCESS.

Audit complémentaire vérifié :

- `TourLauncher.tsx` contenait encore un auto-lancement premier usage après 1500 ms s’il était monté ;
- `GuidedTour.tsx` implémentait navigation inter-pages, résolution patient, overlays et persistance `localStorage` ;
- `tourConfig.ts` exposait encore des textes et promesses fonctionnelles non certifiés dans ce chantier ;
- les racines actives `App.tsx`, `MainLayout.tsx`, `Header.tsx` et `Sidebar.tsx` avaient déjà été vérifiées sans montage de ce second système ;
- `react-joyride` reste déclaré dans `frontend/package.json` et `frontend/package-lock.json`, mais ce second système custom ne l’utilise pas.

Extension T2 en cours :

- branche : `ux/dashboard-tutorial-t2-dormant-cleanup` ;
- PR : `#348` non draft ;
- suppression de `GuidedTour.tsx`, `TourLauncher.tsx` et `tourConfig.ts` ;
- garde de régression renforcé pour scanner tous les fichiers `.ts/.tsx` de `frontend/src` contre les marqueurs du système retiré ;
- aucun déploiement Vercel.

Succès T2 : code des deux auto-tours retiré, garde repo-wide vert, build/tests pertinents verts, PR #348 mergée et master post-merge vérifié.

Ne pas déclarer T2 CLOSED avant ces preuves.

### T3 — Aide volontaire — NEXT après T2

Goal : conserver uniquement une aide qui apporte une valeur claire sans interrompre le travail clinique.

Principes :

- aucun lancement automatique ;
- privilégier micro-aide contextuelle pour fonctions réellement complexes ;
- réutiliser une zone d’aide existante avant d’ajouter une nouvelle UI ;
- aucune promesse IA ou fonctionnelle non vérifiée ;
- respect strict des permissions du rôle courant ;
- si aucune aide globale n’apporte assez de valeur, ne rien ajouter au Dashboard.

Actions :

1. auditer les surfaces d’aide déjà existantes (`Header`, `Sidebar`, Settings, éventuelle aide contextuelle) ;
2. choisir la solution minimale : aide manuelle utile ou aucune nouvelle UI ;
3. si une UI d’aide est ajoutée ou modifiée : BEFORE → Goal visuel → référence/mockup → implémentation → AFTER mêmes viewports → comparaison ;
4. tester RBAC, navigation et absence d’auto-launch.

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
- première passe T2 mergée via PR #344.

En cours :

- **T2 extension dormant cleanup — PR #348** ;
- suppression du second système d’auto-tour et certification du garde repo-wide ;
- aucun déploiement Vercel.

Restant :

1. terminer et merger PR #348 avec preuves ;
2. T3 Aide volontaire ;
3. T4 Certification UX & closeout.

## Next exact

**Valider la PR #348 sur son HEAD final : garde repo-wide + frontend tests/build + runtime/visuel pertinents, merger, vérifier master post-merge, puis passer directement à T3.**

## Handover compact

À toute reprise :

1. lire ce fichier ;
2. vérifier `master` / HEAD / PR #348 / derniers runs ;
3. confirmer T1 merge `99176cb6…` et première passe T2 merge `0d31328e…` ;
4. reprendre directement au `Next exact` ;
5. ne pas déclarer T2 CLOSED avant merge et post-merge de #348.

Aucun déploiement Vercel sans autorisation explicite.
