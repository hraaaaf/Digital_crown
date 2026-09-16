# Céphalo-N — Semantic Color Mockup Contract

## Goal

Unifier la lecture visuelle Céphalo sans créer de design system parallèle :

- les **surfaces, textes, bordures, ombres, focus UI et états interactifs** restent pilotés par les tokens Digital Crown existants ;
- la couche Céphalo ajoute uniquement des **tokens sémantiques scientifiques** stables pour la nature des géométries/mesures ;
- le **statut clinique** reste distinct de la nature de la mesure ;
- tableau, SVG, légende et futur PDF utilisent le même contrat.

### Success

Un même élément scientifique conserve la même famille visuelle dans le tableau et sur le tracé, sur tous les thèmes supportés, sans que la couleur soit l’unique vecteur d’information.

### Proof attendue

BEFORE → contrat mockup → implémentation → AFTER aux mêmes viewports `390x844`, `768x1024`, `1280x900` → comparaison visuelle + tests fonctionnels + absence d’overflow/console errors.

---

## BEFORE verrouillé

Référence produit actuelle : **R19 Analysis Reference Workbench**.

- Produit certifié : `493dd290eec8bd004ec928ebd100707b56099b7c`
- Run : `Cephalo R19 Analysis Reference AFTER #7` / `34903739212`
- Artifact : `10371414961`
- Digest : `sha256:8a4c0c2b286d9754b2ec2f1b8c03151f9d6e9bbaf836a8218928e43925b576c3`
- États : `18/18` valides
- Viewports : `390x844`, `768x1024`, `1280x900`
- `invalidCount=0`
- `blockedExternalRequests=[]`
- zéro erreur page/console
- zéro overflow horizontal

Validité du BEFORE pour le présent lot :

- `frontend/src/features/ortho/components/Step1Cephalo.tsx` : dernière modification produit R19 ;
- `frontend/src/features/ortho/components/CephaloAnalysisWorkbenchPanel.tsx` : dernière modification produit R19 ;
- `frontend/src/features/ortho/CephaloTracingLayer.tsx` : dernière modification produit R19 ;
- `frontend/src/index.css` : aucune modification depuis avant R19 ;
- `frontend/src/features/ortho/cephaloTheme.ts` : tokens Digital Crown actifs déjà consommés par Céphalo.

Le BEFORE ne doit donc pas être recréé avec une autre fixture tant que ces sources restent inchangées.

---

## Règle de design

**Digital Crown = interface. Céphalo = information scientifique.**

### Tokens UI obligatoires

Le mockup et l’implémentation doivent réutiliser :

- `P.bg`
- `P.bgPanel`
- `P.bgCard`
- `P.bgInput`
- `P.border`
- `P.borderFocus`
- `P.text`
- `P.textMuted`
- `P.textDim`
- `P.accent`
- `P.accentSuccess`
- `P.accentWarning`
- `P.accentError`
- `P.shadow`
- `P.shadowLg`

Aucun hex Céphalo ne doit servir à fabriquer une surface, une carte, un bouton, une bordure UI ou un texte UI générique.

---

## Code couleur Céphalo général

Le code couleur exprime une **famille scientifique**, jamais une analyse historique entière.

| Rôle sémantique | Couleur de référence | Usage |
| --- | --- | --- |
| `skeletal` | bleu | structures / mesures squelettiques |
| `dental` | violet | structures / mesures dentaires |
| `soft_tissue` | vert | tissus mous / esthétique |
| `reference` | orange / ambre | plans, axes et constructions de référence |
| `auxiliary` | neutre | repères secondaires / géométrie auxiliaire |

Le système doit conserver ces **hues** sur tous les thèmes, avec adaptation de luminosité/contraste si nécessaire. Il ne doit pas transformer `skeletal` en rose dans le thème Rose ni en vert dans le thème Emerald.

### Statut clinique — couche indépendante

| Statut | Token |
| --- | --- |
| normal / validé | `P.accentSuccess` |
| limite / compensation / vigilance | `P.accentWarning` |
| hors norme / erreur clinique explicite | `P.accentError` |
| non calculable / manquant | `P.textDim` |

La couleur de statut ne remplace jamais la couleur de famille scientifique.

Exemple : `IMPA` reste **dentaire/violet** ; son badge peut être rouge si le backend fournit un statut hors norme.

---

## Mockup de référence

### Desktop large

Conserver le layout R19 : tracé à gauche, tableau d’analyse à droite.

Chaque ligne du tableau contient :

1. marqueur de **famille scientifique** ;
2. libellé ;
3. valeur patient ;
4. norme ;
5. écart ;
6. badge/statut distinct lorsque disponible.

La sélection d’une ligne utilise le **focus UI Digital Crown** (`P.accent` + surface dérivée de `P.bgCard`/`P.bgPanel`) ; elle ne recolore pas toute la ligne avec la couleur clinique.

### SVG

- un plan de référence garde la famille `reference` ;
- une géométrie dentaire garde `dental` ;
- une géométrie squelettique garde `skeletal` ;
- les tissus mous gardent `soft_tissue` ;
- les primitives auxiliaires restent `auxiliary`.

Lors d’un hover/focus :

- conserver la couleur de famille ;
- augmenter épaisseur/opacité ;
- atténuer les primitives non concernées ;
- utiliser `P.accent` uniquement pour le contour/focus UI si nécessaire.

Aucun passage en jaune ne doit effacer l’identité de famille de la géométrie sélectionnée.

### Mobile / tablette

Conserver le comportement responsive R19 : tableau empilé sous le tracé, sans changement de hiérarchie ni overflow horizontal.

---

## Accessibilité / thèmes

- La couleur n’est jamais l’unique signal : texte, badge, icône, épaisseur ou motif complètent l’information.
- Les thèmes `default`, `emerald`, `rose`, `prestige`, `ocean`, `graphite`, `dark`, `high-contrast` doivent conserver leurs propres surfaces et textes.
- En `high-contrast`, la lisibilité prime : motifs/épaisseurs/labels doivent permettre de distinguer les familles même si les couleurs deviennent secondaires.

---

## Dette actuelle explicitement ciblée

1. `CephaloAnalysisWorkbenchPanel.tsx` colore aujourd’hui le marqueur de ligne selon le **statut** (`tone(metric)`), pas selon la famille scientifique.
2. `CephaloTracingLayer.tsx` contient plusieurs hex de construction (`#38bdf8`, `#34d399`, `#f472b6`, `#2dd4bf`, `#c084fc`, `#fb7185`, `#facc15`, `#fb923c`, `#60a5fa`) sans contrat sémantique central.
3. Le sélecteur du tracé utilise encore des classes slate/cyan codées en dur au lieu des tokens Digital Crown.
4. Les couleurs Ricketts/COM sont actuellement liées à des constructions ponctuelles plutôt qu’à un vocabulaire scientifique global.

---

## Hors scope de ce mockup

- aucune nouvelle mesure ;
- aucune nouvelle norme ;
- aucune modification backend scientifique ;
- aucun alias sémantique de mesure ;
- aucune migration DB ;
- aucun changement PDF avant validation du rendu écran ;
- aucun déploiement Vercel.

---

## Gate d’implémentation

L’implémentation peut commencer uniquement si :

1. le BEFORE ci-dessus reste valide ;
2. aucune divergence Céphalo UI nouvelle n’est apparue sur `master` ;
3. les tokens UI restent ceux de Digital Crown ;
4. la palette sémantique est centralisée dans **un seul contrat Céphalo**, sans duplication dans le tableau et le SVG.
