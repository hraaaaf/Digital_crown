# Digital Crown — Mobile Quick Action Hub — Goal UI

Status: DRAFT — awaiting visual validation
Lot: MOB-3
Branch: `ux/mobile-quick-action-hub-mob3`
Baseline master: `508a2e1e174887fe44f271cc6a8283eb89e443c7`

## Goal

Permettre à un praticien de déclencher une action mobile fréquente en **2 gestes maximum** depuis le cockpit, sans chercher une page ni transformer la navigation globale avant MOB-4.

## Succès observable

Depuis le dashboard mobile :

1. le praticien ouvre un hub d’actions rapides en un geste ;
2. il choisit l’action en un second geste ;
3. les actions non autorisées sont absentes ou désactivées fail-closed ;
4. le hub est utilisable à une main sur 390×844 ;
5. aucune fonction desktop lourde n’est introduite ;
6. la bottom nav actuelle reste structurellement inchangée dans MOB-3 ;
7. thème, couleurs, surfaces et police viennent exclusivement des Réglages cabinet ;
8. fermeture intuitive par croix, backdrop ou retour ;
9. aucun overflow horizontal sur 390 / 430 / 768.

## Actions cibles verrouillées

### 1. Nouveau RDV

Réutiliser le flow mobile agenda existant. Ne pas créer un second formulaire de rendez-vous.

### 2. Nouveau patient

Réutiliser le flow de création patient déjà présent dans le mobile. Ne pas créer un dossier desktop miniature.

### 3. Photo clinique

Ouvrir le contexte patient sécurisé existant. Si aucun patient n’est sélectionné, demander d’abord le patient dans une étape compacte.

### 4. Scanner document

Même logique que Photo clinique : contexte patient obligatoire, puis scanner mobile existant.

### 5. Encaisser

Uniquement si la permission financière canonique l’autorise. Flow rapide seulement : sélectionner patient → saisir montant/moyen si nécessaire → confirmation explicite. Aucune Treasury UI.

## Décision UX

MOB-3 ne remplace pas encore la navigation principale.

Le déclencheur cible est un **bouton d’action flottant circulaire** centré juste au-dessus de la bottom nav actuelle. Il utilise la couleur `primary` du cabinet et un symbole `+`.

Raison :

- action disponible depuis tous les onglets ;
- aucune sixième entrée permanente dans la nav ;
- prépare naturellement MOB-4 où le `+` pourra devenir l’action centrale canonique ;
- changement réversible et limité au lot.

## Comportement du hub

Après tap sur `+` :

- backdrop léger ;
- bottom sheet compacte ancrée au-dessus de la safe area ;
- rayon 28–32 px ;
- surface `var(--glass-bg)` + `var(--glass-border)` ;
- ombre premium déjà utilisée par `SecuriteView` ;
- poignée visuelle discrète ;
- titre : `Action rapide` ;
- sous-titre : `Que voulez-vous faire ?` ;
- grille 2 colonnes sur 390/430 ;
- 5e action pleine largeur ou centrée sur la dernière ligne ;
- cibles tactiles ≥ 52 px ;
- labels courts ;
- icônes Lucide ;
- aucune couleur métier décorative figée : primary pour interaction, couleurs sémantiques seulement si réellement nécessaires.

## Hiérarchie cible

Ordre :

1. Nouveau RDV
2. Nouveau patient
3. Photo clinique
4. Scanner document
5. Encaisser

`Encaisser` peut disparaître selon permission, sans trou visuel gênant.

## Invariants visuels Digital Crown

- fond mobile : `var(--bg-medical-pearl)` ;
- surfaces : `var(--glass-bg)` / `var(--glass-border)` ;
- CTA principal : `var(--primary)` ;
- texte principal : tokens existants ;
- typographie : `var(--app-font-family)` ;
- coins : 16–32 px ;
- ombres douces multicouches ;
- reflets blancs internes très subtils ;
- aucun dark/neon redesign ;
- aucun style iOS générique plaqué par-dessus la PWA existante.

## Ce qui est explicitement hors scope MOB-3

- refonte de la bottom nav ;
- `Aujourd’hui / Patients / + / Assistant / Plus` : MOB-4 ;
- devis ;
- notes cliniques ;
- odontogramme ;
- Master Plan ;
- RVG ;
- comparaison pano T0/T1 ;
- annotations ;
- rapport panoramique ;
- comptabilité complète ;
- paramètres cabinet ;
- Marketplace admin.

## BEFORE

Workflow : `.github/workflows/mobile-quick-action-hub-before.yml`
Run attendu : capture dashboard réel du harness mobile actuel en 390×844 / 430×932 / 768×1024.

Le BEFORE doit être archivé avant toute modification UI de MOB-3.

## Gate avant code produit

1. BEFORE réel disponible ;
2. ce Goal UI versionné ;
3. mockup 390 px fidèle à la shell actuelle ;
4. validation visuelle humaine explicite.

Aucun code produit MOB-3 avant ces quatre preuves.
