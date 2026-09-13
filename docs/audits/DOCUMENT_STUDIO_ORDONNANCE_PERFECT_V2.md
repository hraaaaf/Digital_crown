# Document Studio — Ordonnance Perfect V2

Date: 2026-09-13
Baseline: `master` `dca24d01ca5591d4255f3ac85f79a32ab6d673c1`
Branch: `ux/ordonnance-perfect-v2`

## Goal

Faire de l’onglet Ordonnance la surface la plus rapide et lisible du Document Studio, sans modifier le moteur clinique, pharmacologique, la génération PDF ni les contrats backend.

## Succès observable

- Le contenu clinique utile est visible plus haut dans la page, particulièrement à 390/430 px.
- Le header Studio est compact sur Ordonnance.
- Le bloc sécurité patient/médicaments reste présent mais moins dominant visuellement.
- Les actions secondaires n’écrasent pas la zone de saisie.
- La saisie rapide et les lignes médicament restent le centre de gravité visuel.
- Aucun chevauchement sur 390, 430, 768, 1280.
- Le Live Preview reste un overlay responsive et ne redevient pas un drawer étouffant.
- Aucune régression fonctionnelle sur dirty state, sécurité, protocoles, autocomplete, génération, archive et impression.

## BEFORE vérifié

Preuve de référence: artefact GitHub Actions `t2-browser-evidence`, run T2 `34751838021`, artefact `10316051646`, viewport 1280×900 + captures 390×844 et 430×932.

Constats:

1. Trop de hauteur consommée avant la prescription: navigation dossier + StudioHeader + auteur/date + tabs + mentions légales + contexte sécurité.
2. Le moteur clinique est riche, mais noyé dans une hiérarchie visuelle trop fragmentée.
3. Le shell utilise plusieurs surfaces `bg-white/*` imbriquées, donnant un rendu plus utilitaire que premium.
4. Sur mobile, auteur + date repoussent le contenu utile vers le bas.
5. Le Live Preview actuel est correctement un overlay responsive. Cette décision doit être conservée.

## Référence cible

Mockup conceptuel validé dans le chantier Ordonnance:

- hiérarchie immédiate patient/contexte → sécurité → protocoles → saisie → lignes médicament ;
- moins de chrome ;
- glassmorphism sombre/neutral plus cohérent ;
- forte priorité visuelle à la prescription ;
- preview séparé, jamais en colonne compressant le contenu sur petit/moyen viewport.

## Décisions de design

### 1. StudioHeader compact uniquement sur Ordonnance

- Conserver patient, type de document, auteur clinique, date.
- Réduire padding, hauteur et espacement.
- Sur mobile, auteur et date passent en ligne compacte sous le titre sans grosses cartes verticales.
- Ne pas modifier Devis/Honoraires/Certificat/Libre dans ce lot.

### 2. Sécurité clinique compacte

- Conserver les états `unchecked/checking/verified/error` et les warnings.
- Réduire les wrappers, la hauteur et le texte secondaire.
- `Mes protocoles` et `Actualiser le contexte` deviennent actions secondaires compactes.
- Aucune suppression de preuve clinique ni de message d’erreur.

### 3. Saisie = héros

- La QuickEntry reste immédiatement visible.
- Les lignes médicament doivent suivre sans grands blocs décoratifs intermédiaires.
- Les protocoles système/utilisateur deviennent visuellement secondaires.

### 4. Glassmorphism cohérent

- Éviter l’empilement blanc-sur-blanc.
- Réutiliser les tokens existants `primary`, `card-bg`, `border-main`, `text-*` quand disponibles.
- Garder contraste AA sur textes et contrôles.
- Pas de nouvelle palette parallèle.

### 5. Responsive

- 390/430: une seule colonne, actions secondaires compactes, aucun élément > largeur viewport.
- 768: contenu respirant sans side panel permanent.
- 1280: largeur utile maximale pour saisie + cartes médicaments.
- Live Preview: overlay inchangé dans son principe.

## Première validation CI et corrections

Premier HEAD testé: `d60fbe147085e7ceb39707f4adf1ee10fddeaa3a`.

Résultats observés:

- T2 Runtime Browser Certification: `SUCCESS`.
- Cabinet Upgrade PostgreSQL Certification: `SUCCESS`.
- Patient P7 Final Certification: `SUCCESS`.
- Main CI frontend: 602 tests passés, 2 échecs contractuels ciblés.
- P3 Document Author Visual Certification: échec.

Causes prouvées:

1. le compactage avait raccourci le contrôle auteur à 36 px alors que le contrat tactile exige >=44 px ;
2. deux libellés contractuels historiques avaient été raccourcis (`Mes protocoles`, `Contexte patient` + texte associé), cassant R6/R7 sans gain fonctionnel nécessaire ;
3. le workflow P3 exigeait encore `selectorCount == 0` en BEFORE alors que le `master` courant possède déjà le sélecteur auteur.

Corrections appliquées avant nouvelle certification:

- auteur et date Ordonnance restaurés à `min-h-11` (44 px) ;
- actions secondaires sécurité également à `min-h-11` ;
- libellés/description/compteur contractuels restaurés, tout en gardant le layout compact et les styles dark/glass ;
- gate P3 réaligné pour vérifier la conservation du sélecteur actuel en BEFORE et AFTER, sa présélection, son minimum 44 px et l’absence d’overflow ;
- aucune modification backend, PDF, pharmacologique ou des endpoints.

## Correction overlap après inspection visuelle

