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
- le control-plane Marketplace refuse toujours un JWT mobile ordinaire ;
- le control-plane Marketplace n'accepte un mobile SuperAdmin qu'après step-up WebAuthn vérifié, via le JWT court `biometric_uv=true` déjà émis par Digital Crown ;
- les protections web/cookie/Origin existantes restent inchangées ;
- tests dédiés mobile + sécurité backend + build + tests backend existants + certification visuelle/runtime ;
- BEFORE et AFTER comparés sur les mêmes viewports.

## Proof attendue

- matrice endpoint/action/mobile couverte par tests ;
- test dédié `MobileSuperAdminView.test.tsx` ;
- build production ;
- tests backend Marketplace/SuperAdmin pertinents ;
- test sécurité : mobile normal → 403 ; mobile UV WebAuthn → autorisé jusqu'au guard métier ; web/cookie CSRF inchangé ;
- captures 390×844, 430×932, 768×1024 ;
- 0 overflow / 0 runtime error ;
- aucune requête de preview vers une API réelle ;
- aucune suppression/relaxation générale des guards backend.

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

Source : `backend/routers/superadmin.py` ; toutes protégées par `verify_superadmin` et montées sous `/api/superadmin`.

| Domaine | Prérogative | Endpoint | Mobile actuel | MOB-5H |
|---|---|---|---|---|
| Clients | Lister/statistiques | `GET /api/superadmin/clients` | ✅ | conserver |
| Clients | Valider/activer + essai 30j | `POST /api/superadmin/clients/{id}/validate` | ❌ | ajouter |
| Codes d'essai | Lister | `GET /api/superadmin/trial-codes` | ❌ | ajouter |
| Codes d'essai | Créer | `POST /api/superadmin/trial-codes` | ❌ | ajouter |
| Codes d'essai | Révoquer | `POST /api/superadmin/trial-codes/{id}/revoke` | ❌ | ajouter |
| Licence | Prolonger 1m/3m/6m/1y | `POST /api/superadmin/clients/{id}/grant-license` | ✅ | conserver |
| Licence | Révoquer | même endpoint, `action=revoke` | ❌ | ajouter |
| Compte | Archiver/désarchiver | `PATCH /api/superadmin/clients/{id}/archive` | ❌ | ajouter |
| Compte | Suspendre/réactiver | `PATCH /api/superadmin/clients/{id}/suspend` | ✅ | conserver |
| Abonnement | Changer GOLD/PREMIUM/ELITE | `PATCH /api/superadmin/clients/{id}/plan` | ✅ | conserver |
| CRM interne | Notes internes | `PATCH /api/superadmin/clients/{id}/notes` | ❌ | ajouter |
| Audit licence | Historique | `GET /api/superadmin/clients/{id}/license-history` | ❌ | ajouter |
| Relance | Relance renouvellement, WhatsApp si téléphone disponible | `POST /api/superadmin/clients/{id}/send-renewal-email` | ❌ | ajouter |

**Précision vérifiée :** malgré son nom historique `send-renewal-email`, l'implémentation baseline envoie actuellement une relance WhatsApp via le service de notification lorsqu'un téléphone existe, puis journalise `renewal_whatsapp_sent`.

Les effets serveur existants restent autoritaires : invalidation cache licence, historique, écriture licence et tâches de notification lorsque prévues par le backend.

---

## 3. Prérogatives Marketplace SuperAdmin vérifiées

### 3.1 Vue globale / gouvernance P10

Sources : `backend/routers/superadmin.py`, `partner_superadmin.py`, `partner_superadmin_catalog.py`, `partner_superadmin_security.py`.

Montage vérifié : `superadmin.router` inclut `partner_superadmin.router`, lui-même préfixé `/marketplace`; la surface active est donc sous **`/api/superadmin/marketplace`**. `partner_superadmin.router` inclut aussi le catalogue global.

