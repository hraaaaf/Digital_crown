# Digital Crown — Marketplace Audit & Roadmap

**Statut canonique : ACTIF**  
**Date de baseline : 2026-08-30**  
**Repo :** `hraaaaf/Digital_crown`  
**Branche de baseline :** `marketplace/audit-roadmap`  
**Référence code auditée :** `master @ f19df12739fc262adb2238db1842813b4a820619`  
**Déploiement Vercel :** aucun, non requis pour ce lot.

---

## 1. Goal / Succès / Preuve

### Goal
Transformer le Marketplace Digital Crown en module d'approvisionnement fiable, rapide et cohérent : découverte produit → panier → commande → fournisseur → réception → stock → réassort, avec une UX claire et un contrat engineering sûr.

### Succès
Le chantier est terminé uniquement lorsque :

1. l'autorité serveur contrôle prix, totaux et termes commerciaux ;
2. le RBAC Marketplace est explicite et testé ;
3. les paniers multi-fournisseurs ont une règle métier déterministe ;
4. le cycle de commande est réel et traçable jusqu'à la réception ;
5. l'UI est validée BEFORE/AFTER aux mêmes viewports ;
6. les parcours critiques ont des tests backend/frontend/E2E ;
7. la réception peut alimenter le stock sans ressaisie incohérente ;
8. tous les gates finaux de cette roadmap sont verts.

### Preuve attendue
Code + tests automatisés + comportement runtime observé + captures BEFORE/AFTER + audit de cohérence + CI verte. Aucun score visuel « certifié » sans captures runtime.

---

## 2. Scope vérifié

### Frontend inspecté

- `frontend/src/pages/PartnerMarketplacePage.tsx`
- `frontend/src/pages/PartnerProductPage.tsx`
- `frontend/src/pages/PartnerSupplierPage.tsx`
- `frontend/src/pages/PartnerCatalogAdminPage.tsx`
- `frontend/src/features/partnerMarketplace/data.ts`
- `frontend/src/App.tsx`
- `frontend/src/components/Sidebar.tsx`

### Backend inspecté

- `backend/routers/partner_catalog.py`
- `backend/routers/partner_orders.py`
- `backend/models.py`
- `backend/routers/auth.py`

### Tests inspectés

- inventaire `backend/tests`
- inventaire `frontend/src/test`
- recherche ciblée des routes/identifiants Marketplace

**Constat :** aucun test dédié Marketplace n'a été repéré dans l'inventaire et les recherches actuels. Cela signifie « non repéré », pas « preuve absolue d'absence dans tout le repo ».

---

## 3. Baseline fonctionnelle vérifiée

Le Marketplace n'est pas une maquette. Les capacités suivantes existent :

- catalogue fournisseurs + produits ;
- recherche et filtres ;
- pages fournisseur et produit ;
- panier persistant `localStorage` ;
- gestion des quantités ;
- formulaire de commande ;
- création de commande serveur ;
- stratégies commerciales / simulation de revenu ;
- interface superadmin de création catalogue ;
- interface superadmin de rapprochement de commandes ;
- backend de création/mise à jour fournisseurs et produits ;
- backend de création/liste/mise à jour commandes + événements/revenu.

---

## 4. Score baseline

Le score mesure l'état actuel du produit, pas son potentiel.

| Axe | Poids | Score | Confiance | Justification synthétique |
|---|---:|---:|---|---|
| UX | 20 % | **7.2/10** | moyenne | parcours riche et compréhensible, mais densité marketing, contrat formulaire et sémantique d'envoi perfectibles |
| UI / interaction | 15 % | **7.4/10** | moyenne-faible | composants structurés et responsive ; validation visuelle runtime non réalisée dans ce lot |
| Fonctionnalités | 25 % | **6.8/10** | élevée | catalogue/panier/commande/admin présents ; cycle fournisseur→réception→stock incomplet |
| Engineering | 25 % | **5.8/10** | élevée | architecture séparée correcte, mais autorité financière serveur, état commande et couverture tests insuffisants |
| Sécurité / fiabilité | 15 % | **5.2/10** | élevée | permissions commande trop larges et données commerciales modifiables via contrat client |
| **Score pondéré actuel** | **100 %** | **6.5/10** | — | `(7.2×.20)+(7.4×.15)+(6.8×.25)+(5.8×.25)+(5.2×.15)=6.48` |

### Potentiel produit

**9.0/10** — potentiel séparé du score de capacité actuel. Le Marketplace peut devenir un vrai moteur d'approvisionnement cabinet, surtout s'il est relié au stock, à la consommation, aux lots/péremptions et à la performance fournisseur.

