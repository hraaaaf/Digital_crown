# Digital Crown — Marketplace Audit & Roadmap

**Statut canonique : ACTIF**  
**Date de baseline : 2026-08-30**  
**Repo :** `hraaaaf/Digital_crown`  
**Branche active :** `marketplace/p0-trust-integrity`  
**Baseline auditée :** `master @ f19df12739fc262adb2238db1842813b4a820619`  
**Canonique initial mergé :** PR #301 → `master @ 3da5b6858d95d527766b4c4986fee4eca3c12d75`  
**Déploiement Vercel :** interdit sans autorisation explicite ; aucun requis ici.

---

## 1. Goal / Succès / Preuve

### Goal
Transformer le Marketplace Digital Crown en module d'approvisionnement fiable, rapide et cohérent : découverte produit → panier → commande → fournisseur → réception → stock → réassort, avec une UX claire et un contrat engineering sûr.

### Succès final
Le chantier est terminé uniquement lorsque :
1. le serveur contrôle prix, totaux et termes commerciaux ;
2. le RBAC Marketplace est explicite et testé ;
3. le panier multi-fournisseurs suit une règle métier déterministe ;
4. le cycle commande est traçable jusqu'à réception ;
5. l'UI est validée BEFORE/AFTER aux mêmes viewports ;
6. les parcours critiques ont des tests backend/frontend/E2E ;
7. la réception alimente le stock sans double saisie incohérente ;
8. les intégrations fournisseur ont des preuves de livraison/retry ;
9. le Superadmin gouverne fournisseurs, catalogues, accords et incidents ;
10. tous les gates P0→P11 sont verts.

### Preuve attendue
Code + tests automatisés + comportement runtime observé + captures BEFORE/AFTER + audit de cohérence + CI verte. Aucun score visuel certifié sans captures runtime.

---

## 2. Baseline fonctionnelle vérifiée

Le Marketplace actuel possède déjà :
- catalogue fournisseurs + produits ;
- recherche et filtres ;
- pages fournisseur et produit ;
- panier persistant localStorage ;
- gestion des quantités ;
- formulaire de commande ;
- création de commande serveur ;
- stratégies commerciales / simulation de revenu ;
- administration catalogue ;
- rapprochement de commandes ;
- backend fournisseurs/produits ;
- backend commandes + événements/revenu.

### Score baseline
| Axe | Poids | Score | Confiance |
|---|---:|---:|---|
| UX | 20 % | **7.2/10** | moyenne |
| UI / interaction | 15 % | **7.4/10** | moyenne-faible, non certifié runtime |
| Fonctionnalités | 25 % | **6.8/10** | élevée |
| Engineering | 25 % | **5.8/10** | élevée |
| Sécurité / fiabilité | 15 % | **5.2/10** | élevée |
| **Score pondéré** | **100 %** | **6.5/10** | — |

**Potentiel produit séparé : 9.0/10.**

---

## 3. Roadmap canonique P0 → P11 — 100 EP

La nomenclature P0→P11 est la seule nomenclature canonique du chantier. Les anciens lots A/B/C/... sont abandonnés.

