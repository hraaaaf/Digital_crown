# Digital Crown — Voluntary Contextual Tutorial — Canonical Roadmap

Status: CLOSED
Canonical file: `docs/ux/DIGITAL_CROWN_VOLUNTARY_CONTEXTUAL_TUTORIAL_CANONICAL.md`
Repo: `hraaaaf/Digital_crown`
Branch: `ux/voluntary-contextual-tutorial-canonical`
PR: `#352` — MERGED
Base master at chantier creation: `84b9c0ea1fc7b4d10ea7182535053869e1a2b17a`
Certified code HEAD: `a637241fee02dacb1364d303c9a1e730d618bd7f`
Canonical closeout HEAD: `0eaa87db310b99616d855926d2454435975b07ab`
Merge commit on master: `34a033ad018ec58e04273489e585b88e7786e4a5`

## Goal final

Créer un tutoriel Digital Crown utile, contextuel et **100 % volontaire**, capable d'expliquer les workflows critiques sans jamais interrompre spontanément le travail clinique.

## Succès observable

- aucun auto-launch au lancement, au montage Dashboard, au retour de route, au refresh ou à une nouvelle session ;
- aucun timer d'apparition ;
- aucune reprise forcée ;
- lancement explicite depuis `Aide / Guide` ;
- guides courts et contextuels ;
- `Passer`, `Fermer`, `Reprendre plus tard` ;
- progression reprenable uniquement après action utilisateur ;
- filtrage par rôles/permissions ;
- responsive certifié ;
- tests source + runtime + visuels ;
- résultat final aligné aux invariants du Goal UI approuvé ;
- aucun déploiement Vercel effectué.

## Goal UI officiel — APPROUVÉ

Nom : `Voluntary Contextual Tutorial — Dashboard Guide Mockup v1`

Original validé : `a_clean_modern_saas_dashboard_ui_mockup_wide_des_1.png`
Dimensions : `1448×1086`
SHA-256 : `fbdc815dca91b051a44667db10958493ee225c1bc2b3857b518c82488285cc59`
Référence versionnée : `docs/ux/assets/VOLUNTARY_CONTEXTUAL_TUTORIAL_GOAL.svg`

Invariants : Dashboard préservé ; bouton `Aide / Guide` discret ; ouverture exclusivement volontaire ; panneau droit non bloquant ; label `GUIDE VOLONTAIRE` ; progression `Étape X sur Y` ; étapes courtes ; spotlight doux ; aucun overlay plein écran ; actions `Commencer`, `Passer`, `Reprendre plus tard`, `Fermer le guide` ; microcopy volontaire.

## BEFORE certifié

Chantier précédent `Dashboard Tutorial UX` CLOSED sur master `84b9c0ea1fc7b4d10ea7182535053869e1a2b17a`.

Preuves :
- DayOneTour absent ;
- GuidedTour / TourLauncher retirés ;
- GuideTower retiré ;
- timers Clinical Tips automatiques retirés ;
- Dashboard sans aide spontanée ;
- Dashboard Visual Certification `33779398362` : 5/5 artifacts verts ;
- Runtime `33782891558` SUCCESS ;
- CI closeout `33782891425` SUCCESS.

Toute réintroduction d'une aide automatique est une régression.

---

## TUTO-1 — Audit des parcours critiques — DONE

Guides complets retenus :
1. `Créer un patient` ;
2. `Agenda / rendez-vous` ;
3. `Documents patient`.

Micro-guide : `Retrouver un patient` dans `Découvrir le dashboard`.

Point d'entrée : `Header` global dans `MainLayout`.

---

## TUTO-2 — UX architecture — DONE

Spec : `docs/ux/DIGITAL_CROWN_VOLUNTARY_CONTEXTUAL_TUTORIAL_TUTO2_SPEC.md`.

Architecture verrouillée :
- React/Zustand/Router maison ;
- `react-joyride` non réactivé ;
- bouton `Aide / Guide` dans `Header` ;
- panneau droit non bloquant ;
- aucun backdrop global ;
- spotlight `pointer-events: none` ;
- navigation route-aware uniquement après action explicite ;
- Documents démarrable uniquement depuis un dossier patient ;
- filtrage `hasAccess` + `allowedDocumentStudioTabs` ;
- `Escape` ferme ;
- mobile contraint au viewport ;
- état persisté ne contrôle jamais `open`.

---

## TUTO-3 — Implémentation — DONE