### Limite importante

Le **7.4/10 UI n'est pas un score visuel certifié**. Il s'agit d'un score statique basé sur le code et la structure des interactions. La certification visuelle exige des captures runtime BEFORE puis AFTER aux mêmes viewports.

---

## 5. Findings prioritaires

### MP-P0-01 — Autorité financière serveur absente

**Sévérité : P0**  
**Vérifié :** `POST /partner-orders` accepte depuis le client les prix de ligne, totaux et paramètres commerciaux (`unitPrice`, `lineTotal`, `estimatedTotal`, taux et modèle de revenu) sans recalcul catalogue observé.

**Risque :** un client modifié peut envoyer des valeurs financières falsifiées ; les métriques de revenu dérivées perdent leur valeur de preuve.

**Succès :** le serveur résout produit/fournisseur depuis le catalogue, applique la stratégie autorisée et recalcule tous les montants avant persistance.

**Preuve :** tests de tampering + tests de calcul serveur + comparaison payload client / données persistées.

### MP-P0-02 — RBAC commandes trop large

**Sévérité : P0**  
**Vérifié :** lecture et mise à jour des commandes utilisent `require_permission("patients")`. L'UI admin est superadmin, mais le backend n'impose pas ce même niveau pour `GET /partner-orders` et `PATCH /partner-orders/{id}`.

**Risque :** un utilisateur métier autorisé aux patients peut accéder à des données clients/commerciales Marketplace et modifier statut, total final, référence ou note selon le contrat observé.

**Succès :** permission Marketplace dédiée ou garde superadmin explicite selon opération ; tests négatifs par rôle.

**Preuve :** matrice RBAC automatisée.

### MP-P0-03 — Panier multi-fournisseurs incohérent avec une commande mono-fournisseur

**Sévérité : P0**  
**Vérifié :** le catalogue permet d'ajouter des produits de plusieurs fournisseurs ; la soumission utilise un seul fournisseur actif pour l'ensemble de la commande ; aucun rejet serveur de mélange n'a été observé.

**Succès :** soit panier limité à un fournisseur avec feedback explicite, soit split automatique en commandes par fournisseur. Recommandation : **split automatique**.

**Preuve :** E2E panier 2 fournisseurs → 2 commandes cohérentes et montants séparés.

### MP-P1-01 — Contrat formulaire frontend/backend divergent

**Vérifié :** le frontend valide surtout nom/téléphone, alors que le modèle backend exige également des champs non vides tels que clinique, email et ville.

**Risque :** état considéré valide côté UI mais rejeté en 422 côté serveur.

**Succès :** schéma partagé ou validation frontend strictement alignée au contrat backend.

### MP-P1-02 — CTA « envoyer au partenaire » sans transport partenaire observé

**Vérifié :** l'action crée une commande locale `DRAFT` ; aucune intégration email/API fournisseur n'a été observée dans le chemin inspecté.

**Risque :** faux sentiment d'envoi réel.

**Succès :** renommer l'action en « Créer la demande » tant qu'aucun transport n'existe, ou implémenter une livraison fournisseur avec statut/horodatage/preuve.

### MP-P1-03 — Cache catalogue sans TTL appliqué

**Vérifié :** le snapshot possède `syncedAt`, mais la lecture du cache observée n'applique pas de durée maximale.

**Risque :** prix/catalogue obsolètes indéfiniment en mode fallback.

**Succès :** TTL + indicateur de fraîcheur + politique explicite pour commande sur données périmées.

### MP-P1-04 — Panier local non scopé

**Vérifié :** clé globale `dc.marketplace.partner-cart.v1`.

**Risque :** un utilisateur/cabinet partageant le navigateur peut récupérer un panier créé dans un autre contexte.

**Succès :** clé par cabinet + utilisateur ou panier serveur lié au contexte authentifié.

### MP-P1-05 — Fournisseur inactif potentiellement visible

**Vérifié :** la disponibilité produit est filtrée, mais le chemin de listing inspecté ne démontre pas un filtre systématique `supplier.is_active` avant exposition storefront.

**Succès :** un produit d'un fournisseur inactif n'est jamais achetable.

### MP-P1-06 — `isFeatured` / `sortOrder` non respectés par le storefront

**Vérifié :** backend/admin exposent ces champs ; le normaliseur storefront inspecté ne les transporte pas jusqu'au ranking principal.

**Succès :** merchandising déterministe et testé.

