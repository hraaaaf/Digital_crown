# Dashboard — Roadmap de refonte gouvernée

**Statut :** canonique / en cours  
**Créé :** 2026-08-16  
**Baseline auditée :** `master@026f78290cda53ea1b07ba5e8bfd39836448d6ce`  
**Dernier lot fermé :** D1 sur `master@216b41f5b725016a5d947432cff9a1fc2ef2ff8c`  
**Page :** `frontend/src/pages/Dashboard.tsx`  
**Score audit initial :** **7,2 / 10**  
**Objectif de sortie :** **≥ 9,0 / 10**, sans régression clinique, financière, permissions, navigation ni responsive.

## Gouvernance

- Aucun lot n'est crédité sans code, tests ciblés et preuve de validation proportionnée au risque.
- Les permissions sont fail-closed côté interface et autoritaires côté backend.
- Aucun état système positif ne peut être affiché sans preuve.
- Préserver le fonctionnement local-first de Digital Crown.
- Lots indépendants, réversibles, exécutés dans l'ordre `D1 -> D2 -> D3 -> D4 -> D5 -> D6 -> D7 -> D8 -> D9`.
- Toute dette de validation globale est reportée explicitement au gate D9, jamais masquée.

## D1 — Permissions & exposition des données — FERMÉ ✅

**Goal :** supprimer les comportements fail-open et aligner Dashboard / Sidebar / backend.

**Réalisé :**
- `hasAccess()` frontend centralisé ;
- rôle inconnu / utilisateur non résolu refusés par défaut ;
- propriétaire dentiste = accès complet ;
- dentiste salarié legacy = clinique oui, finance/admin non ;
- secrétaire legacy = patients + agenda uniquement ;
- matrice explicite non vide prioritaire sur les fallbacks legacy ;
- widgets/requêtes finance conditionnés à `accounting` ;
- `/stats/financial` et intelligence financière protégés côté backend par `accounting` ;
- dashboard patient/alertes protégés par `patients` ;
- santé cabinet réservée au scope admin côté Dashboard ;
- tests frontend/backend de matrice ajoutés.

**Preuve :** certification ciblée Linux PASS : backend RBAC 6/6, compilation TypeScript de la policy frontend, assertions frontend, `py_compile`, invariants fail-closed et vérification des guards réels. Closeout : `docs/DASHBOARD_D1_CLOSEOUT.md`.

**CI externe :** GitHub Actions n'exécute actuellement aucune étape à cause d'un problème de facturation/plafond du compte (`runner_id=0`). Ce blocage est externe au code. La régression globale + build complet restent obligatoires au plus tard au gate D9.

**Merge :** PR #106 → `master@216b41f5b725016a5d947432cff9a1fc2ef2ff8c`.

## D2 — Vérité du statut système — P0

**Goal :** rendre le statut système factuel et non trompeur.

- supprimer `cabinetHealth === null => Système local actif` ;
- états minimum : `opérationnel`, `vigilance`, `critique`, `non vérifié` ;
- distinguer chargement, API/timeout indisponible et absence d'autorisation ;
- définir texte + icône + couleur accessibles pour chaque état ;
- tester polling, erreur réseau et récupération après erreur.

**Gate D2 :** aucun état positif sans preuve de santé disponible.

## D3 — Marketplace / approvisionnement — P1

**Goal :** transformer le bloc en vraie entrée produit.

- supprimer `Pourquoi ici` et tout rationale dev (`frontend only`, `re-dessiner`, etc.) ;
- corriger textes/accents ;
- conserver une carte Marketplace avec bénéfice métier réel ;
- vérifier visibilité selon rôle et pertinence cabinet ;
- ne pas concurrencer les tâches cliniques prioritaires.

**Gate D3 :** zéro texte interne/dev visible.

## D4 — Architecture du Dashboard — P1

**Goal :** sortir du composant monolithique sans changer le comportement.

- extraire au minimum : `DashboardHeader`, `QuickActions`, `MarketplaceCard`, `RecentActivity`, `WaitingRoom`, `WeeklyPerformance`, `FinanceSummary`, `CabinetHealth`, `IntelligenceAlerts`, `BusinessInsights` ;
- hooks/data loaders par domaine ;
- centraliser loading/error/empty ;
- réduire les appels API dispersés dans le gros `useEffect` ;
- conserver les `data-tour`.

**Gate D4 :** comportement fonctionnel identique, composants testables isolément.

## D5 — Hiérarchie UX / densité — P1

**Goal :** faire du Dashboard un cockpit clinique, pas un mini-BI permanent.

