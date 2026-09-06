# Digital Crown — MOB-5G Marketplace / Approvisionnement — Goal UI

Status: GOAL UI LOCKED — IMPLEMENTATION NOT STARTED

## BEFORE vérifié

Baseline exacte : `062eadf1afc6ffc241be8420313e065a35f7d95b`

Run : `34045330209` — **SUCCESS**

Artifact :
- ID `9992935589`
- nom `mobile-marketplace-mob5g-before`
- taille `419568` octets
- digest `sha256:3e3701efc64a0eb3e3ed94be10b1a43bd5a0bd79cdf38e1c0917dda1220611db`

Viewports capturés :
- 390×844
- 430×932
- 768×1024
- 1280×800

Contrat BEFORE :
- HTTP 200 sur les 4 viewports ;
- 0 page error ;
- 0 console error ;
- 0 overflow horizontal ;
- recherche dans le premier viewport ;
- premier produit dans le premier viewport ;
- disclosure `DRAFT` présente ;
- checkout existant : 1 POST, même URL, succès DRAFT.

## Lecture visuelle BEFORE

### 390 / 430

Points solides :
- identité Digital Crown cohérente ;
- recherche accessible rapidement ;
- prix, disponibilité et quantité lisibles ;
- cartes tactiles suffisamment grandes ;
- aucune casse responsive mesurée.

Frottements :
- ce n'est pas le cockpit mobile canonique : la page utilise le shell desktop responsive avec barre supérieure, pas `Aujourd’hui / Patients / + / Assistant / Plus` ;
- hero `Acheter pour le cabinet` consomme beaucoup de hauteur avant le catalogue ;
- catégories horizontales partiellement hors champ ;
- seulement environ deux cartes complètes visibles immédiatement à 390 px ;
- le parcours ressemble encore à du browsing e-commerce, pas à une saisie d'approvisionnement rapide.

### 768

- mise en page propre mais encore issue de la page desktop ;
- description et métadonnées fournisseur reprennent de la place avant l'action ;
- absence de surface mobile dédiée malgré le viewport tablette/PWA.

### 1280

Points solides :
- sidebar Digital Crown cohérente ;
- catalogue + panier côte à côte ;
- recherche et filtres clairement visibles ;
- panier sticky pertinent.

Frottements :
- grand hero éditorial avant l'achat ;
- checkout complet affiché en permanence dans le panneau panier ;
- nom/cabinet/email redemandés alors qu'ils sont déjà disponibles dans `AppUser` ;
- pas de raccourci Quick Order/SKU explicitement dominant comme chez les références benchmarkées.

## Goal exact

Permettre à un praticien de **trouver une référence connue, ajuster sa quantité et atteindre un checkout prérempli en idéalement moins de 30 secondes**, sur mobile ou desktop, sans quitter Digital Crown et sans dupliquer le moteur Marketplace.

## Succès observable

### Mobile

- `Plus → Marketplace` pour DENTISTE / ADMIN ;
- deep-link `?tab=marketplace` ;
- nav canonique reste exactement 5 boutons / 76 px ;
- recherche nom/SKU visible dans le premier viewport ;
- disponibilité, SKU, prix, unité et quantité lisibles sur chaque référence ;
- `- / +` tactile ;
- panier persistant visible via CTA compact au-dessus de la bottom nav dès qu'il contient un article ;
- checkout dans une surface dédiée/bottom sheet, pas un long formulaire permanent ;
- nom/cabinet/email préremplis depuis `AppUser` quand disponibles ;
- téléphone/ville restent éditables et requis conformément au contrat existant ;
- disclosure claire : création d'un `DRAFT`, pas transmission fournisseur ;
- pas de fiche fournisseur ni fiche produit lourde dans le cockpit mobile ;
- pas d'historique/reorder inventé.

### Desktop

Route conservée : `/approvisionnement`.

- header nettement plus compact ;
- Quick Search / SKU devient l'action dominante ;
- catégories restent secondaires ;
- catalogue et panier restent côte à côte à 1280 ;
- formulaire client n'occupe plus le panneau panier en permanence ;
- le checkout s'ouvre seulement quand l'utilisateur veut finaliser le DRAFT ;
- préremplissage nom/cabinet/email identique au mobile ;
- administration fournisseur reste hors de la surface praticien.

### Technique

