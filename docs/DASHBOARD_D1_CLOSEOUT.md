# Dashboard D1 — Closeout

**Lot :** D1 — Permissions & exposition des données  
**Statut :** FERMÉ sur certification ciblée Linux  
**Date :** 2026-08-16  
**PR :** #106  
**Head fonctionnel certifié :** `1f32b67683c14cfaab0a1a569ca9231aa231a5a4`

## Goal

Supprimer les comportements fail-open du Dashboard et aligner la politique d'accès frontend/backend afin qu'aucune donnée ou action sensible ne soit chargée ou rendue hors permission canonique.

## Résultat vérifié

- politique frontend `hasAccess()` centralisée et fail-closed ;
- rôle inconnu et utilisateur non résolu refusés par défaut ;
- dentiste propriétaire : accès complet ;
- dentiste salarié legacy : clinique autorisé, finance/admin refusés ;
- secrétaire legacy : patients + agenda uniquement ;
- toute matrice explicite non vide prime sur les fallbacks legacy ;
- Dashboard et Sidebar utilisent la source frontend partagée ;
- requêtes financières Dashboard conditionnées à `accounting` ;
- `/stats/financial` et les endpoints d'intelligence financière sont protégés côté backend par `require_permission("accounting")` ;
- dashboard patient/alertes restent protégés par `patients` ;
- données santé cabinet réservées au scope admin côté Dashboard.

## Preuve Linux

Validation ciblée exécutée dans un environnement Linux isolé :

- backend RBAC : **6/6 PASS** ;
- policy frontend : compilation TypeScript **PASS** ;
- assertions frontend de matrice : **PASS** ;
- syntaxe Python `py_compile` : **PASS** ;
- invariants fail-closed : **PASS** ;
- guards des endpoints sensibles du HEAD vérifiés dans le code source exact.

Le rapport de session a été produit sous `D1_LINUX_CERTIFICATION.md` côté environnement d'exécution.

## CI externe

GitHub Actions n'a exécuté aucune étape. GitHub retourne explicitement :

> The job was not started because recent account payments have failed or your spending limit needs to be increased.

Ce blocage est externe au code. Les jobs avaient `runner_id=0` / aucune étape. Il est conservé comme dette de certification globale et devra être résolu avant la certification finale D9.

## Décision de fermeture

Le gate D1 porte sur l'autorisation et l'exposition de données. La validation Linux ciblée couvre directement ce risque ainsi que le câblage des guards backend/frontend. D1 est donc fermé malgré l'indisponibilité externe de GitHub Actions.

La CI globale, le build complet et la régression complète du dépôt restent obligatoires au plus tard au gate D9.