| Domaine | Prérogative | Endpoint actif | Mobile actuel | MOB-5H |
|---|---|---|---|---|
| KPI global | Vue Marketplace multi-cabinets | `GET /api/superadmin/marketplace/overview` | ❌ | ajouter |
| Commandes | Liste globale + filtres | `GET /api/superadmin/marketplace/orders` | ❌ | ajouter |
| Sync | Incidents fournisseur | `GET /api/superadmin/marketplace/sync-incidents` | ❌ | ajouter |
| Fournisseurs | Liste globale | `GET /api/superadmin/marketplace/suppliers` | ❌ | ajouter |
| Gouvernance | Lire accord/activation | `GET /api/superadmin/marketplace/suppliers/{id}/governance` | ❌ | ajouter |
| Gouvernance | Activer/désactiver + accord | `PATCH /api/superadmin/marketplace/suppliers/{id}/governance` | ❌ | ajouter |
| Audit | Journal Marketplace | `GET /api/superadmin/marketplace/audit` | ❌ | ajouter |
| Fournisseurs | Créer/modifier globalement | `POST/PATCH /api/superadmin/marketplace/suppliers...` | ❌ | ajouter |
| Produits | Lister/créer/modifier globalement | `GET/POST/PATCH /api/superadmin/marketplace/products...` | ❌ | ajouter |

Les mutations globales exigent `confirm=true` côté payload et restent protégées par les guards SuperAdmin. Le catalogue tenant-scoped `/api/partner-catalog` conserve par ailleurs ses propres mutations SuperAdmin canoniques ; MOB-5H privilégie la surface globale lorsqu'elle donne le même pouvoir avec sélection explicite du cabinet.

### 3.1.1 Barrière mobile P10 — constat critique vérifié

Le baseline `partner_superadmin_security.py` rejette **tout** Bearer dont `type == "mobile"` avec `MARKETPLACE_SUPERADMIN_WEB_REQUIRED`, y compris une session biométrique. Le test `backend/tests/test_marketplace_superadmin_security.py` certifie explicitement ce comportement.

Cette politique est incompatible avec le Goal demandé de parité mobile complète si elle reste inchangée.

Digital Crown dispose toutefois déjà du mécanisme nécessaire pour fermer l'écart sans ouvrir le control-plane :

- WebAuthn/passkey lié à l'utilisateur + tenant + `device_id` ;
- vérification utilisateur requise (`user_verification=required`) ;
- challenge one-shot/expirant ;
- émission après vérification d'un JWT mobile device-bound avec `biometric_uv=true` ;
- durée de cette session UV : **5 minutes** (`BIOMETRIC_SESSION_TTL`) ;
- `get_current_user` et le decoder mobile vérifient signature, appareil appairé, utilisateur/tenant et révocation.

**Décision sécurité MOB-5H :** remplacer le refus absolu P10 par un refus ciblé :

- JWT mobile normal → toujours 403 ;
- JWT mobile avec `biometric_uv=true` émis après WebAuthn → admissible au guard SuperAdmin ;
- tokens web Bearer → comportement inchangé ;
- mutations cookie → exigences Origin HTTPS inchangées.

Ce changement est une extension étroite de la politique d'authentification, **pas** une suppression de guard. Il doit être couvert par tests backend avant toute certification.

### 3.2 Commandes / dispatch

Sources : `backend/routers/__init__.py`, `partner_orders.py`, `partner_orders_p6.py`, `partner_dispatch.py`.

Montage vérifié : les extensions P6 sont incluses dans `partner_orders.router`, exposé sous `/api/partner-orders`.

Prérogatives vérifiées :
- `GET /api/partner-orders` SuperAdmin-only ;
- `PATCH /api/partner-orders/{order_id}` SuperAdmin-only via la façade P6 active ;
- transition directe vers `SENT_TO_PARTNER` interdite par le PATCH : elle exige `/dispatch` avec preuve de transport ;
- transitions statut/montant/référence/note selon moteur canonique ;
- `GET /api/partner-orders/{order_id}/dispatch` ;
- `POST /api/partner-orders/{order_id}/dispatch` : envoi fournisseur HTTPS avec garde SSRF, hash payload, idempotence et preuve de transport ;
- dispatch réservé à `require_superadmin`.

Mobile actuel : ❌.

### 3.3 Procurement

Source : `backend/routers/partner_procurement.py`.

Routes actives sous `/api/partner-orders` et réservées à `require_superadmin` :

- `GET /api/partner-orders/{order_id}/procurement` ;
- `PUT /api/partner-orders/{order_id}/procurement`.

