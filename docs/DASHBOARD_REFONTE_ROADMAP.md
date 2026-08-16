# Dashboard — Roadmap de refonte gouvernée

**Statut :** canonique / à exécuter  
**Créé :** 2026-08-16  
**Baseline auditée :** `master@026f78290cda53ea1b07ba5e8bfd39836448d6ce`  
**Page :** `frontend/src/pages/Dashboard.tsx`  
**Score audit initial :** **7,2 / 10**  
**Objectif de sortie :** **≥ 9,0 / 10**, sans régression clinique, financière, permissions, navigation ni responsive.

## Règles de gouvernance

- Aucun lot n'est crédité tant que son code, ses tests ciblés et sa preuve de validation ne sont pas terminés.
- Les permissions doivent être fail-closed côté interface et rester autoritaires côté backend.
- Ne jamais masquer une absence de preuve système derrière un état rassurant.
- Préserver le fonctionnement local-first de Digital Crown.
- Les changements doivent être découpés en lots indépendants et réversibles.
- Toute refonte visuelle doit conserver les flux métier utiles avant d'ajouter du polish.
- Certification finale sur HEAD exact, avec responsive et états réels.

## Lots de travail

### D1 — Permissions & exposition des données — P0

**But :** supprimer les comportements fail-open et aligner Dashboard / Sidebar / backend.

- Extraire `hasAccess()` dans une source partagée unique.
- Supprimer les fallbacks `return true` pour rôle inconnu / utilisateur non résolu.
- Aligner le fallback secrétaire avec la politique canonique.
- Conditionner les widgets financiers à `accounting`.
- Vérifier que les endpoints financiers/admin restent eux-mêmes protégés côté backend.
- Ajouter tests de matrice de rôles : admin, propriétaire dentiste, sous-dentiste, secrétaire, rôle inconnu, utilisateur absent.

**Gate D1 :** aucune donnée ou action sensible rendue sans permission explicite.

### D2 — Vérité du statut système — P0

**But :** rendre le statut système factuel et non trompeur.

- Remplacer le comportement `cabinetHealth === null => Système local actif`.
- États minimum : `opérationnel`, `vigilance`, `critique`, `non vérifié`.
- Distinguer chargement, timeout/API indisponible et absence d'autorisation.
- Définir couleur + texte + icône accessibles pour chaque état.
- Tester polling, erreur réseau et récupération après erreur.

**Gate D2 :** aucun état positif n'est affiché sans preuve de santé disponible.

### D3 — Marketplace / approvisionnement — P1

**But :** transformer le bloc en vraie entrée produit.

- Supprimer entièrement le panneau utilisateur `Pourquoi ici` et tout rationale de développement (`frontend only`, `re-dessiner`, etc.).
- Corriger les textes/accents.
- Garder une carte Marketplace claire avec bénéfice métier réel.
- Vérifier visibilité selon rôle et pertinence cabinet.
- Éviter que Marketplace concurrence les tâches cliniques prioritaires.

**Gate D3 :** zéro texte interne/dev visible dans l'interface.

### D4 — Architecture du Dashboard — P1

**But :** sortir du composant monolithique sans changer le comportement.

- Décomposer au minimum : `DashboardHeader`, `QuickActions`, `MarketplaceCard`, `RecentActivity`, `WaitingRoom`, `WeeklyPerformance`, `FinanceSummary`, `CabinetHealth`, `IntelligenceAlerts`, `BusinessInsights`.
- Extraire hooks/data loaders par domaine.
- Centraliser les états loading/error/empty.
- Éviter les appels API dispersés dans un seul `useEffect` géant.
- Conserver les `data-tour` nécessaires à l'onboarding.

**Gate D4 :** comportement fonctionnel identique, composants testables isolément.

### D5 — Hiérarchie UX / densité — P1

**But :** faire du Dashboard un cockpit clinique, pas un mini-BI permanent.

Ordre cible :
1. contexte du jour + recherche + actions rapides ;
2. file d'attente / arrivées ;
3. activité récente ;
4. alertes réellement actionnables ;
5. finances / performance en niveau secondaire ou repliable ;
6. santé système/admin en niveau tertiaire ;
7. Marketplace comme entrée secondaire.

- Réduire la répétition de cartes et titres.
- Définir ce qui est visible immédiatement vs replié.
- Garder les informations décisionnelles, retirer le bruit.
- Vérifier les empty states et les cabinets nouvellement installés.

