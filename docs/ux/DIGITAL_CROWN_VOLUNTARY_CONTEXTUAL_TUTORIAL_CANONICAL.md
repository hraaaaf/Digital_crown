# Digital Crown — Voluntary Contextual Tutorial — Canonical Roadmap

Status: OPEN
Canonical file: `docs/ux/DIGITAL_CROWN_VOLUNTARY_CONTEXTUAL_TUTORIAL_CANONICAL.md`
Repo: `hraaaaf/Digital_crown`
Branch: `ux/voluntary-contextual-tutorial-canonical`
Base master at chantier creation: `84b9c0ea1fc7b4d10ea7182535053869e1a2b17a`

## Goal final

Créer un nouveau système de tutoriel Digital Crown utile, contextuel et **100 % volontaire**, qui aide à comprendre les workflows critiques sans jamais interrompre spontanément le travail clinique.

## Succès observable

Le chantier n'est CLOSED que si :

- aucun tutoriel ne démarre automatiquement au lancement, au montage Dashboard, au retour de route, au refresh ou à une nouvelle session ;
- l'utilisateur lance explicitement le guide depuis une entrée `Aide` / `Guide` claire mais discrète ;
- les guides sont courts, contextualisés et limités aux workflows réellement complexes ;
- l'utilisateur peut `Passer`, `Fermer` et `Reprendre plus tard` ;
- la progression peut être reprise sans bloquer le produit ;
- les états responsive et les rôles ciblés sont certifiés ;
- le rendu final respecte la référence visuelle approuvée ci-dessous ;
- les tests source + runtime + visuels prouvent le comportement ;
- aucun déploiement Vercel n'est effectué sans autorisation explicite.

## Référence visuelle officielle — APPROUVÉE

Le mockup généré et validé par l'utilisateur le 3 septembre 2026 est la **référence visuelle officielle / Goal UI** du chantier.

Nom de référence : `Voluntary Contextual Tutorial — Dashboard Guide Mockup v1`

Source originale validée : `a_clean_modern_saas_dashboard_ui_mockup_wide_des_1.png` — 1448×1086.
SHA-256 de l'original validé : `fbdc815dca91b051a44667db10958493ee225c1bc2b3857b518c82488285cc59`.

Référence visuelle versionnée dans le repo :

![Voluntary Contextual Tutorial — Goal UI](./assets/VOLUNTARY_CONTEXTUAL_TUTORIAL_GOAL.svg)

Le SVG versionné est une transcription vectorielle fidèle des invariants du mockup approuvé. En cas de doute de détail visuel, les invariants ci-dessous + le hash de l'original validé font foi.

### Invariants visuels à reproduire

- Dashboard existant préservé, pas de refonte globale opportuniste ;
- entrée `Aide` / `Guide` visible en haut de l'interface mais non intrusive ;
- ouverture uniquement sur action explicite utilisateur ;
- panneau latéral droit premium, clair, non bloquant ;
- label `GUIDE VOLONTAIRE` ;
- titre de type `Découvrir le dashboard` ;
- progression `Étape 1 sur 4` ;
- liste courte de parcours ;
- étape active mise en évidence ;
- spotlight / contour doux sur la cible, jamais d'overlay agressif plein écran ;
- actions explicites `Commencer`, `Passer`, `Reprendre plus tard`, `Fermer le guide` ;
- microcopy rappelant que le guide est volontaire ;
- esthétique healthcare SaaS calme, arrondie, espacée et cohérente avec Digital Crown.

### Parcours du mockup v1

1. `Créer un patient`
2. `Retrouver un patient`
3. `Agenda`
4. `Documents`

Ces quatre items servent de point de départ, pas de dogme fonctionnel. TUTO-1 doit vérifier dans le produit quels parcours méritent réellement un guide avant d'implémenter.

## Règle UX non négociable

**Le tutoriel ne doit jamais devenir une condition d'utilisation de Digital Crown.**