La première certification verte ne suffisait pas: les captures T2 montraient encore que le `StudioHeader` sticky pouvait recouvrir le début de la zone Protocoles. Le défaut existait déjà en BEFORE, mais il violait explicitement le critère de succès de ce lot.

Correction finale:

- sur `ordonnance` uniquement, le `StudioHeader` repasse dans le flux normal (`relative z-20`) au lieu de `sticky top-0 z-[60]` ;
- les autres onglets conservent leur sticky ;
- un test UX verrouille ce contrat pour éviter le retour du chevauchement.

## AFTER certifié — lot A compactage

HEAD exact: `ff2dc2e548bc02e84379ff85f0bec4fb89f7117d`.

GitHub Actions exact-head:

- CI `#3755` / run `34773776962`: `SUCCESS` ;
- T2 Runtime Browser `#2694` / run `34773776790`: `SUCCESS` ;
- Clinic P3 Document Author Visual `#18` / run `34773776691`: `SUCCESS` ;
- Cabinet Upgrade PostgreSQL `#209` / run `34773776737`: `SUCCESS` ;
- Patient P7 Final `#1348` / run `34773776698`: `SUCCESS` ;
- Settings R11 `#541` / run `34773776733`: `SUCCESS` ;
- M6-I `#1494`: `SKIPPED` attendu.

Artefact visuel final:

- nom: `t2-browser-evidence` ;
- artefact: `10322349101` ;
- digest: `sha256:1e8978977fca480e40087f3631adeb0b637dac076e43459334bce02b62839b4a` ;
- HEAD artefact: `ff2dc2e548bc02e84379ff85f0bec4fb89f7117d` ;
- captures vérifiées: `390×844`, `430×932`, `768×1024`, `1280×900`.

Résultats observés sur l’artefact final:

- aucun chevauchement header/contenu visible aux quatre viewports ;
- aucun overflow horizontal sur Ordonnance ;
- la prescription et les actions finales remontent nettement dans le viewport mobile ;
- le header Ordonnance quitte naturellement l’écran au scroll au lieu de recouvrir la prescription ;
- le Live Preview reste modal/overlay et se ferme par Escape ;
- le stress de navigation T2 termine 10/10 transitions avec dirty guard observé ;
- T2 rapporte 6/6 pages vertes sans erreur runtime.

## Comparaison BEFORE → AFTER

### 390×844 / 430×932

BEFORE: StudioHeader auteur/date dominait la hauteur utile et le contenu de prescription était repoussé sous le fold ; sur les états capturés, un toast et la structure sticky pouvaient étouffer le bas de page.

AFTER: protocoles, ligne médicament, contrôle local, ajout de ligne et footer sont visibles beaucoup plus tôt ; le header ne recouvre plus la surface clinique et aucune compression latérale n’est observée.

### 768×1024

BEFORE: le header et les wrappers prenaient une part disproportionnée de la surface utile.

AFTER: protocoles + ligne médicament + actions finales coexistent dans le viewport avec une hiérarchie plus directe.

### 1280×900

BEFORE: collision visuelle entre header sticky et début des protocoles possible.

AFTER: protocoles, ligne médicament et actions s’alignent sans superposition ; la prescription récupère une surface verticale utile importante.

## Score visuel manuel — lot A

Ce score est un audit humain des captures exact-head, distinct du score automatisé T2 qui vaut 10/10 sur ses propres critères.

- Hiérarchie visuelle: **9.1/10**
- Responsive mobile: **9.3/10**
- Densité utile: **9.2/10**
- Cohérence visuelle Digital Crown / premium: **8.6/10**
- Sécurité clinique: **préservée, aucune régression observée dans les contrats/tests exact-head**

Conclusion: le **lot A compactage est certifié**, mais **Ordonnance Perfect V2 globale n’est pas clôturée**. La cible esthétique >=9/10 n’est pas encore atteinte sur la cohérence Crown/premium.

## Reste V2 connu

1. rendre les protocoles système fréquents accessibles comme quick chips sans supprimer les sélecteurs complets ;
2. renforcer la QuickEntry comme véritable héros visuel de la prescription ;
3. harmoniser les surfaces Ordonnance avec les tokens Crown existants sans empilement blanc-sur-blanc ;
4. refaire les captures BEFORE/AFTER 390/430/768/1280 et rescoring ;
5. ne considérer Perfect V2 clôturé qu’une fois la cohérence visuelle >=9/10 réellement observée.

## Hors périmètre

- Aucun changement backend.
- Aucun changement des règles pharmacologiques.
- Aucun changement des endpoints.
- Aucun changement de génération PDF.
- Aucun ajout LLM.
- Aucun déploiement Vercel.

## Validation obligatoire

BEFORE → implémentation → AFTER aux mêmes viewports:

- 390×844
- 430×932
- 768×1024
- 1280×900

Tests minimum:

- frontend ciblé Document Studio / Ordonnance ;
- build production ;
- browser smoke authentifié ;
- dirty state ;
- sécurité prescription ;
- protocoles ;
- preview overlay / Escape ;
- archive + impression.

## Score cible

- Hiérarchie: >= 9.0/10
- Responsive mobile: >= 9.0/10
- Densité utile: >= 9.0/10
- Cohérence visuelle Digital Crown: >= 9.0/10
- Sécurité clinique: ne doit pas descendre sous l’état actuel

## Critère de clôture

Le lot global n’est fermé qu’avec captures AFTER, comparaison BEFORE/AFTER, tests verts, absence de régression fonctionnelle observée et score visuel cible atteint.