Implémenté :
- `frontend/src/features/tutorial/VoluntaryTutorial.tsx` ;
- `TutorialHelpButton` monté dans `Header` ;
- `VoluntaryTutorialPanel` monté dans `MainLayout` ;
- store fermé par défaut ;
- progression volontaire persistée ;
- guides filtrés selon permissions ;
- navigation route-aware explicite ;
- panneau droit responsive ;
- spotlight doux ;
- ancres Dashboard dédiées ;
- aucun timer dans le nouveau système.

Tests source : `frontend/src/features/tutorial/VoluntaryTutorial.test.ts`.

Preuves intermédiaires :
- CI `33810979054` SUCCESS ;
- Runtime `33810979153` SUCCESS ;
- Dashboard Visual `33810979051` SUCCESS.

---

## TUTO-4 — Certification — DONE

Workflow : `.github/workflows/voluntary-tutorial-visual-cert.yml`.

### Certification finale sur `a637241f`

- Voluntary Tutorial Visual Certification `33850825720` : **SUCCESS** ;
- matrice rôles/viewports : **10/10 SUCCESS** ;
- rôles : `admin`, `secretary` ;
- viewports : `1440`, `1024`, `768`, `430`, `390` ;
- CI `33850825731` : **SUCCESS** ;
- T2 Runtime Browser Certification `33850825503` : **SUCCESS** ;
- Dashboard Visual Certification `33850825603` : **SUCCESS**.

### Revalidation du closeout sur `0eaa87db`

- Voluntary Tutorial Visual Certification `33855896535` : **SUCCESS** ;
- Dashboard Visual Certification `33855896473` : **SUCCESS** ;
- T2 Runtime Browser Certification `33855896472` : **SUCCESS** ;
- CI `33855896726` : **SUCCESS**.

Artifacts TUTO-4 présents pour les 10 combinaisons rôle/viewport. Exemples inspectés :
- `voluntary-tutorial-admin-1440` ;
- `voluntary-tutorial-secretary-390`.

Assertions certifiées :
- progression persistée n'auto-ouvre pas le guide ;
- ouverture uniquement via `Aide / Guide` ;
- panneau ouvert capturé ;
- guide Dashboard actif capturé avec spotlight ;
- `Reprendre plus tard` ferme ;
- refresh après pause ne rouvre pas ;
- erreurs console/page font échouer le job.

### Comparaison Goal UI → AFTER

Conforme aux invariants principaux :
- entrée Aide discrète en haut ;
- panneau latéral droit ;
- label `GUIDE VOLONTAIRE` ;
- hiérarchie claire ;
- progression visible ;
- actions explicites ;
- microcopy rappelant le caractère volontaire ;
- spotlight doux ;
- pas de backdrop bloquant ;
- responsive jusqu'à 390 px.

Écart assumé : le Dashboard micro-guide reste volontairement mono-étape (`Étape 1 sur 1`) tandis que le mockup illustrait un parcours Dashboard 4 étapes. Cette différence correspond à la décision TUTO-1 de garder `Retrouver un patient` comme micro-guide et les workflows critiques comme guides séparés.

Score visuel après inspection des captures : **8.8/10**.

- desktop : très proche de la direction Goal UI, panneau calme et lisible ;
- mobile : fonctionnel et cohérent, mais plus dense car le panneau occupe presque toute la largeur.

## Merge / post-merge

PR `#352` : **MERGED** le 4 septembre 2026.

Merge commit : `34a033ad018ec58e04273489e585b88e7786e4a5`.

Vérification post-merge :
- `master` pointe sur `34a033ad018ec58e04273489e585b88e7786e4a5` ;
- le merge commit a pour parents `84b9c0ea1fc7b4d10ea7182535053869e1a2b17a` et `0eaa87db310b99616d855926d2454435975b07ab` ;
- PR #352 est `closed` et `merged: true` ;
- aucun déploiement Vercel effectué.

## Dette / garde-fous

- `react-joyride` reste une dépendance potentiellement morte mais n'est pas utilisé ;
- `CrownGuide.tsx` existe encore et ne doit pas être réutilisé tel quel sans audit ;
- ne pas mélanger avec Documents A5, SEC-1, Mobile ou Portability ;
- aucun déploiement Vercel effectué ou autorisé dans ce chantier.

## Closeout

TUTO-1 DONE → TUTO-2 DONE → TUTO-3 DONE → TUTO-4 DONE → PR #352 MERGED → post-merge master VERIFIED.

Le chantier est **CLOSED**.
