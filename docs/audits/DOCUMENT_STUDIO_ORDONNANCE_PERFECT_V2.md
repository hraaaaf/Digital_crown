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

Le lot n’est fermé qu’avec captures AFTER, comparaison BEFORE/AFTER, tests verts et absence de régression fonctionnelle observée.
