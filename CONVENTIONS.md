# Conventions — Digital Crown

> Règles de développement et standards de qualité. 
> *Toute modification de code doit respecter ces règles.*

## 1. Principes Fondamentaux
- **SOLID, DRY, KISS** appliqués strictement.
- Optimisation de la complexité algorithmique.
- Zéro "Small Talk" dans les réponses de l'agent.
- Maintien scrupuleux des docstrings et commentaires existants.

## 2. Naming Conventions & Style
- [À définir en fonction de la stack : ex: snake_case, camelCase]
- Typage strict priorisé.

## 3. Workflow de l'Agent
- Utilisation du système de scoring (Complexité / Analyse / Plan) avant chaque implémentation.
- Mise à jour de `STATE.md` en fin de session obligatoire (sections intentionnelles : Prochaine action, Blocker, Décisions).
