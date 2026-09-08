# Landing Cleanup — Canonical

## Goal
Conserver la landing historique de Digital Crown, supprimer les affirmations marketing non prouvées et intégrer le logo officiel déjà utilisé par le Dashboard, sans redesign parasite.

## Succès
- aucun KPI commercial non prouvé sur la landing ;
- aucun claim clinique/IA autonome non supporté par l’architecture courante ;
- aucun engagement de délai 24h non garanti ;
- un seul lien « Démo » dans la navbar ;
- ciblage pays non inventé ;
- logo officiel du Dashboard utilisé dans le header et le footer ;
- validation visuelle AFTER aux viewports 390 / 430 / 768 / 1280 ;
- tests/build/CI adaptés au changement verts.

## Preuves déjà acquises
- Les faux KPI `200+ Cabinets actifs`, `50k+ Dossiers patients`, `4.9 Note moyenne` ont été retirés de `LandingPage.tsx`.
- Certification visuelle KPI : run GitHub Actions `34280938989` = SUCCESS, artifact `10077610166`, 16 captures BEFORE/AFTER, zéro erreur console/page.
- Le Dashboard utilise l’asset officiel `frontend/src/assets/logo.png` via `Sidebar.tsx` (`import Logo from '../assets/logo.png'`).
- Le README canonique décrit Digital Crown comme une plateforme de gestion dentaire & orthodontique local-first, sans ciblage pays explicite, et précise qu’aucune dépendance LLM n’est requise dans l’architecture clinique courante.

## Corrections en cours
1. supprimer le doublon `Démo` dans la navbar ;
2. remplacer `dentistes algériens` par un ciblage neutre et vérifiable : cabinets dentaires ;
3. retirer/reformuler `IA intégrée`, `suggestions de traitement` et `IA clinique avancée` ;
4. retirer `Support dédié 24/7` et les promesses `sous 24h` ;
5. remplacer l’icône/wordmark bricolé de la landing par `frontend/src/assets/logo.png` dans header/footer ;
6. recapturer la page complète et le hero en 390 / 430 / 768 / 1280 ;
7. vérifier tests/build/CI ;
8. nettoyer les workflows temporaires et mettre à jour la PR.

## Git
- repo : `hraaaaf/Digital_crown`
- branche : `feat/landing-ocean-aa-rebuild`
- PR : `#376`
- HEAD de reprise avant ce fichier : `9e7e070dc706867e8c5b0627635718621ce3ccee`
- Vercel : aucun déploiement demandé ou autorisé.

## Next exact
Modifier `frontend/src/pages/LandingPage.tsx` avec les 5 corrections validées en conservant la structure historique, puis lancer une certification visuelle ciblée BEFORE/AFTER.
