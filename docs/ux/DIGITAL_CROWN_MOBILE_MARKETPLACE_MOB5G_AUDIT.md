# Digital Crown — MOB-5G Marketplace / Approvisionnement — Audit verrouillé

Status: AUDIT LOCKED — BEFORE VISUAL PENDING

## Baseline exacte

- Repo : `hraaaaf/Digital_crown`
- baseline master : `062eadf1afc6ffc241be8420313e065a35f7d95b`
- MOB-5E merge : `b850cff2bd03dda667d6e1b6e449230658035d62`
- branche : `ux/mobile-marketplace-mob5g`
- aucun déploiement Vercel autorisé

## Goal du lot

Refondre Marketplace / Approvisionnement pour obtenir un parcours cabinet orienté **achat rapide de références connues**, utilisable sur desktop et mobile, sans dupliquer le moteur catalogue/commande existant.

Succès cible avant implémentation :
- BEFORE exact capturé en 390×844 / 430×932 / 768×1024 / 1280×800 ;
- Goal UI et référence verrouillés après inspection du BEFORE ;
- même catalogue, même panier scoped, même autorité serveur sur prix/fournisseur/commande ;
- mobile utile, pas simple réduction de la page desktop ;
- aucune promesse de fonction non exposée par le backend.

## Audit interne vérifié

### Desktop actuel

Surface : `frontend/src/pages/PartnerMarketplacePage.tsx`
Route utilisée par les preuves existantes : `/approvisionnement`.

Comportement actuel :
- charge `/partner-orders/meta` ;
- charge `/partner-catalog/meta` ;
- charge `/partner-catalog/suppliers` ;
- charge `/partner-catalog/products` ;
- recherche texte + catégories ;
- cartes produit ;
- quantité `- / +` ;
- panier ;
- checkout avec 5 champs obligatoires : nom, cabinet, téléphone, email, ville ;
- `POST /partner-orders` ;
- disclosure explicite : la commande créée reste `DRAFT` et n'est pas encore transmise au fournisseur.

Le desktop est fonctionnel, mais l'expérience est encore structurée comme un catalogue e-commerce responsive. Le formulaire contact répète des données déjà connues pour une partie du profil.

### Mobile actuel

`MobileBottomNav.tsx` expose actuellement dans `Plus` :
- Notifications
- Stock
- Bibliothèque
- Équipe
- Frontdesk
- Finance
- Envois Labo
- Sécurité

**Marketplace n'est pas présent.**

Donc le BEFORE mobile attendu est : cockpit mobile sans accès Marketplace dédié.

### Source de vérité Marketplace

`frontend/src/features/partnerMarketplace/data.ts` :
- cache catalogue `15 min` ;
- cache scoped par `employer_id` quand disponible ;
- panier local scoped `employer_id + user.id` ;
- normalisation unique des produits catalogue ;
- disponibilité : `Disponible / Sur commande / Discontinué`.

### Backend catalogue

`backend/routers/partner_catalog.py` :
- `GET /partner-catalog/meta`
- `GET /partner-catalog/suppliers`
- `GET /partner-catalog/suppliers/{id}`
- `GET /partner-catalog/products`
- `GET /partner-catalog/products/{id}`

Contrôles vérifiés :
- lecture sous `require_permission("patients")` ;
- scoping `current_user.get_employer_id()` ;
- fournisseurs inactifs masqués aux non-SuperAdmin ;
- produits tenant-scoped ;
- écriture catalogue réservée au SuperAdmin.

### Backend commande

`backend/routers/partner_orders.py` :
- `GET /partner-orders/meta` sous permission `patients` ;
- `POST /partner-orders` sous permission `patients` ;
- prix et lignes reconstruits depuis le catalogue serveur ;
- fournisseur inactif et produit discontinué refusés ;
- commande multi-fournisseurs splittée côté serveur en plusieurs DRAFT ;
- machine d'états existante ;
- historique `GET /partner-orders` réservé au SuperAdmin.

`backend/routers/partner_procurement.py` est également SuperAdmin-only.

**Conséquence verrouillée :** pas de `Mes commandes`, `Recommander`, statut livraison ou historique praticien en MOB-5G V1 sans nouveau contrat backend explicite. On ne fabrique pas une fonction parce qu'elle serait jolie dans le mockup.

