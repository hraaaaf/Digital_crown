# DIGITAL CROWN MOBILE — MOB-5H SUPERADMIN AUDIT

Status: AUDIT LOCKED — IMPLEMENTATION NOT STARTED
Baseline exact: `6eb93c75f91402031ecc2c8fc1f8858372a97b9b`
Branch: `ux/mobile-superadmin-mob5h`

## Goal

Rendre sur mobile **100 % des prérogatives SuperAdmin déjà existantes dans Digital Crown**, sans affaiblir le RBAC, les validations serveur, l'idempotence, les transitions métier ni les confirmations sensibles.

## Success

- aucune prérogative SuperAdmin existante n'est supprimée ou rendue inaccessible sur mobile ;
- les mutations réutilisent les endpoints canoniques existants ;
- aucune logique métier/RBAC dupliquée côté mobile ;
- actions destructives, financières ou externes protégées par confirmation explicite ;
- rôle SuperAdmin fail-closed ;
- tests dédiés mobile + build + tests backend existants + certification visuelle/runtime ;
- BEFORE et AFTER comparés sur les mêmes viewports.

## Proof attendue

- matrice endpoint/action/mobile couverte par tests ;
- test dédié `MobileSuperAdminView.test.tsx` ;
- build production ;
- tests backend Marketplace/SuperAdmin pertinents ;
- captures 390×844, 430×932, 768×1024 ;
- 0 overflow / 0 runtime error ;
- aucune requête de preview vers une API réelle ;
- aucune modification des guards backend nécessaire pour obtenir la parité.

---

## 1. État actuel mobile

Source : `frontend/src/features/mobile/Dashboard/views/MobileSuperAdminView.tsx`.

Le mobile actuel sait :

| Domaine | Action | Endpoint | Mobile actuel |
|---|---|---|---|
| Clients | Liste/recherche | `GET /api/superadmin/clients` | ✅ |
| Licence | Changer pack | `PATCH /api/superadmin/clients/{id}/plan` | ✅ |
| Licence | +1m/+3m/+6m/+1y | `POST /api/superadmin/clients/{id}/grant-license` | ✅ |
| Compte | Suspendre/réactiver | `PATCH /api/superadmin/clients/{id}/suspend` | ✅ |

Le composant réutilise le JWT mobile device-bound via `mobileFetch`.

**Trou de couverture vérifié :** aucun fichier `MobileSuperAdminView.test.tsx` n'existe sur le baseline.

---

## 2. Prérogatives core SuperAdmin vérifiées

Source : `backend/routers/superadmin.py` ; toutes protégées par `verify_superadmin`.

| Domaine | Prérogative | Endpoint | Mobile actuel | MOB-5H |
|---|---|---|---|---|
| Clients | Lister/statistiques | `GET /clients` | ✅ | conserver |
| Clients | Valider/activer + essai 30j | `POST /clients/{id}/validate` | ❌ | ajouter |
| Codes d'essai | Lister | `GET /trial-codes` | ❌ | ajouter |
| Codes d'essai | Créer | `POST /trial-codes` | ❌ | ajouter |
| Codes d'essai | Révoquer | `POST /trial-codes/{id}/revoke` | ❌ | ajouter |
| Licence | Prolonger 1m/3m/6m/1y | `POST /clients/{id}/grant-license` | ✅ | conserver |
| Licence | Révoquer | même endpoint, `action=revoke` | ❌ | ajouter |
| Compte | Archiver/désarchiver | `PATCH /clients/{id}/archive` | ❌ | ajouter |
| Compte | Suspendre/réactiver | `PATCH /clients/{id}/suspend` | ✅ | conserver |
| Abonnement | Changer GOLD/PREMIUM/ELITE | `PATCH /clients/{id}/plan` | ✅ | conserver |
| CRM interne | Notes internes | `PATCH /clients/{id}/notes` | ❌ | ajouter |
| Audit licence | Historique | `GET /clients/{id}/license-history` | ❌ | ajouter |
| Relance | Email renouvellement | `POST /clients/{id}/send-renewal-email` | ❌ | ajouter |

Les effets serveur existants restent autoritaires : invalidation cache licence, historique, écriture licence et tâches email lorsque prévues par le backend.

---

## 3. Prérogatives Marketplace SuperAdmin vérifiées

### 3.1 Vue globale / gouvernance

Sources : `backend/routers/partner_superadmin.py`, `partner_superadmin_catalog.py`.