- même backend `/partner-catalog/*` + `/partner-orders/*` ;
- même autorité serveur sur prix, produits, fournisseurs et split multi-fournisseurs ;
- cache catalogue tenant-scoped conservé ;
- panier user-scoped conservé ;
- extraction d'un hook/shared controller frontend pour éviter de recopier load/cache/cart/submit entre desktop et mobile ;
- aucun nouvel endpoint requis pour V1 ;
- aucun appel `/clinics/me` ajouté au parcours Marketplace ;
- aucune logique historique/reorder ajoutée ;
- aucune écriture Supabase directe ;
- aucun déploiement Vercel.

## Référence benchmark retenue

Principe commun Henry Schein / Patterson / Medline / McKesson :

**référence connue / SKU → quantité → panier**, puis browsing/listes en accélérateurs secondaires.

Digital Crown doit reprendre ce principe sans copier leur esthétique ni leurs fonctions non disponibles.

## Mockup mobile verrouillé

```text
┌─────────────────────────────────────┐
│ MARKETPLACE                    🛒 0 │
│ Acheter vite pour le cabinet        │
│                                     │
│ 🔎 Nom, référence ou SKU…           │
│ [Tous] [Dispo] [Consommables] →     │
│                                     │
│ Composite universel                 │
│ CMP-NH-01 · Restauration     ● dispo│
│ 390 MAD / seringue       [−] 0 [+] │
│ ─────────────────────────────────── │
│ Limes rotatives NiTi                │
│ ENDO-NITI · Endodontie       ● dispo│
│ 295 MAD / blister        [−] 0 [+] │
│ ─────────────────────────────────── │
│ Gants nitrile premium               │
│ NIT-PRO-M · Consommables     ● dispo│
│ 78 MAD / boîte           [−] 0 [+] │
│                                     │
│   [ Panier · 3 unités · 763 MAD ]   │  ← seulement si panier non vide
│                                     │
│ Aujourd’hui Patients   + Assistant Plus │
└─────────────────────────────────────┘
```

### Checkout mobile

```text
┌─────────────────────────────────────┐
│ Panier                         Fermer│
│ 3 unités · 763 MAD                  │
│                                     │
│ Composite          1 × 390 MAD      │
│ Limes              1 × 295 MAD      │
│ Gants               1 × 78 MAD      │
│                                     │
│ Commander pour                      │
│ Dr Baseline · Cabinet Atlas         │  ← prérempli
│ baseline@digitalcrown.local         │  ← prérempli
│ Téléphone [....................]     │
│ Ville      [....................]    │
│ Note       [....................]    │
│                                     │
│ [ Enregistrer le brouillon ]        │
│ Crée un DRAFT Digital Crown.        │
│ Rien n'est transmis au fournisseur. │
└─────────────────────────────────────┘
```

## Mockup desktop verrouillé — 1280

```text
┌──────── sidebar ────────┬──────────────────────────────────────────────────────────────┐
│ Digital Crown           │ Approvisionnement                              🛒 3 · 763 MAD│
│                         │ 🔎 Rechercher nom ou SKU…   [Saisie rapide SKU]              │
│ Marketplace             │ [Tous] [Dispo] [Consommables] [Restauration] [Endodontie]   │
│                         │                                                              │
│                         │ PRODUITS                         │ PANIER                      │
│                         │ Composite… 390 MAD [−]0[+]       │ Composite 1 × 390          │
│                         │ Limes…     295 MAD [−]0[+]       │ Limes     1 × 295          │
│                         │ Gants…      78 MAD [−]0[+]       │ Gants      1 × 78          │
│                         │                                 │ ─────────────────          │
│                         │                                 │ Total 763 MAD              │
│                         │                                 │ [Préparer le DRAFT]        │
└─────────────────────────┴─────────────────────────────────┴─────────────────────────────┘
```

Le checkout desktop s'ouvre ensuite dans une surface compacte avec les données préremplies, au lieu d'afficher cinq champs en permanence.

## Non-objectifs V1

- historique de commandes praticien ;
- bouton Recommander ;
- listes d'achat persistées serveur ;
- scan barcode caméra ;
- statut livraison praticien ;
- automatisation de réassort ;
- configuration fournisseur ;
- import/API fournisseur ;
- refonte des pages éditoriales fournisseur/produit ;
- paiement en ligne.

## AFTER obligatoire

Même preuve que BEFORE :
- mobile : 390×844 / 430×932 / 768×1024 ;
- desktop : 1280×800 ;
- 0 overflow horizontal ;
- 0 console/page runtime error ;
- recherche visible dans le premier viewport ;
- interaction quantité ;
- panier ;
- checkout prérempli ;
- exactement 1 POST DRAFT dans la preuve checkout ;
- comparaison visuelle BEFORE/AFTER + score.
