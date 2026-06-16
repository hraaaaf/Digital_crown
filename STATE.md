# STATE — DigitalCrown

> Fichier de reprise (handoff). **Lis-moi en premier** pour savoir où on en est.
> Le bloc AUTO ci-dessous est régénéré automatiquement à chaque fin de session : ne l'édite pas à la main.
> Les sections plus bas sont à toi (l'agent) : tiens-les à jour avant de t'arrêter.

<!-- STATE:AUTO:START -->
## Dernière session (auto — ne pas éditer à la main)
- **Mis à jour :** 2026-06-16 01:22
- **Branche :** `master`
- **Worktree :** `C:/Users/lenovo/Documents/Cabinet/DigitalCrown`

### Fichiers touchés
- _(aucun fichier modifié détecté)_

### Dernières demandes
- _(rien à extraire)_
<!-- STATE:AUTO:END -->

## Prochaine action
- **Committer et merger** : toutes les modifications de la branche `crownbot` sont prêtes et vérifiées (lint ✓, build ✓, py_compile ✓). Créer un commit puis ouvrir une PR vers `master`.

## Blocker / en attente
- Aucun blocker technique actuel.
- Les tests RBAC (`backend/tests/test_access_control.py`) nécessitent le venv backend avec `python-jose` installé — à lancer dans l'environnement backend, pas le Python système.

## Décisions prises
- **Permission `clinical` = portée complète** : couvre le CRUD données cliniques (pharmacopée, contre-indications, protocoles) ET les 5 routes IA par patient. Décision validée par le CTO.
- **`user_id` nullable sur BotSession** : les anciennes sessions sans `user_id` n'apparaissent dans aucune liste (comportement clean sans migration de données, impossible de savoir à qui elles appartiennent).
- **Cache patients 2 min TTL** : évite le rechargement à chaque navigation sans risque de stale trop long.
- **WS auth via `?token=`** : contournement du cross-port en dev (les cookies ne suivent pas les WebSockets cross-origin) — le token vient de `localStorage`/`sessionStorage`.

## Questions ouvertes
- Aucune question ouverte pour l'instant.
