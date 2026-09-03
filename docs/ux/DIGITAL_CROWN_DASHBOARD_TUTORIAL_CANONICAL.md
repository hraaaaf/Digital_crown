# Digital Crown — Dashboard Tutorial UX — Canonical Roadmap

Status: CLOSED
Canonical file: `docs/ux/DIGITAL_CROWN_DASHBOARD_TUTORIAL_CANONICAL.md`
Repo: `hraaaaf/Digital_crown`
Branch: `master`

## Goal final

Supprimer toute interruption automatique non sollicitée liée au tutoriel Dashboard et ne conserver aucune aide globale qui interrompe spontanément le travail clinique.

## Résultat final vérifié

- aucun `DayOneTour` monté ou présent ;
- ancien système `GuidedTour` / `TourLauncher` / `tourConfig` retiré ;
- dernier montage `TourLauncher` retiré de `EliteDock.tsx` ;
- `GuideTower.tsx` retiré car non monté et contenant des promesses non certifiées ;
- timers automatiques `Clinical Tips` 10 s / 120 s retirés de `Sidebar.tsx` ;
- aucune nouvelle UI d’aide forcée ajoutée ;
- garde de régression repo-wide présente dans `frontend/src/features/dashboard/dashboardTutorialT1.test.ts`.

## Lots

### T1 — Neutralisation — CLOSED

- PR `#341` ;
- HEAD `2904cd224542602b68749d2e32a134a78680c8df` ;
- CI `33679414337` SUCCESS ;
- Dashboard Visual `33679414473` SUCCESS ;
- merge `99176cb6e48d04a89638c97fc6fbd265e66dc962`.

### T2 — Nettoyage — CLOSED

Première passe :
- PR `#344` ;
- merge `0d31328e1749a7dd35ec4d8b248e511a94f379c0` ;
- CI `33740817443`, visuel `33740817401`, runtime `33740817497` SUCCESS.

Extension :
- PR `#348` ;
- HEAD final `d4a15fe5793e76ef4ad27f8936d9dc9444b4d933` ;
- CI `33776815043` SUCCESS ;
- runtime `33776814922` SUCCESS ;
- visuel `33776815018` SUCCESS ;
- merge `a419fd1dab7e3573b58845578a03735bd33eb48d` ;
- closeout canonique PR `#349`, merge `26a53698e593a4ad368ab782bb3ad0181263cb9a`.

### T3 — Aide volontaire — CLOSED

Audit :
- `GuideTower.tsx` n’était monté ni dans `App.tsx`, ni `MainLayout.tsx`, ni `Header.tsx`, ni `Sidebar.tsx` ;
- `Sidebar.tsx` déclenchait encore automatiquement un Clinical Tip après 10 s puis toutes les 120 s.

Décision minimale : ne pas ajouter de nouvelle aide globale et retirer les interruptions restantes.

Implémentation :
- PR `#350` ;
- HEAD `6648826cc90ba81d6115911a140766ac7cfae723` ;
- suppression des timers et de `ClinicalTipBubble` dans le shell Sidebar ;
- suppression de `GuideTower.tsx` ;
- animation IA indépendante préservée ;
- garde de régression renforcée.

Preuves :
- CI `33779398441` SUCCESS ;
- Dashboard Visual Certification `33779398362` SUCCESS ;
- T2 Runtime Browser Certification `33779398389` SUCCESS ;
- Settings audit `33779398395` SUCCESS ;
- merge PR #350 `7f8a2d271bc0c99a73496c9afcaf4e2565e40a00` ;
- post-merge `master` vérifié sur ce SHA.

### T4 — Certification UX & closeout — CLOSED

Preuves finales :

- garde source : aucun chemin d’auto-tour, aucun `TourLauncher`, aucun stockage de completion de l’ancien système, aucun timer `triggerTip`, aucune `ClinicalTipBubble` dans `Sidebar` ;
- CI frontend/build du HEAD mergé : run `33779398441` SUCCESS ;
- runtime navigateur du HEAD mergé : run `33779398389` SUCCESS ;
- AFTER visuel : run `33779398362`, 5/5 jobs de capture SUCCESS (`baseline-d2`, `d2`, `d3`, `d7`, `d9`) ;
- rôles/viewports de référence du chantier : ADMIN + SECRETAIRE, 1440 / 1024 / 768 / 430 / 390 ;
- le comportement final est indépendant du cycle de vie Dashboard : aucun mécanisme automatique ne subsiste à déclencher au montage, retour route, refresh ou nouvelle session ;
- aucun déploiement Vercel effectué.

## Comparaison BEFORE / AFTER

BEFORE : tutoriel automatique puis second système dormant, plus Clinical Tips automatiques après 10 s / 120 s.

AFTER : Dashboard visuellement préservé au repos, sans overlay, bulle, tour ni aide globale qui apparaît spontanément.

Score UX initial : **2/10**.
Score UX final interne : **9/10**.

Base du score final :
- déclenchement non sollicité : 10/10 ;
- contrôle utilisateur : 10/10 ;
- pertinence/contextualité : 9/10 ;
- architecture : 9/10 ;
- préservation visuelle : 5/5 captures de certification vertes.

Le score n’est pas 10/10 car aucune nouvelle micro-aide contextuelle n’a été certifiée pour les workflows complexes ; le choix produit final est volontairement minimal plutôt que décoratif.

## Dette hors chantier

- `react-joyride` reste déclaré dans `frontend/package.json` / lockfile comme dépendance morte à nettoyer séparément si confirmé sans autre consommateur.

## État final

Chantier : **CLOSED**.

Dernier master produit vérifié avant ce closeout docs : `7f8a2d271bc0c99a73496c9afcaf4e2565e40a00`.

Aucun blocage produit restant dans ce chantier.