### Préremplissage checkout possible sans nouvelle API

`AppUser` expose :
- `full_name` / `nom_complet`
- `cabinet_name`
- `email`

Ces 3 champs peuvent être préremplis côté frontend.

`CabinetConfig` possède aussi téléphone/adresse, mais `/clinics/me` exige `settings`. Marketplace utilise `patients`. La refonte ne doit donc pas créer une dépendance implicite à Settings.

Décision V1 :
- nom/cabinet/email préremplis quand disponibles ;
- téléphone et ville restent éditables/requis selon le contrat actuel ;
- aucun affaiblissement RBAC.

## Benchmark externe — 4 références primaires

### 1. Henry Schein Dental — Quick Order
Source officielle : `https://www.henryschein.com/us-en/shopping/quickorder.aspx`

Signal utile :
- saisie directe `Item Code + Qty` ;
- jusqu'à plusieurs références sans parcourir le catalogue ;
- outils adjacents : Order from History, Shopping Lists, Speed Entry.

Leçon Digital Crown : le chemin principal doit être **référence connue → quantité → panier**, le browsing venant en second.

### 2. Patterson Dental — Quick Order
Source officielle : `https://www.pattersondental.com/`

Signal utile observé sur leurs pages catalogue :
- `Quick Order` visible directement ;
- saisie item number ;
- scan barcode mentionné ;
- quantité + Add to Cart.

Leçon Digital Crown : SKU et recherche doivent être traités comme raccourci opérationnel, pas comme simple champ décoratif.

### 3. Medline — Shopping Lists / eCommerce capabilities
Sources officielles :
- `https://www.medline.com/help/shopping-lists/`
- `https://www.medline.com/business/ecommerce-capabilities/`

Signaux utiles :
- listes de produits fréquemment commandés ;
- quantité puis ajout à la commande ;
- formulaires/contrats, disponibilité et outils de compte ;
- logique B2B orientée répétition et efficacité.

Leçon Digital Crown : le futur naturel est le réachat/listes, mais MOB-5G V1 ne doit pas l'afficher tant que le contrat praticien d'historique n'existe pas.

### 4. McKesson SupplyManager — Quick Add / Lists
Sources officielles :
- `https://mms.mckesson.com/content/inventory-management/supplymanager/`
- `https://mms.mckesson.com/content/wp-content/uploads/2024/07/new-supplymanager-using-quick-add-1.pdf`

Signaux utiles :
- Quick Add directement depuis l'accueil ;
- item number + quantity ;
- listes/formularies ;
- statut de commande et gouvernance B2B séparés du simple ajout panier.

Leçon Digital Crown : séparer clairement **acheter vite** de **piloter les commandes**, et ne pas injecter la couche admin dans le cockpit praticien.

## Consensus benchmark

Pattern commun aux 4 références :
1. référence/SKU/barcode ou recherche immédiatement accessible ;
2. quantité rapide ;
3. panier toujours lisible ;
4. disponibilité claire ;
5. listes/réachat/historique comme accélérateur lorsqu'un contrat métier existe ;
6. browsing catalogue = chemin secondaire, pas seul point d'entrée.

## Décisions MOB-5G V1 verrouillées avant Goal UI

- desktop + mobile ;
- même backend, aucune seconde couche catalogue ;
- même `partnerMarketplace/data.ts` autant que possible ;
- mobile via `Plus → Marketplace` ou libellé final à verrouiller dans Goal UI ;
- recherche **nom/SKU first** ;
- catégories secondaires ;
- disponibilité visible ;
- quantité rapide ;
- panier persistant scoped ;
- checkout simplifié avec préremplissage réel ;
- disclosure `DRAFT` conservée ;
- aucun historique/reorder praticien inventé ;
- aucune configuration fournisseur/SuperAdmin portée dans le cockpit mobile ;
- aucune dépendance nouvelle à `/clinics/me` si l'utilisateur n'a pas `settings`.

## Gate suivant obligatoire

1. capture BEFORE exacte `062eadf1...` ;
2. inspection réelle 390/430/768/1280 ;
3. Goal UI écrit ;
4. mockup/référence textuelle verrouillée ;
5. seulement ensuite code produit.