Pas de :

- auto-launch ;
- timer d'apparition ;
- reprise forcée ;
- overlay global bloquant ;
- relance automatique après refresh ;
- relance automatique après retour Dashboard ;
- popup promotionnelle de type “Découvrez les nouveautés” déguisée en aide.

## BEFORE de référence

Chantier précédent `Dashboard Tutorial UX` fermé sur master `84b9c0ea1fc7b4d10ea7182535053869e1a2b17a`.

État certifié :

- aucun `DayOneTour` ;
- ancien `GuidedTour` / `TourLauncher` retiré ;
- `GuideTower` retiré ;
- Clinical Tips automatiques retirés ;
- Dashboard sans tutoriel ni bulle spontanée ;
- Dashboard Visual Certification final précédent : run `33779398362`, 5/5 artifacts visuels verts ;
- runtime précédent : `33782891558` SUCCESS ;
- CI closeout précédent : `33782891425` SUCCESS.

Le BEFORE de ce nouveau chantier est donc volontairement **un produit calme sans tutoriel**. Toute régression vers une interruption automatique est interdite.

## Lots

### TUTO-1 — Audit des parcours critiques — OPEN

Goal : déterminer où une aide guidée crée une vraie valeur.

À auditer au minimum :

- créer un patient ;
- retrouver un patient ;
- agenda / rendez-vous ;
- documents ;
- réglages ou workflows complexes éventuellement candidats.

Preuve attendue : code réel + routes + composants + comportement observé + shortlist justifiée des guides retenus.

### TUTO-2 — UX architecture + interaction model — PENDING

Goal : transformer le mockup approuvé en spécification réalisable.

À verrouiller :

- point d'entrée du guide ;
- panel / popover / spotlight ;
- navigation entre étapes et routes ;
- persistance et reprise ;
- états `start`, `in progress`, `paused`, `completed`, `dismissed` ;
- accessibilité clavier / focus ;
- responsive ;
- règles par rôle si nécessaires.

Preuve attendue : spec + mockup de référence + mapping composants/routes + tests proposés.

### TUTO-3 — Implémentation — PENDING

Goal : implémenter le système minimal suffisant.

Principe : ne réintroduire `react-joyride` ou une autre dépendance que si l'audit démontre un gain concret. Sinon privilégier un composant maison simple, testable et cohérent avec le produit.

Preuve attendue : code + tests unitaires/intégration + absence prouvée d'auto-launch.

### TUTO-4 — Certification UI/UX — PENDING

Process obligatoire :

BEFORE → Goal écrit → référence/mockup → implémentation → AFTER mêmes viewports → comparaison + tests → score visuel.

Matrix minimale :

- rôles pertinents ;
- desktop 1440 / 1024 / 768 ;
- mobile 430 / 390 si le guide est exposé sur mobile ;
- open / close / skip / pause / resume ;
- route return ;
- refresh ;
- new session ;
- preuve négative : aucune ouverture automatique.

## Score cible

UX cible interne : **≥ 9/10** sans sacrifier le caractère volontaire.

Le score ne peut être 10/10 sans preuve runtime + visuelle + accessibilité suffisante sur les parcours retenus.

## Dette / garde-fous

- `react-joyride` est encore déclaré comme dépendance potentiellement morte ; ne pas le réactiver par réflexe.
- Ne pas mélanger ce chantier avec Documents A5, SEC-1, Mobile ou Portability.
- Pas de déploiement Vercel sans autorisation explicite.

## Next exact

**TUTO-1 : auditer le code et les routes des 4 parcours du mockup, identifier le meilleur point d'entrée `Aide/Guide`, puis produire la shortlist des guides réellement utiles avant toute implémentation.**

## Séquence restante

TUTO-1 audit → TUTO-2 architecture UX → implémentation TUTO-3 → tests source/runtime → AFTER mêmes viewports → comparaison au mockup approuvé → score → canonical closeout → PR/merge → post-merge.