Contrat mutation vérifié : `supplierReference` obligatoire, `expectedDeliveryAt` optionnel, `backorderedLines[]` avec `productId` + `quantityBackordered`, `note` optionnelle. Le serveur exige une commande `CONFIRMED`, canonicalise les backorders contre commandé/reçu/reliquat et traite un payload identique comme replay idempotent.

Mobile actuel : ❌.

### 3.4 Finance / rapprochement fournisseur

Source : `backend/routers/partner_finance.py`.

Le contrat actif est **plus étroit qu'une gestion générique des paiements**. Il couvre :

- `POST /api/partner-orders/finance/orders/{order_id}/invoices` : enregistrer une facture fournisseur ;
  - `invoiceKey` idempotent, `invoiceReference`, `amountTotal`, devise MAD uniquement, `issuedAt`, `note` ;
- `GET /api/partner-orders/finance/orders/{order_id}/reconciliation` : rapprochement commande / payable fournisseur / factures / réceptions ;
- `GET /api/partner-orders/finance/summary` : synthèse de rapprochement du tenant.

États de rapprochement canoniques vérifiés : `WAITING_INVOICE`, `AMOUNT_MISMATCH`, `WAITING_RECEIPT`, `MATCHED`, `CANCELLED`.

**Aucune API générique paiement/payout/charge cabinet n'est inventoriée dans ce router baseline ; MOB-5H ne doit pas en fabriquer une.**

Mobile actuel : ❌.

### 3.5 Réceptions

Sources : `backend/routers/__init__.py`, `partner_receipts.py`, `partner_receipts_p7.py`.

Prérogatives vérifiées sous `/api/partner-orders` :
- `GET /api/partner-orders/{order_id}/receipts` ;
- `POST /api/partner-orders/{order_id}/receipt` via façade P7 active ;
- payload : `idempotencyKey`, lignes `productId`, `quantityReceived`, `lotNumber`, `expiresAt`, note ;
- réception uniquement depuis `CONFIRMED` ;
- canonicalisation commandé/déjà reçu/reliquat et interdiction de sur-réception ;
- passage à `FULFILLED` lorsque complet ;
- la façade P7 tente ensuite l'application stock de façon rejouable et expose `stockSync` (`APPLIED`, `PENDING_MAPPING` ou `PENDING_RETRY`) sans annuler la vérité réception ;
- routes réservées à `require_superadmin`.

Mobile actuel : ❌.

### 3.6 Synchronisation catalogue fournisseur

Sources : `backend/routers/__init__.py`, `partner_sync.py`, `partner_sync_safety.py`.

Montage vérifié : `partner_sync.router` est inclus dans `partner_catalog.router`, exposé sous `/api/partner-catalog`.

Prérogatives vérifiées :
- `GET /api/partner-catalog/suppliers/{supplier_id}/sync-status` ;
- `POST /api/partner-catalog/suppliers/{supplier_id}/sync` avec option `force` ;
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
- Pour P10 global, exiger un token mobile UV court issu du WebAuthn existant ; un token mobile ordinaire reste refusé.
- Préserver idempotency/version/confirm tokens existants.
- Confirmation renforcée pour : révocation licence, archivage, suspension, désactivation fournisseur/gouvernance, dispatch réel, finance/procurement, réception et toute mutation externe/destructive.
- Preview : données fictives uniquement, aucune API réelle.
- Aucun déploiement Vercel dans ce lot sans autorisation explicite.

---

## 6. Écart produit

Le mobile actuel couvre 3 familles d'actions seulement : pack, prolongation, suspension. La parité exige une vraie console SuperAdmin mobile structurée, pas l'empilement de vingt boutons sur chaque carte client.

Une barrière backend supplémentaire est désormais prouvée : le control-plane P10 est web-only au baseline. MOB-5H doit donc étendre **étroitement** ce guard aux sessions mobiles WebAuthn UV, tout en continuant à refuser les JWT mobiles ordinaires.

**Conclusion audit : MOB-5H = extension fonctionnelle majeure de la surface mobile SuperAdmin + extension biométrique étroite du control-plane P10, sans création de nouvelles prérogatives métier.**