| Phase | EP | Ce que fait le lot | Gate observable |
|---|---:|---|---|
| **P0 — Baseline & audit** | **8** | audit global, score initial, findings, roadmap, fichier canonique | audit + canonique mergés et relus sur `master` |
| **P1 — Trust & sécurité** | **14** | autorité financière serveur, isolation cabinet, RBAC, anti-falsification, règles fournisseurs | tampering impossible + matrice RBAC + tests négatifs |
| **P2 — Order Engine** | **10** | cycle panier → draft → envoi → confirmation → modification → annulation → fulfillment | machine d'état déterministe + audit trail + tests transitions |
| **P3 — Multi-fournisseurs** | **8** | plusieurs fournisseurs, routage/split des commandes, contrats par fournisseur | panier multi-fournisseurs → commandes cohérentes sans mélange |
| **P4 — Catalogue & produits** | **8** | catalogue fiable, catégories, recherche, disponibilité, merchandising, fraîcheur/cache | données publiées cohérentes + TTL + filtres + pagination |
| **P5 — UX/UI Marketplace** | **16** | refonte task-first, navigation, recherche, panier, checkout, responsive, accessibilité | BEFORE → Goal → mockup → AFTER 390/430/768/1280 + E2E |
| **P6 — Procurement** | **10** | demande/commande fournisseur, transmission réelle, suivi, réception | preuve transport + ETA/statut + réception traçable |
| **P7 — Stock Intelligence** | **8** | réception→stock, seuils, consommation, lots/péremptions, reorder | mouvement stock fiable + suggestion/réassort testé |
| **P8 — Finance & monétisation** | **6** | commissions/remises/revente, rapprochement, revenus reconnus, annulations/avoirs | calculs serveur + événements auditables + tests finance |
| **P9 — Automatisation fournisseur** | **4** | API/import fournisseur, synchro prix/stock, retry, résilience | sync idempotente + erreurs/retry + preuve de fraîcheur |
| **P10 — Superadmin Marketplace** | **3** | gouvernance fournisseurs/catalogues/accords, supervision et incidents | opérations sensibles superadmin + journal + dashboards utiles |
| **P11 — Certification finale** | **5** | E2E réel, sécurité, multi-cabinet, perf, a11y, docs, closeout | matrice finale verte + CI + runtime + docs cohérentes |
| **Total** | **100** |  |  |

### Ordre critique
`P0 ✅ → P1 EN COURS → P2 → P3 → P4 → P5 → P6 → P7 → P8 → P9 → P10 → P11`

### Avancement vérifié
- **P0 : 8/8 EP ✅** — PR #301 mergée et fichier canonique relu sur `master`.
- **P1 : 0/14 EP** tant que ses gates ne sont pas tous prouvés.
- **Global : 8/100 EP = 8 %.**

Aucun crédit partiel n'est accordé uniquement parce que du code existe. Crédit après preuve du gate du lot.

---

## 4. P1 — Trust & sécurité — lot actif

### Goal
Faire du serveur l'autorité unique des commandes et limiter lecture/mutation aux rôles explicitement autorisés.

### Travaux connus
- **P1.1 Autorité financière serveur** : reconstruire fournisseur, produit, SKU, prix, total et stratégie depuis le catalogue serveur.
- **P1.2 Anti-tampering** : ignorer/rejeter prix, totaux, noms, fournisseur et conditions commerciales falsifiés côté client.
- **P1.3 Isolation cabinet** : aucun produit/fournisseur/ordre d'un autre cabinet utilisable.
- **P1.4 Fournisseur/produit achetable** : fournisseur actif ; produit non discontinué.
- **P1.5 RBAC commandes** : création autorisée au cabinet ; liste commerciale globale et mutation réservées au Superadmin.
- **P1.6 Tests** : tampering, multi-tenant, fournisseur inactif, produit retiré, lignes dupliquées, rôles négatifs/positifs.

### État P1 vérifié au 2026-08-30
PR active **#302** — branche `marketplace/p0-trust-integrity`.

Implémenté mais non encore crédité :
- reconstruction serveur fournisseur/noms/SKU/prix/totaux ;
- stratégies limitées aux presets serveur ;
- rejet multi-fournisseurs côté endpoint mono-fournisseur ;
- rejet fournisseur inactif ;
- rejet produit discontinué ;
- rejet produit hors cabinet ;
- rejet ligne produit dupliquée ;
- GET `/partner-orders` réservé Superadmin ;
- PATCH `/partner-orders/{id}` réservé Superadmin ;
- POST de création conserve la permission cabinet `patients` ;
- **9 tests ciblés** couvrent intégrité et RBAC.

**Preuve manquante avant crédit :** exécution tests/CI verte et revue finale du comportement.

---

## 5. P2 — Order Engine