### MP-P1-07 — Machine d'état commande trop permissive

**Vérifié :** le PATCH accepte des changements de statut sans graphe de transitions métier complet observé.

**Succès :** transitions autorisées explicites, par exemple :

`DRAFT → SENT → CONFIRMED → SHIPPED → RECEIVED → INVOICED`

avec branches `CANCELLED`, `REJECTED`, `MODIFIED_AFTER_SEND` contrôlées.

### MP-P1-08 — Données commerciales exposées dans le parcours achat

**Vérifié :** stratégies et « revenu simulé » apparaissent dans le module principal et le contrat de lecture repose sur une permission générique patients.

**Succès :** séparer UX acheteur et UX opérateur/commercial ; masquer les données internes selon rôle.

### MP-P2-01 — Administration incomplète

**Vérifié :** création fournisseur/produit + rapprochement commande existent. Le backend expose des PATCH, mais aucune UI d'édition complète équivalente n'a été repérée dans la page admin inspectée.

**Succès :** édition, activation/désactivation, historique et confirmation des actions sensibles.

### MP-P2-02 — Pagination / montée en charge

**Vérifié :** aucune pagination n'a été observée sur les listes catalogue/commandes inspectées.

**Succès :** pagination/limites serveur + recherche filtrée pour volumes réalistes.

### MP-P2-03 — Accessibilité et densité visuelle

**Vérifié statiquement :** multiples labels très petits/uppercase/tracking ; contrôles de quantité icon-only sans `aria-label` observé ; forte densité de cartes marketing.

**Succès :** clavier, nom accessible, zones tactiles, contraste, hiérarchie et densité validés runtime.

### MP-P2-04 — Visuels produits sous-exploités

**Vérifié :** le modèle supporte URLs/galerie mais le storefront s'appuie largement sur des visuels générés/thématiques.

**Succès :** vraies photos produits lorsque disponibles, fallback cohérent sinon.

### MP-P2-05 — Rechargement brutal après ajout produit

**Vérifié :** `PartnerProductPage.tsx` utilise `window.location.reload()` après ajout au panier.

**Succès :** état panier réactif partagé, sans reload de page.

---

## 6. Roadmap canonique — 100 EP

Aucun lot futur n'est crédité simplement parce qu'une partie du code existe déjà. Crédit uniquement après preuve de ses critères.

| Lot | EP | Goal | Gate principal |
|---|---:|---|---|
| **A — Baseline audit + canonique** | **8** | état réel, scores, risques, roadmap | audit code + fichier canonique vérifiés |
| **B — Trust & financial integrity** | **22** | serveur autoritaire + multi-fournisseur sûr | tampering impossible + split/rejet testé |
| **C — RBAC, lifecycle & tests** | **18** | rôles et états commande fiables | matrice RBAC + machine d'état + tests |
| **D — UX/UI task-first** | **20** | achat/réassort rapide, clair, accessible | BEFORE/AFTER + E2E + score visuel |
| **E — Procurement lifecycle** | **15** | commande réellement envoyée et suivie jusqu'à réception | preuve de transport + réception |
| **F — Stock, reorder & analytics** | **12** | Marketplace relié à la consommation/stock | réassort + lots/péremptions + KPI |
| **G — Certification finale** | **5** | chantier prouvé et documenté | CI + runtime + docs + closeout |
| **Total** | **100** |  |  |

### Avancement

**Lot A : 8/8 EP** — audit statique et document canonique produits sur la branche dédiée.  
**Global : 8/100 EP = 8 %.**

Ce pourcentage mesure la roadmap nouvellement définie, pas le pourcentage de fonctionnalités déjà présentes dans l'ancien Marketplace.

---

## 7. Idées produit — score valeur / effort

Échelle valeur : 1–10. Effort : 1 faible → 5 élevé. La priorité tient aussi compte des dépendances P0/P1.

