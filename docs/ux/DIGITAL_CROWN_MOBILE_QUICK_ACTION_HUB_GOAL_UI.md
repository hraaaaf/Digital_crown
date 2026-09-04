# Digital Crown — Mobile Quick Action Hub — Goal UI

Status: AWAITING VISUAL VALIDATION
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
9. aucun overflow horizontal sur 390 / 430 / 768 ;
10. le mockup de référence conserve **le vrai écran Digital Crown**, sans reconstruction graphique du dashboard.

## Actions cibles verrouillées

### 1. Nouveau RDV
Réutiliser `AddApptModal` et le flow Agenda existant.

### 2. Nouveau patient
Réutiliser le flow de création patient déjà présent dans le mobile.

### 3. Photo clinique
Ouvrir le contexte patient sécurisé existant. Si aucun patient n’est sélectionné, demander d’abord le patient dans une étape compacte.

### 4. Scanner document
Même logique que Photo clinique : contexte patient obligatoire, puis scanner mobile existant.

### 5. Encaisser
Uniquement si la permission financière canonique l’autorise. Réutiliser `POST /api/accounting/payments` : sélection patient → montant → moyen de paiement → confirmation explicite. Aucun second moteur financier.

## Décision UX corrigée après inspection du BEFORE réel

Le BEFORE `390×844` prouve qu’un **FAB `+` existe déjà** dans l’Agenda, positionné `bottom-32 right-6`, taille `56×56`, couleur `primary`, et qu’il ouvre actuellement `AddApptModal`.

MOB-3 ne doit donc **pas ajouter un second bouton `+`**.

Cible :

- conserver exactement la géométrie et le style du FAB existant ;
- promouvoir ce FAB du scope `AgendaView` vers la shell mobile afin qu’il soit disponible sur les surfaces autorisées ;
- tap fermé → ouvre Quick Action Hub ;
- tap ouvert → le même bouton devient `×` et ferme le hub ;
- `Nouveau RDV` dans le hub réutilise l’action aujourd’hui portée directement par ce FAB ;
- la bottom nav reste inchangée jusqu’à MOB-4.

Cette décision est plus fidèle à l’application et évite deux contrôles concurrents.

## Comportement du hub

Après tap sur le FAB existant :

- le screenshot/app réel reste visible derrière un backdrop léger ;
- bottom sheet Digital Crown, sans reconstruction du header/dashboard/nav ;
- surface `var(--glass-bg)` + `var(--glass-border)` ;
- rayon ≈ 28–30 px ;
- titre `Action rapide` ;
- sous-titre `Que voulez-vous faire ?` ;
- grille 2 colonnes : RDV / patient / photo / scan ;
- `Encaisser rapidement` pleine largeur si permission ;
- cibles tactiles ≥ 52 px ;
- le FAB existant garde sa position et devient `×` en état ouvert ;
- fermeture aussi possible par backdrop / retour ;
- couleurs et police exclusivement issues du thème cabinet.

## Hiérarchie cible

1. Nouveau RDV
2. Nouveau patient
3. Photo clinique
4. Scanner document
5. Encaisser rapidement

`Encaisser` peut disparaître selon permission, sans trou visuel gênant.

## Invariants visuels Digital Crown

- **fond = vrai dashboard courant**, pas une illustration ;
- vrai logo, vrai header, vraie date, vrai `Bonsoir`, vrais badges, vraie card Preview, vrais tabs Jour/Semaine/Mois, vraie progression, vraie timeline, vraie bottom nav ;
- FAB = même emplacement / dimension / couleur que l’existant ;
- surfaces : tokens existants ;
- typographie : `var(--app-font-family)` ;
- aucune palette/police locale figée ;
- aucun redesign iOS générique ;
- aucun changement de navigation canonique avant MOB-4.

## Hors scope MOB-3

- refonte bottom nav ;
- `Aujourd’hui / Patients / + / Assistant / Plus` : MOB-4 ;
- devis, notes, odontogramme, Master Plan, RVG ;
- pano T0/T1, annotations, rapport panoramique ;
- comptabilité complète / Treasury ;
- paramètres cabinet ;
- Marketplace admin.

## BEFORE — VERIFIED

Run `33906860335` ✅

- HEAD : `040beb21872e63167d149735b24cc6f48554bb8f`
- artifact : `9949854305`
- digest : `sha256:b24cf6ecf919a97be154cfeb45275b54cc3bd2f2f4273fb1ee0f3fa2dee10748`
- viewports : `390×844`, `430×932`, `768×1024`
- mode : harness déterministe, aucune donnée cabinet

Le screenshot 390×844 du BEFORE est la **base graphique obligatoire** du Goal UI corrigé.

## Mockups

- v1 : REJECTED — dashboard/nav trop reconstruits ;
- v2 : REJECTED après feedback humain — nav mieux alignée, mais dashboard encore schématique ;
- v3 : **REAL-APP COMPOSITE — AWAITING VISUAL VALIDATION**.

V3 est construite directement sur `before-390x844.png` de l’artifact `9949854305`. Seuls sont ajoutés : backdrop, bottom sheet, actions et transformation du FAB existant `+` → `×`.

Aucun autre élément du screenshot réel n’est redessiné ou remplacé.

## Gate avant code produit

1. BEFORE réel ✅ ;
2. Goal UI corrigé ✅ ;
3. mockup v3 basé pixel pour pixel sur le BEFORE réel ✅ ;
4. validation visuelle humaine explicite ⏳.

Aucun code produit MOB-3 avant le quatrième gate.
