# Landing Cleanup — Canonical

## Goal
Conserver la landing historique de Digital Crown, supprimer les affirmations marketing non prouvées et intégrer le logo officiel déjà utilisé par le Dashboard, sans redesign parasite.

## Succès
- aucun KPI commercial non prouvé sur la landing ;
- aucun claim clinique/IA autonome non supporté par l’architecture courante ;
- aucun engagement de délai 24 h non garanti ;
- un seul lien « Démo » dans la navbar ;
- ciblage pays non inventé ;
- logo officiel du Dashboard utilisé dans le header et le footer ;
- favicon aligné sur le vrai logo ;
- validation visuelle BEFORE/AFTER aux viewports 390 / 430 / 768 / 1280 ;
- tests/build/CI verts sur le changement ;
- workflow temporaire de certification retiré avant merge.

## État vérifié
Les corrections de contenu sont appliquées dans `frontend/src/pages/LandingPage.tsx` : doublon Démo supprimé, ciblage « dentistes algériens » neutralisé, claims IA non prouvés retirés/reformulés, promesses 24/7 et sous 24 h retirées/reformulées, vrai logo `frontend/src/assets/logo.png` utilisé dans header/footer.

Le favicon de `frontend/index.html` pointe désormais vers `/logo.png`.

## Preuves
- Certification visuelle KPI : run GitHub Actions `34280938989` = SUCCESS.
- Artifact : `landing-original-minus-kpis-before-after` (`10077610166`), 16 captures BEFORE/AFTER, viewports 390 / 430 / 768 / 1280, hero + page complète, zéro erreur console/page.
- CI de validation précédente : run `34282118194` = SUCCESS sur frontend tests/build, garde production et suites backend.
- CI du HEAD `2d14d8c753751d2a956921d5bf58ff09a29c5aaf` : run `34285801009` = SUCCESS ; `Mobile SuperAdmin MOB-5H Cert` et `T2 Runtime Browser Certification` = SUCCESS ; certification passkey = SKIPPED.
- Workflow temporaire `.github/workflows/landing-final-cleanup-cert.yml` supprimé au commit `cce40af1ee6872ed890cc1c6fa96b44771d04715` après récupération des preuves.

## Git
- repo : `hraaaaf/Digital_crown`
- branche : `feat/landing-ocean-aa-rebuild`
- PR : `#376`
- Vercel : aucun déploiement demandé ou autorisé.

## Closeout
Le contenu et la preuve visuelle sont bouclés. La seule étape restante avant clôture est de vérifier la CI du HEAD final de closeout puis passer au human gate de merge.

## Next exact
Vérifier les workflows GitHub Actions associés au HEAD final de la branche. Si verts, merge manuel de la PR #376. Aucun déploiement Vercel.
