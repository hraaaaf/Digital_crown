# Digital Crown — MOB-5D Stock — Audit

Status: AUDIT LOCKED / BEFORE UI
Date: 2026-09-06
Repo: `hraaaaf/Digital_crown`
Branch: `ux/mobile-stock-mob5d`
Baseline: `aaa28ef97b22df2c5654c4e0da7efc15692787a8`

## Goal
Activer une expérience Stock cohérente desktop + mobile à partir du même backend et de la même table métier, sans créer une seconde logique de stock.

## Constat vérifié

### Backend existant
`backend/routers/stock.py` expose déjà :
- `GET /stock/items` ;
- `GET /stock/alerts` ;
- `POST /stock/items` ;
- `PATCH /stock/items/{id}` ;
- `DELETE /stock/items/{id}`.

Toutes les lectures/mutations dérivent le cabinet via `current_user.get_employer_id()` et filtrent `StockItem.employer_id`.

La permission actuelle est `patients` via `require_permission("patients")`.

Le signal métier d'alerte est unique : `quantite <= seuil_alerte`.

### Objet métier existant
Le contrat sérialisé contient : `id`, `nom`, `categorie`, `quantite`, `seuil_alerte`, `unite`, `prix_unitaire`, `fournisseur`, `notes`, `alerte`, `created_at`, `updated_at`.

Catégories observées côté UI existante : `CONSOMMABLE`, `MATERIAU`, `MEDICAMENT`, `EQUIPEMENT`.

### Desktop existant mais dormant
`frontend/src/pages/StockPage.tsx` existe déjà et consomme directement les endpoints ci-dessus. Il sait :
- lister/rechercher/filtrer ;
- afficher les alertes ;
- créer/modifier/supprimer ;
- ajuster la quantité ;
- afficher fournisseur/prix/notes.

Cependant `frontend/src/App.tsx` route actuellement `/stock` vers `ComingSoon`, malgré l'import de `StockPage`.

Décision MOB-5D : activer la page desktop existante seulement si les tests/build restent verts ; ne pas créer de deuxième page desktop.

### Mobile BEFORE
Le shell canonique est `Aujourd’hui / Patients / + / Assistant / Plus`.
`Plus` contient Notifications, Équipe, Frontdesk, Finance, Labo, Sécurité selon le rôle. Il n'existe aucune entrée Stock, aucun `Tab` stock et aucune route bridge `stock` sur la baseline.

Le BEFORE visuel doit être capturé depuis la baseline exacte `aaa28ef9…`, menu `Plus` ouvert, aux mêmes viewports que l'AFTER.

## Contrat produit MOB-5D
Mobile reste un cockpit, pas un clone de la table desktop.

V1 mobile :
- `Plus → Stock` ;
- deep-link `?tab=stock` ;
- synthèse `Rupture / Alerte / OK` dérivée uniquement de `quantite` et du signal serveur `alerte` ;
- recherche et filtre `Tous / À traiter` ;
- mouvement court `−1 / +1`, borné à zéro côté client ;
- ajout rapide : nom, catégorie, quantité, seuil, unité ;
- refresh et erreurs inline ;
- aucune suppression mobile ;
- aucun prix/fournisseur/notes à éditer sur mobile ;
- aucune logique parallèle de réassort ou d'historique inventée.

## Sécurité / données
- même `/stock/*` que desktop ;
- même DB/table `StockItem` ;
- isolation cabinet conservée côté backend ;
- aucune donnée cabinet dans la preview/certification ;
- mutations de preview interdites ;
- pas de migration DB dans ce lot.

## Preuve requise
BEFORE baseline exacte → Goal UI → mockup/référence → implémentation → AFTER 390×844 / 430×932 / 768×1024 → tests tenant/RBAC/routing/UI → build → runtime → comparaison → score visuel.

Deployment: none. No Vercel deployment authorized.