| Domaine | Prérogative | Endpoint/surface | Mobile actuel | MOB-5H |
|---|---|---|---|---|
| KPI global | Vue Marketplace multi-cabinets | `/superadmin/partner-marketplace/overview` | ❌ | ajouter |
| Commandes | Liste globale + filtres | `/superadmin/partner-marketplace/orders` / routes canoniques | ❌ | ajouter |
| Sync | Incidents fournisseur | `/superadmin/partner-marketplace/supplier-sync/incidents` | ❌ | ajouter |
| Fournisseurs | Liste globale | `/superadmin/partner-marketplace/suppliers` | ❌ | ajouter |
| Audit | Journal Marketplace | `/superadmin/partner-marketplace/audit` | ❌ | ajouter |
| Fournisseurs | Activer/désactiver | `PATCH .../suppliers/{id}/active` | ❌ | ajouter |
| Fournisseurs | Créer/modifier | `POST/PATCH .../admin/suppliers` | ❌ | ajouter |
| Produits | Créer/modifier | `POST/PATCH .../admin/products` | ❌ | ajouter |

Les mutations catalog/gouvernance conservent les confirmations explicites exigées par le backend.

### 3.2 Commandes / dispatch

Sources : `backend/routers/partner_orders.py`, `partner_dispatch.py`.

Prérogatives vérifiées :
- consultation/gestion SuperAdmin des commandes partenaires et transitions autorisées ;
- modification du statut/montant/référence/note selon le moteur canonique ;
- `GET /{order_id}/dispatch` ;
- `POST /{order_id}/dispatch` : envoi fournisseur HTTPS avec garde SSRF, hash payload, idempotence et preuve de transport ;
- dispatch réservé à `require_superadmin`.

Mobile actuel : ❌.

### 3.3 Procurement / finance

Sources : `backend/routers/partner_procurement.py`, `partner_finance.py`.

Prérogatives vérifiées :
- lecture détail procurement d'une commande ;
- saisie/mise à jour facture/coût fournisseur/paiement/notes avec version/idempotence ;
- gestion financière des commandes : moyen/statut paiement, timestamps livraison/facture, ajustements/frais, règlement, charge cabinet, payout fournisseur, références ;
- validations de transitions et ledger serveur ;
- routes réservées à `require_superadmin`.

Mobile actuel : ❌.

### 3.4 Réceptions

Source : `backend/routers/partner_receipts.py`.

Prérogatives vérifiées :
- `GET /{order_id}/receipts` ;
- `POST /{order_id}/receipt` ;
- réception partielle/complète, lot, expiration, note, idempotence ;
- interdiction de sur-réception ;
- passage à `FULFILLED` lorsque complet ;
- routes réservées à `require_superadmin`.

Mobile actuel : ❌.

### 3.5 Synchronisation catalogue fournisseur

Source : `backend/routers/partner_sync.py`.

Prérogatives vérifiées :
- `GET /suppliers/{supplier_id}/sync-status` ;
- `POST /suppliers/{supplier_id}/sync` avec option `force` ;
- état/fraîcheur, audit, retry/backoff et application canonique du snapshot ;
- routes réservées à `require_superadmin` ;
- garde d'identité locale renforcée par `partner_sync_safety.py`.

Mobile actuel : ❌.

---

## 4. Règle de parité

La matrice ci-dessus représente les prérogatives SuperAdmin vérifiées au baseline. **Si une autre route `require_superadmin` / `verify_superadmin` active est découverte pendant l'implémentation ou la certification, elle entre automatiquement dans le scope MOB-5H avant fermeture.**

Donc aucune affirmation "100 %" ne sera faite avant le sweep final des guards et la preuve endpoint → UI/test.

---

## 5. Contraintes de sécurité

- Ne jamais remplacer `verify_superadmin` / `require_superadmin` par un contrôle frontend.
- Mobile fail-closed : un utilisateur non SuperAdmin ne voit ni n'appelle ces surfaces.
- Aucune nouvelle écriture directe DB/Supabase.
- Réutiliser `mobileFetch` et le JWT mobile device-bound.
- Préserver idempotency/version/confirm tokens existants.
- Confirmation renforcée pour : révocation licence, archivage, suspension, désactivation fournisseur, dispatch réel, finance/procurement, réception et toute mutation externe/destructive.
- Preview : données fictives uniquement, aucune API réelle.
- Aucun déploiement Vercel dans ce lot sans autorisation explicite.

---

## 6. Écart produit

Le mobile actuel couvre 3 familles d'actions seulement : pack, prolongation, suspension. La parité exige une vraie console SuperAdmin mobile structurée, pas l'empilement de vingt boutons sur chaque carte client.

**Conclusion audit : MOB-5H = extension fonctionnelle majeure de la surface mobile SuperAdmin, sans changement de pouvoir backend.**