### Goal
Transformer la commande en machine d'état métier explicite, non en champ enum librement téléportable.

### Contrat cible
États à finaliser selon le besoin réel :
`DRAFT → SENT_TO_PARTNER → CONFIRMED → FULFILLED`
avec branches contrôlées `MODIFIED_AFTER_SEND` et `CANCELLED`.

Le lot doit décider si des états explicites `SHIPPED`, `RECEIVED`, `INVOICED`, `REJECTED` sont nécessaires ou doivent vivre dans P6/P8.

### Gate
- transitions autorisées explicites ;
- transition illégale rejetée ;
- événements horodatés ;
- idempotence sur actions répétées ;
- tests du graphe complet.

---

## 6. P3 — Multi-fournisseurs

### Goal
Permettre un panier cabinet contenant plusieurs fournisseurs sans jamais fabriquer une commande ambiguë.

### Recommandation canonique
**Split automatique par fournisseur** au moment de la préparation, avec résumé avant validation.

### Gate
Panier contenant ≥2 fournisseurs → N commandes, chacune mono-fournisseur, totaux séparés, références et erreurs indépendantes.

---

## 7. P4 — Catalogue & produits

### Scope
- fournisseurs actifs seulement dans storefront ;
- disponibilité produit fiable ;
- `isFeatured` et `sortOrder` respectés ;
- pagination/limites ;
- recherche et filtres serveur si volume ;
- TTL cache + indication fraîcheur ;
- politique d'achat sur cache périmé ;
- photos réelles lorsqu'elles existent.

### Gate
Catalogue déterministe, frais, performant et non contradictoire entre admin/backend/storefront.

---

## 8. P5 — UX/UI Marketplace

### Goal visuel obligatoire
Toute modification visuelle suit :
**BEFORE → Goal écrit → mockup/référence → implémentation → AFTER mêmes viewports → comparaison + tests → score visuel.**

### Viewports minimum
- 390 px
- 430 px
- 768 px
- 1280 px

### Cibles UX connues
- réduire la densité marketing ;
- rendre recherche/catalogue/panier prioritaires ;
- aligner validation frontend/backend ;
- remplacer le faux CTA « Envoyer au partenaire » tant qu'aucun transport réel n'existe ;
- supprimer `window.location.reload()` sur ajout produit ;
- rendre boutons quantité accessibles ;
- séparer données acheteur des données commerciales internes.

---

## 9. P6 — Procurement

### Scope
- création réelle de demande/commande ;
- transport fournisseur email/API/EDI selon intégration ;
- preuve d'envoi ;
- référence fournisseur ;
- suivi ETA / backorder ;
- réception partielle/complète ;
- rapprochement commande-réception.

### Gate
Une commande test peut être suivie de Digital Crown jusqu'à une réception traçable.

---

## 10. P7 — Stock Intelligence

### Scope
- réception → mouvement de stock ;
- lots/péremptions ;
- seuils min/max ;
- historique consommation ;
- réassort 1 clic ;
- suggestions de réassort ;
- prévention double saisie.

### Gate
Une réception Marketplace crée exactement les mouvements stock attendus, testés et auditables.

---

## 11. P8 — Finance & monétisation

### Scope
- commission ;
- remise/revente ;
- forfait ;
- revenu reconnu selon événement réel ;
- modification/annulation ;
- rapprochement commande/réception/facture ;
- reporting séparé de l'UX acheteur.

### Gate
Calculs reproductibles côté serveur et événements financiers auditables.

---

## 12. P9 — Automatisation fournisseur

### Scope
- import/synchronisation fournisseur ;
- prix et disponibilité ;
- idempotence ;
- retry/backoff ;
- dernière synchro visible ;
- mode dégradé local-first sans masquer l'obsolescence.

### Gate
Sync testée sur succès, timeout, erreur, répétition et reprise.

---

## 13. P10 — Superadmin Marketplace

