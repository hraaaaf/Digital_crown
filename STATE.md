# STATE — DigitalCrown

> Fichier de reprise (handoff). **Lis-moi en premier** pour savoir où on en est.
> Le bloc AUTO ci-dessous est régénéré automatiquement à chaque fin de session : ne l'édite pas à la main.
> Les sections plus bas sont à toi (l'agent) : tiens-les à jour avant de t'arrêter.

<!-- STATE:AUTO:START -->
## Dernière session (auto — ne pas éditer à la main)
- **Mis à jour :** 2026-06-16 09:05
- **Branche :** `master`
- **Worktree :** `C:/Users/lenovo/Documents/Cabinet/DigitalCrown`

### Fichiers touchés
- _(aucun fichier modifié détecté)_

### Dernières demandes
- Go <system-reminder>Message sent at Tue 2026-06-16 08:35:42 UTC.</system-reminder>
- Go <system-reminder>Message sent at Tue 2026-06-16 08:36:05 UTC.</system-reminder>
- Oki go <system-reminder>Message sent at Tue 2026-06-16 08:40:10 UTC.</system-reminder>
- Pour chaque compte qu’il soit dentiste ou assistante le proprio lui donne les acces qu’il veut <system-reminder>Message sent at Tue 2026-06-16 08:49:23 UTC.</sy
- Quand si tu as fini, mets à jour session point m t et la route map et tous les fichiers point m t et on ferme cette session pour ouvrir une autre qui se, qui se
- 4.8/10 !? <system-reminder>Message sent at Tue 2026-06-16 08:53:57 UTC.</system-reminder>
- Fais cet audit et donne une note réelle si c’est encore 4.8 dis le <system-reminder>Message sent at Tue 2026-06-16 08:55:36 UTC.</system-reminder>
- Sur la partie prothese en general commente le code et mets la section comme en construction ou bientôt disponible.. <system-reminder>Message sent at Tue 2026-06
<!-- STATE:AUTO:END -->

## Prochaine action
- **Nouvelle session dédiée au CrownBot / chatbot.** V1 commercialisation et audit RBAC/mobile/PWA sont bouclés (commits `3377eb7` + `f6b5552`). Le bot a déjà été durci sur la branche `crownbot` (mergée, commits 9–13 : execute réel, finance O(1), sécurité lab, contexte multi-turn, carte de confirmation) — le score 4.8/10 cité dans `SESSION.md` est la **baseline de départ avant ces fixes**, pas l'état actuel. Pistes restantes : streaming réponses, élargir la couverture d'intents, historique par `patient_id`.

## État V1 (16 Juin 2026)
- **Architecture local-first confirmée** : tout en local (SQLite/`%APPDATA%`), seul Firebase est en ligne (signup + validation + kill-switch licence). Pas de domaine, pas de SaaS hébergé.
- **Reste avant commercialisation = config seulement** (aucun code) : SMTP, `SUPERADMIN_EMAIL`, validation juridique des CGU/Privacy (`LegalPage.tsx`). Lancer `scripts/check-production-readiness.ps1` pour le check.

## Blocker / en attente
- Aucun blocker technique actuel.
- Les tests RBAC (`backend/tests/test_access_control.py`) nécessitent le venv backend avec `python-jose` installé — à lancer dans l'environnement backend, pas le Python système.

## Décisions prises
- **Accès par sous-compte décidé par le proprio** : dentiste associé OU assistante, le proprio attribue librement chaque permission (9 cases) via `TeamManager`. Accès total réservé au proprio (`employer_id=NULL`). Déjà implémenté, validé CTO.
- **Statuts RDV mobile** : vocabulaire mobile simplifié (PLANIFIE/EN_COURS/TERMINE/ANNULE) ≠ enum métier (PREVU/EN_FAUTEUIL/TERMINE/ANNULE). Mappés via une couche de conversion dans `mobile.py`. Ne jamais passer une valeur mobile directement à `models.AppointmentStatus()`.
- **Email superadmin via `SUPERADMIN_EMAIL`** (env), plus jamais codé en dur.
- **Permission `clinical` = portée complète** : couvre le CRUD données cliniques (pharmacopée, contre-indications, protocoles) ET les 5 routes IA par patient. Décision validée par le CTO.
- **`user_id` nullable sur BotSession** : les anciennes sessions sans `user_id` n'apparaissent dans aucune liste (comportement clean sans migration de données, impossible de savoir à qui elles appartiennent).
- **Cache patients 2 min TTL** : évite le rechargement à chaque navigation sans risque de stale trop long.
- **WS auth via `?token=`** : contournement du cross-port en dev (les cookies ne suivent pas les WebSockets cross-origin) — le token vient de `localStorage`/`sessionStorage`.

## Questions ouvertes
- Aucune question ouverte pour l'instant.