| Idée | Valeur | Effort | Priorité | Pourquoi |
|---|---:|---:|---|---|
| Réassort en 1 clic depuis commande précédente | 9 | 2 | P1 | gain de temps cabinet immédiat |
| Suggestions de réassort selon consommation/min-max | 10 | 4 | P1 | transforme le Marketplace en outil opérationnel |
| Split automatique du panier par fournisseur | 10 | 3 | P0 | corrige contrat métier + améliore UX |
| RFQ / comparaison fournisseurs | 8 | 4 | P2 | arbitrage prix/délai/MOQ |
| Historique prix + MOQ + délai + livraison | 9 | 3 | P1 | décision achat factuelle |
| Score fournisseur SLA | 8 | 3 | P2 | OTD, fill-rate, retours, qualité |
| Workflow budget / approbation | 7 | 4 | P2 | utile cabinets multi-utilisateurs |
| Réception → stock automatique | 10 | 4 | P1 | supprime double saisie et ferme la boucle |
| Lots + péremptions à la réception | 10 | 4 | P1 | forte valeur clinique/logistique |
| Substitutions en rupture | 8 | 3 | P2 | continuité d'approvisionnement |
| Alertes backorder / ETA | 8 | 3 | P2 | réduit incertitude fournisseur |
| Tarification contractuelle par cabinet | 8 | 4 | P2 | prix B2B réalistes |
| Facture / rapprochement commande-réception | 9 | 4 | P2 | contrôle financier |
| Audit trail exportable immuable | 8 | 3 | P1 | gouvernance et support |
| Copilote achats déterministe/IA assistée | 7 | 5 | P3 | utile après données propres, pas avant |

### Recommandation produit

Ne pas commencer par l'IA. La séquence à rendement maximal est :

**intégrité serveur → split fournisseur → RBAC/lifecycle → réassort → réception/stock → analytics → IA.**

Un copilote posé sur des prix falsifiables serait une façon très moderne d'automatiser la mauvaise décision.

---

## 8. Protocole UX/UI obligatoire

Avant tout changement visuel du lot D :

1. **BEFORE** sur le runtime actuel ;
2. Goal visuel écrit + critères ;
3. mockup/référence ;
4. implémentation ;
5. **AFTER** aux mêmes viewports ;
6. comparaison ;
7. tests clavier/accessibilité/responsive ;
8. score visuel final.

### Viewports de référence

- `1440 × 900`
- `1280 × 800`
- `390 × 844`

### Critères de score visuel

- hiérarchie /10 ;
- lisibilité /10 ;
- densité orientée tâche /10 ;
- clarté CTA /10 ;
- cohérence /10 ;
- responsive /10 ;
- accessibilité observable /10.

Aucun « 10/10 » sans preuves BEFORE/AFTER.

---

## 9. Matrice de certification

### Backend

- [ ] utilisateur non admin refusé sur liste/édition admin des commandes ;
- [ ] prix/totaux/termes commerciaux recalculés serveur ;
- [ ] payload financier falsifié rejeté ou ignoré ;
- [ ] mélange fournisseurs rejeté ou split côté serveur ;
- [ ] fournisseur/produit inactif non commandable ;
- [ ] transitions de statut testées ;
- [ ] `finalTotal` modifiable uniquement par rôle autorisé ;
- [ ] pagination/limites testées ;
- [ ] audit events cohérent.

### Frontend

- [ ] `isFeatured`/`sortOrder` respectés ;
- [ ] panier scopé par contexte ;
- [ ] validation formulaire = contrat backend ;
- [ ] multi-fournisseur explicite ;
- [ ] CTA reflète l'action réelle ;
- [ ] TTL/fraîcheur cache visible ;
- [ ] ajout panier sans reload ;
- [ ] données commerciales masquées aux rôles non concernés.

### E2E

- [ ] recherche → filtre → produit → panier → commande ;
- [ ] panier multi-fournisseurs ;
- [ ] erreurs API / 422 rendues proprement ;
- [ ] fallback catalogue obsolète ;
- [ ] clavier + lecteur d'écran minimal ;
- [ ] responsive 1440/1280/390 ;
- [ ] commande → envoi → suivi → réception → stock.

---

## 10. Séquence d'exécution

### Lot B — prochaine action exacte

1. rendre le serveur autoritaire sur catalogue, prix, totaux et termes commerciaux ;
2. ajouter tests de tampering ;
3. définir et implémenter le contrat multi-fournisseur ;
4. vérifier les régressions commande/admin ;
5. mettre à jour ce fichier avec preuves et EP réellement crédités.

### Puis

Lot C RBAC/lifecycle/tests → Lot D UX/UI → Lot E procurement réel → Lot F stock/reorder/analytics → Lot G certification.

---

## 11. Règles de reprise

En nouvelle fenêtre :

1. lire ce fichier ;
2. vérifier `master`, HEAD, branche/PR active et CI ;
3. ne pas reprendre un score ou un EP sans preuve correspondante ;
4. continuer au **Next exact** ci-dessus ;
5. mettre à jour ce fichier après chaque closeout significatif.

Ce fichier est la **source canonique Marketplace** jusqu'à remplacement explicitement documenté.