### Scope
- CRUD complet fournisseurs/produits ;
- activation/désactivation ;
- accords commerciaux ;
- supervision commandes ;
- incidents sync ;
- métriques utiles ;
- confirmation actions sensibles ;
- audit log.

### Gate
Les opérations sensibles sont réservées au Superadmin et testées négativement pour les autres rôles.

---

## 14. P11 — Certification finale

### Matrice minimum
| Domaine | Preuve requise |
|---|---|
| Backend | tests P1-P10 verts |
| Frontend | build + tests ciblés |
| E2E | browse → panier → ordre → suivi → réception |
| Multi-tenant | aucune fuite inter-cabinet |
| RBAC | matrice rôles négative/positive |
| Finance | recalcul serveur + événements cohérents |
| UI | captures BEFORE/AFTER mêmes viewports |
| A11y | clavier/noms accessibles/zones tactiles/contraste |
| Performance | catalogue réaliste sans dégradation majeure |
| Docs | canonique cohérent avec HEAD/PR/CI |

---

## 15. Findings de baseline à fermer

### Critiques / P1-P3
- autorité financière serveur absente dans baseline ;
- RBAC commandes trop large (`patients`) ;
- panier multi-fournisseurs incohérent avec commande mono-fournisseur ;
- isolation/activation fournisseur à rendre contractuelle ;
- machine d'état trop permissive.

### Fonctionnels / P4-P8
- formulaire frontend/backend divergent ;
- CTA d'envoi sans transport réel observé ;
- cache sans TTL appliqué ;
- panier local non scopé par contexte ;
- `isFeatured` / `sortOrder` non utilisés correctement ;
- données commerciales visibles dans parcours achat ;
- administration d'édition incomplète ;
- pagination absente ;
- réception/stock non bouclés.

### UX/UI / P5
- densité marketing ;
- petits labels uppercase ;
- contrôles icon-only sans nom accessible observé ;
- visuels produits sous-exploités ;
- reload complet après ajout produit.

---

## 16. Idées produit scorées

| Idée | Valeur /10 | Effort 1-5 | Phase cible |
|---|---:|---:|---|
| Split automatique panier par fournisseur | 10 | 3 | P3 |
| Réassort 1 clic depuis commande précédente | 9 | 2 | P7 |
| Suggestions selon consommation/min-max | 10 | 4 | P7 |
| Réception → stock automatique | 10 | 4 | P7 |
| Lots + péremptions à la réception | 10 | 4 | P7 |
| Historique prix + MOQ + délai | 9 | 3 | P4/P6 |
| RFQ / comparaison fournisseurs | 8 | 4 | P6 |
| Score fournisseur SLA | 8 | 3 | P6/P10 |
| Alertes backorder / ETA | 8 | 3 | P6 |
| Substitutions en rupture | 8 | 3 | P6 |
| Tarification contractuelle par cabinet | 8 | 4 | P8/P9 |
| Facture / rapprochement commande-réception | 9 | 4 | P8 |
| Workflow budget / approbation | 7 | 4 | P6/P10 |

---

## 17. Règles de crédit et closeout

1. Un lot n'est crédité qu'après preuve de son gate.
2. CI en cours n'arrête jamais les travaux indépendants.
3. Un changement UI ne peut être certifié sans BEFORE/AFTER.
4. Aucun déploiement Vercel sans autorisation explicite.
5. Après chaque lot : validation → mise à jour canonique → cohérence roadmap/% → merge → post-merge → lot suivant.
6. Le score baseline ne change que lorsqu'une nouvelle preuve justifie un rescoring.

---

## 18. Reprise

**Chantier actif : Marketplace Digital Crown**  
**Phase active : P1 — Trust & sécurité**  
**PR active : #302**  
**Branche : `marketplace/p0-trust-integrity`**  
**Avancement vérifié : 8/100 EP = 8 %**  
**Next exact :** inspecter l'exécution des 9 tests P1 et la CI ; corriger si nécessaire ; merger si vert ; créditer P1 uniquement si tous ses gates sont prouvés ; puis démarrer P2.
