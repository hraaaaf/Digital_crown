# Digital Crown — Voluntary Contextual Tutorial — Canonical Roadmap

Status: OPEN
Canonical file: `docs/ux/DIGITAL_CROWN_VOLUNTARY_CONTEXTUAL_TUTORIAL_CANONICAL.md`
Repo: `hraaaaf/Digital_crown`
Branch: `ux/voluntary-contextual-tutorial-canonical`
PR: `#352`
Base master at chantier creation: `84b9c0ea1fc7b4d10ea7182535053869e1a2b17a`

## Goal final

Créer un tutoriel Digital Crown utile, contextuel et **100 % volontaire**, capable d'expliquer les workflows critiques sans jamais interrompre spontanément le travail clinique.

## Succès observable

Le chantier n'est CLOSED que si :

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
- résultat final conforme au Goal UI approuvé ;
- aucun déploiement Vercel sans autorisation explicite.

## Goal UI officiel — APPROUVÉ

Nom : `Voluntary Contextual Tutorial — Dashboard Guide Mockup v1`

Original validé : `a_clean_modern_saas_dashboard_ui_mockup_wide_des_1.png`
Dimensions : `1448×1086`
SHA-256 : `fbdc815dca91b051a44667db10958493ee225c1bc2b3857b518c82488285cc59`

Référence versionnée :

`docs/ux/assets/VOLUNTARY_CONTEXTUAL_TUTORIAL_GOAL.svg`

### Invariants visuels

- Dashboard actuel préservé ;
- bouton `Aide / Guide` discret en haut ;
- ouverture exclusivement volontaire ;
- panneau latéral droit non bloquant ;
- label `GUIDE VOLONTAIRE` ;
- titre de type `Découvrir le dashboard` ;
- progression `Étape X sur Y` ;
- étapes courtes ;
- spotlight/contour doux ;
- aucun overlay plein écran ;
- `Commencer` ;
- `Passer` ;
- `Reprendre plus tard` ;
- `Fermer le guide` ;
- microcopy rappelant le caractère volontaire.

## BEFORE certifié

Chantier précédent `Dashboard Tutorial UX` CLOSED sur master `84b9c0ea1fc7b4d10ea7182535053869e1a2b17a`.

Preuves précédentes :

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

### Preuves source

Routes et shell :

- `frontend/src/App.tsx` : `/dashboard`, `/patients`, `/patients/new`, `/patients/:id`, `/patients/:id/archives`, `/agenda` ;
- `frontend/src/components/Layout/MainLayout.tsx` : `Header` persistant sur les routes protégées ;
- `frontend/src/components/Header.tsx` : zone haute globale adaptée à l'entrée Aide/Guide.

Patients :

- `DashboardHeader.tsx` : recherche patient + ajout rapide ;
- `QuickActions.tsx` : nouveau patient / dossiers / agenda ;
- `PatientList.tsx` : recherche nom/prénom/n° dossier ;
- `AddPatientForm.tsx` : formulaire multi-section, disponibilité n° dossier, validation et anti-doublon.

Agenda :

- `AgendaPage.tsx` ;
- `AgendaStudio.tsx` : jour/semaine/mois/multi, navigation temporelle, demandes, import, création/modification RDV ;
- ancres existantes `agenda-header`, `agenda-view-switcher`.

Documents :

- `PatientDetailsInner.tsx` : action + onglet Documents, route contextuelle `?tab=admin` ;
- `DocumentHub.tsx` : Document Studio multi-type ;
- `StudioTabs.tsx` : ancre DOM `document-tabs` confirmée ;
- `DocumentStudioPermissionPolicy.ts` : filtrage par permissions.

Rôles :

- `accessControl.ts` : politiques `patients` / `agenda` ;
- admin/propriétaire/superadmin autorisés ;
- secrétaire et dentiste salarié selon permissions/defaults existants ;
- Documents filtre chaque type selon `prescriptions`, `patients`, `accounting`, `clinical`.

### Décisions TUTO-1

#### 1. Créer un patient — GUIDE COMPLET RETENU

Route : `/patients/new`.

Valeur du guide : forte, car workflow multi-section avec vérification du n° dossier, validation et anti-doublon.

Cible V1 : 4 étapes maximum.

#### 2. Retrouver un patient — PAS DE GUIDE AUTONOME

Routes : `/dashboard` et `/patients`.

Valeur d'un guide multi-étapes : faible. La recherche est déjà explicite.

Décision : une micro-étape dans `Découvrir le dashboard` uniquement.

#### 3. Agenda / RDV — GUIDE COMPLET RETENU

Route : `/agenda`.

Valeur : forte, car plusieurs vues et interactions temporelles.

V1 exclut import, multi-praticien et réglages avancés.

#### 4. Documents — GUIDE COMPLET RETENU

Contexte : dossier patient, `?tab=admin`.

Valeur : forte, car onglets dynamiques, génération/preview et permissions variables.

Le guide doit suivre les permissions réelles et ne jamais exposer un type inaccessible.

### Shortlist V1 verrouillée

Guides complets :

1. `Créer un patient` ;
2. `Agenda / rendez-vous` ;
3. `Documents patient`.

Micro-guide :

- `Retrouver un patient` dans `Découvrir le dashboard`.

Aucun autre guide V1.

### Point d'entrée retenu

`Header` global dans `MainLayout`.

Raisons : persistant entre routes, conforme au Goal UI, ouverture explicite et absence de dépendance au Dashboard.

---

## TUTO-2 — UX architecture — DONE