Ordre cible :
1. contexte du jour + recherche + actions rapides ;
2. file d'attente / arrivées ;
3. activité récente ;
4. alertes actionnables ;
5. finances / performance secondaires ou repliables ;
6. santé système/admin tertiaire ;
7. Marketplace secondaire.

- réduire cartes/titres répétitifs ;
- définir visible immédiatement vs replié ;
- préserver l'information décisionnelle, retirer le bruit ;
- vérifier empty states et nouveaux cabinets.

**Gate D5 :** les trois tâches les plus fréquentes sont identifiables et actionnables immédiatement.

## D6 — Accessibilité & interactions — P1

**Goal :** interactions robustes clavier/lecteur d'écran.

- noms accessibles explicites aux boutons iconiques ;
- `aria-expanded` / `aria-controls` ;
- gestion focus overlays/recherche/menu +/modal ;
- fermeture Escape cohérente ;
- cibles tactiles suffisantes ;
- contraste light/dark ;
- aucun statut dépendant uniquement de la couleur.

**Gate D6 :** navigation clavier complète sans piège de focus.

## D7 — Responsive & mobile réel — P1

**Goal :** certifier petits écrans et desktop.

- viewports 390 / 430 / 768 / 1280 px ;
- header, recherche, menu +, cartes, file d'attente, badges/statuts, graphiques ;
- aucun overflow horizontal ;
- actions file d'attente utilisables à 390 px ;
- aucun chevauchement avec navigation fixe/mobile ;
- light + dark si supportés.

**Gate D7 :** matrice responsive complète sans finding bloquant.

## D8 — Tests & états dégradés — P1

**Goal :** couverture Dashboard dédiée reproductible.

- Vitest/Testing Library ;
- loading, données, vide, stats KO, RDV KO, finance KO, health KO ;
- permissions par rôle ;
- recherche debounce / aucun résultat / sélection ;
- transitions RDV `prévu -> attente -> fauteuil -> terminé` ;
- Ghost Secrétariat ;
- accordéon performance et menu ajout rapide.

**Gate D8 :** suite Dashboard verte, indépendante des données de production.

## D9 — Certification finale exact-head — P0

**Goal :** fermer le chantier avec preuves sur le même HEAD.

- lint/tests/build frontend ;
- CI exacte après résolution de la facturation GitHub ;
- smoke navigateur ;
- responsive 390/430/768/1280 ;
- permissions frontend + backend double-check ;
- absence de texte interne/dev ;
- console sans erreur bloquante ;
- re-audit indépendant section par section ;
- score final documenté, cible ≥ 9,0/10.

**Gate D9 :** closeout uniquement si toutes les preuves requises sont attachées au même HEAD.

## Avancement canonique

- D1 : **FERMÉ ✅**
- D2 : 0 %
- D3 : 0 %
- D4 : 0 %
- D5 : 0 %
- D6 : 0 %
- D7 : 0 %
- D8 : 0 %
- D9 : 0 %

**Chantier Dashboard refonte : 1/9 lots fermés = 11 %.**

## Findings baseline à ne pas perdre

1. `hasAccess()` Dashboard divergeait de Sidebar et comportait des fallbacks permissifs — **traité D1**.
2. Finance était chargée/rendue sans garde `accounting` explicite — **traité D1**.
3. `cabinetHealth === null` peut afficher `Système local actif` — **ouvert D2**.
4. Marketplace expose `Pourquoi ici` avec rationale de développement — **ouvert D3**.
5. Dashboard concentre trop de domaines et d'appels API — **ouvert D4**.
6. Contrôles iconiques/accessibilité à durcir — **ouvert D6**.
7. Pas de couverture Dashboard dédiée suffisante — **ouvert D8**.
8. CI globale actuellement indisponible pour facturation/plafond GitHub — **dette externe à solder D9**.

## Score baseline

| Domaine | Baseline |
|---|---:|
| Header / recherche | 7,7 |
| Actions principales | 8,8 |
| Marketplace | 4,0 |
| Activité récente | 8,2 |
| File d'attente | 8,5 |
| Performance hebdomadaire | 8,0 |
| Finances | 5,8 |
| Santé système | 5,8 |
| Intelligence / alertes | 7,8 |
| Business insights | 7,5 |
| Responsive statique | 8,4 |
| Accessibilité | 6,4 |
| Architecture | 6,5 |
| **Global** | **7,2 / 10** |

---

Cette roadmap est le registre canonique du chantier Dashboard. Toute fermeture, modification de scope ou preuve doit être reflétée ici.