**Gate D5 :** les trois tâches les plus fréquentes sont identifiables et actionnables sans recherche visuelle.

### D6 — Accessibilité & interactions — P1

**But :** rendre toutes les interactions robustes clavier/lecteur d'écran.

- Ajouter noms accessibles explicites aux boutons iconiques.
- `aria-expanded` / `aria-controls` pour accordéons et menus.
- Gestion focus des overlays, recherche, menu + et modal mobile.
- Fermeture Escape cohérente.
- Cibles tactiles suffisantes.
- Contraste clair/sombre vérifié.
- Ne pas dépendre uniquement de la couleur pour les statuts.

**Gate D6 :** navigation clavier complète des actions Dashboard sans piège de focus.

### D7 — Responsive & mobile réel — P1

**But :** certifier l'usage cabinet sur petits écrans et desktop.

- Viewports minimum : 390, 430, 768, 1280 px.
- Vérifier header, recherche 288 px, menu +, cartes, file d'attente, badges/statuts et graphiques.
- Aucun overflow horizontal.
- Actions de file d'attente utilisables à 390 px.
- Aucun chevauchement avec navigation fixe/mobile.
- Vérifier light + dark si les deux sont supportés.

**Gate D7 :** matrice responsive complète sans finding bloquant.

### D8 — Tests & états dégradés — P1

**But :** donner au Dashboard une couverture dédiée reproductible.

- Créer tests Dashboard ciblés Vitest/Testing Library.
- Cas : chargement, données présentes, données vides, API stats KO, rendez-vous KO, finance KO, health KO.
- Cas permissions par rôle.
- Cas recherche avec debounce + aucun résultat + résultat sélectionné.
- Cas transitions rendez-vous `prévu -> attente -> fauteuil -> terminé`.
- Vérifier le Ghost Secrétariat après séance terminée.
- Tester accordéon performance et menu d'ajout rapide.

**Gate D8 :** suite Dashboard verte et indépendante des données de production.

### D9 — Certification finale exact-head — P0 de clôture

**But :** fermer le chantier avec preuves, pas avec optimisme.

- Lint/tests/build frontend verts.
- Vérification CI sur HEAD exact.
- Smoke navigateur des parcours principaux.
- Responsive 390/430/768/1280.
- Permissions double-check frontend + backend.
- Vérification absence de texte interne/dev.
- Vérification console sans erreur bloquante.
- Re-audit indépendant section par section.
- Score final documenté ; cible ≥ 9,0/10.

**Gate D9 :** closeout seulement si toutes les preuves sont attachées au même HEAD.

## Ordre d'exécution recommandé

`D1 -> D2 -> D3 -> D4 -> D5 -> D6 -> D7 -> D8 -> D9`

D1/D2 sont prioritaires car ils concernent la vérité des permissions et de l'état système. D3 est un nettoyage produit immédiat. D4 stabilise ensuite l'architecture avant la refonte UX et la certification.

## Avancement canonique

- D1 : 0 %
- D2 : 0 %
- D3 : 0 %
- D4 : 0 %
- D5 : 0 %
- D6 : 0 %
- D7 : 0 %
- D8 : 0 %
- D9 : 0 %

**Chantier Dashboard refonte : 0/9 lots fermés = 0 %.**

## Findings baseline à ne pas perdre

1. `hasAccess()` local du Dashboard diverge de Sidebar et comporte des fallbacks permissifs.
2. Finance est chargée/rendue sans garde frontend `accounting` explicite.
3. `cabinetHealth === null` peut afficher `Système local actif`, ce qui confond inconnu et sain.
4. Marketplace expose un panneau `Pourquoi ici` avec rationale de développement.
5. Le composant Dashboard concentre trop de domaines et d'appels API.
6. Plusieurs contrôles iconiques reposent surtout sur `title` et doivent être durcis côté accessibilité.
7. La baseline n'avait pas de preuve de tests Dashboard dédiés retrouvée pendant l'audit.
8. La CI du HEAD baseline était rouge avant exécution réelle des étapes, donc non exploitable comme certification fonctionnelle.

## Score de référence

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

Cette roadmap est le registre canonique du chantier Dashboard. Toute modification de scope, fermeture de lot ou progression doit être reflétée ici afin d'éviter qu'un finding soit perdu entre deux sessions.