Spec canonique de lot :

`docs/ux/DIGITAL_CROWN_VOLUNTARY_CONTEXTUAL_TUTORIAL_TUTO2_SPEC.md`

### Architecture verrouillée

- composant maison React/Zustand/Router ;
- `react-joyride` **non réactivé** ;
- bouton `Aide / Guide` dans `Header` ;
- panneau droit non bloquant ;
- aucun backdrop global ;
- spotlight `pointer-events: none` ;
- progression route-aware ;
- aucune navigation automatique au montage ;
- changement de route uniquement via action explicite `Aller à cette étape` ;
- Documents démarrable seulement depuis un dossier patient ;
- filtrage par `hasAccess` et `allowedDocumentStudioTabs` ;
- `Escape` ferme la surface ;
- mobile : panneau contraint au viewport.

### Sémantique d'état

Runtime non persisté :

- `open` ;
- `activeGuide` ;
- `step`.

Progression persistable :

- `paused` ;
- `completed` ;
- `dismissed`.

Invariant principal : **le stockage ne contrôle jamais `open`**.

Donc un refresh / retour Dashboard / nouvelle session peut conserver l'information de progression sans jamais afficher spontanément le guide.

### Actions

- `Commencer` : action explicite ;
- `Passer` : saute l'étape ;
- `Étape suivante` : avance ;
- `Terminer` : marque terminé ;
- `Reprendre plus tard` : persiste l'étape puis ferme ;
- `Fermer le guide` / `Escape` : ferme sans relance forcée.

---

## TUTO-3 — Implémentation — DONE

### Implémenté

- `frontend/src/features/tutorial/VoluntaryTutorial.tsx` ;
- `TutorialHelpButton` monté dans `Header` ;
- `VoluntaryTutorialPanel` monté dans `MainLayout` ;
- store fermé par défaut ;
- progression volontaire persistée ;
- guides filtrés selon permissions ;
- navigation route-aware explicite ;
- panneau droit responsive ;
- spotlight doux ;
- ancres Dashboard dédiées dans `QuickActions` ;
- réutilisation des ancres existantes Agenda / Patient / Documents ;
- `react-joyride` non utilisé ;
- aucun timer dans le nouveau système.

### Tests source

`frontend/src/features/tutorial/VoluntaryTutorial.test.ts`

Assertions :

- fermé par défaut ;
- ouverture explicite ;
- pause ferme sans reprise automatique ;
- absence de timer ;
- absence de react-joyride ;
- entrée Header et panel MainLayout présents ;
- absence d'overlay global dans le nouveau composant ;
- filtrage permissions ;
- ancres Dashboard présentes.

### Preuves de validation TUTO-3

Sur HEAD code `204d30dac80e5893b77d20b95454877cb4678fa9`, puis commits docs/workflow sans modification du code produit :

- CI `33810979054` : job `Frontend (tests & build)` SUCCESS ;
- étape `Test suite` SUCCESS ;
- étape `Build` SUCCESS ;
- Runtime `33810979153` SUCCESS ;
- Dashboard Visual Certification `33810979051` SUCCESS.

TUTO-3 est donc clôturé au niveau code/build/runtime générique. La preuve visuelle spécifique du guide ouvert relève de TUTO-4.

---

## TUTO-4 — Certification — IN PROGRESS

Process obligatoire :

BEFORE → Goal UI → implémentation → AFTER mêmes viewports → comparaison → runtime → tests → score visuel → closeout.

### Certification dédiée ajoutée

Workflow : `.github/workflows/voluntary-tutorial-visual-cert.yml`

Commit d'ajout : `ad8b9d10d8be40a586cb92ac7ee2e86fac68582d`.

Matrix prévue :

- rôles `admin` + `secretary` ;
- viewports `1440`, `1024`, `768`, `430`, `390` ;
- preuve guide fermé malgré progression persistée ;
- ouverture explicite via `Aide / Guide` ;
- capture panneau ouvert ;
- capture guide Dashboard actif + spotlight ;
- `Reprendre plus tard` ferme le guide ;
- refresh après pause ne rouvre pas le guide ;
- erreurs console/page font échouer le job ;
- artifacts visuels uploadés par rôle + viewport.

### État exact

Au dernier check après le commit `ad8b9d10`, aucun run n'était encore associé à ce nouveau HEAD. Aucun résultat de cette certification dédiée n'est donc déclaré à ce stade.

## Dette / garde-fous

- `react-joyride` reste une dépendance potentiellement morte mais n'est pas utilisé ;
- `CrownGuide.tsx` existe encore et **ne doit pas être réutilisé tel quel** ; vérifier ses usages avant toute suppression ;
- ne pas mélanger avec Documents A5, SEC-1, Mobile ou Portability ;
- aucun déploiement Vercel sans autorisation explicite.

## Next exact

1. lire le premier run attaché au HEAD `ad8b9d10` ;
2. si la certification dédiée est rouge : diagnostiquer précisément le job/viewport → corriger → relancer ;
3. si verte : télécharger/inspecter les artifacts AFTER ;
4. comparer aux invariants du Goal UI et au BEFORE ;
5. attribuer le score visuel uniquement sur preuves ;
6. closeout canonique ;
7. vérifier CI finale ;
8. merge PR #352 si toutes les preuves exigées sont vertes ;
9. post-merge.

## Séquence restante

TUTO-4 run dédié → correction si besoin → inspection AFTER → comparaison Goal UI → score → canonical closeout → CI finale → merge → post-merge.
